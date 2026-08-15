# PRD.md — PayGuard AI

## Product Overview

**PayGuard AI** is a portfolio project that combines payment-domain software engineering, automated testing, and applied AI.

The project simulates a payment gateway using FastAPI and validates its behavior through automated tests. The architecture separates the **API** layer from payment business logic using a Payment Service, transaction repository, domain exceptions, and a transaction state machine.

The longer-term objective is to extend this reliable payment-domain foundation with UI automation, persistent storage, CI/CD, and AI-assisted failure analysis and test generation.

The project is intended to demonstrate how modern QA engineering practices can be applied to a FinTech/payment system while using AI as an augmentation layer rather than replacing conventional engineering and testing.

---

# Problem Statement

Payment systems contain complex transaction lifecycles where seemingly small defects can have significant financial consequences.

Traditional automation can identify that a transaction flow has failed, but investigating the failure often still requires engineers to manually inspect test output, stack traces, application logs, and transaction state.

PayGuard AI addresses this problem through two complementary approaches:

1. **Strong payment-domain test automation** that validates transaction behavior, business rules, and lifecycle transitions.
2. **AI-assisted engineering capabilities** that can eventually analyze failures and suggest additional test scenarios.

The project deliberately establishes a reliable payment-domain foundation before introducing AI capabilities.

The current implementation therefore prioritizes:

- Payment lifecycle correctness
- State transition validation
- Business-rule validation
- Service-layer separation
- **API** contract validation
- Boundary and negative testing
- Deterministic failure simulation

AI capabilities are planned as the next augmentation layer.

---

# Product Goals

| Goal | Description | Status |
| --- | --- | --- |
| Demonstrate payment-domain engineering | Model realistic card and transaction lifecycles with appropriate business rules | Implemented |
| Demonstrate test automation expertise | Build layered automated tests covering domain, service, and API behavior | Implemented |
| Establish maintainable architecture | Separate API, service, domain, repository, and storage responsibilities | Implemented |
| Demonstrate reliability engineering | Introduce failure simulation and prepare for idempotency, concurrency, and persistence testing | Partially implemented / Planned |
| Demonstrate applied AI expertise | Build AI-assisted RCA and test-generation capabilities | Planned |
| Create a portfolio-ready engineering artifact | Maintain clear documentation, reproducible setup, automated regression, and incremental architecture | In Progress |
| Demonstrate enterprise-oriented engineering | Introduce persistence, security, observability, CI/CD, and reliability controls over time | Planned |

---

# Target Users / Audience

Since PayGuard AI is a portfolio project, its primary audience is technical rather than consumer-facing.

## Primary Audience

### Recruiters and Hiring Managers

The project should demonstrate:

- Practical software engineering ability
- QA automation experience
- Payment-domain understanding
- **API** testing
- Python development
- Maintainable architecture
- Applied AI experience

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
- AI-assisted **RCA**
- AI-generated test scenarios
- CI/CD
- Observability

## Development User

The project also serves as a personal engineering laboratory for experimenting with payment-system testing and AI-augmented quality engineering.

---

# Product Principles

## 1. Domain Correctness First

The payment lifecycle must be reliable before AI capabilities are layered on top.

```text
### Payment Domain
    |
    v
### Automated Tests
    |
    v
### Reliable Failure Data
    |
    v
AI Augmentation
````

AI should analyze and augment the engineering process, not compensate for an unstable core system.

---

## 2. Separation of Concerns

The architecture should maintain clear boundaries:

```text **API** | v ### Payment Service | v Domain / State Machine | v Repository | v Storage ```

This makes business logic independently testable and allows infrastructure to evolve without rewriting the payment domain.

---

## 3. Testability

Every important payment-domain rule should be testable independently from the **HTTP** layer.

The current implementation therefore contains separate:

- State machine tests
- Payment service tests
- **API** tests

---

## 4. Deterministic Behavior

The test environment should produce reproducible results.

Failure simulation, controlled test data, and deterministic business rules are preferred over unpredictable external dependencies.

