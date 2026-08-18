from copy import deepcopy
from typing import List, Optional

from app.models import AuditEvent
from app.storage import InMemoryStorage


class AuditRepository:
    """
    Persistence abstraction for audit events.

    The repository is responsible only for storing and retrieving audit
    records. It does not contain business logic.

    The current implementation uses the shared in-memory storage backend.
    A database-backed implementation can replace this repository later
    without changing the AuditService interface.
    """

    def __init__(
            self,
            storage_backend: InMemoryStorage,
    ) -> None:
        self.storage = storage_backend

    # -----------------------------------------------------------------------
    # Audit Event Operations
    # -----------------------------------------------------------------------

    def add(
            self,
            event: AuditEvent,
    ) -> None:
        """
        Persist an audit event.

        The storage layer owns the actual persistence mechanism.
        """

        self.storage.add_audit_event(event)

    def get(
            self,
            audit_event_id: str,
    ) -> Optional[AuditEvent]:
        """
        Retrieve an audit event by its unique identifier.

        Returns:
            A defensive copy of the AuditEvent if found, otherwise None.
        """

        event = self.storage.get_audit_event(audit_event_id)

        if event is None:
            return None

        return deepcopy(event)

    def list_all(self) -> List[AuditEvent]:
        """
        Return all persisted audit events.

        Defensive copies are returned so callers cannot accidentally mutate
        the persisted audit records held by the storage backend.
        """

        events = self.storage.list_audit_events()

        return [
            deepcopy(event)
            for event in events
        ]

    def list_by_transaction(
            self,
            transaction_id: str,
    ) -> List[AuditEvent]:
        """
        Return all audit events associated with a transaction.

        Only events whose transaction_id exactly matches the supplied
        transaction_id are returned.
        """

        events = self.storage.list_audit_events()

        return [
            deepcopy(event)
            for event in events
            if event.transaction_id == transaction_id
        ]

    def list_by_correlation_id(
            self,
            correlation_id: str,
    ) -> List[AuditEvent]:
        """
        Return all audit events associated with a request correlation ID.

        Only events whose correlation_id exactly matches the supplied
        correlation_id are returned.
        """

        events = self.storage.list_audit_events()

        return [
            deepcopy(event)
            for event in events
            if event.correlation_id == correlation_id
        ]