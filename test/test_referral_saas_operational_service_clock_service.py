from contextlib import asynccontextmanager
from datetime import datetime, time, timezone
from types import SimpleNamespace
import uuid

import pytest

from services import referral_saas_operational_service_clock_service as service
from services.referral_saas_service_target_calendar_service import (
    ServiceTargetCalendarResolutionUnavailable,
    ServiceTargetCalendarVersion,
    WeeklyInterval,
)


NOW = datetime(2026, 8, 22, 10, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_clock_stays_unavailable_when_no_approved_policy(monkeypatch):
    async def unavailable(**_kwargs):
        raise service.ServiceTargetPolicyResolutionUnavailable("missing")

    monkeypatch.setattr(service, "resolve_service_target_policy", unavailable)
    clock, status = await service.start_support_case_service_target_clock(
        account_id="00000000-0000-0000-0000-000000000001",
        support_case_id="00000000-0000-0000-0000-000000000002",
        operating_jurisdiction_code="ZA", work_category="ACCESS_SCOPE",
        priority="HIGH", started_at=NOW, actor_ref="operator",
        actor_role="PLATFORM_ADMIN", correlation_id="corr",
        idempotency_key_hash="idem", request_payload_hash="payload",
    )
    assert clock is None
    assert status == "POLICY_UNAVAILABLE"


@pytest.mark.asyncio
async def test_clock_refuses_to_invent_business_calendar_time(monkeypatch):
    async def resolved(**_kwargs):
        return SimpleNamespace(
            start_event="SUPPORT_CASE_CREATED", business_calendar_ref="ZA_BUSINESS",
            business_timezone="Africa/Johannesburg",
        )

    async def unavailable(**_kwargs):
        raise ServiceTargetCalendarResolutionUnavailable("missing")

    monkeypatch.setattr(service, "resolve_service_target_policy", resolved)
    monkeypatch.setattr(service, "resolve_service_target_calendar", unavailable)
    clock, status = await service.start_support_case_service_target_clock(
        account_id="00000000-0000-0000-0000-000000000001",
        support_case_id="00000000-0000-0000-0000-000000000002",
        operating_jurisdiction_code="ZA", work_category="ACCESS_SCOPE",
        priority="HIGH", started_at=NOW, actor_ref="operator",
        actor_role="PLATFORM_ADMIN", correlation_id="corr",
        idempotency_key_hash="idem", request_payload_hash="payload",
    )
    assert clock is None
    assert status == "BUSINESS_CALENDAR_UNAVAILABLE"


def _approved_calendar(*, business_timezone="Africa/Johannesburg"):
    return ServiceTargetCalendarVersion(
        calendar_version_id="00000000-0000-0000-0000-000000000003",
        calendar_code="ZA_BUSINESS", version_number=4, scope_type="ACCOUNT",
        account_id="00000000-0000-0000-0000-000000000001",
        calendar_name="South Africa support hours",
        business_timezone=business_timezone, lifecycle_status="APPROVED",
        effective_from=NOW, effective_to=None, created_by_ref="author",
        reviewed_by_ref="reviewer", reviewed_at=NOW,
        approved_by_ref="approver", approved_at=NOW, metadata={},
        created_at=NOW, updated_at=NOW, retired_at=None,
        weekly_intervals=tuple(
            WeeklyInterval(day, time(9), time(17)) for day in range(1, 6)
        ),
        date_exceptions=(),
    )


class _Transaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False


class _ClockConnection:
    def __init__(self):
        self.insert_args = None

    def transaction(self):
        return _Transaction()

    async def fetchrow(self, query, *args):
        if "SELECT * FROM referral_saas_operational_service_target_clocks" in query:
            return None
        if "INSERT INTO referral_saas_operational_service_target_clocks" in query:
            self.insert_args = args
            return {
                "service_target_clock_id": args[0], "support_case_id": args[1],
                "account_id": args[2], "service_target_policy_id": args[3],
                "policy_code": args[4], "policy_version_number": args[5],
                "service_target_calendar_version_id": args[6],
                "calendar_code": args[7], "calendar_version_number": args[8],
                "calendar_timezone": args[9], "clock_status": "RUNNING",
                "started_at": args[10], "warning_at": args[11], "due_at": args[12],
                "accumulated_paused_seconds": 0, "completed_at": None,
                "breached_at": None, "completion_outcome": None,
            }
        raise AssertionError(query)

    async def execute(self, *_args):
        return "INSERT 0 1"


@pytest.mark.asyncio
async def test_clock_pins_calendar_and_uses_working_time(monkeypatch):
    policy_id = "00000000-0000-0000-0000-000000000004"

    async def resolved_policy(**_kwargs):
        return SimpleNamespace(
            policy_id=policy_id, policy_code="SUPPORT_HIGH", version_number=2,
            start_event="SUPPORT_CASE_CREATED", business_calendar_ref="ZA_BUSINESS",
            business_timezone="Africa/Johannesburg",
            warning_threshold_minutes=60, target_duration_minutes=120,
        )

    async def resolved_calendar(**kwargs):
        assert kwargs["account_id"] == "00000000-0000-0000-0000-000000000001"
        return _approved_calendar()

    connection = _ClockConnection()

    @asynccontextmanager
    async def fake_db_connection():
        yield connection

    monkeypatch.setattr(service, "resolve_service_target_policy", resolved_policy)
    monkeypatch.setattr(service, "resolve_service_target_calendar", resolved_calendar)
    monkeypatch.setattr(service, "db_connection", fake_db_connection)
    friday = datetime(2026, 8, 21, 14, 0, tzinfo=timezone.utc)

    clock, status = await service.start_support_case_service_target_clock(
        account_id="00000000-0000-0000-0000-000000000001",
        support_case_id="00000000-0000-0000-0000-000000000002",
        operating_jurisdiction_code="ZA", work_category="ACCESS_SCOPE",
        priority="HIGH", started_at=friday, actor_ref="operator",
        actor_role="PLATFORM_ADMIN", correlation_id="corr",
        idempotency_key_hash="idem", request_payload_hash="payload",
    )

    assert status == "CLOCK_STARTED"
    assert clock is not None
    assert clock.calendar_code == "ZA_BUSINESS"
    assert clock.calendar_version_number == 4
    assert clock.calendar_version_id == "00000000-0000-0000-0000-000000000003"
    assert clock.warning_at == datetime(2026, 8, 21, 15, 0, tzinfo=timezone.utc)
    assert clock.due_at == datetime(2026, 8, 24, 8, 0, tzinfo=timezone.utc)
    assert connection.insert_args[6] == uuid.UUID(clock.calendar_version_id)


@pytest.mark.asyncio
async def test_clock_fails_closed_on_policy_calendar_timezone_mismatch(monkeypatch):
    async def resolved_policy(**_kwargs):
        return SimpleNamespace(
            start_event="SUPPORT_CASE_CREATED", business_calendar_ref="ZA_BUSINESS",
            business_timezone="UTC", warning_threshold_minutes=60,
            target_duration_minutes=120,
        )

    async def resolved_calendar(**_kwargs):
        return _approved_calendar()

    monkeypatch.setattr(service, "resolve_service_target_policy", resolved_policy)
    monkeypatch.setattr(service, "resolve_service_target_calendar", resolved_calendar)
    clock, status = await service.start_support_case_service_target_clock(
        account_id="00000000-0000-0000-0000-000000000001",
        support_case_id="00000000-0000-0000-0000-000000000002",
        operating_jurisdiction_code="ZA", work_category="ACCESS_SCOPE",
        priority="HIGH", started_at=NOW, actor_ref="operator",
        actor_role="PLATFORM_ADMIN", correlation_id="corr",
        idempotency_key_hash="idem", request_payload_hash="payload",
    )
    assert clock is None
    assert status == "BUSINESS_CALENDAR_TIMEZONE_MISMATCH"


def test_clock_safe_projection_pins_policy_and_outcome():
    row = {
        "service_target_clock_id": "clock", "support_case_id": "case",
        "account_id": "account", "service_target_policy_id": "policy",
        "policy_code": "SUPPORT_HIGH", "policy_version_number": 3,
        "service_target_calendar_version_id": "calendar-version",
        "calendar_code": "ZA_BUSINESS", "calendar_version_number": 4,
        "calendar_timezone": "Africa/Johannesburg",
        "clock_status": "COMPLETED", "started_at": NOW,
        "warning_at": NOW, "due_at": NOW,
        "accumulated_paused_seconds": 60, "completed_at": NOW,
        "breached_at": None, "completion_outcome": "WITHIN_TARGET",
    }
    clock = service._clock(row)
    assert clock.policy_version_number == 3
    assert clock.calendar_version_number == 4
    assert clock.completion_outcome == "WITHIN_TARGET"
    assert clock.accumulated_paused_seconds == 60


def test_clock_guardrails_keep_time_server_owned_and_money_outside_boundary():
    assert "SERVER_OWNED_CLOCK" in service.CLOCK_GUARDRAILS
    assert "NO_BROWSER_TIMER" in service.CLOCK_GUARDRAILS
    assert "NO_BILLING_OR_MONEY_MOVEMENT" in service.CLOCK_GUARDRAILS


def test_clock_window_uses_elapsed_threshold_from_server_start():
    start, warning_at, due_at = service._clock_window(
        started_at=NOW,
        warning_threshold_minutes=30,
        target_duration_minutes=120,
    )
    assert start == NOW
    assert warning_at == datetime(2026, 8, 22, 10, 30, tzinfo=timezone.utc)
    assert due_at == datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)


def test_clock_window_allows_immediate_warning_without_invalid_due_time():
    _, warning_at, due_at = service._clock_window(
        started_at=NOW,
        warning_threshold_minutes=0,
        target_duration_minutes=60,
    )
    assert warning_at == NOW
    assert warning_at < due_at
