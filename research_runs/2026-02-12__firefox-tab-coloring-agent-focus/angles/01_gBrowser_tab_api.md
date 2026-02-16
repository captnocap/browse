# Angle 01 — Firefox gBrowser Tab API

## Claims (with confidence)

- Claim (high): **gBrowser.addTab() accepts an `inBackground` parameter (default `true`) that prevents the newly created tab from being selected/focused.** When `inBackground` is not `false`, the code path `this.selectedTab = t` is never reached, so the tab opens adjacent to the active tab without switching to it. This is the primary mechanism for preventing focus hopping during tab creation. — Source: tabbrowser.js on searchfox.org, confirmed by the addTab implementation which shows `if (!inBackground) { this.selectedTab = t; }`.

- Claim (high): **Tab elements are standard DOM nodes (`tabbrowser-tab` custom elements) that fully support `setAttribute()`, `removeAttribute()`, and `hasAttribute()`.** The `MozTabbrowserTab` class extends `MozElements.MozTab` and is registered via `customElements.define('tabbrowser-tab', MozTabbrowserTab, {})` in `browser/components/tabbrowser/content/tab.js`. Any custom attribute set on a tab element can be targeted by CSS attribute selectors in userChrome.css (e.g., `.tabbrowser-tab[data-agent="3"] .tab-background { background: red; }`).

- Claim (high): **The `selectedTab` setter on gBrowser assigns `this.tabbox.selectedTab = val`, which triggers the visual tab switch and focus change.** Setting attributes on a tab (e.g., `tab.setAttribute('data-agent', '3')`) does NOT trigger the `selectedTab` setter and therefore does NOT cause focus hopping. Only explicit assignment to `gBrowser.selectedTab` or equivalent methods cause the selected tab to change.

- Claim (high): **`gBrowser.getTabForBrowser(aBrowser)` returns the tab element associated with a given browser element, using an internal WeakMap (`_tabForBrowser`).** This is the correct way to find which tab corresponds to a Selenium-controlled browser instance. The reverse mapping is `tab.linkedBrowser`, which returns the `<browser>` element embedded in the tab.

- Claim (high): **Selenium/geckodriver provides `driver.set_context('chrome')` (or the context manager `driver.context(driver.CONTEXT_CHROME)`) to switch command execution from content scope to chrome scope.** In chrome scope, `execute_script()` can access `gBrowser`, `document` (the chrome document), and all other privileged Firefox objects. This is the mechanism to run tab-manipulation JavaScript from a Selenium automation session.

- Claim (high): **The `_tabAttrModified(aTab, aChanged)` method dispatches a `TabAttrModified` CustomEvent on the tab element, with `detail.changed` containing an array of attribute names that changed.** This is an internal notification mechanism and does not affect focus or selection. Setting custom attributes and calling `_tabAttrModified` is safe for UI updates.

- Claim (high): **Firefox's tab internal DOM structure (defined in `MozTabbrowserTab.markup`) uses `inheritedAttributes` to propagate attributes from the `tabbrowser-tab` element to child elements like `.tab-background`, `.tab-content`, `.tab-label`, etc.** The inheritedAttributes static getter maps selectors to attribute lists, e.g., `.tab-background` inherits `selected=visuallyselected,fadein,multiselected,dragover-groupTarget`. Custom attributes NOT in this mapping must be targeted on the parent `.tabbrowser-tab` element in CSS, then descend to children via normal CSS combinators.

- Claim (medium): **The `addTab()` method accepts ~40 named options**, including: `inBackground` (default true), `skipAnimation`, `skipBackgroundNotify`, `noInitialLabel`, `pinned`, `userContextId`, `focusUrlBar`, `createLazyBrowser`, `elementIndex`, `tabIndex`, `tabGroup`, `insertTab`, `bulkOrderedOpen`, `relatedToCurrent`, and many security-related principals. The most relevant for our use case are `inBackground`, `skipAnimation`, and `userContextId`.

