# ARCHITECTURE.md — PayGuard AI

## Overview

PayGuard AI is an AI-augmented payment-system testing and reliability platform.

The current implementation establishes a testable payment-domain foundation, a FastAPI payment gateway, a React/TypeScript web dashboard, API and unit test coverage, and Playwright-based end-to-end browser automation.

The architecture is intentionally being developed incrementally. The current system prioritizes deterministic payment behavior, explicit transaction lifecycle rules, testability, API contracts, frontend/backend separation, idempotency, auditability, and browser-level validation before introducing heavier infrastructure such as PostgreSQL, observability platforms, and AI-powered failure analysis.

The current system is organized around the following primary concerns:

1. **Web Dashboard Layer** — React/TypeScript frontend for interacting with the payment gateway.
2. **API / HTTP Layer** — FastAPI endpoints responsible for request validation, routing, and HTTP responses.
3. **Payment Service Layer** — Contains payment transaction business logic for authorization, capture, settlement, and refunds.
4. **Domain Layer** — Defines transaction states, lifecycle transitions, and typed payment-domain exceptions.
5. **Repository / Storage Layer** — Provides persistence abstraction over the current in-memory implementation.
6. **Audit Layer** — Records operational transaction events without storing raw sensitive payment payloads.
7. **Idempotency Layer** — Prevents duplicate processing when the same idempotency key and request are replayed.
8. **Test Automation Layer** — Pytest-based API/unit tests together with Playwright browser tests.
9. **Planned AI Layer** — Future AI-assisted root cause analysis and test generation.

The planned architecture will extend this foundation with persistent database storage, stronger concurrency controls, observability, containerization, CI/CD orchestration, and AI-assisted engineering workflows.

---

## Current Architecture

