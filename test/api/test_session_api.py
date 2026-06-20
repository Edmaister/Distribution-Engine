from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.routers.session import router
from utils import security


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_session_returns_admin_identity():
    response = _client().get("/auth/session", headers={"x-api-key": "test-admin-key"})

    assert response.status_code == 200
    assert response.json()["session"] == {
        "authenticated": True,
        "role": "ADMIN",
        "tenant_code": "INTERNAL",
        "tenant": "INTERNAL",
        "auth_source": "api_key",
    }
    assert response.json()["recommended_workspace"]["code"] == "admin"
    assert _workspace(response.json(), "admin")["access"] == "allowed"
    assert (
        _workspace(response.json(), "admin")["summary"]
        == "Platform command centre for operators."
    )
    assert (
        _workspace(response.json(), "admin")["guidance"]
        == "This session can use Amplifi Admin."
    )
    assert _workspace(response.json(), "admin_distribution")["access"] == "allowed"
    assert _workspace(response.json(), "admin_billing")["access"] == "allowed"
    assert _workspace(response.json(), "admin_health")["access"] == "allowed"
    assert _workspace(response.json(), "producer_supply")["access"] == "allowed"
    assert {workspace["path"] for workspace in response.json()["workspaces"]} == {
        "/admin",
        "/admin/events",
        "/admin/distribution",
        "/admin/billing",
        "/admin/multi-currency",
        "/admin/settlements",
        "/admin/audit",
        "/admin/health",
        "/partner",
        "/sponsor",
        "/distributor",
        "/consumer",
    }


def test_session_returns_finance_admin_workspace_access():
    response = _client().get(
        "/auth/session", headers={"x-api-key": "test-finance-admin-key"}
    )

    assert response.status_code == 200
    assert response.json()["session"]["role"] == "FINANCE_ADMIN"
    assert response.json()["recommended_workspace"]["code"] == "admin_billing"
    assert _workspace(response.json(), "admin_billing")["access"] == "allowed"
    assert _workspace(response.json(), "admin_billing")["guidance"] == (
        "This finance admin session can operate Funding Spine."
    )
    assert _workspace(response.json(), "admin_multi_currency")["access"] == "allowed"
    assert _workspace(response.json(), "admin_settlements")["access"] == "allowed"
    assert _workspace(response.json(), "admin_distribution")["access"] == "blocked"
    assert _workspace(response.json(), "producer_supply")["access"] == "blocked"


def test_session_returns_distribution_admin_workspace_access():
    response = _client().get(
        "/auth/session", headers={"x-api-key": "test-distribution-admin-key"}
    )

    assert response.status_code == 200
    assert response.json()["session"]["role"] == "DISTRIBUTION_ADMIN"
    assert response.json()["recommended_workspace"]["code"] == "admin_distribution"
    assert _workspace(response.json(), "admin_distribution")["access"] == "allowed"
    assert _workspace(response.json(), "admin_distribution")["guidance"] == (
        "This distribution admin session can operate Demand Marketplace."
    )
    assert _workspace(response.json(), "admin_billing")["access"] == "blocked"
    assert _workspace(response.json(), "distributor_demand")["access"] == "blocked"


def test_session_returns_system_admin_workspace_access():
    response = _client().get(
        "/auth/session", headers={"x-api-key": "test-system-admin-key"}
    )

    assert response.status_code == 200
    assert response.json()["session"]["role"] == "SYSTEM_ADMIN"
    assert response.json()["recommended_workspace"]["code"] == "admin_health"
    assert _workspace(response.json(), "admin_events")["access"] == "allowed"
    assert _workspace(response.json(), "admin_health")["access"] == "allowed"
    assert _workspace(response.json(), "admin_health")["guidance"] == (
        "This system admin session can operate Runtime Health."
    )
    assert _workspace(response.json(), "admin_billing")["access"] == "blocked"
    assert _workspace(response.json(), "consumer_journey")["access"] == "blocked"