- Claim (medium): **Firefox's contextual identity (container tabs) system already implements per-tab coloring via the `usercontextid` attribute and `--identity-tab-color` CSS variable.** The `.tab-context-line` element displays a colored accent line at the top of container tabs. This proves that the Firefox architecture supports per-tab visual differentiation via attributes + CSS, and our agent coloring can follow the same pattern.

- Claim (medium): **Setting a custom attribute on a `tabbrowser-tab` element from chrome context and targeting it in userChrome.css is a well-established pattern used by extensions like Private_Tab and userChromeJS scripts.** The typical flow is: JavaScript sets `tab.setAttribute('customattr', 'value')` from chrome-privileged code, then `userChrome.css` targets it with `.tabbrowser-tab[customattr="value"] .tab-background { ... }`.

- Claim (medium): **From Selenium, accessing gBrowser in chrome context works like this:**
  ```python
  with driver.context(driver.CONTEXT_CHROME):
      driver.execute_script("""
          let tabs = gBrowser.tabs;
          tabs[2].setAttribute('data-agent', '3');
      """)
  ```
  This does NOT switch focus because we are only modifying DOM attributes on the tab element, not assigning to `gBrowser.selectedTab`.

- Claim (medium): **`gBrowser.tabs` is a live NodeList of all `tabbrowser-tab` elements in the tab strip.** You can iterate it with `for...of`, index into it with `gBrowser.tabs[i]`, or use `.length`. Each element is a full DOM `MozTabbrowserTab` instance supporting all standard DOM methods.

- Claim (low): **Direct inline `style` manipulation (`tab.style.setProperty('--agent-color', '#ff0000')`) may be an alternative to attributes + userChrome.css.** This would set a CSS custom property directly on the tab element, which child elements could reference via `var(--agent-color)`. However, this approach bypasses the `_tabAttrModified` event system, and it is unclear whether Firefox's tab rendering pipeline honors inline style custom properties on XUL elements consistently.

- Claim (low): **The `_createTab` method (around line 3910-3920 in tabbrowser.js) creates tabs via `document.createXULElement('tab', { is: 'tabbrowser-tab' })`.** It then sets initial attributes including `fadein`, `label`, `crop`, and `usercontextid` (if provided). Custom attributes could potentially be injected at creation time by calling addTab from chrome context, but post-creation setAttribute is simpler and equally effective.

## Evidence

