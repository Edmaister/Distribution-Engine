from __future__ import annotations

import datetime
import json
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.routers.admin_enterprise_events as router_mod
import services.enterprise_event_inbox_service as svc


class FakeAsyncConnection:
    def __init__(self, *, rows=None, row=None):
        self.rows = rows or []
        self.row = row
        self.fetch_calls = []
        self.fetchrow_calls = []
        self.execute_calls = []

    async def fetch(self, query, *params):
        self.fetch_calls.append((query, params))
        return self.rows

    async def fetchrow(self, query, *params):
        self.fetchrow_calls.append((query, params))
        return self.row

    async def execute(self, query, *params):
        self.execute_calls.append((query, params))
        return "UPDATE 1"


class SequencedFetchConnection(FakeAsyncConnection):
    def __init__(self, fetch_results):
        super().__init__()
        self.fetch_results = list(fetch_results)

    async def fetch(self, query, *params):
        self.fetch_calls.append((query, params))
        return self.fetch_results.pop(0)


class FakeAsyncConnectionContext:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


def patch_async_db(monkeypatch, conn):
    monkeypatch.setattr(
        svc,
        "get_async_connection",
        lambda: FakeAsyncConnectionContext(conn),
    )


@pytest.mark.asyncio
async def test_get_enterprise_event_dashboard(monkeypatch):
    now = datetime.datetime(2026, 6, 10, 12, 0, 0)
    conn = SequencedFetchConnection(
        [
            [
                {"processing_status": "IGNORED", "event_count": 2},
                {"processing_status": "QUEUED", "event_count": 5},
            ],
            [
                {"source_system": "HOGAN", "event_count": 7},
            ],
            [
                {"event_type": "ACCOUNT_ACTIVATED", "event_count": 4},
                {"event_type": "CUSTOMER_PROFILE_UPDATED", "event_count": 3},
            ],
            [
                {
                    "inbox_event_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
                    "tenant_code": "FNB",
                    "source_system": "HOGAN",
                    "source_event_id": "ids-problem-1",
                    "referral_track_id": "track-1",
                    "event_type": "CUSTOMER_PROFILE_UPDATED",
                    "processing_status": "IGNORED",
                    "error_message": "not qualifying",
                    "received_at": now,
                    "has_normalized_payload": False,
                }
            ],
        ]
    )
    patch_async_db(monkeypatch, conn)

    result = await svc.get_enterprise_event_dashboard(
        tenant_code="FNB",
        days=14,
        problem_limit=10,
    )

    assert len(conn.fetch_calls) == 4
    assert conn.fetch_calls[0][1] == ("FNB", 14)
    assert conn.fetch_calls[3][1] == ("FNB", 14, 10)
    assert result["status"] == "ok"
    assert result["tenantCode"] == "FNB"
    assert result["windowDays"] == 14
    assert result["total"] == 7
    assert result["byStatus"] == [
        {"processingStatus": "IGNORED", "eventCount": 2},
        {"processingStatus": "QUEUED", "eventCount": 5},
    ]
    assert result["bySourceSystem"] == [
        {"sourceSystem": "HOGAN", "eventCount": 7},
    ]
    assert result["byEventType"][0]["eventType"] == "ACCOUNT_ACTIVATED"
    assert result["recentProblemEvents"][0]["inboxEventId"] == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    assert result["recentProblemEvents"][0]["hasNormalizedPayload"] is False


@pytest.mark.asyncio
async def test_get_enterprise_event_summary(monkeypatch):
    conn = FakeAsyncConnection(
        rows=[
            {"processing_status": "IGNORED", "event_count": 2},
            {"processing_status": "QUEUED", "event_count": 3},
        ]
    )
    patch_async_db(monkeypatch, conn)
    gauges = []
    monkeypatch.setattr(
        svc,
        "enterprise_event_inbox_current_set",
        lambda **kwargs: gauges.append(kwargs),
    )

    result = await svc.get_enterprise_event_summary()

    assert result == {
        "status": "ok",
        "total": 5,
        "items": [
            {"processingStatus": "IGNORED", "eventCount": 2},
            {"processingStatus": "QUEUED", "eventCount": 3},
        ],
    }
    assert gauges == [
        {"processing_status": "IGNORED", "value": 2},
        {"processing_status": "QUEUED", "value": 3},
    ]


