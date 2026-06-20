from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import pytest

import services.privacy_service as svc


class FakeTx:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self):
        self.queries = []
        self.referrer_row = {
            "referrer_code_id": "ref-code-123",
            "created_at": datetime.utcnow() - timedelta(days=3000),
        }
        self.retention_row = {"retention_days": 1825}

    async def fetchrow(self, query, *params):
        self.queries.append((query, params))

        if "SELECT retention_days" in query:
            return self.retention_row

        if "SELECT referrer_code_id" in query:
            return self.referrer_row

        return None

    async def execute(self, query, *params):
        self.queries.append((query, params))

        if "UPDATE referral_instances" in query:
            return "UPDATE 7"

        if "UPDATE referrer_codes" in query:
            return "UPDATE 1"

        if "DELETE FROM referral_instances" in query:
            return "DELETE 3"

        if "DELETE FROM referrer_codes" in query:
            return "DELETE 2"

        if "INSERT INTO privacy_erasure_audit" in query:
            return "INSERT 0 1"

        return "OK"

    def transaction(self):
        return FakeTx()


def _patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(svc, "db_connection", fake_db_connection)


def test_parse_rowcount():
    assert svc._parse_rowcount("UPDATE 7") == 7
    assert svc._parse_rowcount("DELETE 2") == 2
    assert svc._parse_rowcount("INSERT 0 1") == 1
    assert svc._parse_rowcount(None) == 0
    assert svc._parse_rowcount("bad") == 0


def test_ensure_naive_utc_none_and_naive():
    now = datetime.utcnow()

    assert svc._ensure_naive_utc(None) is None
    assert svc._ensure_naive_utc(now) == now


@pytest.mark.asyncio
async def test_get_retention_days_from_jurisdiction(monkeypatch):
    conn = FakeConn()
    conn.retention_row = {"retention_days": 365}

    _patch_db(monkeypatch, conn)

    result = await svc._get_retention_days("FNB", "ZA")

    assert result == 365
    assert "SELECT retention_days" in conn.queries[0][0]

    params = conn.queries[0][1]
    assert params[0] == "FNB"
    assert params[1] == "ZA"


@pytest.mark.asyncio
async def test_get_retention_days_uses_default_when_missing(monkeypatch):
    conn = FakeConn()
    conn.retention_row = None

    _patch_db(monkeypatch, conn)

    result = await svc._get_retention_days("FNB", "ZA")

    assert result == svc.DEFAULT_RETENTION_DAYS


@pytest.mark.asyncio
async def test_erase_referrer_by_ucn_success(monkeypatch):
    conn = FakeConn()

    async def fake_get_retention_days(tenant_code, jurisdiction_code=None):
        return 1825

    monkeypatch.setattr(svc, "_get_retention_days", fake_get_retention_days)
    _patch_db(monkeypatch, conn)

    result = await svc.erase_referrer_by_ucn(
        referrer_ucn="20260409",
        tenant_code="FNB",
        requested_by="admin",
        correlation_id="corr-123",
    )

    assert result["status"] == "erased"
    assert result["tenant_code"] == "FNB"
    assert result["requested_by"] == "admin"
    assert result["referrer_code_id"] == "ref-code-123"
    assert result["referral_instances_anonymised"] == 7
    assert result["referrer_codes_anonymised"] == 1
    assert result["correlation_id"] == "corr-123"

    executed_sql = "\n".join(q for q, _ in conn.queries)

    assert "SELECT referrer_code_id" in executed_sql
    assert "UPDATE referral_instances" in executed_sql
    assert "UPDATE referrer_codes" in executed_sql
    assert "INSERT INTO privacy_erasure_audit" in executed_sql


@pytest.mark.asyncio
async def test_erase_referrer_by_ucn_generates_correlation_id(monkeypatch):
    conn = FakeConn()

    async def fake_get_retention_days(tenant_code, jurisdiction_code=None):
        return 1825

    monkeypatch.setattr(svc, "_get_retention_days", fake_get_retention_days)
    _patch_db(monkeypatch, conn)

    result = await svc.erase_referrer_by_ucn(
        referrer_ucn="20260409",
        tenant_code="FNB",
    )

    assert result["status"] == "erased"
    assert result["correlation_id"] is not None


