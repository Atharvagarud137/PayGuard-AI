# TECH_STACK.md — PayGuard AI

## Purpose

This document describes the technology stack used by PayGuard AI, the role of each technology, and the reasoning behind the architectural choices.

The stack is intentionally divided into **currently implemented technologies** and **planned technologies**. A dependency being installed in the development environment does not necessarily mean that it is currently part of the implemented application architecture.

PayGuard AI combines three primary engineering areas:

1. **Payment-domain software engineering**
2. **Automated quality engineering and browser validation**
3. **Applied AI for intelligent test analysis and test generation**

The project is being developed incrementally. The current implementation already includes the payment domain, reliability controls such as monetary precision and idempotency, a React/TypeScript dashboard, and Playwright-based E2E automation. The next major architectural stage is durable persistence and stronger concurrency guarantees.

Humanity has somehow decided that an LLM should analyze systems before those systems can reliably explain themselves, so the architecture deliberately puts correctness first.

---

# Current Technology Stack

## Backend / System Under Test

| Technology | Purpose | Status | Why Chosen |
|---|---|---|---|
| **Python 3.11** | Core application language | Implemented | Strong ecosystem for backend development, testing, automation, and AI engineering |
| **FastAPI** | Mock Payment Gateway framework | Implemented | Provides automatic OpenAPI documentation, request validation through Pydantic, and a lightweight architecture suitable for the simulated payment gateway |
| **Pydantic** | Request and response validation | Implemented | Provides structured validation for payment API payloads and integrates naturally with FastAPI |
| **Uvicorn** | ASGI application server | Implemented | Lightweight server for running the FastAPI application |
| **In-Memory Storage** | Current persistence implementation | Implemented | Keeps the current payment-domain implementation deterministic while the repository and service architecture are being validated |
| **Transaction Repository** | Persistence abstraction | Implemented | Separates payment business logic from the underlying storage implementation and provides a migration path toward PostgreSQL |

---

# Payment Domain Architecture

The payment engine uses several architectural patterns and domain components in addition to the framework stack.

| Component | Purpose | Status | Why Used |
|---|---|---|---|
| **Payment Service** | Payment business logic | Implemented | Keeps authorization, capture, settlement, and refund rules outside the HTTP layer |
| **Transaction State Machine** | Payment lifecycle validation | Implemented | Centralizes validation of legal transaction state transitions |
| **Domain Exceptions** | Payment-specific error handling | Implemented | Allows business logic to communicate typed domain failures without depending on HTTP-specific exceptions |
| **Repository Pattern** | Persistence abstraction | Implemented | Allows the current in-memory implementation to be replaced with persistent storage without tightly coupling business logic to a database |
| **Transaction History / Events** | Transaction traceability | Implemented | Records important lifecycle events associated with a transaction |
| **Audit Events** | Operational and security history | Implemented | Records important payment operations without storing raw card numbers |
| **Monetary Precision** | Financial calculation correctness | Implemented | Uses decimal-safe monetary handling rather than relying on binary floating-point arithmetic |
| **Idempotency** | Duplicate-request protection | Implemented | Prevents repeated requests using the same idempotency key from creating duplicate operations |
| **Failure Simulation** | Technical failure testing | Implemented | Provides deterministic failure scenarios for payment-system testing |

---

# Current Payment Lifecycle

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
````

The domain model explicitly validates valid and invalid transitions.

The lifecycle currently supports:

* Authorization
* Capture
* Settlement
* Full refund
* Partial refund
* Completion of remaining refund amounts
* Deterministic technical failure scenarios

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
| **Audit Events**        | Implemented | Records operational events without raw card numbers   |
| **Idempotency**         | Implemented | Prevents duplicate operations for repeated requests   |
| **Failure Simulation**  | Implemented | Supports deterministic technical failure scenarios    |

The current payment flow is intentionally simulated and does not connect to real card networks or production payment processors.

---

# Test Automation Stack

