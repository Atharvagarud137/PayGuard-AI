# SETUP.md — PayGuard AI

## Purpose

This document provides instructions for setting up PayGuard AI locally, running the Mock Payment Gateway, running the Web Dashboard, executing the complete automated test suite, and working with the current Playwright E2E test environment.

PayGuard AI is being developed incrementally. The current implementation contains the payment-domain foundation, transaction lifecycle, service layer, repository abstraction, audit functionality, idempotency handling, Web Dashboard, API tests, unit tests, and Playwright-based E2E coverage.

The current development baseline should be treated as a stable checkpoint before the next implementation phase.

The current setup focuses on:

- Reproducing the existing backend environment
- Running the Mock Payment Gateway
- Running the Web Dashboard
- Running unit and API tests
- Running Playwright E2E tests
- Maintaining deterministic synthetic test data
- Preserving the current layered architecture
- Verifying the complete regression suite before committing changes

PostgreSQL, Docker orchestration, AI/RCA infrastructure, CI/CD, and observability components remain planned capabilities unless explicitly implemented elsewhere in the repository.

---

# Prerequisites

| Requirement | Version / Configuration | Status |
|---|---|---|
| Python | 3.11.x | Required |
| Git | Current stable version | Required |
| Node.js | Current project-compatible version | Required for Dashboard |
| npm | Installed with Node.js | Required for Dashboard |
| IntelliJ IDEA / PyCharm | Current development environment | Recommended |
| Playwright | Installed through Python requirements | Required for E2E tests |
| Chromium | Playwright-managed browser | Required for current E2E tests |
| Docker Desktop | Current stable version | Planned |
| Ollama | Current stable version | Planned |
| PostgreSQL | Current supported version | Planned |

---

# Current Verified Backend Environment

The current backend environment has been verified with:

```text
Python 3.11.9
Pytest 9.1.1
FastAPI
HTTPX
Uvicorn
Pydantic
````

The project dependencies are defined in:

```text
requirements.txt
```

The current requirements include:

```text
fastapi
uvicorn
pydantic
pytest
httpx
selenium
langchain
langchain-community
chromadb
python-dotenv
```

Playwright is also required by the current E2E test suite and must be installed in the active Python environment.

Patch versions may change as dependency maintenance continues.

The current backend uses an in-memory storage implementation.

This means that application restarts clear runtime state including:

* Cards
* Transactions
* Transaction history
* Audit events
* Idempotency records

Do not treat the in-memory implementation as persistent production storage.

---

# Project Structure

The project currently follows a layered backend architecture with a separate React-based dashboard and automated test suite.

```text
PayGuard-AI/
│
├── app/
│   ├── domain/
│   ├── services/
│   ├── repositories/
│   ├── models/
│   ├── storage/
│   └── ...
│
├── dashboard/
│   └── ...
│
├── tests/
│   ├── api/
│   ├── unit/
│   └── e2e/
│       ├── components/
│       ├── pages/
│       ├── conftest.py
│       ├── test_cards.py
│       ├── test_dashboard_smoke.py
│       ├── test_transactions.py
│       └── ...
│
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── TEST_STRATEGY.md
│   ├── TECH_STACK.md
│   ├── API_SPEC.md
│   ├── AI_PIPELINE.md
│   ├── SETUP.md
│   └── playwright-vs-selenium-payguard-ai.md
│
├── .venv/
├── requirements.txt
├── README.md
├── playwright.config.py
└── ...
```

The exact directory structure may evolve as additional platform capabilities are introduced.

---

# Step 1: Clone the Repository

Clone the repository:

```powershell
git clone https://github.com/Atharvagarud137/PayGuard-AI.git
cd PayGuard-AI
```

If the repository has already been cloned:

```powershell
cd D:\Projects\PayGuard-AI
```

Verify the repository:

```powershell
git status
```

Verify the configured remote:

```powershell
git remote -v
```

The repository remote is:

```text
https://github.com/Atharvagarud137/PayGuard-AI.git
```

---

# Step 2: Create the Python Virtual Environment

Create a project-specific virtual environment:

```powershell
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Verify Python:

```powershell
python --version
```

Verify the Python executable:

```powershell
python -c "import sys; print(sys.executable)"
```

The executable should point to the project's virtual environment:

```text
D:\Projects\PayGuard-AI\.venv\Scripts\python.exe
```

## macOS / Linux

Create the environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

---

# Step 3: Install Backend Dependencies

Ensure the virtual environment is active.

Upgrade pip if required:

```powershell
python -m pip install --upgrade pip
```

Install project dependencies:

```powershell
pip install -r requirements.txt
```

Verify Pytest:

```powershell
pytest --version
```

Verify FastAPI:

```powershell
python -c "import fastapi; print(fastapi.__version__)"
```

Verify Uvicorn:

```powershell
uvicorn --version
```

---

# Step 4: Install Playwright

Playwright is used for the current browser-based E2E test suite.

Install the Python Playwright package if it is not already installed:

```powershell
pip install playwright
```

Install the Chromium browser:

```powershell
playwright install chromium
```

Verify Playwright:

```powershell
python -c "import playwright; print('Playwright installed successfully')"
```

The current E2E suite is configured to execute against Chromium.

---

# Step 5: Verify the Backend Environment

Before starting the application or running tests, verify:

```powershell
python --version
pytest --version
git status
```

Verify the Python executable:

```powershell
python -c "import sys; print(sys.executable)"
```

The path should point to:

```text
D:\Projects\PayGuard-AI\.venv\Scripts\python.exe
```

Do not commit:

* `.venv/`
* Generated logs
* Temporary files
* Cache directories
* Local environment files
* Generated test artifacts
* Unrelated IDE files

unless they are explicitly intended to be tracked.

---

# Step 6: Run the Mock Payment Gateway

The Mock Payment Gateway is implemented using FastAPI.

Start the backend with:

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8000
```

## Important: Use `--reload-dir app`

The project is located in a OneDrive-synchronized directory.

Avoid unrestricted:

```powershell
uvicorn app.main:app --reload
```

during development.

Instead use:

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8000
```

Restricting the reload watcher to `app/` prevents unrelated changes in `.venv/`, IDE metadata, synchronized files, and other project directories from triggering unnecessary application restarts.

This is particularly important because the current application uses in-memory storage.

An unintended restart clears:

* Cards
* Transactions
* Transaction history
* Audit events
* Idempotency records
* Other in-memory application state

---

# Step 7: Verify the API

With Uvicorn running, the root endpoint is:

```text
http://localhost:8000/
```

FastAPI Swagger UI:

```text
http://localhost:8000/docs
```

Raw OpenAPI specification:

```text
http://localhost:8000/openapi.json
```

API base path:

```text
http://localhost:8000/api/v1
```

The API exposes the implemented payment operations including:

```text
Card Issuance
     |
     v
Authorization
     |
     v
Capture
     |
     v
Settlement
     |
     v
Refund
```

Transaction lookup and transaction history are also available through the implemented transaction APIs.

---

# Step 8: Run the Backend Test Suite

The current automated test suite contains:

* API tests
* Unit tests
* Playwright E2E tests

The currently verified complete regression baseline is:

```text
96 tests
96 passed
0 failed
```

## Run the Complete Test Suite

From the project root:

```powershell
pytest -v
```

This is the primary regression command.

The complete suite should be run after changes affecting:

* Payment-domain logic
* Transaction lifecycle
* State machine
* Payment services
* Repository behavior
* Storage behavior
* API endpoints
* Request/response models
* Audit functionality
* Idempotency
* Dashboard behavior
* E2E Page Objects
* E2E fixtures
* Playwright configuration

---

# Run API Tests

