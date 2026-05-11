# browse

AI agent browser with native anti-fingerprinting. Uses Firefox ESR with `privacy.resistFingerprinting` (RFP) for C++-level fingerprint resistance — canvas noise, WebGL spoofing, font restriction, screen letterboxing, timer clamping — with an anonymity set of ~200M Firefox users.

This gives you a browser that looks like a real human's browser to every bot detection system on the internet, controllable from Python.

```bash
git clone https://github.com/captnocap/browse.git && cd browse && ./setup.sh
```

Linux x86_64, Python 3.10+. Setup downloads Firefox ESR, patches it, and configures your AI frontend. After setup, just ask your AI to browse — it launches the browser automatically.

For one-shot CLI fetches that just work — no captchas, no bot walls, real browser:

```bash
browse curl https://example.com                 # fetch a page
browse search "best espresso machines 2026"     # Google SERP
browse asearch "claude opus 4.7 release notes"  # multi-engine, ranked by overlap
```

For Python usage:

```python
from browse import AgentBrowser

with AgentBrowser() as browser:
    print(browser.navigate("https://example.com").text)
```

## Why this exists

Every browser automation stealth tool follows the same pattern: take Chrome, then inject JavaScript to override `navigator.webdriver`, spoof canvas, fake WebGL values, etc. The problem is that these JS overrides are detectable. Anti-bot systems check `Function.prototype.toString()`, inspect prototype chains, compare iframe values, and run timing attacks to find the patches.

Firefox with `privacy.resistFingerprinting` solves this at the C++ level. Canvas noise, WebGL spoofing, font restriction, screen letterboxing, and timer clamping are all implemented natively in the browser engine. There's nothing to detect because there's no JavaScript override — the browser genuinely behaves differently at the lowest level.

`browse` takes Firefox ESR, enables RFP hardening, and patches out the single remaining automation signal (`navigator.webdriver`) at the binary level. The result: a browser that passes every bot detection check while being fully controllable from Python.

## What it does

- **One-shot CLI fetch** — `browse curl`, `browse search`, `browse asearch` for curl-style scraping that doesn't trip bot walls, with cross-engine result ranking
- **Native anti-fingerprinting** — canvas noise, WebGL spoofing, font restriction, letterboxing, timer clamping — all C++-level via RFP, no JS injection
- **Binary-patched `navigator.webdriver`** — the property doesn't exist (not overridden to `false`, genuinely `undefined`)
- **Prompt injection filtering** — extracts only visible page content, strips 15+ CSS hiding tricks used to inject hidden instructions for AI agents
- **Two operating modes** — quick mode (spawn, use, close) and session mode (persistent browser shared between human and AI)
- **Per-tab agent indicator** — pink bar appears on tabs the AI has touched, persists until you interact with the tab. Browser theme shifts to match so the indicator survives page loads
- **Tab management** — agents can open, list, and switch between tabs without disrupting the human's browsing
- **Persistent profiles** — browser state (extensions, bookmarks, cookies) persists across sessions by default. Clone from your system Firefox or start fresh
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

This downloads Firefox ESR and geckodriver, installs the Python package, applies the stealth binary patch, and configures MCP for your AI frontend.

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

The browser stays open between connections. You can use it normally with mouse and keyboard while the AI is detached. When an agent is active on a tab, a pink indicator bar appears at the top of the page and the browser theme shifts to pink. When you interact with the tab (click, type, scroll), the indicator clears and the theme returns to normal.

### 4. Profile management

By default, browser state persists across sessions in `~/.config/browse/profile`.

```bash
# Clone your existing Firefox profile (isolated copy)
browse profile clone

# Point at your system Firefox profile directly (shared state)
browse profile use

# Start with a fresh profile
browse profile new

# Set default to disposable (temp profile every launch)
browse profile disposable
```

For a one-off disposable session:

```bash
browse --disposable
```

### 5. Cookie import

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

### 6. Site blocklist

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

## CLI fetch — curl, search, asearch

One-shot commands that drive the real stealth browser and print the result to stdout. If a session is running they attach to it (logged-in cookies come along); if not, they spawn a temporary browser with your persistent profile and tear it down after — so Google won't gate you for being a zero-history identity.

