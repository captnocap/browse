# Angle 06 — WebExtension tabs API

## Claims (with confidence)

- Claim (high): browser.tabs.create() with active:false reliably creates background tabs without stealing focus from the currently active tab. The active property defaults to true; setting it to false prevents the new tab from becoming the active tab. This does NOT affect window focus (use windows.update for that). — MDN docs explicitly document this behavior.

- Claim (high): browser.tabs.executeScript() (MV2) and scripting.executeScript() (MV3) can both execute scripts on non-active tabs by specifying the tab ID. Neither API requires the target tab to be the active/focused tab. The only requirement is appropriate permissions: either host permissions for the target URL, or the activeTab permission (which only grants access to the currently active tab, so host permissions are needed for background tabs). — MDN docs confirm tabId parameter targets any tab with proper permissions.

- Claim (high): tabs.insertCSS() (MV2) and scripting.insertCSS() (MV3) can inject CSS into non-active tabs by specifying the target tab ID. This means visual indicators (borders, color overlays) can be applied to any tab's content without activating it. — MDN docs and Working with the Tabs API guide confirm this.

- Claim (high): browser.tabs.onActivated is a notification-only event that CANNOT prevent or cancel tab activation. It fires after the active tab has already changed. The listener receives {tabId, windowId, previousTabId} but has no mechanism to block the switch. — MDN explicitly states this cannot be prevented.

- Claim (high): browser.tabs.update() can modify a tab's properties (URL, muted, pinned) without activating it — the active property in updateProperties only activates a tab when set to true; setting it to false does nothing. Firefox uniquely supports setting highlighted:true with active:false to highlight a tab without activating it; other browsers may activate the tab even in this case. — MDN documents this Firefox-specific behavior.

- Claim (high): browser.tabs.move() reorders tabs by index within or across windows without changing which tab is active/focused. Moving a tab does not activate it. Pinned/unpinned boundary constraints apply (cannot move unpinned tabs before pinned tabs). Silent failure occurs on invalid moves (returns empty array, no error thrown). — MDN docs confirm no focus side effects.

- Claim (medium): browser.tabs.hide() (Firefox experimental, requires tabHide permission) can hide tabs from the tab strip while their code continues running. However, the currently active tab CANNOT be hidden. This could be useful for managing agent tabs that should not be visible but stay loaded. First use triggers a user notification. — MDN documents the constraint that active tabs cannot be hidden.

- Claim (medium): browser.tabs.warmup() can pre-render an inactive tab for faster visual switching without activating it. This is useful if you know a tab switch is imminent (e.g., agent finishing work). It does not change focus or activation state. — MDN docs describe this as a performance hint only.

- Claim (medium): tabs.moveInSuccession() (Firefox-only) controls which tab becomes active when a tab is closed. This atomically sets successor chains, which is relevant when agent tabs are created/destroyed and you want predictable focus behavior on tab close. — MDN docs describe atomic succession chain manipulation.

- Claim (medium): The tabs.onActivated listener combined with an immediate tabs.update(previousTabId, {active: true}) could theoretically "bounce" focus back to the original tab after an unwanted activation, but this would cause a visible flicker (tab activates then immediately switches back). This is a workaround, not a prevention mechanism. — Inferred from API capabilities; no direct documentation of this pattern.

- Claim (high): Selenium/geckodriver's WebDriver:SwitchToWindow command explicitly waits for "activate" and "focus" events before returning (fixed in Firefox 69, Bug 1335085). This means geckodriver fundamentally requires focus transfer when switching tabs — it is by design, not a bug. There is no Selenium API to switch to a tab without focusing it (feature request #11393 was rejected; maintainers said "that is the nature of how browsers work together with automation"). — Selenium issue #11393 and Mozilla Bug 1335085 confirm this.

- Claim (high): Content scripts declared in manifest.json content_scripts with broad match patterns (e.g., "*://*/*") are automatically injected into ALL matching tabs at load time, including background tabs, without any focus change. This is the most reliable way to ensure every tab gets a content script for visual modifications. — MDN Content scripts documentation confirms automatic injection.

- Claim (medium): The about:config preference browser.tabs.loadDivertedInBackground=true prevents JavaScript-initiated and external links from stealing focus when opened in new tabs. This is a browser-level setting, not a WebExtension API, but could complement extension-based approaches. — Mozilla support forums document this preference.

## Evidence

### Tab Creation Without Focus

- browser.tabs.create({url: "...", active: false}) creates a tab without making it active. The active property "does not affect whether the window is focused (see windows.update). Defaults to true." — [tabs.create() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/create)

- The discarded property allows creating tabs that are not even loaded into memory until activated: browser.tabs.create({url: "...", active: false, discarded: true, title: "Agent Tab"}) — [tabs.create() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/create)

### Script/CSS Execution on Non-Active Tabs

- tabs.executeScript(tabId, {code/file}) can target any tab by ID, not just the active tab. "Defaults to the active tab of the current window" but specifying tabId overrides this. — [tabs.executeScript() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/executeScript)

- scripting.executeScript({target: {tabId: id}, func/files}) in MV3 explicitly targets tabs by ID. Works on non-active tabs with host permissions. Available in Firefox 101+. — [scripting.executeScript() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/scripting/executeScript)

- tabs.insertCSS(tabId, {code: "body {border: 20px dotted pink}"}) works on background tabs. The tabId parameter allows targeting any tab. — [tabs.insertCSS() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/insertCSS)

- scripting.insertCSS({target: {tabId: id}, css: "..."}) is the MV3 equivalent. Requires "scripting" permission + host permissions. — [scripting.insertCSS() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/scripting/insertCSS)

