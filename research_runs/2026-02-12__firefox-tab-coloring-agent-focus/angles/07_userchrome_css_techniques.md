# Angle 07 — Firefox userChrome.css Techniques

## Claims (with confidence)

- Claim (high): Firefox's `tabbrowser-tab` XUL element exposes multiple native attributes that can be targeted with CSS attribute selectors in userChrome.css, including `selected`, `pinned`, `busy`, `pending`, `unread`, `soundplaying`, `usercontextid`, and `fadein`. Since Firefox 119, pseudo-boolean attributes like `selected` and `pinned` became real boolean attributes, so selectors must use `[selected]` instead of `[selected="true"]`. Evidence: Mozilla Support forums, Bugzilla, and multiple userChrome.css community sources confirm this.

- Claim (high): Custom attributes can be set on `tabbrowser-tab` DOM elements via privileged JavaScript (autoconfig/userChrome.js), and then targeted by CSS selectors in userChrome.css. The pattern is: use `tab.setAttribute('myattr', 'value')` in chrome-context JS, then style with `.tabbrowser-tab[myattr="value"] .tab-background { ... }` in userChrome.css. Evidence: userchrome.org documentation on autoconfig scripting, fx-autoconfig project, and Bugzilla bug 487242 discussing the `visited` attribute pattern.

- Claim (high): The `@supports -moz-bool-pref("preference.name")` conditional is available exclusively in Gecko chrome stylesheets (like userChrome.css) and allows conditional CSS blocks based on about:config boolean preferences. You can define arbitrary custom prefs (e.g., `userChrome.agent.colorTabs`) and gate styling on them. Supports `and`, `or`, and `not` operators. Evidence: Mozilla's archived `-moz-bool-pref` documentation at udn.realityripple.com, and the firefox-gnome-theme project issue #137 discussing this approach.

- Claim (high): Firefox container tabs use the `usercontextid` attribute on `tabbrowser-tab` elements and expose the `--identity-tab-color` CSS custom property, which holds the container's assigned color. The `.tab-context-line` element renders the colored strip above container tabs. You can amplify container coloring with rules like `.tabbrowser-tab[usercontextid] .tab-background { background-color: color-mix(in srgb, var(--identity-tab-color) 20%, transparent) !important; }`. Evidence: dangh's GitHub gist for prominent container tab colors, Bugzilla bug 1325057, and multiple userChrome.css examples.

- Claim (high): Selenium's Firefox WebDriver (geckodriver/Marionette) supports a `set_context("chrome")` method that switches execute_script into the browser's privileged chrome context, giving access to `gBrowser`, `document`, and all XUL DOM APIs. This means you can call `gBrowser.tabs[i].setAttribute(...)` from Selenium Python code. Evidence: Selenium Python API docs, Firefox Marionette source documentation.

- Claim (medium): The Proton-era (Firefox 89+) tab DOM structure follows the hierarchy: `.tabbrowser-tab > .tab-stack > .tab-background` (with `.tab-context-line` for containers) and `.tabbrowser-tab > .tab-stack > .tab-content > .tab-label` (for text). The `.tab-background` is the primary target for coloring individual tabs. Evidence: Raymii.org Firefox 89 Proton article, multiple GitHub gists, and MrOtherGuy's firefox-csshacks collection.

- Claim (medium): The `label` attribute on `tabbrowser-tab` elements reflects the page title, enabling CSS attribute substring selectors like `.tabbrowser-tab[label*="GitHub"]` to target tabs by their displayed title. However, this is fragile since titles change with page content. Evidence: copyprogramming.com discussion and Mozilla support forum posts about domain-specific tab coloring.

- Claim (medium): Tree Style Tab (TST) exposes a custom CSS injection point ("Extra style rules" in Advanced options) and provides CSS custom properties like `--theme-colors-tab_background_text-30` (with opacity suffixes). The companion extension "[TST] Colorize Tabs" allows manual per-tab coloring via keyboard shortcuts (Alt+1 through Alt+7 for preset colors). Sidebery similarly supports per-domain automatic tab coloring and custom CSS variable overrides. Evidence: TST wiki on GitHub, TST Colorize Tabs addon page, Sidebery wiki.

