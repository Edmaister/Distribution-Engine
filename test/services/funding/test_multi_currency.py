from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from services.funding.multi_currency import (
    CurrencyPairError,
    _money,
    _validate_pair,
)


def test_money_rounds_half_up():
    assert _money(Decimal("54.005")) == Decimal("54.01")


def test_validate_pair_normalizes_currency_codes():
    assert _validate_pair("zar", "usd") == ("ZAR", "USD")


def test_validate_pair_rejects_same_currency():
    with pytest.raises(CurrencyPairError, match="must differ"):
        _validate_pair("ZAR", "zar")


def test_validate_pair_rejects_invalid_currency():
    with pytest.raises(CurrencyPairError, match="3-letter"):
        _validate_pair("ZA", "USD")
