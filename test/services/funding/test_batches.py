from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from services.fulfilment.settlement.batches import (
    _money,
    add_settlement_to_batch,
    approve_batch,
    create_settlement_batch,
    execute_batch,
    get_settlement_batch,
    list_settlement_batches,
    submit_batch_for_approval,
)


class FakeConnection:
    def __init__(self, *, fetchrow_results=None, fetch_rows=None, fetchval_results=None):
        self.fetchrow_results = fetchrow_results or []
        self.fetch_rows = fetch_rows or []
        self.fetchval_results = fetchval_results or [True]
        self.fetchrow_calls = 0
        self.fetchval_calls = 0
        self.execute_calls = []

    async def fetchrow(self, query, *args):
        if self.fetchrow_calls >= len(self.fetchrow_results):
            return None

        result = self.fetchrow_results[self.fetchrow_calls]
        self.fetchrow_calls += 1
        return result

    async def fetch(self, query, *args):
        return self.fetch_rows

    async def fetchval(self, query, *args):
        if self.fetchval_calls >= len(self.fetchval_results):
            return None

        result = self.fetchval_results[self.fetchval_calls]
        self.fetchval_calls += 1
        return result

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
        "services.fulfilment.settlement.batches.db_connection",
        lambda: FakeDbConnection(conn),
    )


async def fake_ensure_period_open(period_id: str):
    return {
        "period_id": period_id,
        "can_modify": True,
    }


def patch_lock(monkeypatch):
    monkeypatch.setattr(
        "services.fulfilment.settlement.batches.ensure_period_open",
        fake_ensure_period_open,
    )


def test_money_handles_none():
    assert _money(None) == Decimal("0.00")


def test_money_rounds_to_two_decimals():
    assert _money("10.126") == Decimal("10.13")


@pytest.mark.asyncio
async def test_create_settlement_batch(monkeypatch):
    patch_lock(monkeypatch)

    batch_id = uuid4()
    period_id = uuid4()

    row = {
        "batch_id": batch_id,
        "tenant_code": "FNB",
        "batch_reference": "BATCH-001",
        "batch_type": "REWARD_SETTLEMENT",
        "status": "DRAFT",
        "total_count": 0,
        "total_amount": Decimal("0.00"),
        "created_by": "admin",
        "approved_by": None,
        "created_at": None,
        "approved_at": None,
        "settled_at": None,
        "period_id": period_id,
    }

    patch_db(monkeypatch, FakeConnection(fetchrow_results=[row]))

    result = await create_settlement_batch(
        tenant_code="FNB",
        batch_reference="BATCH-001",
        created_by="admin",
        period_id=str(period_id),
    )

    assert result == row


@pytest.mark.asyncio
async def test_add_settlement_to_batch(monkeypatch):
    patch_lock(monkeypatch)

    batch_id = uuid4()
    settlement_id = uuid4()
    batch_item_id = uuid4()
    period_id = uuid4()

    batch = {
        "batch_id": batch_id,
        "status": "DRAFT",
        "period_id": period_id,
    }

    item = {
        "batch_item_id": batch_item_id,
        "batch_id": batch_id,
        "settlement_id": settlement_id,
        "amount": Decimal("100.00"),
        "status": "ADDED",
        "created_at": None,
    }

    updated_batch = {
        "batch_id": batch_id,
        "tenant_code": "FNB",
        "batch_reference": "BATCH-001",
        "batch_type": "REWARD_SETTLEMENT",
        "status": "DRAFT",
        "total_count": 1,
        "total_amount": Decimal("100.00"),
        "created_by": "admin",
        "approved_by": None,
        "created_at": None,
        "approved_at": None,
        "settled_at": None,
        "period_id": period_id,
    }

    patch_db(
        monkeypatch,
        FakeConnection(fetchrow_results=[batch, item, updated_batch]),
    )

    result = await add_settlement_to_batch(
        batch_id=str(batch_id),
        settlement_id=str(settlement_id),
        amount="100.00",
    )

    assert result == {
        "item": item,
        "batch": updated_batch,
    }


@pytest.mark.asyncio
async def test_add_settlement_to_batch_returns_none_when_batch_not_found(monkeypatch):
    patch_db(monkeypatch, FakeConnection(fetchrow_results=[None]))

    result = await add_settlement_to_batch(
        batch_id=str(uuid4()),
        settlement_id=str(uuid4()),
        amount="100.00",
    )

    assert result is None


@pytest.mark.asyncio
async def test_add_settlement_to_batch_returns_none_when_not_draft(monkeypatch):
    patch_lock(monkeypatch)

    patch_db(
        monkeypatch,
        FakeConnection(
            fetchrow_results=[
                {
                    "batch_id": uuid4(),
                    "status": "APPROVED",
                    "period_id": uuid4(),
                },
            ]
        ),
    )

    result = await add_settlement_to_batch(
        batch_id=str(uuid4()),
        settlement_id=str(uuid4()),
        amount="100.00",
    )

    assert result is None


