#!/usr/bin/env python3
"""Diagnostic: dump all proxy/network prefs from a running TB instance."""

import os, sys, json

conf = {}
conf_path = os.path.join(os.path.dirname(__file__), "browse.conf")
if os.path.exists(conf_path):
    with open(conf_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                conf[k.strip()] = v.strip()

TBB_PATH = conf.get("TBB_PATH")
GECKODRIVER = conf.get("GECKODRIVER_PATH")
if GECKODRIVER and os.path.isfile(GECKODRIVER):
    os.environ["PATH"] = os.path.dirname(GECKODRIVER) + ":" + os.environ.get("PATH", "")

from browse.tbselenium.tbdriver import TorBrowserDriver
from browse.tbselenium import common as cm

print("Launching TB in direct mode...")
driver = TorBrowserDriver(TBB_PATH, tor_cfg=cm.USE_DIRECT)

print("\n=== Dumping proxy/network prefs from about:config ===\n")

# Use chrome context to read all prefs
with driver.context(driver.CONTEXT_CHROME):
    prefs = driver.execute_script("""
        let results = {};
        let prefService = Services.prefs;
        // Get all prefs matching these patterns
        let patterns = ['network.proxy', 'network.dns', 'extensions.torlauncher',
                        'extensions.torbutton', 'network.trr', 'network.captive',
                        'privacy.resistFingerprinting', 'torbrowser'];
        for (let pattern of patterns) {
            let children = prefService.getChildList(pattern);
            for (let pref of children) {
                try {
                    let type = prefService.getPrefType(pref);
                    if (type === prefService.PREF_STRING) {
                        results[pref] = prefService.getStringPref(pref);
                    } else if (type === prefService.PREF_INT) {
                        results[pref] = prefService.getIntPref(pref);
                    } else if (type === prefService.PREF_BOOL) {
                        results[pref] = prefService.getBoolPref(pref);
                    }
                } catch(e) {}
            }
        }
        return results;
    """)

# Print grouped
for key in sorted(prefs.keys()):
    val = prefs[key]
    print(f"  {key} = {val!r}")

print(f"\n=== Total: {len(prefs)} prefs ===\n")

# Quick connectivity test
print("Testing DNS resolution via JS...")
with driver.context(driver.CONTEXT_CONTENT):
    try:
        driver.set_page_load_timeout(10)
        driver.get("http://example.com")
        print(f"  SUCCESS: loaded {driver.current_url}")
    except Exception as e:
        print(f"  FAILED: {e}")

driver.quit()
print("\nDone.")
