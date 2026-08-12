# SETUP.md — PayGuard AI

## Purpose

This document provides instructions for setting up PayGuard AI locally, running the Mock Payment Gateway, executing the automated test suite, and preparing the environment for future UI automation and AI capabilities.

The current development workflow primarily requires Python, the project virtual environment, FastAPI, and Pytest. Docker, Ollama, ChromaDB, the Dashboard, and the AI engine are part of the planned project architecture and should only be configured when those components are being actively developed.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11.x | Current development environment |
| Git | Latest | Required for source control |
| IntelliJ IDEA | 2026.1 or PyCharm | Recommended development environment |
| Docker Desktop | Latest | Required for planned containerized services |
| Ollama | Latest | Required for the planned local LLM/AI layer |

### Current Verified Environment

The current project environment has been verified with:

```text Python 3.11.9 pytest 9.1.1 FastAPI 0.**141**.1 Starlette 1.6.0 httpx 0.28.1 ````

The project currently runs successfully using a Python 3.11 virtual environment.

---

## Step 1: Clone the Repository

Clone the repository and move into the project directory:

```powershell git clone [https://github.com/Atharvagarud137/PayGuard-AI.git](https://github.com/Atharvagarud137/PayGuard-AI.git) cd PayGuard-AI ```

If the repository has already been cloned, simply navigate to the project directory:

```powershell cd D:\Projects\PayGuard-AI ```

---

## Step 2: Create the Virtual Environment

Create a project-specific virtual environment:

```powershell python -m venv .venv ```

Activate it on Windows PowerShell:

```powershell .\.venv\Scripts\Activate.ps1 ```

After activation, verify that Python is coming from the project virtual environment:

```powershell python --version python -c *import sys; print(sys.executable)* ```

Expected output should resemble:

```text Python 3.11.9 D:\Projects\PayGuard-AI\.venv\Scripts\python.exe ```

### macOS / Linux

Activate the environment with:

```bash source .venv/bin/activate ```

---

## Step 3: Install Python Dependencies

If the project contains a requirements file, install the project dependencies with:

```powershell pip install -r requirements.txt ```

If dependencies are being installed manually during development, ensure the virtual environment is active before running `pip install`.

Verify Pytest:

```powershell pytest --version ```

Expected:

```text pytest 9.1.1 ```

The exact patch versions may change as the project dependency set evolves.

---

## Step 4: Verify the Project Environment

Before starting development, verify the Git working tree:

```powershell git status ```

A clean repository should report:

```text nothing to commit, working tree clean ```

Verify the configured remote:

```powershell git remote -v ```

The project currently uses:

```text [https://github.com/Atharvagarud137/PayGuard-AI.git](https://github.com/Atharvagarud137/PayGuard-AI.git) ```

---

## Step 5: Run the Mock Payment Gateway

The Mock Payment Gateway is implemented using FastAPI.

Start the development server with:

```powershell uvicorn app.main:app --reload --reload-dir app --port **8000** ```

### Important: Use `--reload-dir app`

Always prefer:

```powershell uvicorn app.main:app --reload --reload-dir app --port **8000** ```

rather than:

```powershell uvicorn app.main:app --reload ```

The project is located in a OneDrive-synchronized directory. When Uvicorn watches the entire project directory, changes made by OneDrive inside `.venv` can be detected as source-code changes.

This can cause:

- Unexpected server restarts
- Loss of in-memory card data
- Loss of in-memory transaction data
- Confusing test/development behavior

Restricting Uvicorn's reload watcher to the `app` directory prevents it from monitoring the virtual environment and other unrelated project files.

### Verify the API

Once the server is running, open:

```text [http://localhost:**8000**/docs](http://localhost:**8000**/docs) ```

The FastAPI Swagger UI should display the available payment gateway endpoints.

---

## Step 6: Run the Automated Tests

The current project has three implemented automated test layers:

```text
### State Machine Tests
        ↓
### Payment Service Tests
        ↓
**API** Tests
```

The current regression baseline is:

```text 64 tests 64 passed 0 failed ```

### Run the complete test suite

From the project root:

```powershell pytest -v ```

This is the recommended command after changes affecting the payment domain, service layer, state machine, repository, or **API**.

### Run API tests

```powershell pytest tests/api -v ```

The **API** suite currently contains 36 tests.

### Run Payment Service tests

```powershell pytest tests/unit/test_payment_service.py -v ```

The Payment Service suite currently contains 14 tests.

### Run State Machine tests

```powershell pytest tests/unit/test_state_machine.py -v ```

The State Machine suite currently contains 14 tests.

### Current Test Baseline

| Test Layer      |  Tests | Current Result           |
| --------------- | -----: | ------------------------ |
| API             |     36 | Passing                  |
| Payment Service |     14 | Passing                  |
| State Machine   |     14 | Passing                  |
| **Total**       | **64** | **64 Passed / 0 Failed** |

---

## Step 7: Access the API Documentation

With the FastAPI server running, open:

```text [http://localhost:**8000**/docs](http://localhost:**8000**/docs) ```

This provides the interactive Swagger UI for the Mock Payment Gateway.

The root health endpoint is:

```text [http://localhost:**8000**/](http://localhost:**8000**/) ```

It should return:

```json { *message*: *PayGuard AI Mock Payment Gateway is running* } ```

---

## Step 8: Run UI Tests

UI automation is part of the planned architecture and will use Selenium.

When the Dashboard and corresponding UI test suite have been implemented, UI tests can be executed with:

```powershell pytest tests/ui -v ```

The Dashboard and Mock Payment Gateway will need to be running before executing tests that depend on live browser/**API** services.

### Current Status

```text UI Dashboard       Planned Selenium Tests     Planned ```

Therefore, UI test execution is not part of the current 64-test regression baseline.

---

## Step 9: Configure the AI Environment

The AI layer is planned to use:

- LangChain
- LangGraph
- ChromaDB
- Ollama
- A local **LLM**

These components are not required to run the current payment-domain test suite.

### Install Ollama

Install Ollama for the appropriate operating system.

Verify the installation:

```powershell ollama --version ```

Pull the selected local model when the AI pipeline is ready:

```powershell ollama pull llama3.1 ```

Verify installed models:

```powershell ollama list ```

### Current Status

```text AI **RCA** Engine          Planned AI Test Case Generator Planned ChromaDB Integration   Planned Ollama Integration    Planned ```

Do not treat the presence of these dependencies in the Python environment as evidence that the AI pipeline is currently implemented.

---

## Step 10: Docker Services

Docker is part of the planned project architecture.

The intended Docker-based environment will eventually include services such as:

```text ### Mock Payment Gateway ### Web Dashboard PostgreSQL ChromaDB Ollama ```

When the corresponding Docker Compose configuration is implemented, the expected command will be:

```powershell docker compose -f docker/docker-compose.yml up -d ```

To inspect running containers:

```powershell docker ps ```

To stop the services:

```powershell docker compose -f docker/docker-compose.yml down ```

### Current Status

Docker-based orchestration is not required for the current payment-domain test suite.

---

## Current Development Workflow

For normal backend development, the recommended workflow is:

### 1. Activate the virtual environment

```powershell .\.venv\Scripts\Activate.ps1 ```

### 2. Verify Python

```powershell python --version ```

### 3. Start the API if endpoint testing is required

```powershell uvicorn app.main:app --reload --reload-dir app --port **8000** ```

### 4. Make the code change

Implement the required change while keeping payment-domain logic separated from the **API** layer.

### 5. Run targeted tests

For example:

```powershell pytest tests/unit/test_payment_service.py -v ```

or:

```powershell pytest tests/api -v ```

### 6. Run the complete regression suite

```powershell pytest -v ```

### 7. Check Git status

```powershell git status ```

### 8. Commit the verified change

```powershell git add . git commit -m *describe the change* git push origin main ```

---

## OneDrive-Specific Considerations

The project is currently located in a OneDrive-synchronized directory.

OneDrive synchronization can occasionally interfere with development tools that monitor files or modify large numbers of files.

Potential symptoms include:

- File lock errors
- Slow dependency installation
- Unexpected file-change detection
- Unexpected Uvicorn reloads
- In-memory application data disappearing after an unintended restart

### Recommended mitigation

If file operations are being disrupted, temporarily pause OneDrive synchronization while performing the operation.

Resume synchronization after the operation is complete.

### Uvicorn Reload Issue

The most important OneDrive-specific configuration is:

```powershell uvicorn app.main:app --reload --reload-dir app --port **8000** ```

Do not use unrestricted project-wide reload monitoring during development.

---

## Common Issues

### 1. Uvicorn repeatedly restarts

**Symptom:**

The FastAPI application repeatedly restarts without changes being made to application source files.

**Likely cause:**

Uvicorn is monitoring `.venv` or other OneDrive-managed files.

**Solution:**

Run:

```powershell uvicorn app.main:app --reload --reload-dir app --port **8000** ```

---

### 2. Card or transaction data disappears

**Symptom:**

Cards or transactions created during a session suddenly disappear.

**Cause:**

The current application uses in-memory storage. Any application restart clears the stored data.

An unexpected Uvicorn reload can therefore appear to be a payment-data problem when it is actually an application restart.

**Solution:**

Check the Uvicorn console for unexpected reloads and ensure that `--reload-dir app` is being used.

Persistent PostgreSQL storage is planned for a future milestone.

---

### 3. Tests fail after an application change

First run the affected test layer:

```powershell pytest tests/unit/test_payment_service.py -v ```

or:

```powershell pytest tests/api -v ```

Then run the complete suite:

```powershell pytest -v ```

Do not assume that a targeted test passing means the entire payment lifecycle remains unaffected.

---

### 4. Git reports unexpected file changes

Check:

```powershell git status ```

If OneDrive has modified or synchronized files during development, inspect the changes before committing.

Do not blindly commit generated files, virtual-environment files, logs, or temporary artifacts.

---

### 5. Virtual environment is not being used

Verify:

```powershell python -c *import sys; print(sys.executable)* ```

The executable should point to:

```text D:\Projects\PayGuard-AI\.venv\Scripts\python.exe ```

If it does not, activate the environment again:

```powershell .\.venv\Scripts\Activate.ps1 ```

---

## Dependency / Test Client Note

The current environment contains:

```text FastAPI 0.**141**.1 Starlette 1.6.0 httpx 0.28.1 ```

The current FastAPI/Starlette test stack reports a deprecation warning related to the TestClient **HTTP** client dependency.

This warning does not currently cause test failures.

The project should address the dependency compatibility warning through the appropriate `httpx2` dependency rather than downgrading FastAPI or Starlette solely to suppress the warning.

After dependency changes, always verify the complete suite:

```powershell pytest -v ```

The functional baseline should remain:

```text 64 tests 64 passed 0 failed ```

---

## Verification Checklist

Use the following checklist when setting up a new development environment.

### Core Environment

- [ ] Python 3.11.x installed
- [ ] Git installed
- [ ] Repository cloned
- [ ] `.venv` created
- [ ] `.venv` activated
- [ ] Python executable verified
- [ ] Dependencies installed
- [ ] Pytest available

### Backend

- [ ] FastAPI starts successfully
- [ ] Uvicorn uses `--reload-dir app`
- [ ] `[http://localhost:**8000**/`](http://localhost:**8000**/`) responds
- [ ] `[http://localhost:**8000**/docs`](http://localhost:**8000**/docs`) loads

### Tests

- [ ] **API** tests pass
- [ ] Payment Service tests pass
- [ ] State Machine tests pass
- [ ] Complete regression suite passes
- [ ] Current baseline remains 64 passed

### Future Components

- [ ] Dashboard configured
- [ ] Selenium configured
- [ ] Docker configured
- [ ] PostgreSQL configured
- [ ] Ollama configured
- [ ] ChromaDB configured
- [ ] AI **RCA** pipeline configured
- [ ] AI Test Case Generator configured
- [ ] CI/CD configured

---

## Current Project State

The current setup is sufficient to develop and test the core payment-domain implementation.

The currently required development stack is:

```text
Python 3.11
    |
    +-- FastAPI
    |
    +-- Pytest
    |
    +-- In-Memory Storage
```

The planned platform will progressively extend this environment:

```text
Current
    |
    v
### Payment Reliability
    |
    v
PostgreSQL
    |
    v
UI + Selenium
    |
    v
AI **RCA** + Test Generation
    |
    v
Docker + CI/CD
    |
    v
Observability + Production-Oriented Hardening
```

The current milestone is considered healthy when:

```text pytest -v ```

returns:

```text 64 passed 0 failed ```

---

## Stopping Services

### Stop Uvicorn

Press:

```text **CTRL** + C ```

in the terminal running Uvicorn.

### Stop Docker Services

When Docker Compose is being used:

```powershell docker compose -f docker/docker-compose.yml down ```

To remove containers and associated Compose resources:

```powershell docker compose -f docker/docker-compose.yml down --remove-orphans ```
