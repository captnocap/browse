import base64
import os
from urllib.parse import urlparse

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException)

from .firefox import launch_firefox, find_firefox_path
from .content import extract_page_content, PageContent, Link, Form, FormField


def _dict_to_page_content(d):
    """Convert a dict (from session server) back into PageContent."""
    links = [Link(text=l["text"], href=l["href"]) for l in d.get("links", [])]
    forms = []
    for f in d.get("forms", []):
        fields = [FormField(name=ff["name"], type=ff["type"],
                            value=ff.get("value", ""),
                            placeholder=ff.get("placeholder", ""))
                  for ff in f.get("fields", [])]
        forms.append(Form(action=f["action"], method=f["method"], fields=fields))
    return PageContent(
        url=d.get("url", ""), title=d.get("title", ""),
        text=d.get("text", ""), links=links, forms=forms,
        meta=d.get("meta", {})
    )


class AgentBrowser:
    """AI agent browser built on Firefox ESR with RFP hardening.

    Two modes of operation:

    Quick mode — spawn a browser, use it, close it:
        with AgentBrowser() as browser:
            content = browser.navigate("https://example.com")

    Session mode — connect to a persistent browser that stays open:
        # Terminal: python -m browse.session
        agent = AgentBrowser.connect()
        agent.navigate("https://example.com")
        agent.detach()  # browser stays open
    """

    def __init__(self, firefox_path=None, proxy=None, headless=False,
                 profile_path=None, pref_dict=None):
        """Initialize the agent browser (quick mode — spawns a new browser).

        Args:
            firefox_path: Path to Firefox installation directory. If None,
                          reads from FIREFOX_PATH env var or browse.conf.
            proxy: Optional proxy URL ("socks5://host:port", "http://host:port").
            headless: Run headless (prefer XVFB instead for stealth).
            profile_path: Custom profile dir for persistent sessions.
            pref_dict: Additional Firefox preferences.
        """
        self._client = None  # only set in session mode
        self._owns_browser = True

        prefs = {}
        if proxy:
            prefs.update(self._parse_proxy(proxy))
        if pref_dict:
            prefs.update(pref_dict)

        self._driver = launch_firefox(
            firefox_path=firefox_path,
            headless=headless,
            profile_path=profile_path,
            pref_dict=prefs,
        )

    @classmethod
    def connect(cls):
        """Connect to a running persistent browser session.

        The browser must already be running via: python -m browse.session

        The returned AgentBrowser shares the browser with the human user.
        Call detach() when done to disconnect without closing the browser.
        """
        from .session import connect_to_session

        instance = object.__new__(cls)
        instance._driver = None
        instance._client = connect_to_session()
        instance._owns_browser = False
        return instance

    @property
    def _is_session_mode(self):
        return self._client is not None

    def detach(self):
        """Disconnect from the browser without closing it.

        In session mode: closes the socket, browser stays open.
        In quick mode: same as quit().
        """
        if self._is_session_mode:
            self._client.close()
            self._client = None
        else:
            self.quit()

    @staticmethod
    def _parse_proxy(proxy_url):
        """Convert a proxy URL string into Firefox preference dict."""
        parsed = urlparse(proxy_url)
        prefs = {}

        if parsed.scheme in ("socks5", "socks"):
            prefs["network.proxy.type"] = 1
            prefs["network.proxy.socks"] = parsed.hostname
            prefs["network.proxy.socks_port"] = parsed.port
            prefs["network.proxy.socks_version"] = 5
            prefs["network.proxy.socks_remote_dns"] = True
        elif parsed.scheme in ("socks4",):
            prefs["network.proxy.type"] = 1
            prefs["network.proxy.socks"] = parsed.hostname
            prefs["network.proxy.socks_port"] = parsed.port
            prefs["network.proxy.socks_version"] = 4
        elif parsed.scheme in ("http", "https"):
            prefs["network.proxy.type"] = 1
            prefs["network.proxy.http"] = parsed.hostname
            prefs["network.proxy.http_port"] = parsed.port
            prefs["network.proxy.ssl"] = parsed.hostname
            prefs["network.proxy.ssl_port"] = parsed.port
        else:
            raise ValueError(f"Unsupported proxy scheme: {parsed.scheme}")

        return prefs

    # ─── Challenge Handling ──────────────────────────────────────────────

    def _handle_challenge(self, result):
        """If a challenge was detected, wait for human to solve it.

        Prints a message, polls until the challenge clears, then returns
        the resulting page content.
        """
        challenge_type = result.get("challenge")
        if not challenge_type:
            return _dict_to_page_content(result)

        labels = {
            "google_captcha": "Google CAPTCHA",
            "cloudflare": "Cloudflare challenge",
            "access_denied": "Access denied",
            "bot_block": "Bot detection block",
            "captcha": "CAPTCHA",
        }
        label = labels.get(challenge_type, challenge_type)
        print(f"[browse] {label} detected — waiting for you to solve it...")

        challenge_url = result.get("url", "")
        cleared = self._client.send({"cmd": "wait_for_clear", "timeout": 120,
                                     "challenge_url": challenge_url})

        if cleared.get("cleared"):
            print(f"[browse] Challenge cleared. Resuming.")
            return _dict_to_page_content(cleared)
        else:
            print(f"[browse] Timed out waiting for challenge to clear.")
            return PageContent(url=result.get("url", ""), title="",
                               text="", links=[], forms=[], meta={})

    # ─── Browser Actions ──────────────────────────────────────────────────

    def navigate(self, url, timeout=30):
        """Navigate to a URL and wait for the page to load.

        If a CAPTCHA or challenge page is detected, prints a message and
        waits for the human to solve it before returning.
        """
        if self._is_session_mode:
            result = self._client.send({"cmd": "navigate", "url": url,
                                        "timeout": timeout})
            return self._handle_challenge(result)
        else:
            self._driver.set_page_load_timeout(timeout)
            self._driver.get(url)
            return extract_page_content(self._driver)

    def click(self, selector, by=By.CSS_SELECTOR, timeout=10):
        """Click an element on the page."""
        if self._is_session_mode:
            return self._client.send({"cmd": "click", "selector": selector,
                                      "by": by, "timeout": timeout})
        else:
            element = WebDriverWait(self._driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
            element.click()
            return True

    def type_text(self, selector, text, by=By.CSS_SELECTOR, timeout=10,
                  clear_first=True):
        """Type text into an input element."""
        if self._is_session_mode:
            return self._client.send({"cmd": "type_text", "selector": selector,
                                      "text": text, "by": by,
                                      "timeout": timeout, "clear": clear_first})
        else:
            element = WebDriverWait(self._driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
            if clear_first:
                element.clear()
            element.send_keys(text)

    def extract_content(self) -> PageContent:
        """Extract structured content from the current page.

        If a challenge page is detected, waits for the human to solve it
        before extracting.
        """
        if self._is_session_mode:
            # Check for challenge first
            check = self._client.send({"cmd": "check_challenge"})
            if check.get("challenge"):
                result = {"challenge": check["challenge"],
                          "url": check.get("url", "")}
                return self._handle_challenge(result)
            result = self._client.send({"cmd": "extract_content"})
            return _dict_to_page_content(result)
        else:
            return extract_page_content(self._driver)

    def extract_links(self) -> list[Link]:
        """Extract all links from the current page."""
        return self.extract_content().links

    def screenshot(self, path=None):
        """Take a screenshot. Returns PNG bytes, or saves to path."""
        if self._is_session_mode:
            result = self._client.send({"cmd": "screenshot"})
            png_data = base64.b64decode(result["png_b64"])
        else:
            png_data = self._driver.get_screenshot_as_png()

        if path:
            with open(path, "wb") as f:
                f.write(png_data)
        return png_data

    def wait_for(self, selector, by=By.CSS_SELECTOR, timeout=30):
        """Wait for an element to be present on the page."""
        if self._is_session_mode:
            # In session mode, just poll via extract_content
            import time
            deadline = time.time() + timeout
            while time.time() < deadline:
                content = self.extract_content()
                if selector.lower() in content.text.lower():
                    return True
                time.sleep(0.5)
            raise TimeoutError(f"Timed out waiting for '{selector}'")
        else:
            return WebDriverWait(self._driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )

    def execute_js(self, script, *args):
        """Execute JavaScript in the page context."""
        if self._is_session_mode:
            return self._client.send({"cmd": "execute_js", "script": script})
        else:
            return self._driver.execute_script(script, *args)

    @property
    def current_url(self):
        """Return the current page URL."""
        if self._is_session_mode:
            return self._client.send({"cmd": "current_url"})
        return self._driver.current_url

    @property
    def page_source(self):
        """Return the current page HTML source."""
        if self._is_session_mode:
            return self._client.send({"cmd": "page_source"})
        return self._driver.page_source

    def back(self):
        """Navigate back."""
        if self._is_session_mode:
            self._client.send({"cmd": "back"})
        else:
            self._driver.back()

    def forward(self):
        """Navigate forward."""
        if self._is_session_mode:
            self._client.send({"cmd": "forward"})
        else:
            self._driver.forward()

    def refresh(self):
        """Refresh the current page."""
        if self._is_session_mode:
            self._client.send({"cmd": "refresh"})
        else:
            self._driver.refresh()

    @property
    def driver(self):
        """Access the underlying driver (only in quick mode)."""
        if self._is_session_mode:
            raise RuntimeError("No direct driver access in session mode. "
                               "Use the AgentBrowser methods instead.")
        return self._driver

    def run_script(self, name_or_path, **params):
        """Execute a navigation script's direct-executable steps.

        Parses the script, substitutes parameters, and runs steps that
        map to known browser actions (navigate, click, type, extract).
        Returns a list of PageContent from extraction steps.

        Args:
            name_or_path: Script name or path to .md file.
            **params: Parameter values to substitute in the script.

        Returns:
            list[PageContent]: Content extracted at each extraction step.
        """
        import re
        from .scripts import load_script

        script = load_script(name_or_path)

        missing = [p for p in script.params if p not in params]
        if missing:
            raise ValueError(f"Missing parameters: {', '.join(missing)}")

        def sub(text):
            for k, v in params.items():
                text = text.replace(f"{{{k}}}", v)
            return text

        url_re = re.compile(r"https?://\S+")
        results = []

        for step in script.steps:
            step = sub(step)
            lower = step.lower()

            if lower.startswith("navigate to "):
                m = url_re.search(step)
                if m:
                    content = self.navigate(m.group(0))
                    results.append(content)
            elif lower.startswith("wait for "):
                import time
                time.sleep(3)
            elif lower.startswith("click "):
                pass  # requires AI interpretation for selector
            elif lower.startswith("type "):
                pass  # requires AI interpretation for selector
            elif "extract" in lower:
                content = self.extract_content()
                results.append(content)

        if not results:
            results.append(self.extract_content())

        return results

    def quit(self):
        """Close the browser (quick mode) or disconnect (session mode)."""
        if self._is_session_mode:
            self.detach()
            return
        if self._driver:
            self._driver.quit()
            self._driver = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.quit()