def test_session_returns_producer_identity():
    response = _client().get(
        "/auth/session", headers={"x-api-key": "test-fnb-producer-insureco-key"}
    )

    assert response.status_code == 200
    assert response.json()["session"]["role"] == "PRODUCER"
    assert response.json()["session"]["tenant_code"] == "FNB"
    assert response.json()["session"]["producer_code"] == "INSURECO"
    assert response.json()["recommended_workspace"]["code"] == "producer_supply"
    producer_workspace = _workspace(response.json(), "producer_supply")
    assert producer_workspace["access"] == "allowed"
    assert producer_workspace["scope"]["producer_code"] == "INSURECO"
    assert producer_workspace["guidance"] == (
        "This session is scoped to the producer shown in the workspace identity."
    )
    assert _workspace(response.json(), "distributor_demand")["access"] == "blocked"
    assert _workspace(response.json(), "distributor_demand")["guidance"] == (
        "Switch to Distributor - Demand, FNB Partner, or Amplifi Admin."
    )
    assert _workspace(response.json(), "admin")["access"] == "blocked"
    assert _workspace(response.json(), "admin")["guidance"] == (
        "Switch to an Amplifi Admin session for platform operations."
    )
    assert _workspace(response.json(), "admin_distribution")["access"] == "blocked"
    assert _workspace(response.json(), "admin_billing")["access"] == "blocked"


def test_session_returns_distributor_identity():
    response = _client().get(
        "/auth/session",
        headers={"x-api-key": "test-fnb-distributor-insurance-advocate-key"},
    )

    assert response.status_code == 200
    assert response.json()["session"]["role"] == "DISTRIBUTOR"
    assert response.json()["session"]["tenant_code"] == "FNB"
    assert response.json()["session"]["distributor_code"] == "DIST-INSURANCE-ADVOCATE"
    assert response.json()["recommended_workspace"]["code"] == "distributor_demand"
    distributor_workspace = _workspace(response.json(), "distributor_demand")
    assert distributor_workspace["access"] == "allowed"
    assert (
        distributor_workspace["scope"]["distributor_code"] == "DIST-INSURANCE-ADVOCATE"
    )
    assert distributor_workspace["guidance"] == (
        "This session is scoped to the distributor shown in the workspace identity."
    )
    assert _workspace(response.json(), "producer_supply")["access"] == "blocked"


def test_session_returns_consumer_identity():
    response = _client().get(
        "/auth/session", headers={"x-api-key": "test-fnb-consumer-key"}
    )

    assert response.status_code == 200
    assert response.json()["session"]["role"] == "CONSUMER"
    assert response.json()["session"]["tenant_code"] == "FNB"
    assert response.json()["recommended_workspace"]["code"] == "consumer_journey"
    assert _workspace(response.json(), "consumer_journey")["access"] == "allowed"
    assert _workspace(response.json(), "consumer_journey")["guidance"] == (
        "This session can continue the customer conversion journey."
    )
    assert _workspace(response.json(), "producer_supply")["access"] == "blocked"


def test_session_returns_partner_identity():
    response = _client().get("/auth/session", headers={"x-api-key": "test-fnb-key"})

    assert response.status_code == 200
    assert response.json()["session"]["role"] == "PARTNER"
    assert response.json()["session"]["tenant_code"] == "FNB"
    assert response.json()["recommended_workspace"]["code"] == "partner_integration"
    assert _workspace(response.json(), "partner_integration")["access"] == "allowed"
    assert _workspace(response.json(), "partner_integration")["guidance"] == (
        "This partner session can review integration health for its tenant."
    )
    assert _workspace(response.json(), "producer_supply")["access"] == "allowed"
    assert _workspace(response.json(), "producer_supply")["guidance"] == (
        "This partner session can review and operate Producer - Supply for its tenant."
    )
    assert _workspace(response.json(), "distributor_demand")["access"] == "allowed"
    assert _workspace(response.json(), "consumer_journey")["access"] == "allowed"
    assert _workspace(response.json(), "admin")["access"] == "blocked"
    assert _workspace(response.json(), "admin_settlements")["access"] == "blocked"


