# PayGuard-AI test strategy

**Status date: 15 November 2026.**

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

GitHub Actions [run #39](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/43557859045), for commit `c1be0651fd3503f12e06061755e39228f32950e0`, completed successfully on 14 November 2026.

| CI job | Result |
|---|---|
| Python unit and API | 142 passed, 1 warning |
| Dashboard Playwright E2E | 6 passed, 2 warnings |
| Python dependency audit | Passed; no known vulnerabilities reported |
| JavaScript dependency audit | Passed; zero vulnerabilities reported |

The CI run therefore executed 148 passing tests across the two test jobs. These figures refer to run #39; the documentation-only commit has a separate run.

Warnings remain: Starlette's TestClient/httpx deprecation, a pytest fixture deprecation, Node dependency deprecations and GitHub Actions Node-runtime notices.

## PostgreSQL test requirements

The application and test fixtures require PostgreSQL. CI uses PostgreSQL 16.

- Set `DATABASE_URL` to the database used by Alembic and the application.
- Set `TEST_DATABASE_URL` to a dedicated disposable PostgreSQL database for pytest (or let it fall back to `DATABASE_URL`).
- Run `alembic upgrade head` before tests that exercise migration-installed triggers.
- Never use a development or production database for tests.

The root test fixture creates ORM tables and drops them at session teardown. Local test runs should use disposable databases. The CI Python and E2E jobs use separate PostgreSQL services.

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