---

## 5. Production-Oriented Design Without False Production Claims

PayGuard AI is a mock payment gateway and is **not** a production payment processor.

However, the architecture should demonstrate engineering practices relevant to real payment systems, including:

- Monetary precision
- Idempotency
- Transaction consistency
- Concurrency control
- Auditability
- Security
- Observability
- Failure recovery

The project should not claim **PCI**-**DSS** certification or production payment-network compliance.

---

# Current Product Scope

## Implemented

### Mock Payment Gateway

The FastAPI application currently supports:

- Card issuance
- Authorization
- Capture
- Settlement
- Full refunds
- Partial refunds
- Transaction lookup
- Simulated technical failures

### Payment Domain

The current domain architecture includes:

- Transaction lifecycle state machine
- Payment Service
- Transaction Repository
- Domain exceptions
- Transaction history/events

### Automated Testing

The current automated regression suite contains:

```text 14 State Machine Tests 14 Payment Service Tests ## 36 API Tests 64 Total Tests 64 Passed 0 Failed ```

The current suite covers:

- Positive scenarios
- Negative scenarios
- Boundary conditions
- Invalid transaction states
- Partial captures
- Full and partial refunds
- Insufficient funds
- Simulated timeout
- Simulated network errors

---

# Current Payment Lifecycle

The current transaction lifecycle is:

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
```

A declined authorization is terminal:

```text
**AUTHORIZATION**
    |
    +---- insufficient funds ----> **DECLINED**
```

The state machine explicitly validates legal and illegal transitions.

---

# Current Architecture

The current logical architecture is:

```text
┌─────────────────────────────┐
│       FastAPI **API**           │
│                             │
│ Request validation          │
│ **HTTP** response handling      │
└─────────────┬───────────────┘
    │
    ▼
┌─────────────────────────────┐
│      Payment Service        │
│                             │
│ Capture                     │
│ Settlement                  │
│ Refund                      │
└─────────────┬───────────────┘
    │
    ▼
┌─────────────────────────────┐
│      Payment Domain         │
│                             │
│ State Machine               │
│ Domain Rules                │
│ Domain Exceptions           │
└─────────────┬───────────────┘
    │
    ▼
┌─────────────────────────────┐
│   Transaction Repository    │
└─────────────┬───────────────┘
    │
    ▼
