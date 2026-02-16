# Angle 05 — Security / Abuse

## Claims (with confidence)
- Prompt injection is the #1 agent attack vector (high): OWASP's 2026 Agentic Top 10 ranks "Agent Goal Hijack" as ASI01. Agents cannot reliably separate instructions from data in emails, PDFs, or web content.
- Single-click data exfiltration from mainstream agents is real (high): The "Reprompt" attack on Microsoft Copilot allowed silent data theft via one click on a legitimate MS link, bypassing enterprise controls. Patched Jan 2026.
- AI-powered fraud is scaling exponentially (high): AI-enabled fraud surged 1,210% in 2025. Experian projects losses hitting $40B by 2027. AI phishing emails hit 54% click-through vs 12% for manual.
- 60% of orgs have no kill switch for misbehaving agents (medium): Most companies cannot stop their AI agents from sharing sensitive data with unknown actors, per 2026 compliance forecasts.
- Agent-to-agent attack surfaces are emerging (medium): Tool-chaining attacks where agents call tools with destructive parameters or chain tools in unexpected sequences (OWASP ASI02). Moltbook breach exposed 1.5M AI agent API keys, enabling mass agent impersonation.
- Deepfake + agent combos enable autonomous social engineering (medium): Agentic AI turns weeks of human social engineering into minutes of autonomous execution. Real-time deepfake calls already cost Arup $25.6M.

## Evidence
- OWASP released dedicated "Top 10 for Agentic Applications 2026" with 100+ expert contributors — [OWASP](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- Reprompt attack: single-click exfil from Copilot, persists after chat close — [Varonis](https://www.varonis.com/blog/reprompt)
- Moltbook breach: 1.5M agent API keys leaked via misconfigured Supabase, no RLS — [AIMojo](https://aimojo.io/moltbook-data-leak/)
- 91,000+ attack sessions targeting AI/LLM infrastructure observed in late 2025 — [eSecurity Planet](https://www.esecurityplanet.com/artificial-intelligence/ai-agent-attacks-in-q4-2025-signal-new-risks-for-2026/)
- AI fraud up 1,210% in 2025, $40B projected by 2027 — [Fortune/Experian](https://fortune.com/2026/01/13/ai-fraud-forecast-2026-experian-deepfakes-scams/)
- Microsoft published runtime defense framework for securing AI agents — [Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/01/23/runtime-risk-realtime-defense-securing-ai-agents/)
- Block/Goose proposed CORS-like model for agent guardrails — [Goose Blog](https://block.github.io/goose/blog/2026/01/05/agentic-guardrails-and-controls/)

## What I'm unsure about
- Whether any fully autonomous agent breach of a major enterprise has occurred yet (predicted for mid-2026, not confirmed)
- Exact scope of agent-to-agent attacks in the wild vs theoretical
- How effective current guardrails (sandboxing, human-in-loop) are at stopping indirect prompt injection at scale

## Sources
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- [Reprompt Attack — Varonis](https://www.varonis.com/blog/reprompt)
- [Moltbook Data Leak — AIMojo](https://aimojo.io/moltbook-data-leak/)
- [AI Agent Attacks Q4 2025 — eSecurity Planet](https://www.esecurityplanet.com/artificial-intelligence/ai-agent-attacks-in-q4-2025-signal-new-risks-for-2026/)
- [AI Fraud Forecast 2026 — Fortune/Experian](https://fortune.com/2026/01/13/ai-fraud-forecast-2026-experian-deepfakes-scams/)
- [Microsoft Runtime Defense for AI Agents](https://www.microsoft.com/en-us/security/blog/2026/01/23/runtime-risk-realtime-defense-securing-ai-agents/)
- [Goose CORS Model for Agent Guardrails](https://block.github.io/goose/blog/2026/01/05/agentic-guardrails-and-controls/)
- [Kaspersky on OWASP Agentic AI Risks](https://www.kaspersky.com/blog/top-agentic-ai-risks-2026/55184/)
- [McAfee — Agentic AI Weaponized for Social Engineering](https://www.mcafee.com/blogs/internet-security/how-agentic-ai-will-be-weaponized-for-social-engineering-attacks/)
- [Reprompt — The Hacker News](https://thehackernews.com/2026/01/researchers-reveal-reprompt-attack.html)
