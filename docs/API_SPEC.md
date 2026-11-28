# API_SPEC.md — PayGuard AI Mock Payment Gateway

**Reviewed: 20 November 2026.** This API contract is descriptive; runtime-generated OpenAPI in development/test is authoritative. Database migrations run under a dedicated migration role; API execution uses the restricted runtime role.

## Purpose

This document defines the REST API exposed by the PayGuard AI Mock Payment Gateway.

The API models a simplified payment transaction lifecycle covering:

- Card issuance
- Authorization
- Capture
- Settlement
- Full refunds
- Partial refunds
- Transaction lookup
- Idempotent authorization
- Idempotent capture
- Idempotent settlement
- Idempotent refund

The API is implemented using FastAPI and backed by PostgreSQL repositories, the payment service, domain state machine, audit chain, and idempotency records. The API handler owns each request's database transaction.

The API specification is exposed through FastAPI OpenAPI in development and test environments. Swagger, ReDoc and OpenAPI routes are disabled in production.

---

# Base URL

For local development:

```text
http://localhost:8000/api/v1
````

FastAPI also exposes:

```text
http://localhost:8000/docs
```

for Swagger UI and:

```text
http://localhost:8000/openapi.json
```

for the raw OpenAPI specification.

> Local development uses HTTP. Production HTTPS termination is a deployment responsibility.

## Authentication and access control

Outside the explicitly keyless `development` and isolated `test` configurations:

| API area | Required header |
|---|---|
| Business operations and dashboard API | `X-API-Key` |
| Audit lookup and integrity endpoints | `X-Admin-API-Key` |
| Test reset endpoint, only when enabled | `X-Test-Reset-Token` |

Production requires `PAYGUARD_API_KEY` and `PAYGUARD_ADMIN_API_KEY`, each at least 32 characters. Key comparisons use constant-time comparison. These are shared API credentials, not per-user authentication or RBAC.

The root `GET /` liveness endpoint is public. Test reset is not registered by default; it can only be enabled with `PAYGUARD_ENV=test`, `PAYGUARD_ENABLE_TEST_ENDPOINTS=true`, and a separate reset token. Failure simulation and OpenAPI documentation are disabled in production.

## Synthetic payment-data boundary

Card issuance creates a synthetic masked card identifier. Card-creation requests do not accept real PAN or CVV/CVC fields; undeclared fields are rejected. Never submit real cardholder data or production payment credentials.

---

# Supported Card Networks

The card issuance API validates the configured card-network values defined by the application's request model. It creates synthetic test records and a generated masked card identifier; it is not a card tokenization service.

The currently supported networks are:

```text
VISA
MASTERCARD
GENERIC
```

`GENERIC` provides a configurable third network for testing network-specific behavior.

---

# Transaction Status Model

The current transaction lifecycle is:

```text
    ┌───────────────┐
    │   AUTHORIZED  │
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │    CAPTURED   │
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │    SETTLED    │
    └───────┬───────┘
            │
       ┌────┴──────────────┐
       │                   │
       ▼                   ▼
┌──────────────────┐  ┌───────────────┐
│PARTIALLY_REFUNDED│  │    REFUNDED   │
└────────┬─────────┘  └───────────────┘
         │
         │ remaining amount refunded
         ▼
  ┌───────────────┐
  │    REFUNDED   │
  └───────────────┘
```

A declined authorization is a terminal transaction state:

```text
AUTHORIZATION
      │
      └──► DECLINED
