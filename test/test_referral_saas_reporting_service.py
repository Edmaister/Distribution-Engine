from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from services import referral_saas_reporting_service as svc
from services import tenant_safe_analytics_service as analytics


def _overview() -> dict:
    return {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "campaign_code": "CAMP001",
        "distributors": {"total_count": 2, "active_count": 1},
        "opportunities": {"total_count": 3, "published_count": 2},
        "routes": {
            "total_count": 8,
            "accepted_count": 6,
            "acceptance_rate": Decimal("0.7500"),
        },
        "commissions": {
            "event_count": 5,
            "total_commission_amount": Decimal("123.45"),
        },
        "conversions": {
            "linked_count": 4,
            "completed_count": 3,
            "completion_rate": Decimal("0.7500"),
            "attribution_rate": Decimal("0.9000"),
        },
        "wallets": {
            "wallet_count": 1,
            "current_balance": Decimal("999.99"),
        },
        "governance": {"open_dispute_count": 1},
    }


def test_referral_saas_report_catalog_exposes_available_and_future_reports():
    catalog = svc.list_referral_saas_report_catalog()

    by_type = {item["report_type"]: item for item in catalog}
    assert by_type["campaign_performance"]["status"] == "AVAILABLE"
    assert by_type["campaign_performance"]["source_report_type"] == (
        analytics.REPORT_DISTRIBUTION_OVERVIEW
    )
    assert by_type["referral_funnel"]["status"] == "NOT_IMPLEMENTED"
    assert by_type["safe_status_distribution"]["metric_class"] == "DERIVED_STATUS"


@pytest.mark.asyncio
async def test_campaign_performance_maps_existing_analytics_to_referral_saas_report(
    monkeypatch,
):
    calls: list[dict] = []

    async def fake_get_marketplace_overview(**kwargs):
        calls.append(kwargs)
        return _overview()

    monkeypatch.setattr(
        analytics,
        "get_marketplace_overview",
        fake_get_marketplace_overview,
    )
    start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    end = datetime(2026, 7, 12, tzinfo=timezone.utc)

    report = await svc.get_referral_saas_report(
        tenant_code="fnb",
        report_type="campaign_performance",
        dimensions=["campaign_ref", "metric_name"],
        filters={
            "campaign_ref": "CAMP001",
            "sponsor_code": "BOXER",
            "referrer_ucn": "900001",
            "raw_customer_identifier": "secret-customer",
        },
        data_window_start=start,
        data_window_end=end,
    )

    assert calls == [
        {
            "tenant_code": "FNB",
            "sponsor_code": "BOXER",
            "campaign_code": "CAMP001",
        }
    ]
    assert report["report_type"] == "campaign_performance"
    assert report["source_report_type"] == "distribution_overview"
    assert report["tenant_scope"] == "FNB"
    assert report["metric_class"] == "OPERATIONAL"
    assert report["filters"] == {
        "campaign_ref": "CAMP001",
        "campaign_code": "CAMP001",
        "sponsor_code": "BOXER",
    }
    assert report["dimensions"] == ["campaign_ref", "metric_name"]
    assert report["data_window_start"] == start.isoformat()
    assert report["data_window_end"] == end.isoformat()
    assert report["reconciliation_status"] == "NOT_APPLICABLE"
    assert report["export_status"] == "NOT_IMPLEMENTED"
    assert set(report["redactions"]) == {
        "raw_customer_identifier",
        "referrer_ucn",
    }

    metric_names = {metric["name"] for metric in report["metrics"]}
    assert "campaigns.ready_count" in metric_names
    assert "referrals.completed_count" in metric_names
    assert "conversion.attribution_rate" in metric_names
    assert "wallets.wallet_count" not in metric_names
    assert "governance.open_dispute_count" not in metric_names
    assert "commissions.total_commission_amount" not in metric_names
    assert "900001" not in str(report)
    assert "secret-customer" not in str(report)


@pytest.mark.asyncio
async def test_future_referral_saas_report_types_remain_explicitly_unimplemented():
    with pytest.raises(
        ValueError,
        match="Referral SaaS report_type not implemented: referral_funnel",
    ):
        await svc.get_referral_saas_report(
            tenant_code="FNB",
            report_type="referral_funnel",
        )


@pytest.mark.asyncio
async def test_unknown_referral_saas_report_type_is_rejected():
    with pytest.raises(ValueError, match="Unsupported Referral SaaS report_type"):
        await svc.get_referral_saas_report(
            tenant_code="FNB",
            report_type="raw_customer_export",
        )


@pytest.mark.asyncio
async def test_referral_saas_report_rejects_unsupported_dimensions_and_filters():
    with pytest.raises(
        ValueError,
        match="Unsupported Referral SaaS report dimension",
    ):
        await svc.get_referral_saas_report(
            tenant_code="FNB",
            report_type="campaign_performance",
            dimensions=["raw_ucn"],
        )

    with pytest.raises(ValueError, match="Unsupported Referral SaaS report filter"):
        await svc.get_referral_saas_report(
            tenant_code="FNB",
            report_type="campaign_performance",
            filters={"opportunity_id": "OPP-1"},
        )
