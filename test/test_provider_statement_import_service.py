from decimal import Decimal

import pytest

from services.provider_statement_import_service import (
    import_provider_statement,
    normalize_provider_statement_record,
)


def test_normalize_provider_statement_record():
    result = normalize_provider_statement_record(
        {
            "provider_reference": " REF-123 ",
            "amount": "100.50",
            "currency": "zar",
        }
    )

    assert result["provider_reference"] == "REF-123"
    assert result["amount"] == Decimal("100.50")
    assert result["currency"] == "ZAR"
    assert result["raw_record"]["provider_reference"] == " REF-123 "


def test_import_provider_statement_splits_valid_and_invalid_records():
    result = import_provider_statement(
        provider_key="CASH_PROVIDER",
        records=[
            {
                "provider_reference": "REF-001",
                "amount": "100.00",
            },
            {
                "provider_reference": "",
                "amount": "200.00",
            },
            {
                "provider_reference": "REF-003",
                "amount": "invalid",
            },
        ],
    )

    assert result["provider_key"] == "CASH_PROVIDER"
    assert result["received_count"] == 3
    assert result["imported_count"] == 1
    assert result["error_count"] == 2
    assert result["records"][0]["provider_reference"] == "REF-001"
    assert result["records"][0]["amount"] == Decimal("100.00")


def test_import_provider_statement_requires_provider_key():
    with pytest.raises(ValueError, match="provider_key is required"):
        import_provider_statement(
            provider_key="",
            records=[],
        )