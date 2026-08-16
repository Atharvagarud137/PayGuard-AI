# TEST_STRATEGY.md — PayGuard AI

## Purpose

This document defines the testing strategy for PayGuard AI.

PayGuard AI is an AI-augmented payment-system testing platform built around a simulated payment gateway. The testing strategy focuses on validating payment-domain correctness, transaction lifecycle behavior, API contracts, failure handling, boundary conditions, and the ability to observe a transaction through its complete lifecycle.

The current implementation provides a functional payment gateway and a Web Dashboard capable of displaying transaction lifecycle state. The next testing phases will extend this foundation with reliability testing, persistent storage validation, UI automation, observability, AI-assisted root cause analysis, and CI/CD validation.

The testing strategy follows a layered approach:

```text
Domain
   ↓
Service
   ↓
API
   ↓
Integration
   ↓
UI / End-to-End
   ↓
Reliability
   ↓
AI Validation
   ↓
CI/CD
````

The objective is not simply to maximize test count. The objective is to establish confidence that payment transactions behave correctly from authorization through capture, settlement, and refund while failures and invalid operations remain deterministic and diagnosable.

---

## Current Test Architecture

The current automated backend test suite is organized into three primary layers:

```text
    ┌──────────────────────┐
    │      API Tests       │
    │       36 tests       │
    └──────────┬───────────┘
               │
    ┌──────────▼───────────┐
    │  Payment Service     │
    │       14 tests       │
    └──────────┬───────────┘
               │
    ┌──────────▼───────────┐
    │   State Machine      │
    │       14 tests       │
    └──────────────────────┘
```

### Current Test Baseline

| Test Layer      | Tool       |  Tests | Status                   |
| --------------- | ---------- | -----: | ------------------------ |
| State Machine   | Pytest     |     14 | Passing                  |
| Payment Service | Pytest     |     14 | Passing                  |
| API             | Pytest     |     36 | Passing                  |
| **Total**       | **Pytest** | **64** | **64 Passed / 0 Failed** |

The current regression baseline contains 64 automated tests with zero failures.

The Web Dashboard is currently implemented as a functional application, but automated browser testing has not yet been introduced.

---

## Test Pyramid

The long-term test strategy follows a layered test pyramid.

| Layer               | Tool                   | Current Status | Purpose                                                                 |
| ------------------- | ---------------------- | -------------- | ----------------------------------------------------------------------- |
| Domain / Unit Tests | Pytest                 | Implemented    | Validate state transitions and payment-domain rules                     |
| Service Tests       | Pytest                 | Implemented    | Validate payment business logic independently of HTTP                   |
| API Tests           | Pytest                 | Implemented    | Validate externally observable gateway behavior                         |
| Integration Tests   | Pytest                 | Planned        | Validate interaction between API, services, repository, and persistence |
| UI Tests            | Selenium               | Planned        | Validate dashboard behavior and transaction lifecycle visibility        |
| End-to-End Tests    | Selenium + API         | Planned        | Validate complete payment scenarios across system boundaries            |
| Reliability Tests   | Pytest                 | Planned        | Validate idempotency, concurrency, retries, and failure recovery        |
| Persistence Tests   | Pytest + PostgreSQL    | Planned        | Validate transactional consistency and durable state                    |
| AI Validation Tests | Pytest / Custom Checks | Planned        | Validate RCA output and generated test scenarios                        |

The project deliberately establishes domain and API correctness before introducing more expensive UI, integration, and AI-driven testing.

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

The dashboard lifecycle view displays:

* Authorization
* Capture
* Settlement
* Partial refund
* Full refund
* Current lifecycle state
* Lifecycle event timestamps
* Amounts associated with each stage
* Transaction history

The automated test strategy will eventually validate both the underlying lifecycle behavior and its UI representation.

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

These transitions are validated by the state-machine tests.

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

# Payment Flow Test Coverage

## Card Issuance

| Category   | Coverage                                  |
| ---------- | ----------------------------------------- |
| Positive   | Valid card successfully created           |
| Negative   | Missing required fields rejected          |
| Negative   | Invalid card network rejected             |
| Boundary   | Zero initial balance behavior             |
| Boundary   | Negative initial balance rejected         |
| Integrity  | Multiple cards receive unique identifiers |
| Validation | Expiry date validation                    |
| Validation | Cardholder information validation         |

---

## Authorization

| Category   | Coverage                                            |
| ---------- | --------------------------------------------------- |
| Positive   | Transaction authorized with sufficient balance      |
| Negative   | Insufficient funds produce a declined transaction   |
| Negative   | Card not found                                      |
| Negative   | Inactive card                                       |
| Boundary   | Authorization for exact available balance           |
| Validation | Missing merchant ID                                 |
| Boundary   | Zero transaction amount                             |
| Validation | Invalid transaction amount                          |
| Integrity  | Authorized amount is recorded correctly             |
| Lifecycle  | Authorization creates the initial transaction state |

---

## Capture

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

---

## Settlement

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

---

## Refund

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

The service-level test suite currently covers:

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

This layer verifies business rules without requiring the HTTP application to be running.

---

# API Testing

API tests validate externally observable behavior of the Mock Payment Gateway.

The current API suite contains 36 tests covering:

* Card issuance
* Authorization
* Capture
* Settlement
* Refunds
* Validation failures
* Missing resources
* Invalid lifecycle states
* Boundary values
* Partial operations
* Simulated technical failures

The API tests also verify appropriate HTTP behavior for domain failures.

Expected categories include:

```text
404  Resource not found

