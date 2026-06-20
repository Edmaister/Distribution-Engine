from decimal import Decimal

import pytest

import services.reward_policy_service as svc


class FakeAsyncConnection:
    def __init__(self, fetchrow_value=None, fetch_value=None):
        self.fetchrow_value = fetchrow_value
        self.fetch_value = fetch_value or []
        self.executed = []

    async def fetchrow(self, sql, *params):
        self.executed.append(("fetchrow", sql, params))
        return self.fetchrow_value

    async def fetch(self, sql, *params):
        self.executed.append(("fetch", sql, params))
        return self.fetch_value


class FakeAsyncConnectionContext:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


def patch_async_db(monkeypatch, conn):
    def fake_get_async_connection():
        return FakeAsyncConnectionContext(conn)

    monkeypatch.setattr(svc, "get_async_connection", fake_get_async_connection)


def sample_row(policy_id=1, product="Transactional", sub_product="DDA13", active=True):
    return (
        policy_id,
        product,
        sub_product,
        "CASH",
        Decimal("100.00"),
        Decimal("50.00"),
        True,
        active,
        "created",
        "updated",
    )


def test_row_to_policy():
    policy = svc._row_to_policy(sample_row())

    assert policy["id"] == 1
    assert policy["product"] == "Transactional"
    assert policy["reward_type"] == "CASH"
    assert policy["referrer_reward_amount"] == Decimal("100.00")
    assert policy["referee_reward_amount"] == Decimal("50.00")
    assert policy["allow_referee_reward"] is True
    assert policy["is_active"] is True


@pytest.mark.asyncio
async def test_get_reward_policy_requires_product():
    with pytest.raises(ValueError, match="product is required"):
        await svc.get_reward_policy("")


@pytest.mark.asyncio
async def test_get_reward_policy_found(monkeypatch):
    conn = FakeAsyncConnection(fetchrow_value=sample_row())
    patch_async_db(monkeypatch, conn)

    result = await svc.get_reward_policy("Transactional", "DDA13")

    assert result is not None
    assert result["product"] == "Transactional"
    assert result["sub_product"] == "DDA13"


@pytest.mark.asyncio
async def test_get_reward_policy_not_found(monkeypatch):
    conn = FakeAsyncConnection(fetchrow_value=None)
    patch_async_db(monkeypatch, conn)

    result = await svc.get_reward_policy("Transactional", "DDA13")

    assert result is None


@pytest.mark.asyncio
async def test_list_reward_policies(monkeypatch):
    rows = [
        sample_row(policy_id=1),
        sample_row(policy_id=2, sub_product=None),
    ]
    conn = FakeAsyncConnection(fetch_value=rows)
    patch_async_db(monkeypatch, conn)

    result = await svc.list_reward_policies(product="Transactional")

    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["id"] == 2


@pytest.mark.asyncio
async def test_list_reward_policies_include_inactive(monkeypatch):
    rows = [sample_row(policy_id=3, active=False)]
    conn = FakeAsyncConnection(fetch_value=rows)
    patch_async_db(monkeypatch, conn)

    result = await svc.list_reward_policies(include_inactive=True)

    assert len(result) == 1
    assert result[0]["is_active"] is False


@pytest.mark.asyncio
async def test_get_reward_policy_by_id_found(monkeypatch):
    conn = FakeAsyncConnection(fetchrow_value=sample_row(policy_id=99))
    patch_async_db(monkeypatch, conn)

    result = await svc.get_reward_policy_by_id(99)

    assert result is not None
    assert result["id"] == 99


@pytest.mark.asyncio
async def test_get_reward_policy_by_id_not_found(monkeypatch):
    conn = FakeAsyncConnection(fetchrow_value=None)
    patch_async_db(monkeypatch, conn)

    result = await svc.get_reward_policy_by_id(999)

    assert result is None


@pytest.mark.asyncio
async def test_has_active_reward_policy_true(monkeypatch):
    async def fake_get_reward_policy(product, sub_product=None):
        return {"id": 1}

    monkeypatch.setattr(svc, "get_reward_policy", fake_get_reward_policy)

    assert await svc.has_active_reward_policy("Transactional", "DDA13") is True


@pytest.mark.asyncio
async def test_has_active_reward_policy_false(monkeypatch):
    async def fake_get_reward_policy(product, sub_product=None):
        return None

    monkeypatch.setattr(svc, "get_reward_policy", fake_get_reward_policy)

    assert await svc.has_active_reward_policy("Transactional", "DDA13") is False