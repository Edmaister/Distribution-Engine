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


def _report(report_type: str = "campaign_performance") -> dict:
    return {
        "report_type": report_type,
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
    assert calls[0]["tenant_code"] == "FNB"
    assert calls[0]["report_type"] == "campaign_performance"
    assert calls[0]["dimensions"] == ["campaign_ref", "metric_name"]
    assert calls[0]["filters"] == {
        "campaign_ref": "CAMP001",
        "sponsor_code": "BOXER",
    }
    assert calls[0]["data_window_start"].isoformat().startswith("2026-07-01")
    assert calls[0]["data_window_end"].isoformat().startswith("2026-07-12")
    assert body["account_scope"] == {
        "source": "explicit_tenant_code",
        "account_ref": None,
        "external_tenant_ref": None,
    }


async def test_referral_saas_report_can_use_identity_tenant_scope(monkeypatch):
    calls: list[dict] = []

    async def fake_get_referral_saas_report(**kwargs):
        calls.append(kwargs)
        return _report()

    monkeypatch.setattr(
        referral_saas_reports,
        "get_referral_saas_report",
        fake_get_referral_saas_report,
    )

    app.dependency_overrides[referral_saas_reports.require_session_key] = lambda: {
        "authenticated": True,
        "role": "ADMIN",
        "tenant_code": "FNB",
        "tenant": "FNB",
    }
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/v1/referral-saas/reports/campaign_performance",
                params={"campaign_code": "CAMP001"},
            )
    finally:
        app.dependency_overrides.pop(referral_saas_reports.require_session_key, None)

    assert response.status_code == 200
    assert calls[0]["tenant_code"] == "FNB"
    assert response.json()["account_scope"] == {
        "source": "identity_tenant",
        "account_ref": None,
        "external_tenant_ref": None,
    }


async def test_referral_saas_report_carries_trusted_account_refs(monkeypatch):
    calls: list[dict] = []

    async def fake_get_referral_saas_report(**kwargs):
        calls.append(kwargs)
        return _report()

    monkeypatch.setattr(
        referral_saas_reports,
        "get_referral_saas_report",
        fake_get_referral_saas_report,
    )

    app.dependency_overrides[referral_saas_reports.require_session_key] = lambda: {
        "authenticated": True,
        "role": "ADMIN",
        "tenant_code": "FNB",
        "tenant": "FNB",
        "account_ref": "acct_fnb_referrals",
        "external_tenant_ref": "org_fnb_referrals",
    }
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/v1/referral-saas/reports/campaign_performance",
                params={"campaign_code": "CAMP001"},
            )
    finally:
        app.dependency_overrides.pop(referral_saas_reports.require_session_key, None)

    assert response.status_code == 200
    assert calls[0]["tenant_code"] == "FNB"
    assert response.json()["account_scope"] == {
        "source": "identity_tenant",
        "account_ref": "acct_fnb_referrals",
        "external_tenant_ref": "org_fnb_referrals",
    }


