from datetime import date, datetime, time, timezone

import pytest
from httpx import AsyncClient

from apps.api.main import app
from apps.api.routers import referral_saas_service_target_calendars as router
from services.referral_saas_service_target_calendar_service import (
    DateException,
    ServiceTargetCalendarResolutionUnavailable,
    ServiceTargetCalendarVersion,
    WeeklyInterval,
)


pytestmark = pytest.mark.asyncio
ADMIN_HEADERS = {"x-api-key": "test-admin-key"}
PARTNER_HEADERS = {"x-api-key": "test-partner-key"}


def _calendar(status: str = "APPROVED") -> ServiceTargetCalendarVersion:
    now = datetime(2026, 8, 22, tzinfo=timezone.utc)
    return ServiceTargetCalendarVersion(
        calendar_version_id="11111111-1111-4111-8111-111111111111",
        calendar_code="SUPPORT_ZA",
        version_number=2,
        scope_type="GLOBAL",
        account_id=None,
        calendar_name="South Africa support hours",
        business_timezone="Africa/Johannesburg",
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
        weekly_intervals=(WeeklyInterval(1, time(8), time(17)),),
        date_exceptions=(
            DateException(date(2026, 12, 25), "CLOSED", None, None, "PUBLIC_HOLIDAY"),
        ),
    )


async def test_calendar_creation_maps_safe_schedule_and_hashes_idempotency(monkeypatch):
    captured = {}

    async def fake_create(**kwargs):
        captured.update(kwargs)
        return _calendar("DRAFT"), "NEW_REQUEST"

    monkeypatch.setattr(router, "create_service_target_calendar", fake_create)
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/service-target-calendars",
            json={
                "calendarCode": "support-za",
                "scopeType": "GLOBAL",
                "calendarName": "South Africa support hours",
                "businessTimezone": "Africa/Johannesburg",
                "effectiveFrom": "2026-08-22T00:00:00Z",
                "weeklyIntervals": [
                    {"localDayOfWeek": 1, "localStartTime": "08:00", "localEndTime": "17:00"}
                ],
                "dateExceptions": [
                    {
                        "localDate": "2026-12-25", "exceptionType": "CLOSED",
                        "reasonCode": "PUBLIC_HOLIDAY",
                    }
                ],
                "idempotencyKey": "calendar-create-1",
            },
        )
    assert response.status_code == 200
    assert response.json()["calendar"]["lifecycle_status"] == "DRAFT"
    assert captured["idempotency_key_hash"] != "calendar-create-1"
    assert captured["weekly_intervals"][0].local_day_of_week == 1


async def test_calendar_resolution_fails_closed_when_coverage_is_missing(monkeypatch):
    async def fake_resolve(**_kwargs):
        raise ServiceTargetCalendarResolutionUnavailable("No approved calendar.")

    monkeypatch.setattr(router, "resolve_service_target_calendar", fake_resolve)
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/service-target-calendars/resolution",
            params={"calendarCode": "SUPPORT_ZA"},
        )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "business_calendar_unavailable"


async def test_calendar_administration_rejects_partner_identity(monkeypatch):
    async def fake_list(**_kwargs):
        raise AssertionError("service must not be called")

    monkeypatch.setattr(router, "list_service_target_calendars", fake_list)
    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get("/v1/referral-saas/service-target-calendars")
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "permission_denied"


async def test_calendar_approval_forwards_independent_governance_command(monkeypatch):
    captured = {}

    async def fake_transition(**kwargs):
        captured.update(kwargs)
        return _calendar("APPROVED"), "NEW_REQUEST"

    monkeypatch.setattr(router, "transition_service_target_calendar", fake_transition)
    calendar_ref = "11111111-1111-4111-8111-111111111111"
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/v1/referral-saas/service-target-calendars/{calendar_ref}/approve",
            json={"reason": "Independent review complete", "idempotencyKey": "approve-1"},
        )
    assert response.status_code == 200
    assert response.json()["calendar"]["lifecycle_status"] == "APPROVED"
    assert captured["action"] == "APPROVE"
    assert captured["idempotency_key_hash"] != "approve-1"
