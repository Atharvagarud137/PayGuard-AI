# PayGuard-AI setup guide

**Status date: 15 November 2026.** This guide reflects the PostgreSQL-backed implementation and the current CI workflow.

## Requirements

| Tool | Version used by CI | Purpose |
|---|---:|---|
| Python | 3.12 | FastAPI and pytest |
| PostgreSQL | 16 | Application and test persistence |
| Node.js | 22 | Dashboard |
| npm | Bundled with Node.js | Dashboard dependencies |
| Playwright Chromium | Installed by Playwright | Browser E2E tests |

A local PostgreSQL server is required for the backend and test suites. The repository does not currently provide a working Docker Compose environment. The tracked Docker files are placeholders, not a supported setup path.

## Clone and install

From PowerShell:

```powershell
git clone https://github.com/Atharvagarud137/PayGuard-AI.git
cd PayGuard-AI

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

If PowerShell blocks activation, use the Python executable directly from `.venv\Scripts\python.exe` or adjust the local execution policy according to your organization's rules.

## Create local PostgreSQL databases

Create a local development database and separate disposable test databases using your PostgreSQL administrator account. For example:

```sql
CREATE ROLE payguard LOGIN PASSWORD 'replace-with-a-local-password';
CREATE DATABASE payguard OWNER payguard;
CREATE DATABASE payguard_api_test OWNER payguard;
CREATE DATABASE payguard_e2e_test OWNER payguard;
```

Use local-only credentials. Do not commit them or reuse production credentials.

The test fixtures create and drop ORM tables at session teardown. Use disposable test databases only. Do not point tests at a development or production database.

## Run the backend in local development mode

In a PowerShell terminal from the repository root:

```powershell
$env:PAYGUARD_ENV = "development"
$env:DATABASE_URL = "postgresql+psycopg://payguard:replace-with-a-local-password@localhost:5432/payguard"

alembic upgrade head
uvicorn app.main:app --reload --reload-dir app --port 8000
```

The local development mode permits keyless service access only when `PAYGUARD_API_KEY` is not configured. Do not use this mode as a production security configuration.

Available local endpoints:

- Health/liveness: `http://localhost:8000/`
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI: `http://localhost:8000/openapi.json`
- API base: `http://localhost:8000/api/v1`

The root endpoint is a basic liveness response. It does not prove PostgreSQL readiness.

## Run the dashboard

Open a second terminal:

```powershell
cd dashboard
npm ci
npm run dev
```

Vite serves the dashboard at `http://localhost:5173`.

To build it:

```powershell
npm run build
```

To run the configured linter:

```powershell
npm run lint
```

The dashboard API client currently hardcodes the local backend URL and does not send `X-API-Key`. It is therefore suitable only for a local development/test backend with no service key configured. Do not expose it as a production dashboard until an appropriate server-side credential flow is implemented. Never place a production API key in a browser-exposed `VITE_*` variable.

## Run Python unit and API tests

Use a dedicated API test database. Set both variables because pytest uses `TEST_DATABASE_URL` (or falls back to `DATABASE_URL`) while Alembic uses `DATABASE_URL`.

```powershell
$env:PAYGUARD_ENV = "test"
$env:DATABASE_URL = "postgresql+psycopg://payguard:replace-with-a-local-password@localhost:5432/payguard_api_test"
$env:TEST_DATABASE_URL = $env:DATABASE_URL

alembic upgrade head
pytest tests/unit tests/api -v --tb=short
```

The root pytest fixtures create ORM tables and drop them when the test session ends. The migrations must be applied first for tests that verify PostgreSQL triggers. Because the fixture drops the ORM tables while the Alembic version table may remain, recreate the disposable test database before repeating the migration/test cycle. Do not reuse this database for application development.

## Run Playwright E2E tests

The E2E suite uses a separate disposable database because the Python/API test fixture drops its schema at teardown.

In a backend terminal:

```powershell
$env:PAYGUARD_ENV = "test"
$env:PAYGUARD_ENABLE_TEST_ENDPOINTS = "true"
$env:PAYGUARD_TEST_RESET_TOKEN = "replace-with-at-least-32-random-test-characters"
$env:DATABASE_URL = "postgresql+psycopg://payguard:replace-with-a-local-password@localhost:5432/payguard_e2e_test"

alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd dashboard
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

From the repository root in a third terminal, use the same test-reset token:

```powershell
$env:PAYGUARD_ENV = "test"
$env:DATABASE_URL = "postgresql+psycopg://payguard:replace-with-a-local-password@localhost:5432/payguard_e2e_test"
$env:TEST_DATABASE_URL = $env:DATABASE_URL
$env:PAYGUARD_TEST_RESET_TOKEN = "replace-with-at-least-32-random-test-characters"

pytest tests/e2e -v --tb=short
```

The E2E fixture calls `POST /api/v1/test/reset` before each test. The backend must have the test-only route explicitly enabled and must use the same token. The reset endpoint is destructive and must never be enabled outside `PAYGUARD_ENV=test`.

## CI-equivalent commands

The GitHub Actions workflow separates the work into three jobs:

```powershell
# Python syntax and migration checks
python -m compileall -q app tests
alembic heads
alembic history
alembic upgrade head

# Python tests
pytest tests/unit tests/api -v --tb=short

# Dashboard build
cd dashboard
npm ci
npm run build

# Dependency audits
pip-audit -r requirements.txt
npm audit --audit-level=high
```

The E2E job also installs Chromium, starts the FastAPI backend and Vite dashboard, then runs `pytest tests/e2e -v --tb=short`.

## Production configuration checklist

Production settings default to fail closed:

- Set `PAYGUARD_ENV=production`.
- Set an explicit PostgreSQL `DATABASE_URL`.
- Set `PAYGUARD_API_KEY` and `PAYGUARD_ADMIN_API_KEY`, each at least 32 characters.
- Set explicit `PAYGUARD_CORS_ORIGINS`; wildcard origins are rejected.
- Keep `PAYGUARD_ENABLE_TEST_ENDPOINTS=false`.
- Do not configure the test reset token or enable failure simulation.
- Terminate HTTPS at a trusted ingress/reverse proxy and apply gateway-level rate limiting.
- Use a secret manager and define key rotation/revocation procedures.

The current dashboard is not production-compatible with API-key enforcement because its browser client does not send a service key. The project has no built-in per-user authentication/RBAC, rate limiter, HSM, tokenization, or PCI DSS assessment. Do not claim PCI DSS compliance.

## Troubleshooting

- **Database connection failure:** verify PostgreSQL is running, the database exists, the URL uses `postgresql+psycopg://`, and credentials are correct.
- **No such table / missing trigger:** run `alembic upgrade head` against the same database used by the process/test.
- **Tests hang or alter data:** confirm the URL points to a dedicated disposable test database, never a shared development database.
- **Dashboard cannot reach API:** confirm backend port 8000, Vite port 5173, and development CORS defaults.
- **401 from the API:** check `PAYGUARD_ENV` and whether a service key is configured. Send `X-API-Key` when a key is required.
- **E2E reset fails:** ensure test mode, test endpoints enabled, and the exact same reset token in backend and pytest processes.