```

The state machine prevents invalid lifecycle transitions.

---

# 1. Card Issuance

## Endpoint

```http
POST /api/v1/cards
```

## Purpose

Creates a new virtual card record that can subsequently be used to authorize transactions.

## Request Body

| Field             | Type   | Required | Description                   |
| ----------------- | ------ | -------- | ----------------------------- |
| `cardholder_name` | string | Yes      | Name associated with the card |
| `network`         | string | Yes      | Supported card network        |
| `initial_balance` | number | Yes      | Initial available balance     |
| `expiry_date`     | string | Yes      | Card expiry date              |

Example request:

```json
{
  "cardholder_name": "Atharva Garud",
  "network": "VISA",
  "initial_balance": 5000,
  "expiry_date": "12/28"
}
```

The request model performs validation before the endpoint executes.

## Successful Response

```text
HTTP 201 Created
```

The response contains the created `Card` model.

The generated card number is masked according to the application's card representation.

Example:

```json
{
  "card_id": "e9fa7848-3e2c-424b-b14d-3001fca837be",
  "card_number": "****-****-****-1234",
  "cardholder_name": "Atharva Garud",
  "network": "VISA",
  "balance": 5000,
  "expiry_date": "12/28",
  "status": "ACTIVE"
}
```

The exact response schema generated by FastAPI/Pydantic should be treated as the authoritative response contract.

## Validation

The API tests verify scenarios including:

* Missing required fields
* Invalid card network
* Zero initial balance
* Negative initial balance
* Multiple card creation producing unique identifiers
* Successful card creation

---

# 2. Authorization

## Endpoint

```http
POST /api/v1/transactions/authorize
```

## Purpose

Attempts to authorize a payment against an active card.

A successful authorization creates a transaction in the `AUTHORIZED` state and records the authorized amount.

## Request Body

| Field         | Type   | Required | Description                          |
| ------------- | ------ | -------- | ------------------------------------ |
| `card_id`     | string | Yes      | Identifier of the card being charged |
| `amount`      | number | Yes      | Amount to authorize                  |
| `merchant_id` | string | Yes      | Identifier of the merchant           |

Example:

```json
{
  "card_id": "e9fa7848-3e2c-424b-b14d-3001fca837be",
  "amount": 50,
  "merchant_id": "MERCHANT-001"
}
```

## Successful Response

```text
HTTP 200 OK
```

Example:

```json
{
  "transaction_id": "transaction-id",
  "status": "AUTHORIZED",
  "authorized_amount": 50
}
```

## Declined Authorization

Insufficient funds do not produce an HTTP 4xx response.

Instead, the API creates a transaction with:

```text
status = DECLINED
decline_reason = INSUFFICIENT_FUNDS
```

Example:

```json
{
  "transaction_id": "transaction-id",
  "status": "DECLINED",
  "decline_reason": "INSUFFICIENT_FUNDS"
}
```

This models the distinction between a valid payment request that is declined by the payment domain and a malformed or invalid API request.

## Error Cases

| Condition              | HTTP Status |
| ---------------------- | ----------: |
| Card not found         |         404 |
| Card inactive          |         400 |
| Missing merchant ID    |         422 |
| Invalid request amount |         422 |
| Zero amount            |         422 |

Request-validation errors are handled by FastAPI/Pydantic before the business logic executes.

---

# 3. Authorization Idempotency

Authorization supports the `Idempotency-Key` HTTP request header.

## Header

```http
Idempotency-Key: auth-idempotency-001
```

## Purpose

The idempotency mechanism prevents a client from accidentally creating multiple authorization operations when the same request is retried.

The system stores:

* The idempotency key
* A deterministic request fingerprint
* The original API response

## Same Key + Same Request

Repeating an authorization request using the same idempotency key and the same request payload returns the original response.

Example:

```http
POST /api/v1/transactions/authorize
Idempotency-Key: auth-idempotency-001
```

Request:

```json
{
  "card_id": "card-id",
  "amount": 1000,
  "merchant_id": "merchant-001"
}
```

The second identical request returns the same transaction response.

The transaction is not created twice.

## Same Key + Different Request

Reusing an idempotency key with a different request payload is rejected.

Response:

```text
HTTP 409 Conflict
```

Example response:

```json
{
  "detail": "Idempotency-Key has already been used for a different authorization request"
}
```

## Different Keys

Different idempotency keys represent separate operations.

For example:

```text
auth-idempotency-004
auth-idempotency-005
```

can create separate authorization transactions even when the request payload is otherwise identical.

## No Idempotency Key

Requests without an `Idempotency-Key` preserve the existing non-idempotent behavior.

Repeated requests without a key therefore create separate authorization operations.

## Idempotency Test Coverage

The API regression suite verifies:

* Same key + same request replays the original response
* Same key does not double-charge the card
* Same key + different request returns `409`
* Different keys create separate operations
* Requests without a key preserve non-idempotent behavior

---

# 4. Capture

## Endpoint

```http
POST /api/v1/transactions/{transaction_id}/capture
```

## Purpose

Captures an amount from an existing `AUTHORIZED` transaction.

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

```text
HTTP 200 OK
```

Example:

```json
{
  "transaction_id": "transaction-id",
  "status": "CAPTURED",
  "captured_amount": 50
}
```

## Business Rules

The capture operation is delegated to the `PaymentService`.

The service validates:

* Transaction existence
* Current transaction state
* Capture amount against authorized amount

## Error Cases

| Condition                             | HTTP Status |
| ------------------------------------- | ----------: |
| Transaction not found                 |         404 |
| Capture exceeds authorized amount     |         400 |
| Transaction not in `AUTHORIZED` state |         409 |
| Zero capture amount                   |         422 |
| Negative capture amount               |         422 |

The API tests verify scenarios including:

* Successful capture
* Partial capture
* Capture exceeding authorization
* Nonexistent transaction
* Already-captured transaction
* Declined transaction
* Zero-amount capture

---

# 5. Capture Idempotency

Capture operations support idempotency using the `Idempotency-Key` HTTP request header.

Example:

```http
POST /api/v1/transactions/{transaction_id}/capture
Idempotency-Key: capture-idempotency-001
```

The same key and identical request can safely be retried without performing the capture twice.

The idempotency mechanism distinguishes:

```text
same key + same request
```

from:

```text
same key + different request
```

A key reused for a different capture request results in:

```text
HTTP 409 Conflict
```

The capture regression tests verify:

* Replaying the same capture request
* Preventing duplicate capture
* Rejecting the same key for a different request
* Allowing separate operations with different idempotency keys
* Preserving existing behavior when no idempotency key is supplied

---

# 6. Settlement

## Endpoint

```http
POST /api/v1/transactions/{transaction_id}/settle
```

## Purpose

Moves a successfully captured transaction into the `SETTLED` state.

Settlement represents completion of the simulated payment lifecycle after capture.

## Path Parameters

| Parameter        | Type   | Required | Description           |
| ---------------- | ------ | -------- | --------------------- |
| `transaction_id` | string | Yes      | Transaction to settle |

## Request Body

No request body is required.

## Successful Response

```text
HTTP 200 OK
```

Example:

```json
{
  "transaction_id": "transaction-id",
  "status": "SETTLED",
  "settled_at": "2026-08-12T07:19:35.023052+00:00"
}
```

The settlement timestamp is generated using UTC.

## Business Rules

Settlement is delegated to the `PaymentService`.

A transaction must currently be:

```text
CAPTURED
```

before it can transition to:

```text
SETTLED
```

## Error Cases

| Condition                           | HTTP Status |
| ----------------------------------- | ----------: |
| Transaction not found               |         404 |
| Transaction not in `CAPTURED` state |         409 |
| Already settled transaction         |         409 |

The settlement tests verify successful settlement, invalid states, nonexistent transactions, repeated settlement, and simulated technical failures.

## Settlement Idempotency

Settlement accepts the optional `Idempotency-Key` header.

- Same key and same transaction: the original settlement response is replayed.
- Same key and a different transaction: HTTP 409 Conflict.
- Different keys represent separate requests.
- Without a key, the endpoint retains non-idempotent behavior.

Concurrent requests sharing a key are serialized by a transaction-scoped PostgreSQL advisory lock. The payment mutation and stored response commit in the same database transaction.

---

# 7. Refund

## Endpoint

```http
POST /api/v1/transactions/{transaction_id}/refund
```

## Purpose

Refunds all or part of a settled transaction.

The implementation supports:

* Full refunds
* Partial refunds
* Multiple partial refunds
* Partial refund followed by a final refund

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

```text
HTTP 200 OK
```

Example full refund:

```json
{
  "transaction_id": "transaction-id",
  "refund_id": "refund-d7c3e15e",
  "status": "REFUNDED",
  "remaining_balance": 0
}
```

Example partial refund:

```json
{
  "transaction_id": "transaction-id",
  "refund_id": "refund-d7c3e15e",
  "status": "PARTIALLY_REFUNDED",
  "remaining_balance": 50
}
```

## Refund Rules

A refund is allowed only when the transaction is:

```text
SETTLED
```

or:

```text
PARTIALLY_REFUNDED
```

The total refunded amount cannot exceed the settled amount.

The transaction becomes:

```text
PARTIALLY_REFUNDED
```

while a refundable balance remains.

Once the complete settled amount has been refunded, the transaction becomes:

```text
REFUNDED
```

## Error Cases

| Condition                                  | HTTP Status |
| ------------------------------------------ | ----------: |
| Transaction not found                      |         404 |
| Transaction not settled/refundable         |         409 |
| Refund exceeds remaining refundable amount |         400 |
| Zero refund amount                         |         422 |
| Negative refund amount                     |         422 |
| Fully refunded transaction                 |         409 |

The API test suite verifies:

* Full refunds
* Partial refunds
* Multiple partial refunds
* Excessive refunds
* Invalid transaction states
* Fully refunded transactions
* Zero refunds
* Negative refunds

## Refund Idempotency

Refund accepts the optional `Idempotency-Key` header.

- Same key and same transaction/refund amount: the original response is replayed.
- Same key with a different transaction or refund amount: HTTP 409 Conflict.
- Different keys represent separate requests.
- Without a key, the endpoint retains non-idempotent behavior.

Concurrent requests sharing a key are serialized by a transaction-scoped PostgreSQL advisory lock. The payment mutation and stored response commit in the same database transaction.

---

# 8. Transaction Lookup

## Endpoint

```http
GET /api/v1/transactions/{transaction_id}
```

## Purpose

Retrieves the complete transaction object, including its current status and transaction history.

This endpoint supports:

* API verification
* Dashboard transaction visibility
* Transaction lifecycle inspection
* UI automation
* Future AI failure analysis

## Path Parameters

| Parameter        | Type   | Required | Description            |
| ---------------- | ------ | -------- | ---------------------- |
| `transaction_id` | string | Yes      | Transaction identifier |

## Successful Response

```text
HTTP 200 OK
```

The response is the application's `Transaction` model.

The model contains transaction information such as:

* Transaction identifier
* Card identifier
* Merchant identifier
* Transaction status
* Authorized amount
* Captured amount
* Settled amount
* Refunded amount
* Decline reason, where applicable
* Transaction creation timestamp
* Transaction history

The transaction history provides the lifecycle events used by the dashboard to display transaction progression.

## Error Cases

| Condition             | HTTP Status |
| --------------------- | ----------: |
| Transaction not found |         404 |

---

# 9. Transaction Collection

The dashboard requires a collection-level transaction endpoint to display current gateway activity.

## Endpoint

```http
GET /api/v1/transactions
```

## Purpose

Returns the transactions currently stored by the application.

The endpoint is consumed by the dashboard Transactions page to:

* Display transaction activity
* Calculate transaction counts
* Display transaction status
* Display transaction amounts
* Allow users to select transactions
* Open transaction lifecycle details

The frontend sorts returned transactions by creation time so the newest transactions appear first.

## Empty Response

When no transactions exist, the endpoint returns an empty collection.

Example:

```json
[]
```

The dashboard represents this condition using its:

```text
No transactions yet
```

empty state.

---

# 10. Health / Root Endpoint

## Endpoint

```http
GET /
```

## Purpose

Provides a basic application availability response for local development.

## Successful Response

```text
HTTP 200 OK
```

Example:

```json
{
  "message": "PayGuard AI Mock Payment Gateway is running"
}
```

This endpoint is a simple application liveness response, not a database dependency health/readiness check. PostgreSQL availability must be monitored separately.

---

# Simulated Failure Injection

The Mock Payment Gateway supports deterministic technical-failure simulation in development and test environments only through the:

```http
X-Simulate-Failure
```

request header.

The feature exists to provide controlled failure scenarios for reliability testing and the future AI Root Cause Analysis pipeline.

## Supported Failure Types

### TIMEOUT

Request header:

```http
X-Simulate-Failure: TIMEOUT
```

Response:

```text
HTTP 504 Gateway Timeout
```

Example:

```json
{
  "detail": "Simulated timeout occurred"
}
```

### NETWORK_ERROR

Request header:

```http
X-Simulate-Failure: NETWORK_ERROR
```

Response:

```text
HTTP 502 Bad Gateway
```

Example:

```json
{
  "detail": "Simulated network error"
}
```

### INVALID_RESPONSE

Request header:

```http
X-Simulate-Failure: INVALID_RESPONSE
```

Response:

```text
HTTP 500 Internal Server Error
```

Example:

```json
{
  "detail": "Simulated invalid response"
}
```

These failures are deterministic and therefore suitable for repeatable automated testing.

---

# Request Validation

FastAPI and Pydantic validate request payloads before payment-domain logic is executed.

This provides a distinction between request-validation failures and payment business-rule failures.

## Request Validation Failure

Examples:

* Missing required field
* Invalid field type
* Invalid numeric constraint
* Invalid enum/network value

These are handled by the API validation layer.

## Payment Business Rule Failure

Examples:

* Insufficient funds
* Capture exceeding authorization
* Refund exceeding remaining refundable amount
* Settlement attempted before capture
* Refund attempted before settlement
* Card inactive

These are handled by the payment-domain/service layer and translated into appropriate HTTP responses.

The intended flow is:

```text
HTTP Request
     |
     v
