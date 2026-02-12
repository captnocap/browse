---
name: deep-research
description: >
  Use when the user asks to "research", "deep dive", "investigate",
  "do a deep research on", "look into", or wants comprehensive multi-source
  research on any topic. Also triggers on "/research <topic>". Runs 10
  parallel agents across structured angles, then synthesizes with
  cross-referenced traceability. Produces a research directory with
  per-angle findings, executive synthesis, consolidated sources, and a
  run log.
version: 2.0.0
---

# Deep Research

10-agent parallel research swarm. Each agent takes one angle, researches independently, and outputs a short structured markdown section with citations. A synthesis pass reads all 10 and produces a cross-referenced executive summary.

**Workflow:** Topic → 10 Angles → Parallel Runs → Synthesis

## Phase 0: Topic

The user provides a topic, or you choose one. Good topics benefit from multi-angle coverage:
- Fast-moving tech + policy (AI agents, BCIs, fusion)
- Controversial claims where triangulation matters
- "Market + science + ethics" intersections

## Phase 1: Generate 10 Angles

Create a `research_runs/<date>__<topic-slug>/` directory with an `angles/` subdirectory and a `.start_time` file.

Use these 10 standard angles (adapt labels to fit the topic):

| # | Angle | Lens |
|---|---|---|
| 01 | Freshness | What changed in the last 6-12 months |
| 02 | Technical | State of the art — capabilities and limits |
| 03 | Market | Business reality — pricing, adoption, winners |
| 04 | Regulation | Laws, enforcement, standards |
| 05 | Security | Fraud, misuse, attack surfaces, mitigations |
| 06 | Ethics | Harms, equity, labor, societal impact |
| 07 | Players | Key players and incentives — who benefits, who loses |
| 08 | Failures | Critical failures and known issues — what breaks, why |
| 09 | Contrarian | Best skeptical critique of the space |
| 10 | Predictions | Short-horizon predictions with confidence bands |

You can generate bespoke angles per topic instead, but the standard backbone makes results comparable across research runs.

**Ask the user** to confirm or adjust the angles before proceeding.

## Phase 2: Parallel Research

Spawn 10 agents using the Task tool. Each agent gets one angle, researches it, and writes its findings to `angles/<NN>_<slug>.md`.

### Agent tool assignments

| Agents | Tool Access | Why |
|---|---|---|
| 7 agents (angles 01-07) | WebSearch/WebFetch only | Fast breadth — these angles need wide source discovery |
| 2 agents (angles 08-09) | Browse only | Deep reads — failures and contrarian views live in long-form articles, HN threads, niche blogs |
| 1 agent (angle 10) | Both | Triangulator — cross-references predictions against data from both tool types |

**Critical:** Browse agents must run sequentially (or use tab isolation if available). Only one browse connection at a time. WebSearch agents can all run in parallel.

Launch order:
1. All 7 WebSearch agents in parallel (angles 01-07)
2. Browse agent for angle 08 (wait for completion)
3. Browse agent for angle 09 (wait for completion)
4. Mixed agent for angle 10 (can run in parallel with WebSearch agents)

### Agent prompt template

Each agent receives this prompt (fill in the angle):

```
You are a research agent. Your task: investigate ONE angle of a research topic.

Topic: "<topic>"
Your angle: "<angle name> — <angle description>"
Tool access: <WebSearch/WebFetch | Browse only | Both>

Research thoroughly using your available tools. Spend 3-6 minutes.

Write your findings to: <path>/angles/<NN>_<slug>.md

Use EXACTLY this format:

# Angle <NN> — <Angle Name>

## Claims (with confidence)
- Claim (high): <specific, falsifiable claim with evidence>
- Claim (medium): <supported but less certain>
- Claim (low): <directional, needs more evidence>

## Evidence
- <specific evidence> — [Source Name](url)
- <specific evidence> — [Source Name](url)

## What I'm unsure about
- <gaps, unknowns, things that need more primary sources>

## Sources
- [Title](url)
- [Title](url)

Rules:
- Keep it SHORT. No essays. Claims + evidence + sources.
- Every claim needs a confidence level (high/medium/low).
- Every piece of evidence needs a source link.
- "What I'm unsure about" is mandatory — intellectual honesty matters.
- If you can't find strong evidence for a claim, say so. Don't fabricate.
```

For **browse-only agents**, include the browse usage pattern:
```bash
python3 -c "
from browse import AgentBrowser
agent = AgentBrowser.connect()
content = agent.navigate('<url>')
print(content.for_llm())
agent.detach()
"
```

