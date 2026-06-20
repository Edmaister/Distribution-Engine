from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from services.fulfilment.settlement.reversals import (
    _money,
    approve_settlement_reversal,
    create_settlement_reversal,
    execute_settlement_reversal,
    get_settlement_reversal,
    list_settlement_reversals,
)


class FakeConnection:
    def __init__(self, *, fetchrow_results=None, fetch_rows=None):
        self.fetchrow_results = fetchrow_results or []
        self.fetch_rows = fetch_rows or []
        self.fetchrow_calls = 0
        self.execute_calls = []

    async def fetchrow(self, query, *args):
        if self.fetchrow_calls >= len(self.fetchrow_results):
            return None

        result = self.fetchrow_results[self.fetchrow_calls]
        self.fetchrow_calls += 1
        return result

    async def fetch(self, query, *args):
        return self.fetch_rows

    async def execute(self, query, *args):
        self.execute_calls.append((query, args))
        return "UPDATE 1"


class FakeDbConnection:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return None


def patch_db(monkeypatch, conn):
    monkeypatch.setattr(
        "services.fulfilment.settlement.reversals.db_connection",
        lambda: FakeDbConnection(conn),
    )


def test_money_handles_none():
    assert _money(None) == Decimal("0.00")


def test_money_rounds_to_two_decimals():
    assert _money("10.126") == Decimal("10.13")


@pytest.mark.asyncio
async def test_create_settlement_reversal(monkeypatch):
    reversal_id = uuid4()
    settlement_id = uuid4()

    settlement = {
        "settlement_id": settlement_id,
        "period_id": None,
    }

    row = {
        "reversal_id": reversal_id,
        "settlement_id": settlement_id,
        "tenant_code": "FNB",
        "reversal_reason": "Duplicate settlement",
        "amount": Decimal("100.00"),
        "status": "REQUESTED",
        "requested_by": "ops-user",
        "approved_by": None,
        "correlation_id": "corr-1",
        "created_at": None,
        "approved_at": None,
        "executed_at": None,
    }

    patch_db(
        monkeypatch,
        FakeConnection(
            fetchrow_results=[
                settlement,  # lookup
                row,         # insert result
            ]
        ),
    )

    result = await create_settlement_reversal(
        settlement_id=str(settlement_id),
        tenant_code="FNB",
        reversal_reason="Duplicate settlement",
        amount="100.00",
        requested_by="ops-user",
        correlation_id="corr-1",
    )

    assert result == row


@pytest.mark.asyncio
async def test_get_settlement_reversal(monkeypatch):
    reversal_id = uuid4()

    row = {
        "reversal_id": reversal_id,
        "settlement_id": uuid4(),
        "tenant_code": "FNB",
        "reversal_reason": "Incorrect amount",
        "amount": Decimal("250.00"),
        "status": "REQUESTED",
        "requested_by": "ops-user",
        "approved_by": None,
        "correlation_id": None,
        "created_at": None,
        "approved_at": None,
        "executed_at": None,
    }

    patch_db(monkeypatch, FakeConnection(fetchrow_results=[row]))

    result = await get_settlement_reversal(reversal_id=str(reversal_id))

    assert result == row


@pytest.mark.asyncio
async def test_get_settlement_reversal_returns_none(monkeypatch):
    patch_db(monkeypatch, FakeConnection(fetchrow_results=[None]))

    result = await get_settlement_reversal(reversal_id=str(uuid4()))

    assert result is None


@pytest.mark.asyncio
async def test_list_settlement_reversals(monkeypatch):
    reversal_id = uuid4()
    settlement_id = uuid4()

    rows = [
        {
            "reversal_id": reversal_id,
            "settlement_id": settlement_id,
            "tenant_code": "FNB",
            "reversal_reason": "Duplicate settlement",
            "amount": Decimal("100.00"),
            "status": "REQUESTED",
            "requested_by": "ops-user",
            "approved_by": None,
            "correlation_id": "corr-1",
            "created_at": None,
            "approved_at": None,
            "executed_at": None,
        }
    ]

    patch_db(monkeypatch, FakeConnection(fetch_rows=rows))

    result = await list_settlement_reversals(
        tenant_code="FNB",
        settlement_id=str(settlement_id),
        status="REQUESTED",
        limit=10,
    )

    assert result == rows


@pytest.mark.asyncio
async def test_approve_settlement_reversal(monkeypatch):
    reversal_id = uuid4()

    row = {
        "reversal_id": reversal_id,
        "settlement_id": uuid4(),
        "tenant_code": "FNB",
        "reversal_reason": "Duplicate settlement",
        "amount": Decimal("100.00"),
        "status": "APPROVED",
        "requested_by": "ops-user",
        "approved_by": "finance-user",
        "correlation_id": "corr-1",
        "created_at": None,
        "approved_at": None,
        "executed_at": None,
    }

    patch_db(monkeypatch, FakeConnection(fetchrow_results=[row]))

    result = await approve_settlement_reversal(
        reversal_id=str(reversal_id),
        approved_by="finance-user",
    )

    assert result == row


@pytest.mark.asyncio
async def test_approve_settlement_reversal_returns_none(monkeypatch):
    patch_db(monkeypatch, FakeConnection(fetchrow_results=[None]))

    result = await approve_settlement_reversal(
        reversal_id=str(uuid4()),
        approved_by="finance-user",
    )

    assert result is None


@pytest.mark.asyncio
async def test_execute_settlement_reversal(monkeypatch):
    reversal_id = uuid4()
    settlement_id = uuid4()

    reversal = {
        "reversal_id": reversal_id,
        "settlement_id": settlement_id,
        "amount": Decimal("100.00"),
        "status": "APPROVED",
    }

    executed = {
        "reversal_id": reversal_id,
        "settlement_id": settlement_id,
        "tenant_code": "FNB",
        "reversal_reason": "Duplicate settlement",
        "amount": Decimal("100.00"),
        "status": "EXECUTED",
        "requested_by": "ops-user",
        "approved_by": "finance-user",
        "correlation_id": "corr-1",
        "created_at": None,
        "approved_at": None,
        "executed_at": None,
    }

    conn = FakeConnection(fetchrow_results=[reversal, executed])
    patch_db(monkeypatch, conn)

    result = await execute_settlement_reversal(reversal_id=str(reversal_id))

    assert result == executed
    assert len(conn.execute_calls) == 1


@pytest.mark.asyncio
async def test_execute_settlement_reversal_returns_none_when_not_found(monkeypatch):
    patch_db(monkeypatch, FakeConnection(fetchrow_results=[None]))

    result = await execute_settlement_reversal(reversal_id=str(uuid4()))

    assert result is None


@pytest.mark.asyncio
async def test_execute_settlement_reversal_returns_none_when_not_approved(monkeypatch):
    reversal = {
        "reversal_id": uuid4(),
        "settlement_id": uuid4(),
        "amount": Decimal("100.00"),
        "status": "REQUESTED",
    }

    conn = FakeConnection(fetchrow_results=[reversal])
    patch_db(monkeypatch, conn)

    result = await execute_settlement_reversal(reversal_id=str(uuid4()))

    assert result is None
    assert conn.execute_calls == []