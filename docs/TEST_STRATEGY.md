# PayGuard-AI test strategy

**Status date: 26 November 2026.**

## Testing objective

Validate payment lifecycle correctness, persistence, transaction atomicity, concurrency behavior, idempotency, audit integrity, security boundaries and the browser dashboard. The test count is not the goal; the goal is evidence for specific invariants and failure paths.

## Current test layers

| Layer | Location | Focus |
|---|---|---|
| Unit | `tests/unit` | Money handling, state machine, payment service, configuration and redaction |
| API / PostgreSQL integration | `tests/api` | Card/payment endpoints, dashboard, persistence, idempotency, audit, security and database concurrency |
| Browser E2E | `tests/e2e` | Dashboard rendering, cards, transactions and lifecycle inspection |
| Dependency audit | GitHub Actions | Python and JavaScript dependency vulnerability checks |

## Latest verified CI evidence

GitHub Actions [run #93](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45749516234) for commit `b54258c` completed successfully on 26 November 2026. Run #80 remains the historical Day 3 schema evidence.

| CI job | Result |
|---|---|
| Python unit and API | 163 passed, 1 warning |
| Dashboard Playwright E2E | 6 passed, 2 warnings |
| Python dependency audit | Passed |
| JavaScript dependency audit | Passed |

The run completed all three CI jobs. Warnings remain: Starlette's TestClient/httpx deprecation, pytest fixture deprecation, Node dependency deprecations and GitHub Actions Node-runtime notices.

## Runtime privilege-boundary tests

The API test suite checks that the application role is not a table owner, cannot create schema objects, can perform the required card data operations and audit reads/inserts, and lacks audit UPDATE, DELETE, TRUNCATE and trigger-management privileges. Audit-maintenance and trigger tampering checks use the migration-owner connection rather than runtime credentials.

## PostgreSQL test requirements

The application and test fixtures require PostgreSQL. CI uses PostgreSQL 16.

- Set `DATABASE_URL` to the database used by Alembic and the application.
- Set `TEST_DATABASE_URL` to a dedicated disposable PostgreSQL database for pytest (or let it fall back to `DATABASE_URL`).
- Run `alembic upgrade head` before tests that exercise migration-installed triggers.
- Never use a development or production database for tests.

The test fixtures verify that Alembic migrations have already been applied; they do not create or drop tables. The runtime/test role has DML access only, while migrations and audit-maintenance tests use the migration-owner role. CI Python and E2E jobs use separate PostgreSQL services and role setups.

## Payment correctness and atomicity

The API tests verify:

- Authorization locks the card row before reading and changing its balance.
- Capture, settlement and refund lock the transaction row before lifecycle mutation.
- Payment state, transaction events, audit events and idempotency records share the request transaction on successful mutation paths.
- Injected failures after flush roll back the relevant financial state and associated writes.
- Database constraints reject selected invalid monetary states.

The concurrency tests use independent PostgreSQL sessions. They cover concurrent authorizations against one card balance, duplicate capture and competing refunds. Passing these tests supports those tested cases; it does not prove all possible concurrency schedules or failure modes.

## Idempotency coverage

Idempotency is tested for authorization, capture, settlement and refund.

- Same key + same request replays the stored response.
- Same key + different request returns HTTP 409.
- Concurrent duplicate requests serialize through a transaction-scoped PostgreSQL advisory lock.
- The mutation and replay record commit in the same transaction.
- A unique database constraint remains a second safeguard.
- Requests without a key remain non-idempotent.

The tests verify one committed mutation, one replay record and the expected audit effect for the concurrent duplicate scenarios. They do not establish a universal exactly-once guarantee across every network or infrastructure failure.

## Audit and security coverage

Audit tests cover event creation, query by transaction/correlation ID, redaction, hash-chain verification, detection of out-of-band modification, and rejection of ordinary UPDATE/DELETE/TRUNCATE statements.

Security tests cover service/admin key boundaries, the test reset token, production failure-simulation restrictions, PAN/CVV field rejection without echoing values, CORS origin handling, generic unexpected-error responses, response headers, no-store behavior, request-size limits and log redaction.

The audit hash chain is tamper-evident against ordinary application operations, not immutable against a database owner/superuser.

## Playwright E2E coverage

The E2E fixtures seed synthetic backend state through the API and use Playwright Chromium for the browser assertions. The frontend and backend are started separately from pytest. The E2E suite does not replace unit or API tests.

Current E2E cases cover card creation, dashboard load, transactions page load/empty state, authorized transaction visibility and lifecycle inspection.

## CI workflow

The workflow has three jobs:

1. **Python Unit and API Tests:** Python 3.12, PostgreSQL 16, syntax check, Alembic validation/migration, then `pytest tests/unit tests/api -v --tb=short`.
2. **Dashboard End-to-End Tests:** PostgreSQL 16, Python 3.12, Node 22, `npm ci`, dashboard build, Chromium install, migrations, backend/frontend startup and `pytest tests/e2e -v --tb=short`.
3. **Dependency Security Audit:** `pip-audit -r requirements.txt` and `npm audit --audit-level=high`.

## Local commands

```powershell
# Use a dedicated PostgreSQL test database and apply migrations first
pytest tests/unit tests/api -v --tb=short

# With the test backend and Vite frontend already running
pytest tests/e2e -v --tb=short

# Dashboard build
cd dashboard
npm ci
npm run build
```

See [SETUP.md](SETUP.md) for database environment variables and the E2E reset-token configuration.

## Known test limitations

- The root pytest fixtures drop ORM tables after a session, so a disposable database must be recreated before repeating migration-dependent test runs.
- E2E tests require a separately running backend and frontend.
- The health endpoint is a liveness response, not a dependency readiness probe.
- No performance/load, chaos, multi-region, penetration or formal PCI DSS assessment is part of the current CI suite.
- No AI RCA or AI-generated test validation is implemented.

No PCI DSS compliance or production payment capability is claimed.


## Day 3 scenario schema validation

`tests/unit/test_scenario_models.py` adds 20 schema tests for scenario/step/assertion/run/result types, ordered dependencies, reference integrity, status lifecycle timestamps, scalar-only inert parameters, assertion expected/observed values and successful-run completeness.

**Local isolated evidence:** 20 passed in a temporary workspace using Pydantic 2.13.5, pytest 9.0.3 and a minimal `TransactionStatus` stub. This was not a full-repository test run. GitHub Actions run [#80](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44981213809) then validated the repository commit: 163 Python/unit/API tests passed (1 warning), 6 browser E2E tests passed (2 warnings), and dependency audits passed. The runner, persistence, action-specific parameter contracts and report generation are not implemented.

## Target reliability-scenario testing strategy (planned)

The test strategy will evolve from endpoint/regression coverage toward evidence that scenario-defined invariants hold under controlled conditions. These capabilities are planned, not yet implemented.

### Scenario test layers
- **Schema/unit:** definition validation, step types, assertion types, canonical serialization and scenario-version rules.
- **Runner integration:** lifecycle, step sequencing, deterministic outcomes, failure handling and evidence persistence.
- **Replay:** re-execution with recorded seed/parameters and comparison of expected observable behavior.
- **Ambiguous outcomes:** request failure before processing, during processing and after commit, with stage semantics explicitly tested.
- **Idempotency/retry:** same key/same payload, same key/conflicting payload, retry after response loss and concurrent duplicates.
- **Webhook:** duplicate, delayed, out-of-order, failed, retry-exhausted and replay delivery.
- **Concurrency:** barrier-controlled races with invariant assertions, not arbitrary sleep-based timing.
- **Recovery:** worker restart, pending-job recovery and durable-state checks where implemented.
- **Evidence/reporting:** assertions, event timelines, sanitized records, reproducibility metadata and report schema.

### Invariant-focused examples
- One logical operation for a replayed idempotent request.
- Refund/capture totals never exceed modeled limits in tested schedules.
- Duplicate webhook delivery does not cause duplicate handling in the sample receiver.
- Out-of-order events are either safely handled or the scenario reports the defined failure.
- A committed operation whose response is lost is discoverable/replayable through the intended contract.

### Evidence requirements
Every scenario report should identify scenario/version, execution ID, inputs/parameters, expected assertions, observed results, timestamps, step outcomes and sanitized evidence. AI-generated explanations, if later used, are evaluated separately from deterministic test verdicts.

### CI policy
Each daily increment adds relevant regression coverage and runs existing CI. Failures block the next roadmap task. Never infer results from a commit or claim tests pass without run evidence.


## Day 4 storage design and planned persistence tests

[ADR-001: Scenario definition and run evidence storage](ADR-001-scenario-storage.md) is the accepted design for the upcoming persistence increment. The initial Day 5 tests must cover versioned definition insert/read, canonical digest and snapshot consistency, run creation tied to an exact definition version, uniqueness and positive-version constraints, timestamp/status checks, restrictive references, and runtime/migrator role separation. Subsequent runner/assertion/evidence increments add lifecycle-transition, step/assertion result and append-only event tests. The ADR is a design record, not evidence that persistence tests or migrations have run.


## Day 5 persistence tests (24 November 2026)

The persistence increment adds PostgreSQL integration coverage for definition round trips, ordered versions, insert-only version uniqueness, missing-definition handling, run creation, exact-version frozen snapshots, run retrieval/list filtering and pagination, invalid inputs, and runtime column privileges. Canonical digest comparison, tagged Decimal round trips that preserve numeric strings, and the 64 KiB payload limit are covered. CI run #86 passed all three jobs for the corrected import commit. Run #87 failed 6 persistence tests because plain JSON strings lost Decimal type identity; run #88 failed 3 run-snapshot tests because the create-run path still used the ordinary JSON serializer. The tagged serializer and corrected run-snapshot path are pending CI. Local PostgreSQL execution was unavailable in the scheduled environment.
\n\n## Day 6 runner skeleton tests\n\nRunner tests cover declared-order execution/context, missing handlers, dependency skips, independent-step continuation, sanitized failures, scalar-output validation, Decimal preservation and the deliberate RUNNING status pending Day 7 assertion evaluation. CI is the verification gate; local execution was unavailable.\n

## Day 7 assertions and finalization

CI run [#93](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45749516234) passed all three jobs for the Day 7 implementation. The runner evaluates six assertion kinds against scalar step-output observations, fails missing/type-invalid observations, and finalizes run status based on both step and assertion results. Three added tests cover all-kind success, mismatch failure and missing-observation failure. Exact CI test counts were not available through the inspected API metadata, and no local suite was run.

Observations are supplied by injected handlers, not independent live payment, PostgreSQL or audit queries. Step and assertion evidence is not persisted yet.


## Scenario-run evidence and timeline

Day 8 adds CI coverage for run creation from a frozen version, result submission, reconstruction, timeline sequence ordering, evidence retrieval, duplicate-terminal submission rejection, snapshot mismatch rejection and append-only runtime table privileges. The runner emits ordered events for run start, step start/completion/failure/skip, assertion evaluation and run completion. Evidence scalar validation rejects common PAN/CVV/CVC, card-number, raw-payload and credential/secret key names, while preserving bounded scalar output values. Local execution remains unavailable in the scheduled environment; CI is the verification gate.
