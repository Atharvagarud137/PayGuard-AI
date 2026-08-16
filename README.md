# PayGuard AI

**AI-Augmented Test Automation Framework for Payment Systems**

PayGuard AI is a portfolio project focused on combining **payment-domain engineering, quality engineering, test automation, software architecture, reliability engineering, and applied AI**.

The project simulates a payment gateway using FastAPI and validates its behavior through layered automated tests.

The current payment lifecycle is:

```text
Card Issuance
      ↓
Authorization
      ↓
Capture
      ↓
Settlement
      ↓
Refund / Partial Refund
````

The project is being developed incrementally. The current foundation establishes deterministic payment-domain behavior and automated regression coverage before introducing stronger persistence, reliability controls, UI automation, CI/CD, observability, and AI-assisted engineering capabilities.

---

# Project at a Glance

| Area                      | Current Status           |
| ------------------------- | ------------------------ |
| Mock Payment Gateway      | Implemented              |
| Payment Domain            | Implemented              |
| Transaction State Machine | Implemented              |
| Payment Service           | Implemented              |
| Repository Abstraction    | Implemented              |
| In-Memory Persistence     | Implemented              |
| API Test Automation       | Implemented              |
| Payment Service Tests     | Implemented              |
| State Machine Tests       | Implemented              |
| Regression Baseline       | **64 passed / 0 failed** |
| React/Vite Dashboard      | In Development           |
| PostgreSQL Persistence    | Next                     |
| Idempotency               | Next                     |
| Concurrency Controls      | Next                     |
| Selenium Automation       | Planned                  |
| CI/CD                     | Planned                  |
| AI Root Cause Analysis    | Planned                  |
| AI Test Generation        | Planned                  |
| ChromaDB                  | Planned                  |
| Ollama                    | Planned                  |
| OpenTelemetry             | Planned                  |
| Docker                    | Planned                  |

---

# Documentation

The project documentation is intentionally divided by engineering concern so that the repository tells the complete story rather than dumping everything into one enormous README.

## Core Project Documentation

| Document                                     | Description                                                                                                                |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| [Product Requirements Document](docs/PRD.md) | Product goals, requirements, scope, roadmap, success criteria, risks, constraints, and definition of done                  |
| [Architecture](docs/ARCHITECTURE.md)         | System architecture, component boundaries, domain/service/repository design, and planned evolution                         |
| [Test Strategy](docs/TEST_STRATEGY.md)       | Test pyramid, test layers, coverage strategy, failure testing, regression strategy, and future AI-assisted testing         |
| [Technology Stack](docs/TECH_STACK.md)       | Current and planned technologies, architectural rationale, dependency strategy, and technology-selection principles        |
| [API Specification](docs/API_SPEC.md)        | Mock Payment Gateway REST API, endpoints, request/response behavior, status codes, lifecycle rules, and failure simulation |
| [AI Pipeline](docs/AI_PIPELINE.md)           | Planned AI Root Cause Analysis and AI test-case-generation pipelines, retrieval architecture, prompting, and evaluation    |
| [Setup Guide](docs/SETUP.md)                 | Local development setup, virtual environment, dependency installation, application startup, testing, and troubleshooting   |

### Recommended Reading Order

For someone reviewing the project for the first time:

```text
README.md
   ↓
PRD.md
   ↓
ARCHITECTURE.md
   ↓
API_SPEC.md
   ↓
TEST_STRATEGY.md
   ↓
TECH_STACK.md
   ↓
SETUP.md
   ↓
AI_PIPELINE.md
```

This order moves from **why the project exists → how it is designed → what the API does → how it is tested → what technologies are used → how to run it → how AI will eventually augment it**.

---

# Why This Project Exists

Payment systems are stateful, failure-sensitive systems where seemingly small defects can create significant financial and operational consequences.

Traditional QA automation can validate whether an expected response was returned, but payment testing also requires understanding:

* Transaction state
* Lifecycle transitions
* Amount consistency
* Invalid operations
* Partial captures
* Partial refunds
* Duplicate operations
* Failure scenarios
* Transaction history
* Persistence
* Concurrency
* Root causes behind test failures

PayGuard AI is intended to evolve into a platform that combines **deterministic payment-domain testing** with **AI-assisted engineering**.

The long-term objectives include:

* Automated validation of payment transaction lifecycles
* Positive, negative, and boundary-condition testing
* API automation
* UI automation
* Failure simulation
* Persistent transaction and audit data
* Reliability and concurrency testing
* AI-assisted root cause analysis
* AI-generated test-case suggestions
* Observability
* CI/CD-based automated validation

The current milestone deliberately prioritizes the payment-domain foundation over AI features.

---

# Current Milestone

## Payment Domain + Automated Regression Foundation

The core Mock Payment Gateway is implemented and covered by an automated regression suite.

Current capabilities include:

* Card issuance
* Transaction authorization
* Transaction capture
* Settlement
* Full refunds
* Partial refunds
* Transaction lookup
* Payment lifecycle state validation
* Transaction state machine
* Payment service layer
* Transaction repository abstraction
* Typed payment-domain exceptions
* Transaction history/events
* Simulated technical failure scenarios

The current implementation uses **in-memory persistence** through the repository abstraction.

The next major milestone is **payment reliability and persistent storage**.

---

# Current Test Baseline

The current automated test architecture contains three primary layers:

| Test Layer      |  Tests | Status                   |
| --------------- | -----: | ------------------------ |
| State Machine   |     14 | Passing                  |
| Payment Service |     14 | Passing                  |
| API             |     36 | Passing                  |
| **Total**       | **64** | **64 Passed / 0 Failed** |

Current regression baseline:

```text
64 tests
64 passed
0 failed
```

The test architecture intentionally separates domain behavior from service behavior and externally observable API behavior.

```text
State Machine Tests
        ↓
