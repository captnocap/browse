"""Stealth patches for hiding automation signals.

Three layers:

Layer 1 — Binary patch: Replaces the "webdriver" string in libxul.so so the
    navigator.webdriver property ceases to exist entirely. Not overridden,
    not false — genuinely undefined, same as a normal browser.

Layer 1b — Omni.ja patch: Replaces the red candy-stripe automation indicator
    CSS with hidden rules so the candycane never appears.

Layer 2 — WebExtension: Injects a content script at document_start in the
    MAIN world that does a prototype-level override of navigator.webdriver
    as defense-in-depth. Also manages per-tab agent indicators and theme.

All patches work on both Firefox ESR and Tor Browser (same engine).
"""

import json
import os
import random
import shutil
import string
import tempfile
import zipfile


# ─── Layer 1: Binary Patch ────────────────────────────────────────────────

# The WebIDL property name in libxul.so. When replaced, navigator.webdriver
# ceases to exist. Marionette still works because its control protocol
# doesn't depend on this DOM property name.
_PATCH_TARGET = b"webdriver"

# File that records what we patched (so we can verify / re-patch)
_PATCH_MARKER = ".browse_patched"


def _generate_replacement(length):
    """Generate a random lowercase string of the given length."""
    return "".join(random.choices(string.ascii_lowercase, k=length)).encode()


def _find_libxul(firefox_path):
    """Locate libxul.so in a Firefox or Tor Browser directory."""
    # Firefox ESR: libxul.so is at the root
    candidate = os.path.join(firefox_path, "libxul.so")
    if os.path.exists(candidate):
        return candidate
    # Tor Browser: libxul.so is under Browser/
    candidate = os.path.join(firefox_path, "Browser", "libxul.so")
    if os.path.exists(candidate):
        return candidate
    return None


def _find_omni(firefox_path):
    """Locate browser/omni.ja in a Firefox or Tor Browser directory."""
    # Firefox ESR: browser/omni.ja at the root
    candidate = os.path.join(firefox_path, "browser", "omni.ja")
    if os.path.exists(candidate):
        return candidate
    # Tor Browser: Browser/browser/omni.ja
    candidate = os.path.join(firefox_path, "Browser", "browser", "omni.ja")
    if os.path.exists(candidate):
        return candidate
    return None


def is_patched(firefox_path):
    """Check if this Firefox installation has already been patched."""
    marker = os.path.join(firefox_path, _PATCH_MARKER)
    return os.path.exists(marker)


def patch_libxul(firefox_path, force=False):
    """Patch libxul.so to remove the navigator.webdriver property.

    Replaces the "webdriver" WebIDL property name string with random
    bytes of the same length. This makes navigator.webdriver undefined
    (the property does not exist) rather than true or false.

    Works on both Firefox ESR and Tor Browser installations.

    Args:
        firefox_path: Path to the Firefox (or Tor Browser) directory.
        force: Re-patch even if already patched.

    Returns:
        True if patched, False if already patched (and not forced).
    """
    marker_path = os.path.join(firefox_path, _PATCH_MARKER)

    if not force and os.path.exists(marker_path):
        return False

    libxul = _find_libxul(firefox_path)
    if not libxul:
        raise FileNotFoundError(
            f"libxul.so not found in {firefox_path}"
        )

    # Read the binary
    with open(libxul, "rb") as f:
        data = f.read()

    count = data.count(_PATCH_TARGET)
    if count == 0:
        # Already patched or unexpected binary
        with open(marker_path, "w") as f:
            f.write("already_clean")
        return True

    # Generate a deterministic-looking but random replacement
    replacement = _generate_replacement(len(_PATCH_TARGET))

    # Replace all occurrences (property name + telemetry strings)
    patched = data.replace(_PATCH_TARGET, replacement)

    # Write back
    with open(libxul, "wb") as f:
        f.write(patched)

    # Record what we did
    with open(marker_path, "w") as f:
        f.write(json.dumps({
            "original": _PATCH_TARGET.decode(),
            "replacement": replacement.decode(),
            "occurrences": count,
            "libxul_size": len(data),
        }, indent=2))

    return True


