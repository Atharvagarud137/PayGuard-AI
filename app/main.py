import hashlib
import random
import string
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.domain.exceptions import (
    CaptureAmountExceededError,
    InvalidTransactionStateError,
    RefundAmountExceededError,
    TransactionNotFoundError,
)

from app.models import (
    AuditEventType,
    AuthorizeRequest,
    Card,
    CardCreateRequest,
    CardStatus,
    CaptureRequest,
    RefundRequest,
    Transaction,
    TransactionEvent,
    TransactionStatus,
)

from app.repositories.audit_repository import AuditRepository
from app.repositories.idempotency_repository import IdempotencyRepository
from app.repositories.transaction_repository import TransactionRepository

from app.services.audit_service import AuditService
from app.services.payment_service import PaymentService

from app.storage import storage

from app.routes.dashboard import router as dashboard_router


# ============================================================================
# Application
# ============================================================================

app = FastAPI(
    title="PayGuard AI - Mock Payment Gateway",
    version="1.0.0",
)


# ============================================================================
# CORS Configuration
# ============================================================================

# The React dashboard runs on localhost:5173 while the FastAPI backend
# runs on 127.0.0.1:8000. These are different browser origins, so the
# backend explicitly allows the dashboard to make API requests.

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Routers
# ============================================================================

app.include_router(dashboard_router)


# ============================================================================
# Repositories and Services
# ============================================================================

transaction_repository = TransactionRepository(
    storage
)

payment_service = PaymentService(
    transaction_repository
)

idempotency_repository = IdempotencyRepository(
    storage
)

audit_repository = AuditRepository(
    storage
)

audit_service = AuditService(
    audit_repository
)


# ============================================================================
# Helper Functions
# ============================================================================

def generate_masked_card_number() -> str:
    """
    Generate a masked card number for the mock payment gateway.

    Only the final four digits are exposed because this project simulates
    payment-domain behavior without handling real PAN data.
    """

    digits = "".join(
        random.choices(
            string.digits,
            k=4,
        )
    )

    return f"****-****-****-{digits}"


def get_correlation_id(
        correlation_id: Optional[str],
) -> str:
    """
    Return the supplied correlation ID or generate one.

    Correlation IDs allow related operations to be traced across the
    application without exposing sensitive payment information.
    """

    if correlation_id:
        return correlation_id

    return str(uuid.uuid4())


def check_simulated_failure(
        x_simulate_failure: Optional[str],
) -> None:
    """
    Trigger deterministic failures for AI RCA and failure-handling tests.

    Supported values:

        TIMEOUT
        NETWORK_ERROR
        INVALID_RESPONSE
    """

    if x_simulate_failure == "TIMEOUT":
        raise HTTPException(
            status_code=504,
            detail="Simulated timeout occurred",
        )

    if x_simulate_failure == "NETWORK_ERROR":
        raise HTTPException(
            status_code=502,
            detail="Simulated network error",
        )

    if x_simulate_failure == "INVALID_RESPONSE":
        raise HTTPException(
            status_code=500,
            detail="Simulated invalid response",
        )


# ============================================================================
# Authorization Idempotency
# ============================================================================

def build_authorization_fingerprint(
        request: AuthorizeRequest,
) -> str:
    """
    Build a deterministic fingerprint for an authorization request.

    The fingerprint represents the request fields that determine the
    authorization operation.

    Decimal values are converted to strings so the fingerprint does not
    depend on floating-point representation.
    """

    normalized_request = (
        f"card_id={request.card_id}|"
        f"amount={request.amount}|"
        f"merchant_id={request.merchant_id}"
    )

    return hashlib.sha256(
        normalized_request.encode("utf-8")
    ).hexdigest()


def validate_idempotency_key(
        idempotency_key: Optional[str],
        request: AuthorizeRequest,
) -> Optional[dict]:
    """
    Validate and retrieve an existing authorization idempotency record.

    Returns:
        Previously stored response when the request can be replayed.

    Raises:
        HTTPException(409):
            When the same idempotency key is reused for a different
            authorization request.
    """

    if not idempotency_key:
        return None

    fingerprint = build_authorization_fingerprint(
        request
    )

    record = idempotency_repository.get(
        idempotency_key
    )

    if record is None:
        return None

    if record["fingerprint"] != fingerprint:
        raise HTTPException(
            status_code=409,
            detail=(
                "Idempotency-Key has already been used for a different "
                "authorization request"
            ),
        )

    return record["response"]


