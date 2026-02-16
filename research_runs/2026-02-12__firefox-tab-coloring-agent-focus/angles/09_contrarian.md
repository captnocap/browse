# Angle 09 — Contrarian: Skeptical Critique

## Claims (with confidence)

- Claim (high): **omni.ja patching is destroyed on every Firefox update** -- the file is replaced wholesale with each version bump, requiring re-patching after every update. A Mozilla moderator (cor-el) confirmed that "the two omni.ja archives are signed in current release (they contain a META-INF folder), so it isn't possible to edit them" in standard release builds. The firefox-omni-tweaks project has had to maintain compatibility across Firefox Nightly 91 through 147 (5+ years of constant breakage-chasing).

- Claim (high): **WebDriver's switch_to.window() focus model is baked into the W3C spec and cannot be circumvented** -- Selenium maintainer titusfortner stated "This really comes down to how webdriver specification requires it" and that the spec mandates a single active browsing context per session. The Selenium team explicitly closed a feature request (#12759) for controlling tabs without focus as "not planned," saying the everyday use case assumes a single active tab.

- Claim (high): **WebDriver BiDi is not yet production-ready for complex automation despite claims** -- while Chrome/Puppeteer declared BiDi "production-ready" in Aug 2024 (Firefox 129), Playwright's Sept 2024 audit found only 1469/3877 tests passing on Firefox (38%) with a massive list of blocking issues including broken viewport setting, missing network interception, broken authentication, missing download events, and intermittent crashes. The issue remains open as of Feb 2026.

- Claim (medium): **Container tabs (contextualIdentities API) are a more robust coloring mechanism than omni.ja CSS patching** -- containers are a supported WebExtension API that survives updates, provides per-tab colored underlines natively, and isolates cookies/storage. However, containers only support 8 predefined color names: blue, turquoise, green, yellow, orange, red, pink, purple. For 10 agents, you would need to reuse colors or find CSS overrides anyway.

- Claim (medium): **Separate browser instances per agent would eliminate both the tab coloring and focus-hopping problems entirely** -- Selenium Grid's standard architecture uses one browser instance per test worker. This sidesteps the focus switching problem (each agent owns its window), eliminates the need for tab coloring (each window is its own visual context), and avoids all chrome-context hacking. The cost is higher memory usage per agent.

- Claim (medium): **Tor Browser's relationship with Firefox containers is complicated and may conflict** -- Tor Browser implements its own First Party Isolation (FPI) which predates and is stricter than Firefox's standard container tabs. FPI uses OriginAttributes similar to containers but for different purposes (anti-tracking rather than multi-identity). Layering container-tab coloring on top of Tor Browser's FPI could create unpredictable interactions with cookie/storage isolation.

- Claim (low): **omni.ja repacking has silent failure modes** -- Reddit users report omni.ja edits silently failing (Firefox falls back to cached version or refuses to start), requiring --purgecaches flags, hex-editor workarounds (to avoid file size changes from recompression), and careful handling of the archive format. Using 7-zip to repack changes file size and breaks things; users had to use hex editors to maintain byte-identical size.

- Claim (low): **The "right" long-term solution is WebDriver BiDi's browsing context model, but it won't be ready for years** -- Selenium maintainer titusfortner noted they'd "be working on replacing the direct method implementation with the new WebDriver-BiDi specification over the next few years." Playwright's 2024 audit showed the gap is enormous, suggesting full BiDi parity is a multi-year effort.

## Evidence

