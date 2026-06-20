from __future__ import annotations

from uuid import uuid4

import pytest

from services.fulfilment.settlement.approvals import (
    approve_batch_request,
    get_batch_approvals,
    reject_batch_request,
    request_batch_approval,
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
        "services.fulfilment.settlement.approvals.db_connection",
        lambda: FakeDbConnection(conn),
    )


@pytest.mark.asyncio
async def test_request_batch_approval_creates_new(monkeypatch):
    batch_id = uuid4()
    approval_id = uuid4()
    period_id = uuid4()

    async def fake_ensure_period_open(period_id: str):
        return {
            "period_id": period_id,
            "can_modify": True,
        }

    monkeypatch.setattr(
        "services.fulfilment.settlement.approvals.ensure_period_open",
        fake_ensure_period_open,
    )

    batch = {
        "batch_id": batch_id,
        "status": "READY_FOR_APPROVAL",
        "period_id": period_id,
    }

    approval = {
        "approval_id": approval_id,
        "batch_id": batch_id,
        "approval_type": "SETTLEMENT_BATCH_APPROVAL",
        "approval_status": "PENDING",
        "requested_by": "maker-user",
        "approved_by": None,
        "comments": "Please approve",
        "created_at": None,
        "approved_at": None,
    }

    patch_db(
        monkeypatch,
        FakeConnection(
            fetchrow_results=[
                batch,
                None,
                approval,
            ],
        ),
    )

    result = await request_batch_approval(
        batch_id=str(batch_id),
        requested_by="maker-user",
        comments="Please approve",
    )

    assert result == approval


@pytest.mark.asyncio
async def test_request_batch_approval_returns_existing(monkeypatch):
    batch_id = uuid4()
    approval_id = uuid4()
    period_id = uuid4()

    async def fake_ensure_period_open(period_id: str):
        return {
            "period_id": period_id,
            "can_modify": True,
        }

    monkeypatch.setattr(
        "services.fulfilment.settlement.approvals.ensure_period_open",
        fake_ensure_period_open,
    )

    batch = {
        "batch_id": batch_id,
        "status": "READY_FOR_APPROVAL",
        "period_id": period_id,
    }

    existing = {
        "approval_id": approval_id,
        "batch_id": batch_id,
        "approval_type": "SETTLEMENT_BATCH_APPROVAL",
        "approval_status": "PENDING",
        "requested_by": "maker-user",
        "approved_by": None,
        "comments": None,
        "created_at": None,
        "approved_at": None,
    }

    patch_db(
        monkeypatch,
        FakeConnection(
            fetchrow_results=[
                batch,
                existing,
            ],
        ),
    )

    result = await request_batch_approval(
        batch_id=str(batch_id),
        requested_by="maker-user",
    )

    assert result == existing


@pytest.mark.asyncio
async def test_request_batch_approval_returns_none_when_batch_not_found(monkeypatch):
    patch_db(monkeypatch, FakeConnection(fetchrow_results=[None]))

    result = await request_batch_approval(
        batch_id=str(uuid4()),
        requested_by="maker-user",
    )

    assert result is None


@pytest.mark.asyncio
async def test_request_batch_approval_returns_none_when_batch_not_ready(monkeypatch):
    period_id = uuid4()

    async def fake_ensure_period_open(period_id: str):
        return {
            "period_id": period_id,
            "can_modify": True,
        }

    monkeypatch.setattr(
        "services.fulfilment.settlement.approvals.ensure_period_open",
        fake_ensure_period_open,
    )

    patch_db(
        monkeypatch,
        FakeConnection(
            fetchrow_results=[
                {
                    "batch_id": uuid4(),
                    "status": "DRAFT",
                    "period_id": period_id,
                }
            ]
        ),
    )

    result = await request_batch_approval(
        batch_id=str(uuid4()),
        requested_by="maker-user",
    )

    assert result is None


@pytest.mark.asyncio
async def test_approve_batch_request(monkeypatch):
    approval_id = uuid4()
    batch_id = uuid4()
    period_id = uuid4()

    async def fake_ensure_period_open(period_id: str):
        return {
            "period_id": period_id,
            "can_modify": True,
        }

    monkeypatch.setattr(
        "services.fulfilment.settlement.approvals.ensure_period_open",
        fake_ensure_period_open,
    )

    existing = {
        "approval_id": approval_id,
        "batch_id": batch_id,
        "period_id": period_id,
    }

    approval = {
        "approval_id": approval_id,
        "batch_id": batch_id,
        "approval_type": "SETTLEMENT_BATCH_APPROVAL",
        "approval_status": "APPROVED",
        "requested_by": "maker-user",
        "approved_by": "checker-user",
        "comments": "Approved",
        "created_at": None,
        "approved_at": None,
    }

    conn = FakeConnection(
        fetchrow_results=[
            existing,
            approval,
        ]
    )
    patch_db(monkeypatch, conn)

    result = await approve_batch_request(
        approval_id=str(approval_id),
        approved_by="checker-user",
        comments="Approved",
    )

    assert result == approval
    assert len(conn.execute_calls) == 1


