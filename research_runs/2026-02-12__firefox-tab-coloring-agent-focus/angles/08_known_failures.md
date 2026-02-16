# Angle 08 — Known Failures and Issues

## Claims (with confidence)

- Claim (high): **Selenium on Linux requires an LD_PRELOAD hack (`x_ignore_nofocus.c`) to prevent focus stealing, and this hack breaks down with multiple windows.** The official Selenium documentation describes a complex system where FocusOut X11 events are intercepted and discarded via a shared library loaded with LD_PRELOAD. This works for single-window cases, but when multiple windows/tabs are involved, a file-based signaling mechanism (`/tmp/switch_window_started`) is required for coordination between WebDriver's Firefox extension and the focus-management component. Window creation, switching, and closing each have their own edge cases. This is legacy Selenium 2 architecture but reveals the fundamental difficulty of focus management in Firefox automation.

- Claim (high): **There is no WebExtension API to color individual browser tabs -- `browser.theme.update()` only affects the active/selected tab's chrome area (frame, toolbar), not inactive tab backgrounds independently.** The Stack Overflow answer by Xan (77.9k rep) directly states: "there's nothing in Firefox or Chrome API that allows you to color individual tabs easily." The Colorful Tabs extension uses `browser.theme.update()` as a workaround but "it only affects the color of the currently selected tab (and the address bar), not providing you with a good overview." The theme API is window-scoped, not tab-scoped. Per-tab coloring is fundamentally impossible through the WebExtension theme API alone.

- Claim (high): **`userChrome.css` tab styling breaks frequently across Firefox major versions, and Mozilla explicitly does not guarantee stability.** Documented breakages include: Firefox 108 (tab CSS selectors changed), Firefox 113 (major breakage -- `-moz-box-ordinal-group` and tab ordering CSS broke, requiring rewrite of tabs-on-bottom hacks), Firefox 133 (tab bar relocation broke CSS), and Firefox 141 (color/theme handling changed, scrambled dark theme customizations). Mozilla's own documentation states: "Firefox is a work in progress and to allow for continuous innovation, Mozilla cannot guarantee that the styled elements will not change." The r/FirefoxCSS subreddit has repeated threads every few releases with titles like "X completely broke my userchrome.css."

- Claim (high): **Geckodriver has a confirmed race condition when switching windows/tabs while tabs are being created or closed.** Issue #1770 in mozilla/geckodriver documented a race condition where `switchToTab` in Marionette throws `TypeError: this.mm is null` when a tab is closed at the same time as a switch attempt. The error occurred in `WebElementEventTarget@chrome://marionette/content/dom.js:46:5` and `switchToTab@chrome://marionette/content/browser.js:525:26`. This was timing-dependent and especially reproducible in the Watir test suite. Fixed in Firefox Nightly 82 (Bugzilla #1663429), but similar timing-dependent issues recur in different forms.

- Claim (high): **Repacking `omni.ja` is fragile, version-sensitive, and officially discouraged by Mozilla.** Mike Kaply (Mozilla consultant) explicitly warns: "If any step in your process to customize and deploy Firefox involves unpacking and repacking omni.ja, you're probably doing it wrong." Key failure modes include: (1) the original omni.ja uses zero compression but naive repacking uses standard compression, producing a file 1/3 the size that may cause performance issues; (2) XUL-era chrome override methods for omni.ja files are now obsolete and do not work; (3) unzip produces scary warnings ("extra bytes at beginning," "reported length of central directory is -34187320 bytes too long") that are actually expected but alarming; (4) the `--purgecaches` flag must be used after modifying omni.ja or changes will not be reflected; (5) Firefox updates overwrite omni.ja, destroying all modifications.

- Claim (high): **`browser.theme.getCurrent()` returns an empty object for built-in and legacy themes, making theme backup/restore broken for extensions that temporarily change tab colors.** Documented by joegreen.pl in detail: when an extension changes the theme via `browser.theme.update()` and then wants to restore the original theme, `browser.theme.getCurrent()` returns `{}` if the original was a built-in theme (like "Light" or "Dark"). Calling `browser.theme.update()` with the empty object resets to the bare default, not the user's selected theme. `browser.theme.reset()` has the same problem -- documentation confirms it "will always reset the theme back to the original default theme, even if the user had selected a different theme before this extension's theme was applied."

- Claim (medium): **Firefox's `tabs.highlight()` API is only supported on Chrome, not Firefox, eliminating a potential path for programmatic tab highlighting.** The MDN compatibility table clearly shows `tabs.highlight()` is Chrome-only. On Firefox, the only extension APIs for tab management are `tabs.update()` (which can set active tab) and `windows.update()` (which can set focused window). Neither provides visual differentiation of individual tabs.

