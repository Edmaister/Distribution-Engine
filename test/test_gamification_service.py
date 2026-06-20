from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

import services.gamification_service as mod


class FakeAsyncConnection:
    def __init__(
        self,
        fetchrow_values=None,
        fetch_values=None,
        fetchval_values=None,
    ):
        self.fetchrow_values = list(fetchrow_values or [])
        self.fetch_values = list(fetch_values or [])
        self.fetchval_values = list(fetchval_values or [])
        self.executed = []

    async def fetchrow(self, query, *params):
        self.executed.append(("fetchrow", query, params))
        return self.fetchrow_values.pop(0) if self.fetchrow_values else None

    async def fetch(self, query, *params):
        self.executed.append(("fetch", query, params))
        return self.fetch_values.pop(0) if self.fetch_values else []

    async def fetchval(self, query, *params):
        self.executed.append(("fetchval", query, params))
        return self.fetchval_values.pop(0) if self.fetchval_values else None

    async def execute(self, query, *params):
        self.executed.append(("execute", query, params))
        return "OK"


class FakeAsyncConnectionContext:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


def patch_async_db(monkeypatch, conn):
    monkeypatch.setattr(
        mod,
        "get_async_connection",
        lambda: FakeAsyncConnectionContext(conn),
    )


def test_utcnow_returns_timezone_aware_datetime():
    result = mod._utcnow()

    assert isinstance(result, datetime)
    assert result.tzinfo is not None


@pytest.mark.asyncio
async def test_add_points_with_meta(monkeypatch):
    conn = FakeAsyncConnection(fetchrow_values=[{"id": 123}])
    patch_async_db(monkeypatch, conn)

    publish = MagicMock()
    monkeypatch.setattr(mod, "publish_event", publish)

    result = await mod.add_points("ref-hash", 10, "TEST_REASON", {"a": 1})

    assert result == 123
    assert "INSERT INTO user_points" in conn.executed[0][1]
    assert conn.executed[0][2] == ("ref-hash", 10, "TEST_REASON", '{"a": 1}')
    publish.assert_called_once_with(
        "referral-events",
        {
            "eventType": "POINTS_ADDED",
            "referrerHash": "ref-hash",
            "points": 10,
            "reason": "TEST_REASON",
            "meta": {"a": 1},
        },
    )


@pytest.mark.asyncio
async def test_add_points_without_meta(monkeypatch):
    conn = FakeAsyncConnection(fetchrow_values=[{"id": 1}])
    patch_async_db(monkeypatch, conn)

    publish = MagicMock()
    monkeypatch.setattr(mod, "publish_event", publish)

    result = await mod.add_points("ref-hash", 5, "NO_META")

    assert result == 1
    assert conn.executed[0][2] == ("ref-hash", 5, "NO_META", "{}")
    assert publish.call_args.args[1]["meta"] == {}


@pytest.mark.asyncio
async def test_get_progress_full(monkeypatch):
    earned = datetime(2026, 5, 4, 12, 0, tzinfo=timezone.utc)

    conn = FakeAsyncConnection(
        fetchval_values=[25, 3, 2],
        fetch_values=[
            [
                {
                    "mission_code": "INVITE_5",
                    "title": "Invite 5",
                    "status": "ACTIVE",
                    "progress": 2,
                    "goal": 5,
                },
                {
                    "mission_code": "EARN_3_REWARDS",
                    "title": "Earn 3",
                    "status": "COMPLETED",
                    "progress": 3,
                    "goal": 3,
                },
            ],
            [
                {
                    "badge_code": "FIRST_BADGE",
                    "title": "First Badge",
                    "earned_at": earned,
                },
                {
                    "badge_code": "NULL_DATE",
                    "title": "Null Date",
                    "earned_at": None,
                },
            ],
        ],
    )
    patch_async_db(monkeypatch, conn)

    result = await mod.get_progress("ref-hash")

    assert result["points"] == 25
    assert result["referrals"] == 3
    assert result["rewards"] == 2
    assert result["badges"][0]["earnedAt"] == earned.isoformat()
    assert len(conn.executed) == 5


