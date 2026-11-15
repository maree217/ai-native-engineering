# ADR-[NUMBER]: [Title: Architectural Decision for AI-Native System]

- **Status**: [Proposed | Accepted | Superseded | Deprecated]
- **Date**: YYYY-MM-DD
- **Author**: [Name / Team]
- **Reviewers**: [Reviewers / ARB Members]

---

## 1. Context & Business Eval
*What real-world business outcome is this system optimizing for, and what triggers this architectural decision?*
- **Target Business Outcome**: (e.g., qualified sales meetings, verified claims, resolution latency)
- **Problem Statement**: 

---

## 2. Delivery Surface & Application Layer Constraints
*Where does the user interact with the output, and what constraints does that impose on state, latency, and auth?*
- **App Layer**: (e.g., Slack/Teams bot, background worker, Web UI, CLI)
- **Deployment Envelope**: (e.g., single container on ECS/ACA, serverless function)
- **Security & Data Boundaries**: (e.g., PII sanitization, no external API persistence)

---

## 3. Loop 1 vs. Loop 2 Architectural Choice
*Is this stage an open agent loop (discovery/spiking) or a fixed, deterministic pipeline slice?*
- **Selected Pattern**: [Loop 1 Open Agent Loop | Loop 2 Fixed-Stage Pipeline]
- **Rationale**: 
- **Stage Topology**: (e.g., `ingest -> normalize -> retrieve -> judge -> verify -> emit`)

---

## 4. One-Way Doors & Reversibility (Kill-Switch)
*Why is this decision expensive to reverse, and what is the blast radius?*
- **Reversibility Rating**: [One-Way Door (High Cost) | Two-Way Door (Low Cost)]
- **Failure Mode & Blast Radius**: (e.g., hallucinated output sent to external client vs. dropped signal)
- **Fallback / Kill-Switch**: (e.g., fail-closed policy, human approval fallback, model downgrade flag)

---

## 5. Tier 1 & Tier 2 Eval Gate
*What evidence proves this decision works before merging or deploying?*
- **Tier 1 (Deterministic TDD)**: (schema assertions, citation presence, latency bound)
- **Tier 2 (Proxy Judgment & Golden Set)**: (minimum golden set pass rate, judge calibration)
- **Run Classification Target**: (zero unhandled `HOLLOW` or silent failures; acceptable `DEGRADED` threshold)

---

## 6. Options Considered & Trade-offs
| Option | Pros | Cons | Why Rejected/Selected |
| --- | --- | --- | --- |
| Option A (Selected) | | | Selected based on eval evidence |
| Option B | | | Rejected due to eval/cost failure |

---

## 7. Consequences & Next Fitness Functions
- **Positive Consequences**: 
- **Negative Consequences / Technical Debt**: 
- **Next Scale Fitness Functions**: (concurrency, token budget ceiling, multi-tenant isolation)
