"""Firefox ESR launcher with RFP hardening.

Replaces the tbselenium/ subpackage. Provides a single launch_firefox()
function used by both quick mode (agent.py) and session mode (session.py).

Firefox with privacy.resistFingerprinting (RFP) gives the same C++-level
anti-fingerprinting as Tor Browser — canvas noise, WebGL spoofing, font
restriction, timer clamping, letterboxing — but the anonymity set is
~200M Firefox users instead of ~2M Tor users.
"""

import json
import os
from time import sleep

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service


# ─── Hardening Preferences ───────────────────────────────────────────────
# Applied to every Firefox instance we launch. These configure RFP and
# disable leaky features without requiring any Tor-specific extensions.

HARDENING_PREFS = {
    # ── Core anti-fingerprinting ──────────────────────────────────────
    'privacy.resistFingerprinting': True,
    'privacy.resistFingerprinting.letterboxing': True,

    # ── First-party isolation ─────────────────────────────────────────
    'privacy.firstparty.isolate': True,
    'network.cookie.cookieBehavior': 1,  # block third-party cookies

    # ── WebRTC leak prevention ────────────────────────────────────────
    'media.peerconnection.enabled': False,
    'media.peerconnection.ice.no_host': True,

    # ── Device / sensor leaks ─────────────────────────────────────────
    'geo.enabled': False,
    'dom.battery.enabled': False,
    'media.navigator.enabled': False,  # no camera/mic enumeration

    # ── Tracking protection ───────────────────────────────────────────
    'privacy.trackingprotection.enabled': True,

    # ── Telemetry / phoning home ──────────────────────────────────────
    'toolkit.telemetry.enabled': False,
    'datareporting.policy.dataSubmissionEnabled': False,
    'app.update.enabled': False,
    'browser.newtabpage.activity-stream.feeds.telemetry': False,
    'browser.newtabpage.activity-stream.telemetry': False,
    'browser.ping-centre.telemetry': False,
    'toolkit.telemetry.archive.enabled': False,
    'toolkit.telemetry.bhrPing.enabled': False,
    'toolkit.telemetry.firstShutdownPing.enabled': False,
    'toolkit.telemetry.newProfilePing.enabled': False,
    'toolkit.telemetry.shutdownPingSender.enabled': False,
    'toolkit.telemetry.updatePing.enabled': False,
    'toolkit.telemetry.unified': False,

    # ── Extension signing (for our stealth + indicator extensions) ────
    'xpinstall.signatures.required': False,
    'xpinstall.whitelist.required': False,

    # ── Chrome context access (for session server) ────────────────────
    'toolkit.legacyUserProfileCustomizations.stylesheets': True,

    # ── Suppress automation indicator ─────────────────────────────────
    'browser.chrome.disableRemoteControlCueForTests': True,

    # ── General browser prefs ─────────────────────────────────────────
    'javascript.enabled': True,
    'browser.startup.page': 0,
    'browser.startup.homepage': 'about:blank',
    'browser.shell.checkDefaultBrowser': False,
    'browser.tabs.warnOnClose': False,
    'browser.tabs.warnOnCloseOtherTabs': False,
    'browser.aboutConfig.showWarning': False,
    'browser.warnOnQuit': False,
    'startup.homepage_welcome_url': '',
    'startup.homepage_welcome_url.additional': '',
    'datareporting.policy.dataSubmissionPolicyBypassNotification': True,
    'security.sandbox.warn_unprivileged_namespaces': False,
    'extensions.lastAppVersion': '0',
    'browser.startup.homepage_override.mstone': 'ignore',
    'webdriver.load.strategy': 'normal',
}


# ─── Configuration ────────────────────────────────────────────────────────

