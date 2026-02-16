# Angle 04 — Firefox Container Tabs Coloring

## Claims (with confidence)

- Claim (high): Firefox's container tab coloring system is driven by CSS classes applied to tab elements by `ContextualIdentityService.sys.mjs`. The `setTabStyle()` function removes any existing `identity-color-*` class from the tab and adds a new class like `identity-color-blue`, `identity-color-red`, etc. These classes are defined in `browser/components/contextualidentity/content/usercontext.css`, where each maps to a pair of CSS custom properties: `--identity-tab-color` and `--identity-icon-color` with specific hex values. Evidence: searchfox.org source for ContextualIdentityService.sys.mjs and usercontext.css.

- Claim (high): The visual container color indicator on tabs is rendered by the `.tab-context-line` DOM element, targeted by the CSS selector `.tabbrowser-tab[usercontextid] > .tab-stack > .tab-background > .tab-context-line`. This element gets `background-color: var(--identity-icon-color)`, with a height of 2px, border-radius of 2px, and horizontal margin of `calc(var(--tab-border-radius) / 2)`. For vertical tabs, it becomes a 2px-wide vertical stripe instead. Evidence: the complete usercontext.css source from searchfox.org/mozilla-central.

- Claim (high): The `contextualIdentities` WebExtension API supports programmatic creation of containers via `browser.contextualIdentities.create({name, color, icon})`. The `color` parameter is limited to 9 predefined string values: "blue", "turquoise", "green", "yellow", "orange", "red", "pink", "purple", "toolbar". The API returns a `ContextualIdentity` object including a `colorCode` property (e.g., "#37adff" for blue) and a unique `cookieStoreId`. Evidence: MDN documentation for contextualIdentities.create() and ContextualIdentity type.

- Claim (high): The exact hex color codes for each container color name are defined in usercontext.css: blue=#37adff, turquoise=#00c79a, green=#51cd00, yellow=#ffcb00, orange=#ff9f00, red=#ff613d, pink=#ff4bda, purple=#af51f5, toolbar=currentColor. Evidence: complete usercontext.css source from searchfox.org.

- Claim (high): Custom hex colors passed to the contextualIdentities API are stored correctly in Firefox's internal data, but the UI does NOT render them. The `data-identity-color` attribute on the tab won't match any predefined CSS class (like `.identity-color-blue`), causing the tab to fall back to black/no color. Bug 1325057 has been open for 9 years (status: NEW/unresolved) requesting support for custom hex colors in the UI. Evidence: Bugzilla bug 1325057 discussion.

- Claim (high): To open a tab in a specific container from a WebExtension, you call `browser.tabs.create({url: "...", cookieStoreId: "firefox-container-1"})`. The `cookieStoreId` value comes from the `ContextualIdentity.cookieStoreId` property returned when creating or querying containers. This requires both "contextualIdentities" and "cookies" permissions. Evidence: MDN Work with contextual identities guide.

- Claim (high): Container definitions persist in the Firefox profile at `containers.json`, with a structure like `{"version":5, "lastUserContextId":5, "identities":[{"icon":"fingerprint", "color":"blue", "l10nId":"user-context-personal", "public":true, "userContextId":1}, ...]}`. Each identity has a numeric `userContextId` that maps to the `usercontextid` attribute on tab DOM elements. Evidence: home-manager issue #4989 and multi-account-containers issue #1208.

- Claim (medium): WebDriver BiDi (supported in Selenium 4+) now supports Firefox containers natively. `browser.createUserContext` creates a new container (user context) and returns a userContext ID. `browsingContext.create` accepts a `userContext` parameter to open a new tab in that container. In Python Selenium, this would be `driver.browser.create_user_context()` and `driver.browsing_context.create(type="tab", user_context=id)`. Evidence: Firefox WebDriver Newsletter 125, Selenium PR #15371, Selenium BiDi docs.

- Claim (medium): The Multi-Account Containers extension itself does NOT inject CSS for tab coloring. The coloring is entirely handled by Firefox's built-in stylesheet (usercontext.css) and the `ContextualIdentityService`. The extension only provides UI for managing containers (creating, editing, assigning sites to containers). The colored tab indicator is a native Firefox feature that activates whenever `privacy.userContext.enabled` is true. Evidence: GitHub source of mozilla/multi-account-containers, Firefox source code structure.

