# Building Production AI Systems: The AI-Native Engineering Guide

Coding agents can generate 90% of your application code in minutes. That makes it dangerously easy to ship a demo that looks finished, passes zero real checks, and collapses the moment it touches real users or an enterprise review board.

The difference between **vibe coding** and **AI-native engineering** is not how well you prompt. It is whether you own the decisions that are expensive to reverse, wire in observability and evals from day one, and prove reliability before you call anything architecture.

---

## 1. What You Design Up Front (And What You Defer)

"Emergent architecture" does **not** mean "no architecture up front." It means you design the **enterprise constraints** up front and defer **internal code decomposition** until the evidence is in.

Before writing code, lock down four layers:

1. **Business & Process Architecture:** What outcome are you optimizing for? (e.g., for a sales intelligence tool, the business outcome is *qualified meetings or closed sales*, not "summarised web pages").
2. **Delivery Surface (Application Layer):** Where does the user actually work? (Teams, Slack, browser, CLI, Mac app). *Adoption fails when you pick the wrong app layer*—if the user lives in Teams, don't force them into a separate web portal.
3. **Deployment & Security Envelope:** What is the simplest real environment the org runs? (e.g., a single Docker container on Azure Container Apps or AWS ECS with enterprise auth and secrets wired in).
4. **The One-Way Doors:** The architectural decisions that are expensive to reverse later.

**The rule:** *Coding agents write the code. You own the one-way doors, and you prove them with evals.*

| Decision | Who decides | Why it matters |
| --- | --- | --- |
| Module layout, glue code, boilerplate | Coding agent (you review) | Cheap to change or regenerate later |
| Business outcome & what "good" looks like | **You** | Everything else iterates against this target |
| Delivery surface & cloud/auth baseline | **You** | Determines user adoption and enterprise security |
| Fixed pipeline vs. agent autonomy | **You** | Sets testability, cost ceiling, and reliability |
| Where model output is trusted vs. checked | **You** | Sets the blast radius of a hallucination or error |
| Where state lives and how failures recover | **You** | Changing it later means migrating live data |
| Where a human signs off | **You** | Controls external risk, brand, and liability |
| Data boundaries and security | **You** | Governs compliance, PII, and customer trust |
| Integration contracts (stage inputs/outputs) | **You** | Other systems and teams build against them |

---

## 2. The AI-Native Build Loop

Start as a **single-container monolith**—not microservices. A monolith with an agent loop and tools (e.g., Playwright, MCP, search, DB) lets you put a working prototype in front of a real user fast. A prototype is only real when an end user can touch it and give feedback.

```text
  ┌──────────────────────────────────────────────────────────────────┐
  │                       LOOP 1: DISCOVERY                          │
  │                                                                  │
  │  [0. Business & Surface] ──► [1. Define "Good" + Telemetry]      │
  │   (Outcome, app layer,        (Golden set + observability        │
  │    container + auth)           wired from day 1)                 │
  │                                        │                         │
  │                                        ▼                         │
  │  [2. Spike in a Monolith] ──► [3. Eval Gate]                     │
  │   (Docker container +          (Consistent, grounded,            │
  │    agent loop + tools)          passes preset threshold?)        │
  │          ▲                             │                         │
  └──────────┴─── tune / ablate ───────────┘                         │ YES
                                                                     ▼
  ┌──────────────────────────────────────────────────────────────────┐
  │                 LOOP 2: HARDENING & ARCHITECTURE                 │
  │                                                                  │
  │  [4. Thin Vertical Slice] ──► [5. Harden (8 Criteria + TDD)]     │
  │   (Freeze reliable flow;       (Unit/functional/non-func tests,  │
  │    one real path end-to-end)    durable state, human gate)       │
  │                                        │                         │
  │                                        ▼                         │
  │  [7. Scale & Feedback Loop] ◄── [6. Codify MVA + ADRs]           │
  │   (Feed real user outcomes       (Write down what the            │
  │    back into golden set;          evidence proved)               │
  │    add scale fitness funcs)                                      │
  └──────────────────────────────────────────────────────────────────┘
```

**How agent loops evolve into pipelines:**  
Using an open agent loop with tools is great for **Loop 1 (Discovery)** because it lets you test what signals and tools actually work. Once you see what works, **freeze the reliable path into fixed stages** if a deterministic pipeline gives you better consistency and testability.

---

## 3. The Three-Tier Testing & Eval Stack

AI engineering does not replace Test-Driven Development (TDD); it adds an eval layer on top of it.

### Tier 1: Traditional TDD (Deterministic Rails)
Run standard **unit tests, functional tests, and non-functional tests** (latency, memory, concurrency limits) on every deterministic block—parsers, API wrappers, database checkpoints, auth middleware, and stage contracts. Each block must work on its own.

### Tier 2: Proxy / Judgment Evals (Fast Daily Loop)
The real edge of an AI application is **judgment** (e.g., *which extracted signal is actually worth acting on?*), **consistency** (not giving one answer today and another tomorrow), and **groundedness** (every claim backed by a source).

