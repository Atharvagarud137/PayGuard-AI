import logging
import re
from typing import Any

from starlette.responses import JSONResponse


_PAN_PATTERN = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
_SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|admin[_-]?api[_-]?key|test[_-]?reset[_-]?token|"
    r"authorization|access[_-]?token|refresh[_-]?token|password|secret|cvv|cvc)"
    r"(\s*[:=]\s*)([^\s,;]+)"
)
_BEARER_PATTERN = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")


def redact_sensitive_text(value: Any) -> str:
    """Redact payment-card-like numbers and common credential formats."""
    text = str(value)
    text = _BEARER_PATTERN.sub("Bearer [REDACTED]", text)
    text = _PAN_PATTERN.sub("[REDACTED-PAN]", text)
    return _SECRET_ASSIGNMENT_PATTERN.sub(
        lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]",
        text,
    )


class RedactingFilter(logging.Filter):
    """Ensure application log messages do not retain common secret values."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.msg = redact_sensitive_text(record.getMessage())
            record.args = ()
            record.exc_info = None
            record.exc_text = None
            record.stack_info = None
        except Exception:
            # A logging filter must never break the request being processed.
            record.msg = "Application log message suppressed"
            record.args = ()
        return True


class _RequestBodyTooLarge(Exception):
    pass


class RequestSizeLimitMiddleware:
    """Reject request bodies larger than the configured application limit."""

    def __init__(self, app, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.lower(): value
            for key, value in scope.get("headers", [])
        }
        content_length = headers.get(b"content-length")

        if content_length is not None:
            try:
                declared_length = int(content_length)
            except ValueError:
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length"},
                )
                await response(scope, receive, send)
                return

            if declared_length < 0:
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length"},
                )
                await response(scope, receive, send)
                return

            if declared_length > self.max_bytes:
                response = JSONResponse(
                    status_code=413,
                    content={"detail": "Request body is too large"},
                )
                await response(scope, receive, send)
                return

        received_bytes = 0

        async def limited_receive():
            nonlocal received_bytes
            message = await receive()
            if message.get("type") == "http.request":
                received_bytes += len(message.get("body", b""))
                if received_bytes > self.max_bytes:
                    raise _RequestBodyTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _RequestBodyTooLarge:
            response = JSONResponse(
                status_code=413,
                content={"detail": "Request body is too large"},
            )
            await response(scope, receive, send)


class SecurityHeadersMiddleware:
    """Add conservative browser-facing security and cache headers."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message):
            if message.get("type") == "http.response.start":
                headers = list(message.get("headers", []))
                existing = {key.lower() for key, _ in headers}
                additions = [
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"no-referrer"),
                    (
                        b"permissions-policy",
                        b"camera=(), microphone=(), geolocation=()",
                    ),
                ]
                if scope.get("path", "").startswith("/api/"):
                    additions.append((b"cache-control", b"no-store"))
                if scope.get("scheme") == "https":
                    additions.append((
                        b"strict-transport-security",
                        b"max-age=31536000; includeSubDomains",
                    ))

                for key, value in additions:
                    if key not in existing:
                        headers.append((key, value))
                        existing.add(key)

                message = {**message, "headers": headers}

            await send(message)

        await self.app(scope, receive, send_with_security_headers)
