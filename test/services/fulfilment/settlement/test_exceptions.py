from __future__ import annotations

from uuid import uuid4

import pytest

from services.fulfilment.settlement.exceptions import (
    create_settlement_exception,
    get_settlement_exception,
    list_settlement_exceptions,
    resolve_settlement_exception,
)


class FakeConnection:
    def __init__(self, *, fetchrow_result=None, fetch_rows=None):
        self.fetchrow_result = fetchrow_result
        self.fetch_rows = fetch_rows or []

    async def fetchrow(self, query, *args):
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
        "services.fulfilment.settlement.exceptions.db_connection",
        lambda: FakeDbConnection(conn),
    )


@pytest.mark.asyncio
async def test_create_settlement_exception(monkeypatch):
    exception_id = uuid4()
    batch_id = uuid4()
    settlement_id = uuid4()

    row = {
        "exception_id": exception_id,
        "batch_id": batch_id,
        "settlement_id": settlement_id,
        "exception_type": "DUPLICATE_SETTLEMENT",
        "severity": "CRITICAL",
        "status": "OPEN",
        "exception_message": "Duplicate settlement detected.",
        "correlation_id": "corr-1",
        "created_at": None,
        "resolved_at": None,
        "resolved_by": None,
    }

    patch_db(monkeypatch, FakeConnection(fetchrow_result=row))

    result = await create_settlement_exception(
        exception_type="DUPLICATE_SETTLEMENT",
        severity="CRITICAL",
        exception_message="Duplicate settlement detected.",
        batch_id=str(batch_id),
        settlement_id=str(settlement_id),
        correlation_id="corr-1",
    )

    assert result == row


@pytest.mark.asyncio
async def test_list_settlement_exceptions(monkeypatch):
    exception_id = uuid4()
    batch_id = uuid4()
    settlement_id = uuid4()

    rows = [
        {
            "exception_id": exception_id,
            "batch_id": batch_id,
            "settlement_id": settlement_id,
            "exception_type": "BATCH_AMOUNT_VARIANCE",
            "severity": "WARNING",
            "status": "OPEN",
            "exception_message": "Batch amount variance.",
            "correlation_id": None,
            "created_at": None,
            "resolved_at": None,
            "resolved_by": None,
        }
    ]

    patch_db(monkeypatch, FakeConnection(fetch_rows=rows))

    result = await list_settlement_exceptions(
        batch_id=str(batch_id),
        settlement_id=str(settlement_id),
        status="OPEN",
        severity="WARNING",
        exception_type="BATCH_AMOUNT_VARIANCE",
        limit=10,
    )

    assert result == rows


@pytest.mark.asyncio
async def test_get_settlement_exception(monkeypatch):
    exception_id = uuid4()

    row = {
        "exception_id": exception_id,
        "batch_id": uuid4(),
        "settlement_id": uuid4(),
        "exception_type": "SETTLEMENT_EXECUTION_FAILED",
        "severity": "CRITICAL",
        "status": "OPEN",
        "exception_message": "Settlement execution failed.",
        "correlation_id": "corr-1",
        "created_at": None,
        "resolved_at": None,
        "resolved_by": None,
    }

    patch_db(monkeypatch, FakeConnection(fetchrow_result=row))

    result = await get_settlement_exception(exception_id=str(exception_id))

    assert result == row


@pytest.mark.asyncio
async def test_get_settlement_exception_returns_none(monkeypatch):
    patch_db(monkeypatch, FakeConnection(fetchrow_result=None))

    result = await get_settlement_exception(exception_id=str(uuid4()))

    assert result is None


@pytest.mark.asyncio
async def test_resolve_settlement_exception(monkeypatch):
    exception_id = uuid4()

    row = {
        "exception_id": exception_id,
        "batch_id": uuid4(),
        "settlement_id": uuid4(),
        "exception_type": "APPROVAL_MISSING",
        "severity": "WARNING",
        "status": "RESOLVED",
        "exception_message": "Approval was missing.",
        "correlation_id": None,
        "created_at": None,
        "resolved_at": None,
        "resolved_by": "ops-user",
    }

    patch_db(monkeypatch, FakeConnection(fetchrow_result=row))

    result = await resolve_settlement_exception(
        exception_id=str(exception_id),
        resolved_by="ops-user",
    )

    assert result == row


@pytest.mark.asyncio
async def test_resolve_settlement_exception_returns_none(monkeypatch):
    patch_db(monkeypatch, FakeConnection(fetchrow_result=None))

    result = await resolve_settlement_exception(
        exception_id=str(uuid4()),
        resolved_by="ops-user",
    )

    assert result is None