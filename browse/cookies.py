"""Cookie import — read cookies from other browsers and inject into a session.

Supports:
  - Firefox (reads cookies.sqlite directly)
  - Chrome/Chromium/Brave (decrypts cookies on Linux)
  - JSON file (array of cookie dicts)
"""

import glob
import json
import os
import sqlite3
import tempfile
import shutil


# ─── Firefox ──────────────────────────────────────────────────────────────

def _find_firefox_profile():
    """Find the default Firefox profile directory."""
    base = os.path.expanduser("~/.mozilla/firefox")
    if not os.path.isdir(base):
        return None
    # Look for profiles in order of preference
    for pattern in ["*.default-release", "*.default"]:
        matches = glob.glob(os.path.join(base, pattern))
        if matches:
            return matches[0]
    return None


def read_firefox(profile_path=None):
    """Read cookies from Firefox's cookies.sqlite."""
    if profile_path is None:
        profile_path = _find_firefox_profile()
    if not profile_path:
        raise FileNotFoundError("No Firefox profile found.")

    db_path = os.path.join(profile_path, "cookies.sqlite")
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"No cookies.sqlite in {profile_path}")

    # Copy the DB since Firefox may have it locked
    tmp = tempfile.mktemp(suffix=".sqlite")
    shutil.copy2(db_path, tmp)

    try:
        conn = sqlite3.connect(tmp)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT name, value, host, path, expiry, isSecure, isHttpOnly "
            "FROM moz_cookies"
        ).fetchall()
        conn.close()
    finally:
        os.unlink(tmp)

    cookies = []
    for r in rows:
        domain = r["host"]
        cookies.append({
            "name": r["name"],
            "value": r["value"],
            "domain": domain,
            "path": r["path"] or "/",
            "expiry": r["expiry"] if r["expiry"] else None,
            "secure": bool(r["isSecure"]),
            "httpOnly": bool(r["isHttpOnly"]),
        })
    return cookies


# ─── Chrome / Chromium / Brave ────────────────────────────────────────────

_CHROME_PATHS = {
    "chrome": os.path.expanduser("~/.config/google-chrome/Default"),
    "chromium": os.path.expanduser("~/.config/chromium/Default"),
    "brave": os.path.expanduser("~/.config/BraveSoftware/Brave-Browser/Default"),
}


def _chrome_decrypt_key(browser="chrome"):
    """Get the Chrome decryption key on Linux."""
    try:
        import secretstorage
        bus = secretstorage.dbus_init()
        collection = secretstorage.get_default_collection(bus)
        if collection.is_locked():
            collection.unlock()
        for item in collection.get_all_items():
            if item.get_label() == "Chrome Safe Storage":
                return item.get_secret()
            if item.get_label() == "Chromium Safe Storage":
                return item.get_secret()
    except Exception:
        pass
    # Fallback key used when no keyring is available
    return b"peanuts"


def _chrome_decrypt_value(encrypted_value, key):
    """Decrypt a Chrome cookie value."""
    if not encrypted_value:
        return ""

    # v10/v11 prefix = encrypted with PBKDF2 + AES-128-CBC
    if encrypted_value[:3] in (b"v10", b"v11"):
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.primitives import hashes, padding

            derived = PBKDF2HMAC(
                algorithm=hashes.SHA1(),
                length=16,
                salt=b"saltysalt",
                iterations=1,
            ).derive(key)

            iv = b" " * 16
            cipher = Cipher(algorithms.AES(derived), modes.CBC(iv))
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(encrypted_value[3:]) + decryptor.finalize()

            # Remove PKCS7 padding
            unpadder = padding.PKCS7(128).unpadder()
            decrypted = unpadder.update(decrypted) + unpadder.finalize()
            return decrypted.decode("utf-8", errors="replace")
        except Exception:
            return ""
    else:
        # Unencrypted (older Chrome)
        return encrypted_value.decode("utf-8", errors="replace")


