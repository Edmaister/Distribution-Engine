from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from services.funding.reconciliation import (
    _money,
    get_funding_reconciliation_run,
    list_funding_reconciliation_exceptions,
    list_funding_reconciliation_runs,
    resolve_funding_reconciliation_exception,
    run_funding_reconciliation,
)


class FakeConnection:
    def __init__(
        self,
        *,
        expected_row=None,
        actual_row=None,
        insert_run_row=None,
        insert_exception_row=None,
        fetch_rows=None,
        fetchrow_result=None,
    ):
        self.expected_row = expected_row
        self.actual_row = actual_row
        self.insert_run_row = insert_run_row
        self.insert_exception_row = insert_exception_row
        self.fetch_rows = fetch_rows or []
        self.fetchrow_result = fetchrow_result
        self.fetchrow_calls = 0
        self.fetchrow_queries = []

    async def fetchrow(self, query, *args):
        self.fetchrow_calls += 1
        self.fetchrow_queries.append((query, args))

        if "FROM funding_reservations" in query:
            return self.expected_row

        if "FROM fulfilment_settlement_ledger" in query:
            return self.actual_row

        if "INSERT INTO funding_reconciliation_runs" in query:
            return self.insert_run_row

        if "INSERT INTO funding_reconciliation_exceptions" in query:
            return self.insert_exception_row

        return self.fetchrow_result

    async def fetch(self, query, *args):
        return self.fetch_rows


class FakeDbConnection:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return None


def patch_db(monkeypatch, conn):
    monkeypatch.setattr(
        "services.funding.reconciliation.db_connection",
        lambda: FakeDbConnection(conn),
    )


def test_money_handles_none():
    assert _money(None) == Decimal("0.00")


def test_money_rounds_to_two_decimals():
    assert _money("10.126") == Decimal("10.13")


@pytest.mark.asyncio
async def test_run_funding_reconciliation_matched(monkeypatch):
    run_id = uuid4()
    conn = FakeConnection(
        expected_row={"expected_amount": Decimal("1000000.00")},
        actual_row={"actual_amount": Decimal("1000000.00")},
        insert_run_row={
            "run_id": run_id,
            "tenant_code": "FNB",
            "expected_amount": Decimal("1000000.00"),
            "actual_amount": Decimal("1000000.00"),
            "variance_amount": Decimal("0.00"),
            "status": "MATCHED",
            "correlation_id": "corr-1",
            "created_at": None,
        },
    )

    patch_db(monkeypatch, conn)

    result = await run_funding_reconciliation(
        tenant_code="FNB",
        correlation_id="corr-1",
    )

    assert result == {
        "status": "ok",
        "run": {
            "run_id": run_id,
            "tenant_code": "FNB",
            "expected_amount": Decimal("1000000.00"),
            "actual_amount": Decimal("1000000.00"),
            "variance_amount": Decimal("0.00"),
            "status": "MATCHED",
            "correlation_id": "corr-1",
            "created_at": None,
        },
        "exception_count": 0,
        "exceptions": [],
    }
    insert_query, insert_args = conn.fetchrow_queries[2]
    assert "INSERT INTO funding_reconciliation_runs" in insert_query
    assert "run_date" in insert_query
    assert "correlation_id" in insert_query
    assert "NOW()" in insert_query
    assert insert_args[-1] == "corr-1"


@pytest.mark.asyncio
async def test_run_funding_reconciliation_creates_exception(monkeypatch):
    run_id = uuid4()
    exception_id = uuid4()

    patch_db(
        monkeypatch,
        FakeConnection(
            expected_row={"expected_amount": Decimal("1000000.00")},
            actual_row={"actual_amount": Decimal("999950.00")},
            insert_run_row={
                "run_id": run_id,
                "tenant_code": "FNB",
                "expected_amount": Decimal("1000000.00"),
                "actual_amount": Decimal("999950.00"),
                "variance_amount": Decimal("-50.00"),
                "status": "EXCEPTION",
                "correlation_id": "corr-1",
                "created_at": None,
            },
            insert_exception_row={
                "exception_id": exception_id,
                "run_id": run_id,
                "tenant_code": "FNB",
                "exception_type": "FUNDING_VARIANCE",
                "reference_id": None,
                "expected_amount": Decimal("1000000.00"),
                "actual_amount": Decimal("999950.00"),
                "variance_amount": Decimal("-50.00"),
                "status": "OPEN",
                "correlation_id": "corr-1",
                "created_at": None,
                "resolved_at": None,
            },
        ),
    )

    result = await run_funding_reconciliation(
        tenant_code="FNB",
        correlation_id="corr-1",
    )

    assert result["status"] == "ok"
    assert result["run"]["status"] == "EXCEPTION"
    assert result["run"]["variance_amount"] == Decimal("-50.00")
    assert result["exception_count"] == 1
    assert result["exceptions"][0]["exception_type"] == "FUNDING_VARIANCE"


