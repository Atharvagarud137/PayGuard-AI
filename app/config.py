import os
from dataclasses import dataclass
from typing import Mapping
from urllib.parse import urlsplit


_LOCAL_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)
_ALLOWED_ENVIRONMENTS = frozenset({"development", "test", "production"})


@dataclass(frozen=True)
class AppSettings:
    environment: str
    cors_origins: tuple[str, ...]
    service_api_key: str | None
    admin_api_key: str | None
    enable_test_endpoints: bool
    test_reset_token: str | None
    docs_enabled: bool
    failure_simulation_enabled: bool
    max_request_bytes: int


def _parse_bool(value: str, *, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be a boolean value")


def _parse_cors_origins(
        raw_value: str | None,
        *,
        environment: str,
) -> tuple[str, ...]:
    if raw_value is None:
        return _LOCAL_CORS_ORIGINS if environment in {"development", "test"} else ()

    origins: list[str] = []
    for raw_origin in raw_value.split(","):
        origin = raw_origin.strip()
        if not origin:
            continue

        parsed = urlsplit(origin)
        if (
            origin == "*"
            or parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or parsed.username
            or parsed.password
        ):
            raise RuntimeError(
                "PAYGUARD_CORS_ORIGINS must contain explicit HTTP(S) origins "
                "without paths, credentials, query strings, or wildcards"
            )

        normalized = f"{parsed.scheme}://{parsed.netloc}"
        if normalized not in origins:
            origins.append(normalized)

    return tuple(origins)


def _parse_positive_int(
        value: str,
        *,
        name: str,
        minimum: int,
        maximum: int,
) -> int:
    try:
        parsed = int(value.strip())
    except (AttributeError, ValueError) as exc:
        raise RuntimeError(f"{name} must be an integer") from exc

    if parsed < minimum or parsed > maximum:
        raise RuntimeError(
            f"{name} must be between {minimum} and {maximum}"
        )
    return parsed


def load_settings(
        environ: Mapping[str, str] | None = None,
) -> AppSettings:
    values = environ if environ is not None else os.environ

    environment = values.get("PAYGUARD_ENV", "production").strip().lower()
    if environment not in _ALLOWED_ENVIRONMENTS:
        raise RuntimeError(
            "PAYGUARD_ENV must be development, test, or production"
        )

    database_url = (values.get("DATABASE_URL") or "").strip()
    service_api_key = (values.get("PAYGUARD_API_KEY") or "").strip() or None
    admin_api_key = (values.get("PAYGUARD_ADMIN_API_KEY") or "").strip() or None

    if environment == "production":
        if not database_url:
            raise RuntimeError(
                "DATABASE_URL must be explicitly configured in production"
            )
        if not service_api_key:
            raise RuntimeError(
                "PAYGUARD_API_KEY must be configured in production"
            )
        if not admin_api_key:
            raise RuntimeError(
                "PAYGUARD_ADMIN_API_KEY must be configured in production"
            )

    if service_api_key is not None and len(service_api_key) < 32:
        raise RuntimeError(
            "PAYGUARD_API_KEY must contain at least 32 characters"
        )
    if admin_api_key is not None and len(admin_api_key) < 32:
        raise RuntimeError(
            "PAYGUARD_ADMIN_API_KEY must contain at least 32 characters"
        )

    enable_test_endpoints = _parse_bool(
        values.get("PAYGUARD_ENABLE_TEST_ENDPOINTS", "false"),
        name="PAYGUARD_ENABLE_TEST_ENDPOINTS",
    )
    test_reset_token = (
        values.get("PAYGUARD_TEST_RESET_TOKEN") or ""
    ).strip() or None

    if enable_test_endpoints and environment != "test":
        raise RuntimeError(
            "PAYGUARD_ENABLE_TEST_ENDPOINTS can only be enabled when "
            "PAYGUARD_ENV=test"
        )
    if enable_test_endpoints and (
        test_reset_token is None or len(test_reset_token) < 32
    ):
        raise RuntimeError(
            "PAYGUARD_TEST_RESET_TOKEN must contain at least 32 characters "
            "when test endpoints are enabled"
        )

    max_request_bytes = _parse_positive_int(
        values.get("PAYGUARD_MAX_REQUEST_BYTES", "65536"),
        name="PAYGUARD_MAX_REQUEST_BYTES",
        minimum=1024,
        maximum=1048576,
    )

    cors_origins = _parse_cors_origins(
        values.get("PAYGUARD_CORS_ORIGINS"),
        environment=environment,
    )

    return AppSettings(
        environment=environment,
        cors_origins=cors_origins,
        service_api_key=service_api_key,
        admin_api_key=admin_api_key,
        enable_test_endpoints=enable_test_endpoints,
        test_reset_token=test_reset_token,
        docs_enabled=environment != "production",
        failure_simulation_enabled=environment in {"development", "test"},
        max_request_bytes=max_request_bytes,
    )


settings = load_settings()
