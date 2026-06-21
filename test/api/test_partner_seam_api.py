from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.routers import partner_seam


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(partner_seam.router)
    app.include_router(partner_seam.admin_router)
    return TestClient(app)


def test_oauth_token_issues_client_credentials_token(monkeypatch):
    async def fake_issue_client_credentials_token(**kwargs):
        assert kwargs == {
            "client_id": "client-1",
            "client_secret": "secret",
            "scope": "events:write referrals:read",
        }
        return {
            "access_token": "token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "events:write referrals:read",
            "tenant_code": "FNB",
        }

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "issue_client_credentials_token",
        fake_issue_client_credentials_token,
    )

    response = _client().post(
        "/oauth/token",
        json={
            "grant_type": "client_credentials",
            "client_id": "client-1",
            "client_secret": "secret",
            "scope": "events:write referrals:read",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "Bearer"
    assert response.json()["tenant_code"] == "FNB"


def test_oauth_token_rejects_unsupported_grant_type():
    response = _client().post(
        "/oauth/token",
        json={
            "grant_type": "password",
            "client_id": "client-1",
            "client_secret": "secret",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"] == "Only client_credentials grant_type is supported"
    )


def test_partner_me_returns_bearer_identity(monkeypatch):
    async def fake_authenticate_partner_access_token(authorization):
        assert authorization == "Bearer token"
        return {
            "authenticated": True,
            "role": "PARTNER",
            "tenant_code": "FNB",
            "tenant": "FNB",
            "client_id": "client-1",
            "scopes": ["events:write"],
        }

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "authenticate_partner_access_token",
        fake_authenticate_partner_access_token,
    )

    response = _client().get("/partner/me", headers={"Authorization": "Bearer token"})

    assert response.status_code == 200
    assert response.json()["identity"]["client_id"] == "client-1"
    assert response.json()["identity"]["role"] == "PARTNER"


def test_partner_integration_returns_partner_scoped_overview(monkeypatch):
    async def fake_get_partner_integration_overview(identity):
        assert identity["role"] == "PARTNER"
        assert identity["tenant_code"] == "FNB"
        return {
            "identity": {"tenant_code": "FNB", "role": "PARTNER"},
            "clients": [],
            "webhooks": [],
            "deliveries": [],
            "summary": {
                "status": "HEALTHY",
                "sent_count": 0,
                "pending_count": 0,
                "failed_count": 0,
            },
            "guardrails": ["No secrets are shown."],
        }

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "get_partner_integration_overview",
        fake_get_partner_integration_overview,
    )

    response = _client().get(
        "/partner/integration",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 200
    assert response.json()["integration"]["identity"]["tenant_code"] == "FNB"
    assert response.json()["integration"]["summary"]["status"] == "HEALTHY"


def test_partner_can_self_onboard_client_for_own_tenant(monkeypatch):
    async def fake_create_partner_client_for_identity(**kwargs):
        assert kwargs["identity"]["tenant_code"] == "FNB"
        assert kwargs["client_name"] == "Claims Integration"
        assert kwargs["scopes"] == ["events:write"]
        return {
            "client_id": "fnb_client",
            "tenant_code": "FNB",
            "client_name": "Claims Integration",
            "scopes": ["events:write"],
            "status": "ACTIVE",
            "client_secret": "secret",
        }

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "create_partner_client_for_identity",
        fake_create_partner_client_for_identity,
    )

    response = _client().post(
        "/partner/clients",
        headers={"x-api-key": "test-partner-key"},
        json={
            "tenant_code": "PNP",
            "client_name": "Claims Integration",
            "scopes": ["events:write"],
        },
    )

    assert response.status_code == 200
    assert response.json()["client"]["tenant_code"] == "FNB"
    assert response.json()["client"]["client_secret"] == "secret"
    assert "only returned once" in response.json()["guardrail"]


def test_partner_can_create_client_scoped_webhook(monkeypatch):
    async def fake_authenticate_partner_access_token(authorization):
        assert authorization == "Bearer token"
        return {
            "authenticated": True,
            "role": "PARTNER",
            "tenant_code": "FNB",
            "tenant": "FNB",
            "client_id": "client-1",
            "scopes": ["events:write"],
        }

    async def fake_create_partner_webhook_subscription(**kwargs):
        assert kwargs["identity"]["client_id"] == "client-1"
        assert kwargs["event_type"] == "OUTCOME_COMPLETED"
        assert kwargs["target_url"] == "https://partner.example/webhooks"
        return {
            "webhook_id": "webhook-1",
            "client_id": "client-1",
            "tenant_code": "FNB",
            "event_type": "OUTCOME_COMPLETED",
            "target_url": "https://partner.example/webhooks",
            "status": "ACTIVE",
            "signing_secret": "secret",
        }

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "authenticate_partner_access_token",
        fake_authenticate_partner_access_token,
    )
    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "create_partner_webhook_subscription",
        fake_create_partner_webhook_subscription,
    )

    response = _client().post(
        "/partner/webhooks",
        headers={"Authorization": "Bearer token"},
        json={
            "event_type": "OUTCOME_COMPLETED",
            "target_url": "https://partner.example/webhooks",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "created"
    assert response.json()["webhook"]["signing_secret"] == "secret"
    assert "only returned once" in response.json()["guardrail"]


def test_partner_can_rotate_client_scoped_webhook_secret(monkeypatch):
    async def fake_authenticate_partner_access_token(authorization):
        assert authorization == "Bearer token"
        return {
            "authenticated": True,
            "role": "PARTNER",
            "tenant_code": "FNB",
            "tenant": "FNB",
            "client_id": "client-1",
            "scopes": ["events:write"],
        }

    async def fake_rotate_partner_webhook_signing_secret(**kwargs):
        assert kwargs["identity"]["client_id"] == "client-1"
        assert kwargs["webhook_id"] == "webhook-1"
        return {
            "webhook_id": "webhook-1",
            "client_id": "client-1",
            "tenant_code": "FNB",
            "event_type": "OUTCOME_COMPLETED",
            "target_url": "https://partner.example/webhooks",
            "status": "ACTIVE",
            "signing_secret": "new-secret",
        }

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "authenticate_partner_access_token",
        fake_authenticate_partner_access_token,
    )
    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "rotate_partner_webhook_signing_secret",
        fake_rotate_partner_webhook_signing_secret,
    )

    response = _client().post(
        "/partner/webhooks/webhook-1/rotate-secret",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rotated"
    assert response.json()["webhook"]["signing_secret"] == "new-secret"
    assert "Replace the old endpoint secret" in response.json()["guardrail"]


def test_partner_can_rotate_legacy_webhook_secrets(monkeypatch):
    async def fake_rotate_partner_legacy_webhook_secrets(**kwargs):
        assert kwargs["identity"]["tenant_code"] == "FNB"
        assert kwargs["limit"] == 10
        return {
            "status": "rotated",
            "tenant_code": "FNB",
            "client_id": None,
            "rotated_count": 1,
            "items": [
                {
                    "webhook_id": "webhook-1",
                    "client_id": "client-1",
                    "tenant_code": "FNB",
                    "event_type": "OUTCOME_COMPLETED",
                    "signing_secret": "new-secret",
                }
            ],
            "guardrail": "Store returned signing_secret values securely. They are only returned once.",
        }

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "rotate_partner_legacy_webhook_secrets",
        fake_rotate_partner_legacy_webhook_secrets,
    )

    response = _client().post(
        "/partner/webhooks/rotate-legacy-secrets?limit=10",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rotated"
    assert response.json()["rotated_count"] == 1
    assert response.json()["items"][0]["signing_secret"] == "new-secret"
    assert "only returned once" in response.json()["guardrail"]


def test_partner_can_read_webhook_exceptions(monkeypatch):
    async def fake_get_exceptions(**kwargs):
        assert kwargs["identity"]["tenant_code"] == "FNB"
        assert kwargs["limit"] == 10
        return [
            {
                "delivery_id": "delivery-1",
                "client_id": "client-1",
                "tenant_code": "FNB",
                "delivery_status": "FAILED",
            }
        ]

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "list_partner_webhook_exceptions",
        fake_get_exceptions,
    )

    response = _client().get(
        "/partner/webhook-deliveries/exceptions?limit=10",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["items"][0]["delivery_status"] == "FAILED"


def test_partner_can_export_webhook_dead_letters(monkeypatch):
    async def fake_export_partner_webhook_dead_letters(**kwargs):
        assert kwargs["identity"]["tenant_code"] == "FNB"
        assert kwargs["limit"] == 25
        return {
            "filename": "partner-webhook-dead-letters-fnb.csv",
            "content_type": "text/csv",
            "count": 1,
            "csv": "delivery_id,delivery_status\r\ndelivery-1,FAILED\r\n",
            "guardrail": "Export contains failed and cancelled webhook delivery evidence only.",
        }

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "export_partner_webhook_dead_letters",
        fake_export_partner_webhook_dead_letters,
    )

    response = _client().get(
        "/partner/webhook-deliveries/dead-letter-export?limit=25",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 200
    assert response.json()["export"]["count"] == 1
    assert response.json()["export"]["content_type"] == "text/csv"
    assert "delivery_status" in response.json()["export"]["csv"]


def test_partner_can_read_webhook_alerts(monkeypatch):
    async def fake_get_partner_webhook_delivery_alerts(**kwargs):
        assert kwargs["identity"]["tenant_code"] == "FNB"
        assert kwargs["limit"] == 10
        return [
            {
                "client_id": "client-1",
                "webhook_id": "webhook-1",
                "event_type": "OUTCOME_COMPLETED",
                "failed_count": 5,
                "severity": "CRITICAL",
                "recommended_action": "Fix the endpoint, then retry failed deliveries.",
            }
        ]

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "get_partner_webhook_delivery_alerts",
        fake_get_partner_webhook_delivery_alerts,
    )

    response = _client().get(
        "/partner/webhook-deliveries/alerts?limit=10",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["items"][0]["severity"] == "CRITICAL"
    assert "failed and cancelled" in response.json()["guardrail"]


def test_partner_can_read_webhook_secret_readiness(monkeypatch):
    async def fake_get_partner_webhook_secret_readiness(identity):
        assert identity["tenant_code"] == "FNB"
        return {
            "status": "ATTENTION",
            "tenant_code": "FNB",
            "client_id": None,
            "protection_mode": "APPLICATION_KEY",
            "config_status": "READY",
            "rotation_status": "ATTENTION",
            "total_subscriptions": 3,
            "protected_subscriptions": 2,
            "legacy_plaintext_subscriptions": 1,
            "recommended_action": "Rotate legacy webhook signing secrets.",
        }

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "get_partner_webhook_secret_readiness",
        fake_get_partner_webhook_secret_readiness,
    )

    response = _client().get(
        "/partner/webhooks/secret-readiness",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 200
    assert response.json()["readiness"]["status"] == "ATTENTION"
    assert response.json()["readiness"]["legacy_plaintext_subscriptions"] == 1
    assert "Secret readiness reports" in response.json()["guardrail"]


def test_partner_can_read_production_readiness(monkeypatch):
    def fake_get_partner_seam_production_readiness():
        return {
            "code_status": "READY",
            "deployment_status": "READY",
            "code_complete": True,
            "checks": [],
        }

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "get_partner_seam_production_readiness",
        fake_get_partner_seam_production_readiness,
    )

    response = _client().get(
        "/partner/readiness",
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 200
    assert response.json()["readiness"]["code_status"] == "READY"
    assert response.json()["readiness"]["code_complete"] is True


def test_partner_can_retry_own_webhook_delivery(monkeypatch):
    async def fake_authenticate_partner_access_token(authorization):
        assert authorization == "Bearer token"
        return {
            "authenticated": True,
            "role": "PARTNER",
            "tenant_code": "FNB",
            "tenant": "FNB",
            "client_id": "client-1",
            "scopes": ["events:write"],
        }

    async def fake_mark_partner_webhook_delivery_for_retry(**kwargs):
        assert kwargs["identity"]["client_id"] == "client-1"
        assert kwargs["delivery_id"] == "delivery-1"
        return {
            "delivery_id": "delivery-1",
            "client_id": "client-1",
            "tenant_code": "FNB",
            "delivery_status": "PENDING",
        }

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "authenticate_partner_access_token",
        fake_authenticate_partner_access_token,
    )
    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "mark_partner_webhook_delivery_for_retry",
        fake_mark_partner_webhook_delivery_for_retry,
    )

    response = _client().post(
        "/partner/webhook-deliveries/delivery-1/retry",
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert response.json()["delivery"]["delivery_status"] == "PENDING"


def test_system_admin_can_create_partner_client(monkeypatch):
    async def fake_create_partner_client(**kwargs):
        assert kwargs["tenant_code"] == "FNB"
        assert kwargs["client_name"] == "External Producer"
        assert kwargs["scopes"] == ["events:write"]
        return {
            "client_id": "client-1",
            "tenant_code": "FNB",
            "client_name": "External Producer",
            "scopes": ["events:write"],
            "status": "ACTIVE",
            "client_secret": "secret",
        }

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "create_partner_client",
        fake_create_partner_client,
    )

    response = _client().post(
        "/admin/partners/clients",
        headers={"x-api-key": "test-system-admin-key"},
        json={
            "tenant_code": "FNB",
            "client_name": "External Producer",
            "scopes": ["events:write"],
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "created"
    assert response.json()["client"]["client_secret"] == "secret"
    assert "only returned once" in response.json()["guardrail"]


def test_partner_admin_routes_require_system_admin_key():
    response = _client().post(
        "/admin/partners/clients",
        headers={"x-api-key": "test-finance-admin-key"},
        json={
            "tenant_code": "FNB",
            "client_name": "External Producer",
            "scopes": ["events:write"],
        },
    )

    assert response.status_code == 403


def test_system_admin_can_create_https_webhook(monkeypatch):
    async def fake_create_webhook_subscription(**kwargs):
        assert kwargs["client_id"] == "client-1"
        assert kwargs["event_type"] == "OUTCOME_COMPLETED"
        assert kwargs["target_url"] == "https://partner.example/webhooks"
        return {
            "webhook_id": "webhook-1",
            "client_id": "client-1",
            "tenant_code": "FNB",
            "event_type": "OUTCOME_COMPLETED",
            "target_url": "https://partner.example/webhooks",
            "status": "ACTIVE",
            "signing_secret": "secret",
        }

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "create_webhook_subscription",
        fake_create_webhook_subscription,
    )

    response = _client().post(
        "/admin/partners/clients/client-1/webhooks",
        headers={"x-api-key": "test-system-admin-key"},
        json={
            "event_type": "OUTCOME_COMPLETED",
            "target_url": "https://partner.example/webhooks",
        },
    )

    assert response.status_code == 200
    assert response.json()["webhook"]["signing_secret"] == "secret"


def test_webhook_rejects_non_https_url():
    response = _client().post(
        "/admin/partners/clients/client-1/webhooks",
        headers={"x-api-key": "test-system-admin-key"},
        json={
            "event_type": "OUTCOME_COMPLETED",
            "target_url": "http://partner.example/webhooks",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "target_url must use https"


def test_system_admin_can_process_webhook_deliveries(monkeypatch):
    async def fake_process_pending_webhook_deliveries(**kwargs):
        assert kwargs == {"limit": 10}
        return {
            "status": "processed",
            "processed_count": 1,
            "sent_count": 1,
            "pending_count": 0,
            "failed_count": 0,
            "items": [{"delivery_id": "delivery-1", "delivery_status": "SENT"}],
        }

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "process_pending_webhook_deliveries",
        fake_process_pending_webhook_deliveries,
    )

    response = _client().post(
        "/admin/partners/webhook-deliveries/process?limit=10",
        headers={"x-api-key": "test-system-admin-key"},
    )

    assert response.status_code == 200
    assert response.json()["sent_count"] == 1


def test_system_admin_can_read_webhook_delivery_summary(monkeypatch):
    async def fake_get_webhook_delivery_summary(**kwargs):
        assert kwargs == {"tenant_code": "FNB", "hours": 24}
        return {
            "window_hours": 24,
            "tenant_code": "FNB",
            "total": 3,
            "sent_count": 2,
            "pending_count": 1,
            "failed_count": 0,
            "status": "PENDING",
            "by_status": {"SENT": 2, "PENDING": 1},
        }

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "get_webhook_delivery_summary",
        fake_get_webhook_delivery_summary,
    )

    response = _client().get(
        "/admin/partners/webhook-deliveries/summary?tenant_code=FNB&hours=24",
        headers={"x-api-key": "test-system-admin-key"},
    )

    assert response.status_code == 200
    assert response.json()["summary"]["status"] == "PENDING"


def test_system_admin_can_read_partner_readiness(monkeypatch):
    def fake_get_partner_seam_production_readiness():
        return {
            "code_status": "READY",
            "deployment_status": "ATTENTION",
            "code_complete": True,
            "checks": [],
        }

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "get_partner_seam_production_readiness",
        fake_get_partner_seam_production_readiness,
    )

    response = _client().get(
        "/admin/partners/readiness",
        headers={"x-api-key": "test-system-admin-key"},
    )

    assert response.status_code == 200
    assert response.json()["readiness"]["code_status"] == "READY"
    assert response.json()["readiness"]["deployment_status"] == "ATTENTION"


