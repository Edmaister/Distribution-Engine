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
        link_rows: list[dict] | None = None,
        quality_rows: list[dict] | None = None,
        status_rows: list[dict] | None = None,
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
        self.link_rows = link_rows or [
            {
                "source_type": "REFERRAL_CODE",
                "link_code_status": "ISSUED",
                "campaign_code": None,
                "issued_period": "2026-07-01",
                "resolved_period": None,
                "link_code_count": 7,
            },
            {
                "source_type": "CAMPAIGN_CODE",
                "link_code_status": "EXPIRED",
                "campaign_code": "CAMP001",
                "issued_period": "2026-07-02",
                "resolved_period": None,
                "link_code_count": 1,
            },
            {
                "source_type": "CAMPAIGN_REFERRAL_LINK",
                "link_code_status": "LINKED",
                "campaign_code": "CAMP001",
                "issued_period": "2026-07-03",
                "resolved_period": "2026-07-03",
                "link_code_count": 4,
            },
            {
                "source_type": "ROUTE_REFERRAL_LINK",
                "link_code_status": "ACTIVE",
                "campaign_code": "CAMP001",
                "issued_period": "2026-07-04",
                "resolved_period": "2026-07-05",
                "link_code_count": 3,
            },
            {
                "source_type": "ROUTE_REFERRAL_LINK",
                "link_code_status": "VOIDED",
                "campaign_code": "CAMP002",
                "issued_period": "2026-07-04",
                "resolved_period": "2026-07-06",
                "link_code_count": 2,
            },
        ]
        self.quality_rows = quality_rows or [
            {
                "trace_status": "COMPLETE",
                "source_confidence": "HIGH",
                "warning_code": None,
                "attribution_source": "CAMPAIGN_REFERRAL_LINK",
                "campaign_code": "CAMP001",
                "outcome_count": 4,
            },
            {
                "trace_status": "PARTIAL",
                "source_confidence": "MEDIUM",
                "warning_code": None,
                "attribution_source": "ROUTE_REFERRAL_LINK",
                "campaign_code": "CAMP001",
                "outcome_count": 2,
            },
            {
                "trace_status": "MISSING_EVIDENCE",
                "source_confidence": "LOW",
                "warning_code": "NO_SOURCE_EVIDENCE",
                "attribution_source": "NONE",
                "campaign_code": None,
                "outcome_count": 1,
            },
            {
                "trace_status": "INCONSISTENT",
                "source_confidence": "CONFLICT",
                "warning_code": "SOURCE_CONFLICT",
                "attribution_source": "MULTIPLE",
                "campaign_code": "CAMP002",
                "outcome_count": 1,
            },
            {
                "trace_status": "UNATTRIBUTED",
                "source_confidence": "LOW",
                "warning_code": None,
                "attribution_source": "NONE",
                "campaign_code": None,
                "outcome_count": 3,
            },
        ]
        self.status_rows = status_rows or [
            {
                "viewer_role": "referrer",
                "source_family": "outcome",
                "safe_status": "PENDING",
                "product_status": "WAITING",
                "action_category": "WAITING_FOR_EVENT",
                "status_count": 5,
            },
            {
                "viewer_role": "referrer",
                "source_family": "outcome",
                "safe_status": "IN_PROGRESS",
                "product_status": "IN_PROGRESS",
                "action_category": "NONE",
                "status_count": 3,
            },
            {
                "viewer_role": "referrer",
                "source_family": "outcome",
                "safe_status": "FULFILLED",
                "product_status": "COMPLETED",
                "action_category": "NONE",
                "status_count": 2,
            },
            {
                "viewer_role": "referrer",
                "source_family": "outcome",
                "safe_status": "ACTION_REQUIRED",
                "product_status": "ACTION_NEEDED",
                "action_category": "CONTACT_SUPPORT",
                "status_count": 1,
            },
        ]
        self.fetch_calls: list[tuple[str, tuple]] = []

    async def fetch(self, query, *params):
        self.fetch_calls.append((query, params))
        if "FROM referral_progress_events" in query:
            return self.recorded_rows
        if "FROM referral_event_failures" in query:
            return self.failure_rows
        if "WITH link_sources AS" in query:
            return self.link_rows
        if "status_count" in query:
            return self.status_rows
        if "WITH base AS" in query:
            return self.quality_rows
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
    assert by_type["link_code_performance"]["status"] == "AVAILABLE"
    assert by_type["link_code_performance"]["source_report_type"] == (
        svc.SOURCE_LINK_CODE_PERFORMANCE
    )
    assert by_type["progress_event_health"]["status"] == "AVAILABLE"
    assert by_type["progress_event_health"]["source_report_type"] == (
        svc.SOURCE_PROGRESS_EVENT_HEALTH
    )
    assert by_type["attribution_quality"]["status"] == "AVAILABLE"
    assert by_type["attribution_quality"]["source_report_type"] == (
        svc.SOURCE_ATTRIBUTION_QUALITY
    )
    assert by_type["safe_status_distribution"]["status"] == "AVAILABLE"
    assert by_type["safe_status_distribution"]["source_report_type"] == (
        svc.SOURCE_SAFE_STATUS_DISTRIBUTION
    )


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
                "overview metrics; validation-state and "
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
async def test_link_code_performance_maps_current_link_code_evidence(monkeypatch):
    conn = FakeConnection()
    monkeypatch.setattr(svc, "db_connection", lambda: FakeDbConnection(conn))
    start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    end = datetime(2026, 7, 12, tzinfo=timezone.utc)

    report = await svc.get_referral_saas_report(
        tenant_code="fnb",
        report_type="link_code_performance",
        dimensions=["source_type", "link_code_status", "metric_name"],
        filters={
            "campaign_ref": "CAMP001",
            "source_type": "ROUTE_REFERRAL_LINK",
            "link_code_status": "ACTIVE",
            "referrer_ucn": "900001",
            "raw_code_payload": "secret",
        },
        data_window_start=start,
        data_window_end=end,
    )

    assert len(conn.fetch_calls) == 1
    query, params = conn.fetch_calls[0]
    assert "FROM referrer_codes rc" in query
    assert "FROM marketing_campaigns mc" in query
    assert "FROM campaign_referral_links crl" in query
    assert "FROM distribution_route_referral_links drl" in query
    assert "rc.tenant_code = $1" in query
    assert "ca.tenant_code = $1" in query
    assert "drl.tenant_code = $1" in query
    assert params == ("FNB", "CAMP001", "ROUTE_REFERRAL_LINK", "ACTIVE", start, end)
    assert report["report_type"] == "link_code_performance"
    assert report["source_report_type"] == "referral_link_code_performance"
    assert report["tenant_scope"] == "FNB"
    assert report["metric_class"] == "OPERATIONAL"
    assert report["filters"] == {
        "tenant_code": "FNB",
        "campaign_ref": "CAMP001",
        "campaign_code": "CAMP001",
        "link_code_status": "ACTIVE",
        "source_type": "ROUTE_REFERRAL_LINK",
    }
    assert report["dimensions"] == [
        "source_type",
        "link_code_status",
        "metric_name",
    ]
    assert report["data_window_start"] == start.isoformat()
    assert report["data_window_end"] == end.isoformat()
    assert report["export_status"] == "NOT_IMPLEMENTED"
    assert set(report["redactions"]) == {"raw_code_payload", "referrer_ucn"}
    assert report["source_warnings"] == [
        {
            "code": "PARTIAL_SOURCE_COVERAGE",
            "message": (
                "Link/code performance uses durable referral code, campaign "
                "code, campaign-referral link, and route-referral link "
                "sources. Composite-code compatibility evidence is not "
                "durable enough for aggregate reporting yet."
            ),
        }
    ]

    counts = {metric["name"]: metric["value"] for metric in report["metrics"]}
    assert counts == {
        "link_codes.active_count": 3,
        "link_codes.expired_count": 1,
        "link_codes.issued_count": 7,
        "link_codes.linked_count": 4,
        "link_codes.voided_count": 2,
    }
    assert all(metric["metric_class"] == "OPERATIONAL" for metric in report["metrics"])
    assert "900001" not in str(report)
    assert "secret" not in str(report)