Payment Service Tests
        ↓
API Tests
```

The detailed testing strategy is documented in [TEST_STRATEGY.md](docs/TEST_STRATEGY.md).

---

# Current Backend Architecture

The current payment transaction flow follows a layered architecture:

```text
┌───────────────────────────────┐
│          FastAPI API          │
│     HTTP / Request Layer      │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│       Payment Service         │
│     Application Business      │
│            Logic              │
└───────────────┬───────────────┘
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
┌───────────────┐  ┌──────────────────┐
│ State Machine │  │ Domain Exceptions│
└───────┬───────┘  └──────────────────┘
        │
        ▼
┌───────────────────────────────┐
│    Transaction Repository     │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│      In-Memory Storage        │
└───────────────────────────────┘
```

The architecture deliberately separates HTTP concerns from payment-domain business logic.

For the complete architectural design and future evolution, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## API Layer

The API layer is responsible for:

* HTTP request handling
* Request validation
* Endpoint routing
* HTTP response formatting
* Mapping domain exceptions to HTTP status codes
* Deterministic failure simulation

The API is implemented using FastAPI and Pydantic.

Detailed endpoint behavior is documented in [API_SPEC.md](docs/API_SPEC.md).

---

## Payment Service Layer

The Payment Service is responsible for application-level payment operations including:

* Transaction retrieval
* Capture business rules
* Settlement business rules
* Refund business rules
* Amount validation
* Transaction state changes
* Transaction history updates
* Persistence through the repository

The service layer keeps payment behavior outside the HTTP layer.

---

## Domain Layer

The domain layer is responsible for:

* Transaction lifecycle states
* Valid state transitions
* Invalid state detection
* Payment-domain rules
* Typed domain exceptions

The state machine provides a centralized mechanism for preventing illegal transaction transitions.

---

## Repository Layer

The repository provides an abstraction between the payment service and the storage implementation.

This allows the application to transition from:

```text
In-Memory Storage
```

to:

```text
PostgreSQL
```

without coupling payment business logic directly to database-specific implementation details.

---

# Payment Transaction Lifecycle

The current transaction lifecycle is explicitly modeled as:

```text
                 ┌──────────────┐
                 │  AUTHORIZED  │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │   CAPTURED   │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │   SETTLED    │
                 └──────┬───────┘
                        │
                ┌───────┴────────┐
                │                │
                ▼                ▼
       ┌──────────────────┐  ┌──────────────┐
       │PARTIALLY_REFUNDED│  │   REFUNDED   │
       └────────┬─────────┘  └──────────────┘
                │
                │ remaining amount refunded
                ▼
         ┌──────────────┐
         │   REFUNDED   │
         └──────────────┘
```

A declined authorization is terminal:

```text
AUTHORIZATION
      |
      +---- insufficient funds ----> DECLINED
