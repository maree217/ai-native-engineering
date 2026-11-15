# Production AI Ship Checklist (8 Hardening Criteria)

Every thin vertical slice must satisfy all 8 criteria before shipping to production. If an item is incomplete, mark it **"Next"**, not **"Done"**.

---

### [ ] 1. Tier 1 Deterministic TDD Passing
- [ ] Unit tests pass for parsers, extractors, normalizers, and schema validators.
- [ ] Integration tests verify stage input/output contracts.
- [ ] Deterministic citation verification runs in pure code before any LLM evaluation.

### [ ] 2. Golden Set & Tier 2 Proxy Evals Calibrated
- [ ] Golden set contains $\ge 10$ realistic cases (including $\ge 3$ adversarial or edge cases).
- [ ] Eval harness executes automatically in CI/CD against the golden set.
- [ ] Pass threshold explicitly met (e.g., groundedness $\ge 90\%$, extraction accuracy $\ge 95\%$).
- [ ] Cross-provider or calibrated judge check implemented (judge model differs from generation model, or calibrated against human annotations).

### [ ] 3. Day-1 Observability & Telemetry Wired
- [ ] Every execution emits a structured trace (trace ID, stage latencies, token consumption, cost).
- [ ] Explicit 4-state outcome classification:
  - **CLEAN**: Passed all deterministic checks and quality thresholds.
  - **DEGRADED**: Finished with partial information, non-fatal fallback, or low confidence alert.
  - **HOLLOW**: Silent failure detected (HTTP 200 / exit 0, but empty, corrupted, or ungrounded payload).
  - **FAILED**: Errored cleanly with handled exception and stopped safely.
- [ ] Automated alerting on `HOLLOW` and elevated `DEGRADED` rates.

### [ ] 4. Failure Modes & Fail-Closed Policies
- [ ] Upstream API timeouts, rate limits, and schema violations explicitly handled.
- [ ] Fail-closed policy: unverified claims or missing citations are dropped or flagged rather than guessed.
- [ ] Explicit error budgets and fallback paths configured.

### [ ] 5. Durable State & Idempotency
- [ ] Crash-and-resume capability: re-running a interrupted execution resumes safely without side effects.
- [ ] Stage outputs cached or persisted with unique idempotency keys.
- [ ] No duplicate side effects (e.g., duplicated notifications or emails) upon rerun.

### [ ] 6. Cost & Latency Budgets Enforced
- [ ] Measured p95 end-to-end latency meets application layer SLA.
- [ ] Dollar cost per run measured and bounded by a strict token budget.
- [ ] Step budget enforced on any open agent loops to prevent infinite recursions.

### [ ] 7. Human-in-the-Loop & External Guardrails
- [ ] Explicit human review or sign-off gate before external side effects (mutations, emails, dispatches).
- [ ] Secrets and credentials managed via cloud secret store (no `.env` or raw keys in repo).
- [ ] PII and sensitive internal data scrubbed before prompt assembly.

### [ ] 8. Architecture Documented (MVA & ADRs)
- [ ] Half-page Architecture Decision Record (ADR) logged for all one-way doors.
- [ ] Next fitness functions named for subsequent scale/concurrency milestones.
