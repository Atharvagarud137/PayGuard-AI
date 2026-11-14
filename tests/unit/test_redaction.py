from app.security import redact_sensitive_text


def test_redacts_card_numbers_and_security_codes():
    value = (
        "pan=4111 1111 1111 1111 cvv=123 "
        "X-API-Key=service-secret"
    )

    redacted = redact_sensitive_text(value)

    assert "4111 1111 1111 1111" not in redacted
    assert "service-secret" not in redacted
    assert "cvv=123" not in redacted.lower()
    assert "[REDACTED-PAN]" in redacted
    assert "[REDACTED]" in redacted


def test_redacts_bearer_tokens_and_admin_credentials():
    value = (
        "Authorization: Bearer eyJhbGciOiJub25lIn0 "
        "X-Admin-API-Key=admin-secret"
    )

    redacted = redact_sensitive_text(value)

    assert "eyJhbGciOiJub25lIn0" not in redacted
    assert "admin-secret" not in redacted



def test_redaction_preserves_uuid_identifiers():
    identifier = "86fb6ec0-85c0-4fdb-aebe-d144d073dc20"

    assert redact_sensitive_text(identifier) == identifier
