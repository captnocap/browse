"""Top-level CLI dispatcher for the browse command.

    browse                          — launch a persistent browser session
    browse --disposable             — launch with a temporary profile
    browse curl <url>               — fetch a URL via the real stealth browser
    browse search <query>           — Google search via the real stealth browser
    browse block <domain>           — block a domain from agent navigation
    browse block --preset <name>    — block a curated set of domains
    browse unblock <domain>         — unblock a domain
    browse blocklist                — show all blocked domains
    browse cookies <source>         — import cookies from another browser
    browse scripts                  — list available navigation scripts
    browse run <name> [--key=val]   — execute a navigation script
    browse profile                  — show/manage profile configuration
    browse profile new              — create a fresh persistent profile
    browse profile clone            — clone a Firefox system profile
    browse profile use <path>       — use a system profile directly
    browse profile disposable       — set default to disposable profiles
"""

import os
import sys


CONF_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "browse.conf"
)

# ─── Presets ──────────────────────────────────────────────────────────────
# Curated domain lists that can be added in one shot.

PRESETS = {
    "malicious": [
        # Google typosquats
        "gooogle.com", "gogle.com", "googel.com", "goggle.com",
        "g00gle.com", "googlr.com", "googke.com", "googl.com",
        "google.cm", "google.co", "google.om",
        # Facebook typosquats
        "faceb00k.com", "facebok.com", "faceboook.com", "faecbook.com",
        "fcaebook.com", "faceboo.com",
        # YouTube typosquats
        "y0utube.com", "youttube.com", "youtub.com", "youube.com",
        "yotube.com", "youtbe.com",
        # Amazon typosquats
        "amaz0n.com", "amazn.com", "amazom.com", "amzon.com",
        "anazon.com",
        # Microsoft typosquats
        "micros0ft.com", "microsft.com", "mircosoft.com", "microsof.com",
        # Twitter/X typosquats
        "twiter.com", "twtter.com", "twittter.com",
        # Apple typosquats
        "appel.com", "aple.com", "appl.com",
        # PayPal typosquats
        "paypa1.com", "paypall.com", "paypl.com", "paypai.com",
        # Banking/finance phishing
        "chase-login.com", "wellsfarg0.com", "bankofamerica-login.com",
        # Known malware/scam TLDs and domains
        "bit.ly", "tinyurl.com",  # URL shorteners agents shouldn't follow
    ],
}


def _read_blocked():
    """Read the current BLOCKED_SITES from browse.conf."""
    if not os.path.exists(CONF_PATH):
        return set()
    with open(CONF_PATH) as f:
        for line in f:
            line = line.strip()
            if line.startswith("BLOCKED_SITES="):
                raw = line.split("=", 1)[1]
                return {d.strip().lower() for d in raw.split(",") if d.strip()}
    return set()