@pytest.mark.asyncio
async def test_link_code_performance_returns_unavailable_when_source_fails(
    monkeypatch,
):
    class BrokenConnection:
        async def fetch(self, query, *params):
            raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        svc, "db_connection", lambda: FakeDbConnection(BrokenConnection())
    )

    report = await svc.get_referral_saas_report(
        tenant_code="FNB",
        report_type="link_code_performance",
    )

    assert report["metrics"] == []
    assert report["freshness"]["status"] == "UNAVAILABLE"
    assert report["source_warnings"][0]["code"] == "SOURCE_UNAVAILABLE"
    assert report["source_warnings"][1]["code"] == "PARTIAL_SOURCE_COVERAGE"


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
async def test_attribution_quality_maps_current_trace_evidence(monkeypatch):
    conn = FakeConnection()
    monkeypatch.setattr(svc, "db_connection", lambda: FakeDbConnection(conn))
    start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    end = datetime(2026, 7, 12, tzinfo=timezone.utc)

    report = await svc.get_referral_saas_report(
        tenant_code="fnb",
        report_type="attribution_quality",
        dimensions=["trace_status", "source_confidence", "metric_name"],
        filters={
            "campaign_ref": "CAMP001",
            "source_confidence": "HIGH",
            "trace_status": "COMPLETE",
            "raw_customer_identifier": "secret-customer",
        },
        data_window_start=start,
        data_window_end=end,
    )

    assert len(conn.fetch_calls) == 1
    query, params = conn.fetch_calls[0]
    assert "FROM referral_instances ri" in query
    assert "LEFT JOIN campaign_referral_links crl" in query
    assert "LEFT JOIN distribution_route_referral_links drl" in query
    assert "ri.tenant_code = $1" in query
    assert params == ("FNB", "CAMP001", start, end, "COMPLETE", "HIGH")
    assert report["report_type"] == "attribution_quality"
    assert report["source_report_type"] == "referral_attribution_quality"
    assert report["tenant_scope"] == "FNB"
    assert report["metric_class"] == "DERIVED_STATUS"
    assert report["filters"] == {
        "tenant_code": "FNB",
        "campaign_ref": "CAMP001",
        "campaign_code": "CAMP001",
        "source_confidence": "HIGH",
        "trace_status": "COMPLETE",
    }
    assert report["dimensions"] == [
        "trace_status",
        "source_confidence",
        "metric_name",
    ]
    assert report["data_window_start"] == start.isoformat()
    assert report["data_window_end"] == end.isoformat()
    assert report["export_status"] == "NOT_IMPLEMENTED"
    assert report["redactions"] == ["raw_customer_identifier"]
    assert report["source_warnings"] == [
        {
            "code": "DERIVED_TRACE_STATUS",
            "message": (
                "Attribution quality uses current referral, campaign-link, "
                "and route-link evidence to derive aggregate trace status; "
                "it does not expose raw outcome trace payloads."
            ),
        }
    ]

    metrics_by_name = {metric["name"]: metric for metric in report["metrics"]}
    assert metrics_by_name["attribution.complete_count"]["value"] == 4
    assert metrics_by_name["attribution.partial_count"]["value"] == 2
    assert metrics_by_name["attribution.missing_evidence_count"]["value"] == 1
    assert metrics_by_name["attribution.inconsistent_count"]["value"] == 1
    assert metrics_by_name["attribution.unattributed_count"]["value"] == 3
    assert all(
        metric["metric_class"] == "DERIVED_STATUS" for metric in report["metrics"]
    )
    assert "secret-customer" not in str(report)


