from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from services.fulfilment.settlement.periods import (
    close_settlement_period,
    create_settlement_period,
    get_current_open_period,
    get_settlement_period,
    list_settlement_periods,
    reopen_settlement_period,
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
        "services.fulfilment.settlement.periods.db_connection",
        lambda: FakeDbConnection(conn),
    )


@pytest.mark.asyncio
async def test_create_settlement_period(monkeypatch):
    period_id = uuid4()

    row = {
        "period_id": period_id,
        "tenant_code": "FNB",
        "period_code": "2026-06",
        "period_start": date(2026, 6, 1),
        "period_end": date(2026, 6, 30),
        "status": "OPEN",
        "created_by": "finance-user",
        "closed_by": None,
        "created_at": None,
        "closed_at": None,
    }

    patch_db(monkeypatch, FakeConnection(fetchrow_result=row))

    result = await create_settlement_period(
        tenant_code="FNB",
        period_code="2026-06",
        period_start="2026-06-01",
        period_end="2026-06-30",
        created_by="finance-user",
    )

    assert result == row


@pytest.mark.asyncio
async def test_get_settlement_period(monkeypatch):
    period_id = uuid4()

    row = {
        "period_id": period_id,
        "tenant_code": "FNB",
        "period_code": "2026-06",
        "period_start": date(2026, 6, 1),
        "period_end": date(2026, 6, 30),
        "status": "OPEN",
        "created_by": "finance-user",
        "closed_by": None,
        "created_at": None,
        "closed_at": None,
    }

    patch_db(monkeypatch, FakeConnection(fetchrow_result=row))

    result = await get_settlement_period(period_id=str(period_id))

    assert result == row


@pytest.mark.asyncio
async def test_get_settlement_period_returns_none(monkeypatch):
    patch_db(monkeypatch, FakeConnection(fetchrow_result=None))

    result = await get_settlement_period(period_id=str(uuid4()))

    assert result is None


@pytest.mark.asyncio
async def test_get_current_open_period(monkeypatch):
    period_id = uuid4()

    row = {
        "period_id": period_id,
        "tenant_code": "FNB",
        "period_code": "2026-06",
        "period_start": date(2026, 6, 1),
        "period_end": date(2026, 6, 30),
        "status": "OPEN",
        "created_by": "finance-user",
        "closed_by": None,
        "created_at": None,
        "closed_at": None,
    }

    patch_db(monkeypatch, FakeConnection(fetchrow_result=row))

    result = await get_current_open_period(tenant_code="FNB")

    assert result == row


@pytest.mark.asyncio
async def test_get_current_open_period_returns_none(monkeypatch):
    patch_db(monkeypatch, FakeConnection(fetchrow_result=None))

    result = await get_current_open_period(tenant_code="FNB")

    assert result is None


@pytest.mark.asyncio
async def test_list_settlement_periods(monkeypatch):
    period_id = uuid4()

    rows = [
        {
            "period_id": period_id,
            "tenant_code": "FNB",
            "period_code": "2026-06",
            "period_start": date(2026, 6, 1),
            "period_end": date(2026, 6, 30),
            "status": "OPEN",
            "created_by": "finance-user",
            "closed_by": None,
            "created_at": None,
            "closed_at": None,
        }
    ]

    patch_db(monkeypatch, FakeConnection(fetch_rows=rows))

    result = await list_settlement_periods(
        tenant_code="FNB",
        status="OPEN",
        limit=10,
    )

    assert result == rows


@pytest.mark.asyncio
async def test_close_settlement_period(monkeypatch):
    period_id = uuid4()

    row = {
        "period_id": period_id,
        "tenant_code": "FNB",
        "period_code": "2026-06",
        "period_start": date(2026, 6, 1),
        "period_end": date(2026, 6, 30),
        "status": "CLOSED",
        "created_by": "finance-user",
        "closed_by": "treasury-user",
        "created_at": None,
        "closed_at": None,
    }

    patch_db(monkeypatch, FakeConnection(fetchrow_result=row))

    result = await close_settlement_period(
        period_id=str(period_id),
        closed_by="treasury-user",
    )

    assert result == row


@pytest.mark.asyncio
async def test_close_settlement_period_returns_none(monkeypatch):
    patch_db(monkeypatch, FakeConnection(fetchrow_result=None))

    result = await close_settlement_period(
        period_id=str(uuid4()),
        closed_by="treasury-user",
    )

    assert result is None


@pytest.mark.asyncio
async def test_reopen_settlement_period(monkeypatch):
    period_id = uuid4()

    row = {
        "period_id": period_id,
        "tenant_code": "FNB",
        "period_code": "2026-06",
        "period_start": date(2026, 6, 1),
        "period_end": date(2026, 6, 30),
        "status": "OPEN",
        "created_by": "finance-user",
        "closed_by": None,
        "created_at": None,
        "closed_at": None,
    }

    patch_db(monkeypatch, FakeConnection(fetchrow_result=row))

    result = await reopen_settlement_period(period_id=str(period_id))

    assert result == row


@pytest.mark.asyncio
async def test_reopen_settlement_period_returns_none(monkeypatch):
    patch_db(monkeypatch, FakeConnection(fetchrow_result=None))

    result = await reopen_settlement_period(period_id=str(uuid4()))

    assert result is None