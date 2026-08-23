# PayGuard AI

**AI-Augmented Test Automation Framework for Payment Systems**

PayGuard AI is a portfolio engineering project focused on combining:

- Payment-domain engineering
- Quality engineering
- API test automation
- End-to-end UI automation
- Software architecture
- Reliability engineering
- Auditability
- Applied AI

The project simulates a payment gateway using FastAPI and validates its behavior through layered automated tests.

The current implementation models the following payment lifecycle:

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

The project is being developed incrementally. The current implementation establishes deterministic payment-domain behavior, service-layer separation, repository abstraction, idempotency, audit events, monetary correctness, dashboard functionality, and automated regression coverage before introducing stronger persistence, concurrency controls, observability, CI/CD, and AI-assisted engineering capabilities.

---

# Project at a Glance

| Area                      | Current Status           |
| ------------------------- | ------------------------ |
| Mock Payment Gateway      | Implemented              |
| Card Issuance             | Implemented              |
| Authorization             | Implemented              |
| Capture                   | Implemented              |
| Settlement                | Implemented              |
| Full Refund               | Implemented              |
| Partial Refund            | Implemented              |
| Transaction Lookup        | Implemented              |
| Transaction State Machine | Implemented              |
| Payment Service           | Implemented              |
| Repository Abstraction    | Implemented              |
| In-Memory Persistence     | Implemented              |
| Decimal Monetary Handling | Implemented              |
| Idempotency               | Implemented              |
| Audit Events              | Implemented              |
| Failure Simulation        | Implemented              |
| API Test Automation       | Implemented              |
| Unit Test Automation      | Implemented              |
| Playwright E2E Automation | Implemented              |
| React/Vite Dashboard      | Implemented              |
| Transaction Lifecycle UI  | Implemented              |
| Regression Baseline       | **96 passed / 0 failed** |
| PostgreSQL Persistence    | Planned                  |
| Concurrency Controls      | Planned                  |
| CI/CD                     | Planned                  |
| AI Root Cause Analysis    | Planned                  |
| AI Test Generation        | Planned                  |
| ChromaDB                  | Planned                  |
| Ollama                    | Planned                  |
| OpenTelemetry             | Planned                  |
| Docker                    | Planned                  |

---

# Documentation

The project documentation is divided by engineering concern so that the repository explains the system instead of forcing someone to excavate the entire codebase like an archaeological site.

## Core Project Documentation

| Document                                     | Description                                                                                                                                 |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| [Product Requirements Document](docs/PRD.md) | Product goals, requirements, scope, roadmap, success criteria, risks, constraints, and definition of done                                   |
| [Architecture](docs/ARCHITECTURE.md)         | System architecture, component boundaries, domain/service/repository design, and planned evolution                                          |
| [Test Strategy](docs/TEST_STRATEGY.md)       | Test pyramid, test layers, regression strategy, failure testing, E2E strategy, and future AI-assisted testing                               |
| [Technology Stack](docs/TECH_STACK.md)       | Current and planned technologies, architectural rationale, dependency strategy, and technology-selection principles                         |
| [API Specification](docs/API_SPEC.md)        | Mock Payment Gateway REST API, endpoints, request/response behavior, status codes, lifecycle rules, idempotency, and failure simulation     |
| [AI Pipeline](docs/AI_PIPELINE.md)           | Planned AI Root Cause Analysis and AI test-case-generation pipelines, retrieval architecture, prompting, and evaluation                     |
| [Setup Guide](docs/SETUP.md)                 | Local development setup, virtual environment, dependency installation, application startup, testing, E2E prerequisites, and troubleshooting |

## Recommended Reading Order

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

This order moves from:

**why the project exists → how it is designed → what the API does → how it is tested → what technologies are used → how to run it → how AI will eventually augment it**

---

# Why This Project Exists

Payment systems are stateful, failure-sensitive systems where seemingly small defects can create significant financial and operational consequences.

Payment testing requires more than checking whether an HTTP response contains the expected status code.

A realistic payment-focused QA system must consider:

* Transaction state
* Lifecycle transitions
* Amount consistency
* Invalid operations
* Partial captures
* Partial refunds
* Duplicate operations
* Idempotency
* Failure scenarios
* Transaction history
* Audit events
* Persistence
* Concurrency
* Root causes behind test failures

PayGuard AI is intended to evolve into a platform that combines deterministic payment-domain testing with AI-assisted engineering.

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

The current implementation deliberately prioritizes correctness, testability, reliability fundamentals, and regression coverage before adding sophisticated AI functionality.

