from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import pytest

import services.recommendation_service as rs


class FakeTx:
    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ):
        return False


class FakeConn:
    def __init__(self, row=None):
        self.row = row
        self.calls = []

    async def fetchrow(
        self,
        query,
        *params,
    ):
        self.calls.append(
            (
                "fetchrow",
                query,
                params,
            )
        )
        return self.row

    async def execute(
        self,
        query,
        *params,
    ):
        self.calls.append(
            (
                "execute",
                query,
                params,
            )
        )
        return "OK"

    def transaction(self):
        return FakeTx()


def patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(rs, "db_connection", fake_db_connection)


def test_score_calculation():
    assert rs._score(0.5, value=0.5, effort=0.5) == 0.4


def test_iso_timezone_and_naive():
    aware = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    naive = datetime(2026, 1, 1, 10, 0)

    assert rs._iso(aware) == "2026-01-01T10:00:00Z"
    assert rs._iso(naive) == "2026-01-01T10:00:00Z"


def test_is_allowed_all_branches():
    assert rs._is_allowed("SEND_INVITE", "REFERRER") is True
    assert rs._is_allowed("COMPLETE_YOUR_APPLICATION", "REFERRER") is False
    assert rs._is_allowed("COMPLETE_YOUR_APPLICATION", "SELF") is True
    assert rs._is_allowed("APPLY_REWARD", "REFERRER") is True
    assert rs._is_allowed("SUPPRESS_NUDGE", "REFERRER") is True
    assert rs._is_allowed("UNKNOWN", "REFERRER") is False


def test_reason_codes_filters_empty_values():
    assert rs._reason_codes("A", "", None, "B") == ["A", "B"]


@pytest.mark.asyncio
async def test_get_referrer_ucn_found(monkeypatch):
    conn = FakeConn(row={"referrer_ucn": "123456789"})
    patch_db(monkeypatch, conn)

    assert await rs._get_referrer_ucn("hash-1") == "123456789"