```bash
# Fetch a page — defaults to LLM-formatted text with link/form summaries
browse curl https://example.com

# Other output modes
browse curl https://example.com --text       # plain text only
browse curl https://example.com --json       # structured JSON
browse curl https://example.com --links      # tab-separated href<TAB>text
browse curl https://example.com --html       # raw page source
browse curl https://example.com -o page.txt  # save instead of printing

# Single-engine search (real SERP, real browser)
browse search "best espresso machines 2026"
browse search "site:reddit.com browse python" --engine ddg

# Multi-engine ranked search — scores each result by cross-engine overlap
browse asearch "claude opus 4.7 release notes" --top 10
```

`asearch` queries Google, DuckDuckGo, and Bing in turn, normalizes URLs (strips tracking params, www., trailing slashes, unwraps Bing's `/ck/a` redirects), then ranks by how many engines agree on each result:

```
[3/3] (b=2,d=3,g=1)  Introducing Claude Opus 4.7
        https://anthropic.com/news/claude-opus-4-7
[3/3] (b=1,d=2,g=4)  Release notes | Claude Help Center
        https://support.claude.com/en/articles/12138966-release-notes
[2/3] (b=4,d=4)      Some site Google didn't surface
        https://example.com/article
```

The `(b=2,d=3,g=1)` annotation shows the rank each engine assigned. Flags shared across `curl`/`search`/`asearch`: `--timeout N`, `--wait N` (post-load settle), `--quick` (force fresh browser instead of the running session), `--screenshot path`, `-o file`.

## API

### AgentBrowser

```python
# Quick mode
browser = AgentBrowser(headless=False, profile_path=None)

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
| `list_tabs()` | List all open tabs with titles and URLs |
| `open_tab(url=None)` | Open a new tab, optionally navigate |
| `use_tab(index)` | Switch to a tab by index |
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

### Layer 1: Firefox RFP anti-fingerprinting

Firefox's `privacy.resistFingerprinting` provides the same C++-level anti-fingerprinting as Tor Browser, with an anonymity set of ~200M Firefox users instead of ~2M Tor users:

| Signal | What RFP does |
|---|---|
| Canvas | Adds per-origin noise to canvas readback |
| WebGL | Spoofs vendor/renderer to "Mozilla" |
| Fonts | Restricts to a standard set, blocks enumeration |
| Screen size | Rounds viewport to 200x100 increments (letterboxing) |
| Timers | Clamps `performance.now()` and `Date.now()` precision |
| WebRTC | Disabled (no IP leak) |
| User-Agent | Standardized across all RFP-enabled Firefox users |

None of this is JavaScript injection. It's native behavior that cannot be detected by page scripts.

### Layer 2: Binary patch (`navigator.webdriver`)

Selenium sets `navigator.webdriver = true` via Firefox's C++ engine. There is no preference to disable it — Mozilla removed `dom.webdriver.enabled` and hardcoded the behavior.

We patch `libxul.so` (Firefox's core library) to replace the `"webdriver"` string with random bytes. This makes the property genuinely not exist:

```javascript
navigator.webdriver  // undefined (not false, not overridden — undefined)
```

### Layer 3: Stealth WebExtension

A minimal WebExtension injected at `document_start` in the MAIN world provides defense-in-depth. It handles edge cases with a prototype-level Proxy override that survives `toString()` inspection.

### Layer 4: Visual indicator system

A browser extension manages per-tab agent indicators:

- **Pink content bar** — injected into tabs the agent has touched via `browser.tabs.executeScript()`, persists until the user interacts (click, type, scroll)
- **Theme shifting** — browser theme swaps between blue (human) and pink (agent) based on which tab is active, so the indicator survives page loads and navigations
- **Automation candycane hidden** — the default Selenium red stripe is removed via `userChrome.css` (loaded before first paint) and runtime CSS injection

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

## Project structure

```
browse/
├── setup.sh                    # One-command setup
├── pyproject.toml              # Package config
├── browse.conf                 # Auto-generated paths, blocklist (gitignored)
├── browse/
│   ├── __init__.py             # Public API exports
│   ├── __main__.py             # python -m browse entry point
│   ├── cli.py                  # CLI dispatcher (browse, profile, block, cookies)
│   ├── agent.py                # AgentBrowser — main API class
│   ├── content.py              # Page extraction + prompt injection filtering
│   ├── cookies.py              # Cookie import (Firefox, Chrome, Brave, JSON)
│   ├── firefox.py              # Firefox ESR launcher with RFP hardening
│   ├── mcp_server.py           # MCP server for AI frontends
│   ├── session.py              # Persistent browser session (TCP server/client)
│   ├── stealth.py              # Binary patcher, extensions, theme system
│   ├── startpage.html          # Session dashboard (agent/human history)
│   └── scripts/                # Reusable automation scripts
├── test_botcheck.html          # Bot detection test page
├── test_injection.html         # Prompt injection test page (18 CSS tricks)
└── test_injection.py           # Automated injection test runner
```

## Requirements

- **Linux x86_64** (binary patching and setup target Linux only)
- **Python 3.10+**
- **selenium >= 4**

`setup.sh` handles downloading Firefox ESR and geckodriver automatically.

## How it compares

| Approach | Fingerprint resistance | Detectable? |
|---|---|---|
| Raw Selenium + Chrome | None | Instantly detected |
| undetected-chromedriver | JS overrides for ~10 signals | Detected by sophisticated systems |
| Playwright stealth | JS overrides | Detected by Cloudflare, DataDome |
| **browse** | Native C++ anti-fingerprinting via RFP + binary patch | Passes all known checks |

The fundamental difference: every other tool tries to make Chrome *look like* a normal browser via JavaScript. `browse` uses Firefox with RFP — a browser that *genuinely* implements anti-fingerprinting at the engine level — and removes the automation flag at the binary level.

## MCP server

For AI frontends that support [Model Context Protocol](https://modelcontextprotocol.io/) (Claude Desktop, Claude Code, LM Studio, etc.), browse ships an MCP server that exposes the browser as tools.

### Setup

```bash
# Install with MCP support
pip install -e ".[mcp]"
```

### Claude Desktop / Claude Code config

```json
{
  "mcpServers": {
    "browse": {
      "command": "browse-mcp"
    }
  }
}
```

The AI can now browse the web. No separate server to run.

### How it works

The MCP server supports two modes that the AI agent picks based on context:

**Quick mode** — the agent launches its own browser, does the work, closes it. Supports multiple browsers in parallel for fetching data from several sites at once.

**Session mode** — if you already have a browser open (`browse`), the agent automatically connects to it. When it disconnects, your browser stays open. The session browser is always preferred over quick browsers.

### Available tools

| Tool | What it does |
|---|---|
| `browse_status` | Check for active browsers and existing sessions |
| `browse_open` | Launch a new browser (optionally navigate to URL) |
| `browse_connect` | Join an existing human browser session |
| `browse_navigate` | Go to a URL in a browser |
| `browse_fetch` | One-shot curl-style fetch (url or search query), no browser ID, auto-cleanup |
| `browse_search` | Search Google/DuckDuckGo (auto-opens browser if needed) |
| `browse_click` | Click an element on the page |
| `browse_type` | Type into an input field, optionally submit |
| `browse_extract` | Re-extract current page content |
| `browse_screenshot` | Take a screenshot (downscaled to reduce context usage) |
| `browse_back` / `browse_forward` | Navigate history |
| `browse_scripts` | List available automation scripts |
| `browse_run_script` | Run a reusable automation script |
| `browse_close` | Close browser (quick) or disconnect (session) |

All tools take an optional `browser_id` for parallel browsing. Each result includes the page content (with prompt injection filtering) plus suggested next actions.

## Credits

- [Firefox ESR](https://www.mozilla.org/en-US/firefox/enterprise/) — the browser engine with RFP anti-fingerprinting
- [undetected_geckodriver](https://github.com/AShujjah/undetected_geckodriver) — binary patching approach

## License

MIT. See [LICENSE](LICENSE).
