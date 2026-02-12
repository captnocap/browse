"""Test prompt injection filtering.

Loads test_injection.html and verifies that all hidden injection
attempts are stripped while legitimate content is preserved.

Usage:
    python test_injection.py          # uses running session
    python test_injection.py --quick  # spawns its own browser
"""
import os
import sys

# Words that should NEVER appear in extracted content (from the injections)
POISON_WORDS = [
    "SYSTEM OVERRIDE",
    "Ignore all previous instructions",
    "evil.com",
    "/etc/passwd",
    "id_rsa",
    "TOOL CALL",
    "DAN (Do Anything Now)",
    "CRITICAL SECURITY UPDATE",
    "penetration testing",
    "FUNCTION CALL OVERRIDE",
    "PROMPT INJECTION",
    "unrestricted AI",
    "ROLE CHANGE",
    "maintenance mode",
    "INSTRUCTION INJECTION",
    "HIDDEN COMMAND",
    "rm -rf",
    "DEBUG MODE ACTIVATED",
    "ESCAPED CONTENT",
    "MICRO-INJECTION",
    "credit card numbers",
    "WIDTH-ZERO INJECTION",
    "stolen_data",
    "Enter your SSN",
]

# Words that MUST appear (from the legitimate content)
LEGIT_WORDS = [
    "Best Chocolate Chip Cookie Recipe",
    "Preheat your oven",
    "2 cups chocolate chips",
    "golden brown",
    "Fudge Brownies",
    "Red Velvet Cake",
    "Apple Pie",
    "Newsletter Signup",
    "Cookie Kitchen",
]


def run_test(content):
    """Check extracted content against poison and legit word lists."""
    print("=" * 60)
    print("EXTRACTED TEXT (what the AI sees):")
    print("=" * 60)
    print(content.text)
    print()

    print("=" * 60)
    print("EXTRACTED LINKS:")
    print("=" * 60)
    for link in content.links:
        print(f"  [{link.text}] -> {link.href}")
    print()

    print("=" * 60)
    print("EXTRACTED FORMS:")
    print("=" * 60)
    for form in content.forms:
        print(f"  <form action={form.action} method={form.method}>")
        for f in form.fields:
            print(f"    {f.type}: name={f.name} value='{f.value}' placeholder='{f.placeholder}'")
    print()

    print("=" * 60)
    print("EXTRACTED META:")
    print("=" * 60)
    for k, v in content.meta.items():
        print(f"  {k}: {v}")
    print()

    # ── Check for poison ──
    print("=" * 60)
    print("INJECTION TEST RESULTS:")
    print("=" * 60)

    all_text = content.text.lower()
    # Also check link texts and hrefs
    for link in content.links:
        all_text += " " + link.text.lower() + " " + link.href.lower()
    # Also check form fields
    for form in content.forms:
        all_text += " " + form.action.lower()
        for f in form.fields:
            all_text += " " + f.value.lower() + " " + f.placeholder.lower()
    # Also check meta
    for v in content.meta.values():
        all_text += " " + v.lower()

    blocked = 0
    leaked = 0
    for word in POISON_WORDS:
        if word.lower() in all_text:
            print(f"  LEAKED:  {word}")
            leaked += 1
        else:
            print(f"  BLOCKED: {word}")
            blocked += 1

    print()

    # ── Check for legit content ──
    print("=" * 60)
    print("LEGITIMATE CONTENT CHECK:")
    print("=" * 60)

    preserved = 0
    lost = 0
    for word in LEGIT_WORDS:
        if word.lower() in content.text.lower():
            print(f"  KEPT:    {word}")
            preserved += 1
        else:
            print(f"  LOST:    {word}")
            lost += 1

    print()

    # ── Summary ──
    print("=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    print(f"  Injections blocked: {blocked}/{len(POISON_WORDS)}")
    print(f"  Injections leaked:  {leaked}/{len(POISON_WORDS)}")
    print(f"  Legit preserved:    {preserved}/{len(LEGIT_WORDS)}")
    print(f"  Legit lost:         {lost}/{len(LEGIT_WORDS)}")
    print()

    if leaked == 0 and lost == 0:
        print("  ALL TESTS PASSED")
    elif leaked > 0:
        print(f"  FAILED — {leaked} injection(s) got through!")
    elif lost > 0:
        print(f"  WARNING — {lost} legitimate content item(s) were stripped")

    print()

    # ── Show LLM-formatted output ──
    print("=" * 60)
    print("LLM OUTPUT (what gets sent to the model):")
    print("=" * 60)
    print(content.for_llm())


def main():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "test_injection.html")
    file_url = f"file://{html_path}"

    if "--quick" in sys.argv:
        from browse import AgentBrowser
        print(f"Loading {file_url} in quick mode...\n")
        with AgentBrowser() as browser:
            content = browser.navigate(file_url)
            run_test(content)
    else:
        from browse import AgentBrowser
        print(f"Connecting to session and loading {file_url}...\n")
        agent = AgentBrowser.connect()
        try:
            content = agent.navigate(file_url)
            run_test(content)
        finally:
            agent.detach()


if __name__ == "__main__":
    main()
