# browse

AI agent browser with native anti-fingerprinting. Uses Tor Browser's engine for its C++-level fingerprint resistance (canvas, WebGL, fonts, screen letterboxing, timer clamping) without routing traffic through the Tor network.

This gives you a browser that looks like a real human's browser to every bot detection system on the internet, controllable from Python.

```bash
git clone https://github.com/captnocap/browse.git && cd browse && ./setup.sh
```

That's it. Linux x86_64, Python 3.10+. Setup downloads Tor Browser, patches it, and configures your AI frontend. After setup, just ask your AI to browse — it launches the browser automatically. No servers to run, no config to edit.

For Python usage:

```python
from browse import AgentBrowser

with AgentBrowser() as browser:
    print(browser.navigate("https://example.com").text)
```

## Why this exists

Every browser automation stealth tool follows the same pattern: take Chrome, then inject JavaScript to override `navigator.webdriver`, spoof canvas, fake WebGL values, etc. The problem is that these JS overrides are detectable. Anti-bot systems check `Function.prototype.toString()`, inspect prototype chains, compare iframe values, and run timing attacks to find the patches.

Tor Browser solves this at the C++ level. Canvas noise, WebGL spoofing, font restriction, screen letterboxing, and timer clamping are all implemented natively in the browser engine. There's nothing to detect because there's no JavaScript override — the browser genuinely behaves differently at the lowest level.

`browse` takes Tor Browser, disables the Tor network routing (uses direct connection or your own proxy), and patches out the single remaining automation signal (`navigator.webdriver`) at the binary level. The result: a browser that passes every bot detection check while being fully controllable from Python.

## What it does

- **Native anti-fingerprinting** — canvas noise, WebGL spoofing, font restriction, letterboxing, timer clamping — all C++-level, no JS injection
- **Binary-patched `navigator.webdriver`** — the property doesn't exist (not overridden to `false`, genuinely `undefined`)
- **Prompt injection filtering** — extracts only visible page content, strips 15+ CSS hiding tricks used to inject hidden instructions for AI agents
- **Two operating modes** — quick mode (spawn, use, close) and session mode (persistent browser shared between human and AI)
- **Agent indicator** — address bar glows green when AI agents are connected, disappears when they disconnect (patched into browser chrome via `omni.ja`)
- **Cookie import** — import cookies from Firefox, Chrome, Chromium, or Brave so you're logged into your sites
- **Site blocklist** — prevent agents from navigating to specific domains, with a built-in typosquat/phishing preset
- **Challenge detection** — automatically detects CAPTCHAs/challenges and waits for human to solve them before resuming
- **Content stability detection** — waits for dynamically-rendered pages to finish loading before extracting content

## Quick start

> **Linux x86_64 only.** The binary patching targets `libxul.so` and the setup downloads Linux-specific builds. macOS/Windows support is not currently implemented.

### 1. Setup

```bash
git clone https://github.com/captnocap/browse.git
cd browse
./setup.sh
```

This downloads Tor Browser and geckodriver, installs the Python package, applies the stealth binary patch, and configures MCP for your AI frontend. Takes about a minute.

### 2. Quick mode — spawn, use, close

```python
from browse import AgentBrowser

with AgentBrowser() as browser:
    content = browser.navigate("https://example.com")
    print(content.title)
    print(content.text)
    print(content.links)
```

### 3. Session mode — persistent browser

Start the browser:

```bash
browse
```

Connect from Python (any number of times, any terminal):

```python
from browse import AgentBrowser

agent = AgentBrowser.connect()
content = agent.navigate("https://www.google.com")
print(content.text)
agent.detach()  # browser stays open
```

The browser stays open between connections. You can use it normally with mouse and keyboard while the AI is detached. When an agent connects, the address bar glows green so you always know when AI is active. The glow disappears when all agents disconnect.

### 4. Cookie import

Import cookies from your regular browser so you're already logged into your sites:

```bash
# Import from Firefox (all cookies)
browse cookies firefox

# Import only specific domains
browse cookies firefox github.com google.com

# Other browsers
browse cookies chrome
browse cookies brave
browse cookies /path/to/cookies.json
```

For large imports (200+ domains), you'll get a confirmation prompt since each domain requires a brief navigation.

### 5. Site blocklist

Block domains that agents cannot navigate to (you can still browse them manually):

```bash
# Block individual sites
browse block example.com

# Load the built-in malicious/typosquat preset (47 domains)
browse block --preset malicious

# Manage
browse unblock example.com
browse blocklist
```

Subdomains are matched automatically — blocking `4chan.org` also blocks `boards.4chan.org`.

## API

### AgentBrowser

```python
# Quick mode
browser = AgentBrowser(tbb_path=None, proxy=None, headless=False, profile_path=None)

# Session mode
agent = AgentBrowser.connect()
```