To test this fast:
1. **Build a 10–20 case golden set** (hand-written or annotated real/synthetic examples, including 3–5 ugly edge cases).
2. **Wire telemetry and observability into the harness from day one.** Your observability trace *is* your eval input—log every prompt, retrieved context, model output, latency, and cost.
3. **Run deterministic checks before LLM judges.** Verify schemas, required fields, and citations in code first. Use an LLM-as-judge for semantic quality, ideally on a **different model provider** than the generator so blind spots don't correlate.
4. **Track four distinct outcomes, not two:**
   - **Clean:** Succeeded technically and passed all deterministic and quality thresholds.
   - **Degraded:** Finished with partial information, non-fatal fallback, or low confidence warning.
   - **Hollow:** Silent failure detected (process returned exit code `0` / HTTP `200`, but produced an empty, placeholder, or ungrounded payload). Telemetry alerts immediately. *Liveness is not correctness.*
   - **Failed:** Errored loudly and stopped safely (schema rejection, unhandled exception, or hard crash).

### Tier 3: Business Outcome Evals (Slow Feedback Loop)
Ultimately, you are optimizing for the **business eval** (did the sales team book a meeting or close a deal?). Because B2B outcomes can take months—and some loops never cleanly close—you cannot gate daily deploys on them. Instead:
- Capture lightweight **user feedback signals** in the delivery surface (accept/reject, thumbs up/down, "booked meeting").
- Feed those real-world outcomes back into your **Tier 2 golden set** so your fast evals stay calibrated to reality.
- **Reliability drives adoption:** once users see consistent, grounded judgment, they trust the tool enough to use it—and real usage tells you how to build the rest of the application properly.

---

## 4. What "Hardened" Means: The 8-Point Ship Checklist

A thin vertical slice is not production-ready just because it runs in a container. It is hardened only when it passes all eight criteria:

| # | Criterion | What "Fake Done" looks like | What "Real Done" looks like |
| --- | --- | --- | --- |
| 1 | **Evals & TDD pass** | "I tested 3 prompts and they looked good." | Unit/functional tests pass on deterministic code; golden set clears the preset threshold. |
| 2 | **Failure modes named & handled** | A generic `try/catch` that logs and returns `""`. | Timeouts, malformed JSON, empty retrieval, and rate limits each have a defined policy: retry, skip, fail closed, or alert. |
| 3 | **Stages can rerun safely** | Rerunning a crashed job sends duplicate messages or writes duplicate rows. | State is durable; stages are idempotent so a crashed run resumes cleanly. |
| 4 | **Observable** | `print()` statements in local terminal. | Every run is traced; outcomes are counted (`clean`, `degraded`, `hollow`, `failed`); silent failures trigger alerts. |
| 5 | **Cost & latency measured** | Guessing from pricing pages. | Actual per-run cost and p95 latency logged from real runs. |
| 6 | **Human sign-off** | Agent emails customers or mutates prod directly. | Explicit approval gate wherever output reaches the outside world. |
| 7 | **Data & security explicit** | API keys in `.env` committed to git; raw PII in prompts. | Clear boundary on what enters prompts, what is stored where, and no secrets in code. |
| 8 | **Decisions written down** | Only you know why it's built this way. | Half-page Architecture Decision Records (ADRs) so another engineer could run and modify it. |

If a criterion isn't met yet, mark it **"Next"**, not **"Done"**.

---

## 5. Building Inside an Organization (Governance Without Waterfall)

When building inside an enterprise, you will face security reviews, compliance, and Architecture Review Boards (ARBs). Do not treat governance as red tape to route around, and do not fall back into 6-month waterfall design docs.

- **Prototype in a sandbox, never on live data.** Use synthetic, masked, or scrubbed data during Loop 1.
- **Pick a boring, compliant deployment baseline early.** A single Docker container on the org's approved cloud (e.g., Azure Container Apps, AWS ECS) with standard auth wired in lets real users test the prototype safely.
- **Show up to the Architecture Review with evidence, not just a diagram.** Bring your **Minimum Viable Architecture (MVA)**—the thin slice, the ADRs for its one-way doors, and the sandbox eval numbers.
- **Name your next fitness functions.** A narrow slice hides scale problems—concurrency, multi-tenancy, and cost at volume. Don't pretend the MVA solves them. Name them as the next automated checks (fitness functions) you will add before scaling traffic.

---

## 6. Worked Example: Sentinel (An Automated Outreach Pipeline)

**Sentinel** is an automated B2B research and outreach system built to give sales teams high-signal prospect briefs and drafts. Instead of describing it as a list of frameworks, here is its architecture told as **decision records backed by evidence**:

| Decision | Alternative considered | Why this one | Evidence | Trade-off accepted |
| --- | --- | --- | --- | --- |
| Fixed 6-stage pipeline (`collect → extract → judge → route → write → send`) | Flexible v1 state machine / agent loop for every run | Fixed stages gave higher consistency and each stage can be tested on its own | v1 retired after running both against the same evals | Less flexibility for ad-hoc run types |
| Judge on a different model provider from the extractor | Same model checks its own work | Models from one provider share blind spots; errors correlate | Open gap: cross-provider comparison number not yet benchmarked | Extra cost and latency per run |
| Fail closed: drop anything not confirmed | Keep unverified claims with a warning flag | A false claim sent to a prospect costs more than a missing one | Judge classifies claims as `confirmed`, `unverified`, or `false` | Lower recall |
| Durable state in PostgreSQL | In-memory or local JSON files | A crashed overnight run resumes at the failed stage instead of restarting | Runs unattended under a watchdog | More infrastructure to operate |
| Human approval before anything is sent | Automatic send | Output reaches real external people | Approval gate enforced in every run | Throughput capped by human review time |
| Retrieval tuned in a lab first | Tune on the live pipeline | Cheap, fast, safe iteration | `recall@5` improved from `0.49` to `0.97` for `~$12` (not yet promoted to live path) | Lab and live data can diverge |
| Health measured by outcome, not uptime | Count completed runs | A run can finish technically and still be hollow/wrong | 46 runs in 30 days: `30 clean`, `15 degraded`, `1 hollow` | More telemetry required per run |

Notice the honesty at the edges: the golden sets are still small (~10 verified outputs per sector), the retrieval improvement isn't on the live path yet, and not all hardening gates are 100% automated. Owning those edges upfront is what separates an engineer from a salesperson.

---

## 7. Engineering Vocabulary Map

Use standard engineering terms when explaining your work to staff engineers, hiring managers, or review boards:

| Plain-English Habit | Engineering Term | What It Means |
| --- | --- | --- |
| Define good first | **Eval-driven development** | TDD for non-deterministic systems: the eval suite exists before the code. |
| Test deterministic blocks | **TDD (Unit / Functional / Non-Functional)** | Automated tests proving each code block, flow, and latency/load bound works. |
| Spike against evals | **Spike / Proof of Concept** | A fast, throwaway build (e.g., monolith container) to test an approach and get user feedback. |
| Try several approaches | **Ablation / A/B evaluation** | Running variants against the same evals so evidence picks the winner. |
| Narrow slice | **Vertical slice / Walking skeleton** | One minimal, real path end-to-end through every layer. |
| Harden | **Productionise** | Error handling, retries, idempotency, observability, and security review. |
| Architecture emerges | **Evolutionary architecture** | Structure grows from measured evidence instead of upfront guessing. |
| Baseline architecture | **Minimum Viable Architecture (MVA)** | The smallest set of decisions that makes the slice run safely. |
| Evals that guard the design | **Fitness functions** | Automated checks that fail when a change breaks an architectural property. |
| Write down why | **Architecture Decision Record (ADR)** | Half a page: decision, options considered, reason, and accepted trade-off. |
| Decisions hard to undo | **One-way doors** | Architecturally significant decisions worth slowing down for. |
| Crash and resume | **Durable state / Idempotent stages** | A stage can rerun after a crash without duplicating side effects. |
| Gate between stages | **Quality gate** | Output is verified before the next stage is allowed to consume it. |
| Drop if unconfirmed | **Fail closed** | When unsure, do nothing rather than doing something wrong. |
| Finished but wrong | **Silent failure (liveness vs. correctness)** | A process exited `0` / `200`, but the output was hollow or broken. |
| Watchdog | **Health check / Supervisor** | An external monitor that detects stalled or degraded runs. |

---

## 8. How to Defend Your Build (The 3-Minute Walkthrough)

When presenting to an Architecture Review Board, tech lead, or interviewer, walk through your system in this exact order—and **stop after step 7** so they can drill into the area they care about:

1. **Problem & Business Eval (20s):** What the business needed, and what real-world outcome you are optimizing for.
2. **Surface & Baseline (20s):** Where the user interacts with it, and the minimal deployment/auth container.
3. **Definition of good (20s):** Your golden set, deterministic checks, judge, and telemetry.
4. **What you tried (30s):** The variants you spiked and what the evals showed.
5. **What won and why (30s):** Your MVA expressed as 3–4 one-way door decisions.
6. **Hardening & Numbers (30s):** Failure handling, durable state, human sign-off, and real run counts (`clean` vs. `degraded` vs. `hollow`, latency, cost).
7. **Honest edge and next step (20s):** What isn't finished yet, and what fitness functions you'd add for scale.

---

## 9. Capstone Exercise: Build and Defend Your Own Slice

Apply this to a real problem. Do not skip steps:

- [ ] **Step 1:** Write down your Business Outcome, Delivery Surface, and Deployment Baseline (1 paragraph).
- [ ] **Step 2:** Create a 15-case golden set (including 3–5 edge cases), wire basic telemetry, and write a grading script *before* building the app.
- [ ] **Step 3:** Ship a single-container monolith spike (e.g., an agent loop with tools) in a sandbox, test 2–3 approaches against the golden set, and get feedback from at least one real user.
- [ ] **Step 4:** Freeze the winning flow into **one thin vertical slice** that passes all 8 hardening criteria (including unit/functional tests on deterministic blocks).
- [ ] **Step 5:** Write **3 half-page ADRs** for the hardest one-way doors you hit, and deliver a **3-minute walkthrough** where a peer or mentor tries to break one decision for 5 minutes straight.
