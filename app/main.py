import random
import string
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Header
from typing import Optional

from app.models import (
    CardCreateRequest, Card, CardStatus,
    AuthorizeRequest, CaptureRequest, RefundRequest,
    Transaction, TransactionStatus, TransactionEvent
)
from app.storage import storage

app = FastAPI(title="PayGuard AI - Mock Payment Gateway", version="1.0.0")


# ---------- Helper Functions ----------

def generate_masked_card_number() -> str:
    digits = "".join(random.choices(string.digits, k=4))
    return f"****-****-****-{digits}"


def check_simulated_failure(x_simulate_failure: Optional[str]):
    if x_simulate_failure == "TIMEOUT":
        raise HTTPException(status_code=504, detail="Simulated timeout occurred")
    if x_simulate_failure == "NETWORK_ERROR":
        raise HTTPException(status_code=502, detail="Simulated network error")
    if x_simulate_failure == "INVALID_RESPONSE":
        raise HTTPException(status_code=500, detail="Simulated invalid response")


# ---------- Card Issuance ----------

@app.post("/api/v1/cards", response_model=Card, status_code=201)
def issue_card(
        request: CardCreateRequest,
        x_simulate_failure: Optional[str] = Header(default=None)
):
    check_simulated_failure(x_simulate_failure)

    card_number = generate_masked_card_number()
    while storage.card_exists_with_number(card_number):
        card_number = generate_masked_card_number()

    card = Card(
        cardholder_name=request.cardholder_name,
        card_number=card_number,
        network=request.network,
        balance=request.initial_balance,
        expiry_date=request.expiry_date
    )
    storage.add_card(card)
    return card


# ---------- Authorization ----------

@app.post("/api/v1/transactions/authorize")
def authorize_transaction(
        request: AuthorizeRequest,
        x_simulate_failure: Optional[str] = Header(default=None)
):
    check_simulated_failure(x_simulate_failure)

    card = storage.get_card(request.card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if card.status != CardStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Card is not active")

    if card.balance < request.amount:
        transaction = Transaction(
            card_id=request.card_id,
            merchant_id=request.merchant_id,
            status=TransactionStatus.DECLINED,
            decline_reason="INSUFFICIENT_FUNDS"
        )
        transaction.history.append(
            TransactionEvent(status=TransactionStatus.DECLINED, detail="Insufficient funds")
        )
        storage.add_transaction(transaction)
        return {
            "transaction_id": transaction.transaction_id,
            "status": transaction.status,
            "decline_reason": transaction.decline_reason
        }

    card.balance -= request.amount
    storage.update_card(card)

    transaction = Transaction(
        card_id=request.card_id,
        merchant_id=request.merchant_id,
        authorized_amount=request.amount,
        status=TransactionStatus.AUTHORIZED
    )
    transaction.history.append(
        TransactionEvent(status=TransactionStatus.AUTHORIZED, detail="Authorization approved")
    )
    storage.add_transaction(transaction)

    return {
        "transaction_id": transaction.transaction_id,
        "status": transaction.status,
        "authorized_amount": transaction.authorized_amount
    }


# ---------- Capture ----------

@app.post("/api/v1/transactions/{transaction_id}/capture")
def capture_transaction(
        transaction_id: str,
        request: CaptureRequest,
        x_simulate_failure: Optional[str] = Header(default=None)
):
    check_simulated_failure(x_simulate_failure)

    transaction = storage.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction.status != TransactionStatus.AUTHORIZED:
        raise HTTPException(status_code=409, detail="Transaction is not in AUTHORIZED state")

    if request.capture_amount > transaction.authorized_amount:
        raise HTTPException(status_code=400, detail="Capture amount exceeds authorized amount")

    transaction.captured_amount = request.capture_amount
    transaction.status = TransactionStatus.CAPTURED
    transaction.history.append(
        TransactionEvent(status=TransactionStatus.CAPTURED, detail="Amount captured")
    )
    storage.update_transaction(transaction)

    return {
        "transaction_id": transaction.transaction_id,
        "status": transaction.status,
        "captured_amount": transaction.captured_amount
    }


# ---------- Settlement ----------

@app.post("/api/v1/transactions/{transaction_id}/settle")
def settle_transaction(
        transaction_id: str,
        x_simulate_failure: Optional[str] = Header(default=None)
):
    check_simulated_failure(x_simulate_failure)

    transaction = storage.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction.status != TransactionStatus.CAPTURED:
        raise HTTPException(status_code=409, detail="Transaction is not in CAPTURED state")

    transaction.settled_amount = transaction.captured_amount
    transaction.status = TransactionStatus.SETTLED
    transaction.history.append(
        TransactionEvent(status=TransactionStatus.SETTLED, detail="Transaction settled")
    )
    storage.update_transaction(transaction)

    return {
        "transaction_id": transaction.transaction_id,
        "status": transaction.status,
        "settled_at": datetime.now(timezone.utc)
    }


# ---------- Refund ----------

@app.post("/api/v1/transactions/{transaction_id}/refund")
def refund_transaction(
        transaction_id: str,
        request: RefundRequest,
        x_simulate_failure: Optional[str] = Header(default=None)
):
    check_simulated_failure(x_simulate_failure)

    transaction = storage.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction.status not in [TransactionStatus.SETTLED, TransactionStatus.PARTIALLY_REFUNDED]:
        raise HTTPException(status_code=409, detail="Transaction is not settled")

    remaining = transaction.settled_amount - transaction.refunded_amount
    if request.refund_amount > remaining:
        raise HTTPException(status_code=400, detail="Refund amount exceeds remaining refundable balance")

    transaction.refunded_amount += request.refund_amount
    remaining_after = transaction.settled_amount - transaction.refunded_amount

    if remaining_after == 0:
        transaction.status = TransactionStatus.REFUNDED
    else:
        transaction.status = TransactionStatus.PARTIALLY_REFUNDED

    transaction.history.append(
        TransactionEvent(status=transaction.status, detail=f"Refunded {request.refund_amount}")
    )
    storage.update_transaction(transaction)

    return {
        "transaction_id": transaction.transaction_id,
        "refund_id": f"refund-{transaction.transaction_id[:8]}",
        "status": transaction.status,
        "remaining_balance": remaining_after
    }


# ---------- Transaction Lookup ----------

@app.get("/api/v1/transactions/{transaction_id}")
def get_transaction(transaction_id: str):
    transaction = storage.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


# ---------- Health Check ----------

@app.get("/")
def root():
    return {"message": "PayGuard AI Mock Payment Gateway is running"}