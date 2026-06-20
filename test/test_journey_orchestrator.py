from __future__ import annotations

import datetime
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest

import services.journey_orchestrator as svc


class FakeTx:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self, row=None, fail_fetch=False, fail_execute=False):
        self.row = row
        self.fail_fetch = fail_fetch
        self.fail_execute = fail_execute
        self.calls = []

    async def fetchrow(self, query, *params):
        self.calls.append(("fetchrow", query, params))
        if self.fail_fetch:
            raise RuntimeError("db fetch failed")
        return self.row

    async def execute(self, query, *params):
        self.calls.append(("execute", query, params))
        if self.fail_execute:
            raise RuntimeError("db execute failed")
        return "OK"

    def transaction(self):
        return FakeTx()


def patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(svc, "db_connection", fake_db_connection)


def referral_instance(**overrides):
    data = {
        "tenant_code": "FNB",
        "referral_track_id": "track-1",
        "referrer_ucn": "referrer-1",
        "product": "Transactional",
        "sub_product": "DDA",
        "status": "VALIDATED",
        "journey_code": "BANKING_TRANSACTIONAL",
        "journey_version": "v1",
        "referee_ucn": None,
        "referee_ucn_hash": None,
        "referee_account_number": None,
        "referee_account_hash": None,
        "referee_account_masked": None,
        "referee_alias": None,
        "referee_alias_normalized": None,
        "ucn_captured_at": None,
        "account_opened_at": None,
        "account_activated_at": None,
        "funded_at": None,
        "debit_order_switched_at": None,
        "salary_switched_at": None,
        "first_transaction_completed_at": None,
        "progress_percent": 0,
        "progress_band": "STARTED",
        "display_status": "Started",
        "next_milestone": "UCN_CAPTURED",
        "is_complete": False,
        "completed_at": None,
        "updated_at": None,
    }
    data.update(overrides)
    return data


def progress_event(**overrides):
    data = {
        "eventType": "REFERRAL_PROGRESS_RECORDED",
        "progressEventType": "UCN_CAPTURED",
        "referralTrackId": "track-1",
        "correlationId": "corr-1",
        "sourceSystem": "unit-test",
        "occurredAt": "2026-01-01T00:00:00Z",
    }
    data.update(overrides)
    return data


def journey_definition():
    return SimpleNamespace(
        core_sequence=[
            "VALIDATED",
            "UCN_CAPTURED",
            "ACCOUNT_OPENED",
            "ACCOUNT_ACTIVATED",
            "FUNDED",
        ],
        allowed_transitions={
            "VALIDATED": {"UCN_CAPTURED"},
            "UCN_CAPTURED": {"ACCOUNT_OPENED"},
            "ACCOUNT_OPENED": {"ACCOUNT_ACTIVATED"},
            "ACCOUNT_ACTIVATED": {"FUNDED"},
            "FUNDED": {
                "DEBIT_ORDER_SWITCHED",
                "SALARY_SWITCHED",
                "FIRST_TRANSACTION_COMPLETED",
            },
        },
        event_to_timestamp_field={
            "UCN_CAPTURED": "ucn_captured_at",
            "ACCOUNT_OPENED": "account_opened_at",
            "ACCOUNT_ACTIVATED": "account_activated_at",
            "FUNDED": "funded_at",
            "DEBIT_ORDER_SWITCHED": "debit_order_switched_at",
            "SALARY_SWITCHED": "salary_switched_at",
            "FIRST_TRANSACTION_COMPLETED": "first_transaction_completed_at",
        },
    )


def progress_definition():
    milestone = SimpleNamespace(
        progress_percent=20,
        progress_band="UCN_CAPTURED",
        display_status="UCN captured",
        next_milestone="ACCOUNT_OPENED",
    )
    return SimpleNamespace(
        milestones={"UCN_CAPTURED": milestone},
        complete_band="COMPLETE",
        complete_display_status="Complete",
    )