| Technology             | Purpose                                                   | Status      | Why Chosen                                                                                                                                     |
| ---------------------- | --------------------------------------------------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Pytest**             | Unit, service, state-machine, API, and E2E test execution | Implemented | Mature Python testing framework with strong fixture support and clean test organization                                                        |
| **Playwright**         | Browser/UI automation                                     | Implemented | Provides reliable browser automation, accessible-role selectors, strong debugging capabilities, and native support for modern web applications |
| **HTTPX**              | HTTP client                                               | Implemented | Provides lightweight HTTP communication for E2E fixtures and API interaction                                                                   |
| **FastAPI TestClient** | Application-level API testing                             | Implemented | Allows API behavior to be tested directly without requiring browser execution                                                                  |
| **Selenium**           | Browser/UI automation                                     | Not Used    | Previously considered, but Playwright is the selected browser automation framework for the project                                             |

Playwright is the project's current browser automation technology.

The E2E suite uses Page Object Model classes to separate browser interaction logic from test scenarios.

---

# Current Automated Test Baseline

The verified regression command is:

```powershell
pytest -v
```

The current verified baseline is:

```text
96 tests
96 passed
0 failed
```

The current test architecture covers:

```text
                    Pytest
                       |
       +---------------+----------------+
       |               |                |
       v               v                v
   Unit Tests       API Tests        E2E Tests
       |               |                |
       v               v                v
 State Machine     FastAPI APIs      Playwright
 Payment Service   Payment Domain    Dashboard
 Audit Service     Idempotency       User Flows
 Money Validation  Failure Cases     Transactions
```

The project also supports targeted E2E execution:

```powershell
pytest tests\e2e\test_transactions.py -v
```

and the complete E2E suite:

```powershell
pytest tests\e2e -v
```

The current E2E suite validates:

* Dashboard loading
* Card issuance through the browser
* Transactions page loading
* Transactions empty state
* API-created authorized transactions appearing in the dashboard
* Transaction lifecycle dialog access

---

# Frontend / Dashboard

The project contains a React/TypeScript dashboard used for visualizing payment-system activity and transaction lifecycles.

| Technology     | Purpose                                   | Status      | Why Chosen                                                                                   |
| -------------- | ----------------------------------------- | ----------- | -------------------------------------------------------------------------------------------- |
| **React**      | Web Dashboard                             | Implemented | Provides a component-based architecture suitable for a transaction-monitoring interface      |
| **TypeScript** | Frontend language                         | Implemented | Provides static typing for frontend state, API responses, and UI components                  |
| **CSS**        | Dashboard styling                         | Implemented | Provides control over the payment-operations dashboard interface and lifecycle visualization |
| **Vite**       | Frontend development server/build tooling | Implemented | Provides a fast development environment suitable for the React/TypeScript dashboard          |
| **Playwright** | Browser/UI automation                     | Implemented | Validates user-visible dashboard behavior against a real browser                             |

The dashboard currently focuses on:

* Transaction visibility
* Transaction status
* Payment amounts
* Transaction lifecycle
* Card-related information
* Payment-system operational views
* Empty and loading states
* Transaction lifecycle inspection

The dashboard is treated as a presentation layer. Payment-domain business rules remain in the backend domain and service layers.

---

# Frontend Automation Architecture

The E2E automation follows a Page Object Model structure.

```text
tests/e2e/
    |
    +-- conftest.py
    |
    +-- test_dashboard_smoke.py
    |
    +-- test_cards.py
    |
    +-- test_transactions.py
    |
    +-- pages/
    |     |
    |     +-- dashboard_page.py
    |     +-- transactions_page.py
    |
    +-- components/
          |
          +-- reusable UI components
```

The Page Objects intentionally prefer:

* Accessible roles
* Accessible names
* Semantic application behavior
* Stable component-level selectors

over highly specific CSS selectors wherever practical.

For example, the Transactions Page Object locates the navigation control using its accessible role and a regular expression because the UI includes an icon in the accessible name.

This reduces unnecessary coupling between the E2E suite and presentational markup.

---

# E2E Environment

The current E2E environment expects the frontend and backend services to already be running.

Backend:

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8000
```

Frontend:

```text
http://localhost:5173
```

Backend:

```text
http://localhost:8000
```

The Playwright fixtures create deterministic backend state through HTTP requests before executing browser assertions.

For example, transaction lifecycle tests create:

```text
Fresh Card
    |
    v
Authorization API
    |
    v
AUTHORIZED Transaction
    |
    v
Browser
    |
    v
Transactions Page
    |
    v