Pydantic Validation
     |
     v
API Layer
     |
     v
Payment Service
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

# Idempotency Architecture

Idempotency records are persisted in PostgreSQL. Each record contains a unique key, deterministic request fingerprint and serialized original response.

For a supplied key, the repository acquires a transaction-scoped PostgreSQL advisory lock. Requests using that key serialize until the current transaction commits or rolls back. The handler then either replays a matching stored response, rejects a fingerprint mismatch with HTTP 409, or executes the mutation and stores the response in the same transaction.

Idempotency covers authorization, capture, settlement and refund. The key remains optional; requests without one are not deduplicated. The unique database constraint is an additional safeguard against duplicate records.

---

# Audit Events

The application stores audit events in PostgreSQL, independently from transaction lifecycle events. AuditService accepts explicit operational fields rather than arbitrary request payloads and applies redaction before persistence.

Audit inserts are serialized into a sequence/hash chain. Each row stores its sequence, previous hash and event hash. Database triggers reject ordinary UPDATE, DELETE and TRUNCATE operations. The admin-protected integrity endpoint verifies sequence continuity and hashes.

This is tamper-evident against ordinary application operations, not immutable against a database owner or superuser able to disable triggers or rewrite the chain.

The audit test suite verifies:

* Authorization audit events
* Declined authorization audit events
* Capture audit events
* Persistence of audit events
* Audit timestamps
* Transaction-based audit lookup
* Correlation-ID-based audit lookup
* Failed-operation audit events
* Audit events without raw sensitive payment payloads

