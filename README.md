# PayGuard-AI

**A Payment Integration Reliability Lab for reproducible synthetic payment failure testing.**

PayGuard-AI models a payment lifecycle with FastAPI, PostgreSQL, a React/TypeScript dashboard, and automated tests. It is a software-testing simulation, not a payment processor. It does not connect to Visa, Mastercard, an acquirer, a bank, or a production payment network.

> **Data boundary:** use synthetic test data only. Do not submit or store real PANs, CVVs/CVCs, cardholder data, payment credentials, or production transaction data.

## Current status (26 November 2026)

Days 1–6 are complete. Day 7's deterministic assertion evaluation and run finalization are implemented and verified by GitHub Actions run [#93](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45749516234) for commit `b54258c`. All three CI jobs passed: Python/unit/API, dashboard E2E, and dependency security audit. Exact test counts were not available from the inspected CI API response. This environment has GitHub API access but no executable repository checkout/terminal, so no local suite or local audit was run.

| Area | Current state |
|---|---|
| Payment lifecycle | Card issuance, authorization, capture, settlement, full and partial refunds |
| Persistence | PostgreSQL through SQLAlchemy repositories and Alembic migrations |
| Transaction correctness | Row locks for card/transaction mutations; request-scoped DB transactions |
| Idempotency | Authorization, capture, settlement and refund |
| Audit | PostgreSQL hash chain, integrity verification, DB triggers blocking ordinary update/delete/truncate |
| Security baseline | Shared service/admin API keys, controlled CORS, safe errors, request-size limit, security headers, redaction |
| Dashboard | React 19 / TypeScript / Vite 8 |
| Scenario lab | Typed scenario models, versioned PostgreSQL definition/run snapshots, deterministic step runner, assertions, persisted step/assertion evidence and ordered timeline APIs implemented. |
| API/unit | CI run #93 passed the Python unit/API job; exact count not exposed in the inspected API metadata |
| Browser E2E | CI run #93 passed the dashboard E2E job; local E2E remains unrun |
| Dependency audits | Python and JavaScript audits passed in CI run #93 |
| AI RCA / test generation | Planned, not implemented |
| OpenTelemetry / metrics | Not implemented |
| Distributed rate limiting | Not implemented; deployment gateway/reverse proxy responsibility |
| PCI DSS | No assessment or compliance claim |

These results apply to the reviewed commit; they do not guarantee future runs. Local Python syntax compilation, Alembic head/history checks, the dashboard production build, and all 143 Python unit/API tests completed successfully. The prior `pytest-results.txt` run recorded 149 setup errors because no database URL was configured; those errors preceded test assertions and were resolved by using an isolated disposable PostgreSQL container. Local browser E2E was skipped because port 8000 is used by another project; its CI job passed. See [the roadmap baseline record](docs/ROADMAP_30_DAY_RELIABILITY_LAB.md) for details.

## Scenario lab foundation

Day 3 added typed scenario/step/assertion/run/result schemas; Day 5 added versioned PostgreSQL definitions and frozen run snapshots; Day 6 added deterministic injected-handler step execution; Day 7 evaluates six assertion kinds against scalar step-output observations and finalizes the run as PASSED only when every step and assertion passes. Missing/type-invalid observations fail assertions. Results remain in-memory and handlers are caller-injected. CI run #93 passed all three jobs. See [the scenario domain model specification](docs/SCENARIO_DOMAIN_MODEL.md) and [the roadmap](docs/ROADMAP_30_DAY_RELIABILITY_LAB.md).

## Payment lifecycle

```text
Card issuance
    |
    v
Authorization -----> DECLINED (terminal business outcome)
    |
    v
Capture
    |
    v
Settlement
    |
    +----> Partial refund(s) ----> REFUNDED
    |
    +----------------------------> REFUNDED
```

The domain layer validates lifecycle transitions and monetary invariants. PostgreSQL constraints provide additional persistence-level checks.

## Architecture

```text
React / TypeScript dashboard
          |
          | HTTP
          v
FastAPI routes and request validation
          |
          v
PaymentService / domain state machine
          |
          +---- PostgreSQL card repository
          +---- PostgreSQL transaction repository
          +---- PostgreSQL audit repository
          +---- PostgreSQL idempotency repository
                         |
                         v
                    PostgreSQL
```

The API owns the SQLAlchemy session and transaction boundary. Repositories flush changes but do not commit. Payment state, lifecycle events, audit records and idempotency responses are committed together by the request handler.