---

# Current Milestone

## Payment Domain + Automated Regression + UI Automation Foundation

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
* Decimal-based monetary handling
* Idempotency-key handling
* Audit event recording
* Transaction history/events
* Deterministic technical failure simulation
* React/Vite dashboard
* Transaction dashboard
* Transaction lifecycle visualization
* Playwright E2E tests

The current implementation uses **in-memory persistence** through the repository/storage abstraction.

The next major engineering milestone is **durable persistence and stronger reliability controls**, particularly PostgreSQL-backed storage and concurrency guarantees.

---

# Current Test Baseline

The project currently contains three primary automated testing layers:

```text
                 ┌──────────────────────┐
                 │    Playwright E2E    │
                 │      UI / Browser    │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │      API Tests       │
                 │   HTTP / Contract    │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │     Unit Tests       │
                 │ Domain / Services    │
                 └──────────────────────┘
```

Current regression baseline:

```text
96 tests
96 passed
0 failed
```

Full regression command:

```powershell
pytest -v
```

Current observed result:

```text
96 passed in 11.50s
```

The E2E suite can also be executed independently:

```powershell
pytest tests\e2e -v
```

Current E2E baseline:

```text
4 tests
4 passed
```

The transaction E2E tests can be executed independently:

```powershell
pytest tests\e2e\test_transactions.py -v
```

Current transaction E2E baseline:

```text
2 tests
2 passed
```

---

# Test Architecture

The project separates testing responsibilities by abstraction level.

## Unit Tests

Unit tests validate application behavior without requiring browser interaction.

They cover areas including:

* Audit event behavior
* Monetary calculations
* Payment service behavior
* Transaction state transitions

Example:

```text
tests/unit/
├── test_audit_service.py
├── test_money.py
├── test_payment_service.py
└── test_state_machine.py
```

## API Tests

API tests validate externally observable payment gateway behavior.

Example structure:

```text
tests/api/
├── test_audit.py
├── test_authorization.py
├── test_capture.py
├── test_card_issuance.py
├── test_refund.py
└── test_settlement.py
```

The API suite covers:

* Successful operations
* Validation failures
* Boundary conditions
* Invalid states
* Insufficient funds
* Missing resources
* Idempotency
* Audit events
* Failure simulation
* Transaction lifecycle behavior

## End-to-End Tests

Playwright is used for browser-level validation of the React/Vite dashboard.

Example structure:

```text
tests/e2e/
├── conftest.py
├── pages/
│   └── transactions_page.py
├── test_cards.py
├── test_dashboard_smoke.py
└── test_transactions.py
```

The current E2E suite validates:

* Dashboard loading
* Card issuance through the UI
* Transactions page navigation
* Transactions page rendering
* Empty transaction state
* Authorized transaction visibility
* Merchant information
* Transaction status
* Transaction lifecycle dialog
* Lifecycle dialog closing

The Page Object Model is used to keep selectors and page interactions separate from test scenarios.

---

# Current Backend Architecture

The current backend follows a layered architecture:

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

---

# API Layer

The API layer is responsible for:

* HTTP request handling
* Request validation
* Endpoint routing
* HTTP response formatting
* Mapping domain exceptions to HTTP status codes
* Idempotency handling
* Failure simulation

The API is implemented using:

* FastAPI
* Pydantic
* Uvicorn

Detailed endpoint behavior is documented in:

[API Specification](docs/API_SPEC.md)

---

# Payment Service Layer

The Payment Service contains application-level payment operations.

Responsibilities include:

* Transaction retrieval
* Capture business rules
* Settlement business rules
* Refund business rules
* Amount validation
* Transaction state changes
* Transaction history updates
* Persistence through repositories
* Payment lifecycle enforcement

The service layer keeps payment behavior outside the HTTP layer.

---

# Domain Layer

The domain layer is responsible for:

* Transaction lifecycle states
* Valid state transitions
* Invalid state detection
* Payment-domain rules
* Typed domain exceptions
* Monetary validation

The state machine provides a centralized mechanism for preventing illegal transaction transitions.

---

# Repository and Storage Layer

The repository layer provides an abstraction between payment services and persistence.

The current implementation uses in-memory storage.

The architectural direction is:

```text
Payment Service
      ↓
Repository
      ↓
In-Memory Storage
```

The planned evolution is:

```text
Payment Service
      ↓
Repository
      ↓
PostgreSQL
```

This allows persistence to evolve without coupling payment business logic directly to database-specific implementation details.

---

# Monetary Handling