def read_chrome(browser="chrome"):
    """Read cookies from Chrome/Chromium/Brave."""
    profile = _CHROME_PATHS.get(browser)
    if not profile or not os.path.isdir(profile):
        raise FileNotFoundError(f"No {browser} profile found at {profile}")

    db_path = os.path.join(profile, "Cookies")
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"No Cookies DB in {profile}")

    # Copy since Chrome locks the file
    tmp = tempfile.mktemp(suffix=".sqlite")
    shutil.copy2(db_path, tmp)

    key = _chrome_decrypt_key(browser)

    try:
        conn = sqlite3.connect(tmp)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT name, encrypted_value, host_key, path, "
            "expires_utc, is_secure, is_httponly "
            "FROM cookies"
        ).fetchall()
        conn.close()
    finally:
        os.unlink(tmp)

    cookies = []
    for r in rows:
        value = _chrome_decrypt_value(r["encrypted_value"], key)
        if not value:
            continue
        # Chrome stores expiry as microseconds since 1601-01-01
        expiry = None
        if r["expires_utc"]:
            epoch = (r["expires_utc"] / 1_000_000) - 11644473600
            if epoch > 0:
                expiry = int(epoch)
        cookies.append({
            "name": r["name"],
            "value": value,
            "domain": r["host_key"],
            "path": r["path"] or "/",
            "expiry": expiry,
            "secure": bool(r["is_secure"]),
            "httpOnly": bool(r["is_httponly"]),
        })
    return cookies


# ─── JSON file ────────────────────────────────────────────────────────────

def read_json(path):
    """Read cookies from a JSON file (array of cookie dicts)."""
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("JSON cookie file must be an array of cookie objects.")
    cookies = []
    for c in data:
        cookies.append({
            "name": c.get("name", ""),
            "value": c.get("value", ""),
            "domain": c.get("domain", ""),
            "path": c.get("path", "/"),
            "expiry": c.get("expiry") or c.get("expirationDate"),
            "secure": c.get("secure", False),
            "httpOnly": c.get("httpOnly", False),
        })
    return cookies


# ─── Injection ────────────────────────────────────────────────────────────

def inject_cookies(client, cookies, verbose=False):
    """Inject cookies into a running session via the SessionClient.

    Groups cookies by domain, navigates to each domain to set them,
    then returns to the original page.
    """
    # Remember where we are
    original_url = client.send({"cmd": "current_url"})

    # Group by domain
    by_domain = {}
    for c in cookies:
        domain = c["domain"].lstrip(".")
        by_domain.setdefault(domain, []).append(c)

    injected = 0
    failed_domains = []

    for domain, domain_cookies in by_domain.items():
        # Navigate to the domain so Selenium allows setting cookies
        try:
            client.send({"cmd": "navigate", "url": f"https://{domain}/",
                         "timeout": 10})
        except Exception:
            try:
                client.send({"cmd": "navigate", "url": f"http://{domain}/",
                             "timeout": 10})
            except Exception:
                failed_domains.append(domain)
                continue

        # Inject each cookie
        for c in domain_cookies:
            cookie_dict = {
                "name": c["name"],
                "value": c["value"],
                "path": c["path"],
                "secure": c["secure"],
                "httpOnly": c["httpOnly"],
            }
            if c.get("domain"):
                cookie_dict["domain"] = c["domain"]
            if c.get("expiry"):
                cookie_dict["expiry"] = int(c["expiry"])
            try:
                client.send({"cmd": "add_cookie", "cookie": cookie_dict})
                injected += 1
            except Exception:
                pass

        if verbose:
            print(f"  {domain}: {len(domain_cookies)} cookies")

    # Go back to where we were
    try:
        if original_url and original_url != "about:blank":
            client.send({"cmd": "navigate", "url": original_url, "timeout": 10})
    except Exception:
        pass

    return injected, failed_domains
