from datetime import datetime, timezone

import pytest

import services.fulfilment_provider_health_service as service


class FakeAsyncDbCursor:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows or []
        self.executed = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def fetchrow(self, query, *args):
        self.executed.append((query, args))
        return self.row

    async def fetch(self, query, *args):
        self.executed.append((query, args))
        return self.rows


def patch_db(monkeypatch, cursor):
    def fake_async_db_cursor():
        return cursor

    monkeypatch.setattr(service, "async_db_cursor", fake_async_db_cursor)


@pytest.mark.asyncio
async def test_get_provider_health_without_tenant(monkeypatch):
    cursor = FakeAsyncDbCursor(
        row={
            "total_count": 10,
            "success_count": 8,
            "failure_count": 2,
            "retryable_failure_count": 1,
            "dlq_count": 1,
            "last_success_at": datetime(2026, 5, 29, 12, 0, tzinfo=timezone.utc),
            "last_failure_at": datetime(2026, 5, 29, 13, 0, tzinfo=timezone.utc),
        }
    )
    patch_db(monkeypatch, cursor)

    monkeypatch.setattr(
        service,
        "get_circuit_snapshot",
        lambda provider_key: {
            "provider_key": provider_key,
            "state": "CLOSED",
        },
    )

    result = await service.get_provider_health(
        provider_key="CASH_PROVIDER",
    )

    assert result["provider_key"] == "CASH_PROVIDER"
    assert result["tenant_code"] is None
    assert result["total_count"] == 10
    assert result["success_count"] == 8
    assert result["failure_count"] == 2
    assert result["retryable_failure_count"] == 1
    assert result["dlq_count"] == 1
    assert result["success_rate"] == 80.0
    assert result["failure_rate"] == 20.0
    assert result["last_success_at"] == "2026-05-29T12:00:00+00:00"
    assert result["last_failure_at"] == "2026-05-29T13:00:00+00:00"
    assert result["circuit"]["state"] == "CLOSED"

    query, args = cursor.executed[0]
    assert "WHERE fulfilment_provider = $1" in query
    assert args == ("CASH_PROVIDER",)


@pytest.mark.asyncio
async def test_get_provider_health_with_tenant(monkeypatch):
    cursor = FakeAsyncDbCursor(
        row={
            "total_count": 4,
            "success_count": 3,
            "failure_count": 1,
            "retryable_failure_count": 1,
            "dlq_count": 0,
            "last_success_at": None,
            "last_failure_at": None,
        }
    )
    patch_db(monkeypatch, cursor)

    monkeypatch.setattr(
        service,
        "get_circuit_snapshot",
        lambda provider_key: {
            "provider_key": provider_key,
            "state": "OPEN",
        },
    )

    result = await service.get_provider_health(
        provider_key="VOUCHER_PROVIDER",
        tenant_code="FNB",
    )

    assert result["tenant_code"] == "FNB"
    assert result["success_rate"] == 75.0
    assert result["failure_rate"] == 25.0
    assert result["last_success_at"] is None
    assert result["last_failure_at"] is None
    assert result["circuit"]["state"] == "OPEN"

    query, args = cursor.executed[0]
    assert "fulfilment_provider = $1" in query
    assert "tenant_code = $2" in query
    assert args == ("VOUCHER_PROVIDER", "FNB")


@pytest.mark.asyncio
async def test_get_provider_health_handles_zero_total(monkeypatch):
    cursor = FakeAsyncDbCursor(
        row={
            "total_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "retryable_failure_count": 0,
            "dlq_count": 0,
            "last_success_at": None,
            "last_failure_at": None,
        }
    )
    patch_db(monkeypatch, cursor)

    monkeypatch.setattr(
        service,
        "get_circuit_snapshot",
        lambda provider_key: {
            "provider_key": provider_key,
            "state": "CLOSED",
        },
    )

    result = await service.get_provider_health(
        provider_key="CASH_PROVIDER",
    )

    assert result["success_rate"] == 0.0
    assert result["failure_rate"] == 0.0


@pytest.mark.asyncio
async def test_list_provider_health_without_tenant(monkeypatch):
    list_cursor = FakeAsyncDbCursor(
        rows=[
            {"fulfilment_provider": "CASH_PROVIDER"},
            {"fulfilment_provider": "VOUCHER_PROVIDER"},
        ]
    )

    health_responses = {
        "CASH_PROVIDER": {"provider_key": "CASH_PROVIDER"},
        "VOUCHER_PROVIDER": {"provider_key": "VOUCHER_PROVIDER"},
    }

    patch_db(monkeypatch, list_cursor)

    async def fake_get_provider_health(*, provider_key, tenant_code=None):
        assert tenant_code is None
        return health_responses[provider_key]

    monkeypatch.setattr(
        service,
        "get_provider_health",
        fake_get_provider_health,
    )

    result = await service.list_provider_health()

    assert result == [
        {"provider_key": "CASH_PROVIDER"},
        {"provider_key": "VOUCHER_PROVIDER"},
    ]

    query, args = list_cursor.executed[0]
    assert "SELECT DISTINCT fulfilment_provider" in query
    assert args == ()


@pytest.mark.asyncio
async def test_list_provider_health_with_tenant(monkeypatch):
    list_cursor = FakeAsyncDbCursor(
        rows=[
            {"fulfilment_provider": "CASH_PROVIDER"},
        ]
    )

    patch_db(monkeypatch, list_cursor)

    async def fake_get_provider_health(*, provider_key, tenant_code=None):
        assert provider_key == "CASH_PROVIDER"
        assert tenant_code == "FNB"
        return {
            "provider_key": provider_key,
            "tenant_code": tenant_code,
        }

    monkeypatch.setattr(
        service,
        "get_provider_health",
        fake_get_provider_health,
    )

    result = await service.list_provider_health(
        tenant_code="FNB",
    )

    assert result == [
        {
            "provider_key": "CASH_PROVIDER",
            "tenant_code": "FNB",
        }
    ]

    query, args = list_cursor.executed[0]
    assert "WHERE tenant_code = $1" in query
    assert args == ("FNB",)