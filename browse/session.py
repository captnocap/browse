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
        self._last_url = None
        self._agent_navigating = False

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
        """Poll for human-initiated URL changes in a daemon thread."""
        while self._running:
            time.sleep(1.5)
            try:
                url = self.driver.current_url
            except Exception:
                continue
            if url == self._last_url:
                continue
            if self._agent_navigating:
                self._last_url = url
                continue
            if url.startswith("about:") or url.startswith("file://"):
                self._last_url = url
                continue
            try:
                title = self.driver.title
            except Exception:
                title = ""
            self._last_url = url
            self._append_history("human", url, title)

    def handle_command(self, cmd):
        """Execute a command on the browser. Returns a JSON-serializable result."""
        action = cmd.get("cmd")

        if action == "navigate":
            self._agent_navigating = True
            try:
                self.driver.set_page_load_timeout(cmd.get("timeout", 30))
                self.driver.get(cmd["url"])
                challenge = self.detect_challenge()
                if challenge:
                    self._last_url = self.driver.current_url
                    return {"challenge": challenge, "url": self.driver.current_url}
                content = self._wait_for_stable_content()
                self._append_history("agent", content.url, content.title)
                self._last_url = self.driver.current_url
                return self._content_to_dict(content)
            finally:
                self._agent_navigating = False

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
            self._agent_navigating = True
            try:
                self.driver.back()
                time.sleep(0.3)
                url = self.driver.current_url
                title = self.driver.title
                if not url.startswith("about:") and not url.startswith("file://"):
                    self._append_history("agent", url, title)
                self._last_url = url
                return True
            finally:
                self._agent_navigating = False

        elif action == "forward":
            self._agent_navigating = True
            try:
                self.driver.forward()
                time.sleep(0.3)
                url = self.driver.current_url
                title = self.driver.title
                if not url.startswith("about:") and not url.startswith("file://"):
                    self._append_history("agent", url, title)
                self._last_url = url
                return True
            finally:
                self._agent_navigating = False

        elif action == "refresh":
            self.driver.refresh()
            return True

        elif action == "ping":
            return "pong"

        else:
            raise ValueError(f"Unknown command: {action}")

    @property
    def client_count(self):
        return self._client_count

    def _update_indicator(self):
        """Toggle the browseagent attribute on the browser chrome root element."""
        connected = self._client_count > 0
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

    def _handle_client(self, conn, addr):
        """Handle one client connection. Reads JSON lines, sends responses."""
        self._client_count += 1
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
        """Start a tiny HTTP server for the indicator extension to poll."""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        session_server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "agents": session_server.client_count,
                    "history": session_server._history,
                }).encode())

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
    args = parser.parse_args()

    existing = get_session_info()
    if existing:
        print(f"Session already running (pid {existing['pid']}, port {existing['port']}).")
        sys.exit(1)

    startpage = os.path.join(os.path.dirname(os.path.abspath(__file__)), "startpage.html")
    homepage_url = f"file://{startpage}"

    print("Launching persistent browser session...")
    driver = launch_session(
        firefox_path=args.firefox_path,
        headless=args.headless,
        profile_path=args.profile,
        homepage=homepage_url,
    )

    server = SessionServer(driver, port=args.port)

    status_port = args.port + 1
    server.start_status_server()

    server._running = True
    url_watcher = threading.Thread(target=server._watch_url, daemon=True)
    url_watcher.start()

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
