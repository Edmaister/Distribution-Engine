from __future__ import annotations

import datetime
import json
from unittest.mock import AsyncMock

import pytest

import apps.Workers.ids_consumer as mod


class FakeAsyncConnection:
    def __init__(self, *, inserted=True):
        self.inserted = inserted
        self.fetchrow_calls = []
        self.execute_calls = []

    def transaction(self):
        return FakeAsyncConnectionContext(self)

    async def fetchrow(self, query, *params):
        self.fetchrow_calls.append((query, params))
        return {"inbox_event_id": "inbox-1"} if self.inserted else None

    async def execute(self, query, *params):
        self.execute_calls.append((query, params))
        return "UPDATE 1"


class FakeAsyncConnectionContext:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


def patch_async_db(monkeypatch, conn):
    monkeypatch.setattr(
        mod,
        "get_async_connection",
        lambda: FakeAsyncConnectionContext(conn),
    )


@pytest.mark.asyncio
async def test_ingest_event_inserts_ignored_inbox_event(monkeypatch):
    conn = FakeAsyncConnection()
    patch_async_db(monkeypatch, conn)

    enqueue = AsyncMock()
    monkeypatch.setattr(mod, "enqueue_event", enqueue)

    occurred_at = datetime.datetime(2026, 5, 25, 10, 0, 0)
    evt = {
        "referralTrackId": "11111111-1111-1111-1111-111111111111",
        "eventType": "NON_QUALIFYING",
        "occurredAt": occurred_at,
        "attributes": {"foo": "bar"},
        "source": "ids",
    }

    result = await mod.ingest_event(evt)
    query, params = conn.fetchrow_calls[0]

    assert "INSERT INTO enterprise_event_inbox" in query
    assert params[0] is None
    assert params[1] == "IDS"
    assert params[4] == "11111111-1111-1111-1111-111111111111"
    assert params[5] == "NON_QUALIFYING"
    assert params[6] == occurred_at
    raw_payload = json.loads(params[7])
    assert raw_payload["referralTrackId"] == evt["referralTrackId"]
    assert raw_payload["eventType"] == evt["eventType"]
    assert raw_payload["occurredAt"] == occurred_at.isoformat()
    assert raw_payload["attributes"] == {"foo": "bar"}
    assert params[8] is None
    assert params[11] == "IGNORED"
    assert result["processingStatus"] == "IGNORED"
    assert result["queued"] is False
    enqueue.assert_not_awaited()


@pytest.mark.asyncio
async def test_ingest_event_accepts_iso_timestamp_strings(monkeypatch):
    conn = FakeAsyncConnection()
    patch_async_db(monkeypatch, conn)
    monkeypatch.setattr(mod, "enqueue_event", AsyncMock())

    await mod.ingest_event(
        {
            "source": "HOGAN",
            "sourceEventId": "ids-string-time",
            "eventType": "CUSTOMER_PROFILE_UPDATED",
            "tenantCode": "FNB",
            "occurredAt": "2026-06-10T12:00:00Z",
        }
    )

    _, params = conn.fetchrow_calls[0]

    assert params[1] == "HOGAN"
    assert params[6] == datetime.datetime(
        2026,
        6,
        10,
        12,
        0,
        0,
        tzinfo=datetime.timezone.utc,
    )
    assert params[11] == "IGNORED"


@pytest.mark.asyncio
async def test_ingest_event_defaults_occurred_at_source_and_ignores_without_tenant(monkeypatch):
    conn = FakeAsyncConnection()
    patch_async_db(monkeypatch, conn)
    monkeypatch.setattr(mod, "enqueue_event", AsyncMock())

    result = await mod.ingest_event(
        {
            "referralTrackId": "22222222-2222-2222-2222-222222222222",
            "eventType": "ACCOUNT_ACTIVATED",
        }
    )

    _, params = conn.fetchrow_calls[0]

    assert params[0] is None
    assert params[1] == "IDS"
    assert params[5] == "ACCOUNT_ACTIVATED"
    assert isinstance(params[6], datetime.datetime)
    assert params[11] == "IGNORED"
    assert result["processingStatus"] == "IGNORED"
    assert result["queued"] is False


