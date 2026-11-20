# PayGuard-AI

**A synthetic payment-system testing and reliability platform.**

PayGuard-AI models a payment lifecycle with FastAPI, PostgreSQL, a React/TypeScript dashboard, and automated tests. It is a software-testing simulation, not a payment processor. It does not connect to Visa, Mastercard, an acquirer, a bank, or a production payment network.

> **Data boundary:** use synthetic test data only. Do not submit or store real PANs, CVVs/CVCs, cardholder data, payment credentials, or production transaction data.

## Current status (15 November 2026)

Phase 2 and the current five-day security/documentation review are in progress. Day 1 (audit-history preservation) and Day 2 (migration/runtime role separation) are implemented. The latest verified CI run for Day 2 is [run #44243773973](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44243773973), which completed successfully on 18 November 2026.

| Area | Current state |
|---|---|
| Payment lifecycle | Card issuance, authorization, capture, settlement, full and partial refunds |
| Persistence | PostgreSQL through SQLAlchemy repositories and Alembic migrations |
| Transaction correctness | Row locks for card/transaction mutations; request-scoped DB transactions |
| Idempotency | Authorization, capture, settlement and refund |
| Audit | PostgreSQL hash chain, integrity verification, DB triggers blocking ordinary update/delete/truncate |
| Security baseline | Shared service/admin API keys, controlled CORS, safe errors, request-size limit, security headers, redaction |
| Dashboard | React 19 / TypeScript / Vite 8 |
| API/unit CI | 143 passed, 1 warning (run #44243773973) |
| Browser E2E CI | 6 passed, 2 warnings (run #44243773973) |
| Dependency audits | Passed in run #44243773973 |
| AI RCA / test generation | Planned, not implemented |
| OpenTelemetry / metrics | Not implemented |
| Distributed rate limiting | Not implemented; deployment gateway/reverse proxy responsibility |
| PCI DSS | No assessment or compliance claim |

The counts above are the results of CI run #44243773973 on the Day 2 commit. They are evidence for that commit, not a guarantee about future runs. Warnings remain in the CI logs.

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

**Important test-database warning:** `tests/conftest.py` creates ORM tables and drops them at session teardown. Point tests only at a disposable, dedicated test database. Do not point the test suite at a development or production database. Alembic migrations must be applied before tests that exercise database triggers.

## Current limitations and roadmap

1. Complete documentation review and final project assessment.
2. Improve production deployment configuration, including an authenticated dashboard client, secret rotation, HTTPS and gateway-level rate limiting.
3. Add operational metrics/tracing and better failure artifacts.
4. Evaluate migration/test-database lifecycle ergonomics.
5. Consider AI RCA and test suggestions only after deterministic reliability and observability needs are met.

No PCI DSS compliance, production payment capability, regulatory certification, or unrestricted exactly-once processing is claimed.
