"""MCP server for browse — anti-fingerprint browser tools for AI agents.

Supports two modes:
  - Quick browsers: agent spawns one or more browsers, uses them, closes
    them. Supports parallel browsing across multiple instances.
  - Session: agent joins an existing human-controlled browser session.
    The browser stays open after the agent detaches.

The server auto-detects if a session is running and informs the agent
so it can ask the user which mode to use.

Usage (Claude Desktop / LM Studio config):
    {
      "mcpServers": {
        "browse": { "command": "browse-mcp" }
      }
    }
"""

import base64
import os
import sys
import time
import threading
from urllib.parse import urlparse

from fastmcp import FastMCP
from mcp.types import TextContent, ImageContent

from .content import extract_page_content
from .session import SessionClient, get_session_info, launch_session
from .agent import _dict_to_page_content
from .stealth import patch_libxul, is_patched

mcp = FastMCP(
    "browse",
    instructions=(
        "Anti-fingerprint browser tools. If browse_status shows a session is "
        "available, use browse_connect to attach to it. Otherwise use browse_open "
        "to launch a browser or browse_search to search. Each result includes "
        "suggested next actions. Multiple browsers can run in parallel."
    ),
)

# ─── Blocklist ────────────────────────────────────────────────────────────
# Sites the agent is not allowed to navigate to. The human can still browse
# these freely in the session — this only restricts agent-initiated navigation.
# Configured via BLOCKED_SITES in browse.conf (comma-separated domains).