@pytest.fixture(autouse=True)
def patch_common(monkeypatch):
    monkeypatch.setattr(svc, "log_event", lambda **kwargs: None)
    monkeypatch.setattr(svc, "get_journey_definition", lambda *a, **k: journey_definition())
    monkeypatch.setattr(svc, "get_progress_definition", lambda *a, **k: progress_definition())


def test_normalize_event_maps_known_types():
    result = svc.normalize_event({"eventType": "UCN_CREATED"})

    assert result["sourceEventType"] == "UCN_CREATED"
    assert result["normalizedEventType"] == "ACCOUNT_OPENED"


def test_parse_occurred_at_defaults_and_parses():
    parsed = svc._parse_occurred_at({"occurredAt": "2026-01-01T00:00:00Z"})
    defaulted = svc._parse_occurred_at({})

    assert parsed.tzinfo is not None
    assert isinstance(defaulted, datetime.datetime)


def test_ensure_utc_handles_naive_aware_and_none():
    naive = datetime.datetime(2026, 1, 1, 0, 0, 0)
    aware = datetime.datetime(2026, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

    assert svc._ensure_utc(None) is None
    assert svc._ensure_utc(naive).tzinfo is None
    assert svc._ensure_utc(aware).tzinfo is None


def test_transition_helpers():
    jd = journey_definition()

    instance = referral_instance(status="VALIDATED")
    assert svc._classify_transition(instance, "UCN_CAPTURED", jd) == "valid"

    instance = referral_instance(status="UCN_CAPTURED", ucn_captured_at=datetime.datetime.utcnow())
    assert svc._classify_transition(instance, "UCN_CAPTURED", jd) == "duplicate"

    instance = referral_instance(status="ACCOUNT_OPENED")
    assert svc._classify_transition(instance, "UCN_CAPTURED", jd) == "backward"

    instance = referral_instance(status="VALIDATED")
    assert svc._classify_transition(instance, "FUNDED", jd) == "out_of_order"

    instance = referral_instance(status="BAD")
    assert svc._classify_transition(instance, "UNKNOWN", jd) == "invalid"


def test_apply_progress_event_to_instance_valid():
    instance = referral_instance(status="VALIDATED")
    result = svc.apply_progress_event_to_instance(
        instance=instance,
        incoming_event="UCN_CAPTURED",
        occurred_at=datetime.datetime.now(datetime.timezone.utc),
        journey_definition=journey_definition(),
        journey_code="BANKING_TRANSACTIONAL",
        journey_version="v1",
    )

    assert result == "valid"
    assert instance["status"] == "UCN_CAPTURED"
    assert instance["progress_percent"] == 20


def test_apply_progress_event_to_instance_invalid():
    instance = referral_instance(status="VALIDATED")
    result = svc.apply_progress_event_to_instance(
        instance=instance,
        incoming_event="FUNDED",
        occurred_at=datetime.datetime.now(datetime.timezone.utc),
        journey_definition=journey_definition(),
        journey_code="BANKING_TRANSACTIONAL",
        journey_version="v1",
    )

    assert result == "out_of_order"


@pytest.mark.asyncio
async def test_handle_referral_progress_recorded_requires_tenant():
    with pytest.raises(ValueError, match="tenant_code is required"):
        await svc.handle_referral_progress_recorded(progress_event(), tenant_code="")


@pytest.mark.asyncio
async def test_handle_referral_progress_recorded_ignores_non_progress_event():
    await svc.handle_referral_progress_recorded(
        {"eventType": "OTHER", "referralTrackId": "track-1"},
        tenant_code="FNB",
    )


@pytest.mark.asyncio
async def test_handle_referral_progress_recorded_ignores_deduped_event():
    await svc.handle_referral_progress_recorded(
        progress_event(deduped=True),
        tenant_code="FNB",
    )


@pytest.mark.asyncio
async def test_handle_referral_progress_recorded_missing_track_id_raises():
    with pytest.raises(ValueError, match="Missing referralTrackId"):
        await svc.handle_referral_progress_recorded(
            progress_event(referralTrackId=""),
            tenant_code="FNB",
        )


@pytest.mark.asyncio
async def test_handle_referral_progress_recorded_referral_not_found(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    await svc.handle_referral_progress_recorded(progress_event(), tenant_code="FNB")

    assert conn.calls[0][0] == "fetchrow"


@pytest.mark.asyncio
async def test_handle_referral_progress_recorded_self_referral(monkeypatch):
    conn = FakeConn(
        row=referral_instance(
            referrer_ucn="same",
            referee_ucn=None,
        )
    )
    patch_db(monkeypatch, conn)

    audits = []

    async def fake_audit(**kwargs):
        audits.append(kwargs)

    monkeypatch.setattr(svc, "_write_processing_audit_async", fake_audit)

    await svc.handle_referral_progress_recorded(
        progress_event(refereeUCN="same"),
        tenant_code="FNB",
    )

    assert audits[0]["processing_status"] == "IGNORED"
    assert audits[0]["reason"] == "SELF_REFERRAL_NOT_ALLOWED"


@pytest.mark.asyncio
async def test_handle_referral_progress_recorded_invalid_transition(monkeypatch):
    conn = FakeConn(row=referral_instance(status="VALIDATED"))
    patch_db(monkeypatch, conn)

    audits = []

    async def fake_audit(**kwargs):
        audits.append(kwargs)

    monkeypatch.setattr(svc, "_write_processing_audit_async", fake_audit)

    await svc.handle_referral_progress_recorded(
        progress_event(progressEventType="FUNDED"),
        tenant_code="FNB",
    )

    assert audits[0]["processing_status"] == "IGNORED"
    assert audits[0]["reason"] == "out_of_order"


@pytest.mark.asyncio
async def test_handle_referral_progress_recorded_valid_flow(monkeypatch):
    conn = FakeConn(row=referral_instance(status="VALIDATED"))
    patch_db(monkeypatch, conn)

    calls = {
        "audit": [],
        "reward": 0,
        "badges": 0,
        "missions": [],
        "leaderboard": [],
    }

    async def fake_audit(**kwargs):
        calls["audit"].append(kwargs)

    async def fake_rewards(before, after):
        calls["reward"] += 1

    async def fake_badges(**kwargs):
        calls["badges"] += 1

    async def fake_missions(referral_track_id, event_type, tenant_code=None):
        calls["missions"].append((referral_track_id, event_type, tenant_code))
        return [{"missionCode": "M1"}]

    async def fake_leaderboard(**kwargs):
        calls["leaderboard"].append(kwargs)

    monkeypatch.setattr(svc, "_write_processing_audit_async", fake_audit)
    monkeypatch.setattr(svc, "_issue_base_rewards_if_eligible_async", fake_rewards)
    monkeypatch.setattr(svc, "_issue_badges_async", fake_badges)
    monkeypatch.setattr(svc, "apply_event_to_missions", fake_missions)
    monkeypatch.setattr(svc, "_publish_leaderboard_rebuild", fake_leaderboard)

    await svc.handle_referral_progress_recorded(progress_event(), tenant_code="FNB")

    execute_calls = [call for call in conn.calls if call[0] == "execute"]

    assert execute_calls
    assert calls["audit"][0]["processing_status"] == "PROCESSED"
    assert calls["reward"] == 1
    assert calls["badges"] == 1
    assert calls["missions"] == [("track-1", "UCN_CAPTURED", "FNB")]
    assert calls["leaderboard"][0]["tenant_code"] == "FNB"
    assert calls["leaderboard"][0]["referrer_ucn"] == "referrer-1"


@pytest.mark.asyncio
async def test_handle_referral_progress_recorded_binds_event_journey_when_instance_is_unbound(monkeypatch):
    conn = FakeConn(row=referral_instance(journey_code=None, journey_version=None))
    patch_db(monkeypatch, conn)

    async def fake_audit(**kwargs):
        return None

    async def fake_rewards(before, after):
        return None

    async def fake_badges(**kwargs):
        return None

    async def fake_missions(**kwargs):
        return []

    async def fake_leaderboard(**kwargs):
        return None

    monkeypatch.setattr(svc, "_write_processing_audit_async", fake_audit)
    monkeypatch.setattr(svc, "_issue_base_rewards_if_eligible_async", fake_rewards)
    monkeypatch.setattr(svc, "_issue_badges_async", fake_badges)
    monkeypatch.setattr(svc, "apply_event_to_missions", fake_missions)
    monkeypatch.setattr(svc, "_publish_leaderboard_rebuild", fake_leaderboard)

    await svc.handle_referral_progress_recorded(
        progress_event(
            journeyCode="INSURANCE_POLICY",
            journeyVersion="v1",
        ),
        tenant_code="FNB",
    )

    execute_call = next(call for call in conn.calls if call[0] == "execute")
    params = execute_call[2]
    assert params[1] == "INSURANCE_POLICY"
    assert params[2] == "v1"


@pytest.mark.asyncio
async def test_handle_referral_progress_recorded_downstream_failures_are_logged(monkeypatch):
    conn = FakeConn(row=referral_instance(status="VALIDATED"))
    patch_db(monkeypatch, conn)

    async def fake_audit(**kwargs):
        return None

    async def fail_rewards(before, after):
        raise RuntimeError("reward failed")

    async def fail_badges(**kwargs):
        raise RuntimeError("badges failed")

    async def fail_missions(**kwargs):
        raise RuntimeError("missions failed")

    async def fail_leaderboard(**kwargs):
        raise RuntimeError("leaderboard failed")

    monkeypatch.setattr(svc, "_write_processing_audit_async", fake_audit)
    monkeypatch.setattr(svc, "_issue_base_rewards_if_eligible_async", fail_rewards)
    monkeypatch.setattr(svc, "_issue_badges_async", fail_badges)
    monkeypatch.setattr(svc, "apply_event_to_missions", fail_missions)
    monkeypatch.setattr(svc, "_publish_leaderboard_rebuild", fail_leaderboard)

    await svc.handle_referral_progress_recorded(progress_event(), tenant_code="FNB")


@pytest.mark.asyncio
async def test_handle_referral_progress_recorded_db_error_writes_failed_audit(monkeypatch):
    conn = FakeConn(row=referral_instance(status="VALIDATED"), fail_execute=True)
    patch_db(monkeypatch, conn)

    audits = []

    async def fake_audit(**kwargs):
        audits.append(kwargs)

    monkeypatch.setattr(svc, "_write_processing_audit_async", fake_audit)

    with pytest.raises(RuntimeError, match="db execute failed"):
        await svc.handle_referral_progress_recorded(progress_event(), tenant_code="FNB")

    assert audits[-1]["processing_status"] == "FAILED"


@pytest.mark.asyncio
async def test_publish_leaderboard_rebuild_awaits_publisher(monkeypatch):
    captured = {}

    async def fake_publish(**kwargs):
        captured.update(kwargs)
        return {"status": "published"}

    monkeypatch.setattr(
        svc,
        "publish_leaderboard_rebuild_requested",
        fake_publish,
    )

    await svc._publish_leaderboard_rebuild(
        tenant_code="FNB",
        referrer_ucn="123",
        correlation_id="corr",
        referral_track_id="track",
    )

    assert captured["tenant_code"] == "FNB"
    assert captured["referrer_ucn"] == "123"


@pytest.mark.asyncio
async def test_issue_wrappers_call_async_reward_and_async_badges(monkeypatch):
    reward_called = {}
    badge_called = {}

    async def fake_reward(before, after):
        reward_called["called"] = True

    async def fake_badges(**kwargs):
        badge_called["called"] = True

    monkeypatch.setattr(svc, "_issue_base_rewards_if_eligible", fake_reward)
    monkeypatch.setattr(svc, "_issue_badges", fake_badges)

    await svc._issue_base_rewards_if_eligible_async({}, {})
    await svc._issue_badges_async(
        referral_before={},
        referral_after={},
        incoming_event="UCN_CAPTURED",
        correlation_id="corr",
        referral_track_id="track",
        source_system="test",
        dedupe_key=None,
    )

    assert reward_called["called"] is True
    assert badge_called["called"] is True
