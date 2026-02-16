# Angle 05 — Selenium/Marionette Focus Control

## Claims (with confidence)

- Claim (high): Selenium WebDriver's `switch_to.window(handle)` API does NOT expose a focus parameter -- it only accepts a window handle string. The underlying Marionette protocol, however, DOES have a `focus` boolean parameter (defaulting to `true`) on its `WebDriver:SwitchToWindow` command. This parameter was added in Firefox 54 via Bug 1124604. There is a real API gap: Selenium users cannot pass `focus=False` through the standard WebDriver API.

- Claim (high): The W3C WebDriver spec explicitly states that Switch To Window should "update any implementation-specific state that would result from the user selecting the current browsing context for interaction, without altering OS-level focus." This means the spec intends that the OS-level window focus should NOT change, but the browser's internal selected tab/context DOES change. In practice, Firefox's Marionette implementation visually switches the selected tab (changes `gBrowser.selectedTab`) and waits for the TabSelect event before returning.

- Claim (high): When Marionette's `switchToWindow` is called with `focus=true` (the default), it calls `curBrowser.focusWindow()` which brings the window to foreground, waits for "activate" and "focus" events, and waits for the asynchronous "TabSelect" event. This was fixed in Firefox 69 (Bug 1335085) to eliminate a race condition where the command returned before the tab was actually visually selected.

- Claim (high): When Marionette's `switchToWindow` is called with `focus=false`, the internal browsing context references (`currentSession.chromeBrowsingContext` and `currentSession.contentBrowsingContext`) are still updated, but `focusWindow()` is NOT called. This means subsequent commands will target the new tab's content, but the visual tab strip may not change. However, this parameter is only available through the raw Marionette protocol (port 2828) or the `marionette_driver` Python package -- NOT through Selenium's WebDriver API via GeckoDriver.

- Claim (high): WebDriver BiDi (the next-generation protocol) fundamentally solves this problem. BiDi commands like `script.evaluate` and `script.callFunction` accept a `target` parameter specifying a browsing context or realm. This allows executing scripts in ANY tab without switching to it at all. BiDi's `browsingContext.navigate` can navigate a specific tab by context ID. Firefox has implemented BiDi support, and Selenium 4 exposes it in Python/Java.

- Claim (medium): Firefox's `focusmanager.testmode` preference (set to `true` by Marionette by default) allows Firefox to virtually maintain focus state even when the browser window is in the background. This means focus/blur events still fire correctly for automation even when Firefox isn't the foreground application. Bug 1398111 fixed this by calling `window.focus()` on the chrome window during `WebDriver:NewSession`, simulating that Firefox is always the topmost app.

- Claim (medium): Using Marionette's chrome context (`CONTEXT_CHROME`), you can execute privileged JavaScript that accesses `gBrowser` and operate on specific tabs without visually switching to them. For example, `gBrowser.getBrowserForTab(gBrowser.tabs[n])` returns the browser element for any tab, and you could inject content or styles into that tab's content document. This approach bypasses the need for `switchToWindow` entirely for operations like CSS injection.

- Claim (medium): The `tabs.insertCSS(tabId, details)` WebExtension API can inject CSS into a specific tab by its ID without activating that tab. If a companion WebExtension is running alongside Selenium automation, it could handle per-tab CSS injection (e.g., for tab coloring borders) without any tab switching at all.

- Claim (low): GeckoDriver (the Rust-based WebDriver proxy) translates W3C WebDriver HTTP commands into Marionette protocol messages. It likely does NOT pass a `focus` parameter to Marionette's `switchToWindow` because the W3C WebDriver spec does not define such a parameter. The spec only defines a `handle` field. This means the Marionette-level `focus=false` capability is effectively inaccessible through the standard Selenium -> GeckoDriver -> Marionette chain.

## Evidence