```

The state machine explicitly prevents invalid lifecycle transitions.

Examples include:

* Capturing a declined transaction
* Capturing an already captured transaction
* Capturing a settled transaction
* Settling an authorized transaction before capture
* Settling an already settled transaction
* Refunding an unsettled transaction
* Refunding more than the remaining refundable amount
* Fully refunding an already fully refunded transaction

These rules are independently tested by the state-machine test suite.

---

# Transaction History

Transactions maintain lifecycle history events.

The history records significant transaction state changes associated with:

* Authorization
* Capture
* Settlement
* Partial refund
* Full refund
* Other recorded transaction lifecycle events

The transaction history is currently application-level data backed by in-memory persistence.

A future persistence layer will make this history durable and more suitable for:

* Debugging
* Auditability
* Reliability analysis
* Failure investigation
* Future AI-assisted root cause analysis

---

# Core Components

| Component                | Current Status | Description                                                        |
| ------------------------ | -------------- | ------------------------------------------------------------------ |
| Mock Payment Gateway     | Implemented    | FastAPI service simulating core payment transaction flows          |
| Payment Domain           | Implemented    | Transaction lifecycle and payment-domain rules                     |
| State Machine            | Implemented    | Explicit validation of payment transaction state transitions       |
| Payment Service          | Implemented    | Application layer containing capture, settlement, and refund logic |
| Transaction Repository   | Implemented    | Persistence abstraction for transaction data                       |
| In-Memory Storage        | Implemented    | Current transaction storage implementation                         |
| Card Issuance            | Implemented    | Creates simulated payment cards                                    |
| Authorization            | Implemented    | Validates cards and creates authorized transactions                |
| Capture                  | Implemented    | Captures authorized transaction amounts                            |
| Settlement               | Implemented    | Settles captured transactions                                      |
| Full Refund              | Implemented    | Refunds a settled transaction completely                           |
| Partial Refund           | Implemented    | Supports refunds smaller than the remaining refundable amount      |
| Transaction Lookup       | Implemented    | Retrieves transaction details and lifecycle history                |
| API Test Suite           | Implemented    | Pytest coverage for positive, negative, and boundary scenarios     |
| Service Test Suite       | Implemented    | Tests payment business logic independently of HTTP                 |
| State Machine Test Suite | Implemented    | Tests transaction lifecycle transitions                            |
| Web Dashboard            | In Development | React/Vite dashboard for payment and transaction visibility        |
| Transaction Lifecycle UI | In Development | Dashboard interface for inspecting transaction lifecycle           |
| PostgreSQL Persistence   | Planned        | Durable transaction and event storage                              |
| Audit/Event Persistence  | Planned        | Durable lifecycle and transaction event history                    |
| Selenium UI Tests        | Planned        | Automated validation of dashboard behavior                         |
| AI RCA Engine            | Planned        | AI-assisted analysis of test failures                              |
| AI Test Case Generator   | Planned        | LLM-assisted suggestions for additional test scenarios             |
| Observability            | Planned        | Metrics, traces, and structured telemetry                          |
| Containerization         | Planned        | Docker-based service orchestration                                 |
| CI/CD Pipeline           | Planned        | Automated regression and future AI-assisted workflows              |

---

# Web Dashboard

A React/Vite dashboard is being developed as the primary visual interface for interacting with the Mock Payment Gateway.

Current dashboard functionality includes:

* Payment gateway overview
* Transaction visibility
* Transaction lifecycle inspection
* Card management
* Card issuance
* Transaction status
* Transaction amounts
* Transaction history

The dashboard is designed around the complete transaction lifecycle rather than treating transactions as isolated records.

A transaction can be inspected from authorization through:

```text
AUTHORIZED
     ↓
CAPTURED
     ↓
SETTLED
     ↓
REFUNDED
```

including partial-refund scenarios.

The dashboard is also intended to become the primary System Under Test for future Selenium automation.

---

# Transaction Lifecycle Visualization

The dashboard provides a lifecycle view for an individual transaction.

The intended model is:

```text
AUTHORIZED ───► CAPTURED ───► SETTLED ───► REFUNDED
```

For partially refunded transactions:

```text
AUTHORIZED
     ↓
CAPTURED
     ↓
SETTLED
     ↓
PARTIALLY REFUNDED
     ↓
REFUNDED
```

The lifecycle UI distinguishes between:

* Completed stages
* Current stage
* Upcoming stages
* Failed authorization

The lifecycle visualization is a presentation layer over the payment-domain state and transaction history.

It does not replace the backend state machine.

---

# Tech Stack

## Current / Core

* **Python 3.11**
* **FastAPI**
* **Pydantic**
* **Uvicorn**
* **Pytest**
* **React**
* **TypeScript**
* **Vite**
* Repository pattern
* Domain state machine
* Domain exceptions
* In-memory persistence

## Planned / Future

* **Selenium** for UI automation
* **SQLAlchemy** for database access
* **PostgreSQL** for persistent storage
* **LangChain** for AI orchestration
* **LangGraph** for workflow orchestration
* **ChromaDB** for vector-based retrieval
* **Ollama** for local LLM execution
* **OpenTelemetry** for observability
* **Docker** for containerization
* **GitHub Actions** for CI/CD

Technologies listed as planned are part of the intended architecture and should not be interpreted as fully implemented functionality.

The complete technology rationale is documented in [TECH_STACK.md](docs/TECH_STACK.md).

---

# API

The Mock Payment Gateway currently exposes endpoints for:

* Card issuance
* Authorization
* Capture
* Settlement
* Refund
* Transaction lookup
* Application health

The API also supports deterministic failure simulation through:

```text
X-Simulate-Failure
```

Supported failure scenarios include:

```text
TIMEOUT
NETWORK_ERROR
INVALID_RESPONSE
```

For complete request/response definitions, business rules, status codes, lifecycle behavior, and failure simulation details, see:

**[API Specification →](docs/API_SPEC.md)**

---

# Failure Simulation

The API supports deterministic technical failure simulation through the `X-Simulate-Failure` request header.

The intended behavior is:

```text
X-Simulate-Failure: TIMEOUT
        ↓