Payment amounts are treated as monetary values rather than arbitrary floating-point numbers.

The current implementation validates:

* Positive authorization amounts
* Positive capture amounts
* Positive refund amounts
* Two-decimal monetary precision
* Exact Decimal arithmetic

The test suite explicitly validates that:

* Valid two-decimal amounts are accepted
* More than two decimal places are rejected
* Zero authorization amounts are rejected
* Negative authorization amounts are rejected
* Capture operations use Decimal arithmetic
* Refund operations use Decimal arithmetic

This is an important payment-domain constraint because floating-point arithmetic is a poor foundation for financial calculations. Computers have many talents. Correctly guessing how much money you owe is not one of them.

---

# Idempotency

Idempotency is implemented for authorization and capture operations.

The implementation stores an idempotency key together with:

```text
Request Fingerprint
        +
Original Response
```

This allows the system to distinguish between:

```text
Same Idempotency-Key
        +
Same Request
        ↓
Replay Original Response
```

and:

```text
Same Idempotency-Key
        +
Different Request
        ↓
HTTP 409 Conflict
```

The test suite validates:

* Replaying the same authorization request
* Preventing duplicate balance deduction
* Rejecting a reused key with a different request
* Treating different idempotency keys as separate operations
* Preserving non-idempotent behavior when no key is supplied

The same reliability principle is also covered for capture operations.

---

# Audit Events

The application records audit events separately from payment transactions.

Audit events are intended to represent operational and security history without storing raw sensitive payment payloads.

The audit layer supports:

* Creating audit events
* Persisting audit events
* Retrieving individual events
* Listing audit events
* Correlation with transactions
* Correlation with request/operation identifiers
* Recording failed operations

The test suite verifies that audit events are created for relevant payment operations and that raw card numbers are not stored in audit payloads.

Current audit persistence is in memory.

Durable audit/event storage is planned as part of the PostgreSQL milestone.

---

# Payment Transaction Lifecycle

The transaction lifecycle is explicitly modeled as:

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
                 ┌──────┴────────┐
                 │               │
                 ▼               ▼
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

The history records significant state changes associated with:

* Authorization
* Capture
* Settlement
* Partial refund
* Full refund
* Other transaction lifecycle events

The current history implementation is backed by in-memory persistence.

Future durable persistence will make transaction history more suitable for:

* Debugging
* Auditability
* Reliability analysis
* Failure investigation
* AI-assisted root cause analysis

---

# Failure Simulation

The API supports deterministic technical failure simulation through:

```text
X-Simulate-Failure
```

Supported scenarios include:

```text
TIMEOUT
NETWORK_ERROR
INVALID_RESPONSE
```

The intended behavior is:

```text
X-Simulate-Failure: TIMEOUT
        ↓
HTTP 504
```

```text
X-Simulate-Failure: NETWORK_ERROR
        ↓
HTTP 502
```

```text
X-Simulate-Failure: INVALID_RESPONSE
        ↓
HTTP 500
```

The mechanism provides reproducible failures for:

* Reliability testing
* Negative API testing
* Failure-handling validation
* Future AI root cause analysis

---

# Web Dashboard

The project includes a React/Vite dashboard used as the primary visual interface for interacting with the Mock Payment Gateway.

Current dashboard functionality includes:

* Payment gateway overview
* Card management
* Card issuance
* Transaction visibility
* Transaction status
* Transaction amounts
* Transaction history
* Transaction lifecycle inspection

The dashboard is designed around the payment lifecycle rather than treating transactions as isolated records.

A transaction can be inspected through:

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

---

# Transaction Lifecycle UI

The Transactions page provides a dedicated interface for inspecting payment activity.

The current UI supports:

* Transaction listing
* Transaction identifiers
* Merchant information
* Transaction status
* Transaction amount
* Empty-state handling
* Refresh functionality
* Lifecycle inspection
* Lifecycle dialog
* Transaction lifecycle visualization

The lifecycle view distinguishes between:

* Completed stages
* Current stage
* Upcoming stages
* Failed authorization

The lifecycle visualization is a presentation layer over backend transaction state and history.

It does not replace the backend state machine.

---

# Playwright E2E Automation

Playwright is currently used for browser-level automation.

The E2E framework uses:

* Pytest
* Playwright
* Page Object Model
* API-backed test data setup
* Chromium

The E2E environment expects:

```text
Frontend
http://localhost:5173

Backend
http://localhost:8000
```

The frontend is intentionally not started by pytest.

The Vite development server must be running before E2E tests are executed.

Example frontend startup:

```powershell
npm run dev
```

The backend can be started with:

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8000
```

The restricted Uvicorn reload directory is intentional and keeps reload behavior focused on the application source.

---

# E2E Test Data

E2E tests create deterministic backend data through the API before interacting with the dashboard.

For example:

```text
Create Card
    ↓
Authorize Transaction
    ↓
Open Dashboard
    ↓
Open Transactions
    ↓
Locate Transaction
    ↓
Validate Merchant / Status
    ↓
Open Lifecycle
    ↓
Close Lifecycle
```

This approach avoids depending on manually seeded application state.

The E2E fixtures create:

* A fresh active test card
* A deterministic authorized transaction

This provides isolated backend state for transaction-focused browser tests.

---

# Page Object Model

The E2E suite uses Page Objects to separate UI selectors and browser interactions from test scenarios.

The current Transactions Page Object encapsulates:

* Transactions navigation
* Page heading
* Page description
* Transactions list
* Transaction table
* Empty state
* Refresh button
* Transaction lookup
* Transaction status validation
* Transaction amount validation
* Lifecycle dialog
* Lifecycle dialog opening
* Lifecycle dialog closing

The Page Object also handles the shortened transaction identifier rendered by the UI.

Backend:

```text
b8cd34da-d6f8-48d1-933a-74bcc919aea4
```

Frontend:

```text
b8cd34da...19aea4
```

This keeps test cases based on backend transaction IDs while allowing the Page Object to understand presentation-layer formatting.

---

# Test Execution

## Run the Complete Regression Suite

```powershell
pytest -v
```

Current baseline:

```text
96 passed
0 failed
```

## Run API Tests

```powershell
pytest tests\api -v
```

## Run Unit Tests

```powershell
pytest tests\unit -v
```

## Run E2E Tests

Start the frontend first:

```powershell
npm run dev
```

Start the backend:

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8000
```

Then run:

```powershell
pytest tests\e2e -v
```

## Run Transaction E2E Tests Only

```powershell
pytest tests\e2e\test_transactions.py -v
```

Current observed result:

```text
2 passed
```

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

The API also supports:

* Idempotency keys
* Audit event recording
* Deterministic failure simulation

For complete request/response definitions, business rules, status codes, lifecycle behavior, idempotency behavior, and failure simulation details, see:

**[API Specification →](docs/API_SPEC.md)**

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

---

# Core Components

| Component                 | Current Status     | Description                                                   |
| ------------------------- | ------------------ | ------------------------------------------------------------- |
| Mock Payment Gateway      | Implemented        | FastAPI service simulating core payment transaction flows     |
| Payment Domain            | Implemented        | Transaction lifecycle and payment-domain rules                |
| State Machine             | Implemented        | Explicit validation of payment transaction state transitions  |
| Payment Service           | Implemented        | Application layer containing payment business logic           |
| Transaction Repository    | Implemented        | Persistence abstraction for transaction data                  |
| In-Memory Storage         | Implemented        | Current storage implementation                                |
| Card Issuance             | Implemented        | Creates simulated payment cards                               |
| Authorization             | Implemented        | Validates cards and creates authorized transactions           |
| Capture                   | Implemented        | Captures authorized transaction amounts                       |
| Settlement                | Implemented        | Settles captured transactions                                 |
| Full Refund               | Implemented        | Refunds a settled transaction completely                      |
| Partial Refund            | Implemented        | Supports refunds smaller than the remaining refundable amount |
| Transaction Lookup        | Implemented        | Retrieves transaction details and lifecycle history           |
| Decimal Monetary Handling | Implemented        | Provides exact monetary arithmetic and validation             |
| Idempotency               | Implemented        | Prevents duplicate processing for supported operations        |
| Audit Events              | Implemented        | Records operational/security lifecycle events                 |
| Failure Simulation        | Implemented        | Provides deterministic technical failure scenarios            |
| API Test Suite            | Implemented        | Pytest coverage of API behavior                               |
| Unit Test Suite           | Implemented        | Tests domain and service behavior independently               |
| Playwright E2E Suite      | Implemented        | Browser-level dashboard validation                            |
| Web Dashboard             | Implemented        | React/Vite payment and transaction interface                  |
| Transaction Lifecycle UI  | Implemented        | Dashboard interface for lifecycle inspection                  |
| PostgreSQL Persistence    | Planned            | Durable transaction and event storage                         |
| Concurrency Controls      | Planned            | Race-condition prevention and transaction isolation           |
| Selenium Automation       | Not currently used | Playwright is the current browser automation framework        |
| AI RCA Engine             | Planned            | AI-assisted analysis of test failures                         |
| AI Test Generator         | Planned            | LLM-assisted test scenario generation                         |
| Observability             | Planned            | Metrics, traces, and structured telemetry                     |
| Containerization          | Planned            | Docker-based service orchestration                            |
| CI/CD Pipeline            | Planned            | Automated regression and deployment workflows                 |

