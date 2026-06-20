from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.routers.enterprise_events as enterprise_events


@pytest.fixture()
def client():
    app = FastAPI()
    app.include_router(enterprise_events.router)
    return TestClient(app)


def test_enterprise_event_ingest_requires_api_key(client):
    response = client.post(
        "/enterprise/events",
        json={"eventType": "ACCOUNT_ACTIVATED"},
    )

    assert response.status_code == 401


def test_enterprise_event_ingest_uses_partner_tenant(client, monkeypatch):
    captured = {}

    async def fake_ingest_event(event):
        captured["event"] = event
        return {
            "status": "ok",
            "processingStatus": "QUEUED",
            "eventType": event["eventType"],
            "progressEventType": "ACCOUNT_ACTIVATED",
            "journeyCode": "BANKING_TRANSACTIONAL",
            "journeyVersion": "v1",
            "dedupeKey": "dedupe-1",
            "queued": True,
        }

    monkeypatch.setattr(enterprise_events, "ingest_event", fake_ingest_event)

    response = client.post(
        "/enterprise/events",
        json={
            "source": "HOGAN",
            "sourceEventId": "ids-1",
            "eventType": "ACCOUNT_ACTIVATED",
            "referralTrackId": "track-1",
        },
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 200
    assert response.json()["processingStatus"] == "QUEUED"
    assert captured["event"]["tenantCode"] == "FNB"
    assert captured["event"]["sourceEventId"] == "ids-1"


def test_enterprise_event_ingest_admin_can_send_tenant(client, monkeypatch):
    captured = {}

    async def fake_ingest_event(event):
        captured["event"] = event
        return {
            "status": "ok",
            "processingStatus": "IGNORED",
            "eventType": event["eventType"],
            "progressEventType": None,
            "journeyCode": None,
            "journeyVersion": None,
            "dedupeKey": "dedupe-2",
            "queued": False,
        }

    monkeypatch.setattr(enterprise_events, "ingest_event", fake_ingest_event)

    response = client.post(
        "/enterprise/events",
        json={
            "tenantCode": "PNP",
            "source": "HOGAN",
            "eventType": "CUSTOMER_PROFILE_UPDATED",
        },
        headers={"x-api-key": "test-admin-key"},
    )

    assert response.status_code == 200
    assert response.json()["processingStatus"] == "IGNORED"
    assert captured["event"]["tenantCode"] == "PNP"


def test_enterprise_event_ingest_returns_duplicate(client, monkeypatch):
    async def fake_ingest_event(event):
        return {
            "status": "duplicate",
            "processingStatus": "DUPLICATE",
            "eventType": event["eventType"],
            "progressEventType": None,
            "journeyCode": None,
            "journeyVersion": None,
            "dedupeKey": "dedupe-duplicate",
            "queued": False,
        }

    monkeypatch.setattr(enterprise_events, "ingest_event", fake_ingest_event)

    response = client.post(
        "/enterprise/events",
        json={
            "source": "HOGAN",
            "sourceEventId": "ids-duplicate",
            "eventType": "ACCOUNT_ACTIVATED",
        },
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "duplicate",
        "processingStatus": "DUPLICATE",
        "eventType": "ACCOUNT_ACTIVATED",
        "progressEventType": None,
        "journeyCode": None,
        "journeyVersion": None,
        "dedupeKey": "dedupe-duplicate",
        "queued": False,
    }


def test_enterprise_event_ingest_failure_returns_clean_error(client, monkeypatch):
    async def fake_ingest_event(_event):
        raise RuntimeError("queue unavailable")

    monkeypatch.setattr(enterprise_events, "ingest_event", fake_ingest_event)

    response = client.post(
        "/enterprise/events",
        json={
            "source": "HOGAN",
            "sourceEventId": "ids-fail",
            "eventType": "ACCOUNT_ACTIVATED",
        },
        headers={"x-api-key": "test-partner-key"},
    )

    assert response.status_code == 500
    assert response.json()["detail"]["error"] == "ENTERPRISE_EVENT_INGESTION_FAILED"