For browse agents searching Google:
```bash
python3 -c "
from browse import AgentBrowser
agent = AgentBrowser.connect()
content = agent.navigate('https://www.google.com/search?q=<query>')
print(content.for_llm())
agent.detach()
"
```

## Phase 3: Synthesis

After all 10 agents complete, read all angle files and produce two outputs.

### synthesis.md

```markdown
# <Topic>
## Multi-Angle Research Synthesis

**Date:** <date>
**Angles analyzed:** 10
**Method:** Parallel multi-agent research (7 WebSearch, 2 Browse, 1 mixed)

---

## Executive Summary
<2-3 paragraph overview — what's the state of this topic right now?>

## Consensus Points
- **<Point>** (Supported by Angles: X, Y, Z): <explanation>
- **<Point>** (Supported by Angles: X, Y, Z): <explanation>

## Key Disagreements & Uncertainties
- **<Disagreement>** (Angles X, Y vs. Angle Z): <what they disagree on and why>
- **Uncertainty: <topic>** (Angles X, Y): <what we don't know>

## What's Real
- **<Thing>**: <evidence it's real, not hype> (Supported by Angles: X, Y)

## What's Hype
- **<Thing>**: <why it's overstated> (Contradicted by Angles: X, Y)

## Critical Risks
- **<Risk>** (Supported by Angles: X, Y): <what could go wrong>

## Predictions (Near-Term)
- **<Prediction>** (confidence, Validated by Angles: X, Y): <justified prediction>

## What to Monitor Next
- <specific thing to watch> — why it matters, what would change the picture
```

**The key rule: every conclusion must cite which angles support it.**
- "Supported by Angles: 2, 3, 5"
- "Contradicted by Angle: 9"
- "Uncertain: needs more primary sources"

This makes the output defensible and reduces hallucination.

### sources.md

Consolidated bibliography across all 10 angles:

```markdown
# <Topic>
## Consolidated Source Bibliography

**Date:** <date>
**Total unique sources:** <count>
**Organized by:** Angle of origin (deduplicated; shared sources noted)

---

## Angle 01 — <Name>
1. [Title](url)
2. [Title](url) *(also cited in Angle 7)*

## Angle 02 — <Name>
...

---

## Cross-Angle Source Overlap
| Source | Angles |
|---|---|
| <source> | 1, 7 |

## Source Quality Notes
- <observations about source reliability, gaps, methodology differences>
```

### runlog.json

Record the run metadata:

```json
{
  "topic": "<topic>",
  "date": "<date>",
  "total_time_seconds": <N>,
  "total_time_human": "<Xm Ys>",
  "phases": {
    "research": {
      "duration": "<time>",
      "agents": 10,
      "breakdown": {
        "websearch_agents": 7,
        "browse_agents": 2,
        "mixed_agents": 1
      }
    },
    "synthesis": {
      "duration": "<time>",
      "agents": 1
    }
  },
  "angles": [
    {"id": 1, "name": "<name>", "type": "websearch", "file": "01_<slug>.md"},
    ...
  ],
  "outputs": {
    "synthesis": "synthesis.md",
    "sources": "sources.md",
    "total_sources": <N>
  }
}
```

## Output Structure

```
research_runs/
  <date>__<topic-slug>/
    angles/
      01_freshness.md
      02_technical.md
      03_market.md
      04_regulation.md
      05_security.md
      06_ethics.md
      07_players.md
      08_failures.md
      09_contrarian.md
      10_predictions.md
    synthesis.md
    sources.md
    runlog.json
    .start_time
```

## Rules

1. **Angle files must be short and punchy** — claims + evidence + sources. No 1,000-word essays. The structured template prevents bloat and keeps synthesis tractable.
2. **Every claim needs a confidence level** — high, medium, or low. Forces intellectual honesty.
3. **Every conclusion in synthesis must cite supporting angles** — "Supported by Angles: 2, 5, 8". This is non-negotiable. It makes the output defensible.
4. **"What I'm unsure about" is mandatory** — every angle must include gaps and unknowns. Research that claims certainty everywhere is lying.
5. **Browse agents run sequentially** — one browser connection at a time. WebSearch agents run in parallel.
6. **No fabrication** — if evidence is weak, say so. Rate confidence as low. Don't invent sources.
7. **Write progressively** — angle files are written as agents complete, not batched at the end. The user can watch research accumulate.
8. **Track tool provenance** — sources.md notes which tool found each source (WebSearch, WebFetch, or Browse).