400  Invalid amount or business constraint

409  Invalid transaction lifecycle state

422  Request validation failure

502  Simulated network error

504  Simulated timeout
```

The API layer is responsible for translating domain exceptions into HTTP responses. Payment-domain tests do not depend on these HTTP semantics.

---

# End-to-End Payment Lifecycle Testing

The long-term goal of PayGuard AI is to validate the complete payment lifecycle as a single executable scenario.

A complete end-to-end scenario should eventually cover:

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

An end-to-end test should verify not only that each individual operation succeeds, but also that state and financial values remain consistent across the entire sequence.

For example:

```text
Initial Card Balance
        │
        ▼
Authorization
        │
        ├── Transaction = AUTHORIZED
        │
        ▼
Capture
        │
        ├── Transaction = CAPTURED
        │
        ▼
Settlement
        │
        ├── Transaction = SETTLED
        │
        ▼
Refund
        │
        └── Transaction = REFUNDED
```

The test should validate:

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

These tests are distinct from individual API tests because they validate the complete workflow rather than isolated endpoints.

---

# Dashboard Testing Strategy

The Web Dashboard currently provides a visual interface for:

* Monitoring cards
* Viewing transactions
* Inspecting transaction status
* Opening a transaction lifecycle view
* Viewing lifecycle stages
* Viewing transaction amounts
* Viewing transaction event timestamps
* Refreshing transaction data

The dashboard is intended to become the primary UI target for automated browser testing.

## Manual Dashboard Validation

Before Selenium automation is introduced, the following behaviors should be manually validated:

### Transactions

* Transaction list loads correctly
* Transaction status matches backend state
* Merchant information is displayed correctly
* Transaction amount is displayed correctly
* Transaction timestamps are displayed correctly
* Refresh operation updates the transaction list

### Lifecycle View

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

# Future UI Automation

Selenium automation will eventually validate the dashboard through real browser interactions.

Planned UI scenarios include:

### Dashboard Availability

* Application loads successfully
* Navigation elements are available
* Backend connectivity state is displayed correctly

### Transaction List

* Transactions are displayed
* Transaction IDs are visible
* Merchant IDs are visible
* Amounts are displayed correctly
* Status is displayed correctly
* Refresh functionality works

### Transaction Lifecycle

* Lifecycle can be opened from a transaction
* Authorization stage is displayed
* Capture stage is displayed
* Settlement stage is displayed
* Refund stage is displayed
* Completed stages are visually distinguished
* Current stages are visually distinguished
* Upcoming stages are visually distinguished
* Declined states are displayed correctly
* Lifecycle event timestamps are displayed
* Lifecycle amounts are displayed

### Negative UI Scenarios

* Backend unavailable
* Empty transaction list
* Transaction lookup failure
* Invalid transaction response
* API timeout
* API error response

UI tests should validate user-visible behavior rather than duplicate the entire API test suite.

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

This separation is tested indirectly through both service-level and API-level tests.

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

These failure modes provide deterministic inputs for:

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
* Transaction lifecycle behavior

## Run the complete suite

```powershell
pytest -v
```

## Run API tests only

```powershell
pytest tests/api -v
```

## Run service-layer tests

```powershell
pytest tests/unit/test_payment_service.py -v
```

## Run state-machine tests

```powershell
pytest tests/unit/test_state_machine.py -v
```

Current regression baseline:

```text
64 tests
64 passed
0 failed
```

The baseline should remain green as new functionality is introduced.

---

# Test Environment Strategy

## Current Development Environment

The current automated backend tests run locally using:

* Python 3.11
* FastAPI
* Pytest
* In-memory application storage

The current backend test suite does not require:

* PostgreSQL
* Docker
* ChromaDB
* Ollama
* Selenium

The Web Dashboard can be run separately against the local payment gateway for manual functional validation.

---

## Planned Test Environments

| Environment               | Purpose                               | Status      |
| ------------------------- | ------------------------------------- | ----------- |
| Local Backend             | Rapid backend regression testing      | Implemented |
| Local Dashboard + Backend | Manual end-to-end workflow validation | Implemented |
| Local + PostgreSQL        | Persistence and consistency testing   | Planned     |
| Docker Compose            | Integrated multi-service testing      | Planned     |
| CI                        | Automated regression testing          | Planned     |
| AI Validation Environment | RCA and test-generation evaluation    | Planned     |

---

# Future Reliability Testing

Payment systems require more than functional correctness.

The next reliability-focused testing phase will cover:

* Idempotency
* Concurrency
* Duplicate requests
* Transaction consistency
* Retry behavior
* Failure recovery
* Persistence failures
* Monetary precision

---

## Idempotency Testing

The system should verify that repeated requests using the same idempotency key do not create duplicate payment operations.

Future scenarios include:

```text
Duplicate Authorization
Duplicate Capture
Duplicate Settlement
Duplicate Refund
```

Expected behavior:

```text
First Request
    │
    ▼
