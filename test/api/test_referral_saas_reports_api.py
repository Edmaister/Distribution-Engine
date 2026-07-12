from __future__ import annotations

import pytest
from httpx import AsyncClient

from apps.api.main import app
from apps.api.routers import referral_saas_reports

pytestmark = pytest.mark.asyncio

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}
DISTRIBUTION_ADMIN_HEADERS = {"x-api-key": "test-distribution-admin-key"}
SYSTEM_ADMIN_HEADERS = {"x-api-key": "test-system-admin-key"}
PARTNER_HEADERS = {"x-api-key": "test-partner-key"}


def _report() -> dict:
    return {
        "report_type": "campaign_performance",
        "source_report_type": "distribution_overview",
        "tenant_scope": "FNB",
        "external_tenant_ref": None,
        "filters": {"campaign_ref": "CAMP001", "campaign_code": "CAMP001"},
        "dimensions": ["campaign_ref", "metric_name"],
        "metric_class": "OPERATIONAL",
        "metrics": [
            {
                "name": "conversion.attribution_rate",
                "value": "0.9000",
                "unit": "ratio",
                "metric_class": "OPERATIONAL",
                "source": "referral_saas_report_catalog",
                "dimensions": {
                    "campaign_ref": "CAMP001",
                    "campaign_code": "CAMP001",
                    "metric_name": "conversion.attribution_rate",
                },
            }
        ],
        "data_window_start": "2026-07-01T00:00:00+00:00",
        "data_window_end": "2026-07-12T00:00:00+00:00",
        "generated_at": "2026-07-12T12:00:00+00:00",
        "freshness": {"status": "FRESH", "sources": []},
        "source_warnings": [],
        "redactions": [],
        "reconciliation_status": "NOT_APPLICABLE",
        "catalog_status": "AVAILABLE",
        "export_status": "NOT_IMPLEMENTED",
    }


@pytest.mark.parametrize(
    "headers",
    [ADMIN_HEADERS, DISTRIBUTION_ADMIN_HEADERS, SYSTEM_ADMIN_HEADERS],
)
async def test_referral_saas_report_reader_can_fetch_campaign_performance(
    monkeypatch,
    headers,
):
    calls: list[dict] = []

    async def fake_get_referral_saas_report(**kwargs):
        calls.append(kwargs)
        return _report()

    monkeypatch.setattr(
        referral_saas_reports,
        "get_referral_saas_report",
        fake_get_referral_saas_report,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=headers) as client:
        response = await client.get(
            "/v1/referral-saas/reports/campaign_performance",
            params=[
                ("tenant_code", "fnb"),
                ("dimensions", "campaign_ref"),
                ("dimensions", "metric_name"),
                ("campaign_ref", "CAMP001"),
                ("sponsor_code", "BOXER"),
                ("data_window_start", "2026-07-01T00:00:00Z"),
                ("data_window_end", "2026-07-12T00:00:00Z"),
            ],
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["report"]["report_type"] == "campaign_performance"
    assert body["report"]["export_status"] == "NOT_IMPLEMENTED"
    assert body["guardrail"].startswith("Read-only Referral SaaS report wrapper")
    assert "create exports" in body["guardrail"]
    assert len(calls) == 1
    assert calls[0]["tenant_code"] == "fnb"
    assert calls[0]["report_type"] == "campaign_performance"
    assert calls[0]["dimensions"] == ["campaign_ref", "metric_name"]
    assert calls[0]["filters"] == {
        "campaign_ref": "CAMP001",
        "sponsor_code": "BOXER",
    }
    assert calls[0]["data_window_start"].isoformat().startswith("2026-07-01")
    assert calls[0]["data_window_end"].isoformat().startswith("2026-07-12")


async def test_referral_saas_report_requires_credentials(monkeypatch):
    async def fake_get_referral_saas_report(**kwargs):  # pragma: no cover
        raise AssertionError("service should not be called")

    monkeypatch.setattr(
        referral_saas_reports,
        "get_referral_saas_report",
        fake_get_referral_saas_report,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/v1/referral-saas/reports/campaign_performance",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 401


async def test_referral_saas_report_rejects_partner_identity(monkeypatch):
    async def fake_get_referral_saas_report(**kwargs):  # pragma: no cover
        raise AssertionError("service should not be called")

    monkeypatch.setattr(
        referral_saas_reports,
        "get_referral_saas_report",
        fake_get_referral_saas_report,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PARTNER_HEADERS
    ) as client:
        response = await client.get(
            "/v1/referral-saas/reports/campaign_performance",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == {
        "code": "permission_denied",
        "message": "API key is not authorised for Referral SaaS reports.",
    }


async def test_referral_saas_report_returns_safe_validation_error(monkeypatch):
    async def fake_get_referral_saas_report(**kwargs):
        raise ValueError("Referral SaaS report_type not implemented: referral_funnel")

    monkeypatch.setattr(
        referral_saas_reports,
        "get_referral_saas_report",
        fake_get_referral_saas_report,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/v1/referral-saas/reports/referral_funnel",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "validation_error",
        "message": "Referral SaaS report_type not implemented: referral_funnel",
    }
