# TECH_STACK.md — PayGuard AI

## Purpose

This document describes the technology stack used by PayGuard AI, the role of each technology, and the reasoning behind the architectural choices.

The stack is intentionally divided into **currently implemented technologies** and **planned technologies**. A dependency being installed in the development environment does not necessarily mean that it is currently part of the implemented application architecture.

PayGuard AI combines two primary engineering areas:

1. **Payment-domain software engineering and test automation**
2. **Applied AI for intelligent test analysis and test generation**

The project is being developed incrementally. The current priority is to establish a reliable payment-domain foundation, followed by persistence and reliability controls, before introducing the broader UI automation and AI layers. Humanity has somehow decided that adding an LLM before making the database trustworthy is a good idea, so this separation is deliberate.

---

# Current Technology Stack

## Backend / System Under Test

| Technology                 | Purpose                         | Status      | Why Chosen                                                                                                                                               |
| -------------------------- | ------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Python 3.11**            | Core application language       | Implemented | Strong ecosystem for backend development, testing, automation, and AI engineering                                                                        |
| **FastAPI**                | Mock Payment Gateway framework  | Implemented | Provides automatic OpenAPI documentation, request validation through Pydantic, and a lightweight architecture suitable for the simulated payment gateway |
| **Pydantic**               | Request and response validation | Implemented | Provides structured validation for payment API payloads and integrates naturally with FastAPI                                                            |
| **Uvicorn**                | ASGI application server         | Implemented | Lightweight and suitable for running the FastAPI development server                                                                                      |
| **In-Memory Storage**      | Current application persistence | Implemented | Keeps the initial payment-domain implementation simple and deterministic while the domain and service architecture are being validated                   |
| **Transaction Repository** | Persistence abstraction         | Implemented | Separates payment business logic from the underlying storage implementation and provides a migration path toward PostgreSQL                              |

---

# Payment Domain Architecture

The payment engine currently uses several architectural patterns and domain components in addition to the framework stack.

| Component                        | Purpose                         | Status      | Why Used                                                                                                                                 |
| -------------------------------- | ------------------------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Payment Service**              | Payment business logic          | Implemented | Keeps capture, settlement, and refund rules outside the HTTP layer                                                                       |
| **Transaction State Machine**    | Payment lifecycle validation    | Implemented | Provides a centralized mechanism for validating legal transaction state transitions                                                      |
| **Domain Exceptions**            | Payment-specific error handling | Implemented | Allows business logic to communicate typed domain failures without depending on HTTP-specific exceptions                                 |
| **Repository Pattern**           | Persistence abstraction         | Implemented | Allows the current in-memory implementation to be replaced with persistent storage without tightly coupling business logic to a database |
| **Transaction History / Events** | Transaction traceability        | Implemented | Records important lifecycle events associated with a transaction                                                                         |

## Current Payment Lifecycle

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

The domain model explicitly validates valid and invalid transitions.

The lifecycle currently supports:

* Authorization
* Capture
* Settlement
* Full refund
* Partial refund
* Completion of remaining refund amounts

Invalid transitions are rejected by the domain state machine.

---

# Payment API Capabilities

The current Mock Payment Gateway exposes the core payment operations used by the project.

| Capability              | Status      | Description                                           |
| ----------------------- | ----------- | ----------------------------------------------------- |
| **Card Issuance**       | Implemented | Creates simulated payment cards                       |
| **Authorization**       | Implemented | Validates a card and authorizes a transaction         |
| **Capture**             | Implemented | Captures an authorized transaction                    |
| **Settlement**          | Implemented | Settles a captured transaction                        |
| **Full Refund**         | Implemented | Refunds the complete refundable amount                |
| **Partial Refund**      | Implemented | Refunds part of the settled amount                    |
| **Transaction Lookup**  | Implemented | Retrieves transaction state and lifecycle information |
| **Transaction History** | Implemented | Records lifecycle events associated with transactions |
| **Failure Simulation**  | Implemented | Supports deterministic technical failure scenarios    |