Operation Executed
    │
    ▼
Result Stored

Second Identical Request
    │
    ▼
Previously Stored Result
    │
    ▼
No Duplicate Financial Operation
```

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

The database layer will become particularly important for these tests once PostgreSQL persistence is introduced.

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

The persistence tests should ensure that a transaction remains correct after:

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

Future tests should cover:

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

The exact business rules should remain defined by the payment-domain implementation.

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

# AI-Augmentation Strategy

AI capabilities will be introduced after the payment-domain and reliability foundation is sufficiently mature.

The AI layer is intended to assist testers and developers rather than replace deterministic automated validation.

---

## Root Cause Analysis

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

The AI should not be treated as the source of truth for payment correctness.

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

Initial target:

> Correctly classify at least 8 out of 10 known, deterministically injected failure scenarios.

This target should be reviewed once a representative evaluation dataset exists.

---

## Test Case Generation Validation

Generated test scenarios should be evaluated for:

* API relevance
* Correct endpoint understanding
* Boundary-value coverage
* Negative-case coverage
* Non-duplication
* Executability
* Payment-domain correctness

Initial target:

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

Changes affecting the following components should trigger the backend regression suite:

* Payment domain
* State machine
* Payment service
* Repository
* API endpoints
* Request/response models
* Transaction lifecycle behavior

Primary command:

```powershell
pytest -v
```

---

## Future

Once integration, UI, and CI infrastructure are implemented:

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
End-to-End Payment Tests
    │
    ▼
UI Tests
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

Future persistent test environments should use isolated databases and disposable test data.

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

Performance testing is not part of the current 64-test regression baseline.

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
    └── Transaction / Correlation IDs
```