```text
                         ┌───────────────────────────┐
                         │       Web Dashboard       │
                         │     React / TypeScript     │
                         │                           │
                         │  Overview                 │
                         │  Cards                    │
                         │  Transactions             │
                         │  Lifecycle Inspection     │
                         │  AI Insights              │
                         └─────────────┬─────────────┘
                                       │
                                       │ HTTP / REST
                                       ▼
                         ┌───────────────────────────┐
                         │        FastAPI API        │
                         │       / HTTP Layer        │
                         └─────────────┬─────────────┘
                                       │
                                       ▼
                         ┌───────────────────────────┐
                         │      Payment Service      │
                         │    Business Operations    │
                         └─────────────┬─────────────┘
                                       │
                     ┌─────────────────┼─────────────────┐
                     │                 │                 │
                     ▼                 ▼                 ▼
             ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
             │ State Machine │ │ Audit Service │ │  Idempotency  │
             │               │ │               │ │   Handling    │
             └───────┬───────┘ └───────────────┘ └───────────────┘
                     │
                     ▼
             ┌─────────────────────┐
             │ Transaction         │
             │ Repository          │
             └──────────┬──────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │  In-Memory Storage  │
             │ Cards               │
             │ Transactions        │
             │ Audit Events        │
             │ Idempotency Records │
             └─────────────────────┘
````

The current architecture keeps HTTP concerns separate from payment-domain business logic.

The web dashboard communicates with the FastAPI backend through HTTP/REST APIs. The dashboard does not directly access application storage or payment-domain logic.

The backend remains the source of truth for:

* Transaction state
* Transaction amounts
* Lifecycle transitions
* Transaction history
* Payment validation
* Idempotency behavior
* Audit event recording

This separation allows:

* Backend payment behavior to be tested independently.
* Frontend behavior to be validated against the same API used by API tests.
* Transaction lifecycle rules to remain centralized.
* Storage to be replaced without rewriting payment business logic.
* Browser automation to validate the real dashboard/API integration.

---

## Current Architecture Components

| Layer           | Component                 | Responsibility                                                   | Status      |
| --------------- | ------------------------- | ---------------------------------------------------------------- | ----------- |
| UI              | Web Dashboard             | Browser interface for payment operations and monitoring          | Implemented |
| UI              | Overview Interface        | Gateway status and transaction summary                           | Implemented |
| UI              | Cards Interface           | Card creation and card information                               | Implemented |
| UI              | Transactions Interface    | Transaction monitoring and status display                        | Implemented |
| UI              | Lifecycle View            | Transaction lifecycle and history inspection                     | Implemented |
| API             | FastAPI                   | HTTP routing, validation, response handling                      | Implemented |
| Application     | Payment Service           | Authorization, capture, settlement, refunds                      | Implemented |
| Domain          | Transaction State Machine | Validates lifecycle transitions                                  | Implemented |
| Domain          | Payment Exceptions        | Typed payment-domain errors                                      | Implemented |
| Persistence     | Transaction Repository    | Abstracts transaction persistence                                | Implemented |
| Persistence     | In-Memory Storage         | Stores application state                                         | Implemented |
| Reliability     | Idempotency               | Prevents duplicate processing for replayed requests              | Implemented |
| Audit           | Audit Service             | Records operational/payment audit events                         | Implemented |
| API             | Failure Simulation        | Deterministic technical failure injection                        | Implemented |
| Test Automation | API Tests                 | Positive, negative, boundary, idempotency, and failure scenarios | Implemented |
| Test Automation | Unit Tests                | Service, money, audit, and state-machine validation              | Implemented |
| Test Automation | Playwright E2E            | Browser-level dashboard validation                               | Implemented |
| AI Engine       | RCA Pipeline              | AI-assisted root cause analysis                                  | Planned     |
| AI Engine       | Test Generator            | LLM-assisted test scenario generation                            | Planned     |
| Persistence     | PostgreSQL                | Durable transactional storage                                    | Planned     |
| Observability   | OpenTelemetry             | Application/test observability                                   | Planned     |
| Orchestration   | Docker                    | Service containerization                                         | Planned     |
| CI/CD           | GitHub Actions            | Automated test and AI workflows                                  | Planned     |

---

## Web Dashboard Architecture

The web dashboard provides the browser interface over the PayGuard AI payment gateway.

The current dashboard contains:

```text
Web Dashboard
│
├── Overview
│   ├── Gateway Status
│   ├── Transaction Summary
│   ├── Recent Transactions
│   ├── System Health
│   └── Payment Operations
│
├── Transactions
│   ├── Transaction Summary
│   ├── Transaction Table
│   ├── Transaction Status
│   ├── Transaction Amount
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

The frontend communicates with the FastAPI backend through API services.

The intended dependency direction is:

```text
React / TypeScript Dashboard
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
            │
            ▼
         Storage
```

The frontend does not directly access the storage layer.

The backend remains responsible for payment-domain decisions.

---

## Transaction Dashboard

The Transactions page provides a monitoring interface for payment activity.

The current interface supports:

* Total transaction count
* Completed transaction count
* In-progress transaction count
* Transaction ID
* Merchant ID
* Transaction amount
* Transaction status
* Creation timestamp
* Transaction lifecycle inspection
* Empty-state rendering
* Transaction refresh

A transaction can be selected through the **View Lifecycle** action.

The frontend obtains transaction information through the backend API and renders the transaction lifecycle.

The frontend does not independently determine whether a transaction transition is valid.

The backend state machine remains the source of truth.

---

## Transaction Lifecycle View

The transaction lifecycle interface provides a visual representation of the backend transaction state and transaction history.

The primary lifecycle is:

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

Partial refunds are represented as:

```text
SETTLED
   │
   ▼
PARTIALLY_REFUNDED
   │
   ▼
REFUNDED
```

The lifecycle interface exposes transaction information such as:

* Transaction ID
* Merchant ID
* Authorized amount
* Captured amount
* Settled amount
* Refunded amount
* Lifecycle stage
* Lifecycle event description
* Lifecycle event timestamp
* Card ID
* Transaction creation timestamp

The lifecycle UI is a presentation layer over backend transaction history.

The frontend should not reconstruct or independently validate the transaction state machine.

---

## Payment Transaction Lifecycle

