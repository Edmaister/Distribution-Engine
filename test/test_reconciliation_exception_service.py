import pytest

from services import reconciliation_exception_service as mod
from services.reconciliation_exception_status import (
    ReconciliationExceptionStatus,
)


class FakeConnection:
    def __init__(self):
        self.fetchrow_result = None
        self.fetch_results = []
        self.fetchrow_calls = []
        self.fetch_calls = []

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
async def test_create_exception(monkeypatch):
    conn = FakeConnection()
    conn.fetchrow_result = {
        "exception_id": "exception-123",
        "run_id": "run-123",
        "provider_reference": "REF-1",
        "exception_type": "MISSING",
        "status": ReconciliationExceptionStatus.OPEN.value,
    }

    monkeypatch.setattr(mod, "db_connection", lambda: FakeDbConnection(conn))

    result = await mod.create_exception(
        run_id="run-123",
        provider_reference="REF-1",
        exception_type="MISSING",
    )

    assert result["exception_id"] == "exception-123"
    assert result["status"] == ReconciliationExceptionStatus.OPEN.value
    assert conn.fetchrow_calls


@pytest.mark.asyncio
async def test_assign_exception(monkeypatch):
    conn = FakeConnection()
    conn.fetchrow_result = {
        "exception_id": "exception-123",
        "assigned_to": "finance.user",
        "status": ReconciliationExceptionStatus.ASSIGNED.value,
    }

    monkeypatch.setattr(mod, "db_connection", lambda: FakeDbConnection(conn))

    result = await mod.assign_exception(
        exception_id="exception-123",
        assigned_to="finance.user",
    )

    assert result["assigned_to"] == "finance.user"
    assert result["status"] == ReconciliationExceptionStatus.ASSIGNED.value


@pytest.mark.asyncio
async def test_assign_exception_returns_none_when_not_found(monkeypatch):
    conn = FakeConnection()
    conn.fetchrow_result = None

    monkeypatch.setattr(mod, "db_connection", lambda: FakeDbConnection(conn))

    result = await mod.assign_exception(
        exception_id="missing",
        assigned_to="finance.user",
    )

    assert result is None


@pytest.mark.asyncio
async def test_resolve_exception(monkeypatch):
    conn = FakeConnection()
    conn.fetchrow_result = {
        "exception_id": "exception-123",
        "resolution_notes": "Resolved after provider confirmation",
        "status": ReconciliationExceptionStatus.RESOLVED.value,
    }

    monkeypatch.setattr(mod, "db_connection", lambda: FakeDbConnection(conn))

    result = await mod.resolve_exception(
        exception_id="exception-123",
        resolution_notes="Resolved after provider confirmation",
    )

    assert result["status"] == ReconciliationExceptionStatus.RESOLVED.value
    assert result["resolution_notes"] == "Resolved after provider confirmation"


@pytest.mark.asyncio
async def test_resolve_exception_returns_none_when_not_found(monkeypatch):
    conn = FakeConnection()
    conn.fetchrow_result = None

    monkeypatch.setattr(mod, "db_connection", lambda: FakeDbConnection(conn))

    result = await mod.resolve_exception(
        exception_id="missing",
        resolution_notes="Not found",
    )

    assert result is None


@pytest.mark.asyncio
async def test_reopen_exception(monkeypatch):
    conn = FakeConnection()
    conn.fetchrow_result = {
        "exception_id": "exception-123",
        "status": ReconciliationExceptionStatus.REOPENED.value,
        "resolved_at": None,
    }

    monkeypatch.setattr(mod, "db_connection", lambda: FakeDbConnection(conn))

    result = await mod.reopen_exception(
        exception_id="exception-123",
    )

    assert result["status"] == ReconciliationExceptionStatus.REOPENED.value
    assert result["resolved_at"] is None


@pytest.mark.asyncio
async def test_reopen_exception_returns_none_when_not_found(monkeypatch):
    conn = FakeConnection()
    conn.fetchrow_result = None

    monkeypatch.setattr(mod, "db_connection", lambda: FakeDbConnection(conn))

    result = await mod.reopen_exception(
        exception_id="missing",
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_exception(monkeypatch):
    conn = FakeConnection()
    conn.fetchrow_result = {
        "exception_id": "exception-123",
        "status": ReconciliationExceptionStatus.OPEN.value,
    }

    monkeypatch.setattr(mod, "db_connection", lambda: FakeDbConnection(conn))

    result = await mod.get_exception(
        exception_id="exception-123",
    )

    assert result["exception_id"] == "exception-123"


@pytest.mark.asyncio
async def test_get_exception_returns_none_when_not_found(monkeypatch):
    conn = FakeConnection()
    conn.fetchrow_result = None

    monkeypatch.setattr(mod, "db_connection", lambda: FakeDbConnection(conn))

    result = await mod.get_exception(
        exception_id="missing",
    )

    assert result is None


@pytest.mark.asyncio
async def test_list_exceptions_with_filters(monkeypatch):
    conn = FakeConnection()
    conn.fetch_results = [
        {
            "exception_id": "exception-123",
            "status": ReconciliationExceptionStatus.ASSIGNED.value,
            "assigned_to": "finance.user",
        }
    ]

    monkeypatch.setattr(mod, "db_connection", lambda: FakeDbConnection(conn))

    result = await mod.list_exceptions(
        status=ReconciliationExceptionStatus.ASSIGNED.value,
        assigned_to="finance.user",
        limit=10,
    )

    assert len(result) == 1
    assert result[0]["exception_id"] == "exception-123"
    assert conn.fetch_calls


@pytest.mark.asyncio
async def test_list_exceptions_without_filters(monkeypatch):
    conn = FakeConnection()
    conn.fetch_results = []

    monkeypatch.setattr(mod, "db_connection", lambda: FakeDbConnection(conn))

    result = await mod.list_exceptions()

    assert result == []
    assert conn.fetch_calls