import pytest

from services import finance_metrics_service as mod


@pytest.mark.asyncio
async def test_get_reconciliation_metrics(monkeypatch):
    async def fake_list_reconciliation_runs(**kwargs):
        return [
            {
                "total_records": 100,
                "matched_count": 90,
                "missing_count": 5,
                "duplicate_count": 2,
                "overpaid_count": 2,
                "underpaid_count": 1,
            }
        ]

    monkeypatch.setattr(
        mod,
        "list_reconciliation_runs",
        fake_list_reconciliation_runs,
    )

    result = await mod.get_reconciliation_metrics()

    assert result["total_runs"] == 1
    assert result["total_records"] == 100
    assert result["matched_count"] == 90
    assert result["match_rate"] == 90.0

@pytest.mark.asyncio
async def test_get_reconciliation_metrics_handles_no_records(monkeypatch):
    async def fake_list_reconciliation_runs(**kwargs):
        return []

    monkeypatch.setattr(
        mod,
        "list_reconciliation_runs",
        fake_list_reconciliation_runs,
    )

    result = await mod.get_reconciliation_metrics()

    assert result["total_runs"] == 0
    assert result["total_records"] == 0
    assert result["matched_count"] == 0
    assert result["match_rate"] == 0