# PRD.md — PayGuard AI

## Product Overview

**PayGuard AI** is a portfolio project that combines payment-domain software engineering, automated testing, reliability engineering, and applied AI.

The project simulates a payment gateway using FastAPI and validates its behavior through automated tests. The architecture separates the **API** layer from payment business logic through a Payment Service, transaction repository, domain exceptions, and a transaction state machine.

The longer-term objective is to evolve this foundation into an enterprise-style payment testing platform incorporating persistent storage, reliability controls, UI automation, CI/CD, observability, and AI-assisted failure analysis and test generation.

The project is intended to demonstrate how modern QA engineering practices can be applied to a FinTech/payment system while using AI as an augmentation layer rather than a replacement for conventional engineering and testing.

The current implementation intentionally stops at the payment-domain and automated-regression foundation. The next strategic priority is **payment reliability and persistence**, particularly PostgreSQL, monetary precision, idempotency, concurrency, and durable transaction history.

---

# Problem Statement

Payment systems contain complex transaction lifecycles where seemingly small defects can have significant financial consequences.

Traditional automation can identify that a transaction flow has failed, but investigating the failure often still requires engineers to manually inspect test output, stack traces, application logs, request/response data, and transaction state.

PayGuard AI addresses this problem through two complementary approaches:

1. **Strong payment-domain test automation** that validates transaction behavior, business rules, lifecycle transitions, boundary conditions, and failure scenarios.
2. **AI-assisted engineering capabilities** that can eventually analyze failures and suggest additional test scenarios.

The project deliberately establishes a reliable payment-domain foundation before introducing AI capabilities.

The current implementation therefore prioritizes:

- Payment lifecycle correctness
- State transition validation
- Business-rule validation
- Service-layer separation
- **API** contract validation
- Positive, negative, and boundary testing
- Deterministic failure simulation
- Repository-based persistence abstraction
- Regression stability

AI capabilities remain a future augmentation layer and will only be introduced after the underlying payment behavior and reliability model are sufficiently mature.

---

# Product Goals

| Goal | Description | Status |
| --- | --- | --- |
| Demonstrate payment-domain engineering | Model card and transaction lifecycles with explicit business rules | Implemented |
| Demonstrate test automation expertise | Build layered automated tests covering domain, service, and API behavior | Implemented |
| Establish maintainable architecture | Separate API, service, domain, repository, and storage responsibilities | Implemented |
| Establish a reliable payment foundation | Introduce persistence, monetary precision, idempotency, concurrency, and consistency controls | Next Priority |
| Demonstrate applied AI expertise | Build AI-assisted RCA and test-generation capabilities on top of reliable test data | Planned |
| Demonstrate UI automation expertise | Build a dashboard and validate it through Selenium | Planned |
| Demonstrate CI/CD engineering | Automate regression execution and failure reporting | Planned |
| Demonstrate observability | Trace payment and test-execution behavior | Planned |
| Create a portfolio-ready engineering artifact | Maintain clear documentation, reproducible setup, automated regression, and incremental architecture | In Progress |
| Demonstrate enterprise-oriented engineering | Apply payment-system reliability, security, observability, and automation practices | Planned |

---

# Target Users / Audience

PayGuard AI is a portfolio project, so its primary audience is technical rather than consumer-facing.

## Primary Audience

### Recruiters and Hiring Managers

The project should demonstrate:

- Practical software engineering ability
- QA automation expertise
- Payment-domain understanding
- **API** testing
- Python development
- Maintainable architecture
- Reliability engineering
- Applied AI capabilities

## Secondary Audience

### Technical Interviewers / Engineering Teams

The project should provide enough technical depth to discuss:

- Payment transaction lifecycles
- State machines
- **API** design
- Service-layer architecture
- Repository patterns
- Test strategy
- Failure handling
- Idempotency
- Persistence
- Concurrency
- Monetary precision
- AI-assisted **RCA**
- AI-generated test scenarios
- CI/CD
- Observability
- Security considerations

## Development User

The project also serves as an engineering laboratory for experimenting with:

- Payment-system testing
- Reliability engineering
- Test automation
- AI-augmented quality engineering
- Local AI workflows