```powershell
pytest tests/api -v
```

API tests cover payment gateway behavior including:

* Card issuance
* Authorization
* Capture
* Settlement
* Refunds
* Validation failures
* Invalid transaction states
* Boundary conditions
* Idempotency
* Audit events
* Simulated technical failures

---

# Run Unit Tests

Run the complete unit test suite:

```powershell
pytest tests/unit -v
```

Run payment service tests specifically:

```powershell
pytest tests/unit/test_payment_service.py -v
```

Run state machine tests:

```powershell
pytest tests/unit/test_state_machine.py -v
```

The state machine tests validate transaction lifecycle rules independently from the API and storage implementation.

---

# Step 9: Run Playwright E2E Tests

The current UI automation framework is **Playwright with Python and pytest**.

The E2E tests are located under:

```text
tests/e2e/
```

The current suite includes coverage for:

* Dashboard smoke validation
* Card issuance
* Transactions page
* Transaction empty state
* Authorized transaction visibility
* Transaction lifecycle dialog

Current E2E test files include:

```text
tests/e2e/test_dashboard_smoke.py
tests/e2e/test_cards.py
tests/e2e/test_transactions.py
```

Page Objects are maintained under:

```text
tests/e2e/pages/
```

Current Page Objects include:

```text
tests/e2e/pages/cards_page.py
tests/e2e/pages/dashboard_page.py
tests/e2e/pages/transactions_page.py
```

The E2E fixtures are defined in:

```text
tests/e2e/conftest.py
```

---

# E2E Environment Requirements

Playwright E2E tests require both the backend and frontend to be running.

## Backend

Start:

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8000
```

Backend URL:

```text
http://localhost:8000
```

## Frontend

From the Dashboard directory:

```powershell
cd dashboard
```

Install dependencies when required:

```powershell
npm install
```

Inspect available npm scripts:

```powershell
npm run
```

Use the development command defined by `dashboard/package.json`.

For a Vite-based development environment this is typically:

```powershell
npm run dev
```

The current E2E configuration expects the Dashboard at:

```text
http://localhost:5173
```

Therefore the normal local topology is:

```text
Frontend
http://localhost:5173
       |
       | HTTP
       v
FastAPI Backend
http://localhost:8000
```

---

# Run All E2E Tests

With both backend and frontend running:

```powershell
pytest tests\e2e -v
```

The current verified E2E baseline is:

```text
4 tests
4 passed
0 failed
```

The current E2E tests include:

```text
test_cards.py
    test_issue_card_successfully

test_dashboard_smoke.py
    test_dashboard_loads

test_transactions.py
    test_transactions_page_loads
    test_transactions_page_shows_empty_state
```

Additional transaction E2E coverage may be added as the workflow expands.

---

# Run Individual E2E Tests

Dashboard smoke test:

```powershell
pytest tests\e2e\test_dashboard_smoke.py -v
```

Card E2E tests:

```powershell
pytest tests\e2e\test_cards.py -v
```

Transaction E2E tests:

```powershell
pytest tests\e2e\test_transactions.py -v
```

Run one individual test:

```powershell
pytest tests\e2e\test_transactions.py::test_transactions_page_loads -v
```

---

# E2E Fixture Architecture

The E2E test suite uses fixtures defined in:

```text
tests\e2e\conftest.py
```

The current fixtures include:

```text
frontend_url
backend_url
dashboard_page
issued_e2e_card
authorized_transaction
```

The `issued_e2e_card` fixture creates a fresh active card through the backend API before tests that require a valid payment card.

The `authorized_transaction` fixture creates an authorized transaction through the backend API.

This approach gives UI tests deterministic backend state without requiring the browser to perform every prerequisite operation manually.

The general E2E flow is:

```text
pytest
  |
  v
E2E Fixture
  |
  +----> Create Card through API
  |
  +----> Authorize Transaction through API
  |
  v
Playwright Browser
  |
  v
