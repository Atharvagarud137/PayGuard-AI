# PayGuard-AI technology stack

**Status date: 20 November 2026.** Version ranges below come from the repository manifests. CI versions are noted separately; dependencies are not all pinned to one exact patch release.

## Backend and persistence

| Technology | Role | Status |
|---|---|---|
| Python | Backend and test language | Implemented; CI uses Python 3.12 |
| FastAPI | REST API and request validation | Implemented |
| Pydantic | Request/response models | Implemented |
| Uvicorn | ASGI server | Implemented |
| SQLAlchemy | ORM and database sessions | Implemented (`>=2.0,<3.0`) |
| psycopg 3 | PostgreSQL driver | Implemented (`>=3.2,<4.0`) |
| PostgreSQL | Durable payment, event, audit and idempotency state | Implemented; CI uses PostgreSQL 16 |
| Alembic | Schema migrations | Implemented; current migration head is `005_audit_reference_without_fk` |
| python-dotenv | Environment configuration dependency | Present in requirements |

The backend is a modular monolith. Payment services depend on repository interfaces; the active API wiring uses PostgreSQL repositories.

## Payment reliability components

| Component | Role | Status |
|---|---|---|
| Decimal monetary handling | Avoid binary floating-point money arithmetic | Implemented |
| Transaction state machine | Validate lifecycle transitions | Implemented |
| PostgreSQL row locks | Serialize card balance and transaction lifecycle mutations | Implemented and covered by PostgreSQL tests |
| Transaction-scoped advisory locks | Serialize requests sharing an idempotency key | Implemented |
| Idempotency records | Store request fingerprints and original responses | Implemented for authorization, capture, settlement and refund |
| Database constraints | Enforce selected monetary and relational invariants | Implemented |
| Audit hash chain | Sequence, previous hash and event hash | Implemented |
| Audit mutation triggers | Reject ordinary update/delete/truncate | Implemented |
| Failure simulation | Deterministic technical failures | Development/test only |

## Security components

Implemented controls include environment-driven settings, service/admin API-key checks, explicit CORS origins, test-only route gating, safe validation/unexpected-error responses, log/audit redaction, request-body limits and response security headers.

Not implemented: per-user identity/RBAC, tenant isolation, key rotation/revocation, an external secret manager, built-in rate limiting, HSM/tokenization, WAF, metrics and distributed tracing. HTTPS and gateway-level rate limiting are deployment responsibilities.

## Dashboard and frontend

| Technology | Role | Status |
|---|---|---|
| React | UI library | Implemented; package range `^19.2.8` |
| TypeScript | Frontend language | Implemented; package range `~6.0.2` |
| Vite | Development server and build | Implemented; package range `^8.3.8` |
| Oxlint | Dashboard lint script | Configured; not part of the current CI jobs |
| Node.js | Frontend runtime | CI uses Node.js 22 |

The dashboard has overview, cards and transaction views. Its API client currently hardcodes localhost and does not send `X-API-Key`, so it is a local development/test UI, not a production-ready authenticated console.

## Test and CI stack

| Technology | Role | Status |
|---|---|---|
| pytest | Unit and API/PostgreSQL integration tests | Implemented; requirement range `>=8,<10` |
| HTTPX / FastAPI TestClient | API calls and application tests | Implemented |
| Playwright + pytest-playwright | Chromium E2E automation | Implemented |
| GitHub Actions | Python/API, E2E and dependency-audit jobs | Implemented |
| pip-audit | Python dependency vulnerability audit | Implemented in CI |
| npm audit | Dashboard dependency vulnerability audit | Implemented in CI |

The latest verified CI run is [run #44243773973](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/44243773973), on 18 November 2026:

- Python unit/API: 143 passed, 1 warning.
- Playwright E2E: 6 passed, 2 warnings.
- Python and JavaScript dependency audits: passed; no known vulnerabilities reported.

Warnings include the Starlette TestClient/httpx deprecation, a pytest fixture deprecation, Node dependency deprecations and GitHub Actions Node-runtime deprecation notices.

## Not currently implemented

- AI RCA, LLM orchestration, embeddings, ChromaDB and AI test generation.
- OpenTelemetry tracing, metrics and structured failure-artifact storage.
- Runnable Docker/Compose deployment. The tracked Docker files are placeholders.
- Selenium automation. Playwright is the active browser test framework; Selenium is not in the current requirements.
- Production dashboard credential handling.

## Dependency policy

Use `requirements.txt` and `dashboard/package-lock.json` as the authoritative dependency inputs. CI installs the Python ranges from requirements and uses `npm ci` for the lockfile. Dependency audit results describe the state at the time of the run and must be refreshed regularly.

No PCI DSS compliance, production payment capability or regulatory certification is claimed.
