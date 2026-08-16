# ARCHITECTURE.md — PayGuard AI

## Overview

PayGuard AI is being developed as an AI-augmented test automation framework for payment systems.

The architecture is being developed incrementally. The current implementation focuses on establishing a reliable and testable payment-domain foundation together with a functional web dashboard for interacting with and inspecting payment transactions.

The current system is organized around five primary concerns:

1. **API / HTTP Layer** — FastAPI endpoints responsible for request handling and HTTP responses.
2. **Payment Service Layer** — Contains payment transaction business logic for authorization, capture, settlement, and refunds.
3. **Domain Layer** — Defines transaction state transitions and typed payment-domain exceptions.
4. **Repository / Storage Layer** — Provides persistence abstraction over the current in-memory storage implementation.
5. **Web Dashboard Layer** — React/TypeScript frontend for card management, transaction monitoring, and transaction lifecycle inspection.

The planned architecture will extend this foundation with persistent database storage, UI automation, AI-powered failure analysis, AI-generated test cases, observability, containerization, and CI/CD orchestration.

---

## Current Architecture

```text
                         ┌─────────────────────────┐
                         │      Web Dashboard      │
                         │    React / TypeScript   │
                         │                         │
                         │  Cards                  │
                         │  Transactions           │
                         │  Lifecycle Inspection   │
                         └────────────┬────────────┘
                                      │
                                      │ HTTP / REST
                                      ▼
                         ┌─────────────────────────┐
                         │       FastAPI API       │
                         │      / HTTP Layer       │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │     Payment Service     │
                         │   Business Operations   │
                         └────────────┬────────────┘
                                      │
                         ┌────────────┴─────────────┐
                         │                          │
                         ▼                          ▼
              ┌─────────────────────┐    ┌─────────────────────┐
              │   State Machine     │    │  Domain Exceptions  │
              │ Transaction States  │    │   Payment Errors    │
              └──────────┬──────────┘    └─────────────────────┘
                         │
                         ▼
              ┌─────────────────────────┐
              │ Transaction Repository  │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │    In-Memory Storage    │
              │    Current Persistence  │
              └─────────────────────────┘
````

The current architecture intentionally keeps HTTP concerns separate from payment-domain business logic.

The web dashboard communicates with the FastAPI backend through HTTP/REST APIs. The dashboard does not contain the core payment-domain rules.

This separation allows:

* Backend payment behavior to be tested independently
* The frontend to consume the same API used by automated tests
* Transaction lifecycle rules to remain centralized in the domain layer
* Persistence to be replaced without rewriting payment business logic

---

## Current Architecture Components

| Layer             | Component                  | Responsibility                                                                     | Status      |
| ----------------- | -------------------------- | ---------------------------------------------------------------------------------- | ----------- |
| UI                | Web Dashboard              | Provides the browser-based interface for interacting with the payment gateway      | Implemented |
| UI                | Cards Interface            | Displays and manages simulated payment cards                                       | Implemented |
| UI                | Transactions Interface     | Displays transaction activity and transaction status                               | Implemented |
| UI                | Transaction Lifecycle View | Displays authorization, capture, settlement, and refund lifecycle events           | Implemented |
| API               | FastAPI                    | Exposes payment gateway endpoints and translates domain errors into HTTP responses | Implemented |
| Application       | Payment Service            | Implements authorization, capture, settlement, and refund business logic           | Implemented |
| Domain            | Transaction State Machine  | Validates valid and invalid transaction lifecycle transitions                      | Implemented |
| Domain            | Payment Exceptions         | Provides typed domain errors for payment operations                                | Implemented |
| Persistence       | Transaction Repository     | Abstracts transaction persistence from business logic                              | Implemented |
| Persistence       | In-Memory Storage          | Current storage implementation                                                     | Implemented |
| System Under Test | Card Issuance              | Creates simulated payment cards                                                    | Implemented |
| System Under Test | Authorization              | Validates cards and authorizes transactions                                        | Implemented |
| System Under Test | Capture                    | Captures authorized transactions                                                   | Implemented |
| System Under Test | Settlement                 | Settles captured transactions                                                      | Implemented |
| System Under Test | Refund                     | Supports full and partial refunds                                                  | Implemented |
| Test Automation   | API Tests                  | Validates API behavior across positive, negative, and boundary cases               | Implemented |
| Test Automation   | Service Tests              | Validates payment business logic independently of HTTP                             | Implemented |
| Test Automation   | State Machine Tests        | Validates transaction lifecycle rules                                              | Implemented |
| Test Automation   | UI Tests                   | Selenium-based dashboard validation                                                | Planned     |
| AI Engine         | RCA Pipeline               | Planned AI-assisted failure analysis                                               | Planned     |
| AI Engine         | Test Case Generator        | Planned LLM-based test scenario generation                                         | Planned     |
| Persistence       | PostgreSQL                 | Planned persistent transactional storage                                           | Planned     |
| Observability     | OpenTelemetry              | Planned application and test observability                                         | Planned     |
| Orchestration     | Docker                     | Planned service containerization                                                   | Planned     |
| CI/CD             | GitHub Actions             | Planned automated test and AI workflow execution                                   | Planned     |

---

## Web Dashboard Architecture

The web dashboard provides a frontend interface over the payment gateway.

The current dashboard contains the following primary areas:

```text
Web Dashboard
│
├── Overview
│
├── Transactions
│   ├── Transaction Summary
│   ├── Transaction Table
│   ├── Transaction Status
│   └── Transaction Lifecycle
│
├── Cards
│   ├── Card Creation
│   ├── Card Listing
│   ├── Card Status
│   └── Card Balance
│
└── AI Insights
    └── Planned AI functionality
