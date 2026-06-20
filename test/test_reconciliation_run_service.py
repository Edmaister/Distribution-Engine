from decimal import Decimal

import pytest

from services.reconciliation_run_service import (
    run_reconciliation,
)


@pytest.mark.asyncio
async def test_run_reconciliation(monkeypatch):
    created_run = {}
    created_results = {}

    async def fake_create_reconciliation_run(**kwargs):
        created_run.update(kwargs)
        return {
            "run_id": "run-123",
            **kwargs,
        }

    async def fake_create_reconciliation_results(**kwargs):
        created_results.update(kwargs)
        return len(kwargs["results"])

    import services.reconciliation_run_service as mod

    monkeypatch.setattr(
        mod,
        "create_reconciliation_run",
        fake_create_reconciliation_run,
    )

    monkeypatch.setattr(
        mod,
        "create_reconciliation_results",
        fake_create_reconciliation_results,
    )

    result = await run_reconciliation(
        tenant_code="FNB",
        provider_key="CASH_PROVIDER",
        platform_records=[
            {
                "provider_reference": "REF-1",
                "amount": Decimal("100"),
            },
            {
                "provider_reference": "REF-2",
                "amount": Decimal("200"),
            },
        ],
        provider_records=[
            {
                "provider_reference": "REF-1",
                "amount": Decimal("100"),
            }
        ],
    )

    assert result["run_id"] == "run-123"
    assert result["provider_key"] == "CASH_PROVIDER"

    assert result["summary"]["matched"] == 1
    assert result["summary"]["missing"] == 1
    assert result["summary"]["duplicate"] == 0
    assert result["summary"]["overpaid"] == 0
    assert result["summary"]["underpaid"] == 0

    assert len(result["results"]) == 2

    assert created_run["tenant_code"] == "FNB"
    assert created_run["provider_key"] == "CASH_PROVIDER"
    assert created_run["total_records"] == 2
    assert created_run["matched_count"] == 1
    assert created_run["missing_count"] == 1

    assert created_results["run_id"] == "run-123"
    assert len(created_results["results"]) == 2