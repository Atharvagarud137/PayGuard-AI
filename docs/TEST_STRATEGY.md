# TEST_STRATEGY.md — PayGuard AI

## Purpose

This document defines the testing strategy for PayGuard AI.

PayGuard AI is an AI-augmented payment-system testing platform built around a simulated payment gateway. The testing strategy focuses on validating payment-domain correctness, transaction lifecycle behavior, API contracts, failure handling, boundary conditions, idempotency, auditability, and the ability to observe transactions through their complete lifecycle.

The current implementation provides:

- A functional payment gateway
- Payment-domain and state-machine validation
- Payment service validation
- API-level validation
- Idempotency handling
- Audit-event recording
- A functional Web Dashboard
- Automated Playwright browser tests for the dashboard
- End-to-end transaction setup through the API and validation through the UI

The testing strategy follows a layered approach:

```text
Domain / State Machine
        ↓
Payment Service
        ↓
API
        ↓
Integration
        ↓
UI / End-to-End
        ↓
Reliability
        ↓
Observability
        ↓
AI Validation
        ↓
CI/CD
````

The objective is not simply to maximize test count. The objective is to establish confidence that payment transactions behave correctly from authorization through capture, settlement, and refund while failures, invalid operations, duplicate requests, and lifecycle inconsistencies remain deterministic and diagnosable.

---

# Current Test Architecture

The current automated test suite is organized into four implemented layers:

```text
┌──────────────────────────┐
│       API Tests          │
│        36 tests          │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│    Payment Service        │
│        14 tests           │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│     State Machine         │
│        14 tests           │
└──────────────────────────┘

┌──────────────────────────┐
│       E2E Tests           │
│         4 tests           │
│      Playwright           │
└──────────────────────────┘
```

## Current Test Baseline

| Test Layer      | Tool                |               Tests | Status      |
| --------------- | ------------------- | ------------------: | ----------- |
| State Machine   | Pytest              |                  14 | Passing     |
| Payment Service | Pytest              |                  14 | Passing     |
| API             | Pytest              |                  36 | Passing     |
| E2E / UI        | Pytest + Playwright |                   4 | Passing     |
| **Total**       | **Pytest**          | **68 direct tests** | **Passing** |

The complete current regression run reports:

```text
96 collected
96 passed
0 failed
```

The difference between the 68 directly counted tests above and the 96-test regression total is due to the broader test suite containing additional unit/API coverage beyond the principal layers summarized in the table.

The latest verified regression baseline is:

```text
96 tests
96 passed
0 failed
```

The E2E suite currently contains:

```text
4 tests
4 passed
```

The current E2E suite validates:

* Dashboard navigation
* Transactions page loading
* Transactions empty state
* Authorized transaction visibility
* Merchant visibility
* Transaction status visibility
* Transaction lifecycle dialog
* Lifecycle dialog closing

---

# Test Pyramid

The project follows a layered test pyramid in which lower-level tests provide fast deterministic feedback and higher-level tests validate cross-system behavior.

| Layer                  | Tool                   | Current Status                    | Purpose                                                          |
| ---------------------- | ---------------------- | --------------------------------- | ---------------------------------------------------------------- |
| Domain / State Machine | Pytest                 | Implemented                       | Validate lifecycle rules and domain transitions                  |
| Service Tests          | Pytest                 | Implemented                       | Validate payment business logic independently of HTTP            |
| API Tests              | Pytest + HTTP client   | Implemented                       | Validate externally observable gateway behavior                  |
| E2E / UI Tests         | Playwright + Pytest    | Implemented                       | Validate dashboard behavior through a real browser               |
| Integration Tests      | Pytest                 | Planned                           | Validate API, services, repositories, and persistence together   |
| Reliability Tests      | Pytest                 | Partially implemented / Expanding | Validate idempotency, failure handling, retries, and concurrency |
| Persistence Tests      | Pytest + PostgreSQL    | Planned                           | Validate durable state and transactional consistency             |
| Observability Tests    | Pytest / OpenTelemetry | Planned                           | Validate logs, tracing, correlation, and diagnostic context      |
| AI Validation Tests    | Pytest / Custom Checks | Planned                           | Validate RCA and generated test scenarios                        |
| CI/CD Validation       | GitHub Actions         | Planned                           | Execute automated regression in CI                               |

The project deliberately establishes domain and API correctness before introducing more expensive integration, persistence, reliability, and AI-driven testing.

---

# Payment Transaction Lifecycle

The central functional flow under test is the payment transaction lifecycle:

```text
┌───────────────┐
│  AUTHORIZED   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   CAPTURED    │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   SETTLED     │
└───────┬───────┘
        │
        ├──────────────────┐
        │                  │
        ▼                  ▼
┌───────────────────┐  ┌───────────────┐
│ PARTIALLY_REFUNDED│  │   REFUNDED    │
└─────────┬─────────┘  └───────────────┘
          │
          │ Remaining amount refunded
          ▼
   ┌───────────────┐
   │   REFUNDED    │
   └───────────────┘
