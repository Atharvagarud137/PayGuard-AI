# PayGuard-AI: 30-Day Product Pivot Roadmap

**Plan begins:** 21 November 2026 (Day 1)  
**Planning window:** 21 November–20 December 2026  
**Delivery model:** One meaningful, verified direct commit to `main` per working day.  
**Working assumption:** roughly 2–3 hours on weekdays, longer sessions on weekends where practical.

## Product direction

PayGuard-AI pivots from a simulated payment gateway with planned AI features into a **Payment Integration Reliability Lab**. Its purpose is to help engineers test their payment integrations against reproducible, controlled failure conditions and evaluate behavior with deterministic assertions and evidence.

> It is a synthetic test tool. It is not a processor, does not connect to real payment networks, and must never receive real PAN, CVV/CVC, credentials, or production transaction data.

## Product promise

Run reproducible payment failure scenarios—including ambiguous outcomes, retry/idempotency behavior, webhook failures, and concurrency races—then produce structured evidence and reports.

## Rules of execution

- Direct commits to `main`; no pull requests.
- Inspect the latest main commit and CI status before each day's task.
- A CI failure blocks the next day's task. Fix it, verify it, and then resume.
- Use expected-head checks when updating `main`; do not overwrite a changed head.
- Do not rewrite history or delete historical commits.
- Never claim tests pass without actual results.
- Update README after every significant milestone; update the relevant docs and this roadmap status.
- Only synthetic data. Do not claim PCI DSS compliance, real processing, or universal exactly-once guarantees.
- Scope each daily task to a shippable, reviewable increment. If a task overruns, split it rather than rushing.

## Day-by-day plan

| Day | Date | Focus | Daily commit/deliverable | Acceptance / evidence |
|---|---|---|---|---|
| 1 | 21 Nov | Baseline gate | Verify latest docs commit CI; full repository, security, test and readiness review; record blockers | Latest CI verified; no critical blocker hidden; baseline documented |
| 2 | 22 Nov | Pivot documentation and scope | Establish product language, goals/non-goals, scope and roadmap in docs | README and PRD agree; scenario-lab direction explicit |
| 3 | 23 Nov | Scenario domain model | Typed scenario, step, assertion, run/result and status schemas | Schema validation tests; no arbitrary executable code |
| 4 | 24 Nov | Scenario storage design | Design persisted scenario definitions and execution evidence; ADR | Model and migrations reviewed; migration/runtime separation retained |
| 5 | 25 Nov | Scenario persistence | Persist scenario definitions and run records with migration/tests | CRUD persistence and validation tests pass |
| 6 | 26 Nov | Scenario runner skeleton | Runner orchestration, lifecycle/status, deterministic step ordering | Basic scenario executes and records outcomes |
| 7 | 27 Nov | Assertions | Assertion registry and deterministic assertion evaluation | Positive/negative assertion tests |
| 8 | 28 Nov | Timeline/evidence | Structured event timeline, execution identifiers, evidence records | Run evidence can be queried and ordered |
| 9 | 29 Nov | Report artifacts | JSON report and versioned report schema | Reports are stable, machine-readable and tested |
| 10 | 30 Nov | Replay | Replay metadata and deterministic replay of selected scenario | Re-run reproducibility test; no claims for unseeded nondeterminism |
| 11 | 1 Dec | Failure injection design | Stage-aware failure-injection model and ADR | Defined stages, safety boundaries, validation |
| 12 | 2 Dec | Response loss after commit | Implement post-commit response-loss scenario | DB commit exists; response is lost; scenario captures evidence |
| 13 | 3 Dec | Retry scenario | Same-key retry and response replay scenario | Single mutation and response replay assertions |
| 14 | 4 Dec | Conflicting retry | Same key with changed payload scenario | Deterministic conflict; no mutation |
| 15 | 5 Dec | Ambiguous outcome suite | Timeout-before/during/after-processing scenarios (only where deterministic stage semantics are supported) | Stage-specific assertions and tests |
| 16 | 6 Dec | Crash/recovery seam | Add controlled interruption/recovery test seam; avoid unsafe production kill hooks | Recovery behavior verified in isolated tests |
| 17 | 7 Dec | Webhook event model | Event schema, payload, delivery record and state model | Schema and lifecycle tests |
| 18 | 8 Dec | Atomic outbox | Persist payment event/outbox job atomically for supported simulated events | Transaction rollback/atomicity tests |
| 19 | 9 Dec | Webhook worker | Worker dispatch and configurable local receiver | Successful delivery and evidence |
| 20 | 10 Dec | Retry policy | Backoff, bounded attempts, terminal/dead-letter status | Retry timing/state tests |
| 21 | 11 Dec | Webhook fault scenarios | Duplicate, delayed and failed delivery controls | Deterministic webhook scenario tests |
| 22 | 12 Dec | Ordering/signature | Out-of-order delivery and synthetic signing/verification | Ordering and invalid-signature tests |
| 23 | 13 Dec | Concurrency harness | Barrier-controlled parallel execution and parameters | Harness reproducible without timing guesses |
| 24 | 14 Dec | Idempotency races | Concurrent duplicate/conflicting-key scenario tests | Invariant assertions, evidence timeline |
| 25 | 15 Dec | Lifecycle races | Capture/refund races and invariant validation | Amount/state invariants hold in tested cases |
| 26 | 16 Dec | Evidence/report improvements | Failure classification, run summary and reproduction metadata | Reports explain assertion failures using facts |
| 27 | 17 Dec | CLI | Minimal CLI to run/list/replay scenarios and export reports | CLI smoke tests; documented commands |
| 28 | 18 Dec | Sample merchant target | Minimal synthetic sample integration/receiver for end-to-end demonstration | A scenario tests observable behavior of sample integration |
| 29 | 19 Dec | Docker Compose and UX | One-command local stack, setup and troubleshooting | Fresh-start setup verified; no secrets baked in |
| 30 | 20 Dec | Release/readiness | Full verification, security review, docs, demo scenarios and public-readiness decision | CI evidence, known limitations, release/no-release decision |