### Concurrency and idempotency

- Authorization locks the card row with `SELECT ... FOR UPDATE` before checking/updating its balance.
- Capture, settlement and refund lock the transaction row before lifecycle read-modify-write operations.
- Idempotency uses a transaction-scoped PostgreSQL advisory lock for each key.
- The first request stores its request fingerprint and response in the same transaction as the payment mutation.
- The same key and same request replays the stored response. Reusing a key with a different request returns HTTP 409.
- Requests without an idempotency key remain non-idempotent.

The concurrency tests use independent PostgreSQL sessions. They establish the tested scenarios, not a universal exactly-once guarantee for every possible failure mode or deployment.

### Audit integrity

Audit inserts are serialized into a sequence/hash chain. PostgreSQL triggers reject ordinary updates, deletes and truncation. An admin-protected endpoint verifies the chain. This is tamper-evident against normal application/database operations, not immutable against a database owner or superuser able to disable triggers and rewrite data. There is no external signed anchor or WORM archive.

## Security boundary

- `PAYGUARD_ENV` defaults to `production`; local development must explicitly set `development`.
- Production requires `DATABASE_URL`, `PAYGUARD_API_KEY` and `PAYGUARD_ADMIN_API_KEY`. API keys must be at least 32 characters.
- Business/dashboard routes use `X-API-Key`; audit routes use `X-Admin-API-Key`.
- Test reset is disabled by default and can only be enabled in `test` mode with a separate token.
- Failure simulation and FastAPI docs are disabled in production.
- CORS requires explicit origins in production. Wildcard origins are rejected.
- Request bodies are limited to 64 KiB by default (configurable from 1 KiB to 1 MiB).
- Validation errors do not echo submitted values; unexpected errors return a generic response.
- Logs and audit fields pass through redaction helpers.

These are code-level controls, not a complete identity platform. There is no per-user authentication/RBAC, API-key rotation workflow, built-in rate limiter, or production secret manager. HTTPS, gateway rate limiting, network controls, secret storage/rotation and monitoring must be supplied by a deployment environment.

**Dashboard production limitation:** the current dashboard client calls `http://localhost:8000/api/v1` and does not attach `X-API-Key`. It is a local development/test UI, not a production-ready authenticated frontend. Do not expose it as a production operations console without changing its API configuration and credential flow.

## Repository documentation

| Document | Covers |
|---|---|
| [Product requirements](docs/PRD.md) | Product scope, non-goals and requirements |
| [Architecture](docs/ARCHITECTURE.md) | Runtime boundaries, transactions, locks, idempotency and audit |
| [Scenario domain model](docs/SCENARIO_DOMAIN_MODEL.md) | Typed contracts, storage boundary and Day 6 runner behavior/limitations. |
| [API specification](docs/API_SPEC.md) | Routes, headers, request behavior and responses |
| [Test strategy](docs/TEST_STRATEGY.md) | PostgreSQL integration, concurrency, security and E2E tests |
| [Technology stack](docs/TECH_STACK.md) | Runtime and development tools |
| [Setup guide](docs/SETUP.md) | Local PostgreSQL, backend, dashboard and test commands |
| [AI pipeline](docs/AI_PIPELINE.md) | Proposed, not implemented, AI workflows |
| [Playwright vs Selenium](docs/playwright-vs-selenium-payguard-ai.md) | Browser automation choice |
| [Historical GitHub audit](docs/reference/github-vs-local-audit.md) | Earlier repository snapshot, superseded by current status |
| [Recovered project context](docs/reference/payguard-ai-context-from-chatgpt.md) | Historical decisions and prior work |

## Run locally

See [docs/SETUP.md](docs/SETUP.md) for the full setup. In brief:

1. Start a local PostgreSQL instance and create a development database.
2. Set `PAYGUARD_ENV=development` and `DATABASE_URL`.
3. Run `alembic upgrade head`.
4. Start the API with `uvicorn app.main:app --reload --reload-dir app --port 8000`.
5. In `dashboard/`, run `npm ci` and `npm run dev`.

The dashboard currently targets `http://localhost:8000`.

## Test and CI commands

The CI workflow separates the suites:

```powershell
# Requires a dedicated PostgreSQL test database and migrations at head
pytest tests/unit tests/api -v --tb=short

# Requires the backend and Vite frontend to be running in test mode
pytest tests/e2e -v --tb=short

# Dashboard production build
cd dashboard
npm ci
npm run build

# Optional local lint command
npm run lint
```

