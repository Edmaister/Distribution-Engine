from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import pytest

import services.campaign_service as cs


class FakeTx:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self, row=None):
        self.row = row
        self.calls = []

    async def fetchrow(self, query, *params):
        self.calls.append(("fetchrow", query, params))
        return self.row

    async def execute(self, query, *params):
        self.calls.append(("execute", query, params))
        return "OK"

    def transaction(self):
        return FakeTx()


def patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(cs, "db_connection", fake_db_connection)


def test_generate_campaign_code():
    code = cs._generate_campaign_code("fnb", "gold", "summer sale")
    assert "FNB" in code
    assert "GOLD" in code


@pytest.mark.asyncio
async def test_create_campaign_missing_fields():
    body, status = await cs.create_campaign(
        tenant_code="FNB",
        segment="",
        name="Test",
    )

    assert status == 422
    assert body["ok"] is False


@pytest.mark.asyncio
async def test_create_campaign_invalid_dates():
    now = datetime.now(timezone.utc)

    body, status = await cs.create_campaign(
        tenant_code="FNB",
        segment="GOLD",
        name="Test",
        starts_at=now,
        ends_at=now - timedelta(days=1),
    )

    assert status == 422


@pytest.mark.asyncio
async def test_create_campaign_success(monkeypatch):
    conn = FakeConn(row={"campaign_code": "CODE123"})
    patch_db(monkeypatch, conn)

    body, status = await cs.create_campaign(
        tenant_code="FNB",
        segment="GOLD",
        name="Test Campaign",
    )

    assert status == 201
    assert body["ok"] is True
    assert body["campaign_code"] == "CODE123"


@pytest.mark.asyncio
async def test_validate_campaign_missing_code():
    body, status = await cs.validate_campaign_and_create_track(
        tenant_code="FNB",
        campaign_code="",
    )

    assert status == 422


@pytest.mark.asyncio
async def test_validate_campaign_not_found(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    body, status = await cs.validate_campaign_and_create_track(
        tenant_code="FNB",
        campaign_code="ABC",
    )

    assert status == 200
    assert body["valid"] is False


@pytest.mark.asyncio
async def test_validate_campaign_tenant_mismatch(monkeypatch):
    conn = FakeConn(
        row={
            "campaign_code": "ABC",
            "tenant_code": "OTHER",
            "is_active": True,
            "starts_at": None,
            "ends_at": None,
        }
    )
    patch_db(monkeypatch, conn)

    body, status = await cs.validate_campaign_and_create_track(
        tenant_code="FNB",
        campaign_code="ABC",
    )

    assert status == 200
    assert body["valid"] is False
    assert body["reason"] == "Tenant mismatch"


@pytest.mark.asyncio
async def test_validate_campaign_inactive(monkeypatch):
    conn = FakeConn(
        row={
            "campaign_code": "ABC",
            "tenant_code": "FNB",
            "is_active": False,
            "starts_at": None,
            "ends_at": None,
        }
    )
    patch_db(monkeypatch, conn)

    body, status = await cs.validate_campaign_and_create_track(
        tenant_code="FNB",
        campaign_code="ABC",
    )

    assert body["valid"] is False
    assert "inactive" in body["reason"].lower()


@pytest.mark.asyncio
async def test_validate_campaign_not_started(monkeypatch):
    future = datetime.now(timezone.utc) + timedelta(days=1)

    conn = FakeConn(
        row={
            "campaign_code": "ABC",
            "tenant_code": "FNB",
            "is_active": True,
            "starts_at": future,
            "ends_at": None,
        }
    )
    patch_db(monkeypatch, conn)

    body, status = await cs.validate_campaign_and_create_track(
        tenant_code="FNB",
        campaign_code="ABC",
    )

    assert body["valid"] is False
    assert body["reason"] == "Campaign not started"


@pytest.mark.asyncio
async def test_validate_campaign_expired(monkeypatch):
    past = datetime.now(timezone.utc) - timedelta(days=1)

    conn = FakeConn(
        row={
            "campaign_code": "ABC",
            "tenant_code": "FNB",
            "is_active": True,
            "starts_at": None,
            "ends_at": past,
        }
    )
    patch_db(monkeypatch, conn)

    body, status = await cs.validate_campaign_and_create_track(
        tenant_code="FNB",
        campaign_code="ABC",
    )

    assert body["valid"] is False
    assert body["reason"] == "Campaign expired"


@pytest.mark.asyncio
async def test_validate_campaign_success(monkeypatch):
    conn = FakeConn(
        row={
            "campaign_code": "ABC",
            "tenant_code": "FNB",
            "is_active": True,
            "starts_at": None,
            "ends_at": None,
        }
    )
    patch_db(monkeypatch, conn)

    body, status = await cs.validate_campaign_and_create_track(
        tenant_code="FNB",
        campaign_code="ABC",
    )

    assert status == 200
    assert body["valid"] is True
    assert body["campaignCode"] == "ABC"
    assert body["campaignTrackId"] is not None


@pytest.mark.asyncio
async def test_update_campaign_status_missing():
    body, status = await cs.update_campaign_track_status(
        campaign_track_id="",
        status="VALIDATED",
    )

    assert status == 422


@pytest.mark.asyncio
async def test_update_campaign_status_missing_status():
    body, status = await cs.update_campaign_track_status(
        campaign_track_id="t1",
        status="",
    )

    assert status == 422


@pytest.mark.asyncio
async def test_update_campaign_status_invalid_status():
    body, status = await cs.update_campaign_track_status(
        campaign_track_id="t1",
        status="BAD",
    )

    assert status == 422


@pytest.mark.asyncio
async def test_update_campaign_status_not_found(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    body, status = await cs.update_campaign_track_status(
        campaign_track_id="t1",
        status="VALIDATED",
    )

    assert status == 404


@pytest.mark.asyncio
async def test_update_campaign_status_success(monkeypatch):
    conn = FakeConn(
        row={
            "campaign_track_id": "t1",
            "status": "VALIDATED",
        }
    )
    patch_db(monkeypatch, conn)

    body, status = await cs.update_campaign_track_status(
        campaign_track_id="t1",
        status="VALIDATED",
    )

    assert status == 200
    assert body["ok"] is True
    assert body["campaignTrackId"] == "t1"
    assert body["newStatus"] == "VALIDATED"