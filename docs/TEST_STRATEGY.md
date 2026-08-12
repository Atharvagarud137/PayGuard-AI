# TEST_STRATEGY.md — PayGuard AI

## Purpose

This document defines the testing strategy for PayGuard AI.

The current testing focus is the Mock Payment Gateway and its payment-domain logic. The strategy is designed to validate the correctness of payment transaction lifecycles, business rules, state transitions, **API** behavior, failure handling, and boundary conditions.

As the project evolves, the strategy will expand to cover the Web Dashboard, Selenium automation, AI-generated outputs, persistence, concurrency, observability, and CI/CD workflows.

---

## Current Test Architecture

The current automated test suite is organized into three layers:

```text
    ┌──────────────────────┐
    │      **API** Tests       │
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
````

### Current Test Baseline

| Test Layer      | Tool       |  Tests | Status                   |
| --------------- | ---------- | -----: | ------------------------ |
| State Machine   | Pytest     |     14 | Passing                  |
| Payment Service | Pytest     |     14 | Passing                  |
| API             | Pytest     |     36 | Passing                  |
| **Total**       | **Pytest** | **64** | **64 Passed / 0 Failed** |

The complete regression suite currently executes successfully with zero test failures.

---

## Test Pyramid

The long-term test strategy follows a layered test pyramid rather than relying exclusively on **API** or end-to-end tests.

| Layer               | Tool                   | Current Status | Purpose                                                          |
| ------------------- | ---------------------- | -------------- | ---------------------------------------------------------------- |
| Domain / Unit Tests | Pytest                 | Implemented    | Validate state transitions and individual payment-domain rules   |
| Service Tests       | Pytest                 | Implemented    | Validate payment business logic independently of HTTP            |
| API Tests           | Pytest                 | Implemented    | Validate externally observable payment gateway behavior          |
| UI Tests            | Selenium               | Planned        | Validate dashboard behavior and transaction visibility           |
| AI Validation Tests | Pytest / Custom Checks | Planned        | Validate RCA summaries and generated test-case suggestions       |
| Reliability Tests   | Pytest                 | Planned        | Validate idempotency, concurrency, retries, and failure recovery |
| Persistence Tests   | Pytest + Database      | Planned        | Validate transactional consistency and database behavior         |

The project currently prioritizes domain and **API** correctness before expanding into UI and AI testing.

---

## Payment Transaction Lifecycle

The primary payment lifecycle under test is:

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

The test suite verifies both valid and invalid lifecycle transitions.

### Valid Transitions

- `**AUTHORIZED** → **CAPTURED**`
- `**CAPTURED** → **SETTLED**`
- `**SETTLED** → PARTIALLY_REFUNDED`
- `**SETTLED** → **REFUNDED**`
- `PARTIALLY_REFUNDED → PARTIALLY_REFUNDED`
- `PARTIALLY_REFUNDED → **REFUNDED**`

### Invalid Transitions

The state-machine tests also verify that invalid transitions are rejected, including:

- `**AUTHORIZED** → **SETTLED**`
- `**AUTHORIZED** → **REFUNDED**`
- `**CAPTURED** → **REFUNDED**`
- `**SETTLED** → **CAPTURED**`
- `**REFUNDED** → **CAPTURED**`
- `**REFUNDED** → **REFUNDED**`
- `**DECLINED** → **CAPTURED**`

This ensures that transaction lifecycle rules are enforced centrally rather than being duplicated across individual **API** endpoints.

---

## Payment Flow Test Coverage

### Card Issuance

| Category  | Coverage                                  |
| --------- | ----------------------------------------- |
| Positive  | Valid card successfully created           |
| Negative  | Missing required fields rejected          |
| Negative  | Invalid card network rejected             |
| Boundary  | Zero initial balance rejected             |
| Boundary  | Negative initial balance rejected         |
| Integrity | Multiple cards receive unique identifiers |

### Authorization

| Category   | Coverage                                          |
| ---------- | ------------------------------------------------- |
| Positive   | Transaction authorized with sufficient balance    |
| Negative   | Insufficient funds produce a declined transaction |
| Negative   | Card not found                                    |
| Negative   | Inactive card                                     |
| Boundary   | Authorization for exact available balance         |
| Validation | Missing merchant ID                               |
| Boundary   | Zero transaction amount                           |

### Capture

| Category    | Coverage                                          |
| ----------- | ------------------------------------------------- |
| Positive    | Authorized transaction successfully captured      |
| Positive    | Partial capture                                   |
| Negative    | Capture exceeds authorized amount                 |
| Negative    | Transaction not found                             |
| Negative    | Capture attempted on an invalid transaction state |
| Negative    | Already captured transaction                      |
| Boundary    | Zero capture amount                               |
| Reliability | Declined transaction cannot be captured           |

### Settlement

| Category    | Coverage                                  |
| ----------- | ----------------------------------------- |
| Positive    | Captured transaction successfully settled |
| Negative    | Transaction not found                     |
| Negative    | Settlement attempted before capture       |
| Negative    | Already settled transaction               |
| Reliability | Simulated timeout                         |
| Reliability | Simulated network error                   |

### Refund

| Category | Coverage                                    |
| -------- | ------------------------------------------- |
| Positive | Full refund                                 |
| Positive | Partial refund                              |
| Positive | Partial refund followed by remaining refund |
| Positive | Multiple partial refunds                    |
| Negative | Refund exceeds remaining refundable amount  |
| Negative | Refund attempted before settlement          |
| Negative | Already fully refunded transaction          |
| Negative | Transaction not found                       |
| Boundary | Zero refund amount                          |
| Boundary | Negative refund amount                      |

---

## State Machine Testing

The state machine is tested independently of the **HTTP** layer.

The tests verify:

## Valid transaction transitions are accepted.

## Invalid transaction transitions are rejected. ## Terminal states cannot transition into unrelated states. ## Partial refund transitions can occur repeatedly while refundable balance remains. ## A fully refunded transaction transitions to the terminal `REFUNDED` state.

This isolation ensures that lifecycle correctness does not depend on FastAPI, **HTTP** clients, or storage implementation details.

---

## Payment Service Testing

The `PaymentService` is tested independently from the **API** layer.

The current service-level test suite covers:

### Capture

- Successful capture
- Capture amount exceeding authorization
- Nonexistent transaction
- Invalid transaction state

### Settlement

- Successful settlement
- Nonexistent transaction
- Invalid transaction state

### Refund

- Full refund
- Partial refund
- Partial refund followed by full refund
- Refund exceeding remaining balance
- Nonexistent transaction
- Invalid transaction state
- Already refunded transaction

This layer verifies payment business rules before they are exposed through **HTTP**.

---

## API Testing

**API** tests validate the externally observable behavior of the payment gateway.

The **API** suite currently contains 36 tests covering:

- Card issuance
- Authorization
- Capture
- Settlement
- Refunds

The tests include:

- Successful operations
- Validation failures
- Missing resources
- Invalid transaction states
- Boundary values
- Partial operations
- Simulated technical failures

The **API** tests also verify appropriate **HTTP** behavior for domain failures.

Examples include:

```text **404** Resource not found

