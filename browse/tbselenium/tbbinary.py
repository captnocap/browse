"""Legacy TBBinary — FirefoxBinary was removed in Selenium 4.

This module is kept for compatibility but TBBinary is no longer used.
The driver now passes the binary path via Options.binary instead.
"""


class TBBinary:
    """Stub replacement for the removed FirefoxBinary-based class."""

    def __init__(self, firefox_path=None, log_file=None):
        self.firefox_path = firefox_path
        self.log_file = log_file
        self.process = None

    def kill(self):
        if self.process and self.process.poll() is None:
            self.process.kill()
            self.process.wait()