HTTP 504

X-Simulate-Failure: NETWORK_ERROR
        ↓
HTTP 502

X-Simulate-Failure: INVALID_RESPONSE
        ↓
HTTP 500
```

The purpose of this mechanism is to provide reproducible technical failures for:

* Reliability testing
* Negative API testing
* Failure-handling validation
* Future AI root cause analysis

---

# Test Architecture

The current test architecture separates concerns across multiple layers:

```text
┌─────────────────────────┐
│       API Tests         │
│          36             │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Payment Service Tests │
│          14             │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   State Machine Tests   │
│          14             │
└─────────────────────────┘
```

Current baseline:

```text
API Tests              36
Payment Service        14
State Machine          14
────────────────────────
Total                  64

Passed                 64
Failed                  0
```

### API Tests

Validate externally observable payment gateway behavior, including:

* Request validation
* Successful operations
* Invalid operations
* Failure responses
* Transaction lifecycle behavior

### Payment Service Tests

Validate payment business logic independently from HTTP.

### State Machine Tests

Validate transaction lifecycle transitions independently from both HTTP and infrastructure.

This separation makes failures easier to localize and provides a stronger foundation for future AI-assisted analysis.

The complete testing approach is documented in [TEST_STRATEGY.md](docs/TEST_STRATEGY.md).

---

# Payment Reliability Roadmap

The next major engineering milestone is **payment reliability and persistence**.

The current in-memory architecture is intentionally simple, but it does not provide the guarantees expected from a realistic payment system.

The next phase will address:

### Monetary Safety

* Decimal-based monetary representation
* Explicit currency handling
* Amount consistency
* Rounding rules
* Prevention of floating-point inconsistencies

### Idempotency

* Duplicate authorization protection
* Duplicate capture protection
* Duplicate settlement protection
* Duplicate refund protection
* Idempotency-key handling

### Concurrency

* Concurrent transaction updates
* Race-condition prevention
* Database locking
* Transaction isolation
* Consistent state transitions

### Persistence

* Durable transactions
* Durable lifecycle history
* Database constraints
* Atomic updates
* Recovery after application restart

### Transaction Consistency

* Explicit transaction boundaries
* Rollback behavior
* Consistent state transitions
* Failure recovery

These capabilities are more important than immediately adding AI functionality. A payment system with impressive AI and weak transaction guarantees is still a very efficient way to manufacture incorrect financial state.

---

# AI-Augmented Testing

AI is planned as an augmentation layer rather than a replacement for deterministic automation.

The planned AI capabilities are:

## AI Root Cause Analysis

When a test fails, the future AI pipeline will:

```text
Test Failure
      ↓
Failure Context Extraction
      ↓
Embedding
      ↓
Historical Failure Retrieval
      ↓
ChromaDB
      ↓
Local LLM via Ollama
      ↓
Root Cause Summary
```

The generated RCA should include:

* Likely failure category
* Relevant evidence
* Concise explanation
* Suggested corrective action where appropriate
* Confidence or uncertainty where appropriate

The AI must not present unsupported assumptions as established facts.

## AI Test Case Generation

The future test-generation pipeline will consume the FastAPI OpenAPI specification:

```text
FastAPI OpenAPI Specification
      ↓
LLM Analysis
      ↓
Endpoint / Schema Analysis
      ↓
Edge-Case Identification
      ↓
Test Scenario Suggestions
      ↓
Duplicate Detection
      ↓
Human Review
```

Candidate scenarios may include:

* Boundary values
* Missing fields
* Invalid values
* Invalid state transitions
* Payment-specific edge cases
* Concurrency scenarios
* Reliability scenarios
* Existing coverage gaps

Generated scenarios will remain suggestions until reviewed and validated by an engineer.

The detailed design is documented in [AI_PIPELINE.md](docs/AI_PIPELINE.md).

---

# AI Evaluation

AI functionality will be evaluated separately from the conventional test suite.

Initial RCA evaluation target:

> Correctly identify the failure category in at least 8 out of 10 deterministic evaluation scenarios.

The evaluation should consider:

* Evidence usage
* Relevance
* Accuracy
* Consistency
* Actionability
* Unsupported conclusions
* Hallucination rate

Initial AI test-generation target:

> Produce at least 5 relevant, non-duplicate edge-case scenarios for a selected endpoint.

Generated scenarios should be reviewed for:

* API correctness
* Domain correctness
* Relevance
* Non-duplication
* Executability
* Expected-result correctness

These are future evaluation targets, not claims about current AI functionality.

---

# Project Roadmap

The project is intentionally being developed in stages.

```text
Payment Gateway Foundation
          ↓
