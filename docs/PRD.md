# PayGuard-AI product requirements

**Status date: 15 November 2026.**

## Product overview

PayGuard-AI is a portfolio engineering project that models a synthetic payment gateway and tests its reliability. It combines payment-domain logic, PostgreSQL persistence, API automation, browser automation and security-focused verification.

It is not a payment processor and does not connect to real card networks, banks, acquirers or production payment rails. The project must use synthetic data only. Real PAN and CVV/CVC data are out of scope and must not be submitted or stored.

## Product goals

| Goal | Status | Evidence / boundary |
|---|---|---|
| Model card and transaction lifecycle | Implemented | Authorization, capture, settlement, full/partial refund |
| Validate payment invariants | Implemented | Domain rules, SQL constraints and PostgreSQL tests |
| Durable state | Implemented | PostgreSQL repositories and Alembic migrations |
| Transaction atomicity | Implemented for tested mutation paths | Request-scoped DB transactions and rollback tests |
| Duplicate-request handling | Implemented for four mutations | PostgreSQL advisory lock, fingerprint and response replay |
| Audit traceability | Implemented | Persisted audit events, hash chain, integrity endpoint and DB mutation guards |
| API/unit automation | Implemented | Pytest |
| Browser automation | Implemented | Playwright Chromium |
| Security baseline | Implemented | Shared API keys, CORS, safe errors, redaction, request-size/header controls |
| CI and dependency checks | Implemented | GitHub Actions run #39 passed |
| AI RCA and test generation | Planned | No AI pipeline is implemented |
| Production deployment / PCI DSS compliance | Not claimed | Significant controls and independent assessment remain outside scope |

## Target audience

- QA Automation and SDET engineers.
- Backend and payment-domain engineers.
- Engineers reviewing API reliability, concurrency and database consistency.
- Recruiters and technical interviewers evaluating a portfolio project.

## In-scope functionality

### Payment simulation

- Generate synthetic card records with masked card identifiers.
- Authorize transactions, including deterministic declines.
- Capture authorized amounts.
- Settle captured transactions.
- Perform full and partial refunds.
- Inspect transaction status and lifecycle history.
- Inject deterministic technical failures in development/test environments only.

### Reliability

- Use decimal-safe money handling.
- Enforce lifecycle and amount invariants in the domain and database.
- Lock card rows for authorization balance changes.
- Lock transaction rows for capture, settlement and refund.
- Commit payment state, lifecycle events, audit records and idempotency response together on successful mutation paths.
- Replay completed responses for the same idempotency key and request; reject a different request with HTTP 409.

### Security baseline

- Require service and admin API keys outside the explicitly keyless development/test configurations.
- Keep destructive test reset disabled unless test mode and a separate reset token are configured.
- Reject wildcard CORS origins.
- Avoid echoing request values in validation errors and unexpected errors.
- Redact common payment-card and credential patterns from logs and audit fields.
- Limit request-body size and set conservative response headers.

## Non-goals

- Real card processing, acquiring, settlement networks or banking integrations.
- Storage or handling of real PAN, CVV/CVC or production cardholder data.
- PCI DSS certification or a claim of compliance.
- Full user identity, RBAC, tenant isolation or key lifecycle management.
- Production-grade rate limiting, WAF, HSM, tokenization or fraud detection.
- AI-generated decisions that approve, decline or mutate payments.

## Functional requirements and status

| Requirement | Status |
|---|---|
| Card issuance and lookup | Implemented for synthetic records |
| Authorization / capture / settlement / refund | Implemented |
| Transaction history and dashboard views | Implemented |
| Idempotency for authorization, capture, settlement and refund | Implemented |
| PostgreSQL persistence and migrations | Implemented |
| Concurrent balance/lifecycle protection | Implemented for tested paths |
| Persisted audit events and integrity verification | Implemented |
| Security and dependency regression tests | Implemented |
| AI RCA / test generation | Planned |

## Reliability acceptance criteria

The implementation should continue to demonstrate, through PostgreSQL tests:

1. Two concurrent authorizations cannot spend the same card balance twice.
2. Two captures of the same transaction cannot both apply the lifecycle transition.
3. Competing refunds cannot exceed the settled refundable amount.
4. A failed write after mutation flush rolls back the related payment state and associated records.
5. A repeated idempotency key with the same fingerprint replays the stored response.
6. A repeated key with a different fingerprint returns a conflict.
7. Concurrent duplicates create one committed mutation and one replay record in the tested scenarios.

These criteria describe tested scenarios, not a guarantee of exactly-once behavior under every failure mode.

## Security and privacy requirements

- Synthetic test data only.
- Do not add PAN/CVV fields to card-creation requests.
- Do not put secrets in source control or browser bundles.
- Production must provide explicit database and API-key configuration.
- HTTPS, secret rotation, deployment network controls and gateway rate limiting remain deployment responsibilities.
- Audit hash chaining is tamper-evident but not immutable against a database superuser.

## Verified test evidence

GitHub Actions [run #39](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/43557859045), associated with commit `c1be0651fd3503f12e06061755e39228f32950e0), completed successfully on 14 November 2026:

- 142 Python unit/API tests passed (1 warning).
- 6 Playwright E2E tests passed (2 warnings).
- `pip-audit` and `npm audit --audit-level=high` passed with no known vulnerabilities reported.

These are historical CI results for that commit. The documentation-only commit has its own CI run and must be checked separately.

## Roadmap

1. Finish the documentation sweep and final evidence review.
2. Resolve production dashboard credential flow without exposing secrets in browser code.
3. Add API-key rotation/revocation and external secret management.
4. Add deployment-level HTTPS, network controls and rate limiting.
5. Add metrics, tracing and structured failure artifacts.
6. Evaluate AI RCA and test suggestions after reliability/observability gaps are addressed.

No PCI DSS compliance, regulatory certification or production payment capability is claimed.