- Claim (medium): For Tor Browser, userChrome.css technically works if `toolkit.legacyUserProfileCustomizations.stylesheets` is set to `true` in about:config, but the Tor Project officially discourages this because any UI customization can create a unique browser fingerprint that compromises anonymity. There is no hard technical block, but Tor-specific profiles may not have this pref enabled by default. Evidence: Tor Project GitLab issue #25467, Tor Project forum discussion on safe customization.

- Claim (medium): The MrOtherGuy fx-autoconfig loader is the most maintained approach for running privileged JavaScript in Firefox's chrome context. It works by placing a config.js in the Firefox program directory and JS scripts in the profile's chrome folder. The aminomancer/uc.css.js project builds on fx-autoconfig and demonstrates setting custom attributes on root/tab elements (e.g., `:root[vertical-tabs]`) that are then styled via userChrome.css. Evidence: GitHub repos for fx-autoconfig and uc.css.js.

- Claim (low): It may be possible to use Selenium's Marionette chrome context to dynamically set per-tab custom attributes (e.g., `data-agent-id="agent-3"`) on `tabbrowser-tab` elements, then have a pre-loaded userChrome.css that styles those attributes with distinct colors. This would create a live, dynamic per-tab coloring system driven by automation code. No direct example of this exact pattern was found, but each individual component (Marionette chrome context, setAttribute on tabs, CSS attribute selectors in userChrome.css) is well-documented independently.

## Evidence

