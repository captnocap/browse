"""Script loader and parser for browse navigation flows.

Users write simple markdown files with numbered steps. The system
parses them, substitutes parameters, and formats them as agent
instructions or executes them directly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

BUILTIN_DIR = Path(__file__).parent / "scripts"
USER_DIR = Path.home() / ".config" / "browse" / "scripts"

_STEP_RE = re.compile(r"^\d+\.\s+(.+)$")
_PARAM_RE = re.compile(r"\{(\w+)\}")
_URL_RE = re.compile(r"https?://\S+")


@dataclass
class Script:
    name: str
    title: str
    steps: list[str]
    output: str | None = None
    params: list[str] = field(default_factory=list)
    path: Path | None = None


def parse_script(text: str, name: str = "", path: Path | None = None) -> Script:
    """Parse markdown text into a Script."""
    title = ""
    steps: list[str] = []
    output_lines: list[str] = []
    in_output = False

    for line in text.splitlines():
        stripped = line.strip()

        if not title and stripped.startswith("# "):
            title = stripped[2:].strip()
            continue

        if stripped.lower().startswith("## output"):
            in_output = True
            continue

        if in_output and stripped.startswith("## "):
            in_output = False

        if in_output:
            output_lines.append(line)
            continue

        m = _STEP_RE.match(stripped)
        if m:
            steps.append(m.group(1))

    output = "\n".join(output_lines).strip() or None

    params = sorted(set(
        _PARAM_RE.findall(" ".join(steps) + " " + (output or ""))
    ))

    return Script(
        name=name or _slug(title),
        title=title or name,
        steps=steps,
        output=output,
        params=params,
        path=path,
    )


def load_script(name_or_path: str) -> Script:
    """Load a script by name (searches both dirs) or by file path."""
    p = Path(name_or_path)
    if p.suffix == ".md" and p.exists():
        return parse_script(p.read_text(), name=p.stem, path=p)

    for d in (USER_DIR, BUILTIN_DIR):
        candidate = d / f"{name_or_path}.md"
        if candidate.exists():
            return parse_script(candidate.read_text(), name=name_or_path, path=candidate)

    raise FileNotFoundError(
        f"Script '{name_or_path}' not found in {USER_DIR} or {BUILTIN_DIR}"
    )


def list_scripts() -> list[Script]:
    """Discover all scripts from both directories. User scripts override built-in."""
    found: dict[str, Script] = {}

    for d in (BUILTIN_DIR, USER_DIR):
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            script = parse_script(f.read_text(), name=f.stem, path=f)
            found[script.name] = script

    return sorted(found.values(), key=lambda s: s.name)


def format_for_agent(script: Script, **params: str) -> str:
    """Render a script as structured instructions for an AI agent.

    Substitutes {param} placeholders with provided values.
    Returns a string ready to feed to an LLM as browsing instructions.
    """
    missing = [p for p in script.params if p not in params]
    if missing:
        raise ValueError(f"Missing parameters: {', '.join(missing)}")

    def sub(text: str) -> str:
        for k, v in params.items():
            text = text.replace(f"{{{k}}}", v)
        return text

    lines = [
        f"# Script: {sub(script.title)}",
        "",
        "Execute the following steps using the browser. "
        "Complete each step before moving to the next.",
        "",
    ]

    for i, step in enumerate(script.steps, 1):
        lines.append(f"{i}. {sub(step)}")

    if script.output:
        lines.append("")
        lines.append(f"**Output format:** {sub(script.output)}")

    return "\n".join(lines)


def _slug(title: str) -> str:
    """Convert a title to a filename-safe slug."""
    s = title.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s-]+", "-", s)
    return s.strip("-")
