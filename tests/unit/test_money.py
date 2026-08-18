from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models import (
    AuthorizeRequest,
    CaptureRequest,
    RefundRequest,
)


def test_decimal_arithmetic_is_exact():
    result = (
            Decimal("0.10")
            + Decimal("0.20")
            - Decimal("0.30")
    )

    assert result == Decimal("0.00")


def test_two_decimal_amount_is_valid():
    request = AuthorizeRequest(
        card_id="card-123",
        amount=Decimal("10.25"),
        merchant_id="merchant-123",
    )

    assert request.amount == Decimal("10.25")


def test_more_than_two_decimal_places_is_rejected():
    with pytest.raises(ValidationError):
        AuthorizeRequest(
            card_id="card-123",
            amount=Decimal("10.255"),
            merchant_id="merchant-123",
        )


def test_zero_authorization_is_rejected():
    with pytest.raises(ValidationError):
        AuthorizeRequest(
            card_id="card-123",
            amount=Decimal("0.00"),
            merchant_id="merchant-123",
        )


def test_negative_authorization_is_rejected():
    with pytest.raises(ValidationError):
        AuthorizeRequest(
            card_id="card-123",
            amount=Decimal("-10.00"),
            merchant_id="merchant-123",
        )


def test_capture_amount_uses_decimal():
    request = CaptureRequest(
        capture_amount=Decimal("33.33"),
    )

    assert request.capture_amount == Decimal("33.33")


def test_refund_amount_uses_decimal():
    request = RefundRequest(
        refund_amount=Decimal("10.01"),
    )

    assert request.refund_amount == Decimal("10.01")