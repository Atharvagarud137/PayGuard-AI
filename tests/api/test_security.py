from dataclasses import replace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import main
from app.config import settings


def test_service_key_protects_business_and_dashboard_apis(
        client,
        monkeypatch,
):
    service_key = "s" * 40
    monkeypatch.setattr(
        main,
        "settings",
        replace(
            settings,
            environment="production",
            service_api_key=service_key,
        ),
    )

    missing_read = client.get("/api/v1/dashboard/summary")
    invalid_write = client.post(
        "/api/v1/cards",
        json={
            "cardholder_name": "Synthetic Test User",
            "network": "VISA",
            "initial_balance": "100.00",
            "expiry_date": "12/2030",
        },
        headers={"X-API-Key": "wrong-key"},
    )
    valid_read = client.get(
        "/api/v1/dashboard/summary",
        headers={"X-API-Key": service_key},
    )
    valid_write = client.post(
        "/api/v1/cards",
        json={
            "cardholder_name": "Synthetic Test User",
            "network": "VISA",
            "initial_balance": "100.00",
            "expiry_date": "12/2030",
        },
        headers={"X-API-Key": service_key},
    )

    assert missing_read.status_code == 401
    assert invalid_write.status_code == 401
    assert valid_read.status_code == 200
    assert valid_write.status_code == 201


def test_audit_routes_require_admin_key_outside_test_environment(
        client,
        monkeypatch,
):
    admin_key = "a" * 40
    monkeypatch.setattr(
        main,
        "settings",
        replace(
            settings,
            environment="production",
            admin_api_key=admin_key,
        ),
    )

    missing = client.get("/api/v1/audit/correlation/security-test")
    invalid = client.get(
        "/api/v1/audit/correlation/security-test",
        headers={"X-Admin-API-Key": "wrong-key"},
    )
    valid = client.get(
        "/api/v1/audit/correlation/security-test",
        headers={"X-Admin-API-Key": admin_key},
    )
    integrity_missing = client.get("/api/v1/audit/integrity")
    integrity_valid = client.get(
        "/api/v1/audit/integrity",
        headers={"X-Admin-API-Key": admin_key},
    )

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert valid.status_code == 200
    assert valid.json() == []
    assert integrity_missing.status_code == 401
    assert integrity_valid.status_code == 200
    assert integrity_valid.json()["valid"] is True


def test_test_reset_endpoint_requires_dedicated_token(client):
    missing = client.post("/api/v1/test/reset")
    valid = client.post(
        "/api/v1/test/reset",
        headers={"X-Test-Reset-Token": settings.test_reset_token},
    )

    assert missing.status_code == 401
    assert valid.status_code == 200


def test_failure_simulation_is_rejected_in_production(monkeypatch):
    monkeypatch.setattr(
        main,
        "settings",
        replace(
            settings,
            environment="production",
            failure_simulation_enabled=False,
        ),
    )

    with pytest.raises(HTTPException) as error:
        main.check_simulated_failure("TIMEOUT")

    assert error.value.status_code == 403


def test_card_creation_rejects_pan_and_cvv_fields_without_echoing_values(
        client,
):
    pan_marker = "SYNTHETIC-PAN-MUST-NOT-BE-ECHOED"
    cvv_marker = "SYNTHETIC-CVV-MUST-NOT-BE-ECHOED"
    response = client.post(
        "/api/v1/cards",
        json={
            "cardholder_name": "Synthetic Test User",
            "network": "VISA",
            "initial_balance": "100.00",
            "expiry_date": "12/2030",
            "pan": pan_marker,
            "cvv": cvv_marker,
        },
    )

    assert response.status_code == 422
    assert pan_marker not in response.text
    assert cvv_marker not in response.text
    assert '"input"' not in response.text


def test_untrusted_origin_is_not_allowed_by_cors(client):
    response = client.options(
        "/api/v1/cards",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert "access-control-allow-origin" not in response.headers


def test_unexpected_errors_return_generic_details_without_echoing_secrets(
        client,
        monkeypatch,
):
    secret_marker = "SENSITIVE-DB-ERROR-MUST-NOT-LEAK"

    def fail_card_lookup(self, card_number):
        raise RuntimeError(secret_marker)

    monkeypatch.setattr(
        main.PostgresCardRepository,
        "exists_with_number",
        fail_card_lookup,
    )

    with TestClient(main.app, raise_server_exceptions=False) as safe_client:
        response = safe_client.post(
            "/api/v1/cards",
            json={
                "cardholder_name": "Synthetic Test User",
                "network": "VISA",
                "initial_balance": "100.00",
                "expiry_date": "12/2030",
            },
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert secret_marker not in response.text



def test_security_headers_are_present(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["permissions-policy"] == (
        "camera=(), microphone=(), geolocation=()"
    )


def test_api_responses_are_not_cached(client):
    response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"


def test_oversized_request_body_is_rejected_before_validation(client):
    response = client.post(
        "/api/v1/cards",
        content=b"x" * (settings.max_request_bytes + 1),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "Request body is too large"}


def test_application_logs_redact_card_numbers_and_credentials(caplog):
    import logging

    with caplog.at_level(logging.WARNING, logger="payguard"):
        main.logger.warning(
            "Rejected PAN=%s CVV=%s X-API-Key=%s",
            "4111 1111 1111 1111",
            "123",
            "service-secret-marker",
        )

    assert "4111 1111 1111 1111" not in caplog.text
    assert "CVV=123" not in caplog.text
    assert "service-secret-marker" not in caplog.text
    assert "[REDACTED-PAN]" in caplog.text
    assert "[REDACTED]" in caplog.text