---

# Product Principles

## 1. Domain Correctness First

The payment lifecycle must be reliable before AI capabilities are layered on top.

```text
Payment Domain
      |
      v
Automated Tests
      |
      v
Reliable Failure Data
      |
      v
AI Augmentation
````

AI should analyze and augment the engineering process, not compensate for an unstable core system.

---

## 2. Reliability Before Architectural Expansion

The project should solve the most important payment-domain problems before adding additional infrastructure.

The intended progression is:

```text
Core Payment Domain
      |
      v
Automated Regression
      |
      v
Payment Reliability
      |
      v
Persistent Storage
      |
      v
Automation Platform
      |
      v
AI Augmentation
```

Adding technologies without solving the underlying reliability problems would produce architectural decoration rather than engineering value. Humanity has already contributed enough of that.

---

## 3. Separation of Concerns

The architecture should maintain clear boundaries:

```text
API
 |
 v
Payment Service
 |
 v
Domain / State Machine
 |
 v
Repository
 |
 v
Storage
```

This makes business logic independently testable and allows infrastructure to evolve without rewriting the payment domain.

---

## 4. Testability

Every important payment-domain rule should be testable independently from the **HTTP** layer.

The current implementation therefore contains separate:

* State machine tests
* Payment service tests
* **API** tests

---

## 5. Deterministic Behavior

The test environment should produce reproducible results.

Failure simulation, controlled test data, explicit state transitions, and deterministic business rules are preferred over uncontrolled external dependencies.

---

## 6. Production-Oriented Design Without False Production Claims

PayGuard AI is a mock payment gateway and is **not** a production payment processor.

However, the architecture should demonstrate engineering practices relevant to real payment systems, including:

* Monetary precision
* Idempotency
* Transaction consistency
* Concurrency control
* Durable persistence
* Auditability
* Security
* Observability
* Failure recovery

The project must not claim:

* Production payment processing
* Real VISA/Mastercard network integration
* **PCI-DSS** certification
* Production cardholder-data compliance

---

# Current Product Scope

## Implemented

### Mock Payment Gateway

The FastAPI application currently supports:

* Card issuance
* Authorization
* Capture
* Settlement
* Full refunds
* Partial refunds
* Transaction lookup
* Simulated technical failures

### Payment Domain

The current domain architecture includes:

* Transaction lifecycle state machine
* Payment Service
* Transaction Repository
* Typed domain exceptions
* Transaction history/events

### Automated Testing

The current automated regression suite contains:

```text
14 State Machine Tests
14 Payment Service Tests
36 API Tests
-----------------
64 Total Tests
64 Passed
0 Failed
```

The current suite covers:

* Positive scenarios
* Negative scenarios
* Boundary conditions
* Invalid transaction states
* Partial captures
* Full refunds
* Partial refunds
* Multiple partial refunds
* Insufficient funds
* Simulated timeout
* Simulated network errors
* Simulated invalid responses

---

# Current Payment Lifecycle

The current transaction lifecycle is:

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

A declined authorization is terminal:

```text
AUTHORIZATION
    |
    +---- insufficient funds ----> DECLINED
```

The state machine explicitly validates legal and illegal transitions.

Invalid operations include:

* Capturing a declined transaction
* Capturing an already captured transaction
* Settling an authorized transaction before capture
* Settling an already settled transaction
* Refunding an unsettled transaction
* Refunding an already fully refunded transaction
* Refunding more than the remaining refundable amount

---

# Current Architecture

The current logical architecture is:

```text
┌─────────────────────────────┐
│         FastAPI API         │
│                             │
│ Request validation          │
│ HTTP response handling      │
│ Domain error translation    │
│ Failure simulation          │
└─────────────┬───────────────┘
              |
              v
┌─────────────────────────────┐
│       Payment Service       │
│                             │
│ Capture                     │
│ Settlement                  │
│ Refund                      │
└─────────────┬───────────────┘
              |
              v
┌─────────────────────────────┐
│       Payment Domain        │
│                             │
│ State Machine               │
│ Domain Rules                │
│ Domain Exceptions           │
└─────────────┬───────────────┘
              |
              v
