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
| 8 | 27 Nov | Timeline/evidence | Structured event timeline, execution identifiers, persisted step/assertion evidence and query APIs | CI verification pending; run evidence can be queried and ordered |
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

## LinkedIn milestone tracking (deferred until plan completion)

Track verified engineering facts at milestone days 1, 7, 10, 16, 22, 26, 29 and 30 for the final build-in-public series. The user has decided to prepare and post the LinkedIn series only after the full 30-day plan is complete. During the roadmap, record engineering evidence only: do not prepare, expand, publish or schedule post drafts. The existing Day 1 draft remains historical, unpublished content. After Day 30, prepare the series from verified commits, tests, CI results, lessons and sanitized visual suggestions for the user's review. Never publish or schedule without explicit authorization.

## Deployment milestone (Days 29–30)\n\nDeploy the dashboard UI to Vercel at Day 29 as staging, provided the backend API is separately hosted or otherwise reachable through a verified deployment environment. Vercel is not assumed to host the Python backend. Document environment variables, CORS, URL configuration, deployment URLs and any external backend host. Do not expose secrets in the frontend bundle; synthetic data only. Day 30 validates the final deployment and makes a release/no-release decision. If backend hosting or configuration is unavailable, deployment remains blocked rather than being presented as live.\n\n## Phase gates

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
| 1 | Complete | [`bd4aa96`](https://github.com/Atharvagarud137/PayGuard-AI/commit/bd4aa96bb67f955f4fc5735a9c162c7487e14c4e) | CI run [#76](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44740263945) for `fb18505` and run [#77](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44741250041) for `bd4aa96` passed all three jobs; 143 local unit/API tests, compileall, Alembic head/history and dashboard build are recorded as passing | Local E2E not run because port 8000 was occupied; CI E2E passed. Local dependency audits not run; CI audit passed. |
| 2 | Complete (documentation-only) | [`6591b995`](https://github.com/Atharvagarud137/PayGuard-AI/commit/6591b9953c559d8426be05d72a339eaf0ece6e78); evidence commit [`3c999c2`](https://github.com/Atharvagarud137/PayGuard-AI/commit/3c999c2ac7a2cbf28bb55b9df658a243ff1e7fc7) | Runs [#78](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44861407842) and [#79](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44861550394) passed all three jobs | Scope reconciliation, README status and Day 1 LinkedIn draft; no scenario-engine code or tests added. |
| 3 | Complete | [`dd30878`](https://github.com/Atharvagarud137/PayGuard-AI/commit/dd30878bb99ed4f773020e63967ecd6a3592e6be) | CI run [#80](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44981213809) passed all three jobs: 163 Python/API tests (1 warning), 6 E2E tests (2 warnings), dependency audits passed | Typed scenario/step/assertion/run/result models and 20 schema tests; CI verified. Runner/persistence not implemented. |
| 4 | Complete (design-only) | [`b3bc41ca`](https://github.com/Atharvagarud137/PayGuard-AI/commit/b3bc41caf47b48277bebf894db937e2ea8325590) | CI run [#83](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45107175082) passed all three jobs | Storage ADR accepted; documentation-only. No local tests or migration execution. Run #82 was cancelled when the evidence correction commit superseded it; #83 verified the current commit. Day 5 persistence remains next. |
| 5 | Complete | [b4fd439](https://github.com/Atharvagarud137/PayGuard-AI/commit/b4fd4396750a5664bf126096873d4ec571796317) | CI run [#89](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45321910212) passed all three jobs | Corrected tagged serialization for frozen run snapshots. Python/API, E2E and dependency audits passed. Local execution unavailable. |
| 6 | Complete | [`ab432a3`](https://github.com/Atharvagarud137/PayGuard-AI/commit/ab432a312dcc06e50fd87a53634b98f5c99ce89d) | CI run [#91](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45359793956) passed all three jobs: 180 Python/unit/API tests (1 warning), 6 E2E tests (2 warnings), dependency audits passed | Deterministic injected-handler runner, ordered steps, scalar outputs, sanitized errors, dependency skips and independent-step continuation; in-memory results only. Day 7 added assertions/finalization; step-result persistence remains Day 8 scope. Run #90 was cancelled and superseded by #91. |\n| 7 | Complete | Code [`b54258c`](https://github.com/Atharvagarud137/PayGuard-AI/commit/b54258c24a02cb4e829921ef2308a9fd4512106d); evidence [`d4f5b9`](https://github.com/Atharvagarud137/PayGuard-AI/commit/d4f5b91145714502b42f99753f967ac5c89f8283) | Code CI [#93](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45749516234) and evidence CI [#94](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45749754060) passed all three jobs. Evidence/status commit [#95](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45749928521) also passed all three jobs | Deterministic assertion registry and run finalization; see Day 7 record below. |\n| 8 | In progress (CI pending) | — | — | Structured runner events; persisted step/assertion evidence; ordered timeline API. Local tests unavailable. |
| 29 | Planned | — | — | Docker Compose fresh-start UX and Vercel dashboard staging deployment; backend hosting/configuration must be separately provisioned and verified. |\n| 30 | Planned | — | — | Final readiness review, deployment verification, API/dashboard connectivity, security/configuration checks and release/no-release decision. |
| LinkedIn series | Deferred until Day 30 completion | — | Engineering evidence only during roadmap | Milestones tracked on Days 1, 7, 10, 16, 22, 26, 29, 30; no new drafts or publishing during the plan. Existing Day 1 draft remains historical and unpublished. |


## Day 1 baseline record (20 November 2026)

- **Verified baseline commit:** `fb18505f30e72cbb3016b5fecff7267d53a42416` (`docs: record Day 1 baseline blockers`), on `main` and pushed to `origin/main`.
- **Working tree:** the only pre-existing local change is untracked `pytest-results.txt`; it was preserved.
- **CI:** GitHub Actions run [#76](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44740263945) completed successfully. Python Unit and API Tests, Dashboard End-to-End Tests, and Dependency Security Audit all reported success.
- **Local checks completed:** `.venv` Python `compileall -q app tests`, `alembic heads`, `alembic history`, and dashboard `npm run build` all exited successfully. The Python unit and API suite reported **143 passed in 5.04s** against a disposable PostgreSQL 16 container, initialized with CI-equivalent migration and runtime roles.
- **E2E limitation:** local E2E was not run because the suite hardcodes backend port 8000, already used by another running project. Those containers were left untouched. The dashboard E2E job passed in CI run #76.
- **Security/readiness evidence:** CI dependency audits and the tests for runtime DB privileges/security completed successfully. The CI workflow and test setup were reviewed; both test suites depend on a migrated PostgreSQL database.
- **Cleanup:** the disposable `payguard-day1-postgres-20261120` container was stopped and removed. It had no mounted volumes; other Docker containers were left running.
- **Next:** Day 1 baseline gate closed. Day 2 documentation scope is reconciled; see the Day 2 record below. The old `pytest-results.txt` remains as an untracked local artifact and was not modified.


## Day 1 LinkedIn draft (draft; not published)

**Post copy:**

PayGuard-AI is shifting from a mock payment gateway toward a Payment Integration Reliability Lab. Before adding more features, I wanted a baseline I could point to instead of relying on optimism, which is not a test strategy.

The recorded local baseline includes 143 Python unit/API tests passing in 5.04 seconds against a disposable PostgreSQL 16 setup, plus Python compilation, Alembic head/history checks and a dashboard production build. GitHub Actions run #76 passed the Python/API, browser E2E and dependency-audit jobs. Run #77 also passed all three jobs for the baseline-completion documentation commit.

I did not run browser E2E locally because another project occupied the backend's fixed port 8000. The CI E2E job passed. That limitation stays in the record rather than being quietly converted into a claim that everything ran locally.

The 30-day plan now focuses on scenario definitions, deterministic assertions, evidence and replay, controlled failure injection, webhook reliability and concurrency. AI is deliberately deferred until the deterministic evidence foundation is built.

**Takeaway:** baseline evidence and explicit limitations come before feature velocity.

**Sanitized visual suggestion:** a simple three-job CI status screenshot beside a diagram labelled *planned* showing Scenario → Runner → Assertions/Evidence → Report/Replay. Exclude secrets, tokens and transaction data.

**Hashtags:** #QA #TestAutomation #Payments #ReliabilityEngineering #SoftwareTesting #Python #PostgreSQL

**Status:** Draft prepared for review; not published or externally scheduled.

## Day 2 documentation record (21 November 2026)

- **Scope:** product language, goals, non-goals and reliability-lab direction.
- **Verified documentation agreement:** README, PRD, architecture and test strategy describe the same product direction: an incremental scenario-testing lab inside the existing modular monolith, not a rewrite or real payment processor.
- **Scope boundaries:** synthetic data only; no real PAN/CVV, production payment processing or PCI claims; scenario engine, assertions, evidence/replay, failure injection, webhook and concurrency capabilities remain planned until implemented; AI remains deferred.
- **Changes in this increment:** reconciled status wording, recorded Day 2 verification, and prepared the Day 1 milestone draft. No scenario-engine code or tests were added.
- **CI:** GitHub Actions run [#78](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44861407842) completed successfully for commit `6591b995`; Python/API, dashboard E2E and dependency-audit jobs all passed. Evidence-record commit `3c999c2` was also validated by run [#79](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44861550394), all three jobs passed.
- **Limitations:** this scheduled environment has GitHub API access but no executable repository checkout/terminal, so it did not rerun local tests or local security tools.


## Day 3 schema increment (22 November 2026)

- **Scope:** typed declarative scenario definitions, steps, assertions, run lifecycle and result schemas; validation tests and schema boundary documentation.
- **Implemented:** enums for declared action/assertion kinds and run/step/assertion status; unique identifier/reference checks; dependencies restricted to earlier steps; timezone-aware lifecycle timestamps; scalar-only parameters/outputs; expected-value validation; result consistency and successful-run completeness.
- **Local evidence:** 20 schema tests passed in an isolated temporary workspace with Pydantic 2.13.5, pytest 9.0.3 and a minimal `TransactionStatus` stub. This is not a full-repository test run.
- **Commit:** [`dd30878`](https://github.com/Atharvagarud137/PayGuard-AI/commit/dd30878bb99ed4f773020e63967ecd6a3592e6be).
- **CI:** run [#80](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44981213809) passed all three jobs. Python/unit/API: 163 passed, 1 warning; dashboard E2E: 6 passed, 2 warnings; Python and JavaScript dependency audits passed.
- **Limitations:** no full local repository execution or local security audit was possible in this scheduled environment; the isolated schema run used a minimal `TransactionStatus` stub. CI executed the actual repository tests. The runner and persistence remain out of scope.
- **Not implemented:** scenario storage, migrations, runner, action-specific parameter contracts, failure-injection execution, evidence persistence and report export. Day 4 storage design was completed on 23 November; see the Day 4 record below.
- **Safety:** synthetic data only; no arbitrary code execution, payment processing or PCI claims.


## Day 4 scenario storage design (23 November 2026)

- **Scope:** storage design and ADR only.
- **Decision:** use the existing PostgreSQL database; immutable logical scenario versions; canonical payload digest; run records referencing an exact version and storing a frozen snapshot; relational fields for IDs/status/timestamps and JSONB for bounded validated payloads; phased step/assertion/event tables; explicit transaction boundaries and restrictive evidence retention.
- **ADR:** [ADR-001](ADR-001-scenario-storage.md).
- **Migration/role boundary:** the next migration follows `005_audit_reference_without_fk`; DDL remains migration-owner-only. The runtime role must remain DML-limited and must not gain schema ownership or CREATE privileges. Existing audit privileges/guards are unchanged.
- **Implementation boundary:** Day 5 starts with scenario-definition and run persistence. Runner results, assertion records and timeline events remain phased to their scheduled days.
- **CI:** run [#83](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45107175082) passed all three jobs for commit `b3bc41ca`. Run #82 was cancelled when the status correction commit superseded it.
- **Verification limitation:** this environment had GitHub API access but no executable repository checkout/terminal. No local tests, migration execution or local security tooling were run.
- **LinkedIn:** no draft or publishing work during the plan. Post preparation is deferred until Day 30 is complete.


## Day 5 scenario persistence implementation (24 November 2026)

- **Scope:** insert-only versioned scenario definitions, canonical JSON SHA-256 digests, frozen run snapshots and run-record retrieval/listing.
- **Migration:** revision `006_scenario_storage`, following `005_audit_reference_without_fk`.
- **Runtime privilege boundary:** definitions are SELECT/INSERT only. Runs are SELECT/INSERT with column-level UPDATE permission limited to status and lifecycle/failure fields; snapshot and identifier columns are not writable by the runtime role. Runs and definitions are not deletable by the runtime role.
- **Tests:** definition round trip, version ordering/uniqueness, run creation and retrieval, snapshot version binding, listing/pagination, invalid inputs and privilege assertions.
- **CI evidence:** run [#85](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45321053287) was cancelled after a corrective commit superseded it. Run [#86](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45321126812) passed all three jobs. Run [#87](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45321422221) had 168 Python/API tests pass and 6 persistence tests fail; run [#88](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45321699636) had 171 pass and 3 run-snapshot tests fail. E2E and dependency audits passed both runs. The first failure exposed Decimal type loss; the second exposed a create-run path still using ordinary JSON serialization. Both are being corrected.
- **Limitations:** the scheduled environment has GitHub repository access but no executable repository checkout or local PostgreSQL terminal. No runner, lifecycle transition service, step/assertion/timeline persistence, failure injection, report export or API routes were added. No LinkedIn content was prepared.
\n\n## Day 5 verification correction (24 November 2026)\n\nRun [#89](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45321910212) completed successfully on commit `b4fd439`: Python/unit/API, dashboard E2E and dependency-security jobs passed. Day 5 is complete. No local rerun was performed because an executable checkout/terminal was unavailable.\n\n## Day 6 scenario runner skeleton (25 November 2026)\n\n- **Status:** Complete. The runner implementation was committed early on 24 November and verified for the Day 6 calendar gate on 25 November.\n- **Code commit:** [`ab432a3`](https://github.com/Atharvagarud137/PayGuard-AI/commit/ab432a312dcc06e50fd87a53634b98f5c99ce89d), correcting failure tracking to use a set.\n- **CI:** run [#91](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45359793956) completed successfully across all three jobs. Python/unit/API suite: **180 passed, 1 warning**. Dashboard E2E: **6 passed, 2 warnings**. Python and dashboard dependency audits passed. Run #90 was cancelled for the earlier runner commit and is not treated as verification; #91 supersedes it.\n- **Implementation:** caller-injected handlers; deterministic declared step order; previous outputs passed as handler context; scalar output validation; sanitized handler failures; dependent steps skipped after failure; independent steps continue. Six runner tests passed in CI.\n- **Limitations:** run/step results are returned in memory only. Assertions and final run status are Day 7 scope. The runner does not persist step outcomes, perform real payment operations or register default action handlers. No local suite or local security tools were executed because this scheduled environment has no executable repository checkout/terminal.\n- **Safety:** synthetic test data only; no real PAN/CVV, production processing, arbitrary executable payloads or PCI claims.\n

## Day 7 assertions and run finalization (26 November 2026)

- **Status:** Complete.
- **Implementation commit:** [`b54258c`](https://github.com/Atharvagarud137/PayGuard-AI/commit/b54258c24a02cb4e829921ef2308a9fd4512106d).
- **CI:** Run [#93](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45749516234) passed Python unit/API, dashboard E2E and dependency security audit jobs. The inspected CI API metadata did not expose exact test counts. No local suite or local audit was run.
- **Implementation:** assertion registry evaluates step status, transaction status, idempotency replay, transaction count, amount invariant and audit integrity. Step-status reads the target result; other kinds read a declared scalar output key from the target step or, when untargeted, the latest step in scenario order containing that key. Missing or type-invalid observations fail. Assertion results are evaluated after step execution and run status is finalized: PASSED only if every step and assertion passes, otherwise FAILED.
- **Tests:** three additional runner tests cover all six assertion kinds passing, a value mismatch, and a missing observation. Existing runner tests were updated for assertion evaluation and terminal run status. CI verified the increment.
- **Limitations:** no executable checkout/terminal was available for local test execution. Step results are still in-memory; handler output is the observation boundary and does not independently query a payment service, PostgreSQL or audit storage. No default payment-action handlers or persisted step/assertion evidence were added. Synthetic data only.


## Day 8 timeline and evidence increment (27 November 2026)

- Status: implementation committed; CI pending.
- Scope: create runs from frozen scenario versions, bind runner output to the persisted run ID, persist terminal step/assertion results and structured events atomically, and query evidence/timeline in deterministic order.
- Migration: 007_scenario_evidence adds append-only step, assertion and timeline tables with per-run ordinals/sequences and runtime SELECT/INSERT privileges.
- API: run creation, terminal evidence submission, evidence retrieval and ordered timeline retrieval.
- Events: run start/completion, step start/completion/failure/skip and assertion evaluation; payloads are bounded scalar metadata rather than raw request bodies.
- Limitations: caller-injected handlers only; no real payment operations. No local test execution or migration run was performed in this scheduled environment.
