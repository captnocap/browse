# browse — future QoL enhancements

## Tab management
- Expose `browse_list_tabs`, `browse_use_tab`, `browse_open_tab` in MCP server — currently only available via Python API
- Tab grouping — let agents label tabs by purpose (e.g. "research", "login") so they can find them without tracking indices
- Auto-close stale agent tabs after configurable timeout

## Agent indicator
- Explore using the `toolbar_bottom_separator` gap (visible with side tabs) as a mini status bar — show current agent action text
- Per-agent colors when multiple agents connect simultaneously (the CSS is ready, wiring was never completed)
- Indicator on the startpage dashboard showing which tabs are agent-controlled in real time

## Content extraction
- JS-heavy site support — configurable wait strategy (wait for specific selector, network idle, etc.) instead of link-count stabilization
- Infinite scroll handling — auto-scroll and accumulate content for feeds/timelines
- iframe content extraction — currently only extracts from the top frame
- PDF/document content extraction when browser is viewing a PDF

## MCP server
- `browse_scroll` tool — scroll down/up to load more content or reach elements below the fold
- `browse_wait` tool — wait for a specific selector to appear before extracting (useful for SPAs)
- `browse_tabs` tool — list/switch/open tabs from MCP (mirrors the Python API)
- Streaming extraction — return partial content while page is still loading for very slow sites
- Screenshot scaling configurable via browse.conf (currently hardcoded 1024px)

## Profile system
- `browse profile list` — show all saved profiles
- `browse profile delete <name>` — remove a profile
- Named profiles — `browse --profile work` / `browse --profile personal` instead of paths
- Auto-detect and warn if cloned profile is from a significantly newer Firefox version

## Cookie management
- Cookie export — save current session cookies to file for backup/sharing
- Per-domain cookie clear — `browse cookies clear github.com`
- Cookie freshness check — warn if imported cookies are expired

## Stealth
- Rotate user-agent on a configurable schedule while keeping RFP consistency
- Proxy rotation support — pool of proxies with automatic failover
- macOS/Windows support — adapt binary patching for platform-specific libxul
- Test suite that runs bot detection checks automatically and reports pass/fail

## Session mode
- Multiple named sessions — run more than one browser session simultaneously
- Session resume — reconnect to a browser that was launched in a previous terminal session
- Remote session — connect to a browse session running on another machine
- Activity log — persistent log of all agent actions (not just navigation history)

## Startpage dashboard
- Live tab list with agent/human labels and pink/blue indicators
- Action feed — show what the agent is doing in real time (clicking, typing, navigating)
- Manual agent control — buttons to disconnect agents, close agent tabs from the dashboard

## Developer experience
- `browse test` — run the bot detection suite and print a pass/fail report
- `browse debug` — launch with verbose logging for troubleshooting
- Python async API — `async with AgentBrowser() as browser:` for use in async frameworks
- Type stubs / py.typed for IDE autocomplete
