"""Top-level CLI dispatcher for the browse command.

    browse                          — launch a persistent browser session
    browse block <domain>           — block a domain from agent navigation
    browse block --preset <name>    — block a curated set of domains
    browse unblock <domain>         — unblock a domain
    browse blocklist                — show all blocked domains
    browse cookies <source>         — import cookies from another browser
    browse scripts                  — list available navigation scripts
    browse run <name> [--key=val]   — execute a navigation script
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


def main():
    args = sys.argv[1:]

    if not args or args[0].startswith("-"):
        # No subcommand — launch browser session
        from .session import main as session_main
        session_main()
        return

    cmd = args[0]

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

    else:
        print(f"Unknown command: {cmd}")
        print("Usage: browse [block|unblock|blocklist|cookies|scripts|run]")
        sys.exit(1)
