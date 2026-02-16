# Angle 10 — Integration Strategy

Cross-referencing findings about Firefox tab APIs, CSS, and Selenium focus management to determine the best practical approach for our specific use case: a Selenium-driven Tor Browser (Firefox ESR based) where multiple AI agents connect via TCP, each gets a tab, and we need (a) each agent's tab to have a unique colored indicator and (b) the human user's visual focus to not be disrupted when agents connect/disconnect/execute commands.

## Claims (with confidence)

- Claim (high): **Tor Browser 15.0 is based on Firefox ESR 140**, released October 2025. The next major version (16.0, based on ESR 153) is expected mid-Q3 2026. All APIs and CSS features available in Firefox 140 are available in the current Tor Browser stable. This means the `--remote-allow-system-access` flag (landed in Firefox 138, bug 1710425) is available and is what our codebase already passes via `-remote-allow-system-access`.

- Claim (high): **gBrowser.tabs[i].setAttribute() works for setting arbitrary custom attributes on tab XUL elements from chrome context**, and these attributes are targetable by CSS in both userChrome.css and omni.ja stylesheets. Firefox's own codebase uses this exact pattern: `tab.setAttribute("usercontextid", userContextId)` followed by `ContextualIdentityService.setTabStyle(tab)` to apply per-container-tab colors. We can replicate this pattern with our own custom attribute (e.g., `browseagent-color`).

- Claim (high): **Selenium's `switch_to.window(handle)` changes BOTH the Marionette browsing context AND the visual/selected tab in Firefox.** There is no standard WebDriver Classic way to set the browsing context to a background tab without also making it the visually selected tab. This is confirmed by Selenium documentation stating "switching is done by changing the focus" and Firefox requiring FocusIn events for the switch to complete.

- Claim (high): **Chrome-context JS via `gBrowser.selectedTab = tab` / `gBrowser.selectTabAtIndex(n)` DOES change the visually focused tab.** However, `gBrowser.getBrowserForTab(someTab)` allows accessing a specific tab's browser element without changing the selected tab. Combined with messageManager or direct DOM access, this allows chrome-privilege code to interact with background tabs.

- Claim (high): **The omni.ja CSS patch approach (already implemented in stealth.py) is the correct mechanism for tab coloring.** The CSS in omni.ja's `chrome/browser/skin/classic/browser/urlbar-searchbar.css` can target `.tabbrowser-tab[browseagent-color="green"] .tab-background` attribute selectors. This is the same technique Firefox uses internally for container tabs with `[usercontextid]`.

- Claim (medium): **The current architecture's approach of calling `_restore_human_focus()` after every command is the right pattern**, but it has a visual flicker issue because `switch_to.window()` must change the selected tab before the command runs. The chrome-context approach (`gBrowser.getBrowserForTab()`) could eliminate the need for `switch_to.window()` for some commands (like execute_js), but not all (click, type_text require content-context focus).

- Claim (medium): **WebDriver BiDi's `script.callFunction` with a browsing context target can execute scripts in a specific tab without switching visual focus**, and this is supported in Firefox 140+ (BiDi reached 100% coverage in Firefox ~131). However, Selenium's Python BiDi API is still maturing, and Tor Browser may not have all BiDi features enabled. This is the future-proof solution but may not be production-ready today.

- Claim (medium): **Per-tab coloring via chrome JS + omni.ja CSS is more reliable than the current content-script injection approach** (`_inject_agent_bar`). Content-injected bars can be lost on navigation, removed by page JS, or invisible on certain pages. Chrome-level tab styling persists regardless of page content.

- Claim (low): **The frame script / messageManager approach (`gBrowser.getBrowserForTab(tab).messageManager.loadFrameScript()`) could allow injecting scripts into background tabs without switching**, but this is a legacy Firefox API that may be removed in future ESR versions. It still works in Firefox 140 ESR but is not the recommended path forward.

## Evidence

### Firefox ESR Version in Tor Browser