- Claim (medium): **Chrome 133 introduced a regression where PDF tabs create duplicate window handles, breaking Selenium's `switchTo().window()` for all multi-tab workflows.** While Chrome-specific, this illustrates how browser updates can unexpectedly break tab-switching automation. The Selenium issue #15318 documents that switching back to a parent window after closing a child window opens a new blank window and throws "No such window." Geckodriver/Firefox was specifically noted as NOT having this issue, but the pattern of browser-version-specific regressions in tab handling is universal.

- Claim (medium): **On Linux, the X11 window manager can steal focus from Firefox during automation, and there is no reliable cross-platform way to prevent this.** The Selenium focus-stealing documentation describes the need to intercept X11 FocusOut events at the XLib layer. This approach is Linux-specific and does not apply to Wayland. The solution requires cooperation between multiple components and falls apart when the window manager aggressively manages focus (e.g., "focus follows mouse" policies).

- Claim (medium): **Extensions cannot programmatically focus the tab bar or modify individual tab strip appearance.** Confirmed by Mozilla's Simeon Vincent (WebExtensions Community Group member) in June 2025: "Currently an extension's ability to manage focus in Firefox is limited to switching focus between windows (using windows.update()) and selecting an active tab (using tabs.update()). [...] browser vendors are very hesitant about allowing extensions to do things like focus the address bar." There is no API to style, decorate, or modify the visual appearance of a given tab from an extension.

- Claim (low): **`browser.tabs.loadDivertedInBackground` about:config preference can prevent some focus-stealing when opening tabs, but it is not controllable via Selenium automation and may be ignored in some scenarios.** Stack Overflow answers and Mozilla support threads mention this preference, but its behavior is inconsistent and it does not apply to programmatic tab creation via WebDriver.

## Evidence

