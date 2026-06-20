from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.routers.admin_dlq_replay as router_mod
import services.dlq_replay_service as svc


def test_replay_referral_progress_event(monkeypatch):
    captured = {}

    def fake_handle_referral_progress_recorded(event, tenant_code):
        captured["event"] = event
        captured["tenant_code"] = tenant_code

    monkeypatch.setattr(
        svc,
        "handle_referral_progress_recorded",
        fake_handle_referral_progress_recorded,
    )

    result = svc.replay_dlq_event(
        {
            "originalEvent": {
                "eventType": "REFERRAL_PROGRESS_RECORDED",
                "tenant_code": "FNB",
                "referralTrackId": "track-123",
            },
            "error": "worker failed",
        }
    )

    assert result == {
        "status": "replayed",
        "eventType": "REFERRAL_PROGRESS_RECORDED",
        "tenantCode": "FNB",
    }
    assert captured["tenant_code"] == "FNB"
    assert captured["event"]["referralTrackId"] == "track-123"


def test_replay_leaderboard_rebuild_event(monkeypatch):
    captured = {}

    def fake_rebuild_leaderboard_for_referrer(*, tenant_code, referrer_ucn):
        captured["tenant_code"] = tenant_code
        captured["referrer_ucn"] = referrer_ucn

    monkeypatch.setattr(
        svc,
        "rebuild_leaderboard_for_referrer",
        fake_rebuild_leaderboard_for_referrer,
    )

    result = svc.replay_dlq_event(
        {
            "originalEvent": {
                "eventType": svc.EVENT_TYPE_LEADERBOARD_REBUILD_REQUESTED,
                "tenantCode": "FNB",
                "referrerUcn": "123",
            },
            "error": "leaderboard failed",
        }
    )

    assert result == {
        "status": "replayed",
        "eventType": svc.EVENT_TYPE_LEADERBOARD_REBUILD_REQUESTED,
        "tenantCode": "FNB",
        "referrerUcn": "123",
    }
    assert captured == {
        "tenant_code": "FNB",
        "referrer_ucn": "123",
    }


def test_replay_missing_original_event_raises():
    with pytest.raises(ValueError, match="Missing or invalid originalEvent"):
        svc.replay_dlq_event({"error": "boom"})


def test_replay_missing_tenant_raises():
    with pytest.raises(ValueError, match="Missing tenantCode or tenant_code"):
        svc.replay_dlq_event(
            {
                "originalEvent": {
                    "eventType": "REFERRAL_PROGRESS_RECORDED",
                    "referralTrackId": "track-123",
                }
            }
        )


def test_replay_leaderboard_missing_referrer_raises():
    with pytest.raises(ValueError, match="Missing referrerUcn or referrer_ucn"):
        svc.replay_dlq_event(
            {
                "originalEvent": {
                    "eventType": svc.EVENT_TYPE_LEADERBOARD_REBUILD_REQUESTED,
                    "tenantCode": "FNB",
                }
            }
        )


def test_replay_unsupported_event_raises():
    with pytest.raises(ValueError, match="Unsupported DLQ event type"):
        svc.replay_dlq_event(
            {
                "originalEvent": {
                    "eventType": "UNKNOWN_EVENT",
                    "tenantCode": "FNB",
                }
            }
        )


def _admin_client():
    from utils.security import require_admin_key

    app = FastAPI()
    app.include_router(router_mod.router)

    app.dependency_overrides[require_admin_key] = lambda: {"role": "ADMIN"}

    return TestClient(app)


def test_admin_dlq_replay_endpoint_success(monkeypatch):
    client = _admin_client()

    monkeypatch.setattr(
        router_mod,
        "replay_dlq_event",
        lambda payload: {
            "status": "replayed",
            "eventType": "REFERRAL_PROGRESS_RECORDED",
            "tenantCode": "FNB",
        },
    )

    response = client.post(
        "/admin/dlq/replay",
        headers={"x-api-key": "dev-admin-key-123"},
        json={
            "originalEvent": {
                "eventType": "REFERRAL_PROGRESS_RECORDED",
                "tenant_code": "FNB",
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "replayed"


def test_admin_dlq_replay_endpoint_bad_payload(monkeypatch):
    client = _admin_client()

    def fake_replay(payload):
        raise ValueError("Missing or invalid originalEvent")

    monkeypatch.setattr(router_mod, "replay_dlq_event", fake_replay)

    response = client.post(
        "/admin/dlq/replay",
        headers={"x-api-key": "dev-admin-key-123"},
        json={"error": "boom"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Missing or invalid originalEvent",
    }