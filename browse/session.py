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

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .firefox import launch_firefox
from .content import extract_page_content

SESSION_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".browse_session.json"
)

DEFAULT_PORT = 7331


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
        self._client_count = 0
        self._history = []
        self._last_watched_url = None
        self._last_agent_url = None
        self._last_command_time = 0
        self._agent_bar_tabs = {}  # {tab_index: timestamp} — [4] in visual indicator flow (see stealth.py)

    CHALLENGE_URL_PATTERNS = [
        ("/sorry/", "google_captcha"),
        ("google.com/sorry", "google_captcha"),
        ("/cdn-cgi/challenge", "cloudflare"),
        ("captcha", "captcha"),
    ]

    def detect_challenge(self):
        """Check if the current URL is a known challenge/intercept page."""
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
        """Wait for the page to stop loading by watching link count stabilize."""
        deadline = time.time() + max_wait

        while time.time() < deadline:
            count = self._link_count()
            if count > 0:
                break
            time.sleep(0.3)

        while time.time() < deadline:
            first_count = self._link_count()
            time.sleep(0.5)
            second_count = self._link_count()
            if second_count == first_count:
                break

        return extract_page_content(self.driver)

    def wait_for_challenge_clear(self, challenge_url, poll_interval=1.0, timeout=120):
        """Poll until the URL changes away from the challenge page."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                current = self.driver.current_url
                if current != challenge_url and self.detect_challenge() is None:
                    content = self._wait_for_stable_content()
                    return {
                        "cleared": True,
                        **self._content_to_dict(content),
                    }
            except Exception:
                pass
            time.sleep(poll_interval)
        return {"cleared": False, "reason": "timeout"}

    @staticmethod
    def _content_to_dict(content):
        """Convert PageContent to a JSON-serializable dict."""
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

    def _append_history(self, source, url, title):
        """Append a history entry, capped at 200."""
        entry = {
            "source": source,
            "url": url,
            "title": title or "",
            "ts": time.strftime("%H:%M:%S"),
        }
        self._history.append(entry)
        if len(self._history) > 200:
            self._history = self._history[-200:]

    def _watch_url(self):
        """Poll for human-initiated URL changes in a daemon thread.

        Uses chrome context to read the user's actual visual tab,
        independent of where Selenium's context is pointed.
        """
        while self._running:
            time.sleep(1.5)
            if not self.lock.acquire(timeout=0.1):
                continue
            try:
                with self.driver.context(self.driver.CONTEXT_CHROME):
                    info = self.driver.execute_script('''
                        let tab = gBrowser.selectedTab;
                        let browser = gBrowser.getBrowserForTab(tab);
                        return {url: browser.currentURI.spec, title: tab.label};
                    ''')
                url = info['url']
                title = info['title']
            except Exception:
                continue
            finally:
                self.lock.release()
            if url == self._last_watched_url:
                continue
            self._last_watched_url = url
            if url.startswith("about:") or url.startswith("file://"):
                continue
            if url == self._last_agent_url:
                self._last_agent_url = None
                continue
            self._append_history("human", url, title)

    def _signal_activity(self):
        """Set the URL bar glow with a 30s auto-clear timeout."""
        try:
            with self.driver.context(self.driver.CONTEXT_CHROME):
                self.driver.execute_script('''
                    if (window._browseAgentTimer) clearTimeout(window._browseAgentTimer);
                    document.documentElement.setAttribute("browseagent", "true");
                    window._browseAgentTimer = setTimeout(() => {
                        document.documentElement.removeAttribute("browseagent");
                    }, 30000);
                ''')
        except Exception:
            pass

    def _mark_agent_tab(self):
        """[4] Record the current Selenium-targeted tab for the extension to highlight.
        Called from use_tab(). The extension polls bar_tabs via [5] and injects the bar via [6].
        Also stamps the XUL tab element with browse-agent attribute for [10] tab strip styling.
        See stealth.py for the full visual indicator flow."""
        try:
            handles = self.driver.window_handles
            idx = handles.index(self.driver.current_window_handle)
            self._agent_bar_tabs[idx] = time.time()
            self._pulse_agent_tab(idx)
        except Exception:
            pass

    def _pulse_agent_tab(self, idx):
        """[10] Set browse-agent="active" on a tab with 5s auto-downgrade to "true".
        "active" = agent is live on this tab (pulsing CSS).
        "true" = agent touched this tab but is idle (static pink CSS)."""
        try:
            with self.driver.context(self.driver.CONTEXT_CHROME):
                self.driver.execute_script('''
                    let tab = gBrowser.tabs[arguments[0]];
                    if (!tab) return;
                    tab.setAttribute("browse-agent", "active");
                    // Clear any existing downgrade timer
                    if (tab._browseAgentTimer) clearTimeout(tab._browseAgentTimer);
                    tab._browseAgentTimer = setTimeout(() => {
                        if (tab.getAttribute("browse-agent") === "active")
                            tab.setAttribute("browse-agent", "true");
                    }, 5000);
                ''', idx)
        except Exception:
            pass

    def handle_command(self, cmd):
        """Execute a command on the browser. Returns a JSON-serializable result."""
        action = cmd.get("cmd")
        self._last_command_time = time.time()

        # [10] Pulse the active tab on any command that touches page content
        _TAB_COMMANDS = {"navigate", "click", "type_text", "back", "forward",
                         "refresh", "extract_content", "execute_js", "screenshot"}
        if action in _TAB_COMMANDS:
            try:
                handles = self.driver.window_handles
                idx = handles.index(self.driver.current_window_handle)
                if idx in self._agent_bar_tabs:
                    self._pulse_agent_tab(idx)
            except Exception:
                pass
            # Ensure we're back in content context after chrome calls
            self.driver.set_context(self.driver.CONTEXT_CONTENT)

        if action == "navigate":
            self.driver.set_page_load_timeout(cmd.get("timeout", 30))
            self.driver.get(cmd["url"])
            challenge = self.detect_challenge()
            if challenge:
                return {"challenge": challenge, "url": self.driver.current_url}
            content = self._wait_for_stable_content()
            self._append_history("agent", content.url, content.title)
            self._last_agent_url = content.url
            return self._content_to_dict(content)

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
            return self._content_to_dict(content)

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
            time.sleep(0.3)
            url = self.driver.current_url
            title = self.driver.title
            if not url.startswith("about:") and not url.startswith("file://"):
                self._append_history("agent", url, title)
                self._last_agent_url = url
            return True

        elif action == "forward":
            self.driver.forward()
            time.sleep(0.3)
            url = self.driver.current_url
            title = self.driver.title
            if not url.startswith("about:") and not url.startswith("file://"):
                self._append_history("agent", url, title)
                self._last_agent_url = url
            return True

        elif action == "refresh":
            self.driver.refresh()
            return True

        elif action == "list_tabs":
            with self.driver.context(self.driver.CONTEXT_CHROME):
                tabs = self.driver.execute_script('''
                    let result = [];
                    let activeTab = gBrowser.selectedTab;
                    for (let i = 0; i < gBrowser.tabs.length; i++) {
                        let tab = gBrowser.tabs[i];
                        let browser = gBrowser.getBrowserForTab(tab);
                        result.push({
                            index: i,
                            url: browser.currentURI.spec,
                            title: tab.label,
                            active: tab === activeTab
                        });
                    }
                    return result;
                ''')
            return {"tabs": tabs}

        elif action == "use_tab":
            index = cmd["index"]
            handles = self.driver.window_handles
            if index >= len(handles):
                raise ValueError(
                    f"Tab index {index} out of range ({len(handles)} tabs open)")
            # Save user's current visual tab
            with self.driver.context(self.driver.CONTEXT_CHROME):
                user_idx = self.driver.execute_script(
                    'return Array.from(gBrowser.tabs).indexOf(gBrowser.selectedTab);'
                )
            # Point Selenium at the target tab
            self.driver.switch_to.window(handles[index])
            # Restore user's visual tab (no hop)
            with self.driver.context(self.driver.CONTEXT_CHROME):
                self.driver.execute_script(
                    'gBrowser.selectedTab = gBrowser.tabs[arguments[0]];',
                    user_idx,
                )
            # Inject agent bar on the targeted tab
            self._mark_agent_tab()
            # Return info about it
            with self.driver.context(self.driver.CONTEXT_CHROME):
                info = self.driver.execute_script('''
                    let tab = gBrowser.tabs[arguments[0]];
                    let browser = gBrowser.getBrowserForTab(tab);
                    return {index: arguments[0],
                            url: browser.currentURI.spec,
                            title: tab.label};
                ''', index)
            return info

        elif action == "open_tab":
            url = cmd.get("url", "about:blank")
            with self.driver.context(self.driver.CONTEXT_CHROME):
                self.driver.execute_script(
                    'gBrowser.addTab(arguments[0], {inBackground: true,'
                    ' triggeringPrincipal:'
                    ' Services.scriptSecurityManager.getSystemPrincipal()});',
                    url,
                )
            # Mark the new tab (last one) as agent-touched
            try:
                new_idx = len(self.driver.window_handles) - 1
                self._agent_bar_tabs[new_idx] = time.time()
                self._pulse_agent_tab(new_idx)
            except Exception:
                pass
            # Return updated tab list
            return self.handle_command({"cmd": "list_tabs"})

        elif action == "ping":
            return "pong"

        else:
            raise ValueError(f"Unknown command: {action}")

    @property
    def client_count(self):
        return self._client_count

    def _handle_client(self, conn, addr):
        """Handle one client connection. Reads JSON lines, sends responses."""
        self._client_count += 1
        try:
            with conn:
                buf = b""
                while self._running:
                    try:
                        data = conn.recv(65536)
                        if not data:
                            break
                        buf += data
                        while b"\n" in buf:
                            line, buf = buf.split(b"\n", 1)
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                cmd = json.loads(line)
                            except json.JSONDecodeError as e:
                                resp = {"ok": False, "error": f"Bad JSON: {e}"}
                                conn.sendall(
                                    json.dumps(resp).encode() + b"\n")
                                continue

                            with self.lock:
                                try:
                                    result = self.handle_command(cmd)
                                    resp = {"ok": True, "result": result}
                                except Exception as e:
                                    resp = {"ok": False, "error": str(e)}

                            conn.sendall(json.dumps(resp).encode() + b"\n")
                    except (ConnectionResetError, BrokenPipeError):
                        break
        finally:
            self._client_count -= 1

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
        """Start a tiny HTTP server for the indicator extension to poll."""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        session_server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                try:
                    tab_count = len(session_server.driver.window_handles)
                except Exception:
                    tab_count = 0
                active = (time.time() - session_server._last_command_time) < 30
                now = time.time()
                # [5] Serve bar_tabs for the indicator extension to poll (see stealth.py flow).
                # Clean up entries older than 10 min, and clear [10] tab attributes.
                stale = [i for i, ts in session_server._agent_bar_tabs.items()
                         if now - ts >= 600]
                for idx in stale:
                    del session_server._agent_bar_tabs[idx]
                    try:
                        with session_server.driver.context(session_server.driver.CONTEXT_CHROME):
                            session_server.driver.execute_script('''
                                let tab = gBrowser.tabs[arguments[0]];
                                if (tab) tab.removeAttribute("browse-agent");
                            ''', idx)
                    except Exception:
                        pass
                bar_tabs = {str(i): ts for i, ts in
                            session_server._agent_bar_tabs.items()}
                self.wfile.write(json.dumps({
                    "agents": session_server.client_count,
                    "active": active,
                    "history": session_server._history,
                    "tab_count": tab_count,
                    "bar_tabs": bar_tabs,
                }).encode())

            def do_POST(self):
                """Handle tab dismissal from the indicator extension."""
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    body = json.loads(self.rfile.read(length))
                    tab_idx = body.get("dismiss_tab")
                    if tab_idx is not None:
                        tab_idx = int(tab_idx)
                        session_server._agent_bar_tabs.pop(tab_idx, None)
                        try:
                            with session_server.driver.context(session_server.driver.CONTEXT_CHROME):
                                session_server.driver.execute_script('''
                                    let tab = gBrowser.tabs[arguments[0]];
                                    if (tab) tab.removeAttribute("browse-agent");
                                ''', tab_idx)
                        except Exception:
                            pass
                except Exception:
                    pass
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok":true}')

            def do_OPTIONS(self):
                """CORS preflight for POST requests."""
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            def log_message(self, *args):
                pass

        httpd = HTTPServer(("127.0.0.1", self.port + 1), Handler)
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        return httpd


# ─── Client ──────────────────────────────────────────────────────────────

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

        while b"\n" not in self._buf:
            data = self.sock.recv(1048576)
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
    client.send({"cmd": "ping"})
    return client


# ─── Launch ───────────────────────────────────────────────────────────────

def launch_session(firefox_path=None, geckodriver_path=None,
                   headless=False, profile_path=None, homepage=None):
    """Launch the browser and return the Selenium driver."""
    return launch_firefox(
        firefox_path=firefox_path,
        geckodriver_path=geckodriver_path,
        headless=headless,
        profile_path=profile_path,
        homepage=homepage,
    )


def main():
    """CLI entry point — launch a persistent session."""
    import argparse
    parser = argparse.ArgumentParser(
        description="Launch a persistent agent browser session"
    )
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Command server port (default: {DEFAULT_PORT})")
    parser.add_argument("--firefox-path", help="Path to Firefox installation")
    parser.add_argument("--profile", help="Path to a persistent profile dir")
    parser.add_argument("--disposable", action="store_true",
                        help="Use a temporary profile (discarded on exit)")
    args = parser.parse_args()

    existing = get_session_info()
    if existing:
        print(f"Session already running (pid {existing['pid']}, port {existing['port']}).")
        sys.exit(1)

    # Resolve profile path
    if args.disposable:
        profile_path = None
    elif args.profile:
        profile_path = os.path.expanduser(args.profile)
        os.makedirs(profile_path, exist_ok=True)
    else:
        from .firefox import _read_conf
        conf = _read_conf()
        mode = conf.get("PROFILE_MODE", "persistent").lower()
        if mode == "disposable":
            profile_path = None
        else:
            profile_path = conf.get(
                "PROFILE_PATH",
                os.path.expanduser("~/.config/browse/profile"),
            )
            profile_path = os.path.expanduser(profile_path)
            os.makedirs(profile_path, exist_ok=True)

    if profile_path:
        print(f"  Profile: {profile_path}")
    else:
        print("  Profile: disposable (temporary)")

    startpage = os.path.join(os.path.dirname(os.path.abspath(__file__)), "startpage.html")
    homepage_url = f"file://{startpage}"

    print("Launching persistent browser session...")
    driver = launch_session(
        firefox_path=args.firefox_path,
        headless=args.headless,
        profile_path=profile_path,
        homepage=homepage_url,
    )

    server = SessionServer(driver, port=args.port)

    status_port = args.port + 1
    server.start_status_server()

    server._running = True
    url_watcher = threading.Thread(target=server._watch_url, daemon=True)
    url_watcher.start()

    # Install indicator extension — drives steps [6]-[9] of the visual indicator flow.
    # Polls the status endpoint [5] and manages the per-tab bar + theme system.
    # See stealth.py for the full numbered map.
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

    print(f"  Browser is running.")
    print(f"  Command server on 127.0.0.1:{args.port}")
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

    def _watch_browser():
        while True:
            time.sleep(2)
            try:
                driver.current_url
            except Exception:
                print("\nBrowser closed. Shutting down...")
                server.shutdown()
                if os.path.exists(SESSION_FILE):
                    os.remove(SESSION_FILE)
                os._exit(0)

    watcher = threading.Thread(target=_watch_browser, daemon=True)
    watcher.start()

    try:
        server.serve()
    finally:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)


if __name__ == "__main__":
    main()
