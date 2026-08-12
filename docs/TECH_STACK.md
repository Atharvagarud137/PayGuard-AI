# TECH_STACK.md — PayGuard AI

## Purpose

This document describes the technology stack used by PayGuard AI, the role of each technology, and the reasoning behind the architectural choices.

The stack is intentionally divided into **currently implemented technologies** and **planned technologies**. A dependency being installed in the development environment does not necessarily mean that it is currently part of the implemented application architecture.

The project combines two primary engineering areas:

1. **Payment-domain software engineering and test automation**
2. **Applied AI for intelligent test analysis and test generation**

---

## Current Technology Stack

### Backend / System Under Test

| Technology | Purpose | Status | Why Chosen |
| ---------- | ------- | ------ | ---------- |
| **Python 3.11** | Core application language | Implemented | Strong ecosystem for backend development, testing, automation, and AI engineering |
| **FastAPI** | Mock Payment Gateway framework | Implemented | Provides automatic OpenAPI documentation, strong request validation through Pydantic, and a lightweight architecture suitable for the simulated payment gateway |
| **Pydantic** | Request and response validation | Implemented | Provides structured validation for payment API payloads and integrates naturally with FastAPI |
| **Uvicorn** | ASGI application server | Implemented | Lightweight and well suited for running the FastAPI development server |
| **In-Memory Storage** | Current application persistence | Implemented | Keeps the initial payment-domain implementation simple and deterministic while the domain and service architecture are being validated |
| **Transaction Repository** | Persistence abstraction | Implemented | Separates payment business logic from the underlying storage implementation and provides a migration path toward PostgreSQL |

---

## Payment Domain Architecture

The payment engine currently uses several architectural patterns and domain components in addition to the framework stack.

| Component | Purpose | Status | Why Used |
| --------- | ------- | ------ | -------- |
| **Payment Service** | Payment business logic | Implemented | Keeps capture, settlement, and refund rules outside the HTTP layer |
| **Transaction State Machine** | Payment lifecycle validation | Implemented | Provides a centralized mechanism for validating legal transaction state transitions |
| **Domain Exceptions** | Payment-specific error handling | Implemented | Allows business logic to communicate typed domain failures without depending on HTTP-specific exceptions |
| **Repository Pattern** | Persistence abstraction | Implemented | Allows the current in-memory implementation to be replaced with persistent storage without tightly coupling business logic to a database |
| **Transaction History / Events** | Transaction traceability | Implemented | Records important lifecycle events associated with a transaction |

### Current Payment Lifecycle

```text
**AUTHORIZED**
    |
    v
 **CAPTURED**
    |
    v
 **SETTLED**
    |
    +----------------------+
    |                      |
    v                      v
PARTIALLY_REFUNDED      **REFUNDED**
    |
    v
 **REFUNDED**
````

The domain model explicitly validates valid and invalid transitions.

---

# Test Automation Stack

| Technology                           | Purpose                                       | Status      | Why Chosen                                                                                                          |
| ------------------------------------ | --------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------- |
| **Pytest**                           | Unit, service, state-machine, and API testing | Implemented | Mature Python testing framework with strong fixture support and clean integration with CI/CD                        |
| **FastAPI TestClient / HTTP client** | API endpoint testing                          | Implemented | Allows API behavior to be tested without requiring a separately deployed gateway                                    |
| **Selenium**                         | Browser/UI automation                         | Planned     | Widely used in enterprise QA environments and provides realistic browser-based validation for the planned dashboard |
| **HTTPX**                            | HTTP client dependency                        | Installed   | Used by the current FastAPI/Starlette testing stack and other project dependencies                                  |

### Current Automated Test Baseline

The current project contains:

| Test Layer      |  Tests | Status                   |
| --------------- | -----: | ------------------------ |
| State Machine   |     14 | Passing                  |
| Payment Service |     14 | Passing                  |
| API             |     36 | Passing                  |
| **Total**       | **64** | **64 Passed / 0 Failed** |

The test architecture intentionally separates:

```text
### State Machine
      ↓