The payment domain models transaction lifecycle states explicitly.

```text
AUTHORIZED
    │
    ▼
CAPTURED
    │
    ▼
SETTLED
    │
    ├───────────────┐
    │               │
    ▼               ▼
PARTIALLY_       REFUNDED
REFUNDED
    │
    ▼
REFUNDED
```

The state machine explicitly prevents invalid transitions.

Examples include:

* Capturing a declined transaction
* Capturing an already captured transaction
* Settling an authorized transaction before capture
* Settling an already settled transaction
* Refunding an unsettled transaction
* Refunding an already fully refunded transaction
* Refunding more than the remaining refundable amount

These lifecycle rules are independently tested by the state-machine test suite.

---

## Transaction History

Each transaction maintains lifecycle history events.

A completed transaction can contain a sequence such as:

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

Transaction history provides the data used by the dashboard lifecycle view.

The architectural separation is:

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

The frontend should not independently reconstruct the authoritative transaction history.

---

## Payment Service Layer

The `PaymentService` provides application-level business operations for transaction processing.

Current responsibilities include:

* Retrieve transactions through the repository
* Validate transaction existence
* Validate transaction state
* Validate transaction amounts
* Apply lifecycle transitions
* Update transaction amounts
* Append transaction history
* Persist updated transactions
* Coordinate payment-domain operations

The service layer does not depend on FastAPI-specific HTTP semantics.

This keeps business behavior testable without requiring an HTTP server.

---

## Authorization

Authorization validates an active payment card and creates a transaction.

The conceptual flow is:

```text
Authorization Request
        │
        ▼
   Validate Card
        │
        ├── Card Not Found
        │       │
        │       ▼
        │     Error
        │
        ├── Card Inactive
        │       │
        │       ▼
        │     Error
        │
        ▼
   Validate Amount
        │
        ├── Invalid Amount
        │       │
        │       ▼
        │     Validation Error
        │
        ▼
  Validate Available Balance
        │
        ├── Insufficient Funds
        │       │
        │       ▼
        │     DECLINED
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

Authorization also participates in idempotency handling when an `Idempotency-Key` is supplied.

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
* Record the corresponding audit event

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
* Record the corresponding audit event

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
* Record the corresponding audit event

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

The transaction state machine provides a centralized location for validating lifecycle transitions.

Current valid transitions include:

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

The state machine is independent from the API layer.

This allows lifecycle rules to be tested without starting the HTTP application.

---

## Domain Exceptions

Payment operations use typed domain exceptions rather than requiring callers to interpret arbitrary error-message strings.

The current exception hierarchy includes:

```text
PaymentError
│
├── TransactionNotFoundError
├── InvalidTransactionStateError
├── CaptureAmountExceededError
└── RefundAmountExceededError
```

The FastAPI layer translates domain exceptions into appropriate HTTP responses.

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

This keeps payment services independent from HTTP semantics while preserving a clear API contract.

---

## Repository Layer

The transaction repository provides a persistence abstraction between the payment service and the storage mechanism.

Current responsibilities include:

* Adding transactions
* Retrieving transactions
* Updating transactions

The current implementation delegates persistence to in-memory storage.

```text
PaymentService
      │
      ▼
TransactionRepository
      │
      ▼
In-Memory Storage
```

The repository abstraction allows the persistence implementation to evolve without coupling payment business logic directly to a database.

---

## Current Persistence Model

The current application uses in-memory storage.

The storage implementation currently maintains separate collections for:

```text
InMemoryStorage
│
├── cards
├── transactions
├── audit_events
└── idempotency_records
```

This is appropriate for the current development stage because it allows payment-domain behavior and test automation to be developed without introducing database infrastructure prematurely.

However, in-memory persistence is not suitable for production-like payment processing.

Current limitations include:

* Data is not durable
* Application restart loses state
* No database transactions
* No row-level locking
* No distributed concurrency control
* No persistence-level uniqueness constraints
* No durable audit/event history
* Idempotency records are not durable across process restarts

These limitations are part of the planned persistence and reliability phases.

---

## Idempotency

Idempotency is currently implemented at the application level.

The API can accept an `Idempotency-Key` for authorization requests.

The system stores:

```text
Idempotency Record
│
├── Idempotency Key
├── Request Fingerprint
└── Original Response
```

This allows the system to distinguish between:

```text
Same key + same request
        │
        ▼
