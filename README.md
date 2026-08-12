# PayGuard AI

**AI-Augmented Test Automation Framework for Payment Systems**

PayGuard AI is a portfolio project focused on combining payment-domain test automation, software architecture, and applied AI. The project simulates a payment gateway covering card issuance, authorization, capture, settlement, and refunds, while building a structured foundation for **API** automation, UI automation, observability, and AI-assisted failure analysis.

The project is being developed incrementally, with the payment-domain foundation established before introducing the AI-driven testing capabilities.

## Why This Project Exists

Traditional QA automation validates whether a system behaves as expected. PayGuard AI aims to go further by combining reliable payment-domain modeling with intelligent test analysis.

The project is designed to eventually support:

- Automated validation of payment transaction lifecycles
- Positive, negative, and boundary-condition testing
- AI-assisted root cause analysis of test failures
- AI-generated test-case suggestions
- UI and **API** automation
- Failure simulation for realistic payment-system scenarios
- CI/CD-based automated validation

The current development phase focuses on building a reliable and testable payment-domain foundation before layering AI capabilities on top of it.

## Current Milestone

### Core Payment Gateway + Domain Architecture

The core Mock Payment Gateway is implemented and covered by an automated regression suite.

Current capabilities include:

- Card issuance
- Transaction authorization
- Transaction capture
- Settlement
- Full refunds
- Partial refunds
- Transaction lookup
- Payment lifecycle state validation
- Transaction state machine
- Payment service layer
- Transaction repository abstraction
- Typed payment-domain exceptions
- Simulated timeout and network failure scenarios

### Current Test Baseline

The current automated test suite contains:

| Test Layer | Tests | Status |
| ----------- | ----: | ------ |
| State Machine | 14 | Passing |
| Payment Service | 14 | Passing |
| API | 36 | Passing |
| **Total** | **64** | **64 Passed / 0 Failed** |

The complete test suite currently executes successfully with zero test failures.

## Current Backend Architecture

The payment transaction flow currently follows a layered architecture:

```text
    FastAPI
    |
    v
    **API** / **HTTP** Layer
    |
    v
    Payment Service
    |
    +--------+--------+
    |                 |
    v                 v
    State Machine      Domain Exceptions
    |
    v
    Transaction
    Repository
    |
    v
    In-Memory Storage
````

The architecture deliberately separates **HTTP** concerns from payment business logic.

The **API** layer is responsible for:

- **HTTP** request handling
- Request validation
- **HTTP** response formatting
- Mapping domain exceptions to **HTTP** status codes
- Simulated failure handling

The payment service is responsible for:

- Capture business rules
- Settlement business rules
- Refund business rules
- Transaction state changes
- Transaction history updates

The domain state machine is responsible for validating transaction lifecycle transitions.

The repository provides an abstraction between the payment service and the current storage implementation.

## Payment Transaction Lifecycle

The current transaction lifecycle is modeled using explicit states:

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

Invalid lifecycle transitions are rejected by the domain state machine.

This includes scenarios such as attempting to capture an already captured, settled, refunded, or declined transaction.

## Core Components

| Component              | Current Status | Description                                                                |
| ---------------------- | -------------- | -------------------------------------------------------------------------- |
| Mock Payment Gateway   | Implemented    | FastAPI service simulating core payment transaction flows                  |
| Payment Domain         | Implemented    | Transaction lifecycle and business rules                                   |
| State Machine          | Implemented    | Explicit validation of payment transaction state transitions               |
| Payment Service        | Implemented    | Application/service layer containing capture, settlement, and refund logic |
| Transaction Repository | Implemented    | Persistence abstraction for transaction data                               |
| In-Memory Storage      | Implemented    | Current storage implementation used by the payment gateway                 |
| API Test Suite         | Implemented    | Pytest coverage for positive, negative, and boundary scenarios             |
| UI Dashboard           | Planned        | Web interface intended to provide a Selenium automation target             |
| UI Test Suite          | Planned        | Selenium-based validation of dashboard behavior                            |
| AI RCA Engine          | Planned        | LangChain, ChromaDB, and local LLM-based failure analysis                  |
| AI Test Case Generator | Planned        | LLM-based suggestions for additional API test scenarios                    |
| PostgreSQL Persistence | Planned        | Persistent database layer for production-oriented architecture             |
| CI/CD Pipeline         | Planned        | Automated test execution and future AI-assisted failure analysis           |
| Containerization       | Planned        | Docker-based orchestration of project services                             |

## Tech Stack

### Current / Core

- **Python 3.11**
- **FastAPI**
- **Pydantic**
- **Pytest**
- **Repository pattern**
- **Domain state machine**
- **In-memory persistence**

### Planned / Integrated as the Project Evolves

- **Selenium** for UI automation
- **SQLAlchemy** and PostgreSQL for persistent storage
- **LangChain** for AI orchestration
- **LangGraph** for workflow orchestration
- **ChromaDB** for vector-based retrieval
- **Ollama** for local **LLM** execution
- **OpenTelemetry** for observability
- **Docker** for containerization
- **GitHub Actions** for CI/CD

Technologies listed as planned are part of the intended project architecture and should not be interpreted as fully implemented functionality in the current milestone.

## Current Project Status

**Milestone 2: Core Payment Lifecycle + Domain Architecture — Complete**

The current implementation has established a tested foundation for the payment gateway.

### Completed

- [x] Card issuance
- [x] Transaction authorization
- [x] Transaction capture
- [x] Settlement
- [x] Full refunds
- [x] Partial refunds
- [x] Transaction lookup
- [x] Payment state machine
- [x] Payment service layer
- [x] Transaction repository abstraction
- [x] Typed payment-domain exceptions
- [x] **API** regression tests
- [x] Service-layer tests
- [x] State-machine tests
- [x] 64-test automated regression baseline

### In Progress / Next

- [ ] Dependency and test-client cleanup
- [ ] Monetary precision model
- [ ] Idempotency support
- [ ] Concurrency and race-condition handling
- [ ] Persistent storage design
- [ ] PostgreSQL integration
- [ ] Auditability and transaction event persistence
- [ ] Observability
- [ ] UI dashboard
- [ ] Selenium automation
- [ ] AI root cause analysis
- [ ] AI-generated test cases
- [ ] CI/CD integration
- [ ] Containerization

## Planned Roadmap

The project will continue in incremental milestones rather than introducing all components simultaneously.

### Milestone 1 — Payment Gateway Foundation

- Core payment APIs
- Card issuance
- Authorization
- Capture
- Settlement
- Refunds
- Failure simulation

**Status: Complete**

### Milestone 2 — Domain Architecture and Testability

- Transaction state machine
- Payment service layer
- Repository abstraction
- Typed domain exceptions
- Unit and **API** test coverage

**Status: Complete**

### Milestone 3 — Payment Reliability

- Monetary precision
- Idempotency
- Concurrency safety
- Transaction consistency
- Persistent storage
- PostgreSQL integration
- Audit trail
- Structured error handling

**Status: Next**

### Milestone 4 — Automation Platform

- Web dashboard
- Selenium automation
- Expanded **API** test coverage
- End-to-end payment scenarios
- CI/CD integration

**Status: Planned**

### Milestone 5 — AI-Augmented Testing

- Failure-log ingestion
- AI-assisted root cause analysis
- Historical failure retrieval
- AI-generated test scenarios
- **LLM** evaluation and validation

**Status: Planned**

### Milestone 6 — Production-Oriented Platform Architecture

- Dockerized services
- Observability
- Persistent event/audit architecture
- Scalable execution
- Security hardening
- End-to-end CI/CD automation

**Status: Planned**

## Current Limitations

The current implementation is intentionally a mock payment gateway and should not be considered a production payment processor.

Current limitations include:

- Transactions are stored in memory
- PostgreSQL persistence is not yet implemented
- Idempotency is not yet implemented
- Distributed concurrency control is not yet implemented
- Production card-network integrations are not implemented
- Authentication and authorization are not yet implemented
- **PCI**-compliant card-data handling is outside the current scope
- AI-based root cause analysis is not yet implemented
- AI-generated test cases are not yet implemented
- CI/CD automation is not yet implemented
- UI automation is not yet implemented

These limitations are part of the planned evolution of the project rather than defects in the current **MVP** milestone.

## Documentation

| Document                | Purpose                                                            |
| ----------------------- | ------------------------------------------------------------------ |
| `docs/PRD.md`           | Product requirements, scope, and success criteria                  |
| `docs/ARCHITECTURE.md`  | System architecture and component interactions                     |
| `docs/TEST_STRATEGY.md` | Testing strategy, test layers, coverage goals, and AI augmentation |
| `docs/TECH_STACK.md`    | Technology choices and architectural justification                 |
| `docs/API_SPEC.md`      | Mock payment gateway endpoint definitions and API behavior         |
| `docs/AI_PIPELINE.md`   | AI root cause analysis and test-generation design                  |
| `docs/SETUP.md`         | Local development and setup instructions                           |

## Author

**Atharva Garud** — Associate Engineer @ Worldline, **ISTQB** Certified, building at the intersection of quality engineering, payment systems, test automation, and applied AI.