```

The lifecycle is enforced by the transaction state machine.

The Web Dashboard provides a visual representation of this lifecycle so that a tester can inspect the progression of an individual transaction.

The lifecycle model includes:

* Authorization
* Capture
* Settlement
* Partial refund
* Full refund
* Current lifecycle state
* Lifecycle event timestamps
* Amounts associated with each stage
* Transaction history

Automated tests validate lifecycle behavior at the state-machine, service, API, and UI levels where appropriate.

---

# Valid State Transitions

The current valid lifecycle transitions are:

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

These transitions are validated independently by the state-machine tests.

---

# Invalid State Transitions

The state machine must reject invalid operations.

Examples include:

```text
AUTHORIZED
    ├──X SETTLED
    └──X REFUNDED

CAPTURED
    └──X REFUNDED

SETTLED
    └──X CAPTURED

REFUNDED
    ├──X CAPTURED
    └──X REFUNDED

DECLINED
    └──X CAPTURED
```

The objective is to ensure that lifecycle rules are enforced centrally rather than duplicated across individual API endpoints.

---

# Card Issuance Testing

Card issuance is validated through API-level tests.

| Category   | Coverage                                  |
| ---------- | ----------------------------------------- |
| Positive   | Valid card successfully created           |
| Negative   | Missing required fields rejected          |
| Negative   | Invalid card network rejected             |
| Boundary   | Zero initial balance rejected             |
| Boundary   | Negative initial balance rejected         |
| Integrity  | Multiple cards receive unique identifiers |
| Validation | Cardholder information validation         |
| Validation | Expiry date validation                    |
| Security   | Card number is masked in API response     |

A successful card issuance must produce:

* A unique `card_id`
* The requested cardholder
* The requested network
* The requested initial balance
* An `ACTIVE` status
* A masked card number

The tests must never depend on real payment-card information.

---

# Authorization Testing

Authorization is validated through API tests.

| Category      | Coverage                                                           |
| ------------- | ------------------------------------------------------------------ |
| Positive      | Transaction authorized with sufficient balance                     |
| Negative      | Insufficient funds produce a declined transaction                  |
| Negative      | Card not found                                                     |
| Negative      | Inactive card                                                      |
| Boundary      | Authorization for exact available balance                          |
| Validation    | Missing merchant ID                                                |
| Boundary      | Zero transaction amount                                            |
| Validation    | Invalid transaction amount                                         |
| Integrity     | Authorized amount is recorded correctly                            |
| Lifecycle     | Authorization creates the initial transaction state                |
| Idempotency   | Same key replays the original result                               |
| Idempotency   | Same key does not double-charge                                    |
| Idempotency   | Same key with different request is rejected                        |
| Integrity     | Different keys create separate operations                          |
| Compatibility | Requests without an idempotency key retain non-idempotent behavior |

Expected behaviors include:

```text
Sufficient balance
        ↓
AUTHORIZED

Insufficient balance
        ↓
DECLINED
```

The authorization tests also verify the idempotency contract.

---

# Idempotency Testing

Idempotency is currently implemented for authorization operations.

The expected behavior is:

```text
First Request
     │
     ▼
Operation Executed
     │
     ▼
Result Stored
     │
     ▼
Second Identical Request
     │
     ▼
Original Result Replayed
     │
     ▼