Replay original response
```

and:

```text
Same key + different request
        │
        ▼
Reject request
```

A reused key with a different authorization request is rejected with a conflict response.

Different idempotency keys represent separate authorization operations.

Requests without an idempotency key retain the existing non-idempotent behavior.

The current implementation is application-level and backed by in-memory storage. Durable idempotency and concurrency-safe behavior remain future production-hardening work.

---

## Audit Architecture

The application maintains a separate audit-event collection.

Audit events represent operational and transaction history and are stored independently from transaction objects.

The current storage model is:

```text
InMemoryStorage
      │
      ├── Transactions
      │
      └── Audit Events
```

Audit events are stored defensively so external references cannot mutate persisted audit records accidentally.

The current audit test suite validates:

* Audit event creation
* Audit event persistence
* Audit event timestamps
* Lookup by transaction
* Lookup by correlation identifier
* Support for failed operations
* Operation without requiring sensitive payloads
* Absence of raw card numbers in audit events

The current audit implementation remains in-memory and is therefore not durable across application restarts.

---

## API / HTTP Layer

The FastAPI layer currently handles:

* Request validation
* Endpoint routing
* Card issuance
* Transaction authorization
* Transaction capture
* Transaction settlement
* Transaction refunds
* Transaction lookup
* Simulated technical failures
* HTTP response formatting
* Translation of domain exceptions into HTTP responses
* Idempotency request handling

The API layer should not contain the core transaction state-machine rules.

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

The API supports deterministic technical failure simulation through the `X-Simulate-Failure` request header.

Supported simulation values include:

```text
TIMEOUT
NETWORK_ERROR
INVALID_RESPONSE
```

The intended behavior is:

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

The purpose of deterministic failure injection is to provide reproducible technical failure conditions for reliability testing and future AI-assisted root cause analysis.

---

## Test Architecture

The current automated test suite uses Pytest.

It contains:

1. API tests
2. Unit tests
3. Playwright end-to-end tests

The current regression suite contains:

```text
API Tests
     │
     ├── Authorization
     ├── Capture
     ├── Card Issuance
     ├── Refund
     ├── Settlement
     └── Audit
     
Unit Tests
     │
     ├── Payment Service
     ├── State Machine
     └── Money / Monetary Validation

E2E Tests
     │
     ├── Dashboard Smoke
     ├── Card Issuance
     └── Transactions
```

### Current Regression Baseline

The current project baseline is:

```text
Total Tests       96
Passed            96
Failed             0
```

The regression suite includes:

* Positive cases
* Negative cases
* Boundary cases
* Validation cases
* State-transition cases
* Idempotency cases
* Audit cases
* Browser-level dashboard cases

The baseline should be updated whenever tests are intentionally added or removed.

---

## API Test Architecture

API tests validate externally observable FastAPI behavior.

The authorization suite covers scenarios including:

* Successful authorization
* Insufficient funds
* Card not found
* Inactive card
* Exact balance authorization
* Missing required fields
* Invalid amounts
* Idempotency replay
* Prevention of duplicate charging
* Idempotency-key reuse with a different request
* Separate operations for different idempotency keys
* Requests without an idempotency key

The card issuance suite covers:

* Successful card creation
* Missing required fields
* Invalid card networks
* Zero initial balance
* Negative initial balance
* Unique card identifiers

Capture, settlement, refund, and audit suites similarly validate positive, negative, boundary, and reliability behavior.

---

## Unit Test Architecture

Unit tests validate business logic independently from the HTTP layer.

The current unit coverage includes:

```text
Unit Tests
│
├── Payment Service
│   ├── Capture
│   ├── Settlement
│   └── Refund
│
├── State Machine
│   ├── Valid transitions
│   └── Invalid transitions
│
├── Money
│   ├── Decimal arithmetic
│   ├── Amount validation
│   └── Payment amount boundaries
│
└── Audit Service
    ├── Event creation
    ├── Persistence
    ├── Lookup
    └── Sensitive-data protection
