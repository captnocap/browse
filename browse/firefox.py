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
                          patch_omni, is_omni_patched,
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

    if not is_omni_patched(firefox_path):
        patch_omni(firefox_path)

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

    # Profile
    if profile_path:
        options.add_argument("-profile")
        options.add_argument(profile_path)

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

    return driver
