from contextlib import asynccontextmanager

import pytest

import os

os.environ.setdefault(
    "REFERRAL_CODE_SECRET",
    "test-referral-secret-123456789"
)

import services.referral_code as rc


# -----------------------
# Fake async DB
# -----------------------

class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


class FakeAsyncConn:
    def __init__(self, fetchrow_values=None):
        self._fetchrow_values = list(fetchrow_values or [])
        self.executed = []

    def transaction(self):
        return FakeTransaction()

    async def fetchrow(self, sql, *params):
        self.executed.append((sql, params))
        if self._fetchrow_values:
            return self._fetchrow_values.pop(0)
        return None

    async def execute(self, sql, *params):
        self.executed.append((sql, params))
        return "EXECUTE 1"


def patch_async_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(rc, "db_connection", fake_db_connection)


# -----------------------
# Tests
# -----------------------

def test_generate_referral_code():
    code = rc._generate_referral_code()
    assert len(code) == 10


def test_handle_validation():
    assert rc._is_handle_valid("Valid_123")
    assert not rc._is_handle_valid("x")
    assert not rc._is_handle_valid("invalid space")


@pytest.mark.asyncio
async def test_get_or_create_missing_fields():
    body, status = await rc.get_or_create_referrer_code(
        referrer_ucn="",
        tenant="FNB",
        sticker="ST1",
        segment="PREMIER",
        accepted_terms=True,
    )

    assert status == 400
    assert body["error_code"] == "MISSING_FIELDS"


@pytest.mark.asyncio
async def test_get_or_create_requires_terms():
    body, status = await rc.get_or_create_referrer_code(
        referrer_ucn="123",
        tenant="FNB",
        sticker="ST1",
        segment="PREMIER",
        accepted_terms=False,
    )

    assert status == 400
    assert body["error_code"] == "ACCEPTED_TERMS_REQUIRED"


@pytest.mark.asyncio
async def test_get_or_create_existing(monkeypatch):
    conn = FakeAsyncConn(
        fetchrow_values=[
            {
                "referral_code": "CODE123",
                "gaming_handle": "Handle1",
            }
        ]
    )
    patch_async_db(monkeypatch, conn)

    monkeypatch.setattr(rc, "_identity_lookup_key", lambda x: "hash")

    body, status = await rc.get_or_create_referrer_code(
        referrer_ucn="123",
        tenant="FNB",
        sticker="ST1",
        segment="PREMIER",
        accepted_terms=True,
    )

    assert status == 200
    assert body["created"] is False
    assert body["referral_code"] == "CODE123"
    assert body["gaming_handle"] == "Handle1"


@pytest.mark.asyncio
async def test_get_or_create_new(monkeypatch):
    conn = FakeAsyncConn(fetchrow_values=[None])
    patch_async_db(monkeypatch, conn)

    monkeypatch.setattr(rc, "_identity_lookup_key", lambda x: "hash")
    monkeypatch.setattr(rc, "_generate_referral_code", lambda: "NEWCODE")

    async def fake_pick_handle(conn, preferred):
        return "HandleX"

    monkeypatch.setattr(rc, "_pick_handle", fake_pick_handle)

    body, status = await rc.get_or_create_referrer_code(
        referrer_ucn="123",
        tenant="FNB",
        sticker="ST1",
        segment="PREMIER",
        accepted_terms=True,
    )

    assert status == 201
    assert body["created"] is True
    assert body["referral_code"] == "NEWCODE"


@pytest.mark.asyncio
async def test_validate_referral_code_missing_inputs():
    body, status = await rc.validate_referral_code(
        tenant_code="",
        referral_code="",
        accepted_terms=False,
    )

    assert status == 400


@pytest.mark.asyncio
async def test_validate_referral_code_not_found(monkeypatch):
    conn = FakeAsyncConn(fetchrow_values=[None])
    patch_async_db(monkeypatch, conn)

    body, status = await rc.validate_referral_code(
        tenant_code="FNB",
        referral_code="ABC",
        accepted_terms=True,
    )

    assert status == 404
    assert body["valid"] is False


@pytest.mark.asyncio
async def test_validate_referral_code_success(monkeypatch):
    conn = FakeAsyncConn(
        fetchrow_values=[
            {
                "referrer_code_id": "code-id",
                "referrer_ucn": "123",
            }
        ]
    )
    patch_async_db(monkeypatch, conn)

    monkeypatch.setattr(rc, "_normalize_alias", lambda x: "Alias1")
    monkeypatch.setattr(rc, "_validate_alias", lambda x: (True, None, "alias1"))

    body, status = await rc.validate_referral_code(
        tenant_code="FNB",
        referral_code="ABC",
        accepted_terms=True,
    )

    assert status == 200
    assert body["valid"] is True


@pytest.mark.asyncio
async def test_capture_referee_ucn_missing():
    body, status = await rc.capture_referee_ucn(
        referral_track_id="",
        referee_ucn="",
        tenant_code="FNB",
    )

    assert status == 400


@pytest.mark.asyncio
async def test_capture_referee_ucn_not_found(monkeypatch):
    conn = FakeAsyncConn(fetchrow_values=[None])
    patch_async_db(monkeypatch, conn)

    body, status = await rc.capture_referee_ucn(
        referral_track_id="t1",
        referee_ucn="123",
        tenant_code="FNB",
    )

    assert status == 404


@pytest.mark.asyncio
async def test_capture_referee_ucn_success(monkeypatch):
    conn = FakeAsyncConn(
        fetchrow_values=[
            {
                "product": "Transactional",
                "sub_product": "DDA",
                "tenant_code": "FNB",
                "tenant_is_active": True,
            }
        ]
    )
    patch_async_db(monkeypatch, conn)

    async def fake_handle_progress_event(req, tenant_code=None):
        return {}, 200

    monkeypatch.setattr(
        rc,
        "_identity_lookup_key",
        lambda x: "hash",
    )

    monkeypatch.setattr(
        rc,
        "handle_progress_event",
        fake_handle_progress_event,
    )

    body, status = await rc.capture_referee_ucn(
        referral_track_id="t1",
        referee_ucn="123",
        tenant_code="FNB",
    )

    assert status == 200
    assert body["error_code"] is None