```

The service and state-machine layers can therefore be validated without requiring the frontend or a browser.

---

## Playwright E2E Architecture

The current UI automation layer uses **Playwright with Python**, integrated with Pytest.

The current E2E architecture is:

```text
Pytest
   │
   ▼
Playwright
   │
   ▼
Chromium
   │
   ▼
React / TypeScript Dashboard
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

The frontend development server is currently expected to be running before E2E tests execute.

The E2E environment uses:

```text
Frontend: http://localhost:5173
Backend:  http://localhost:8000
```

The E2E fixtures create deterministic backend data through the API before browser assertions are executed.

This avoids relying on manually prepared browser state.

---

## E2E Page Object Model

The Playwright test suite uses a Page Object Model.

The current Transactions page object encapsulates:

* Sidebar navigation
* Transactions page heading
* Page description
* Transactions list
* Transaction table
* Empty state
* Refresh control
* Lifecycle dialog
* Transaction lookup
* Transaction status assertions
* Transaction amount assertions
* Lifecycle dialog interaction

The Page Object converts backend transaction UUIDs into the shortened representation currently rendered by the frontend.

For example:

```text
Backend:

b8cd34da-d6f8-48d1-933a-74bcc919aea4

Frontend:

b8cd34da...19aea4
```

This keeps presentation-specific locator behavior inside the Page Object rather than scattering it throughout individual tests.

---

## E2E Test Data Strategy

The E2E suite creates required backend data through API fixtures.

The current transaction E2E flow is:

```text
E2E Fixture
    │
    ▼
Create Card through API
    │
    ▼
Create Authorized Transaction through API
    │
    ▼
Open Browser
    │
    ▼
Navigate Dashboard
    │
    ▼
Open Transactions
    │
    ▼
Validate Transaction
    │
    ▼
Open Lifecycle
    │
    ▼
Validate Lifecycle Dialog
```

This provides deterministic test data while still validating the real browser application.

The fixture-based approach also prevents the E2E suite from depending on manually created cards or transactions.

---

## Current E2E Coverage

The current E2E suite validates:

```text
Dashboard
   └── Dashboard smoke test

Cards
   └── Card issuance workflow

Transactions
   ├── Transactions page loads
   ├── Empty transaction state
   ├── Authorized transaction appears
   └── Authorized transaction lifecycle can be opened
```

The current E2E suite is implemented with Playwright rather than Selenium.

---

## Planned Extended E2E Coverage

Future browser automation should expand coverage to include:

* Dashboard navigation
* Card creation
* Card listing
* Card status
* Transaction authorization
* Transaction capture
* Transaction settlement
* Full refund
* Partial refund
* Transaction lifecycle rendering
* Refresh behavior
* Error handling
* Empty states
* Backend/frontend state synchronization
* Failure simulation behavior
* Idempotency-related UI behavior where applicable

The E2E suite should continue to use API-backed fixtures for deterministic setup rather than depending on brittle pre-existing browser state.

---

## Planned Extended Architecture

The broader platform is intended to evolve into:

```text
                         ┌───────────────────────┐
                         │    Web Dashboard      │
                         │ React / TypeScript    │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │   Playwright E2E      │
                         │    Test Suite         │
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
                                     ▼
                         ┌───────────────────────┐
                         │ Payment Domain Model  │
                         │   + State Machine     │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │     Repository        │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │      PostgreSQL       │
                         └───────────────────────┘


        ┌──────────────────────┐
        │    Pytest Results    │
        │    Failure Logs      │
        │    Stack Traces      │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │     AI RCA Engine    │
        │ LangChain + ChromaDB │
        │       + Ollama       │
        └──────────────────────┘


        ┌──────────────────────┐
        │  AI Test Generator   │
        │  OpenAPI + LLM       │
        └──────────────────────┘


                 CI/CD
                   │
                   ▼
             GitHub Actions
```