**400** Invalid amount or business constraint

**409** Invalid transaction lifecycle state

**422** Request validation failure

**502** Simulated network error

**504** Simulated timeout ```

---

## Domain Exception Testing

Payment-domain failures are represented using typed exceptions rather than requiring the service layer to communicate through **HTTP**-specific exceptions.

The current exception hierarchy includes:

```text PaymentError │ ├── TransactionNotFoundError ├── InvalidTransactionStateError ├── CaptureAmountExceededError └── RefundAmountExceededError ```

The service layer raises domain-level errors.

The **API** layer translates those errors into appropriate **HTTP** responses.

This separation is tested indirectly through both service-level and **API**-level tests.

---

## Failure Simulation

The Mock Payment Gateway supports deterministic technical failure simulation using the `X-Simulate-Failure` request header.

Supported scenarios include:

```text **TIMEOUT** NETWORK_ERROR INVALID_RESPONSE ```

These failure modes are used to test how the **API** behaves when technical failures occur.

They also provide a foundation for future resilience testing and AI-assisted root cause analysis.

---

## Current Regression Strategy

The full test suite should be executed after changes affecting payment-domain behavior, service logic, **API** endpoints, or state transitions.

### Run the complete suite

```powershell pytest -v ```

### Run API tests only

```powershell pytest tests/api -v ```

### Run service-layer tests

```powershell pytest tests/unit/test_payment_service.py -v ```

### Run state-machine tests

```powershell pytest tests/unit/test_state_machine.py -v ```

The current regression baseline is:

```text 64 tests 64 passed 0 failed ```

This baseline should remain green as new functionality is introduced.

---

## Test Environment Strategy

### Current Development Environment

The current automated tests run locally using:

- Python 3.11
- Pytest
- FastAPI
- In-memory application storage

The current test suite does not require PostgreSQL, Docker, ChromaDB, Ollama, or the Web Dashboard.

### Planned Test Environments

| Environment               | Purpose                                         | Status      |
| ------------------------- | ----------------------------------------------- | ----------- |
| Local                     | Development and rapid regression testing        | Implemented |
| Local + Database          | Persistence and transaction consistency testing | Planned     |
| Docker Compose            | Integrated multi-service testing                | Planned     |
| CI                        | Automated regression testing                    | Planned     |
| AI Validation Environment | RCA and test-generation validation              | Planned     |

---

## Future Reliability Testing

Payment systems require more than functional correctness. The next testing phase will introduce reliability-focused scenarios.

### Idempotency Testing

The system should verify that repeated requests with the same idempotency key do not create duplicate payment operations.

Examples:

- Duplicate authorization
- Duplicate capture
- Duplicate settlement
- Duplicate refund

### Concurrency Testing

The system should be tested for race conditions involving simultaneous operations on the same transaction.

Examples:

```text
Request A ───────► Capture
                  │