- Claim (medium): For our Selenium automation use case, we could create up to 9 distinctly-colored containers (one per predefined color), assign each agent's tab to a different container via WebDriver BiDi, and get native per-tab color indicators without any CSS injection or extension. The limitation is 9 colors maximum from the predefined set. Evidence: synthesis of contextualIdentities API docs and WebDriver BiDi capabilities.

- Claim (low): It may be possible to get more than 9 colors by combining container color indicators with userChrome.css overrides that target `.tabbrowser-tab[usercontextid="N"]` with custom background colors, since the `usercontextid` attribute carries the numeric ID of each container. However, this requires pre-configuring the profile with `toolkit.legacyUserProfileCustomizations.stylesheets` set to true and placing a userChrome.css file in the profile's chrome directory. Evidence: various userChrome.css community examples.

## Evidence

- Firefox source file `browser/components/contextualidentity/content/usercontext.css` defines all 9 color classes (`.identity-color-blue` through `.identity-color-toolbar`) with their hex values and also defines the `.tab-context-line` styling rule — [Searchfox: usercontext.css](https://searchfox.org/mozilla-central/source/browser/components/contextualidentity/content/usercontext.css)

- `ContextualIdentityService.sys.mjs` contains the `setTabStyle()` function that applies classes with prefix `"identity-color-"` + the color name string to tab elements, and removes old identity-color classes first — [Searchfox: ContextualIdentityService.sys.mjs](https://searchfox.org/mozilla-central/source/toolkit/components/contextualidentity/ContextualIdentityService.sys.mjs)

- The `--identity-tab-color` CSS variable is referenced in 4 files: usercontext.css (defines it 9 times), tabs.css line 2542 (uses it for tab background), urlbarView.css (uses it for URL bar border), and a stylelint config — [Searchfox search: identity-tab-color](https://searchfox.org/mozilla-central/search?q=identity-tab-color)

- MDN documents `contextualIdentities.create()` accepting name, color (9 values), and icon (13 values), returning a Promise resolving to a ContextualIdentity with cookieStoreId and colorCode — [MDN: contextualIdentities.create()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/contextualIdentities/create)

- The ContextualIdentity type has a `colorCode` property that returns the hex code (e.g., "#37adff"), recommended by Mozilla for use in extensions since they may update the codes — [MDN: ContextualIdentity](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/contextualIdentities/ContextualIdentity)

- Bug 1325057 (opened 2017, still NEW) confirms custom hex colors are stored but not rendered by Firefox UI, which defaults to black when the color name doesn't match a predefined class — [Bugzilla: Bug 1325057](https://bugzilla.mozilla.org/show_bug.cgi?id=1325057)

- Firefox WebDriver Newsletter 125 documents that `browser.createUserContext` and the `userContext` parameter for `browsingContext.create` were implemented in Firefox, allowing container management via WebDriver BiDi — [Firefox WebDriver Newsletter 125](https://fxdx.dev/firefox-webdriver-newsletter-125/)

- Selenium PR #15371 adds `create_user_context()`, `get_user_contexts()`, and `remove_user_context()` to the BiDi browser module — [Selenium PR #15371](https://github.com/SeleniumHQ/selenium/pull/15371)

- The `containers.json` file in Firefox profiles stores container definitions with `userContextId`, `color`, `icon`, and `name` fields — [GitHub: home-manager issue #4989](https://github.com/nix-community/home-manager/issues/4989)

- CSS selector `.tabbrowser-tab[usercontextid] .tab-background { background: var(--identity-tab-color) !important; }` can color the entire tab background (not just the line) via userChrome.css — [Prominent tab color gist](https://gist.github.com/dangh/25315d954898f20a76a0d9b6f14c9b4d)

- The `--identity-tab-color` variable is also used in the URL bar to color the label text: `#userContext-label { color: var(--identity-tab-color); }` — [Searchfox: usercontext.css](https://searchfox.org/mozilla-central/source/browser/components/contextualidentity/content/usercontext.css)

## What I'm unsure about

- Whether Selenium's Python BiDi bindings for `create_user_context()` and `browsingContext.create(user_context=...)` are fully stable and released, or still in development. The Ruby bindings were added in PR #15371 but the Python equivalent PR #15616 was only recently submitted.

- Whether WebDriver BiDi containers created via `browser.createUserContext` map exactly to Firefox's contextualIdentities (with the same color/icon system), or whether they are a separate lower-level concept. The WebDriver BiDi spec calls them "user contexts" without specifying color assignment. It's unclear if you can set a color when creating a user context via BiDi (the spec may not support color/icon parameters, only Firefox's WebExtension API does).

- Whether Tor Browser (which is based on Firefox ESR) supports the contextualIdentities API and container tab coloring at all. Tor Browser has its own first-party isolation that may conflict with or replace the container system. Tor Browser also strips many WebExtension APIs for privacy.

- The exact interaction between `privacy.userContext.enabled`, `privacy.userContext.ui.enabled`, and the Multi-Account Containers extension. It's unclear whether enabling `privacy.userContext.enabled` alone is sufficient to get tab coloring, or if the extension is also needed.

- Whether the WebDriver BiDi `browser.createUserContext` command supports a `proxy` argument in released Firefox versions (it was mentioned in Newsletter 141 for Firefox Nightly), and whether this could be combined with container colors for per-agent network isolation.

- How many containers Firefox supports before performance degrades. For a 10-agent swarm each with their own container, 10 containers should be fine, but the ceiling is undocumented.

## Key Takeaway for Implementation

The most promising approach for per-agent tab coloring is:

1. **Via WebExtension (most control):** Build a small helper WebExtension with `contextualIdentities` and `cookies` permissions. On load, create N containers with distinct colors from the predefined set (blue, turquoise, green, yellow, orange, red, pink, purple -- 8 usable colors, "toolbar" is theme-dependent). Open each agent's tab via `browser.tabs.create({cookieStoreId})`. Load the extension via Selenium's `install_addon()`. The tab-context-line will automatically show the correct color.

2. **Via WebDriver BiDi (emerging, less CSS control):** Use `driver.browser.create_user_context()` to create containers, then `driver.browsing_context.create(type="tab", user_context=id)` to open tabs. However, it's unclear if BiDi lets you set the container color -- you may get containers without visual differentiation.

3. **Via profile pre-configuration:** Write `containers.json` into the Firefox profile before launch with predefined containers and colors, enable `privacy.userContext.enabled` and `toolkit.legacyUserProfileCustomizations.stylesheets`, add a `userChrome.css` with enhanced coloring rules (full tab background instead of just a 2px line), then use the WebExtension approach or BiDi to assign tabs.

The 2px `tab-context-line` may be too subtle for quick agent identification. Enhancing it via userChrome.css to color the full tab background is straightforward: `.tabbrowser-tab[usercontextid] .tab-background { background: var(--identity-tab-color) !important; opacity: 0.6 !important; }`

## Sources

- [Searchfox: usercontext.css (container color CSS definitions)](https://searchfox.org/mozilla-central/source/browser/components/contextualidentity/content/usercontext.css)
- [Searchfox: ContextualIdentityService.sys.mjs](https://searchfox.org/mozilla-central/source/toolkit/components/contextualidentity/ContextualIdentityService.sys.mjs)
- [MDN: contextualIdentities API overview](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/contextualIdentities)
- [MDN: contextualIdentities.create()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/contextualIdentities/create)
- [MDN: ContextualIdentity type](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/contextualIdentities/ContextualIdentity)
- [MDN: Work with contextual identities](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Work_with_contextual_identities)
- [Bugzilla Bug 1325057: Allow custom colors for container tabs](https://bugzilla.mozilla.org/show_bug.cgi?id=1325057)
- [Firefox WebDriver Newsletter 125 (userContext BiDi support)](https://fxdx.dev/firefox-webdriver-newsletter-125/)
- [Firefox WebDriver Newsletter 141 (proxy support for createUserContext)](https://fxdx.dev/firefox-webdriver-newsletter-141/)
- [Selenium PR #15371: Browser module with user context methods](https://github.com/SeleniumHQ/selenium/pull/15371)
- [W3C WebDriver BiDi Specification](https://w3c.github.io/webdriver-bidi/)
- [GitHub: mozilla/multi-account-containers](https://github.com/mozilla/multi-account-containers)
- [GitHub Issue #391: Custom colors for containers](https://github.com/mozilla/multi-account-containers/issues/391)
- [Prominent tab color for Firefox container (userChrome.css gist)](https://gist.github.com/dangh/25315d954898f20a76a0d9b6f14c9b4d)
- [Searchfox: tabs.css (tab-context-line usage)](https://searchfox.org/mozilla-central/source/browser/themes/shared/tabbrowser/tabs.css)
