"""Deterministic working-time calculations for approved service-target calendars."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UTC = timezone.utc
MAX_CALCULATION_DAYS = 36_600


class BusinessCalendarError(ValueError):
    """Base error for invalid or unavailable business-calendar calculations."""


class BusinessCalendarValidationError(BusinessCalendarError):
    """Raised when a calendar version is not safe to calculate."""


class BusinessCalendarCalculationUnavailable(BusinessCalendarError):
    """Raised when a bounded calculation cannot find enough working time."""


@dataclass(frozen=True, order=True)
class LocalWorkingInterval:
    start: time
    end: time

    def __post_init__(self) -> None:
        if self.start.tzinfo is not None or self.end.tzinfo is not None:
            raise BusinessCalendarValidationError(
                "Working interval times must be timezone-naive local wall times."
            )
        if self.start >= self.end:
            raise BusinessCalendarValidationError(
                "Working intervals must have positive, day-bounded duration."
            )


@dataclass(frozen=True)
class BusinessCalendarVersion:
    calendar_code: str
    version_number: int
    business_timezone: str
    lifecycle_status: str
    weekly_intervals: Mapping[int, tuple[LocalWorkingInterval, ...]]
    closed_dates: frozenset[date] = frozenset()
    exceptional_working_intervals: Mapping[
        date, tuple[LocalWorkingInterval, ...]
    ] | None = None

    def __post_init__(self) -> None:
        if not self.calendar_code.strip():
            raise BusinessCalendarValidationError("Calendar code is required.")
        if self.version_number <= 0:
            raise BusinessCalendarValidationError(
                "Calendar version number must be positive."
            )
        if self.lifecycle_status != "APPROVED":
            raise BusinessCalendarValidationError(
                "Only approved calendar versions can be calculated."
            )
        try:
            ZoneInfo(self.business_timezone)
        except ZoneInfoNotFoundError as exc:
            raise BusinessCalendarValidationError(
                "Business timezone must be a valid IANA timezone."
            ) from exc

        exceptional = self.exceptional_working_intervals or {}
        if self.closed_dates.intersection(exceptional):
            raise BusinessCalendarValidationError(
                "A local date cannot be both closed and exceptionally working."
            )
        if not any(self.weekly_intervals.values()) and not any(exceptional.values()):
            raise BusinessCalendarValidationError(
                "A calendar must contain at least one working interval."
            )
        for day, intervals in self.weekly_intervals.items():
            if day < 1 or day > 7:
                raise BusinessCalendarValidationError(
                    "Weekly interval days must use ISO values 1 through 7."
                )
            _validate_non_overlapping(intervals)
        for intervals in exceptional.values():
            _validate_non_overlapping(intervals)


def _validate_non_overlapping(intervals: Iterable[LocalWorkingInterval]) -> None:
    ordered = sorted(intervals)
    for previous, current in zip(ordered, ordered[1:]):
        if current.start < previous.end:
            raise BusinessCalendarValidationError(
                "Working intervals for one local date must not overlap."
            )


class BusinessCalendarCalculator:
    """Calculate UTC instants from one pinned, approved calendar version."""

    def __init__(self, calendar: BusinessCalendarVersion) -> None:
        self.calendar = calendar
        self.timezone = ZoneInfo(calendar.business_timezone)

    def is_working_instant(self, at: datetime) -> bool:
        instant = _aware_utc(at)
        local_date = instant.astimezone(self.timezone).date()
        return any(
            start <= instant < end
            for start, end in self._utc_intervals_for_date(local_date)
        )

    def working_seconds_between(self, started_at: datetime, ended_at: datetime) -> int:
        start = _aware_utc(started_at)
        end = _aware_utc(ended_at)
        if end < start:
            raise BusinessCalendarValidationError(
                "Calculation end must not precede its start."
            )
        if end == start:
            return 0

        current_date = start.astimezone(self.timezone).date()
        final_date = end.astimezone(self.timezone).date()
        total = 0
        for _ in range(MAX_CALCULATION_DAYS):
            for interval_start, interval_end in self._utc_intervals_for_date(
                current_date
            ):
                overlap_start = max(start, interval_start)
                overlap_end = min(end, interval_end)
                if overlap_end > overlap_start:
                    total += int((overlap_end - overlap_start).total_seconds())
            if current_date >= final_date:
                return total
            current_date += timedelta(days=1)
        raise BusinessCalendarCalculationUnavailable(
            "Working-time calculation exceeded its bounded date range."
        )

    def add_working_minutes(self, started_at: datetime, minutes: int) -> datetime:
        if isinstance(minutes, bool) or not isinstance(minutes, int) or minutes < 0:
            raise BusinessCalendarValidationError(
                "Working minutes must be a non-negative integer."
            )
        return self.add_working_seconds(started_at, minutes * 60)

    def add_working_seconds(self, started_at: datetime, seconds: int) -> datetime:
        if isinstance(seconds, bool) or not isinstance(seconds, int) or seconds < 0:
            raise BusinessCalendarValidationError(
                "Working seconds must be a non-negative integer."
            )
        cursor = _aware_utc(started_at)
        remaining_seconds = seconds
        if remaining_seconds == 0:
            return cursor

        current_date = cursor.astimezone(self.timezone).date()
        for _ in range(MAX_CALCULATION_DAYS):
            for interval_start, interval_end in self._utc_intervals_for_date(
                current_date
            ):
                usable_start = max(cursor, interval_start)
                if usable_start >= interval_end:
                    continue
                available = int((interval_end - usable_start).total_seconds())
                if remaining_seconds <= available:
                    return usable_start + timedelta(seconds=remaining_seconds)
                remaining_seconds -= available
                cursor = interval_end
            current_date += timedelta(days=1)
        raise BusinessCalendarCalculationUnavailable(
            "No sufficient working interval was found in the bounded date range."
        )

    def _utc_intervals_for_date(
        self, local_date: date
    ) -> tuple[tuple[datetime, datetime], ...]:
        if local_date in self.calendar.closed_dates:
            return ()
        exceptional = self.calendar.exceptional_working_intervals or {}
        intervals = exceptional.get(
            local_date,
            self.calendar.weekly_intervals.get(local_date.isoweekday(), ()),
        )
        resolved = []
        for interval in intervals:
            start = _resolve_local_boundary(
                datetime.combine(local_date, interval.start),
                self.timezone,
                boundary="start",
            )
            end = _resolve_local_boundary(
                datetime.combine(local_date, interval.end),
                self.timezone,
                boundary="end",
            )
            if end <= start:
                raise BusinessCalendarCalculationUnavailable(
                    "Resolved working interval has no positive UTC duration."
                )
            resolved.append((start, end))
        return tuple(resolved)


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise BusinessCalendarValidationError(
            "Calendar calculations require timezone-aware timestamps."
        )
    return value.astimezone(UTC)


def _resolve_local_boundary(
    local_value: datetime, zone: ZoneInfo, *, boundary: str
) -> datetime:
    candidates = []
    for fold in (0, 1):
        candidate = local_value.replace(tzinfo=zone, fold=fold).astimezone(UTC)
        round_trip = candidate.astimezone(zone).replace(tzinfo=None)
        if round_trip == local_value and candidate not in candidates:
            candidates.append(candidate)
    if candidates:
        return min(candidates) if boundary == "start" else max(candidates)

    # A forward DST transition can remove local wall times. Advance to the first
    # representable local minute after the gap, as required by the contract.
    advanced = local_value.replace(second=0, microsecond=0)
    if advanced <= local_value:
        advanced += timedelta(minutes=1)
    for _ in range(180):
        for fold in (0, 1):
            candidate = advanced.replace(tzinfo=zone, fold=fold).astimezone(UTC)
            if candidate.astimezone(zone).replace(tzinfo=None) == advanced:
                return candidate
        advanced += timedelta(minutes=1)
    raise BusinessCalendarCalculationUnavailable(
        "Local calendar boundary could not be resolved in its IANA timezone."
    )