---

# Payment Reliability Roadmap

The next major engineering milestone is **payment reliability and durable persistence**.

The current in-memory architecture is intentionally simple, but it does not provide the guarantees expected from a realistic payment system.

## Monetary Safety

Implemented:

* Decimal-based monetary representation
* Two-decimal validation
* Exact Decimal arithmetic
* Positive amount validation

Future work:

* Explicit currency handling
* Currency-aware amount rules
* Cross-operation amount consistency
* Formal rounding rules

## Idempotency

Implemented:

* Authorization idempotency
* Capture idempotency
* Request fingerprinting
* Response replay
* Conflict detection for reused keys

Future work:

* Persistent idempotency records
* Database-backed idempotency guarantees
* Durable recovery semantics
* Broader operation coverage where required

## Concurrency

Planned:

* Concurrent transaction updates
* Race-condition prevention
* Database locking
* Transaction isolation
* Consistent state transitions
* Atomic lifecycle operations

## Persistence

Planned:

* Durable transactions
* Durable lifecycle history
* Durable audit events
* Database constraints
* Atomic updates
* Recovery after application restart
* PostgreSQL-backed repositories

## Transaction Consistency

Planned:

* Explicit transaction boundaries
* Rollback behavior
* Atomic state changes
* Consistent lifecycle updates
* Persistence failure handling

A payment system with impressive AI and weak transaction guarantees is still a very efficient way to manufacture incorrect financial state.

---

# AI-Augmented Testing

AI is planned as an augmentation layer rather than a replacement for deterministic automation.

The project deliberately establishes the payment domain and test infrastructure first.

The planned AI capabilities include:

* AI Root Cause Analysis
* AI-generated test scenarios
* Historical failure retrieval
* Retrieval-augmented failure analysis
* OpenAPI-driven test generation
* Local LLM inference
* AI output evaluation

---

# AI Root Cause Analysis

When a test fails, the future AI pipeline is intended to process the failure through:

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

---

# AI Test Case Generation

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

The detailed design is documented in:

[AI_PIPELINE.md](docs/AI_PIPELINE.md)

---

# AI Evaluation

AI functionality will be evaluated separately from the conventional regression suite.

Initial RCA evaluation target:

> Correctly identify the failure category in at least 8 out of 10 deterministic evaluation scenarios.

Evaluation should consider:

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

The project is being developed incrementally:

```text
Payment Gateway Foundation
          ↓
Domain State Machine
          ↓
Service Layer
          ↓
Repository Abstraction
          ↓
Monetary Safety
          ↓
Idempotency
          ↓
Audit Events
          ↓
Dashboard + Playwright E2E
          ↓
PostgreSQL Persistence
          ↓
Concurrency / Reliability
          ↓
Durable Audit / Event History
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

The underlying payment system needs deterministic behavior, reliable state management, persistence, concurrency controls, and strong test coverage before AI becomes genuinely useful.

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
* [x] Decimal monetary validation
* [x] Unit tests
* [x] API tests
* [x] 96-test regression baseline

---

## Milestone 3 — Payment Reliability Foundations

**Status: In Progress**

Completed:

* [x] Decimal monetary arithmetic
* [x] Amount validation
* [x] Authorization idempotency
* [x] Capture idempotency
* [x] Request fingerprinting
* [x] Idempotency response replay
* [x] Audit event recording
* [x] Audit event testing

Remaining:

* [ ] PostgreSQL persistence
* [ ] Durable transaction history
* [ ] Durable audit/event records
* [ ] Database constraints
* [ ] Explicit transaction boundaries
* [ ] Persistence failure handling
* [ ] Concurrency and race-condition handling
* [ ] Database-backed integration tests

---

## Milestone 4 — Automation Platform

**Status: In Progress**

* [x] React/Vite dashboard
* [x] Transaction dashboard
* [x] Transaction lifecycle visualization
* [x] Card management interface
* [x] Card issuance UI
* [x] Playwright browser automation
* [x] Page Object Model
* [x] Dashboard smoke test
* [x] Transaction page tests
* [x] API-backed E2E test data
* [ ] Expanded end-to-end payment scenarios
* [ ] CI/CD integration

Playwright is currently the browser automation framework.

Selenium is not currently part of the implemented automation stack.

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
* [ ] ChromaDB integration
* [ ] Ollama integration

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
* [ ] Production-oriented deployment architecture

---

# Current Limitations

PayGuard AI is a **mock payment gateway and portfolio engineering project**, not a production payment processor.

The current implementation does not provide:

* Durable transaction storage
* Production database guarantees
* Distributed concurrency control
* Production payment-network connectivity
* Production authentication
* Production authorization
* PCI-DSS certification
* Production cardholder-data processing
* Full observability
* AI-powered RCA
* AI-generated executable tests
* Full automated CI/CD
* Production deployment infrastructure
* Production-grade distributed transaction guarantees

The following capabilities are implemented but currently rely on in-memory application state:

* Transactions
* Cards
* Audit events
* Idempotency records

Application restart therefore clears these records.

These limitations are intentional and tracked as future engineering milestones.

---

# Reliability and Security Direction

Before the platform can be considered production-oriented, the following concerns must be addressed.

## Monetary Safety

* Decimal-based monetary representation
* Explicit currency handling
* Amount consistency across lifecycle operations
* Prevention of rounding-related inconsistencies

## Idempotency

Implemented foundation:

* Duplicate authorization protection
* Duplicate capture protection
* Idempotency-key handling
* Request fingerprinting
* Response replay
* Conflict detection

Future work:

* Durable idempotency records
* Database-backed idempotency guarantees
* Recovery semantics across application restarts

## Concurrency

Planned:

* Concurrent transaction updates
* Race-condition prevention
* Database locking
* Transaction isolation
* Consistent state transitions

## Persistence

Planned:

* Durable transactions
* Durable lifecycle history
* Durable audit events
* Database constraints
* Atomic updates
* Recovery after application restart

## Security

Planned:

* Authentication
* Authorization
* Secrets management
* Input validation
* Rate limiting
* Secure logging
* Sensitive-data protection
* PCI-related design considerations

## Observability

Planned:

* Structured logging
* Metrics
* Distributed tracing
* Transaction correlation IDs
* Failure telemetry

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
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
          Product        Architecture         API
          PRD.md         ARCHITECTURE.md     API_SPEC.md
             │                │                │
             └────────────────┼────────────────┘
                              |
                              ▼
                     Quality Engineering
                              |
                     ┌────────┴────────┐
                     ▼                 ▼
              TEST_STRATEGY.md   TECH_STACK.md
                     |
                     ▼
                AI Augmentation
                     |
                     ▼
                AI_PIPELINE.md
                     |
                     ▼
                 Development
                     |
                     ▼
                  SETUP.md
```

## Documentation Links

* 📋 [PRD.md](docs/PRD.md)
  Product requirements, scope, roadmap, success criteria, risks, assumptions, and definition of done.

* 🏗️ [ARCHITECTURE.md](docs/ARCHITECTURE.md)
  System architecture, component responsibilities, domain boundaries, persistence architecture, and planned evolution.

* 🧪 [TEST_STRATEGY.md](docs/TEST_STRATEGY.md)
  Test strategy, testing layers, regression approach, negative testing, failure simulation, E2E testing, and future AI-assisted testing.

* ⚙️ [TECH_STACK.md](docs/TECH_STACK.md)
  Current and planned technology stack, technology-selection rationale, dependency strategy, and infrastructure decisions.

* 🔌 [API_SPEC.md](docs/API_SPEC.md)
  Complete Mock Payment Gateway API contract, endpoint behavior, request/response models, lifecycle rules, idempotency, and simulated failures.

* 🤖 [AI_PIPELINE.md](docs/AI_PIPELINE.md)
  AI Root Cause Analysis and AI test-case-generation architecture, retrieval strategy, prompt design, storage, and evaluation.