These outputs will provide the foundation for the planned AI failure-analysis pipeline.

---

# Tools Summary

| Tool                             | Purpose                                              | Status      |
| -------------------------------- | ---------------------------------------------------- | ----------- |
| Pytest                           | Unit, service, state-machine, and API test execution | Implemented |
| FastAPI TestClient / HTTP Client | API endpoint testing                                 | Implemented |
| Selenium                         | Browser automation for dashboard testing             | Planned     |
| PostgreSQL                       | Persistent transaction and test data                 | Planned     |
| SQLAlchemy                       | Database access layer                                | Planned     |
| LangChain                        | LLM orchestration                                    | Planned     |
| LangGraph                        | AI workflow orchestration                            | Planned     |
| ChromaDB                         | Historical failure retrieval                         | Planned     |
| Ollama                           | Local LLM inference                                  | Planned     |
| Docker                           | Integrated test environment                          | Planned     |
| GitHub Actions                   | CI/CD execution                                      | Planned     |
| OpenTelemetry                    | Observability and tracing                            | Planned     |

---

# Current Test Status

## Completed

* [x] 14 state-machine tests
* [x] 14 payment-service tests
* [x] 36 API tests
* [x] 64 total automated backend tests
* [x] Full regression suite passing
* [x] Positive payment scenarios
* [x] Negative payment scenarios
* [x] Boundary-value testing
* [x] Invalid state-transition testing
* [x] Partial refund testing
* [x] Full refund testing
* [x] Simulated timeout testing
* [x] Simulated network-error testing
* [x] Transaction lifecycle API functionality
* [x] Web Dashboard transaction monitoring
* [x] Dashboard transaction lifecycle visualization
* [x] Lifecycle event and amount visibility

## Planned

* [ ] Automated Selenium dashboard testing
* [ ] Automated end-to-end payment lifecycle tests
* [ ] PostgreSQL integration testing
* [ ] Idempotency testing
* [ ] Concurrency testing
* [ ] Transaction rollback testing
* [ ] Persistence failure testing
* [ ] Monetary precision testing
* [ ] Transaction consistency testing
* [ ] Security testing
* [ ] Performance testing
* [ ] Observability validation
* [ ] AI RCA validation
* [ ] AI test-generation validation
* [ ] CI/CD integration testing

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

Individual endpoint correctness is necessary but insufficient. The platform must eventually validate authorization, capture, settlement, and refund as one coherent payment journey.

## Keep UI Tests Focused

Selenium tests should validate what a user can see and do. They should not simply reproduce every API test through a browser.

## AI Is an Assistant, Not an Oracle

AI-generated root causes and test cases must be validated against deterministic system behavior.

## Preserve Regression Stability

New functionality should extend the test suite without weakening the existing regression baseline.

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
Complete Lifecycle + Reliability Tests
        │
        ▼
Phase 4
PostgreSQL + Integration Tests
        │
        ▼
Phase 5
Selenium + End-to-End Tests
        │
        ▼
Phase 6
Observability + CI/CD
        │
        ▼
Phase 7
AI RCA + AI Test Generation


The current foundation is the domain, service, and API test suite with a working dashboard for transaction and lifecycle inspection.

The next major testing expansion should focus on **reliability, persistence, and automated end-to-end lifecycle validation** before introducing AI-driven test intelligence.

