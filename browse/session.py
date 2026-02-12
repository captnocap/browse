"""Persistent browser session — launch once, connect many times.

Server (run in a terminal):
    python -m browse.session

Client (from Python, any other terminal):
    from browse import AgentBrowser
    agent = AgentBrowser.connect()
    agent.navigate("https://example.com")
    agent.detach()

The browser stays open between agent connections. The human uses it
normally via mouse/keyboard. The AI taps in via connect(), does work,
and taps out via detach().
"""

import base64
import json
import os
import signal
import socket
import sys
import threading
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .tbselenium import common as cm
from .tbselenium.utils import set_tbb_pref, prepend_to_env_var
from .content import extract_page_content
from .stealth import patch_libxul, is_patched, patch_omni, is_omni_patched, build_stealth_extension

SESSION_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".browse_session.json"
)

DEFAULT_PORT = 7331

# Color palette assigned round-robin to connected agents.
_AGENT_COLORS = [
    ("#00ff88", "green"),
    ("#00aaff", "blue"),
    ("#ff8800", "orange"),
    ("#ff00ff", "magenta"),
    ("#ffdd00", "yellow"),
    ("#00ffff", "cyan"),
    ("#ff4466", "red"),
    ("#aa88ff", "purple"),
]


def _read_conf():
    """Read browse.conf for TBB/geckodriver paths."""
    conf = {}
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conf_path = os.path.join(here, "browse.conf")
    if os.path.exists(conf_path):
        with open(conf_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    conf[k.strip()] = v.strip()
    return conf


def _setup_env(tbb_path):
    """Set up LD_LIBRARY_PATH, FONTCONFIG, etc. for Tor Browser."""
    browser_dir = os.path.join(tbb_path, cm.DEFAULT_TBB_BROWSER_DIR)
    tor_binary_dir = os.path.join(tbb_path, cm.DEFAULT_TOR_BINARY_DIR)
    os.environ["LD_LIBRARY_PATH"] = tor_binary_dir
    os.environ["FONTCONFIG_PATH"] = os.path.join(
        tbb_path, cm.DEFAULT_FONTCONFIG_PATH)
    os.environ["FONTCONFIG_FILE"] = cm.FONTCONFIG_FILE
    os.environ["HOME"] = browser_dir
    prepend_to_env_var("PATH", browser_dir)
    os.chdir(browser_dir)


def _apply_direct_prefs(driver):
    """Force direct-connection prefs via about:config on a running browser."""
    prefs = {
        'network.proxy.type': 0,
        'network.proxy.socks': '',
        'network.proxy.socks_port': 0,
        'network.proxy.socks_remote_dns': False,
        'network.proxy.http': '',
        'network.proxy.http_port': 0,
        'network.proxy.ssl': '',
        'network.proxy.ssl_port': 0,
        'network.proxy.no_proxies_on': '',
        'network.dns.disabled': False,
        'extensions.torlauncher.start_tor': False,
    }
    for name, value in prefs.items():
        set_tbb_pref(driver, name, value)


# ─── Command Server ──────────────────────────────────────────────────────
# Thin TCP server that holds the Selenium driver and executes commands
# sent as JSON lines. This lets any client (AI agent, script, etc.)
# control the browser without needing to own the driver process.

class SessionServer:
    def __init__(self, driver, port=DEFAULT_PORT):
        self.driver = driver
        self.port = port
        self.lock = threading.Lock()
        self._running = False
        # Per-agent tab tracking: agent_id -> {handle, color, color_name}
        self._agents = {}
        self._next_agent_id = 0
        self._human_tab = driver.current_window_handle

    # URLs that indicate a challenge/intercept page.
    # We only need to watch the URL — when the human clears the challenge,
    # the browser navigates away to the real destination.
    CHALLENGE_URL_PATTERNS = [
        # Google intercepts with /sorry/ before showing results
        ("/sorry/", "google_captcha"),
        ("google.com/sorry", "google_captcha"),
        # Cloudflare challenge pages
        ("/cdn-cgi/challenge", "cloudflare"),
        # Generic captcha services
        ("captcha", "captcha"),
    ]

    def detect_challenge(self):
        """Check if the current URL is a known challenge/intercept page.

        Returns a challenge type string if detected, or None if clear.
        """
        try:
            url = self.driver.current_url
            for pattern, challenge_type in self.CHALLENGE_URL_PATTERNS:
                if pattern in url:
                    return challenge_type
            return None
        except Exception:
            return None

    def _link_count(self):
        """Quick link count via JS — cheaper than full extraction."""
        try:
            return self.driver.execute_script(
                "return document.querySelectorAll('a[href]').length"
            )
        except Exception:
            return 0

    def _wait_for_stable_content(self, max_wait=5.0):
        """Wait for the page to stop loading by watching link count stabilize.

        Grabs an initial count, waits a beat, checks again. If the count
        grew, the page is still rendering — wait and re-check. Once it
        stabilizes (two consecutive reads match), return the content.
        """
        import time as _time
        deadline = _time.time() + max_wait

        # Wait for at least one link to appear
        while _time.time() < deadline:
            count = self._link_count()
            if count > 0:
                break
            _time.sleep(0.3)

        # Double-tap: check if count is still growing
        while _time.time() < deadline:
            first_count = self._link_count()
            _time.sleep(0.5)
            second_count = self._link_count()
            if second_count == first_count:
                break  # stable

        content = extract_page_content(self.driver)
        return content

    def wait_for_challenge_clear(self, challenge_url, poll_interval=1.0, timeout=120):
        """Poll until the URL changes away from the challenge page
        AND the destination page has fully rendered.
        """
        import time as _time
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            try:
                current = self.driver.current_url
                if current != challenge_url and self.detect_challenge() is None:
                    content = self._wait_for_stable_content()
                    return {
                        "cleared": True,
                        "url": content.url, "title": content.title,
                        "text": content.text,
                        "links": [{"text": l.text, "href": l.href} for l in content.links],
                        "forms": [{"action": f.action, "method": f.method,
                                   "fields": [{"name": ff.name, "type": ff.type,
                                               "value": ff.value, "placeholder": ff.placeholder}
                                              for ff in f.fields]}
                                  for f in content.forms],
                        "meta": content.meta,
                    }
            except Exception:
                pass
            _time.sleep(poll_interval)
        return {"cleared": False, "reason": "timeout"}

    def handle_command(self, cmd, agent_id=None):
        """Execute a command on the browser. Returns a JSON-serializable result."""
        action = cmd.get("cmd")

        if action == "navigate":
            self.driver.set_page_load_timeout(cmd.get("timeout", 30))
            self.driver.get(cmd["url"])
            # Check for challenge after navigation
            challenge = self.detect_challenge()
            if challenge:
                return {"challenge": challenge, "url": self.driver.current_url}
            content = self._wait_for_stable_content()
            return {
                "url": content.url, "title": content.title,
                "text": content.text,
                "links": [{"text": l.text, "href": l.href} for l in content.links],
                "forms": [{"action": f.action, "method": f.method,
                           "fields": [{"name": ff.name, "type": ff.type,
                                       "value": ff.value, "placeholder": ff.placeholder}
                                      for ff in f.fields]}
                          for f in content.forms],
                "meta": content.meta,
            }

        elif action == "check_challenge":
            challenge = self.detect_challenge()
            return {"challenge": challenge, "url": self.driver.current_url}

        elif action == "wait_for_clear":
            timeout = cmd.get("timeout", 120)
            poll = cmd.get("poll_interval", 1.0)
            challenge_url = cmd.get("challenge_url", self.driver.current_url)
            return self.wait_for_challenge_clear(challenge_url, poll, timeout)

        elif action == "extract_content":
            content = extract_page_content(self.driver)
            return {
                "url": content.url, "title": content.title,
                "text": content.text,
                "links": [{"text": l.text, "href": l.href} for l in content.links],
                "forms": [{"action": f.action, "method": f.method,
                           "fields": [{"name": ff.name, "type": ff.type,
                                       "value": ff.value, "placeholder": ff.placeholder}
                                      for ff in f.fields]}
                          for f in content.forms],
                "meta": content.meta,
            }

        elif action == "click":
            by = cmd.get("by", By.CSS_SELECTOR)
            timeout = cmd.get("timeout", 10)
            el = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, cmd["selector"]))
            )
            el.click()
            return True

        elif action == "type_text":
            by = cmd.get("by", By.CSS_SELECTOR)
            timeout = cmd.get("timeout", 10)
            el = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, cmd["selector"]))
            )
            if cmd.get("clear", True):
                el.clear()
            el.send_keys(cmd["text"])
            return True

        elif action == "send_keys":
            from selenium.webdriver.common.keys import Keys
            by = cmd.get("by", By.CSS_SELECTOR)
            timeout = cmd.get("timeout", 10)
            el = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, cmd["selector"]))
            )
            key_name = cmd.get("key", "RETURN")
            key = getattr(Keys, key_name, Keys.RETURN)
            el.send_keys(key)
            return True

        elif action == "screenshot":
            png = self.driver.get_screenshot_as_png()
            return {"png_b64": base64.b64encode(png).decode()}

        elif action == "execute_js":
            return self.driver.execute_script(cmd["script"])

        elif action == "add_cookie":
            self.driver.add_cookie(cmd["cookie"])
            return True

        elif action == "current_url":
            return self.driver.current_url

        elif action == "page_source":
            return self.driver.page_source

        elif action == "back":
            self.driver.back()
            return True

        elif action == "forward":
            self.driver.forward()
            return True

        elif action == "refresh":
            self.driver.refresh()
            return True

        elif action == "ping":
            if agent_id and agent_id in self._agents:
                agent = self._agents[agent_id]
                return {
                    "pong": True,
                    "agent_id": agent_id,
                    "color": agent["color"],
                    "color_name": agent["color_name"],
                }
            return "pong"

        elif action == "list_agents":
            agents = []
            for aid, info in self._agents.items():
                try:
                    self.driver.switch_to.window(info["handle"])
                    url = self.driver.current_url
                except Exception:
                    url = "(unknown)"
                agents.append({
                    "id": aid,
                    "color": info["color"],
                    "color_name": info["color_name"],
                    "url": url,
                })
            # Switch back to requesting agent's tab
            if agent_id and agent_id in self._agents:
                self.driver.switch_to.window(self._agents[agent_id]["handle"])
            return agents

        else:
            raise ValueError(f"Unknown command: {action}")

    @property
    def client_count(self):
        return len(self._agents)

    def _update_indicator(self):
        """Toggle the browseagent attribute on the browser chrome root element.
        Must hold self.lock (or be called right after releasing it when safe).
        """
        connected = len(self._agents) > 0
        try:
            with self.driver.context(self.driver.CONTEXT_CHROME):
                if connected:
                    self.driver.execute_script(
                        'document.documentElement.setAttribute("browseagent", "true");'
                    )
                else:
                    self.driver.execute_script(
                        'document.documentElement.removeAttribute("browseagent");'
                    )
        except Exception:
            pass

    # ─── Per-Agent Tab Management ─────────────────────────────────────

    def _assign_agent(self):
        """Open a new tab and assign it to a new agent. Must hold self.lock.

        Uses Firefox's gBrowser.addTab with inBackground:true so the new
        tab opens silently without stealing the user's focus.
        """
        self._next_agent_id += 1
        agent_id = self._next_agent_id
        color_idx = (agent_id - 1) % len(_AGENT_COLORS)
        color, color_name = _AGENT_COLORS[color_idx]

        startpage = 'file://' + os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'startpage.html')

        # Open a background tab via Firefox chrome API (no focus steal)
        try:
            with self.driver.context(self.driver.CONTEXT_CHROME):
                self.driver.execute_script(
                    "gBrowser.addTab(arguments[0], {"
                    "  inBackground: true,"
                    "  triggeringPrincipal: Services.scriptSecurityManager.getSystemPrincipal()"
                    "});",
                    startpage,
                )
        except Exception:
            # Fallback: standard window.open (will flash briefly)
            self.driver.switch_to.window(self._human_tab)
            self.driver.execute_script("window.open(arguments[0], '_blank');", startpage)

        # The new tab is the one not yet assigned to any agent or the human
        known = {self._human_tab} | {a["handle"] for a in self._agents.values()}
        new_handle = [h for h in self.driver.window_handles if h not in known][-1]

        self._agents[agent_id] = {
            "handle": new_handle,
            "color": color,
            "color_name": color_name,
        }

        # Ensure visual focus stays on the human tab
        self._restore_human_focus()
        return agent_id

    def _restore_human_focus(self):
        """Snap visual focus back to the human's tab via chrome API.

        Uses gBrowser.selectedTab to change the visible tab without
        affecting Selenium's internal browsing context.
        """
        try:
            with self.driver.context(self.driver.CONTEXT_CHROME):
                self.driver.execute_script(
                    "gBrowser.selectTabAtIndex(0);"
                )
        except Exception:
            try:
                self.driver.switch_to.window(self._human_tab)
            except Exception:
                pass

    def _release_agent(self, agent_id):
        """Close the agent's tab and clean up. Must hold self.lock."""
        if agent_id not in self._agents:
            return
        agent = self._agents.pop(agent_id)
        try:
            self.driver.switch_to.window(agent["handle"])
            self.driver.close()
        except Exception:
            pass
        self._restore_human_focus()

    def _inject_agent_bar(self, agent_id):
        """Inject a colored indicator bar at the top of the page content."""
        if agent_id not in self._agents:
            return
        color = self._agents[agent_id]["color"]
        color_name = self._agents[agent_id]["color_name"]
        js = (
            "(function(){"
            "var e=document.getElementById('browse-agent-bar');"
            "if(e)e.remove();"
            "var b=document.createElement('div');"
            "b.id='browse-agent-bar';"
            "b.style.cssText='position:fixed;top:0;left:0;right:0;"
            "height:3px;background:" + color + ";"
            "z-index:2147483647;box-shadow:0 0 10px " + color + ";"
            "pointer-events:none;';"
            "b.setAttribute('data-agent','" + color_name + "');"
            "if(document.body)document.body.prepend(b);"
            "})();"
        )
        try:
            self.driver.execute_script(js)
        except Exception:
            pass

    # Commands after which we re-inject the agent's colored page bar.
    _NAV_COMMANDS = {"navigate", "back", "forward", "refresh"}

    def _handle_client(self, conn, addr):
        """Handle one client connection. Opens a dedicated tab for the agent."""
        with self.lock:
            agent_id = self._assign_agent()
            self._update_indicator()
        try:
            with conn:
                buf = b""
                while self._running:
                    try:
                        data = conn.recv(65536)
                        if not data:
                            break
                        buf += data
                        # Process complete lines
                        while b"\n" in buf:
                            line, buf = buf.split(b"\n", 1)
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                cmd = json.loads(line)
                            except json.JSONDecodeError as e:
                                resp = {"ok": False, "error": f"Bad JSON: {e}"}
                                conn.sendall(json.dumps(resp).encode() + b"\n")
                                continue

                            with self.lock:
                                try:
                                    # Switch to this agent's tab
                                    if agent_id in self._agents:
                                        self.driver.switch_to.window(
                                            self._agents[agent_id]["handle"])
                                    result = self.handle_command(cmd, agent_id=agent_id)
                                    # Re-inject colored bar after navigation
                                    if cmd.get("cmd") in self._NAV_COMMANDS:
                                        self._inject_agent_bar(agent_id)
                                    resp = {"ok": True, "result": result}
                                except Exception as e:
                                    resp = {"ok": False, "error": str(e)}
                                finally:
                                    # Snap visual focus back to human tab
                                    self._restore_human_focus()

                            conn.sendall(json.dumps(resp).encode() + b"\n")
                    except (ConnectionResetError, BrokenPipeError):
                        break
        finally:
            with self.lock:
                self._release_agent(agent_id)
                self._update_indicator()

    def serve(self):
        """Start the command server. Blocks until shutdown."""
        self._running = True
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", self.port))
        sock.listen(5)
        sock.settimeout(1.0)

        print(f"  Command server listening on 127.0.0.1:{self.port}")

        while self._running:
            try:
                conn, addr = sock.accept()
                t = threading.Thread(target=self._handle_client,
                                     args=(conn, addr), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except OSError:
                break

        sock.close()

    def shutdown(self):
        self._running = False

    def start_status_server(self):
        """Start a tiny HTTP server returning agent status as JSON."""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        session_server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                agent_list = []
                for aid, info in session_server._agents.items():
                    agent_list.append({
                        "id": aid,
                        "color": info["color"],
                        "color_name": info["color_name"],
                    })
                self.wfile.write(json.dumps({
                    "agents": len(session_server._agents),
                    "agent_list": agent_list,
                }).encode())

            def log_message(self, *args):
                pass  # suppress request logs

        httpd = HTTPServer(("127.0.0.1", self.port + 1), Handler)
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        return httpd


# ─── Client ──────────────────────────────────────────────────────────────
# Connects to a running SessionServer over TCP.

class SessionClient:
    """Client that sends commands to a running session server."""

    def __init__(self, host="127.0.0.1", port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self._buf = b""

    def send(self, cmd):
        """Send a command dict and return the result."""
        payload = json.dumps(cmd).encode() + b"\n"
        self.sock.sendall(payload)

        # Read response
        while b"\n" not in self._buf:
            data = self.sock.recv(1048576)  # 1MB chunks for screenshots
            if not data:
                raise ConnectionError("Session server closed connection")
            self._buf += data

        line, self._buf = self._buf.split(b"\n", 1)
        resp = json.loads(line)
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", "Unknown error"))
        return resp.get("result")

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


# ─── Session Info ─────────────────────────────────────────────────────────

def get_session_info():
    """Read saved session info, or None if no session is running."""
    if not os.path.exists(SESSION_FILE):
        return None
    with open(SESSION_FILE) as f:
        info = json.load(f)
    # Check if process is still alive
    try:
        os.kill(info["pid"], 0)
    except (OSError, ProcessLookupError):
        os.remove(SESSION_FILE)
        return None
    return info


def connect_to_session():
    """Connect to a running session. Returns a SessionClient."""
    info = get_session_info()
    if info is None:
        raise ConnectionError(
            "No running session found. Start one with: python -m browse.session"
        )
    client = SessionClient(port=info["port"])
    # Verify connection
    client.send({"cmd": "ping"})
    return client


# ─── Launch ───────────────────────────────────────────────────────────────

def launch_session(tbb_path=None, geckodriver_path=None,
                   headless=False, profile_path=None):
    """Launch the browser and return the Selenium driver."""
    conf = _read_conf()
    tbb_path = tbb_path or conf.get("TBB_PATH") or os.environ.get("TBB_PATH")
    geckodriver_path = (geckodriver_path or conf.get("GECKODRIVER_PATH")
                        or os.environ.get("GECKODRIVER_PATH"))

    if not tbb_path:
        raise ValueError("TBB_PATH not found. Run setup.sh first.")

    # Layer 1a: Binary patch libxul.so to remove navigator.webdriver
    if not is_patched(tbb_path):
        print("  Applying stealth patch to libxul.so...")
        patch_libxul(tbb_path)
        print("  Patched — navigator.webdriver will be undefined.")

    # Layer 1b: Patch omni.ja to replace automation indicator with agent glow
    if not is_omni_patched(tbb_path):
        print("  Patching omni.ja — replacing automation indicator...")
        patch_omni(tbb_path)
        print("  Patched — address bar will glow green when agents connect.")

    _setup_env(tbb_path)

    fx_binary = os.path.join(tbb_path, cm.DEFAULT_TBB_FX_BINARY_PATH)
    default_profile = profile_path or os.path.join(
        tbb_path, cm.DEFAULT_TBB_PROFILE_PATH)

    options = Options()
    options.binary = fx_binary
    options.add_argument('--class')
    options.add_argument('"Tor Browser"')
    options.add_argument('-remote-allow-system-access')
    if headless:
        options.add_argument('-headless')

    pre_prefs = {
        'network.proxy.type': 0,
        'network.proxy.socks': '',
        'network.proxy.socks_port': 0,
        'network.proxy.socks_remote_dns': False,
        'network.dns.disabled': False,
        'extensions.torlauncher.start_tor': False,
        'extensions.torlauncher.prompt_at_startup': False,
        'extensions.torlauncher.quickstart': False,
        'privacy.resistFingerprinting': True,
        'privacy.resistFingerprinting.letterboxing': True,
        'javascript.enabled': True,
        'media.peerconnection.enabled': False,
        'browser.startup.page': 1,
        'browser.startup.homepage': 'file://' + os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'startpage.html'),
        'app.update.enabled': False,
        'extensions.torbutton.versioncheck_enabled': False,
        'extensions.torbutton.prompted_language': True,
        'intl.language_notification.shown': True,
        'torbrowser.settings.quickstart.enabled': True,
        'xpinstall.signatures.required': False,
        'xpinstall.whitelist.required': False,
        'toolkit.legacyUserProfileCustomizations.stylesheets': True,
        'browse.agent.connected': False,
        'browser.chrome.disableRemoteControlCueForTests': True,
    }
    for k, v in pre_prefs.items():
        options.set_preference(k, v)

    if profile_path:
        options.add_argument("-profile")
        options.add_argument(profile_path)
    else:
        options.profile = default_profile

    service = Service(executable_path=geckodriver_path)
    driver = webdriver.Firefox(service=service, options=options)
    time.sleep(1)

    _apply_direct_prefs(driver)

    # Layer 2: Install stealth WebExtension (defense-in-depth)
    try:
        xpi_path = build_stealth_extension()
        driver.install_addon(xpi_path, temporary=True)
    except Exception as e:
        print(f"  Warning: stealth extension failed to install: {e}")

    return driver


def main():
    """CLI entry point — launch a persistent session."""
    import argparse
    parser = argparse.ArgumentParser(
        description="Launch a persistent agent browser session"
    )
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Command server port (default: {DEFAULT_PORT})")
    parser.add_argument("--tbb-path", help="Path to Tor Browser Bundle")
    parser.add_argument("--profile", help="Path to a persistent profile dir")
    args = parser.parse_args()

    existing = get_session_info()
    if existing:
        print(f"Session already running (pid {existing['pid']}, port {existing['port']}).")
        sys.exit(1)

    print("Launching persistent browser session...")
    driver = launch_session(
        tbb_path=args.tbb_path,
        headless=args.headless,
        profile_path=args.profile,
    )

    server = SessionServer(driver, port=args.port)

    # Start HTTP status endpoint for the indicator extension
    status_port = args.port + 1
    server.start_status_server()

    # Install the agent indicator extension
    try:
        from .stealth import build_indicator_extension
        xpi_path = build_indicator_extension(status_port)
        driver.install_addon(xpi_path, temporary=True)
        print(f"  Agent indicator active (status on port {status_port}).")
    except Exception as e:
        print(f"  Warning: indicator extension failed to install: {e}")

    session_info = {
        "port": args.port,
        "pid": os.getpid(),
    }
    with open(SESSION_FILE, "w") as f:
        json.dump(session_info, f, indent=2)

    print(f"  Browser is running (your tab is private).")
    print(f"  Command server on 127.0.0.1:{args.port}")
    print(f"  Each agent gets its own color-coded tab.")
    print()
    print("  Connect with:  AgentBrowser.connect()")
    print("  Shut down with: Ctrl+C")
    print()

    def shutdown(sig, frame):
        print("\nShutting down...")
        server.shutdown()
        try:
            driver.quit()
        except Exception:
            pass
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Watchdog: detect when the browser window is closed by the user
    def _watch_browser():
        while True:
            time.sleep(2)
            try:
                # window_handles doesn't switch tabs — safe for multi-tab
                handles = driver.window_handles
                if server._human_tab not in handles:
                    raise Exception("Human tab closed")
            except Exception:
                print("\nBrowser closed. Shutting down...")
                server.shutdown()
                if os.path.exists(SESSION_FILE):
                    os.remove(SESSION_FILE)
                os._exit(0)

    watcher = threading.Thread(target=_watch_browser, daemon=True)
    watcher.start()

    # Run command server (blocks)
    try:
        server.serve()
    finally:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)


if __name__ == "__main__":
    main()
