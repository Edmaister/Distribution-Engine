import json

import pytest

from services.fulfilment_idempotency import build_fulfilment_idempotency_key
from services.fulfilment_status import FulfilmentStatus
import services.fulfilment_audit_service as service


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


def test_build_fulfilment_idempotency_key_normalises_values():
    key = build_fulfilment_idempotency_key(
        tenant_code="fnb",
        referral_track_id="ref123",
        reward_type="cash",
        beneficiary_ucn="20260409",
        journey_stage="account_opened",
    )

    assert key == "FNB:REF123:CASH:20260409:ACCOUNT_OPENED"


def test_build_fulfilment_idempotency_key_handles_missing_values():
    key = build_fulfilment_idempotency_key(
        tenant_code="fnb",
        referral_track_id=None,
        reward_type="cash",
        beneficiary_ucn=None,
        journey_stage=None,
    )

    assert key == "FNB:NO_TRACK_ID:CASH:NO_BENEFICIARY:DEFAULT"


@pytest.mark.asyncio
async def test_create_fulfilment_audit_record(monkeypatch):
    cursor = FakeAsyncDbCursor(
        row={
            "audit_id": "audit-123",
            "status": "PENDING",
        }
    )
    patch_db(monkeypatch, cursor)

    result = await service.create_fulfilment_audit_record(
        tenant_code="FNB",
        referral_track_id="REF123",
        referrer_ucn="111",
        referee_ucn="222",
        reward_type="CASH",
        fulfilment_provider="CASH_PROVIDER",
        idempotency_key="FNB:REF123:CASH:222:ACCOUNT_OPENED",
        correlation_id="corr-1",
        event_type="ACCOUNT_OPENED",
    )

    assert result == {
        "audit_id": "audit-123",
        "status": "PENDING",
    }

    query, args = cursor.executed[0]
    assert "INSERT INTO fulfilment_audit" in query
    assert args[0] == "FNB"
    assert args[6] == "FNB:REF123:CASH:222:ACCOUNT_OPENED"
    assert args[7] == FulfilmentStatus.PENDING.value


@pytest.mark.asyncio
async def test_get_existing_audit_by_idempotency_key_found(monkeypatch):
    cursor = FakeAsyncDbCursor(
        row={
            "audit_id": "audit-123",
            "status": "SUCCESS",
            "provider_reference": "provider-ref-1",
        }
    )
    patch_db(monkeypatch, cursor)

    result = await service.get_existing_audit_by_idempotency_key(
        "FNB:REF123:CASH:222:ACCOUNT_OPENED"
    )

    assert result == {
        "audit_id": "audit-123",
        "status": "SUCCESS",
        "provider_reference": "provider-ref-1",
    }

    query, args = cursor.executed[0]
    assert "WHERE idempotency_key = $1" in query
    assert args == ("FNB:REF123:CASH:222:ACCOUNT_OPENED",)


@pytest.mark.asyncio
async def test_get_existing_audit_by_idempotency_key_not_found(monkeypatch):
    cursor = FakeAsyncDbCursor(row=None)
    patch_db(monkeypatch, cursor)

    result = await service.get_existing_audit_by_idempotency_key("missing-key")

    assert result is None


@pytest.mark.asyncio
async def test_mark_fulfilment_processing(monkeypatch):
    cursor = FakeAsyncDbCursor()
    patch_db(monkeypatch, cursor)

    await service.mark_fulfilment_processing(audit_id="audit-123")

    query, args = cursor.executed[0]
    assert "status = $1" in query
    assert args == (FulfilmentStatus.PROCESSING.value, "audit-123")


@pytest.mark.asyncio
async def test_mark_fulfilment_success(monkeypatch):
    cursor = FakeAsyncDbCursor()
    patch_db(monkeypatch, cursor)

    await service.mark_fulfilment_success(
        audit_id="audit-123",
        provider_reference="provider-ref-1",
        provider_status="PAID",
        provider_response={"ok": True},
    )

    query, args = cursor.executed[0]
    assert "provider_reference = $2" in query
    assert args[0] == FulfilmentStatus.SUCCESS.value
    assert args[1] == "provider-ref-1"
    assert args[2] == "PAID"
    assert json.loads(args[3]) == {"ok": True}
    assert args[4] == "audit-123"


@pytest.mark.asyncio
async def test_mark_fulfilment_failed_retryable(monkeypatch):
    cursor = FakeAsyncDbCursor()
    patch_db(monkeypatch, cursor)

    await service.mark_fulfilment_failed(
        audit_id="audit-123",
        failure_reason="Provider timeout",
        error_code="TIMEOUT",
        retryable=True,
    )

    query, args = cursor.executed[0]
    assert "failure_reason = $2" in query
    assert args == (
        FulfilmentStatus.FAILED_RETRYABLE.value,
        "Provider timeout",
        "TIMEOUT",
        "audit-123",
    )


@pytest.mark.asyncio
async def test_mark_fulfilment_failed_final(monkeypatch):
    cursor = FakeAsyncDbCursor()
    patch_db(monkeypatch, cursor)

    await service.mark_fulfilment_failed(
        audit_id="audit-123",
        failure_reason="Invalid account",
        error_code="INVALID_ACCOUNT",
        retryable=False,
    )

    query, args = cursor.executed[0]
    assert "status = $1" in query
    assert args[0] == FulfilmentStatus.FAILED_FINAL.value


@pytest.mark.asyncio
async def test_increment_fulfilment_attempt_not_exhausted(monkeypatch):
    cursor = FakeAsyncDbCursor(
        row={
            "attempt_no": 2,
            "max_attempts": 3,
        }
    )
    patch_db(monkeypatch, cursor)

    result = await service.increment_fulfilment_attempt(audit_id="audit-123")

    assert result == {
        "attempt_no": 2,
        "max_attempts": 3,
        "retries_exhausted": False,
    }


@pytest.mark.asyncio
async def test_increment_fulfilment_attempt_exhausted(monkeypatch):
    cursor = FakeAsyncDbCursor(
        row={
            "attempt_no": 3,
            "max_attempts": 3,
        }
    )
    patch_db(monkeypatch, cursor)

    result = await service.increment_fulfilment_attempt(audit_id="audit-123")

    assert result == {
        "attempt_no": 3,
        "max_attempts": 3,
        "retries_exhausted": True,
    }