| Method | Description |
|---|---|
| `navigate(url)` | Navigate to URL, returns `PageContent` |
| `click(selector)` | Click an element (CSS selector) |
| `type_text(selector, text)` | Type into an input field |
| `extract_content()` | Extract structured content from current page |
| `extract_links()` | Extract all visible links |
| `screenshot(path=None)` | Take screenshot, returns PNG bytes |
| `execute_js(script)` | Execute JavaScript in page context |
| `wait_for(selector, timeout=30)` | Wait for element to appear |
| `back()` / `forward()` / `refresh()` | Navigation |
| `current_url` | Current page URL |
| `page_source` | Current page HTML |
| `detach()` | Disconnect without closing browser (session mode) |
| `quit()` | Close browser (quick mode) |

### PageContent

```python
content = browser.navigate("https://example.com")

content.url        # "https://example.com"
content.title      # "Example Domain"
content.text       # visible text only (hidden content stripped)
content.links      # [Link(text="More info", href="https://..."), ...]
content.forms      # [Form(action="/search", method="get", fields=[...])]
content.meta       # {"description": "...", "og:title": "..."}

# Format for LLM consumption with untrusted-data boundaries
content.for_llm()
```

### Proxy support

```python
# SOCKS5
browser = AgentBrowser(proxy="socks5://127.0.0.1:1080")

# HTTP
browser = AgentBrowser(proxy="http://127.0.0.1:8080")

# No proxy (direct connection, default)
browser = AgentBrowser()
```

## How the stealth works

### Layer 1: Tor Browser's native anti-fingerprinting

Tor Browser is a hardened Firefox fork. Its anti-fingerprinting is implemented in C++ in the browser engine itself:

| Signal | What Tor Browser does |
|---|---|
| Canvas | Adds per-origin noise to canvas readback via `privacy.resistFingerprinting` |
| WebGL | Spoofs vendor/renderer to "Mozilla" |
| Fonts | Restricts to a standard set, blocks enumeration |
| Screen size | Rounds viewport to 200x100 increments (letterboxing) |
| Timers | Clamps `performance.now()` and `Date.now()` precision |
| WebRTC | Disabled (no IP leak) |
| User-Agent | Standardized across all Tor Browser users |

None of this is JavaScript injection. It's native behavior that cannot be detected by page scripts.

### Layer 2: Binary patch (`navigator.webdriver`)

Selenium sets `navigator.webdriver = true` via Firefox's C++ engine. There is no preference to disable it — Mozilla removed `dom.webdriver.enabled` and hardcoded the behavior.