@pytest.mark.asyncio
async def test_get_referrer_ucn_not_found(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    assert await rs._get_referrer_ucn("hash-1") is None


@pytest.mark.asyncio
async def test_closest_mission_for_not_found(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    assert await rs._closest_mission_for("hash-1") is None


@pytest.mark.asyncio
async def test_closest_mission_for_found(monkeypatch):
    conn = FakeConn(
        row={
            "mission_code": "MISSION_1",
            "title": "Invite 3 friends",
            "progress": 2,
            "goal": 3,
            "reward_points": 100,
        }
    )
    patch_db(monkeypatch, conn)

    result = await rs._closest_mission_for("hash-1")

    assert result["action"] == "COMPLETE_MISSION"
    assert result["audience"] == "REFERRER"
    assert result["meta"]["mission_code"] == "MISSION_1"


@pytest.mark.asyncio
async def test_hour_with_best_response_found(monkeypatch):
    conn = FakeConn(row={"hour_of_day": 15})
    patch_db(monkeypatch, conn)

    assert await rs._hour_with_best_response("hash-1") == 15


@pytest.mark.asyncio
async def test_hour_with_best_response_not_found(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    assert await rs._hour_with_best_response("hash-1") is None


@pytest.mark.asyncio
async def test_hour_with_best_response_db_error(monkeypatch):
    def boom():
        raise Exception("db down")

    monkeypatch.setattr(rs, "db_connection", boom)

    assert await rs._hour_with_best_response("hash-1") is None


@pytest.mark.asyncio
async def test_invite_nudge_without_best_hour(monkeypatch):
    async def fake_hour(referrer_hash):
        return None

    monkeypatch.setattr(rs, "_hour_with_best_response", fake_hour)

    result = await rs._invite_nudge_for("hash-1")

    assert result["action"] == "SEND_INVITE"
    assert result["meta"]["bestHour"] is None


@pytest.mark.asyncio
async def test_invite_nudge_with_best_hour(monkeypatch):
    async def fake_hour(referrer_hash):
        return 14

    monkeypatch.setattr(rs, "_hour_with_best_response", fake_hour)

    result = await rs._invite_nudge_for("hash-1")

    assert result["action"] == "SEND_INVITE"
    assert result["meta"]["bestHour"] == 14


@pytest.mark.asyncio
async def test_dangling_rewards_not_found(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    assert await rs._dangling_rewards("hash-1") is None


@pytest.mark.asyncio
async def test_dangling_rewards_found(monkeypatch):
    conn = FakeConn(
        row={
            "referral_track_id": "track-1",
            "last_event_at": datetime(
                2026,
                1,
                1,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            "qualifying_event_count": 3,
        }
    )
    patch_db(monkeypatch, conn)

    result = await rs._dangling_rewards("hash-1")

    assert result["action"] == "APPLY_REWARD"
    assert result["audience"] == "OPS"

    assert (
        result["meta"]["referralTrackId"]
        == "track-1"
    )

    assert (
        result["meta"]["lastQualifyingEventAt"]
        == "2026-01-01T10:00:00Z"
    )

    assert (
        result["meta"]["qualifyingEventCount"]
        == 3
    )


@pytest.mark.asyncio
async def test_latest_self_referral_no_referrer_ucn(monkeypatch):
    async def fake_get(referrer_hash):
        return None

    monkeypatch.setattr(rs, "_get_referrer_ucn", fake_get)

    assert await rs._latest_self_referral("hash-1") is None


@pytest.mark.asyncio
async def test_latest_self_referral_no_row(monkeypatch):
    async def fake_get(referrer_hash):
        return "123"

    monkeypatch.setattr(rs, "_get_referrer_ucn", fake_get)

    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    assert await rs._latest_self_referral("hash-1") is None


@pytest.mark.asyncio
async def test_latest_self_referral_found(monkeypatch):
    async def fake_get(referrer_hash):
        return "123"

    monkeypatch.setattr(rs, "_get_referrer_ucn", fake_get)

    created = datetime(
        2026,
        1,
        1,
        10,
        0,
        tzinfo=timezone.utc,
    )

    conn = FakeConn(
        row={
            "referral_track_id": "track-1",
            "status": "VALIDATED",
            "created_at": created,
            "account_opened_at": None,
            "account_activated_at": None,
            "funded_at": None,
            "debit_order_switched_at": None,
            "salary_switched_at": None,
            "first_transaction_completed_at": None,
        }
    )

    patch_db(monkeypatch, conn)

    result = await rs._latest_self_referral("hash-1")

    assert result["referralTrackId"] == "track-1"
    assert result["referral_track_id"] == "track-1"
    assert result["status"] == "VALIDATED"
    assert result["createdAt"] == created
    assert result["accountOpenedAt"] is None


@pytest.mark.asyncio
async def test_self_actions_no_journey(monkeypatch):
    async def fake_latest(referrer_hash):
        return None

    monkeypatch.setattr(rs, "_latest_self_referral", fake_latest)

    assert await rs._self_actions_for("hash-1") == []


@pytest.mark.asyncio
async def test_self_actions_account_not_opened(monkeypatch):
    async def fake_latest(referrer_hash):
        return {
            "referralTrackId": "track-1",
            "account_opened_at": None,
        }

    monkeypatch.setattr(rs, "_latest_self_referral", fake_latest)

    result = await rs._self_actions_for("hash-1")

    assert result[0]["action"] == "COMPLETE_YOUR_APPLICATION"


@pytest.mark.asyncio
async def test_get_cached_recommendations_no_row(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    assert await rs.get_cached_recommendations("hash-1") is None


@pytest.mark.asyncio
async def test_get_cached_recommendations_expired(monkeypatch):
    old_time = datetime.now(timezone.utc) - timedelta(days=2)
    conn = FakeConn(row={"items": {"x": 1}, "generated_at": old_time, "ttl_seconds": 1})
    patch_db(monkeypatch, conn)

    assert await rs.get_cached_recommendations("hash-1") is None


@pytest.mark.asyncio
async def test_get_cached_recommendations_valid(monkeypatch):
    fresh_time = datetime.now(timezone.utc)
    cached = {"primaryAction": {"action": "SEND_INVITE"}}
    conn = FakeConn(row={"items": cached, "generated_at": fresh_time, "ttl_seconds": 86400})
    patch_db(monkeypatch, conn)

    assert await rs.get_cached_recommendations("hash-1") == cached


@pytest.mark.asyncio
async def test_upsert_recommendations_cache(monkeypatch):
    conn = FakeConn()
    patch_db(monkeypatch, conn)

    await rs.upsert_recommendations_cache(
        "hash-1",
        {"primaryAction": {"action": "SEND_INVITE"}},
        ttl_seconds=60,
    )

    assert len(conn.calls) == 1
    assert conn.calls[0][0] == "execute"
    assert conn.calls[0][2][0] == "hash-1"
    assert conn.calls[0][2][2] == 60


@pytest.mark.asyncio
async def test_recommend_for_referrer_returns_cached_result(monkeypatch):
    cached = {
        "referrerHash": "hash-1",
        "primaryAction": {"action": "SEND_INVITE"},
        "secondaryActions": [],
        "opsActions": [],
    }

    async def fake_cache(referrer_hash):
        return cached

    monkeypatch.setattr(rs, "get_cached_recommendations", fake_cache)

    result = await rs.recommend_for_referrer("hash-1", segment="Premier")

    assert result == cached


@pytest.mark.asyncio
async def test_recommend_for_referrer_builds_ranked_actions(monkeypatch):
    async def fake_cache(referrer_hash):
        return None

    async def fake_mission(referrer_hash):
        return {
            "action": "COMPLETE_MISSION",
            "audience": "REFERRER",
            "priorityScore": 0.8,
        }

    async def fake_invite(referrer_hash):
        return {
            "action": "SEND_INVITE",
            "audience": "REFERRER",
            "priorityScore": 0.4,
        }

    async def fake_self(referrer_hash):
        return []

    async def fake_dangling(referrer_hash):
        return None

    saved = []

    async def fake_upsert(referrer_hash, items, ttl_seconds=86400):
        saved.append((referrer_hash, items, ttl_seconds))

    monkeypatch.setattr(rs, "get_cached_recommendations", fake_cache)
    monkeypatch.setattr(rs, "_closest_mission_for", fake_mission)
    monkeypatch.setattr(rs, "_invite_nudge_for", fake_invite)
    monkeypatch.setattr(rs, "_self_actions_for", fake_self)
    monkeypatch.setattr(rs, "_dangling_rewards", fake_dangling)
    monkeypatch.setattr(rs, "upsert_recommendations_cache", fake_upsert)

    result = await rs.recommend_for_referrer("hash-1", segment="Premier", top_k=2)

    assert result["primaryAction"]["action"] == "COMPLETE_MISSION"
    assert result["secondaryActions"][0]["action"] == "SEND_INVITE"
    assert saved[0][0] == "hash-1"


@pytest.mark.asyncio
async def test_recommend_for_referrer_filters_self_actions_for_referrer(monkeypatch):
    async def fake_mission(referrer_hash):
        return None

    async def fake_invite(referrer_hash):
        return None

    async def fake_dangling(referrer_hash):
        return None

    async def fake_self(referrer_hash):
        return [
            {
                "action": "COMPLETE_YOUR_APPLICATION",
                "audience": "SELF",
                "priorityScore": 0.9,
            }
        ]

    monkeypatch.setattr(rs, "_closest_mission_for", fake_mission)
    monkeypatch.setattr(rs, "_invite_nudge_for", fake_invite)
    monkeypatch.setattr(rs, "_dangling_rewards", fake_dangling)
    monkeypatch.setattr(rs, "_self_actions_for", fake_self)

    result = await rs.recommend_for_referrer(
        "hash-1",
        segment="Premier",
        subject_role="REFERRER",
        use_cache=False,
    )

    assert result["primaryAction"] is None


@pytest.mark.asyncio
async def test_recommend_for_self_allows_self_actions(monkeypatch):
    async def fake_mission(referrer_hash):
        return None

    async def fake_invite(referrer_hash):
        return None

    async def fake_dangling(referrer_hash):
        return None

    async def fake_self(referrer_hash):
        return [
            {
                "action": "COMPLETE_YOUR_APPLICATION",
                "audience": "SELF",
                "priorityScore": 0.9,
            }
        ]

    monkeypatch.setattr(rs, "_closest_mission_for", fake_mission)
    monkeypatch.setattr(rs, "_invite_nudge_for", fake_invite)
    monkeypatch.setattr(rs, "_dangling_rewards", fake_dangling)
    monkeypatch.setattr(rs, "_self_actions_for", fake_self)

    result = await rs.recommend_for_referrer(
        "hash-1",
        segment="Premier",
        subject_role="SELF",
        use_cache=False,
    )

    assert result["primaryAction"]["action"] == "COMPLETE_YOUR_APPLICATION"


@pytest.mark.asyncio
async def test_recommend_for_referrer_separates_ops_actions(monkeypatch):
    async def fake_mission(referrer_hash):
        return None

    async def fake_invite(referrer_hash):
        return {
            "action": "SEND_INVITE",
            "audience": "REFERRER",
            "priorityScore": 0.4,
        }

    async def fake_dangling(referrer_hash):
        return {
            "action": "APPLY_REWARD",
            "audience": "OPS",
            "priorityScore": 0.8,
        }

    async def fake_self(referrer_hash):
        return []

    monkeypatch.setattr(rs, "_closest_mission_for", fake_mission)
    monkeypatch.setattr(rs, "_invite_nudge_for", fake_invite)
    monkeypatch.setattr(rs, "_dangling_rewards", fake_dangling)
    monkeypatch.setattr(rs, "_self_actions_for", fake_self)

    result = await rs.recommend_for_referrer(
        "hash-1",
        segment="Premier",
        use_cache=False,
    )

    assert result["primaryAction"]["action"] == "APPLY_REWARD"
    assert result["secondaryActions"][0]["action"] == "SEND_INVITE"
    assert result["opsActions"][0]["action"] == "APPLY_REWARD"


@pytest.mark.asyncio
async def test_compute_campaign_insights_stub():
    result = await rs.compute_campaign_insights("CAMP1", segment="Gold", tenant="FNB")

    assert result["campaignCode"] == "CAMP1"
    assert result["metrics"]["scanned30d"] == 0