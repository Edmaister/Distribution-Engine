from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.routers import admin_channels


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(admin_channels.router)
    return TestClient(app)


def test_admin_channel_readiness_requires_auth():
    response = _client().get("/admin/channels/readiness")

    assert response.status_code == 401


def test_distribution_admin_can_read_channel_readiness():
    response = _client().get(
        "/admin/channels/readiness",
        headers={"x-api-key": "test-distribution-admin-key"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["readiness"]["configuration_source"] == "channel_catalog"
    assert payload["readiness"]["summary"]["supported_channels"] == [
        "WHATSAPP",
        "SMS",
        "USSD",
    ]


def test_distribution_admin_can_read_channel_recommendations(monkeypatch):
    def fake_recommend_channels(**kwargs):
        assert kwargs == {
            "event_type": "ROUTE_ASSIGNED",
            "audience": "DISTRIBUTOR",
            "target_channels": ["WHATSAPP"],
            "distributor_channels": ["WHATSAPP", "SMS"],
        }
        return {
            "status": "READY",
            "top_channel": {"channel_code": "WHATSAPP"},
            "items": [],
        }

    monkeypatch.setattr(admin_channels, "recommend_channels", fake_recommend_channels)

    response = _client().post(
        "/admin/channels/recommendations",
        headers={"x-api-key": "test-distribution-admin-key"},
        json={
            "event_type": "ROUTE_ASSIGNED",
            "audience": "DISTRIBUTOR",
            "target_channels": ["WHATSAPP"],
            "distributor_channels": ["WHATSAPP", "SMS"],
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["recommendations"]["top_channel"]["channel_code"] == "WHATSAPP"
    )


def test_distribution_admin_can_read_delivery_operations(monkeypatch):
    def fake_list_channel_deliveries(**kwargs):
        assert kwargs == {"status_filter": "SENT", "limit": 25}
        return {
            "status": "ok",
            "summary": {"count": 1, "sent": 1},
            "items": [
                {
                    "delivery_id": "CHD-1",
                    "status": "SENT",
                    "recipient_ref": "recipient:abc123",
                }
            ],
        }

    monkeypatch.setattr(
        admin_channels, "list_channel_deliveries", fake_list_channel_deliveries
    )

    response = _client().get(
        "/admin/channels/deliveries?status=SENT&limit=25",
        headers={"x-api-key": "test-distribution-admin-key"},
    )

    assert response.status_code == 200
    assert response.json()["deliveries"]["items"][0]["recipient_ref"].startswith(
        "recipient:"
    )


def test_distribution_admin_can_read_channel_audit(monkeypatch):
    def fake_list_channel_audit(**kwargs):
        assert kwargs == {"limit": 10}
        return {
            "status": "ok",
            "items": [
                {
                    "audit_id": "CHA-1",
                    "delivery_id": "CHD-1",
                    "event_type": "SENT",
                    "recipient_ref": "recipient:abc123",
                }
            ],
        }

    monkeypatch.setattr(admin_channels, "list_channel_audit", fake_list_channel_audit)

    response = _client().get(
        "/admin/channels/audit?limit=10",
        headers={"x-api-key": "test-distribution-admin-key"},
    )

    assert response.status_code == 200
    assert response.json()["audit"]["items"][0]["event_type"] == "SENT"


def test_distribution_admin_can_dispatch_configured_channel(monkeypatch):
    async def fake_dispatch_channel_message(**kwargs):
        return {
            "status": "SENT",
            "channel_code": kwargs["channel_code"].upper(),
            "adapter_type": "MESSAGING",
            "recipient": kwargs["recipient"],
            "provider_status": 202,
            "provider_response": "queued",
            "guardrail": "Provider response is recorded without exposing provider secrets.",
        }

    monkeypatch.setattr(
        admin_channels, "dispatch_channel_message", fake_dispatch_channel_message
    )

    response = _client().post(
        "/admin/channels/dispatch",
        headers={"x-api-key": "test-distribution-admin-key"},
        json={
            "channel_code": "WHATSAPP",
            "tenant_code": "FNB",
            "recipient": "+27123456789",
            "message": "Your referral is ready",
            "context": {"referral_track_id": "track-1"},
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "sent"
    assert response.json()["dispatch"]["channel_code"] == "WHATSAPP"


def test_distribution_admin_can_retry_failed_channel_delivery(monkeypatch):
    async def fake_retry_channel_delivery(**kwargs):
        assert kwargs == {"delivery_id": "CHD-1"}
        return {
            "status": "SENT",
            "delivery": {
                "delivery_id": "CHD-1",
                "status": "SENT",
                "attempt_count": 2,
                "recipient_ref": "recipient:abc123",
            },
            "guardrail": "Retries are limited.",
        }

    monkeypatch.setattr(admin_channels, "retry_channel_delivery", fake_retry_channel_delivery)

    response = _client().post(
        "/admin/channels/deliveries/CHD-1/retry",
        headers={"x-api-key": "test-distribution-admin-key"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "sent"
    assert response.json()["retry"]["delivery"]["attempt_count"] == 2


def test_dispatch_requires_distribution_admin():
    response = _client().post(
        "/admin/channels/dispatch",
        json={
            "channel_code": "SMS",
            "recipient": "+27123456789",
            "message": "Hello",
        },
    )

    assert response.status_code == 401