┌─────────────────────────────┐
│    Transaction Repository   │
└─────────────┬───────────────┘
              |
              v
┌─────────────────────────────┐
│       In-Memory Storage     │
└─────────────────────────────┘
```

The repository abstraction deliberately isolates payment business logic from the current storage implementation.

This provides a migration path toward PostgreSQL without requiring the payment service to become database-aware.

---

# Functional Requirements

## FR-01: Card Issuance

The system shall allow creation of virtual card records containing:

* Cardholder name
* Card network
* Initial balance
* Expiry date

The system shall:

* Validate required fields
* Validate the configured card network
* Reject invalid initial balances
* Generate unique card identifiers
* Generate masked card numbers
* Create active cards by default

---

## FR-02: Authorization

The system shall allow an active card to authorize a transaction.

The authorization process shall:

* Validate that the card exists
* Validate that the card is active
* Validate the request payload
* Validate the transaction amount
* Check available balance
* Create a transaction
* Produce an `AUTHORIZED` transaction when approved
* Produce a `DECLINED` transaction when funds are insufficient

Insufficient funds are treated as a payment-domain decline rather than an **API** or server failure.

---

## FR-03: Capture

The system shall allow an authorized transaction to be captured.

The system shall:

* Reject nonexistent transactions
* Reject invalid transaction states
* Prevent capture above the authorized amount
* Support partial capture
* Record the captured amount
* Record the transaction event
* Transition the transaction to `CAPTURED`

---

## FR-04: Settlement

The system shall allow a captured transaction to be settled.

The system shall:

* Reject nonexistent transactions
* Reject transactions that are not captured
* Record the settlement amount
* Record settlement time
* Record the transaction event
* Transition the transaction to `SETTLED`

---

## FR-05: Refund

The system shall allow settled transactions to be refunded.

The system shall support:

* Full refunds
* Partial refunds
* Multiple partial refunds
* Partial refund followed by a final refund

The system shall:

* Reject refunds before settlement
* Reject refunds exceeding the remaining refundable amount
* Reject zero refund amounts
* Reject negative refund amounts
* Record refund events
* Transition partially refunded transactions to `PARTIALLY_REFUNDED`
* Transition fully refunded transactions to `REFUNDED`
* Prevent further refunds after complete refund

---

## FR-06: Transaction Lookup

The system shall allow retrieval of a transaction using its transaction identifier.

The response shall expose relevant transaction information, including where applicable:

* Transaction identifier
* Card identifier
* Merchant identifier
* Transaction status
* Authorized amount
* Captured amount
* Settled amount
* Refunded amount
* Decline reason
* Transaction history

---

## FR-07: Failure Simulation

The system shall support deterministic technical-failure simulation using the `X-Simulate-Failure` request header.

Supported scenarios currently include:

```text
TIMEOUT
NETWORK_ERROR
INVALID_RESPONSE
```

These failures provide repeatable scenarios for:

* Reliability testing
* Regression testing
* Failure analysis
* Future AI-assisted RCA

---

# Non-Functional Requirements

## NFR-01: Testability

Payment-domain business rules should be independently testable without requiring the **HTTP** layer.

## NFR-02: Maintainability

Business logic should remain separated from framework and persistence concerns.

## NFR-03: Determinism

Automated tests should be repeatable and should not depend on uncontrolled external payment systems.

## NFR-04: Extensibility

The architecture should allow:

* Additional payment flows
* Additional card networks
* Persistent storage
* UI automation
* AI analysis
* CI/CD
* Observability

without requiring a fundamental rewrite of the payment domain.

## NFR-05: Security

The system should avoid using real payment credentials or production cardholder information.

Future iterations should introduce:

* Authentication
* Authorization
* Rate limiting
* Secure secrets management
* Sensitive-data protection
* Structured security logging

## NFR-06: Reliability

Future versions should address:

* Idempotency
* Concurrency
* Transaction consistency
* Persistence failures
* Retry behavior
* Recovery scenarios

## NFR-07: Financial Accuracy

Financial calculations should use an explicit monetary representation suitable for currency arithmetic rather than relying on binary floating-point behavior.

The reliability phase should establish:

* Decimal monetary representation
* Currency precision rules
* Rounding behavior
* Minimum and maximum supported amounts

---

# Current Persistence Model

The current application uses in-memory storage.

This is appropriate for the initial domain implementation because it provides:

* Simple development
* Fast execution
* Deterministic tests
* Minimal infrastructure
* Easy local experimentation

However, in-memory storage is not suitable for realistic payment-system durability.

It currently does not provide:

* Persistence across application restarts
* Database transactions
* Transaction isolation
* Durable audit history
* Multi-process consistency
* Database-level constraints
* Database-backed concurrency control

The next architecture phase will introduce PostgreSQL through the existing repository abstraction.

---

# Persistence Requirements

The future persistence implementation should provide:

### PR-01: Durable Transactions

Transaction state must survive application restarts.

### PR-02: Transactional Updates

Payment operations that modify related records must execute within appropriate database transaction boundaries.

### PR-03: Consistency

The database must prevent states that violate payment-domain invariants.

### PR-04: Concurrency Control

Concurrent operations on the same transaction must not produce invalid lifecycle states or duplicate financial operations.

### PR-05: Auditability

Important payment lifecycle events should be durably persisted.

### PR-06: Repository Isolation

The Payment Service should continue to depend on repository abstractions rather than directly on SQLAlchemy or PostgreSQL implementation details.

---

# Reliability Requirements

The next major product phase is focused on payment reliability.

## REL-01: Idempotency

Repeated requests representing the same logical payment operation should not result in duplicate financial effects.

Initial operations requiring idempotency consideration:

* Authorization
* Capture
* Settlement
* Refund

The implementation should support deterministic handling of repeated requests.

---

## REL-02: Concurrency Safety

Concurrent operations on the same transaction must preserve transaction invariants.

Examples include:

```text
Request A ─────► Capture
Request B ─────► Capture
```

The system must prevent both requests from independently succeeding when only one capture is valid.

Equivalent scenarios should be tested for:

* Settlement
* Refund
* Partial refund
* Final refund

---

## REL-03: Monetary Precision

Financial calculations must not depend on binary floating-point arithmetic.

The implementation should explicitly define:

* Currency representation
* Precision
* Rounding rules
* Comparison rules
* Partial-operation behavior

---

## REL-04: Transaction Consistency

A payment operation should either complete its required state and data changes consistently or fail without leaving an invalid intermediate state.

---

## REL-05: Durable Audit History

Payment lifecycle events should eventually be stored durably so that transaction history survives application restarts and can be used for:

* Debugging
* Auditability
* Reliability analysis
* Future AI failure analysis

---

# Scope

## Current Scope

| Feature                          | Status      |
| -------------------------------- | ----------- |
| Mock Payment Gateway             | Implemented |
| Card Issuance                    | Implemented |
| Authorization                    | Implemented |
| Capture                          | Implemented |
| Settlement                       | Implemented |
| Full Refund                      | Implemented |
| Partial Refund                   | Implemented |
| Transaction Lookup               | Implemented |
| State Machine                    | Implemented |
| Payment Service                  | Implemented |
| Repository Abstraction           | Implemented |
| Domain Exceptions                | Implemented |
| Transaction History/Events       | Implemented |
| API Test Suite                   | Implemented |
| Service Test Suite               | Implemented |
| State Machine Test Suite         | Implemented |
| Deterministic Failure Simulation | Implemented |

---

## Next Scope

| Feature                       | Status |
| ----------------------------- | ------ |
| Monetary Precision Hardening  | Next   |
| PostgreSQL Persistence        | Next   |
| SQLAlchemy Integration        | Next   |
| Idempotency                   | Next   |
| Concurrency Controls          | Next   |
| Transaction Consistency       | Next   |
| Durable Audit/Event Storage   | Next   |
| Persistence Integration Tests | Next   |
| Persistence Failure Tests     | Next   |

---

## Future Scope

| Feature                | Status  |
| ---------------------- | ------- |
| UI Dashboard           | Planned |
| Selenium Automation    | Planned |
| End-to-End Test Flows  | Planned |
| Docker Compose         | Planned |
| GitHub Actions CI/CD   | Planned |
| AI RCA Engine          | Planned |
| AI Test Case Generator | Planned |
| ChromaDB Integration   | Planned |
| Ollama Integration     | Planned |
| OpenTelemetry          | Planned |
| Security Hardening     | Planned |
| Performance Testing    | Planned |

---

# Out of Scope

The following remain outside the project's intended scope.

| Item                                     | Reason                                                                                             |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Real VISA/Mastercard network integration | The project uses a controlled mock payment gateway                                                 |
| Processing real cardholder data          | Unnecessary and inappropriate for a portfolio project                                              |
| PCI-DSS certification                    | The project can demonstrate secure engineering practices but cannot claim regulatory certification |
| Production payment processing            | The application is a simulation and portfolio artifact                                             |
| Full banking infrastructure              | Beyond the project's intended scope                                                                |
| Consumer-facing production application   | The primary objective is engineering demonstration                                                 |
| Real financial settlement                | Settlement is simulated within the payment domain                                                  |
| Production-grade card issuing            | Card issuance is simulated for testing                                                             |
| Multi-language application support       | Not relevant to the core engineering objectives                                                    |

---

# AI Product Requirements

AI capabilities are planned as an augmentation layer on top of the payment and reliability foundation.

AI should not become the next implementation priority until the reliability phase provides meaningful persistent transaction and failure data.

---

## AI-01: Root Cause Analysis

The system should eventually:

* Capture failed test output
* Extract relevant failure context
* Retrieve similar historical failures
* Provide relevant context to an LLM
* Generate a concise root cause summary
* Identify the likely failure category
* Provide evidence supporting the conclusion
* Suggest corrective actions where appropriate
* Avoid presenting unsupported guesses as facts

Planned architecture:

```text
Test Failure
    |
    v
