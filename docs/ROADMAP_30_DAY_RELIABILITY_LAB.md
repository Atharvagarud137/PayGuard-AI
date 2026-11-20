# PayGuard-AI: 30-Day Product Pivot Roadmap

**Plan begins:** 20 November 2026 (Day 1)  
**Planning window:** 20 November–19 December 2026  
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
| 1 | 20 Nov | Baseline gate | Verify latest docs commit CI; full repository, security, test and readiness review; record blockers | Latest CI verified; no critical blocker hidden; baseline documented |
| 2 | 21 Nov | Pivot documentation and scope | Establish product language, goals/non-goals, scope and roadmap in docs | README and PRD agree; scenario-lab direction explicit |
| 3 | 22 Nov | Scenario domain model | Typed scenario, step, assertion, run/result and status schemas | Schema validation tests; no arbitrary executable code |
| 4 | 23 Nov | Scenario storage design | Design persisted scenario definitions and execution evidence; ADR | Model and migrations reviewed; migration/runtime separation retained |
| 5 | 24 Nov | Scenario persistence | Persist scenario definitions and run records with migration/tests | CRUD persistence and validation tests pass |
| 6 | 25 Nov | Scenario runner skeleton | Runner orchestration, lifecycle/status, deterministic step ordering | Basic scenario executes and records outcomes |
| 7 | 26 Nov | Assertions | Assertion registry and deterministic assertion evaluation | Positive/negative assertion tests |
| 8 | 27 Nov | Timeline/evidence | Structured event timeline, execution identifiers, evidence records | Run evidence can be queried and ordered |
| 9 | 28 Nov | Report artifacts | JSON report and versioned report schema | Reports are stable, machine-readable and tested |
| 10 | 29 Nov | Replay | Replay metadata and deterministic replay of selected scenario | Re-run reproducibility test; no claims for unseeded nondeterminism |
| 11 | 30 Nov | Failure injection design | Stage-aware failure-injection model and ADR | Defined stages, safety boundaries, validation |
| 12 | 1 Dec | Response loss after commit | Implement post-commit response-loss scenario | DB commit exists; response is lost; scenario captures evidence |
| 13 | 2 Dec | Retry scenario | Same-key retry and response replay scenario | Single mutation and response replay assertions |
| 14 | 3 Dec | Conflicting retry | Same key with changed payload scenario | Deterministic conflict; no mutation |
| 15 | 4 Dec | Ambiguous outcome suite | Timeout-before/during/after-processing scenarios (only where deterministic stage semantics are supported) | Stage-specific assertions and tests |
| 16 | 5 Dec | Crash/recovery seam | Add controlled interruption/recovery test seam; avoid unsafe production kill hooks | Recovery behavior verified in isolated tests |
| 17 | 6 Dec | Webhook event model | Event schema, payload, delivery record and state model | Schema and lifecycle tests |
| 18 | 7 Dec | Atomic outbox | Persist payment event/outbox job atomically for supported simulated events | Transaction rollback/atomicity tests |
| 19 | 8 Dec | Webhook worker | Worker dispatch and configurable local receiver | Successful delivery and evidence |
| 20 | 9 Dec | Retry policy | Backoff, bounded attempts, terminal/dead-letter status | Retry timing/state tests |
| 21 | 10 Dec | Webhook fault scenarios | Duplicate, delayed and failed delivery controls | Deterministic webhook scenario tests |
| 22 | 11 Dec | Ordering/signature | Out-of-order delivery and synthetic signing/verification | Ordering and invalid-signature tests |
| 23 | 12 Dec | Concurrency harness | Barrier-controlled parallel execution and parameters | Harness reproducible without timing guesses |
| 24 | 13 Dec | Idempotency races | Concurrent duplicate/conflicting-key scenario tests | Invariant assertions, evidence timeline |
| 25 | 14 Dec | Lifecycle races | Capture/refund races and invariant validation | Amount/state invariants hold in tested cases |
| 26 | 15 Dec | Evidence/report improvements | Failure classification, run summary and reproduction metadata | Reports explain assertion failures using facts |
| 27 | 16 Dec | CLI | Minimal CLI to run/list/replay scenarios and export reports | CLI smoke tests; documented commands |
| 28 | 17 Dec | Sample merchant target | Minimal synthetic sample integration/receiver for end-to-end demonstration | A scenario tests observable behavior of sample integration |
| 29 | 18 Dec | Docker Compose and UX | One-command local stack, setup and troubleshooting | Fresh-start setup verified; no secrets baked in |
| 30 | 19 Dec | Release/readiness | Full verification, security review, docs, demo scenarios and public-readiness decision | CI evidence, known limitations, release/no-release decision |

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
| 1 | In progress (blocked on local PostgreSQL test service) | — | GitHub CI run [#75](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44719567377) passed all three jobs; local compileall, Alembic head/history, and dashboard production build passed; local pytest could not initialize without a database URL | Checkout and terminal are available. `pytest-results.txt` records 149 fixture setup errors caused by missing `TEST_DATABASE_URL`/`DATABASE_URL`; Docker daemon access is denied. No test assertions ran in that report. |
| 2–30 | Planned | — | — | Do not advance until the Day 1 local PostgreSQL test environment is available and baseline review is complete. CI is green. |
| LinkedIn posts | Day 1 draft pending baseline completion | — | Draft must remain strictly factual | 8 evidence-grounded milestone drafts; publication remains user-controlled |


## Day 1 baseline record (20 November 2026)

- **Verified head:** `c45efd619acb7e2be3cfa033e994a21602b46642` (`docs: update README with Day 1 CI status`), on local `main` and matching `origin/main` at inspection time.
- **Working tree:** the only pre-existing local change is untracked `pytest-results.txt`; it was preserved.
- **CI:** GitHub Actions run [#75](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44719567377) for the verified head completed successfully. Python Unit and API Tests, Dashboard End-to-End Tests, and Dependency Security Audit all reported success.
- **Local checks completed:** `.venv` Python `compileall -q app tests`, `alembic heads`, `alembic history`, and `npm run build` in `dashboard` all exited successfully.
- **Local pytest blocker:** no `TEST_DATABASE_URL` or `DATABASE_URL` is configured. The existing `pytest-results.txt` records 149 setup errors at the shared PostgreSQL fixture, before test assertions could execute. Docker is installed but access to the Docker Desktop daemon is denied in this environment. No local pytest pass is claimed.
- **Security/readiness evidence:** CI's dependency audit and its tests for runtime DB privileges/security completed successfully on this commit. The local CI workflow was reviewed and confirms PostgreSQL service/migrations are prerequisites for both test suites.
- **Next:** provide a reachable disposable PostgreSQL test database (or enable Docker daemon access), then run the local test suites and finish the baseline review before starting Day 2. This is an environment blocker; CI is green.
