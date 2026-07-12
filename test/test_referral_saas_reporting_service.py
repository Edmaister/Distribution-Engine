from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from services import referral_saas_reporting_service as svc
from services import tenant_safe_analytics_service as analytics


class FakeConnection:
    def __init__(
        self,
        *,
        recorded_rows: list[dict] | None = None,
        failure_rows: list[dict] | None = None,
    ):
        self.recorded_rows = recorded_rows or [
            {
                "event_type": "ACCOUNT_OPENED",
                "source_system": "PROGRESS_API",
                "recorded_count": 3,
            }
        ]
        self.failure_rows = failure_rows or [
            {
                "event_type": "ACCOUNT_OPENED",
                "source_system": "SQS",
                "failure_category": "TRANSIENT",
                "status": "OPEN",
                "failed_count": 2,
                "retry_attempt_count": 5,
            },
            {
                "event_type": "FUNDED",
                "source_system": "SQS",
                "failure_category": "DATA_QUALITY",
                "status": "RESOLVED",
                "failed_count": 1,
                "retry_attempt_count": 1,
            },
        ]
        self.fetch_calls: list[tuple[str, tuple]] = []

    async def fetch(self, query, *params):
        self.fetch_calls.append((query, params))
        if "FROM referral_progress_events" in query:
            return self.recorded_rows
        if "FROM referral_event_failures" in query:
            return self.failure_rows
        raise AssertionError(f"unexpected query: {query}")


class FakeDbConnection:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


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
    assert by_type["referral_funnel"]["status"] == "AVAILABLE"
    assert by_type["referral_funnel"]["source_report_type"] == (
        analytics.REPORT_DISTRIBUTION_OVERVIEW
    )
    assert by_type["progress_event_health"]["status"] == "AVAILABLE"
    assert by_type["progress_event_health"]["source_report_type"] == (
        svc.SOURCE_PROGRESS_EVENT_HEALTH
    )
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
async def test_referral_funnel_maps_existing_analytics_with_partial_source_warning(
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

    report = await svc.get_referral_saas_report(
        tenant_code="fnb",
        report_type="referral_funnel",
        dimensions=["campaign_ref", "metric_name", "progress_band"],
        filters={"campaign_ref": "CAMP001"},
    )

    assert calls == [
        {
            "tenant_code": "FNB",
            "sponsor_code": None,
            "campaign_code": "CAMP001",
        }
    ]
    assert report["report_type"] == "referral_funnel"
    assert report["source_report_type"] == "distribution_overview"
    assert report["filters"] == {
        "campaign_ref": "CAMP001",
        "campaign_code": "CAMP001",
    }
    assert report["dimensions"] == ["campaign_ref", "metric_name", "progress_band"]
    assert report["export_status"] == "NOT_IMPLEMENTED"
    assert report["source_warnings"] == [
        {
            "code": "PARTIAL_SOURCE_COVERAGE",
            "message": (
                "Referral funnel currently uses tenant-safe distribution "
                "overview metrics; code-issued, validation-state, and "
                "progress-milestone stage counts need dedicated follow-up "
                "report sources before they can be promised."
            ),
        }
    ]

    metric_names = {metric["name"] for metric in report["metrics"]}
    assert "funnel.linked_route_count" in metric_names
    assert "funnel.accepted_route_count" in metric_names
    assert "funnel.completed_referral_count" in metric_names
    assert "funnel.attribution_rate" in metric_names
    assert "campaigns.ready_count" not in metric_names
    assert "wallets.wallet_count" not in metric_names
    assert "governance.open_dispute_count" not in metric_names
    assert "commissions.total_commission_amount" not in metric_names


@pytest.mark.asyncio
async def test_progress_event_health_maps_tenant_scoped_progress_sources(monkeypatch):
    conn = FakeConnection()
    monkeypatch.setattr(svc, "db_connection", lambda: FakeDbConnection(conn))
    start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    end = datetime(2026, 7, 12, tzinfo=timezone.utc)

    report = await svc.get_referral_saas_report(
        tenant_code="fnb",
        report_type="progress_event_health",
        dimensions=["event_type", "source_system", "metric_name"],
        filters={
            "event_type": "ACCOUNT_OPENED",
            "source_system": "SQS",
            "referrer_ucn": "900001",
            "raw_payload": "secret",
        },
        data_window_start=start,
        data_window_end=end,
    )

    assert len(conn.fetch_calls) == 2
    assert "JOIN referral_instances ri" in conn.fetch_calls[0][0]
    assert "ri.tenant_code = $1" in conn.fetch_calls[0][0]
    assert conn.fetch_calls[0][1] == (
        "FNB",
        "ACCOUNT_OPENED",
        "SQS",
        start,
        end,
    )
    assert conn.fetch_calls[1][1] == (
        "FNB",
        "ACCOUNT_OPENED",
        "SQS",
        None,
        None,
        start,
        end,
    )
    assert report["report_type"] == "progress_event_health"
    assert report["source_report_type"] == "referral_progress_event_health"
    assert report["tenant_scope"] == "FNB"
    assert report["filters"] == {
        "tenant_code": "FNB",
        "event_type": "ACCOUNT_OPENED",
        "source_system": "SQS",
    }
    assert report["dimensions"] == ["event_type", "source_system", "metric_name"]
    assert report["data_window_start"] == start.isoformat()
    assert report["data_window_end"] == end.isoformat()
    assert report["export_status"] == "NOT_IMPLEMENTED"
    assert set(report["redactions"]) == {"raw_payload", "referrer_ucn"}

    metric_names = {metric["name"] for metric in report["metrics"]}
    assert "progress.events_recorded_count" in metric_names
    assert "progress.events_failed_count" in metric_names
    assert "progress.retry_attempt_count" in metric_names
    assert "progress.events_open_failure_count" in metric_names
    assert "progress.events_resolved_failure_count" in metric_names
    assert "progress.events_deduped_count" not in metric_names
    assert "900001" not in str(report)
    assert "secret" not in str(report)
    assert {warning["code"] for warning in report["source_warnings"]} == {
        "PARTIAL_SOURCE_COVERAGE",
        "UNSCOPED_FAILURES_EXCLUDED",
    }


@pytest.mark.asyncio
async def test_progress_event_health_returns_unavailable_when_source_fails(monkeypatch):
    class BrokenConnection:
        async def fetch(self, query, *params):
            raise RuntimeError("database unavailable")

    monkeypatch.setattr(svc, "db_connection", lambda: FakeDbConnection(BrokenConnection()))

    report = await svc.get_referral_saas_report(
        tenant_code="FNB",
        report_type="progress_event_health",
    )

    assert report["metrics"] == []
    assert report["freshness"]["status"] == "UNAVAILABLE"
    assert report["source_warnings"][0]["code"] == "SOURCE_UNAVAILABLE"
    assert {warning["code"] for warning in report["source_warnings"][1:]} == {
        "PARTIAL_SOURCE_COVERAGE",
        "UNSCOPED_FAILURES_EXCLUDED",
    }


@pytest.mark.asyncio
async def test_future_referral_saas_report_types_remain_explicitly_unimplemented():
    with pytest.raises(
        ValueError,
        match="Referral SaaS report_type not implemented: attribution_quality",
    ):
        await svc.get_referral_saas_report(
            tenant_code="FNB",
            report_type="attribution_quality",
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
