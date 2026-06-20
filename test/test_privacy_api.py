from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi.testclient import TestClient

from apps.api.main import app
from utils.security import require_admin_key
import apps.api.routers.privacy as privacy_router


def _override_admin_key():
    return {
        "authenticated": True,
        "role": "ADMIN",
        "tenant": "INTERNAL",
        "tenant_code": "INTERNAL",
    }


def _client():
    app.dependency_overrides[require_admin_key] = _override_admin_key
    return TestClient(app, raise_server_exceptions=False)


def _cleanup():
    app.dependency_overrides.clear()


def _fake_erased_response(**kwargs):
    return {
        "status": "erased",
        "message": "ok",
        "tenant_code": kwargs["tenant_code"],
        "requested_by": kwargs.get("requested_by"),
        "referrer_code_id": "ref-code-123",
        "referral_instances_anonymised": 7,
        "referrer_codes_anonymised": 1,
        "correlation_id": kwargs.get("correlation_id"),
    }


class FakeConn:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows or []
        self.calls = []

    async def fetchrow(self, query, *params):
        self.calls.append(("fetchrow", query, params))
        return self.row

    async def fetch(self, query, *params):
        self.calls.append(("fetch", query, params))
        return self.rows


def patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(privacy_router, "db_connection", fake_db_connection)


def test_erase_referrer_success(monkeypatch):
    client = _client()

    async def fake_erase_referrer_by_ucn(*args, **kwargs):
        assert kwargs["referrer_ucn"] == "20260409"
        assert kwargs["tenant_code"] == "FNB"
        assert kwargs["requested_by"] == "tester"
        assert kwargs["correlation_id"] is not None
        assert kwargs.get("jurisdiction_code") is None
        return _fake_erased_response(**kwargs)

    monkeypatch.setattr(
        privacy_router,
        "erase_referrer_by_ucn",
        fake_erase_referrer_by_ucn,
    )

    response = client.delete(
        "/v1/privacy/referrers/20260409?tenant_code=FNB",
        headers={"x-api-key": "dev-admin-key-123", "x-requested-by": "tester"},
    )

    _cleanup()

    assert response.status_code == 200
    assert response.json()["status"] == "erased"


def test_erase_referrer_with_jurisdiction_code(monkeypatch):
    client = _client()

    async def fake_erase_referrer_by_ucn(*args, **kwargs):
        assert kwargs["jurisdiction_code"] == "ZA"
        return _fake_erased_response(**kwargs)

    monkeypatch.setattr(
        privacy_router,
        "erase_referrer_by_ucn",
        fake_erase_referrer_by_ucn,
    )

    response = client.delete(
        "/v1/privacy/referrers/20260409?tenant_code=FNB&jurisdiction_code=ZA",
        headers={"x-api-key": "dev-admin-key-123"},
    )

    _cleanup()

    assert response.status_code == 200
    assert response.json()["tenant_code"] == "FNB"


def test_erase_referrer_uses_default_tenant(monkeypatch):
    client = _client()

    async def fake_erase_referrer_by_ucn(*args, **kwargs):
        assert kwargs["tenant_code"] is not None
        return _fake_erased_response(**kwargs)

    monkeypatch.setattr(
        privacy_router,
        "erase_referrer_by_ucn",
        fake_erase_referrer_by_ucn,
    )

    response = client.delete(
        "/v1/privacy/referrers/20260409",
        headers={"x-api-key": "dev-admin-key-123"},
    )

    _cleanup()

    assert response.status_code == 200


def test_erase_referrer_not_found(monkeypatch):
    client = _client()

    async def fake_erase_referrer_by_ucn(*args, **kwargs):
        return {
            "status": "not_found",
            "tenant_code": kwargs["tenant_code"],
            "requested_by": kwargs.get("requested_by"),
            "correlation_id": kwargs.get("correlation_id"),
        }

    monkeypatch.setattr(
        privacy_router,
        "erase_referrer_by_ucn",
        fake_erase_referrer_by_ucn,
    )

    response = client.delete(
        "/v1/privacy/referrers/999999?tenant_code=FNB",
        headers={"x-api-key": "dev-admin-key-123"},
    )

    _cleanup()

    assert response.status_code == 404
    assert response.json()["detail"]["status"] == "not_found"