No Duplicate Financial Operation
```

The current API tests verify:

* Repeating the same authorization request with the same idempotency key returns the same response.
* Repeating the same request does not deduct the card balance twice.
* Reusing an idempotency key for a different request returns HTTP `409`.
* Different idempotency keys create separate transactions.
* Requests without an idempotency key preserve existing non-idempotent behavior.

Future reliability testing should extend idempotency validation to:

* Capture
* Settlement
* Refund
* Concurrent duplicate requests
* Retry behavior
* Failure followed by retry

---

# Capture Testing

| Category    | Coverage                                     |
| ----------- | -------------------------------------------- |
| Positive    | Authorized transaction successfully captured |
| Positive    | Partial capture                              |
| Negative    | Capture exceeds authorized amount            |
| Negative    | Transaction not found                        |
| Negative    | Capture attempted from invalid state         |
| Negative    | Already captured transaction                 |
| Boundary    | Zero capture amount                          |
| Reliability | Declined transaction cannot be captured      |
| Lifecycle   | Capture updates transaction history          |
| Integrity   | Captured amount is preserved correctly       |
| Idempotency | Planned extension                            |

---

# Settlement Testing

| Category    | Coverage                                  |
| ----------- | ----------------------------------------- |
| Positive    | Captured transaction successfully settled |
| Negative    | Transaction not found                     |
| Negative    | Settlement attempted before capture       |
| Negative    | Already settled transaction               |
| Reliability | Simulated timeout                         |
| Reliability | Simulated network error                   |
| Lifecycle   | Settlement updates transaction history    |
| Integrity   | Settled amount is preserved correctly     |
| Idempotency | Planned extension                         |

---

# Refund Testing

| Category  | Coverage                                      |
| --------- | --------------------------------------------- |
| Positive  | Full refund                                   |
| Positive  | Partial refund                                |
| Positive  | Partial refund followed by remaining refund   |
| Positive  | Multiple partial refunds                      |
| Negative  | Refund exceeds remaining refundable amount    |
| Negative  | Refund attempted before settlement            |
| Negative  | Already fully refunded transaction            |
| Negative  | Transaction not found                         |
| Boundary  | Zero refund amount                            |
| Boundary  | Negative refund amount                        |
| Lifecycle | Refund events are recorded                    |
| Integrity | Refunded amount is accumulated correctly      |
| Lifecycle | Fully refunded transaction reaches `REFUNDED` |

---

# State Machine Testing

The state machine is tested independently of the HTTP layer.

The state-machine tests verify:

* Valid transaction transitions are accepted.
* Invalid transaction transitions are rejected.
* Terminal states cannot transition into unrelated states.
* Partial refunds can occur repeatedly while refundable balance remains.
* A fully refunded transaction transitions to `REFUNDED`.
* Declined transactions cannot proceed through the normal capture lifecycle.

This isolation ensures that lifecycle correctness does not depend on FastAPI, HTTP clients, or the storage implementation.

---

# Payment Service Testing

The `PaymentService` is tested independently from the API layer.

The service-level suite covers:

## Capture

* Successful capture
* Partial capture
* Capture amount exceeding authorization
* Nonexistent transaction
* Invalid transaction state
* Already captured transaction

## Settlement

* Successful settlement
* Nonexistent transaction
* Invalid transaction state
* Already settled transaction

## Refund

* Full refund
* Partial refund
* Partial refund followed by remaining refund
* Multiple refund operations
* Refund exceeding remaining balance
* Nonexistent transaction
* Invalid transaction state
* Already fully refunded transaction

This layer verifies business rules without requiring the HTTP application to be exercised through browser interactions.

---

# API Testing

API tests validate externally observable behavior of the simulated payment gateway.

The API suite covers:

* Card issuance
* Authorization
* Capture
* Settlement
* Refunds
* Request validation
* Missing resources
* Invalid lifecycle states
* Boundary values
* Partial operations
* Idempotency
* Audit-event generation
* Simulated technical failures

Expected HTTP categories include:

```text
404  Resource not found

400  Invalid amount or business constraint

409  Invalid transaction lifecycle state
     or idempotency conflict

422  Request validation failure

502  Simulated network error

504  Simulated timeout
```

The API layer is responsible for translating domain exceptions into HTTP responses.

Payment-domain tests do not depend on HTTP semantics.

---

# Audit Testing

Audit behavior is part of the implemented backend test strategy.

The audit tests verify that payment operations produce appropriate audit events.

Current coverage includes:

* Authorization creates an audit event.
* Declined authorization creates an audit event.
* Capture creates an audit event.
* Audit events can be persisted and retrieved.
* Audit events can be queried by transaction.
* Audit events can be queried by correlation identifier.
* Failed operations can be represented.
* Audit events do not require sensitive payloads.
* Raw card numbers must not appear in audit data.

Audit testing is particularly important for a payment-system simulation because lifecycle correctness alone does not provide sufficient operational traceability.

---

# Domain Exception Testing

Payment-domain failures are represented using typed exceptions rather than HTTP-specific exceptions.

The current exception hierarchy includes:

```text
PaymentError
│
├── TransactionNotFoundError
├── InvalidTransactionStateError
├── CaptureAmountExceededError
└── RefundAmountExceededError
```

The service layer raises domain-level exceptions.

The API layer translates those exceptions into HTTP responses.

This separation is tested through both service-level and API-level tests.

---

# End-to-End Payment Lifecycle Testing

The E2E strategy validates behavior across system boundaries.

The current E2E architecture uses:

* Pytest
* Playwright
* HTTP client setup for deterministic backend test data
* Page Object Model
* Local Vite frontend
* Local FastAPI backend

The current E2E test flow is:

```text
API
 │
 ├── Create Test Card
 │
 └── Create Authorized Transaction
          │
          ▼
      Playwright
          │
          ▼
    Open Dashboard
          │
          ▼
    Open Transactions
          │
          ▼
   Verify Transaction
          │
          ▼
 Open Lifecycle Dialog
```

The E2E fixtures intentionally create backend state through the API instead of attempting to manufacture complex payment state exclusively through UI interactions.

This provides:

* Deterministic setup
* Faster test execution
* Lower UI coupling
* Better separation between API and UI responsibilities

A future full lifecycle E2E scenario should eventually cover:

```text
Card Issuance
      │
      ▼
Authorization
      │
      ▼
Capture
      │
      ▼
Settlement
      │
      ▼