* 🛠️ [SETUP.md](docs/SETUP.md)
  Local setup, environment configuration, application startup, automated tests, E2E prerequisites, troubleshooting, and development workflow.

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
│   ├── api/
│   │   └── FastAPI endpoints
│   │
│   ├── models/
│   ├── storage/
│   └── main.py
│
├── tests/
│   ├── api/
│   │   ├── test_audit.py
│   │   ├── test_authorization.py
│   │   ├── test_capture.py
│   │   ├── test_card_issuance.py
│   │   ├── test_refund.py
│   │   └── test_settlement.py
│   │
│   ├── unit/
│   │   ├── test_audit_service.py
│   │   ├── test_money.py
│   │   ├── test_payment_service.py
│   │   └── test_state_machine.py
│   │
│   └── e2e/
│       ├── conftest.py
│       ├── pages/
│       │   └── transactions_page.py
│       ├── test_cards.py
│       ├── test_dashboard_smoke.py
│       └── test_transactions.py
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
│   ├── SETUP.md
│   └── playwright-vs-selenium-payguard-ai.md
│
├── requirements.txt
├── pytest.ini
└── README.md
```

The exact directory structure may evolve as additional components are implemented.

---

# Tech Stack

## Current / Implemented

### Backend

* **Python 3.11**
* **FastAPI**
* **Pydantic**
* **Uvicorn**

### Testing

* **Pytest**
* **Playwright**
* **pytest-playwright**
* Page Object Model
* API-backed E2E fixtures

### Frontend

* **React**
* **TypeScript**
* **Vite**

### Architecture

* Repository pattern
* Domain state machine
* Domain exceptions
* Service layer
* In-memory persistence
* Decimal monetary representation
* Idempotency
* Audit event recording

## Planned / Future

* **SQLAlchemy**
* **PostgreSQL**
* **Selenium**, only if there is a specific engineering reason to introduce it alongside or instead of Playwright
* **LangChain**
* **LangGraph**
* **ChromaDB**
* **Ollama**
* **OpenTelemetry**
* **Docker**
* **GitHub Actions**

Technologies listed as planned are part of the intended architecture and should not be interpreted as fully implemented functionality.

The complete technology rationale is documented in:

[TECH_STACK.md](docs/TECH_STACK.md)

---

# Local Development

## Backend

The current backend development workflow requires:

* Python 3.11
* Virtual environment
* FastAPI
* Uvicorn
* Pytest

Create the environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the backend:

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8000
```

Run the complete regression suite:

```powershell
pytest -v
```

---

# Frontend Development

The dashboard is a React/Vite application.

Start the frontend development server:

```powershell
npm run dev
```

The E2E suite expects the frontend at:

```text
http://localhost:5173
```

The backend is expected at:

```text
http://localhost:8000
```

For complete setup instructions, see:

**[Setup Guide →](docs/SETUP.md)**

---

# Running the E2E Environment

Before running browser tests, ensure both services are available.

## Terminal 1 — Backend

```powershell
.\.venv\Scripts\Activate.ps1

uvicorn app.main:app --reload --reload-dir app --port 8000
```

## Terminal 2 — Frontend

```powershell
npm run dev
```

## Terminal 3 — Tests

```powershell
.\.venv\Scripts\Activate.ps1

pytest tests\e2e -v
```

Expected current result:

```text
4 passed
```

---

# Regression Validation

The project currently provides three useful levels of regression execution.

## Focused Transaction E2E

```powershell
pytest tests\e2e\test_transactions.py -v
```

Expected:

```text
2 passed
```

## Complete E2E Suite

```powershell
pytest tests\e2e -v
```

Expected:

```text
4 passed
```

## Complete Regression Suite

```powershell
pytest -v
```

Expected:

```text
96 passed
```

The complete suite should remain green before changes are committed.

---

# Engineering Documentation

The project deliberately separates product requirements, architecture, testing, technology choices, API behavior, AI design, and setup instructions.

## Product Perspective

**[PRD.md](docs/PRD.md)** answers:

* Why does PayGuard AI exist?
* What problem does it solve?
* What are the functional requirements?
* What is implemented?
* What is planned?
* What are the success criteria?
* What is the roadmap?

## Architecture Perspective

**[ARCHITECTURE.md](docs/ARCHITECTURE.md)** answers:

* How are components separated?
* Where does payment business logic live?
* How does the state machine work?
* How does persistence abstraction work?
* How does idempotency fit into the architecture?
* How are audit events handled?
* How will PostgreSQL fit into the architecture?
* How will the platform evolve?

## Quality Engineering Perspective

**[TEST_STRATEGY.md](docs/TEST_STRATEGY.md)** answers:

* What is being tested?
* At which layer?
* Why are tests separated?
* How are negative and boundary cases handled?
* How are failure scenarios simulated?
* How is browser automation structured?
* How are E2E test fixtures managed?
* How will AI-assisted testing be introduced?

## Technology Perspective

**[TECH_STACK.md](docs/TECH_STACK.md)** answers:

* Which technologies are currently implemented?
* Which technologies are planned?
* Why was each technology selected?
* How are dependencies managed?
* What is the intended infrastructure architecture?

## API Perspective