@pytest.mark.asyncio
async def test_list_enterprise_events_filters(monkeypatch):
    now = datetime.datetime(2026, 6, 10, 12, 0, 0)
    conn = FakeAsyncConnection(
        rows=[
            {
                "inbox_event_id": UUID("11111111-1111-1111-1111-111111111111"),
                "tenant_code": "FNB",
                "source_system": "HOGAN",
                "source_event_id": "ids-1",
                "correlation_id": "corr-1",
                "referral_track_id": "track-1",
                "event_type": "ACCOUNT_ACTIVATED",
                "occurred_at": now,
                "received_at": now,
                "processing_status": "QUEUED",
                "processed_at": now,
                "error_message": None,
                "has_normalized_payload": True,
            }
        ]
    )
    patch_async_db(monkeypatch, conn)

    result = await svc.list_enterprise_events(
        processing_status="QUEUED",
        source_system="HOGAN",
        referral_track_id="track-1",
        limit=25,
    )

    query, params = conn.fetch_calls[0]
    assert "processing_status = $1" in query
    assert "source_system = $2" in query
    assert "referral_track_id = $3" in query
    assert params == ("QUEUED", "HOGAN", "track-1", 25)
    assert result["count"] == 1
    assert result["items"][0]["inboxEventId"] == "11111111-1111-1111-1111-111111111111"
    assert result["items"][0]["hasNormalizedPayload"] is True


@pytest.mark.asyncio
async def test_replay_enterprise_event_dry_run(monkeypatch):
    conn = FakeAsyncConnection(
        row={
            "inbox_event_id": UUID("22222222-2222-2222-2222-222222222222"),
            "tenant_code": "FNB",
            "source_system": "HOGAN",
            "source_event_id": "ids-2",
            "referral_track_id": "track-2",
            "event_type": "ACCOUNT_ACTIVATED",
            "normalized_payload": json.dumps(
                {
                    "eventType": "REFERRAL_PROGRESS_RECORDED",
                    "progressEventType": "ACCOUNT_ACTIVATED",
                    "tenantCode": "FNB",
                    "referralTrackId": "track-2",
                }
            ),
            "processing_status": "QUEUED",
        }
    )
    patch_async_db(monkeypatch, conn)
    replay_metrics = []
    monkeypatch.setattr(
        svc,
        "enterprise_event_replay_inc",
        lambda **kwargs: replay_metrics.append(kwargs),
    )

    result = await svc.replay_enterprise_event(
        inbox_event_id="22222222-2222-2222-2222-222222222222",
        dry_run=True,
    )

    assert result["status"] == "replayable"
    assert result["queued"] is False
    assert result["progressEventType"] == "ACCOUNT_ACTIVATED"
    assert replay_metrics == [
        {"event_type": "ACCOUNT_ACTIVATED", "status": "replayable"}
    ]


@pytest.mark.asyncio
async def test_replay_enterprise_event_queues_payload(monkeypatch):
    fetch_conn = FakeAsyncConnection(
        row={
            "inbox_event_id": UUID("33333333-3333-3333-3333-333333333333"),
            "tenant_code": "FNB",
            "source_system": "HOGAN",
            "source_event_id": "ids-3",
            "referral_track_id": "track-3",
            "event_type": "SALARY_DEPOSIT",
            "normalized_payload": {
                "eventType": "REFERRAL_PROGRESS_RECORDED",
                "progressEventType": "SALARY_SWITCHED",
                "tenantCode": "FNB",
                "referralTrackId": "track-3",
            },
            "processing_status": "QUEUED",
        }
    )
    update_conn = FakeAsyncConnection()
    conns = [fetch_conn, update_conn]
    monkeypatch.setattr(
        svc,
        "get_async_connection",
        lambda: FakeAsyncConnectionContext(conns.pop(0)),
    )

    enqueued = []
    replay_metrics = []

    async def fake_enqueue(payload):
        enqueued.append(payload)

    monkeypatch.setattr(svc, "enqueue_event", fake_enqueue)
    monkeypatch.setattr(
        svc,
        "enterprise_event_replay_inc",
        lambda **kwargs: replay_metrics.append(kwargs),
    )

    result = await svc.replay_enterprise_event(
        inbox_event_id="33333333-3333-3333-3333-333333333333",
        dry_run=False,
    )

    assert result["status"] == "replay_queued"
    assert result["queued"] is True
    assert enqueued[0]["progressEventType"] == "SALARY_SWITCHED"
    assert "processing_status = 'QUEUED'" in update_conn.execute_calls[0][0]
    assert replay_metrics == [
        {"event_type": "SALARY_DEPOSIT", "status": "replay_queued"}
    ]