Refund
```

Such a test should verify:

* Correct transaction state after every operation
* Correct authorized amount
* Correct captured amount
* Correct settled amount
* Correct refunded amount
* Correct card balance
* Correct transaction history
* Correct lifecycle timestamps
* No invalid intermediate state
* No duplicate financial operation

---

# Dashboard Testing Strategy

The Web Dashboard provides a visual interface for:

* Monitoring cards
* Viewing transactions
* Inspecting transaction status
* Viewing merchant information
* Viewing transaction amounts
* Opening transaction lifecycle details
* Viewing lifecycle stages
* Viewing lifecycle event timestamps
* Refreshing transaction data

The dashboard is now an automated Playwright test target.

---

# Current Playwright E2E Coverage

The current E2E suite contains four tests.

## Dashboard Smoke Test

Validates that the dashboard loads successfully.

## Transactions Page Load

Validates:

* Transactions navigation is available.
* Transactions page opens.
* Transactions heading is displayed.
* Transactions description is displayed.
* Transactions list panel is displayed.

## Transactions Empty State

Validates:

* Transactions page loads.
* Empty transaction state is displayed when no transactions exist.

## Authorized Transaction Visibility

The test creates a card and transaction through the backend API and then validates the transaction through the browser.

It verifies:

* Transaction appears in the transaction table.
* Merchant identifier is displayed.
* `AUTHORIZED` status is displayed.

## Transaction Lifecycle Dialog

The test creates an authorized transaction through the API and then validates that:

* The transaction appears in the UI.
* Lifecycle action is available.
* Lifecycle dialog opens.
* Lifecycle dialog is visible.
* Lifecycle dialog can be closed.

---

# Page Object Model

The E2E suite uses a Page Object Model.

The Transactions Page Object encapsulates:

* Navigation
* Page heading
* Page description
* Transaction list
* Transaction table
* Empty state
* Refresh control
* Transaction lookup
* Transaction status assertions
* Transaction amount assertions
* Lifecycle dialog
* Lifecycle dialog controls

The Page Object intentionally prefers:

* Accessible roles
* Accessible names
* Application semantics
* Stable CSS classes where necessary

The Page Object avoids unnecessary dependence on deeply nested DOM structure.

Transaction UUIDs are shortened by the frontend, so the Page Object converts the backend transaction identifier into the UI representation before locating the transaction row.

---

# E2E Test Data Strategy

E2E tests use dedicated API fixtures.

The current E2E fixtures provide:

```text
frontend_url
backend_url
dashboard_page
issued_e2e_card
authorized_transaction
```

The `issued_e2e_card` fixture creates a fresh active VISA test card.

The `authorized_transaction` fixture creates an authorized transaction against that card.

The test data is:

* Synthetic
* Deterministic
* Non-production
* Disposable
* Created through the local API

No real payment credentials are used.

---

# E2E Environment

The E2E suite currently expects the local frontend and backend to already be running.

Frontend:

```text
http://localhost:5173
```

Backend:

```text
http://localhost:8000
```

The backend can be started with:

```powershell
uvicorn app.main:app --reload --reload-dir app --port 8000
```

The frontend should be started separately using the project's configured Vite development command.

Pytest does not currently start the frontend automatically.

This deliberate separation keeps the E2E fixture responsible for test setup rather than process management.

---

# E2E Regression Commands

Run only the Transactions E2E tests:

```powershell
pytest tests\e2e\test_transactions.py -v
```

Run the complete E2E suite:

```powershell
pytest tests\e2e -v
```

Expected current E2E result:

```text
4 passed
```

Run the complete project regression suite:

```powershell
pytest -v
```

Expected current result:

```text
96 passed
0 failed
```

---

# UI Test Principles

UI tests should validate user-visible behavior rather than reproduce the entire API suite.

For example, API tests should verify:

```text
POST /api/v1/transactions/authorize
→
Correct HTTP response
→
Correct transaction state
```

A UI test should instead verify:

```text
Transaction created
→
Open Transactions
→
Transaction visible
→
Correct merchant
→
Correct status
→
Lifecycle can be opened
```

This separation prevents the E2E suite from becoming slow, brittle, and redundant.

---

# Manual Dashboard Validation

Manual validation remains useful for behaviors that have not yet been automated.

The following should be manually validated when relevant:

## Transactions

* Transaction list loads correctly.
* Transaction status matches backend state.
* Merchant information is displayed correctly.
* Transaction amount is displayed correctly.
* Transaction timestamps are displayed correctly.
* Refresh operation updates transaction data.

## Lifecycle View

For a fully completed transaction:

```text
AUTHORIZED  ✓
CAPTURED    ✓
SETTLED     ✓
REFUNDED    ✓
```

The UI should correctly distinguish:

* Completed stages
* Current stage
* Upcoming stages
* Failed stages

For partial refunds:

```text
AUTHORIZED          ✓
CAPTURED            ✓
SETTLED             ✓
PARTIALLY_REFUNDED  ●
```

The dashboard must not incorrectly display a partially refunded transaction as fully refunded.

For declined transactions, authorization should be represented as failed and downstream lifecycle stages should not appear as completed.

---

# Failure Simulation

The Mock Payment Gateway supports deterministic technical failure simulation through the `X-Simulate-Failure` request header.

Supported scenarios include:

```text
TIMEOUT
NETWORK_ERROR
INVALID_RESPONSE
```

Expected behavior:

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

These deterministic failure modes provide inputs for:

* API testing
* Reliability testing
* Failure recovery testing
* Future AI root cause analysis

---

# Current Regression Strategy

The full test suite should be executed after changes affecting:

* Payment-domain behavior
* State transitions
* Payment service logic
* Repository behavior
* API endpoints
* Request/response models
* Idempotency behavior
* Audit behavior
* Transaction lifecycle behavior
* Dashboard transaction behavior
* E2E fixtures
* Page Objects

## Complete Suite

```powershell
pytest -v
```

## API Tests

```powershell
pytest tests\api -v
```

## Service Tests

```powershell
pytest tests\unit\test_payment_service.py -v
```

## State Machine Tests

```powershell
pytest tests\unit\test_state_machine.py -v
```

## E2E Tests

```powershell
pytest tests\e2e -v
```

## Transactions E2E Tests

```powershell
pytest tests\e2e\test_transactions.py -v
```

Current verified regression baseline:

```text
96 tests collected
96 passed
0 failed
```

The baseline should remain green as new functionality is introduced.

---

# Test Environment Strategy

## Current Development Environment

The current automated backend and E2E tests run locally using:

* Python 3.11
* FastAPI
* Pytest
* Playwright
* HTTP client support
* In-memory application storage
* Local Vite frontend

The current backend test suite does not require:

* PostgreSQL
* Docker
* ChromaDB
* Ollama

Playwright browser automation is required for the E2E suite.

---

# Planned Test Environments

| Environment               | Purpose                             | Status      |
| ------------------------- | ----------------------------------- | ----------- |
| Local Backend             | Rapid backend regression testing    | Implemented |
| Local Dashboard + Backend | E2E browser validation              | Implemented |
| Local + PostgreSQL        | Persistence and consistency testing | Planned     |
| Docker Compose            | Integrated multi-service testing    | Planned     |
| CI                        | Automated regression testing        | Planned     |
| AI Validation Environment | RCA and test-generation evaluation  | Planned     |

---

# Reliability Testing

Payment systems require more than functional correctness.

The next reliability-focused testing phase will cover:

* Idempotency
* Concurrent requests
* Duplicate operations
* Transaction consistency
* Retry behavior
* Failure recovery
* Persistence failures
* Monetary precision
* Audit consistency

Idempotency is already implemented for authorization and should be expanded to additional payment operations.

---

# Concurrency Testing

The system should eventually be tested for race conditions involving simultaneous operations on the same transaction.

Example:

```text
Request A ─────────────► Capture
                         │
