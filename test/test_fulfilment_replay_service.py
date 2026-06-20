import pytest

import services.fulfilment_replay_service as service


class FakeAsyncDbCursor:
    def __init__(self, row=None):
        self.row = row
        self.executed = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, query, *args):
        self.executed.append((query, args))

    async def fetchrow(self, query, *args):
        self.executed.append((query, args))
        return self.row


def patch_db(monkeypatch, cursor):
    def fake_async_db_cursor():
        return cursor

    monkeypatch.setattr(service, "async_db_cursor", fake_async_db_cursor)


@pytest.mark.asyncio
async def test_replay_failed_fulfilment_not_found(monkeypatch):
    cursor = FakeAsyncDbCursor(row=None)
    patch_db(monkeypatch, cursor)

    result = await service.replay_failed_fulfilment(audit_id="missing")

    assert result == {
        "status": "not_found",
        "audit_id": "missing",
    }


@pytest.mark.asyncio
async def test_replay_failed_fulfilment_skips_success(monkeypatch):
    cursor = FakeAsyncDbCursor(
        row={
            "audit_id": "audit-123",
            "status": "SUCCESS",
        }
    )
    patch_db(monkeypatch, cursor)

    result = await service.replay_failed_fulfilment(audit_id="audit-123")

    assert result == {
        "status": "skipped",
        "reason": "already_successful",
        "audit_id": "audit-123",
    }


@pytest.mark.asyncio
async def test_replay_failed_fulfilment_requests_replay(monkeypatch):
    cursor = FakeAsyncDbCursor(
        row={
            "audit_id": "audit-123",
            "tenant_code": "FNB",
            "referral_track_id": "REF123",
            "referrer_ucn": "111",
            "referee_ucn": "222",
            "reward_type": "CASH",
            "fulfilment_provider": "CASH_PROVIDER",
            "idempotency_key": "OLD-KEY",
            "status": "FAILED_FINAL",
            "attempt_no": 3,
            "max_attempts": 3,
            "correlation_id": "reward-123",
            "event_type": "REWARD_FULFILMENT_REQUESTED",
            "failure_reason": "provider hard failure",
            "error_code": "TIMEOUT",
            "provider_reference": None,
            "provider_status": None,
            "provider_response": None,
        }
    )
    patch_db(monkeypatch, cursor)

    published = {}

    async def fake_publish_reward_fulfilment_requested(**kwargs):
        published.update(kwargs)
        return {"eventId": "event-123", **kwargs}

    monkeypatch.setattr(
        service,
        "publish_reward_fulfilment_requested",
        fake_publish_reward_fulfilment_requested,
    )

    result = await service.replay_failed_fulfilment(audit_id="audit-123")

    assert result["status"] == "replay_requested"
    assert result["audit_id"] == "audit-123"
    assert result["event"]["eventId"] == "event-123"

    assert published["tenant_code"] == "FNB"
    assert published["reward_id"] == "reward-123"
    assert published["reward_type"] == "CASH"
    assert published["recipient_ucn"] == "222"
    assert published["metadata"]["replay"] is True
    assert published["metadata"]["source_audit_id"] == "audit-123"
    assert published["metadata"]["original_idempotency_key"] == "OLD-KEY"

@pytest.mark.asyncio
async def test_replay_failed_fulfilment_skips_processing(monkeypatch):
    cursor = FakeAsyncDbCursor(
        row={
            "audit_id": "audit-123",
            "status": "PROCESSING",
        }
    )
    patch_db(monkeypatch, cursor)

    result = await service.replay_failed_fulfilment(audit_id="audit-123")

    assert result == {
        "status": "skipped",
        "reason": "currently_processing",
        "audit_id": "audit-123",
    }


@pytest.mark.asyncio
async def test_replay_failed_fulfilment_skips_non_replayable_status(monkeypatch):
    cursor = FakeAsyncDbCursor(
        row={
            "audit_id": "audit-123",
            "status": "PENDING",
        }
    )
    patch_db(monkeypatch, cursor)

    result = await service.replay_failed_fulfilment(audit_id="audit-123")

    assert result == {
        "status": "skipped",
        "reason": "status_not_replayable:PENDING",
        "audit_id": "audit-123",
    }


@pytest.mark.asyncio
async def test_get_fulfilment_audit_by_id_returns_dict(monkeypatch):
    cursor = FakeAsyncDbCursor(
        row={
            "audit_id": "audit-123",
            "tenant_code": "FNB",
            "status": "FAILED_FINAL",
        }
    )
    patch_db(monkeypatch, cursor)

    result = await service.get_fulfilment_audit_by_id(audit_id="audit-123")

    assert result == {
        "audit_id": "audit-123",
        "tenant_code": "FNB",
        "status": "FAILED_FINAL",
    }


@pytest.mark.asyncio
async def test_mark_fulfilment_replay_requested(monkeypatch):
    cursor = FakeAsyncDbCursor()
    patch_db(monkeypatch, cursor)

    await service.mark_fulfilment_replay_requested(audit_id="audit-123")

    query, args = cursor.executed[0]

    assert "status = 'PENDING'" in query
    assert args == ("audit-123",)