```

The dashboard is implemented using React and TypeScript.

The frontend communicates with the FastAPI backend through the API service layer.

The dashboard does not directly access the storage layer.

The intended dependency direction is:

```text
React Dashboard
      │
      ▼
Frontend API Service
      │
      ▼
FastAPI API
      │
      ▼
Payment Service
      │
      ▼
Domain / Repository
```

This ensures that frontend functionality remains decoupled from backend implementation details.

---

## Transaction Dashboard

The Transactions page provides a monitoring interface for payment activity.

The current interface displays:

* Total transaction count
* Completed transaction count
* In-progress transaction count
* Transaction ID
* Merchant ID
* Transaction amount
* Transaction status
* Creation timestamp
* Lifecycle inspection action

A transaction can be selected through the **View Lifecycle** action.

The frontend retrieves the transaction details from the backend and renders the lifecycle history.

---

## Transaction Lifecycle View

The transaction lifecycle interface provides a visual representation of the backend transaction state and transaction history.

The current lifecycle stages are:

```text
AUTHORIZED
     │
     ▼
CAPTURED
     │
     ▼
SETTLED
     │
     ▼
REFUNDED
```

For partial refunds:

```text
SETTLED
     │
     ▼
PARTIALLY_REFUNDED
     │
     ▼
REFUNDED
```

The lifecycle interface currently displays:

* Transaction ID
* Merchant ID
* Authorized amount
* Captured amount
* Settled amount
* Refunded amount
* Lifecycle stage
* Stage completion state
* Lifecycle event description
* Lifecycle event timestamp
* Card ID
* Transaction creation timestamp

The lifecycle UI is a presentation layer over the transaction history maintained by the backend.

The frontend does not determine whether a transaction transition is valid.

The backend state machine remains the source of truth.

---

## Payment Transaction Lifecycle

The payment domain currently models the transaction lifecycle using explicit states.

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
      ┌────┴─────────────┐
      │                  │
      ▼                  ▼
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

The state machine explicitly prevents invalid transitions.

Examples of invalid operations include:

* Capturing a declined transaction
* Capturing an already captured transaction
* Settling an authorized transaction before capture
* Settling an already settled transaction
* Refunding an unsettled transaction
* Refunding an already fully refunded transaction
* Refunding an amount greater than the remaining refundable amount

These lifecycle rules are independently tested by the state-machine test suite.

---

## Transaction History

Each transaction maintains lifecycle history events.

A completed transaction can therefore contain a sequence similar to:

```text
AUTHORIZED
    │
    ├── Authorization approved
    │
    ▼
CAPTURED
    │
    ├── Amount captured
    │
    ▼
SETTLED
    │
    ├── Transaction settled
    │
    ▼
REFUNDED
    │
    └── Refunded amount