- omni.ja is replaced every update, signed in release builds, cannot be edited without workarounds -- [Mozilla Support Forum - Edit omni.ja](https://support.mozilla.org/en-US/questions/1319962)
- firefox-omni-tweaks requires re-execution after every Firefox update, tested across Nightly 91-147 -- [SebastianSimon/firefox-omni-tweaks](https://github.com/SebastianSimon/firefox-omni-tweaks)
- Reddit users report omni.ja edits failing silently, requiring hex editors to maintain file size, --purgecaches flags -- [r/firefox - Omni.ja file not working](https://www.reddit.com/r/firefox/comments/1jcbdi6/omnija_file_not_working/)
- Selenium closed "Enable control of tabs without focus" as not planned; titusfortner: "This really comes down to how webdriver specification requires it" -- [SeleniumHQ/selenium#12759](https://github.com/SeleniumHQ/selenium/issues/12759)
- StackOverflow consensus: "You can not achieve that (change focus without focus) in Selenium" -- [SO: switch tabs without focusing](https://stackoverflow.com/questions/67650964/how-to-switch-tabs-in-selenium-without-focusing-the-window)
- WebDriver BiDi declared "production-ready" in Firefox 129 / Puppeteer 23, but only for basic automation -- [Chrome for Developers blog](https://developer.chrome.com/blog/firefox-support-in-puppeteer-with-webdriver-bidi)
- Playwright found only 38% of tests passing on Firefox with BiDi, massive list of spec gaps and Firefox bugs -- [microsoft/playwright#32577](https://github.com/microsoft/playwright/issues/32577)
- contextualIdentities API supports only 8 color names (blue, turquoise, green, yellow, orange, red, pink, purple) -- [Tridactyl docs referencing contextualIdentities color values](https://tridactyl.xyz/build/static/docs/modules/_src_excmds_.html)
- Firefox Containers separate cookies, localStorage, indexedDB, HTTP cache, image cache per container; built-in colored tab underlines -- [MozillaWiki - Containers](https://wiki.mozilla.org/Security/Contextual_Identity_Project/Containers)
- Tor Browser's FPI predates and is stricter than standard container tabs; uses similar OriginAttributes mechanism -- [MozillaWiki - Containers (Alternative Features section)](https://wiki.mozilla.org/Security/Contextual_Identity_Project/Containers)
- Selenium Grid standard architecture: one browser instance per test worker, avoids tab/focus issues entirely -- [BrowserStack - Parallel Testing](https://www.browserstack.com/guide/parallel-testing-with-selenium)

## What I'm unsure about

- Whether Tor Browser specifically disables the contextualIdentities WebExtension API or if it works alongside FPI. I could not find a definitive source on this.
- Whether the omni.ja signing in release builds also applies to Tor Browser builds (which are based on Firefox ESR). Tor Browser may use unsigned builds that still allow editing.
- How much actual RAM overhead separate Tor Browser instances add per agent vs. tabs in a single instance. The "too expensive" argument against separate windows needs benchmarking.
- Whether WebDriver BiDi will eventually support truly parallel browsing context control (operating on non-focused tabs without switching). The spec's direction is unclear on this specific capability.
- Whether userChrome.css could achieve the same tab coloring effect as omni.ja patching without touching internal files -- this would survive updates but has its own limitations (Firefox has been threatening to remove userChrome.css support).
- The glacambre/firefox-patches project mentioned "post-build patching" of omni.ja as a technique, but I could not find reports of long-term maintainability from anyone using it in production automation tools.

## Sources

- [Mozilla Support Forum - Edit omni.ja](https://support.mozilla.org/en-US/questions/1319962)
- [SebastianSimon/firefox-omni-tweaks (GitHub)](https://github.com/SebastianSimon/firefox-omni-tweaks)
- [r/firefox - Omni.ja file not working](https://www.reddit.com/r/firefox/comments/1jcbdi6/omnija_file_not_working/)
- [SeleniumHQ/selenium#12759 - Enable control of tabs without focus](https://github.com/SeleniumHQ/selenium/issues/12759)
- [StackOverflow - How to switch tabs without focusing the window](https://stackoverflow.com/questions/67650964/how-to-switch-tabs-in-selenium-without-focusing-the-window)
- [Chrome for Developers - WebDriver BiDi production-ready](https://developer.chrome.com/blog/firefox-support-in-puppeteer-with-webdriver-bidi)
- [microsoft/playwright#32577 - Current limitations blocking BiDi adoption](https://github.com/microsoft/playwright/issues/32577)
- [MozillaWiki - Security/Contextual Identity Project/Containers](https://wiki.mozilla.org/Security/Contextual_Identity_Project/Containers)
- [Tridactyl docs - contextualIdentities color values](https://tridactyl.xyz/build/static/docs/modules/_src_excmds_.html)
- [glacambre/firefox-patches#1 - Post-build patch](https://github.com/glacambre/firefox-patches/issues/1)
- [BrowserStack - Parallel Test Execution in Selenium](https://www.browserstack.com/guide/parallel-testing-with-selenium)