@pytest.mark.asyncio
async def test_attribution_quality_returns_unavailable_when_source_fails(monkeypatch):
    class BrokenConnection:
        async def fetch(self, query, *params):
            raise RuntimeError("database unavailable")

    monkeypatch.setattr(svc, "db_connection", lambda: FakeDbConnection(BrokenConnection()))

    report = await svc.get_referral_saas_report(
        tenant_code="FNB",
        report_type="attribution_quality",
    )

    assert report["metrics"] == []
    assert report["freshness"]["status"] == "UNAVAILABLE"
    assert report["source_warnings"][0]["code"] == "SOURCE_UNAVAILABLE"
    assert report["source_warnings"][1]["code"] == "DERIVED_TRACE_STATUS"


@pytest.mark.asyncio
async def test_safe_status_distribution_maps_current_outcome_evidence(monkeypatch):
    conn = FakeConnection()
    monkeypatch.setattr(svc, "db_connection", lambda: FakeDbConnection(conn))
    start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    end = datetime(2026, 7, 12, tzinfo=timezone.utc)

    report = await svc.get_referral_saas_report(
        tenant_code="fnb",
        report_type="safe_status_distribution",
        dimensions=["viewer_role", "product_status", "metric_name"],
        filters={
            "viewer_role": "referrer",
            "product_status": "WAITING",
            "safe_status": "PENDING",
            "raw_ucn": "900001",
        },
        data_window_start=start,
        data_window_end=end,
    )

    assert len(conn.fetch_calls) == 1
    query, params = conn.fetch_calls[0]
    assert "FROM referral_instances ri" in query
    assert "ri.tenant_code = $1" in query
    assert params == ("FNB", "referrer", "PENDING", "WAITING", None, start, end)
    assert report["report_type"] == "safe_status_distribution"
    assert report["source_report_type"] == "referral_safe_status_distribution"
    assert report["tenant_scope"] == "FNB"
    assert report["metric_class"] == "DERIVED_STATUS"
    assert report["filters"] == {
        "tenant_code": "FNB",
        "viewer_role": "referrer",
        "product_status": "WAITING",
        "safe_status": "PENDING",
    }
    assert report["dimensions"] == ["viewer_role", "product_status", "metric_name"]
    assert report["data_window_start"] == start.isoformat()
    assert report["data_window_end"] == end.isoformat()
    assert report["export_status"] == "NOT_IMPLEMENTED"
    assert report["redactions"] == ["raw_ucn"]
    assert report["source_warnings"] == [
        {
            "code": "DERIVED_SAFE_STATUS",
            "message": (
                "Safe-status distribution is derived from tenant-scoped "
                "referral outcome evidence using the Referral SaaS safe "
                "status projection vocabulary; it does not expose raw "
                "viewer, UCN, reward, audit, provider, or money evidence."
            ),
        }
    ]

    counts = {
        metric["dimensions"]["product_status"]: metric["value"]
        for metric in report["metrics"]
    }
    assert counts == {
        "ACTION_NEEDED": 1,
        "COMPLETED": 2,
        "IN_PROGRESS": 3,
        "WAITING": 5,
    }
    assert all(metric["name"] == "status.safe_status_count" for metric in report["metrics"])
    assert all(
        metric["metric_class"] == "DERIVED_STATUS" for metric in report["metrics"]
    )
    assert "900001" not in str(report)


@pytest.mark.asyncio
async def test_safe_status_distribution_returns_unavailable_when_source_fails(
    monkeypatch,
):
    class BrokenConnection:
        async def fetch(self, query, *params):
            raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        svc, "db_connection", lambda: FakeDbConnection(BrokenConnection())
    )

    report = await svc.get_referral_saas_report(
        tenant_code="FNB",
        report_type="safe_status_distribution",
    )

    assert report["metrics"] == []
    assert report["freshness"]["status"] == "UNAVAILABLE"
    assert report["source_warnings"][0]["code"] == "SOURCE_UNAVAILABLE"
    assert report["source_warnings"][1]["code"] == "DERIVED_SAFE_STATUS"


@pytest.mark.asyncio
async def test_future_referral_saas_report_types_remain_explicitly_unimplemented():
    with pytest.raises(
        ValueError,
        match="Referral SaaS report_type not implemented: reward_visibility_summary",
    ):
        await svc.get_referral_saas_report(
            tenant_code="FNB",
            report_type="reward_visibility_summary",
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