## LinkedIn project documentation (integrated into delivery)

Build a truthful public engineering narrative alongside implementation. This is a documentation/content deliverable, not a substitute for engineering work.

- Prepare **8 milestone post drafts**, tentatively aligned to Days 1, 7, 10, 16, 22, 26, 29 and 30 (adjust dates if milestones move).
- Draft each post only after verifying the actual work, commit, tests and CI evidence. Clearly distinguish implemented functionality from planned work; do not inflate results, expose secrets, include sensitive details, or claim PCI/compliance/real processing.
- Use a consistent story arc: project pivot and problem statement; scenario engine; first reproducible ambiguous-outcome slice; fault-injection/recovery learning; webhook reliability; concurrency and invariants; runnable demo; final retrospective and evidence.
- Include concise post copy, a useful technical takeaway, relevant sanitized screenshots/diagram suggestions where available, and restrained hashtags. Avoid generic motivational filler and engagement bait.
- **Draft and deliver posts for the user's review; do not publish to LinkedIn or schedule them externally without explicit authorization.**
- Maintain the draft/post status in the roadmap (drafted, reviewed, published by user) without inventing publication status.

## Phase gates

### Gate A: Scenario engine (Days 2–10)
No failure injection or webhook work until scenario definitions, execution, assertions, evidence and replay are sufficiently stable.

### Gate B: Ambiguous outcomes (Days 11–16)
Prove the commit/response-loss/retry behavior with deterministic evidence. Avoid vague "timeout simulation" that does not identify the injection stage.

### Gate C: Webhook reliability (Days 17–22)
Use durable event/outbox records and a worker. Delivery attempts must be observable and replayable.

### Gate D: Concurrency lab (Days 23–26)
Use controlled synchronization and invariant-based checks. Do not infer reliability from request volume alone.

### Gate E: Usability and release (Days 27–30)
CLI, sample target, Docker, documentation and final readiness assessment.

## AI scope

AI is intentionally outside this 30-day implementation plan except for preserving a future extension point in structured evidence. Do not add embeddings, ChromaDB, LangChain, LangGraph, an agent, or generated executable tests during this roadmap.

A later AI phase may:
1. Summarize evidence.
2. Classify failure categories.
3. Suggest hypotheses explicitly marked unverified.
4. Suggest structured scenarios, validated before execution.
5. Measure hallucination/unsupported-claim rate against a curated evaluation set.

The deterministic runner and test results remain authoritative.

## Daily status template

- **Status:** Not started / In progress / Complete / Blocked
- **Commit:** SHA and link
- **CI:** Actual status, run link, and test results; never inferred
- **Changes:** What was shipped
- **Evidence:** Tests and observed results
- **Limitations:** Remaining caveats
- **README:** Milestone summary updated when significant

## Status tracking

| Day | Status | Commit | CI/evidence | Notes |
|---|---|---|---|---|
| 1 | Scheduled | — | Pending | Baseline/readiness gate |
| 2–30 | Planned | — | — | Daily increments; blocked by failing CI |\n| LinkedIn posts | Planned | — | — | 8 evidence-grounded milestone drafts; publication remains user-controlled |