Raw card numbers must not be included in audit-event payloads.

---

# HTTP Status Code Conventions

The current API follows these conventions:

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

The exact validation response body for `422` responses is generated by FastAPI/Pydantic and should not be duplicated manually in this document.

---

# Payment Lifecycle Examples

## Successful Payment

```text
Issue Card
    |
    v
Authorize
    |
    v
Capture
    |
    v
Settle
    |
    v
Refund (optional)
```

Example lifecycle:

```text
CARD CREATED
     |
     v
AUTHORIZED
     |
     v
CAPTURED
     |
     v
SETTLED
     |
     v
REFUNDED
```

---

## Partial Refund Lifecycle

```text
SETTLED
    |
    v
PARTIALLY_REFUNDED
    |
    v
PARTIALLY_REFUNDED
    |
    v
REFUNDED
```

The transaction remains refundable until the total refunded amount reaches the settled amount.

---

## Declined Payment

```text
CARD
 |
 v
AUTHORIZATION
 |
 +---- insufficient funds ----> DECLINED
```

A declined authorization is stored as a transaction rather than treated as an unavailable resource or server failure.

---

# API-to-Service Architecture

The API layer is intentionally kept separate from payment business logic.

```text
┌──────────────────────────────┐
│          FastAPI API         │
│                              │
│ Request validation           │
│ HTTP responses               │
│ HTTP error mapping           │
│ Idempotency handling         │
│ Failure injection            │
└──────────────┬───────────────┘
               |
               v
┌──────────────────────────────┐
│       PaymentService         │
│                              │
│ Authorization                │
│ Capture                      │
│ Settlement                   │
│ Refund                       │
└──────────────┬───────────────┘
               |
               v
┌──────────────────────────────┐
│       Domain / State         │
│                              │
│ Transaction lifecycle        │
│ Business rules               │
│ Domain exceptions            │
└──────────────┬───────────────┘
               |
               v
┌──────────────────────────────┐
│       PostgreSQL Repositories│
│                              │
│ Card / Transaction           │
│ Audit / Idempotency          │
└──────────────┬───────────────┘
               |
               v
┌──────────────────────────────┐
│          PostgreSQL          │
│                              │
│ Cards / Transactions         │
│ Transaction events           │
│ Audit hash chain             │
│ Idempotency records          │
└──────────────────────────────┘
```