Request B ───────► Capture
```

The expected behavior is that the transaction cannot be captured twice.

Similar scenarios should be tested for refunds and settlement.

### Persistence Testing

After PostgreSQL is introduced, tests should verify:

- Transaction commit behavior
- Rollback behavior
- Constraint enforcement
- Data consistency
- Transaction isolation
- Recovery after database failures
- Durable transaction history

### Monetary Precision Testing

Payment amounts must be tested for exactness.

Future tests should cover:

- Currency precision
- Decimal boundaries
- Rounding rules
- Minimum transaction amounts
- Maximum transaction amounts
- Partial captures
- Partial refunds

The system should avoid floating-point arithmetic for financial calculations.

---

## Future UI Testing

The Web Dashboard is planned as the UI target for Selenium automation.

UI tests will eventually validate:

- Dashboard availability
- Transaction lookup
- Transaction status
- Transaction history
- Refund visibility
- Error-state presentation
- Successful payment flow visibility

UI tests should focus on user-visible behavior rather than duplicating the full **API** test suite.

---

## AI-Augmentation Strategy

AI capabilities will be introduced after the payment-domain and reliability foundation is sufficiently mature.

### Root Cause Analysis

The planned **RCA** pipeline is:

```text
### Test Failure
    |
    v
Failure Logs / Stack Trace
    |
    v
### Failure Context Extraction
    |
    v
### Embedding Generation
    |
    v
ChromaDB Retrieval
    |
    v
Local **LLM** via Ollama
    |
    v
### Root Cause Summary
```

The AI should use historical failure context to identify recurring problems rather than relying solely on the current stack trace.

### AI Test Case Generation

The planned test-generation workflow is:

```text
OpenAPI Specification
    |
    v
    **LLM** Analysis
    |
    v
Edge-Case Identification
    |
    v
### Test Scenario Suggestions
    |
    v
### Human Review
```

AI-generated test cases will initially be treated as suggestions requiring human review and validation.

---

## AI Output Validation Criteria

AI output must have its own quality criteria rather than being accepted simply because an **LLM** generated a plausible response.

### RCA Validation

Future **RCA** validation should measure:

- Correct identification of failure category
- Correct identification of affected component
- Consistency with the actual stack trace
- Relevance of retrieved historical failures
- Absence of unsupported conclusions
- Actionability of the suggested root cause

Initial target:

> Correctly classify at least 8 out of 10 known, deterministically injected failure scenarios.

### Test Case Generation Validation

Generated test scenarios should be evaluated for:

- Relevance to the **API**
- Correct understanding of endpoint behavior
- Boundary-value coverage
- Negative-case coverage
- Non-duplication
- Executability
- Domain correctness

Initial target:

> Generate at least 5 relevant, non-duplicate edge-case scenarios per selected endpoint.

These targets will be finalized once the AI pipeline is implemented and a representative evaluation dataset exists.

---

## Failure Handling and Future RCA Flow

The planned CI/**RCA** workflow is:

```text
## Test execution
    |
    v