┌─────────────────────────────┐
│       In-Memory Storage      │
└─────────────────────────────┘
```

This architecture is intentionally suitable for evolving toward persistent storage without coupling payment business logic directly to a database.

---

# Functional Requirements

## FR-01: Card Issuance

The system shall allow creation of virtual card records containing:

- Cardholder name
- Card network
- Initial balance
- Expiry date

The system shall:

- Validate required fields
- Validate the configured card network
- Reject invalid initial balances
- Generate unique card identifiers
- Generate masked card numbers
- Create active cards by default

---

## FR-02: Authorization

The system shall allow an active card to authorize a transaction.

The authorization process shall:

## Validate the card exists.

## Validate the card is active. ## Validate the request. ## Check available balance. ## Create a transaction. ## Produce an `AUTHORIZED` transaction when approved. ## Produce a `DECLINED` transaction when funds are insufficient.

Insufficient funds are treated as a payment-domain decline rather than an **API**/server failure.

---

## FR-03: Capture

The system shall allow an authorized transaction to be captured.

The system shall:

- Reject nonexistent transactions.
- Reject invalid transaction states.
- Prevent capture above the authorized amount.
- Support partial capture.
- Record the captured amount.
- Transition the transaction to `**CAPTURED**`.

---

## FR-04: Settlement

The system shall allow a captured transaction to be settled.

The system shall:

- Reject nonexistent transactions.
- Reject transactions that are not captured.
- Record the settlement amount.
- Record settlement time.
- Transition the transaction to `**SETTLED**`.

---

## FR-05: Refund

The system shall allow settled transactions to be refunded.

The system shall support:

- Full refunds
- Partial refunds
- Multiple partial refunds
- Partial refund followed by final refund

The system shall:

- Reject refunds before settlement.
- Reject refunds exceeding the remaining refundable amount.
- Reject zero and negative refund amounts.
- Transition partially refunded transactions to `PARTIALLY_REFUNDED`.
- Transition fully refunded transactions to `**REFUNDED**`.
- Prevent further refunds after complete refund.

---

## FR-06: Transaction Lookup

The system shall allow retrieval of a transaction using its transaction identifier.

The response shall expose relevant transaction information and historical lifecycle events.

---

## FR-07: Failure Simulation

The system shall support deterministic technical-failure simulation using the `X-Simulate-Failure` header.

Supported scenarios currently include:

```text **TIMEOUT** NETWORK_ERROR INVALID_RESPONSE ```

These failures provide repeatable scenarios for reliability testing and future AI-assisted **RCA**.

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

- Additional payment flows
- Additional card networks
- Persistent storage
- UI automation
- AI analysis
- CI/CD
- Observability

without requiring a fundamental rewrite of the payment domain.

## NFR-05: Security

The system should avoid using real payment credentials or production cardholder information.

Future iterations should introduce:

- Authentication
- Authorization
- Rate limiting
- Secure secrets management
- Sensitive-data protection
- Structured security logging

## NFR-06: Reliability

Future versions should address:

- Idempotency
- Concurrency
- Transaction consistency
- Persistence failures
- Retry behavior
- Recovery scenarios

## NFR-07: Financial Accuracy

Future persistent/payment calculations should use appropriate decimal monetary representation rather than binary floating-point arithmetic.

---

# Current Persistence Model

The current application uses in-memory storage.

This is appropriate for the initial domain implementation because it provides:

- Simple development
- Fast execution
- Deterministic tests
- Minimal infrastructure
- Easy local experimentation

However, in-memory storage is not suitable for realistic payment-system durability.

It currently does not provide:

- Persistence across restarts
- Database transactions
- Transaction isolation
- Durable audit history
- Multi-process consistency
- Database-level constraints

A PostgreSQL-backed repository is therefore planned.

---

# Scope

## Current Scope

The current milestone focuses on:

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
| API Test Suite                   | Implemented |
| Service Test Suite               | Implemented |
| State Machine Test Suite         | Implemented |
| Deterministic Failure Simulation | Implemented |

---

## Planned Scope

| Feature                      | Status  |
| ---------------------------- | ------- |
| PostgreSQL Persistence       | Planned |
| Idempotency                  | Planned |
| Concurrency Controls         | Planned |
| Monetary Precision Hardening | Planned |
| UI Dashboard                 | Planned |
| Selenium Automation          | Planned |
| Docker Compose               | Planned |
| GitHub Actions CI/CD         | Planned |
| AI RCA Engine                | Planned |
| AI Test Case Generator       | Planned |
| ChromaDB Integration         | Planned |
| Ollama Integration           | Planned |
| OpenTelemetry                | Planned |
| Security Hardening           | Planned |
| Performance Testing          | Planned |

---

# Out of Scope

The following remain outside the project's intended scope.

| Item                                     | Reason                                                                                    |
| ---------------------------------------- | ----------------------------------------------------------------------------------------- |
| Real VISA/Mastercard network integration | The project uses a controlled mock payment gateway                                        |
| Processing real cardholder data          | Unnecessary and inappropriate for a portfolio project                                     |
| PCI-DSS certification                    | The project can demonstrate security principles but cannot claim regulatory certification |
| Production payment processing            | The application is a simulation and learning/portfolio artifact                           |
| Full banking infrastructure              | Beyond the project's intended scope                                                       |
| Consumer-facing production application   | The primary objective is engineering demonstration                                        |
| Multi-language application support       | Not relevant to the core engineering objectives                                           |

---

# AI Product Requirements

AI capabilities are planned as an augmentation layer on top of the existing testing foundation.

## AI-01: Root Cause Analysis

The system should eventually:

## Capture failed test output.

## Extract relevant failure context. ## Retrieve similar historical failures. ## Provide relevant context to an LLM. ## Generate a concise root cause summary. ## Provide evidence supporting the conclusion. ## Avoid presenting unsupported guesses as facts.

Planned architecture:

```text
### Test Failure
    |
    v
