
import hashlib
import random
import string
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
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
from app.routes.dashboard import router as dashboard_router
from app.services.audit_service import AuditService
from app.services.payment_service import PaymentService


# ============================================================================
# Application
# ============================================================================

app = FastAPI(
    title="PayGuard AI - Mock Payment Gateway",
    version="1.0.0",
)

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

app.include_router(dashboard_router)


# ============================================================================
# Database / Service Dependencies
# ============================================================================

def get_payment_service(
        db: Session = Depends(get_db),
) -> PaymentService:
    """Create payment repositories sharing the request-scoped session."""
    return PaymentService(
        repository=PostgresTransactionRepository(db),
        card_repository=PostgresCardRepository(db),
    )


def get_audit_service(
        db: Session = Depends(get_db),
) -> AuditService:
    """Create an audit service using the request-scoped session."""
    return AuditService(PostgresAuditRepository(db))


def get_idempotency_repository(
        db: Session = Depends(get_db),
) -> PostgresIdempotencyRepository:
    """Create an idempotency repository using the request-scoped session."""
    return PostgresIdempotencyRepository(db)


# ============================================================================
# Test State Reset
# ============================================================================

@app.post("/api/v1/test/reset")
def reset_test_state(
        db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Reset application state for isolated local and E2E tests.

    This destructive endpoint must not be exposed in production.
    """
    try:
        # Delete dependent records before their parent records.
        db.execute(delete(IdempotencyRecordDB))
        db.execute(delete(AuditEventDB))
        db.execute(delete(TransactionEventDB))
        db.execute(delete(TransactionDB))
        db.execute(delete(CardDB))
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Test state reset successfully"}


# ============================================================================
# Shared Helpers
# ============================================================================

def generate_masked_card_number() -> str:
    """Generate a mock card number that exposes only four digits."""
    digits = "".join(random.choices(string.digits, k=4))
    return f"****-****-****-{digits}"


def get_correlation_id(
        correlation_id: Optional[str],
) -> str:
    """Use the supplied correlation ID or generate a new UUID."""
    if correlation_id and correlation_id.strip():
        return correlation_id.strip()
    return str(uuid.uuid4())


def check_simulated_failure(
        x_simulate_failure: Optional[str],
) -> None:
    """Trigger deterministic failures for failure-handling tests."""
    failure = (
        x_simulate_failure.strip().upper()
        if x_simulate_failure
        else None
    )

    failures = {
        "TIMEOUT": (504, "Simulated timeout occurred"),
        "NETWORK_ERROR": (502, "Simulated network error"),
        "INVALID_RESPONSE": (500, "Simulated invalid response"),
    }

    if failure in failures:
        status_code, detail = failures[failure]
        raise HTTPException(status_code=status_code, detail=detail)


def build_fingerprint(*parts: Any) -> str:
    """Create a stable SHA-256 fingerprint from request fields."""
    normalized = "|".join(str(part) for part in parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_authorization_fingerprint(
        request: AuthorizeRequest,
) -> str:
    return build_fingerprint(
        "authorize",
        request.card_id,
        Decimal(str(request.amount)).normalize(),
        request.merchant_id,
    )


def build_capture_fingerprint(
        transaction_id: str,
        request: CaptureRequest,
) -> str:
    return build_fingerprint(
        "capture",
        transaction_id,
        Decimal(str(request.capture_amount)).normalize(),
    )


def validate_idempotency_key(
        idempotency_key: Optional[str],
        fingerprint: str,
        idempotency_repository: PostgresIdempotencyRepository,
) -> Optional[dict]:
    """
    Return a previous response when a key and fingerprint match.

    Reusing a key for a different request is rejected. This lookup alone
    does not provide race-safe request claiming; that requires atomic
    coordination in the persistence and service layers.
    """
    if not idempotency_key:
        return None

    key = idempotency_key.strip()
    if not key:
        return None

    record = idempotency_repository.get(key)
    if record is None:
        return None

    if record["fingerprint"] != fingerprint:
        raise HTTPException(
            status_code=409,
            detail=(
                "Idempotency-Key has already been used for a "
                "different request"
            ),
        )

    return record["response"]


def store_idempotency_result(
        idempotency_key: Optional[str],
        fingerprint: str,
        response: dict,
        idempotency_repository: PostgresIdempotencyRepository,
) -> None:
    """Persist a completed response for subsequent matching requests."""
    if not idempotency_key or not idempotency_key.strip():
        return

    idempotency_repository.add(
        idempotency_key=idempotency_key.strip(),
        fingerprint=fingerprint,
        response=response,
    )


def record_audit(
        audit_service: AuditService,
        *,
        event_type: AuditEventType,
        action: str,
        outcome: str,
        correlation_id: str,
        transaction_id: Optional[str] = None,
        card_id: Optional[str] = None,
        merchant_id: Optional[str] = None,
        amount: Optional[Any] = None,
        detail: Optional[str] = None,
) -> None:
    """Keep audit creation consistent across API operations."""
    audit_service.record(
        event_type=event_type,
        action=action,
        outcome=outcome,
        correlation_id=correlation_id,
        transaction_id=transaction_id,
        card_id=card_id,
        merchant_id=merchant_id,
        amount=amount,
        detail=detail,
    )


def translate_payment_error(
        exc: Exception,
        *,
        operation: str,
) -> HTTPException:
    """Translate known payment-domain exceptions into HTTP responses."""
    if isinstance(exc, TransactionNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))

    if isinstance(exc, CaptureAmountExceededError):
        return HTTPException(status_code=400, detail=str(exc))

    if isinstance(exc, RefundAmountExceededError):
        return HTTPException(status_code=400, detail=str(exc))

    if isinstance(exc, InvalidTransactionStateError):
        status_code = 400 if operation == "authorize" else 409
        return HTTPException(status_code=status_code, detail=str(exc))

    return HTTPException(
        status_code=500,
        detail="An unexpected payment processing error occurred",
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
        x_simulate_failure: Optional[str] = Header(default=None),
        db: Session = Depends(get_db),
) -> Card:
    """Issue a mock virtual card."""
    check_simulated_failure(x_simulate_failure)

    card_repository = PostgresCardRepository(db)
    card_number = generate_masked_card_number()

    # A unique database constraint remains the final uniqueness guarantee.
    while card_repository.exists_with_number(card_number):
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
    except SQLAlchemyError:
        db.rollback()
        raise

    return card


# ============================================================================
# Authorization
# ============================================================================

@app.post("/api/v1/transactions/authorize")
def authorize_transaction(
        request: AuthorizeRequest,
        x_simulate_failure: Optional[str] = Header(default=None),
        idempotency_key: Optional[str] = Header(
            default=None,
            alias="Idempotency-Key",
        ),
        correlation_id: Optional[str] = Header(
            default=None,
            alias="X-Correlation-ID",
        ),
        db: Session = Depends(get_db),
) -> dict:
    """Authorize a payment against an active card."""
    correlation_id = get_correlation_id(correlation_id)
    check_simulated_failure(x_simulate_failure)

    payment_service = PaymentService(
        PostgresTransactionRepository(db),
        PostgresCardRepository(db),
    )
    audit_service = AuditService(PostgresAuditRepository(db))
    idempotency_repository = PostgresIdempotencyRepository(db)
    fingerprint = build_authorization_fingerprint(request)

    try:
        existing_response = validate_idempotency_key(
            idempotency_key,
            fingerprint,
            idempotency_repository,
        )
        if existing_response is not None:
            db.rollback()
            return existing_response

        transaction = payment_service.authorize(
            card_id=request.card_id,
            amount=Decimal(str(request.amount)),
            merchant_id=request.merchant_id,
        )

        if transaction.status.value == "DECLINED":
            response = {
                "transaction_id": transaction.transaction_id,
                "status": transaction.status,
                "decline_reason": transaction.decline_reason,
            }
            outcome = "DECLINED"
            detail = transaction.decline_reason or "Authorization declined"
        else:
            response = {
                "transaction_id": transaction.transaction_id,
                "status": transaction.status,
                "authorized_amount": transaction.authorized_amount,
            }
            outcome = "SUCCESS"
            detail = "Authorization approved"

        record_audit(
            audit_service,
            event_type=AuditEventType.AUTHORIZATION,
            action="AUTHORIZE",
            outcome=outcome,
            correlation_id=correlation_id,
            transaction_id=transaction.transaction_id,
            card_id=transaction.card_id,
            merchant_id=transaction.merchant_id,
            amount=request.amount,
            detail=detail,
        )

        store_idempotency_result(
            idempotency_key,
            fingerprint,
            response,
            idempotency_repository,
        )
        db.commit()
        return response

    except TransactionNotFoundError as exc:
        db.rollback()
        record_audit(
            audit_service,
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
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    except InvalidTransactionStateError as exc:
        db.rollback()
        record_audit(
            audit_service,
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
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A data conflict occurred while processing authorization",
        ) from exc
    except Exception:
        db.rollback()
        raise


# ============================================================================
# Capture
# ============================================================================

@app.post("/api/v1/transactions/{transaction_id}/capture")
def capture_transaction(
        transaction_id: str,
        request: CaptureRequest,
        x_simulate_failure: Optional[str] = Header(default=None),
        idempotency_key: Optional[str] = Header(
            default=None,
            alias="Idempotency-Key",
        ),
        correlation_id: Optional[str] = Header(
            default=None,
            alias="X-Correlation-ID",
        ),
        db: Session = Depends(get_db),
) -> dict:
    """Capture an authorized transaction."""
    correlation_id = get_correlation_id(correlation_id)
    check_simulated_failure(x_simulate_failure)

    payment_service = PaymentService(
        PostgresTransactionRepository(db),
        PostgresCardRepository(db),
    )
    audit_service = AuditService(PostgresAuditRepository(db))
    idempotency_repository = PostgresIdempotencyRepository(db)
    fingerprint = build_capture_fingerprint(transaction_id, request)

    try:
        existing_response = validate_idempotency_key(
            idempotency_key,
            fingerprint,
            idempotency_repository,
        )
        if existing_response is not None:
            db.rollback()
            return existing_response

        transaction = payment_service.capture(
            transaction_id=transaction_id,
            capture_amount=Decimal(str(request.capture_amount)),
        )

        response = {
            "transaction_id": transaction.transaction_id,
            "status": transaction.status,
            "captured_amount": transaction.captured_amount,
        }

        record_audit(
            audit_service,
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

        store_idempotency_result(
            idempotency_key,
            fingerprint,
            response,
            idempotency_repository,
        )
        db.commit()
        return response

    except (
            TransactionNotFoundError,
            CaptureAmountExceededError,
            InvalidTransactionStateError,
    ) as exc:
        db.rollback()
        record_audit(
            audit_service,
            event_type=AuditEventType.CAPTURE,
            action="CAPTURE",
            outcome="FAILURE",
            correlation_id=correlation_id,
            transaction_id=(
                None
                if isinstance(exc, TransactionNotFoundError)
                else transaction_id
            ),
            amount=request.capture_amount,
            detail=f"Transaction {transaction_id}: {exc}",
        )
        db.commit()
        raise translate_payment_error(exc, operation="capture") from exc

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A data conflict occurred while processing capture",
        ) from exc
    except Exception:
        db.rollback()
        raise


# ============================================================================
# Settlement
# ============================================================================

@app.post("/api/v1/transactions/{transaction_id}/settle")
def settle_transaction(
        transaction_id: str,
        x_simulate_failure: Optional[str] = Header(default=None),
        correlation_id: Optional[str] = Header(
            default=None,
            alias="X-Correlation-ID",
        ),
        db: Session = Depends(get_db),
) -> dict:
    """Settle a captured transaction."""
    correlation_id = get_correlation_id(correlation_id)
    check_simulated_failure(x_simulate_failure)

    payment_service = PaymentService(
        PostgresTransactionRepository(db),
        PostgresCardRepository(db),
    )
    audit_service = AuditService(PostgresAuditRepository(db))

    try:
        transaction = payment_service.settle(transaction_id)

        record_audit(
            audit_service,
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

        response = {
            "transaction_id": transaction.transaction_id,
            "status": transaction.status,
            "settled_at": datetime.now(timezone.utc),
        }
        db.commit()
        return response

    except (TransactionNotFoundError, InvalidTransactionStateError) as exc:
        db.rollback()
        record_audit(
            audit_service,
            event_type=AuditEventType.SETTLEMENT,
            action="SETTLE",
            outcome="FAILURE",
            correlation_id=correlation_id,
            transaction_id=(
                None
                if isinstance(exc, TransactionNotFoundError)
                else transaction_id
            ),
            detail=f"Transaction {transaction_id}: {exc}",
        )
        db.commit()
        raise translate_payment_error(exc, operation="settle") from exc

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A data conflict occurred while processing settlement",
        ) from exc
    except Exception:
        db.rollback()
        raise


# ============================================================================
# Refund
# ============================================================================

@app.post("/api/v1/transactions/{transaction_id}/refund")
def refund_transaction(
        transaction_id: str,
        request: RefundRequest,
        x_simulate_failure: Optional[str] = Header(default=None),
        correlation_id: Optional[str] = Header(
            default=None,
            alias="X-Correlation-ID",
        ),
        db: Session = Depends(get_db),
) -> dict:
    """Refund a settled transaction, either partially or completely."""
    correlation_id = get_correlation_id(correlation_id)
    check_simulated_failure(x_simulate_failure)

    payment_service = PaymentService(
        PostgresTransactionRepository(db),
        PostgresCardRepository(db),
    )
    audit_service = AuditService(PostgresAuditRepository(db))

    try:
        transaction, remaining_after = payment_service.refund(
            transaction_id=transaction_id,
            refund_amount=Decimal(str(request.refund_amount)),
        )

        response = {
            "transaction_id": transaction.transaction_id,
            "refund_id": f"refund-{transaction.transaction_id[:8]}",
            "status": transaction.status,
            "remaining_balance": remaining_after,
        }

        record_audit(
            audit_service,
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

    except (
            TransactionNotFoundError,
            RefundAmountExceededError,
            InvalidTransactionStateError,
    ) as exc:
        db.rollback()
        record_audit(
            audit_service,
            event_type=AuditEventType.REFUND,
            action="REFUND",
            outcome="FAILURE",
            correlation_id=correlation_id,
            transaction_id=(
                None
                if isinstance(exc, TransactionNotFoundError)
                else transaction_id
            ),
            amount=request.refund_amount,
            detail=f"Transaction {transaction_id}: {exc}",
        )
        db.commit()
        raise translate_payment_error(exc, operation="refund") from exc

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A data conflict occurred while processing refund",
        ) from exc
    except Exception:
        db.rollback()
        raise


# ============================================================================
# Transaction Lookup
# ============================================================================

@app.get("/api/v1/transactions/{transaction_id}")
def get_transaction(
        transaction_id: str,
        payment_service: PaymentService = Depends(get_payment_service),
):
    """Retrieve a transaction by its unique identifier."""
    transaction = payment_service.get_transaction(transaction_id)

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    return transaction


# ============================================================================
# Audit Lookup
# ============================================================================

@app.get("/api/v1/audit/transactions/{transaction_id}")
def get_transaction_audit_events(
        transaction_id: str,
        payment_service: PaymentService = Depends(get_payment_service),
        audit_service: AuditService = Depends(get_audit_service),
):
    """Retrieve the operational audit trail for a transaction."""
    transaction = payment_service.get_transaction(transaction_id)

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    return audit_service.list_by_transaction(transaction_id)


@app.get("/api/v1/audit/correlation/{correlation_id}")
def get_correlation_audit_events(
        correlation_id: str,
        audit_service: AuditService = Depends(get_audit_service),
):
    """Retrieve audit events associated with a correlation ID."""
    return audit_service.list_by_correlation_id(correlation_id)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/")
def root() -> dict[str, str]:
    """Return the basic application health status."""
    return {
        "message": "PayGuard AI Mock Payment Gateway is running",
    }
