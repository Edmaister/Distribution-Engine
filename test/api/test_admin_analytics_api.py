from __future__ import annotations

import pytest
from httpx import AsyncClient

from apps.api.main import app
from apps.api.routers import admin_analytics

pytestmark = pytest.mark.asyncio

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}
DISTRIBUTION_ADMIN_HEADERS = {"x-api-key": "test-distribution-admin-key"}
FINANCE_ADMIN_HEADERS = {"x-api-key": "test-finance-admin-key"}
SYSTEM_ADMIN_HEADERS = {"x-api-key": "test-system-admin-key"}


def _report(*, metric_class: str = "OPERATIONAL") -> dict:
    return {
        "report_type": "distribution_overview",
        "tenant_scope": "FNB",
        "external_tenant_ref": None,
        "filters": {"tenant_code": "FNB", "campaign_code": "CAMP001"},
        "dimensions": ["tenant_code", "campaign_code", "metric_name"],
        "metric_class": metric_class,
        "metrics": [
            {
                "name": "routes.total_count",
                "value": 3,
                "unit": "count",
                "metric_class": metric_class,
                "source": "distribution_reporting",
                "dimensions": {
                    "tenant_code": "FNB",
                    "campaign_code": "CAMP001",
                    "metric_name": "routes.total_count",
                },
            }
        ],
        "data_window_start": "2026-06-01T00:00:00+00:00",
        "data_window_end": "2026-06-25T00:00:00+00:00",
        "generated_at": "2026-06-25T00:00:00+00:00",
        "freshness": {"status": "FRESH", "sources": []},
        "source_warnings": [],
        "redactions": [],
        "reconciliation_status": "NOT_APPLICABLE",
    }


@pytest.mark.parametrize(
    "headers",
    [
        ADMIN_HEADERS,
        DISTRIBUTION_ADMIN_HEADERS,
        FINANCE_ADMIN_HEADERS,
        SYSTEM_ADMIN_HEADERS,
    ],
)
async def test_admin_can_fetch_tenant_safe_analytics_report(monkeypatch, headers):
    calls = []

    async def fake_get_tenant_safe_analytics_report(**kwargs):
        calls.append(kwargs)
        return _report()

    monkeypatch.setattr(
        admin_analytics,
        "get_tenant_safe_analytics_report",
        fake_get_tenant_safe_analytics_report,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=headers) as client:
        response = await client.get(
            "/admin/analytics/reports/distribution_overview",
            params=[
                ("tenant_code", "fnb"),
                ("dimensions", "tenant_code"),
                ("dimensions", "campaign_code"),
                ("dimensions", "metric_name"),
                ("campaign_code", "CAMP001"),
                ("data_window_start", "2026-06-01T00:00:00Z"),
                ("data_window_end", "2026-06-25T00:00:00Z"),
            ],
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["report"]["metric_class"] == "OPERATIONAL"
    assert body["guardrail"].startswith("Read-only admin tenant-safe analytics")
    assert len(calls) == 1
    assert calls[0]["tenant_code"] == "fnb"
    assert calls[0]["report_type"] == "distribution_overview"
    assert calls[0]["dimensions"] == ["tenant_code", "campaign_code", "metric_name"]
    assert calls[0]["filters"] == {"campaign_code": "CAMP001"}
    assert calls[0]["data_window_start"].isoformat().startswith("2026-06-01")
    assert calls[0]["data_window_end"].isoformat().startswith("2026-06-25")


async def test_admin_analytics_forwards_reconciliation_filter(monkeypatch):
    calls = []

    async def fake_get_tenant_safe_analytics_report(**kwargs):
        calls.append(kwargs)
        return _report(metric_class="LEDGER_BACKED")

    monkeypatch.setattr(
        admin_analytics,
        "get_tenant_safe_analytics_report",
        fake_get_tenant_safe_analytics_report,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=FINANCE_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/analytics/reports/reconciliation_summary",
            params={
                "tenant_code": "FNB",
                "dimensions": "provider_key",
                "provider_key": "BANK_FILE",
            },
        )

    assert response.status_code == 200
    assert response.json()["report"]["metric_class"] == "LEDGER_BACKED"
    assert calls[0]["filters"] == {"provider_key": "BANK_FILE"}


async def test_admin_analytics_returns_401_without_credentials(monkeypatch):
    async def fake_get_tenant_safe_analytics_report(**kwargs):  # pragma: no cover
        raise AssertionError("service should not be called")

    monkeypatch.setattr(
        admin_analytics,
        "get_tenant_safe_analytics_report",
        fake_get_tenant_safe_analytics_report,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/admin/analytics/reports/distribution_overview",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 401


async def test_admin_analytics_rejects_partner_identity(monkeypatch):
    async def fake_get_tenant_safe_analytics_report(**kwargs):  # pragma: no cover
        raise AssertionError("service should not be called")

    monkeypatch.setattr(
        admin_analytics,
        "get_tenant_safe_analytics_report",
        fake_get_tenant_safe_analytics_report,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers={"x-api-key": "test-partner-key"}
    ) as client:
        response = await client.get(
            "/admin/analytics/reports/distribution_overview",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == {
        "code": "permission_denied",
        "message": "API key is not authorised for analytics reports.",
    }


async def test_admin_analytics_returns_safe_validation_error(monkeypatch):
    async def fake_get_tenant_safe_analytics_report(**kwargs):
        raise ValueError("Unsupported analytics dimension(s): raw_ucn")

    monkeypatch.setattr(
        admin_analytics,
        "get_tenant_safe_analytics_report",
        fake_get_tenant_safe_analytics_report,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/analytics/reports/distribution_overview",
            params={"tenant_code": "FNB", "dimensions": "raw_ucn"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "validation_error",
        "message": "Unsupported analytics dimension(s): raw_ucn",
    }


async def test_admin_analytics_preserves_unavailable_source_warning(monkeypatch):
    async def fake_get_tenant_safe_analytics_report(**kwargs):
        report = _report()
        report["metrics"] = []
        report["freshness"] = {"status": "UNAVAILABLE", "sources": []}
        report["source_warnings"] = [
            {
                "code": "SOURCE_UNAVAILABLE",
                "severity": "WARNING",
                "source": "distribution_reporting",
                "message": "Analytics source could not be read safely.",
            }
        ]
        return report

    monkeypatch.setattr(
        admin_analytics,
        "get_tenant_safe_analytics_report",
        fake_get_tenant_safe_analytics_report,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=DISTRIBUTION_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/analytics/reports/distribution_overview",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["report"]["freshness"]["status"] == "UNAVAILABLE"
    assert body["report"]["source_warnings"][0]["code"] == "SOURCE_UNAVAILABLE"
