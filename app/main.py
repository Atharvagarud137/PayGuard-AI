import hashlib
import random
import string
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.database_models import (
    AuditEventDB,
    CardDB,
    IdempotencyRecordDB,
    TransactionDB,
    TransactionEventDB,
)

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
    CaptureRequest,
    RefundRequest,
)

from app.repositories.postgres_audit_repository import (
    PostgresAuditRepository,
)
from app.repositories.postgres_card_repository import (
    PostgresCardRepository,
)
from app.repositories.postgres_idempotency_repository import (
    PostgresIdempotencyRepository,
)
from app.repositories.postgres_transaction_repository import (
    PostgresTransactionRepository,
)

from app.services.audit_service import AuditService
from app.services.payment_service import PaymentService

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
# Database / Service Factory
# ============================================================================

def get_payment_service(
        db: Session = Depends(get_db),
) -> PaymentService:
    """
    Construct a PaymentService using repositories backed by the current
    request-scoped PostgreSQL session.

    The same SQLAlchemy session is shared by the card and transaction
    repositories so payment operations can execute within one database
    transaction.
    """
    transaction_repository = PostgresTransactionRepository(db)
    card_repository = PostgresCardRepository(db)

    return PaymentService(
        repository=transaction_repository,
        card_repository=card_repository,
    )


def get_audit_service(
        db: Session = Depends(get_db),
) -> AuditService:
    """
    Construct an AuditService using the current request-scoped PostgreSQL
    session.
    """
    audit_repository = PostgresAuditRepository(db)

    return AuditService(
        audit_repository,
    )


def get_idempotency_repository(
        db: Session = Depends(get_db),
) -> PostgresIdempotencyRepository:
    """
    Construct the PostgreSQL idempotency repository using the current
    request-scoped database session.
    """
    return PostgresIdempotencyRepository(db)


# ============================================================================
# Test State Reset
# ============================================================================

