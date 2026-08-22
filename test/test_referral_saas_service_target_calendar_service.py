from datetime import date, time

import pytest

from services.referral_saas_service_target_calendar_service import (
    DateException,
    ServiceTargetCalendarValidationError,
    WeeklyInterval,
    _validate_schedule,
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