Domain State Machine
          ↓
Service Layer
          ↓
Repository Abstraction
          ↓
Payment Reliability
          ↓
PostgreSQL Persistence
          ↓
Durable Audit / Event History
          ↓
Dashboard + UI Automation
          ↓
CI/CD
          ↓
AI Root Cause Analysis
          ↓
AI Test Generation
          ↓
Observability + Security Hardening
```

The sequence is intentional.

The underlying payment system needs deterministic behavior, reliable state management, persistence, and test coverage before AI becomes genuinely useful.

---

# Current Project Status

## Milestone 1 — Payment Gateway Foundation

**Status: Complete**

* [x] Core payment APIs
* [x] Card issuance
* [x] Authorization
* [x] Capture
* [x] Settlement
* [x] Full refunds
* [x] Partial refunds
* [x] Transaction lookup
* [x] Failure simulation

---

## Milestone 2 — Domain Architecture and Testability

**Status: Complete**

* [x] Transaction state machine
* [x] Payment service layer
* [x] Repository abstraction
* [x] Typed domain exceptions
* [x] Transaction lookup
* [x] Transaction history
* [x] Unit tests
* [x] API tests
* [x] 64-test regression baseline

---

## Milestone 3 — Payment Reliability and Persistence

**Status: Next**

Planned work:

* [ ] Monetary precision model
* [ ] Idempotency support
* [ ] Concurrency and race-condition handling
* [ ] Transaction consistency
* [ ] PostgreSQL persistence
* [ ] Durable transaction history
* [ ] Durable audit/event records
* [ ] Database constraints
* [ ] Explicit transaction boundaries
* [ ] Persistence failure handling
* [ ] Database-backed integration tests

---

## Milestone 4 — Automation Platform

**Status: In Development**

* [x] Initial web dashboard foundation
* [x] Transaction dashboard
* [x] Transaction lifecycle visualization
* [x] Card management interface
* [ ] Selenium UI automation
* [ ] Expanded API test coverage
* [ ] End-to-end payment scenarios
* [ ] CI/CD integration

---

## Milestone 5 — AI-Augmented Testing

**Status: Planned**

* [ ] Failure-log ingestion
* [ ] Failure context extraction
* [ ] Historical failure retrieval
* [ ] AI-assisted root cause analysis
* [ ] AI-generated test scenarios
* [ ] LLM evaluation and validation
* [ ] Human-review workflow

---

## Milestone 6 — Production-Oriented Platform Architecture

**Status: Planned**

* [ ] Dockerized services
* [ ] OpenTelemetry
* [ ] Structured observability
* [ ] Persistent audit architecture
* [ ] Scalable test execution
* [ ] Authentication and authorization
* [ ] Security hardening
* [ ] End-to-end CI/CD automation
* [ ] Performance testing

---

# Current Limitations

The current implementation is a development-oriented mock payment gateway and should not be considered a production payment processor.

Current limitations include:

* Transactions are stored in memory
* Application restart loses transaction state
* PostgreSQL persistence is not implemented
* Transaction history is not durably persisted
* Idempotency is not implemented
* Distributed concurrency control is not implemented
* Database-level transaction guarantees are not implemented
* Monetary precision hardening is not yet implemented
* Production card-network integrations are not implemented
* Authentication and authorization are not implemented
* PCI-compliant card-data handling is outside the current scope
* Full observability is not implemented
* AI root cause analysis is not implemented
* AI-generated test cases are not implemented
* Selenium automation is not implemented
* CI/CD automation is not implemented
* Docker orchestration is not implemented

These limitations represent the current development boundary and are explicitly tracked in the project roadmap.

---

# Reliability and Security Direction

Before the platform can be considered production-oriented, the following concerns must be addressed.

## Monetary Safety

* Decimal-based monetary representation
* Explicit currency handling
* Amount consistency across lifecycle operations
* Prevention of rounding-related inconsistencies

## Idempotency

* Duplicate authorization protection
* Duplicate capture protection
* Duplicate settlement protection
* Duplicate refund protection
* Idempotency-key handling

## Concurrency

* Concurrent transaction updates
* Race-condition prevention
* Database locking
* Transaction isolation
* Consistent state transitions

## Persistence

* Durable transactions
* Durable lifecycle history
* Database constraints
* Atomic updates
* Recovery after application restart

## Security

* Authentication
* Authorization
* Secrets management
* Input validation
* Rate limiting
* Secure logging
* Sensitive-data protection
* PCI-related design considerations

## Observability

* Structured logging
* Metrics
* Distributed tracing
* Transaction correlation IDs
* Failure telemetry

These areas are part of the planned reliability architecture.

---

# Development Philosophy

PayGuard AI follows several architectural principles.

## Domain First

Payment lifecycle rules are modeled explicitly instead of being scattered across API endpoints.

## Separation of Concerns

API handling, business logic, domain rules, persistence, and testing remain independently testable.

## Deterministic Behavior

The payment gateway should behave predictably enough that automated tests can reproduce both successful and failure scenarios.

## Testability

Core business behavior should be testable without requiring the HTTP server or external infrastructure.

## Persistence Abstraction

The repository pattern allows storage to evolve without rewriting payment business logic.

## AI as Augmentation

AI should assist engineers with failure analysis and test generation rather than becoming an unvalidated source of truth.

## Incremental Complexity

Architectural complexity is introduced only when the underlying behavior justifies it.

The project therefore prioritizes:

```text
Correctness
    ↓