def test_session_accepts_jwt_producer_claims(monkeypatch):
    monkeypatch.setattr(
        security,
        "get_settings",
        lambda: SimpleNamespace(
            auth_jwt_secret="jwt-secret",
            auth_jwt_issuer="amplifi-test",
            auth_jwt_audience="referral-engine",
            app_env="test",
        ),
    )
    token = _jwt(
        {
            "sub": "producer-user-1",
            "role": "PRODUCER",
            "tenant_code": "FNB",
            "producer_code": "INSURECO",
            "iss": "amplifi-test",
            "aud": "referral-engine",
            "exp": int(time.time()) + 300,
        }
    )

    response = _client().get(
        "/auth/session", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["session"]["role"] == "PRODUCER"
    assert response.json()["session"]["auth_source"] == "jwt"
    assert response.json()["session"]["subject"] == "producer-user-1"
    assert response.json()["session"]["producer_code"] == "INSURECO"
    assert response.json()["recommended_workspace"]["code"] == "producer_supply"


def test_session_accepts_configured_jwt_claim_names(monkeypatch):
    monkeypatch.setattr(
        security,
        "get_settings",
        lambda: SimpleNamespace(
            auth_jwt_secret="jwt-secret",
            auth_jwt_issuer="bank-idp",
            auth_jwt_audience="referral-engine",
            auth_jwt_role_claims="app_role",
            auth_jwt_tenant_claims="tenant_id",
            auth_jwt_subject_claims="user_id",
            auth_jwt_producer_claims="producer_id",
            auth_jwt_distributor_claims="distributor_id",
            auth_jwt_client_claims="azp",
            auth_jwt_scope_claims="permissions",
            app_env="test",
        ),
    )
    token = _jwt(
        {
            "user_id": "producer-user-2",
            "app_role": "PRODUCER",
            "tenant_id": "FNB",
            "producer_id": "INSURECO",
            "azp": "bank-portal",
            "permissions": ["producer:supply"],
            "iss": "bank-idp",
            "aud": "referral-engine",
            "exp": int(time.time()) + 300,
        }
    )

    response = _client().get(
        "/auth/session", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["session"]["role"] == "PRODUCER"
    assert response.json()["session"]["auth_source"] == "jwt"
    assert response.json()["session"]["subject"] == "producer-user-2"
    assert response.json()["session"]["producer_code"] == "INSURECO"
    assert response.json()["recommended_workspace"]["code"] == "producer_supply"


def test_session_rejects_jwt_wrong_audience(monkeypatch):
    monkeypatch.setattr(
        security,
        "get_settings",
        lambda: SimpleNamespace(
            auth_jwt_secret="jwt-secret",
            auth_jwt_issuer="amplifi-test",
            auth_jwt_audience="referral-engine",
            app_env="test",
        ),
    )
    token = _jwt(
        {
            "sub": "admin-user-1",
            "role": "ADMIN",
            "tenant_code": "INTERNAL",
            "iss": "amplifi-test",
            "aud": "wrong",
            "exp": int(time.time()) + 300,
        }
    )

    response = _client().get(
        "/auth/session", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401


def test_session_rejects_missing_key():
    response = _client().get("/auth/session")

    assert response.status_code == 401


def test_session_rejects_unknown_key():
    response = _client().get("/auth/session", headers={"x-api-key": "unknown"})

    assert response.status_code == 401


def _workspace(payload: dict, code: str) -> dict:
    return next(item for item in payload["workspaces"] if item["code"] == code)


def _jwt(payload: dict, secret: str = "jwt-secret") -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_part = _b64(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _b64(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(
        secret.encode("utf-8"),
        f"{header_part}.{payload_part}".encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{header_part}.{payload_part}.{_b64(signature)}"


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
