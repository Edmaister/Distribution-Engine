from __future__ import annotations

from datetime import date, datetime, time, timezone

import pytest

from services.referral_saas_service_target_business_calendar import (
    BusinessCalendarCalculator,
    BusinessCalendarValidationError,
    BusinessCalendarVersion,
    LocalWorkingInterval,
)

UTC = timezone.utc


def _calendar(
    *,
    timezone_name: str = "Africa/Johannesburg",
    weekly: dict[int, tuple[LocalWorkingInterval, ...]] | None = None,
    closed: frozenset[date] = frozenset(),
    exceptional: dict[date, tuple[LocalWorkingInterval, ...]] | None = None,
    lifecycle: str = "APPROVED",
) -> BusinessCalendarVersion:
    return BusinessCalendarVersion(
        calendar_code="SUPPORT_HOURS",
        version_number=1,
        business_timezone=timezone_name,
        lifecycle_status=lifecycle,
        weekly_intervals=weekly
        if weekly is not None
        else {
            day: (LocalWorkingInterval(time(9), time(17)),)
            for day in range(1, 6)
        },
        closed_dates=closed,
        exceptional_working_intervals=exceptional,
    )


def test_add_working_minutes_skips_non_working_time_and_weekend() -> None:
    calculator = BusinessCalendarCalculator(_calendar())
    started = datetime(2026, 8, 21, 14, 0, tzinfo=UTC)  # Friday 16:00 local.

    assert calculator.add_working_minutes(started, 120) == datetime(
        2026, 8, 24, 8, 0, tzinfo=UTC
    )


def test_working_seconds_between_uses_half_open_intervals() -> None:
    calculator = BusinessCalendarCalculator(_calendar())

    assert calculator.working_seconds_between(
        datetime(2026, 8, 17, 6, 59, tzinfo=UTC),
        datetime(2026, 8, 17, 15, 1, tzinfo=UTC),
    ) == 8 * 60 * 60
    assert calculator.is_working_instant(
        datetime(2026, 8, 17, 7, 0, tzinfo=UTC)
    )
    assert not calculator.is_working_instant(
        datetime(2026, 8, 17, 15, 0, tzinfo=UTC)
    )


def test_full_day_closure_overrides_weekly_schedule() -> None:
    calculator = BusinessCalendarCalculator(
        _calendar(closed=frozenset({date(2026, 8, 18)}))
    )

    assert calculator.add_working_minutes(
        datetime(2026, 8, 17, 14, 0, tzinfo=UTC), 120
    ) == datetime(2026, 8, 19, 8, 0, tzinfo=UTC)


def test_exceptional_working_intervals_replace_the_weekly_day() -> None:
    calculator = BusinessCalendarCalculator(
        _calendar(
            exceptional={
                date(2026, 8, 22): (
                    LocalWorkingInterval(time(10), time(12)),
                )
            }
        )
    )

    assert calculator.working_seconds_between(
        datetime(2026, 8, 22, 0, 0, tzinfo=UTC),
        datetime(2026, 8, 23, 0, 0, tzinfo=UTC),
    ) == 2 * 60 * 60


def test_spring_dst_gap_advances_a_nonexistent_boundary() -> None:
    calculator = BusinessCalendarCalculator(
        _calendar(
            timezone_name="America/New_York",
            weekly={
                7: (LocalWorkingInterval(time(2, 30), time(4)),),
            },
        )
    )

    assert calculator.working_seconds_between(
        datetime(2026, 3, 8, 0, 0, tzinfo=UTC),
        datetime(2026, 3, 9, 0, 0, tzinfo=UTC),
    ) == 60 * 60


def test_spring_dst_gap_uses_the_first_valid_minute() -> None:
    calculator = BusinessCalendarCalculator(
        _calendar(
            timezone_name="America/New_York",
            weekly={
                7: (LocalWorkingInterval(time(2, 30, 30), time(3, 30)),),
            },
        )
    )

    assert calculator.working_seconds_between(
        datetime(2026, 3, 8, 0, 0, tzinfo=UTC),
        datetime(2026, 3, 9, 0, 0, tzinfo=UTC),
    ) == 30 * 60


def test_fall_dst_repeat_preserves_the_full_ambiguous_interval() -> None:
    calculator = BusinessCalendarCalculator(
        _calendar(
            timezone_name="America/New_York",
            weekly={
                7: (LocalWorkingInterval(time(1), time(2)),),
            },
        )
    )

    assert calculator.working_seconds_between(
        datetime(2026, 11, 1, 0, 0, tzinfo=UTC),
        datetime(2026, 11, 2, 0, 0, tzinfo=UTC),
    ) == 2 * 60 * 60


def test_unapproved_or_invalid_timezone_calendar_fails_closed() -> None:
    with pytest.raises(BusinessCalendarValidationError, match="Only approved"):
        _calendar(lifecycle="DRAFT")
    with pytest.raises(BusinessCalendarValidationError, match="valid IANA"):
        _calendar(timezone_name="Not/A_Timezone")


def test_overlapping_intervals_and_conflicting_exceptions_fail_validation() -> None:
    with pytest.raises(BusinessCalendarValidationError, match="must not overlap"):
        _calendar(
            weekly={
                1: (
                    LocalWorkingInterval(time(9), time(12)),
                    LocalWorkingInterval(time(11), time(13)),
                )
            }
        )
    with pytest.raises(BusinessCalendarValidationError, match="both closed"):
        _calendar(
            closed=frozenset({date(2026, 8, 17)}),
            exceptional={
                date(2026, 8, 17): (
                    LocalWorkingInterval(time(10), time(12)),
                )
            },
        )


def test_naive_timestamps_and_negative_minutes_are_rejected() -> None:
    calculator = BusinessCalendarCalculator(_calendar())
    with pytest.raises(BusinessCalendarValidationError, match="timezone-aware"):
        calculator.is_working_instant(datetime(2026, 8, 17, 9))
    with pytest.raises(BusinessCalendarValidationError, match="non-negative"):
        calculator.add_working_minutes(
            datetime(2026, 8, 17, 9, tzinfo=UTC), -1
        )