@pytest.mark.asyncio
async def test_ingest_event_qualifying_event_queues_progress(monkeypatch):
    conn = FakeAsyncConnection()
    patch_async_db(monkeypatch, conn)

    enqueued = []
    metrics = []

    async def enqueue(event):
        enqueued.append(event)

    monkeypatch.setattr(mod, "enqueue_event", enqueue)
    monkeypatch.setattr(
        mod,
        "enterprise_event_ingested_inc",
        lambda **kwargs: metrics.append(kwargs),
    )

    occurred_at = datetime.datetime(2026, 5, 25, 10, 30, 0)
    evt = {
        "referralTrackId": "33333333-3333-3333-3333-333333333333",
        "eventType": "DEBIT_ORDER_SWITCHED",
        "tenant": "FNB",
        "sticker": "QR1",
        "campaignCode": "CAMP001",
        "refereeUCN": "UCN-123",
        "sourceEventId": "ids-123",
        "occurredAt": occurred_at,
    }

    result = await mod.ingest_event(evt)
    _, params = conn.fetchrow_calls[0]

    assert params[0] == "FNB"
    assert params[1] == "IDS"
    assert params[2] == "ids-123"
    assert params[3] == "33333333-3333-3333-3333-333333333333"
    assert params[4] == "33333333-3333-3333-3333-333333333333"
    assert params[11] == "QUEUED"
    assert result["processingStatus"] == "QUEUED"
    assert result["progressEventType"] == "DEBIT_ORDER_SWITCHED"
    assert result["queued"] is True

    assert len(enqueued) == 1
    progress_event = enqueued[0]
    assert progress_event["eventType"] == "REFERRAL_PROGRESS_RECORDED"
    assert progress_event["progressEventType"] == "DEBIT_ORDER_SWITCHED"
    assert progress_event["journeyCode"] == "BANKING_TRANSACTIONAL"
    assert progress_event["journeyVersion"] == "v1"
    assert progress_event["sourceEventType"] == "DEBIT_ORDER_SWITCHED"
    assert progress_event["sourceSystem"] == "IDS"
    assert progress_event["sourceEventId"] == "ids-123"
    assert progress_event["tenantCode"] == "FNB"
    assert progress_event["referralTrackId"] == "33333333-3333-3333-3333-333333333333"
    assert progress_event["occurredAt"] == occurred_at
    assert progress_event["dedupeKey"] == result["dedupeKey"]
    assert metrics == [
        {
            "source_system": "IDS",
            "event_type": "DEBIT_ORDER_SWITCHED",
            "processing_status": "QUEUED",
        }
    ]


@pytest.mark.asyncio
async def test_ingest_event_duplicate_does_not_enqueue(monkeypatch):
    conn = FakeAsyncConnection(inserted=False)
    patch_async_db(monkeypatch, conn)

    enqueue = AsyncMock()
    metrics = []
    monkeypatch.setattr(mod, "enqueue_event", enqueue)
    monkeypatch.setattr(
        mod,
        "enterprise_event_ingested_inc",
        lambda **kwargs: metrics.append(kwargs),
    )

    result = await mod.ingest_event(
        {
            "referralTrackId": "44444444-4444-4444-4444-444444444444",
            "eventType": "ACCOUNT_ACTIVATED",
            "tenant": "FNB",
            "sourceEventId": "ids-duplicate",
        }
    )

    assert result["status"] == "duplicate"
    assert result["processingStatus"] == "DUPLICATE"
    assert result["queued"] is False
    enqueue.assert_not_awaited()
    assert metrics == [
        {
            "source_system": "IDS",
            "event_type": "ACCOUNT_ACTIVATED",
            "processing_status": "DUPLICATE",
        }
    ]


