from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest

import services.badge_service as svc


class FakeTx:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(
        self,
        row=None,
        rows=None,
        value=0,
        execute_result="INSERT 0 1",
    ):
        self.row = row
        self.rows = rows or []
        self.value = value
        self.execute_result = execute_result
        self.calls = []

    async def fetchrow(self, query, *params):
        self.calls.append(("fetchrow", query, params))
        return self.row

    async def fetch(self, query, *params):
        self.calls.append(("fetch", query, params))
        return self.rows

    async def fetchval(self, query, *params):
        self.calls.append(("fetchval", query, params))
        return self.value

    async def execute(self, query, *params):
        self.calls.append(("execute", query, params))
        return self.execute_result

    def transaction(self):
        return FakeTx()


def patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(svc, "db_connection", fake_db_connection)


def referral_row(referrer_ucn="123"):
    return {
        "referral_track_id": "track-1",
        "referrer_ucn": referrer_ucn,
    }


def badge_definition(
    code="FIRST_REFERRAL",
    trigger_type="REFERRAL_CREATED_COUNT",
    trigger_value=1,
):
    return {
        "badge_code": code,
        "badge_name": code,
        "badge_description": "Badge description",
        "badge_category": "REFERRAL",
        "trigger_type": trigger_type,
        "trigger_value": trigger_value,
        "icon_name": "star",
        "display_priority": 1,
        "regulatory_tags": ["TCF"],
    }


def awarded_badge_row():
    return {
        "badge_code": "FIRST_REFERRAL",
        "awarded_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "award_reason": "First referral created",
        "metadata_json": {"x": 1},
        "badge_name": "First Referral",
        "badge_description": "Created first referral",
        "badge_category": "REFERRAL",
        "icon_name": "star",
        "regulatory_tags": ["TCF"],
    }


@pytest.mark.asyncio
async def test_get_referral_row_found(monkeypatch):
    conn = FakeConn(row=referral_row())
    patch_db(monkeypatch, conn)

    result = await svc._get_referral_row("track-1")

    assert result["referrer_ucn"] == "123"


