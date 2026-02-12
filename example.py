#!/usr/bin/env python3
"""Quick test — launches the agent browser and visits a fingerprint test site."""

import os
import sys

# Read config from setup.sh output
conf = {}
conf_path = os.path.join(os.path.dirname(__file__), "browse.conf")
if os.path.exists(conf_path):
    with open(conf_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                conf[k.strip()] = v.strip()

TBB_PATH = conf.get("TBB_PATH") or os.environ.get("TBB_PATH")
GECKODRIVER = conf.get("GECKODRIVER_PATH") or os.environ.get("GECKODRIVER_PATH")

if not TBB_PATH:
    print("Error: TBB_PATH not set. Run setup.sh first or set the environment variable.")
    sys.exit(1)

# Put geckodriver on PATH if we know where it is
if GECKODRIVER and os.path.isfile(GECKODRIVER):
    geckodriver_dir = os.path.dirname(GECKODRIVER)
    os.environ["PATH"] = geckodriver_dir + ":" + os.environ.get("PATH", "")

from browse import AgentBrowser

print(f"Launching agent browser (Tor Browser engine, direct connection)...")
print(f"  TBB path: {TBB_PATH}")
print()

with AgentBrowser(TBB_PATH) as browser:
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
