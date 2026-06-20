from __future__ import annotations

from contextlib import asynccontextmanager

import pytest

import services.campaign_policy_service as svc


class FakeConn:
    def __init__(self, row=None):
        self.row = row
        self.calls = []

    async def fetchrow(self, query, *params):
        self.calls.append(("fetchrow", query, params))
        return self.row


def patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(svc, "db_connection", fake_db_connection)


@pytest.fixture(autouse=True)
def clear_cache():
    svc._cache.clear()
    svc._cache_expiry.clear()
    yield
    svc._cache.clear()
    svc._cache_expiry.clear()


def test_norm():
    assert svc._norm(None) is None
    assert svc._norm("") is None
    assert svc._norm(" fnb ") == "FNB"


def test_key():
    assert svc._key("fnb", "camp1") == "FNB::CAMP1"
    assert svc._key(None, None) == "::"


def test_json_load_or():
    assert svc._json_load_or([], None) == []
    assert svc._json_load_or([], "") == []
    assert svc._json_load_or([], "bad-json") == []
    assert svc._json_load_or([], '[{"x": 1}]') == [{"x": 1}]


def test_row_get_dict_tuple_and_default():
    row = {"a": 1}
    assert svc._row_get(row, "a") == 1
    assert svc._row_get(row, "b", "default") == "default"

    tuple_row = ("x", "y")
    assert svc._row_get(tuple_row, 1) == "y"
    assert svc._row_get(tuple_row, 9, "missing") == "missing"


def test_row_to_policy_dict():
    row = {
        "rolling_window_days": 30,
        "rules_text": '[{"rule": "x"}]',
        "product_windows_text": '{"gold": 30}',
        "reward_amounts_text": '{"gold": 100}',
        "product_rules_text": '{"gold": {"allowed": true}}',
        "version": 2,
    }

    result = svc._row_to_policy(row)

    assert result["rollingWindowDays"] == 30
    assert result["rules"] == [{"rule": "x"}]
    assert result["productWindows"] == {"gold": 30}
    assert result["rewardAmounts"] == {"gold": 100}
    assert result["productRules"] == {"gold": {"allowed": True}}
    assert result["version"] == 2


def test_row_to_policy_tuple_and_defaults():
    row = (
        None,
        "bad-json",
        None,
        None,
        None,
        None,
    )

    result = svc._row_to_policy(row)

    assert result["rollingWindowDays"] == svc.DEFAULT_ROLLING_WINDOW_DAYS
    assert result["rules"] == svc.DEFAULT_RULES
    assert result["productWindows"] == {}
    assert result["rewardAmounts"] == {}
    assert result["productRules"] == {}
    assert result["version"] == 1


def test_default_policy():
    result = svc._default_policy()

    assert result["enabled"] == svc.ENABLE_COOLDOWNS
    assert result["dryRun"] == svc.DRY_RUN
    assert result["rollingWindowDays"] == svc.DEFAULT_ROLLING_WINDOW_DAYS
    assert result["rules"] == svc.DEFAULT_RULES
    assert result["version"] == 1


@pytest.mark.asyncio
async def test_get_effective_policy_without_campaign_uses_default():
    result = await svc.get_effective_policy(tenant="FNB", campaign_code=None)

    assert result == svc._default_policy()


@pytest.mark.asyncio
async def test_get_effective_policy_with_campaign_db_row(monkeypatch):
    conn = FakeConn(
        row={
            "rolling_window_days": 45,
            "rules_text": '[{"type": "cooldown"}]',
            "product_windows_text": '{"gold": 45}',
            "reward_amounts_text": '{"gold": 150}',
            "product_rules_text": '{"gold": {"allowed": false}}',
            "version": 3,
        }
    )
    patch_db(monkeypatch, conn)

    result = await svc.get_effective_policy(
        tenant="fnb",
        campaign_code="camp001",
    )

    assert result["rollingWindowDays"] == 45
    assert result["rules"] == [{"type": "cooldown"}]
    assert result["productWindows"] == {"gold": 45}
    assert result["rewardAmounts"] == {"gold": 150}
    assert result["productRules"] == {"gold": {"allowed": False}}
    assert result["version"] == 3

    assert conn.calls[0][2] == ("CAMP001", "FNB")


@pytest.mark.asyncio
async def test_get_effective_policy_with_campaign_no_row_uses_default(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    result = await svc.get_effective_policy(
        tenant="FNB",
        campaign_code="MISSING",
    )

    assert result == svc._default_policy()


@pytest.mark.asyncio
async def test_get_effective_policy_cache_hit(monkeypatch):
    conn = FakeConn(
        row={
            "rolling_window_days": 30,
            "rules_text": "[]",
            "product_windows_text": "{}",
            "reward_amounts_text": "{}",
            "product_rules_text": "{}",
            "version": 1,
        }
    )
    patch_db(monkeypatch, conn)

    first = await svc.get_effective_policy(
        tenant="FNB",
        campaign_code="CAMP001",
    )
    second = await svc.get_effective_policy(
        tenant="FNB",
        campaign_code="CAMP001",
    )

    assert first == second
    assert len(conn.calls) == 1


@pytest.mark.asyncio
async def test_get_effective_policy_cache_expired(monkeypatch):
    current = [1000.0]

    def fake_now():
        return current[0]

    monkeypatch.setattr(svc, "_now", fake_now)
    monkeypatch.setattr(svc, "POLICY_CACHE_TTL_SEC", 10)

    conn = FakeConn(
        row={
            "rolling_window_days": 30,
            "rules_text": "[]",
            "product_windows_text": "{}",
            "reward_amounts_text": "{}",
            "product_rules_text": "{}",
            "version": 1,
        }
    )
    patch_db(monkeypatch, conn)

    await svc.get_effective_policy(
        tenant="FNB",
        campaign_code="CAMP001",
    )

    current[0] = 2000.0  # force expiry

    await svc.get_effective_policy(
        tenant="FNB",
        campaign_code="CAMP001",
    )

    assert len(conn.calls) == 2