```

The history provides the data used by the dashboard lifecycle view.

This creates a clear separation between:

```text
Backend
    │
    ├── Determines transaction state
    ├── Records lifecycle event
    └── Stores transaction history
             │
             ▼
Frontend
    │
    └── Visualizes transaction history
```

The frontend should not reconstruct transaction history independently from individual API calls.

---

## Payment Service Layer

The `PaymentService` provides the application-level business operations for transaction processing.

Current responsibilities include:

* Retrieve transactions through the repository
* Validate transaction existence
* Validate transaction state
* Validate transaction amounts
* Apply lifecycle transitions
* Update transaction amounts
* Append transaction history
* Persist updated transactions

The service layer does not depend on FastAPI or HTTP-specific exceptions.

---

## Authorization

The authorization operation validates an active payment card and creates a transaction.

The conceptual flow is:

```text
Authorization Request
        │
        ▼
Validate Card
        │
        ├── Invalid / Inactive
        │          │
        │          ▼
        │        Error
        │
        ▼
Validate Amount
        │
        ▼
Create Transaction
        │
        ▼
AUTHORIZED
        │
        ▼
Record Transaction Event
```

A successful authorization creates the transaction that begins the payment lifecycle.

---

## Capture

The capture operation performs the following:

* Retrieve the transaction through the repository
* Validate transaction existence
* Validate transaction state
* Validate capture amount
* Apply the capture
* Update transaction state
* Append transaction history
* Persist the updated transaction

Expected lifecycle transition:

```text
AUTHORIZED
     │
     ▼
CAPTURED
```

---

## Settlement

The settlement operation performs the following:

* Retrieve the transaction
* Validate transaction existence
* Validate that the transaction is captured
* Set the settled amount
* Transition the transaction to `SETTLED`
* Record the transaction event
* Persist the updated transaction

Expected lifecycle transition:

```text
CAPTURED
     │
     ▼
SETTLED
```

---

## Refund

The refund operation performs the following:

* Retrieve the transaction
* Validate transaction existence
* Validate settlement state
* Calculate the remaining refundable amount
* Prevent refunds exceeding the remaining amount
* Support partial refunds
* Record the refund event
* Transition fully refunded transactions to `REFUNDED`
* Persist the updated transaction

Expected lifecycle transitions:

```text
SETTLED
   │
   ├──────────────► REFUNDED
   │
   └──────────────► PARTIALLY_REFUNDED
                         │
                         └──────────────► REFUNDED
```

---

## Domain State Machine

The transaction state machine provides a single location for validating lifecycle transitions.

The current valid transitions include:

```text
AUTHORIZED
    │
    └──► CAPTURED

CAPTURED
    │
    └──► SETTLED

SETTLED
    ├──► PARTIALLY_REFUNDED
    └──► REFUNDED

PARTIALLY_REFUNDED
    ├──► PARTIALLY_REFUNDED
    └──► REFUNDED
```

Terminal states currently include:

```text
DECLINED
REFUNDED
```

The state machine is deliberately independent from the API layer so that transaction lifecycle rules can be tested without running the HTTP application.

---

## Domain Exceptions

Payment operations use typed domain exceptions rather than requiring the API layer to interpret error-message strings.

The current exception hierarchy is:

```text
PaymentError
│
├── TransactionNotFoundError
├── InvalidTransactionStateError
├── CaptureAmountExceededError
└── RefundAmountExceededError
```

These exceptions are translated by the FastAPI layer into appropriate HTTP responses.

For example:

```text
TransactionNotFoundError
        │
        ▼
      HTTP 404

CaptureAmountExceededError
        │
        ▼
      HTTP 400

InvalidTransactionStateError
        │
        ▼
      HTTP 409
```

This keeps the payment service independent of HTTP semantics while preserving a clear API contract.

---

## Repository Layer

The transaction repository provides a persistence abstraction between the payment service and the underlying storage mechanism.

Current responsibilities include:

* Adding transactions
* Retrieving transactions
* Updating transactions

The current implementation delegates to the in-memory storage layer.

```text
PaymentService
      │
      ▼
TransactionRepository
      │
      ▼