- The Marionette Python driver docs confirm `switch_to_window(handle, focus=True)` with an explicit focus boolean parameter -- [marionette_driver package docs](https://firefox-source-docs.mozilla.org/python/marionette_driver.html)

- Bug 1124604 added the `focus` parameter to `switch_to_window()` in Marionette, resolved as FIXED in Firefox 54 -- [Bugzilla Bug 1124604](https://bugzilla.mozilla.org/show_bug.cgi?id=1124604)

- Bug 1335085 fixed a race condition where `WebDriver:SwitchToWindow` returned before the target tab actually had focus. The fix waits for TabSelect and activate/focus events -- [Bugzilla Bug 1335085](https://bugzilla.mozilla.org/show_bug.cgi?id=1335085)

- Bug 1398111 fixed missing focus events when Firefox is in background by setting `focusmanager.testmode` and calling `window.focus()` during session creation. Three patches were landed: frame reference updates, virtual focus on session creation, and test mode persistence -- [Bugzilla Bug 1398111](https://bugzilla.mozilla.org/show_bug.cgi?id=1398111)

- Selenium issue #11393 requested "switch to tab without focusing" and was closed as a question, with the Selenium team suggesting headless mode or Grid as workarounds. No implementation planned -- [GitHub Issue #11393](https://github.com/SeleniumHQ/selenium/issues/11393)

- The W3C WebDriver spec defines Switch To Window as updating implementation-specific state "without altering OS-level focus" -- [W3C WebDriver Spec](https://w3c.github.io/webdriver/)

- The Marionette driver source at `remote/marionette/driver.sys.mjs` shows `switchToWindow` extracting `focus` from `cmd.parameters` with default `true`, then calling `setWindowHandle()` which conditionally calls `focusWindow()` based on the focus parameter -- [Fossies mirror of driver.sys.mjs](https://fossies.org/linux/firefox/remote/marionette/driver.sys.mjs)

- WebDriver BiDi spec allows `script.evaluate` to target a specific browsing context via `ContextTarget = { context: Context }`, eliminating the need to switch windows -- [W3C WebDriver BiDi Spec](https://w3c.github.io/webdriver-bidi/)

- The `tabs.insertCSS(tabId, details)` WebExtension API can inject CSS into any tab by ID without activating it -- [MDN tabs.insertCSS](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/Tabs/insertCSS)

- `gBrowser` (tabbrowser.js) manages tabs and provides `getBrowserForTab()` to access specific tab browser elements without selection -- [Firefox tabbrowser docs](https://firefox-source-docs.mozilla.org/browser/base/tabbrowser/index.html)

- Bug 1216949 confirmed that click interactions fail when Firefox is not focused, due to missing focus events rather than queued clicks -- [Bugzilla Bug 1216949](https://bugzilla.mozilla.org/show_bug.cgi?id=1216949)

## Architectural Summary

The Selenium/GeckoDriver/Marionette/Firefox stack has FOUR distinct layers with different capabilities:

```
Layer 1: Selenium WebDriver API (Python/Java/etc)
  - switch_to.window(handle) -- NO focus parameter
  - Only way to run commands on a different tab is to switch to it
  - BiDi APIs (Selenium 4+) can target specific contexts without switching

Layer 2: GeckoDriver (Rust HTTP proxy)
  - Translates W3C WebDriver HTTP to Marionette protocol
  - Likely sends focus=true by default (W3C spec has no focus param)
  - Does NOT expose Marionette-specific extensions

Layer 3: Marionette Protocol (inside Firefox, port 2828)
  - WebDriver:SwitchToWindow accepts {handle, focus} parameters
  - focus=false: updates internal context without calling focusWindow()
  - Accessible directly via marionette_driver Python package
  - CONTEXT_CHROME allows privileged gBrowser access

Layer 4: Firefox Internals (gBrowser, tabbrowser.js)
  - gBrowser.selectedTab is the visually selected tab
  - gBrowser.getBrowserForTab(tab) accesses any tab's browser
  - Tab selection fires TabSelect event asynchronously
  - focusmanager.testmode virtualizes focus for background windows
```

## Key Distinction: "Current Browsing Context" vs "Visually Selected Tab"

The Marionette protocol maintains its own concept of "current browsing context" (stored in `currentSession.contentBrowsingContext` and `currentSession.chromeBrowsingContext`). This is the tab that Marionette commands will target.

Firefox's UI maintains a separate concept of the "visually selected tab" (`gBrowser.selectedTab`), which is the tab the user sees as active in the tab strip.

When `focus=true` (default and Selenium behavior): Both are synchronized -- Marionette's current context AND the visual tab switch together.

When `focus=false` (Marionette-only): Only Marionette's current context changes. The visual tab MAY remain unchanged (though this depends on implementation details of how `setWindowHandle` updates things without `focusWindow()`).

## Practical Implications for Tab Coloring / Agent Focus

### Problem
When multiple agents connect to tabs via Selenium, each `switch_to.window()` call causes a visual tab hop. This creates a jarring flickering effect as different agents take turns operating on their tabs.

### Solutions (ranked by feasibility)

1. **WebDriver BiDi (best long-term solution)**: Use BiDi `script.evaluate` / `script.callFunction` with a target context to execute JavaScript in specific tabs without switching. Selenium 4 supports this for Firefox. This completely eliminates tab switching for script execution.

2. **Direct Marionette protocol with focus=false**: Bypass GeckoDriver and connect directly to Marionette on its port using the `marionette_driver` Python package. Call `switch_to_window(handle, focus=False)` to change the command target without visual tab switching. Caveat: some operations (click, sendKeys) may still require focus to work correctly.

3. **Chrome context + gBrowser**: Use Marionette's `set_context(CONTEXT_CHROME)` and `execute_script()` to run privileged JS that accesses `gBrowser.getBrowserForTab()` for specific tabs. This can inject styles, read DOM content, or manipulate tabs without switching. This is the most powerful approach for operations like injecting colored borders into specific tabs.

4. **Companion WebExtension with tabs.insertCSS**: Deploy a WebExtension that listens for messages (e.g., via native messaging or a local WebSocket) and calls `tabs.insertCSS(tabId, ...)` to inject per-tab coloring CSS without any tab switching.

5. **Headless mode**: Eliminates visual artifacts entirely, but also eliminates the visual feedback that tab coloring is meant to provide.

## What I'm unsure about

- Whether GeckoDriver actually hardcodes `focus=true` when translating the W3C SwitchToWindow command to Marionette, or whether it omits the parameter and lets Marionette default. I could not access the GeckoDriver Rust source code directly to confirm.

- The exact behavior of Marionette's `setWindowHandle` when `focus=false` -- specifically whether it still changes `gBrowser.selectedTab` (just without waiting for events) or truly leaves the visual tab unchanged. The source analysis suggests it skips `focusWindow()` but may still update tab state.

- Whether Selenium 4's BiDi implementation in Python for Firefox is mature enough to use `script.evaluate` with a target context reliably. BiDi is still evolving and some features may be incomplete.

- Whether the `focusmanager.testmode` preference affects the visual tab switching behavior, or only affects focus/blur event firing. The documentation suggests it only handles focus events, not visual state.

- The exact interaction between Marionette's `focus=false` and Firefox's internal tab management -- whether content scripts (not chrome scripts) can be reliably executed in a tab that is not visually selected without `focusmanager.testmode`.

- Whether `gBrowser.getBrowserForTab(tab).contentDocument` is accessible for cross-origin pages when operating from chrome context, or if same-origin restrictions still apply within privileged Marionette scripts.

## Sources

- [Selenium Windows/Tabs Documentation](https://www.selenium.dev/documentation/webdriver/interactions/windows/)
- [Selenium Issue #11393: Switch to tab without focusing](https://github.com/SeleniumHQ/selenium/issues/11393)
- [Bugzilla Bug 1124604: Add focus parameter to switch_to_window()](https://bugzilla.mozilla.org/show_bug.cgi?id=1124604)
- [Bugzilla Bug 1335085: SwitchToWindow must wait for activate/focus events](https://bugzilla.mozilla.org/show_bug.cgi?id=1335085)
- [Bugzilla Bug 1398111: Missing focus events in background](https://bugzilla.mozilla.org/show_bug.cgi?id=1398111)
- [Bugzilla Bug 1216949: Interactions not effective unless Firefox focused](https://bugzilla.mozilla.org/show_bug.cgi?id=1216949)
- [Bugzilla Bug 1523234: New window focus issues](https://bugzilla.mozilla.org/show_bug.cgi?id=1523234)
- [Bugzilla Bug 1588424: SwitchToWindow handle argument](https://bugzilla.mozilla.org/show_bug.cgi?id=1588424)
- [Bugzilla Bug 704583: FocusManager testing mode for concurrent webdriver tests](https://bugzilla.mozilla.org/show_bug.cgi?id=704583)
- [Bugzilla Bug 1489967: Keep focus with focusmanager test mode](https://bugzilla.mozilla.org/show_bug.cgi?id=1489967)
- [W3C WebDriver Specification](https://w3c.github.io/webdriver/)
- [W3C WebDriver BiDi Specification](https://w3c.github.io/webdriver-bidi/)
- [W3C WebDriver BiDi Issue #18: Script execution contexts](https://github.com/w3c/webdriver-bidi/issues/18)
- [W3C WebDriver BiDi Issue #63: Script execution module](https://github.com/w3c/webdriver-bidi/issues/63)
- [Marionette Introduction (Firefox Source Docs)](https://firefox-source-docs.mozilla.org/testing/marionette/Intro.html)
- [Marionette Driver Python API Docs](https://firefox-source-docs.mozilla.org/python/marionette_driver.html)
- [Marionette Index (Firefox Source Docs)](https://firefox-source-docs.mozilla.org/testing/marionette/index.html)
- [GeckoDriver GitHub Repository](https://github.com/mozilla/geckodriver)
- [GeckoDriver Issue #610: Switch to window and top-level browsing context](https://github.com/mozilla/geckodriver/issues/610)
- [Selenium Issue #5831: Switch To Window translation](https://github.com/SeleniumHQ/selenium/issues/5831)
- [Firefox tabbrowser Documentation](https://firefox-source-docs.mozilla.org/browser/base/tabbrowser/index.html)
- [Fossies: remote/marionette/driver.sys.mjs source](https://fossies.org/linux/firefox/remote/marionette/driver.sys.mjs)
- [Searchfox: WindowManager.sys.mjs](https://searchfox.org/mozilla-central/source/remote/shared/WindowManager.sys.mjs)
- [MDN: tabs.insertCSS()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/Tabs/insertCSS)
- [Selenium BiDi Browsing Context Docs](https://www.selenium.dev/documentation/webdriver/bidi/w3c/browsing_context/)
- [Selenium BiDi Script Docs](https://www.selenium.dev/pt-br/documentation/webdriver/bidi/w3c/script/)
- [WebDriver BiDi Core Proposal](https://github.com/w3c/webdriver-bidi/blob/main/proposals/core.md)
- [LambdaTest: Solving Selenium Focus Issues](https://www.lambdatest.com/blog/solving-selenium-focus-issues/)