### Payment Service
      ↓
**API**
```

This allows payment-domain rules to be tested independently from **HTTP** behavior.

---

# Frontend / Dashboard

| Technology                                              | Purpose       | Status  | Why Chosen                                                                                                                              |
| ------------------------------------------------------- | ------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **HTML / JavaScript or lightweight frontend framework** | Web Dashboard | Planned | The dashboard is intended primarily as a realistic Selenium target for validating transaction visibility and user-facing payment states |

The dashboard is deliberately not a current architectural priority. The payment-domain foundation is being established before UI automation is introduced.

---

# AI Engineering Stack

The AI layer is part of the planned PayGuard AI architecture and is not yet part of the current 64-test payment-domain implementation.

| Technology        | Purpose                      | Status  | Why Chosen                                                                                           |
| ----------------- | ---------------------------- | ------- | ---------------------------------------------------------------------------------------------------- |
| **LangChain**     | LLM orchestration            | Planned | Provides components for building retrieval and LLM-based workflows                                   |
| **LangGraph**     | AI workflow orchestration    | Planned | Provides a structured approach for multi-step AI workflows such as failure analysis                  |
| **ChromaDB**      | Vector storage               | Planned | Lightweight local vector database suitable for storing and retrieving historical failure information |
| **Ollama**        | Local LLM inference          | Planned | Enables local model execution without requiring a hosted LLM API                                     |
| **OpenTelemetry** | AI/application observability | Planned | Provides a foundation for tracing and measuring application and AI workflows                         |

---

## Planned AI Architecture

### AI Root Cause Analysis

The planned **RCA** pipeline will follow:

```text
### Test Failure
    |
    v
Failure Logs / Stack Trace
    |
    v
### Failure Context Extraction
    |
    v
### Embedding Generation
    |
    v
ChromaDB Retrieval
    |
    v
Local **LLM** via Ollama
    |
    v
### Root Cause Summary
```

### AI Test Case Generation

The planned test-generation pipeline will use the FastAPI OpenAPI specification:

```text
FastAPI OpenAPI Specification
    |
    v
    **LLM** Analysis
    |
    v
    Edge-Case Identification
    |
    v
 Test Scenario Suggestions
    |
    v
    Human Review
```

AI-generated scenarios will initially be treated as suggestions rather than automatically trusted executable tests.

---

# Persistence

## Current Persistence

| Technology            | Status      | Purpose                                                              |
| --------------------- | ----------- | -------------------------------------------------------------------- |
| **In-Memory Storage** | Implemented | Temporary persistence mechanism for the current Mock Payment Gateway |

The current storage approach is intentionally simple and is sufficient for validating the payment lifecycle and service architecture.

However, it does not provide:

- Durable storage
- Database transactions
- Transaction isolation
- Row-level locking
- Persistence across application restarts
- Database-level constraints

---

## Planned Persistence

| Technology     | Status  | Purpose                       | Why Planned                                                                                                              |
| -------------- | ------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **SQLAlchemy** | Planned | Database abstraction / ORM    | Provides a structured persistence layer for PostgreSQL integration                                                       |
| **PostgreSQL** | Planned | Durable transactional storage | Provides the transactional guarantees and concurrency controls required for a more realistic payment-system architecture |

The repository abstraction is intended to allow this migration without requiring payment business logic to depend directly on PostgreSQL.

---

# Containerization and Orchestration

| Technology         | Purpose                     | Status  | Why Chosen                                                                                        |
| ------------------ | --------------------------- | ------- | ------------------------------------------------------------------------------------------------- |
| **Docker**         | Service containerization    | Planned | Provides reproducible environments across development and CI                                      |
| **Docker Compose** | Multi-service orchestration | Planned | Simplifies running the gateway, dashboard, database, vector store, and local AI services together |

The planned containerized environment may eventually include:

```text
### Mock Payment Gateway
    |
    +-- PostgreSQL
    |
    +-- Web Dashboard
    |
    +-- ChromaDB
    |
    +-- Ollama
