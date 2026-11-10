from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.database_models import CardDB, TransactionDB
from app.models import (
    Card,
    Transaction,
    TransactionStatus,
)
from app.repositories.postgres_card_repository import (
    PostgresCardRepository,
)
from app.repositories.postgres_transaction_repository import (
    PostgresTransactionRepository,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["Dashboard"],
)


# ============================================================================
# Dashboard Summary
# ============================================================================

@router.get("/dashboard/summary")
def get_dashboard_summary(
        db: Session = Depends(get_db),
) -> dict[str, int | float]:
    """
    Return dashboard metrics from the PostgreSQL transaction records.

    The database is the single source of truth for payment operations.
    """
    status_rows = db.execute(
        select(
            TransactionDB.status,
            func.count(TransactionDB.id),
        ).group_by(TransactionDB.status)
    ).all()

    counts = {
        str(status): int(count)
        for status, count in status_rows
    }

    total_transactions = sum(counts.values())

    successful = sum(
        counts.get(status.value, 0)
        for status in (
            TransactionStatus.SETTLED,
            TransactionStatus.REFUNDED,
            TransactionStatus.PARTIALLY_REFUNDED,
        )
    )

    pending = sum(
        counts.get(status.value, 0)
        for status in (
            TransactionStatus.AUTHORIZED,
            TransactionStatus.CAPTURED,
        )
    )

    declined = counts.get(TransactionStatus.DECLINED.value, 0)

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
def get_transactions(
        db: Session = Depends(get_db),
) -> List[Transaction]:
    """
    Return PostgreSQL-backed transactions, newest first.

    Lifecycle events are loaded with the transaction so conversion does not
    depend on a session that has already been closed.
    """
    statement = (
        select(TransactionDB)
        .options(selectinload(TransactionDB.events))
        .order_by(
            TransactionDB.created_at.desc(),
            TransactionDB.id.desc(),
        )
    )
    transaction_records = db.execute(
        statement
    ).scalars().all()

    return [
        PostgresTransactionRepository._to_domain_model(record)
        for record in transaction_records
    ]


# ============================================================================
# Card List
# ============================================================================

@router.get("/cards", response_model=List[Card])
def get_cards(
        db: Session = Depends(get_db),
) -> List[Card]:
    """
    Return PostgreSQL-backed cards, newest first.

    Card numbers remain masked by the domain model and API contract.
    """
    statement = select(CardDB).order_by(
        CardDB.created_at.desc(),
        CardDB.id.desc(),
    )
    card_records = db.execute(statement).scalars().all()

    return [
        PostgresCardRepository._to_domain_model(record)
        for record in card_records
    ]
