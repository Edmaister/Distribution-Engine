from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.routers.campaigns as mod


class FakeTx:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self, row=None, fail=False):
        self.row = row
        self.fail = fail
        self.calls = []

    async def fetchrow(self, query, *params):
        if self.fail:
            raise RuntimeError("db broke")
        self.calls.append(("fetchrow", query, params))
        return self.row

    def transaction(self):
        return FakeTx()


def patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(mod, "db_connection", fake_db_connection)


@pytest.fixture
def app():
    test_app = FastAPI()
    test_app.include_router(mod.public_router)
    test_app.include_router(mod.router)

    test_app.dependency_overrides[mod.require_admin_key] = lambda: {
        "tenant_code": "FNB",
        "role": "admin",
    }
    test_app.dependency_overrides[mod.require_partner_key] = lambda: {
        "tenant_code": "FNB",
        "role": "partner",
    }

    return test_app


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


def create_payload(**overrides):
    payload = {
        "tenant_code": "FNB",
        "segment": "PERSONAL",
        "name": "Test Campaign",
        "campaign_code": "CAMP001",
        "starts_at": None,
        "ends_at": None,
        "max_uses": 100,
        "attributes": {"channel": "qr"},
    }
    payload.update(overrides)
    return payload


def validate_payload(**overrides):
    payload = {
        "tenant_code": "FNB",
        "campaign_code": "CAMP001",
        "user_ucn_encrypted": "encrypted-user",
        "device_fingerprint": "device-1",
        "ip_address": "127.0.0.1",
        "qr_payload": "payload",
        "source_channel": "QR",
        "metadata": {"source": "unit-test"},
    }
    payload.update(overrides)
    return payload


def track_payload(**overrides):
    payload = {"status": "VALIDATED"}
    payload.update(overrides)
    return payload


def policy_payload(**overrides):
    payload = {
        "tenant_code": "FNB",
        "version": 1,
        "is_active": True,
        "rolling_window_days": 30,
        "rules_json": {"max": 3},
        "product_windows_json": {"gold": 30},
        "reward_amounts_json": {"gold": 100},
        "product_rules_json": {"gold": {"allowed": True}},
    }
    payload.update(overrides)
    return payload


def test_correlation_id_known():
    request = type("Request", (), {})()
    request.state = type("State", (), {"correlation_id": "cid-123"})()

    assert mod._correlation_id(request) == "cid-123"


def test_correlation_id_unknown():
    request = type("Request", (), {})()
    request.state = type("State", (), {})()

    assert mod._correlation_id(request) == "unknown"


def test_error_response_shape():
    request = type("Request", (), {})()
    request.state = type("State", (), {"correlation_id": "cid-err"})()

    response = mod._error(request, 400, "VALIDATION_ERROR", "Bad request")

    assert response.status_code == 400
    assert response.headers["x-request-id"] == "cid-err"


def test_unwrap_tuple_result():
    body, status_code = mod._unwrap_service_result(({"ok": True}, 201))
    assert body == {"ok": True}
    assert status_code == 201


def test_unwrap_dict_result_with_status():
    body, status_code = mod._unwrap_service_result({"ok": True, "status": 202})
    assert body == {"ok": True, "status": 202}
    assert status_code == 202


def test_unwrap_dict_result_without_status():
    body, status_code = mod._unwrap_service_result({"ok": True})
    assert body == {"ok": True}
    assert status_code == 200


def test_unwrap_unexpected_type():
    body, status_code = mod._unwrap_service_result("bad")
    assert status_code == 500
    assert body["error_code"] == "INTERNAL_ERROR"


