# API_SPEC.md — PayGuard AI Mock Payment Gateway

## Purpose

This document defines the REST API endpoints for the Mock Payment Gateway, covering the full transaction lifecycle: card issuance, authorization, capture, settlement, and refund. This spec drives both the FastAPI implementation and the test suites (API, UI, and AI-generated test cases).

## Base URL

https://localhost:8000/api/v1

## Supported Card Networks

VISA, Mastercard, Generic (a configurable third network for testing network-specific rule variations)

## 1. Card Issuance

**Endpoint:** `POST /cards`

**Purpose:** Creates a new virtual card record for use in subsequent transactions.

| Field | Type | Required | Description |
|---|---|---|---|
| cardholder_name | string | Yes | Name on the card |
| network | string | Yes | One of: VISA, MASTERCARD, GENERIC |
| initial_balance | number | Yes | Starting available balance |
| expiry_date | string | Yes | Format: MM/YY |

**Response Fields**

| Field | Type | Description |
|---|---|---|
| card_id | string | Unique identifier for the card |
| card_number | string | Masked card number (e.g., ****-****-****-1234) |
| status | string | ACTIVE by default |
| created_at | timestamp | Creation time |

**Error Cases:** Missing required fields (400), invalid network type (400), duplicate card detection (409)

## 2. Authorization

**Endpoint:** `POST /transactions/authorize`

**Purpose:** Places a hold on funds for a purchase, checking balance sufficiency.

| Field | Type | Required | Description |
|---|---|---|---|
| card_id | string | Yes | Card being charged |
| amount | number | Yes | Amount to authorize |
| merchant_id | string | Yes | Identifier of the merchant |

**Response Fields**

| Field | Type | Description |
|---|---|---|
| transaction_id | string | Unique transaction identifier |
| status | string | APPROVED or DECLINED |
| decline_reason | string | Populated only if declined (e.g., INSUFFICIENT_FUNDS) |
| authorized_amount | number | Amount held |

**Error Cases:** Card not found (404), card inactive/expired (400), insufficient balance (200 with DECLINED status, not a 4xx — mirrors real payment network behavior)

## 3. Capture

**Endpoint:** `POST /transactions/{transaction_id}/capture`

**Purpose:** Confirms and captures a previously authorized amount, finalizing the charge.

| Field | Type | Required | Description |
|---|---|---|---|
| capture_amount | number | Yes | Amount to capture (must be ≤ authorized amount) |

**Response Fields**

| Field | Type | Description |
|---|---|---|
| transaction_id | string | Same as authorization transaction |
| status | string | CAPTURED |
| captured_amount | number | Final captured amount |

**Error Cases:** Transaction not found (404), capture amount exceeds authorized amount (400), transaction already captured (409), capture of zero or negative amount (400)

## 4. Settlement

**Endpoint:** `POST /transactions/{transaction_id}/settle`

**Purpose:** Simulates end-of-day batch settlement, moving funds from capture to settled state.

**Response Fields**

| Field | Type | Description |
|---|---|---|
| transaction_id | string | Transaction being settled |
| status | string | SETTLED |
| settled_at | timestamp | Time of settlement |

**Error Cases:** Transaction not in CAPTURED state (409), transaction already settled (409), simulated settlement timeout (504, used to test AI RCA timeout detection)

## 5. Refund

**Endpoint:** `POST /transactions/{transaction_id}/refund`

**Purpose:** Refunds a settled transaction, fully or partially.

| Field | Type | Required | Description |
|---|---|---|---|
| refund_amount | number | Yes | Amount to refund (must be ≤ settled amount) |

**Response Fields**

| Field | Type | Description |
|---|---|---|
| transaction_id | string | Original transaction reference |
| refund_id | string | Unique refund identifier |
| status | string | REFUNDED or PARTIALLY_REFUNDED |
| remaining_balance | number | Amount still available to refund, if partial |

**Error Cases:** Transaction not settled (409), refund exceeds settled amount (400), refund of already fully-refunded transaction (409)

## 6. Transaction Lookup (Supporting Endpoint)

**Endpoint:** `GET /transactions/{transaction_id}`

**Purpose:** Retrieves full transaction history and current status — used by both the Dashboard and test suites to verify state transitions.

**Response Fields**

| Field | Type | Description |
|---|---|---|
| transaction_id | string | Transaction identifier |
| card_id | string | Associated card |
| status | string | Current status (AUTHORIZED, CAPTURED, SETTLED, REFUNDED, DECLINED) |
| history | list | Chronological list of status changes with timestamps |

## Status Lifecycle

AUTHORIZED → CAPTURED → SETTLED → REFUNDED (or PARTIALLY_REFUNDED)
↘ DECLINED (terminal state, from AUTHORIZED step only)

## Auto-Generated Documentation

FastAPI automatically exposes interactive API documentation at `/docs` (Swagger UI) and the raw OpenAPI spec at `/openapi.json`. The AI Test Case Generator will consume this OpenAPI spec directly to propose additional edge cases.

## Simulated Failure Injection (For Testing AI RCA)

To generate realistic failure scenarios for the AI RCA Engine to analyze, the mock gateway will support a special header, `X-Simulate-Failure`, accepted on any endpoint, with values such as TIMEOUT, NETWORK_ERROR, or INVALID_RESPONSE — allowing controlled, repeatable failure testing.