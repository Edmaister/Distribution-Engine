from datetime import date, datetime, time, timezone

import pytest

from services.referral_saas_service_target_calendar_service import (
    DateException,
    ServiceTargetCalendarVersion,
    ServiceTargetCalendarValidationError,
    WeeklyInterval,
    _validate_schedule,
    preview_service_target_calendar,
)


def test_calendar_schedule_validation_accepts_weekly_and_exception_evidence():
    _validate_schedule(
        calendar_code="SUPPORT_ZA",
        version_number=1,
        business_timezone="Africa/Johannesburg",
        weekly_intervals=(WeeklyInterval(1, time(8), time(17)),),
        date_exceptions=(
            DateException(date(2026, 12, 25), "CLOSED", None, None, "PUBLIC_HOLIDAY"),
            DateException(
                date(2026, 12, 26), "WORKING_INTERVAL", time(9), time(12),
                "APPROVED_EXCEPTION",
            ),
        ),
    )


def test_calendar_schedule_validation_rejects_overlapping_weekly_intervals():
    with pytest.raises(ServiceTargetCalendarValidationError, match="overlap"):
        _validate_schedule(
            calendar_code="SUPPORT_ZA",
            version_number=1,
            business_timezone="Africa/Johannesburg",
            weekly_intervals=(
                WeeklyInterval(1, time(8), time(12)),
                WeeklyInterval(1, time(11), time(17)),
            ),
            date_exceptions=(),
        )


def test_calendar_schedule_validation_rejects_conflicting_date_evidence():
    with pytest.raises(ServiceTargetCalendarValidationError, match="both closed"):
        _validate_schedule(
            calendar_code="SUPPORT_ZA",
            version_number=1,
            business_timezone="Africa/Johannesburg",
            weekly_intervals=(WeeklyInterval(1, time(8), time(17)),),
            date_exceptions=(
                DateException(date(2026, 12, 25), "CLOSED", None, None, "HOLIDAY"),
                DateException(
                    date(2026, 12, 25), "WORKING_INTERVAL", time(9), time(12),
                    "EXCEPTION",
                ),
            ),
        )


@pytest.mark.asyncio
async def test_calendar_preview_uses_saved_schedule_without_creating_clock(monkeypatch):
    calendar = ServiceTargetCalendarVersion(
        calendar_version_id="calendar-version-1",
        calendar_code="SUPPORT_ZA",
        version_number=2,
        scope_type="GLOBAL",
        account_id=None,
        calendar_name="South Africa support hours",
        business_timezone="Africa/Johannesburg",
        lifecycle_status="DRAFT",
        effective_from=datetime(2026, 8, 1, tzinfo=timezone.utc),
        effective_to=None,
        created_by_ref="admin-1",
        reviewed_by_ref=None,
        reviewed_at=None,
        approved_by_ref=None,
        approved_at=None,
        metadata={},
        created_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        retired_at=None,
        weekly_intervals=(WeeklyInterval(1, time(8), time(17)),),
        date_exceptions=(),
    )

    async def fake_get(calendar_ref: str):
        assert calendar_ref == "calendar-version-1"
        return calendar

    monkeypatch.setattr(
        "services.referral_saas_service_target_calendar_service.get_service_target_calendar",
        fake_get,
    )

    result = await preview_service_target_calendar(
        calendar_ref="calendar-version-1",
        started_at=datetime(2026, 8, 3, 6, tzinfo=timezone.utc),
        warning_threshold_minutes=120,
        target_duration_minutes=480,
    )

    assert result["warningAt"] == datetime(2026, 8, 3, 8, tzinfo=timezone.utc)
    assert result["dueAt"] == datetime(2026, 8, 3, 14, tzinfo=timezone.utc)
    assert result["calculationMode"] == "BUSINESS_TIME_PREVIEW"
    assert result["clockCreated"] is False