Request B ─────────────► Capture
```

The expected behavior is that only one capture operation succeeds.

Similar scenarios should be tested for:

* Concurrent refunds
* Concurrent settlement
* Concurrent authorization attempts
* Simultaneous updates to the same transaction
* Duplicate API requests

The database layer will become particularly important once PostgreSQL persistence is introduced.

---

# Persistence Testing

After PostgreSQL is introduced, tests should verify:

* Transaction commit behavior
* Rollback behavior
* Constraint enforcement
* Data consistency
* Transaction isolation
* Recovery after database failures
* Durable transaction history
* Persistent card balances
* Persistent transaction lifecycle state
* Persistent audit events

The persistence test flow should verify:

```text
API Request
    │
    ▼
Service Operation
    │
    ▼
Database Commit
    │
    ▼
Application Restart
    │
    ▼
Transaction Still Available
```

This is one of the primary differences between the current in-memory implementation and the planned persistent architecture.

---

# Monetary Precision Testing

Payment amounts must be represented and tested with financial precision.

Tests should cover:

* Currency precision
* Decimal boundaries
* Rounding rules
* Minimum transaction amounts
* Maximum transaction amounts
* Partial captures
* Partial refunds
* Multiple partial refunds
* Remaining refundable balance
* Card balance updates

Financial calculations should avoid floating-point arithmetic where exact monetary representation is required.

---

# Transaction Consistency Testing

End-to-end payment testing must verify that related financial values remain consistent.

For a transaction:

```text
authorized_amount
captured_amount
settled_amount
refunded_amount
```

The test suite should verify invariants such as:

```text
captured_amount <= authorized_amount

settled_amount <= captured_amount

refunded_amount <= settled_amount
```

For partial refunds:

```text
refunded_amount < settled_amount
```

For full refunds:

```text
refunded_amount == settled_amount
```

The exact business rules remain defined by the payment-domain implementation.

---

# Transaction History Testing

Transaction history is a critical part of the payment lifecycle and future auditability.

Tests should verify that lifecycle operations produce corresponding events.

Example:

```text
Authorization
      │
      ▼
Transaction History
      │
      ├── AUTHORIZED
      │
      ▼
Capture
      │
      ├── CAPTURED
      │
      ▼
Settlement
      │
      ├── SETTLED
      │
      ▼
Refund
      │
      └── REFUNDED