def _load_blocklist():
    """Load blocked domains from browse.conf."""
    conf_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "browse.conf"
    )
    if not os.path.exists(conf_path):
        return set()
    with open(conf_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("BLOCKED_SITES="):
                raw = line.split("=", 1)[1]
                return {d.strip().lower() for d in raw.split(",") if d.strip()}
    return set()

_blocked_sites = _load_blocklist()


def _is_blocked(url):
    """Check if a URL's domain is on the blocklist."""
    if not _blocked_sites:
        return False
    try:
        domain = urlparse(url).netloc.lower()
        # Match domain and any subdomain (e.g. "4chan.org" blocks "boards.4chan.org")
        for blocked in _blocked_sites:
            if domain == blocked or domain.endswith("." + blocked):
                return True
    except Exception:
        pass
    return False


# ─── Browser Pool ─────────────────────────────────────────────────────────
# Each browser gets a short ID. Quick browsers are owned by the MCP server
# and closed on browse_close. Session browsers are detached, not closed.

_browsers = {}      # id -> {"driver": driver, "mode": "quick"|"session", "client": client_or_None}
_next_id = 1
_lock = threading.Lock()


def _new_id():
    global _next_id
    with _lock:
        bid = str(_next_id)
        _next_id += 1
        return bid


def _get_browser(browser_id=None):
    """Get a browser by ID. If None, returns the most recently created one."""
    if not _browsers:
        raise RuntimeError(
            "No browser open. Use browse_open to launch one, "
            "or browse_connect to join a session."
        )
    if browser_id is None:
        browser_id = max(_browsers.keys(), key=int)
    if browser_id not in _browsers:
        raise RuntimeError(
            f"Browser {browser_id} not found. "
            f"Active browsers: {', '.join(_browsers.keys())}"
        )
    return browser_id, _browsers[browser_id]


def _type_and_submit(browser, selector, text):
    """Type text into a field and press Enter to submit, like a human would."""
    if browser["mode"] == "session":
        browser["client"].send({"cmd": "type_text", "selector": selector,
                                 "text": text, "by": "css selector",
                                 "timeout": 10, "clear": True})
        browser["client"].send({"cmd": "send_keys", "selector": selector,
                                 "key": "RETURN", "by": "css selector",
                                 "timeout": 10})
    else:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        el = WebDriverWait(browser["driver"], 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        el.clear()
        el.send_keys(text)
        el.send_keys(Keys.RETURN)


def _extract(browser):
    """Extract page content from a browser instance.

    Checks for captcha/challenge pages first. If one is detected,
    waits for the human to solve it before extracting.
    """
    # Get current URL and check for challenge
    try:
        if browser["mode"] == "session":
            current = browser["client"].send({"cmd": "current_url"})
        else:
            current = browser["driver"].current_url
        challenge = _detect_challenge(current)
        if challenge:
            content = _wait_for_clear(browser, current)
            if content is not None:
                return content
    except Exception:
        pass

    if browser["mode"] == "session":
        result = browser["client"].send({"cmd": "extract_content"})
        return _dict_to_page_content(result)
    return extract_page_content(browser["driver"])


CHALLENGE_URL_PATTERNS = [
    ("/sorry/", "google_captcha"),
    ("google.com/sorry", "google_captcha"),
    ("/cdn-cgi/challenge", "cloudflare"),
    ("captcha", "captcha"),
]

CHALLENGE_LABELS = {
    "google_captcha": "Google CAPTCHA",
    "cloudflare": "Cloudflare challenge",
    "captcha": "CAPTCHA",
}


def _detect_challenge(url):
    """Check if a URL matches a known challenge/captcha pattern."""
    for pattern, challenge_type in CHALLENGE_URL_PATTERNS:
        if pattern in url:
            return challenge_type
    return None


def _wait_for_clear(browser, challenge_url, timeout=120):
    """Poll until the browser navigates away from a challenge page.

    Returns the extracted page content once clear, or None on timeout.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if browser["mode"] == "session":
                current = browser["client"].send({"cmd": "current_url"})
            else:
                current = browser["driver"].current_url
            if current != challenge_url and _detect_challenge(current) is None:
                time.sleep(2)  # let the destination page render
                return _extract(browser)
        except Exception:
            pass
        time.sleep(1)
    return None


def _navigate(browser, url, timeout=30):
    """Navigate a browser to a URL. Waits for captcha resolution if needed."""
    if _is_blocked(url):
        from .content import PageContent
        return PageContent(url=url, title="Blocked", text=f"This site is blocked. Choose a different URL.", links=[], forms=[], meta={})
    if browser["mode"] == "session":
        result = browser["client"].send({"cmd": "navigate", "url": url, "timeout": timeout})
        if result.get("challenge"):
            challenge_type = result["challenge"]
            label = CHALLENGE_LABELS.get(challenge_type, challenge_type)
            cleared = browser["client"].send({
                "cmd": "wait_for_clear", "timeout": 120,
                "challenge_url": result.get("url", ""),
            })
            if not cleared.get("cleared"):
                from .content import PageContent
                return PageContent(url=result.get("url", ""), title="", text=f"{label} — timed out waiting.", links=[], forms=[], meta={})
            return _dict_to_page_content(cleared)
        return _dict_to_page_content(result)
    else:
        browser["driver"].set_page_load_timeout(timeout)
        browser["driver"].get(url)
        current = browser["driver"].current_url
        challenge = _detect_challenge(current)
        if challenge:
            label = CHALLENGE_LABELS.get(challenge, challenge)
            content = _wait_for_clear(browser, current)
            if content is None:
                from .content import PageContent
                return PageContent(url=current, title="", text=f"{label} — timed out waiting.", links=[], forms=[], meta={})
            return content
        return extract_page_content(browser["driver"])


def _format_result(content, browser_id):
    """Format page content with actions menu."""
    lines = [content.for_llm()]
    lines.append("")
    lines.append(f"[Browser {browser_id}]")
    lines.append("")
    lines.append("--- What would you like to do? ---")

    named_links = [l for l in content.links if l.text.strip()]
    if named_links:
        lines.append("")
        lines.append(f"NAVIGATE to a link ({len(named_links)} available):")
        for link in named_links[:15]:
            lines.append(f'  - "{link.text.strip()[:60]}" -> {link.href}')
        if len(named_links) > 15:
            lines.append(f"  ... and {len(named_links) - 15} more")

    if content.forms:
        lines.append("")
        lines.append("FILL a form:")
        for form in content.forms:
            visible = [f for f in form.fields if f.type != "hidden"]
            if visible:
                names = [f.name or f.type for f in visible[:5]]
                lines.append(f"  - {form.method.upper()} {form.action} ({', '.join(names)})")

    lines.append("")
    lines.append("Or: browse_search, browse_back, browse_screenshot, browse_close")

    return "\n".join(lines)


# ─── Tools ────────────────────────────────────────────────────────────────


@mcp.tool
def browse_status() -> str:
    """Check browser status. If no browsers are open and a session is
    available, automatically connects to it.

    Only call this once — do NOT call browse_status again.
    """
    # If no browsers open and a session is available, auto-connect
    if not _browsers:
        session = get_session_info()
        if session:
            bid = _new_id()
            client = SessionClient(port=session["port"])
            client.send({"cmd": "ping"})
            _browsers[bid] = {"driver": None, "mode": "session", "client": client}
            content = _extract(_browsers[bid])
            return f"Connected as Browser {bid}.\n\n" + _format_result(content, bid)

    # Otherwise report what's open
    lines = []

    if _browsers:
        lines.append(f"Active browsers: {len(_browsers)}")
        for bid, b in _browsers.items():
            mode = b["mode"]
            try:
                if mode == "session":
                    url = b["client"].send({"cmd": "current_url"})
                else:
                    url = b["driver"].current_url
            except Exception:
                url = "(unknown)"
            lines.append(f"  Browser {bid} [{mode}]: {url}")
    else:
        lines.append("No browsers open. Use browse_open to launch a browser.")

    lines.append("")
    lines.append("Do NOT call browse_status again.")

    return "\n".join(lines)


@mcp.tool
def browse_open(url: str = "") -> str:
    """Launch a new browser and optionally navigate to a URL.

    The browser runs with full anti-fingerprinting (Tor Browser engine)
    and won't trigger bot detection. Returns a browser ID for use with
    other tools. Multiple browsers can be open simultaneously for
    parallel browsing.

    Args:
        url: URL to navigate to. If empty, opens to a blank page.
    """
    bid = _new_id()

    driver = launch_session()
    _browsers[bid] = {"driver": driver, "mode": "quick", "client": None}

    if url:
        content = _navigate(_browsers[bid], url)
        return f"Browser {bid} launched.\n\n" + _format_result(content, bid)
    else:
        return (
            f"Browser {bid} launched and ready.\n\n"
            f"Use browse_navigate with a URL to go somewhere, "
            f"or browse_search to search the web."
        )


@mcp.tool
def browse_connect() -> str:
    """Attach to an available browser session.

    Connects to a running browser. Use browse_close when done to
    disconnect (the browser stays open).
    """
    session = get_session_info()
    if session is None:
        return (
            "No session available. Use browse_open to launch a browser instead."
        )

    bid = _new_id()
    client = SessionClient(port=session["port"])
    client.send({"cmd": "ping"})

    _browsers[bid] = {"driver": None, "mode": "session", "client": client}

    content = _extract(_browsers[bid])
    return f"Connected as Browser {bid}.\n\n" + _format_result(content, bid)


@mcp.tool
def browse_navigate(url: str, browser_id: str = "") -> str:
    """Navigate to a URL in a browser.

    Args:
        url: The URL to visit.
        browser_id: Which browser to use. Leave empty for the most recent one.
    """
    bid, browser = _get_browser(browser_id or None)
    content = _navigate(browser, url)
    return _format_result(content, bid)


@mcp.tool
def browse_search(query: str, engine: str = "google", browser_id: str = "") -> str:
    """Search the web. Opens a browser if none exist.

    Args:
        query: What to search for.
        engine: "google" or "duckduckgo".
        browser_id: Which browser to use. Leave empty for the most recent one.
    """
    # Auto-open a browser if none exist
    if not _browsers:
        bid = _new_id()
        driver = launch_session()
        _browsers[bid] = {"driver": driver, "mode": "quick", "client": None}
    else:
        bid, _ = _get_browser(browser_id or None)

    browser = _browsers[bid]

    if engine == "duckduckgo":
        _navigate(browser, "https://duckduckgo.com")
        selector = "input[name=q]"
    else:
        _navigate(browser, "https://www.google.com")
        selector = "textarea[name=q]"

    _type_and_submit(browser, selector, query)

    time.sleep(3)
    content = _extract(browser)
    return _format_result(content, bid)


@mcp.tool
def browse_click(selector: str, browser_id: str = "") -> str:
    """Click an element on the page.

    Args:
        selector: CSS selector for the element to click.
        browser_id: Which browser to use. Leave empty for the most recent one.
    """
    bid, browser = _get_browser(browser_id or None)

    if browser["mode"] == "session":
        browser["client"].send({"cmd": "click", "selector": selector,
                                 "by": "css selector", "timeout": 10})
    else:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        el = WebDriverWait(browser["driver"], 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        el.click()

    time.sleep(1)
    content = _extract(browser)
    return _format_result(content, bid)


@mcp.tool
def browse_type(selector: str, text: str, submit: bool = False, browser_id: str = "") -> str:
    """Type text into an input field.

    Args:
        selector: CSS selector for the input element.
        text: The text to type.
        submit: If True, submit the parent form after typing.
        browser_id: Which browser to use.
    """
    bid, browser = _get_browser(browser_id or None)

    if submit:
        _type_and_submit(browser, selector, text)
    else:
        if browser["mode"] == "session":
            browser["client"].send({"cmd": "type_text", "selector": selector, "text": text,
                                     "by": "css selector", "timeout": 10, "clear": True})
        else:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            el = WebDriverWait(browser["driver"], 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            el.clear()
            el.send_keys(text)

    content = _extract(browser)
    return _format_result(content, bid)


@mcp.tool
def browse_extract(browser_id: str = "") -> str:
    """Re-extract content from the current page.

    Use if the page has changed (JS updates, scrolling, waiting).

    Args:
        browser_id: Which browser. Leave empty for the most recent one.
    """
    bid, browser = _get_browser(browser_id or None)
    content = _extract(browser)
    return _format_result(content, bid)


@mcp.tool
def browse_screenshot(browser_id: str = "") -> list:
    """Take a screenshot of the current page.

    Args:
        browser_id: Which browser. Leave empty for the most recent one.
    """
    bid, browser = _get_browser(browser_id or None)

    if browser["mode"] == "session":
        result = browser["client"].send({"cmd": "screenshot"})
        png_b64 = result["png_b64"]
        url = browser["client"].send({"cmd": "current_url"})
    else:
        png_b64 = base64.b64encode(browser["driver"].get_screenshot_as_png()).decode()
        url = browser["driver"].current_url

    return [
        TextContent(type="text", text=f"[Browser {bid}] Screenshot of: {url}"),
        ImageContent(type="image", data=png_b64, mimeType="image/png"),
    ]


@mcp.tool
def browse_back(browser_id: str = "") -> str:
    """Go back to the previous page.

    Args:
        browser_id: Which browser. Leave empty for the most recent one.
    """
    bid, browser = _get_browser(browser_id or None)
    if browser["mode"] == "session":
        browser["client"].send({"cmd": "back"})
    else:
        browser["driver"].back()
    time.sleep(1)
    content = _extract(browser)
    return _format_result(content, bid)


@mcp.tool
def browse_forward(browser_id: str = "") -> str:
    """Go forward to the next page.

    Args:
        browser_id: Which browser. Leave empty for the most recent one.
    """
    bid, browser = _get_browser(browser_id or None)
    if browser["mode"] == "session":
        browser["client"].send({"cmd": "forward"})
    else:
        browser["driver"].forward()
    time.sleep(1)
    content = _extract(browser)
    return _format_result(content, bid)


@mcp.tool
def browse_close(browser_id: str = "") -> str:
    """Close a browser.

    If attached via browse_connect, this disconnects without closing
    the browser. If launched via browse_open, this closes it entirely.

    Args:
        browser_id: Which browser to close. Leave empty for the most recent one.
    """
    bid, browser = _get_browser(browser_id or None)

    if browser["mode"] == "session":
        try:
            browser["client"].close()
        except Exception:
            pass
        del _browsers[bid]
        return f"Browser {bid} disconnected."
    else:
        try:
            browser["driver"].quit()
        except Exception:
            pass
        del _browsers[bid]
        remaining = len(_browsers)
        if remaining:
            return f"Browser {bid} closed. {remaining} browser(s) still active."
        return f"Browser {bid} closed."


# ─── Entry Point ──────────────────────────────────────────────────────────

def main():
    transport = "stdio"
    if "--sse" in sys.argv:
        transport = "sse"
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