def test_create_campaign_success_campaign_code(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", lambda tenant: tenant)

    async def fake_create_campaign(**kwargs):
        return {
            "ok": True,
            "campaign_code": "CAMP001",
            "mode": "MIGRATED",
            "status": 201,
        }

    monkeypatch.setattr(mod, "create_campaign", fake_create_campaign)

    res = client.post("/campaigns", json=create_payload())

    assert res.status_code == 201
    assert res.json() == {"campaignCode": "CAMP001", "mode": "MIGRATED"}


def test_create_campaign_success_campaignCode_alias(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", lambda tenant: tenant)

    async def fake_create_campaign(**kwargs):
        return {
            "ok": True,
            "campaignCode": "CAMP002",
            "create_mode": "GENERATED",
            "status": 200,
        }

    monkeypatch.setattr(mod, "create_campaign", fake_create_campaign)

    res = client.post("/campaigns", json=create_payload(campaign_code="CAMP002"))

    assert res.status_code == 200
    assert res.json() == {"campaignCode": "CAMP002", "mode": "GENERATED"}


def test_create_campaign_success_nested_campaign_code(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", lambda tenant: tenant)

    async def fake_create_campaign(**kwargs):
        return {
            "ok": True,
            "campaign": {"campaign_code": "CAMP003"},
            "status": 201,
        }

    monkeypatch.setattr(mod, "create_campaign", fake_create_campaign)

    res = client.post("/campaigns", json=create_payload(campaign_code="CAMP003"))

    assert res.status_code == 201
    assert res.json()["campaignCode"] == "CAMP003"


def test_create_campaign_success_nested_campaignCode(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", lambda tenant: tenant)

    async def fake_create_campaign(**kwargs):
        return {
            "ok": True,
            "campaign": {"campaignCode": "CAMP004"},
            "status": 201,
        }

    monkeypatch.setattr(mod, "create_campaign", fake_create_campaign)

    res = client.post("/campaigns", json=create_payload(campaign_code="CAMP004"))

    assert res.status_code == 201
    assert res.json()["campaignCode"] == "CAMP004"


def test_create_campaign_service_error(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", lambda tenant: tenant)

    async def fake_create_campaign(**kwargs):
        return {
            "ok": False,
            "error_code": "VALIDATION_ERROR",
            "message": "Bad campaign",
        }, 422

    monkeypatch.setattr(mod, "create_campaign", fake_create_campaign)

    res = client.post("/campaigns", json=create_payload())

    assert res.status_code == 422
    assert res.json()["detail"]["error_code"] == "VALIDATION_ERROR"


def test_create_campaign_missing_campaign_code_returns_500(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", lambda tenant: tenant)

    async def fake_create_campaign(**kwargs):
        return {"ok": True}

    monkeypatch.setattr(mod, "create_campaign", fake_create_campaign)

    res = client.post("/campaigns", json=create_payload())

    assert res.status_code == 500
    assert res.json()["detail"]["error_code"] == "INTERNAL_ERROR"


def test_create_campaign_value_error(client, monkeypatch):
    monkeypatch.setattr(
        mod,
        "require_valid_tenant",
        lambda tenant: (_ for _ in ()).throw(ValueError("bad tenant")),
    )

    res = client.post("/campaigns", json=create_payload())

    assert res.status_code == 400
    assert res.json()["detail"]["error_code"] == "VALIDATION_ERROR"


def test_create_campaign_unexpected_error(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", lambda tenant: tenant)

    async def raise_error(**kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(mod, "create_campaign", raise_error)

    res = client.post("/campaigns", json=create_payload())

    assert res.status_code == 500
    assert res.json()["detail"]["error_code"] == "INTERNAL_ERROR"


def test_validate_campaign_success(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", lambda tenant: tenant)

    async def fake_validate(**kwargs):
        return {
            "valid": True,
            "reason": None,
            "campaignCode": "CAMP001",
            "campaignTrackId": "track-1",
        }, 200

    monkeypatch.setattr(mod, "validate_campaign_and_create_track", fake_validate)

    res = client.post("/campaigns/validate", json=validate_payload())

    assert res.status_code == 200
    assert res.json() == {
        "valid": True,
        "reason": None,
        "campaignCode": "CAMP001",
        "campaignTrackId": "track-1",
    }


def test_validate_campaign_invalid_campaign(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", lambda tenant: tenant)

    async def fake_validate(**kwargs):
        return {
            "valid": False,
            "reason": "Campaign code not found",
            "campaignCode": "BAD",
            "campaignTrackId": None,
        }, 200

    monkeypatch.setattr(mod, "validate_campaign_and_create_track", fake_validate)

    res = client.post("/campaigns/validate", json=validate_payload(campaign_code="BAD"))

    assert res.status_code == 200
    assert res.json()["valid"] is False
    assert res.json()["reason"] == "Campaign code not found"


def test_validate_campaign_service_error(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", lambda tenant: tenant)

    async def fake_validate(**kwargs):
        return {
            "ok": False,
            "error_code": "VALIDATION_ERROR",
            "message": "campaign_code is required",
        }, 422

    monkeypatch.setattr(mod, "validate_campaign_and_create_track", fake_validate)

    res = client.post("/campaigns/validate", json=validate_payload())

    assert res.status_code == 422
    assert res.json()["detail"]["error_code"] == "VALIDATION_ERROR"


def test_validate_campaign_value_error(client, monkeypatch):
    monkeypatch.setattr(
        mod,
        "require_valid_tenant",
        lambda tenant: (_ for _ in ()).throw(ValueError("bad tenant")),
    )

    res = client.post("/campaigns/validate", json=validate_payload())

    assert res.status_code == 400
    assert res.json()["detail"]["error_code"] == "VALIDATION_ERROR"


def test_validate_campaign_unexpected_error(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", lambda tenant: tenant)

    async def raise_error(**kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(mod, "validate_campaign_and_create_track", raise_error)

    res = client.post("/campaigns/validate", json=validate_payload())

    assert res.status_code == 500
    assert res.json()["detail"]["error_code"] == "INTERNAL_ERROR"


def test_update_campaign_track_success(client, monkeypatch):
    async def fake_update(**kwargs):
        return {
            "ok": True,
            "campaignTrackId": "track-1",
            "newStatus": "VALIDATED",
        }, 200

    monkeypatch.setattr(mod, "update_campaign_track_status", fake_update)

    res = client.patch("/campaigns/tracks/track-1", json=track_payload())

    assert res.status_code == 200
    assert res.json() == {
        "campaignTrackId": "track-1",
        "newStatus": "VALIDATED",
    }


def test_update_campaign_track_success_snake_case(client, monkeypatch):
    async def fake_update(**kwargs):
        return {
            "ok": True,
            "campaign_track_id": "track-2",
            "new_status": "COMPLETED",
        }, 200

    monkeypatch.setattr(mod, "update_campaign_track_status", fake_update)

    res = client.patch("/campaigns/tracks/track-2", json=track_payload(status="COMPLETED"))

    assert res.status_code == 200
    assert res.json()["campaignTrackId"] == "track-2"
    assert res.json()["newStatus"] == "COMPLETED"


def test_update_campaign_track_success_fallback_track_id_and_status(client, monkeypatch):
    async def fake_update(**kwargs):
        return {
            "ok": True,
            "status": "ATTRIBUTED",
        }, 200

    monkeypatch.setattr(mod, "update_campaign_track_status", fake_update)

    res = client.patch("/campaigns/tracks/track-3", json=track_payload(status="ATTRIBUTED"))

    assert res.status_code == 200
    assert res.json()["campaignTrackId"] == "track-3"
    assert res.json()["newStatus"] == "ATTRIBUTED"


def test_update_campaign_track_service_error_ok_false(client, monkeypatch):
    async def fake_update(**kwargs):
        return {
            "ok": False,
            "error_code": "BAD_STATUS",
            "message": "Bad status",
        }, 400

    monkeypatch.setattr(mod, "update_campaign_track_status", fake_update)

    res = client.patch("/campaigns/tracks/track-1", json=track_payload())

    assert res.status_code == 400
    assert res.json()["detail"]["error_code"] == "BAD_STATUS"


def test_update_campaign_track_service_error_code_only(client, monkeypatch):
    async def fake_update(**kwargs):
        return {
            "error_code": "NOT_FOUND",
            "message": "Missing",
        }, 404

    monkeypatch.setattr(mod, "update_campaign_track_status", fake_update)

    res = client.patch("/campaigns/tracks/track-1", json=track_payload())

    assert res.status_code == 404
    assert res.json()["detail"]["error_code"] == "NOT_FOUND"


def test_update_campaign_track_missing_new_status_returns_500(client, monkeypatch):
    async def fake_update(**kwargs):
        return {"ok": True}, 200

    monkeypatch.setattr(mod, "update_campaign_track_status", fake_update)

    res = client.patch("/campaigns/tracks/track-1", json=track_payload())

    assert res.status_code == 500
    assert res.json()["detail"]["error_code"] == "INTERNAL_ERROR"


def test_update_campaign_track_value_error(client, monkeypatch):
    async def raise_value_error(**kwargs):
        raise ValueError("bad status")

    monkeypatch.setattr(mod, "update_campaign_track_status", raise_value_error)

    res = client.patch("/campaigns/tracks/track-1", json=track_payload())

    assert res.status_code == 400
    assert res.json()["detail"]["error_code"] == "VALIDATION_ERROR"


def test_update_campaign_track_unexpected_error(client, monkeypatch):
    async def raise_error(**kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(mod, "update_campaign_track_status", raise_error)

    res = client.patch("/campaigns/tracks/track-1", json=track_payload())

    assert res.status_code == 500
    assert res.json()["detail"]["error_code"] == "INTERNAL_ERROR"


def test_get_campaign_policy_success(client, monkeypatch):
    async def fake_policy(tenant, campaign_code):
        return {
            "tenant": tenant,
            "campaign_code": campaign_code,
            "policy": {"ok": True},
        }

    monkeypatch.setattr(mod, "get_effective_policy", fake_policy)

    res = client.get("/campaigns/CAMP001/policy")

    assert res.status_code == 200
    assert res.json()["tenant"] == "FNB"
    assert res.json()["campaign_code"] == "CAMP001"


def test_get_campaign_policy_value_error(client, monkeypatch):
    async def raise_value_error(**kwargs):
        raise ValueError("bad policy")

    monkeypatch.setattr(mod, "get_effective_policy", raise_value_error)

    res = client.get("/campaigns/CAMP001/policy")

    assert res.status_code == 400
    assert res.json()["detail"]["error_code"] == "VALIDATION_ERROR"


def test_get_campaign_policy_unexpected_error(client, monkeypatch):
    async def raise_error(**kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(mod, "get_effective_policy", raise_error)

    res = client.get("/campaigns/CAMP001/policy")

    assert res.status_code == 500
    assert res.json()["detail"]["error_code"] == "INTERNAL_ERROR"


def test_upsert_campaign_policy_success_with_all_json_fields(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", lambda tenant: tenant)

    returned_at = datetime(2026, 5, 4, 10, 30, 0)
    row = {
        "campaign_code": "CAMP001",
        "tenant_code": "FNB",
        "version": 1,
        "is_active": True,
        "rolling_window_days": 30,
        "rules_json": {"max": 3},
        "product_windows_json": {"gold": 30},
        "reward_amounts_json": {"gold": 100},
        "product_rules_json": {"gold": {"allowed": True}},
        "updated_at": returned_at,
    }
    conn = FakeConn(row=row)
    patch_db(monkeypatch, conn)

    res = client.put("/campaigns/CAMP001/policy", json=policy_payload())

    assert res.status_code == 200
    body = res.json()
    assert body["campaign_code"] == "CAMP001"
    assert body["tenant_code"] == "FNB"
    assert body["updated_at"] == returned_at.isoformat()
    assert conn.calls[0][2][0] == "CAMP001"
    assert conn.calls[0][2][1] == "FNB"


def test_upsert_campaign_policy_success_with_null_date(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", lambda tenant: tenant)

    row = {
        "campaign_code": "CAMP002",
        "tenant_code": "FNB",
        "version": 2,
        "is_active": False,
        "rolling_window_days": None,
        "rules_json": [],
        "product_windows_json": {},
        "reward_amounts_json": {},
        "product_rules_json": {},
        "updated_at": None,
    }
    conn = FakeConn(row=row)
    patch_db(monkeypatch, conn)

    res = client.put(
        "/campaigns/CAMP002/policy",
        json=policy_payload(
            version=2,
            is_active=False,
            rolling_window_days=None,
            rules_json=None,
            product_windows_json=None,
            reward_amounts_json=None,
            product_rules_json=None,
        ),
    )

    assert res.status_code == 200
    body = res.json()
    assert body["updated_at"] is None
    assert body["rules_json"] == []


def test_upsert_campaign_policy_tuple_row_fallback(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", lambda tenant: tenant)

    returned_at = datetime(2026, 5, 4, 10, 30, 0)
    row = (
        "CAMP003",
        "FNB",
        3,
        True,
        45,
        {"max": 5},
        {"gold": 45},
        {"gold": 200},
        {"gold": {"allowed": False}},
        returned_at,
    )
    conn = FakeConn(row=row)
    patch_db(monkeypatch, conn)

    res = client.put(
        "/campaigns/CAMP003/policy",
        json=policy_payload(version=3, rolling_window_days=45),
    )

    assert res.status_code == 200
    body = res.json()
    assert body["campaign_code"] == "CAMP003"
    assert body["version"] == 3
    assert body["updated_at"] == returned_at.isoformat()


def test_upsert_campaign_policy_value_error(client, monkeypatch):
    monkeypatch.setattr(
        mod,
        "require_valid_tenant",
        lambda tenant: (_ for _ in ()).throw(ValueError("bad tenant")),
    )

    res = client.put("/campaigns/CAMP001/policy", json=policy_payload())

    assert res.status_code == 400
    assert res.json()["detail"]["error_code"] == "VALIDATION_ERROR"


def test_upsert_campaign_policy_unexpected_error(client, monkeypatch):
    monkeypatch.setattr(mod, "require_valid_tenant", lambda tenant: tenant)

    conn = FakeConn(fail=True)
    patch_db(monkeypatch, conn)

    res = client.put("/campaigns/CAMP001/policy", json=policy_payload())

    assert res.status_code == 500
    assert res.json()["detail"]["error_code"] == "INTERNAL_ERROR"