@pytest.mark.asyncio
async def test_replay_enterprise_event_without_normalized_payload_skips(monkeypatch):
    conn = FakeAsyncConnection(
        row={
            "inbox_event_id": UUID("44444444-4444-4444-4444-444444444444"),
            "tenant_code": "FNB",
            "source_system": "HOGAN",
            "source_event_id": "ids-4",
            "referral_track_id": None,
            "event_type": "CUSTOMER_PROFILE_UPDATED",
            "normalized_payload": None,
            "processing_status": "IGNORED",
        }
    )
    patch_async_db(monkeypatch, conn)
    replay_metrics = []
    monkeypatch.setattr(
        svc,
        "enterprise_event_replay_inc",
        lambda **kwargs: replay_metrics.append(kwargs),
    )

    result = await svc.replay_enterprise_event(
        inbox_event_id="44444444-4444-4444-4444-444444444444",
        dry_run=False,
    )

    assert result["status"] == "skipped"
    assert result["reason"] == "no_normalized_payload"
    assert result["queued"] is False
    assert replay_metrics == [
        {"event_type": "CUSTOMER_PROFILE_UPDATED", "status": "skipped"}
    ]


@pytest.mark.asyncio
async def test_replay_enterprise_event_missing_raises(monkeypatch):
    conn = FakeAsyncConnection(row=None)
    patch_async_db(monkeypatch, conn)

    with pytest.raises(ValueError, match="Enterprise inbox event not found"):
        await svc.replay_enterprise_event(
            inbox_event_id="missing",
            dry_run=True,
        )


def _admin_client():
    app = FastAPI()
    app.include_router(router_mod.router)
    app.dependency_overrides[router_mod.require_admin_key] = lambda: {"role": "ADMIN"}
    return TestClient(app)


def test_admin_enterprise_events_summary_endpoint(monkeypatch):
    client = _admin_client()

    async def fake_summary():
        return {"status": "ok", "total": 0, "items": []}

    monkeypatch.setattr(router_mod, "get_enterprise_event_summary", fake_summary)

    response = client.get("/admin/enterprise-events/summary")

    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_admin_enterprise_events_dashboard_endpoint_normalizes_params(monkeypatch):
    client = _admin_client()
    captured = {}

    async def fake_dashboard(**kwargs):
        captured.update(kwargs)
        return {
            "status": "ok",
            "tenantCode": kwargs["tenant_code"],
            "windowDays": kwargs["days"],
            "total": 0,
            "byStatus": [],
            "bySourceSystem": [],
            "byEventType": [],
            "recentProblemEvents": [],
        }

    monkeypatch.setattr(router_mod, "get_enterprise_event_dashboard", fake_dashboard)

    response = client.get(
        "/admin/enterprise-events/dashboard",
        params={"tenantCode": " fnb ", "days": 14, "problemLimit": 10},
    )

    assert response.status_code == 200
    assert captured == {
        "tenant_code": "FNB",
        "days": 14,
        "problem_limit": 10,
    }
    assert response.json()["tenantCode"] == "FNB"


def test_admin_enterprise_events_list_endpoint_normalizes_filters(monkeypatch):
    client = _admin_client()
    captured = {}

    async def fake_list(**kwargs):
        captured.update(kwargs)
        return {"status": "ok", "count": 0, "items": []}

    monkeypatch.setattr(router_mod, "list_enterprise_events", fake_list)

    response = client.get(
        "/admin/enterprise-events",
        params={"processingStatus": "queued", "sourceSystem": "hogan", "limit": 10},
    )

    assert response.status_code == 200
    assert captured["processing_status"] == "QUEUED"
    assert captured["source_system"] == "HOGAN"
    assert captured["limit"] == 10


def test_admin_enterprise_events_replay_not_found(monkeypatch):
    client = _admin_client()

    async def fake_replay(**_kwargs):
        raise ValueError("Enterprise inbox event not found")

    monkeypatch.setattr(router_mod, "replay_enterprise_event", fake_replay)

    response = client.post("/admin/enterprise-events/missing/replay")

    assert response.status_code == 404
    assert response.json()["detail"] == "Enterprise inbox event not found"
