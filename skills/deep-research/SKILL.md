---
name: deep-research
description: >
  Use when the user asks to "research", "deep dive", "investigate",
  "do a deep research on", "look into", or wants comprehensive multi-source
  research on any topic. Also triggers on "/research <topic>". Combines
  WebSearch for broad discovery with the browse tool for deep reading of
  full articles. Produces a structured research directory with findings,
  sources, and raw transcripts.
version: 1.0.0
---

# Deep Research

Multi-phase research workflow that combines WebSearch (broad discovery) with the browse tool (deep article reading) to produce comprehensive, well-sourced research on any topic. Output is a structured directory of findings, annotated sources, and raw transcripts.

## Workflow

### Phase 1: Decompose

Break the topic into 3-5 research angles. Each angle is a distinct sub-topic, perspective, or domain worth investigating independently.

1. Analyze the topic and identify angles (e.g. for "fusion energy": scientific breakthroughs, major companies, regulatory landscape, investment trends, technical challenges)
2. Create the output directory:
   ```
   research/<topic-slug>/
   ├── angles/
   └── transcripts/
   ```
3. Write `angles.md` listing each angle with 2-3 guiding research questions
4. **Ask the user** to confirm or adjust the angles before proceeding

### Phase 2: WebSearch Survey

Use the built-in WebSearch tool to cast a wide net across all angles.

For each angle:
1. Run 2-3 WebSearch queries with different phrasings (broad, specific, recent)
2. Collect every URL, title, and snippet returned

After all searches complete:
1. Deduplicate URLs
2. Categorize each source by angle
3. Rate priority: **high** (directly relevant, authoritative), **medium** (useful context), **low** (tangential)
4. Write `sources.md` with the full categorized inventory
5. Identify the top ~15 high-priority links for deep diving

### Phase 3: Browse Deep Dive

Use the browse tool to read full articles and find sources WebSearch missed.

**For each high-priority link:**
```bash
python3 -c "
from browse import AgentBrowser
agent = AgentBrowser.connect()
content = agent.navigate('<url>')
print(content.for_llm())
agent.detach()
"
```

Save each extraction to `transcripts/<source-slug>.md` with this header:
```markdown
# <Article Title>
- **URL:** <url>
- **Extracted:** <date>
- **Tool:** browse
- **Angle:** <which angle this relates to>

---

<full extracted text>
```

**For each angle**, also run 1-2 Google searches through browse to find supplementary sources:
```bash
python3 -c "
from browse import AgentBrowser
agent = AgentBrowser.connect()
content = agent.navigate('https://www.google.com/search?q=<angle-specific+query>')
print(content.for_llm())
agent.detach()
"
```

Follow promising new links discovered in articles or Google results. Save those transcripts too.

**Important:** Always `agent.detach()` after each navigation. Connect fresh for each page visit to avoid holding the session.

### Phase 4: Synthesis

Write the final research output.

**Per-angle reports** (`angles/<angle-slug>.md`):
```markdown
# <Angle Title>

## Key Findings
- Finding with [source citation](url)
- Finding with [source citation](url)

## Notable Data Points
- Statistic or quote with attribution

## Gaps & Contradictions
- What sources disagreed on or didn't cover
```

**Executive summary** (`README.md`):
```markdown
# Research: <Topic>

## Overview
<2-3 paragraph summary of the topic landscape>

## Key Findings
- <Top 5-7 bullet points across all angles>

## Research Angles
| Angle | Key Insight | Sources |
|---|---|---|
| <angle> | <one-line takeaway> | <count> |

## Methodology
- **WebSearch queries:** <count>
- **Browse pages visited:** <count>
- **Total sources:** <count>
- **Transcripts saved:** <count>

## Files
- [angles.md](angles.md) — Research angles and questions
- [sources.md](sources.md) — Complete source inventory
- [angles/<name>.md](angles/<name>.md) — Detailed findings per angle
- [transcripts/](transcripts/) — Raw page extractions
```

**Update `sources.md`** with final annotations:
```markdown
| # | URL | Title | Tool | Angle | Priority | Key Takeaway |
|---|---|---|---|---|---|---|
| 1 | <url> | <title> | WebSearch | <angle> | high | <one-line> |
| 2 | <url> | <title> | browse | <angle> | high | <one-line> |
```

## Rules

1. **Always cite sources** — every claim in angle reports links back to a source URL
2. **Save every transcript** — raw browse extractions go to `transcripts/` so the user can verify
3. **Track the tool** — every source in `sources.md` notes whether it came from WebSearch, WebFetch, or browse
4. **Write progressively** — create files as each phase completes, don't wait until the end
5. **No fabrication** — if a source doesn't support a claim, don't include it. Note gaps explicitly.
6. **Respect the browser** — one browse connection at a time, always detach when done
7. **Ask before diving** — confirm research angles with the user after Phase 1 before spending time on Phases 2-4