def _write_blocked(domains):
    """Write the BLOCKED_SITES line back to browse.conf."""
    if not os.path.exists(CONF_PATH):
        with open(CONF_PATH, "w") as f:
            f.write(f"BLOCKED_SITES={','.join(sorted(domains))}\n")
        return

    with open(CONF_PATH) as f:
        lines = f.readlines()

    found = False
    new_lines = []
    for line in lines:
        if line.strip().startswith("BLOCKED_SITES="):
            new_lines.append(f"BLOCKED_SITES={','.join(sorted(domains))}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"BLOCKED_SITES={','.join(sorted(domains))}\n")

    with open(CONF_PATH, "w") as f:
        f.writelines(new_lines)


def _normalize_domain(domain):
    """Strip protocol/path, keep just the domain."""
    domain = domain.lower().strip()
    if "://" in domain:
        domain = domain.split("://", 1)[1]
    domain = domain.split("/")[0]
    return domain


def _find_firefox_profiles():
    """Discover Firefox profiles from ~/.mozilla/firefox/profiles.ini."""
    import configparser
    profiles_ini = os.path.expanduser("~/.mozilla/firefox/profiles.ini")
    if not os.path.exists(profiles_ini):
        return []
    cp = configparser.ConfigParser()
    cp.read(profiles_ini)
    profiles = []
    for section in cp.sections():
        if not section.startswith("Profile"):
            continue
        name = cp.get(section, "Name", fallback=None)
        path = cp.get(section, "Path", fallback=None)
        is_relative = cp.getint(section, "IsRelative", fallback=1)
        if not path:
            continue
        if is_relative:
            full_path = os.path.expanduser(f"~/.mozilla/firefox/{path}")
        else:
            full_path = path
        if os.path.isdir(full_path):
            default = cp.getboolean(section, "Default", fallback=False)
            profiles.append({"name": name, "path": full_path, "default": default})
    return profiles


def _handle_profile(args):
    """Handle the browse profile subcommand."""
    import shutil

    browse_profile = os.path.expanduser("~/.config/browse/profile")

    if not args:
        # Show current profile config
        conf = {}
        if os.path.exists(CONF_PATH):
            with open(CONF_PATH) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        conf[k.strip()] = v.strip()

        mode = conf.get("PROFILE_MODE", "persistent")
        path = conf.get("PROFILE_PATH", browse_profile)
        print(f"  Mode: {mode}")
        print(f"  Path: {path}")
        exists = os.path.isdir(os.path.expanduser(path))
        print(f"  Exists: {'yes' if exists else 'no'}")
        print()
        print("  Commands:")
        print("    browse profile new           Create a fresh persistent profile")
        print("    browse profile clone          Clone a Firefox system profile")
        print("    browse profile use <path>     Use a system profile directly (lock warning)")
        print("    browse profile disposable     Set default to disposable (temp) profiles")
        return

    subcmd = args[0]

    if subcmd == "new":
        if os.path.isdir(browse_profile):
            confirm = input(f"  Profile already exists at {browse_profile}. Overwrite? [y/N] ").strip().lower()
            if confirm != "y":
                print("  Aborted.")
                return
            shutil.rmtree(browse_profile)
        os.makedirs(browse_profile, exist_ok=True)
        _set_conf("PROFILE_MODE", "persistent")
        _set_conf("PROFILE_PATH", browse_profile)
        print(f"  Created fresh profile at {browse_profile}")
        print("  This is now your default profile.")

    elif subcmd == "clone":
        profiles = _find_firefox_profiles()
        if not profiles:
            print("  No Firefox profiles found in ~/.mozilla/firefox/")
            sys.exit(1)

        print("  Available Firefox profiles:")
        for i, p in enumerate(profiles):
            default_tag = " (default)" if p["default"] else ""
            print(f"    [{i}] {p['name']}{default_tag}")
            print(f"        {p['path']}")
        print()

        choice = input("  Clone which profile? [number] ").strip()
        try:
            idx = int(choice)
            source = profiles[idx]
        except (ValueError, IndexError):
            print("  Invalid choice.")
            return

        if os.path.isdir(browse_profile):
            confirm = input(f"  Profile already exists at {browse_profile}. Overwrite? [y/N] ").strip().lower()
            if confirm != "y":
                print("  Aborted.")
                return
            shutil.rmtree(browse_profile)

        print(f"  Cloning '{source['name']}' → {browse_profile}")
        skip_files = {"lock", ".parentlock", "parent.lock", "compatibility.ini"}
        shutil.copytree(
            source["path"], browse_profile,
            ignore=lambda d, files: [f for f in files if f in skip_files],
        )
        _set_conf("PROFILE_MODE", "persistent")
        _set_conf("PROFILE_PATH", browse_profile)
        print("  Done. This is now your default profile.")
        print("  Your original Firefox profile is untouched.")

    elif subcmd == "use":
        if len(args) < 2:
            # List available profiles for the user to pick
            profiles = _find_firefox_profiles()
            if not profiles:
                print("  No Firefox profiles found.")
                print("  Usage: browse profile use <path>")
                sys.exit(1)

            print("  Available Firefox profiles:")
            for i, p in enumerate(profiles):
                default_tag = " (default)" if p["default"] else ""
                print(f"    [{i}] {p['name']}{default_tag}")
                print(f"        {p['path']}")
            print()
            print("  WARNING: Using a system profile directly means Firefox and")
            print("  browse cannot run at the same time (profile lock conflict).")
            print()

            choice = input("  Use which profile? [number] ").strip()
            try:
                idx = int(choice)
                target = profiles[idx]["path"]
            except (ValueError, IndexError):
                print("  Invalid choice.")
                return
        else:
            target = os.path.expanduser(args[1])
            if not os.path.isdir(target):
                print(f"  Not a directory: {target}")
                sys.exit(1)

        print(f"  WARNING: Using system profile directly at {target}")
        print("  Firefox must be closed when running browse with this profile.")
        _set_conf("PROFILE_MODE", "persistent")
        _set_conf("PROFILE_PATH", target)
        print(f"  Default profile set to: {target}")

    elif subcmd == "disposable":
        _set_conf("PROFILE_MODE", "disposable")
        print("  Default set to disposable (temporary) profiles.")
        print("  Each launch gets a fresh profile that's discarded on exit.")

    else:
        print(f"  Unknown profile command: {subcmd}")
        print("  Commands: new, clone, use, disposable")
        sys.exit(1)


def _set_conf(key, value):
    """Set a key in browse.conf."""
    if not os.path.exists(CONF_PATH):
        with open(CONF_PATH, "w") as f:
            f.write(f"{key}={value}\n")
        return
    with open(CONF_PATH) as f:
        lines = f.readlines()
    found = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}={value}\n")
    with open(CONF_PATH, "w") as f:
        f.writelines(new_lines)