**[API_SPEC.md](docs/API_SPEC.md)** answers:

* Which endpoints exist?
* What requests do they accept?
* What responses do they produce?
* Which HTTP status codes are used?
* What payment-domain rules apply?
* How is idempotency handled?
* How are technical failures simulated?

## AI Perspective

**[AI_PIPELINE.md](docs/AI_PIPELINE.md)** answers:

* How will test failures enter the AI pipeline?
* How will historical failures be retrieved?
* How will ChromaDB be used?
* How will Ollama provide local LLM inference?
* How will AI-generated test cases be produced?
* How will AI output be evaluated?

## Developer Perspective

**[SETUP.md](docs/SETUP.md)** answers:

* How do I install the project?
* How do I run the backend?
* How do I run the dashboard?
* How do I run the tests?
* How do I configure the development environment?
* How do I run the E2E suite?
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
* [x] Decimal monetary validation
* [x] Idempotency
* [x] Audit events
* [x] Deterministic failure simulation
* [x] API test suite
* [x] Unit test suite
* [x] Playwright E2E suite
* [x] React/Vite dashboard
* [x] Transaction dashboard
* [x] Transaction lifecycle visualization
* [x] Card management interface
* [x] 96-test regression baseline

## Next

* [ ] PostgreSQL persistence
* [ ] Durable transaction history
* [ ] Durable audit/event storage
* [ ] Database constraints
* [ ] Explicit transaction boundaries
* [ ] Persistence failure handling
* [ ] Concurrency safety
* [ ] Race-condition testing
* [ ] Database-backed integration tests
* [ ] Reliability testing
* [ ] Observability foundation

## Planned

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
* [ ] Scalable test execution

---

# Current Limitations

PayGuard AI is a **mock payment gateway and portfolio engineering project**, not a production payment processor.

The current implementation does not provide:

* Durable transaction storage
* Production database guarantees
* Distributed concurrency control
* Real payment-network connectivity
* Production authentication
* Production authorization
* PCI-DSS certification
* Production cardholder-data processing
* Full observability
* AI-powered RCA
* AI-generated executable tests
* Automated CI/CD
* Production deployment infrastructure

The application currently uses in-memory storage.

Consequently:

```text
Application Restart
       ↓
In-Memory State Lost
       ↓
Cards / Transactions / Audit / Idempotency Records Cleared
```

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

That ordering is deliberate.

Otherwise, you are essentially asking an LLM to diagnose a mess while proudly calling the mess an architecture.

---

# Portfolio Value

PayGuard AI is designed to demonstrate practical experience across several engineering disciplines.

## Quality Engineering

* Layered test architecture
* Unit testing
* API automation
* Browser automation
* Page Object Model
* Positive testing
* Negative testing
* Boundary testing
* Failure simulation
* Regression testing
* E2E test data management

## Payment Engineering

* Transaction lifecycle modeling
* State machines
* Authorization
* Capture
* Settlement
* Partial refunds
* Transaction history
* Idempotency
* Audit events
* Payment-domain exceptions
* Monetary correctness
* Reliability requirements

## Software Architecture

* Separation of concerns
* Service layer
* Repository pattern
* Domain modeling
* Persistence abstraction
* Explicit state machine
* Incremental architecture

## Frontend Engineering

* React
* TypeScript
* Vite
* Transaction visualization
* Payment lifecycle UI
* Card management
* Browser automation

## Reliability Engineering

Current:

* Decimal monetary handling
* Idempotency
* Audit event recording
* Deterministic failure simulation

Planned:

* PostgreSQL
* Concurrency control
* Transaction consistency
* Durable audit history
* Failure recovery
* Database transaction isolation

## AI Engineering

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

The intended architecture is:

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
                │ Pytest → API → Playwright → E2E          │
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
                          └─────────┬─────────┘
                                    │
                                    ▼
                            Root Cause Analysis


                          OpenAPI Specification
                                    │
                                    ▼
                          ┌───────────────────┐
                          │ AI Test Generator │
                          │      + LLM        │
                          └─────────┬─────────┘
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

**Start here:**

[PRD.md](docs/PRD.md)
→ [ARCHITECTURE.md](docs/ARCHITECTURE.md)
→ [API_SPEC.md](docs/API_SPEC.md)
→ [TEST_STRATEGY.md](docs/TEST_STRATEGY.md)
→ [TECH_STACK.md](docs/TECH_STACK.md)
→ [AI_PIPELINE.md](docs/AI_PIPELINE.md)
→ [SETUP.md](docs/SETUP.md)

