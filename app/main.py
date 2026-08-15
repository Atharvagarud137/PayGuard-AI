import random
import string
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

from app.repositories.transaction_repository import TransactionRepository
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
# Dependencies
# ============================================================================

transaction_repository = TransactionRepository(storage)

payment_service = PaymentService(
    transaction_repository
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
        random.choices(string.digits, k=4)
    )

    return f"****-****-****-{digits}"


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
):
    """
    Issue a new virtual card.

    Card persistence currently uses the shared in-memory storage.
    """

    check_simulated_failure(x_simulate_failure)

    card_number = generate_masked_card_number()

    while storage.card_exists_with_number(card_number):
        card_number = generate_masked_card_number()

    card = Card(
        cardholder_name=request.cardholder_name,
        card_number=card_number,
        network=request.network,
        balance=request.initial_balance,
        expiry_date=request.expiry_date,
    )

    storage.add_card(card)

    return card


# ============================================================================
# Authorization
# ============================================================================

@app.post("/api/v1/transactions/authorize")
def authorize_transaction(
        request: AuthorizeRequest,
        x_simulate_failure: Optional[str] = Header(default=None),
):
    """
    Authorize a payment against an active card.

    Successful authorization:

        - validates the card
        - validates available balance
        - reduces available balance
        - creates an AUTHORIZED transaction

    Insufficient funds:

        - creates a DECLINED transaction
        - returns the decline as a normal payment response
    """

    check_simulated_failure(x_simulate_failure)

    card = storage.get_card(request.card_id)

    if not card:
        raise HTTPException(
            status_code=404,
            detail="Card not found",
        )

    if card.status != CardStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail="Card is not active",
        )

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

        transaction_repository.add(transaction)

        return {
            "transaction_id": transaction.transaction_id,
            "status": transaction.status,
            "decline_reason": transaction.decline_reason,
        }

    card.balance -= request.amount

    storage.update_card(card)

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

    transaction_repository.add(transaction)

    return {
        "transaction_id": transaction.transaction_id,
        "status": transaction.status,
        "authorized_amount": transaction.authorized_amount,
    }


# ============================================================================
# Capture
# ============================================================================

@app.post(
    "/api/v1/transactions/{transaction_id}/capture"
)
def capture_transaction(
        transaction_id: str,
        request: CaptureRequest,
        x_simulate_failure: Optional[str] = Header(default=None),
):
    """
    Capture an authorized transaction.
    """

    check_simulated_failure(x_simulate_failure)

    try:
        transaction = payment_service.capture(
            transaction_id=transaction_id,
            capture_amount=request.capture_amount,
        )

    except TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except CaptureAmountExceededError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except InvalidTransactionStateError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "transaction_id": transaction.transaction_id,
        "status": transaction.status,
        "captured_amount": transaction.captured_amount,
    }


# ============================================================================
# Settlement
# ============================================================================

@app.post(
    "/api/v1/transactions/{transaction_id}/settle"
)
def settle_transaction(
        transaction_id: str,
        x_simulate_failure: Optional[str] = Header(default=None),
):
    """
    Settle a captured transaction.
    """

    check_simulated_failure(x_simulate_failure)

    try:
        transaction = payment_service.settle(
            transaction_id=transaction_id,
        )

    except TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except InvalidTransactionStateError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

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
        x_simulate_failure: Optional[str] = Header(default=None),
):
    """
    Refund a settled transaction either partially or completely.
    """

    check_simulated_failure(x_simulate_failure)

    try:
        transaction, remaining_after = payment_service.refund(
            transaction_id=transaction_id,
            refund_amount=request.refund_amount,
        )

    except TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except RefundAmountExceededError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except InvalidTransactionStateError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        "transaction_id": transaction.transaction_id,
        "refund_id": f"refund-{transaction.transaction_id[:8]}",
        "status": transaction.status,
        "remaining_balance": remaining_after,
    }


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