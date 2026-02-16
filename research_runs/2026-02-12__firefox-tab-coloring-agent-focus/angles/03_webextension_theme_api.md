# Angle 03 --- WebExtension Theme API

## Claims (with confidence)

- Claim (high): `browser.theme.update(windowId, theme)` supports per-window theming since Firefox 57. The `windowId` parameter is optional; when omitted the theme applies to all windows, when provided it applies only to that specific window. This is confirmed by MDN documentation and multiple Mozilla blog posts. --- [MDN theme.update()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme/update)

- Claim (high): Per-tab theming is NOT supported by the Theme API. The finest granularity is per-window. There is no `browser.theme.update(tabId, theme)` signature. Bug 1320585 ("Allow styling individual tabs") proposed a `browser.tabs.setStyle(tabId, style)` API but it was never implemented. --- [Bugzilla 1320585](https://bugzilla.mozilla.org/show_bug.cgi?id=1320585)

- Claim (high): The `tab_line` color property controls the colored line (accent stripe) on the active/selected tab. It was added to allow independent styling of the tab line that previously inherited from `accentcolor`. Available since approximately Firefox 60 (Bug 1439734). --- [Bugzilla 1439734](https://bugzilla.mozilla.org/show_bug.cgi?id=1439734), [MDN theme manifest](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/theme)

- Claim (high): The `tab_loading` color property controls the color of the tab loading indicator (spinner and burst animation). It can be set to any CSS color value or RGB array. --- [MDN theme manifest](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/theme)

- Claim (high): The `tab_background_text` color property sets the text color of inactive/background tabs. It also serves as the fallback for active tab text if `tab_text` is not defined. It is an alias for the legacy `textcolor` property. Available since Firefox 59. --- [MDN theme manifest](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/theme)

- Claim (high): `tab_selected` controls the background color of the active/selected tab. When not specified, `frame` and `frame_inactive` colors apply instead. Available since approximately Firefox 60. --- [MDN theme manifest](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/theme)

- Claim (high): `tab_text` controls the text color of the selected/active tab. Added in Firefox 59. If `tab_line` is not defined, `tab_text` also determines the tab line color. --- [MDN theme manifest](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/theme)

- Claim (high): Dynamic theme changes are instantaneous -- calling `browser.theme.update()` immediately changes the browser chrome appearance. Firefox is the only browser that supports dynamically updating the theme via the WebExtensions API. --- [Danny Guo: Building Dynamic Firefox Themes](https://www.dannyguo.com/blog/building-dynamic-firefox-themes)

- Claim (high): The standard pattern for simulating per-tab colors is: listen to `browser.tabs.onActivated`, look up the tab's `windowId`, then call `browser.theme.update(windowId, theme)` with a color scheme associated with that tab. This is exactly what extensions like "Adaptive Tab Bar Colour" and "Containers Theme" do. --- [Adaptive Tab Bar Colour](https://github.com/easonwong-de/Adaptive-Tab-Bar-Colour), [Containers Theme](https://addons.mozilla.org/en-US/firefox/addon/containers-theme/)

- Claim (high): `browser.theme.getCurrent(windowId)` retrieves the current theme for a specific window, returning a Promise resolving to a Theme object. If no extension-supplied theme is applied, it resolves to an empty object. --- [MDN theme.getCurrent()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme/getCurrent)

- Claim (high): `browser.theme.reset(windowId)` resets the theme for a specific window (or all windows if windowId is omitted). --- [MDN theme.reset()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme/reset)

- Claim (high): `browser.theme.onUpdated` fires when an extension-supplied theme is applied, updated, or removed. The listener receives an `updateInfo` object containing the `theme` object and the `windowId` of the affected window. --- [MDN theme.onUpdated](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme/onUpdated)

- Claim (medium): The `theme_experiment` manifest key allows mapping custom CSS variables to Firefox internal UI selectors, potentially enabling more granular control than the standard theme properties. However, this is restricted to Firefox Developer Edition and Nightly, and requires the `extensions.experiments.enabled` pref. Custom properties defined via `theme_experiment` can also be used in `browser.theme.update()`. --- [MDN theme_experiment](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/theme_experiment)

- Claim (medium): Firefox container tabs have their own built-in per-tab color indicator (a thin colored line at the top of each tab, using the contextual identity color), which is separate from the Theme API. This is rendered via the `.tab-context-line` CSS element on tabs with the `[usercontextid]` attribute. This is the only native per-tab coloring mechanism in Firefox. --- [Bugzilla 1387117](https://bugzilla.mozilla.org/show_bug.cgi?id=1387117)

- Claim (medium): For our Selenium automation use case (one tab per agent), the most practical approach would be: (a) use one window per agent and apply per-window themes via `browser.theme.update(windowId, theme)`, or (b) use a single window and update the window theme on every tab switch via `tabs.onActivated`, or (c) combine the Theme API's `tab_line`/`tab_selected` colors with container tabs (`contextualIdentities`) to get both a window-wide theme and per-tab color indicators.

## Evidence

### Full Theme API Surface

The `browser.theme` namespace provides four methods and one event:

```
browser.theme.update(windowId?, theme)   -- apply a theme (per-window or global)
browser.theme.reset(windowId?)           -- reset theme (per-window or global)
browser.theme.getCurrent(windowId?)      -- get current theme (per-window or global)
browser.theme.onUpdated                  -- event fired on theme changes
```

Required permission: `"theme"` in manifest.json.

--- [MDN theme API](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme)

### Tab-Related Color Properties (Complete List)

| Property | What It Controls | Firefox Version |
|---|---|---|
| `tab_line` | Colored line/stripe on the active tab | ~60 |
| `tab_loading` | Tab loading spinner and burst animation color | 57+ |
| `tab_background_text` | Text color of inactive tabs (alias for `textcolor`) | 59 |
| `tab_text` | Text color of the selected/active tab | 59 |
| `tab_selected` | Background color of the selected/active tab | ~60 |
| `tab_background_separator` | Vertical separator between background tabs (DEPRECATED since Firefox 89) | 57-89 |

--- [MDN theme manifest](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/theme)

### Other Key Color Properties for Agent Theming

| Property | What It Controls |
|---|---|
| `frame` | Header/chrome background color (mandatory) |
| `frame_inactive` | Header background when window is inactive |
| `toolbar` | Navigation bar, bookmarks bar, selected tab, find bar background |
| `toolbar_text` | Navigation bar text |
| `toolbar_field` | URL bar / search bar background |
| `toolbar_field_text` | URL bar text |
| `toolbar_field_border` | URL bar border |
| `toolbar_field_border_focus` | URL bar border when focused |
| `toolbar_field_focus` | URL bar background when focused |
| `popup` | Popup/dropdown background |
| `popup_text` | Popup text |
| `sidebar` | Sidebar background |
| `sidebar_text` | Sidebar text |
| `ntp_background` | New tab page background |
| `ntp_text` | New tab page text |

--- [MDN theme manifest](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/theme)

### Color Format Support

Colors can be specified as:
- CSS hex strings: `"#CF723F"`
- CSS named colors: `"red"` (Firefox only, not Chrome)
- RGB arrays: `[207, 114, 63]`
- CSS functional notation (Firefox 68.2+): `"rgb(180 240 180 / 90%)"`

--- [MDN theme manifest](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/theme)

### Per-Window Theme Update Example (from MDN)

```javascript
const agentTheme = {
  colors: {
    frame: "#CF723F",           // header/chrome background
    tab_background_text: "#111", // inactive tab text
    tab_line: "#FF0000",         // active tab accent line
    tab_selected: "#FFFFFF",     // active tab background
    tab_text: "#000000",         // active tab text
    toolbar: "#E07030",          // toolbar background
    toolbar_text: "#111111",     // toolbar text
  },
};

async function applyThemeToWindow(windowId) {
  browser.theme.update(windowId, agentTheme);
}

// Apply to current window
let currentWindow = await browser.windows.getLastFocused();
browser.theme.update(currentWindow.id, agentTheme);
```

--- [MDN theme.update()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme/update)

### Per-Tab Simulation Pattern (from real extensions)

```javascript
// Listen for tab switches and update the window theme accordingly
browser.tabs.onActivated.addListener(async (activeInfo) => {
  let tab = await browser.tabs.get(activeInfo.tabId);
  let color = getColorForTab(tab);  // your logic to pick a color
  browser.theme.update(tab.windowId, {
    colors: {
      frame: color,
      tab_background_text: "#FFFFFF",
      tab_line: color,
      toolbar: color,
    }
  });
});
```

This is the pattern used by Adaptive Tab Bar Colour, Containers Theme, Colorize Container Toolbar, and similar extensions. The theme changes are instantaneous but affect the entire window chrome, not individual tab elements.

--- [Adaptive Tab Bar Colour](https://github.com/easonwong-de/Adaptive-Tab-Bar-Colour), [Containers Theme](https://addons.mozilla.org/en-US/firefox/addon/containers-theme/)

### Bug Tracker: Per-Tab Theming Requests

- **Bug 1320585** ("Allow styling individual tabs"): Proposed `browser.tabs.setStyle(tabId, style)` with `text_color`, `background`, `font_style`, `font_weight` fields. Discussion concluded that WebExtension code should NOT set styles directly on tab elements; instead, a set of CSS variables for colors in the theme was considered. Status: the feature was never implemented as a standard API.

- **Bug 1342712** ("Allow browser themes to be scoped to a specific window or active tab"): This bug resulted in the per-window `windowId` parameter being added to `theme.update()` and `theme.reset()`. The per-active-tab scoping part was not implemented as a native API feature.

- **Bug 1439734** ("Allow setting the tab line color"): Resolved -- the `tab_line` color property was added so themes could independently style the active tab's accent line.

--- [Bugzilla 1320585](https://bugzilla.mozilla.org/show_bug.cgi?id=1320585), [Bugzilla 1342712](https://bugzilla.mozilla.org/show_bug.cgi?id=1342712), [Bugzilla 1439734](https://bugzilla.mozilla.org/show_bug.cgi?id=1439734)

### Container Tabs: Native Per-Tab Color Indicators

Firefox container tabs (contextual identities) provide a thin colored line at the top of each tab (`.tab-context-line` element), colored according to the container's assigned color. This is the only built-in mechanism for per-tab visual differentiation in the tab strip. The color moved from the bottom to the top of the tab in Firefox 89 (Proton redesign). The container indicator is separate from the Theme API -- it uses the contextualIdentities system.

--- [Bugzilla 1387117](https://bugzilla.mozilla.org/show_bug.cgi?id=1387117), [Bugzilla 1325057](https://bugzilla.mozilla.org/show_bug.cgi?id=1325057)

### Real-World Extensions Using Dynamic Themes

| Extension | Technique |
|---|---|
| **Adaptive Tab Bar Colour** | Reads website theme-color/meta tag, calls `theme.update(windowId)` on every tab switch |
| **Containers Theme** | Sets window theme to match the active container tab's color |
| **Colorize Container Toolbar** | Colors toolbar based on active container tab |
| **Chromatastic** | Continuously cycles rainbow colors via `setInterval` + `theme.update()` |
| **Color Tailor** | Reads website primary color and applies it to chrome |
| **Firefox Color** | Mozilla's own theme editor, uses the Theme API |

--- [Adaptive Tab Bar Colour](https://addons.mozilla.org/en-US/firefox/addon/adaptive-tab-bar-colour/), [Colorize Tabs](https://addons.mozilla.org/en-US/firefox/addon/colorize-tabs/), [Chromatastic](https://github.com/dguo/chromatastic), [Firefox Color](https://color.firefox.com/)

## What I'm unsure about

- **Tor Browser compatibility**: No specific documentation found on whether Tor Browser restricts or modifies the `browser.theme` API. Tor Browser is based on Firefox ESR and may disable or restrict extension APIs for fingerprinting/privacy reasons. The theme API could potentially be restricted since it could be used to detect extension presence. This needs direct testing.

- **Performance of rapid theme.update() calls**: When switching tabs rapidly, calling `browser.theme.update()` on every `tabs.onActivated` event could potentially cause visual flickering or performance issues. The Adaptive Tab Bar Colour extension notes that "smooth colour transitions for the tab bar are not natively supported" and requires userChrome.css workarounds for smooth transitions. The exact overhead of frequent `theme.update()` calls is not documented.

- **Interaction with Selenium WebDriver**: It is unclear how the Theme API interacts with Selenium-controlled browser sessions. Since `browser.theme.update()` is a WebExtension API, it would need to be called from within an installed extension, not directly from Selenium. The extension would need to be pre-loaded or installed programmatically. Alternatively, the extension could expose a messaging interface that Selenium-injected content scripts communicate with.

- **Multiple extensions competing for theme control**: The MDN docs note that only one extension can control the theme at a time. If another theme extension is installed, there may be conflicts. The `theme.onUpdated` event fires when themes change, but conflict resolution behavior is not well-documented.

- **Whether `tab_line` visually persists on inactive tabs**: The `tab_line` property appears to only affect the selected/active tab line. It is unclear if there is any Theme API property that can color the line/indicator on inactive tabs (which would be more useful for our per-agent-tab-coloring use case).

- **Exact Firefox version requirements for each property**: While I've documented approximate versions, the exact Firefox ESR version that Tor Browser is based on determines which properties are actually available. Most tab-related properties require Firefox 59-60+, which should be available in all modern Tor Browser versions.

- **Whether `theme_experiment` could enable true per-tab styling**: The `theme_experiment` key allows mapping custom CSS variables to internal Firefox UI selectors. In theory, one could target individual tab elements via their internal CSS selectors. However, this is restricted to Developer Edition/Nightly and may not be usable in production or Tor Browser.

## Sources

- [MDN: browser.theme.update()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme/update)
- [MDN: theme manifest.json](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/theme)
- [MDN: browser.theme API](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme)
- [MDN: browser.theme.getCurrent()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme/getCurrent)
- [MDN: browser.theme.reset()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme/reset)
- [MDN: theme.onUpdated](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme/onUpdated)
- [MDN: theme_experiment](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/theme_experiment)
- [Mozilla Hacks: Using the new theming API in Firefox](https://hacks.mozilla.org/2017/12/using-the-new-theming-api-in-firefox/)
- [Mozilla Add-ons Blog: Theme API Update (March 2018)](https://blog.mozilla.org/addons/2018/03/08/theme-api-update/)
- [Firefox Extension Workshop: Dynamic Themes](https://extensionworkshop.com/documentation/themes/dynamic-themes/)
- [Danny Guo: Building Dynamic Firefox Themes](https://www.dannyguo.com/blog/building-dynamic-firefox-themes)
- [Bugzilla 1320585: Allow styling individual tabs](https://bugzilla.mozilla.org/show_bug.cgi?id=1320585)
- [Bugzilla 1342712: Allow browser themes to be scoped to a specific window or active tab](https://bugzilla.mozilla.org/show_bug.cgi?id=1342712)
- [Bugzilla 1439734: Allow setting the tab line color](https://bugzilla.mozilla.org/show_bug.cgi?id=1439734)
- [Bugzilla 1387117: Container color indicator visibility](https://bugzilla.mozilla.org/show_bug.cgi?id=1387117)
- [Bugzilla 1325057: Contextual identities custom colors](https://bugzilla.mozilla.org/show_bug.cgi?id=1325057)
- [GitHub: Adaptive Tab Bar Colour](https://github.com/easonwong-de/Adaptive-Tab-Bar-Colour)
- [GitHub: Chromatastic](https://github.com/dguo/chromatastic)
- [GitHub: Color Tailor](https://github.com/dguo/color-tailor)
- [AMO: Adaptive Tab Bar Colour](https://addons.mozilla.org/en-US/firefox/addon/adaptive-tab-bar-colour/)
- [AMO: Containers Theme](https://addons.mozilla.org/en-US/firefox/addon/containers-theme/)
- [AMO: Colorize Container Toolbar](https://addons.mozilla.org/en-US/firefox/addon/colorize-container-toolbar/)
- [AMO: Colorize Tabs](https://addons.mozilla.org/en-US/firefox/addon/colorize-tabs/)
- [Firefox Color](https://color.firefox.com/)
