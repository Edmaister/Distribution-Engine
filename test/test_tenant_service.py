import pytest

import services.tenant_service as svc


class FakeAsyncConnection:
    def __init__(self, fetchrow_value=None):
        self.fetchrow_value = fetchrow_value
        self.executed = []

    async def execute(self, sql, *params):
        self.executed.append(("execute", sql, params))

    async def fetchrow(self, sql, *params):
        self.executed.append(("fetchrow", sql, params))
        return self.fetchrow_value


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


@pytest.mark.asyncio
async def test_create_tenant_inserts_or_updates(monkeypatch):
    conn = FakeAsyncConnection()
    patch_async_db(monkeypatch, conn)

    await svc.create_tenant(
        tenant_code="FNB",
        tenant_name="First National Bank",
        industry="Banking",
    )

    action, sql, params = conn.executed[0]

    assert action == "execute"
    assert "INSERT INTO tenants" in sql
    assert "ON CONFLICT" in sql
    assert params == ("FNB", "First National Bank", "Banking")


@pytest.mark.asyncio
async def test_get_tenant_returns_row(monkeypatch):
    expected = {
        "tenant_code": "FNB",
        "tenant_name": "First National Bank",
        "industry": "Banking",
        "currency": "ZAR",
        "locale": "en-ZA",
        "is_active": True,
    }

    conn = FakeAsyncConnection(fetchrow_value=expected)
    patch_async_db(monkeypatch, conn)

    result = await svc.get_tenant("FNB")

    action, sql, params = conn.executed[0]

    assert action == "fetchrow"
    assert "SELECT tenant_code" in sql
    assert "FROM tenants" in sql
    assert params == ("FNB",)
    assert result == expected


@pytest.mark.asyncio
async def test_get_tenant_returns_none_when_missing(monkeypatch):
    conn = FakeAsyncConnection(fetchrow_value=None)
    patch_async_db(monkeypatch, conn)

    result = await svc.get_tenant("UNKNOWN")

    assert result is None