### Tab DOM Structure and Native Attributes
- Firefox's `tabbrowser-tab` XUL element is the fundamental tab unit. Each tab has attributes: `selected` (boolean, active tab), `pinned` (boolean), `busy` (loading), `pending` (unloaded/discarded), `unread`, `soundplaying`/`muted`, `usercontextid` (container ID), `fadein` (animation state), `label` (page title), `image` (favicon URL), `linkedpanel` (associated panel ID). -- [Mozilla Support: userChrome.css Help With Customizing Tabs](https://support.mozilla.org/en-US/questions/1446142)
- Since Firefox 119, tab attributes changed from pseudo-boolean strings (`selected="true"`) to real boolean attributes. Use `[selected]` not `[selected="true"]`. -- [Mozilla Support: userChrome.css Help With Customizing Tabs part 2](https://support.mozilla.org/en-US/questions/1446142)
- Proton tab DOM hierarchy: `.tabbrowser-tab > .tab-stack > .tab-background` and `.tabbrowser-tab > .tab-stack > .tab-content > .tab-label`. The `.tab-context-line` sits inside `.tab-background` for container tabs. -- [Raymii.org: Firefox 89 Proton UI Tab Styling](https://raymii.org/s/blog/Firefox-89-proton-ui-tab-styling.html)

### CSS Attribute Selectors for Per-Tab Coloring
- Basic active tab coloring: `.tabbrowser-tab[selected] .tab-background { background-color: #cff !important; background-image: none !important; }` -- [Mozilla Support: Changing Active Tab Colour](https://support.mozilla.org/en-US/questions/1282095)
- Container tab coloring via `usercontextid`: `.tabbrowser-tab[usercontextid] .tab-background { border-top: 3px solid var(--identity-tab-color); }` -- [Gist: Prominent tab color for Firefox container](https://gist.github.com/dangh/25315d954898f20a76a0d9b6f14c9b4d)
- Title-based targeting: `.tabbrowser-tab[label*="Hacker News"] .tab-background { background-color: #FF6600 !important; }` -- [CopyProgramming: Auto color of tabs based on URL/domain](https://copyprogramming.com/howto/auto-color-of-tabs-in-firefox-based-on-url-domain)
- Audio-playing tab: `.tabbrowser-tab[soundplaying] .tab-background { background-color: rgba(0,128,0,0.2) !important; }` -- [Mozilla Support: Tabs highlighted when playing audio](https://support.mozilla.org/en-US/questions/1429001)

### Custom Attributes via Privileged JavaScript
- The autoconfig (userChrome.js) mechanism allows running privileged JS at Firefox startup. Setup: place a `.js` file in `<firefox-install>/defaults/pref/` that points to a config file, which in turn loads scripts with chrome privileges. -- [userchrome.org: What is Autoconfig Startup Scripting](https://www.userchrome.org/what-is-userchrome-js.html)
- MrOtherGuy's fx-autoconfig is the modern loader: scripts placed in `<profile>/chrome/JS/` run in chrome context with access to `gBrowser`, `document`, and all XUL APIs. -- [GitHub: MrOtherGuy/fx-autoconfig](https://github.com/MrOtherGuy/fx-autoconfig)
- Pattern for custom attributes: In chrome JS, `gBrowser.tabs[i].setAttribute('data-agent', 'agent-1')`. In userChrome.css, `.tabbrowser-tab[data-agent="agent-1"] .tab-background { background-color: #e74c3c !important; }`. The Bugzilla bug 487242 discusses this exact pattern with the `visited` attribute. -- [Bugzilla: Bug 487242](https://bugzilla.mozilla.org/show_bug.cgi?id=487242)
- The aminomancer/uc.css.js project extensively uses this pattern, setting attributes like `vertical-tabs` on `:root` and styling with `:root[vertical-tabs] #TabsToolbar { ... }`. -- [GitHub: aminomancer/uc.css.js](https://github.com/aminomancer/uc.css.js/)

### -moz-bool-pref() Conditional CSS
- `@supports -moz-bool-pref("pref.name") { ... }` evaluates to true if the named about:config boolean preference is true. Only works in Gecko chrome stylesheets. Supports `and`, `or`, `not` operators. -- [Mozilla Docs: CSS -moz-bool-pref()](http://udn.realityripple.com/docs/Mozilla/Gecko/Chrome/CSS/-moz-bool-pref)
- Practical use: define `userChrome.tabs.agentColoring` as a boolean pref, then `@supports -moz-bool-pref("userChrome.tabs.agentColoring") { .tabbrowser-tab[data-agent] .tab-background { ... } }` to enable/disable the feature. -- Derived from [firefox-gnome-theme issue #137](https://github.com/rafaelmardojai/firefox-gnome-theme/issues/137)

### Selenium/Marionette Chrome Context Access
- Selenium Firefox WebDriver exposes `set_context(context)` where context is `CONTEXT_CHROME` or `CONTEXT_CONTENT`. In chrome context, `execute_script` has access to `gBrowser`, `document`, and privileged APIs. -- [Selenium Python API: Firefox WebDriver](https://www.selenium.dev/selenium/docs/api/py/selenium_webdriver_firefox/selenium.webdriver.firefox.webdriver.html)
- Usage pattern: `driver.set_context(driver.CONTEXT_CHROME)` then `driver.execute_script("gBrowser.selectedTab.setAttribute('data-agent', 'agent-1')")`. Context can be restored with `driver.set_context(driver.CONTEXT_CONTENT)`. -- [Firefox Source Docs: Marionette](https://firefox-source-docs.mozilla.org/testing/marionette/Intro.html)
- Alternative: `with driver.context(driver.CONTEXT_CHROME): driver.execute_script(...)` for scoped chrome access. -- [Selenium docs](https://www.selenium.dev/selenium/docs/api/py/selenium_webdriver_firefox/selenium.webdriver.firefox.webdriver.html)

### Tree Style Tab and Sidebery Extension Approaches
- TST provides "Extra style rules" text field in Advanced options for custom CSS. Uses CSS custom properties with opacity suffixes: `--theme-colors-tab_background_text-30` = text color at 30% opacity. -- [GitHub: TST Code Snippets Wiki](https://github.com/piroor/treestyletab/wiki/Code-snippets-for-custom-style-rules)
- "[TST] Colorize Tabs" companion extension: Alt+1 through Alt+7 set red/green/blue/yellow/brown/purple/orange, Alt+0 clears. Works via TST's sub-extension API. -- [AMO: TST Colorize Tabs](https://addons.mozilla.org/en-US/firefox/addon/tst-colorize-tabs/)
- "TST Colored Tabs" (different extension): automatically colorizes tabs based on opened domain using a hash-to-color algorithm. -- [GitHub: MurzNN/TST-Colored-tabs](https://github.com/MurzNN/TST-Colored-tabs)
- Sidebery supports per-domain automatic coloring and custom CSS with variables. Wiki provides userChrome.css snippets. -- [GitHub: Sidebery Wiki - Firefox Styles Snippets](https://github.com/mbnuqw/sidebery/wiki/Firefox-Styles-Snippets-(via-userChrome.css))

### Tor Browser Specifics
- userChrome.css works in Tor Browser if `toolkit.legacyUserProfileCustomizations.stylesheets` is enabled in about:config. -- [Tor Project GitLab: Issue #25467](https://gitlab.torproject.org/tpo/applications/tor-browser/-/issues/25467)
- The Tor Project officially discourages UI customization because it creates fingerprintable differences from the default Tor Browser configuration. -- [Tor Project Forum: Safely customizing Tor Browser](https://forum.torproject.org/t/safely-customizing-tor-browser-possible/6660)
- For automation scenarios (not anonymity-critical), the fingerprinting concern is irrelevant, so userChrome.css can be freely used. -- Inferred from context.

### Standalone Tab Coloring Extensions
- ColorfulTabs: offers "Generate Colors by Domain Hostname" for automatic domain-based coloring, manual right-click color assignment, and preset domain-color mappings. -- [GitHub: func0der/colorfulTabs](https://github.com/func0der/colorfulTabs)
- ColorTabs: set custom colors per domain/subdomain, with import/export. -- [AMO: ColorTabs](https://addons.mozilla.org/en-US/firefox/addon/colortabs/)
- Adaptive Tab Bar Color: changes the entire tab bar color to match the current page's theme color. -- [AMO: Adaptive Tab Bar Colour](https://addons.mozilla.org/en-US/firefox/addon/adaptive-tab-bar-colour/)

## Practical Implementation Recipe

For coloring individual browser tabs based on agent connection in a Selenium automation scenario, the recommended approach combines two components:

### Component 1: userChrome.css (pre-installed in Firefox profile)

```css
/* Enable with toolkit.legacyUserProfileCustomizations.stylesheets = true */

/* Agent color assignments via custom attributes */
.tabbrowser-tab[data-agent-id="0"] .tab-background {
    background-color: rgba(231, 76, 60, 0.3) !important;  /* red */
    background-image: none !important;
}
.tabbrowser-tab[data-agent-id="1"] .tab-background {
    background-color: rgba(46, 204, 113, 0.3) !important;  /* green */
    background-image: none !important;
}
.tabbrowser-tab[data-agent-id="2"] .tab-background {
    background-color: rgba(52, 152, 219, 0.3) !important;  /* blue */
    background-image: none !important;
}
.tabbrowser-tab[data-agent-id="3"] .tab-background {
    background-color: rgba(155, 89, 182, 0.3) !important;  /* purple */
    background-image: none !important;
}

/* Optional: also color the tab label text */
.tabbrowser-tab[data-agent-id="0"] .tab-label { color: #e74c3c !important; }
.tabbrowser-tab[data-agent-id="1"] .tab-label { color: #27ae60 !important; }
.tabbrowser-tab[data-agent-id="2"] .tab-label { color: #2980b9 !important; }
.tabbrowser-tab[data-agent-id="3"] .tab-label { color: #8e44ad !important; }

/* Optional: conditional enable/disable via about:config pref */
/*
@supports -moz-bool-pref("userChrome.agentColors.enabled") {
    .tabbrowser-tab[data-agent-id] .tab-background {
        ... styles ...
    }
}
*/
```

### Component 2: Selenium Python code (runtime attribute setting)

```python
from selenium import webdriver

driver = webdriver.Firefox()

# Set a custom attribute on a specific tab
def color_tab(driver, tab_index, agent_id):
    with driver.context(driver.CONTEXT_CHROME):
        driver.execute_script(f"""
            let tab = gBrowser.tabs[{tab_index}];
            if (tab) {{
                tab.setAttribute('data-agent-id', '{agent_id}');
            }}
        """)

# Clear agent color from a tab
def uncolor_tab(driver, tab_index):
    with driver.context(driver.CONTEXT_CHROME):
        driver.execute_script(f"""
            let tab = gBrowser.tabs[{tab_index}];
            if (tab) {{
                tab.removeAttribute('data-agent-id');
            }}
        """)

# Color the first tab as agent 0
color_tab(driver, 0, "0")

# Color the third tab as agent 2
color_tab(driver, 2, "2")
```

## What I'm unsure about

- Whether `data-*` custom attributes persist on XUL `tabbrowser-tab` elements across tab moves/reorderings, or whether Firefox's internal tab management code might strip unknown attributes during certain operations.
- The exact Selenium Python API surface for `context()` as a context manager vs `set_context()` as a method -- different Selenium versions may expose these differently, and the geckodriver version matters.
- Whether Marionette's chrome context `execute_script` can reliably access `gBrowser` in all Firefox/Tor Browser versions, or whether some builds restrict this. The geckodriver issue #1067 about global JS variables not persisting suggests there may be sandbox isolation caveats.
- How frequently Firefox updates break userChrome.css selectors targeting internal tab structure. The community (MrOtherGuy, aminomancer) tracks breakage, but the `.tab-background` and `.tab-stack` selectors have been stable since Proton (Firefox 89).
- Whether Tor Browser's ESR release cadence means its tab DOM structure lags behind mainline Firefox, requiring version-specific CSS selectors.
- The exact behavior of `@supports -moz-bool-pref()` with custom/nonexistent preferences -- whether a nonexistent pref evaluates as `false` or causes a parse error.
- Whether multiple Selenium WebDriver instances connecting to the same Firefox profile (shared browser) would conflict when setting attributes in chrome context, or if Marionette serializes chrome-context script execution.
- Whether setting attributes via Marionette chrome context triggers CSS re-evaluation immediately or requires a forced reflow/repaint.

## Sources

- [Mozilla Support: userChrome.css code for changing active tab colour](https://support.mozilla.org/en-US/questions/1282095)
- [Mozilla Support: userChrome.css Help With Customizing Tabs (part 2)](https://support.mozilla.org/en-US/questions/1446142)
- [Raymii.org: Firefox 89 Proton UI Tab Styling](https://raymii.org/s/blog/Firefox-89-proton-ui-tab-styling.html)
- [Gist: Firefox CSS to change accent color on tabs (Arty2)](https://gist.github.com/Arty2/d64726abac823662b36c406aa80181a7)
- [Gist: Prominent tab color for Firefox container (dangh)](https://gist.github.com/dangh/25315d954898f20a76a0d9b6f14c9b4d)
- [userchrome.org: What is Autoconfig Startup Scripting (userChrome.js)](https://www.userchrome.org/what-is-userchrome-js.html)
- [userchrome.org: What is userChrome.css](https://www.userchrome.org/what-is-userchrome-css.html)
- [userchrome.org: Firefox Changes Breaking userChrome.css](https://www.userchrome.org/firefox-changes-userchrome-css.html)
- [GitHub: MrOtherGuy/fx-autoconfig](https://github.com/MrOtherGuy/fx-autoconfig)
- [GitHub: MrOtherGuy/firefox-csshacks](https://github.com/MrOtherGuy/firefox-csshacks)
- [GitHub: aminomancer/uc.css.js](https://github.com/aminomancer/uc.css.js/)
- [GitHub: xiaoxiaoflood/firefox-scripts (userChromeJS)](https://github.com/xiaoxiaoflood/firefox-scripts)
- [GitHub: Aris-t2/CustomCSSforFx](https://github.com/Aris-t2/CustomCSSforFx)
- [GitHub: black7375/Firefox-UI-Fix Preference docs](https://github.com/black7375/Firefox-UI-Fix/blob/master/docs/Preference.md)
- [Mozilla archived docs: CSS -moz-bool-pref()](http://udn.realityripple.com/docs/Mozilla/Gecko/Chrome/CSS/-moz-bool-pref)
- [GitHub: firefox-gnome-theme issue #137 on -moz-bool-pref](https://github.com/rafaelmardojai/firefox-gnome-theme/issues/137)
- [GitHub: piroor/treestyletab](https://github.com/piroor/treestyletab)
- [GitHub: TST Code snippets for custom style rules](https://github.com/piroor/treestyletab/wiki/Code-snippets-for-custom-style-rules)
- [AMO: TST Colorize Tabs](https://addons.mozilla.org/en-US/firefox/addon/tst-colorize-tabs/)
- [GitHub: MurzNN/TST-Colored-tabs](https://github.com/MurzNN/TST-Colored-tabs)
- [GitHub: Sidebery Wiki - Firefox Styles Snippets](https://github.com/mbnuqw/sidebery/wiki/Firefox-Styles-Snippets-(via-userChrome.css))
- [AMO: Sidebery](https://addons.mozilla.org/en-US/firefox/addon/sidebery/)
- [GitHub: func0der/colorfulTabs](https://github.com/func0der/colorfulTabs)
- [AMO: ColorTabs](https://addons.mozilla.org/en-US/firefox/addon/colortabs/)
- [AMO: Adaptive Tab Bar Colour](https://addons.mozilla.org/en-US/firefox/addon/adaptive-tab-bar-colour/)
- [Bugzilla: Bug 487242 - tab visited attribute](https://bugzilla.mozilla.org/show_bug.cgi?id=487242)
- [Bugzilla: Bug 1325057 - Contextual identities custom colors](https://bugzilla.mozilla.org/show_bug.cgi?id=1325057)
- [Firefox Source Docs: tabbrowser](https://firefox-source-docs.mozilla.org/browser/base/tabbrowser/index.html)
- [Firefox Source Docs: Marionette Introduction](https://firefox-source-docs.mozilla.org/testing/marionette/Intro.html)
- [Firefox Source Docs: Marionette Python driver](https://firefox-source-docs.mozilla.org/python/marionette_driver.html)
- [Selenium Python API: Firefox WebDriver](https://www.selenium.dev/selenium/docs/api/py/selenium_webdriver_firefox/selenium.webdriver.firefox.webdriver.html)
- [Selenium docs: Firefox specific functionality](https://www.selenium.dev/documentation/webdriver/browsers/firefox/)
- [CopyProgramming: Auto color of tabs based on URL/domain](https://copyprogramming.com/howto/auto-color-of-tabs-in-firefox-based-on-url-domain)
- [Tor Project GitLab: Issue #25467 - failing to read userChrome.css](https://gitlab.torproject.org/tpo/applications/tor-browser/-/issues/25467)
- [Tor Project Forum: Safely customizing Tor Browser](https://forum.torproject.org/t/safely-customizing-tor-browser-possible/6660)
- [gHacks: Firefox 69 userChrome.css disabled by default](https://www.ghacks.net/2019/05/24/firefox-69-userchrome-css-and-usercontent-css-disabled-by-default/)
- [Gist: Firefox userChrome.css Proton Tabs (rdwebdesign)](https://gist.github.com/rdwebdesign/950be4889bb1782613241d5fb0466dd9)
- [Gist: Firefox UserChrome.css (silvercircle)](https://gist.github.com/silvercircle/ab3064fd17cb9f8fcba62b5e6576147c)
- [GitHub: geckodriver issue #1067 - Global JS variables don't persist](https://github.com/mozilla/geckodriver/issues/1067)