The current payment flow is intentionally simulated and does not connect to real card networks or production payment processors.

---

# Test Automation Stack

| Technology                           | Purpose                                       | Status      | Why Chosen                                                                                   |
| ------------------------------------ | --------------------------------------------- | ----------- | -------------------------------------------------------------------------------------------- |
| **Pytest**                           | Unit, service, state-machine, and API testing | Implemented | Mature Python testing framework with strong fixture support and clean integration with CI/CD |
| **FastAPI TestClient / HTTP client** | API endpoint testing                          | Implemented | Allows API behavior to be tested without requiring a separately deployed gateway             |
| **Selenium**                         | Browser/UI automation                         | Planned     | Provides realistic browser-based validation for the planned dashboard                        |
| **HTTPX**                            | HTTP client dependency                        | Installed   | Used by the current FastAPI/Starlette testing stack and related project dependencies         |

## Current Automated Test Baseline

The current project contains:

| Test Layer      |  Tests | Status                   |
| --------------- | -----: | ------------------------ |
| State Machine   |     14 | Passing                  |
| Payment Service |     14 | Passing                  |
| API             |     36 | Passing                  |
| **Total**       | **64** | **64 Passed / 0 Failed** |

The test architecture intentionally separates:

```text
State Machine
      |
      v
Payment Service
      |
      v
API
```

This allows payment-domain rules to be tested independently from HTTP behavior.

---

# Frontend / Dashboard

The project currently contains a Web Dashboard implementation used for visualizing payment-system activity and transaction lifecycles.

| Technology             | Purpose               | Status      | Why Chosen                                                                                                              |
| ---------------------- | --------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------- |
| **React / TypeScript** | Web Dashboard         | Implemented | Provides a structured component-based frontend suitable for a transaction-monitoring interface and future UI automation |
| **CSS**                | Dashboard styling     | Implemented | Provides control over the dark payment-operations dashboard interface and lifecycle visualization                       |
| **Selenium**           | Browser/UI automation | Planned     | Intended to validate user-visible dashboard behavior                                                                    |

The dashboard currently focuses on:

* Transaction visibility
* Transaction status
* Payment amounts
* Transaction lifecycle
* Card-related information
* Payment-system operational views

The dashboard is currently treated as a frontend target for future automated UI validation rather than as the source of payment-domain business rules.

---

# AI Engineering Stack

The AI layer is part of the planned PayGuard AI architecture and is not yet part of the current 64-test payment-domain implementation.

| Technology        | Purpose                          | Status  | Why Chosen                                                                                           |
| ----------------- | -------------------------------- | ------- | ---------------------------------------------------------------------------------------------------- |
| **LangChain**     | LLM orchestration                | Planned | Provides components for building retrieval and LLM-based workflows                                   |
| **LangGraph**     | AI workflow orchestration        | Planned | Provides a structured approach for multi-step AI workflows such as failure analysis                  |
| **ChromaDB**      | Vector storage                   | Planned | Lightweight local vector database suitable for storing and retrieving historical failure information |
| **Ollama**        | Local LLM inference              | Planned | Enables local model execution without requiring a hosted LLM API                                     |
| **OpenTelemetry** | Application and AI observability | Planned | Provides a foundation for tracing and measuring application and AI workflows                         |

---

# Planned AI Architecture

## AI Root Cause Analysis

The planned **RCA** pipeline will follow:

```text
Test Failure
    |
    v
Failure Logs / Stack Trace
    |
    v
Failure Context Extraction
    |
    v
Embedding Generation
    |
    v
ChromaDB Retrieval
    |
    v
Local LLM via Ollama
    |
    v
Root Cause Summary
```

The intended purpose is to correlate the current failure with historical failure information before generating an RCA.

The AI should assist investigation rather than become an unverified source of truth.

## AI Test Case Generation

The planned test-generation pipeline will use the FastAPI OpenAPI specification:

```text
FastAPI OpenAPI Specification
    |
    v
LLM Analysis
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

* Durable storage
* Database transactions
* Transaction isolation
* Row-level locking
* Persistence across application restarts
* Database-level constraints
* Distributed concurrency control
* Durable transaction history

These limitations are important because the next architectural stage is focused on reliability and persistence rather than immediately adding more application features.

---

# Planned Persistence

| Technology     | Status  | Purpose                       | Why Planned                                                                                                                                     |
| -------------- | ------- | ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **SQLAlchemy** | Planned | Database abstraction / ORM    | Provides a structured persistence layer for PostgreSQL integration                                                                              |
| **PostgreSQL** | Planned | Durable transactional storage | Provides transactional guarantees, persistence, constraints, and concurrency controls required for a more realistic payment-system architecture |

The repository abstraction is intended to allow this migration without requiring payment business logic to depend directly on PostgreSQL.

The planned persistence architecture is:

```text
Payment Service
      |
      v
Transaction Repository
      |
      v
SQLAlchemy
      |
      v
PostgreSQL
```

The migration should preserve the existing payment-domain interface wherever practical.

---

# Reliability Technology Requirements

Persistence alone does not make a payment system reliable. The next stage must also address transaction consistency and duplicate operations.

The planned reliability layer includes:

| Capability                 | Status  | Purpose                                                                |
| -------------------------- | ------- | ---------------------------------------------------------------------- |
| **Monetary Precision**     | Planned | Prevent floating-point inaccuracies in financial calculations          |
| **Idempotency**            | Planned | Prevent duplicate payment operations caused by repeated requests       |
| **Concurrency Control**    | Planned | Prevent race conditions involving simultaneous transaction operations  |
| **Database Transactions**  | Planned | Ensure related state changes are committed or rolled back consistently |
| **Durable Audit History**  | Planned | Preserve transaction lifecycle events across application restarts      |
| **Failure Recovery**       | Planned | Define safe behavior for technical failures and retries                |
| **Consistency Validation** | Planned | Ensure transaction amounts and states remain internally consistent     |

These controls are more important to the architecture's next stage than adding additional surface-level features.

---

# Containerization and Orchestration

| Technology         | Purpose                     | Status  | Why Chosen                                                                                        |
| ------------------ | --------------------------- | ------- | ------------------------------------------------------------------------------------------------- |
| **Docker**         | Service containerization    | Planned | Provides reproducible environments across development and CI                                      |
| **Docker Compose** | Multi-service orchestration | Planned | Simplifies running the gateway, dashboard, database, vector store, and local AI services together |

The planned containerized environment may eventually include:

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

Containerization will be introduced as the corresponding services become implementation-ready.

---

# CI/CD

| Technology         | Purpose                                               | Status      | Why Chosen                                                                                            |
| ------------------ | ----------------------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------- |
| **GitHub Actions** | Continuous integration and future automated execution | Planned     | Integrates directly with GitHub and can execute the automated regression suite as the project evolves |
| **Git**            | Version control                                       | Implemented | Provides source-code versioning and the development workflow                                          |

The intended CI/CD pipeline will eventually execute the appropriate testing layers and may trigger AI-assisted analysis when failures occur.

Planned workflow:

```text
Commit / Pull Request
    |
    v
Domain / Unit Tests
    |
    v
Service Tests
    |
    v
API Tests
    |
    v
Integration Tests
    |
    v
UI Tests
    |
    v