```

Future persistence testing should verify that these events survive application restarts and remain associated with the correct transaction.

---

# Security Testing Considerations

As the project evolves, security testing should cover:

* Input validation
* Authentication
* Authorization
* Rate limiting
* Sensitive-data exposure
* Logging of payment information
* Secrets management
* API abuse scenarios
* Injection attacks
* Insecure direct object references
* Error-message information leakage
* Idempotency abuse
* Audit-log integrity

The current project is a simulated payment gateway and is not a PCI-DSS-certified payment environment.

Security testing should therefore demonstrate secure engineering practices rather than claim regulatory certification.

---

# Observability Testing

Observability will become increasingly important as the project moves toward reliability testing and AI-assisted RCA.

Future observability testing should validate:

* Structured application logs
* Correlation IDs
* Transaction identifiers
* Request identifiers
* Lifecycle event tracing
* Error logging
* API latency measurements
* Failure classification
* Trace propagation across services
* Audit-event correlation

A transaction should eventually be traceable across:

```text
API Request
    │
    ▼
Payment Service
    │
    ▼
Domain Operation
    │
    ▼
Repository
    │
    ▼
Database
```

This information will also provide useful context for the planned AI RCA pipeline.

---

# Performance Testing

Performance testing is not part of the current regression baseline.

Future performance testing should evaluate:

* Authorization throughput
* Capture throughput
* Settlement throughput
* Refund throughput
* Concurrent transaction processing
* API response latency
* Database latency
* Dashboard response time
* Failure-handling latency

Performance thresholds should be defined once the persistent architecture and deployment topology are established.

---

# AI-Augmentation Strategy

AI capabilities will be introduced after the deterministic payment-domain and reliability foundation is sufficiently mature.

The AI layer is intended to assist testers and developers rather than replace deterministic automated validation.

AI output must never become the source of truth for payment correctness.

---

# Root Cause Analysis

The planned RCA pipeline is:

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
Developer / QA Review
```

The system should retrieve similar historical failures before generating an explanation.

The AI should provide evidence-based assistance and should not silently determine whether a payment-system failure is acceptable.

---

# AI Test Case Generation

The planned test-generation workflow is:

```text
OpenAPI Specification
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
Validated Automated Test
```

Generated test cases should initially remain suggestions.

They should not automatically become part of the trusted regression suite without validation.

---

# AI Output Validation Criteria

AI output requires independent validation.

## RCA Validation

Future RCA evaluation should measure:

* Correct failure classification
* Correct affected component
* Consistency with the actual stack trace
* Relevance of retrieved historical failures
* Absence of unsupported conclusions
* Actionability of the suggested root cause

Initial evaluation target:

> Correctly classify at least 8 out of 10 known, deterministically injected failure scenarios.

This target should be reviewed once a representative evaluation dataset exists.

## Test Case Generation Validation

Generated test scenarios should be evaluated for:

* API relevance
* Correct endpoint understanding
* Boundary-value coverage
* Negative-case coverage
* Non-duplication
* Executability
* Payment-domain correctness

Initial evaluation target:

> Generate at least 5 relevant, non-duplicate edge-case scenarios per selected endpoint.

These targets are evaluation goals rather than current implementation guarantees.

---

# Failure Handling and Future RCA Flow

The planned CI/RCA workflow is:

```text
Test Execution
    │
    ▼
Failure Detected
    │
    ▼
Failure Logs + Stack Trace Captured
    │
    ▼
RCA Pipeline Triggered
    │
    ▼
Similar Historical Failures Retrieved
    │
    ▼
LLM Generates RCA Summary
    │
    ▼
RCA Report Produced
    │
    ▼
Developer / QA Review
```

The AI should assist investigation rather than silently determine whether a payment-system failure is acceptable.

---

# Regression Strategy

The regression strategy will expand as additional system layers are introduced.

## Current

Changes affecting the following components should trigger the appropriate regression suite:

* Payment domain
* State machine
* Payment service
* Repository
* API endpoints
* Request/response models
* Idempotency behavior
* Audit behavior
* Transaction lifecycle behavior
* Dashboard transaction behavior
* E2E Page Objects
* E2E fixtures

The primary command is:

```powershell
pytest -v
```

For UI-specific changes:

```powershell
pytest tests\e2e -v
```

For backend-only changes:

```powershell
pytest tests\api tests\unit -v
```

---

# Future CI Regression Flow

Once CI infrastructure is implemented:

```text
Pull Request
    │
    ▼
Domain / Unit Tests
    │
    ▼
Service Tests
    │
    ▼
API Tests
    │
    ▼
Integration Tests
    │
    ▼
Playwright E2E Tests
    │
    ▼
Reliability Tests
    │
    ▼
AI Validation
```

Long-running reliability and AI evaluation suites may later run separately from the fast pull-request regression suite.

---

# Test Data Strategy

The test environment should use controlled payment data.

Test data must remain:

* Deterministic
* Reproducible
* Non-production
* Synthetic
* Free of real cardholder information
* Suitable for automated execution

No real:

* PAN
* CVV
* Cardholder authentication data
* Production payment credentials