@pytest.mark.asyncio
async def test_list_funding_reconciliation_runs(monkeypatch):
    run_id = uuid4()

    rows = [
        {
            "run_id": run_id,
            "tenant_code": "FNB",
            "expected_amount": Decimal("100.00"),
            "actual_amount": Decimal("100.00"),
            "variance_amount": Decimal("0.00"),
            "status": "MATCHED",
            "correlation_id": None,
            "created_at": None,
        }
    ]

    patch_db(monkeypatch, FakeConnection(fetch_rows=rows))

    result = await list_funding_reconciliation_runs(
        tenant_code="FNB",
        status="MATCHED",
        limit=10,
    )

    assert result == rows


@pytest.mark.asyncio
async def test_get_funding_reconciliation_run_returns_none(monkeypatch):
    patch_db(monkeypatch, FakeConnection(fetchrow_result=None))

    result = await get_funding_reconciliation_run(run_id=str(uuid4()))

    assert result is None


@pytest.mark.asyncio
async def test_get_funding_reconciliation_run_returns_run_with_exceptions(monkeypatch):
    run_id = uuid4()
    exception_id = uuid4()

    run = {
        "run_id": run_id,
        "tenant_code": "FNB",
        "expected_amount": Decimal("1000000.00"),
        "actual_amount": Decimal("999950.00"),
        "variance_amount": Decimal("-50.00"),
        "status": "EXCEPTION",
        "correlation_id": "corr-1",
        "created_at": None,
    }

    exceptions = [
        {
            "exception_id": exception_id,
            "run_id": run_id,
            "tenant_code": "FNB",
            "exception_type": "FUNDING_VARIANCE",
            "reference_id": None,
            "expected_amount": Decimal("1000000.00"),
            "actual_amount": Decimal("999950.00"),
            "variance_amount": Decimal("-50.00"),
            "status": "OPEN",
            "correlation_id": "corr-1",
            "created_at": None,
            "resolved_at": None,
        }
    ]

    patch_db(
        monkeypatch,
        FakeConnection(
            fetchrow_result=run,
            fetch_rows=exceptions,
        ),
    )

    result = await get_funding_reconciliation_run(run_id=str(run_id))

    assert result == {
        "run": run,
        "exception_count": 1,
        "exceptions": exceptions,
    }


@pytest.mark.asyncio
async def test_list_funding_reconciliation_exceptions(monkeypatch):
    exception_id = uuid4()
    run_id = uuid4()

    rows = [
        {
            "exception_id": exception_id,
            "run_id": run_id,
            "tenant_code": "FNB",
            "exception_type": "FUNDING_VARIANCE",
            "reference_id": None,
            "expected_amount": Decimal("100.00"),
            "actual_amount": Decimal("90.00"),
            "variance_amount": Decimal("-10.00"),
            "status": "OPEN",
            "correlation_id": None,
            "created_at": None,
            "resolved_at": None,
        }
    ]

    patch_db(monkeypatch, FakeConnection(fetch_rows=rows))

    result = await list_funding_reconciliation_exceptions(
        tenant_code="FNB",
        status="OPEN",
        limit=10,
    )

    assert result == rows


@pytest.mark.asyncio
async def test_resolve_funding_reconciliation_exception(monkeypatch):
    exception_id = uuid4()

    row = {
        "exception_id": exception_id,
        "run_id": uuid4(),
        "tenant_code": "FNB",
        "exception_type": "FUNDING_VARIANCE",
        "reference_id": None,
        "expected_amount": Decimal("100.00"),
        "actual_amount": Decimal("90.00"),
        "variance_amount": Decimal("-10.00"),
        "status": "RESOLVED",
        "correlation_id": None,
        "created_at": None,
        "resolved_at": None,
    }

    patch_db(monkeypatch, FakeConnection(fetchrow_result=row))

    result = await resolve_funding_reconciliation_exception(
        exception_id=str(exception_id),
    )

    assert result == row


@pytest.mark.asyncio
async def test_resolve_funding_reconciliation_exception_returns_none(monkeypatch):
    patch_db(monkeypatch, FakeConnection(fetchrow_result=None))

    result = await resolve_funding_reconciliation_exception(
        exception_id=str(uuid4()),
    )

    assert result is None
