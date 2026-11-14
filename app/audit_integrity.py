import hashlib
import json
from datetime import datetime, timezone
from typing import Any


ZERO_HASH = "0" * 64


def calculate_audit_hash(
        *,
        sequence: int,
        previous_hash: str,
        event_id: str,
        transaction_id: str | None,
        event_type: str,
        message: str,
        correlation_id: str,
        metadata_json: dict[str, Any] | None,
        created_at: datetime,
) -> str:
    """Calculate the canonical hash for one audit-chain entry."""
    timestamp = created_at
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    timestamp = timestamp.astimezone(timezone.utc)

    payload = {
        "sequence": sequence,
        "id": event_id,
        "transaction_id": transaction_id,
        "event_type": event_type,
        "message": message,
        "correlation_id": correlation_id,
        "metadata_json": metadata_json or {},
        "created_at": timestamp.isoformat(),
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(
        f"{previous_hash}:{canonical}".encode("utf-8")
    ).hexdigest()
