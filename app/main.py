import hashlib
import logging
import random
import secrets
import string
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import delete, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
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
from app.security import (
    RedactingFilter,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
)


# ============================================================================
# Application
# ============================================================================

def require_service_access(
        x_api_key: Optional[str] = Header(
            default=None,
            alias="X-API-Key",
        ),
) -> None:
    """Require the service key for business and dashboard API access."""
    expected = settings.service_api_key

    # Local development and isolated tests may run without a shared key.
    if settings.environment in {"development", "test"} and expected is None:
        return

    if expected is None:
        raise HTTPException(
            status_code=503,
            detail="Service API access is not configured",
        )

    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid service credentials",
            headers={"WWW-Authenticate": "ApiKey"},
        )


logger = logging.getLogger("payguard")
logger.addFilter(RedactingFilter())

app = FastAPI(
    title="PayGuard AI - Mock Payment Gateway",
    version="1.0.0",
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)

allowed_headers = [
    "Content-Type",
    "Idempotency-Key",
    "X-Correlation-ID",
    "X-API-Key",
    "X-Admin-API-Key",
    "X-Test-Reset-Token",
]
if settings.failure_simulation_enabled:
    allowed_headers.append("X-Simulate-Failure")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=allowed_headers,
    max_age=600,
)
app.add_middleware(
    RequestSizeLimitMiddleware,
    max_bytes=settings.max_request_bytes,
)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(
    dashboard_router,
    dependencies=[Depends(require_service_access)],
)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
) -> JSONResponse:
    """Return validation details without echoing submitted field values."""
    safe_errors = [
        {
            "loc": list(error.get("loc", ())),
            "msg": error.get("msg", "Invalid request"),
            "type": error.get("type", "value_error"),
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"detail": safe_errors},
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(
        request: Request,
        exc: Exception,
) -> JSONResponse:
    """Log only safe error metadata and return a generic client response."""
    route = request.scope.get("route")
    route_template = getattr(route, "path", "unmatched")
    logger.error(
        "Unhandled application error type=%s route=%s",
        type(exc).__name__,
        route_template,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


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

def reset_test_state(
        db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Reset application state for isolated local and E2E tests.

    This destructive endpoint must not be exposed in production.
    """
    try:
        # The destructive reset route exists only in explicitly enabled
        # test mode. This transaction-local flag is the sole delete exception
        # in the PostgreSQL append-only audit trigger.
        db.execute(
            text(
                "SELECT set_config("
                "'payguard.allow_audit_delete', 'on', true)"
                ")"
            )
        )

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

def require_test_reset_token(
        x_test_reset_token: Optional[str] = Header(
            default=None,
            alias="X-Test-Reset-Token",
        ),
) -> None:
    """Require the dedicated token for the destructive test-only endpoint."""
    expected = settings.test_reset_token
    if (
        settings.environment != "test"
        or not settings.enable_test_endpoints
        or expected is None
    ):
        raise HTTPException(status_code=404, detail="Not found")

    if (
        not x_test_reset_token
        or not secrets.compare_digest(x_test_reset_token, expected)
    ):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid test reset credentials",
            headers={"WWW-Authenticate": "ApiKey"},
        )


# Register the destructive helper only when explicitly enabled in test mode.
if settings.enable_test_endpoints:
    app.post(
        "/api/v1/test/reset",
        dependencies=[Depends(require_test_reset_token)],
    )(reset_test_state)

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
        value = correlation_id.strip()
        if len(value) > 128:
            raise HTTPException(
                status_code=422,
                detail="X-Correlation-ID must be 128 characters or fewer",
            )
        return value
    return str(uuid.uuid4())


def check_simulated_failure(
        x_simulate_failure: Optional[str],
) -> None:
    """Trigger deterministic failures for failure-handling tests."""
    if not x_simulate_failure:
        return

    if not settings.failure_simulation_enabled:
        raise HTTPException(
            status_code=403,
            detail="Failure simulation is disabled in this environment",
        )

    failure = x_simulate_failure.strip().upper()

    failures = {
        "TIMEOUT": (504, "Simulated timeout occurred"),
        "NETWORK_ERROR": (502, "Simulated network error"),
        "INVALID_RESPONSE": (500, "Simulated invalid response"),
    }

    if failure in failures:
        status_code, detail = failures[failure]
        raise HTTPException(status_code=status_code, detail=detail)


def build_fingerprint(*parts: Any) -> str:
    """
    Create a stable SHA-256 fingerprint for payment request fields.

    Keep the established encoding so completed authorization and capture
    records created by earlier versions remain replayable after deployment.
    """
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


def build_settlement_fingerprint(transaction_id: str) -> str:
    return build_fingerprint("settlement", transaction_id)


def build_refund_fingerprint(
        transaction_id: str,
        request: RefundRequest,
) -> str:
    return build_fingerprint(
        "refund",
        transaction_id,
        Decimal(str(request.refund_amount)).normalize(),
    )


def validate_idempotency_key(
        idempotency_key: Optional[str],
        fingerprint: str,
        idempotency_repository: PostgresIdempotencyRepository,
) -> Optional[dict]:
    """
    Serialize requests sharing a key, then return a matching prior response.

    The PostgreSQL transaction-scoped advisory lock is held until the
    caller commits or rolls back the payment operation and its replay record.
    """
    if not idempotency_key:
        return None

    key = idempotency_key.strip()
    if not key:
        return None

    if len(key) > 255:
        raise HTTPException(
            status_code=422,
            detail="Idempotency-Key must be 255 characters or fewer",
        )

    idempotency_repository.claim(key)
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
        # Keep the persisted replay payload aligned with the API's JSON
        # representation while preserving exact decimal values as strings.
        response=jsonable_encoder(
            response,
            custom_encoder={
                Decimal: str,
                datetime: lambda value: (
                    value.isoformat().replace("+00:00", "Z")
                ),
            },
        ),
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
    dependencies=[Depends(require_service_access)],
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

@app.post(
    "/api/v1/transactions/authorize",
    dependencies=[Depends(require_service_access)],
)
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

@app.post(
    "/api/v1/transactions/{transaction_id}/capture",
    dependencies=[Depends(require_service_access)],
)
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

@app.post(
    "/api/v1/transactions/{transaction_id}/settle",
    dependencies=[Depends(require_service_access)],
)
def settle_transaction(
        transaction_id: str,
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
    """Settle a captured transaction."""
    correlation_id = get_correlation_id(correlation_id)
    check_simulated_failure(x_simulate_failure)

    payment_service = PaymentService(
        PostgresTransactionRepository(db),
        PostgresCardRepository(db),
    )
    audit_service = AuditService(PostgresAuditRepository(db))
    idempotency_repository = PostgresIdempotencyRepository(db)
    fingerprint = build_settlement_fingerprint(transaction_id)

    try:
        existing_response = validate_idempotency_key(
            idempotency_key,
            fingerprint,
            idempotency_repository,
        )
        if existing_response is not None:
            db.rollback()
            return existing_response

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

        store_idempotency_result(
            idempotency_key,
            fingerprint,
            response,
            idempotency_repository,
        )
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

@app.post(
    "/api/v1/transactions/{transaction_id}/refund",
    dependencies=[Depends(require_service_access)],
)
def refund_transaction(
        transaction_id: str,
        request: RefundRequest,
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
    """Refund a settled transaction, either partially or completely."""
    correlation_id = get_correlation_id(correlation_id)
    check_simulated_failure(x_simulate_failure)

    payment_service = PaymentService(
        PostgresTransactionRepository(db),
        PostgresCardRepository(db),
    )
    audit_service = AuditService(PostgresAuditRepository(db))
    idempotency_repository = PostgresIdempotencyRepository(db)
    fingerprint = build_refund_fingerprint(transaction_id, request)

    try:
        existing_response = validate_idempotency_key(
            idempotency_key,
            fingerprint,
            idempotency_repository,
        )
        if existing_response is not None:
            db.rollback()
            return existing_response

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

@app.get(
    "/api/v1/transactions/{transaction_id}",
    dependencies=[Depends(require_service_access)],
)
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

def require_admin_access(
        x_admin_api_key: Optional[str] = Header(
            default=None,
            alias="X-Admin-API-Key",
        ),
) -> None:
    """Authorize access to operational audit data with a service API key."""
    expected = settings.admin_api_key

    # API tests run in an explicitly isolated test environment.
    if settings.environment == "test" and expected is None:
        return

    if expected is None:
        raise HTTPException(
            status_code=503,
            detail="Administrative access is not configured",
        )

    if (
        not x_admin_api_key
        or not secrets.compare_digest(x_admin_api_key, expected)
    ):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid administrative credentials",
            headers={"WWW-Authenticate": "ApiKey"},
        )


@app.get(
    "/api/v1/audit/transactions/{transaction_id}",
    dependencies=[Depends(require_admin_access)],
)
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


@app.get(
    "/api/v1/audit/correlation/{correlation_id}",
    dependencies=[Depends(require_admin_access)],
)
def get_correlation_audit_events(
        correlation_id: str,
        audit_service: AuditService = Depends(get_audit_service),
):
    """Retrieve audit events associated with a correlation ID."""
    return audit_service.list_by_correlation_id(correlation_id)


@app.get(
    "/api/v1/audit/integrity",
    dependencies=[Depends(require_admin_access)],
)
def get_audit_integrity(
        audit_service: AuditService = Depends(get_audit_service),
) -> dict:
    """Verify the append-only audit hash chain for administrative review."""
    return audit_service.verify_integrity()


# ============================================================================
# Health Check
# ============================================================================

@app.get("/")
def root() -> dict[str, str]:
    """Return the basic application health status."""
    return {
        "message": "PayGuard AI Mock Payment Gateway is running",
    }