In-Memory Storage
```

The repository abstraction is intended to make the eventual migration to PostgreSQL possible without coupling payment business logic directly to a database implementation.

---

## Current Persistence Model

The current application uses in-memory storage.

This is appropriate for the current development stage because it allows payment-domain behavior and architecture to be validated without introducing database infrastructure prematurely.

However, in-memory persistence is not suitable for production-like payment processing.

Current limitations include:

* Data is not durable
* Application restart loses state
* No database transactions
* No row-level locking
* No distributed concurrency control
* No persistence-level uniqueness constraints
* No durable audit/event history

These limitations are part of the planned persistence phase.

---

## API / HTTP Layer

The FastAPI layer currently handles:

* Request validation
* Endpoint routing
* Card operations
* Transaction authorization
* Transaction capture
* Transaction settlement
* Transaction refunds
* Transaction lookup
* Simulated failure injection
* HTTP response formatting
* Translation of domain exceptions into HTTP responses

The API layer should not contain core payment-domain rules.

The intended responsibility boundary is:

```text
HTTP Request
     │
     ▼
FastAPI Endpoint
     │
     ▼
Payment Service
     │
     ▼
Domain Logic
     │
     ▼
Repository
     │
     ▼
Storage
```

This separation allows payment behavior to be tested independently from HTTP behavior.

---

## Failure Simulation

The API currently supports simulated technical failures through the `X-Simulate-Failure` request header.

Supported simulation values include:

```text
TIMEOUT
NETWORK_ERROR
INVALID_RESPONSE
```

These scenarios provide deterministic failure conditions for reliability testing and future AI-assisted root cause analysis.

Current behavior:

```text
X-Simulate-Failure: TIMEOUT
        │
        ▼
      HTTP 504

X-Simulate-Failure: NETWORK_ERROR
        │
        ▼
      HTTP 502

X-Simulate-Failure: INVALID_RESPONSE
        │
        ▼
      HTTP 500
```

This mechanism provides controlled failure inputs for the future AI RCA pipeline.

---

## Test Architecture

The current automated testing architecture contains three backend test layers.

```text
    ┌─────────────────────┐
    │      API Tests      │
    │       36 tests      │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │  Payment Service    │
    │       14 tests      │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │   State Machine     │
    │       14 tests      │
    └─────────────────────┘
```

Current baseline:

```text
API Tests             36
Payment Service       14
State Machine         14
─────────────────────────
Total                 64

Passed                64
Failed                 0
```

The API tests validate externally observable payment gateway behavior.

The payment-service tests validate business logic without HTTP.

The state-machine tests validate transaction lifecycle rules independently.

The web dashboard is currently implemented but dedicated Selenium UI automation remains planned.

---

## Planned UI Test Architecture

The dashboard is currently implemented manually and is intended to become a target for automated UI validation.

The planned UI automation architecture is:

```text
        Selenium
           │
           ▼
   Web Dashboard
           │
           ▼
      FastAPI API
           │
           ▼
   Payment Services
           │
           ▼
    Payment Domain
```

The planned Selenium test suite will validate:

* Dashboard navigation
* Card creation
* Card listing
* Transaction authorization
* Transaction capture
* Transaction settlement
* Transaction refund
* Transaction lifecycle rendering
* Error handling
* UI state synchronization with backend state

UI tests are deliberately planned after the dashboard and backend behavior have been established.

---

## Planned Extended Architecture

The current payment platform will eventually be extended into a broader payment testing and AI platform.

```text
                         ┌───────────────────────┐
                         │    Web Dashboard      │
                         │ React / TypeScript    │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │     Selenium UI       │
                         │     Test Suite        │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │     Payment API       │
                         │       FastAPI         │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │   Payment Services    │
                         └───────────┬───────────┘
                                     │
                         ┌───────────▼───────────┐
                         │ Payment Domain Model  │
                         │   + State Machine     │
                         └───────────┬───────────┘
                                     │
                         ┌───────────▼───────────┐
                         │     Repository        │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │      PostgreSQL       │
                         └───────────────────────┘


        ┌───────────────────┐
        │   Pytest Tests    │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────────┐
        │ Test Results / Logs   │
        └──────────┬────────────┘
                   │
                   ▼
        ┌───────────────────────┐
        │    AI RCA Engine      │
        │ LangChain + ChromaDB  │
        │       + Ollama        │
        └───────────────────────┘


        ┌───────────────────────┐
        │  AI Test Generator    │
        │  OpenAPI + LLM        │
        └───────────────────────┘


                  CI/CD
                    │
                    ▼
             GitHub Actions