Dashboard
  |
  v
Transactions Page
  |
  v
User-visible Assertions
```

This keeps E2E tests focused on frontend behavior rather than turning every test into a slow recreation of the entire payment workflow.

---

# Playwright Configuration

The project contains:

```text
playwright.config.py
```

This file belongs at the project root:

```text
D:\Projects\PayGuard-AI\playwright.config.py
```

The project does not currently rely on:

```text
pytest.ini
```

or:

```text
pyproject.toml
```

for the Playwright configuration.

The Python pytest Playwright plugin provides the browser fixture used by the E2E tests.

---

# Page Object Model

The E2E suite uses a Page Object Model.

Page Objects are stored under:

```text
tests/e2e/pages/
```

The purpose of Page Objects is to separate:

```text
Test Intent
    |
    v
Page Object
    |
    v
Playwright Locators
    |
    v
Application UI
```

Tests should describe user behavior and business expectations.

Selectors and page-specific interaction details should remain inside Page Objects whenever practical.

For example:

```python
transactions_page.open()
transactions_page.expect_page_loaded()
transactions_page.expect_empty_state()
```

rather than duplicating selectors throughout individual test functions.

---

# Locator Strategy

The current Playwright implementation prefers:

1. Accessible roles
2. Accessible names
3. Application semantics
4. Stable test identifiers
5. Stable CSS selectors where necessary

Examples include:

```python
page.get_by_role(
    "button",
    name=re.compile(r"Transactions$"),
)
```

and:

```python
page.get_by_role(
    "heading",
    name="Transactions",
    exact=True,
)
```

Dashboard health assertions also use application-level test identifiers such as:

```text
system-health
health-payment-gateway
health-payment-gateway-state
```

Avoid selectors based purely on generated CSS structure when a stable semantic locator exists.

---

# Transaction E2E Coverage

The transaction E2E tests currently validate:

## Transactions Page Loading

The test verifies:

* Transactions navigation is visible
* Transactions page can be opened
* Page heading is visible
* Page description is visible
* Transaction list panel is visible

## Empty State

When no transactions are available, the test verifies:

```text
No transactions yet
```

is visible.

## Authorized Transaction

An authorized transaction can be created through the backend API fixture and then verified through the Dashboard.

The test verifies:

* Transaction appears in the table
* Merchant ID is visible
* Transaction status is `AUTHORIZED`

## Transaction Lifecycle

The transaction lifecycle dialog can be opened from the transaction row.

The test verifies:

* The transaction row is visible
* `View Lifecycle` is available
* The lifecycle dialog opens
* The lifecycle dialog can be closed

---

# E2E Test Data

E2E tests use synthetic payment data.

Example card:

```text
Cardholder:
E2E Transaction User

Network:
VISA

Initial Balance:
5000
```

Example transaction:

```text
Amount:
100

Merchant:
e2e-merchant-001
```

The tests should never use:

* Real PANs
* Real CVVs
* Real payment credentials
* Real customer information
* Production authentication credentials

The project is a Mock Payment Gateway and is not a PCI-DSS-certified payment processing environment.

---

# Dashboard

The Dashboard is a separate frontend application located under:

```text
dashboard/
```

The expected local development URL is:

```text
http://localhost:5173
```

The Dashboard communicates with the backend through HTTP APIs.

The backend remains the source of truth for:

* Transaction state
* Payment business rules
* Lifecycle transitions
* Transaction persistence
* Domain validation
* Audit information

The frontend should primarily consume and present backend data.

It should not duplicate payment business rules.

---

# Dashboard Development

From the project root:

```powershell
cd dashboard
```

Install dependencies:

```powershell
npm install
```

Inspect available scripts:

```powershell
npm run
```

Start the development server using the script defined in:

```text
dashboard/package.json
```

For the current Vite development environment:

```powershell
npm run dev
```

The Dashboard should then be available at:

```text
http://localhost:5173
```

---

# Backend and Frontend Relationship

The intended local development topology is:

```text
┌────────────────────────────┐
│        Web Dashboard       │
│        Port 5173           │
└─────────────┬──────────────┘
              |
              | HTTP
              v
┌────────────────────────────┐
│      FastAPI Gateway       │
│        Port 8000           │
└─────────────┬──────────────┘
              |
              v
┌────────────────────────────┐
│      Payment Service       │
└─────────────┬──────────────┘
              |
              v
┌────────────────────────────┐
│ Payment Domain / State     │
│ Machine                    │
└─────────────┬──────────────┘
              |
              v
┌────────────────────────────┐
│ Transaction Repository     │
└─────────────┬──────────────┘
              |
              v
┌────────────────────────────┐
│     In-Memory Storage      │
└────────────────────────────┘
```

The Dashboard should communicate with the backend through the API rather than directly accessing application internals.

---

# Current Frontend Development Status

The current Dashboard implementation provides the foundation for:

* Overview
* Transactions
* Cards
* Payment operations
* System health
* Transaction lifecycle inspection

The current E2E suite verifies the implemented Dashboard behavior.

The current development checkpoint should be treated as a stable baseline before introducing the next major architectural capability.

---

# AI Environment

The AI layer is planned and is not required to run the current payment-domain regression suite.

The planned AI stack includes:

* LangChain
* LangGraph
* ChromaDB
* Ollama
* Local LLM
* Failure-log processing
* AI Root Cause Analysis
* AI test-case generation

These components should not be installed merely to run:

```powershell
pytest -v
```

unless the corresponding implementation requires them.

The intended AI flow is:

```text
Test Failure
     |
     v
Failure Context
     |
     v
Historical Failure Retrieval
     |
     v
Local LLM
     |
     v
RCA Summary
```

The planned AI Test Case Generator will eventually consume the FastAPI OpenAPI specification and produce reviewable test suggestions.

---

# Ollama

Ollama is part of the planned local AI environment.

When the AI pipeline is actively developed, verify installation:

```powershell
ollama --version
```

List installed models:

```powershell
ollama list
```

A model can be installed according to the model selected for the project.

For example:

```powershell
ollama pull llama3.1
```

The exact model should be finalized based on evaluation requirements and available local hardware.

Do not treat an installed Ollama model as evidence that the AI pipeline itself is implemented.

---

# Docker

Docker is planned for integrated local and CI environments.

The intended environment may eventually contain:

```text
Mock Payment Gateway
        |
        +-- PostgreSQL
        |
        +-- Web Dashboard
        |
        +-- ChromaDB
        |
        +-- Ollama
```

When the Docker Compose implementation is available, the expected command is:

```powershell
docker compose -f docker/docker-compose.yml up -d
```

Inspect running containers:

```powershell
docker ps
```

Stop the Compose environment:

```powershell
docker compose -f docker/docker-compose.yml down
```

Docker is not currently required for the core local regression workflow.

---

# Current Development Workflow

For backend changes:

## 1. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

## 2. Verify Python

```powershell
python --version
```

## 3. Start the backend when required

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8000
```

## 4. Start the Dashboard when required

From another terminal:

```powershell
cd dashboard
npm run dev
```

## 5. Run targeted tests

For unit tests:

```powershell
pytest tests/unit -v
```

For API tests:

```powershell
pytest tests/api -v
```

For E2E tests:

```powershell
pytest tests/e2e -v
```

## 6. Run the complete regression suite

```powershell
pytest -v
```

The current verified baseline is:

```text
96 passed
0 failed
```

## 7. Inspect the Git working tree

```powershell
git status
```

## 8. Review the actual diff

```powershell
git diff
```

## 9. Review the diff summary

```powershell
git diff --stat
```

## 10. Commit only verified changes

```powershell
git add .
git commit -m "describe the change"
```

## 11. Push the commit

```powershell
git push origin main
```

Do not commit a change simply because the application starts.

Payment software has a long and unfortunate history of technically functioning software behaving incorrectly.

---

# OneDrive-Specific Considerations

The project is currently located in a OneDrive-synchronized directory.

OneDrive synchronization may interfere with:

* File watchers
* Dependency installation
* Virtual-environment files
* Temporary files
* IDE indexing
* Uvicorn reload behavior
* Browser test artifacts

Potential symptoms include:

* Unexpected Uvicorn restarts
* File locking
* Slow dependency operations
* Changes appearing in Git unexpectedly
* In-memory transaction data disappearing
* Intermittent test behavior

If synchronization is interfering with development, temporarily pause OneDrive synchronization while performing the affected operation.

Resume synchronization afterward.

---

# Uvicorn Reload Configuration

The recommended development command is:

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8000
```

The important configuration is:

```text
--reload-dir app
```

This limits automatic reload monitoring to the backend application source.

Avoid:

```powershell
uvicorn app.main:app --reload
```

when the project is located inside the synchronized directory.

---

# Common Issues

## 1. Uvicorn repeatedly restarts

### Symptom

The FastAPI application restarts without intentional changes to application source files.

### Likely Cause

Uvicorn is monitoring `.venv`, IDE files, synchronized files, or other project directories.

### Solution

Use:

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8000
```

---

# 2. Card or transaction data disappears

### Symptom

Cards or transactions created during a session suddenly disappear.

### Cause

The current application uses in-memory storage.

Any application restart clears:

* Cards
* Transactions
* Transaction history
* Audit events
* Idempotency records

### Solution

Check the Uvicorn console for an unexpected restart.

Use:

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8000
```

Persistent database storage is a future architectural phase.

---

# 3. Tests fail after a code change

First run the affected test layer:

```powershell
pytest tests/unit -v
```

or:

```powershell
pytest tests/api -v
```

or:

```powershell
pytest tests/e2e -v
```

Then run:

```powershell
pytest -v
```

Do not consider a targeted test passing sufficient evidence that the complete payment lifecycle and UI regression suite remain correct.

---

# 4. Playwright browser is missing

### Symptom

Pytest detects the Playwright plugin but cannot launch Chromium.

### Solution

Run:

```powershell
playwright install chromium
```

Then verify:

```powershell
pytest tests/e2e -v
```

---

# 5. E2E tests cannot reach the Dashboard

### Symptom

Playwright tests fail while navigating to:

```text
http://localhost:5173
```

### Solution

Verify that the frontend is running.

From the Dashboard directory:

```powershell
cd dashboard
npm run dev
```

Confirm that the Dashboard is accessible at:

```text
http://localhost:5173
```

---

# 6. E2E tests cannot reach the backend

### Symptom

E2E fixtures fail while creating cards or transactions through the API.

### Solution

Verify that the backend is running:

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8000
```

Then verify:

```text
http://localhost:8000/
```

and:

```text
http://localhost:8000/docs
```

The E2E fixtures use:

```text
http://localhost:8000
```

as the backend URL.

---

# 7. Transactions E2E tests fail because no transaction exists

Transaction E2E tests that require backend state use the fixture:

```text
authorized_transaction
```

This fixture creates:

1. A fresh active E2E card
2. An authorized transaction against that card

The fixture uses:

```text
Merchant:
e2e-merchant-001

Amount:
100
```

If the fixture fails, inspect the backend first.

Do not manually create random application state and assume the test is broken. Humans have enough ways to create mysterious state already.

---

# 8. Git reports unexpected changes

Check:

```powershell
git status
```

Then inspect:

```powershell
git diff
```

Do not blindly commit changes produced by:

* OneDrive
* IDEs
* Build tools
* Test execution
* Dependency installation
* Temporary scripts
* Generated browser artifacts

---

# 9. Virtual environment is not active

Verify:

```powershell
python -c "import sys; print(sys.executable)"
```

The path should point to:

```text
D:\Projects\PayGuard-AI\.venv\Scripts\python.exe
```

If it does not:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

# 10. Port 8000 is already in use

Check which process is using port 8000:

```powershell
netstat -ano | findstr :8000
```

If another development server is running, stop it before starting another Uvicorn instance.

Alternatively:

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8001
```

If the Dashboard expects port 8000, update its API configuration accordingly.

---

# 11. Port 5173 is already in use

Check the frontend development server or other process occupying the port.

On Windows:

```powershell
netstat -ano | findstr :5173
```

If the Vite development server selects another port, the E2E fixture configuration must be updated to match the actual frontend URL.

The current expected frontend URL is:

```text
http://localhost:5173
```

---

# 12. Dashboard cannot reach the API

Verify that the backend is running:

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8000
```

Then verify:

```text
http://localhost:8000/
```

and:

```text
http://localhost:8000/docs
```

If the backend is available but the Dashboard cannot communicate with it, inspect:

* Frontend API base URL
* Browser console errors
* Network requests
* CORS configuration
* Backend terminal logs

Do not modify backend payment logic to solve a frontend configuration problem.

---

# 13. Dashboard dependency installation fails

From the Dashboard directory:

```powershell
cd dashboard
```

Check Node.js:

```powershell
node --version
```

Check npm:

```powershell
npm --version
```

Install dependencies:

```powershell
npm install
```

Inspect available scripts:

```powershell
npm run
```

Then use the script defined by the project.

---

# 14. Test count changes

The current verified regression baseline is:

```text
96 tests
96 passed
0 failed
```

The test count may increase as new functionality is implemented.

A changed test count is not automatically a problem.

When tests are added, removed, renamed, or reorganized, update the relevant documentation so that the documented baseline remains consistent with the actual repository.

---

# Environment Variables

The current payment gateway does not require production credentials or external service secrets to run the core regression suite.

Do not place secrets directly into source files.

If environment variables are introduced in future phases, use a local environment file excluded from Git:

```text
.env
```

Never commit:

* API keys
* Passwords
* Database credentials
* LLM provider credentials
* Production payment credentials
* Real cardholder data

The Mock Payment Gateway should continue to use synthetic non-production data.

---

# Test Data Requirements

The current test environment should use deterministic, synthetic payment data.

Never use:

* Real PANs
* Real CVVs
* Production card credentials
* Real customer payment information
* Production authentication credentials

The project is a Mock Payment Gateway and is not a PCI-DSS-certified payment processing environment.

---

# Verification Checklist

Use this checklist when setting up or restoring the development environment.

## Core Environment

* [ ] Python 3.11.x installed
* [ ] Git installed
* [ ] Repository cloned
* [ ] `.venv` created
* [ ] `.venv` activated
* [ ] Python executable verified
* [ ] Backend dependencies installed
* [ ] Pytest available
* [ ] Playwright installed
* [ ] Chromium installed through Playwright

## Backend

* [ ] FastAPI starts successfully
* [ ] Uvicorn uses `--reload-dir app`
* [ ] `http://localhost:8000/` responds
* [ ] `http://localhost:8000/docs` loads
* [ ] `http://localhost:8000/openapi.json` loads

## Dashboard

* [ ] Node.js installed
* [ ] npm available
* [ ] Dashboard dependencies installed
* [ ] Dashboard starts successfully
* [ ] Dashboard available at `http://localhost:5173`
* [ ] Dashboard can reach the FastAPI backend

## Tests

* [ ] Unit tests pass
* [ ] API tests pass
* [ ] E2E tests pass
* [ ] Complete regression suite passes
* [ ] Current baseline is verified as `96 passed`

## E2E

* [ ] Chromium installed
* [ ] Backend running on port 8000
* [ ] Dashboard running on port 5173
* [ ] Dashboard smoke test passes
* [ ] Card E2E test passes
* [ ] Transactions E2E tests pass
* [ ] Transaction lifecycle E2E coverage passes

## Future Components

* [ ] PostgreSQL configured
* [ ] Docker configured
* [ ] Ollama configured
* [ ] ChromaDB configured
* [ ] AI RCA pipeline configured
* [ ] AI Test Case Generator configured
* [ ] CI/CD configured
* [ ] OpenTelemetry configured

---

# Current Project State

The current development baseline consists of:

```text
Python 3.11
    |
    +-- FastAPI
    |
    +-- Pydantic
    |
    +-- Uvicorn
    |
    +-- Pytest
    |
    +-- Playwright
    |
    +-- In-Memory Storage
    |
    +-- Web Dashboard
    |
    +-- API Tests
    |
    +-- Unit Tests
    |
    +-- E2E Tests
```

The backend architecture is:

```text
FastAPI
    |
    v
Payment Service
    |
    v
Payment Domain / State Machine
    |
    v
Repository Layer
    |
    v
In-Memory Storage
```

The current E2E architecture is:

```text
pytest
    |
    v
Playwright
    |
    v
Page Objects
    |
    v
Dashboard
    |
    v
FastAPI API
```

The current verified regression baseline is:

```text
96 tests
96 passed
0 failed
```

The broader planned architecture is:

```text
Current Payment Foundation
        |
        v
Payment Reliability
        |
        v
Persistent Storage
        |
        v
UI + Playwright
        |
        v
AI RCA + Test Generation
        |
        v
Docker + CI/CD
        |
        v
Observability + Security Hardening
```

The project should move to each future phase only when its requirements, implementation, tests, and documentation are aligned.

---

# Documentation References

The project documentation is organized as follows:

| Document                                     | Purpose                                            |
| -------------------------------------------- | -------------------------------------------------- |
| `docs/PRD.md`                                | Product requirements, scope, and success criteria  |
| `docs/ARCHITECTURE.md`                       | System architecture and component interactions     |
| `docs/TEST_STRATEGY.md`                      | Testing strategy and regression approach           |
| `docs/TECH_STACK.md`                         | Technology choices and architectural justification |
| `docs/API_SPEC.md`                           | Mock Payment Gateway API contract                  |
| `docs/AI_PIPELINE.md`                        | Planned AI RCA and test-generation architecture    |
| `docs/SETUP.md`                              | Local development and environment setup            |
| `docs/playwright-vs-selenium-payguard-ai.md` | Playwright vs Selenium evaluation for PayGuard AI  |

These documents should remain consistent with the actual implementation.

A planned capability should not be documented as implemented merely because its directory, dependency, or placeholder exists.

---

# Stopping Services

## Stop Uvicorn

In the terminal running the backend, press:

```text
CTRL + C
```

This stops the FastAPI development server.

Because the current application uses in-memory storage, stopping or restarting the backend clears runtime payment data.

---

## Stop the Dashboard

Stop the frontend development process using:

```text
CTRL + C
```

in the terminal running the Dashboard.

---

## Stop Docker Services

When Docker Compose is being used:

```powershell
docker compose -f docker/docker-compose.yml down
```

To remove orphaned containers:

```powershell
docker compose -f docker/docker-compose.yml down --remove-orphans
```

Docker is currently not required for the core local regression suite.

---

# Final Development Verification

Before considering a change complete, run:

```powershell
pytest -v
```

The current verified baseline is:

```text
96 passed
0 failed
```

Then inspect:

```powershell
git status
```

Review the complete diff:

```powershell
git diff
```

Review the summary:

```powershell
git diff --stat
```

The repository should contain only intentional changes.

The project should be left in a reproducible state before development is paused again.

The desired baseline is:

```text
Application Code
       +
Tests
       +
Documentation
       +
Git History
       |
       v
Consistent Development Baseline
```



