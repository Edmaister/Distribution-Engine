import pytest

from services import provider_sla_service as mod


class FakeConnection:
    def __init__(self):
        self.fetchrow_result = None
        self.fetch_results = []
        self.execute_calls = []
        self.fetchrow_calls = []
        self.fetch_calls = []

    async def execute(self, sql, *args):
        self.execute_calls.append((sql, args))
        return "OK"

    async def fetchrow(self, sql, *args):
        self.fetchrow_calls.append((sql, args))
        return self.fetchrow_result

    async def fetch(self, sql, *args):
        self.fetch_calls.append((sql, args))
        return self.fetch_results


class FakeDbConnection:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_record_provider_success(monkeypatch):
    conn = FakeConnection()

    monkeypatch.setattr(
        mod,
        "db_connection",
        lambda: FakeDbConnection(conn),
    )

    await mod.record_provider_success(
        provider_key="CASH_PROVIDER",
        latency_ms=120,
    )

    assert len(conn.execute_calls) == 1

    _, args = conn.execute_calls[0]

    assert args[0] == "CASH_PROVIDER"
    assert args[1] == 120


@pytest.mark.asyncio
async def test_record_provider_failure(monkeypatch):
    conn = FakeConnection()

    monkeypatch.setattr(
        mod,
        "db_connection",
        lambda: FakeDbConnection(conn),
    )

    await mod.record_provider_failure(
        provider_key="CASH_PROVIDER",
        latency_ms=500,
    )

    assert len(conn.execute_calls) == 1

    _, args = conn.execute_calls[0]

    assert args[0] == "CASH_PROVIDER"
    assert args[1] == 500


@pytest.mark.asyncio
async def test_record_provider_retry(monkeypatch):
    conn = FakeConnection()

    monkeypatch.setattr(
        mod,
        "db_connection",
        lambda: FakeDbConnection(conn),
    )

    await mod.record_provider_retry(
        provider_key="CASH_PROVIDER",
    )

    assert len(conn.execute_calls) == 1

    _, args = conn.execute_calls[0]

    assert args[0] == "CASH_PROVIDER"


@pytest.mark.asyncio
async def test_get_provider_sla_metrics(monkeypatch):
    conn = FakeConnection()

    conn.fetchrow_result = {
        "provider_key": "CASH_PROVIDER",
        "success_count": 100,
    }

    monkeypatch.setattr(
        mod,
        "db_connection",
        lambda: FakeDbConnection(conn),
    )

    result = await mod.get_provider_sla_metrics(
        provider_key="CASH_PROVIDER",
    )

    assert result["provider_key"] == "CASH_PROVIDER"
    assert result["success_count"] == 100


@pytest.mark.asyncio
async def test_get_provider_sla_metrics_not_found(monkeypatch):
    conn = FakeConnection()

    conn.fetchrow_result = None

    monkeypatch.setattr(
        mod,
        "db_connection",
        lambda: FakeDbConnection(conn),
    )

    result = await mod.get_provider_sla_metrics(
        provider_key="UNKNOWN",
    )

    assert result is None


@pytest.mark.asyncio
async def test_list_provider_sla_metrics(monkeypatch):
    conn = FakeConnection()

    conn.fetch_results = [
        {
            "provider_key": "CASH_PROVIDER",
            "success_count": 100,
        },
        {
            "provider_key": "VOUCHER_PROVIDER",
            "success_count": 95,
        },
    ]

    monkeypatch.setattr(
        mod,
        "db_connection",
        lambda: FakeDbConnection(conn),
    )

    result = await mod.list_provider_sla_metrics(
        limit=100,
    )

    assert len(result) == 2
    assert result[0]["provider_key"] == "CASH_PROVIDER"
    assert result[1]["provider_key"] == "VOUCHER_PROVIDER"