```

This is the target architecture rather than the current implementation.

---

## Planned AI Architecture

The AI layer will be introduced after the payment-domain, persistence, and reliability foundations are sufficiently mature.

### Root Cause Analysis

The planned RCA flow is:

```text
Test Failure
     │
     ▼
Failure Logs / Stack Trace
     │
     ▼
Failure Context Extraction
     │
     ▼
Embedding Generation
     │
     ▼
ChromaDB Retrieval
     │
     ▼
Local LLM via Ollama
     │
     ▼
Root Cause Summary
     │
     ▼
CI / Markdown Report
```

The system is intended to retrieve similar historical failures before asking the LLM to generate an explanation.

The AI RCA system should eventually use:

* Test failure information
* Stack traces
* Request/response information
* Application logs
* Transaction lifecycle state
* Historical failure data
* Retrieved similar failures

AI-generated explanations should remain reviewable rather than being treated as authoritative system decisions.

### AI Test Case Generation

The planned test-generation flow is:

```text
FastAPI OpenAPI Specification
          │
          ▼
      LLM Analysis
          │
          ▼
   Edge-Case Identification
          │
          ▼
   Test Scenario Suggestions
          │
          ▼
      Human Review
          │
          ▼
      Test Creation
```

AI-generated test cases will be treated as suggestions requiring validation rather than automatically trusted as executable truth.

---

## Data Flow

### Current Payment Transaction Flow

```text
Client / Dashboard
       │
       ▼
     FastAPI
       │
       ▼
 Payment Service
       │
       ├──► State Machine
       │
       ▼
Transaction Repository
       │
       ▼
In-Memory Storage
```

### Current Transaction Lifecycle Flow

```text
Authorization
      │
      ▼
AUTHORIZED
      │
      ▼
Capture
      │
      ▼
CAPTURED
      │
      ▼
Settlement
      │
      ▼
SETTLED
      │
      ├──────────────► Refund
      │                    │
      │                    ▼
      │              PARTIALLY_REFUNDED
      │                    │
      │                    ▼
      │                REFUNDED
      │
      └──────────────► REFUNDED
```

### Dashboard Lifecycle Flow

```text
Transaction ID
      │
      ▼
GET Transaction Details
      │
      ▼
Transaction History
      │
      ▼
Frontend Lifecycle Mapping
      │
      ▼
Lifecycle Visualization
```

### Planned Test Failure Flow

```text
Test Execution
      │
      ▼
Failure / Logs
      │
      ▼
AI RCA Pipeline
      │
      ├──► ChromaDB
      │
      └──► Local LLM
      │
      ▼
RCA Report
```

### Planned Test Generation Flow

```text
OpenAPI Specification
      │
      ▼
AI Test Generator
      │
      ▼
Test Scenario Suggestions
      │
      ▼
Human Review
```

---

## Directory-to-Component Mapping

The current implementation and planned architecture are reflected below.

| Directory                 | Component                                        | Status      |
| ------------------------- | ------------------------------------------------ | ----------- |
| `app/`                    | FastAPI application and payment domain           | Implemented |
| `app/domain/`             | State machine and payment-domain exceptions      | Implemented |
| `app/services/`           | Payment service layer                            | Implemented |
| `app/repositories/`       | Transaction repository abstraction               | Implemented |
| `tests/api/`              | API test suite                                   | Implemented |
| `tests/unit/`             | State-machine and service-layer tests            | Implemented |
| `dashboard/`              | React/TypeScript Web Dashboard                   | Implemented |
| `dashboard/src/pages/`    | Dashboard pages including Cards and Transactions | Implemented |
| `dashboard/src/services/` | Frontend API integration                         | Implemented |
| `tests/ui/`               | Selenium UI tests                                | Planned     |
| `ai_engine/`              | RCA and test-generation pipelines                | Planned     |
| `docker/`                 | Docker Compose and service Dockerfiles           | Planned     |
| `.github/workflows/`      | CI/CD workflows                                  | Planned     |

---

## Design Principles

### Separation of Concerns

HTTP handling, payment business logic, state validation, persistence, and frontend presentation are kept in separate layers.

```text
UI
 ↓
API
 ↓
Service
 ↓
Domain
 ↓
Repository
 ↓
