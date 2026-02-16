# Angle 02 — Firefox Tab CSS Architecture

## Claims (with confidence)

- Claim (high): Each Firefox tab is a custom element `<tab is="tabbrowser-tab">` whose internal DOM is created by the `MozTabbrowserTab` class defined in `browser/components/tabbrowser/content/tab.js`. The markup is generated as a static property and appended during `initialize()`. — Source: searchfox.org tab.js

- Claim (high): The current (Firefox 130+) tab DOM hierarchy is: `.tabbrowser-tab > .tab-stack > { .tab-background, .tab-content }`. Inside `.tab-background`: `{ .tab-context-line, .tab-loading-burst, .tab-group-line }`. Inside `.tab-content`: `{ .tab-icon-stack, .tab-audio-button, .tab-label-container > .tab-label, .tab-close-button }`. There is NO element called `.tab-line` in current Firefox — it was renamed/replaced by `.tab-context-line` (for containers) and `.tab-group-line` (for tab groups) during the Proton-era refactors. — Source: searchfox.org tab.js markup template

- Claim (high): The `.tab-context-line` element is the colored indicator line for container (contextual identity) tabs. Its CSS rule from `usercontext.css` is: `.tabbrowser-tab[usercontextid] > .tab-stack > .tab-background > .tab-context-line { background-color: var(--identity-icon-color); height: 2px; border-radius: 2px; margin: 0 calc(var(--tab-border-radius) / 2); position: relative; }`. For vertical tabs it switches to `width: 2px; height: auto;`. — Source: searchfox.org usercontext.css

