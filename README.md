# PayGuard-AI

**A Payment Integration Reliability Lab for reproducible synthetic payment failure testing.**

PayGuard-AI models a payment lifecycle with FastAPI, PostgreSQL, a React/TypeScript dashboard, and automated tests. It is a software-testing simulation, not a payment processor. It does not connect to Visa, Mastercard, an acquirer, a bank, or a production payment network.

> **Data boundary:** use synthetic test data only. Do not submit or store real PANs, CVVs/CVCs, cardholder data, payment credentials, or production transaction data.

## Current status (22 November 2026)

The 30-day Payment Integration Reliability Lab roadmap is active. Day 1's baseline gate, Day 2's documentation scope and Day 3's typed schema increment are complete. Scenario schema commit `dd30878` passed all three GitHub Actions jobs in run [#80](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44981213809): 163 Python/unit/API tests passed (1 warning), 6 dashboard E2E tests passed (2 warnings), and dependency audits passed. Day 1 and Day 2 evidence remains recorded in the roadmap. This scheduled environment did not run a full local repository suite or local security tools.

| Area | Current state |
|---|---|
| Payment lifecycle | Card issuance, authorization, capture, settlement, full and partial refunds |
| Persistence | PostgreSQL through SQLAlchemy repositories and Alembic migrations |
| Transaction correctness | Row locks for card/transaction mutations; request-scoped DB transactions |
| Idempotency | Authorization, capture, settlement and refund |
| Audit | PostgreSQL hash chain, integrity verification, DB triggers blocking ordinary update/delete/truncate |
| Security baseline | Shared service/admin API keys, controlled CORS, safe errors, request-size limit, security headers, redaction |
| Dashboard | React 19 / TypeScript / Vite 8 |
| Scenario domain model | Typed declarative schemas and validation tests implemented; run #80 passed. Runner and persistence are not implemented. |
| API/unit | 143 passed locally at baseline; 163 passed in CI run #80 (1 warning) |
| Browser E2E | 6 passed in CI run #80 (2 warnings); local E2E remains unrun |
| Dependency audits | Passed in run #80 |
| AI RCA / test generation | Planned, not implemented |
| OpenTelemetry / metrics | Not implemented |
| Distributed rate limiting | Not implemented; deployment gateway/reverse proxy responsibility |
| PCI DSS | No assessment or compliance claim |

These results apply to the reviewed commit; they do not guarantee future runs. Local Python syntax compilation, Alembic head/history checks, the dashboard production build, and all 143 Python unit/API tests completed successfully. The prior `pytest-results.txt` run recorded 149 setup errors because no database URL was configured; those errors preceded test assertions and were resolved by using an isolated disposable PostgreSQL container. Local browser E2E was skipped because port 8000 is used by another project; its CI job passed. See [the roadmap baseline record](docs/ROADMAP_30_DAY_RELIABILITY_LAB.md) for details.

## Scenario domain model

The Day 3 schema increment defines scenario, step, assertion, run and result models with status enums, ordered dependencies, reference checks and lifecycle validation. Parameters and outputs are limited to inert scalar values; no runner or persistence is included. See [the scenario domain model specification](docs/SCENARIO_DOMAIN_MODEL.md). The schema suite has 20 tests; all were included in the 163-test Python/API CI suite in run #80. A separate isolated run also passed 20 tests using a minimal `TransactionStatus` stub, but it was not full-repository verification.

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
| [Scenario domain model](docs/SCENARIO_DOMAIN_MODEL.md) | Day 3 typed schema boundaries and validation rules; execution/persistence remain future work. |
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

## Current limitations and roadmap

1. Complete the Day 1 baseline review. GitHub CI run #73 is green, but local full-suite execution and deeper source/security review remain pending due to lack of an executable repository workspace.
2. Pivot into a Payment Integration Reliability Lab: scenario engine, deterministic assertions, structured evidence and replay.
3. Implement ambiguous outcomes and retry/idempotency scenarios.
4. Implement durable webhook simulation, retries, ordering and delivery evidence.
5. Add controlled concurrency/race testing and invariant-based reports.
6. Add CLI, sample merchant target and Docker Compose usability.
7. Consider evidence-grounded AI assistance only after the deterministic reliability lab is established.

No PCI DSS compliance, production payment capability, regulatory certification, or unrestricted exactly-once processing is claimed.


## Product pivot: Payment Integration Reliability Lab

PayGuard-AI's product direction is now to test how integrations behave under reproducible failure conditions, rather than expand the simulated gateway as an end in itself. The simulator remains infrastructure inside the lab.

The planned core capabilities are scenario execution, controlled ambiguous outcomes (such as commit followed by response loss), retry/idempotency testing, durable webhook simulation, concurrency/race testing, deterministic assertions, structured evidence, replay and exportable reports. AI analysis is deferred until the deterministic runner and evidence pipeline are mature.

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

No persistence code, ORM tables or migration were added on Day 4. This environment had GitHub repository access but no executable repository checkout/terminal, so no local tests, migration execution or local security tools were run. The next increment is Day 5 persistence, limited to the scheduled definition/run storage scope and verified by CI.


### Day 4 verification evidence

- **Design/evidence commit:** [`b3bc41ca`](https://github.com/Atharvagarud137/PayGuard-AI/commit/b3bc41caf47b48277bebf894db937e2ea8325590).
- **CI:** run [#83](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45107175082) passed Python unit/API, dashboard E2E and dependency-security jobs.
- **Superseded run:** #82 was cancelled when the follow-up status correction commit was pushed; run #83 verified the current Day 4 commit.
- **Limitations:** documentation-only work. No local test execution, migration execution or local security-tool run was possible in this environment. No scenario persistence code or migration was added.


## Day 5 scenario persistence (24 November 2026)

The Day 5 persistence increment is implemented on `main`. CI run [#86](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45321126812) passed all three jobs for the corrected import commit. Follow-up CI run [#87](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45321422221) exposed a Decimal type-preservation bug, corrected with tagged Decimal payloads. Run [#88](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45321699636) then exposed one remaining path: run creation still used ordinary JSON serialization rather than the tagged payload helper. The fix is now pending CI. Both runs had passing E2E and dependency audits. The increment includes insert-only, versioned scenario-definition storage, canonical SHA-256 payload digests, run creation from an exact persisted version, and frozen JSONB snapshots. Run status fields are queryable, and runtime permissions allow lifecycle-column updates without granting changes to definition versions or run snapshots.

The implementation adds PostgreSQL tables and an Alembic migration, a repository for definition/version and run-snapshot CRUD, integration tests, and restricted runtime privileges. No runner, step/assertion evidence tables, failure injection, report export or API endpoints were added in this increment. Local execution is unavailable in this scheduled environment; CI is the verification gate.