Storage
```

Each layer should have a clear responsibility and should avoid leaking implementation details into adjacent layers.

### Domain-First Design

Payment lifecycle rules are modeled explicitly instead of being scattered across API endpoints.

This provides a single source of truth for transaction state transitions.

### Testability

Business logic should be testable without requiring the HTTP server, frontend, database, or external infrastructure.

The current service and state-machine test suites follow this principle.

### Persistence Abstraction

Payment services interact with transactions through a repository rather than directly depending on the storage implementation.

This allows the persistence mechanism to evolve from in-memory storage to PostgreSQL.

### Frontend / Backend Separation

The dashboard communicates with the backend through defined API contracts.

The frontend should not contain payment-domain business rules.

The backend remains the source of truth for:

* Transaction state
* Transaction amounts
* Lifecycle transitions
* Transaction history
* Payment validation

### Deterministic Failure Simulation

Controlled technical failures can be injected through API headers.

This makes failure scenarios reproducible and provides a foundation for future resilience and AI-RCA testing.

### Offline-Friendly AI

The planned AI architecture uses a local LLM through Ollama rather than requiring a hosted LLM API.

This supports local experimentation and avoids mandatory external API costs.

### Traceability

Payment transactions maintain transaction history events.

The transaction lifecycle dashboard exposes this history for visual inspection.

Future versions will extend this into a durable audit/event model suitable for payment-system debugging and observability.

### Incremental Architecture Evolution

The project intentionally introduces architectural complexity only when the underlying behavior has been validated.

The current progression is:

```text
Core Payment Flow
        ↓
Domain State Machine
        ↓
Service Layer
        ↓
Repository Abstraction
        ↓
Web Dashboard
        ↓
Persistent Storage
        ↓
Reliability Controls
        ↓
UI Automation
        ↓
AI Augmentation
        ↓
CI/CD + Observability
```

---

## Reliability and Security Considerations

The current implementation is a development-oriented mock gateway and does not represent a production payment processor.

Before the platform can be considered production-oriented, the architecture must address:

* Idempotency
* Monetary precision
* Database transaction boundaries
* Concurrency control
* Duplicate request handling
* Durable audit trails
* Authentication and authorization
* Secrets management
* Input validation
* Rate limiting
* Structured logging
* Observability
* Data protection
* PCI-related design considerations
* Failure recovery and retry semantics
* API versioning
* Transaction consistency
* Frontend/backend error synchronization

These concerns are part of the planned architecture rather than completed functionality.

---

## Deployment View

### Current Development Environment

The current payment gateway can be run as a local FastAPI application.

The current project also contains a local web dashboard that communicates with the gateway through the API layer.

The primary backend development environment currently uses:

```text
Python 3.11
FastAPI
Pytest
In-Memory Storage
```

The dashboard is implemented as a React/TypeScript application.

### Planned Local Deployment

The broader platform is intended to use Docker Compose to orchestrate services such as:

| Service              | Default Port | Status      |
| -------------------- | -----------: | ----------- |
| Mock Payment Gateway |       `8000` | Implemented |
| Web Dashboard        |       `3000` | Implemented |
| ChromaDB             |       `8001` | Planned     |
| Ollama               |      `11434` | Planned     |
| PostgreSQL           |       `5432` | Planned     |

The exact deployment topology will be finalized as the corresponding components are implemented.

---

## Current Architectural Status

### Completed

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
* [x] React/TypeScript web dashboard
* [x] Cards dashboard
* [x] Transactions dashboard
* [x] Transaction summary statistics
* [x] Transaction status display
* [x] Transaction lifecycle inspection
* [x] Transaction lifecycle history visualization
* [x] Frontend/backend API integration

### Planned

* [ ] Monetary precision model
* [ ] Idempotency
* [ ] Concurrency safety
* [ ] PostgreSQL persistence
* [ ] Durable audit/event storage
* [ ] Authentication and authorization
* [ ] Observability
* [ ] Selenium UI automation
* [ ] AI root cause analysis
* [ ] AI test case generation
* [ ] Docker deployment
* [ ] GitHub Actions CI/CD
* [ ] Production-oriented security hardening
* [ ] Advanced transaction filtering and search
* [ ] Automated lifecycle validation from the dashboard
* [ ] Historical transaction analytics