def store_idempotency_result(
        idempotency_key: Optional[str],
        request: AuthorizeRequest,
        response: dict,
) -> None:
    """
    Store a completed authorization result for future replay.

    Technical failures are raised before this function is called, so they
    are intentionally not stored as completed idempotent operations.
    """

    if not idempotency_key:
        return

    fingerprint = build_authorization_fingerprint(
        request
    )

    idempotency_repository.add(
        idempotency_key=idempotency_key,
        fingerprint=fingerprint,
        response=response,
    )


# ============================================================================
# Capture Idempotency
# ============================================================================

def build_capture_fingerprint(
        transaction_id: str,
        request: CaptureRequest,
) -> str:
    """
    Build a deterministic fingerprint for a capture request.

    The fingerprint represents the transaction and capture amount that
    determine the capture operation.
    """

    normalized_request = (
        f"transaction_id={transaction_id}|"
        f"capture_amount={request.capture_amount}"
    )

    return hashlib.sha256(
        normalized_request.encode("utf-8")
    ).hexdigest()


def validate_capture_idempotency_key(
        idempotency_key: Optional[str],
        transaction_id: str,
        request: CaptureRequest,
) -> Optional[dict]:
    """
    Validate and retrieve an existing capture idempotency record.

    Returns:
        Previously stored response when the request can be replayed.

    Raises:
        HTTPException(409):
            When the same idempotency key is reused for a different
            capture request.
    """

    if not idempotency_key:
        return None

    fingerprint = build_capture_fingerprint(
        transaction_id=transaction_id,
        request=request,
    )

    record = idempotency_repository.get(
        idempotency_key
    )

    if record is None:
        return None

    if record["fingerprint"] != fingerprint:
        raise HTTPException(
            status_code=409,
            detail=(
                "Idempotency-Key has already been used for a different "
                "capture request"
            ),
        )

    return record["response"]


def store_capture_idempotency_result(
        idempotency_key: Optional[str],
        transaction_id: str,
        request: CaptureRequest,
        response: dict,
) -> None:
    """
    Store a completed capture result for future replay.

    Technical and business failures are raised before this function is
    called, so failed capture operations are not stored as completed
    idempotent operations.
    """

    if not idempotency_key:
        return

    fingerprint = build_capture_fingerprint(
        transaction_id=transaction_id,
        request=request,
    )

    idempotency_repository.add(
        idempotency_key=idempotency_key,
        fingerprint=fingerprint,
        response=response,
    )


# ============================================================================
# Card Issuance
# ============================================================================

@app.post(
    "/api/v1/cards",
    response_model=Card,
    status_code=201,
)
def issue_card(
        request: CardCreateRequest,
        x_simulate_failure: Optional[str] = Header(
            default=None
        ),
):
    """
    Issue a new virtual card.

    Card persistence currently uses the shared in-memory storage.
    """

    check_simulated_failure(
        x_simulate_failure
    )

    card_number = generate_masked_card_number()

    while storage.card_exists_with_number(
            card_number
    ):
        card_number = generate_masked_card_number()

    card = Card(
        cardholder_name=request.cardholder_name,
        card_number=card_number,
        network=request.network,
        balance=request.initial_balance,
        expiry_date=request.expiry_date,
    )

    storage.add_card(
        card
    )

    return card


# ============================================================================
# Authorization
# ============================================================================

