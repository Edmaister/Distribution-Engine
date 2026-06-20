from decimal import Decimal

from services.fulfilment.settlement.reconciliation import reconcile_settlements
from services.fulfilment.settlement.reconciliation_status import ReconciliationStatus


def test_reconcile_settlements_classifies_results():
    platform_records = [
        {
            "provider_reference": "REF-MATCHED",
            "amount": Decimal("100.00"),
        },
        {
            "provider_reference": "REF-MISSING",
            "amount": Decimal("200.00"),
        },
        {
            "provider_reference": "REF-OVERPAID",
            "amount": Decimal("300.00"),
        },
        {
            "provider_reference": "REF-UNDERPAID",
            "amount": Decimal("400.00"),
        },
        {
            "provider_reference": "REF-DUPLICATE",
            "amount": Decimal("500.00"),
        },
    ]

    provider_records = [
        {
            "provider_reference": "REF-MATCHED",
            "amount": Decimal("100.00"),
        },
        {
            "provider_reference": "REF-OVERPAID",
            "amount": Decimal("350.00"),
        },
        {
            "provider_reference": "REF-UNDERPAID",
            "amount": Decimal("350.00"),
        },
        {
            "provider_reference": "REF-DUPLICATE",
            "amount": Decimal("500.00"),
        },
        {
            "provider_reference": "REF-DUPLICATE",
            "amount": Decimal("500.00"),
        },
    ]

    results = reconcile_settlements(
        platform_records=platform_records,
        provider_records=provider_records,
    )

    result_by_ref = {
        item["provider_reference"]: item
        for item in results
    }

    assert result_by_ref["REF-MATCHED"]["status"] == ReconciliationStatus.MATCHED.value
    assert result_by_ref["REF-MISSING"]["status"] == ReconciliationStatus.MISSING.value
    assert result_by_ref["REF-OVERPAID"]["status"] == ReconciliationStatus.OVERPAID.value
    assert result_by_ref["REF-UNDERPAID"]["status"] == ReconciliationStatus.UNDERPAID.value
    assert result_by_ref["REF-DUPLICATE"]["status"] == ReconciliationStatus.DUPLICATE.value


def test_reconcile_settlements_handles_missing_provider_reference():
    platform_records = [
        {
            "provider_reference": None,
            "amount": Decimal("100.00"),
        }
    ]

    provider_records = []

    results = reconcile_settlements(
        platform_records=platform_records,
        provider_records=provider_records,
    )

    assert results[0]["provider_reference"] is None
    assert results[0]["status"] == ReconciliationStatus.MISSING.value
    assert results[0]["platform_amount"] == Decimal("100.00")
    assert results[0]["provider_amount"] is None