# ─── Layer 1b: Omni.ja Patch (automation indicator) ──────────────────────
# Replaces the red candy-stripe "remote control" CSS in the browser chrome
# with hidden rules so the candycane never appears.
#
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  VISUAL INDICATOR FLOW — how the agent bar + theme system works        │
# │                                                                        │
# │  Candycane hiding (3 redundant layers — belt + suspenders + duct tape): │
# │    [1] omni.ja patch (here) — rewrites CSS at the source in the        │
# │        browser's internal archive. Done once per Firefox install.       │
# │    [2] userChrome.css (firefox.py) — written into the profile before   │
# │        launch. Loaded by Firefox before first paint, no flash.         │
# │    [3] Runtime CSS injection (firefox.py _inject_chrome_css) —         │
# │        injected via nsIStyleSheetService after launch as fallback.     │
# │                                                                        │
# │  Agent indicator (extension-driven, session mode only):                │
# │    [4] session.py _mark_agent_tab() — when an agent calls use_tab(),   │
# │        records {tab_index: timestamp} in _agent_bar_tabs.              │
# │    [5] session.py status endpoint — serves _agent_bar_tabs as          │
# │        bar_tabs in the JSON status response (HTTP, port+1).            │
# │    [6] Indicator extension (this file, _INDICATOR_SCRIPT) — polls [5], │
# │        injects a pink 4px bar into agent-touched tabs via              │
# │        browser.tabs.executeScript(tabId, ...).                         │
# │    [7] Extension theme system — applies BASE_THEME (blue/gray) on     │
# │        load. When user switches to an agent-touched tab, swaps to      │
# │        ACTIVE_TAB_THEME (pink borders + separator). This ensures the   │
# │        indicator survives page loads (theme is browser-level, not DOM). │
# │    [8] User dismissal — when user clicks/types/scrolls on the tab,     │
# │        the injected bar JS sends browser.runtime.sendMessage            │
# │        {type:'bar-dismissed'}. Extension removes bar, adds tab to      │
# │        dismissedTabs set, swaps theme back to BASE_THEME.              │
# │    [9] Re-injection — browser.tabs.onUpdated re-injects the bar after  │
# │        page loads on tracked (non-dismissed) tabs, since navigations   │
# │        destroy the DOM.                                                │
# │                                                                        │
# │  Files involved:                                                       │
# │    stealth.py  — [1] omni.ja patch, [6][7][8][9] extension code        │
# │    firefox.py  — [2] userChrome.css, [3] runtime CSS injection         │
# │    session.py  — [4] _mark_agent_tab, [5] status endpoint bar_tabs     │
# └─────────────────────────────────────────────────────────────────────────┘

_OMNI_PATCH_MARKER = ".browse_omni_patched"

_REMOTE_CONTROL_CSS_OLD = """:root[remotecontrol] {
  #remote-control-box {
    visibility: visible;
    padding-inline: var(--urlbar-icon-padding);
  }

  #remote-control-icon {
    list-style-image: url(chrome://browser/content/static-robot.png);
    width: 16px;
    height: 16px;
  }

  #urlbar-background {
    background-image: repeating-linear-gradient(
      -45deg,
      rgba(255, 60, 60, 0.25) 0 25px,
      rgba(175, 0, 0, 0.25) 25px 50px
    );

    background-attachment: fixed;
    /* Override the usual breakout animation so the gradient doesn't shift around
       when the panel opens. */
    animation: none !important;
  }
}"""

_REMOTE_CONTROL_CSS_NEW = """:root[remotecontrol] {
  #remote-control-box {
    visibility: hidden;
  }

  #remote-control-icon {
    display: none;
  }

  #urlbar-background {
    background-image: none;
    animation: none !important;
  }
}"""


def is_omni_patched(firefox_path):
    """Check if omni.ja has been patched."""
    marker = os.path.join(firefox_path, _OMNI_PATCH_MARKER)
    return os.path.exists(marker)