Failure Context
    |
    v
Embedding
    |
    v
ChromaDB
    |
    v
Historical Failures
    |
    v
Ollama / Local LLM
    |
    v
RCA Summary
```

The AI should function as an investigation assistant rather than an autonomous authority.

---

## AI-02: Test Case Generation

The system should eventually consume the FastAPI OpenAPI specification and generate additional test scenarios.

The generated scenarios should focus on:

* Boundary conditions
* Negative scenarios
* Invalid state transitions
* Missing fields
* Invalid values
* Payment-specific edge cases
* Reliability scenarios
* Concurrency scenarios
* Potential gaps in existing coverage

AI-generated test cases will require human review before being treated as authoritative.

---

# AI Quality Requirements

AI output should be evaluated independently from conventional test results.

## RCA Quality

The initial target is:

> Correctly identify the failure category in at least 8 out of 10 deterministic evaluation scenarios.

Evaluation should also consider:

* Evidence usage
* Relevance
* Accuracy
* Consistency
* Actionability
* Unsupported conclusions
* Hallucination rate

The evaluation dataset should contain known failure scenarios with expected categories and supporting evidence.

---

## Test Case Generation Quality

The initial target is:

> Produce at least 5 relevant, non-duplicate edge-case scenarios for a selected endpoint.

Generated scenarios should be reviewed for:

* API correctness
* Domain correctness
* Relevance
* Non-duplication
* Executability
* Expected-result correctness
* Coverage value

These targets are evaluation criteria, not claims about AI performance before the pipeline is implemented.

---

# Security Requirements

PayGuard AI is not intended to process real payment information.

The system shall use synthetic test data.

Future security work should address:

* **API** authentication
* Role-based authorization where required
* Input validation
* Rate limiting
* Secrets management
* Sensitive-data redaction
* Secure logging
* Error-message information leakage
* Dependency security
* Container security
* Access control
* Secure configuration

The project should explicitly avoid representing itself as **PCI-DSS** compliant or certified.

---

# Observability Requirements

Future versions should provide sufficient observability to trace a transaction and diagnose failures.

Planned capabilities include:

* Structured application logs
* Correlation/request IDs
* Transaction lifecycle events
* Distributed tracing
* Database operation visibility
* AI workflow tracing
* CI failure artifacts
* Failure-to-transaction correlation

OpenTelemetry is planned as the primary observability framework.

Observability should be introduced after the underlying transaction and persistence architecture is sufficiently stable to produce meaningful telemetry.

---

# Performance and Reliability Requirements

Performance testing is not part of the current 64-test regression baseline.

Future performance validation should focus on realistic payment-system behavior rather than arbitrary throughput numbers.

Areas to evaluate include:

* API response latency
* Concurrent transaction processing
* Database transaction latency
* Lock contention
* Repeated payment operations
* Refund processing
* Repository performance
* Failure recovery
* Resource utilization

Performance targets should be established after PostgreSQL persistence and concurrency controls are implemented.

---

# Success Criteria

Success criteria distinguish between currently achieved capabilities and future targets.

## Current Success Criteria

| Metric                     | Current Result                           |
| -------------------------- | ---------------------------------------- |
| Automated regression suite | 64 tests                                 |
| Passing tests              | 64                                       |
| Failed tests               | 0                                        |
| State-machine testing      | Implemented                              |
| Payment Service testing    | Implemented                              |
| API testing                | 36 tests                                 |
| Refund scenarios           | Full, partial, multiple partial          |
| Failure simulation         | Timeout, network error, invalid response |
| Layered architecture       | Implemented                              |
| Repository abstraction     | Implemented                              |
| Domain exceptions          | Implemented                              |

The current baseline is:

```text
64 tests
64 passed
0 failed
```

---

## Next-Phase Success Criteria

| Metric                  | Target                                                     |
| ----------------------- | ---------------------------------------------------------- |
| Monetary representation | Explicit decimal-based currency handling                   |
| Persistence             | Transaction data survives application restart              |
| Database transactions   | Payment operations have appropriate transaction boundaries |
| Idempotency             | Duplicate payment operations safely handled                |
| Concurrency             | Concurrent operations do not violate payment invariants    |
| Audit history           | Lifecycle events persist durably                           |
| Integration tests       | Database-backed payment flows covered                      |
| Persistence failures    | Rollback and failure behavior validated                    |
| Regression              | Existing 64-test baseline remains green                    |

---

## Future Success Criteria

| Metric             | Target                                                   |
| ------------------ | -------------------------------------------------------- |
| UI automation      | Core dashboard workflows automated                       |
| E2E testing        | Core payment lifecycle validated end-to-end              |
| CI/CD              | Automated regression execution on pull requests/pushes   |
| AI RCA             | ≥80% correct classification across evaluation scenarios  |
| AI test generation | ≥5 useful, non-duplicate scenarios per selected endpoint |
| Observability      | Transaction and failure flows traceable                  |
| Security           | Core API security controls implemented                   |
| Performance        | Baselines established for realistic workloads            |
| Documentation      | Documentation reflects actual implementation state       |

---

# Project Phases / Roadmap

The project roadmap has been revised to prioritize reliability before UI and AI expansion.

## Phase 1 — Payment Gateway Foundation

**Status: Completed**

Deliverables:

* FastAPI Mock Payment Gateway
* Card issuance
* Authorization
* Capture
* Settlement
* Refunds
* Transaction lookup
* In-memory storage
* Basic failure simulation

---

## Phase 2 — Payment Domain Architecture

**Status: Completed**

Deliverables:

* Payment Service
* Transaction Repository
* Domain exceptions
* Transaction state machine
* Transaction history/events
* Separation between **API** and business logic

---

## Phase 3 — Automated Regression Foundation

**Status: Completed**

Deliverables:

* State-machine tests
* Payment Service tests
* **API** tests
* Positive scenarios
* Negative scenarios
* Boundary scenarios
* Refund coverage
* Failure simulation tests

Current baseline:

```text
64 passed
0 failed
```

---

## Phase 4 — Payment Reliability and Persistence

**Status: Next Priority**

Planned deliverables:

* Monetary precision
* PostgreSQL persistence
* SQLAlchemy integration
* Transaction boundaries
* Idempotency
* Concurrency protection
* Transaction consistency
* Durable audit/event storage
* Persistence failure handling
* Database-backed integration tests

This phase is the immediate priority.

The goal is to transform the current deterministic in-memory payment model into a more realistic and testable transactional system.

---

## Phase 5 — Automation Platform

**Status: Planned**

Planned deliverables:

* Web Dashboard
* Selenium automation
* End-to-end payment flows
* Transaction history validation
* UI error-state testing
* Expanded integration testing

The dashboard and frontend should be introduced only after the backend reliability foundation is sufficiently stable.

---

## Phase 6 — CI/CD

**Status: Planned**

Planned deliverables:

* GitHub Actions
* Automated regression execution
* Test artifacts
* Failure reporting
* Environment setup
* Integration-test execution
* Future AI RCA integration

---

## Phase 7 — AI Root Cause Analysis

**Status: Planned**

Planned deliverables:

* Failure-log ingestion
* Failure context extraction
* Historical failure retrieval
* ChromaDB integration
* Ollama integration
* RCA generation
* RCA evaluation framework
* Human-review workflow

---

## Phase 8 — AI Test Case Generation

**Status: Planned**

Planned deliverables:

* OpenAPI ingestion
* LLM-based API analysis
* Edge-case generation
* Reliability scenario generation
* Duplicate detection
* Human-review workflow
* Generated test scenario reports

---

## Phase 9 — Observability and Security Hardening

**Status: Planned**

Planned deliverables:

* OpenTelemetry
* Structured logging
* Correlation IDs
* Security controls
* Rate limiting
* Secrets management
* Sensitive-data redaction
* Dependency security
* Container security
* Performance baselines

---

# Milestone Definition

A milestone should be considered complete only when:

* The feature is implemented.
* Automated tests exist for the feature.
* Existing regression tests remain green.
* Documentation reflects actual behavior.
* Known limitations are documented.
* Failure behavior is understood.
* The implementation does not falsely claim production capabilities it does not possess.

For infrastructure-heavy milestones, successful completion should also include reproducible local setup and appropriate integration tests.

---

# Assumptions

The project currently assumes:

* Development primarily uses Python 3.11.
* The current test environment uses a local Python virtual environment.
* Payment data is synthetic.
* The Mock Payment Gateway is not connected to real payment networks.
* The current storage implementation is in-memory.
* The project is developed locally.
* The project may be developed from a OneDrive-synchronized directory, requiring restricted Uvicorn reload monitoring.
* AI capabilities will initially use local inference through Ollama.
* AI-generated conclusions and test cases will require validation.
* PostgreSQL will become the next persistent storage implementation through the repository abstraction.
* Existing payment-domain behavior should remain stable while infrastructure is introduced.

---

# Constraints

The project has several deliberate constraints.

## Portfolio Project

The system is designed to demonstrate engineering capability rather than operate as a commercial payment platform.

## No Real Payment Data

No production PANs, CVVs, credentials, or other sensitive payment information should be introduced.

## Controlled External Dependencies

The payment gateway must remain deterministic and locally testable.

## Incremental Architecture

Infrastructure should be introduced when it solves a real requirement rather than being added purely for architectural decoration.

## Local-First AI

The planned AI layer should initially support local experimentation through Ollama rather than requiring a hosted LLM service.

## Regression Stability

Existing tests should remain green as new capabilities are introduced.

---

# Risks and Mitigations

| Risk                                    | Impact      | Mitigation                                                                 |
| --------------------------------------- | ----------- | -------------------------------------------------------------------------- |
| In-memory storage loses data on restart | High        | Introduce PostgreSQL persistence                                           |
| Duplicate payment operations            | High        | Implement idempotency                                                      |
| Concurrent transaction operations       | High        | Add concurrency controls and database transactions                         |
| Floating-point monetary calculations    | High        | Use decimal-based monetary representation                                  |
| Database transaction inconsistency      | High        | Define explicit transaction boundaries and rollback behavior               |
| AI hallucination                        | Medium/High | Evidence-based RCA, evaluation dataset, and human review                   |
| AI-generated duplicate/invalid tests    | Medium      | Validation and duplicate detection                                         |
| OneDrive-triggered reloads              | Medium      | Restrict Uvicorn watcher to `app/`                                         |
| Dependency incompatibilities            | Medium      | Controlled dependency management and regression testing                    |
| Insufficient observability              | Medium      | Structured logging and OpenTelemetry                                       |
| Security assumptions                    | High        | Explicitly separate portfolio simulation from production/PCI claims        |
| Premature architectural expansion       | Medium      | Introduce new infrastructure only when justified by a concrete requirement |

---

# Definition of Done

The project will be considered portfolio-ready when the following minimum capabilities are demonstrated.

## Payment Domain

* [x] Card issuance
* [x] Authorization
* [x] Capture
* [x] Settlement
* [x] Full refund
* [x] Partial refund
* [x] Transaction lookup
* [x] State-machine validation

## Automated Testing

* [x] State-machine tests
* [x] Payment Service tests
* [x] **API** tests
* [x] Positive scenarios
* [x] Negative scenarios
* [x] Boundary scenarios
* [x] Failure simulation
* [x] 64-test regression baseline

## Architecture

* [x] Payment Service
* [x] Repository abstraction
* [x] Domain exceptions
* [x] Separation of **API** and business logic
* [x] Transaction history/events

## Reliability

* [ ] Monetary precision hardening
* [ ] PostgreSQL persistence
* [ ] SQLAlchemy integration
* [ ] Idempotency
* [ ] Concurrency protection
* [ ] Transaction consistency
* [ ] Durable audit/event storage
* [ ] Persistence failure handling
* [ ] Database-backed integration tests

## Automation

* [ ] UI Dashboard
* [ ] Selenium tests
* [ ] End-to-end test flows
* [ ] CI/CD pipeline

## AI

* [ ] AI **RCA** engine
* [ ] Historical failure retrieval
* [ ] ChromaDB integration
* [ ] Ollama integration
* [ ] AI test-case generator
* [ ] AI output evaluation

## Engineering Quality

* [ ] Security hardening
* [ ] Observability
* [ ] Performance testing
* [ ] Containerized integration environment

---

# Current Product Status

**Current milestone: Payment Domain + Automated Regression Foundation**

PayGuard AI has progressed beyond the initial mock-**API** stage.

The current implementation contains:

* A functioning payment transaction lifecycle
* Separated payment business logic
* A transaction state machine
* Repository abstraction
* Typed domain exceptions
* Refund handling
* Transaction history/events
* Deterministic failure simulation
* 64 automated regression tests
* 64 passing tests
* 0 failing tests

The next strategic priority is **payment reliability and persistence**.

The project should not immediately expand into frontend, UI automation, or AI implementation before addressing the limitations of in-memory persistence and payment reliability.

The recommended progression is:

```text
                 CURRENT
                    |
                    v
