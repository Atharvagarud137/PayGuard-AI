# SETUP.md — PayGuard AI

## Purpose

This document provides step-by-step instructions to set up PayGuard AI locally, covering environment setup, dependency installation, Docker services, and Ollama configuration.

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.12 | Core language for all services |
| IntelliJ IDEA | 2026.1 (or PyCharm) | Primary development environment |
| Docker Desktop | Latest | Required for containerized services (ChromaDB, Ollama, Dashboard) |
| Git | Latest | Version control |
| Ollama | Latest | Local LLM runtime |

## Step 1: Clone the Repository

git clone <repository-url>
cd PayGuard-AI

## Step 2: Create and Activate Virtual Environment

python -m venv .venv
.\.venv\Scripts\Activate.ps1

On macOS/Linux, activation instead uses `source .venv/bin/activate`.

## Step 3: Install Python Dependencies

pip install -r requirements.txt

## Step 4: Install and Configure Ollama

1. Download Ollama from its official website and install it for your OS.
2. Pull the chosen local model:

ollama pull llama3.1

3. Verify Ollama is running:

ollama list

## Step 5: Start Supporting Services via Docker Compose

From the project root:

docker compose -f docker/docker-compose.yml up -d

This starts ChromaDB and the Dashboard as background services. The Mock Payment Gateway can be run separately for active development (see Step 6) or included in Compose once stable.

## Step 6: Run the Mock Payment Gateway Locally

uvicorn app.main:app --reload --reload-dir app --port 8000

**Important:** Always use `--reload-dir app` rather than plain `--reload`. Without this flag, uvicorn watches the entire project directory, including `.venv`. On OneDrive-synced setups, background syncing constantly touches files inside `.venv`, which uvicorn misinterprets as code changes — triggering repeated, unwanted server restarts and wiping in-memory card/transaction data between requests. Scoping the watch to `app` only eliminates this issue entirely.

Once running, visit `http://localhost:8000/docs` to view the interactive API documentation.

## Step 7: Run the Test Suites

**API Tests:**

pytest tests/api

**UI Tests:**

pytest tests/ui

Ensure the Dashboard and Gateway are running before executing UI tests, since Selenium requires a live browser target.

## Step 8: Run the AI Engine (RCA / Test Case Generator)

Once failure logs exist (generated automatically when a test fails), run:

python ai_engine/rca_pipeline.py

To generate test case suggestions from the live API spec:

python ai_engine/test_case_generator.py

## Step 9: Verify Everything Is Working

| Check | Expected Result |
|---|---|
| `http://localhost:8000/docs` | Swagger UI loads with all payment endpoints |
| `http://localhost:3000` | Dashboard loads and displays transaction data |
| `pytest tests/api` | Tests run and pass (or fail intentionally for demo purposes) |
| `ollama list` | Shows the installed model as available |
| ChromaDB container | Shows as running via `docker ps` |

## Common Issues (OneDrive-Specific)

Since this project resides in a OneDrive-synced folder, you may occasionally encounter file lock errors during test runs or dependency installs. If this happens, pause OneDrive sync temporarily via the system tray icon, complete the operation, then resume sync.

**Frequent, unexplained server restarts / data disappearing between requests:** This happens when uvicorn's `--reload` watches the entire project folder, including `.venv`, and OneDrive's background sync touches those files constantly, triggering false-positive reloads. Always run uvicorn with `--reload-dir app` to scope file watching to only your actual source code, as shown in Step 6.

## Stopping Services

docker compose -f docker/docker-compose.yml down