def patch_omni(firefox_path, force=False):
    """Patch omni.ja to hide the red automation indicator (candycane).

    [1] in the visual indicator flow. Replaces the candy-stripe remote
    control CSS with hidden rules so the red bar never appears.

    Firefox uses a custom omni.ja format with a prepended optimization header
    that Python's zipfile module can't handle. We use the system unzip/zip
    commands instead.

    Args:
        firefox_path: Path to the Firefox (or Tor Browser) directory.
        force: Re-patch even if already patched.

    Returns:
        True if patched, False if already patched (and not forced).
    """
    import subprocess
    import tempfile

    marker_path = os.path.join(firefox_path, _OMNI_PATCH_MARKER)

    if not force and os.path.exists(marker_path):
        return False

    omni_path = _find_omni(firefox_path)
    if not omni_path:
        raise FileNotFoundError(
            f"browser/omni.ja not found in {firefox_path}"
        )

    css_file = "chrome/browser/skin/classic/browser/urlbar-searchbar.css"

    # Extract the CSS file using system unzip (handles Firefox's custom format)
    with tempfile.TemporaryDirectory(prefix="browse_omni_") as tmpdir:
        result = subprocess.run(
            ["unzip", "-o", omni_path, css_file, "-d", tmpdir],
            capture_output=True, text=True)
        css_path = os.path.join(tmpdir, css_file)

        if not os.path.exists(css_path):
            print(f"  Warning: {css_file} not found in {omni_path}")
            with open(marker_path, "w") as f:
                f.write("omni_skipped_no_css")
            return False

        with open(css_path, "r") as f:
            text = f.read()

        patched = False
        if _REMOTE_CONTROL_CSS_OLD in text:
            text = text.replace(_REMOTE_CONTROL_CSS_OLD, _REMOTE_CONTROL_CSS_NEW)
            patched = True

        if not patched:
            # Already patched or CSS structure changed
            with open(marker_path, "w") as f:
                f.write("omni_already_clean")
            return True

        with open(css_path, "w") as f:
            f.write(text)

        # Update the CSS back into omni.ja using system zip
        subprocess.run(
            ["zip", "-0", omni_path, css_file],
            cwd=tmpdir, capture_output=True, text=True)

    with open(marker_path, "w") as f:
        f.write("omni_patched")

    return True


# ─── Layer 2: Stealth WebExtension ────────────────────────────────────────

# Content script that runs at document_start in the MAIN world.
# Does a prototype-level override with toString patching so that
# even if some code path still exposes a webdriver-like property,
# it returns false and looks native.
_CONTENT_SCRIPT = """\
(function() {
    // Override on the prototype so getOwnPropertyDescriptor checks pass
    var proto = Navigator.prototype;
    var desc = Object.getOwnPropertyDescriptor(proto, 'webdriver');

    // If the property doesn't exist (binary patch worked), just ensure
    // it stays gone even if something re-adds it
    if (!desc) {
        // Define it as false with a native-looking getter
        var nativeGet = function webdriver() { return false; };
        Object.defineProperty(proto, 'webdriver', {
            get: nativeGet,
            configurable: true,
            enumerable: true
        });

        // Patch toString for this getter
        var origToString = Function.prototype.toString;
        var toStringProxy = new Proxy(origToString, {
            apply: function(target, thisArg, args) {
                if (thisArg === nativeGet) {
                    return 'function get webdriver() { [native code] }';
                }
                if (thisArg === toStringProxy) {
                    return 'function toString() { [native code] }';
                }
                return Reflect.apply(target, thisArg, args);
            }
        });
        Function.prototype.toString = toStringProxy;
        return;
    }

    // If the property exists (binary patch didn't run or missed),
    // do a full prototype-level override
    var originalGetter = desc.get;

    var fakeGetter = new Proxy(originalGetter, {
        apply: function(target, thisArg, args) {
            return false;
        }
    });

    Object.defineProperty(proto, 'webdriver', {
        get: fakeGetter,
        configurable: desc.configurable,
        enumerable: desc.enumerable
    });

    // Patch Function.prototype.toString to hide the proxy
    var origToString = Function.prototype.toString;
    var toStringProxy = new Proxy(origToString, {
        apply: function(target, thisArg, args) {
            if (thisArg === fakeGetter) {
                return 'function get webdriver() { [native code] }';
            }
            if (thisArg === toStringProxy) {
                return 'function toString() { [native code] }';
            }
            return Reflect.apply(target, thisArg, args);
        }
    });
    Function.prototype.toString = toStringProxy;
})();
"""

_MANIFEST = {
    "manifest_version": 2,
    "name": "Browse Stealth",
    "version": "1.0",
    "description": "Defense-in-depth stealth for browse agent",
    "content_scripts": [
        {
            "matches": ["<all_urls>"],
            "js": ["stealth.js"],
            "run_at": "document_start",
            "all_frames": True,
            "match_about_blank": True,
        }
    ],
}