## Failure detected
    |
    v
## Failure logs and stack trace captured
    |
    v
## RCA pipeline triggered
    |
    v
## Similar historical failures retrieved
    |
    v
## LLM generates RCA summary
    |
    v
## RCA report produced
    |
    v
## Developer / QA review
```

The AI should assist investigation rather than silently determine whether a payment-system failure is acceptable.

---

## Regression Strategy

The regression strategy will evolve as additional components are introduced.

### Current

Run the full automated suite for changes affecting:

- Payment domain
- State machine
- Payment service
- Repository
- **API** endpoints
- Request/response models

The primary regression command is:

```powershell pytest -v ```

### Future

Once CI/CD is implemented:

```text
### Pull Request
    |
    v
Unit / Domain Tests
    |
    v
### Service Tests
    |
    v
**API** Tests
    |
    v
### Integration Tests
    |
    v
UI Tests
    |
    v
AI Validation
```

A scheduled regression run may later be introduced for longer-running AI and integration tests.

CI scheduling should only be introduced once the corresponding CI pipeline and test infrastructure are implemented.

---

## Test Data Strategy

The current test suite primarily uses controlled test fixtures and simulated payment data.

Test data should remain:

- Deterministic
- Reproducible
- Non-production
- Free of real cardholder information
- Suitable for automated execution

No real **PAN**, **CVV**, cardholder authentication data, or production payment credentials should be used in the test environment.

Future persistent test environments should use isolated test databases and disposable test data.

---

## Security Testing Considerations

As the project evolves, security testing should cover:

- Input validation
- Authentication
- Authorization
- Rate limiting
- Sensitive-data exposure
- Logging of payment information
- Secrets management
- **API** abuse scenarios
- Injection attacks
- Insecure direct object references
- Error-message information leakage

The current project is a mock payment gateway and is not a **PCI**-**DSS**-certified payment environment.

Security testing should therefore focus on demonstrating secure engineering practices rather than claiming regulatory certification.

---

## Tools Summary

| Tool                             | Purpose                                              | Status      |
| -------------------------------- | ---------------------------------------------------- | ----------- |
| Pytest                           | Unit, service, state-machine, and API test execution | Implemented |
| HTTP client / FastAPI TestClient | API endpoint testing                                 | Implemented |
| Selenium                         | Browser automation for UI testing                    | Planned     |
| LangChain                        | LLM orchestration for RCA and test generation        | Planned     |
| LangGraph                        | AI workflow orchestration                            | Planned     |
| ChromaDB                         | Vector storage for historical failure retrieval      | Planned     |
| Ollama                           | Local LLM inference                                  | Planned     |
| PostgreSQL                       | Persistent test/payment data                         | Planned     |
| Docker                           | Integrated test environment                          | Planned     |
| GitHub Actions                   | CI/CD execution and future scheduled testing         | Planned     |
| OpenTelemetry                    | Observability and tracing                            | Planned     |

---

## Current Test Status

### Completed

- [x] 14 state-machine tests
- [x] 14 payment-service tests
- [x] 36 **API** tests
- [x] 64 total automated tests
- [x] Full regression suite passing
- [x] Positive payment scenarios
- [x] Negative payment scenarios
- [x] Boundary-value testing
- [x] Invalid state-transition testing
- [x] Partial and full refund testing
- [x] Simulated timeout testing
- [x] Simulated network-error testing

### Planned

- [ ] UI automation
- [ ] End-to-end browser testing
- [ ] PostgreSQL integration testing
- [ ] Idempotency testing
- [ ] Concurrency testing
- [ ] Transaction rollback testing
- [ ] Persistence failure testing
- [ ] Security testing
- [ ] Performance testing
- [ ] AI **RCA** validation
- [ ] AI test-generation validation
- [ ] CI/CD integration testing
- [ ] Observability validation
