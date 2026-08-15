from typing import List

from fastapi import APIRouter

from app.models import (
    Card,
    Transaction,
    TransactionStatus,
)
from app.storage import storage


router = APIRouter(
    prefix="/api/v1",
    tags=["Dashboard"],
)


# ============================================================================
# Dashboard Summary
# ============================================================================

@router.get("/dashboard/summary")
def get_dashboard_summary():
    """
    Return aggregated payment gateway metrics for the dashboard.

    Status classification:

    Successful:
        SETTLED
        REFUNDED
        PARTIALLY_REFUNDED

    Pending:
        AUTHORIZED
        CAPTURED

    Declined:
        DECLINED
    """

    transactions = list(storage.transactions.values())

    total_transactions = len(transactions)

    successful = sum(
        1
        for transaction in transactions
        if transaction.status
        in (
            TransactionStatus.SETTLED,
            TransactionStatus.REFUNDED,
            TransactionStatus.PARTIALLY_REFUNDED,
        )
    )

    pending = sum(
        1
        for transaction in transactions
        if transaction.status
        in (
            TransactionStatus.AUTHORIZED,
            TransactionStatus.CAPTURED,
        )
    )

    declined = sum(
        1
        for transaction in transactions
        if transaction.status == TransactionStatus.DECLINED
    )

    success_rate = (
        round((successful / total_transactions) * 100, 2)
        if total_transactions > 0
        else 0.0
    )

    return {
        "total_transactions": total_transactions,
        "successful": successful,
        "pending": pending,
        "declined": declined,
        "success_rate": success_rate,
    }


# ============================================================================
# Transaction List
# ============================================================================

@router.get("/transactions", response_model=List[Transaction])
def get_transactions():
    """
    Return all transactions currently stored by the payment gateway.

    Transactions are returned newest first.
    """

    transactions = list(storage.transactions.values())

    transactions.sort(
        key=lambda transaction: transaction.created_at,
        reverse=True,
    )

    return transactions


# ============================================================================
# Card List
# ============================================================================

@router.get("/cards", response_model=List[Card])
def get_cards():
    """
    Return all cards currently stored by the payment gateway.

    Cards are returned newest first.
    """

    cards = list(storage.cards.values())

    cards.sort(
        key=lambda card: card.created_at,
        reverse=True,
    )

    return cards