# Firefox Tab Coloring & Focus Control for Multi-Agent Browser Automation
## Multi-Angle Research Synthesis

**Date:** 2026-02-12
**Angles analyzed:** 10
**Method:** Parallel multi-agent research (7 WebSearch, 2 Browse, 1 mixed)

---

## Executive Summary

Per-agent tab coloring in Firefox is achievable and well-supported through a **custom attribute + CSS** approach that mirrors Firefox's own container tab system. The current codebase's failure to color tabs stems from a gap between the color assignment in Python (`_AGENT_COLORS` palette) and the browser chrome: the omni.ja CSS only uses hardcoded green via `:root[browseagent]`, and the indicator extension themes the entire window rather than individual tabs. The fix is to set a per-tab attribute (`browseagent-color`) on `tabbrowser-tab` DOM elements via Selenium's chrome context, then add CSS rules in the omni.ja patch targeting `.tabbrowser-tab[browseagent-color="green"] .tab-background`. This follows the exact same architectural pattern Firefox uses for container tab coloring with `[usercontextid]` and `--identity-tab-color`.

Tab focus hopping is a harder problem. Selenium's `switch_to.window()` **must** change the visually active tab -- this is mandated by the W3C WebDriver specification and Selenium's team explicitly rejected feature requests to change it. The Marionette protocol underneath has a `focus=false` parameter (Bug 1124604), but it's not exposed through Selenium's API. The current `_restore_human_focus()` pattern of snapping back to the human's tab after each agent command is the correct approach, but causes brief visual flicker. The only complete solution is WebDriver BiDi's browsing context targeting, which allows executing scripts in specific tabs without switching -- but Playwright's audit found only 38% of tests passing on Firefox as of late 2024, making it not yet production-ready.

## Consensus Points

- **Custom tab attributes + CSS is the correct coloring mechanism** (Supported by Angles: 01, 02, 07, 10): `tab.setAttribute('browseagent-color', colorName)` from chrome context JS, targeted by `.tabbrowser-tab[browseagent-color="X"] .tab-background {...}` CSS rules. This is the same pattern Firefox uses internally for container tabs (`usercontextid` + `--identity-tab-color`). Setting attributes on `tabbrowser-tab` elements does NOT trigger focus changes.