We patch `libxul.so` (Firefox's core library) to replace the `"webdriver"` string with random bytes. This makes the property genuinely not exist:

```javascript
navigator.webdriver  // undefined (not false, not overridden — undefined)
```

This is the same approach used by [undetected_geckodriver](https://github.com/AShujjah/undetected_geckodriver). The patch is applied automatically on first run.

### Layer 3: Automation indicator patch (`omni.ja`)

Firefox shows a red candy-stripe bar when the browser is under Marionette control. We patch `omni.ja` (the browser's internal chrome archive) to replace this with an agent-aware indicator: the address bar glows green when agents are connected, and returns to normal when they disconnect. The session server toggles a `browseagent` attribute on the browser chrome root element, and the patched CSS responds to it.

### Layer 4: Stealth WebExtension

A minimal WebExtension injected at `document_start` in the MAIN world provides defense-in-depth. It handles edge cases with a prototype-level Proxy override that survives `toString()` inspection. This layer is rarely needed since the binary patch handles the property, but it catches any secondary code paths.

### Layer 5: Prompt injection filtering

When extracting page content for AI consumption, we walk the DOM and check every element's computed style. If an element is hidden by any CSS trick, its entire subtree is skipped:

| Hiding trick | Detection method |
|---|---|
| `display: none` | `getComputedStyle` |
| `visibility: hidden` | `getComputedStyle` |
| `opacity: 0` | `getComputedStyle` |
| `font-size: 0` | `getComputedStyle` |
| Same fg/bg color | Color comparison |
| Off-screen positioning | `getBoundingClientRect` |
| `clip-path: inset(100%)` | `getComputedStyle` |
| `clip: rect(0,0,0,0)` | Regex on computed clip |
| `text-indent: -9999px` | `getComputedStyle` |
| `overflow: hidden` + zero size | Combined check |
| `transform: scale(0)` | Regex on computed matrix |
| `filter: opacity(0)` | Regex on filter |
| `aria-hidden="true"` | Attribute check |
| HTML `hidden` attribute | Property check |
| Hidden child in hidden parent | Subtree skipping |

Additionally:
- Meta tags are allowlisted (only `description`, `og:title`, etc.)
- Hidden form input values are stripped
- Links and forms are also visibility-filtered
- `PageContent.for_llm()` wraps output in `UNTRUSTED WEB CONTENT` delimiters

## Challenge detection

When a CAPTCHA or challenge page is detected (Google `/sorry/`, Cloudflare, etc.), the agent prints a message and waits for the human to solve it:

```
[browse] Google CAPTCHA detected — waiting for you to solve it...
[browse] Challenge cleared. Resuming.
```

The AI monitors the URL and page content. Once the challenge clears and the destination page stabilizes, it automatically resumes extraction.

## Project structure

```
browse/
├── setup.sh                    # One-command setup
├── pyproject.toml              # Package config
├── browse.conf                 # Auto-generated paths, blocklist (gitignored)
├── browse/
│   ├── __init__.py             # Public API exports
│   ├── __main__.py             # python -m browse.session entry point
│   ├── cli.py                  # CLI dispatcher (browse, block, cookies, etc.)
│   ├── agent.py                # AgentBrowser — main API class
│   ├── content.py              # Page extraction + prompt injection filtering
│   ├── cookies.py              # Cookie import (Firefox, Chrome, Brave, JSON)
│   ├── mcp_server.py           # MCP server for AI frontends
│   ├── session.py              # Persistent browser session (TCP server/client)
│   ├── stealth.py              # Binary patcher, omni.ja patcher, extensions
│   └── tbselenium/             # Vendored + modified tor-browser-selenium
│       ├── common.py           # + USE_DIRECT mode constant
│       ├── tbdriver.py         # + Direct connection support
│       ├── tbbinary.py         # Selenium 4 compatibility stub
│       ├── utils.py            # Preference setting utilities
│       └── exceptions.py       # Exception classes
├── test_botcheck.html          # Bot detection test page
├── test_injection.html         # Prompt injection test page (18 CSS tricks)
└── test_injection.py           # Automated injection test runner
```

## Requirements

- **Linux x86_64** (binary patching and setup target Linux only — macOS/Windows not yet supported)
- **Python 3.10+**
- **selenium >= 4**

`setup.sh` handles downloading Tor Browser and geckodriver automatically.

## How it compares

| Approach | Fingerprint resistance | Detectable? |
|---|---|---|
| Raw Selenium + Chrome | None | Instantly detected |
| undetected-chromedriver | JS overrides for ~10 signals | Detected by sophisticated systems |
| Playwright stealth | JS overrides | Detected by Cloudflare, DataDome |
| **browse** | Native C++ anti-fingerprinting + binary patch | Passes all known checks |

The fundamental difference: every other tool tries to make Chrome *look like* a normal browser via JavaScript. `browse` uses a browser that *is* a normal browser (Tor Browser) — it just removes the automation flag at the binary level.

## MCP server

For AI frontends that support [Model Context Protocol](https://modelcontextprotocol.io/) (Claude Desktop, LM Studio, etc.), browse ships an MCP server that exposes the browser as tools.

### Setup

```bash
# Install with MCP support
pip install -e ".[mcp]"
```

### Claude Desktop / LM Studio config

```json
{
  "mcpServers": {
    "browse": {
      "command": "browse-mcp"
    }
  }
}
```

That's it. The AI can now browse the web. No separate server to run.

### How it works

The MCP server supports two modes that the AI agent picks based on context:

**Quick mode** — the agent launches its own browser, does the work, closes it. Supports multiple browsers in parallel for fetching data from several sites at once.

**Session mode** — if you already have a browser open (`browse`), the agent automatically connects to it. When it disconnects, your browser stays open.

### Available tools

| Tool | What it does |
|---|---|
| `browse_status` | Check for active browsers and existing sessions |
| `browse_open` | Launch a new browser (optionally navigate to URL) |
| `browse_connect` | Join an existing human browser session |
| `browse_navigate` | Go to a URL in a browser |
| `browse_search` | Search Google/DuckDuckGo (auto-opens browser if needed) |
| `browse_click` | Click an element on the page |
| `browse_type` | Type into an input field, optionally submit |
| `browse_extract` | Re-extract current page content |
| `browse_screenshot` | Take a screenshot (returns image) |
| `browse_back` / `browse_forward` | Navigate history |
| `browse_close` | Close browser (quick) or disconnect (session) |

All tools take an optional `browser_id` for parallel browsing. Each result includes the page content (with prompt injection filtering) plus a menu of suggested next actions, so the agent picks from options rather than burning GPU cycles reasoning about what to do next.

## Credits

- [Tor Browser](https://www.torproject.org/) — the anti-fingerprinting engine
- [tor-browser-selenium](https://github.com/webfp/tor-browser-selenium) — vendored and modified (MIT license)
- [undetected_geckodriver](https://github.com/AShujjah/undetected_geckodriver) — binary patching approach

## License

MIT. See [LICENSE](LICENSE).
