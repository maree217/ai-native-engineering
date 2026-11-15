---
name: Case Study Submission
about: Submit an anonymized production case study following the Loop 1 -> Loop 2 progression.
title: "[Case Study]: "
labels: case-study
assignees: ''
---

### System Overview
- **Domain / Sector**: (e.g., B2B Sales Intelligence, Legal Document Review, Customer Support Triage)
- **Delivery Surface**: (e.g., Slack App, Web UI, Async Background Worker, CLI)
- **Deployment Baseline**: (e.g., AWS ECS single-container, Azure Container Apps)

### Business Eval (Tier 3 Outcome)
*What real-world business metric was this system built to move?*

### Loop 1: Discovery Spike
- **Spike Architecture**: (Monolith container, agent loop, tools used)
- **Key Discoveries**: (What failed, what signals proved valuable)
- **Golden Set Size & Edge Cases**: 

### Loop 2: Hardened Vertical Slice
- **Fixed Stages**: (e.g., `ingest -> normalize -> retrieve -> judge -> verify -> emit`)
- **Deterministic Guardrails**: (Schema validations, regex checks, citation enforcement)
- **Judge Configuration**: (Different provider, calibrated prompt, or code assertions)

### Telemetry & Hardened Metrics
- **Run Count & Period**: (e.g., 50 runs over 30 days)
- **Outcome Distribution**:
  - Clean: `X`
  - Degraded: `Y`
  - Hollow (Caught silent failures): `Z`
  - Failed (Handled errors): `W`
- **Cost & Latency Benchmarks**: (p95 latency and average cost per run)

### Key Architectural Decision Record (ADR)
*Summarize the single most critical one-way door decision and the trade-off accepted:*
- **Decision**:
- **Why chosen over alternatives**:
- **Trade-off accepted**:
