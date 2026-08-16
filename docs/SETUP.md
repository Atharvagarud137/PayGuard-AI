# SETUP.md — PayGuard AI

## Purpose

This document provides instructions for setting up PayGuard AI locally, running the Mock Payment Gateway, executing the automated test suite, and working with the Web Dashboard.

PayGuard AI is being developed incrementally. The current implementation has established the payment-domain foundation, transaction lifecycle, service layer, repository abstraction, automated regression suite, and the initial Web Dashboard.

At the current project stage, active development of the backend and frontend is temporarily paused. The implemented code and documentation are retained as the baseline for the next development phase.

The current setup therefore focuses on:

- Reproducing the existing backend environment
- Running the Mock Payment Gateway when required
- Running the existing automated regression suite
- Inspecting the Web Dashboard when required
- Maintaining a clean and reproducible development environment
- Preserving the current architecture before the next implementation phase

PostgreSQL, AI/RCA infrastructure, Docker orchestration, CI/CD, and other planned platform components are not required for the current baseline.

---

# Prerequisites

| Requirement | Version / Configuration | Status |
|---|---|---|
| Python | 3.11.x | Required |
| Git | Current stable version | Required |
| IntelliJ IDEA / PyCharm | Current development environment | Recommended |
| Node.js / npm | Required when working on the Dashboard | Required for frontend development |
| Docker Desktop | Current stable version | Planned |
| Ollama | Current stable version | Planned |
| PostgreSQL | Current supported version | Planned |

## Current Verified Backend Environment

The current backend environment has been verified with:

```text
Python 3.11.9
Pytest 9.1.1
FastAPI 0.141.1
Starlette 1.6.0
HTTPX 0.28.1
Uvicorn 0.52.1
Pydantic 2.13.4
````

Patch versions may change as dependency maintenance continues.

The current backend uses an in-memory storage implementation.

---

# Project Structure

The project currently follows a layered backend architecture with a separate dashboard.

```text
PayGuard-AI/
│
├── app/
│   ├── domain/
│   ├── services/
│   ├── repositories/
│   └── ...
│
├── tests/
│   ├── api/
│   └── unit/
│
├── dashboard/
│   └── ...
│
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── TEST_STRATEGY.md
│   ├── TECH_STACK.md
│   ├── API_SPEC.md
│   ├── AI_PIPELINE.md
│   └── SETUP.md
│
├── .venv/
├── requirements.txt
└── ...
```

The exact directory structure may evolve as new platform components are introduced.

---

# Step 1: Clone the Repository

Clone the repository:

```powershell
git clone https://github.com/Atharvagarud137/PayGuard-AI.git
cd PayGuard-AI
```

If the repository has already been cloned, navigate to the project directory:

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

The executable should point to the project's virtual environment, for example:

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

The exact dependency versions may change as the project evolves.

---

# Step 4: Verify the Backend Environment

Before running the application or tests, verify:

```powershell
python --version
pytest --version
git status
```

The Python interpreter should belong to `.venv`.

The Git working tree should be inspected before making changes:

```powershell
git status
```

Do not commit:

* `.venv/`
* Generated logs
* Temporary files
* Cache directories
* Local environment files
* Generated test artifacts
* Unrelated IDE files

unless they are explicitly intended to be tracked by the project.

---

# Step 5: Run the Mock Payment Gateway

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

Instead, use:

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8000
```

Restricting the reload watcher to `app/` prevents unrelated changes in `.venv/`, IDE metadata, synchronized files, and other project directories from triggering unnecessary application restarts.

This is particularly important because the current application uses in-memory storage.

An unintended restart clears:

* Cards
* Transactions
* Transaction history
* Other in-memory application state

---

# Step 6: Verify the API

With Uvicorn running, the root endpoint is:

```text
http://localhost:8000/
```

The FastAPI Swagger UI is available at:

```text
http://localhost:8000/docs
```

The raw OpenAPI specification is available at:

```text
http://localhost:8000/openapi.json
```

The API base path is:

```text
http://localhost:8000/api/v1
```

The Swagger UI should expose the currently implemented payment operations.

These include the core payment lifecycle:

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

Transaction lookup is also available for inspecting transaction state and history.

---

# Step 7: Run the Automated Test Suite

The current automated test architecture contains three implemented layers:

```text
State Machine Tests
        |
        v
Payment Service Tests
        |
        v
API Tests
```

The current documented regression baseline is:

```text
64 tests
64 passed
0 failed
```

## Run the Complete Regression Suite

From the project root:

```powershell
pytest -v
```

This is the primary regression command.

Run the complete suite after changes affecting:

* Payment-domain logic
* Transaction lifecycle
* State machine
* Payment service
* Repository behavior
* API endpoints
* Request/response models
* Transaction history

---

# Run API Tests

```powershell
pytest tests/api -v
```

Current documented API baseline:

```text
36 tests
```

The API tests cover payment gateway behavior including:

* Card issuance
* Authorization
* Capture
* Settlement
* Refunds
* Validation failures
* Invalid transaction states
* Boundary conditions
* Simulated technical failures

---

# Run Payment Service Tests

```powershell
pytest tests/unit/test_payment_service.py -v
```

Current documented baseline:

```text
14 tests
```

These tests validate payment business logic independently of FastAPI and HTTP behavior.

---

# Run State Machine Tests

```powershell
pytest tests/unit/test_state_machine.py -v
```

Current documented baseline:

```text
14 tests
```

These tests validate transaction lifecycle rules independently from the API and storage implementation.

---

# Current Regression Baseline

| Test Layer      |  Tests | Expected Result          |
| --------------- | -----: | ------------------------ |
| API             |     36 | Passing                  |
| Payment Service |     14 | Passing                  |
| State Machine   |     14 | Passing                  |
| **Total**       | **64** | **64 Passed / 0 Failed** |

The 64-test baseline represents the currently documented regression suite.

When new functionality is added, the test count is expected to increase.

The important requirement is that the full regression suite remains green.

---

# Step 8: Web Dashboard

The project contains a Web Dashboard intended to provide a visual interface for payment transaction monitoring and future Selenium automation.

The dashboard is currently treated as a separate frontend application from the FastAPI backend.

The dashboard is intended to provide visibility into concepts such as:

* Payment transactions
* Transaction status
* Transaction details
* Transaction lifecycle
* Transaction history
* Payment cards
* System information
* AI-related functionality planned for later phases

The transaction lifecycle displayed by the dashboard follows the backend payment-domain model.

```text
AUTHORIZED
     |
     v
CAPTURED
     |
     v
SETTLED
     |
     +----------------------+
     |                      |
     v                      v
PARTIALLY_REFUNDED      REFUNDED
     |
     v
REFUNDED
```

The Dashboard should not become a second implementation of payment business rules.

The backend remains the source of truth for:

* Transaction state
* Payment business rules
* Lifecycle transitions
* Transaction persistence
* Domain validation

The frontend should primarily consume and present backend data.

---

# Current Frontend Development Status

Frontend and backend development are currently paused.

This does not mean the existing implementation should be removed.

The current state should be treated as a stable development checkpoint.

```text
Implemented Backend
        |
        v
Implemented Dashboard Foundation
        |
        v
Documentation Updated
        |
        v
Development Paused
```

The purpose of the pause is to preserve the current architecture and establish a clean baseline before introducing the next major architectural capability.

The next implementation phase should be selected deliberately rather than adding functionality simply because the project has empty roadmap boxes.

---

# Running the Dashboard

The exact frontend startup command depends on the dashboard's package configuration.

From the dashboard directory:

```powershell
cd dashboard
```

Install frontend dependencies when required:

```powershell
npm install
```

Then use the development script defined in `dashboard/package.json`.

Typically this will be:

```powershell
npm run dev
```

or:

```powershell
npm start
```

Use the command actually defined in `package.json` rather than assuming a framework-specific command.

To inspect the available scripts:

```powershell
npm run
```

The frontend should be treated independently from the FastAPI process.

---

# Backend and Frontend Relationship

The intended local development topology is:

```text
┌──────────────────────────┐
│      Web Dashboard       │
│       Frontend           │
└────────────┬─────────────┘
             |
             | HTTP
             v
┌──────────────────────────┐
│     FastAPI Gateway      │
│       Port 8000          │
└────────────┬─────────────┘
             |
             v
┌──────────────────────────┐
│    Payment Service       │
└────────────┬─────────────┘
             |
             v
┌──────────────────────────┐
│   Payment Domain /       │
│   Transaction State      │
└────────────┬─────────────┘
             |
             v
┌──────────────────────────┐
│ Transaction Repository   │
└────────────┬─────────────┘
             |
             v
┌──────────────────────────┐
│    In-Memory Storage     │
└──────────────────────────┘
```

The Dashboard should communicate with the backend through the API rather than directly accessing application internals.

---

# Step 9: UI Automation

Selenium is part of the planned test automation architecture.

When the UI test suite is implemented, the expected command is:

```powershell
pytest tests/ui -v
```

The Dashboard and Mock Payment Gateway will need to be running for tests that depend on live services.

Planned UI coverage includes:

* Dashboard availability
* Transaction listing
* Transaction lookup
* Transaction status
* Transaction lifecycle visibility
* Transaction history
* Card visibility
* Error-state presentation
* User-visible payment workflow behavior

UI tests should validate user-visible behavior rather than duplicate the complete API regression suite.

---

# Step 10: AI Environment

The AI layer is planned but is not required for the current payment-domain baseline.

The planned AI stack includes:

* LangChain
* LangGraph
* ChromaDB
* Ollama
* Local LLM
* Failure-log processing
* AI Root Cause Analysis
* AI test-case generation

These components should not be installed merely to run the current backend regression suite.

The intended architecture is:

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

The AI Test Case Generator will eventually consume the FastAPI OpenAPI specification and generate reviewable test suggestions.

---

# Ollama

Ollama is part of the planned local AI environment.

When the AI pipeline is actively developed, verify the installation:

```powershell
ollama --version
```

A model can then be installed according to the model selected for the project.

For example:

```powershell
ollama pull llama3.1
```

List installed models:

```powershell
ollama list
```

The exact model should be finalized based on the evaluation requirements and available local hardware.

Do not treat an installed Ollama model as evidence that the AI pipeline itself is implemented.

---

# Step 11: Docker

Docker is planned for integrated local and CI environments.

The intended environment will eventually contain services such as:

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

When the Docker Compose implementation exists, the expected command will be:

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

Docker is not currently required for the documented 64-test backend regression suite.

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

## 3. Make the change

Keep payment-domain logic separated from:

* FastAPI routing
* HTTP-specific behavior
* Storage implementation details

## 4. Run targeted tests

For service changes:

```powershell
pytest tests/unit/test_payment_service.py -v
```

For state-machine changes:

```powershell
pytest tests/unit/test_state_machine.py -v
```

For API changes:

```powershell
pytest tests/api -v
```

## 5. Run the complete regression suite

```powershell
pytest -v
```

## 6. Inspect the Git working tree

```powershell
git status
```

## 7. Review the actual diff

```powershell
git diff
```

## 8. Commit only verified changes

```powershell
git add .
git commit -m "describe the change"
```

## 9. Push the commit

```powershell
git push origin main
```

Do not commit a change simply because the application starts. Payment software has a long and unfortunate history of technically functioning software behaving incorrectly.

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

Potential symptoms include:

* Unexpected Uvicorn restarts
* File locking
* Slow dependency operations
* Changes appearing in Git unexpectedly
* In-memory transaction data disappearing

If synchronization is interfering with development, temporarily pause OneDrive synchronization while performing the affected operation.

Resume synchronization afterward.

---

# Uvicorn Reload Configuration

The recommended development command is:

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8000
```

The important part is:

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

### Likely cause

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
* Other in-memory state

An unintended Uvicorn reload can therefore appear to be a payment-data problem.

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
pytest tests/unit/test_payment_service.py -v
```

or:

```powershell
pytest tests/api -v
```

or:

```powershell
pytest tests/unit/test_state_machine.py -v
```

Then run:

```powershell
pytest -v
```

Do not consider a targeted test passing sufficient evidence that the complete payment lifecycle remains correct.

---

# 4. Git reports unexpected changes

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

---

# 5. Virtual environment is not active

Verify:

```powershell
python -c "import sys; print(sys.executable)"
```

The path should point to:

```text
D:\Projects\PayGuard-AI\.venv\Scripts\python.exe
```

If it does not, activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

# 6. Port 8000 is already in use

Check which process is using port 8000:

```powershell
netstat -ano | findstr :8000
```

If another development server is running, stop it before starting another Uvicorn instance.

Alternatively, run the application on another port:

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8001
```

If the frontend expects port 8000, update its API configuration accordingly rather than creating a mysterious networking problem and then blaming the computer.

---

# 7. Dashboard cannot reach the API

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

# 8. Dashboard dependency installation fails

From the dashboard directory:

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

# Dependency / Test Client Note

The documented backend environment currently contains:

```text
FastAPI 0.141.1
Starlette 1.6.0
HTTPX 0.28.1
```

The existing environment may produce a TestClient-related deprecation warning associated with the HTTP client dependency.

A warning should not be confused with a test failure.

Before changing FastAPI, Starlette, or HTTPX versions, verify the actual compatibility requirements of the installed stack and run:

```powershell
pytest -v
```

Do not downgrade core framework dependencies merely to silence a warning without understanding the compatibility impact.

The functional regression baseline remains:

```text
64 tests
64 passed
0 failed
```

unless the test suite has intentionally changed.

---

# Environment Variables

The current documented payment gateway does not require production credentials or external service secrets to run the core regression suite.

Do not place secrets directly into source files.

If environment variables are introduced in future phases, use a local environment file that is excluded from Git:

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

The mock gateway should continue to use non-production test data.

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

## Backend

* [ ] FastAPI starts successfully
* [ ] Uvicorn uses `--reload-dir app`
* [ ] `http://localhost:8000/` responds
* [ ] `http://localhost:8000/docs` loads
* [ ] `http://localhost:8000/openapi.json` loads

## Tests

* [ ] API tests pass
* [ ] Payment Service tests pass
* [ ] State Machine tests pass
* [ ] Complete regression suite passes
* [ ] Current documented baseline remains 64 passed

## Dashboard

* [ ] Node.js installed
* [ ] npm available
* [ ] Dashboard dependencies installed
* [ ] Dashboard starts successfully when required
* [ ] Dashboard can reach the FastAPI backend
* [ ] Transaction lifecycle renders correctly

## Future Components

* [ ] Selenium configured
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
    +-- In-Memory Storage
    |
    +-- Web Dashboard
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
Transaction Repository
    |
    v
In-Memory Storage
```

The current documented regression baseline is:

```text
64 tests
64 passed
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
PostgreSQL
        |
        v
UI + Selenium
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

The project is currently paused at the existing backend/frontend checkpoint.

The next architectural phase should be introduced only after its requirements are defined and the corresponding documentation, implementation, and tests are aligned.

---

# Documentation References

The project documentation is organized as follows:

| Document                | Purpose                                            |
| ----------------------- | -------------------------------------------------- |
| `docs/PRD.md`           | Product requirements, scope, and success criteria  |
| `docs/ARCHITECTURE.md`  | System architecture and component interactions     |
| `docs/TEST_STRATEGY.md` | Testing strategy and regression approach           |
| `docs/TECH_STACK.md`    | Technology choices and architectural justification |
| `docs/API_SPEC.md`      | Mock Payment Gateway API contract                  |
| `docs/AI_PIPELINE.md`   | Planned AI RCA and test-generation architecture    |
| `docs/SETUP.md`         | Local development and environment setup            |

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

Docker is currently part of the planned platform architecture rather than a requirement for the core backend regression suite.

---

# Final Development Verification

Before considering a backend change complete, execute:

```powershell
pytest -v
```

The expected current baseline is:

```text
64 passed
0 failed
```

Then inspect:

```powershell
git status
```

and:

```powershell
git diff
```

The repository should contain only intentional changes.

The project should be left in a reproducible state before development is paused again.

That means:

```text
Application code
        +
Tests
        +
Documentation
        +
Git history
        |
        v
Consistent Development Baseline
```

This baseline is more valuable than adding another half-finished feature merely because the roadmap has room for one.