- **addTab implementation with inBackground parameter**: The full parameter list was extracted from the tabbrowser.js source, showing `inBackground = true` as the default, and the conditional `if (!inBackground) { this.selectedTab = t; }` — [tabbrowser.js on Searchfox](https://searchfox.org/mozilla-central/source/browser/components/tabbrowser/content/tabbrowser.js)

- **MozTabbrowserTab class definition**: Class extends `MozElements.MozTab`, registered via `customElements.define("tabbrowser-tab", MozTabbrowserTab, {})` in tab.js. Includes `inheritedAttributes` static getter mapping attributes to child element selectors. — [tab.js on Searchfox](https://searchfox.org/mozilla-central/source/browser/components/tabbrowser/content/tab.js)

- **selectedTab getter/setter**: Getter returns `this._selectedTab`, setter checks for modal windows and sets `this.tabbox.selectedTab = val`. — [tabbrowser.js on Searchfox](https://searchfox.org/mozilla-central/source/browser/components/tabbrowser/content/tabbrowser.js)

- **getTabForBrowser uses WeakMap**: `_tabForBrowser = new WeakMap()` stores browser-to-tab mappings; `getTabForBrowser(aBrowser) { return this._tabForBrowser.get(aBrowser); }` — [tabbrowser.js on Searchfox](https://searchfox.org/mozilla-central/source/browser/components/tabbrowser/content/tabbrowser.js)

- **_tabAttrModified dispatches CustomEvent**: `new CustomEvent("TabAttrModified", { bubbles: true, cancelable: false, detail: { changed: aChanged } })` — [tabbrowser.js on Searchfox](https://searchfox.org/mozilla-central/source/browser/components/tabbrowser/content/tabbrowser.js)

- **Selenium's set_context API**: `set_context(context) -> None` with constants `CONTEXT_CHROME = 'chrome'` and `CONTEXT_CONTENT = 'content'`. Context manager: `with driver.context(driver.CONTEXT_CHROME):` — [Selenium Python API Docs](https://www.selenium.dev/selenium/docs/api/py/selenium_webdriver_firefox/selenium.webdriver.firefox.webdriver.html)

- **Marionette's using_context**: `with marionette.using_context(marionette.CONTEXT_CHROME):` provides equivalent chrome access. `execute_script()` in chrome context can use `window.wrappedJSObject` for full access. — [Marionette Driver Docs](https://firefox-source-docs.mozilla.org/python/marionette_driver.html)

- **Container tab coloring as precedent**: `.tabbrowser-tab[usercontextid] .tab-context-line` uses `--identity-tab-color` CSS variable. The `usercontextid` attribute is set on the tab element, and CSS in the browser chrome styles the accent line accordingly. — [MDN contextualIdentities](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/contextualIdentities)

- **userChrome.css attribute selectors work on tabbrowser-tab**: Confirmed by multiple Firefox community examples targeting `.tabbrowser-tab[selected]`, `.tabbrowser-tab[pinned]`, `.tabbrowser-tab[usercontextid]`. Custom attributes follow the same pattern. — [Mozilla Support Forum](https://support.mozilla.org/en-US/questions/1446142)

- **Tab markup structure**: `MozTabbrowserTab.markup` defines the shadow content as `<stack class="tab-stack"><vbox class="tab-background"><hbox class="tab-context-line"/><hbox class="tab-loading-burst"/><hbox class="tab-group-line"/></vbox><hbox class="tab-content">...</hbox></stack>` — [tab.js on Searchfox](https://searchfox.org/mozilla-central/source/browser/components/tabbrowser/content/tab.js)

- **Firefox 119+ changed pseudo-boolean attributes to real booleans**: Selectors must use `[selected]` not `[selected="true"]`. Custom attributes should follow the same pattern for forward compatibility. — [Mozilla Support Forum](https://support.mozilla.org/en-US/questions/1446142)

- **Bug 1475606 confirms addTab options object pattern**: The modern addTab API uses a single options object rather than positional parameters. `inBackground` was added/formalized in this refactor. — [Bugzilla 1475606](https://bugzilla.mozilla.org/show_bug.cgi?id=1475606)

## Key API Reference

### gBrowser Core Methods

```javascript
// Add a tab without switching to it (inBackground defaults to true)
let tab = gBrowser.addTab("about:blank", {
    inBackground: true,        // do NOT switch to this tab
    skipAnimation: true,       // skip opening animation
    triggeringPrincipal: Services.scriptSecurityManager.getSystemPrincipal()
});

// Get/set the selected tab (CAUSES focus change)
gBrowser.selectedTab = someTab;    // switches to tab
let current = gBrowser.selectedTab; // gets current tab

// Map between tabs and browsers
let browser = tab.linkedBrowser;              // tab -> browser
let tab = gBrowser.getTabForBrowser(browser); // browser -> tab
let browser = gBrowser.selectedBrowser;       // shortcut for selectedTab.linkedBrowser
let browser = gBrowser.getBrowserForTab(tab); // equivalent to tab.linkedBrowser

// Iterate all tabs
for (let tab of gBrowser.tabs) {
    tab.setAttribute('data-agent', 'none');
}

// Access specific tab by index
let thirdTab = gBrowser.tabs[2];
```

### Tab Attribute Manipulation (NO focus change)

```javascript
// Set a custom attribute on a specific tab
tab.setAttribute('data-agent-id', '3');
tab.setAttribute('data-agent-color', '#ff6600');
tab.setAttribute('data-agent-active', '');  // boolean attribute

// Remove attribute
tab.removeAttribute('data-agent-active');

// Query attributes
tab.hasAttribute('data-agent-id');  // true/false
tab.getAttribute('data-agent-id');  // '3'

// Set inline CSS custom property
tab.style.setProperty('--agent-color', '#ff6600');
```

### Selenium Chrome Context Pattern

```python
from selenium.webdriver.firefox.webdriver import WebDriver

driver: WebDriver  # already connected

# Approach 1: context manager (recommended)
with driver.context(driver.CONTEXT_CHROME):
    driver.execute_script("""
        // Find the tab for a specific browser by index
        let tab = gBrowser.tabs[arguments[0]];
        tab.setAttribute('data-agent-id', arguments[1]);
        tab.setAttribute('data-agent-color', arguments[2]);
    """, tab_index, agent_id, agent_color)

# Approach 2: explicit set_context
driver.set_context('chrome')
driver.execute_script("""
    for (let tab of gBrowser.tabs) {
        tab.removeAttribute('data-agent-active');
    }
    gBrowser.tabs[arguments[0]].setAttribute('data-agent-active', '');
""", active_tab_index)
driver.set_context('content')  # IMPORTANT: switch back
```

### userChrome.css Rules for Agent Tab Coloring

```css
/* Agent-specific tab background coloring */
.tabbrowser-tab[data-agent-id="1"] .tab-background {
    background: rgba(255, 100, 100, 0.3) !important;
}
.tabbrowser-tab[data-agent-id="2"] .tab-background {
    background: rgba(100, 255, 100, 0.3) !important;
}
.tabbrowser-tab[data-agent-id="3"] .tab-background {
    background: rgba(100, 100, 255, 0.3) !important;
}

/* Active agent indicator (pulsing accent line, similar to container tabs) */
.tabbrowser-tab[data-agent-active] .tab-context-line {
    display: block !important;
    background-color: var(--agent-color, #ff6600) !important;
    opacity: 1 !important;
    height: 3px !important;
}

/* Alternative: use inline CSS custom property */
.tabbrowser-tab[data-agent-id] .tab-background {
    background: color-mix(in srgb, var(--agent-color, transparent) 25%, transparent) !important;
}
```

## What I am unsure about

- **Whether inline `style.setProperty()` on tabbrowser-tab elements reliably propagates CSS custom properties to child elements in all Firefox rendering modes.** XUL elements have historically had quirks with CSS custom properties. Attribute-based selectors in userChrome.css are the safer bet, but inline custom properties would be more flexible (no need to pre-define colors in CSS).

- **The exact behavior of `gBrowser.getTabForBrowser()` when called with the Selenium-controlled browser element from chrome context.** In theory, each Selenium session controls one browser, and `driver.execute_script('return gBrowser.selectedBrowser', context='chrome')` should return the browser element for the *currently active tab in that window* (not necessarily the tab Selenium is controlling). Mapping a specific Selenium driver instance to its tab may require storing the tab index or browser reference at connection time.

- **Whether calling `tab.setAttribute()` from chrome context triggers any side effects in Firefox's tab management code** beyond the CSS update. The `_tabAttrModified` method only fires when called explicitly by tabbrowser code, so setting arbitrary custom attributes should not trigger it. But MutationObservers or other internal listeners might react.

- **Race conditions when multiple Selenium drivers simultaneously execute chrome-context scripts.** If multiple agents connect to the same Firefox instance and each calls `execute_script` in chrome context, these calls go through Marionette which serializes commands per connection. But if multiple geckodriver instances share the same Firefox process, the chrome context operations may interleave unpredictably.

- **Whether the `tab.group` property and the newer tab grouping features (2024-2025) affect attribute inheritance or CSS targeting.** The `MozTabbrowserTab` code shows `get group() { return this.closest("tab-group"); }` which suggests tabs can be wrapped in group elements, potentially affecting CSS selector specificity.

- **Whether Tor Browser (which is based on Firefox ESR) has the same `set_context` support and gBrowser API surface.** Tor Browser applies security patches that might restrict chrome context access or disable certain Marionette features. Testing is needed.

- **The full list of built-in attributes that Firefox sets on tabbrowser-tab elements.** From source analysis, known attributes include: `selected`, `visuallyselected`, `fadein`, `pinned`, `pending`, `busy`, `multiselected`, `usercontextid`, `label`, `crop`, `attention`, `titlechanged`, `soundplaying`, `muted`, `sharing`, `pictureinpicture`, `notselectedsinceload`, `dragover-groupTarget`. Custom attributes should use a `data-` prefix to avoid collisions.

## Sources

- [Firefox tabbrowser Source Docs](https://firefox-source-docs.mozilla.org/browser/base/tabbrowser/index.html)
- [tabbrowser.js on Searchfox (mozilla-central)](https://searchfox.org/mozilla-central/source/browser/components/tabbrowser/content/tabbrowser.js)
- [tab.js on Searchfox (MozTabbrowserTab class)](https://searchfox.org/mozilla-central/source/browser/components/tabbrowser/content/tab.js)
- [Searchfox: tabbrowser directory listing](https://searchfox.org/mozilla-central/source/browser/components/tabbrowser/content)
- [Bug 1475606 - Extend addTab to allow selecting a tab](https://bugzilla.mozilla.org/show_bug.cgi?id=1475606)
- [Bug 1297157 - Abstract away visuallyselected attribute](https://bugzilla.mozilla.org/show_bug.cgi?id=1297157)
- [Bug 1171245 - Include changed attributes in TabAttrModified event](https://bugzilla.mozilla.org/show_bug.cgi?id=1171245)
- [Bug 1111276 - Replace selectedTab.linkedBrowser with selectedBrowser](https://bugzilla.mozilla.org/show_bug.cgi?id=1111276)
- [Selenium Python API: Firefox WebDriver](https://www.selenium.dev/selenium/docs/api/py/selenium_webdriver_firefox/selenium.webdriver.firefox.webdriver.html)
- [Marionette Driver Package Docs](https://firefox-source-docs.mozilla.org/python/marionette_driver.html)
- [Introduction to Marionette](https://firefox-source-docs.mozilla.org/testing/marionette/Intro.html)
- [MDN: contextualIdentities API](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/contextualIdentities)
- [MDN: Work with contextual identities](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Work_with_contextual_identities)
- [MDN: tabs API](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs)
- [Mozilla Support: userChrome.css Tab Customization (part 2)](https://support.mozilla.org/en-US/questions/1446142)
- [Mozilla Support: userChrome.css changing active tab colour](https://support.mozilla.org/en-US/questions/1282095)
- [Firefox 89 Proton UI Tab Styling (Raymii.org)](https://raymii.org/s/blog/Firefox-89-proton-ui-tab-styling.html)
- [Tabbed Browser Archive - MDN](https://udn.realityripple.com/docs/Archive/Add-ons/Tabbed_browser)
- [Marcos Caceres: Gecko gBrowser and tabs](https://marcosc.com/2015/01/gecko-gbrowser-and-tabs/)
- [Intoli: JavaScript Injection with Selenium and Marionette](https://intoli.com/blog/javascript-injection/)
- [Private_Tab Extension (example of tab attribute manipulation)](https://github.com/Infocatcher/Private_Tab)
- [Bug 487242 - userChrome.css tab state differentiation regression](https://bugzilla.mozilla.org/show_bug.cgi?id=487242)
- [Bug 1387117 - Container color indicator visibility](https://bugzilla.mozilla.org/show_bug.cgi?id=1387117)
- [geckodriver Issue #740 - Actions in chrome context](https://github.com/mozilla/geckodriver/issues/740)