┌─────────────────────────────────┐
│ Payment Domain Foundation       │
│ 64 Tests Green                  │
└────────────────┬────────────────┘
                 |
                 v
┌─────────────────────────────────┐
│ Payment Reliability             │
│                                 │
│ Monetary Precision              │
│ PostgreSQL                      │
│ Idempotency                     │
│ Concurrency                     │
│ Transaction Consistency         │
│ Durable Audit Events            │
└────────────────┬────────────────┘
                 |
                 v
┌─────────────────────────────────┐
│ Automation Platform             │
│                                 │
│ UI Dashboard                    │
│ Selenium                        │
│ End-to-End Testing              │
└────────────────┬────────────────┘
                 |
                 v
┌─────────────────────────────────┐
│ CI/CD                           │
│                                 │
│ GitHub Actions                  │
│ Automated Regression            │
└────────────────┬────────────────┘
                 |
                 v
┌─────────────────────────────────┐
│ AI Root Cause Analysis          │
│                                 │
│ ChromaDB + Ollama               │
└────────────────┬────────────────┘
                 |
                 v
┌─────────────────────────────────┐
│ AI Test Case Generation         │
│                                 │
│ OpenAPI + LLM                   │
└────────────────┬────────────────┘
                 |
                 v
┌─────────────────────────────────┐
│ Security + Observability        │
│                                 │
│ OpenTelemetry + Hardening       │
└─────────────────────────────────┘
```

The current 64-test green baseline is the foundation for the next stage of the project.

Future functionality must be introduced without weakening the existing payment-domain invariants or regressing the automated test baseline.

