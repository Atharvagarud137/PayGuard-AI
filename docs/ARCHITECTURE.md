# ARCHITECTURE.md — PayGuard AI

## Overview

PayGuard AI consists of four major layers: the Payment Gateway (system under test), the Test Automation Layer, the AI Engine, and the Orchestration/CI layer. Each layer is independently containerized but communicates through well-defined interfaces, mirroring a realistic microservice-style testing environment.

## High-Level Architecture

| Layer | Component | Responsibility |
|---|---|---|
| System Under Test | Mock Payment Gateway (FastAPI) | Simulates card issuance, authorization, capture, settlement, and refund flows |
| System Under Test | Web Dashboard | Displays transaction status and history; serves as the UI target for Selenium tests |
| Test Automation | API Test Suite (Pytest) | Validates payment gateway endpoints across positive, negative, and boundary scenarios |
| Test Automation | UI Test Suite (Selenium) | Validates dashboard behavior and transaction visibility |
| AI Engine | RCA Pipeline (LangChain + ChromaDB + Ollama) | Ingests failed test logs, retrieves similar past failures, and generates root cause summaries |
| AI Engine | Test Case Generator (LangChain + Ollama) | Reads the API spec and proposes additional edge-case test scenarios |
| Orchestration | Docker Compose | Runs the payment gateway, dashboard, and AI engine as isolated services |
| Orchestration | GitHub Actions | Runs tests on every push; triggers RCA pipeline automatically when tests fail |

## Component Interaction Flow

1. **Test Execution**: Pytest and Selenium tests run against the Mock Payment Gateway and Web Dashboard respectively.
2. **Failure Capture**: When a test fails, logs and stack traces are written to a shared log store.
3. **RCA Trigger**: The CI pipeline detects failures and invokes the AI RCA Engine, passing the failure logs.
4. **RCA Processing**: The RCA Engine embeds the failure text, retrieves similar historical failures from ChromaDB, and uses the local LLM (via Ollama) to generate a root cause summary.
5. **Test Case Suggestion**: Independently, the Test Case Generator reads the OpenAPI spec exposed by the Mock Payment Gateway and proposes new edge-case scenarios, which are output as a markdown report for review.
6. **Reporting**: Both RCA summaries and test case suggestions are surfaced in the CI pipeline logs and optionally saved as artifacts.

## Data Flow Summary

| Stage | Data | Source | Destination |
|---|---|---|---|
| Test Execution | Test results, logs | Pytest / Selenium | Local log files / CI artifacts |
| Failure Analysis | Failure logs, stack traces | Log files | ChromaDB (embedded) + LLM |
| RCA Output | Root cause summary | LLM (Ollama) | CI logs / markdown report |
| Test Generation | API spec | FastAPI OpenAPI endpoint | LLM (Ollama) |
| Suggestion Output | New test case ideas | LLM (Ollama) | Markdown report |

## Directory-to-Component Mapping

| Directory | Maps to Component |
|---|---|
| `app/` | Mock Payment Gateway (FastAPI) |
| `dashboard/` | Web Dashboard |
| `tests/api/` | API Test Suite |
| `tests/ui/` | UI Test Suite |
| `ai_engine/` | RCA Pipeline + Test Case Generator |
| `docker/` | Docker Compose and service Dockerfiles |
| `.github/workflows/` | CI/CD pipeline definitions |

## Design Principles

- **Isolation**: Each service (gateway, dashboard, AI engine) runs independently and communicates over well-defined APIs, allowing components to be tested or demoed in isolation.
- **Offline-first AI**: The AI Engine uses a local LLM via Ollama rather than a hosted API, so the entire project can run without internet access or API costs.
- **Traceability**: Every test failure that triggers RCA is logged with enough context (timestamp, endpoint, payload, stack trace) to make the AI's root cause summary meaningful and verifiable.
- **Extensibility**: New payment flows or card networks can be added to the Mock Payment Gateway without changing the test automation or AI layers, since both operate against the OpenAPI spec and log format rather than hardcoded logic.

## Deployment View (Local Development)

| Service | Port (Default) | Notes |
|---|---|---|
| Mock Payment Gateway | 8000 | FastAPI with auto-generated OpenAPI docs at `/docs` |
| Web Dashboard | 3000 | Simple frontend served separately, calls the Gateway API |
| ChromaDB | 8001 | Vector store for RCA embeddings |
| Ollama | 11434 | Local LLM server |

All services are orchestrated via `docker/docker-compose.yml` for local development, with GitHub Actions replicating the same setup in CI using service containers.