should be used.

E2E fixtures should create disposable backend data specifically for each test scenario.

Future persistent test environments should use isolated databases and disposable test data.

---

# Test Isolation

Tests should avoid depending on state created by unrelated tests.

Backend tests should use isolated fixtures and reset application state where necessary.

E2E tests should create their required backend state through dedicated fixtures.

The E2E suite should not rely on:

* Transactions created by previous tests
* Cards created by previous tests
* Manual browser state
* Production data
* A specific execution order

Each test should establish the minimum state required to validate its behavior.

---

# Test Reporting

Future test execution should produce structured results suitable for:

* Local development
* Pull-request validation
* CI/CD reporting
* Failure analysis
* AI RCA ingestion
* Historical trend analysis

Potential reporting outputs include:

```text
Test Results
    │
    ├── Pass / Fail Summary
    ├── Failure Details
    ├── Stack Traces
    ├── Execution Time
    ├── Environment Metadata
    ├── Browser Metadata
    └── Transaction / Correlation IDs
```

Playwright failures should eventually retain useful browser diagnostics such as:

* Screenshot
* Trace
* Console output
* Network information
* Failure location

These artifacts will provide valuable context for future automated RCA.

---

# Tools Summary

| Tool                             | Purpose                                                   | Status      |
| -------------------------------- | --------------------------------------------------------- | ----------- |
| Pytest                           | Unit, service, state-machine, API, and E2E test execution | Implemented |
| HTTP Client / FastAPI TestClient | API endpoint testing and E2E data setup                   | Implemented |
| Playwright                       | Browser automation for dashboard testing                  | Implemented |
| Page Object Model                | Maintainable E2E UI abstraction                           | Implemented |
| In-Memory Storage                | Deterministic local test persistence                      | Implemented |
| PostgreSQL                       | Persistent transaction and test data                      | Planned     |
| SQLAlchemy                       | Database access layer                                     | Planned     |
| LangChain                        | LLM orchestration                                         | Planned     |
| LangGraph                        | AI workflow orchestration                                 | Planned     |
| ChromaDB                         | Historical failure retrieval                              | Planned     |
| Ollama                           | Local LLM inference                                       | Planned     |
| Docker                           | Integrated test environment                               | Planned     |
| GitHub Actions                   | CI/CD execution                                           | Planned     |
| OpenTelemetry                    | Observability and tracing                                 | Planned     |

---

# Current Test Status

## Completed

* [x] State-machine testing
* [x] Payment-service testing
* [x] API testing
* [x] Positive payment scenarios
* [x] Negative payment scenarios
* [x] Boundary-value testing
* [x] Invalid state-transition testing
* [x] Partial refund testing
* [x] Full refund testing
* [x] Simulated timeout testing
* [x] Simulated network-error testing
* [x] Idempotency testing for authorization
* [x] Audit-event testing
* [x] Transaction lifecycle API functionality
* [x] Web Dashboard transaction monitoring
* [x] Dashboard transaction lifecycle visualization
* [x] Playwright dashboard smoke testing
* [x] Playwright Transactions page testing
* [x] Playwright empty-state testing
* [x] Playwright authorized-transaction visibility
* [x] Playwright lifecycle dialog testing
* [x] E2E API fixture-based test data setup
* [x] Page Object Model for Transactions
* [x] Full regression suite passing

## Current Regression Baseline

```text
96 tests collected
96 passed
0 failed
```

## Current E2E Baseline

```text
4 tests collected
4 passed
0 failed
```

---

# Planned

* [ ] Complete automated end-to-end payment lifecycle
* [ ] Capture idempotency testing
* [ ] Settlement idempotency testing
* [ ] Refund idempotency testing
* [ ] Concurrent transaction testing
* [ ] PostgreSQL integration testing
* [ ] Transaction rollback testing
* [ ] Persistence failure testing
* [ ] Monetary precision expansion
* [ ] Transaction consistency testing
* [ ] Security testing
* [ ] Performance testing
* [ ] Observability validation
* [ ] Playwright negative UI scenarios
* [ ] Playwright backend-unavailable scenarios
* [ ] Playwright API timeout scenarios
* [ ] Playwright lifecycle-state visualization coverage
* [ ] CI/CD integration
* [ ] AI RCA validation
* [ ] AI test-generation validation

---

# Testing Principles

PayGuard AI follows several principles throughout its testing strategy.

## Test Behavior, Not Implementation

Tests should primarily validate observable behavior and business rules rather than internal implementation details.

## Keep Domain Tests Independent

Payment lifecycle rules should be testable without starting the HTTP server.

## Prefer Deterministic Failures

Failure simulation should produce repeatable scenarios so that reliability and AI RCA testing remain reproducible.

## Validate Financial Invariants

Payment amounts and balances must remain internally consistent throughout the lifecycle.

## Treat the Complete Lifecycle as a Workflow

Individual endpoint correctness is necessary but insufficient.

The platform must eventually validate authorization, capture, settlement, and refund as one coherent payment journey.

## Keep UI Tests Focused