@pytest.mark.asyncio
async def test_submit_batch_for_approval(monkeypatch):
    patch_lock(monkeypatch)

    batch_id = uuid4()
    period_id = uuid4()

    existing = {
        "batch_id": batch_id,
        "status": "DRAFT",
        "period_id": period_id,
    }

    row = {
        "batch_id": batch_id,
        "status": "READY_FOR_APPROVAL",
        "period_id": period_id,
    }

    patch_db(
        monkeypatch,
        FakeConnection(
            fetchrow_results=[
                existing,
                row,
            ]
        ),
    )

    result = await submit_batch_for_approval(batch_id=str(batch_id))

    assert result == row


@pytest.mark.asyncio
async def test_submit_batch_for_approval_returns_none(monkeypatch):
    patch_db(monkeypatch, FakeConnection(fetchrow_results=[None]))

    result = await submit_batch_for_approval(batch_id=str(uuid4()))

    assert result is None


@pytest.mark.asyncio
async def test_approve_batch(monkeypatch):
    patch_lock(monkeypatch)

    batch_id = uuid4()
    period_id = uuid4()

    existing = {
        "batch_id": batch_id,
        "status": "READY_FOR_APPROVAL",
        "period_id": period_id,
    }

    row = {
        "batch_id": batch_id,
        "status": "APPROVED",
        "approved_by": "finance-user",
        "period_id": period_id,
    }

    patch_db(
        monkeypatch,
        FakeConnection(
            fetchrow_results=[
                existing,
                row,
            ]
        ),
    )

    result = await approve_batch(
        batch_id=str(batch_id),
        approved_by="finance-user",
    )

    assert result == row


@pytest.mark.asyncio
async def test_approve_batch_returns_none(monkeypatch):
    patch_db(monkeypatch, FakeConnection(fetchrow_results=[None]))

    result = await approve_batch(
        batch_id=str(uuid4()),
        approved_by="finance-user",
    )

    assert result is None


@pytest.mark.asyncio
async def test_execute_batch(monkeypatch):
    patch_lock(monkeypatch)

    batch_id = uuid4()
    period_id = uuid4()

    existing = {
        "batch_id": batch_id,
        "status": "APPROVED",
        "period_id": period_id,
    }

    processing_batch = {
        "batch_id": batch_id,
    }

    settled_batch = {
        "batch_id": batch_id,
        "tenant_code": "FNB",
        "batch_reference": "BATCH-001",
        "batch_type": "REWARD_SETTLEMENT",
        "status": "SETTLED",
        "total_count": 1,
        "total_amount": Decimal("100.00"),
        "created_by": "admin",
        "approved_by": "finance-user",
        "created_at": None,
        "approved_at": None,
        "settled_at": None,
        "period_id": period_id,
    }

    conn = FakeConnection(
        fetchrow_results=[
            existing,
            processing_batch,
            settled_batch,
        ]
    )
    patch_db(monkeypatch, conn)

    result = await execute_batch(batch_id=str(batch_id))

    assert result == settled_batch
    assert len(conn.execute_calls) == 1


@pytest.mark.asyncio
async def test_execute_batch_returns_none(monkeypatch):
    patch_db(monkeypatch, FakeConnection(fetchrow_results=[None]))

    result = await execute_batch(batch_id=str(uuid4()))

    assert result is None


@pytest.mark.asyncio
async def test_get_settlement_batch(monkeypatch):
    batch_id = uuid4()
    item_id = uuid4()
    period_id = uuid4()

    batch = {
        "batch_id": batch_id,
        "tenant_code": "FNB",
        "batch_reference": "BATCH-001",
        "batch_type": "REWARD_SETTLEMENT",
        "status": "DRAFT",
        "total_count": 1,
        "total_amount": Decimal("100.00"),
        "created_by": "admin",
        "approved_by": None,
        "created_at": None,
        "approved_at": None,
        "settled_at": None,
        "period_id": period_id,
    }

    items = [
        {
            "batch_item_id": item_id,
            "batch_id": batch_id,
            "settlement_id": uuid4(),
            "amount": Decimal("100.00"),
            "status": "ADDED",
            "created_at": None,
        }
    ]

    patch_db(
        monkeypatch,
        FakeConnection(
            fetchrow_results=[batch],
            fetch_rows=items,
        ),
    )

    result = await get_settlement_batch(batch_id=str(batch_id))

    assert result == {
        "batch": batch,
        "item_count": 1,
        "items": items,
    }


@pytest.mark.asyncio
async def test_get_settlement_batch_returns_none(monkeypatch):
    patch_db(monkeypatch, FakeConnection(fetchrow_results=[None]))

    result = await get_settlement_batch(batch_id=str(uuid4()))

    assert result is None


@pytest.mark.asyncio
async def test_list_settlement_batches(monkeypatch):
    period_id = uuid4()

    rows = [
        {
            "batch_id": uuid4(),
            "tenant_code": "FNB",
            "batch_reference": "BATCH-001",
            "batch_type": "REWARD_SETTLEMENT",
            "status": "DRAFT",
            "total_count": 0,
            "total_amount": Decimal("0.00"),
            "created_by": "admin",
            "approved_by": None,
            "created_at": None,
            "approved_at": None,
            "settled_at": None,
            "period_id": period_id,
        }
    ]

    patch_db(monkeypatch, FakeConnection(fetch_rows=rows))

    result = await list_settlement_batches(
        tenant_code="FNB",
        status="DRAFT",
        limit=10,
    )

    assert result == rows