AI Validation
```

The pipeline should be introduced incrementally. Tests and infrastructure should not be added to CI before they are stable enough to provide meaningful feedback.

---

# Observability

Observability is a planned part of the production-oriented architecture.

| Technology             | Purpose                            | Status      |
| ---------------------- | ---------------------------------- | ----------- |
| **OpenTelemetry**      | Distributed tracing and telemetry  | Planned     |
| **Structured Logging** | Payment and test event diagnostics | Planned     |
| **Transaction Events** | Payment lifecycle traceability     | Implemented |

Observability will become particularly important when the project introduces:

* PostgreSQL
* Asynchronous processing
* AI workflows
* CI/CD execution
* Failure correlation
* Multiple application services
* Persistent transaction history

The transaction history already provides a domain-level foundation for later observability work.

---

# Development Environment

| Tool                                       | Purpose                               | Status      |
| ------------------------------------------ | ------------------------------------- | ----------- |
| **IntelliJ IDEA / PyCharm**                | Primary development environment       | Implemented |
| **Git**                                    | Version control                       | Implemented |
| **Python venv**                            | Dependency isolation                  | Implemented |
| **PowerShell**                             | Local development commands on Windows | Implemented |
| **React / TypeScript Development Tooling** | Dashboard development                 | Implemented |
| **Docker Desktop**                         | Container development                 | Planned     |
| **Ollama**                                 | Local LLM runtime                     | Planned     |

The backend development environment currently targets Python 3.11.

Exact package patch versions may change as dependency maintenance continues.

---

# Dependency Management

The project currently uses a Python virtual environment:

```text
.venv/
```

The virtual environment isolates project dependencies from the system Python installation.

The project should maintain a controlled dependency definition rather than relying solely on the complete output of:

```powershell
pip freeze
```

The dependency list should distinguish between:

* Runtime dependencies
* Development/testing dependencies
* Frontend dependencies
* AI dependencies
* Infrastructure/deployment dependencies

This separation becomes increasingly important as the project introduces PostgreSQL, AI services, observability, and containerized infrastructure.

---

# HTTP Client Compatibility

The current environment contains:

```text
httpx==0.28.1
```

The existing FastAPI/Starlette testing environment has produced a TestClient compatibility/deprecation warning related to the HTTP client dependency.

Dependency changes should be handled deliberately rather than downgrading the framework stack simply to eliminate a warning.

Any dependency change must be followed by the complete regression suite:

```powershell
pytest -v
```

The functional baseline should remain:

```text
64 tests
64 passed
0 failed
```

If the dependency versions change, the exact versions should be documented again based on the verified development environment rather than copied indefinitely from an older environment snapshot.

---

# Technology Selection Principles

The PayGuard AI stack follows several principles.

## 1. Domain correctness before AI

The payment lifecycle is modeled and tested before AI capabilities are introduced.

The system should first produce reliable payment behavior before an LLM is asked to analyze that behavior.

```text
Payment Domain
      |
      v
Reliable Tests
      |
      v
Failure Data
      |
      v
AI Analysis
```

## 2. Persistence before advanced automation

The system should establish durable and consistent transaction behavior before building automation and AI features that depend on transaction history.

```text
Payment Domain
      |
      v
Repository
      |
      v
Persistent Storage
      |
      v
Reliability Controls
      |
      v
Automation
      |
      v
AI
```

This keeps the architecture grounded in reliable system behavior rather than building intelligence around ephemeral data.

## 3. Separation of concerns

The architecture separates:

```text
API
 ↓
Payment Service
 ↓
Domain
 ↓
Repository
 ↓
Storage
```

This prevents framework-specific concerns from spreading throughout the payment domain.

## 4. Testability

Business rules should be testable independently from the HTTP layer.

This is why the project contains separate state-machine, payment-service, and API test suites.

## 5. Local-first AI

The planned AI layer uses Ollama and local models to support:

* Local experimentation
* Reproducible demonstrations
* Reduced external API dependency
* Avoidance of mandatory hosted-LLM costs

## 6. Production-oriented payment design

Although PayGuard AI is a mock payment gateway rather than a production payment processor, architectural decisions are made with payment-system concerns in mind.

Future architecture will address:

* Monetary precision
* Idempotency
* Concurrency
* Persistence
* Auditability
* Authentication
* Authorization
* Observability
* Security
* Failure recovery

## 7. Incremental complexity

Technologies are introduced when they solve an actual architectural problem.

The current progression is:

```text
FastAPI Payment Gateway
    |
    v
Payment Domain
    |
    v
State Machine
    |
    v
Payment Service
    |
    v
Repository Abstraction
    |
    v
Persistent Storage
    |
    v