Testability
    ↓
Reliability
    ↓
Persistence
    ↓
Automation
    ↓
Observability
    ↓
AI Augmentation
```

---

# Project Documentation Map

The repository documentation is organized around the major engineering concerns of PayGuard AI.

```text
                         PayGuard AI
                              |
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
      Product             Architecture          API
      PRD.md              ARCHITECTURE.md       API_SPEC.md
          │                   │                   │
          └───────────────────┼───────────────────┘
                              |
                              ▼
                         Quality Engineering
                              |
                    ┌─────────┴─────────┐
                    ▼                   ▼
             TEST_STRATEGY.md      TECH_STACK.md
                    │
                    ▼
               AI Augmentation
                    │
                    ▼
              AI_PIPELINE.md
                    │
                    ▼
               Development
                    │
                    ▼
                 SETUP.md
```

### Documentation Links

* 📋 [PRD.md](docs/PRD.md)
  Product requirements, scope, roadmap, success criteria, risks, assumptions, and definition of done.

* 🏗️ [ARCHITECTURE.md](docs/ARCHITECTURE.md)
  System architecture, component responsibilities, domain boundaries, persistence architecture, and planned evolution.

* 🧪 [TEST_STRATEGY.md](docs/TEST_STRATEGY.md)
  Test strategy, testing layers, regression approach, negative testing, failure simulation, coverage, and future AI-assisted testing.

* ⚙️ [TECH_STACK.md](docs/TECH_STACK.md)
  Current and planned technology stack, technology-selection rationale, dependency strategy, and infrastructure decisions.

* 🔌 [API_SPEC.md](docs/API_SPEC.md)
  Complete Mock Payment Gateway API contract, endpoint behavior, request/response models, lifecycle rules, and simulated failures.

* 🤖 [AI_PIPELINE.md](docs/AI_PIPELINE.md)
  AI Root Cause Analysis and AI test-case-generation architecture, retrieval strategy, prompt design, storage, and evaluation.

* 🛠️ [SETUP.md](docs/SETUP.md)
  Local setup, environment configuration, application startup, automated tests, troubleshooting, and development workflow.

---

# Project Structure

The project follows a separation of API, domain, service, persistence, testing, dashboard, AI, and documentation concerns.

```text
PayGuard-AI/
│
├── app/
│   ├── domain/
│   │   ├── state_machine/
│   │   └── exceptions/
│   │
│   ├── services/
│   │   └── payment_service/
│   │
│   ├── repositories/
│   │   └── transaction_repository/
│   │
│   └── api/
│       └── FastAPI endpoints
│
├── tests/
│   ├── api/
│   └── unit/
│
├── dashboard/
│   ├── src/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   └── package.json
│
├── ai_engine/
│   └── planned AI pipelines
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
└── .github/
    └── workflows/
```

The exact directory structure may evolve as additional components are implemented.

---

# Local Development

The current backend development workflow requires:

* Python 3.11
* Virtual environment
* FastAPI
* Uvicorn
* Pytest

The basic workflow is:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -v
uvicorn app.main:app --reload --reload-dir app --port 8000
```

The restricted Uvicorn reload directory is intentional because the project may be developed inside a OneDrive-synchronized directory.

For complete setup instructions, troubleshooting, environment requirements, and future service configuration, see:

**[Setup Guide →](docs/SETUP.md)**

---

# API Documentation

When the Mock Payment Gateway is running locally:

```text
Swagger UI:
http://localhost:8000/docs

OpenAPI:
http://localhost:8000/openapi.json

Health:
http://localhost:8000/
```

