# Firefox Tab Coloring & Focus Control for Multi-Agent Browser Automation
## Consolidated Source Bibliography

**Date:** 2026-02-12
**Total unique sources:** 98
**Organized by:** Angle of origin (deduplicated; shared sources noted)

---

## Angle 01 — gBrowser Tab API

1. [tabbrowser.js on Searchfox (mozilla-central)](https://searchfox.org/mozilla-central/source/browser/components/tabbrowser/content/tabbrowser.js) *(also cited in Angles 02, 04, 10)* — WebSearch
2. [tab.js on Searchfox (MozTabbrowserTab class)](https://searchfox.org/mozilla-central/source/browser/components/tabbrowser/content/tab.js) *(also cited in Angle 02)* — WebSearch
3. [Firefox tabbrowser Source Docs](https://firefox-source-docs.mozilla.org/browser/base/tabbrowser/index.html) *(also cited in Angles 05, 10)* — WebSearch
4. [Selenium Python API: Firefox WebDriver](https://www.selenium.dev/selenium/docs/api/py/selenium_webdriver_firefox/selenium.webdriver.firefox.webdriver.html) *(also cited in Angles 05, 07, 10)* — WebSearch
5. [Marionette Driver Package Docs](https://firefox-source-docs.mozilla.org/python/marionette_driver.html) *(also cited in Angles 05, 10)* — WebSearch
6. [Introduction to Marionette](https://firefox-source-docs.mozilla.org/testing/marionette/Intro.html) *(also cited in Angles 05, 07)* — WebSearch
7. [MDN: contextualIdentities API](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/contextualIdentities) *(also cited in Angle 04)* — WebSearch
8. [MDN: Work with contextual identities](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Work_with_contextual_identities) *(also cited in Angles 04, 10)* — WebSearch
9. [Mozilla Support: userChrome.css Tab Customization](https://support.mozilla.org/en-US/questions/1446142) *(also cited in Angles 02, 07)* — WebSearch
10. [Firefox 89 Proton UI Tab Styling (Raymii.org)](https://raymii.org/s/blog/Firefox-89-proton-ui-tab-styling.html) *(also cited in Angles 02, 07, 10)* — WebSearch
11. [Bug 1475606 - Extend addTab options object](https://bugzilla.mozilla.org/show_bug.cgi?id=1475606) — WebSearch
12. [Bug 1297157 - Abstract away visuallyselected attribute](https://bugzilla.mozilla.org/show_bug.cgi?id=1297157) — WebSearch
13. [Bug 1171245 - Include changed attributes in TabAttrModified](https://bugzilla.mozilla.org/show_bug.cgi?id=1171245) — WebSearch
14. [Bug 1111276 - Replace selectedTab.linkedBrowser](https://bugzilla.mozilla.org/show_bug.cgi?id=1111276) — WebSearch
15. [Marcos Caceres: Gecko gBrowser and tabs](https://marcosc.com/2015/01/gecko-gbrowser-and-tabs/) — WebSearch
16. [Intoli: JavaScript Injection with Selenium and Marionette](https://intoli.com/blog/javascript-injection/) *(also cited in Angle 10)* — WebSearch
17. [Private_Tab Extension (tab attribute manipulation)](https://github.com/Infocatcher/Private_Tab) — WebSearch
18. [Bug 487242 - userChrome.css tab state differentiation](https://bugzilla.mozilla.org/show_bug.cgi?id=487242) *(also cited in Angles 02, 07)* — WebSearch
19. [Bug 1387117 - Container color indicator visibility](https://bugzilla.mozilla.org/show_bug.cgi?id=1387117) *(also cited in Angles 02, 03, 10)* — WebSearch
20. [geckodriver Issue #740 - Actions in chrome context](https://github.com/mozilla/geckodriver/issues/740) — WebSearch
21. [Searchfox: tabbrowser directory listing](https://searchfox.org/mozilla-central/source/browser/components/tabbrowser/content) — WebSearch
22. [Tabbed Browser Archive - MDN](https://udn.realityripple.com/docs/Archive/Add-ons/Tabbed_browser) — WebSearch
23. [Mozilla Support: Tab colour question](https://support.mozilla.org/en-US/questions/1282095) *(also cited in Angles 02, 07)* — WebSearch

## Angle 02 — Tab CSS Architecture

24. [tabs.css on Searchfox (shared tab theme)](https://searchfox.org/mozilla-central/source/browser/themes/shared/tabbrowser/tabs.css) *(also cited in Angle 04)* — WebSearch
25. [usercontext.css on Searchfox (container colors)](https://searchfox.org/mozilla-central/source/browser/components/contextualidentity/content/usercontext.css) *(also cited in Angle 04)* — WebSearch
26. [navigator-toolbox.inc.xhtml on Searchfox](https://searchfox.org/mozilla-central/source/browser/base/content/navigator-toolbox.inc.xhtml) — WebSearch
27. [Bug 1439734 - Allow setting the tab line color](https://bugzilla.mozilla.org/show_bug.cgi?id=1439734) *(also cited in Angle 03)* — WebSearch
28. [Firefox 89+ Proton UI Styling (userchrome.org)](https://www.userchrome.org/firefox-89-styling-proton-ui.html) *(also cited in Angles 07, 10)* — WebSearch
29. [CSS variables used by Firefox (MrOtherGuy gist)](https://gist.github.com/MrOtherGuy/a673848c95823225f7b198199f87a396) — WebSearch
30. [Prominent tab color for Firefox container (dangh gist)](https://gist.github.com/dangh/25315d954898f20a76a0d9b6f14c9b4d) *(also cited in Angles 04, 07)* — WebSearch
31. [Firefox CSS accent color on tabs (Arty2 gist)](https://gist.github.com/Arty2/d64726abac823662b36c406aa80181a7) *(also cited in Angle 07)* — WebSearch
32. [MrOtherGuy/firefox-csshacks collection](https://github.com/MrOtherGuy/firefox-csshacks) *(also cited in Angle 07)* — WebSearch
33. [Tab colouring position issue (#2029)](https://github.com/mozilla/multi-account-containers/issues/2029) — WebSearch
34. [Bug 1325057 - Custom colors for container tabs](https://bugzilla.mozilla.org/show_bug.cgi?id=1325057) *(also cited in Angles 03, 04, 07)* — WebSearch
35. [Mozilla Support: Tab-line behavior change](https://support.mozilla.org/en-US/questions/1397107) — WebSearch
36. [Searchfox: browser_startup_flicker.js](https://searchfox.org/mozilla-central/source/browser/base/content/test/performance/browser_startup_flicker.js) — WebSearch

## Angle 03 — WebExtension Theme API

37. [MDN: browser.theme.update()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme/update) — WebSearch
38. [MDN: theme manifest.json](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/theme) — WebSearch
39. [MDN: browser.theme API](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme) — WebSearch
40. [MDN: browser.theme.getCurrent()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme/getCurrent) — WebSearch
41. [MDN: browser.theme.reset()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme/reset) — WebSearch
42. [MDN: theme.onUpdated](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/theme/onUpdated) — WebSearch
43. [MDN: theme_experiment](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/theme_experiment) — WebSearch
44. [Mozilla Hacks: Using the new theming API](https://hacks.mozilla.org/2017/12/using-the-new-theming-api-in-firefox/) — WebSearch
45. [Mozilla Add-ons Blog: Theme API Update (2018)](https://blog.mozilla.org/addons/2018/03/08/theme-api-update/) — WebSearch
46. [Firefox Extension Workshop: Dynamic Themes](https://extensionworkshop.com/documentation/themes/dynamic-themes/) — WebSearch
47. [Danny Guo: Building Dynamic Firefox Themes](https://www.dannyguo.com/blog/building-dynamic-firefox-themes) — WebSearch
48. [Bug 1320585: Allow styling individual tabs](https://bugzilla.mozilla.org/show_bug.cgi?id=1320585) — WebSearch
49. [Bug 1342712: Scoped themes per window/tab](https://bugzilla.mozilla.org/show_bug.cgi?id=1342712) — WebSearch
50. [Adaptive Tab Bar Colour (GitHub)](https://github.com/easonwong-de/Adaptive-Tab-Bar-Colour) — WebSearch
51. [Chromatastic (GitHub)](https://github.com/dguo/chromatastic) — WebSearch
52. [AMO: Adaptive Tab Bar Colour](https://addons.mozilla.org/en-US/firefox/addon/adaptive-tab-bar-colour/) *(also cited in Angle 07)* — WebSearch
53. [AMO: Containers Theme](https://addons.mozilla.org/en-US/firefox/addon/containers-theme/) — WebSearch
54. [AMO: Colorize Tabs](https://addons.mozilla.org/en-US/firefox/addon/colorize-tabs/) *(also cited in Angle 07)* — WebSearch
55. [Firefox Color](https://color.firefox.com/) — WebSearch

## Angle 04 — Container Tabs Coloring

56. [Searchfox: ContextualIdentityService.sys.mjs](https://searchfox.org/mozilla-central/source/toolkit/components/contextualidentity/ContextualIdentityService.sys.mjs) — WebSearch
57. [MDN: contextualIdentities.create()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/contextualIdentities/create) — WebSearch
58. [MDN: ContextualIdentity type](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/contextualIdentities/ContextualIdentity) — WebSearch
59. [Firefox WebDriver Newsletter 125](https://fxdx.dev/firefox-webdriver-newsletter-125/) — WebSearch
60. [Firefox WebDriver Newsletter 141](https://fxdx.dev/firefox-webdriver-newsletter-141/) — WebSearch
61. [Selenium PR #15371: Browser module user context](https://github.com/SeleniumHQ/selenium/pull/15371) — WebSearch
62. [W3C WebDriver BiDi Specification](https://w3c.github.io/webdriver-bidi/) *(also cited in Angles 05, 10)* — WebSearch
63. [GitHub: mozilla/multi-account-containers](https://github.com/mozilla/multi-account-containers) — WebSearch
64. [GitHub Issue #391: Custom colors for containers](https://github.com/mozilla/multi-account-containers/issues/391) — WebSearch
65. [home-manager issue #4989 (containers.json)](https://github.com/nix-community/home-manager/issues/4989) — WebSearch

## Angle 05 — Selenium/Marionette Focus Control

66. [Selenium: Windows/Tabs Documentation](https://www.selenium.dev/documentation/webdriver/interactions/windows/) *(also cited in Angle 10)* — WebSearch
67. [Selenium Issue #11393: Switch tab without focus](https://github.com/SeleniumHQ/selenium/issues/11393) *(also cited in Angle 06)* — WebSearch
68. [Bug 1124604: Focus parameter for switch_to_window](https://bugzilla.mozilla.org/show_bug.cgi?id=1124604) — WebSearch
69. [Bug 1335085: SwitchToWindow activate/focus events](https://bugzilla.mozilla.org/show_bug.cgi?id=1335085) *(also cited in Angle 06)* — WebSearch
70. [Bug 1398111: Missing focus events in background](https://bugzilla.mozilla.org/show_bug.cgi?id=1398111) — WebSearch
71. [Bug 1216949: Interactions not effective without focus](https://bugzilla.mozilla.org/show_bug.cgi?id=1216949) — WebSearch
72. [W3C WebDriver Specification](https://w3c.github.io/webdriver/) — WebSearch
73. [Fossies: Marionette driver.sys.mjs source](https://fossies.org/linux/firefox/remote/marionette/driver.sys.mjs) — WebSearch
74. [MDN: tabs.insertCSS()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/Tabs/insertCSS) *(also cited in Angle 06)* — WebSearch
75. [Selenium BiDi Browsing Context Docs](https://www.selenium.dev/documentation/webdriver/bidi/w3c/browsing_context/) — WebSearch
76. [Bug 704583: FocusManager testing mode](https://bugzilla.mozilla.org/show_bug.cgi?id=704583) — WebSearch
77. [LambdaTest: Solving Selenium Focus Issues](https://www.lambdatest.com/blog/solving-selenium-focus-issues/) *(also cited in Angle 10)* — WebSearch
78. [W3C BiDi Issue #18: Script execution contexts](https://github.com/w3c/webdriver-bidi/issues/18) *(also cited in Angle 10)* — WebSearch

## Angle 06 — WebExtension tabs API

79. [MDN: tabs.create()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/create) — WebSearch
80. [MDN: tabs.update()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/update) — WebSearch
81. [MDN: tabs.executeScript()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/executeScript) — WebSearch
82. [MDN: scripting.executeScript()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/scripting/executeScript) — WebSearch
83. [MDN: tabs.onActivated](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/onActivated) — WebSearch
84. [MDN: tabs.move()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/move) — WebSearch
85. [MDN: tabs.hide()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/hide) — WebSearch
86. [MDN: tabs.warmup()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/warmup) — WebSearch
87. [MDN: tabs.moveInSuccession()](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/moveInSuccession) — WebSearch
88. [MDN: Content scripts](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Content_scripts) — WebSearch
89. [MDN: Working with the Tabs API](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Working_with_the_Tabs_API) — WebSearch
90. [geckodriver Issue #906: DOM events with parallel browsers](https://github.com/mozilla/geckodriver/issues/906) — WebSearch

## Angle 07 — userChrome.css Techniques

91. [userchrome.org: What is userChrome.css](https://www.userchrome.org/what-is-userchrome-css.html) *(also cited in Angle 10)* — WebSearch
92. [userchrome.org: What is Autoconfig Startup Scripting](https://www.userchrome.org/what-is-userchrome-js.html) — WebSearch
93. [userchrome.org: Firefox Changes Breaking userChrome.css](https://www.userchrome.org/firefox-changes-userchrome-css.html) — WebSearch
94. [GitHub: MrOtherGuy/fx-autoconfig](https://github.com/MrOtherGuy/fx-autoconfig) — WebSearch
95. [GitHub: aminomancer/uc.css.js](https://github.com/aminomancer/uc.css.js/) — WebSearch
96. [GitHub: xiaoxiaoflood/firefox-scripts](https://github.com/xiaoxiaoflood/firefox-scripts) — WebSearch
97. [GitHub: Aris-t2/CustomCSSforFx](https://github.com/Aris-t2/CustomCSSforFx) *(also cited in Angle 10)* — WebSearch
98. [Mozilla archived: CSS -moz-bool-pref()](http://udn.realityripple.com/docs/Mozilla/Gecko/Chrome/CSS/-moz-bool-pref) — WebSearch
99. [firefox-gnome-theme issue #137: -moz-bool-pref](https://github.com/rafaelmardojai/firefox-gnome-theme/issues/137) — WebSearch
100. [GitHub: piroor/treestyletab](https://github.com/piroor/treestyletab) — WebSearch
101. [TST Code Snippets Wiki](https://github.com/piroor/treestyletab/wiki/Code-snippets-for-custom-style-rules) — WebSearch
102. [AMO: TST Colorize Tabs](https://addons.mozilla.org/en-US/firefox/addon/tst-colorize-tabs/) — WebSearch
103. [GitHub: MurzNN/TST-Colored-tabs](https://github.com/MurzNN/TST-Colored-tabs) — WebSearch
104. [GitHub: Sidebery Wiki - Firefox Styles](https://github.com/mbnuqw/sidebery/wiki/Firefox-Styles-Snippets-(via-userChrome.css)) — WebSearch
105. [GitHub: func0der/colorfulTabs](https://github.com/func0der/colorfulTabs) — WebSearch
106. [AMO: ColorTabs](https://addons.mozilla.org/en-US/firefox/addon/colortabs/) — WebSearch
107. [Tor Project GitLab: Issue #25467](https://gitlab.torproject.org/tpo/applications/tor-browser/-/issues/25467) — WebSearch
108. [Tor Project Forum: Safely customizing Tor Browser](https://forum.torproject.org/t/safely-customizing-tor-browser-possible/6660) — WebSearch
109. [gHacks: Firefox 69 userChrome.css disabled by default](https://www.ghacks.net/2019/05/24/firefox-69-userchrome-css-and-usercontent-css-disabled-by-default/) — WebSearch
110. [GitHub: black7375/Firefox-UI-Fix Preference docs](https://github.com/black7375/Firefox-UI-Fix/blob/master/docs/Preference.md) — WebSearch
111. [geckodriver issue #1067: Global JS variables](https://github.com/mozilla/geckodriver/issues/1067) — WebSearch
112. [CopyProgramming: Auto color tabs by URL/domain](https://copyprogramming.com/howto/auto-color-of-tabs-in-firefox-based-on-url-domain) — WebSearch
113. [Selenium docs: Firefox specific functionality](https://www.selenium.dev/documentation/webdriver/browsers/firefox/) — WebSearch

## Angle 08 — Known Failures and Issues

114. [Selenium Focus Stealing Documentation](https://www.selenium.dev/documentation/legacy/selenium_2/focus_stealing/) *(also cited in Angle 10)* — Browse
115. [geckodriver #1770: Race condition switching windows](https://github.com/mozilla/geckodriver/issues/1770) — Browse
116. [geckodriver #1769: Opening windows breaks handles](https://github.com/mozilla/geckodriver/issues/1769) — Browse
117. [Selenium #15318: Switch to window broken Chrome 133](https://github.com/SeleniumHQ/selenium/issues/15318) — Browse
118. [SO: Set browser tab background color with extension](https://stackoverflow.com/questions/70446946/set-the-browsers-tab-background-color-with-browser-extension-addon) — Browse
119. [r/FirefoxCSS: 113 completely broke my userchrome.css](https://www.reddit.com/r/FirefoxCSS/comments/13cx7wk/113_completely_broke_my_userchromecss_and_i_dont/) — Browse
120. [r/firefox: Version 141 breaks all userChrome.css](https://www.reddit.com/r/firefox/comments/1m8q2tx/version_141_breaks_all_userchromecss/) — Browse
121. [r/FirefoxCSS: Update to 108.0 broke tabs CSS](https://www.reddit.com/r/FirefoxCSS/comments/znk650/if_update_to_1080_broke_your_tabs_css_this_might/) — Browse
122. [Mike Kaply: Don't Unpack and Repack omni.ja](https://mike.kaply.com/2013/05/06/dont-unpack-and-repack-omni-jar/) — Browse
123. [Shallowsky: Modifying Firefox Files Inside Omni.ja](https://shallowsky.com/blog/tech/web/modifying-omni.ja.html) — Browse
124. [joegreen.pl: Firefox Theme API issues](https://blog.joegreen.pl/firefox-webextensions-theme-api.html) — Browse
125. [Mozilla Discourse: Focusing on Tab Bar (June 2025)](https://discourse.mozilla.org/t/focusing-on-tab-bar/143936) — Browse
126. [Mozilla Discourse: How to change tab color](https://discourse.mozilla.org/t/how-to-change-the-color-or-highlighted-status-of-a-tab/22336) — Browse
127. [Bug 332195: alert() steals focus from other tab](https://bugzilla.mozilla.org/show_bug.cgi?id=332195) — Browse
128. [Bug 1663429: Race condition fix for switchToTab](https://bugzilla.mozilla.org/show_bug.cgi?id=1663429) — Browse
129. [SebastianSimon/firefox-omni-tweaks](https://github.com/SebastianSimon/firefox-omni-tweaks) *(also cited in Angle 09)* — Browse
130. [r/FirefoxCSS: FF updates keep breaking my CSS](https://www.reddit.com/r/FirefoxCSS/comments/12lcarq/i_am_getting_desperateff_updates_keep_breaking_my/) — Browse

## Angle 09 — Contrarian: Skeptical Critique

131. [Mozilla Support: Edit omni.ja](https://support.mozilla.org/en-US/questions/1319962) — Browse
132. [r/firefox: Omni.ja file not working](https://www.reddit.com/r/firefox/comments/1jcbdi6/omnija_file_not_working/) — Browse
133. [Selenium #12759: Enable control of tabs without focus](https://github.com/SeleniumHQ/selenium/issues/12759) — Browse
134. [SO: Switch tabs without focusing](https://stackoverflow.com/questions/67650964/how-to-switch-tabs-in-selenium-without-focusing-the-window) — Browse
135. [Chrome for Developers: WebDriver BiDi production-ready](https://developer.chrome.com/blog/firefox-support-in-puppeteer-with-webdriver-bidi) — Browse
136. [Playwright #32577: BiDi limitations blocking adoption](https://github.com/microsoft/playwright/issues/32577) — Browse
137. [MozillaWiki: Containers project](https://wiki.mozilla.org/Security/Contextual_Identity_Project/Containers) — Browse
138. [Tridactyl docs: contextualIdentities colors](https://tridactyl.xyz/build/static/docs/modules/_src_excmds_.html) — Browse
139. [glacambre/firefox-patches: Post-build patch](https://github.com/glacambre/firefox-patches/issues/1) — Browse
140. [BrowserStack: Parallel Test Execution](https://www.browserstack.com/guide/parallel-testing-with-selenium) — Browse

## Angle 10 — Integration Strategy

141. [9to5Linux: Tor Browser 15.0 on Firefox 140 ESR](https://9to5linux.com/tor-browser-15-0-anonymous-web-browser-is-out-based-on-firefox-140-esr-series) — Both
142. [OTF: Transitioning Tor Browser to ESR 140](https://www.opentech.fund/projects-we-support/supported-projects/transitioning-tor-browser-to-firefox-esr-140/) — Both
143. [Bug 1710425: Chrome Context System Access Flag](https://bugzilla.mozilla.org/show_bug.cgi?id=1710425) — Both
144. [Geckodriver Flags Documentation](https://firefox-source-docs.mozilla.org/testing/geckodriver/Flags.html) — Both
145. [Firefox Nightly Blog: 100% WebDriver BiDi](https://blog.nightly.mozilla.org/2024/07/18/100-webdriver-bidi-and-101-more-these-weeks-in-firefox-issue-164/) — Both
146. [Firefox Browser Console Documentation](https://firefox-source-docs.mozilla.org/devtools-user/browser_console/index.html) — Both

---

## Cross-Angle Source Overlap

| Source | Angles |
|---|---|
| tabbrowser.js on Searchfox | 01, 02, 04, 10 |
| tab.js on Searchfox | 01, 02 |
| Firefox tabbrowser Source Docs | 01, 05, 10 |
| Selenium Python API: Firefox WebDriver | 01, 05, 07, 10 |
| Marionette Driver Docs | 01, 05, 10 |
| Marionette Introduction | 01, 05, 07 |
| MDN: contextualIdentities | 01, 04 |
| MDN: Work with contextual identities | 01, 04, 10 |
| Mozilla Support: Tab Customization (1446142) | 01, 02, 07 |
| Raymii.org Proton Tab Styling | 01, 02, 07, 10 |
| Bug 1387117: Container indicator | 01, 02, 03, 10 |
| Bug 1325057: Custom container colors | 02, 03, 04, 07 |
| Bug 487242: Tab visited attribute | 01, 02, 07 |
| Prominent container tab color (dangh gist) | 02, 04, 07 |
| Bug 1439734: Tab line color | 02, 03 |
| W3C WebDriver BiDi Spec | 04, 05, 10 |
| Selenium Issue #11393 | 05, 06 |
| Bug 1335085: SwitchToWindow events | 05, 06 |
| MDN: tabs.insertCSS | 05, 06 |
| Selenium Focus Stealing Docs | 08, 10 |
| firefox-omni-tweaks | 08, 09 |
| userchrome.org Proton UI | 02, 07, 10 |
| MrOtherGuy/firefox-csshacks | 02, 07 |
| Mozilla Support: Active tab colour (1282095) | 01, 02, 07 |

## Source Quality Notes

- **Primary/official sources** (MDN, Searchfox, Bugzilla, Selenium docs): High quality, current, authoritative. These form the core evidence base.
- **Community sources** (Reddit, Mozilla Support forums, userchrome.org): Valuable for real-world breakage reports and practical recipes, but may be outdated. Multiple corroborating reports increase confidence.
- **GitHub projects** (fx-autoconfig, firefox-csshacks, uc.css.js): Active maintenance indicates ongoing viability. Projects with years of commit history are more reliable.
- **Blog posts** (Mike Kaply, Danny Guo, joegreen.pl): Expert opinions with varying recency. Mike Kaply's omni.ja warning is from 2013 but remains relevant.
- **Stack Overflow**: Mixed quality. High-rep answers (Xan, 77.9k) are reliable for API limitations. Lower-rep answers may be outdated.
- **Gap**: No primary source found for Tor Browser's specific behavior with chrome context, container tabs, or omni.ja patching. All Tor Browser claims are inferred from Firefox ESR behavior.