- Tor Browser 15.0 is based on Firefox ESR 140 series — [9to5Linux: Tor Browser 15.0](https://9to5linux.com/tor-browser-15-0-anonymous-web-browser-is-out-based-on-firefox-140-esr-series)
- Tor Browser 16.0 (ESR 153) expected Q3 2026 — [OTF: Transitioning to ESR 140](https://www.opentech.fund/projects-we-support/supported-projects/transitioning-tor-browser-to-firefox-esr-140/)

### Chrome Context and --remote-allow-system-access

- Bug 1710425 (RESOLVED FIXED in Firefox 138): Chrome context requires `--remote-allow-system-access` on Firefox or `--allow-system-access` on geckodriver — [Bugzilla 1710425](https://bugzilla.mozilla.org/show_bug.cgi?id=1710425)
- Our codebase already passes `-remote-allow-system-access` in session.py line 728 — verified in source code
- Geckodriver docs confirm the flag enables the `/session/{id}/moz/context` endpoint — [Geckodriver Flags](https://firefox-source-docs.mozilla.org/testing/geckodriver/Flags.html)

### gBrowser.tabs setAttribute for Custom Attributes

- Firefox tabbrowser.js source shows `tab.setAttribute("usercontextid", userContextId)` followed by `ContextualIdentityService.setTabStyle(tab)` for container tab coloring — [Searchfox: tabbrowser.js](https://searchfox.org/mozilla-central/source/browser/components/tabbrowser/content/tabbrowser.js)
- Container tab CSS uses `.tabbrowser-tab[usercontextid] .tab-background` with `var(--identity-tab-color)` — [MDN: Contextual Identities](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Work_with_contextual_identities)
- Custom attributes set via JS are immediately targetable by CSS attribute selectors in userChrome.css — [userchrome.org](https://www.userchrome.org/what-is-userchrome-css.html)

### CSS Tab Structure in Proton UI

- Tab background: `.tabbrowser-tab .tab-background` — [Proton UI Styling Guide](https://www.userchrome.org/firefox-89-styling-proton-ui.html)
- Tab accent line: `.tabbrowser-tab .tab-context-line` (for container indicators) — [Raymii.org: Firefox 89 Tab Styling](https://raymii.org/s/blog/Firefox-89-proton-ui-tab-styling.html)
- Selected tab: `.tabbrowser-tab[selected="true"] .tab-background` — [userchrome.org Proton](https://www.userchrome.org/firefox-89-styling-proton-ui.html)

### Selenium switch_to.window Changes Visual Focus

- "Switching windows is done by changing the focus" — [Selenium Legacy Docs: Focus Stealing](https://www.selenium.dev/documentation/legacy/selenium_2/focus_stealing/)
- On Linux/Firefox, switch_to.window requires FocusIn events to complete — same source
- WebDriver spec says switch_to.window "will focus the new window or tab on screen" — [Selenium: Windows and Tabs](https://www.selenium.dev/documentation/webdriver/interactions/windows/)

### Marionette Chrome Context Script Execution

- `set_context("chrome")` + `execute_script()` allows access to gBrowser and all chrome APIs — [Marionette Driver Docs](https://firefox-source-docs.mozilla.org/python/marionette_driver.html)
- Example: `driver.set_context("chrome"); driver.execute_script("return gBrowser.tabs.length")` — [Selenium Firefox WebDriver API](https://www.selenium.dev/selenium/docs/api/py/selenium_webdriver_firefox/selenium.webdriver.firefox.webdriver.html)
- The `using_context()` context manager automatically saves/restores context — same source

### WebDriver BiDi for Future Focus-Free Script Execution

- BiDi allows "targeting any context and handling events from that context without the need to switch to it first" — [W3C WebDriver BiDi](https://w3c.github.io/webdriver-bidi/)
- `script.callFunction` accepts a ContextTarget with specific browsing context ID — [W3C BiDi Issue #18](https://github.com/w3c/webdriver-bidi/issues/18)
- Firefox reached 100% BiDi module coverage around Firefox 131 — [Firefox Nightly Blog](https://blog.nightly.mozilla.org/2024/07/18/100-webdriver-bidi-and-101-more-these-weeks-in-firefox-issue-164/)

### Our Current Codebase Architecture

- session.py already uses `gBrowser.addTab(url, {inBackground: true, ...})` for background tab creation (line 410-416)
- `_restore_human_focus()` uses `gBrowser.selectTabAtIndex(0)` to snap back to human tab (line 446-453)
- `_update_indicator()` sets/removes `browseagent` attribute on `document.documentElement` for chrome CSS targeting (line 360-376)
- stealth.py patches omni.ja CSS to add `:root[browseagent]` selectors for tab-line and urlbar glow (lines 133-174)
- The indicator WebExtension uses `browser.theme.update()` for whole-window theming, not per-tab coloring

## What I'm unsure about

- **Whether `switch_to.window()` always causes a visible tab flash on Linux/Wayland.** The Selenium docs say it changes focus, but some internal Marionette operations may batch focus changes. Our `_restore_human_focus()` call immediately after might reduce visible flicker to near-zero, but I haven't confirmed this empirically with timing measurements.

- **Whether `gBrowser.getBrowserForTab(tab).contentWindow` allows full content-context script execution from chrome context without ever setting the tab as selected.** The messageManager approach works for injecting frame scripts, but whether you can do the equivalent of `driver.execute_script()` in a background tab's content from chrome context alone needs verification.

- **The exact CSS selector path for the tab context/accent line in Firefox 140 ESR.** Proton UI has evolved across versions. The selectors `.tab-context-line`, `.tab-bottom-line`, and `.tab-line` have all been used in different Firefox versions. We need to verify which one exists in Firefox 140 ESR specifically.

- **Whether Tor Browser 15.0 has any patches that disable or restrict the `--remote-allow-system-access` functionality.** Tor Browser makes security-focused modifications to Firefox. While our codebase already uses this flag successfully, it's unclear if all chrome-context operations (especially those touching tab DOM attributes) work identically to upstream Firefox.

- **Whether WebDriver BiDi's `script.callFunction` with a specific browsing context actually avoids changing the visually selected tab, or if Firefox's implementation still triggers a visual tab switch internally.** The spec says it targets a context, but the implementation detail of whether this triggers UI focus changes is unclear.

- **Thread safety of the current `_handle_client` approach when multiple agents send commands concurrently.** The lock serializes commands, but the pattern of switch_to.window -> execute -> _restore_human_focus could interleave poorly if the lock is released between operations (it isn't currently, but this is fragile).

## Recommended Integration Strategy

### Immediate Improvement: Per-Tab Chrome CSS Coloring

The highest-impact, lowest-risk improvement is to extend the existing omni.ja patch and chrome-context JS to set per-tab color attributes:

**Step 1: Extend omni.ja CSS** to include selectors for a custom attribute:
```css
.tabbrowser-tab[browseagent-color="green"] .tab-background {
  background: linear-gradient(to bottom, #00ff8822, transparent) !important;
}
.tabbrowser-tab[browseagent-color="green"] .tab-context-line {
  background-color: #00ff88 !important;
  display: block !important;
  opacity: 1 !important;
}
/* Repeat for each color in _AGENT_COLORS */
```

**Step 2: In `_assign_agent()`**, after creating the tab, set the attribute via chrome context:
```python
with self.driver.context(self.driver.CONTEXT_CHROME):
    self.driver.execute_script(
        """
        let tabs = gBrowser.tabs;
        for (let tab of tabs) {
            if (tab.linkedBrowser.permanentKey === arguments[1]) {
                tab.setAttribute('browseagent-color', arguments[0]);
                break;
            }
        }
        """,
        color_name, new_handle_identifier
    )
```

Or more practically, since we know the tab was just created:
```python
with self.driver.context(self.driver.CONTEXT_CHROME):
    self.driver.execute_script(
        """
        // The last tab is the one we just created
        let tab = gBrowser.tabs[gBrowser.tabs.length - 1];
        tab.setAttribute('browseagent-color', arguments[0]);
        """,
        color_name
    )
```

**Step 3: In `_release_agent()`**, remove the attribute before closing.

### Medium-Term: Minimize Visual Focus Disruption

The current approach of `switch_to.window(agent_handle)` -> execute -> `_restore_human_focus()` causes brief visual flicker. To minimize this:

1. **For read-only operations** (extract_content, current_url, execute_js that only reads): Execute in chrome context using `gBrowser.getBrowserForTab()` to access the tab's content without switching visual focus.

2. **For write operations** (navigate, click, type_text): These require the tab to be the active browsing context. The switch is unavoidable, but can be made as brief as possible by keeping the `_restore_human_focus()` call immediately after in the same lock acquisition.

3. **For the agent bar injection**: Replace with the chrome-level tab coloring described above. The content-injected bar is fragile and unnecessary if tabs are colored.

### Long-Term: WebDriver BiDi

When Selenium's Python BiDi API stabilizes and Tor Browser confirms BiDi support:

1. Use `script.callFunction` with a specific browsing context to execute JS in agent tabs without any focus switching.
2. Use `browsingContext.navigate` targeted at specific contexts.
3. This would eliminate the switch_to.window/restore_human_focus dance entirely.

## Sources

- [9to5Linux: Tor Browser 15.0 Based on Firefox 140 ESR](https://9to5linux.com/tor-browser-15-0-anonymous-web-browser-is-out-based-on-firefox-140-esr-series)
- [OTF: Transitioning Tor Browser to Firefox ESR 140](https://www.opentech.fund/projects-we-support/supported-projects/transitioning-tor-browser-to-firefox-esr-140/)
- [Bugzilla 1710425: Chrome Context System Access Flag](https://bugzilla.mozilla.org/show_bug.cgi?id=1710425)
- [Geckodriver Flags Documentation](https://firefox-source-docs.mozilla.org/testing/geckodriver/Flags.html)
- [Searchfox: tabbrowser.js Source](https://searchfox.org/mozilla-central/source/browser/components/tabbrowser/content/tabbrowser.js)
- [Firefox tabbrowser Documentation](https://firefox-source-docs.mozilla.org/browser/base/tabbrowser/index.html)
- [MDN: Contextual Identities / Container Tabs](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Work_with_contextual_identities)
- [Selenium: Working with Windows and Tabs](https://www.selenium.dev/documentation/webdriver/interactions/windows/)
- [Selenium Legacy: Focus Stealing in Firefox](https://www.selenium.dev/documentation/legacy/selenium_2/focus_stealing/)
- [Marionette Driver Package Documentation](https://firefox-source-docs.mozilla.org/python/marionette_driver.html)
- [Selenium Python Firefox WebDriver API](https://www.selenium.dev/selenium/docs/api/py/selenium_webdriver_firefox/selenium.webdriver.firefox.webdriver.html)
- [W3C WebDriver BiDi Specification](https://w3c.github.io/webdriver-bidi/)
- [W3C BiDi Issue #18: Script Execution Contexts](https://github.com/w3c/webdriver-bidi/issues/18)
- [Firefox Nightly Blog: 100% WebDriver BiDi Coverage](https://blog.nightly.mozilla.org/2024/07/18/100-webdriver-bidi-and-101-more-these-weeks-in-firefox-issue-164/)
- [userchrome.org: Firefox 89+ Proton UI Styling](https://www.userchrome.org/firefox-89-styling-proton-ui.html)
- [Raymii.org: Firefox 89 Proton UI Tab Styling](https://raymii.org/s/blog/Firefox-89-proton-ui-tab-styling.html)
- [userchrome.org: What is userChrome.css](https://www.userchrome.org/what-is-userchrome-css.html)
- [CustomCSSforFx GitHub Repository](https://github.com/Aris-t2/CustomCSSforFx)
- [Firefox Browser Console Documentation](https://firefox-source-docs.mozilla.org/devtools-user/browser_console/index.html)
- [Bugzilla 1387117: Container Tab Color Indicator Visibility](https://bugzilla.mozilla.org/show_bug.cgi?id=1387117)
- [Intoli: JavaScript Injection with Selenium and Marionette](https://intoli.com/blog/javascript-injection/)
- [LambdaTest: Solving Selenium Focus Issues](https://www.lambdatest.com/blog/solving-selenium-focus-issues/)