- **Selenium's `switch_to.window()` always causes visual tab switching** (Supported by Angles: 05, 06, 08, 09): The W3C WebDriver spec mandates updating "implementation-specific state that would result from the user selecting the current browsing context." GeckoDriver's implementation calls `focusWindow()` and waits for `TabSelect` events. Selenium explicitly rejected feature requests for focus-free tab switching (#11393, #12759).

- **The omni.ja CSS patch is the right delivery mechanism for this project** (Supported by Angles: 02, 07, 10; Cautioned by Angles: 08, 09): Since the project already patches omni.ja for stealth purposes, adding per-tab color CSS rules there is the path of least resistance. However, omni.ja is fragile -- replaced on every Firefox update, signed in release builds, and has silent failure modes with repacking.

- **`gBrowser.addTab()` with `inBackground: true` prevents focus hopping during tab creation** (Supported by Angles: 01, 10): The code path skips `this.selectedTab = t` when `inBackground` is not `false`. The current codebase already uses this correctly.

- **Chrome context (`driver.context(driver.CONTEXT_CHROME)`) provides full access to tab DOM manipulation** (Supported by Angles: 01, 05, 07, 10): Confirmed working in Tor Browser 15.0 (Firefox ESR 140) with `--remote-allow-system-access` flag, which the codebase already passes.

- **Content-injected agent bars are fragile** (Supported by Angles: 07, 10): The current `_inject_agent_bar()` approach injects a 3px bar into page content, which is lost on navigation, removable by page JS, and invisible on certain pages. Chrome-level tab coloring via attributes is strictly superior.

## Key Disagreements & Uncertainties

- **Container tabs vs. custom attributes** (Angle 04 vs. Angles 01, 02, 07, 10): Container tabs (contextualIdentities API) provide a supported, update-proof coloring mechanism with native `.tab-context-line` indicators. However, they're limited to 8 predefined colors (blue, turquoise, green, yellow, orange, red, pink, purple), which is tight for a 10-agent swarm. Custom attributes offer unlimited colors but require omni.ja patching. **Resolution: Custom attributes are better for this use case** because we already patch omni.ja and need more than 8 colors.

- **omni.ja patching fragility** (Angles 08, 09 vs. Angle 10): omni.ja is replaced on every Firefox update, signed in release builds, and has silent failure modes. The firefox-omni-tweaks project has maintained compatibility across 56+ versions over 5 years, suggesting it's doable but high-maintenance. **Mitigating factor:** Tor Browser uses ESR releases (updated ~yearly), reducing the update frequency. The project already commits to omni.ja patching for stealth, so adding CSS rules is marginal cost.

- **Uncertainty: WebDriver BiDi readiness** (Angles 05, 09, 10): BiDi's `script.callFunction` with browsing context targets would eliminate focus switching entirely. Chrome/Puppeteer declared it "production-ready" in mid-2024, but Playwright found only 38% of tests passing on Firefox with dozens of blocking issues. Selenium's Python BiDi bindings are still maturing. **Status: not ready for production use in this project**.

- **Uncertainty: Tor Browser + container tabs interaction** (Angles 04, 09): Tor Browser's First Party Isolation (FPI) predates and is stricter than standard container tabs. Whether the contextualIdentities API works alongside FPI is poorly documented and could create unpredictable cookie/storage behavior.

## What's Real

- **Chrome-context tab attribute manipulation works** (Supported by Angles: 01, 07, 10): `tab.setAttribute()` from Marionette chrome context is well-documented, Firefox uses it internally, and community projects (Private_Tab, uc.css.js, fx-autoconfig) rely on it. CSS attribute selectors on `tabbrowser-tab` elements have been stable since Proton (Firefox 89).

- **Container tabs provide native per-tab coloring** (Supported by Angles: 02, 04): The `.tab-context-line` element with `--identity-tab-color` CSS variable is a built-in, supported, update-proof mechanism. Creating containers programmatically via the contextualIdentities API is straightforward.

- **The `_restore_human_focus()` pattern is correct** (Supported by Angles: 05, 10): `gBrowser.selectTabAtIndex(0)` immediately after each agent command is the right approach. The visual flicker is unavoidable with WebDriver Classic but can be minimized by keeping the lock held during the entire switch-execute-restore cycle.

## What's Hype

- **WebDriver BiDi as a near-term solution** (Contradicted by Angles: 09): Despite being declared "production-ready" by Chrome/Puppeteer, Playwright's systematic audit found massive gaps on Firefox (38% test pass rate). Key missing features include viewport management, network interception, authentication handling, and download events. Full BiDi parity is a multi-year effort.

- **Theme API for per-tab coloring** (Contradicted by Angles: 03, 08): `browser.theme.update()` is per-WINDOW, not per-TAB. The Colorful Tabs extension using this API "only affects the color of the currently selected tab (and the address bar), not providing you with a good overview." Per-tab coloring through the theme API is fundamentally impossible. Bug 1320585 ("Allow styling individual tabs") was never implemented.

- **Marionette `focus=false` as a workaround** (Contradicted by Angles: 05, 09): While Marionette's protocol has `focus=false` on `switchToWindow`, it's not exposed through Selenium's WebDriver API via GeckoDriver. Using the raw Marionette protocol bypasses Selenium entirely and is unsupported. Even with `focus=false`, some operations (click, sendKeys) may still require focus.

## Critical Risks

- **omni.ja patching breaks on Firefox/Tor Browser updates** (Supported by Angles: 08, 09): The file is replaced wholesale. Tor Browser ESR updates (~yearly) are less frequent but still require re-patching. The project's `patch_omni()` function must be re-run after every update.

- **Geckodriver race conditions during concurrent tab operations** (Supported by Angles: 08, 10): Issue #1770 documented `TypeError: this.mm is null` when switching tabs during creation/closure. The project serializes commands with a lock, but the switch-execute-restore pattern is inherently timing-sensitive.

- **userChrome.css and omni.ja CSS selectors break across Firefox versions** (Supported by Angles: 02, 08): Firefox 108, 113, 133, and 141 all broke tab CSS selectors. The `.tab-background` selector has been stable since Proton (FF89), but Firefox 119 changed boolean attributes from `selected="true"` to `[selected]`. Future versions may change tab DOM structure.

- **Multiple concurrent chrome-context script executions may interleave** (Supported by Angles: 01, 10): If multiple agents simultaneously execute chrome-context scripts via Marionette, commands are serialized per connection but multiple geckodriver instances sharing the same Firefox process could interleave. The current lock-based serialization mitigates this.

## Predictions (Near-Term)

- **Custom attribute + omni.ja CSS approach will work reliably for Tor Browser 15.x** (high confidence, Validated by Angles: 01, 02, 07, 10): The underlying APIs (`setAttribute`, CSS attribute selectors, chrome context) have been stable since Firefox 89. Tor Browser 15.0 (ESR 140) supports all required features.

- **Tab focus hopping will remain an issue until WebDriver BiDi matures** (high confidence, Validated by Angles: 05, 06, 09): There is no workaround within WebDriver Classic. The switch-execute-restore pattern is the best available approach. BiDi won't be production-ready for Firefox automation for at least 1-2 years.

- **Container tabs will be a viable coloring alternative if the project moves away from omni.ja patching** (medium confidence, Validated by Angles: 04, 09): The 8-color limitation can be extended with CSS overrides targeting `[usercontextid="N"]`, and containers survive browser updates. However, Tor Browser FPI compatibility needs testing.

- **Firefox will not add a per-tab theming API** (medium confidence, Validated by Angles: 03, 08): Bug 1320585 has been open since 2017 with no progress. Mozilla's WebExtension team is "very hesitant about allowing extensions to do things like focus the address bar" let alone style individual tabs. The Theme API will remain per-window.

## What to Monitor Next

- **WebDriver BiDi test pass rate on Firefox** -- Playwright's issue #32577 tracks blocking issues. When the pass rate exceeds 80%, BiDi becomes viable for replacing the switch-to-window pattern.

- **Tor Browser 16.0 (ESR 153) release** -- Expected Q3 2026. The tab DOM structure may change, requiring CSS selector updates in the omni.ja patch.

- **Firefox tab groups feature** -- Shipping 2025-2026. May introduce new API surface for per-group coloring that could be leveraged.

- **Selenium Python BiDi API stabilization** -- `script.callFunction` with browsing context targets would eliminate focus switching entirely. Track Selenium release notes for Firefox BiDi coverage.

- **`toolkit.legacyUserProfileCustomizations.stylesheets` deprecation** -- Firefox has been threatening to remove userChrome.css support. If this happens, omni.ja would be the only CSS injection path, making the current approach even more important.

## Recommended Implementation (Priority Order)

### 1. Fix Tab Coloring (Immediate)

**Root cause:** omni.ja CSS uses hardcoded green via `:root[browseagent]`. Per-agent colors from `_AGENT_COLORS` never reach the tab strip.

**Fix:**
- In `stealth.py` `patch_omni()`: Add CSS rules for each color: `.tabbrowser-tab[browseagent-color="green"] .tab-background { background: linear-gradient(to bottom, rgba(0,255,136,0.15), transparent) !important; }` and `.tabbrowser-tab[browseagent-color="green"] .tab-context-line { background-color: #00ff88 !important; display: block !important; opacity: 1 !important; }`
- In `session.py` `_assign_agent()`: After creating the tab, set the attribute via chrome context: `tab.setAttribute('browseagent-color', colorName)`
- In `session.py` `_release_agent()`: Remove the attribute before closing: `tab.removeAttribute('browseagent-color')`

### 2. Minimize Focus Disruption (Short-term)

**Root cause:** `switch_to.window()` changes the visually selected tab. `_restore_human_focus()` snaps back but causes flicker.

**Mitigations:**
- For read-only operations (extract_content, current_url, read-only JS): Use `gBrowser.getBrowserForTab()` from chrome context to access the tab's content without switching visual focus
- For write operations (navigate, click, type): Keep the switch-execute-restore cycle as tight as possible within a single lock acquisition
- Replace `_inject_agent_bar()` content injection with chrome-level tab coloring (eliminates one source of navigation-triggered disruption)

### 3. WebDriver BiDi Migration (Long-term)

When Selenium's Python BiDi API is stable and Tor Browser confirms BiDi support, use `script.callFunction` with specific browsing context targets to eliminate focus switching entirely.