- Claim (high): Container tab colors are defined via CSS custom properties in `browser/components/contextualidentity/content/usercontext.css`. Nine named color classes exist: `.identity-color-blue` (#37adff), `.identity-color-turquoise` (#00c79a), `.identity-color-green` (#51cd00), `.identity-color-yellow` (#ffcb00), `.identity-color-orange` (#ff9f00), `.identity-color-red` (#ff613d), `.identity-color-pink` (#ff4bda), `.identity-color-purple` (#af51f5), `.identity-color-toolbar` (currentColor). Each sets both `--identity-tab-color` and `--identity-icon-color`. — Source: searchfox.org usercontext.css

- Claim (high): The `.tab-background` element is the main visual surface of a tab. Key CSS from `browser/themes/shared/tabbrowser/tabs.css`: `border-radius: var(--tab-border-radius); margin-block: var(--tab-block-margin); min-height: var(--tab-min-height); outline: var(--tab-outline);`. Selected state: `&:is([selected], [multiselected]) { background-color: var(--tab-selected-bgcolor); box-shadow: var(--tab-selected-shadow); }`. Hover: `.tabbrowser-tab:hover > .tab-stack > .tab-background:not([selected], [multiselected]) { background-color: var(--tab-hover-background-color); }`. — Source: searchfox.org tabs.css

- Claim (high): As of Firefox 119+, tab attributes `selected`, `pinned`, `multiselected`, etc. changed from pseudo-boolean string attributes (`selected="true"`) to real boolean attributes. CSS selectors must now use `[selected]` and `:not([selected])` instead of `[selected="true"]`. Older userChrome.css rules using `="true"` will silently stop matching. — Source: Mozilla Support forums, multiple corroborating reports

- Claim (high): Known tabbrowser-tab element attributes usable in CSS selectors include: `selected`, `visuallyselected`, `pinned`, `multiselected`, `fadein`, `busy`, `pending`, `unread`, `soundplaying`, `muted`, `sharing`, `attention`, `crashed`, `usercontextid`, `pictureinpicture`, `notselectedsinceload`. All are boolean attributes (119+) except `usercontextid` which has a numeric value identifying the container. — Sources: bugzilla.mozilla.org, userChrome.css community, searchfox.org

- Claim (high): Custom attributes CAN be set on `.tabbrowser-tab` elements via JavaScript (`tab.setAttribute("myattr", "")`) and then targeted in CSS with `.tabbrowser-tab[myattr]` selectors. This is the established pattern used by userChromeJS extensions and autoconfig scripts. When done from privileged chrome context (e.g., Browser Console, autoconfig loader), these attributes persist on the element and are styleable from userChrome.css. — Sources: bugzilla.mozilla.org bug 487242, Mozilla Support forums

- Claim (high): The `.tab-group-line` is a new element (2024+) for tab grouping. It is `display: none` by default and shown only inside `tab-group` elements. In horizontal mode it renders as a colored bar at the bottom of the tab: `height: var(--tab-group-line-thickness); inset-block-end: var(--tab-group-line-toolbar-border-distance);`. Color is `var(--tab-group-line-color)` which uses the `light-dark()` function. — Source: searchfox.org tabs.css

- Claim (medium): The old `.tab-line` element that many pre-Proton userChrome.css recipes target (e.g., `.tab-line[selected="true"] { background-color: red; }`) no longer exists in current Firefox. It was the colored accent line at the top of the selected tab in Photon-era Firefox (pre-89). The `--lwt-tab-line-color` CSS variable still exists for theme compatibility but now maps to `--tab-outline-color` via `&[lwtheme] { --tab-outline-color: var(--lwt-tab-line-color, currentColor); }`. — Sources: bugzilla.mozilla.org bug 1439734, MrOtherGuy CSS variables gist, community reports

- Claim (medium): From Selenium/WebDriver, `execute_script()` runs in web content scope, NOT chrome scope. To set attributes on tabbrowser-tab elements, you would need either: (a) a privileged extension / autoconfig script that listens for messages, or (b) `execute_script()` targeting `window.browsingContext` or using marionette protocol directly. Standard Selenium `execute_script` cannot access XUL chrome elements like `.tabbrowser-tab`. — Sources: Selenium docs, Mozilla Browser Console docs, palant.info article on Selenium limitations

- Claim (high): The `.tab-content` element holds the visible tab contents (icon, label, close button). It inherits state attributes from the parent tab: `.tab-content:is([selected], [multiselected]) { color: var(--tab-selected-textcolor); color-scheme: var(--tab-selected-color-scheme); }`. The `.tab-label` element has `white-space: nowrap` and supports an `[attention]` attribute that bolds unselected tabs. — Source: searchfox.org tabs.css

## Evidence

- **Tab DOM structure from source code**: The `MozTabbrowserTab` class in `browser/components/tabbrowser/content/tab.js` defines the complete markup as a static template. The hierarchy is `tab-stack > { tab-background { tab-context-line, tab-loading-burst, tab-group-line }, tab-content { tab-icon-stack, tab-audio-button, tab-label-container { tab-text.tab-label }, tab-note-icon, tab-close-button } }`. — [tab.js on Searchfox](https://searchfox.org/mozilla-central/source/browser/components/tabbrowser/content/tab.js)

- **Tab CSS rules from shared theme**: The file `browser/themes/shared/tabbrowser/tabs.css` is the primary stylesheet. It uses CSS nesting and custom properties extensively. Key variables: `--tab-selected-bgcolor`, `--tab-selected-textcolor`, `--tab-hover-background-color`, `--tab-border-radius`, `--tab-block-margin`, `--tab-min-height`, `--tab-inline-padding`, `--tab-outline`, `--tab-group-line-color`. — [tabs.css on Searchfox](https://searchfox.org/mozilla-central/source/browser/themes/shared/tabbrowser/tabs.css)

- **Container color definitions**: The `usercontext.css` file at `browser/components/contextualidentity/content/usercontext.css` defines 9 identity color classes, each setting `--identity-tab-color` and `--identity-icon-color`. The `.tab-context-line` is styled with `background-color: var(--identity-icon-color)` only when `[usercontextid]` attribute is present. — [usercontext.css on Searchfox](https://searchfox.org/mozilla-central/source/browser/components/contextualidentity/content/usercontext.css)

- **Navigator-toolbox markup**: The initial tab element in `navigator-toolbox.inc.xhtml` is minimal: `<tab is="tabbrowser-tab" class="tabbrowser-tab" selected="true" visuallyselected="" fadein=""/>`. All internal DOM is constructed by the custom element class. — [navigator-toolbox.inc.xhtml on Searchfox](https://searchfox.org/mozilla-central/source/browser/base/content/navigator-toolbox.inc.xhtml)

- **Boolean attribute change (Firefox 119+)**: Multiple community reports confirm that `[selected="true"]` stopped working and must be changed to `[selected]`. This affects all tab boolean attributes. — [Mozilla Support: userChrome.css - Help With Customizing Tabs](https://support.mozilla.org/en-US/questions/1446030)

- **Theme tab line color variable**: Bug 1439734 added `--lwt-tab-line-color` to allow themes to set the tab line color. In current Firefox this maps to `--tab-outline-color` rather than the old `.tab-line` element. — [Bugzilla Bug 1439734](https://bugzilla.mozilla.org/show_bug.cgi?id=1439734)

- **Prominent container tab coloring example**: A userChrome.css approach uses `.tabbrowser-tab[usercontextid] .tab-background { background: var(--identity-tab-color) !important; opacity: 0.6 !important; }` to make the entire tab background match the container color, rather than just the thin context line. — [Prominent tab color for Firefox container Gist](https://gist.github.com/dangh/25315d954898f20a76a0d9b6f14c9b4d)

- **Custom attribute styling pattern**: Bugzilla bug 487242 documents using `tab.setAttribute("visited", "true")` via JavaScript and then styling with `.tabbrowser-tab:not([visited]) .tab-text` in userChrome.css. This confirms the setAttribute + CSS attribute selector pattern works. — [Bugzilla Bug 487242](https://bugzilla.mozilla.org/show_bug.cgi?id=487242)

- **Firefox CSS variables reference**: MrOtherGuy maintains a comprehensive gist of CSS variables used by Firefox, including `--lwt-tab-line-color`, `--identity-tab-color`, `--identity-icon-color`, and all tab-related variables. — [CSS variables used by Firefox (MrOtherGuy)](https://gist.github.com/MrOtherGuy/a673848c95823225f7b198199f87a396)

- **Test files confirm querySelector pattern**: Firefox's own performance tests use `querySelector("tab[selected=true] .tab-background")` to find tab elements, confirming the DOM structure is queryable. — [Searchfox: browser_startup_flicker.js](https://searchfox.org/mozilla-central/source/browser/base/content/test/performance/browser_startup_flicker.js)

## Practical Application: Per-Tab Coloring via Custom Attributes

The research reveals a clear strategy for coloring individual tabs based on agent connection:

1. **Set a custom attribute on the tab element** from privileged JavaScript:
   ```javascript
   // From chrome-privileged context (autoconfig, extension, or Browser Console):
   let tab = gBrowser.tabs[tabIndex];
   tab.setAttribute("agent-id", "agent-03");
   tab.setAttribute("agent-color", "#ff6600");
   ```

2. **Style via userChrome.css** using attribute selectors:
   ```css
   /* Color the context line for agent-connected tabs */
   .tabbrowser-tab[agent-id] > .tab-stack > .tab-background > .tab-context-line {
     display: flex !important;
     background-color: attr(agent-color) !important;  /* Note: attr() for colors has limited support */
     height: 3px !important;
   }

   /* Better: use predefined agent color classes */
   .tabbrowser-tab[agent-id="agent-01"] > .tab-stack > .tab-background {
     outline: 2px solid #ff0000 !important;
   }
   .tabbrowser-tab[agent-id="agent-02"] > .tab-stack > .tab-background {
     outline: 2px solid #00ff00 !important;
   }
   ```

3. **Alternative: Use the container mechanism directly**. Since Firefox already colors `.tab-context-line` based on `--identity-icon-color` when `[usercontextid]` is present, assigning each agent to a distinct container automatically colors the tab indicator line.

## What I'm unsure about

- **Exact version `.tab-line` was removed**: The old `.tab-line` element that Photon-era userChrome.css recipes reference no longer exists in current tab.js markup. It was likely removed during the Firefox 89 Proton transition, but I could not find the exact commit or version that made this change. Many old tutorials still reference `.tab-line[selected="true"]` which will not work on current Firefox.

- **CSS `attr()` function for colors**: The proposed approach of using `attr(agent-color)` for dynamic colors in CSS has limited browser support. It may not work in Firefox's chrome context. A safer approach is predefined attribute values with matching CSS rules.

- **Selenium `execute_script` and chrome context**: Standard Selenium `execute_script()` runs in web content scope and cannot access chrome DOM elements like `tabbrowser-tab`. The exact mechanism to bridge this gap (Marionette commands, autoconfig scripts, or a privileged helper extension) needs further investigation. The `browser.Runtime.evaluate` CDP command or direct Marionette `execute_script_in_chrome` might work if available.

- **Whether `.tab-group-line` could be repurposed**: The `.tab-group-line` element is `display: none` by default and only shown inside `tab-group` parent elements. It might be possible to force-show it via CSS for agent coloring, but this could conflict with future tab grouping features.

- **Stability of internal CSS selectors**: Firefox explicitly does not guarantee stability of chrome CSS selectors between versions. The tab structure has changed multiple times (XBL era -> Custom Elements, Photon -> Proton, addition of tab-group-line). Any userChrome.css approach requires maintenance across Firefox updates.

## Complete Tab DOM Tree (Current Firefox, from tab.js source)

```
<tab is="tabbrowser-tab" class="tabbrowser-tab"
     selected pinned fadein busy usercontextid="N" ...>
  <stack class="tab-stack" flex="1">
    <vbox class="tab-background">
      <hbox class="tab-context-line"/>       <!-- container color indicator -->
      <hbox class="tab-loading-burst" flex="1"/>  <!-- loading animation -->
      <hbox class="tab-group-line"/>          <!-- tab group color indicator -->
    </vbox>
    <hbox class="tab-content" align="center">
      <stack class="tab-icon-stack">
        <hbox class="tab-throbber"/>
        <hbox class="tab-icon-pending"/>
        <img class="tab-icon-image" role="presentation" decoding="sync"/>
        <image class="tab-sharing-icon-overlay" role="presentation"/>
        <image class="tab-icon-overlay" role="presentation"/>
        <image class="tab-note-icon-overlay" role="presentation"/>
      </stack>
      <moz-button type="icon ghost" size="small"
                  class="tab-audio-button" tabindex="-1"/>
      <vbox class="tab-label-container" align="start" pack="center" flex="1">
        <label class="tab-text tab-label" role="presentation"/>
        <hbox class="tab-secondary-label">
          <label class="tab-icon-sound-label tab-icon-sound-pip-label" .../>
        </hbox>
      </vbox>
      <image class="tab-note-icon" role="presentation"/>
      <image class="tab-close-button close-icon" role="button" .../>
    </hbox>
  </stack>
</tab>
```

## Sources

- [tab.js on Searchfox (tab markup template)](https://searchfox.org/mozilla-central/source/browser/components/tabbrowser/content/tab.js)
- [tabs.css on Searchfox (shared tab theme)](https://searchfox.org/mozilla-central/source/browser/themes/shared/tabbrowser/tabs.css)
- [usercontext.css on Searchfox (container identity colors)](https://searchfox.org/mozilla-central/source/browser/components/contextualidentity/content/usercontext.css)
- [navigator-toolbox.inc.xhtml on Searchfox](https://searchfox.org/mozilla-central/source/browser/base/content/navigator-toolbox.inc.xhtml)
- [Bugzilla Bug 1439734 - Allow setting the tab line color](https://bugzilla.mozilla.org/show_bug.cgi?id=1439734)
- [Bugzilla Bug 487242 - Custom tab attributes for styling](https://bugzilla.mozilla.org/show_bug.cgi?id=487242)
- [Bugzilla Bug 1325057 - Container tab custom colors](https://bugzilla.mozilla.org/show_bug.cgi?id=1325057)
- [Bugzilla Bug 1387117 - Container color indicator visibility](https://bugzilla.mozilla.org/show_bug.cgi?id=1387117)
- [Firefox 89+ Proton UI Styling (userchrome.org)](https://www.userchrome.org/firefox-89-styling-proton-ui.html)
- [Firefox 89 Proton UI Tab Styling (Raymii.org)](https://raymii.org/s/blog/Firefox-89-proton-ui-tab-styling.html)
- [CSS variables used by Firefox (MrOtherGuy gist)](https://gist.github.com/MrOtherGuy/a673848c95823225f7b198199f87a396)
- [Prominent tab color for Firefox container (dangh gist)](https://gist.github.com/dangh/25315d954898f20a76a0d9b6f14c9b4d)
- [Firefox CSS accent color on tabs (Arty2 gist)](https://gist.github.com/Arty2/d64726abac823662b36c406aa80181a7)
- [MrOtherGuy/firefox-csshacks collection](https://github.com/MrOtherGuy/firefox-csshacks)
- [Mozilla Support: userChrome.css Tab Customization](https://support.mozilla.org/en-US/questions/1446030)
- [Mozilla Support: Active tab colour](https://support.mozilla.org/en-US/questions/1282095)
- [Mozilla Support: Tab-line behavior change](https://support.mozilla.org/en-US/questions/1397107)
- [tabbrowser documentation (Firefox Source Docs)](https://firefox-source-docs.mozilla.org/browser/base/tabbrowser/index.html)
- [Tab colouring position issue (#2029)](https://github.com/mozilla/multi-account-containers/issues/2029)
