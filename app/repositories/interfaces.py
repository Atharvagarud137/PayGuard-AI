from typing import Any, Dict, List, Optional, Protocol

from app.models import AuditEvent, Card, Transaction


class CardRepositoryProtocol(Protocol):
    """
    Persistence contract for payment cards.

    Application code depends on this contract rather than on a specific
    persistence implementation.
    """

    def add(self, card: Card) -> None:
        ...

    def get(self, card_id: str) -> Optional[Card]:
        ...

    def update(self, card: Card) -> None:
        ...

    def exists_with_number(self, card_number: str) -> bool:
        ...


class TransactionRepositoryProtocol(Protocol):
    """
    Persistence contract for payment transactions.
    """

    def add(self, transaction: Transaction) -> None:
        ...

    def get(self, transaction_id: str) -> Optional[Transaction]:
        ...

    def update(self, transaction: Transaction) -> None:
        ...


class AuditRepositoryProtocol(Protocol):
    """
    Persistence contract for audit events.
    """

    def add(self, event: AuditEvent) -> None:
        ...

    def get(self, audit_event_id: str) -> Optional[AuditEvent]:
        ...

    def list_all(self) -> List[AuditEvent]:
        ...

    def list_by_transaction(
            self,
            transaction_id: str,
    ) -> List[AuditEvent]:
        ...

    def list_by_correlation_id(
            self,
            correlation_id: str,
    ) -> List[AuditEvent]:
        ...


class IdempotencyRepositoryProtocol(Protocol):
    """
    Persistence contract for idempotency records.

    The repository stores the request fingerprint and original response.
    Idempotency business rules remain outside the persistence layer.
    """

    def get(
            self,
            idempotency_key: str,
    ) -> Optional[Dict[str, Any]]:
        ...

    def add(
            self,
            idempotency_key: str,
            fingerprint: str,
            response: Dict[str, Any],
    ) -> None:
        ...