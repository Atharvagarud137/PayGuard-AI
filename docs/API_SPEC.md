# API_SPEC.md — PayGuard AI Mock Payment Gateway

## Purpose

This document defines the **REST** **API** exposed by the PayGuard AI Mock Payment Gateway.

The **API** models a simplified payment transaction lifecycle covering:

- Card issuance
- Authorization
- Capture
- Settlement
- Full and partial refunds
- Transaction lookup

The **API** is implemented using FastAPI and is backed by the project's payment-domain, payment-service, repository, and state-machine layers.

The **API** specification is also exposed automatically through FastAPI's OpenAPI implementation and is intended to become the source for future AI-assisted test-case generation.

---

## Base URL

For local development:

```text [http://localhost:**8000**/api/v1](http://localhost:**8000**/api/v1) ````

FastAPI also exposes:

```text [http://localhost:**8000**/docs](http://localhost:**8000**/docs) ```

for Swagger UI and:

```text [http://localhost:**8000**/openapi.json](http://localhost:**8000**/openapi.json) ```

for the raw OpenAPI specification.

> **HTTPS** is not currently configured. The development **API** uses **HTTP**.

---

# Supported Card Networks

The card issuance **API** currently validates the configured card-network values defined by the application's request model.

The supported networks are:

```text **VISA** **MASTERCARD** **GENERIC** ```

`**GENERIC**` provides a configurable third network for testing network-specific behavior.

---

# Transaction Status Model

The current transaction lifecycle is:

```text
    ┌───────────────┐
    │  **AUTHORIZED**   │
    └───────┬───────┘
    │
    ▼
    ┌───────────────┐
    │   **CAPTURED**    │
    └───────┬───────┘
    │
    ▼
    ┌───────────────┐
    │    **SETTLED**    │
    └───────┬───────┘
    │
    ┌───────────┴───────────┐
    │                       │
    ▼                       ▼
    ┌────────────────────┐    ┌────────────────┐
    │ PARTIALLY_REFUNDED │    │    **REFUNDED**    │
    └─────────┬──────────┘    └────────────────┘
    │
    ▼
    ┌────────────────┐
    │    **REFUNDED**    │
    └────────────────┘
```

A declined authorization is a terminal transaction state:

```text
**AUTHORIZATION**
    |
    └──► **DECLINED**
```

The state machine prevents invalid lifecycle transitions.

---

# 1. Card Issuance

## Endpoint

```http **POST** /api/v1/cards ```

## Purpose

Creates a new virtual card record that can subsequently be used to authorize transactions.

## Request Body

| Field             | Type   | Required | Description                   |
| ----------------- | ------ | -------- | ----------------------------- |
| `cardholder_name` | string | Yes      | Name associated with the card |
| `network`         | string | Yes      | Supported card network        |
| `initial_balance` | number | Yes      | Initial available balance     |
| `expiry_date`     | string | Yes      | Card expiry date              |

The request model performs validation before the endpoint executes.

## Response

****HTTP** **201** Created**

The response contains the created `Card` model.

The generated card number is masked and follows the application's masked-card representation.

Example:

```json { *card_number*: *****-****-****-**1234*** } ```

The complete response schema is generated from the FastAPI/Pydantic `Card` model and should be treated as the authoritative response contract.

## Validation

The current **API** tests verify:

- Missing required fields
- Invalid card network
- Zero initial balance
- Negative initial balance
- Multiple card creation producing unique card identifiers

---

# 2. Authorization

## Endpoint

```http **POST** /api/v1/transactions/authorize ```

## Purpose

Attempts to authorize a payment against an active card.

A successful authorization reserves the requested amount against the card's available balance and creates a transaction in the `**AUTHORIZED**` state.

## Request Body

| Field         | Type   | Required | Description                          |
| ------------- | ------ | -------- | ------------------------------------ |
| `card_id`     | string | Yes      | Identifier of the card being charged |
| `amount`      | number | Yes      | Amount to authorize                  |
| `merchant_id` | string | Yes      | Identifier of the merchant           |

## Successful Response

****HTTP** **200** OK**

Example:

```json
{
    *transaction_id*: *transaction-id*,
    *status*: *AUTHORIZED*,
    *authorized_amount*: **100**
}
```

## Declined Authorization

Insufficient funds do not produce an **HTTP** 4xx response.

Instead, the **API** creates a transaction with:

```text status = **DECLINED** decline_reason = INSUFFICIENT_FUNDS ```

Example:

```json
{
    *transaction_id*: *transaction-id*,
    *status*: *DECLINED*,
    *decline_reason*: *INSUFFICIENT_FUNDS*
}
```

This models the distinction between a successfully processed payment request that is declined by the payment domain and a malformed or invalid **API** request.

## Error Cases

| Condition              | HTTP Status |
| ---------------------- | ----------: |
| Card not found         |         404 |
| Card inactive          |         400 |
| Missing merchant ID    |         422 |
| Invalid request amount |         422 |
| Zero amount            |         422 |

Request-validation status codes are handled by FastAPI/Pydantic before the business logic executes.

---

# 3. Capture

## Endpoint

```http **POST** /api/v1/transactions/{transaction_id}/capture ```

## Purpose

Captures an amount from an existing `**AUTHORIZED**` transaction.

The capture amount cannot exceed the authorized amount.

## Path Parameters

| Parameter        | Type   | Required | Description            |
| ---------------- | ------ | -------- | ---------------------- |
| `transaction_id` | string | Yes      | Transaction to capture |

## Request Body

| Field            | Type   | Required | Description       |
| ---------------- | ------ | -------- | ----------------- |
| `capture_amount` | number | Yes      | Amount to capture |

## Successful Response

****HTTP** **200** OK**

Example:

```json
{
    *transaction_id*: *transaction-id*,
    *status*: *CAPTURED*,
    *captured_amount*: **100**
}
```

## Business Rules

The capture operation is delegated to the `PaymentService`.

The service validates:

- Transaction existence
- Current transaction state
- Capture amount against authorized amount

## Error Cases

| Condition                             | HTTP Status |
| ------------------------------------- | ----------: |
| Transaction not found                 |         404 |
| Capture exceeds authorized amount     |         400 |
| Transaction not in `AUTHORIZED` state |         409 |
| Zero capture amount                   |         422 |
| Negative capture amount               |         422 |

The **API** tests currently verify successful capture, partial capture, excessive capture, nonexistent transactions, already-captured transactions, declined transactions, and zero-amount capture.

---

# 4. Settlement

## Endpoint

```http **POST** /api/v1/transactions/{transaction_id}/settle ```

## Purpose

Moves a successfully captured transaction into the `**SETTLED**` state.

Settlement represents the completion of the simulated payment lifecycle after capture.

## Path Parameters

| Parameter        | Type   | Required | Description           |
| ---------------- | ------ | -------- | --------------------- |
| `transaction_id` | string | Yes      | Transaction to settle |

## Request Body

No request body is required.

## Successful Response

****HTTP** **200** OK**

Example:

```json
{
    *transaction_id*: *transaction-id*,
    *status*: *SETTLED*,
    *settled_at*: ***2026**-08-**12T07**:19:35.**023052**+00:00*
}
```

The settlement timestamp is generated using **UTC**.

## Business Rules

Settlement is delegated to the `PaymentService`.

A transaction must currently be:

```text **CAPTURED** ```

before it can transition to:

```text **SETTLED** ```

## Error Cases

| Condition                           | HTTP Status |
| ----------------------------------- | ----------: |
| Transaction not found               |         404 |
| Transaction not in `CAPTURED` state |         409 |
| Already settled transaction         |         409 |

---

# 5. Refund

## Endpoint

```http **POST** /api/v1/transactions/{transaction_id}/refund ```

## Purpose

Refunds all or part of a settled transaction.

The implementation supports:

- Full refunds
- Partial refunds
- Multiple partial refunds
- Partial refund followed by a final refund

Refund processing is delegated to the `PaymentService`.

## Path Parameters

| Parameter        | Type   | Required | Description           |
| ---------------- | ------ | -------- | --------------------- |
| `transaction_id` | string | Yes      | Transaction to refund |

## Request Body

| Field           | Type   | Required | Description      |
| --------------- | ------ | -------- | ---------------- |
| `refund_amount` | number | Yes      | Amount to refund |

## Successful Response

****HTTP** **200** OK**

Example:

```json
{
    *transaction_id*: *transaction-id*,
    *refund_id*: *refund-d7c3e15e*,
    *status*: *REFUNDED*,
    *remaining_balance*: 0
}
```

For a partial refund:

```json
{
    *transaction_id*: *transaction-id*,
    *refund_id*: *refund-d7c3e15e*,
    *status*: *PARTIALLY_REFUNDED*,
    *remaining_balance*: 50
}
```

## Refund Rules

A refund is allowed only when the transaction is:

```text **SETTLED** ```

or:

```text PARTIALLY_REFUNDED ```

The total amount refunded cannot exceed the settled amount.

The transaction becomes:

```text PARTIALLY_REFUNDED ```

while a refundable balance remains.

Once the complete settled amount has been refunded, the transaction becomes:

```text **REFUNDED** ```

## Error Cases

| Condition                                  | HTTP Status |
| ------------------------------------------ | ----------: |
| Transaction not found                      |         404 |
| Transaction not settled/refundable         |         409 |
| Refund exceeds remaining refundable amount |         400 |
| Zero refund amount                         |         422 |
| Negative refund amount                     |         422 |
| Fully refunded transaction                 |         409 |

The current **API** test suite verifies full refunds, partial refunds, multiple partial refunds, excessive refunds, invalid transaction states, fully refunded transactions, zero refunds, and negative refunds.

---

# 6. Transaction Lookup

## Endpoint

```http **GET** /api/v1/transactions/{transaction_id} ```

## Purpose

Retrieves the complete transaction object, including its current status and transaction history.

This endpoint is intended to support:

- **API** verification
- Future Dashboard functionality
- Transaction lifecycle inspection
- Future test automation
- Future AI failure analysis

## Path Parameters

| Parameter        | Type   | Required | Description            |
| ---------------- | ------ | -------- | ---------------------- |
| `transaction_id` | string | Yes      | Transaction identifier |

## Successful Response

****HTTP** **200** OK**

The response is the application's `Transaction` model.

The model contains transaction information such as:

- Transaction identifier
- Card identifier
- Merchant identifier
- Transaction status
- Authorized amount
- Captured amount
- Settled amount
- Refunded amount
- Decline reason, where applicable
- Transaction history

## Error Cases

| Condition             | HTTP Status |
| --------------------- | ----------: |
| Transaction not found |         404 |

---

# 7. Health / Root Endpoint

## Endpoint

```http **GET** / ```

## Purpose

Provides a basic application health response for local development.

## Successful Response

****HTTP** **200** OK**

```json { *message*: *PayGuard AI Mock Payment Gateway is running* } ```

This endpoint is currently a simple application availability check rather than a full dependency health check.

A more comprehensive health/readiness model can be introduced when PostgreSQL, Docker services, and other external dependencies become part of the runtime architecture.

---

# Simulated Failure Injection

The Mock Payment Gateway supports deterministic technical-failure simulation through the:

```http X-Simulate-Failure ```

request header.

The feature exists to provide controlled failure scenarios for reliability testing and the future AI Root Cause Analysis pipeline.

## Supported Failure Types

### TIMEOUT

```http X-Simulate-Failure: **TIMEOUT** ```

Returns:

```text **HTTP** **504** Gateway Timeout ```

Response:

```json { *detail*: *Simulated timeout occurred* } ```

### NETWORK_ERROR

```http X-Simulate-Failure: NETWORK_ERROR ```

Returns:

```text **HTTP** **502** Bad Gateway ```

Response:

```json { *detail*: *Simulated network error* } ```

### INVALID_RESPONSE

```http X-Simulate-Failure: INVALID_RESPONSE ```

Returns:

```text **HTTP** **500** Internal Server Error ```

Response:

```json { *detail*: *Simulated invalid response* } ```

These failures are deterministic and therefore suitable for repeatable automated testing.

---

# Request Validation

FastAPI and Pydantic validate request payloads before payment-domain logic is executed.

This provides a distinction between:

### Request Validation Failure

Examples:

- Missing required field
- Invalid field type
- Invalid numeric constraint
- Invalid enum/network value

These are handled by the **API** validation layer.

### Payment Business Rule Failure

Examples:

- Insufficient funds
- Capture exceeding authorization
- Refund exceeding remaining refundable amount
- Settlement attempted before capture
- Refund attempted before settlement

These are handled by the payment-domain/service layer and translated into appropriate **HTTP** responses.

This separation is intentional:

```text
**HTTP** Request
    |
    v
### Pydantic Validation
    |
    v
**API** Layer
    |
    v
### Payment Service
    |
    v
Domain Rules / State Machine
    |
    v
Repository
    |
    v
Storage
```

---

# HTTP Status Code Conventions

The current **API** follows these conventions:

| Status | Meaning in PayGuard AI                                       |
| -----: | ------------------------------------------------------------ |
|    200 | Successful operation or business-level payment decline       |
|    201 | Resource successfully created                                |
|    400 | Business-rule violation involving an otherwise valid request |
|    404 | Requested card or transaction does not exist                 |
|    409 | Operation conflicts with the current transaction state       |
|    422 | Request validation failure                                   |
|    500 | Simulated internal/invalid-response failure                  |
|    502 | Simulated network failure                                    |
|    504 | Simulated timeout                                            |

The exact validation response body for `**422**` responses is generated by FastAPI/Pydantic and should not be duplicated manually in this document.

---

# Payment Lifecycle Examples

## Successful Payment

```text
## Issue Card
    |
    v
## Authorize
    |
    v
## Capture
    |
    v
## Settle
    |
    v
## Refund (optional)
```

Example lifecycle:

```text
**CARD** **CREATED**
    |
    v
**AUTHORIZED**
    |
    v
**CAPTURED**
    |
    v
**SETTLED**
    |
    v
**REFUNDED**
```

---

## Partial Refund Lifecycle

```text
**SETTLED**
    |
    v
PARTIALLY_REFUNDED
    |
    v
PARTIALLY_REFUNDED
    |
    v
**REFUNDED**
```

The transaction remains refundable until the total refunded amount reaches the settled amount.

---

## Declined Payment

```text **CARD** | v **AUTHORIZATION** | +---- insufficient funds ----> **DECLINED** ```

A declined authorization is stored as a transaction rather than treated as an unavailable resource or server failure.

---

# API-to-Service Architecture

The **API** layer is intentionally kept separate from payment business logic.

```text
┌──────────────────────────────┐
│         FastAPI **API**          │
│                              │
│ Request validation           │
│ **HTTP** responses               │
│ **HTTP** error mapping           │
└──────────────┬───────────────┘
    │
    ▼
┌──────────────────────────────┐
│       PaymentService         │
│                              │
│ Capture                      │
│ Settlement                   │
│ Refund                       │
└──────────────┬───────────────┘
    │
    ▼
┌──────────────────────────────┐
│       Domain / State         │
│                              │
│ Transaction lifecycle        │
│ Business rules               │
│ Domain exceptions            │
└──────────────┬───────────────┘
    │
    ▼
┌──────────────────────────────┐
│    Transaction Repository    │
└──────────────┬───────────────┘
    │
    ▼
┌──────────────────────────────┐
│       Current Storage        │
│        In-memory             │
└──────────────────────────────┘
```

This architecture provides a migration path toward persistent database-backed storage without coupling the payment service directly to FastAPI or a specific database implementation.

---

# Current API Test Coverage

The **API** specification is backed by an automated regression suite.

Current **API** coverage includes:

| Endpoint / Capability |  Tests |
| --------------------- | -----: |
| Authorization         |      7 |
| Capture               |      7 |
| Card Issuance         |      6 |
| Refund                |     10 |
| Settlement            |      6 |
| **Total**             | **36** |

The current **API** suite verifies:

- Positive scenarios
- Negative scenarios
- Boundary conditions
- Invalid transaction states
- Partial captures
- Partial refunds
- Full refunds
- Insufficient funds
- Simulated technical failures

The complete project regression suite currently contains:

```text 36 **API** tests 14 Payment Service tests ## 14 State Machine tests 64 total tests 64 passed 0 failed ```

---

# OpenAPI Documentation

FastAPI automatically generates the OpenAPI specification from the implemented request models, response models, and route definitions.

Interactive documentation:

```text [http://localhost:**8000**/docs](http://localhost:**8000**/docs) ```

Raw OpenAPI document:

```text [http://localhost:**8000**/openapi.json](http://localhost:**8000**/openapi.json) ```

The generated OpenAPI document should be treated as the machine-readable **API** contract.

Future AI test-case generation can consume this specification to identify additional scenarios.

---

# Future API Enhancements

The current **API** intentionally represents a simplified payment gateway. The following capabilities are candidates for future iterations:

- Idempotency keys
- Request correlation IDs
- Authentication and authorization
- Rate limiting
- Currency support
- Explicit monetary precision handling
- Transaction timestamps
- Merchant validation
- Card expiry validation
- Transaction expiration
- Authorization reversal/void
- Multiple capture support
- Refund identifiers as persistent entities
- Persistent refund records
- Webhook/event simulation
- PostgreSQL-backed persistence
- Optimistic or pessimistic concurrency controls
- Audit logging
- Health and readiness endpoints
- Structured error codes

These capabilities should be introduced incrementally rather than added merely to make the **API** specification look impressive. Payment software already has enough opportunities for accidental complexity without manufacturing more of it.

---

# API Design Principles

The current **API** follows these principles:

## 1. Payment-domain failures are not treated as generic server failures

For example, insufficient funds result in a valid `**DECLINED**` transaction rather than a server error.

## 2. Transaction state controls allowed operations

Capture, settlement, and refund operations are constrained by the transaction's current lifecycle state.

## 3. Business logic remains outside the HTTP layer

Payment operations are delegated to the payment service and domain layer where appropriate.

## 4. Validation occurs at the API boundary

Malformed or invalid request payloads are rejected before they reach the payment-domain logic.

## 5. The API remains deterministic for testing

Failure injection and controlled test data allow repeatable scenarios for automated regression and future AI-assisted failure analysis.

---

# Current API Status

| Capability                 | Status      |
| -------------------------- | ----------- |
| Card issuance              | Implemented |
| Authorization              | Implemented |
| Capture                    | Implemented |
| Settlement                 | Implemented |
| Full refund                | Implemented |
| Partial refund             | Implemented |
| Transaction lookup         | Implemented |
| Simulated timeout          | Implemented |
| Simulated network error    | Implemented |
| Simulated invalid response | Implemented |
| OpenAPI generation         | Implemented |
| Swagger UI                 | Implemented |
| Payment state machine      | Implemented |
| Payment service layer      | Implemented |
| Repository abstraction     | Implemented |
| Persistent database        | Planned     |
| Idempotency                | Planned     |
| Authentication             | Planned     |
| Rate limiting              | Planned     |
| Webhooks                   | Planned     |
| AI test-case generation    | Planned     |
| AI Root Cause Analysis     | Planned     |