@pytest.mark.asyncio
async def test_get_referral_row_not_found(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    assert await svc._get_referral_row("missing") is None


@pytest.mark.asyncio
async def test_get_badge_definitions(monkeypatch):
    conn = FakeConn(rows=[badge_definition()])
    patch_db(monkeypatch, conn)

    result = await svc._get_badge_definitions()

    assert result[0]["badge_code"] == "FIRST_REFERRAL"


@pytest.mark.asyncio
async def test_badge_exists_true_and_false(monkeypatch):
    conn = FakeConn(row={"exists": 1})
    patch_db(monkeypatch, conn)

    assert await svc._badge_exists("123", "FIRST_REFERRAL") is True

    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    assert await svc._badge_exists("123", "FIRST_REFERRAL") is False


@pytest.mark.asyncio
async def test_award_badge_inserted(monkeypatch):
    conn = FakeConn(execute_result="INSERT 0 1")
    patch_db(monkeypatch, conn)

    result = await svc._award_badge(
        beneficiary_ref="123",
        badge_code="FIRST_REFERRAL",
        award_reason="First referral created",
        metadata={"a": 1},
        referral_track_id="track-1",
    )

    assert result is True


@pytest.mark.asyncio
async def test_award_badge_not_inserted(monkeypatch):
    conn = FakeConn(execute_result="INSERT 0 0")
    patch_db(monkeypatch, conn)

    result = await svc._award_badge(
        beneficiary_ref="123",
        badge_code="FIRST_REFERRAL",
        award_reason="Already exists",
    )

    assert result is False


@pytest.mark.asyncio
async def test_count_helpers(monkeypatch):
    conn = FakeConn(value=3)
    patch_db(monkeypatch, conn)

    assert await svc._count_referrals_created("123") == 3
    assert await svc._count_completed_referrals("123") == 3
    assert await svc._count_hve_referrals("123") == 3


@pytest.mark.asyncio
async def test_evaluate_and_award_referral_created_badge(monkeypatch):
    async def fake_created(ref):
        return 1

    async def fake_completed(ref):
        return 0

    async def fake_hve(ref):
        return 0

    async def fake_definitions():
        return [badge_definition()]

    async def fake_exists(ref, code):
        return False

    async def fake_award(**kwargs):
        return True

    monkeypatch.setattr(svc, "_count_referrals_created", fake_created)
    monkeypatch.setattr(svc, "_count_completed_referrals", fake_completed)
    monkeypatch.setattr(svc, "_count_hve_referrals", fake_hve)
    monkeypatch.setattr(svc, "_get_badge_definitions", fake_definitions)
    monkeypatch.setattr(svc, "_badge_exists", fake_exists)
    monkeypatch.setattr(svc, "_award_badge", fake_award)

    result = await svc._evaluate_and_award_badges("123", "track-1")

    assert len(result) == 1
    assert result[0]["badgeCode"] == "FIRST_REFERRAL"


@pytest.mark.asyncio
async def test_evaluate_and_award_completed_and_hve_badges(monkeypatch):
    async def fake_created(ref):
        return 0

    async def fake_completed(ref):
        return 2

    async def fake_hve(ref):
        return 1

    async def fake_definitions():
        return [
            badge_definition(
                code="COMPLETED_2",
                trigger_type="COMPLETED_REFERRALS_COUNT",
                trigger_value=2,
            ),
            badge_definition(
                code="HVE_1",
                trigger_type="HVE_COUNT",
                trigger_value=1,
            ),
        ]

    async def fake_exists(ref, code):
        return False

    async def fake_award(**kwargs):
        return True

    monkeypatch.setattr(svc, "_count_referrals_created", fake_created)
    monkeypatch.setattr(svc, "_count_completed_referrals", fake_completed)
    monkeypatch.setattr(svc, "_count_hve_referrals", fake_hve)
    monkeypatch.setattr(svc, "_get_badge_definitions", fake_definitions)
    monkeypatch.setattr(svc, "_badge_exists", fake_exists)
    monkeypatch.setattr(svc, "_award_badge", fake_award)

    result = await svc._evaluate_and_award_badges("123", "track-1")

    assert [b["badgeCode"] for b in result] == ["COMPLETED_2", "HVE_1"]


@pytest.mark.asyncio
async def test_evaluate_and_award_skips_when_threshold_not_met(monkeypatch):
    async def fake_count(ref):
        return 0

    async def fake_definitions():
        return [badge_definition(trigger_value=5)]

    monkeypatch.setattr(svc, "_count_referrals_created", fake_count)
    monkeypatch.setattr(svc, "_count_completed_referrals", fake_count)
    monkeypatch.setattr(svc, "_count_hve_referrals", fake_count)
    monkeypatch.setattr(svc, "_get_badge_definitions", fake_definitions)

    result = await svc._evaluate_and_award_badges("123")

    assert result == []


@pytest.mark.asyncio
async def test_evaluate_and_award_skips_existing_badge(monkeypatch):
    async def fake_created(ref):
        return 10

    async def fake_zero(ref):
        return 0

    async def fake_definitions():
        return [badge_definition()]

    async def fake_exists(ref, code):
        return True

    monkeypatch.setattr(svc, "_count_referrals_created", fake_created)
    monkeypatch.setattr(svc, "_count_completed_referrals", fake_zero)
    monkeypatch.setattr(svc, "_count_hve_referrals", fake_zero)
    monkeypatch.setattr(svc, "_get_badge_definitions", fake_definitions)
    monkeypatch.setattr(svc, "_badge_exists", fake_exists)

    result = await svc._evaluate_and_award_badges("123")

    assert result == []


@pytest.mark.asyncio
async def test_evaluate_badges_for_referral_created(monkeypatch):
    async def fake_referral(track):
        return referral_row("123")

    async def fake_eval(beneficiary_ref, referral_track_id=None, referrer_hash=None):
        return [{"badgeCode": "FIRST_REFERRAL"}]

    monkeypatch.setattr(svc, "_get_referral_row", fake_referral)
    monkeypatch.setattr(svc, "_evaluate_and_award_badges", fake_eval)

    result = await svc.evaluate_badges_for_referral_created("track-1")

    assert result == [{"badgeCode": "FIRST_REFERRAL"}]


@pytest.mark.asyncio
async def test_evaluate_badges_for_referral_created_no_referrer(monkeypatch):
    async def fake_referral(track):
        return {"referral_track_id": track, "referrer_ucn": None}

    monkeypatch.setattr(svc, "_get_referral_row", fake_referral)

    result = await svc.evaluate_badges_for_referral_created("track-1")

    assert result == []


@pytest.mark.asyncio
async def test_evaluate_badges_for_referral_completion(monkeypatch):
    async def fake_referral(track):
        return referral_row("123")

    async def fake_eval(beneficiary_ref, referral_track_id=None, referrer_hash=None):
        return [{"badgeCode": "COMPLETED_1"}]

    monkeypatch.setattr(svc, "_get_referral_row", fake_referral)
    monkeypatch.setattr(svc, "_evaluate_and_award_badges", fake_eval)

    result = await svc.evaluate_badges_for_referral_completion("track-1")

    assert result == [{"badgeCode": "COMPLETED_1"}]


@pytest.mark.asyncio
async def test_evaluate_badges_for_hve_event_invalid_event():
    result = await svc.evaluate_badges_for_hve_event("track-1", "NOT_HVE")

    assert result == []


@pytest.mark.asyncio
async def test_evaluate_badges_for_hve_event_valid(monkeypatch):
    async def fake_referral(track):
        return referral_row("123")

    async def fake_eval(beneficiary_ref, referral_track_id=None, referrer_hash=None):
        return [{"badgeCode": "HVE_1"}]

    monkeypatch.setattr(svc, "_get_referral_row", fake_referral)
    monkeypatch.setattr(svc, "_evaluate_and_award_badges", fake_eval)

    result = await svc.evaluate_badges_for_hve_event(
        "track-1",
        "SALARY_SWITCHED",
    )

    assert result == [{"badgeCode": "HVE_1"}]


@pytest.mark.asyncio
async def test_list_badges_for_referral(monkeypatch):
    async def fake_referral(track):
        return referral_row("123")

    async def fake_list(referrer_ucn, tenant_code=None):
        return [{"badgeCode": "FIRST_REFERRAL"}]

    monkeypatch.setattr(svc, "_get_referral_row", fake_referral)
    monkeypatch.setattr(svc, "list_badges_for_referrer", fake_list)

    result = await svc.list_badges_for_referral("track-1", tenant_code="FNB")

    assert result == [{"badgeCode": "FIRST_REFERRAL"}]


@pytest.mark.asyncio
async def test_list_badges_for_referral_no_referrer(monkeypatch):
    async def fake_referral(track):
        return None

    monkeypatch.setattr(svc, "_get_referral_row", fake_referral)

    result = await svc.list_badges_for_referral("track-1", tenant_code="FNB")

    assert result == []


@pytest.mark.asyncio
async def test_list_badges_for_referrer(monkeypatch):
    conn = FakeConn(rows=[awarded_badge_row()])
    patch_db(monkeypatch, conn)

    result = await svc.list_badges_for_referrer("123", tenant_code="FNB")

    assert len(result) == 1
    assert result[0]["badgeCode"] == "FIRST_REFERRAL"
    assert result[0]["compliance"]["blocked"] is False


def test_format_badge():
    result = svc._format_badge(
        badge_definition(),
        "First referral created",
    )

    assert result["badgeCode"] == "FIRST_REFERRAL"
    assert result["awardReason"] == "First referral created"
