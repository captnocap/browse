import shutil
from os import environ, chdir
from os.path import isdir, isfile, join, abspath, dirname
from time import sleep
from http.client import CannotSendRequest
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxDriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import WebDriverException
from . import common as cm
from .utils import prepend_to_env_var, is_busy
from .tbbinary import TBBinary
from .exceptions import (
    TBDriverConfigError, TBDriverPortError, TBDriverPathError)


DEFAULT_BANNED_PORTS = "9050,9051,9150,9151"
GECKO_DRIVER_EXE_PATH = shutil.which("geckodriver")


class TorBrowserDriver(FirefoxDriver):
    """Extend Firefox webdriver to automate Tor Browser.

    Supports direct connection mode (USE_DIRECT) for using Tor Browser's
    anti-fingerprinting without routing through the Tor network.
    """
    def __init__(self,
                 tbb_path="",
                 tor_cfg=cm.USE_RUNNING_TOR,
                 tbb_fx_binary_path="",
                 tbb_profile_path="",
                 tbb_logfile_path="",
                 tor_data_dir="",
                 executable_path=GECKO_DRIVER_EXE_PATH,
                 pref_dict={},
                 socks_port=None,
                 control_port=None,
                 extensions=[],
                 default_bridge_type="",
                 headless=False,
                 options=None,
                 use_custom_profile=False,
                 geckodriver_port=0
                 ):
        self.use_custom_profile = use_custom_profile
        self.tor_cfg = tor_cfg
        self.setup_tbb_paths(tbb_path, tbb_fx_binary_path,
                             tbb_profile_path, tor_data_dir)
        self.options = Options() if options is None else options
        install_noscript = False

        USE_DEPRECATED_PROFILE_METHOD = True
        if self.use_custom_profile:
            self.options.add_argument("-profile")
            self.options.add_argument(self.tbb_profile_path)
        elif USE_DEPRECATED_PROFILE_METHOD:
            self.options.profile = self.tbb_profile_path
        else:
            install_noscript = True

        self.init_ports(tor_cfg, socks_port, control_port)
        self.init_prefs(pref_dict, default_bridge_type)
        self.export_env_vars()

        if use_custom_profile:
            print(f'Using custom profile: {self.tbb_profile_path}')
            tbb_service = Service(
                executable_path=executable_path,
                log_path=tbb_logfile_path,
                service_args=["--marionette-port", "2828"],
                port=geckodriver_port
                )
        else:
            tbb_service = Service(
                executable_path=executable_path,
                log_path=tbb_logfile_path,
                port=geckodriver_port
                )

        self.options.binary = self.tbb_fx_binary_path
        self.options.add_argument('--class')
        self.options.add_argument('"Tor Browser"')
        self.options.add_argument('-remote-allow-system-access')
        if headless:
            self.options.add_argument('-headless')

        super(TorBrowserDriver, self).__init__(
            service=tbb_service,
            options=self.options,
            )
        self.is_running = True
        self.install_extensions(extensions, install_noscript)
        self.temp_profile_dir = self.capabilities["moz:profile"]
        sleep(1)

        # In direct mode, force proxy settings via about:config AFTER launch
        # so we override anything the torlauncher/torbutton extensions set.
        if self.tor_cfg == cm.USE_DIRECT:
            self._force_direct_connection(pref_dict)
            # Apply stealth patches (binary patch + extension)
            self._apply_stealth()

    def install_extensions(self, extensions, install_noscript):
        """Install the given extensions to the profile we are launching."""
        if install_noscript:
            no_script_xpi = join(
                self.tbb_path, cm.DEFAULT_TBB_NO_SCRIPT_XPI_PATH)
            extensions.append(no_script_xpi)

        for extension in extensions:
            self.install_addon(extension)

    def init_ports(self, tor_cfg, socks_port, control_port):
        """Check SOCKS port and Tor config inputs.

        In USE_DIRECT mode, skip all port checks — no Tor connection needed.
        """
        if tor_cfg == cm.USE_DIRECT:
            self.socks_port = None
            self.control_port = None
            return

        if tor_cfg == cm.LAUNCH_NEW_TBB_TOR:
            raise TBDriverConfigError(
                """`LAUNCH_NEW_TBB_TOR` config is not supported anymore.
                Use USE_RUNNING_TOR or USE_STEM""")

        if tor_cfg not in [cm.USE_RUNNING_TOR, cm.USE_STEM]:
            raise TBDriverConfigError("Unrecognized tor_cfg: %s" % tor_cfg)

        if socks_port is None:
            if tor_cfg == cm.USE_RUNNING_TOR:
                socks_port = cm.DEFAULT_SOCKS_PORT
            else:
                socks_port = cm.STEM_SOCKS_PORT
        if control_port is None:
            if tor_cfg == cm.USE_RUNNING_TOR:
                control_port = cm.DEFAULT_CONTROL_PORT
            else:
                control_port = cm.STEM_CONTROL_PORT

        if not is_busy(socks_port):
            raise TBDriverPortError("SOCKS port %s is not listening"
                                    % socks_port)

        self.socks_port = socks_port
        self.control_port = control_port

    def setup_tbb_paths(self, tbb_path, tbb_fx_binary_path, tbb_profile_path,
                        tor_data_dir):
        """Update instance variables based on the passed paths."""
        if not (tbb_path or (tbb_fx_binary_path and tbb_profile_path)):
            raise TBDriverPathError("Either TBB path or Firefox profile"
                                    " and binary path should be provided"
                                    " %s" % tbb_path)

        if tbb_path:
            if not isdir(tbb_path):
                raise TBDriverPathError("TBB path is not a directory %s"
                                        % tbb_path)
            tbb_fx_binary_path = join(tbb_path, cm.DEFAULT_TBB_FX_BINARY_PATH)
        else:
            tbb_path = dirname(dirname(tbb_fx_binary_path))

        if not tbb_profile_path:
            tbb_profile_path = join(tbb_path, cm.DEFAULT_TBB_PROFILE_PATH)

        if not isfile(tbb_fx_binary_path):
            raise TBDriverPathError("Invalid Firefox binary %s"
                                    % tbb_fx_binary_path)
        if not isdir(tbb_profile_path):
            raise TBDriverPathError("Invalid Firefox profile dir %s"
                                    % tbb_profile_path)
        self.tbb_path = abspath(tbb_path)
        self.tbb_profile_path = abspath(tbb_profile_path)
        self.tbb_fx_binary_path = abspath(tbb_fx_binary_path)
        self.tbb_browser_dir = abspath(join(tbb_path,
                                            cm.DEFAULT_TBB_BROWSER_DIR))
        if tor_data_dir:
            self.tor_data_dir = tor_data_dir
        else:
            self.tor_data_dir = join(tbb_path, cm.DEFAULT_TOR_DATA_PATH)
        # TB can't find bundled "fonts" if we don't switch to tbb_browser_dir
        chdir(self.tbb_browser_dir)

    def load_url(self, url, wait_on_page=0, wait_for_page_body=False):
        """Load a URL and wait before returning."""
        self.get(url)
        if wait_for_page_body:
            self.find_element_by("body", find_by=By.TAG_NAME)
        sleep(wait_on_page)

    def find_element_by(self, selector, timeout=30,
                        find_by=By.CSS_SELECTOR):
        """Wait until the element matching the selector appears or timeout."""
        return WebDriverWait(self, timeout).until(
            EC.presence_of_element_located((find_by, selector)))

    def add_ports_to_fx_banned_ports(self, socks_port, control_port):
        """By default, ports 9050,9051,9150,9151 are banned in TB."""
        if socks_port in cm.KNOWN_SOCKS_PORTS:
            return
        tb_prefs = self.options.preferences
        set_pref = self.options.set_preference

        for port_ban_pref in cm.PORT_BAN_PREFS:
            banned_ports = tb_prefs.get(port_ban_pref, DEFAULT_BANNED_PORTS)
            set_pref(port_ban_pref, "%s,%s,%s" %
                     (banned_ports, socks_port, control_port))

    def set_tb_prefs_for_using_system_tor(self, control_port):
        """Set preferences for running TB with system-installed Tor."""
        set_pref = self.options.set_preference
        set_pref('extensions.torlauncher.start_tor', False)
        set_pref('extensions.torbutton.block_disk', False)
        set_pref('extensions.torbutton.custom.socks_host', '127.0.0.1')
        set_pref('extensions.torbutton.custom.socks_port', self.socks_port)
        set_pref('extensions.torbutton.inserted_button', True)
        set_pref('extensions.torbutton.launch_warning', False)
        set_pref('privacy.spoof_english', 2)
        set_pref('extensions.torbutton.loglevel', 2)
        set_pref('extensions.torbutton.logmethod', 0)
        set_pref('extensions.torbutton.settings_method', 'custom')
        set_pref('extensions.torbutton.use_privoxy', False)
        set_pref('extensions.torlauncher.control_port', control_port)
        set_pref('extensions.torlauncher.loglevel', 2)
        set_pref('extensions.torlauncher.logmethod', 0)
        set_pref('extensions.torlauncher.prompt_at_startup', False)
        set_pref('xpinstall.signatures.required', False)
        set_pref('xpinstall.whitelist.required', False)

    def set_prefs_for_direct_connection(self):
        """Configure browser for direct connection — no Tor, no SOCKS.

        Keeps all anti-fingerprinting protections active while routing
        traffic directly (or through a user-configured proxy).
        """
        set_pref = self.options.set_preference

        # Kill Tor launcher entirely
        set_pref('extensions.torlauncher.start_tor', False)
        set_pref('extensions.torlauncher.prompt_at_startup', False)
        set_pref('extensions.torlauncher.quickstart', False)

        # Direct connection — no proxy
        set_pref('network.proxy.type', 0)
        set_pref('network.proxy.socks', '')
        set_pref('network.proxy.socks_port', 0)
        set_pref('network.proxy.socks_remote_dns', False)

        # Keep all anti-fingerprinting ON
        set_pref('privacy.resistFingerprinting', True)
        set_pref('privacy.resistFingerprinting.letterboxing', True)

        # Enable JavaScript
        set_pref('javascript.enabled', True)

        # Prevent WebRTC IP leak
        set_pref('media.peerconnection.enabled', False)

        # Disable Tor-specific UI annoyances
        set_pref('extensions.torbutton.inserted_button', True)
        set_pref('extensions.torbutton.launch_warning', False)
        set_pref('extensions.torbutton.loglevel', 2)
        set_pref('extensions.torbutton.logmethod', 0)
        set_pref('privacy.spoof_english', 2)

        # Allow extension installs
        set_pref('xpinstall.signatures.required', False)
        set_pref('xpinstall.whitelist.required', False)

    def _apply_stealth(self):
        """Apply stealth patches to hide automation signals."""
        from ..stealth import patch_libxul, is_patched, build_stealth_extension

        # Layer 1: Binary patch (only on first run)
        if not is_patched(self.tbb_path):
            patch_libxul(self.tbb_path)

        # Layer 2: Stealth WebExtension
        try:
            xpi_path = build_stealth_extension()
            self.install_addon(xpi_path, temporary=True)
        except Exception:
            pass  # Non-fatal — Layer 1 is the real fix

    def _force_direct_connection(self, user_prefs):
        """Set proxy prefs via about:config after launch.

        The torlauncher/torbutton extensions override pre-launch prefs,
        so we set them again here via Services.prefs in chrome context
        to get the final word.
        """
        from .utils import set_tbb_pref

        direct_prefs = {
            'network.proxy.type': 0,
            'network.proxy.socks': '',
            'network.proxy.socks_port': 0,
            'network.proxy.socks_remote_dns': False,
            'network.proxy.http': '',
            'network.proxy.http_port': 0,
            'network.proxy.ssl': '',
            'network.proxy.ssl_port': 0,
            'network.proxy.no_proxies_on': '',
            'extensions.torlauncher.start_tor': False,
            # TB disables native DNS because it expects SOCKS to handle it.
            # Re-enable it for direct connection.
            'network.dns.disabled': False,
        }

        # If user passed proxy prefs, those take priority over direct defaults
        if user_prefs:
            direct_prefs.update(user_prefs)

        for name, value in direct_prefs.items():
            set_tbb_pref(self, name, value)

    def init_prefs(self, pref_dict, default_bridge_type):
        set_pref = self.options.set_preference

        if self.tor_cfg == cm.USE_DIRECT:
            # Direct connection mode — skip all Tor/SOCKS prefs
            set_pref('browser.startup.page', "0")
            set_pref('torbrowser.settings.quickstart.enabled', True)
            set_pref('browser.startup.homepage', 'about:newtab')
            set_pref('app.update.enabled', False)
            set_pref('extensions.torbutton.versioncheck_enabled', False)
            set_pref('extensions.torbutton.prompted_language', True)
            set_pref('intl.language_notification.shown', True)
            set_pref('webdriver.load.strategy', 'normal')
            self.set_prefs_for_direct_connection()
        else:
            # Original Tor-connected mode
            self.add_ports_to_fx_banned_ports(self.socks_port,
                                              self.control_port)
            set_pref('browser.startup.page', "0")
            set_pref('torbrowser.settings.quickstart.enabled', True)
            set_pref('browser.startup.homepage', 'about:newtab')
            set_pref('extensions.torlauncher.prompt_at_startup', 0)
            set_pref('webdriver.load.strategy', 'normal')
            set_pref('app.update.enabled', False)
            set_pref('extensions.torbutton.versioncheck_enabled', False)
            if default_bridge_type:
                set_pref('extensions.torlauncher.default_bridge_type',
                         default_bridge_type)
            set_pref('extensions.torbutton.prompted_language', True)
            set_pref('intl.language_notification.shown', True)
            set_pref('network.proxy.socks_port', self.socks_port)
            set_pref('extensions.torbutton.socks_port', self.socks_port)
            set_pref('extensions.torlauncher.control_port',
                     self.control_port)
            self.set_tb_prefs_for_using_system_tor(self.control_port)

        # pref_dict overwrites above preferences
        for pref_name, pref_val in pref_dict.items():
            set_pref(pref_name, pref_val)

    def export_env_vars(self):
        """Setup LD_LIBRARY_PATH and HOME environment variables."""
        tor_binary_dir = join(self.tbb_path, cm.DEFAULT_TOR_BINARY_DIR)
        environ["LD_LIBRARY_PATH"] = tor_binary_dir
        environ["FONTCONFIG_PATH"] = join(self.tbb_path,
                                          cm.DEFAULT_FONTCONFIG_PATH)
        environ["FONTCONFIG_FILE"] = cm.FONTCONFIG_FILE
        environ["HOME"] = self.tbb_browser_dir
        prepend_to_env_var("PATH", self.tbb_browser_dir)

    def get_tb_binary(self, logfile=None):
        """Return FirefoxBinary pointing to the TBB's firefox binary."""
        tbb_logfile = open(logfile, 'a+') if logfile else None
        return TBBinary(firefox_path=self.tbb_fx_binary_path,
                        log_file=tbb_logfile)

    @property
    def is_connection_error_page(self):
        """Check if we get a connection error."""
        return "ENTITY connectionFailure.title" in self.page_source

    def clean_up_profile_dirs(self):
        """Remove temporary profile directories."""
        if self.use_custom_profile:
            return

        if self.temp_profile_dir and isdir(self.temp_profile_dir):
            shutil.rmtree(self.temp_profile_dir)

    def quit(self):
        """Quit the driver. Clean up if the parent's quit fails."""
        self.is_running = False
        try:
            super(TorBrowserDriver, self).quit()
        except (CannotSendRequest, AttributeError, WebDriverException):
            try:
                if hasattr(self, "service"):
                    self.service.stop()
                if hasattr(self, "options") and hasattr(
                        self.options, "profile"):
                    self.clean_up_profile_dirs()
            except Exception as e:
                print("[tbselenium] Exception while quitting: %s" % e)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.quit()