def _read_conf():
    """Read browse.conf for Firefox/geckodriver paths."""
    conf = {}
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conf_path = os.path.join(here, "browse.conf")
    if os.path.exists(conf_path):
        with open(conf_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    conf[k.strip()] = v.strip()
    return conf


def find_firefox_path():
    """Locate the Firefox binary directory from config or environment.

    Checks (in order):
      1. FIREFOX_PATH environment variable
      2. FIREFOX_PATH in browse.conf
      3. TBB_PATH in browse.conf (backwards compatibility)
      4. TBB_PATH environment variable (backwards compatibility)

    Returns:
        Path string, or None if not found.
    """
    env = os.environ.get("FIREFOX_PATH")
    if env and os.path.isdir(env):
        return env

    conf = _read_conf()

    fp = conf.get("FIREFOX_PATH")
    if fp and os.path.isdir(fp):
        return fp

    # Backwards compatibility with v1 configs
    tp = conf.get("TBB_PATH")
    if tp and os.path.isdir(tp):
        return tp

    tp_env = os.environ.get("TBB_PATH")
    if tp_env and os.path.isdir(tp_env):
        return tp_env

    return None


def find_geckodriver_path():
    """Locate the geckodriver binary from config, environment, or PATH."""
    conf = _read_conf()

    gp = conf.get("GECKODRIVER_PATH")
    if gp and os.path.isfile(gp):
        return gp

    import shutil
    system = shutil.which("geckodriver")
    if system:
        return system

    return None


# ─── Environment Setup ────────────────────────────────────────────────────

def setup_env(firefox_path):
    """Set LD_LIBRARY_PATH so Firefox can find its bundled shared libs."""
    os.environ["LD_LIBRARY_PATH"] = firefox_path
    # Prepend to PATH so child processes can find the firefox binary
    path = os.environ.get("PATH", "")
    if firefox_path not in path.split(":"):
        os.environ["PATH"] = firefox_path + ":" + path


# ─── Chrome-Context Pref Setter ───────────────────────────────────────────

def set_pref(driver, name, value):
    """Set a Firefox preference via Services.prefs in chrome context.

    Used to override preferences on a running browser instance (e.g., after
    launch when Options.set_preference isn't available).
    """
    script = 'Services.prefs.'
    if isinstance(value, bool):
        script += 'setBoolPref'
    elif isinstance(value, str):
        script += 'setStringPref'
    else:
        script += 'setIntPref'
    script += '({0}, {1});'.format(json.dumps(name), json.dumps(value))

    try:
        with driver.context(driver.CONTEXT_CHROME):
            driver.execute_script(script)
    finally:
        driver.set_context(driver.CONTEXT_CONTENT)


# ─── Firefox Launcher ─────────────────────────────────────────────────────

def launch_firefox(firefox_path=None, geckodriver_path=None,
                   headless=False, profile_path=None,
                   pref_dict=None, homepage=None):
    """Launch Firefox ESR with full RFP hardening and stealth patches.

    This is the single entry point for creating a browser instance, used
    by both quick mode (AgentBrowser) and session mode (SessionServer).

    Args:
        firefox_path: Path to the Firefox installation directory.
            If None, auto-detected from browse.conf / env.
        geckodriver_path: Path to the geckodriver binary.
            If None, auto-detected from browse.conf / env / PATH.
        headless: Run headless (prefer XVFB for better stealth).
        profile_path: Path to a persistent profile directory. If None,
            Selenium creates a temporary profile.
        pref_dict: Additional Firefox preferences (override hardening defaults).
        homepage: URL to set as the startup homepage.

    Returns:
        A Selenium WebDriver (Firefox) instance.
    """
    from .stealth import (patch_libxul, is_patched,
                          build_stealth_extension)

    # Resolve paths
    if firefox_path is None:
        firefox_path = find_firefox_path()
    if not firefox_path:
        raise ValueError(
            "Firefox path not found. Run setup.sh or set FIREFOX_PATH."
        )

    if geckodriver_path is None:
        geckodriver_path = find_geckodriver_path()
    if not geckodriver_path:
        raise ValueError(
            "geckodriver not found. Run setup.sh or install geckodriver."
        )

    # Find the firefox binary
    fx_binary = os.path.join(firefox_path, "firefox")
    if not os.path.isfile(fx_binary):
        raise FileNotFoundError(f"Firefox binary not found at {fx_binary}")

    # Apply stealth patches (idempotent — marker files prevent re-patching)
    if not is_patched(firefox_path):
        patch_libxul(firefox_path)

    # Set up environment
    setup_env(firefox_path)

    # Build Options
    options = Options()
    options.binary = fx_binary
    options.add_argument('-remote-allow-system-access')
    if headless:
        options.add_argument('-headless')

    # Apply hardening prefs
    for k, v in HARDENING_PREFS.items():
        options.set_preference(k, v)

    # Homepage override
    if homepage:
        options.set_preference('browser.startup.page', 1)
        options.set_preference('browser.startup.homepage', homepage)

    # User prefs override everything
    if pref_dict:
        for k, v in pref_dict.items():
            options.set_preference(k, v)

    # Profile — ensure userChrome.css is present to hide the candycane
    # before the browser window renders (CSS injection after launch is too late).
    if profile_path:
        _ensure_user_chrome_css(profile_path)
        options.add_argument("-profile")
        options.add_argument(profile_path)
    else:
        # Create a temp profile with userChrome.css pre-installed
        import tempfile
        _tmp_profile = tempfile.mkdtemp(prefix="browse_profile_")
        _ensure_user_chrome_css(_tmp_profile)
        options.add_argument("-profile")
        options.add_argument(_tmp_profile)

    # Launch
    service = Service(executable_path=geckodriver_path)
    driver = webdriver.Firefox(service=service, options=options)
    sleep(1)

    # Install stealth extension (defense-in-depth for navigator.webdriver)
    try:
        xpi_path = build_stealth_extension()
        driver.install_addon(xpi_path, temporary=True)
    except Exception as e:
        print(f"  Warning: stealth extension failed to install: {e}")

    # [3] Runtime CSS injection — fallback candycane hiding.
    # See stealth.py for the full visual indicator flow.
    try:
        _inject_chrome_css(driver)
    except Exception as e:
        print(f"  Warning: chrome CSS injection failed: {e}")

    return driver


# ─── Profile userChrome.css ──────────────────────────────────────────────
# [2] in the visual indicator flow (see stealth.py for the full numbered map).
# Written into the profile before launch so Firefox loads it before first paint.

def _ensure_user_chrome_css(profile_path):
    """Write userChrome.css into a profile to hide the automation candycane.

    This is loaded by Firefox before the window renders, so there's no
    flash of the red stripe. Requires toolkit.legacyUserProfileCustomizations.stylesheets = true.
    """
    chrome_dir = os.path.join(profile_path, "chrome")
    os.makedirs(chrome_dir, exist_ok=True)
    css_path = os.path.join(chrome_dir, "userChrome.css")
    with open(css_path, "w") as f:
        f.write(_CHROME_CSS)


# ─── Chrome CSS Injection ────────────────────────────────────────────────
# [3] in the visual indicator flow (see stealth.py for the full numbered map).
# Runtime fallback — injected via nsIStyleSheetService after launch.

_CHROME_CSS = """
/* Hide the Selenium/Marionette automation indicator (candycane) */
:root[remotecontrol] #remote-control-box { visibility: hidden !important; }
:root[remotecontrol] #remote-control-icon { display: none !important; }
:root[remotecontrol] #urlbar-background {
  background-image: none !important;
  animation: none !important;
}

/* [10] Per-tab agent indicator — styled via browse-agent attribute on XUL tab elements.
   Set by session.py _mark_agent_tab(), cleared on dismissal or 10 min expiry.
   Two states: "active" (agent live, pulsing) and "true" (agent touched, static). */

/* Static pink — agent touched this tab but is idle */
tab[browse-agent="true"] .tab-background {
  background: rgba(255, 0, 170, 0.12) !important;
  outline: 1px solid rgba(255, 0, 170, 0.35) !important;
  outline-offset: -1px;
}

tab[browse-agent="true"] .tab-line {
  background-color: #ff00aa !important;
  opacity: 1 !important;
  height: 2px !important;
}

tab[browse-agent="true"][selected] .tab-background {
  background: rgba(255, 0, 170, 0.2) !important;
  outline: 1px solid rgba(255, 0, 170, 0.5) !important;
}

/* Pulsing pink — agent is actively working on this tab */
@keyframes browse-tab-pulse {
  0%, 100% {
    background: rgba(255, 0, 170, 0.12);
    outline-color: rgba(255, 0, 170, 0.35);
  }
  50% {
    background: rgba(255, 0, 170, 0.3);
    outline-color: rgba(255, 0, 170, 0.7);
  }
}

tab[browse-agent="active"] .tab-background {
  outline: 1px solid rgba(255, 0, 170, 0.7) !important;
  outline-offset: -1px;
  animation: browse-tab-pulse 1s ease-in-out infinite !important;
}

tab[browse-agent="active"] .tab-line {
  background-color: #ff00aa !important;
  opacity: 1 !important;
  height: 3px !important;
}

tab[browse-agent="active"][selected] .tab-background {
  outline: 1px solid rgba(255, 0, 170, 0.8) !important;
  animation: browse-tab-pulse 1s ease-in-out infinite !important;
}

"""


def _inject_chrome_css(driver):
    """Inject CSS into the browser chrome to hide automation indicators.

    Uses nsIStyleSheetService to register a user agent stylesheet, which
    is the proper way to inject CSS into Firefox's chrome context.
    """
    with driver.context(driver.CONTEXT_CHROME):
        driver.execute_script("""
            var sss = Components.classes['@mozilla.org/content/style-sheet-service;1']
                        .getService(Components.interfaces.nsIStyleSheetService);
            var css = arguments[0];
            var uri = Services.io.newURI(
                'data:text/css,' + encodeURIComponent(css));
            if (!sss.sheetRegistered(uri, sss.USER_SHEET)) {
                sss.loadAndRegisterSheet(uri, sss.USER_SHEET);
            }
        """, _CHROME_CSS)
