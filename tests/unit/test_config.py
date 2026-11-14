import pytest

from app.config import load_settings


def production_environment(**overrides):
    values = {
        "PAYGUARD_ENV": "production",
        "DATABASE_URL": (
            "postgresql+psycopg://payguard:secret@localhost/payguard"
        ),
        "PAYGUARD_API_KEY": "s" * 40,
        "PAYGUARD_ADMIN_API_KEY": "p" * 40,
    }
    values.update(overrides)
    return values


def test_production_requires_explicit_database_and_admin_credentials():
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        load_settings({
            "PAYGUARD_ENV": "production",
            "PAYGUARD_ADMIN_API_KEY": "p" * 40,
        })

    with pytest.raises(RuntimeError, match="PAYGUARD_API_KEY"):
        load_settings({
            "PAYGUARD_ENV": "production",
            "DATABASE_URL": (
                "postgresql+psycopg://payguard:secret@localhost/payguard"
            ),
            "PAYGUARD_ADMIN_API_KEY": "p" * 40,
        })

    with pytest.raises(RuntimeError, match="PAYGUARD_ADMIN_API_KEY"):
        load_settings({
            "PAYGUARD_ENV": "production",
            "DATABASE_URL": (
                "postgresql+psycopg://payguard:secret@localhost/payguard"
            ),
            "PAYGUARD_API_KEY": "s" * 40,
        })


def test_production_defaults_fail_closed():
    settings = load_settings(production_environment())

    assert settings.environment == "production"
    assert settings.cors_origins == ()
    assert settings.docs_enabled is False
    assert settings.failure_simulation_enabled is False
    assert settings.enable_test_endpoints is False


def test_cors_rejects_wildcards_and_non_origin_urls():
    with pytest.raises(RuntimeError, match="explicit HTTP"):
        load_settings(
            production_environment(PAYGUARD_CORS_ORIGINS="*")
        )

    with pytest.raises(RuntimeError, match="explicit HTTP"):
        load_settings(
            production_environment(
                PAYGUARD_CORS_ORIGINS="https://example.com/api"
            )
        )


def test_test_endpoints_cannot_be_enabled_outside_test_environment():
    with pytest.raises(RuntimeError, match="only be enabled"):
        load_settings(
            production_environment(
                PAYGUARD_ENABLE_TEST_ENDPOINTS="true",
                PAYGUARD_TEST_RESET_TOKEN="t" * 40,
            )
        )


def test_test_endpoints_require_a_long_reset_token():
    with pytest.raises(RuntimeError, match="at least 32 characters"):
        load_settings({
            "PAYGUARD_ENV": "test",
            "PAYGUARD_ENABLE_TEST_ENDPOINTS": "true",
            "PAYGUARD_TEST_RESET_TOKEN": "short",
        })


def test_test_environment_can_explicitly_enable_protected_reset_route():
    settings = load_settings({
        "PAYGUARD_ENV": "test",
        "PAYGUARD_ENABLE_TEST_ENDPOINTS": "true",
        "PAYGUARD_TEST_RESET_TOKEN": "t" * 40,
    })

    assert settings.enable_test_endpoints is True
    assert settings.test_reset_token == "t" * 40
    assert settings.failure_simulation_enabled is True



def test_max_request_bytes_is_configurable_with_safe_bounds():
    settings = load_settings({
        "PAYGUARD_ENV": "test",
        "PAYGUARD_MAX_REQUEST_BYTES": "2048",
    })

    assert settings.max_request_bytes == 2048

    with pytest.raises(RuntimeError, match="between 1024 and 1048576"):
        load_settings({
            "PAYGUARD_ENV": "test",
            "PAYGUARD_MAX_REQUEST_BYTES": "512",
        })