Lifecycle Dialog
```

This avoids requiring the browser test itself to perform every prerequisite operation through the UI.

---

# AI Engineering Stack

The AI layer is part of the planned PayGuard AI architecture.

It is not currently required for the core payment-domain regression suite.

| Technology        | Purpose                          | Status  | Why Chosen                                                                       |
| ----------------- | -------------------------------- | ------- | -------------------------------------------------------------------------------- |
| **LangChain**     | LLM orchestration                | Planned | Provides components for retrieval and LLM-based workflows                        |
| **LangGraph**     | AI workflow orchestration        | Planned | Provides a structured approach for multi-step workflows such as failure analysis |
| **ChromaDB**      | Vector storage                   | Planned | Lightweight local vector database suitable for historical failure retrieval      |
| **Ollama**        | Local LLM inference              | Planned | Enables local model execution without requiring a hosted LLM API                 |
| **OpenTelemetry** | Application and AI observability | Planned | Provides a foundation for tracing application and AI workflows                   |

---

# Planned AI Architecture

## AI Root Cause Analysis

The planned RCA pipeline will follow:

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

---

# AI Test Case Generation

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

| Technology                      | Status      | Purpose                                                       |
| ------------------------------- | ----------- | ------------------------------------------------------------- |
| **In-Memory Storage**           | Implemented | Current persistence mechanism for the Mock Payment Gateway    |
| **Repository Abstraction**      | Implemented | Isolates application services from the storage implementation |
| **Audit Event Storage**         | Implemented | Stores audit records during the application lifetime          |
| **Transaction History Storage** | Implemented | Stores lifecycle events during the application lifetime       |

The current storage implementation provides deterministic application state but does not provide durable persistence.

It does not currently provide:

* Persistence across application restarts
* Database transactions
* Transaction isolation
* Row-level locking
* Database-level constraints
* Distributed concurrency control
* Durable transaction history

These limitations define the next major persistence stage.

---

# Planned Persistence

| Technology     | Status  | Purpose                       | Why Planned                                                                           |
| -------------- | ------- | ----------------------------- | ------------------------------------------------------------------------------------- |
| **SQLAlchemy** | Planned | Database abstraction / ORM    | Provides a structured persistence layer for PostgreSQL integration                    |
| **PostgreSQL** | Planned | Durable transactional storage | Provides persistence, transactional guarantees, constraints, and concurrency controls |

The repository abstraction is intended to allow this migration without requiring payment business logic to depend directly on PostgreSQL.

Planned architecture:

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

The migration should preserve the existing payment-domain interfaces wherever practical.

---

# Reliability Technology Requirements

Several reliability controls are already implemented. Others remain architectural priorities.

| Capability                 | Status                | Purpose                                                                                    |
| -------------------------- | --------------------- | ------------------------------------------------------------------------------------------ |
| **Monetary Precision**     | Implemented           | Prevent floating-point inaccuracies in financial calculations                              |
| **Idempotency**            | Implemented           | Prevent duplicate payment operations caused by repeated requests                           |
| **Concurrency Control**    | Planned               | Prevent race conditions involving simultaneous transaction operations                      |
| **Database Transactions**  | Planned               | Ensure related state changes are committed or rolled back consistently                     |
| **Durable Audit History**  | Planned               | Preserve audit and transaction history across application restarts                         |
| **Failure Recovery**       | Partially Implemented | Deterministic technical failure scenarios exist; broader recovery semantics remain planned |
| **Consistency Validation** | Implemented           | Payment-domain tests validate lifecycle and monetary consistency                           |

The current implementation deliberately establishes monetary correctness and idempotency before introducing database-backed concurrency controls.

---

# Idempotency Architecture

Idempotency is currently implemented at the application storage/API level.

The current authorization behavior distinguishes between:

```text
Same Idempotency-Key
        |
        +-- Same Request
        |      |
        |      v
        |   Replay Original Response
        |
        +-- Different Request
               |
               v
             HTTP 409