def _read_conf():
    """Read browse.conf into a dict."""
    conf = {}
    if not os.path.exists(CONF_PATH):
        return conf
    with open(CONF_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                conf[k.strip()] = v.strip()
    return conf


def _acquire_agent(prefer_session=True, quiet=False):
    """Return (agent, owns) — connect to running session if available, else spawn quick.

    Quick mode reuses the persistent profile from browse.conf so cookies/history
    survive (Google etc. won't gate a zero-history profile). Profile lock is free
    because we only spawn quick when no session is running.
    """
    from .agent import AgentBrowser
    if prefer_session:
        from .session import get_session_info
        if get_session_info():
            if not quiet:
                print("[browse] using running session", file=sys.stderr)
            return AgentBrowser.connect(), False
    conf = _read_conf()
    profile_path = None
    if conf.get("PROFILE_MODE", "persistent") == "persistent":
        path = conf.get("PROFILE_PATH")
        if path and os.path.isdir(os.path.expanduser(path)):
            profile_path = os.path.expanduser(path)
    if not quiet:
        if profile_path:
            print(f"[browse] no session — spawning quick browser with persistent profile",
                  file=sys.stderr)
        else:
            print("[browse] no session running — spawning quick browser (disposable)",
                  file=sys.stderr)
    return AgentBrowser(profile_path=profile_path), True


def _render_content(content, mode):
    """Render PageContent in the requested output mode."""
    import json
    if mode == "json":
        return json.dumps({
            "url": content.url,
            "title": content.title,
            "text": content.text,
            "links": [{"text": l.text, "href": l.href} for l in content.links],
            "forms": [{"action": f.action, "method": f.method,
                       "fields": [{"name": ff.name, "type": ff.type,
                                   "value": ff.value, "placeholder": ff.placeholder}
                                  for ff in f.fields]}
                      for f in content.forms],
        }, indent=2)
    if mode == "text":
        return content.text
    if mode == "links":
        return "\n".join(f"{l.href}\t{l.text}" for l in content.links)
    if mode == "html":
        # Caller should pass page_source separately
        return content
    return content.for_llm()


def _parse_fetch_args(args, usage):
    """Parse shared flags for curl/search. Returns (positional, opts)."""
    opts = {"mode": "llm", "output": None, "screenshot": None,
            "timeout": 30, "wait": 0, "quick": False, "html": False}
    positional = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--json",):
            opts["mode"] = "json"
        elif a in ("--text",):
            opts["mode"] = "text"
        elif a in ("--links",):
            opts["mode"] = "links"
        elif a in ("--html",):
            opts["html"] = True
        elif a in ("-o", "--output"):
            i += 1
            opts["output"] = args[i]
        elif a == "--screenshot":
            i += 1
            opts["screenshot"] = args[i]
        elif a in ("--timeout",):
            i += 1
            opts["timeout"] = int(args[i])
        elif a in ("--wait",):
            i += 1
            opts["wait"] = float(args[i])
        elif a == "--quick":
            opts["quick"] = True
        elif a in ("-h", "--help"):
            print(usage)
            sys.exit(0)
        elif a.startswith("-"):
            print(f"Unknown option: {a}\n{usage}", file=sys.stderr)
            sys.exit(2)
        else:
            positional.append(a)
        i += 1
    return positional, opts


def _emit(payload, output):
    if output:
        mode = "wb" if isinstance(payload, (bytes, bytearray)) else "w"
        with open(output, mode) as f:
            f.write(payload)
        print(f"[browse] wrote {output}", file=sys.stderr)
    else:
        if isinstance(payload, (bytes, bytearray)):
            sys.stdout.buffer.write(payload)
        else:
            print(payload)


def _handle_curl(args):
    usage = (
        "Usage: browse curl <url> [--json|--text|--links|--html] "
        "[-o file] [--screenshot path] [--timeout N] [--wait N] [--quick]"
    )
    positional, opts = _parse_fetch_args(args, usage)
    if not positional:
        print(usage, file=sys.stderr)
        sys.exit(1)
    url = positional[0]
    if "://" not in url:
        url = "https://" + url

    agent, owns = _acquire_agent(prefer_session=not opts["quick"])
    try:
        content = agent.navigate(url, timeout=opts["timeout"])
        if opts["wait"]:
            import time
            time.sleep(opts["wait"])
            content = agent.extract_content()
        if opts["screenshot"]:
            agent.screenshot(opts["screenshot"])
            print(f"[browse] screenshot saved to {opts['screenshot']}",
                  file=sys.stderr)
        if opts["html"]:
            _emit(agent.page_source, opts["output"])
        else:
            _emit(_render_content(content, opts["mode"]), opts["output"])
    finally:
        if owns:
            agent.quit()
        else:
            agent.detach()


def _handle_search(args):
    usage = (
        "Usage: browse search <query...> [--json|--text|--links|--html] "
        "[-o file] [--screenshot path] [--timeout N] [--wait N] [--quick] "
        "[--engine google|ddg]"
    )
    # Extract --engine before generic parse
    engine = "google"
    cleaned = []
    i = 0
    while i < len(args):
        if args[i] == "--engine":
            engine = args[i + 1]
            i += 2
            continue
        cleaned.append(args[i])
        i += 1

    positional, opts = _parse_fetch_args(cleaned, usage)
    if not positional:
        print(usage, file=sys.stderr)
        sys.exit(1)

    from urllib.parse import quote_plus
    query = " ".join(positional)
    if engine == "ddg":
        url = f"https://duckduckgo.com/?q={quote_plus(query)}"
    else:
        url = f"https://www.google.com/search?q={quote_plus(query)}"

    agent, owns = _acquire_agent(prefer_session=not opts["quick"])
    try:
        content = agent.navigate(url, timeout=opts["timeout"])
        if opts["wait"]:
            import time
            time.sleep(opts["wait"])
            content = agent.extract_content()
        if opts["screenshot"]:
            agent.screenshot(opts["screenshot"])
            print(f"[browse] screenshot saved to {opts['screenshot']}",
                  file=sys.stderr)
        if opts["html"]:
            _emit(agent.page_source, opts["output"])
        else:
            _emit(_render_content(content, opts["mode"]), opts["output"])
    finally:
        if owns:
            agent.quit()
        else:
            agent.detach()


# ─── Advanced multi-engine search ─────────────────────────────────────────

ASEARCH_ENGINES = {
    "google": "https://www.google.com/search?q={}",
    "duckduckgo": "https://duckduckgo.com/?q={}",
    "bing": "https://www.bing.com/search?q={}",
}

_NAV_HOSTS = {
    "google": ("google.com", "gstatic.com", "googleusercontent.com",
               "googleadservices.com"),
    "duckduckgo": ("duckduckgo.com", "duck.com", "duck.ai", "spreadprivacy.com"),
    "bing": ("bing.com", "microsoft.com", "microsofttranslator.com",
             "msn.com", "go.microsoft.com"),
}


def _host_is_nav(host, engine):
    host = host.lower()
    if host.startswith("www."):
        host = host[4:]
    for bad in _NAV_HOSTS[engine]:
        if host == bad or host.endswith("." + bad):
            return True
    return False


def _bing_unwrap(url):
    """Unwrap bing.com/ck/a redirect URLs to recover the real destination."""
    if "bing.com/ck/a" not in url:
        return url
    from urllib.parse import urlparse, parse_qs
    import base64
    try:
        q = parse_qs(urlparse(url).query)
        u = q.get("u", [None])[0]
        if not u or len(u) < 3:
            return url
        b = u[2:] + "=" * (-(len(u) - 2) % 4)
        decoded = base64.urlsafe_b64decode(b).decode("utf-8", errors="ignore")
        if decoded.startswith("http"):
            return decoded
    except Exception:
        pass
    return url


def _normalize_result_url(url):
    """Lowercase host, strip www., strip tracking params, strip trailing slash."""
    from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
    BAD = {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
           "fbclid", "gclid", "ref", "ref_src", "_ga", "mc_cid", "mc_eid",
           "sca_esv", "sa", "ved", "usg", "ictx", "fbs", "aep", "ntc",
           "source", "ei", "iflsig", "uact", "oq", "sourceid"}
    try:
        p = urlparse(url)
    except Exception:
        return None
    if p.scheme not in ("http", "https"):
        return None
    host = p.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    qs = [(k, v) for k, v in parse_qsl(p.query) if k.lower() not in BAD]
    path = p.path.rstrip("/") or "/"
    query = urlencode(qs) if qs else ""
    return urlunparse((p.scheme, host, path, "", query, ""))


def _extract_results(content, engine):
    """Filter PageContent.links to real result links for one engine.

    Returns deduped, ordered list of (normalized_url, display_text).
    """
    from urllib.parse import urlparse
    seen = set()
    results = []
    for link in content.links:
        href = link.href.strip()
        if not href.startswith(("http://", "https://")):
            continue
        if engine == "bing":
            href = _bing_unwrap(href)
        try:
            host = urlparse(href).netloc.lower()
        except Exception:
            continue
        if not host or _host_is_nav(host, engine):
            continue
        norm = _normalize_result_url(href)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        text = (link.text or "").strip() or host
        results.append((norm, text))
    return results


def _handle_asearch(args):
    usage = (
        "Usage: browse asearch <query...> [--engines google,duckduckgo,bing] "
        "[--json] [-o file] [--timeout N] [--wait N] [--quick] [--top N]"
    )
    engines = list(ASEARCH_ENGINES.keys())
    top = 25
    cleaned = []
    i = 0
    while i < len(args):
        if args[i] == "--engines":
            engines = [e.strip() for e in args[i + 1].split(",") if e.strip()]
            i += 2
            continue
        if args[i] == "--top":
            top = int(args[i + 1])
            i += 2
            continue
        cleaned.append(args[i])
        i += 1

    unknown = [e for e in engines if e not in ASEARCH_ENGINES]
    if unknown:
        print(f"Unknown engines: {', '.join(unknown)}", file=sys.stderr)
        print(f"Available: {', '.join(ASEARCH_ENGINES)}", file=sys.stderr)
        sys.exit(2)

    positional, opts = _parse_fetch_args(cleaned, usage)
    if not positional:
        print(usage, file=sys.stderr)
        sys.exit(1)

    from urllib.parse import quote_plus
    query = " ".join(positional)
    encoded = quote_plus(query)

    # Default settle wait — Bing especially needs JS to render results.
    settle = opts["wait"] if opts["wait"] else 2.0

    agent, owns = _acquire_agent(prefer_session=not opts["quick"])
    rank_score = {}  # normalized_url -> {"text": str, "engines": {engine: rank}}
    try:
        import time
        for engine in engines:
            url = ASEARCH_ENGINES[engine].format(encoded)
            print(f"[browse] querying {engine}...", file=sys.stderr)
            content = agent.navigate(url, timeout=opts["timeout"])
            time.sleep(settle)
            content = agent.extract_content()
            results = _extract_results(content, engine)
            for rank, (norm, text) in enumerate(results[:50], 1):
                entry = rank_score.setdefault(norm, {"text": text, "engines": {}})
                if len(text) > len(entry["text"]):
                    entry["text"] = text
                entry["engines"][engine] = rank
    finally:
        if owns:
            agent.quit()
        else:
            agent.detach()

    def score(entry):
        # Primary: number of engines it appeared on. Tiebreaker: sum of 1/rank.
        return (len(entry["engines"]),
                sum(1.0 / r for r in entry["engines"].values()))

    ranked = sorted(rank_score.items(), key=lambda kv: score(kv[1]),
                    reverse=True)[:top]
    n_engines = len(engines)

    if opts["mode"] == "json":
        import json
        payload = json.dumps([
            {"url": norm, "title": e["text"],
             "engines": e["engines"], "overlap": len(e["engines"]),
             "max_overlap": n_engines}
            for norm, e in ranked
        ], indent=2)
        _emit(payload, opts["output"])
        return

    lines = [f"Advanced search: {query!r} across {', '.join(engines)}", ""]
    for norm, e in ranked:
        engs = sorted(e["engines"].keys())
        ranks = ",".join(f"{k[:1]}={e['engines'][k]}" for k in engs)
        lines.append(
            f"[{len(e['engines'])}/{n_engines}] ({ranks})  {e['text'][:80]}")
        lines.append(f"        {norm}")
    _emit("\n".join(lines), opts["output"])


def main():
    args = sys.argv[1:]

    if not args or args[0].startswith("-"):
        # No subcommand — launch browser session
        from .session import main as session_main
        session_main()
        return

    cmd = args[0]

    if cmd == "curl":
        _handle_curl(args[1:])
        return

    if cmd == "search":
        _handle_search(args[1:])
        return

    if cmd in ("asearch", "search-all"):
        _handle_asearch(args[1:])
        return

    if cmd == "block":
        if len(args) < 2:
            print("Usage: browse block <domain>")
            print("       browse block --preset <name>")
            print(f"  Available presets: {', '.join(PRESETS.keys())}")
            sys.exit(1)

        if args[1] == "--preset":
            name = args[2] if len(args) > 2 else None
            if name not in PRESETS:
                print(f"Unknown preset: {name}")
                print(f"Available presets: {', '.join(PRESETS.keys())}")
                sys.exit(1)
            blocked = _read_blocked()
            added = []
            for d in PRESETS[name]:
                if d not in blocked:
                    blocked.add(d)
                    added.append(d)
            _write_blocked(blocked)
            print(f"Added {len(added)} domains from '{name}' preset ({len(PRESETS[name])} total, {len(PRESETS[name]) - len(added)} already blocked).")
        else:
            domain = _normalize_domain(args[1])
            blocked = _read_blocked()
            if domain in blocked:
                print(f"{domain} is already blocked.")
            else:
                blocked.add(domain)
                _write_blocked(blocked)
                print(f"Blocked {domain}")

    elif cmd == "unblock":
        if len(args) < 2:
            print("Usage: browse unblock <domain>")
            sys.exit(1)
        domain = _normalize_domain(args[1])
        blocked = _read_blocked()
        if domain not in blocked:
            print(f"{domain} is not blocked.")
        else:
            blocked.discard(domain)
            _write_blocked(blocked)
            print(f"Unblocked {domain}")

    elif cmd == "blocklist":
        blocked = _read_blocked()
        if blocked:
            for d in sorted(blocked):
                print(f"  {d}")
        else:
            print("No sites blocked.")

    elif cmd == "cookies":
        if len(args) < 2:
            print("Usage: browse cookies <source>")
            print("  Sources: firefox, chrome, chromium, brave, <path-to-json>")
            sys.exit(1)

        source = args[1]

        # Read cookies from source
        from .cookies import read_firefox, read_chrome, read_json, inject_cookies
        if source == "firefox":
            print("Reading cookies from Firefox...")
            cookies = read_firefox()
        elif source in ("chrome", "chromium", "brave"):
            print(f"Reading cookies from {source}...")
            cookies = read_chrome(browser=source)
        elif os.path.isfile(source):
            print(f"Reading cookies from {source}...")
            cookies = read_json(source)
        else:
            print(f"Unknown source: {source}")
            print("  Sources: firefox, chrome, chromium, brave, <path-to-json>")
            sys.exit(1)

        if not cookies:
            print("No cookies found.")
            sys.exit(0)

        # Domain filter
        domains = None
        if len(args) > 2:
            domains = {d.lower().lstrip(".") for d in args[2:]}
            cookies = [c for c in cookies
                       if any(c["domain"].lstrip(".").endswith(d) for d in domains)]
            print(f"Filtered to {len(cookies)} cookies for: {', '.join(domains)}")
        else:
            domain_count = len({c["domain"].lstrip(".") for c in cookies})
            print(f"Found {len(cookies)} cookies across {domain_count} domains.")
            if domain_count > 20:
                print(f"\nThis will navigate to {domain_count} domains to inject cookies.")
                print(f"Filter with: browse cookies {source} github.com google.com ...")
                confirm = input("Continue anyway? [y/N] ").strip().lower()
                if confirm != "y":
                    print("Aborted.")
                    sys.exit(0)

        # Connect to session and inject
        from .session import get_session_info, SessionClient
        session = get_session_info()
        if not session:
            print("No browser session running. Start one first with: browse")
            sys.exit(1)

        client = SessionClient(port=session["port"])
        client.send({"cmd": "ping"})

        print("Injecting cookies into session...")
        injected, failed = inject_cookies(client, cookies, verbose=True)
        client.close()

        print(f"\nDone. {injected} cookies injected.")
        if failed:
            print(f"Could not reach {len(failed)} domains: {', '.join(failed[:10])}")

    elif cmd == "scripts":
        from .scripts import list_scripts
        scripts = list_scripts()
        if not scripts:
            print("No scripts found.")
            print(f"  Built-in: {os.path.join(os.path.dirname(__file__), 'scripts')}")
            print(f"  User:     {os.path.expanduser('~/.config/browse/scripts')}")
        else:
            for s in scripts:
                params = f" ({', '.join('{' + p + '}' for p in s.params)})" if s.params else ""
                loc = "user" if str(s.path).startswith(os.path.expanduser("~/.config")) else "built-in"
                print(f"  {s.name:<20} {s.title}{params}  [{loc}]")

    elif cmd == "run":
        if len(args) < 2:
            print("Usage: browse run <script-name> [--key=value ...]")
            sys.exit(1)

        script_name = args[1]
        params = {}
        for a in args[2:]:
            if a.startswith("--") and "=" in a:
                k, v = a[2:].split("=", 1)
                params[k] = v

        from .scripts import load_script, format_for_agent
        try:
            script = load_script(script_name)
        except FileNotFoundError as e:
            print(str(e))
            sys.exit(1)

        missing = [p for p in script.params if p not in params]
        if missing:
            print(f"Missing parameters: {', '.join('--' + p + '=...' for p in missing)}")
            sys.exit(1)

        from .session import get_session_info, connect_to_session
        session = get_session_info()
        if not session:
            print("No browser session running. Start one first with: browse")
            sys.exit(1)

        from .agent import AgentBrowser
        agent = AgentBrowser.connect()

        try:
            results = agent.run_script(script_name, **params)
            for i, content in enumerate(results):
                print(f"\n--- Step {i + 1} ---")
                print(content.for_llm())
        finally:
            agent.detach()

    elif cmd == "profile":
        _handle_profile(args[1:])

    else:
        print(f"Unknown command: {cmd}")
        print("Usage: browse [curl|search|asearch|block|unblock|blocklist|cookies|scripts|run|profile]")
        sys.exit(1)
