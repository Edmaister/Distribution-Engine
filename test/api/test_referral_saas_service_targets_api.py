from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from apps.api.main import app
from apps.api.routers import referral_saas_service_targets as router
from services.referral_saas_operational_service_target_service import (
    ServiceTargetPolicy,
    ServiceTargetPolicyResolutionUnavailable,
)


pytestmark = pytest.mark.asyncio
ADMIN_HEADERS = {"x-api-key": "test-admin-key"}
PARTNER_HEADERS = {"x-api-key": "test-partner-key"}


def _policy(status: str = "APPROVED") -> ServiceTargetPolicy:
    now = datetime(2026, 8, 22, tzinfo=timezone.utc)
    return ServiceTargetPolicy(
        policy_id="11111111-1111-4111-8111-111111111111",
        policy_code="SUPPORT_STANDARD_ZA",
        version_number=2,
        operating_jurisdiction_code="ZA",
        work_type="SUPPORT_CASE",
        work_category="GENERAL",
        priority="NORMAL",
        business_timezone="Africa/Johannesburg",
        target_duration_minutes=480,
        warning_threshold_minutes=60,
        business_calendar_ref=None,
        start_event="CASE_CREATED",
        completion_event="CASE_RESOLVED",
        approved_pause_reasons=("WAITING_FOR_CUSTOMER",),
        lifecycle_status=status,
        effective_from=now,
        effective_to=None,
        created_by_ref="creator",
        reviewed_by_ref="reviewer",
        reviewed_at=now,
        approved_by_ref="reviewer",
        approved_at=now,
        metadata={},
        created_at=now,
        updated_at=now,
        retired_at=None,
    )


async def test_policy_resolution_returns_only_approved_safe_policy(monkeypatch):
    captured = {}

    async def fake_resolve(**kwargs):
        captured.update(kwargs)
        return _policy()

    monkeypatch.setattr(router, "resolve_service_target_policy", fake_resolve)
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/service-target-policies/resolution",
            params={
                "operatingJurisdictionCode": "ZA",
                "workType": "SUPPORT_CASE",
                "workCategory": "GENERAL",
                "priority": "NORMAL",
            },
        )
    assert response.status_code == 200
    assert response.json()["policy"]["lifecycle_status"] == "APPROVED"
    assert "request_payload_hash" not in response.json()["policy"]
    assert captured["operating_jurisdiction_code"] == "ZA"


async def test_policy_resolution_fails_closed_when_coverage_is_missing(monkeypatch):
    async def fake_resolve(**_kwargs):
        raise ServiceTargetPolicyResolutionUnavailable("No approved policy.")

    monkeypatch.setattr(router, "resolve_service_target_policy", fake_resolve)
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/service-target-policies/resolution",
            params={
                "operatingJurisdictionCode": "ZA",
                "workType": "SUPPORT_CASE",
                "workCategory": "GENERAL",
                "priority": "NORMAL",
            },
        )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "service_target_policy_unavailable"


async def test_policy_administration_rejects_partner_identity(monkeypatch):
    async def fake_list(**_kwargs):
        raise AssertionError("service must not be called")

    monkeypatch.setattr(router, "list_service_target_policies", fake_list)
    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get("/v1/referral-saas/service-target-policies")
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "permission_denied"


async def test_submit_review_forwards_audited_command(monkeypatch):
    captured = {}

    async def fake_transition(**kwargs):
        captured.update(kwargs)
        return _policy("IN_REVIEW"), "NEW_REQUEST"

    monkeypatch.setattr(router, "transition_service_target_policy", fake_transition)
    policy_ref = "11111111-1111-4111-8111-111111111111"
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/v1/referral-saas/service-target-policies/{policy_ref}/submit-review",
            json={"reason": "Ready for independent review", "idempotencyKey": "submit-1"},
        )
    assert response.status_code == 200
    assert response.json()["policy"]["lifecycle_status"] == "IN_REVIEW"
    assert captured["action"] == "SUBMIT_REVIEW"
    assert captured["idempotency_key_hash"] != "submit-1"