This represents the target architecture rather than the current implementation.

---

## Planned AI Architecture

The AI layer will be introduced after the payment-domain, persistence, reliability, and test-automation foundations are sufficiently mature.

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

Potential RCA inputs include:

* Test failure information
* Stack traces
* Request/response information
* Application logs
* Transaction lifecycle state
* Historical failure data
* Retrieved similar failures

AI-generated explanations should remain reviewable and should not be treated as authoritative system decisions.

---

## AI Test Case Generation

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

AI-generated tests should be treated as suggestions requiring validation.

The system should not blindly convert LLM output into trusted executable tests.

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
       ├──► Audit
       │
       └──► Idempotency
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

### E2E Test Flow

```text
Pytest
  │
  ▼
API Fixture
  │
  ├──► Create Card
  │
  └──► Create Transaction
           │
           ▼
     Playwright Browser
           │
           ▼
      Web Dashboard
           │
           ▼
     UI Assertions
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

| Directory                 | Component                                                            | Status      |
| ------------------------- | -------------------------------------------------------------------- | ----------- |
| `app/`                    | FastAPI application and payment-domain implementation                | Implemented |
| `app/domain/`             | State machine and payment-domain exceptions                          | Implemented |
| `app/services/`           | Payment service and audit-related business logic                     | Implemented |
| `app/repositories/`       | Transaction repository abstraction                                   | Implemented |
| `app/storage.py`          | In-memory cards, transactions, audit events, and idempotency records | Implemented |
| `tests/api/`              | API test suite                                                       | Implemented |
| `tests/unit/`             | Service, state-machine, money, and audit tests                       | Implemented |
| `tests/e2e/`              | Playwright E2E test suite                                            | Implemented |
| `tests/e2e/pages/`        | Playwright Page Objects                                              | Implemented |
| `dashboard/`              | React/TypeScript web dashboard                                       | Implemented |
| `dashboard/src/pages/`    | Dashboard pages including Cards and Transactions                     | Implemented |
| `dashboard/src/services/` | Frontend API integration                                             | Implemented |
| `ai_engine/`              | RCA and test-generation pipelines                                    | Planned     |
| `docker/`                 | Docker Compose and service Dockerfiles                               | Planned     |
| `.github/workflows/`      | CI/CD workflows                                                      | Planned     |

---

## Design Principles

### Separation of Concerns

HTTP handling, payment business logic, state validation, persistence, frontend presentation, audit recording, and browser automation remain separate concerns.

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

Test automation interacts with the system through defined interfaces rather than embedding business logic inside tests.

---

### Domain-First Design

Payment lifecycle rules are modeled explicitly instead of being scattered across API endpoints.

This provides a single source of truth for transaction state transitions.

---

### Testability

Business logic should be testable without requiring:

* The browser
* The frontend
* The HTTP server
* A production database
* External AI infrastructure

The current service, money, audit, and state-machine tests follow this principle.

---

### Persistence Abstraction

Payment services interact with transactions through a repository rather than directly depending on the storage implementation.

This allows the persistence mechanism to evolve from in-memory storage to PostgreSQL.

---

### Frontend / Backend Separation

The dashboard communicates with the backend through API contracts.

The frontend should not contain payment-domain business rules.

The backend remains the source of truth for:

* Transaction state
* Transaction amounts
* Lifecycle transitions
* Transaction history
* Payment validation
* Idempotency behavior

---

### Deterministic Failure Simulation

Controlled technical failures can be injected through API headers.

This makes failure scenarios reproducible and provides a foundation for reliability testing and future AI-assisted RCA.

---

### Deterministic Test Data

E2E tests create required backend state through API fixtures.

This avoids dependence on manually prepared application state and makes browser tests reproducible.

---

### Page Object Encapsulation

Playwright selectors and page-specific UI behavior are encapsulated in Page Objects.

Tests should express business behavior rather than repeat raw locator implementation.

For example:

```text
Test
 │
 └── transactions_page.open()
 └── transactions_page.expect_page_loaded()
 └── transactions_page.expect_transaction_visible(id)
 └── transactions_page.open_transaction_lifecycle(id)