```

Containerization will be introduced as the corresponding services become implementation-ready.

---

# CI/CD

| Technology         | Purpose                                               | Status      | Why Chosen                                                                                            |
| ------------------ | ----------------------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------- |
| **GitHub Actions** | Continuous integration and future automated execution | Planned     | Integrates directly with GitHub and can execute the automated regression suite as the project evolves |
| **Git**            | Version control                                       | Implemented | Provides source-code versioning and collaborative development workflow                                |

The intended CI/CD pipeline will eventually execute the appropriate testing layers and may trigger AI-assisted analysis when failures occur.

Planned workflow:

```text
Commit / Pull Request
    |
    v
Domain / Unit Tests
    |
    v
### Service Tests
    |
    v
**API** Tests
    |
    v
### Integration Tests
    |
    v
UI Tests
    |
    v
AI Validation
```

---

# Observability

Observability is a planned part of the production-oriented architecture.

| Technology             | Purpose                            | Status      |
| ---------------------- | ---------------------------------- | ----------- |
| **OpenTelemetry**      | Distributed tracing and telemetry  | Planned     |
| **Structured Logging** | Payment and test event diagnostics | Planned     |
| **Transaction Events** | Payment lifecycle traceability     | Implemented |

Observability will become particularly important when the project introduces:

- PostgreSQL
- asynchronous processing
- AI workflows
- CI/CD execution
- failure correlation
- distributed services

---

# Development Environment

| Tool                        | Purpose                               | Status      |
| --------------------------- | ------------------------------------- | ----------- |
| **IntelliJ IDEA / PyCharm** | Primary development environment       | Implemented |
| **Git**                     | Version control                       | Implemented |
| **Python venv**             | Dependency isolation                  | Implemented |
| **PowerShell**              | Local development commands on Windows | Implemented |
| **Docker Desktop**          | Container development                 | Planned     |
| **Ollama**                  | Local LLM runtime                     | Planned     |

The current verified development environment uses:

```text Python 3.11.9 pytest 9.1.1 FastAPI 0.**141**.1 Starlette 1.6.0 httpx 0.28.1 Uvicorn 0.52.1 Pydantic 2.13.4 ```

Patch versions may change as dependency maintenance continues.

---

# Dependency Management

The project currently uses a Python virtual environment:

```text .venv/ ```

The virtual environment isolates project dependencies from the system Python installation.

The project should maintain a controlled dependency definition rather than relying solely on the complete output of:

```powershell pip freeze ```

The dependency list should distinguish between:

- Runtime dependencies
- Development/testing dependencies
- AI dependencies
- Infrastructure/deployment dependencies

This becomes increasingly important as the project introduces LangChain, LangGraph, ChromaDB, PostgreSQL, observability, and containerized services.

---

# HTTP Client Compatibility

The current environment contains:

```text httpx==0.28.1 ```

The FastAPI/Starlette test environment currently produces a TestClient deprecation warning related to the **HTTP** client dependency.

The project should use the appropriate `httpx2` dependency for the Starlette TestClient compatibility path rather than downgrading the current FastAPI/Starlette stack solely to remove the warning.

Any dependency change must be followed by the complete regression suite:

```powershell pytest -v ```

The functional baseline must remain:

```text 64 tests 64 passed 0 failed ```

---

# Technology Selection Principles

The PayGuard AI stack follows several principles.

## 1. Domain correctness before AI

The payment lifecycle is being modeled and tested before AI capabilities are introduced.

The system should first produce reliable payment behavior before an **LLM** is asked to analyze that behavior.

```text
### Payment Domain
      ↓
### Reliable Tests
      ↓
### Failure Data
      ↓
AI Analysis
```

## 2. Separation of concerns

The architecture separates:

```text **API** ↓ ### Payment Service ↓ Domain ↓ Repository ↓ Storage ```