def test_system_admin_can_read_webhook_delivery_alerts(monkeypatch):
    async def fake_get_admin_partner_webhook_delivery_alerts(**kwargs):
        assert kwargs == {"tenant_code": "FNB", "client_id": "client-1", "limit": 10}
        return [
            {
                "tenant_code": "FNB",
                "client_id": "client-1",
                "webhook_id": "webhook-1",
                "event_type": "OUTCOME_COMPLETED",
                "failed_count": 3,
                "severity": "WARNING",
                "last_notification_status": "SENT",
            }
        ]

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "get_admin_partner_webhook_delivery_alerts",
        fake_get_admin_partner_webhook_delivery_alerts,
    )

    response = _client().get(
        "/admin/partners/webhook-deliveries/alerts?tenant_code=FNB&client_id=client-1&limit=10",
        headers={"x-api-key": "test-system-admin-key"},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["items"][0]["last_notification_status"] == "SENT"


def test_system_admin_can_notify_webhook_delivery_alerts(monkeypatch):
    async def fake_notify_partner_webhook_delivery_alerts(**kwargs):
        assert kwargs == {
            "tenant_code": "FNB",
            "client_id": "client-1",
            "limit": 10,
            "channel": "IN_APP",
        }
        return {
            "status": "notified",
            "channel": "IN_APP",
            "notified_count": 1,
            "items": [
                {"notification_id": "notification-1", "notification_status": "SENT"}
            ],
            "guardrail": "Notification evidence is recorded for current failed or cancelled webhook delivery alerts.",
        }

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "notify_partner_webhook_delivery_alerts",
        fake_notify_partner_webhook_delivery_alerts,
    )

    response = _client().post(
        "/admin/partners/webhook-deliveries/alerts/notify?tenant_code=FNB&client_id=client-1&limit=10&channel=IN_APP",
        headers={"x-api-key": "test-system-admin-key"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "notified"
    assert response.json()["notified_count"] == 1


def test_system_admin_can_retry_failed_webhook_delivery(monkeypatch):
    async def fake_mark_webhook_delivery_for_retry(**kwargs):
        assert kwargs["delivery_id"] == "delivery-1"
        assert kwargs["identity"]["role"] == "SYSTEM_ADMIN"
        assert kwargs["identity"]["tenant_code"] == "INTERNAL"
        return {"delivery_id": "delivery-1", "delivery_status": "PENDING"}

    monkeypatch.setattr(
        partner_seam.partner_seam_service,
        "mark_webhook_delivery_for_retry",
        fake_mark_webhook_delivery_for_retry,
    )

    response = _client().post(
        "/admin/partners/webhook-deliveries/delivery-1/retry",
        headers={"x-api-key": "test-system-admin-key"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert response.json()["delivery"]["delivery_status"] == "PENDING"