@pytest.mark.asyncio
async def test_ingest_event_updates_failed_status_when_enqueue_fails(monkeypatch):
    conn = FakeAsyncConnection()
    patch_async_db(monkeypatch, conn)

    async def enqueue(_event):
        raise RuntimeError("queue unavailable")

    monkeypatch.setattr(mod, "enqueue_event", enqueue)

    with pytest.raises(RuntimeError, match="queue unavailable"):
        await mod.ingest_event(
            {
                "referralTrackId": "55555555-5555-5555-5555-555555555555",
                "eventType": "ACCOUNT_ACTIVATED",
                "tenant": "FNB",
                "refereeUCN": "UCN-555",
                "sourceEventId": "ids-fail",
            }
        )

    query, params = conn.execute_calls[0]
    assert "processing_status = 'FAILED'" in query
    assert params[1] == "queue unavailable"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event_type,expected_progress_event_type,expected_journey_code",
    [
        ("POLICY_ACTIVATED", "POLICY_ISSUED", "INSURANCE_POLICY"),
        ("ACCOUNT_ACTIVATED", "ACCOUNT_ACTIVATED", "BANKING_TRANSACTIONAL"),
        ("DEBIT_ORDER_SWITCHED", "DEBIT_ORDER_SWITCHED", "BANKING_TRANSACTIONAL"),
        ("SALARY_DEPOSIT", "SALARY_SWITCHED", "BANKING_TRANSACTIONAL"),
        ("SALARY_SWITCHED", "SALARY_SWITCHED", "BANKING_TRANSACTIONAL"),
        ("FIRST_PREMIUM_PAID", "FIRST_PREMIUM_PAID", "INSURANCE_POLICY"),
    ],
)
async def test_all_qualifying_events_route_expected_progress_event(
    monkeypatch,
    event_type,
    expected_progress_event_type,
    expected_journey_code,
):
    conn = FakeAsyncConnection()
    patch_async_db(monkeypatch, conn)

    enqueued = []
    monkeypatch.setattr(mod, "enqueue_event", lambda event: enqueued.append(event))

    await mod.ingest_event(
        {
            "referralTrackId": "66666666-6666-6666-6666-666666666666",
            "eventType": event_type,
            "tenant": "FNB",
            **({"policyNumber": "POL-123"} if expected_journey_code == "INSURANCE_POLICY" else {}),
            **({"refereeUCN": "UCN-666"} if expected_journey_code == "BANKING_TRANSACTIONAL" else {}),
        }
    )

    assert len(enqueued) == 1
    assert enqueued[0]["eventType"] == "REFERRAL_PROGRESS_RECORDED"
    assert enqueued[0]["progressEventType"] == expected_progress_event_type
    assert enqueued[0]["journeyCode"] == expected_journey_code
    assert enqueued[0]["journeyVersion"] == "v1"


@pytest.mark.asyncio
async def test_ingest_event_respects_explicit_insurance_journey(monkeypatch):
    conn = FakeAsyncConnection()
    patch_async_db(monkeypatch, conn)

    enqueued = []
    monkeypatch.setattr(mod, "enqueue_event", lambda event: enqueued.append(event))

    result = await mod.ingest_event(
        {
            "referralTrackId": "77777777-7777-7777-7777-777777777777",
            "eventType": "FIRST_PREMIUM_PAID",
            "journeyCode": "INSURANCE_POLICY",
            "journeyVersion": "v1",
            "policyNumber": "POL-123",
            "tenant": "FNB",
        }
    )

    assert result["processingStatus"] == "QUEUED"
    assert result["progressEventType"] == "FIRST_PREMIUM_PAID"
    assert result["journeyCode"] == "INSURANCE_POLICY"
    assert enqueued[0]["journeyCode"] == "INSURANCE_POLICY"


@pytest.mark.asyncio
async def test_ingest_event_ignores_insurance_event_missing_policy_number(monkeypatch):
    conn = FakeAsyncConnection()
    patch_async_db(monkeypatch, conn)

    enqueued = []
    monkeypatch.setattr(mod, "enqueue_event", lambda event: enqueued.append(event))

    result = await mod.ingest_event(
        {
            "referralTrackId": "88888888-8888-8888-8888-888888888888",
            "eventType": "FIRST_PREMIUM_PAID",
            "journeyCode": "INSURANCE_POLICY",
            "journeyVersion": "v1",
            "tenant": "FNB",
        }
    )

    assert result["processingStatus"] == "IGNORED"
    assert result["queued"] is False
    assert enqueued == []
