from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest

import services.referral_bootstrap_service as svc
from services.referral_bootstrap_service import ReferralBootstrapError


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

    def transaction(self):
        return FakeTx()


def patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(svc, "db_connection", fake_db_connection)


@pytest.mark.asyncio
async def test_get_referrer_by_ucn_and_tenant_found(monkeypatch):
    row = {"referrer_ucn": "123", "tenant_code": "FNB"}
    conn = FakeConn(row=row)
    patch_db(monkeypatch, conn)

    result = await svc.get_referrer_by_ucn_and_tenant("123", "FNB")

    assert result == row
    assert conn.calls[0][2] == ("123", "FNB")


@pytest.mark.asyncio
async def test_bootstrap_referrer_profile_returns_existing_referrer(monkeypatch):
    existing_row = {
        "referrer_ucn": "12345678901",
        "tenant_code": "FNB",
        "referral_code": "ABC12345",
        "gaming_handle": "Stormers1",
        "accepted_terms": True,
    }

    async def fake_get(referrer_ucn, tenant_code):
        return existing_row

    monkeypatch.setattr(svc, "get_referrer_by_ucn_and_tenant", fake_get)

    result = await svc.bootstrap_referrer_profile("12345678901", "FNB")

    assert result["exists"] is True
    assert result["referralCode"] == "ABC12345"
    assert result["alias"] == "Stormers1"
    assert result["qrEligible"] is True


@pytest.mark.asyncio
async def test_bootstrap_referrer_profile_returns_not_found(monkeypatch):
    async def fake_get(referrer_ucn, tenant_code):
        return None

    monkeypatch.setattr(svc, "get_referrer_by_ucn_and_tenant", fake_get)

    result = await svc.bootstrap_referrer_profile("12345678901", "FNB")

    assert result["exists"] is False
    assert result["referralCode"] is None
    assert result["qrEligible"] is False


@pytest.mark.asyncio
async def test_bootstrap_referrer_profile_existing_but_terms_not_accepted(monkeypatch):
    existing_row = {
        "referrer_ucn": "12345678901",
        "tenant_code": "FNB",
        "referral_code": "ABC12345",
        "gaming_handle": "Stormers1",
        "accepted_terms": False,
    }

    async def fake_get(referrer_ucn, tenant_code):
        return existing_row

    monkeypatch.setattr(svc, "get_referrer_by_ucn_and_tenant", fake_get)

    result = await svc.bootstrap_referrer_profile("12345678901", "FNB")

    assert result["exists"] is True
    assert result["acceptedTerms"] is False
    assert result["requiresTermsAcceptance"] is True
    assert result["qrEligible"] is False


@pytest.mark.asyncio
async def test_accept_terms_success(monkeypatch):
    accepted_at = datetime(2026, 4, 7, 10, 15, 30, tzinfo=timezone.utc)
    row = {
        "referrer_ucn": "12345678901",
        "tenant_code": "FNB",
        "accepted_terms": True,
        "accepted_terms_at": accepted_at,
    }

    conn = FakeConn(row=row)
    patch_db(monkeypatch, conn)

    result = await svc.accept_terms("12345678901", "FNB")

    assert result == {
        "referrerUcn": "12345678901",
        "tenantCode": "FNB",
        "acceptedTerms": True,
        "acceptedTermsAt": accepted_at.isoformat(),
        "message": "Terms accepted successfully",
    }


@pytest.mark.asyncio
async def test_accept_terms_not_found(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    with pytest.raises(ReferralBootstrapError, match="Referrer profile not found"):
        await svc.accept_terms("12345678901", "FNB")