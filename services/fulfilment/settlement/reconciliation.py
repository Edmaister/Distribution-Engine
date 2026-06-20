from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import Any

from services.fulfilment.settlement.reconciliation_status import ReconciliationStatus


def _to_decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def reconcile_settlements(
    *,
    platform_records: list[dict[str, Any]],
    provider_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    provider_reference_counts = Counter(
        item["provider_reference"]
        for item in provider_records
        if item.get("provider_reference")
    )

    provider_lookup = {
        item["provider_reference"]: item
        for item in provider_records
        if item.get("provider_reference")
    }

    results = []

    for platform_record in platform_records:
        provider_reference = platform_record.get("provider_reference")

        if not provider_reference:
            results.append(
                {
                    "provider_reference": None,
                    "status": ReconciliationStatus.MISSING.value,
                    "platform_amount": _to_decimal(platform_record.get("amount", 0)),
                    "provider_amount": None,
                }
            )
            continue

        if provider_reference_counts.get(provider_reference, 0) > 1:
            provider_record = provider_lookup.get(provider_reference)

            results.append(
                {
                    "provider_reference": provider_reference,
                    "status": ReconciliationStatus.DUPLICATE.value,
                    "platform_amount": _to_decimal(platform_record.get("amount", 0)),
                    "provider_amount": _to_decimal(provider_record.get("amount", 0))
                    if provider_record
                    else None,
                }
            )
            continue

        provider_record = provider_lookup.get(provider_reference)

        if provider_record is None:
            results.append(
                {
                    "provider_reference": provider_reference,
                    "status": ReconciliationStatus.MISSING.value,
                    "platform_amount": _to_decimal(platform_record.get("amount", 0)),
                    "provider_amount": None,
                }
            )
            continue

        platform_amount = _to_decimal(platform_record["amount"])
        provider_amount = _to_decimal(provider_record["amount"])

        if platform_amount == provider_amount:
            status = ReconciliationStatus.MATCHED
        elif provider_amount > platform_amount:
            status = ReconciliationStatus.OVERPAID
        else:
            status = ReconciliationStatus.UNDERPAID

        results.append(
            {
                "provider_reference": provider_reference,
                "status": status.value,
                "platform_amount": platform_amount,
                "provider_amount": provider_amount,
            }
        )

    return results