This prevents framework-specific concerns from spreading throughout the payment domain.

## 3. Testability

Business rules should be testable independently from the **HTTP** layer.

This is why the project contains separate state-machine, payment-service, and **API** test suites.

## 4. Local-first AI

The planned AI layer uses Ollama and local models to support:

- Local experimentation
- Reproducible demonstrations
- Reduced external **API** dependency
- Avoidance of mandatory hosted-**LLM** costs

## 5. Production-oriented payment design

Although PayGuard AI is a mock payment gateway rather than a production payment processor, architectural decisions are made with payment-system concerns in mind.

Future architecture will address:

- Monetary precision
- Idempotency
- Concurrency
- Persistence
- Auditability
- Authentication
- Authorization
- Observability
- Security
- Failure recovery

## 6. Incremental complexity

Technologies are introduced when they solve an actual architectural problem.

The current progression is:

```text
FastAPI Payment Gateway
    |
    v
### Payment Domain
    |
    v
### State Machine
    |
    v
### Payment Service
    |
    v
### Repository Abstraction
    |
    v
PostgreSQL
    |
    v
### Reliability Controls
    |
    v
UI + Automation
    |
    v
AI Augmentation
    |
    v
CI/CD + Observability
```

---

# Current vs Planned Stack

| Area              | Current                           | Planned                                  |
| ----------------- | --------------------------------- | ---------------------------------------- |
| Language          | Python 3.11                       | —                                        |
| Backend           | FastAPI                           | —                                        |
| Validation        | Pydantic                          | —                                        |
| Server            | Uvicorn                           | —                                        |
| Storage           | In-memory                         | PostgreSQL                               |
| Persistence Layer | Repository                        | SQLAlchemy + PostgreSQL                  |
| Domain            | State Machine + Domain Exceptions | Extended payment reliability controls    |
| API Testing       | Pytest                            | Expanded integration testing             |
| Service Testing   | Pytest                            | Expanded reliability testing             |
| State Testing     | Pytest                            | Expanded lifecycle testing               |
| UI Automation     | —                                 | Selenium                                 |
| Dashboard         | —                                 | HTML/JavaScript or lightweight framework |
| AI Orchestration  | —                                 | LangChain + LangGraph                    |
| Vector Database   | —                                 | ChromaDB                                 |
| Local LLM         | —                                 | Ollama                                   |
| Observability     | —                                 | OpenTelemetry                            |
| Containers        | —                                 | Docker + Docker Compose                  |
| CI/CD             | —                                 | GitHub Actions                           |

---

# Summary Rationale

PayGuard AI deliberately combines technologies that support both sides of the project's engineering objective.

### Payment and QA Engineering

- **FastAPI** provides the Mock Payment Gateway.
- **Pydantic** provides structured **API** validation.
- **Pytest** provides the primary automated testing framework.
- **Selenium** is planned for realistic browser-level automation.
- **State machines, services, repositories, and domain exceptions** provide a maintainable payment-domain architecture.
- **PostgreSQL and SQLAlchemy** are planned for durable, transactional persistence.

### Applied AI

- **LangChain** and **LangGraph** are planned for AI workflow orchestration.
- **ChromaDB** is planned for historical failure retrieval.
- **Ollama** is planned for local **LLM** inference.
- **OpenTelemetry** is planned for observability across application and AI workflows.

The overall technology strategy is therefore not simply a collection of popular tools. Each technology has a defined role in the evolution of the system:

```text
### Reliable Payment Domain
    |
    v
### Automated Validation
    |
    v
Persistent + Reliable Architecture
    |
    v
Enterprise-Style Test Automation
    |
    v
AI-Assisted Failure Analysis
    |
    v
AI-Assisted Test Generation
```

The immediate priority remains the payment-domain and reliability foundation. AI, UI automation, persistence, containerization, and CI/CD will be introduced incrementally as the corresponding architectural requirements are implemented.