@pytest.mark.asyncio
async def test_approve_batch_request_returns_none(monkeypatch):
    conn = FakeConnection(fetchrow_results=[None])
    patch_db(monkeypatch, conn)

    result = await approve_batch_request(
        approval_id=str(uuid4()),
        approved_by="checker-user",
    )

    assert result is None
    assert conn.execute_calls == []


@pytest.mark.asyncio
async def test_reject_batch_request(monkeypatch):
    approval_id = uuid4()
    batch_id = uuid4()
    period_id = uuid4()

    async def fake_ensure_period_open(period_id: str):
        return {
            "period_id": period_id,
            "can_modify": True,
        }

    monkeypatch.setattr(
        "services.fulfilment.settlement.approvals.ensure_period_open",
        fake_ensure_period_open,
    )

    existing = {
        "approval_id": approval_id,
        "batch_id": batch_id,
        "period_id": period_id,
    }

    approval = {
        "approval_id": approval_id,
        "batch_id": batch_id,
        "approval_type": "SETTLEMENT_BATCH_APPROVAL",
        "approval_status": "REJECTED",
        "requested_by": "maker-user",
        "approved_by": "checker-user",
        "comments": "Rejected",
        "created_at": None,
        "approved_at": None,
    }

    conn = FakeConnection(
        fetchrow_results=[
            existing,
            approval,
        ]
    )
    patch_db(monkeypatch, conn)

    result = await reject_batch_request(
        approval_id=str(approval_id),
        rejected_by="checker-user",
        comments="Rejected",
    )

    assert result == approval
    assert len(conn.execute_calls) == 1


@pytest.mark.asyncio
async def test_reject_batch_request_uses_default_comment(monkeypatch):
    approval_id = uuid4()
    batch_id = uuid4()
    period_id = uuid4()

    async def fake_ensure_period_open(period_id: str):
        return {
            "period_id": period_id,
            "can_modify": True,
        }

    monkeypatch.setattr(
        "services.fulfilment.settlement.approvals.ensure_period_open",
        fake_ensure_period_open,
    )

    existing = {
        "approval_id": approval_id,
        "batch_id": batch_id,
        "period_id": period_id,
    }

    approval = {
        "approval_id": approval_id,
        "batch_id": batch_id,
        "approval_type": "SETTLEMENT_BATCH_APPROVAL",
        "approval_status": "REJECTED",
        "requested_by": "maker-user",
        "approved_by": "checker-user",
        "comments": "Rejected by checker-user",
        "created_at": None,
        "approved_at": None,
    }

    conn = FakeConnection(
        fetchrow_results=[
            existing,
            approval,
        ]
    )
    patch_db(monkeypatch, conn)

    result = await reject_batch_request(
        approval_id=str(approval_id),
        rejected_by="checker-user",
    )

    assert result == approval
    assert len(conn.execute_calls) == 1


@pytest.mark.asyncio
async def test_reject_batch_request_returns_none(monkeypatch):
    conn = FakeConnection(fetchrow_results=[None])
    patch_db(monkeypatch, conn)

    result = await reject_batch_request(
        approval_id=str(uuid4()),
        rejected_by="checker-user",
    )

    assert result is None
    assert conn.execute_calls == []


@pytest.mark.asyncio
async def test_get_batch_approvals(monkeypatch):
    batch_id = uuid4()
    approval_id = uuid4()

    rows = [
        {
            "approval_id": approval_id,
            "batch_id": batch_id,
            "approval_type": "SETTLEMENT_BATCH_APPROVAL",
            "approval_status": "PENDING",
            "requested_by": "maker-user",
            "approved_by": None,
            "comments": None,
            "created_at": None,
            "approved_at": None,
        }
    ]

    patch_db(monkeypatch, FakeConnection(fetch_rows=rows))

    result = await get_batch_approvals(batch_id=str(batch_id))

    assert result == rows