def build_stealth_extension(output_dir=None):
    """Build the stealth WebExtension as an .xpi file.

    Args:
        output_dir: Directory to write the .xpi to. If None, uses a temp dir.

    Returns:
        Path to the built .xpi file.
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="browse_stealth_")

    xpi_path = os.path.join(output_dir, "browse_stealth.xpi")

    with zipfile.ZipFile(xpi_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(_MANIFEST, indent=2))
        zf.writestr("stealth.js", _CONTENT_SCRIPT)

    return xpi_path


# ─── Agent Indicator Extension ────────────────────────────────────────────
# Polls the session status HTTP endpoint and applies a glowing theme to the
# address bar when agents are connected. Shows agent count as a badge.

_INDICATOR_MANIFEST = {
    "manifest_version": 2,
    "name": "Browse Agent Indicator",
    "version": "1.0",
    "description": "Shows when AI agents are connected to the browser",
    "permissions": ["theme", "tabs", "<all_urls>"],
    "browser_specific_settings": {
        "gecko": {
            "id": "browse-indicator@localhost",
        }
    },
    "browser_action": {
        "default_title": "Agent Status",
    },
    "background": {
        "scripts": ["indicator.js"],
    },
}

_INDICATOR_SCRIPT = """
// ── Indicator Extension Background Script ──────────────────────────────
// Implements steps [6]-[9] of the visual indicator flow.
// See the numbered map at the top of this file (Layer 1b section).

const POLL_MS = 1000;
const STATUS_PORT = __STATUS_PORT__;

// [7] Theme system — two states: BASE (human, blue/gray) and ACTIVE_TAB (agent, pink).
const BASE_THEME = {
  colors: {
    frame: "#0d1117",
    tab_background_text: "#c9d1d9",
    toolbar: "#161b22",
    toolbar_field: "#0d1117",
    toolbar_field_border: "#30363d",
    toolbar_field_border_focus: "#58a6ff",
    toolbar_field_text: "#c9d1d9",
    toolbar_bottom_separator: "transparent",
    tab_line: "#58a6ff",
    popup: "#161b22",
    popup_text: "#c9d1d9",
    popup_border: "#30363d",
  },
};

// Agent is active — pink address bar border + pink tab line
const ACTIVE_THEME = {
  colors: {
    ...BASE_THEME.colors,
    toolbar_field_border: "#ff00aa",
    toolbar_field_border_focus: "#ff00aa",
    popup_border: "#ff00aa",
    tab_line: "#ff00aa",
  },
};

// Viewing an agent-touched tab — pink border + pink separator
const ACTIVE_TAB_THEME = {
  colors: {
    ...ACTIVE_THEME.colors,
    toolbar_bottom_separator: "#ff00aa",
  },
};

// [6] Pink bar injected into agent-touched tabs. [8] Dismissed on user interaction.
const BAR_INJECT_JS = `(function(){
    var e=document.getElementById('browse-agent-bar');
    if(e)return;
    var b=document.createElement('div');
    b.id='browse-agent-bar';
    b.style.cssText='position:fixed;top:0;left:0;right:0;height:4px;'
        +'background:#ff00aa;z-index:2147483647;pointer-events:none;'
        +'box-shadow:0 0 10px #ff00aa;'
        +'animation:browse-agent-pulse 2s ease-in-out infinite;';
    var style=document.getElementById('browse-agent-style');
    if(!style){
        style=document.createElement('style');
        style.id='browse-agent-style';
        style.textContent='@keyframes browse-agent-pulse{'
            +'0%,100%{opacity:0.7;box-shadow:0 0 6px #ff00aa;}'
            +'50%{opacity:1;box-shadow:0 0 14px #ff00aa;}}';
        document.head.appendChild(style);
    }
    if(document.body)document.body.prepend(b);
    function dismiss(){
        var el=document.getElementById('browse-agent-bar');
        if(el)el.remove();
        document.removeEventListener('click',dismiss);
        document.removeEventListener('keydown',dismiss);
        document.removeEventListener('scroll',dismiss,true);
        try{browser.runtime.sendMessage({type:'bar-dismissed'});}catch(e){}
    }
    document.addEventListener('click',dismiss,{once:true});
    document.addEventListener('keydown',dismiss,{once:true});
    document.addEventListener('scroll',dismiss,{once:true,capture:true});
})();`;

const BAR_REMOVE_JS = `(function(){
    var e=document.getElementById('browse-agent-bar');
    if(e)e.remove();
})();`;