Reliability Controls
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

This sequence is intentional. Adding six infrastructure systems at once would produce six new ways for the project to fail, which is not especially clever QA.

---

# Current vs Planned Stack

| Area              | Current                           | Planned                               |
| ----------------- | --------------------------------- | ------------------------------------- |
| Language          | Python 3.11                       | —                                     |
| Backend           | FastAPI                           | —                                     |
| Validation        | Pydantic                          | —                                     |
| Server            | Uvicorn                           | —                                     |
| Storage           | In-memory                         | PostgreSQL                            |
| Persistence Layer | Repository                        | SQLAlchemy + PostgreSQL               |
| Domain            | State Machine + Domain Exceptions | Extended payment reliability controls |
| API Testing       | Pytest                            | Expanded integration testing          |
| Service Testing   | Pytest                            | Expanded reliability testing          |
| State Testing     | Pytest                            | Expanded lifecycle testing            |
| Dashboard         | React + TypeScript                | Expanded dashboard functionality      |
| UI Automation     | —                                 | Selenium                              |
| AI Orchestration  | —                                 | LangChain + LangGraph                 |
| Vector Database   | —                                 | ChromaDB                              |
| Local LLM         | —                                 | Ollama                                |
| Observability     | —                                 | OpenTelemetry                         |
| Containers        | —                                 | Docker + Docker Compose               |
| CI/CD             | —                                 | GitHub Actions                        |

---

# Recommended Technology Evolution

The intended implementation sequence is:

### Phase 1 — Core Payment Domain

**Implemented**

* FastAPI
* Pydantic
* Uvicorn
* Payment service
* State machine
* Repository abstraction
* In-memory storage
* Pytest
* API testing

### Phase 2 — Payment Reliability

**Next priority**

* Monetary precision
* PostgreSQL
* SQLAlchemy
* Database transactions
* Idempotency
* Concurrency control
* Durable transaction history
* Persistence tests

### Phase 3 — Automation Platform

**Planned**

* React / TypeScript dashboard refinement
* Selenium
* Expanded API testing
* Integration testing
* End-to-end transaction scenarios

### Phase 4 — AI-Augmented Testing

**Planned**

* LangChain
* LangGraph
* ChromaDB
* Ollama
* Historical failure retrieval
* AI-assisted RCA
* AI-generated test scenarios

### Phase 5 — Operational Platform

**Planned**

* Docker
* Docker Compose
* OpenTelemetry
* GitHub Actions
* CI/CD automation
* Security hardening
* Production-oriented observability

---

# Summary Rationale

PayGuard AI deliberately combines technologies that support both sides of the project's engineering objective.

## Payment and QA Engineering

* **FastAPI** provides the Mock Payment Gateway.
* **Pydantic** provides structured API validation.
* **Pytest** provides the primary automated testing framework.
* **React and TypeScript** provide the current transaction-monitoring dashboard.
* **Selenium** is planned for realistic browser-level automation.
* **State machines, services, repositories, and domain exceptions** provide a maintainable payment-domain architecture.
* **PostgreSQL and SQLAlchemy** are planned for durable, transactional persistence.

## Applied AI

* **LangChain** and **LangGraph** are planned for AI workflow orchestration.
* **ChromaDB** is planned for historical failure retrieval.
* **Ollama** is planned for local LLM inference.
* **OpenTelemetry** is planned for observability across application and AI workflows.

The overall technology strategy is therefore not simply a collection of popular tools. Each technology has a defined role in the evolution of the system:

```text
Reliable Payment Domain
    |
    v
Automated Validation
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
    |
    v
CI/CD + Observability
```

The immediate priority is the **payment reliability foundation**, particularly persistent storage, monetary correctness, idempotency, concurrency safety, and durable transaction history.

The dashboard and API foundation are already sufficient to support the next engineering stage. AI should be introduced after the system produces reliable, persistent, and sufficiently rich failure and transaction data. That gives the AI something useful to analyze instead of asking it to perform interpretive gymnastics over disappearing in-memory state.
