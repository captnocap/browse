# Angle 02 — Technical State of the Art

## Claims (with confidence)
- Claim (high): Agent architectures have converged on ReAct-style loops (reason-act-observe) with modular memory, tool use, and reflection — no longer single-model monoliths but orchestrated multi-component systems.
- Claim (high): SWE-bench Verified top scores hit ~81% (Claude Opus 4.5/4.6), up from ~65% a year ago. Agent scaffolding adds 10-20 points over raw model scores.
- Claim (high): Context windows plateau at 1-2M tokens, but effective use degrades well before that limit — models lose information mid-context and fail silently when overflowing.
- Claim (medium): Multimodal agents (vision + code execution + web browsing) are production-real: Operator, Manus AI, and Claude computer-use ship to consumers. DOM+vision hybrid parsing is the winning web-browsing pattern.
- Claim (high): Compounding errors remain the core unsolved blocker. A 95%-reliable step over 20 steps yields 36% end-to-end success. Field tests show 63% failure rates on 100-step tasks.
- Claim (medium): Multi-agent orchestration ("puppeteer" patterns) is surging — Gartner reported 1,445% growth in multi-agent inquiries from Q1 2024 to Q2 2025 — but adds new failure modes from agent-to-agent error propagation.

## Evidence
- SWE-bench Verified Feb 2026: Claude Opus 4.5 at 80.9%, GPT-5.2 at 80.0%, open-source DeepSeek V3.2 at 73.0% — [SWE-Bench Verified Leaderboard](https://www.marc0.dev/en/leaderboard)
- GAIA Level 3 (hardest): Writer Action Agent at 61%, Manus AI ~57.7% — [O-mega benchmarks guide](https://o-mega.ai/articles/top-10-ai-benchmarks-for-economically-valuable-work-2026)
- WebArena: IBM CUGA agent record at ~61.7% success — [O-mega computer-use guide](https://o-mega.ai/articles/the-2025-2026-guide-to-ai-computer-use-benchmarks-and-top-ai-agents)
- Compounding error math: 1% per-step error over 5,000 steps makes correctness essentially random — [DeepMind founder warning](https://www.computerweekly.com/news/366620886/Deepmind-founder-warns-of-compounding-AI-agent-errors)
- 63% failure rate on 100-step agent tasks in field tests — [Medium analysis](https://liorgd.medium.com/ai-agents-are-failing-63-of-the-time-heres-the-simple-fix-no-one-talks-about-bada84805cbe)
- Context windows at 1-2M tokens but quality degrades with length; agents fail silently at overflow — [Factory.ai context window problem](https://factory.ai/news/context-window-problem)
- Agentic Vision (Gemini 3 Flash) uses Think-Act-Observe loop with code execution to ground image understanding — [StartupHub.ai](https://www.startuphub.ai/ai-news/ai-research/2026/agentic-vision-gemini-3-flash-code-execution-solves-visual-hallucination)

## What I'm unsure about
- Exact real-world reliability numbers for consumer-facing agents (Operator, Manus, Claude computer-use) outside benchmarks — vendors don't publish failure rates.
- Whether multi-agent orchestration actually improves reliability vs. single-agent loops for consumer tasks, or just adds complexity.
- How much the "lost in the middle" context problem has actually improved in 2026-era models vs. 2024 findings.

## Sources
- [SWE-Bench Verified Leaderboard Feb 2026](https://www.marc0.dev/en/leaderboard)
- [O-mega: Top 10 AI Benchmarks for Real Work 2026](https://o-mega.ai/articles/top-10-ai-benchmarks-for-economically-valuable-work-2026)
- [O-mega: 2025-2026 AI Computer-Use Benchmarks Guide](https://o-mega.ai/articles/the-2025-2026-guide-to-ai-computer-use-benchmarks-and-top-ai-agents)
- [Factory.ai: The Context Window Problem](https://factory.ai/news/context-window-problem)
- [DeepMind founder warns of compounding AI agent errors](https://www.computerweekly.com/news/366620886/Deepmind-founder-warns-of-compounding-AI-agent-errors)
- [AI Agents Are Failing 63% of the Time](https://liorgd.medium.com/ai-agents-are-failing-63-of-the-time-heres-the-simple-fix-no-one-talks-about-bada84805cbe)
- [AI Trend 2026: The Agent Reliability Gap](https://fourweekmba.com/ai-trend-2026-the-agent-reliability-gap-keeps-humans-in-the-loop/)
- [Agentic Vision Gemini 3 Flash](https://www.startuphub.ai/ai-news/ai-research/2026/agentic-vision-gemini-3-flash-code-execution-solves-visual-hallucination)
- [HuggingFace: AI Trends 2026 — Reflective Agents](https://huggingface.co/blog/aufklarer/ai-trends-2026-test-time-reasoning-reflective-agen)
- [arxiv: AI Agent Systems Survey](https://arxiv.org/html/2601.01743v1)