@pytest.mark.asyncio
async def test_erase_referrer_by_ucn_passes_jurisdiction_code(monkeypatch):
    conn = FakeConn()
    captured = {}

    async def fake_get_retention_days(tenant_code, jurisdiction_code=None):
        captured["tenant_code"] = tenant_code
        captured["jurisdiction_code"] = jurisdiction_code
        return 1825

    monkeypatch.setattr(svc, "_get_retention_days", fake_get_retention_days)
    _patch_db(monkeypatch, conn)

    result = await svc.erase_referrer_by_ucn(
        referrer_ucn="20260409",
        tenant_code="FNB",
        jurisdiction_code="ZA",
    )

    assert result["status"] == "erased"
    assert captured["tenant_code"] == "FNB"
    assert captured["jurisdiction_code"] == "ZA"


@pytest.mark.asyncio
async def test_erase_referrer_by_ucn_blocks_referee_request():
    result = await svc.erase_referrer_by_ucn(
        referrer_ucn="20260409",
        tenant_code="FNB",
        requested_by="referee",
    )

    assert result["status"] == "blocked"
    assert result["tenant_code"] == "FNB"
    assert "Referee-initiated" in result["message"]


@pytest.mark.asyncio
async def test_erase_referrer_by_ucn_not_found_writes_audit(monkeypatch):
    conn = FakeConn()
    conn.referrer_row = None

    async def fake_get_retention_days(tenant_code, jurisdiction_code=None):
        return 1825

    monkeypatch.setattr(svc, "_get_retention_days", fake_get_retention_days)
    _patch_db(monkeypatch, conn)

    result = await svc.erase_referrer_by_ucn(
        referrer_ucn="missing-ucn",
        tenant_code="FNB",
        requested_by="admin",
        correlation_id="corr-not-found",
    )

    assert result["status"] == "not_found"
    assert result["tenant_code"] == "FNB"
    assert result["requested_by"] == "admin"
    assert result["correlation_id"] == "corr-not-found"

    executed_sql = "\n".join(q for q, _ in conn.queries)

    assert "SELECT referrer_code_id" in executed_sql
    assert "INSERT INTO privacy_erasure_audit" in executed_sql
    assert "UPDATE referral_instances" not in executed_sql
    assert "UPDATE referrer_codes" not in executed_sql


@pytest.mark.asyncio
async def test_erase_referrer_by_ucn_blocks_when_inside_retention(monkeypatch):
    conn = FakeConn()
    conn.referrer_row = {
        "referrer_code_id": "ref-code-123",
        "created_at": datetime.utcnow(),
    }

    async def fake_get_retention_days(tenant_code, jurisdiction_code=None):
        return 1825

    monkeypatch.setattr(svc, "_get_retention_days", fake_get_retention_days)
    _patch_db(monkeypatch, conn)

    result = await svc.erase_referrer_by_ucn(
        referrer_ucn="20260409",
        tenant_code="FNB",
        requested_by="admin",
        correlation_id="corr-retention",
    )

    assert result["status"] == "blocked"
    assert result["tenant_code"] == "FNB"
    assert result["retention_days"] == 1825
    assert result["correlation_id"] == "corr-retention"
    assert "retention period" in result["message"]

    executed_sql = "\n".join(q for q, _ in conn.queries)

    assert "UPDATE referral_instances" not in executed_sql
    assert "UPDATE referrer_codes" not in executed_sql


@pytest.mark.asyncio
async def test_purge_expired_data(monkeypatch):
    conn = FakeConn()

    async def fake_get_retention_days(tenant_code, jurisdiction_code=None):
        return 1825

    monkeypatch.setattr(svc, "_get_retention_days", fake_get_retention_days)
    _patch_db(monkeypatch, conn)

    result = await svc.purge_expired_data("FNB")

    assert result["status"] == "purged"
    assert result["tenant_code"] == "FNB"
    assert result["retention_days"] == 1825
    assert result["deleted_referral_instances"] == 3
    assert result["deleted_referrer_codes"] == 2
    assert "cutoff_date" in result

    executed_sql = "\n".join(q for q, _ in conn.queries)

    assert "DELETE FROM referral_instances" in executed_sql
    assert "DELETE FROM referrer_codes" in executed_sql