@app.post("/api/v1/test/reset")
def reset_test_state(
        db: Session = Depends(get_db),
):
    """
    Reset all PostgreSQL application state.

    This endpoint exists exclusively for local E2E test isolation.

    It clears:
        - idempotency records
        - audit events
        - transaction events
        - transactions
        - cards

    Child records are deleted before parent records to satisfy foreign-key
    constraints.

    Do not expose this endpoint in a production deployment.
    """
    try:
        db.execute(
            delete(IdempotencyRecordDB)
        )

        db.execute(
            delete(AuditEventDB)
        )

        db.execute(
            delete(TransactionEventDB)
        )

        db.execute(
            delete(TransactionDB)
        )

        db.execute(
            delete(CardDB)
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "message": "Test state reset successfully",
    }


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

    Decimal values are normalized through their string representation so
    the fingerprint does not depend on binary floating-point formatting.
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
        idempotency_repository: PostgresIdempotencyRepository,
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
        idempotency_repository: PostgresIdempotencyRepository,
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
        idempotency_repository: PostgresIdempotencyRepository,
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
        idempotency_repository: PostgresIdempotencyRepository,
) -> None:
    """
    Store a completed capture result for future replay.
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
            default=None,
        ),
        db: Session = Depends(get_db),
):
    """
    Issue a new virtual card.

    Card persistence is delegated to the PostgreSQL card repository.
    """
    check_simulated_failure(
        x_simulate_failure
    )

    card_repository = PostgresCardRepository(db)

    card_number = generate_masked_card_number()

    while card_repository.exists_with_number(
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

    try:
        card_repository.add(card)
        db.commit()

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Card could not be created because of a data conflict",
        ) from exc

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
            default=None,
        ),
        idempotency_key: Optional[str] = Header(
            default=None,
            alias="Idempotency-Key",
        ),
        correlation_id: Optional[str] = Header(
            default=None,
            alias="X-Correlation-ID",
        ),
        db: Session = Depends(get_db),
):
    """
    Authorize a payment against an active card.

    The PaymentService owns authorization business logic.

    The API layer is responsible for:
        - HTTP request handling
        - Idempotency
        - Correlation IDs
        - Audit recording
        - HTTP error translation
        - Database transaction boundaries
    """
    correlation_id = get_correlation_id(
        correlation_id
    )

    check_simulated_failure(
        x_simulate_failure
    )

    transaction_repository = PostgresTransactionRepository(db)
    card_repository = PostgresCardRepository(db)
    idempotency_repository = PostgresIdempotencyRepository(db)
    audit_repository = PostgresAuditRepository(db)

    payment_service = PaymentService(
        transaction_repository,
        card_repository,
    )

    audit_service = AuditService(
        audit_repository
    )

    # ------------------------------------------------------------------------
    # Idempotency Replay
    # ------------------------------------------------------------------------

    existing_response = validate_idempotency_key(
        idempotency_key=idempotency_key,
        request=request,
        idempotency_repository=idempotency_repository,
    )

    if existing_response is not None:
        db.rollback()
        return existing_response

    # ------------------------------------------------------------------------
    # Authorization Business Operation
    # ------------------------------------------------------------------------

    try:
        transaction = payment_service.authorize(
            card_id=request.card_id,
            amount=Decimal(str(request.amount)),
            merchant_id=request.merchant_id,
        )

    except TransactionNotFoundError as exc:
        audit_service.record(
            event_type=AuditEventType.AUTHORIZATION,
            action="AUTHORIZE",
            outcome="FAILURE",
            correlation_id=correlation_id,
            card_id=request.card_id,
            merchant_id=request.merchant_id,
            amount=request.amount,
            detail=str(exc),
        )

        db.commit()

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except InvalidTransactionStateError as exc:
        audit_service.record(
            event_type=AuditEventType.AUTHORIZATION,
            action="AUTHORIZE",
            outcome="FAILURE",
            correlation_id=correlation_id,
            card_id=request.card_id,
            merchant_id=request.merchant_id,
            amount=request.amount,
            detail=str(exc),
        )

        db.commit()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    # ------------------------------------------------------------------------
    # Declined Authorization
    # ------------------------------------------------------------------------

    if transaction.status.value == "DECLINED":
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
            card_id=transaction.card_id,
            merchant_id=transaction.merchant_id,
            amount=request.amount,
            detail="Insufficient funds",
        )

        store_idempotency_result(
            idempotency_key=idempotency_key,
            request=request,
            response=response,
            idempotency_repository=idempotency_repository,
        )

        db.commit()

        return response

    # ------------------------------------------------------------------------
    # Successful Authorization
    # ------------------------------------------------------------------------

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
        card_id=transaction.card_id,
        merchant_id=transaction.merchant_id,
        amount=request.amount,
        detail="Authorization approved",
    )

    store_idempotency_result(
        idempotency_key=idempotency_key,
        request=request,
        response=response,
        idempotency_repository=idempotency_repository,
    )

    db.commit()

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
            default=None,
        ),
        idempotency_key: Optional[str] = Header(
            default=None,
            alias="Idempotency-Key",
        ),
        correlation_id: Optional[str] = Header(
            default=None,
            alias="X-Correlation-ID",
        ),
        db: Session = Depends(get_db),
):
    """
    Capture an authorized transaction.
    """
    correlation_id = get_correlation_id(
        correlation_id
    )

    check_simulated_failure(
        x_simulate_failure
    )

    transaction_repository = PostgresTransactionRepository(db)
    idempotency_repository = PostgresIdempotencyRepository(db)
    audit_repository = PostgresAuditRepository(db)

    payment_service = PaymentService(
        transaction_repository,
        PostgresCardRepository(db),
    )

    audit_service = AuditService(
        audit_repository
    )

    # ------------------------------------------------------------------------
    # Idempotency Replay
    # ------------------------------------------------------------------------

    existing_response = validate_capture_idempotency_key(
        idempotency_key=idempotency_key,
        transaction_id=transaction_id,
        request=request,
        idempotency_repository=idempotency_repository,
    )

    if existing_response is not None:
        db.rollback()
        return existing_response

    # ------------------------------------------------------------------------
    # Capture Business Operation
    # ------------------------------------------------------------------------

    try:
        transaction = payment_service.capture(
            transaction_id=transaction_id,
            capture_amount=Decimal(
                str(request.capture_amount)
            ),
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

        db.commit()

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

        db.commit()

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

        db.commit()

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    response = {
        "transaction_id": transaction.transaction_id,
        "status": transaction.status,
        "captured_amount": transaction.captured_amount,
    }

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

    store_capture_idempotency_result(
        idempotency_key=idempotency_key,
        transaction_id=transaction_id,
        request=request,
        response=response,
        idempotency_repository=idempotency_repository,
    )

    db.commit()

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
            default=None,
        ),
        correlation_id: Optional[str] = Header(
            default=None,
            alias="X-Correlation-ID",
        ),
        db: Session = Depends(get_db),
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

    payment_service = PaymentService(
        PostgresTransactionRepository(db),
        PostgresCardRepository(db),
    )

    audit_service = AuditService(
        PostgresAuditRepository(db)
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

        db.commit()

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

        db.commit()

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

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

    db.commit()

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
            default=None,
        ),
        correlation_id: Optional[str] = Header(
            default=None,
            alias="X-Correlation-ID",
        ),
        db: Session = Depends(get_db),
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

    payment_service = PaymentService(
        PostgresTransactionRepository(db),
        PostgresCardRepository(db),
    )

    audit_service = AuditService(
        PostgresAuditRepository(db)
    )

    try:
        transaction, remaining_after = payment_service.refund(
            transaction_id=transaction_id,
            refund_amount=Decimal(
                str(request.refund_amount)
            ),
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

        db.commit()

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

        db.commit()

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

        db.commit()

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    response = {
        "transaction_id": transaction.transaction_id,
        "refund_id": f"refund-{transaction.transaction_id[:8]}",
        "status": transaction.status,
        "remaining_balance": remaining_after,
    }

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

    db.commit()

    return response


# ============================================================================
# Transaction Lookup
# ============================================================================

@app.get(
    "/api/v1/transactions/{transaction_id}"
)
def get_transaction(
        transaction_id: str,
        payment_service: PaymentService = Depends(
            get_payment_service,
        ),
):
    """
    Retrieve a transaction by its unique identifier.
    """
    transaction = payment_service.get_transaction(
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
        payment_service: PaymentService = Depends(
            get_payment_service,
        ),
        audit_service: AuditService = Depends(
            get_audit_service,
        ),
):
    """
    Retrieve the audit trail associated with a transaction.

    This endpoint exposes operational audit metadata only. It does not
    expose raw card numbers, authentication credentials, or request
    payloads.
    """
    transaction = payment_service.get_transaction(
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
        audit_service: AuditService = Depends(
            get_audit_service,
        ),
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
        "message": "PayGuard AI Mock Payment Gateway is running",
    }