from copy import deepcopy
from typing import Any, Dict, List, Optional

from app.models import (
    AuditEvent,
    Card,
    Transaction,
)


class InMemoryStorage:
    """
    In-memory persistence implementation used by the PayGuard AI
    application and test suite.

    The storage layer is responsible only for persistence.

    Business rules such as authorization, capture, settlement,
    refunds, state transitions, and idempotency validation remain
    outside this class.

    The implementation can later be replaced by a database-backed
    repository without changing the service-layer interfaces.
    """

    def __init__(self) -> None:
        self.cards: Dict[str, Card] = {}
        self.transactions: Dict[str, Transaction] = {}

        # -------------------------------------------------------------------
        # Audit Events
        # -------------------------------------------------------------------
        #
        # Audit events are stored separately from payment transactions.
        # They represent operational/security history and do not contain
        # raw sensitive payment payloads.
        #
        self.audit_events: Dict[str, AuditEvent] = {}

        # -------------------------------------------------------------------
        # Idempotency Records
        # -------------------------------------------------------------------
        #
        # Each record contains:
        #
        #   fingerprint -> deterministic representation of the request
        #   response    -> original API response
        #
        # This allows the API to distinguish:
        #
        #   same key + same request
        #   same key + different request
        #
        self.idempotency_records: Dict[str, Dict[str, Any]] = {}

    # =======================================================================
    # Card Operations
    # =======================================================================

    def add_card(
            self,
            card: Card,
    ) -> None:
        """
        Persist a new card.
        """

        self.cards[card.card_id] = card

    def get_card(
            self,
            card_id: str,
    ) -> Optional[Card]:
        """
        Retrieve a card by its unique identifier.

        Returns:
            The stored Card if found, otherwise None.
        """

        return self.cards.get(card_id)

    def update_card(
            self,
            card: Card,
    ) -> None:
        """
        Persist the current state of an existing card.
        """

        self.cards[card.card_id] = card

    def card_exists_with_number(
            self,
            card_number: str,
    ) -> bool:
        """
        Check whether a card with the supplied card number already exists.
        """

        return any(
            existing_card.card_number == card_number
            for existing_card in self.cards.values()
        )

    # =======================================================================
    # Transaction Operations
    # =======================================================================

    def add_transaction(
            self,
            transaction: Transaction,
    ) -> None:
        """
        Persist a new transaction.
        """

        self.transactions[transaction.transaction_id] = transaction

    def get_transaction(
            self,
            transaction_id: str,
    ) -> Optional[Transaction]:
        """
        Retrieve a transaction by its unique identifier.

        Returns:
            The stored Transaction if found, otherwise None.
        """

        return self.transactions.get(transaction_id)

    def update_transaction(
            self,
            transaction: Transaction,
    ) -> None:
        """
        Persist the current state of an existing transaction.
        """

        self.transactions[transaction.transaction_id] = transaction

    # =======================================================================
    # Audit Operations
    # =======================================================================

    def add_audit_event(
            self,
            event: AuditEvent,
    ) -> None:
        """
        Persist an audit event.

        A deep copy is stored so external references cannot mutate the
        persisted audit record after insertion.
        """

        self.audit_events[event.audit_event_id] = deepcopy(event)

    def get_audit_event(
            self,
            audit_event_id: str,
    ) -> Optional[AuditEvent]:
        """
        Retrieve an audit event by its unique identifier.

        Returns:
            A defensive copy of the AuditEvent if found, otherwise None.
        """

        event = self.audit_events.get(audit_event_id)

        if event is None:
            return None

        return deepcopy(event)

    def list_audit_events(
            self,
    ) -> List[AuditEvent]:
        """
        Return all persisted audit events.

        Defensive copies are returned so callers cannot mutate the
        stored audit records.
        """

        return [
            deepcopy(event)
            for event in self.audit_events.values()
        ]

    # =======================================================================
    # Idempotency Operations
    # =======================================================================

    def get_idempotency_record(
            self,
            idempotency_key: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an idempotency record by key.

        A deep copy is returned so callers cannot accidentally mutate
        the persisted idempotency record.
        """

        record = self.idempotency_records.get(
            idempotency_key
        )

        if record is None:
            return None

        return deepcopy(record)

    def add_idempotency_record(
            self,
            idempotency_key: str,
            fingerprint: str,
            response: Dict[str, Any],
    ) -> None:
        """
        Persist an idempotency record.

        The request fingerprint and original API response are stored
        together so repeated requests can safely replay the original
        result.
        """

        self.idempotency_records[idempotency_key] = {
            "fingerprint": fingerprint,
            "response": deepcopy(response),
        }

    # =======================================================================
    # Reset
    # =======================================================================

    def reset(self) -> None:
        """
        Clear all persisted application state.

        This method exists for test isolation and local development.

        A production database-backed implementation should not expose
        an equivalent destructive operation through application code.
        """

        self.cards.clear()
        self.transactions.clear()
        self.audit_events.clear()
        self.idempotency_records.clear()


# ===========================================================================
# Shared Application Storage
# ===========================================================================

# Single shared in-memory storage instance used by the application.
#
# Repositories depend on this abstraction instead of allowing services
# to manipulate storage directly.
storage = InMemoryStorage()