```

This reduces selector duplication and isolates frontend presentation changes.

---

### Idempotent Payment Operations

Authorization supports idempotency keys so clients can safely retry requests without unintentionally creating duplicate operations.

The current implementation distinguishes:

```text
Same key + same request
        =
Replay original response
```

from:

```text
Same key + different request
        =
Conflict
```

Durable and concurrency-safe idempotency remains a future persistence concern.

---

### Auditability

Important payment operations produce audit information.

Audit records should remain separate from raw payment payloads and should not expose sensitive card information.

Future implementations should make audit history durable and queryable.

---

### Offline-Friendly AI

The planned AI architecture uses a local LLM through Ollama rather than requiring a hosted LLM API.

This supports local experimentation and reduces mandatory dependence on external API infrastructure.

---

### Human Review of AI Output

AI-generated root-cause explanations and test scenarios should be treated as engineering assistance rather than authoritative decisions.

Human review remains required before AI-generated output becomes part of the trusted test or diagnostic workflow.

---

### Traceability

Payment transactions maintain lifecycle history events.

The transaction lifecycle dashboard exposes this history for visual inspection.

Future versions will extend this into a durable audit/event model suitable for payment-system debugging and observability.

---

### Incremental Architecture Evolution

The project intentionally introduces architectural complexity only after the underlying behavior has been validated.

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
Audit + Idempotency
        ↓
Web Dashboard
        ↓
Playwright E2E Automation
        ↓
Persistent Storage
        ↓
Reliability Controls
        ↓
Observability
        ↓
AI Augmentation
        ↓
CI/CD
```

---

## Reliability and Security Considerations

The current implementation is a development-oriented mock payment gateway and does not represent a production payment processor.

Before the platform can be considered production-oriented, the architecture must address:

* Durable persistence
* Database transaction boundaries
* Concurrency control
* Durable idempotency
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
* Production-grade monitoring
* Disaster recovery

Some reliability concerns are already represented in the current test architecture, particularly:

* Idempotency behavior
* Monetary validation
* State-transition validation
* Audit event behavior
* Deterministic failure simulation

However, application-level implementation should not be confused with production-grade infrastructure guarantees.

---

## Deployment View

### Current Development Environment

The current payment gateway runs locally as a FastAPI application.

The local dashboard runs as a React/TypeScript development application and communicates with the backend through the API layer.

The current backend development environment uses:

```text
Python 3.11
FastAPI
Pytest
In-Memory Storage
```

The current E2E environment uses:

```text
Frontend
http://localhost:5173

Backend
http://localhost:8000
```

The frontend development server is expected to be running before Playwright E2E tests are executed.

### Planned Local Deployment

The broader platform is intended to use Docker Compose to orchestrate services such as:

| Service              | Default Port | Status      |
| -------------------- | -----------: | ----------- |
| Mock Payment Gateway |       `8000` | Implemented |
| Web Dashboard        |       `5173` | Implemented |
| ChromaDB             |       `8001` | Planned     |
| Ollama               |      `11434` | Planned     |
| PostgreSQL           |       `5432` | Planned     |

The exact deployment topology will be finalized as the corresponding infrastructure components are implemented.

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
* [x] Monetary validation
* [x] Idempotency handling
* [x] Audit event recording
* [x] Deterministic failure simulation
* [x] API test suite
* [x] Payment service test suite
* [x] State-machine test suite
* [x] Money validation tests
* [x] Audit service tests
* [x] React/TypeScript web dashboard
* [x] Overview dashboard
* [x] Cards dashboard
* [x] Transactions dashboard
* [x] Transaction summary statistics
* [x] Transaction status display
* [x] Transaction lifecycle inspection
* [x] Transaction lifecycle history visualization
* [x] Frontend/backend API integration
* [x] Playwright E2E test infrastructure
* [x] Playwright Page Object Model
* [x] Dashboard smoke E2E test
* [x] Card issuance E2E test
* [x] Transactions E2E tests
* [x] API-backed E2E test fixtures
* [x] 96-test passing regression baseline