Playwright tests should validate what a user can see and do.

They should not simply reproduce every API test through a browser.

## Use APIs for Deterministic E2E Setup

Complex backend state should be created through controlled API fixtures when the purpose of the test is to validate UI behavior.

This keeps browser tests focused on user-visible behavior.

## AI Is an Assistant, Not an Oracle

AI-generated root causes and test cases must be validated against deterministic system behavior.

## Preserve Regression Stability

New functionality should extend the test suite without weakening the existing regression baseline.

## Protect Payment Data

Tests must use synthetic data and must never require real payment credentials or cardholder information.

---

# Testing Roadmap

The testing strategy will evolve alongside the architecture.

```text
Phase 1
Core Payment Tests
        │
        ▼
Phase 2
Domain + Service + API Tests
        │
        ▼
Phase 3
Idempotency + Audit + Lifecycle Tests
        │
        ▼
Phase 4
Playwright Dashboard + E2E Tests
        │
        ▼
Phase 5
Reliability + Concurrency Tests
        │
        ▼
Phase 6
PostgreSQL + Integration Tests
        │
        ▼
Phase 7
Observability + CI/CD
        │
        ▼
Phase 8
AI RCA + AI Test Generation
```

The current foundation consists of:

* Domain and state-machine testing
* Payment-service testing
* API testing
* Idempotency validation
* Audit validation
* A working dashboard
* Playwright browser automation
* API-backed E2E test fixtures
* Transaction lifecycle UI validation

The immediate testing priorities should be:

1. Expand E2E coverage across the complete payment lifecycle.
2. Extend idempotency testing beyond authorization.
3. Add reliability and concurrency scenarios.
4. Introduce persistent-storage integration tests.
5. Improve Playwright failure diagnostics and negative-path coverage.
6. Establish CI regression execution.
7. Introduce AI-assisted RCA only after deterministic test and observability foundations are sufficiently mature.

The AI layer should remain downstream of the deterministic testing foundation. A payment-testing platform that asks an LLM whether a broken payment is "probably fine" would be a spectacularly bad idea.

---

# Definition of Done for Test Coverage

A feature should not be considered adequately tested merely because its happy path works.

For payment functionality, the minimum expected coverage should consider:

```text
                ┌───────────────────┐
                │  Happy Path       │
                └─────────┬─────────┘
                          │
                ┌─────────▼─────────┐
                │ Negative Cases    │
                └─────────┬─────────┘
                          │
                ┌─────────▼─────────┐
                │ Boundary Cases    │
                └─────────┬─────────┘
                          │
                ┌─────────▼─────────┐
                │ State Transitions │
                └─────────┬─────────┘
                          │
                ┌─────────▼─────────┐
                │ Financial Invariants│
                └─────────┬─────────┘
                          │
                ┌─────────▼─────────┐
                │ Idempotency       │
                └─────────┬─────────┘
                          │
                ┌─────────▼─────────┐
                │ Auditability      │
                └─────────┬─────────┘
                          │
                ┌─────────▼─────────┐
                │ E2E Visibility    │
                └───────────────────┘
```

The exact test layers required depend on the change.

For example:

| Change                   | Minimum Regression                          |
| ------------------------ | ------------------------------------------- |
| State transition         | State machine + service + affected API      |
| Payment service          | Unit/service + affected API                 |
| API contract             | API + affected E2E                          |
| Idempotency              | API + reliability tests                     |
| Dashboard transaction UI | Playwright E2E                              |
| Lifecycle UI             | Playwright E2E + API                        |
| Persistence              | Integration + API + E2E                     |
| Observability            | Unit/integration + diagnostic validation    |
| AI RCA                   | Deterministic failure suite + AI evaluation |

---

# Final Regression Standard

The project should maintain the following standard before committing changes that affect tested functionality:

```text
pytest -v
```

Expected:

```text
96 passed
0 failed
```

For E2E-affecting changes:

```powershell
pytest tests\e2e -v
```

Expected:

```text
4 passed
```

The exact test count will increase as coverage expands. The invariant is not the number `96`; the invariant is that the complete applicable regression suite remains green and that new behavior is accompanied by appropriate automated coverage.

---

# Conclusion

PayGuard AI's testing strategy is built around deterministic validation of payment-domain behavior first, followed by increasingly broader system-level validation.

The current implementation already provides:

* State-machine tests
* Payment-service tests
* API tests
* Idempotency tests
* Audit tests
* Playwright dashboard tests
* API-backed E2E fixtures
* Transaction visibility validation
* Transaction lifecycle UI validation
* A green full regression baseline

The next stage should focus on increasing confidence across system boundaries rather than simply increasing the number of tests.

The priority order is:

```text
Deterministic Domain Correctness
        ↓
Service Correctness
        ↓
API Correctness
        ↓
Idempotency + Auditability
        ↓
UI / E2E Coverage
        ↓
Reliability + Concurrency
        ↓
Persistence
        ↓
Observability
        ↓
CI/CD
        ↓
AI-Assisted Testing
```