@pytest.mark.asyncio
async def test_get_progress_handles_none_totals(monkeypatch):
    conn = FakeAsyncConnection(
        fetchval_values=[None, None, None],
        fetch_values=[[], []],
    )
    patch_async_db(monkeypatch, conn)

    result = await mod.get_progress("ref-hash")

    assert result["points"] == 0
    assert result["referrals"] == 0
    assert result["rewards"] == 0
    assert result["missions"] == []
    assert result["badges"] == []


@pytest.mark.asyncio
async def test_ensure_mission_progress(monkeypatch):
    conn = FakeAsyncConnection()
    patch_async_db(monkeypatch, conn)

    await mod.ensure_mission_progress("ref-hash", "INVITE_5")

    assert "INSERT INTO user_mission_progress" in conn.executed[0][1]
    assert conn.executed[0][2] == ("ref-hash", "INVITE_5")


@pytest.mark.asyncio
async def test_increment_mission_default_increment(monkeypatch):
    conn = FakeAsyncConnection()
    patch_async_db(monkeypatch, conn)

    await mod.increment_mission("ref-hash", "INVITE_5")

    assert "UPDATE user_mission_progress" in conn.executed[0][1]
    assert conn.executed[0][2] == (1, "ref-hash", "INVITE_5")


@pytest.mark.asyncio
async def test_increment_mission_custom_increment(monkeypatch):
    conn = FakeAsyncConnection()
    patch_async_db(monkeypatch, conn)

    await mod.increment_mission("ref-hash", "INVITE_5", 3)

    assert conn.executed[0][2] == (3, "ref-hash", "INVITE_5")


@pytest.mark.asyncio
async def test_complete_mission_no_mission_row(monkeypatch):
    conn = FakeAsyncConnection(fetchrow_values=[None])
    patch_async_db(monkeypatch, conn)

    result = await mod.complete_mission_if_goal("ref-hash", "MISSING")

    assert result is None


@pytest.mark.asyncio
async def test_complete_mission_no_progress_row(monkeypatch):
    conn = FakeAsyncConnection(
        fetchrow_values=[
            {"goal": 5, "reward_points": 10},
            None,
        ]
    )
    patch_async_db(monkeypatch, conn)

    result = await mod.complete_mission_if_goal("ref-hash", "INVITE_5")

    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["COMPLETED", "REWARDED"])
async def test_complete_mission_already_done(monkeypatch, status):
    conn = FakeAsyncConnection(
        fetchrow_values=[
            {"goal": 5, "reward_points": 10},
            {"progress": 5, "status": status},
        ]
    )
    patch_async_db(monkeypatch, conn)

    result = await mod.complete_mission_if_goal("ref-hash", "INVITE_5")

    assert result is None


@pytest.mark.asyncio
async def test_complete_mission_progress_below_goal(monkeypatch):
    conn = FakeAsyncConnection(
        fetchrow_values=[
            {"goal": 5, "reward_points": 10},
            {"progress": 4, "status": "ACTIVE"},
        ]
    )
    patch_async_db(monkeypatch, conn)

    result = await mod.complete_mission_if_goal("ref-hash", "INVITE_5")

    assert result is None


@pytest.mark.asyncio
async def test_complete_mission_update_returns_none(monkeypatch):
    conn = FakeAsyncConnection(
        fetchrow_values=[
            {"goal": 5, "reward_points": 10},
            {"progress": 5, "status": "ACTIVE"},
            None,
        ]
    )
    patch_async_db(monkeypatch, conn)

    result = await mod.complete_mission_if_goal("ref-hash", "INVITE_5")

    assert result is None