@app.post(
    "/api/v1/transactions/authorize"
)
def authorize_transaction(
        request: AuthorizeRequest,
        x_simulate_failure: Optional[str] = Header(
            default=None
        ),
        idempotency_key: Optional[str] = Header(
            default=None,
            alias="Idempotency-Key",
        ),
        correlation_id: Optional[str] = Header(
            default=None,
            alias="X-Correlation-ID",
        ),
):
    """
    Authorize a payment against an active card.

    Idempotency behavior:

        - A new Idempotency-Key processes the authorization normally.
        - Reusing the same key with the same request replays the original
          response.
        - Reusing the same key with a different request returns HTTP 409.
        - Omitting the key preserves the existing non-idempotent behavior.

    Audit behavior:

        - Successful authorization creates an audit event.
        - Declined authorization creates an audit event.
        - Business validation failures create an audit event.
        - Idempotent replay does not create another payment operation.

    Technical failures are evaluated before idempotency processing.
    """

    correlation_id = get_correlation_id(
        correlation_id
    )

    check_simulated_failure(
        x_simulate_failure
    )

    # ------------------------------------------------------------------------
    # Idempotency Replay
    # ------------------------------------------------------------------------

    existing_response = validate_idempotency_key(
        idempotency_key=idempotency_key,
        request=request,
    )

    if existing_response is not None:
        return existing_response

    # ------------------------------------------------------------------------
    # Card Validation
    # ------------------------------------------------------------------------

    card = storage.get_card(
        request.card_id
    )

    if not card:
        audit_service.record(
            event_type=AuditEventType.AUTHORIZATION,
            action="AUTHORIZE",
            outcome="FAILURE",
            correlation_id=correlation_id,
            card_id=request.card_id,
            merchant_id=request.merchant_id,
            amount=request.amount,
            detail="Card not found",
        )

        raise HTTPException(
            status_code=404,
            detail="Card not found",
        )

    if card.status != CardStatus.ACTIVE:
        audit_service.record(
            event_type=AuditEventType.AUTHORIZATION,
            action="AUTHORIZE",
            outcome="FAILURE",
            correlation_id=correlation_id,
            card_id=request.card_id,
            merchant_id=request.merchant_id,
            amount=request.amount,
            detail="Card is not active",
        )

        raise HTTPException(
            status_code=400,
            detail="Card is not active",
        )

    # ------------------------------------------------------------------------
    # Authorization Decision
    # ------------------------------------------------------------------------

    if card.balance < request.amount:
        transaction = Transaction(
            card_id=request.card_id,
            merchant_id=request.merchant_id,
            status=TransactionStatus.DECLINED,
            decline_reason="INSUFFICIENT_FUNDS",
        )

        transaction.history.append(
            TransactionEvent(
                status=TransactionStatus.DECLINED,
                detail="Insufficient funds",
            )
        )

        transaction_repository.add(
            transaction
        )

        response = {
            "transaction_id": transaction.transaction_id,
            "status": transaction.status,
            "decline_reason": transaction.decline_reason,
        }

        audit_service.record(
            event_type=AuditEventType.AUTHORIZATION,
            action="AUTHORIZE",
            outcome="DECLINED",
            correlation_id=correlation_id,
            transaction_id=transaction.transaction_id,
            card_id=request.card_id,
            merchant_id=request.merchant_id,
            amount=request.amount,
            detail="Insufficient funds",
        )

        store_idempotency_result(
            idempotency_key=idempotency_key,
            request=request,
            response=response,
        )

        return response

    # ------------------------------------------------------------------------
    # Successful Authorization
    # ------------------------------------------------------------------------

    card.balance -= request.amount

    storage.update_card(
        card
    )

    transaction = Transaction(
        card_id=request.card_id,
        merchant_id=request.merchant_id,
        authorized_amount=request.amount,
        status=TransactionStatus.AUTHORIZED,
    )

    transaction.history.append(
        TransactionEvent(
            status=TransactionStatus.AUTHORIZED,
            detail="Authorization approved",
        )
    )

    transaction_repository.add(
        transaction
    )

    response = {
        "transaction_id": transaction.transaction_id,
        "status": transaction.status,
        "authorized_amount": transaction.authorized_amount,
    }

    audit_service.record(
        event_type=AuditEventType.AUTHORIZATION,
        action="AUTHORIZE",
        outcome="SUCCESS",
        correlation_id=correlation_id,
        transaction_id=transaction.transaction_id,
        card_id=request.card_id,
        merchant_id=request.merchant_id,
        amount=request.amount,
        detail="Authorization approved",
    )

    store_idempotency_result(
        idempotency_key=idempotency_key,
        request=request,
        response=response,
    )

    return response


# ============================================================================
# Capture
# ============================================================================

