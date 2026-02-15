#!/usr/bin/env python3
"""Quick test — launches the agent browser and visits a fingerprint test site."""

import os
import sys

from browse import AgentBrowser

print("Launching agent browser (Firefox ESR + RFP)...")
print()

with AgentBrowser() as browser:
    # Visit the bot detection test page
    print("Navigating to bot.sannysoft.com...")
    content = browser.navigate("https://bot.sannysoft.com")
    print(f"  Title: {content.title}")
    print(f"  URL:   {content.url}")
    print()

    # Take a screenshot
    screenshot_path = os.path.join(os.path.dirname(__file__), "stealth-test.png")
    browser.screenshot(screenshot_path)
    print(f"  Screenshot saved: {screenshot_path}")
    print()

    # Try a second site
    print("Navigating to browserleaks.com/canvas...")
    content = browser.navigate("https://browserleaks.com/canvas")
    print(f"  Title: {content.title}")
    print(f"  Links found: {len(content.links)}")
    print()

    # Show current fingerprint-relevant info
    ua = browser.execute_js("return navigator.userAgent")
    platform = browser.execute_js("return navigator.platform")
    webdriver = browser.execute_js("return navigator.webdriver")
    plugins = browser.execute_js("return navigator.plugins.length")
    print("  Browser fingerprint signals:")
    print(f"    User-Agent: {ua}")
    print(f"    Platform:   {platform}")
    print(f"    webdriver:  {webdriver}")
    print(f"    Plugins:    {plugins}")

    print("\nBrowser is open. Press Enter to close it...")
    input()

print("Done. Browser closed.")
