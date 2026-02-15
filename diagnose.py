#!/usr/bin/env python3
"""Diagnostic: dump all proxy/network/RFP prefs from a running Firefox instance."""

from browse.firefox import launch_firefox

print("Launching Firefox ESR in RFP mode...")
driver = launch_firefox()

print("\n=== Dumping privacy/network prefs from about:config ===\n")

# Use chrome context to read all prefs
with driver.context(driver.CONTEXT_CHROME):
    prefs = driver.execute_script("""
        let results = {};
        let prefService = Services.prefs;
        // Get all prefs matching these patterns
        let patterns = ['network.proxy', 'network.dns', 'network.cookie',
                        'privacy.resistFingerprinting', 'privacy.firstparty',
                        'privacy.trackingprotection', 'media.peerconnection',
                        'geo.enabled', 'dom.battery', 'media.navigator',
                        'toolkit.telemetry', 'webdriver'];
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