The generated OpenAPI specification is also intended to become the source for future AI-assisted test-case generation.

For the human-readable API contract:

**[API Specification →](docs/API_SPEC.md)**

---

# Engineering Documentation

The project deliberately separates product requirements, architecture, testing, technology choices, API behavior, AI design, and setup instructions.

This allows an engineer or reviewer to inspect the project from several different perspectives.

### Product Perspective

**[PRD.md](docs/PRD.md)** answers:

* Why does PayGuard AI exist?
* What problem does it solve?
* What are the functional requirements?
* What is implemented?
* What is planned?
* What are the success criteria?
* What is the roadmap?

### Architecture Perspective

**[ARCHITECTURE.md](docs/ARCHITECTURE.md)** answers:

* How are components separated?
* Where does payment business logic live?
* How does the state machine work?
* How does persistence abstraction work?
* How will PostgreSQL fit into the architecture?
* How will the platform evolve?

### Quality Engineering Perspective

**[TEST_STRATEGY.md](docs/TEST_STRATEGY.md)** answers:

* What is being tested?
* At which layer?
* Why are tests separated?
* How are negative and boundary cases handled?
* How are failures simulated?
* How will UI and AI testing be introduced?

### Technology Perspective

**[TECH_STACK.md](docs/TECH_STACK.md)** answers:

* Which technologies are currently implemented?
* Which technologies are planned?
* Why was each technology selected?
* How are dependencies managed?
* What is the intended infrastructure architecture?

### API Perspective

**[API_SPEC.md](docs/API_SPEC.md)** answers:

* Which endpoints exist?
* What requests do they accept?
* What responses do they produce?
* Which HTTP status codes are used?
* What payment-domain rules apply?
* How are technical failures simulated?

### AI Perspective

**[AI_PIPELINE.md](docs/AI_PIPELINE.md)** answers:

* How will test failures enter the AI pipeline?
* How will historical failures be retrieved?
* How will ChromaDB be used?
* How will Ollama provide local LLM inference?
* How will AI-generated test cases be produced?
* How will AI output be evaluated?

### Developer Perspective

**[SETUP.md](docs/SETUP.md)** answers:

* How do I install the project?
* How do I run the gateway?
* How do I run the tests?
* How do I configure the development environment?
* How do I troubleshoot common issues?

---

# Current Architectural Status

## Completed

* [x] FastAPI payment gateway
* [x] Card issuance
* [x] Authorization
* [x] Capture
* [x] Settlement
* [x] Full refunds
* [x] Partial refunds
* [x] Transaction lookup
* [x] Transaction history
* [x] Transaction state machine
* [x] Payment service layer
* [x] Transaction repository abstraction
* [x] Typed domain exceptions
* [x] API test suite
* [x] Payment service test suite
* [x] State-machine test suite
* [x] 64-test regression baseline
* [x] Initial React/Vite dashboard
* [x] Transaction dashboard
* [x] Transaction lifecycle visualization
* [x] Card management interface

## Next

* [ ] Monetary precision model
* [ ] Idempotency
* [ ] Concurrency safety
* [ ] PostgreSQL persistence
* [ ] Durable transaction history
* [ ] Durable audit/event storage
* [ ] Database constraints
* [ ] Transaction boundaries
* [ ] Persistence failure handling
* [ ] Database-backed integration tests
* [ ] Reliability testing
* [ ] Observability foundation

## Planned

* [ ] Selenium UI automation
* [ ] Expanded end-to-end payment scenarios
* [ ] AI root cause analysis
* [ ] AI test-case generation
* [ ] ChromaDB integration
* [ ] Ollama integration
* [ ] Docker deployment
* [ ] GitHub Actions CI/CD
* [ ] Authentication and authorization
* [ ] Production-oriented security hardening
* [ ] Performance testing
* [ ] OpenTelemetry

---

# Current Limitations

PayGuard AI is a **mock payment gateway and portfolio engineering project**, not a production payment processor.

The current implementation does not provide:

* Durable transaction storage
* Production database guarantees
* Idempotency
* Distributed concurrency control
* Real payment-network connectivity
* Production authentication
* Production authorization
* PCI-DSS certification
* Production cardholder-data processing
* Full observability
* AI-powered RCA
* AI-generated executable tests
* Automated UI regression
* Automated CI/CD
* Production deployment infrastructure

These limitations are intentional and tracked as future engineering milestones.

---

# Project Philosophy

PayGuard AI is built around a simple progression:

```text
Correctness
    ↓
Testability
    ↓
Reliability
    ↓
Persistence
    ↓
Automation
    ↓
Observability
    ↓
AI Augmentation
```

The project does not treat AI as a substitute for engineering fundamentals.

The payment domain must first behave correctly.

The test suite must then prove that behavior.