```

The current test suite verifies:

* Replaying the same request
* Preventing duplicate balance deductions
* Rejecting a different request using the same key
* Allowing different idempotency keys to represent separate operations
* Preserving non-idempotent behavior when no key is supplied

The current implementation is application-memory based. Durable idempotency storage will become important when PostgreSQL is introduced.

---

# Monetary Precision

Financial calculations use decimal-safe arithmetic rather than relying on binary floating-point behavior.

The test suite validates:

* Exact decimal arithmetic
* Valid two-decimal monetary values
* Rejection of excessive decimal precision
* Rejection of zero authorization amounts
* Rejection of negative authorization amounts
* Decimal-safe capture calculations
* Decimal-safe refund calculations

This is a foundational payment-domain concern and is therefore implemented before database migration.

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

| Technology         | Purpose                                        | Status      | Why Chosen                                                                                  |
| ------------------ | ---------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------- |
| **GitHub Actions** | Continuous integration and automated execution | Planned     | Integrates directly with GitHub and can execute the regression suite as the project evolves |
| **Git**            | Version control                                | Implemented | Provides source-code versioning and development workflow                                    |

The intended CI/CD pipeline will eventually execute the appropriate testing layers and may trigger AI-assisted analysis when failures occur.

Planned workflow:

```text
Commit / Pull Request
    |
    v
Unit / Domain Tests
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
E2E / Playwright Tests
    |
    v
AI-Assisted Analysis
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
| **Audit Events**       | Operational/security traceability  | Implemented |

Observability will become particularly important when the project introduces:

* PostgreSQL
* Asynchronous processing
* AI workflows
* CI/CD execution
* Failure correlation
* Multiple application services
* Persistent transaction history

The existing transaction history and audit-event model provide a domain-level foundation for later observability work.

---

# Development Environment

| Tool                           | Purpose                               | Status      |
| ------------------------------ | ------------------------------------- | ----------- |
| **PyCharm / IntelliJ IDEA**    | Primary development environment       | Implemented |
| **Git**                        | Version control                       | Implemented |
| **Python venv**                | Dependency isolation                  | Implemented |
| **PowerShell**                 | Local development commands on Windows | Implemented |
| **React / TypeScript Tooling** | Dashboard development                 | Implemented |
| **Vite**                       | Frontend development server           | Implemented |
| **Playwright**                 | Browser automation                    | Implemented |
| **Docker Desktop**             | Container development                 | Planned     |
| **Ollama**                     | Local LLM runtime                     | Planned     |

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

The project uses HTTPX for HTTP-based test fixtures and related application testing.

The exact installed HTTPX version should be treated as an environment detail rather than a permanent architectural requirement.

Dependency changes should be handled deliberately rather than changing the framework stack simply to eliminate warnings.

Any dependency change must be followed by the complete regression suite:

```powershell
pytest -v
```

The current verified functional baseline is:

```text
96 tests
96 passed
0 failed
```

If dependency versions change, the exact versions should be documented again based on the verified development environment rather than copied indefinitely from an older environment snapshot.

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

---

## 2. Persistence before advanced automation

The system should establish durable and consistent transaction behavior before building automation and AI features that depend heavily on historical transaction data.

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

---

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

---

## 4. Testability

Business rules should be testable independently from the HTTP and browser layers.

This is why the project contains separate:

* State-machine tests
* Payment-service tests
* API tests
* Audit-service tests
* Monetary validation tests
* Browser-level E2E tests

The Page Object Model further separates browser interaction logic from individual E2E scenarios.

---

## 5. Playwright-first browser automation

Playwright is the selected browser automation framework for the project.

The choice is based on:

* Reliable browser automation
* Modern web-application support
* Accessible-role selectors
* Strong auto-waiting behavior
* Browser context isolation
* Built-in Chromium/Firefox/WebKit support
* Useful debugging and tracing capabilities
* Good integration with Pytest through the Playwright plugin

Selenium is therefore not part of the current browser automation implementation.

---

## 6. Local-first AI

The planned AI layer uses Ollama and local models to support:

* Local experimentation
* Reproducible demonstrations
* Reduced external API dependency
* Avoidance of mandatory hosted-LLM costs

---

## 7. Production-oriented payment design

Although PayGuard AI is a mock payment gateway rather than a production payment processor, architectural decisions are made with payment-system concerns in mind.

The architecture addresses or plans for:

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

---

## 8. Incremental complexity

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
Monetary Precision
    |
    v
Idempotency
    |
    v
Dashboard
    |
    v
Playwright E2E Automation
    |
    v
Persistent Storage
    |
    v
Concurrency Controls
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

