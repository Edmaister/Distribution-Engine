from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from services import tenant_safe_analytics_service as svc


def _overview() -> dict:
    return {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "campaign_code": "CAMP001",
        "distributors": {"total_count": 10, "active_count": 8},
        "opportunities": {"total_count": 4, "published_count": 3},
        "routes": {
            "total_count": 20,
            "accepted_count": 5,
            "acceptance_rate": Decimal("0.2500"),
        },
        "commissions": {
            "event_count": 3,
            "total_commission_amount": Decimal("150.00"),
        },
        "conversions": {
            "linked_count": 4,
            "completed_count": 2,
            "completion_rate": Decimal("0.5000"),
            "attribution_rate": Decimal("0.8000"),
        },
        "wallets": {
            "wallet_count": 2,
            "current_balance": Decimal("100.00"),
        },
        "governance": {"open_dispute_count": 1},
    }


@pytest.mark.asyncio
async def test_distribution_overview_returns_tenant_safe_operational_metrics(
    monkeypatch,
):
    calls = []

    async def fake_get_marketplace_overview(**kwargs):
        calls.append(kwargs)
        return _overview()

    monkeypatch.setattr(
        svc,
        "get_marketplace_overview",
        fake_get_marketplace_overview,
    )

    result = await svc.get_tenant_safe_analytics_report(
        tenant_code="fnb",
        report_type="distribution_overview",
        dimensions=["tenant_code", "campaign_code", "metric_name"],
        filters={
            "sponsor_code": "BOXER",
            "campaign_code": "CAMP001",
            "referrer_ucn": "900001",
        },
    )

    assert result["report_type"] == "distribution_overview"
    assert result["tenant_scope"] == "FNB"
    assert result["metric_class"] == "OPERATIONAL"
    assert result["filters"] == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "campaign_code": "CAMP001",
    }
    assert result["redactions"] == ["referrer_ucn"]
    assert result["freshness"]["status"] == "FRESH"
    assert result["reconciliation_status"] == "NOT_APPLICABLE"
    assert calls == [
        {
            "tenant_code": "FNB",
            "sponsor_code": "BOXER",
            "campaign_code": "CAMP001",
        }
    ]

    metric_names = {metric["name"] for metric in result["metrics"]}
    assert "routes.acceptance_rate" in metric_names
    assert "wallets.wallet_count" in metric_names
    assert "commissions.total_commission_amount" not in metric_names
    assert "wallets.current_balance" not in metric_names
    assert "900001" not in str(result)


@pytest.mark.asyncio
async def test_reconciliation_summary_keeps_ledger_metric_class(monkeypatch):
    calls = []

    async def fake_get_reconciliation_metrics(**kwargs):
        calls.append(kwargs)
        return {
            "total_runs": 1,
            "total_records": 100,
            "matched_count": 90,
            "missing_count": 5,
            "duplicate_count": 2,
            "overpaid_count": 2,
            "underpaid_count": 1,
            "match_rate": 90.0,
        }

    monkeypatch.setattr(
        svc,
        "get_reconciliation_metrics",
        fake_get_reconciliation_metrics,
    )

    result = await svc.get_tenant_safe_analytics_report(
        tenant_code="FNB",
        report_type="reconciliation_summary",
        dimensions=["tenant_code", "provider_key", "reconciliation_status"],
        filters={"provider_key": "BANK_FILE"},
    )

    assert result["metric_class"] == "LEDGER_BACKED"
    assert result["reconciliation_status"] == "PARTIAL"
    assert calls == [{"tenant_code": "FNB", "provider_key": "BANK_FILE"}]
    assert all(
        metric["metric_class"] == "LEDGER_BACKED" for metric in result["metrics"]
    )
    assert result["metrics"][-1]["unit"] == "percent"


@pytest.mark.asyncio
async def test_reconciliation_summary_maps_full_match(monkeypatch):
    async def fake_get_reconciliation_metrics(**kwargs):
        return {
            "total_runs": 1,
            "total_records": 10,
            "matched_count": 10,
            "match_rate": 100.0,
        }

    monkeypatch.setattr(
        svc,
        "get_reconciliation_metrics",
        fake_get_reconciliation_metrics,
    )

    result = await svc.get_tenant_safe_analytics_report(
        tenant_code="FNB",
        report_type="reconciliation_summary",
    )

    assert result["reconciliation_status"] == "MATCHED"


@pytest.mark.asyncio
async def test_unknown_report_type_is_rejected():
    with pytest.raises(ValueError, match="Unsupported analytics report_type"):
        await svc.get_tenant_safe_analytics_report(
            tenant_code="FNB",
            report_type="raw_customer_export",
        )


@pytest.mark.asyncio
async def test_unknown_dimension_is_rejected():
    with pytest.raises(ValueError, match="Unsupported analytics dimension"):
        await svc.get_tenant_safe_analytics_report(
            tenant_code="FNB",
            report_type="distribution_overview",
            dimensions=["tenant_code", "raw_ucn"],
        )


@pytest.mark.asyncio
async def test_unknown_filter_is_rejected():
    with pytest.raises(ValueError, match="Unsupported analytics filter"):
        await svc.get_tenant_safe_analytics_report(
            tenant_code="FNB",
            report_type="distribution_overview",
            filters={"opportunity_id": "OPP-1"},
        )


@pytest.mark.asyncio
async def test_tenant_code_is_required():
    with pytest.raises(ValueError, match="tenant_code is required"):
        await svc.get_tenant_safe_analytics_report(
            tenant_code="",
            report_type="distribution_overview",
        )


@pytest.mark.asyncio
async def test_invalid_data_window_is_rejected():
    when = datetime(2026, 6, 25, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="data_window_start must be before"):
        await svc.get_tenant_safe_analytics_report(
            tenant_code="FNB",
            report_type="distribution_overview",
            data_window_start=when,
            data_window_end=when,
        )


@pytest.mark.asyncio
async def test_source_failure_returns_unavailable_freshness(monkeypatch):
    async def fake_get_marketplace_overview(**kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        svc,
        "get_marketplace_overview",
        fake_get_marketplace_overview,
    )

    result = await svc.get_tenant_safe_analytics_report(
        tenant_code="FNB",
        report_type="distribution_overview",
    )

    assert result["metrics"] == []
    assert result["freshness"]["status"] == "UNAVAILABLE"
    assert result["source_warnings"][0]["code"] == "SOURCE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_data_window_is_reflected(monkeypatch):
    async def fake_get_marketplace_overview(**kwargs):
        return _overview()

    monkeypatch.setattr(
        svc,
        "get_marketplace_overview",
        fake_get_marketplace_overview,
    )
    start = datetime(2026, 6, 1, tzinfo=timezone.utc)
    end = datetime(2026, 6, 25, tzinfo=timezone.utc)

    result = await svc.get_tenant_safe_analytics_report(
        tenant_code="FNB",
        report_type="distribution_overview",
        data_window_start=start,
        data_window_end=end,
    )

    assert result["data_window_start"] == start.isoformat()
    assert result["data_window_end"] == end.isoformat()
    assert result["freshness"]["data_window_start"] == start.isoformat()
    assert result["freshness"]["data_window_end"] == end.isoformat()