### Failure Context
    |
    v
Embedding
    |
    v
ChromaDB
    |
    v
### Historical Failures
    |
    v
Ollama / Local **LLM**
    |
    v
**RCA** Summary
```

---

## AI-02: Test Case Generation

The system should eventually consume the FastAPI OpenAPI specification and generate additional test scenarios.

The generated scenarios should focus on:

- Boundary conditions
- Negative scenarios
- Invalid state transitions
- Missing fields
- Invalid values
- Payment-specific edge cases

AI-generated test cases will require human review before being treated as authoritative.

---

# AI Quality Requirements

AI output should be evaluated independently from conventional test results.

## RCA

The initial target is:

> Correctly identify the failure category in at least 8 out of 10 deterministic test scenarios.

Evaluation should also consider:

- Evidence usage
- Relevance
- Accuracy
- Consistency
- Actionability
- Hallucination rate

## Test Case Generation

The initial target is:

> Produce at least 5 relevant, non-duplicate edge-case scenarios for a selected endpoint.

Generated scenarios should be reviewed for:

- Relevance
- Correct **API** understanding
- Domain correctness
- Non-duplication
- Executability

These targets should be treated as initial evaluation criteria rather than claims about AI performance before the pipeline is implemented.

---

# Security Requirements

PayGuard AI is not intended to process real payment information.

The system shall use synthetic test data.

Future security work should address:

- **API** authentication
- Role-based authorization where required
- Input validation
- Rate limiting
- Secrets management
- Sensitive-data redaction
- Secure logging
- Error-message information leakage
- Dependency security
- Container security

The project should explicitly avoid representing itself as **PCI**-**DSS** compliant or certified.

---

# Observability Requirements

Future versions should provide sufficient observability to trace a transaction and diagnose failures.

Planned capabilities include:

- Structured application logs
- Correlation/request IDs
- Transaction lifecycle events
- Distributed tracing
- AI workflow tracing
- CI failure artifacts

OpenTelemetry is planned as the primary observability framework.

---

# Success Criteria

Success criteria have been revised to distinguish what is already achieved from future targets.

## Current Success Criteria

| Metric                     | Current Result                           |
| -------------------------- | ---------------------------------------- |
| Automated regression suite | 64 tests                                 |
| Passing tests              | 64                                       |
| Failed tests               | 0                                        |
| State-machine coverage     | Implemented                              |
| Payment Service coverage   | Implemented                              |
| API coverage               | 36 tests                                 |
| Refund scenarios           | Full, partial, multiple partial          |
| Failure simulation         | Timeout, network error, invalid response |
| Layered architecture       | Implemented                              |

The current baseline is:

```text 64 tests 64 passed 0 failed ```

---

## Future Success Criteria

| Metric             | Target                                                   |
| ------------------ | -------------------------------------------------------- |
| API regression     | All implemented payment endpoints covered                |
| Domain regression  | All supported state transitions covered                  |
| Idempotency        | Duplicate payment operations safely handled              |
| Persistence        | Transaction data survives application restart            |
| Concurrency        | Concurrent operations do not violate payment invariants  |
| UI automation      | Core dashboard workflows automated                       |
| AI RCA             | ≥80% correct classification across evaluation scenarios  |
| AI test generation | ≥5 useful, non-duplicate scenarios per selected endpoint |
| CI/CD              | Automated regression execution on pull requests/pushes   |
| Observability      | Transaction and failure flows traceable                  |
| Security           | Core API security controls implemented                   |
| Documentation      | Documentation reflects actual implementation state       |

---

# Project Phases / Roadmap

The original phase structure has been revised to reflect the actual implementation progress.

## Phase 1 — Payment Gateway Foundation

**Status: Completed**

Deliverables:

- FastAPI Mock Payment Gateway
- Card issuance
- Authorization
- Capture
- Settlement
- Refunds
- Transaction lookup
- In-memory storage
- Basic failure simulation

---

## Phase 2 — Payment Domain Architecture

**Status: Completed**

Deliverables:

- Payment Service
- Transaction Repository
- Domain exceptions
- Transaction state machine
- Transaction history/events
- Separation between **API** and business logic

---

## Phase 3 — Automated Regression Foundation

**Status: Completed**

Deliverables:

- State-machine tests
- Payment Service tests
- **API** tests
- Positive scenarios
- Negative scenarios
- Boundary scenarios
- Refund coverage
- Failure simulation tests

Current baseline:

```text 64 passed 0 failed ```

---

## Phase 4 — Payment Reliability

**Status: Next Priority**

Planned deliverables:

- PostgreSQL persistence
- SQLAlchemy integration
- Idempotency
- Concurrency protection
- Transaction consistency
- Monetary precision
- Persistence failure handling
- Expanded integration tests

This phase is more important than immediately adding AI. A payment system with clever AI and weak transaction guarantees is still a payment system waiting to become a cautionary tale.

---

## Phase 5 — UI and End-to-End Automation

**Status: Planned**

Deliverables:

- Web Dashboard
- Selenium automation
- End-to-end transaction flows
- Transaction history validation
- UI error-state testing

---

## Phase 6 — CI/CD

**Status: Planned**

Deliverables:

- GitHub Actions
- Automated regression execution
- Test artifacts
- Failure reporting
- Environment setup
- Future AI **RCA** integration

---

## Phase 7 — AI Root Cause Analysis

**Status: Planned**

Deliverables:

- Failure-log ingestion
- Failure context extraction
- Historical failure retrieval
- ChromaDB integration
- Ollama integration
- **RCA** generation
- **RCA** evaluation framework

---

## Phase 8 — AI Test Case Generation

**Status: Planned**

Deliverables:

- OpenAPI ingestion
- **LLM**-based **API** analysis
- Edge-case generation
- Duplicate detection
- Human-review workflow
- Generated test scenario reports

---

## Phase 9 — Observability and Security Hardening

**Status: Planned**

Deliverables:

- OpenTelemetry
- Structured logging
- Correlation IDs
- Security controls
- Rate limiting
- Secrets management
- Sensitive-data redaction
- Dependency and container security

---

# Milestone Definition

A milestone should be considered complete only when:

## The feature is implemented.

## Automated tests exist for the feature. ## Existing regression tests remain green. ## Documentation reflects the actual behavior. ## Known limitations are documented. ## The implementation does not falsely claim production capabilities it does not possess.

---

# Assumptions

The project currently assumes:

- Development will primarily use Python 3.11.
- The current test environment uses a local Python virtual environment.
- Payment data is synthetic.
- The Mock Payment Gateway is not connected to real payment networks.
- The current storage implementation is in-memory.
- The project is developed locally.
- The project may be developed from a OneDrive-synchronized directory, requiring Uvicorn reload configuration to avoid unintended restarts.
- AI capabilities will initially use local inference through Ollama.
- AI-generated conclusions and test cases will require validation rather than being treated as inherently correct.

---

# Constraints

The project has several deliberate constraints:

### Portfolio Project

The system is designed to demonstrate engineering capability rather than operate as a commercial payment platform.

### No Real Payment Data

No production PANs, CVVs, credentials, or other sensitive payment information should be introduced.

### Controlled External Dependencies

The payment gateway must remain deterministic and locally testable.

### Incremental Architecture

Infrastructure should be introduced when it solves a real requirement rather than being added purely for architectural decoration.

---

# Risks and Mitigations

| Risk                                    | Impact      | Mitigation                                                          |
| --------------------------------------- | ----------- | ------------------------------------------------------------------- |
| In-memory storage loses data on restart | High        | Introduce PostgreSQL persistence                                    |
| Duplicate payment operations            | High        | Implement idempotency                                               |
| Concurrent transaction operations       | High        | Add concurrency controls and database transactions                  |
| Floating-point monetary calculations    | High        | Use decimal-based monetary representation                           |
| AI hallucination                        | Medium/High | Evidence-based RCA and human review                                 |
| AI-generated duplicate/invalid tests    | Medium      | Validation and duplicate detection                                  |
| OneDrive-triggered reloads              | Medium      | Restrict Uvicorn watcher to `app/`                                  |
| Dependency incompatibilities            | Medium      | Pin/manage dependencies and run regression after upgrades           |
| Insufficient observability              | Medium      | Structured logging and OpenTelemetry                                |
| Security assumptions                    | High        | Explicitly separate portfolio simulation from production/PCI claims |

---

# Definition of Done

The project will be considered portfolio-ready when the following minimum capabilities are demonstrated:

### Payment Domain

- [x] Card issuance
- [x] Authorization
- [x] Capture
- [x] Settlement
- [x] Full refund
- [x] Partial refund
- [x] Transaction lookup
- [x] State-machine validation

### Automated Testing

- [x] State-machine tests
- [x] Payment Service tests
- [x] **API** tests
- [x] Positive scenarios
- [x] Negative scenarios
- [x] Boundary scenarios
- [x] Failure simulation
- [x] 64-test regression baseline

### Architecture

- [x] Payment Service
- [x] Repository abstraction
- [x] Domain exceptions
- [x] Separation of **API** and business logic

### Reliability

- [ ] PostgreSQL persistence
- [ ] Idempotency
- [ ] Concurrency protection
- [ ] Monetary precision hardening
- [ ] Persistence failure handling

### Automation

- [ ] UI Dashboard
- [ ] Selenium tests
- [ ] End-to-end test flows
- [ ] CI/CD pipeline

### AI

- [ ] AI **RCA** engine
- [ ] Historical failure retrieval
- [ ] ChromaDB integration
- [ ] Ollama integration
- [ ] AI test-case generator
- [ ] AI output evaluation

### Engineering Quality

- [ ] Security hardening
- [ ] Observability
- [ ] Performance testing
- [ ] Containerized integration environment

---

# Current Product Status

**Current milestone: Payment Domain + Automated Regression Foundation**

PayGuard AI has progressed beyond the initial mock-**API** stage.

The current implementation contains a functioning payment transaction lifecycle, separated payment business logic, a transaction state machine, repository abstraction, domain exceptions, refund handling, deterministic failure simulation, and a 64-test automated regression suite.

The next strategic priority is **payment reliability and persistence**, not immediately adding more AI functionality.

The recommended progression is:

```text
    **CURRENT**
    |
    v
    ┌─────────────────────────────┐
    │ Payment Domain Foundation   │
    │        64 Tests Green       │
    └──────────────┬──────────────┘
    |
    v
    ┌─────────────────────────────┐
    │ Payment Reliability         │
    │ PostgreSQL                  │
    │ Idempotency                 │
    │ Concurrency                 │
    │ Monetary Precision          │
    └──────────────┬──────────────┘
    |
    v
    ┌─────────────────────────────┐
    │ UI + **E2E** Automation         │
    │ Selenium                    │
    └──────────────┬──────────────┘
    |
    v
    ┌─────────────────────────────┐
    │ CI/CD                       │
    │ GitHub Actions              │
    └──────────────┬──────────────┘
    |
    v
    ┌─────────────────────────────┐
    │ AI Root Cause Analysis      │
    │ ChromaDB + Ollama           │
    └──────────────┬──────────────┘
    |
    v
    ┌─────────────────────────────┐
    │ AI Test Case Generation     │
    │ OpenAPI + **LLM**               │
    └──────────────┬──────────────┘
    |
    v
    ┌─────────────────────────────┐
    │ Security + Observability    │
    │ OpenTelemetry + Hardening   │
    └─────────────────────────────┘
```

The current 64-test green baseline is the foundation for the next stage of the project. Future functionality should be introduced without regressing this baseline.