| Area              | Current                                      | Planned                                |
| ----------------- | -------------------------------------------- | -------------------------------------- |
| Language          | Python 3.11                                  | —                                      |
| Backend           | FastAPI                                      | —                                      |
| Validation        | Pydantic                                     | —                                      |
| Server            | Uvicorn                                      | —                                      |
| Storage           | In-memory                                    | PostgreSQL                             |
| Persistence Layer | Repository                                   | SQLAlchemy + PostgreSQL                |
| Domain            | State Machine + Services + Domain Exceptions | Extended payment reliability controls  |
| Monetary Handling | Decimal-safe implementation                  | —                                      |
| Idempotency       | Implemented                                  | Durable database-backed implementation |
| API Testing       | Pytest                                       | Expanded integration testing           |
| Service Testing   | Pytest                                       | Expanded reliability testing           |
| State Testing     | Pytest                                       | Expanded lifecycle testing             |
| Audit Testing     | Pytest                                       | Durable audit testing                  |
| Dashboard         | React + TypeScript + CSS                     | Expanded dashboard functionality       |
| Frontend Tooling  | Vite                                         | —                                      |
| UI Automation     | Playwright                                   | Expanded cross-browser E2E coverage    |
| AI Orchestration  | —                                            | LangChain + LangGraph                  |
| Vector Database   | —                                            | ChromaDB                               |
| Local LLM         | —                                            | Ollama                                 |
| Observability     | Transaction/Audit Events                     | OpenTelemetry + Structured Logging     |
| Containers        | —                                            | Docker + Docker Compose                |
| CI/CD             | —                                            | GitHub Actions                         |

---

# Recommended Technology Evolution

The intended implementation sequence is:

## Phase 1 — Core Payment Domain

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
* Audit events
* Transaction history

---

## Phase 2 — Payment Reliability

**Partially Implemented / Current Priority**

* Monetary precision
* Idempotency
* Consistency validation
* PostgreSQL
* SQLAlchemy
* Database transactions
* Concurrency control
* Durable transaction history
* Durable idempotency records
* Persistence tests

The first three reliability concerns are already represented in the current application and test suite. PostgreSQL-backed durability and concurrency controls remain the next major persistence work.

---

## Phase 3 — Automation Platform

**Implemented / Expanding**

* React / TypeScript dashboard
* Vite frontend tooling
* Playwright
* Page Object Model
* API-backed E2E fixtures
* Dashboard smoke tests
* Card E2E scenarios
* Transaction E2E scenarios
* Expanded API testing
* Integration testing
* End-to-end transaction lifecycle scenarios

---

## Phase 4 — AI-Augmented Testing

**Planned**

* LangChain
* LangGraph
* ChromaDB
* Ollama
* Historical failure retrieval
* AI-assisted RCA
* AI-generated test scenarios
* Human review of generated scenarios

---

## Phase 5 — Operational Platform

**Planned**

* Docker
* Docker Compose
* OpenTelemetry
* GitHub Actions
* CI/CD automation
* Security hardening
* Production-oriented observability
* Durable operational telemetry

---

# Summary Rationale

PayGuard AI deliberately combines technologies that support the project's payment-engineering, quality-engineering, and AI objectives.

## Payment and QA Engineering

* **FastAPI** provides the Mock Payment Gateway.
* **Pydantic** provides structured API validation.
* **Pytest** provides the primary automated testing framework.
* **React and TypeScript** provide the transaction-monitoring dashboard.
* **Vite** provides the frontend development environment.
* **Playwright** provides browser-level E2E automation.
* **Page Objects** keep browser interaction logic maintainable.
* **State machines, services, repositories, and domain exceptions** provide a maintainable payment-domain architecture.
* **Decimal-safe monetary handling** protects financial calculations.
* **Idempotency** protects payment operations from duplicate requests.
* **PostgreSQL and SQLAlchemy** are planned for durable transactional persistence.

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
Monetary Correctness
    |
    v
Idempotent Operations
    |
    v
Automated Validation
    |
    v
Browser-Level E2E Automation
    |
    v
Persistent + Concurrent Architecture
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

The immediate architectural priority is **durable payment reliability**, particularly:

* PostgreSQL persistence
* Database transactions
* Concurrency safety
* Durable idempotency
* Durable audit history
* Failure recovery

The current backend, dashboard, API test suite, and Playwright E2E foundation are already sufficiently mature to support that next stage.



