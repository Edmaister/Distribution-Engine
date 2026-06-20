from __future__ import annotations

import hashlib
import hmac
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.routers import channels
from services import channel_readiness_service


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(channels.router)
    return TestClient(app)


def test_receive_channel_webhook_accepts_signed_payload(monkeypatch):
    monkeypatch.setattr(
        channel_readiness_service,
        "get_settings",
        lambda: type("Settings", (), {"channel_sms_provider_secret": "sms-secret"})(),
    )
    body = json.dumps(
        {
            "messageId": "msg-1",
            "msisdn": "+27123456789",
            "text": "YES",
        },
        separators=(",", ":"),
    ).encode("utf-8")
    signature = hmac.new(b"sms-secret", body, hashlib.sha256).hexdigest()

    response = _client().post(
        "/channels/webhooks/SMS",
        content=body,
        headers={
            "content-type": "application/json",
            "x-amplifi-signature": signature,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert response.json()["channel_code"] == "SMS"
    assert response.json()["inbound"]["message_id"] == "msg-1"


def test_receive_channel_webhook_rejects_bad_signature(monkeypatch):
    monkeypatch.setattr(
        channel_readiness_service,
        "get_settings",
        lambda: type("Settings", (), {"channel_sms_provider_secret": "sms-secret"})(),
    )

    response = _client().post(
        "/channels/webhooks/SMS",
        json={"messageId": "msg-1", "text": "YES"},
        headers={"x-amplifi-signature": "bad"},
    )

    assert response.status_code == 401


def test_channel_preferences_require_session():
    response = _client().get(
        "/channels/preferences/CONSUMER/REF-1?tenant_code=FNB",
    )

    assert response.status_code == 401


def test_consumer_can_write_and_read_channel_preferences():
    channel_readiness_service._reset_channel_delivery_state_for_tests()

    response = _client().put(
        "/channels/preferences/CONSUMER/ref-1",
        headers={"x-api-key": "test-fnb-consumer-key"},
        json={
            "tenant_code": "FNB",
            "preferred_channels": ["sms", "whatsapp", "unknown"],
            "consent_channels": ["whatsapp"],
            "opt_out_channels": ["sms"],
        },
    )

    assert response.status_code == 200
    preferences = response.json()["preferences"]
    assert preferences["preferred_channels"] == ["SMS", "WHATSAPP"]
    assert preferences["consent_channels"] == ["WHATSAPP"]
    assert preferences["opt_out_channels"] == ["SMS"]
    assert preferences["recommendation_channels"] == ["WHATSAPP"]

    read_response = _client().get(
        "/channels/preferences/CONSUMER/ref-1?tenant_code=FNB",
        headers={"x-api-key": "test-fnb-consumer-key"},
    )

    assert read_response.status_code == 200
    assert read_response.json()["preferences"]["subject_id"] == "REF-1"


def test_distributor_preferences_are_distributor_scoped():
    channel_readiness_service._reset_channel_delivery_state_for_tests()

    response = _client().put(
        "/channels/preferences/DISTRIBUTOR/DIST-INSURANCE-ADVOCATE",
        headers={"x-api-key": "test-fnb-distributor-insurance-advocate-key"},
        json={
            "tenant_code": "FNB",
            "preferred_channels": ["whatsapp", "ussd"],
            "consent_channels": ["whatsapp", "ussd"],
            "opt_out_channels": [],
        },
    )

    assert response.status_code == 200
    assert response.json()["preferences"]["audience"] == "DISTRIBUTOR"

    blocked = _client().put(
        "/channels/preferences/DISTRIBUTOR/OTHER-DIST",
        headers={"x-api-key": "test-fnb-distributor-insurance-advocate-key"},
        json={
            "tenant_code": "FNB",
            "preferred_channels": ["whatsapp"],
        },
    )

    assert blocked.status_code == 403


def test_recommend_channels_applies_user_preferences(monkeypatch):
    monkeypatch.setattr(
        channel_readiness_service,
        "get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "channel_whatsapp_provider_url": "https://channels.example/whatsapp",
                "channel_whatsapp_provider_secret": "whatsapp-secret",
                "channel_sms_provider_url": "https://channels.example/sms",
                "channel_sms_provider_secret": "sms-secret",
                "channel_ussd_provider_url": "https://channels.example/ussd",
                "channel_ussd_provider_secret": "ussd-secret",
            },
        )(),
    )

    result = channel_readiness_service.recommend_channels(
        event_type="REFERRAL_STARTED",
        audience="CONSUMER",
        channel_preferences={
            "preferred_channels": ["SMS"],
            "opt_out_channels": ["SMS"],
        },
    )

    sms = next(item for item in result["items"] if item["channel_code"] == "SMS")
    assert result["preferences_applied"] is True
    assert sms["preference_status"] == "OPTED_OUT"
    assert "preference: opted out" in sms["reasons"]
    assert result["top_channel"]["channel_code"] != "SMS"
