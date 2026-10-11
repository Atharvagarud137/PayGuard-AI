# Audit: public GitHub repo vs. this local checkout

**Question answered:** is the public repo behind the local code, and did the chat's final review
describe GitHub accurately?

**Method:** compared the local checkout against an independent shallow clone of
`https://github.com/Atharvagarud137/PayGuard-AI` (what a public consumer actually sees), plus the
remote-tracking ref, tracked-file inventory, and file-level assertions checked directly rather than
recalled.

**Result: the public repo is not behind. It is the same commit — and the chat's review was working
from a wrong inference.**

---

## 1. Local and public are identical

| Check | Result |
| --- | --- |
| Local `HEAD` | `1beef880b21ecfcb4e80fd9e7f81b101e03d2270` |
| `git ls-remote origin main` | `1beef880b21ecfcb4e80fd9e7f81b101e03d2270` |
| Fresh `git clone --depth 1` of the public URL | `1beef880b21ecfcb4e80fd9e7f81b101e03d2270` |
| Tracked file inventory, local vs public | **identical — 96 files, zero differences** |
| Local-only content | only untracked `.freebuff/` and `docs/reference/` |

There is exactly one branch (`main`) and no divergence. Nothing has been committed locally without
being pushed, and nothing on `main` is missing locally.

### Why this matters

The chat's second review inferred:

> `LOCAL DEVELOPMENT STATE > PUBLIC DOCUMENTATION STATE`

and described the repository as suffering from *"documentation-to-implementation drift"* in the sense
of a public snapshot lagging newer local work. **That inference is falsified.** The drift is
**documentation vs. code**, and it is committed and public in both places at the same commit. The
README, `docs/ARCHITECTURE.md`, `docs/TECH_STACK.md` and `docs/PRD.md` describe an in-memory system
while the code behind them is PostgreSQL-backed — and that contradiction is published, not local.

This matters because it changes the fix. There is nothing to "push up". Phase 0 is purely an
**edit-the-documentation** task.

The 230 MB `PayGuard-AI.zip` remains unverified (it was never extractable in the original session).
Given the trees are identical, the most likely explanation for its size is `dashboard/node_modules`
and/or `.venv` bundled in — but that is a hypothesis, and this document does not treat it as fact.

---

## 2. The chat's claims about GitHub, re-verified against the repo

Each claim from the review was checked in the public clone rather than trusted.

| Claim from the chat | Verified? | Evidence |
| --- | --- | --- |
| `.github/workflows/ci.yml` is 0 bytes | ✅ true | 0 bytes in the clone |
| `requirements.txt` unpinned; still lists `selenium`, `langchain`, `langchain-community`, `chromadb` | ✅ true | contents match, no version pins |
| README reports a stale 96-test baseline | ✅ true | `README.md` lines 61, 223–224, 237, 893, 1296 |
| README says PostgreSQL / Concurrency / CI/CD / Docker are "Planned" | ✅ true | `README.md` status table |
| Docs describe in-memory storage as the current implementation | ✅ true | `docs/ARCHITECTURE.md:116,125`; `docs/TECH_STACK.md:31,45`; `docs/PRD.md:814` |
| Repo tree contains `alembic/`, `docker/`, `ai_engine/` | ✅ true | top-level listing |
| ZIP contents could not be inspected | ✅ true, and still true | not extractable then; not attempted here |

So the review's *findings* were accurate. What was wrong was its *framing* of local vs. public.

---

## 3. New findings the chat's review missed

These were found by checking assertions against the tree rather than reviewing prose.

### 3.1 The API is now fully PostgreSQL-backed — and the documented test command cannot work without a database

`app/main.py` no longer uses the in-memory storage for requests. Every route depends on a database
session and constructs `Postgres*` repositories:

```text
app/main.py:15   from app.database import get_db
app/main.py:97   db: Session = Depends(get_db)     → PostgresTransactionRepository(db)
app/main.py:117  db: Session = Depends(get_db)     → PostgresAuditRepository(db)
app/main.py:131  db: Session = Depends(get_db)     → PostgresIdempotencyRepository(db)
app/main.py:460  db: Session = Depends(get_db)     → PostgresCardRepository(db)
app/main.py:523+ authorize / capture / settle / refund wired the same way
```

The API tests drive the app through `TestClient(app)` (`tests/api/conftest.py:8`), so they inherit
that dependency. **Observed behaviour:** `pytest tests/api` does not fail — it *hangs*. Captured with
`faulthandler`:

```text
File ".../psycopg/waiting.py", line 114 in wait_conn
File ".../psycopg/connection.py", line 109 in connect
File ".../sqlalchemy/engine/create.py", line 667 in connect
... ORM session._connection_for_bind → _execute_internal
```

The request blocks in `psycopg.wait_conn` waiting on a socket, because nothing is listening on the
target. `pytest tests/api/test_audit.py -x` was killed at 90 s (exit 124); the first single test was
killed at 25 s with the same stack.

Two consequences worth fixing regardless of documentation:

1. **The README's `pytest -v → 96 passed in 11.50s` cannot be reproduced on a machine without
   PostgreSQL.** No document mentions that a database is now required to run the test suite.
2. `app/database.py` builds the engine from `DATABASE_URL` (default
   `postgresql+psycopg://payguard:payguard@localhost:5432/payguard`) with **no `connect_timeout` and
   no pool pre-ping configuration**, so an unreachable database produces an indefinite hang instead of
   a fast, clear failure. For a project about trustworthy tests, a suite that silently hangs is the
   more expensive bug of the two.

### 3.2 98 tests collect, not 96

```text
pytest --collect-only -q  →  98 tests collected
    tests/unit + tests/api  →  92
    tests/e2e               →   6   (needs frontend :5173 and backend :8000)
```

Consistent with the chat's later internal count of 98, and incompatible with the README's 96.

### 3.3 Empty files beyond `ci.yml`

All 0-byte tracked files that are **not** `__init__.py` package markers:

| File | Notes |
| --- | --- |
| `.github/workflows/ci.yml` | already known |
| `docker/Dockerfile` | **new** — 0 bytes |
| `docker/docker-compose.yml` | **new** — 0 bytes (no content at all) |
| `app/failure_simulation.py` | **new** — and never imported anywhere in the repository |
| `tests/e2e/pages/dashboard_page.py` | **new** — orphan; the `dashboard_page` used by the tests is a Playwright `page` *fixture* in `tests/e2e/conftest.py:62`, not this module |

The `docker/` directory therefore advertises containerisation in the repo tree while containing two
empty files — the same pattern as the empty CI workflow.

### 3.4 `pytest.ini` is documented but absent

`README.md:1673` lists `pytest.ini` in the project-structure diagram. No `pytest.ini` exists at the
repository root (only `playwright.config.py`, `alembic.ini`, `requirements.txt`). The README's tree
diagram also shows `app/domain/state_machine/` and `app/services/payment_service/` as packages and
omits every `postgres_*` repository.

### 3.5 `selenium` has no tests, and `tests/ui/` is a dead directory

`tests/ui/` contains only `__init__.py` — zero tests — while `selenium` remains a mandatory
dependency in `requirements.txt`. Playwright is the actual E2E stack in use.

### 3.6 Duplicate commit message in published history

`1beef88` and `51f412c` are both titled *"Add PostgreSQL persistence foundation"*. Both are on
`main` and therefore public.

---

## 4. What could NOT be verified

Stated plainly rather than assumed:

- **Whether the 92 unit/API tests actually pass against a live PostgreSQL.** Not attempted-to-green:
  the Docker daemon is not running (`npipe:////./pipe/dockerDesktopLinuxEngine` unavailable),
  `docker/docker-compose.yml` is empty so there is no container definition to bring up, and nothing
  is listening on port 5432. **No green baseline is claimed for this repository in its current
  state.** The README's 96/98-passed figures are stale documentation, not a verified result.
- **Whether the 6 E2E tests pass**, which requires a running frontend and backend.
- **The contents of `PayGuard-AI.zip`.**

---

## 5. Recommended order

1. **Make the database unreachable fail fast** — add a connect timeout, then decide whether the API
   suite gets its own database-backed fixtures or a database-free in-memory seam. A hanging suite is
   worse than a red one.
2. **Phase 0 documentation reconciliation** — README, `ARCHITECTURE.md`, `TECH_STACK.md`, `PRD.md`,
   milestone status, test count, and the project-structure diagram. The code is not ahead of the
   docs and the docs are not ahead of a push; the docs are simply wrong, publicly.
3. **Decide the fate of the empty placeholders** — `ci.yml`, `docker/Dockerfile`,
   `docker/docker-compose.yml`, and the two orphan modules. Either implement them or remove them;
   a repository arguing for reliability cannot ship empty artifacts that imply capability.
4. **Split AI dependencies** out of the mandatory requirements and pin versions.

None of the above is a code-architecture problem. It is the "maturity synchronisation" the review
identified — now confirmed to be a public, committed condition rather than a local one.
