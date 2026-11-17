# PayGuard-AI architecture

**Status date: 15 November 2026.** This document describes the implementation at `main` commit `c1be0651fd3503f12e06061755e39228f32950e0`. AI workflows, production deployment hardening and distributed operations remain future work.

## System boundary

PayGuard-AI is a synthetic payment gateway and reliability-testing platform. It is not a processor, acquirer, issuer, card-network integration or production payment application. Card identifiers are generated/masked for test use. Real PAN and CVV/CVC data must never be submitted.

## Runtime architecture

```text
React + TypeScript dashboard
          |
          | HTTP / JSON
          v
FastAPI application
  - request validation
  - service/admin API-key checks
  - idempotency orchestration
  - error mapping
  - security middleware
          |
          v
PaymentService + transaction state machine
          |
          +---- PostgresCardRepository
          +---- PostgresTransactionRepository
          +---- PostgresAuditRepository
          +---- PostgresIdempotencyRepository
                         |
                         v
                     PostgreSQL
```

The backend is a modular monolith. The HTTP layer coordinates requests and transactions; payment rules live in the service/domain layer; repositories translate domain objects to PostgreSQL models. The dashboard calls the HTTP API and does not access the database directly.

## Persistence model

SQLAlchemy models and Alembic migrations define PostgreSQL tables for:

- Cards and their synthetic masked identifiers.
- Transactions and their monetary lifecycle fields.
- Transaction lifecycle events.
- Audit events and the audit hash chain.
- Idempotency records containing a key, request fingerprint and serialized response.

Database constraints enforce selected invariants such as non-negative amounts and captured/settled/refunded totals not exceeding their parent amounts. These checks complement domain validation; they do not replace it.

The application uses a request-scoped SQLAlchemy session. Repositories flush but do not commit. The API handler owns commit/rollback so a successful mutation can persist its financial state, lifecycle event, audit record and idempotency response in one transaction. Failure paths roll back the financial mutation before recording a separate failure audit event where the route supports it.

## Concurrency controls

- Authorization obtains a PostgreSQL row lock on the card before checking and changing its balance.
- Capture, settlement and refund obtain a row lock on the transaction before lifecycle read-modify-write operations.
- Locks remain held until the surrounding transaction commits or rolls back.
- Tests exercise concurrent authorization against one card, duplicate capture and competing refunds using independent PostgreSQL sessions.

The test results establish those scenarios under the tested PostgreSQL setup. They are not a blanket guarantee for every multi-step workflow, infrastructure failure, isolation configuration or deployment topology.

## Idempotency

The API supports optional `Idempotency-Key` headers on authorization, capture, settlement and refund.

For a supplied key:

1. The repository obtains a transaction-scoped PostgreSQL advisory lock derived from the key.
2. The handler looks up an existing completed record.
3. A matching request fingerprint returns the original stored response.
4. A different fingerprint returns HTTP 409.
5. If no record exists, the mutation executes and its response is stored in the same database transaction.
6. Commit or rollback releases the advisory lock.

A unique database constraint remains a second safeguard against duplicate records. The key is optional; calls without one retain non-idempotent behavior. The implementation does not claim universal exactly-once delivery across every possible client/network/database failure.

## Audit design

Audit inserts are serialized using a transaction-scoped advisory lock. Each row stores a sequence number, previous hash and event hash calculated from canonical event fields. The admin-protected integrity endpoint checks sequence continuity and hashes.

Database triggers reject UPDATE, DELETE and TRUNCATE operations. The test reset route does not delete audit rows; it preserves append-only history while clearing synthetic payment data. No caller-settable PostgreSQL setting grants an audit-delete exception. This design is tamper-evident against ordinary application operations, not immutable against a database owner/superuser who can disable triggers or rewrite the chain. There is no external signed anchor, WORM storage or independent audit export.

AuditService accepts explicit operational fields rather than arbitrary request bodies and applies redaction before persistence. Audit routes require the admin key outside isolated tests.

## Security controls implemented

- `PAYGUARD_ENV` supports `development`, `test` and `production`; the default is `production`.
- Production requires an explicit database URL and separate service/admin API keys, each at least 32 characters.
- Business and dashboard API routes require `X-API-Key`; audit routes require `X-Admin-API-Key`.
- Key comparisons use constant-time comparison.
- CORS uses explicit origins; wildcard origins are rejected.
- FastAPI docs/OpenAPI and failure simulation are disabled in production.
- The destructive test-reset route is not registered by default and can only be enabled in test mode with a separate token.
- Request bodies are limited to 64 KiB by default, configurable within 1 KiB–1 MiB.
- Validation errors omit submitted values; unexpected errors return generic details.
- Security headers and API `Cache-Control: no-store` are added.
- Log messages and audit fields are passed through sensitive-value redaction.

## Known security and deployment gaps

There is no per-user identity, RBAC, tenant isolation, key rotation/revocation workflow, built-in rate limiter, external secret manager, metrics/tracing stack or automated incident response. HTTPS and gateway/reverse-proxy rate limiting must be supplied by deployment infrastructure.

The dashboard API client currently hardcodes `http://localhost:8000/api/v1` and does not attach `X-API-Key`. It therefore works only with a local development/test backend that has no service key configured. It is not production-ready; do not embed a production key in a browser-exposed Vite variable.

The root endpoint is a basic liveness response, not a database readiness check.

## Test architecture and verified evidence

The test suite includes unit, API/PostgreSQL integration, concurrency, rollback, security/redaction, audit-integrity and Playwright browser tests. CI run [#39](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/43557859045) on 14 November 2026 recorded:

- Python unit/API: 142 passed, 1 warning.
- Playwright Chromium E2E: 6 passed, 2 warnings.
- Python and JavaScript dependency audits: passed; no known vulnerabilities reported.

The CI workflow uses separate PostgreSQL services for the Python/API and E2E jobs. The test fixtures drop ORM tables at session teardown, so local tests must use disposable dedicated databases.

## Planned architecture

- Production-safe dashboard authentication/configuration.
- API-key rotation and external secret management.
- Gateway-level rate limiting and deployment network controls.
- Structured failure artifacts, metrics and distributed tracing.
- AI root-cause analysis and test-case suggestions, only after the deterministic foundation is sufficient.

No PCI DSS compliance or production payment capability is claimed.