### Planned

* [ ] PostgreSQL persistence
* [ ] Durable audit/event storage
* [ ] Durable idempotency storage
* [ ] Concurrency-safe transaction processing
* [ ] Production-grade authentication and authorization
* [ ] OpenTelemetry observability
* [ ] Structured application logging
* [ ] Docker deployment
* [ ] GitHub Actions CI/CD
* [ ] AI root cause analysis
* [ ] AI test case generation
* [ ] Historical failure retrieval
* [ ] Advanced transaction filtering and search
* [ ] Automated lifecycle validation from the dashboard
* [ ] Historical transaction analytics
* [ ] Production-oriented security hardening
* [ ] Failure recovery and retry strategy
* [ ] Distributed reliability controls

---

## Architectural Roadmap

The architecture should evolve in the following order:

```text
Phase 1
Core Payment Domain
        │
        ▼
Phase 2
Service + Repository Architecture
        │
        ▼
Phase 3
API Reliability
(Idempotency + Audit + Validation)
        │
        ▼
Phase 4
Web Dashboard
        │
        ▼
Phase 5
Playwright E2E Automation
        │
        ▼
Phase 6
Persistent Storage
(PostgreSQL)
        │
        ▼
Phase 7
Concurrency + Reliability
        │
        ▼
Phase 8
Observability
        │
        ▼
Phase 9
AI RCA
        │
        ▼
Phase 10
AI Test Generation
        │
        ▼
Phase 11
CI/CD + Full Platform Orchestration
```

Each phase should preserve the testability and separation-of-concerns established by the previous phase.

The architecture should not introduce infrastructure merely because the diagram looks more impressive with twelve boxes and a database. Each new component should solve a demonstrated engineering requirement.

---

## Architectural Decision Summary

The current architecture makes the following deliberate decisions:

| Decision                | Current Approach              | Reason                                                     |
| ----------------------- | ----------------------------- | ---------------------------------------------------------- |
| API framework           | FastAPI                       | Clear API contracts and Python ecosystem                   |
| Backend language        | Python 3.11                   | Current application/runtime baseline                       |
| Payment logic           | Service layer                 | Separates business rules from HTTP                         |
| Lifecycle validation    | Explicit state machine        | Centralizes transaction rules                              |
| Persistence abstraction | Repository                    | Allows future database migration                           |
| Current persistence     | In-memory storage             | Fast deterministic development                             |
| Idempotency             | Application-level records     | Prevents duplicate authorization processing                |
| Audit                   | Separate audit events         | Operational traceability without raw card payloads         |
| Frontend                | React + TypeScript            | Browser-based payment dashboard                            |
| UI automation           | Playwright + Pytest           | Browser-level validation integrated with Python test suite |
| Test structure          | API + Unit + E2E              | Multiple validation layers                                 |
| E2E data setup          | API fixtures                  | Deterministic browser test state                           |
| Failure simulation      | API header                    | Reproducible technical failures                            |
| Future database         | PostgreSQL                    | Durable transactional persistence                          |
| Future RCA              | LangChain + ChromaDB + Ollama | Local retrieval-augmented diagnostic workflow              |
| Future test generation  | OpenAPI + LLM                 | API-contract-driven scenario generation                    |
| Future CI/CD            | GitHub Actions                | Automated regression and AI workflows                      |

---

## Final Architecture Principle

PayGuard AI is being developed as a testable payment system first and an AI platform second.

The architecture therefore prioritizes:

```text
Correct Payment Behavior
        ↓
Explicit Domain Rules
        ↓
Reliable APIs
        ↓
Auditability + Idempotency
        ↓
Deterministic Tests
        ↓
Browser Validation
        ↓
Persistent Infrastructure
        ↓
Observability
        ↓
AI Assistance
```