### Tab Update Without Focus Change

- tabs.update(tabId, {url: "..."}): changing a tab's URL does NOT activate it. Only setting active:true activates. "If false, [active] does nothing." — [tabs.update() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/update)

- Firefox-specific: tabs.update(tabId, {highlighted: true, active: false}) highlights without activating. "Other browsers may activate the tab even in this case." — [tabs.update() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/update)

- Known bug: tabs.update() with a URL places cursor focus in the URL bar rather than in the loaded content (Bug 1411465). — [Bugzilla 1411465](https://bugzilla.mozilla.org/show_bug.cgi?id=1411465)

### Tab Activation Cannot Be Prevented

- tabs.onActivated: "Cannot be prevented or cancelled - This is a notification event only." It provides {tabId, windowId, previousTabId} after the fact. — [tabs.onActivated - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/onActivated)

### Tab Movement Without Focus

- tabs.move(tabId, {index: N}) moves tabs positionally without activating them. Index -1 moves to end. Pinned tab boundary rules apply. — [tabs.move() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/move)

### Tab Hiding (Firefox Experimental)

- tabs.hide(tabId) hides tabs from the tab strip. Code continues running. Cannot hide the active tab, pinned tabs, or tabs sharing screen/mic/camera. Requires "tabHide" permission. — [tabs.hide() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/hide)

### Tab Successor Control

- tabs.moveInSuccession([tabId1, tabId2, ...], anchorTabId) atomically sets the successor chain. "All of the succession changes happen atomically, without having to worry about races." — [tabs.moveInSuccession() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/moveInSuccession)

### Selenium Focus Behavior

- Geckodriver's SwitchToWindow explicitly waits for activate+focus events (Bug 1335085, fixed in Firefox 69). "Tab selection operates asynchronously in Firefox." — [Bugzilla 1335085](https://bugzilla.mozilla.org/show_bug.cgi?id=1335085)

- Selenium maintainers rejected the request for silent tab switching: "That is the nature of how browsers work together with automation." Recommended headless mode or Selenium Grid. — [Selenium Issue #11393](https://github.com/SeleniumHQ/selenium/issues/11393)

### Content Scripts Auto-Injection

- Manifest content_scripts with match patterns inject into all matching pages at load time, including background tabs. No focus change occurs from injection. — [Content scripts - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Content_scripts)

## What I'm unsure about

- Whether tabs.hide() is still considered "experimental" in 2026 Firefox or has graduated to stable. The MDN docs marked it experimental; its long-term status in Tor Browser specifically is unclear.

- Whether there is any race condition when using tabs.create({active: false}) immediately followed by tabs.executeScript(newTabId, ...) — the tab may not have finished loading. The tabs.create() promise resolves before the page loads; you may need to listen for tabs.onUpdated with status:"complete" before injecting scripts.

- Whether Tor Browser's hardened Firefox fork imposes additional restrictions on the tabs API (e.g., blocking tabs.hide, limiting tabs.executeScript to same-origin, etc.). Tor Browser often disables or restricts WebExtension APIs for privacy.

- The exact behavior of tabs.executeScript on a discarded tab (created with discarded:true). The tab has no loaded content, so script injection would likely fail until the tab is activated/loaded.

- Whether a WebExtension can intercept and block Selenium/geckodriver's tab-switching focus behavior. Since geckodriver waits for real browser activate/focus events, an extension would need to somehow suppress those events at the platform level, which seems unlikely.

- The interaction between tabs.warmup() and Selenium tab switching — whether pre-warming a tab reduces the visual disruption of a forced focus switch.

- Whether tabs.highlight({tabs: [index], windowId}) with a single tab changes the active tab or just the selection state. MDN says "the first tab in the tabs array will become active," suggesting it always changes focus.

- Performance implications of rapidly injecting CSS via scripting.insertCSS into many tabs simultaneously (e.g., 10 agent tabs all getting color updates).

## Sources

- [tabs.create() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/create)
- [tabs.update() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/update)
- [tabs.executeScript() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/executeScript)
- [scripting.executeScript() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/scripting/executeScript)
- [tabs.insertCSS() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/insertCSS)
- [scripting.insertCSS() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/scripting/insertCSS)
- [tabs.onActivated - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/onActivated)
- [tabs.move() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/move)
- [tabs.hide() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/hide)
- [tabs.warmup() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/warmup)
- [tabs.moveInSuccession() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/moveInSuccession)
- [tabs.highlight() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/highlight)
- [tabs.query() - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/query)
- [tabs API overview - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs)
- [Working with the Tabs API - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Working_with_the_Tabs_API)
- [Content scripts - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Content_scripts)
- [Selenium Issue #11393 - Switch to tab without focusing](https://github.com/SeleniumHQ/selenium/issues/11393)
- [Mozilla Bug 1335085 - SwitchToWindow activate/focus events](https://bugzilla.mozilla.org/show_bug.cgi?id=1335085)
- [Mozilla Bug 1411465 - tabs.update URL bar focus](https://bugzilla.mozilla.org/show_bug.cgi?id=1411465)
- [Bugzilla 1384515 - Tab hiding API](https://bugzilla.mozilla.org/show_bug.cgi?id=1384515)
- [Selenium Focus Stealing on Linux](https://www.selenium.dev/documentation/legacy/selenium_2/focus_stealing/)
- [Geckodriver Issue #906 - DOM events with parallel browsers](https://github.com/mozilla/geckodriver/issues/906)