@pytest.mark.asyncio
async def test_complete_mission_success_with_reward_points(monkeypatch):
    conn = FakeAsyncConnection(
        fetchrow_values=[
            {"goal": 5, "reward_points": 10},
            {"progress": 5, "status": "ACTIVE"},
            {"?column?": 1},
        ]
    )
    patch_async_db(monkeypatch, conn)

    add_points = AsyncMock()
    publish = MagicMock()
    monkeypatch.setattr(mod, "add_points", add_points)
    monkeypatch.setattr(mod, "publish_event", publish)

    result = await mod.complete_mission_if_goal("ref-hash", "INVITE_5")

    assert result == {"missionCode": "INVITE_5", "rewardPoints": 10}
    add_points.assert_awaited_once_with(
        "ref-hash",
        10,
        "MISSION:INVITE_5",
        {"mission": "INVITE_5"},
    )
    publish.assert_called_once()


@pytest.mark.asyncio
async def test_complete_mission_success_without_reward_points(monkeypatch):
    conn = FakeAsyncConnection(
        fetchrow_values=[
            {"goal": 5, "reward_points": 0},
            {"progress": 5, "status": "STARTED"},
            {"?column?": 1},
        ]
    )
    patch_async_db(monkeypatch, conn)

    add_points = AsyncMock()
    publish = MagicMock()
    monkeypatch.setattr(mod, "add_points", add_points)
    monkeypatch.setattr(mod, "publish_event", publish)

    result = await mod.complete_mission_if_goal("ref-hash", "INVITE_5")

    assert result == {"missionCode": "INVITE_5", "rewardPoints": 0}
    add_points.assert_not_awaited()
    publish.assert_called_once()


@pytest.mark.asyncio
async def test_award_badge_created(monkeypatch):
    conn = FakeAsyncConnection(fetchrow_values=[{"?column?": 1}])
    patch_async_db(monkeypatch, conn)

    publish = MagicMock()
    monkeypatch.setattr(mod, "publish_event", publish)

    result = await mod.award_badge("ref-hash", "BADGE_1")

    assert result is True
    publish.assert_called_once()


@pytest.mark.asyncio
async def test_award_badge_not_created(monkeypatch):
    conn = FakeAsyncConnection(fetchrow_values=[None])
    patch_async_db(monkeypatch, conn)

    publish = MagicMock()
    monkeypatch.setattr(mod, "publish_event", publish)

    result = await mod.award_badge("ref-hash", "BADGE_1")

    assert result is False
    publish.assert_not_called()


@pytest.mark.asyncio
async def test_on_referral_created(monkeypatch):
    ensure = AsyncMock()
    increment = AsyncMock()
    complete = AsyncMock()

    monkeypatch.setattr(mod, "ensure_mission_progress", ensure)
    monkeypatch.setattr(mod, "increment_mission", increment)
    monkeypatch.setattr(mod, "complete_mission_if_goal", complete)

    await mod.on_referral_created("ref-hash")

    ensure.assert_awaited_once_with("ref-hash", "INVITE_5")
    increment.assert_awaited_once_with("ref-hash", "INVITE_5", 1)
    complete.assert_awaited_once_with("ref-hash", "INVITE_5")


@pytest.mark.asyncio
async def test_on_reward_applied(monkeypatch):
    add_points = AsyncMock()
    ensure = AsyncMock()
    increment = AsyncMock()
    complete = AsyncMock()

    monkeypatch.setattr(mod, "add_points", add_points)
    monkeypatch.setattr(mod, "ensure_mission_progress", ensure)
    monkeypatch.setattr(mod, "increment_mission", increment)
    monkeypatch.setattr(mod, "complete_mission_if_goal", complete)

    await mod.on_reward_applied("ref-hash", "CASHBACK")

    add_points.assert_awaited_once_with("ref-hash", 5, "REWARD:CASHBACK")
    ensure.assert_awaited_once_with("ref-hash", "EARN_3_REWARDS")
    increment.assert_awaited_once_with("ref-hash", "EARN_3_REWARDS", 1)
    complete.assert_awaited_once_with("ref-hash", "EARN_3_REWARDS")