The system must then become reliable under persistence, concurrency, duplicate operations, and failure scenarios.

Only then does AI become genuinely useful as an engineering multiplier.

That ordering is deliberate. Otherwise, you are essentially asking an LLM to diagnose a mess while proudly calling the mess an architecture.

---

# Portfolio Value

PayGuard AI is designed to demonstrate practical experience across several engineering disciplines:

### Quality Engineering

* Layered test architecture
* API automation
* Domain testing
* Negative testing
* Boundary testing
* Failure simulation
* Regression testing

### Payment Engineering

* Transaction lifecycle modeling
* State machines
* Capture and settlement
* Partial refunds
* Transaction history
* Payment-domain exceptions
* Reliability requirements

### Software Architecture

* Separation of concerns
* Service layer
* Repository pattern
* Domain modeling
* Persistence abstraction
* Incremental architecture

### Frontend Engineering

* React
* TypeScript
* Vite
* Transaction visualization
* Payment lifecycle UI

### Reliability Engineering

Planned work includes:

* Idempotency
* Concurrency control
* PostgreSQL
* Transaction consistency
* Durable audit history
* Failure recovery

### AI Engineering

Planned capabilities include:

* Retrieval-augmented failure analysis
* Local LLM inference
* Failure classification
* AI-assisted root cause analysis
* OpenAPI-driven test generation
* AI output evaluation

The project therefore demonstrates a progression from conventional QA automation toward AI-augmented quality engineering.

---

# Future Vision

The intended final architecture is:

```text
                         ┌───────────────────────┐
                         │    Web Dashboard      │
                         │     React / Vite      │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │      FastAPI API      │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │    Payment Service    │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │ Payment Domain /      │
                         │ State Machine         │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │ Transaction Repository│
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │      PostgreSQL       │
                         └───────────────────────┘


              ┌─────────────────────────────────────────┐
              │             QA Automation                │
              │                                          │
              │ Pytest → API → Selenium → E2E            │
              └──────────────────┬──────────────────────┘
                                 │
                                 ▼
                       ┌───────────────────┐
                       │ Failure Artifacts │
                       └─────────┬─────────┘
                                 │
                                 ▼
                       ┌───────────────────┐
                       │   AI RCA Engine   │
                       │ ChromaDB + Ollama │
                       └───────────────────┘
                                 │
                                 ▼
                       Root Cause Analysis


                       OpenAPI Specification
                                 │
                                 ▼
                       ┌───────────────────┐
                       │ AI Test Generator │
                       │      + LLM        │
                       └───────────────────┘
                                 │
                                 ▼
                       Test Scenario Suggestions
                                 │
                                 ▼
                           Human Review
```

The architecture will evolve incrementally toward this model rather than implementing every component simultaneously.

---

# Definition of Done

A project milestone is considered complete only when:

* The feature is implemented.
* Automated tests exist for the feature.
* Existing regression tests remain green.
* Documentation reflects actual implementation state.
* Known limitations are documented.
* Failure behavior is understood.
* The implementation does not falsely claim production capabilities it does not possess.

For infrastructure-heavy milestones, completion should also include:

* Reproducible local setup
* Appropriate integration tests
* Failure-path validation
* Documentation of operational assumptions

---

# Author

**Atharva Garud**
Associate Engineer @ Worldline
**ISTQB Certified**

Building at the intersection of:

* Quality Engineering
* Payment Systems
* Test Automation
* Software Architecture
* Reliability Engineering
* Applied AI

---

# Repository Documentation Quick Access

| Area                 | Document                                     |
| -------------------- | -------------------------------------------- |
| Product Requirements | [📋 PRD.md](docs/PRD.md)                     |
| System Architecture  | [🏗️ ARCHITECTURE.md](docs/ARCHITECTURE.md)  |
| Test Strategy        | [🧪 TEST_STRATEGY.md](docs/TEST_STRATEGY.md) |
| Technology Stack     | [⚙️ TECH_STACK.md](docs/TECH_STACK.md)       |
| API Specification    | [🔌 API_SPEC.md](docs/API_SPEC.md)           |
| AI Pipeline          | [🤖 AI_PIPELINE.md](docs/AI_PIPELINE.md)     |
| Local Setup          | [🛠️ SETUP.md](docs/SETUP.md)                |

**Start here:** [PRD.md](docs/PRD.md) → [ARCHITECTURE.md](docs/ARCHITECTURE.md) → [API_SPEC.md](docs/API_SPEC.md) → [TEST_STRATEGY.md](docs/TEST_STRATEGY.md) → [TECH_STACK.md](docs/TECH_STACK.md) → [AI_PIPELINE.md](docs/AI_PIPELINE.md) → [SETUP.md](docs/SETUP.md)