CI run #39 used Python 3.12, PostgreSQL 16 and Node.js 22. It ran the Python unit/API suite, Playwright Chromium E2E suite, `pip-audit`, and `npm audit --audit-level=high`.

**Test-database warning:** fixtures require an already-migrated disposable PostgreSQL database and do not create or drop ORM tables. Point tests only at a dedicated disposable database, never a development or production database.

## Scenario evidence and timeline (Day 8 increment; CI pending)

Scenario runs can be created from an immutable stored scenario version, and a terminal runner result can be submitted against that run ID. Step and assertion results, structured events and the run lifecycle are persisted in one database transaction. Timeline queries return a deterministic sequence; evidence records are ordered by the definition's step/assertion ordinals. The evidence tables are insert-only for the runtime role. Common field names associated with PAN/CVV/CVC, card numbers, raw request/response bodies, credentials, secrets, passwords and API keys are rejected in scalar evidence. This is a key-name guard, not a substitute for synthetic-only data discipline. The runner still uses caller-injected handlers and is not wired to live payment operations. Local tests were not run in this scheduled environment.

API endpoints added:
- POST /api/v1/scenarios/{scenario_id}/versions/{version}/runs
- POST /api/v1/scenario-runs/{run_id}/evidence
- GET /api/v1/scenario-runs/{run_id}/evidence
- GET /api/v1/scenario-runs/{run_id}/timeline

## Current limitations and roadmap

1. Day 8: structured event timeline, durable step/assertion evidence and ordered query APIs (CI verification pending).
2. Days 9–10: report schema/export and deterministic replay.
3. Days 11–16: stage-aware failure injection, ambiguous outcomes, retry/idempotency and crash/recovery tests.
4. Days 17–22: webhook model, outbox, delivery worker, retries, faults, ordering and synthetic signatures.
5. Days 23–26: controlled concurrency/race scenarios and evidence-grounded reports.
6. Days 27–30: CLI, sample merchant, Docker Compose, Vercel dashboard staging and final readiness decision.
7. AI assistance remains deferred until the deterministic reliability foundation is complete.

No PCI DSS compliance, production payment capability, regulatory certification, or unrestricted exactly-once processing is claimed.


## Product pivot: Payment Integration Reliability Lab

PayGuard-AI's product direction is now to test how integrations behave under reproducible failure conditions, rather than expand the simulated gateway as an end in itself. The simulator remains infrastructure inside the lab.

The planned capabilities include controlled ambiguous outcomes (such as commit followed by response loss), retry/idempotency testing, durable webhook simulation, concurrency/race testing, deterministic assertions, structured evidence, replay and exportable reports. Scenario definitions, storage and the basic in-memory runner are implemented; the remaining capabilities are still roadmap items. AI analysis is deferred until the deterministic runner and evidence pipeline are mature.

**This pivot is a roadmap, not a claim that these features already exist.** The current implementation remains the synthetic payment lifecycle and reliability foundation described above.

### LinkedIn build-in-public plan

Milestone evidence is tracked at Days 1, 7, 10, 16, 22, 26, 29 and 30. The user has decided to prepare and publish the LinkedIn series only after the full 30-day plan is complete. No new LinkedIn drafts, publishing or scheduling work will be done during the roadmap. The existing Day 1 draft is retained as historical, unpublished content and will not be expanded during the plan.

### Roadmap and daily updates

- [30-day daily implementation roadmap](docs/ROADMAP_30_DAY_RELIABILITY_LAB.md): planned daily increments, gates, deliverables and acceptance criteria.
- [Product requirements](docs/PRD.md): updated product direction, scope and non-goals.
- [Architecture](docs/ARCHITECTURE.md): current architecture and planned scenario-lab evolution.
- [Test strategy](docs/TEST_STRATEGY.md): current evidence and target scenario-testing strategy.
- [API specification](docs/API_SPEC.md): current API contract only; proposed scenario APIs are not implemented contracts.
- [AI pipeline](docs/AI_PIPELINE.md): AI is deferred and evidence-grounded, not an immediate build priority.

**Daily execution rule:** each day's work is committed directly to main only after inspecting the latest commit and CI. A failing CI run blocks the next planned day's task. README status, evidence and known limitations are updated on significant milestones. No PRs or history rewriting.


## Day 1 baseline status (20 November 2026)