def test_erase_referrer_internal_error(monkeypatch):
    client = _client()

    async def fake_erase_referrer_by_ucn(*args, **kwargs):
        raise RuntimeError("database failed")

    monkeypatch.setattr(
        privacy_router,
        "erase_referrer_by_ucn",
        fake_erase_referrer_by_ucn,
    )

    response = client.delete(
        "/v1/privacy/referrers/20260409?tenant_code=FNB",
        headers={"x-api-key": "dev-admin-key-123"},
    )

    _cleanup()

    assert response.status_code == 500
    assert response.json()["detail"]["error"] == "INTERNAL_ERROR"


def test_run_privacy_purge_now(monkeypatch):
    client = _client()

    async def fake_run_privacy_purge():
        return {"status": "completed", "results": []}

    monkeypatch.setattr(
        privacy_router,
        "run_privacy_purge",
        fake_run_privacy_purge,
    )

    response = client.post(
        "/v1/privacy/purge/run",
        headers={"x-api-key": "dev-admin-key-123"},
    )

    _cleanup()

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_get_privacy_audit_by_correlation_id_success(monkeypatch):
    client = _client()

    conn = FakeConn(
        row={
            "audit_id": "audit-1",
            "correlation_id": "corr-123",
            "tenant_code": "FNB",
            "referrer_code_id": "ref-code-123",
            "requested_by": "admin",
            "status": "erased",
            "referral_instances_anonymised": 7,
            "referrer_codes_anonymised": 1,
            "created_at": "2026-05-05T22:27:30+00:00",
        }
    )
    patch_db(monkeypatch, conn)

    response = client.get(
        "/v1/privacy/audit/corr-123",
        headers={"x-api-key": "dev-admin-key-123"},
    )

    _cleanup()

    assert response.status_code == 200
    assert response.json()["status"] == "erased"
    assert conn.calls[0][2] == ("corr-123",)


def test_get_privacy_audit_by_correlation_id_not_found(monkeypatch):
    client = _client()

    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    response = client.get(
        "/v1/privacy/audit/missing-corr",
        headers={"x-api-key": "dev-admin-key-123"},
    )

    _cleanup()

    assert response.status_code == 404
    assert response.json()["detail"] == "Audit record not found"


def test_search_privacy_audit_no_filters(monkeypatch):
    client = _client()

    conn = FakeConn(
        rows=[
            {
                "audit_id": "audit-1",
                "correlation_id": "corr-1",
            }
        ]
    )
    patch_db(monkeypatch, conn)

    response = client.get(
        "/v1/privacy/audit",
        headers={"x-api-key": "dev-admin-key-123"},
    )

    _cleanup()

    assert response.status_code == 200
    assert response.json()[0]["correlation_id"] == "corr-1"
    assert conn.calls[0][2] == (50,)


def test_search_privacy_audit_with_all_filters(monkeypatch):
    client = _client()

    conn = FakeConn(
        rows=[
            {
                "audit_id": "audit-1",
                "correlation_id": "corr-1",
                "status": "erased",
            }
        ]
    )
    patch_db(monkeypatch, conn)

    response = client.get(
        "/v1/privacy/audit?tenant_code=FNB&requested_by=admin&status=erased&limit=25",
        headers={"x-api-key": "dev-admin-key-123"},
    )

    _cleanup()

    assert response.status_code == 200
    assert response.json()[0]["status"] == "erased"
    assert conn.calls[0][2] == ("FNB", "admin", "erased", 25)


def test_search_privacy_audit_limit_validation():
    client = _client()

    response = client.get(
        "/v1/privacy/audit?limit=0",
        headers={"x-api-key": "dev-admin-key-123"},
    )

    _cleanup()

    assert response.status_code == 422