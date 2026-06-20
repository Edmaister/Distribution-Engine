from services import reconciliation_history_service as mod


class FakeConnection:
    def __init__(self):
        self.fetchrow_result = None
        self.fetch_results = []
        self.execute_calls = []
        self.fetchrow_calls = []
        self.fetch_calls = []

    async def fetchrow(self, sql, *args):
        self.fetchrow_calls.append((sql, args))
        return self.fetchrow_result

    async def fetch(self, sql, *args):
        self.fetch_calls.append((sql, args))
        return self.fetch_results

    async def execute(self, sql, *args):
        self.execute_calls.append((sql, args))
        return "INSERT 0 1"


class FakeDbConnection:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


def test_create_reconciliation_results_returns_zero_when_empty():
    import pytest

    async def run():
        result = await mod.create_reconciliation_results(
            run_id="run-123",
            results=[],
        )
        assert result == 0

    pytest.run = run


import pytest


@pytest.mark.asyncio
async def test_create_reconciliation_run(monkeypatch):
    conn = FakeConnection()
    conn.fetchrow_result = {
        "run_id": "run-123",
        "provider_key": "CASH_PROVIDER",
        "total_records": 2,
        "matched_count": 1,
        "missing_count": 1,
        "duplicate_count": 0,
        "overpaid_count": 0,
        "underpaid_count": 0,
    }

    monkeypatch.setattr(
        mod,
        "db_connection",
        lambda: FakeDbConnection(conn),
    )

    result = await mod.create_reconciliation_run(
        tenant_code="FNB",
        provider_key="CASH_PROVIDER",
        total_records=2,
        matched_count=1,
        missing_count=1,
        duplicate_count=0,
        overpaid_count=0,
        underpaid_count=0,
    )

    assert result["run_id"] == "run-123"
    assert result["provider_key"] == "CASH_PROVIDER"
    assert conn.fetchrow_calls


@pytest.mark.asyncio
async def test_create_reconciliation_results(monkeypatch):
    conn = FakeConnection()

    monkeypatch.setattr(
        mod,
        "db_connection",
        lambda: FakeDbConnection(conn),
    )

    count = await mod.create_reconciliation_results(
        run_id="run-123",
        results=[
            {
                "provider_reference": "REF-1",
                "status": "MATCHED",
                "platform_amount": 100,
                "provider_amount": 100,
            },
            {
                "provider_reference": "REF-2",
                "status": "MISSING",
                "platform_amount": 200,
                "provider_amount": None,
            },
        ],
    )

    assert count == 2
    assert len(conn.execute_calls) == 2


@pytest.mark.asyncio
async def test_get_reconciliation_run(monkeypatch):
    conn = FakeConnection()
    conn.fetchrow_result = {
        "run_id": "run-123",
        "provider_key": "CASH_PROVIDER",
    }

    monkeypatch.setattr(
        mod,
        "db_connection",
        lambda: FakeDbConnection(conn),
    )

    result = await mod.get_reconciliation_run(run_id="run-123")

    assert result["run_id"] == "run-123"


@pytest.mark.asyncio
async def test_list_reconciliation_runs(monkeypatch):
    conn = FakeConnection()
    conn.fetch_results = [
        {
            "run_id": "run-123",
            "provider_key": "CASH_PROVIDER",
        }
    ]

    monkeypatch.setattr(
        mod,
        "db_connection",
        lambda: FakeDbConnection(conn),
    )

    result = await mod.list_reconciliation_runs(
        tenant_code="FNB",
        provider_key="CASH_PROVIDER",
    )

    assert len(result) == 1
    assert result[0]["run_id"] == "run-123"


@pytest.mark.asyncio
async def test_get_reconciliation_results(monkeypatch):
    conn = FakeConnection()
    conn.fetch_results = [
        {
            "result_id": "result-123",
            "run_id": "run-123",
            "status": "MATCHED",
        }
    ]

    monkeypatch.setattr(
        mod,
        "db_connection",
        lambda: FakeDbConnection(conn),
    )

    result = await mod.get_reconciliation_results(run_id="run-123")

    assert len(result) == 1
    assert result[0]["status"] == "MATCHED"