Day 1 is complete in the repository's recorded baseline. Commit `fb18505` records the local verification results: 143 Python unit/API tests passed in 5.04 seconds against a disposable PostgreSQL 16 database with migration/runtime roles separated; `compileall`, Alembic head/history and the dashboard production build also passed. GitHub Actions run [#76](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44740263945) passed all three jobs for `fb18505`, and run [#77](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44741250041) passed all three jobs for completion commit `bd4aa96`.

Local browser E2E was not run because another project occupied backend port 8000; the CI E2E job passed. Local dependency-audit commands were not run in the recorded baseline, but the CI security-audit job passed. This scheduled run confirmed the repository record and CI; it did not rerun local tests or security tools because it still lacks an executable checkout/terminal.

## Day 2 documentation status (21 November 2026)

The product-scope gate is complete as a documentation-only increment. README, PRD, architecture and test strategy consistently describe PayGuard-AI as a **planned Payment Integration Reliability Lab** built on the existing modular monolith. Scenario definitions, deterministic assertions, evidence/replay, controlled failure injection, webhooks and concurrency are planned; no new scenario-engine implementation is claimed. Synthetic-data-only boundaries remain explicit, and AI is deferred until the deterministic evidence foundation exists. The Day 1 post draft is retained as historical, unpublished content. Further LinkedIn drafting is deferred until the entire 30-day roadmap is complete.


## Day 4 scenario storage design (23 November 2026)

Day 4 is complete as a design-only increment. Commit `b3bc41ca` was verified by GitHub Actions run [#83](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45107175082), which passed all three jobs. The accepted storage decision is documented in [ADR-001: Scenario storage and run evidence](docs/ADR-001-scenario-storage.md). The design uses the existing PostgreSQL database, versioned immutable scenario definitions, run records with frozen definition snapshots, and phased step/assertion/event evidence tables. It preserves the Alembic migration-owner/runtime-role split and explicitly addresses transaction boundaries for ambiguous post-commit outcomes.

No persistence code, ORM tables or migration were added on Day 4. Day 5 subsequently implemented definition/run snapshot storage; see the Day 5 record. Day 4 local tests, migration execution and local security tooling were not run.


### Day 4 verification evidence

- **Design/evidence commit:** [`b3bc41ca`](https://github.com/Atharvagarud137/PayGuard-AI/commit/b3bc41caf47b48277bebf894db937e2ea8325590).
- **CI:** run [#83](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45107175082) passed Python unit/API, dashboard E2E and dependency-security jobs.
- **Superseded run:** #82 was cancelled when the follow-up status correction commit was pushed; run #83 verified the current Day 4 commit.
- **Limitations:** documentation-only work. No local test execution, migration execution or local security-tool run was possible in this environment. No scenario persistence code or migration was added.


## Day 5 scenario persistence (24 November 2026)

The Day 5 persistence increment is implemented on `main`. CI runs [#87](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45321422221) and [#88](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45321699636) exposed Decimal and tagged-snapshot serialization defects; the final correction was verified by run [#89](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45321910212), which passed all three jobs. The increment includes insert-only, versioned scenario-definition storage, canonical SHA-256 payload digests, run creation from an exact persisted version, and frozen JSONB snapshots. Run status fields are queryable, and runtime permissions allow lifecycle-column updates without granting changes to definition versions or run snapshots.

The implementation adds PostgreSQL tables and an Alembic migration, a repository for definition/version and run-snapshot CRUD, integration tests, and restricted runtime privileges. No runner, step/assertion evidence tables, failure injection, report export or API endpoints were added in this increment. Local execution is unavailable in this scheduled environment; CI is the verification gate.
\n\n## Day 6 runner skeleton (25 November 2026)\n\nThe runner is implemented in `app/services/scenario_runner.py` with caller-injected handlers. It executes steps in declared order, passes previous outputs to handlers, rejects invalid/nested outputs through schema validation, sanitizes handler failures, skips dependent steps after failures and continues independent steps. Six runner tests are included in CI run [#91](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45359793956), which passed all three jobs.\n\nThe returned result is in-memory only. Assertions and finalization are Day 7 scope; run status deliberately remains `RUNNING` and assertion results remain empty. Step-level execution evidence is not persisted to PostgreSQL yet. No local execution was performed in this scheduled environment.\n\n## Deployment plan\n\nThe roadmap targets Vercel dashboard staging on Day 29 and final deployment/readiness validation on Day 30. Vercel hosts the dashboard; the Python API requires separately configured and verified backend hosting. Deployment depends on secure configuration, API reachability, CORS and synthetic-only validation.