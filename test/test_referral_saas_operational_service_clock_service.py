from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from services import referral_saas_operational_service_clock_service as service


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
        )

    monkeypatch.setattr(service, "resolve_service_target_policy", resolved)
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


def test_clock_safe_projection_pins_policy_and_outcome():
    row = {
        "service_target_clock_id": "clock", "support_case_id": "case",
        "account_id": "account", "service_target_policy_id": "policy",
        "policy_code": "SUPPORT_HIGH", "policy_version_number": 3,
        "clock_status": "COMPLETED", "started_at": NOW,
        "warning_at": NOW, "due_at": NOW,
        "accumulated_paused_seconds": 60, "completed_at": NOW,
        "breached_at": None, "completion_outcome": "WITHIN_TARGET",
    }
    clock = service._clock(row)
    assert clock.policy_version_number == 3
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