- Selenium officially documents a complex LD_PRELOAD-based hack for focus management on Linux that intercepts X11 FocusOut events -- [Selenium Focus Stealing Documentation](https://www.selenium.dev/documentation/legacy/selenium_2/focus_stealing/)
- Geckodriver issue #1770 confirms a race condition in Marionette's `switchToTab` when windows are simultaneously created/closed, producing "TypeError: this.mm is null" -- [geckodriver #1770](https://github.com/mozilla/geckodriver/issues/1770)
- Geckodriver issue #1769 documents that "Opening new windows breaks window_handles" starting in Firefox 81 -- [geckodriver #1769](https://github.com/mozilla/geckodriver/issues/1769)
- Stack Overflow answer with 77.9k rep user confirms "there's nothing in Firefox or Chrome API that allows you to color individual tabs easily" and that Colorful Tabs only colors the active tab -- [SO #70447889](https://stackoverflow.com/questions/70446946/set-the-browsers-tab-background-color-with-browser-extension-addon)
- Firefox 113 broke tab-ordering CSS hacks using `-moz-box-ordinal-group`, requiring complete rewrites for tabs-on-bottom layouts -- [r/FirefoxCSS thread](https://www.reddit.com/r/FirefoxCSS/comments/13cx7wk/113_completely_broke_my_userchromecss_and_i_dont/)
- Firefox 141 scrambled color/theme customizations; profile format change prevented simple rollback -- [r/firefox thread](https://www.reddit.com/r/firefox/comments/1m8q2tx/version_141_breaks_all_userchromecss/)
- Firefox 108 broke tab CSS selectors, requiring removal of specific CSS rules -- [r/FirefoxCSS thread](https://www.reddit.com/r/FirefoxCSS/comments/znk650/if_update_to_1080_broke_your_tabs_css_this_might/)
- Mike Kaply (Mozilla consultant) explicitly warns against unpacking/repacking omni.ja, stating almost all modifications can be done via other mechanisms -- [Mike's Musings](https://mike.kaply.com/2013/05/06/dont-unpack-and-repack-omni-jar/)
- Akkana Peck documents that repacked omni.ja is 1/3 the size of original due to compression differences, and unzip produces alarming warnings about extra bytes -- [Shallowsky blog](https://shallowsky.com/blog/tech/web/modifying-omni.ja.html)
- `browser.theme.getCurrent()` returns empty object for built-in themes, and `browser.theme.reset()` always resets to default (not user's selected theme) -- [joegreen.pl blog](https://blog.joegreen.pl/firefox-webextensions-theme-api.html)
- Mozilla's Simeon Vincent confirms extensions cannot focus the tab bar or modify tab strip appearance (June 2025) -- [Mozilla Discourse](https://discourse.mozilla.org/t/focusing-on-tab-bar/143936)
- Mozilla Discourse thread from 2017 confirms no API existed then for changing tab color/highlighting, pointing to Bugzilla #1320585 for future work -- [Mozilla Discourse](https://discourse.mozilla.org/t/how-to-change-the-color-or-highlighted-status-of-a-tab/22336)
- Bugzilla #332195 documents that `alert()` steals focus from other tabs, which was only partially fixed by tab-modal prompts -- [Bugzilla](https://bugzilla.mozilla.org/show_bug.cgi?id=332195)
- Selenium issue #15318 documents Chrome 133 creating duplicate window handles for PDF tabs, breaking switchTo().window() -- [Selenium #15318](https://github.com/SeleniumHQ/selenium/issues/15318)
- Bugzilla #1663429 was the specific fix for the geckodriver race condition in switchToTab -- [Bugzilla](https://bugzilla.mozilla.org/show_bug.cgi?id=1663429)

## What I'm unsure about

- Whether Tor Browser's specific hardening (no WebExtensions, restricted about:config) introduces additional failure modes beyond standard Firefox when it comes to userChrome.css tab styling. Tor Browser is based on Firefox ESR so it may dodge some breakages but also may strip userChrome.css support entirely.
- The exact current state of the `browser.theme.getCurrent()` bug -- whether built-in themes have been rewritten to WebExtensions as was promised, which would fix the empty-object return. This was supposedly planned but I could not confirm it was completed.
- Whether Selenium 4's BiDi protocol (WebDriver BiDi) changes the focus-management story fundamentally, or if the same X11-level issues remain.
- How Wayland (replacing X11 on Linux) affects the focus-stealing problem -- the Selenium LD_PRELOAD hack is entirely X11-specific and would not function on Wayland at all.
- Whether Firefox's new native tab groups feature (shipping 2025-2026) introduces any new API surface for per-group or per-tab coloring that extensions could leverage.
- The extent to which `omni.ja` modification failure modes apply to Tor Browser specifically, which may use a different packaging structure or verification.
- Whether there are any Marionette-level (not WebDriver-level) commands that could perform tab operations without triggering focus changes, bypassing the standard selenium switch_to mechanism.

## Sources

- [Selenium Focus Stealing Documentation](https://www.selenium.dev/documentation/legacy/selenium_2/focus_stealing/)
- [geckodriver #1770 - Race condition when switching windows](https://github.com/mozilla/geckodriver/issues/1770)
- [geckodriver #1769 - Opening new windows breaks window_handles](https://github.com/mozilla/geckodriver/issues/1769)
- [Selenium #15318 - Switch to window broken after Chrome 133](https://github.com/SeleniumHQ/selenium/issues/15318)
- [SO - Set browser tab background color with extension](https://stackoverflow.com/questions/70446946/set-the-browsers-tab-background-color-with-browser-extension-addon)
- [r/FirefoxCSS - 113 completely broke my userchrome.css](https://www.reddit.com/r/FirefoxCSS/comments/13cx7wk/113_completely_broke_my_userchromecss_and_i_dont/)
- [r/firefox - Version 141 breaks all userChrome.css customizations](https://www.reddit.com/r/firefox/comments/1m8q2tx/version_141_breaks_all_userchromecss/)
- [r/FirefoxCSS - If update to 108.0 broke your tabs CSS](https://www.reddit.com/r/FirefoxCSS/comments/znk650/if_update_to_1080_broke_your_tabs_css_this_might/)
- [Mike Kaply - Don't Unpack and Repack omni.ja](https://mike.kaply.com/2013/05/06/dont-unpack-and-repack-omni-jar/)
- [Shallowsky - Modifying Firefox Files Inside Omni.ja](https://shallowsky.com/blog/tech/web/modifying-omni.ja.html)
- [joegreen.pl - Firefox WebExtensions Theme API issue](https://blog.joegreen.pl/firefox-webextensions-theme-api.html)
- [Mozilla Discourse - Focusing on Tab Bar (June 2025)](https://discourse.mozilla.org/t/focusing-on-tab-bar/143936)
- [Mozilla Discourse - How to change color or highlighted status of a tab](https://discourse.mozilla.org/t/how-to-change-the-color-or-highlighted-status-of-a-tab/22336)
- [Bugzilla #332195 - alert() steals focus from other tab](https://bugzilla.mozilla.org/show_bug.cgi?id=332195)
- [Bugzilla #1663429 - Race condition fix for switchToTab](https://bugzilla.mozilla.org/show_bug.cgi?id=1663429)
- [r/FirefoxCSS - I am getting desperate...FF updates keep breaking my CSS](https://www.reddit.com/r/FirefoxCSS/comments/12lcarq/i_am_getting_desperateff_updates_keep_breaking_my/)
- [GitHub - SebastianSimon/firefox-omni-tweaks](https://github.com/SebastianSimon/firefox-omni-tweaks)