@app.post(
    "/api/v1/transactions/{transaction_id}/capture"
)
def capture_transaction(
        transaction_id: str,
        request: CaptureRequest,
        x_simulate_failure: Optional[str] = Header(
            default=None
        ),
        idempotency_key: Optional[str] = Header(
            default=None,
            alias="Idempotency-Key",
        ),
        correlation_id: Optional[str] = Header(
            default=None,
            alias="X-Correlation-ID",
        ),
):
    """
    Capture an authorized transaction.

    Idempotency behavior:

        - A new Idempotency-Key processes the capture normally.
        - Reusing the same key with the same transaction and amount
          replays the original response.
        - Reusing the same key with a different capture request returns
          HTTP 409.
        - Omitting the key preserves the existing non-idempotent behavior.
    """

    correlation_id = get_correlation_id(
        correlation_id
    )

    check_simulated_failure(
        x_simulate_failure
    )

    # ------------------------------------------------------------------------
    # Idempotency Replay
    # ------------------------------------------------------------------------

    existing_response = validate_capture_idempotency_key(
        idempotency_key=idempotency_key,
        transaction_id=transaction_id,
        request=request,
    )

    if existing_response is not None:
        return existing_response

    # ------------------------------------------------------------------------
    # Capture Business Operation
    # ------------------------------------------------------------------------

    try:
        transaction = payment_service.capture(
            transaction_id=transaction_id,
            capture_amount=request.capture_amount,
        )

    except TransactionNotFoundError as exc:

        audit_service.record(
            event_type=AuditEventType.CAPTURE,
            action="CAPTURE",
            outcome="FAILURE",
            correlation_id=correlation_id,
            transaction_id=transaction_id,
            amount=request.capture_amount,
            detail=str(exc),
        )

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except CaptureAmountExceededError as exc:

        audit_service.record(
            event_type=AuditEventType.CAPTURE,
            action="CAPTURE",
            outcome="FAILURE",
            correlation_id=correlation_id,
            transaction_id=transaction_id,
            amount=request.capture_amount,
            detail=str(exc),
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except InvalidTransactionStateError as exc:

        audit_service.record(
            event_type=AuditEventType.CAPTURE,
            action="CAPTURE",
            outcome="FAILURE",
            correlation_id=correlation_id,
            transaction_id=transaction_id,
            amount=request.capture_amount,
            detail=str(exc),
        )

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    # ------------------------------------------------------------------------
    # API Response
    # ------------------------------------------------------------------------

    response = {
        "transaction_id": transaction.transaction_id,
        "status": transaction.status,
        "captured_amount": transaction.captured_amount,
    }

    # ------------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------------

    audit_service.record(
        event_type=AuditEventType.CAPTURE,
        action="CAPTURE",
        outcome="SUCCESS",
        correlation_id=correlation_id,
        transaction_id=transaction.transaction_id,
        card_id=transaction.card_id,
        merchant_id=transaction.merchant_id,
        amount=request.capture_amount,
        detail="Capture successful",
    )

    # ------------------------------------------------------------------------
    # Store Idempotency Result
    # ------------------------------------------------------------------------

    store_capture_idempotency_result(
        idempotency_key=idempotency_key,
        transaction_id=transaction_id,
        request=request,
        response=response,
    )

    return response


# ============================================================================
# Settlement
# ============================================================================

@app.post(
    "/api/v1/transactions/{transaction_id}/settle"
)
def settle_transaction(
        transaction_id: str,
        x_simulate_failure: Optional[str] = Header(
            default=None
        ),
        correlation_id: Optional[str] = Header(
            default=None,
            alias="X-Correlation-ID",
        ),
):
    """
    Settle a captured transaction.
    """

    correlation_id = get_correlation_id(
        correlation_id
    )

    check_simulated_failure(
        x_simulate_failure
    )

    try:
        transaction = payment_service.settle(
            transaction_id=transaction_id,
        )

    except TransactionNotFoundError as exc:

        audit_service.record(
            event_type=AuditEventType.SETTLEMENT,
            action="SETTLE",
            outcome="FAILURE",
            correlation_id=correlation_id,
            transaction_id=transaction_id,
            detail=str(exc),
        )

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except InvalidTransactionStateError as exc:

        audit_service.record(
            event_type=AuditEventType.SETTLEMENT,
            action="SETTLE",
            outcome="FAILURE",
            correlation_id=correlation_id,
            transaction_id=transaction_id,
            detail=str(exc),
        )

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    # ------------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------------

    audit_service.record(
        event_type=AuditEventType.SETTLEMENT,
        action="SETTLE",
        outcome="SUCCESS",
        correlation_id=correlation_id,
        transaction_id=transaction.transaction_id,
        card_id=transaction.card_id,
        merchant_id=transaction.merchant_id,
        amount=transaction.settled_amount,
        detail="Settlement successful",
    )

    return {
        "transaction_id": transaction.transaction_id,
        "status": transaction.status,
        "settled_at": datetime.now(timezone.utc),
    }


# ============================================================================
# Refund
# ============================================================================

@app.post(
    "/api/v1/transactions/{transaction_id}/refund"
)
def refund_transaction(
        transaction_id: str,
        request: RefundRequest,
        x_simulate_failure: Optional[str] = Header(
            default=None
        ),
        correlation_id: Optional[str] = Header(
            default=None,
            alias="X-Correlation-ID",
        ),
):
    """
    Refund a settled transaction either partially or completely.
    """

    correlation_id = get_correlation_id(
        correlation_id
    )

    check_simulated_failure(
        x_simulate_failure
    )

    try:
        transaction, remaining_after = payment_service.refund(
            transaction_id=transaction_id,
            refund_amount=request.refund_amount,
        )

    except TransactionNotFoundError as exc:

        audit_service.record(
            event_type=AuditEventType.REFUND,
            action="REFUND",
            outcome="FAILURE",
            correlation_id=correlation_id,
            transaction_id=transaction_id,
            amount=request.refund_amount,
            detail=str(exc),
        )

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except RefundAmountExceededError as exc:

        audit_service.record(
            event_type=AuditEventType.REFUND,
            action="REFUND",
            outcome="FAILURE",
            correlation_id=correlation_id,
            transaction_id=transaction_id,
            amount=request.refund_amount,
            detail=str(exc),
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except InvalidTransactionStateError as exc:

        audit_service.record(
            event_type=AuditEventType.REFUND,
            action="REFUND",
            outcome="FAILURE",
            correlation_id=correlation_id,
            transaction_id=transaction_id,
            amount=request.refund_amount,
            detail=str(exc),
        )

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    # ------------------------------------------------------------------------
    # API Response
    # ------------------------------------------------------------------------

    response = {
        "transaction_id": transaction.transaction_id,
        "refund_id": f"refund-{transaction.transaction_id[:8]}",
        "status": transaction.status,
        "remaining_balance": remaining_after,
    }

    # ------------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------------

    audit_service.record(
        event_type=AuditEventType.REFUND,
        action="REFUND",
        outcome="SUCCESS",
        correlation_id=correlation_id,
        transaction_id=transaction.transaction_id,
        card_id=transaction.card_id,
        merchant_id=transaction.merchant_id,
        amount=request.refund_amount,
        detail="Refund successful",
    )

    return response


# ============================================================================
# Transaction Lookup
# ============================================================================

@app.get(
    "/api/v1/transactions/{transaction_id}"
)
def get_transaction(
        transaction_id: str,
):
    """
    Retrieve a transaction by its unique identifier.
    """

    transaction = transaction_repository.get(
        transaction_id
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    return transaction


# ============================================================================
# Audit Lookup
# ============================================================================

@app.get(
    "/api/v1/audit/transactions/{transaction_id}"
)
def get_transaction_audit_events(
        transaction_id: str,
):
    """
    Retrieve the audit trail associated with a transaction.

    This endpoint exposes operational audit metadata only. It does not
    expose raw card numbers, authentication credentials, or request
    payloads.
    """

    transaction = transaction_repository.get(
        transaction_id
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    return audit_service.list_by_transaction(
        transaction_id
    )


@app.get(
    "/api/v1/audit/correlation/{correlation_id}"
)
def get_correlation_audit_events(
        correlation_id: str,
):
    """
    Retrieve audit events associated with a correlation ID.
    """

    return audit_service.list_by_correlation_id(
        correlation_id
    )


# ============================================================================
# Health Check
# ============================================================================

@app.get("/")
def root():
    """
    Basic application health endpoint.
    """

    return {
        "message": "PayGuard AI Mock Payment Gateway is running"
    }