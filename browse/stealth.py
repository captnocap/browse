"""Stealth patches for hiding automation signals.

Two layers:

Layer 1 — Binary patch: Replaces the "webdriver" string in libxul.so so the
    navigator.webdriver property ceases to exist entirely. Not overridden,
    not false — genuinely undefined, same as a normal browser.

Layer 2 — WebExtension: Injects a content script at document_start in the
    MAIN world that does a prototype-level override of navigator.webdriver
    as defense-in-depth. Handles edge cases like iframes.
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


def is_patched(tbb_path):
    """Check if this Tor Browser installation has already been patched."""
    marker = os.path.join(tbb_path, _PATCH_MARKER)
    return os.path.exists(marker)


def patch_libxul(tbb_path, force=False):
    """Patch libxul.so to remove the navigator.webdriver property.

    Replaces the "webdriver" WebIDL property name string with random
    bytes of the same length. This makes navigator.webdriver undefined
    (the property does not exist) rather than true or false.

    Args:
        tbb_path: Path to the Tor Browser Bundle directory.
        force: Re-patch even if already patched.

    Returns:
        True if patched, False if already patched (and not forced).
    """
    marker_path = os.path.join(tbb_path, _PATCH_MARKER)

    if not force and os.path.exists(marker_path):
        return False

    libxul = os.path.join(tbb_path, "Browser", "libxul.so")
    if not os.path.exists(libxul):
        raise FileNotFoundError(f"libxul.so not found at {libxul}")

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
# with an agent-aware indicator that glows green when agents are connected.

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
}

/* Browse agent indicator — controlled by browseagent attribute on root */
@keyframes agent-pulse {
  0%, 100% {
    box-shadow: 0 0 8px #00ff88, 0 0 3px #00ff88 inset;
    border-color: #00ff88;
  }
  50% {
    box-shadow: 0 0 14px #00ffaa, 0 0 5px #00ffaa inset;
    border-color: #00ffaa;
  }
}

:root[browseagent] #urlbar-background {
  border: 2px solid #00ff88 !important;
  box-shadow: 0 0 8px #00ff88, 0 0 3px #00ff88 inset !important;
  animation: agent-pulse 2s ease-in-out infinite !important;
}

:root[browseagent] .tabbrowser-tab[selected] .tab-line {
  background-color: #00ff88 !important;
  opacity: 1 !important;
  height: 3px !important;
}

:root[browseagent] #navigator-toolbox {
  border-bottom: 1px solid #00ff8855 !important;
}"""


def is_omni_patched(tbb_path):
    """Check if omni.ja has been patched."""
    marker = os.path.join(tbb_path, _OMNI_PATCH_MARKER)
    return os.path.exists(marker)


def patch_omni(tbb_path, force=False):
    """Patch omni.ja to replace the red automation indicator with the agent glow.

    Replaces the candy-stripe remote control CSS with:
    - Hidden by default (no red bar)
    - Green glow when browse.agent.connected pref is true

    Args:
        tbb_path: Path to the Tor Browser Bundle directory.
        force: Re-patch even if already patched.

    Returns:
        True if patched, False if already patched (and not forced).
    """
    marker_path = os.path.join(tbb_path, _OMNI_PATCH_MARKER)

    if not force and os.path.exists(marker_path):
        return False

    omni_path = os.path.join(tbb_path, "Browser", "browser", "omni.ja")
    if not os.path.exists(omni_path):
        raise FileNotFoundError(f"omni.ja not found at {omni_path}")

    css_file = "chrome/browser/skin/classic/browser/urlbar-searchbar.css"

    # Read the existing omni.ja
    tmp_path = omni_path + ".tmp"
    patched = False
    with zipfile.ZipFile(omni_path, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == css_file:
                    text = data.decode("utf-8")
                    # Replace original red candy-stripe
                    if _REMOTE_CONTROL_CSS_OLD in text:
                        text = text.replace(
                            _REMOTE_CONTROL_CSS_OLD,
                            _REMOTE_CONTROL_CSS_NEW
                        )
                        patched = True
                    # Replace previous browse patch version
                    old_marker = "/* Browse agent indicator"
                    if not patched and old_marker in text:
                        idx = text.find(old_marker)
                        end = text.find("\n/**", idx)
                        if end < 0:
                            end = len(text)
                        # Keep everything before the old marker, insert new
                        text = text[:idx] + _REMOTE_CONTROL_CSS_NEW.split("}")[-1].lstrip() + "\n" + text[end:]
                        patched = True
                    data = text.encode("utf-8")
                zout.writestr(item, data)

    # Replace original
    shutil.move(tmp_path, omni_path)

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
    "permissions": ["theme"],
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
const POLL_MS = 1000;
const STATUS_PORT = __STATUS_PORT__;

const AGENT_THEME = {
  colors: {
    frame: "#0d1117",
    tab_background_text: "#c9d1d9",
    toolbar: "#161b22",
    toolbar_field: "#0d1117",
    toolbar_field_border: "#00ff88",
    toolbar_field_border_focus: "#00ff88",
    toolbar_field_text: "#c9d1d9",
    toolbar_bottom_separator: "#00ff88",
    popup: "#161b22",
    popup_text: "#c9d1d9",
    popup_border: "#00ff88",
    tab_line: "#00ff88",
    tab_loading: "#00ff88",
  },
};

// Pulsing: alternate between bright and dim glow
const AGENT_THEME_DIM = {
  colors: {
    ...AGENT_THEME.colors,
    toolbar_field_border: "#00cc6a",
    toolbar_field_border_focus: "#00cc6a",
    toolbar_bottom_separator: "#00cc6a",
    tab_line: "#00cc6a",
    tab_loading: "#00cc6a",
  },
};

let lastCount = 0;
let pulse = false;

async function poll() {
  try {
    const resp = await fetch("http://127.0.0.1:" + STATUS_PORT + "/");
    const data = await resp.json();
    const count = data.agents || 0;

    if (count > 0) {
      // Pulse between bright and dim green
      pulse = !pulse;
      browser.theme.update(pulse ? AGENT_THEME : AGENT_THEME_DIM);
      browser.browserAction.setBadgeText({ text: String(count) });
      browser.browserAction.setBadgeBackgroundColor({ color: "#00ff88" });
      browser.browserAction.setBadgeTextColor({ color: "#000000" });
    } else if (count === 0 && lastCount > 0) {
      browser.theme.reset();
      browser.browserAction.setBadgeText({ text: "" });
    }

    lastCount = count;
  } catch (e) {
    // Status server not reachable
    if (lastCount > 0) {
      browser.theme.reset();
      browser.browserAction.setBadgeText({ text: "" });
      lastCount = 0;
    }
  }
}

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
