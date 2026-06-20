from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


REQUIRED_PROVIDER_STATEMENT_FIELDS = {
    "provider_reference",
    "amount",
}


def _to_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid amount: {value}") from exc


def _normalize_provider_reference(value: Any) -> str:
    provider_reference = str(value or "").strip()

    if not provider_reference:
        raise ValueError("provider_reference is required")

    return provider_reference


def normalize_provider_statement_record(
    record: dict[str, Any],
) -> dict[str, Any]:
    missing_fields = [
        field
        for field in REQUIRED_PROVIDER_STATEMENT_FIELDS
        if field not in record
    ]

    if missing_fields:
        raise ValueError(
            f"Missing required provider statement fields: {missing_fields}"
        )

    return {
        "provider_reference": _normalize_provider_reference(
            record.get("provider_reference")
        ),
        "amount": _to_decimal(record.get("amount")),
        "currency": str(record.get("currency") or "ZAR").strip().upper(),
        "raw_record": record,
    }


def import_provider_statement(
    *,
    provider_key: str,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    if not provider_key or not provider_key.strip():
        raise ValueError("provider_key is required")

    normalized_records = []
    errors = []

    for index, record in enumerate(records):
        try:
            normalized_records.append(
                normalize_provider_statement_record(record)
            )
        except Exception as exc:
            errors.append(
                {
                    "index": index,
                    "error": str(exc),
                    "record": record,
                }
            )

    return {
        "provider_key": provider_key.strip(),
        "received_count": len(records),
        "imported_count": len(normalized_records),
        "error_count": len(errors),
        "records": normalized_records,
        "errors": errors,
    }