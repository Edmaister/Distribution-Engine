from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.routers.worker as worker


def _client(monkeypatch):
    monkeypatch.setattr(worker, "WORKER_SECRET", "test-worker-secret")

    app = FastAPI()
    app.include_router(worker.router)

    return TestClient(app)


def test_worker_consumes_leaderboard_rebuild_event(monkeypatch):
    client = _client(monkeypatch)

    captured = {}

    def fake_rebuild_leaderboard_for_referrer(*, tenant_code: str, referrer_ucn: str):
        captured["tenant_code"] = tenant_code
        captured["referrer_ucn"] = referrer_ucn

    monkeypatch.setattr(
        worker,
        "rebuild_leaderboard_for_referrer",
        fake_rebuild_leaderboard_for_referrer,
    )

    response = client.post(
        "/worker/referral-events",
        headers={"x-worker-secret": "test-worker-secret"},
        json={
            "eventType": "LEADERBOARD_REBUILD_REQUESTED",
            "tenantCode": "FNB",
            "referrerUcn": "123",
            "correlationId": "corr-123",
            "referralTrackId": "track-123",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "processed": True,
        "eventType": "LEADERBOARD_REBUILD_REQUESTED",
    }

    assert captured == {
        "tenant_code": "FNB",
        "referrer_ucn": "123",
    }


def test_worker_leaderboard_rebuild_event_missing_referrer_fails_safely(monkeypatch):
    client = _client(monkeypatch)

    called = False

    def fake_rebuild_leaderboard_for_referrer(*, tenant_code: str, referrer_ucn: str):
        nonlocal called
        called = True

    monkeypatch.setattr(
        worker,
        "rebuild_leaderboard_for_referrer",
        fake_rebuild_leaderboard_for_referrer,
    )

    response = client.post(
        "/worker/referral-events",
        headers={"x-worker-secret": "test-worker-secret"},
        json={
            "eventType": "LEADERBOARD_REBUILD_REQUESTED",
            "tenantCode": "FNB",
            "correlationId": "corr-123",
            "referralTrackId": "track-123",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ignored",
        "reason": "missing referrerUcn",
    }
    assert called is False


def test_worker_unsupported_event_fails_safely(monkeypatch):
    client = _client(monkeypatch)

    response = client.post(
        "/worker/referral-events",
        headers={"x-worker-secret": "test-worker-secret"},
        json={
            "eventType": "UNKNOWN_EVENT",
            "tenantCode": "FNB",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["processed"] is False
    assert "unsupported or unrecognized event payload" in body["reason"]


def test_worker_unwraps_sqs_body_for_leaderboard_rebuild(monkeypatch):
    client = _client(monkeypatch)

    captured = {}

    def fake_rebuild_leaderboard_for_referrer(*, tenant_code: str, referrer_ucn: str):
        captured["tenant_code"] = tenant_code
        captured["referrer_ucn"] = referrer_ucn

    monkeypatch.setattr(
        worker,
        "rebuild_leaderboard_for_referrer",
        fake_rebuild_leaderboard_for_referrer,
    )

    response = client.post(
        "/worker/referral-events",
        headers={"x-worker-secret": "test-worker-secret"},
        json={
            "body": (
                '{"eventType":"LEADERBOARD_REBUILD_REQUESTED",'
                '"tenantCode":"FNB",'
                '"referrerUcn":"123",'
                '"correlationId":"corr-123",'
                '"referralTrackId":"track-123"}'
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["processed"] is True
    assert captured == {
        "tenant_code": "FNB",
        "referrer_ucn": "123",
    }