let injectedTs = {};  // {tabId: serverTimestamp} — tracks what we last injected
let dismissedTabs = new Set();  // tabs where user dismissed the bar
let onAgentTab = false;  // is the user currently viewing an agent-marked tab

// [7] Apply theme based on whether user is viewing an agent-touched tab.
function applyTheme() {
  browser.theme.update(onAgentTab ? ACTIVE_TAB_THEME : BASE_THEME);
}

// [7] Apply base theme immediately on load.
applyTheme();

// [7] Swap theme when user switches tabs.
browser.tabs.onActivated.addListener(async (activeInfo) => {
  onAgentTab = !!injectedTs[activeInfo.tabId] && !dismissedTabs.has(activeInfo.tabId);
  applyTheme();
});

// [8] User dismissed the bar — swap theme back to base.
browser.runtime.onMessage.addListener((msg, sender) => {
  if (msg.type === 'bar-dismissed' && sender.tab) {
    dismissedTabs.add(sender.tab.id);
    onAgentTab = false;
    applyTheme();
  }
});

async function poll() {
  try {
    const resp = await fetch("http://127.0.0.1:" + STATUS_PORT + "/");
    const data = await resp.json();
    const active = data.active === true;
    const barTabs = data.bar_tabs || {};

    // Badge
    if (active) {
      browser.browserAction.setBadgeText({ text: "\\u25CF" });
      browser.browserAction.setBadgeBackgroundColor({ color: "#ff00aa" });
      browser.browserAction.setBadgeTextColor({ color: "#000000" });
    } else {
      browser.browserAction.setBadgeText({ text: "" });
    }

    // Per-tab agent bar via extension tabs API
    const allTabs = await browser.tabs.query({});
    const wantIds = new Set();

    for (const [idxStr, serverTs] of Object.entries(barTabs)) {
      const idx = parseInt(idxStr);
      const tab = allTabs.find(t => t.index === idx);
      if (!tab) continue;
      wantIds.add(tab.id);

      // Agent touched tab again (newer timestamp) — clear dismissal
      if (injectedTs[tab.id] && serverTs > injectedTs[tab.id]) {
        dismissedTabs.delete(tab.id);
      }

      // Only inject if not dismissed and agent touched it
      if (!dismissedTabs.has(tab.id) && (!injectedTs[tab.id] || serverTs > injectedTs[tab.id])) {
        try {
          await browser.tabs.executeScript(tab.id, { code: BAR_INJECT_JS });
        } catch(e) {}
        injectedTs[tab.id] = serverTs;
        // Update theme if user is currently viewing this tab
        if (tab.active) {
          onAgentTab = true;
          applyTheme();
        }
      }
    }

    // Remove bar from tabs no longer tracked by server (e.g. 10 min cleanup)
    for (const tabId of Object.keys(injectedTs)) {
      if (!wantIds.has(parseInt(tabId))) {
        try {
          await browser.tabs.executeScript(parseInt(tabId), { code: BAR_REMOVE_JS });
        } catch(e) {}
        delete injectedTs[tabId];
      }
    }

  } catch (e) {
    // Status server unreachable — keep theme, just clear badge
    browser.browserAction.setBadgeText({ text: "" });
  }
}

// [9] Re-inject bar after page loads (navigations destroy the DOM).
browser.tabs.onUpdated.addListener((tabId, changeInfo) => {
  if (changeInfo.status === "complete" && injectedTs[tabId] && !dismissedTabs.has(tabId)) {
    try {
      browser.tabs.executeScript(tabId, { code: BAR_INJECT_JS });
    } catch(e) {}
  }
});

setInterval(poll, POLL_MS);
poll();
"""


def build_indicator_extension(status_port, output_dir=None):
    """Build the agent indicator WebExtension as an .xpi file.

    Args:
        status_port: The HTTP port the status server is running on.
        output_dir: Directory to write the .xpi to. If None, uses a temp dir.

    Returns:
        Path to the built .xpi file.
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="browse_indicator_")

    script = _INDICATOR_SCRIPT.replace("__STATUS_PORT__", str(status_port))

    xpi_path = os.path.join(output_dir, "browse_indicator.xpi")

    with zipfile.ZipFile(xpi_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(_INDICATOR_MANIFEST, indent=2))
        zf.writestr("indicator.js", script)

    return xpi_path