The API uses PostgreSQL repositories. The request handler owns the SQLAlchemy transaction; repositories flush but do not commit. Related payment, lifecycle, audit and idempotency writes are committed or rolled back together on the successful mutation paths.

---

# Current Automated Test Coverage

The project currently has an automated regression suite covering:

* API tests
* End-to-end Playwright tests
* Unit tests
* Payment service tests
* State-machine tests
* Audit service tests
* Monetary validation tests

The latest verified pre-documentation CI run is [run #39](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/43557859045), for commit `c1be0651fd3503f12e06061755e39228f32950e0`:

```text
Python unit/API: 142 passed, 1 warning
Playwright Chromium E2E: 6 passed, 2 warnings
Dependency audits: passed
```

The suites run in separate CI jobs. These are the results for run #39, not a claim about the later documentation commit.

## API Coverage

The API suite covers:

* Card issuance
* Authorization
* Authorization idempotency
* Capture
* Capture idempotency
* Settlement idempotency
* Refund idempotency
* Audit behavior
* Simulated technical failures
* Boundary conditions
* Invalid states
* Request validation

## End-to-End Coverage

The current E2E suite covers:

* Dashboard loading
* Card issuance through the UI
* Transactions page loading
* Transactions empty state
* Authorized transaction visibility
* Transaction merchant visibility
* Transaction status visibility
* Transaction lifecycle dialog opening and closing

The E2E tests use Playwright Page Objects and API-backed fixtures to create deterministic transaction state.

---

# OpenAPI Documentation

FastAPI automatically generates the OpenAPI specification from the implemented request models, response models, and route definitions.

Interactive documentation:

```text
http://localhost:8000/docs
```

Raw OpenAPI document:

```text
http://localhost:8000/openapi.json
```

The generated OpenAPI document should be treated as the machine-readable API contract.

Future AI-assisted test generation can consume this specification to identify additional scenarios.

---

# Current API Capabilities

| Capability | Status |
|---|---|
| Card issuance and payment lifecycle | Implemented |
| Authorization idempotency | Implemented |
| Capture idempotency | Implemented |
| Settlement idempotency | Implemented |
| Refund idempotency | Implemented |
| Transaction lookup and collection | Implemented |
| Failure simulation | Implemented in development/test only |
| OpenAPI generation / Swagger UI | Implemented in development/test; disabled in production |
| Payment state machine and service layer | Implemented |
| PostgreSQL repositories and migrations | Implemented |
| Persisted audit events and integrity verification | Implemented |
| Shared service/admin API keys | Implemented |
| Per-user authentication / RBAC | Not implemented |
| Built-in rate limiting | Not implemented; deployment gateway responsibility |
| Webhooks | Planned |
| AI test-case generation | Planned |
| AI Root Cause Analysis | Planned |

---

# Future API Enhancements

The current API intentionally represents a simplified payment gateway.

The following capabilities are candidates for future iterations:

* Per-user identity, RBAC and tenant isolation
* API-key rotation/revocation and external secret management
* Deployment-level rate limiting and network controls
* Webhooks
* Broader currency support and explicit currency metadata
* Production dashboard credential flow
* AI-assisted test generation and root-cause analysis
* Card expiry validation
* Transaction expiration
* Authorization reversal/void
* Multiple capture support
* Persistent refund entities
* Webhook/event simulation
* Optimistic or pessimistic concurrency controls
* Structured error codes
* Comprehensive health and readiness endpoints
* Expanded AI-assisted test-case generation
* AI Root Cause Analysis

These capabilities should be introduced incrementally rather than added merely to increase the apparent complexity of the API.

---

# API Design Principles

The current API follows these principles.

## 1. Payment-domain failures are not generic server failures

For example, insufficient funds result in a valid `DECLINED` transaction rather than a server error.

## 2. Transaction state controls allowed operations

Capture, settlement, and refund operations are constrained by the transaction's current lifecycle state.

## 3. Business logic remains outside the HTTP layer

Payment operations are delegated to the payment service and domain layer where appropriate.

## 4. Validation occurs at the API boundary

Malformed or invalid request payloads are rejected before they reach payment-domain logic.

## 5. Idempotency prevents duplicate operations

Operations that support idempotency can safely replay the original result when clients retry an identical request.

A reused key with a different request is rejected rather than silently creating a different operation.

## 6. The API remains deterministic for testing

Failure injection and controlled test data allow repeatable scenarios for automated regression and future AI-assisted failure analysis.

## 7. Transaction history remains observable

Transaction lifecycle events are exposed through transaction lookup so that downstream consumers such as the dashboard and future automation can inspect payment progression.

## 8. Sensitive payment information is not exposed unnecessarily

Card numbers are represented in masked form, and audit events must not contain raw card numbers.

---

# Current API Validation Summary

The currently verified transaction flow is:

```text
Card Creation
     |
     | HTTP 201
     v
Authorization
     |
     | HTTP 200
     v
Capture
     |
     | HTTP 200
     v
Settlement
     |
     | HTTP 200
     v
Refund
     |
     | HTTP 200
     v
Transaction Lifecycle Completed
```

The transaction lifecycle exposed by the application is:

```text
AUTHORIZED
     |
     v
CAPTURED
     |
     v
SETTLED
     |
     v
REFUNDED
```

Partial refunds introduce the intermediate state:

```text
SETTLED
     |
     v
PARTIALLY_REFUNDED
     |
     v
REFUNDED
```

Declined authorization follows:

```text
AUTHORIZED REQUEST
       |
       | insufficient funds
       v
   DECLINED
```

The API currently provides the simulated payment flow and reliability controls described in this specification. Remaining deployment concerns include per-user identity/RBAC, API-key rotation, HTTPS termination, external secret management and gateway-level rate limiting. AI-assisted failure analysis remains planned. The application does not claim PCI DSS compliance or production payment capability.




## Future scenario-lab API (proposal only)

The following is a product direction, not an implemented API contract. No endpoint names, schemas or response codes should be relied upon until the implementation and runtime OpenAPI validate them.

Candidate API capabilities:
- Create/validate scenario definitions.
- List and retrieve scenario definitions and versions.
- Execute a scenario and obtain a run identifier.
- Inspect run status, steps, assertions and event timeline.
- Replay a recorded run with reproducibility parameters.
- Export JSON/Markdown/HTML evidence.
- Manage synthetic webhook receiver configuration and delivery evidence in an isolated local environment.

The actual runtime-generated OpenAPI in development/test remains authoritative. Proposed scenario endpoints must not be documented as available until implemented and tested.


# 4. Scenario evidence API (Day 8; verified)

Scenario run creation and evidence submission/query endpoints are implemented as a synthetic test-lab boundary:

- POST /api/v1/scenarios/{scenario_id}/versions/{version}/runs creates a pending run tied to a frozen stored definition.
- POST /api/v1/scenario-runs/{run_id}/evidence accepts a terminal ScenarioRunResult for that exact snapshot and run ID. Decimal values in JSON payloads use the tagged form {\"$decimal\":\"10.00\"} to preserve numeric type.
- GET /api/v1/scenario-runs/{run_id}/evidence retrieves ordered step/assertion evidence and the finalized run record.
- GET /api/v1/scenario-runs/{run_id}/timeline retrieves timeline events ordered by sequence.

The evidence write is transactional and rejected once the run is no longer pending. Evidence and timeline tables are append-only to the runtime role. The endpoints do not invoke real payment operations or accept production data.


Day 8 verification: CI run [#99](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45935233245) passed the Python/API job (187 tests, 1 warning), browser E2E job (6 tests, 2 warnings) and dependency audit. Evidence/status commit [#100](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/45935515769) also passed all three jobs. Local execution was not performed in the scheduled environment.


# 5. Scenario-run report API (Day 9; verified)

- GET /api/v1/scenario-runs/{run_id}/report returns schema-version-1 JSON derived from a stored terminal run and its persisted evidence. The report includes scenario/run metadata, the frozen scenario snapshot SHA-256, a summary of step and assertion counts/duration, results and the ordered timeline.
- GET /api/v1/scenario-run-reports/schema/1 returns the JSON Schema for the version-1 report contract. Unsupported versions return 404.

The report endpoint returns 404 for an unknown run and 409 when terminal evidence has not been persisted. It does not rerun the scenario. Decimal values are serialized as strings by the JSON model representation to avoid precision loss. This is synthetic evidence only.


Day 9 verification: CI run [#101](https://github.com/Atharvagarud137/PayGuard-AI/actions/runs/46103670172) passed all three jobs: 192 Python/unit/API tests (1 warning), 6 browser E2E tests (2 warnings) and dependency audits. No local execution was performed.