async def test_referral_saas_report_reader_can_fetch_referral_funnel(monkeypatch):
    calls: list[dict] = []

    async def fake_get_referral_saas_report(**kwargs):
        calls.append(kwargs)
        return _report(report_type="referral_funnel")

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
            params={"tenant_code": "FNB", "campaign_code": "CAMP001"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["report"]["report_type"] == "referral_funnel"
    assert calls[0]["tenant_code"] == "FNB"
    assert calls[0]["report_type"] == "referral_funnel"
    assert calls[0]["filters"] == {"campaign_code": "CAMP001"}


async def test_referral_saas_report_reader_can_fetch_link_code_performance(
    monkeypatch,
):
    calls: list[dict] = []

    async def fake_get_referral_saas_report(**kwargs):
        calls.append(kwargs)
        return _report(report_type="link_code_performance")

    monkeypatch.setattr(
        referral_saas_reports,
        "get_referral_saas_report",
        fake_get_referral_saas_report,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/v1/referral-saas/reports/link_code_performance",
            params={
                "tenant_code": "FNB",
                "campaign_ref": "CAMP001",
                "source_type": "ROUTE_REFERRAL_LINK",
                "link_code_status": "ACTIVE",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["report"]["report_type"] == "link_code_performance"
    assert calls[0]["tenant_code"] == "FNB"
    assert calls[0]["report_type"] == "link_code_performance"
    assert calls[0]["filters"] == {
        "campaign_ref": "CAMP001",
        "link_code_status": "ACTIVE",
        "source_type": "ROUTE_REFERRAL_LINK",
    }


async def test_referral_saas_report_reader_can_fetch_progress_event_health(
    monkeypatch,
):
    calls: list[dict] = []

    async def fake_get_referral_saas_report(**kwargs):
        calls.append(kwargs)
        return _report(report_type="progress_event_health")

    monkeypatch.setattr(
        referral_saas_reports,
        "get_referral_saas_report",
        fake_get_referral_saas_report,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/v1/referral-saas/reports/progress_event_health",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["report"]["report_type"] == "progress_event_health"
    assert calls[0]["tenant_code"] == "FNB"
    assert calls[0]["report_type"] == "progress_event_health"


async def test_referral_saas_report_reader_can_fetch_attribution_quality(
    monkeypatch,
):
    calls: list[dict] = []

    async def fake_get_referral_saas_report(**kwargs):
        calls.append(kwargs)
        return _report(report_type="attribution_quality")

    monkeypatch.setattr(
        referral_saas_reports,
        "get_referral_saas_report",
        fake_get_referral_saas_report,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/v1/referral-saas/reports/attribution_quality",
            params={"tenant_code": "FNB", "campaign_ref": "CAMP001"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["report"]["report_type"] == "attribution_quality"
    assert calls[0]["tenant_code"] == "FNB"
    assert calls[0]["report_type"] == "attribution_quality"
    assert calls[0]["filters"] == {"campaign_ref": "CAMP001"}


async def test_referral_saas_report_reader_can_fetch_safe_status_distribution(
    monkeypatch,
):
    calls: list[dict] = []

    async def fake_get_referral_saas_report(**kwargs):
        calls.append(kwargs)
        return _report(report_type="safe_status_distribution")

    monkeypatch.setattr(
        referral_saas_reports,
        "get_referral_saas_report",
        fake_get_referral_saas_report,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/v1/referral-saas/reports/safe_status_distribution",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["report"]["report_type"] == "safe_status_distribution"
    assert calls[0]["tenant_code"] == "FNB"
    assert calls[0]["report_type"] == "safe_status_distribution"


async def test_referral_saas_report_reader_can_fetch_reward_visibility_summary(
    monkeypatch,
):
    calls: list[dict] = []

    async def fake_get_referral_saas_report(**kwargs):
        calls.append(kwargs)
        return _report(report_type="reward_visibility_summary")

    monkeypatch.setattr(
        referral_saas_reports,
        "get_referral_saas_report",
        fake_get_referral_saas_report,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/v1/referral-saas/reports/reward_visibility_summary",
            params={
                "tenant_code": "FNB",
                "beneficiary_type": "REFERRER",
                "product": "TRANSACTIONAL",
                "reward_source": "BASE",
                "reward_status": "APPLIED",
                "reward_type": "CASH",
                "sub_product": "GOLD",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["report"]["report_type"] == "reward_visibility_summary"
    assert calls[0]["tenant_code"] == "FNB"
    assert calls[0]["report_type"] == "reward_visibility_summary"
    assert calls[0]["filters"] == {
        "beneficiary_type": "REFERRER",
        "product": "TRANSACTIONAL",
        "reward_source": "BASE",
        "reward_status": "APPLIED",
        "reward_type": "CASH",
        "sub_product": "GOLD",
    }


async def test_referral_saas_report_reader_can_validate_export_request(monkeypatch):
    calls: list[dict] = []

    def fake_validate_referral_saas_report_export_request(**kwargs):
        calls.append(kwargs)
        return {
            "tenant_scope": kwargs["tenant_code"],
            "report_type": kwargs["report_type"],
            "source_report_type": "distribution_overview",
            "metric_class": "OPERATIONAL",
            "dimensions": kwargs["dimensions"],
            "filters": kwargs["filters"],
            "redactions": ["raw_ucn"],
            "export_format": kwargs["export_format"],
            "redaction_profile": kwargs["redaction_profile"],
            "row_limit": kwargs["row_limit"],
            "data_window_start": kwargs["data_window_start"],
            "data_window_end": kwargs["data_window_end"],
            "catalog_status": "AVAILABLE",
            "export_status": "VALIDATED_NOT_CREATED",
            "creation_status": "NOT_IMPLEMENTED",
            "storage_status": "NOT_IMPLEMENTED",
            "delivery_status": "NOT_IMPLEMENTED",
            "audit_status": "NOT_IMPLEMENTED",
            "guardrail": "Export request validated only.",
        }

    monkeypatch.setattr(
        referral_saas_reports,
        "validate_referral_saas_report_export_request",
        fake_validate_referral_saas_report_export_request,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/v1/referral-saas/reports/campaign_performance/exports/validate",
            params={"tenant_code": "FNB"},
            json={
                "format": "csv",
                "redaction_profile": "tenant_safe",
                "dimensions": ["campaign_ref", "metric_name"],
                "filters": {"campaign_ref": "CAMP001", "raw_ucn": "12345"},
                "row_limit": 2500,
                "data_window_start": "2026-07-01T00:00:00Z",
                "data_window_end": "2026-07-12T00:00:00Z",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["export_request"]["export_status"] == "VALIDATED_NOT_CREATED"
    assert body["export_request"]["creation_status"] == "NOT_IMPLEMENTED"
    assert "does not create export files" in body["guardrail"]
    assert calls[0]["tenant_code"] == "FNB"
    assert calls[0]["report_type"] == "campaign_performance"
    assert calls[0]["export_format"] == "csv"
    assert calls[0]["redaction_profile"] == "tenant_safe"
    assert calls[0]["dimensions"] == ["campaign_ref", "metric_name"]
    assert calls[0]["filters"] == {"campaign_ref": "CAMP001", "raw_ucn": "12345"}
    assert calls[0]["row_limit"] == 2500
    assert calls[0]["data_window_start"].isoformat().startswith("2026-07-01")
    assert calls[0]["data_window_end"].isoformat().startswith("2026-07-12")
    assert body["account_scope"] == {
        "source": "explicit_tenant_code",
        "account_ref": None,
        "external_tenant_ref": None,
    }


async def test_referral_saas_export_validation_carries_trusted_account_refs(
    monkeypatch,
):
    calls: list[dict] = []

    def fake_validate_referral_saas_report_export_request(**kwargs):
        calls.append(kwargs)
        return {
            "tenant_scope": kwargs["tenant_code"],
            "report_type": kwargs["report_type"],
            "source_report_type": "distribution_overview",
            "metric_class": "OPERATIONAL",
            "dimensions": ["campaign_code", "metric_name"],
            "filters": {},
            "redactions": [],
            "export_format": "json",
            "redaction_profile": "tenant_safe",
            "row_limit": 10000,
            "data_window_start": None,
            "data_window_end": None,
            "catalog_status": "AVAILABLE",
            "export_status": "VALIDATED_NOT_CREATED",
            "creation_status": "NOT_IMPLEMENTED",
            "storage_status": "NOT_IMPLEMENTED",
            "delivery_status": "NOT_IMPLEMENTED",
            "audit_status": "NOT_IMPLEMENTED",
            "guardrail": "Export request validated only.",
        }

    monkeypatch.setattr(
        referral_saas_reports,
        "validate_referral_saas_report_export_request",
        fake_validate_referral_saas_report_export_request,
    )

    app.dependency_overrides[referral_saas_reports.require_session_key] = lambda: {
        "authenticated": True,
        "role": "ADMIN",
        "tenant_code": "FNB",
        "tenant": "FNB",
        "account_ref": "acct_fnb_referrals",
        "external_tenant_ref": "org_fnb_referrals",
    }
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/v1/referral-saas/reports/campaign_performance/exports/validate",
                json={"format": "json"},
            )
    finally:
        app.dependency_overrides.pop(referral_saas_reports.require_session_key, None)

    assert response.status_code == 200
    assert calls[0]["tenant_code"] == "FNB"
    assert response.json()["account_scope"] == {
        "source": "identity_tenant",
        "account_ref": "acct_fnb_referrals",
        "external_tenant_ref": "org_fnb_referrals",
    }


async def test_referral_saas_report_reader_can_preview_export_payload(monkeypatch):
    calls: list[dict] = []

    async def fake_build_referral_saas_report_export_preview(**kwargs):
        calls.append(kwargs)
        return {
            "export_request": {
                "tenant_scope": kwargs["tenant_code"],
                "report_type": kwargs["report_type"],
                "export_format": kwargs["export_format"],
                "redaction_profile": kwargs["redaction_profile"],
                "row_limit": kwargs["row_limit"],
            },
            "report": _report(report_type=kwargs["report_type"]),
            "preview": {
                "status": "PREVIEW_READY",
                "export_format": kwargs["export_format"],
                "content_type": "text/csv",
                "file_extension": "csv",
                "metadata": {"row_count": 1, "redactions": ["raw_ucn"]},
                "payload": "metric_name,value\nconversion.attribution_rate,0.9000\n",
            },
            "creation_status": "NOT_IMPLEMENTED",
            "storage_status": "NOT_IMPLEMENTED",
            "delivery_status": "NOT_IMPLEMENTED",
            "audit_status": "NOT_IMPLEMENTED",
            "guardrail": "Inline export preview only.",
        }

    monkeypatch.setattr(
        referral_saas_reports,
        "build_referral_saas_report_export_preview",
        fake_build_referral_saas_report_export_preview,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/v1/referral-saas/reports/campaign_performance/exports/preview",
            params={"tenant_code": "FNB"},
            json={
                "format": "csv",
                "redaction_profile": "tenant_safe",
                "dimensions": ["campaign_ref", "metric_name"],
                "filters": {"campaign_ref": "CAMP001", "raw_ucn": "12345"},
                "row_limit": 1,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["export_preview"]["preview"]["status"] == "PREVIEW_READY"
    assert body["export_preview"]["creation_status"] == "NOT_IMPLEMENTED"
    assert "does not create export files" in body["guardrail"]
    assert calls[0]["tenant_code"] == "FNB"
    assert calls[0]["report_type"] == "campaign_performance"
    assert calls[0]["export_format"] == "csv"
    assert calls[0]["redaction_profile"] == "tenant_safe"
    assert calls[0]["dimensions"] == ["campaign_ref", "metric_name"]
    assert calls[0]["filters"] == {"campaign_ref": "CAMP001", "raw_ucn": "12345"}
    assert calls[0]["row_limit"] == 1
    assert body["account_scope"] == {
        "source": "explicit_tenant_code",
        "account_ref": None,
        "external_tenant_ref": None,
    }


async def test_referral_saas_export_preview_returns_safe_validation_error(
    monkeypatch,
):
    async def fake_build_referral_saas_report_export_preview(**kwargs):
        raise ValueError("Unsupported Referral SaaS export format: xlsx")

    monkeypatch.setattr(
        referral_saas_reports,
        "build_referral_saas_report_export_preview",
        fake_build_referral_saas_report_export_preview,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/v1/referral-saas/reports/campaign_performance/exports/preview",
            params={"tenant_code": "FNB"},
            json={"format": "xlsx"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "validation_error",
        "message": "Unsupported Referral SaaS export format: xlsx",
    }


async def test_referral_saas_export_validation_returns_safe_validation_error(
    monkeypatch,
):
    def fake_validate_referral_saas_report_export_request(**kwargs):
        raise ValueError("Unsupported Referral SaaS export format: xlsx")

    monkeypatch.setattr(
        referral_saas_reports,
        "validate_referral_saas_report_export_request",
        fake_validate_referral_saas_report_export_request,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/v1/referral-saas/reports/campaign_performance/exports/validate",
            params={"tenant_code": "FNB"},
            json={"format": "xlsx"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "validation_error",
        "message": "Unsupported Referral SaaS export format: xlsx",
    }


async def test_referral_saas_export_validation_rejects_partner_identity(monkeypatch):
    def fake_validate_referral_saas_report_export_request(**kwargs):  # pragma: no cover
        raise AssertionError("service should not be called")

    monkeypatch.setattr(
        referral_saas_reports,
        "validate_referral_saas_report_export_request",
        fake_validate_referral_saas_report_export_request,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PARTNER_HEADERS
    ) as client:
        response = await client.post(
            "/v1/referral-saas/reports/campaign_performance/exports/validate",
            params={"tenant_code": "FNB"},
            json={"format": "csv"},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == {
        "code": "permission_denied",
        "message": "API key is not authorised for Referral SaaS reports.",
    }


async def test_referral_saas_report_rejects_internal_reader_without_scope(monkeypatch):
    async def fake_get_referral_saas_report(**kwargs):  # pragma: no cover
        raise AssertionError("service should not be called")

    monkeypatch.setattr(
        referral_saas_reports,
        "get_referral_saas_report",
        fake_get_referral_saas_report,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/v1/referral-saas/reports/campaign_performance",
        )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "validation_error",
        "message": (
            "tenant_code is required until Referral SaaS account scope resolution "
            "is implemented for internal report readers"
        ),
    }


async def test_referral_saas_report_rejects_cross_tenant_scope(monkeypatch):
    async def fake_get_referral_saas_report(**kwargs):  # pragma: no cover
        raise AssertionError("service should not be called")

    monkeypatch.setattr(
        referral_saas_reports,
        "get_referral_saas_report",
        fake_get_referral_saas_report,
    )

    app.dependency_overrides[referral_saas_reports.require_session_key] = lambda: {
        "authenticated": True,
        "role": "ADMIN",
        "tenant_code": "FNB",
        "tenant": "FNB",
    }
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/v1/referral-saas/reports/campaign_performance",
                params={"tenant_code": "PNP"},
            )
    finally:
        app.dependency_overrides.pop(referral_saas_reports.require_session_key, None)

    assert response.status_code == 403
    assert response.json()["detail"] == {
        "code": "permission_denied",
        "message": "Requested tenant scope is not available.",
    }


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
        raise ValueError("Unsupported Referral SaaS report_type: raw_customer_export")

    monkeypatch.setattr(
        referral_saas_reports,
        "get_referral_saas_report",
        fake_get_referral_saas_report,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/v1/referral-saas/reports/raw_customer_export",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "validation_error",
        "message": "Unsupported Referral SaaS report_type: raw_customer_export",
    }
