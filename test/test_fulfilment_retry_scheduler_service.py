from datetime import datetime, timezone

import pytest

import services.fulfilment_retry_scheduler_service as service
from services.fulfilment_retry_policy_service import FulfilmentRetryPolicy


def _policy():
    return FulfilmentRetryPolicy(
        provider_key="CASH_PROVIDER",
        max_attempts=3,
        backoff_seconds=60,
        retryable_error_codes={"TIMEOUT"},
        non_retryable_error_codes={"INVALID_ACCOUNT"},
    )


def test_calculate_next_retry_at():
    now = datetime(2026, 5, 29, 12, 0, 0, tzinfo=timezone.utc)

    result = service.calculate_next_retry_at(
        policy=_policy(),
        attempt_no=2,
        now=now,
    )

    assert result == datetime(2026, 5, 29, 12, 2, 0, tzinfo=timezone.utc)


def test_build_fulfilment_retry_metadata():
    next_retry_at = datetime(2026, 5, 29, 12, 2, 0, tzinfo=timezone.utc)

    result = service.build_fulfilment_retry_metadata(
        audit_id="audit-123",
        idempotency_key="KEY-123",
        attempt_no=2,
        max_attempts=3,
        next_retry_at=next_retry_at,
        failure_reason="provider timeout",
        existing_metadata={"existing": "value"},
    )

    assert result == {
        "existing": "value",
        "retry": True,
        "source_audit_id": "audit-123",
        "idempotency_key": "KEY-123",
        "attempt_no": 2,
        "max_attempts": 3,
        "next_retry_at": "2026-05-29T12:02:00+00:00",
        "failure_reason": "provider timeout",
    }


def test_build_fulfilment_retry_metadata_without_existing_metadata():
    next_retry_at = datetime(2026, 5, 29, 12, 1, 0, tzinfo=timezone.utc)

    result = service.build_fulfilment_retry_metadata(
        audit_id="audit-123",
        idempotency_key="KEY-123",
        attempt_no=1,
        max_attempts=3,
        next_retry_at=next_retry_at,
        failure_reason="temporary failure",
        existing_metadata=None,
    )

    assert result["retry"] is True
    assert result["source_audit_id"] == "audit-123"
    assert result["next_retry_at"] == "2026-05-29T12:01:00+00:00"


@pytest.mark.asyncio
async def test_schedule_fulfilment_retry(monkeypatch):
    published = {}

    async def fake_publish_reward_fulfilment_requested(**kwargs):
        published.update(kwargs)
        return {
            "eventId": "event-123",
            **kwargs,
        }

    monkeypatch.setattr(
        service,
        "publish_reward_fulfilment_requested",
        fake_publish_reward_fulfilment_requested,
    )

    result = await service.schedule_fulfilment_retry(
        tenant_code="FNB",
        reward_id="reward-123",
        reward_type="CASH",
        reward_value=100.0,
        recipient_ucn="123456789",
        currency="ZAR",
        journey_code="MAIN_BANK_SWITCH",
        milestone_code="ACCOUNT_OPENED",
        product_code="DDA13",
        audit_id="audit-123",
        idempotency_key="KEY-123",
        attempt_no=2,
        max_attempts=3,
        policy=_policy(),
        failure_reason="provider timeout",
        metadata={"correlation_id": "corr-123"},
    )

    assert result["status"] == "retry_scheduled"
    assert result["audit_id"] == "audit-123"
    assert result["attempt_no"] == 2
    assert result["max_attempts"] == 3
    assert result["event"]["eventId"] == "event-123"

    assert published["tenant_code"] == "FNB"
    assert published["reward_id"] == "reward-123"
    assert published["reward_type"] == "CASH"
    assert published["reward_value"] == 100.0
    assert published["recipient_ucn"] == "123456789"
    assert published["metadata"]["retry"] is True
    assert published["metadata"]["source_audit_id"] == "audit-123"
    assert published["metadata"]["idempotency_key"] == "KEY-123"
    assert published["metadata"]["attempt_no"] == 2
    assert published["metadata"]["max_attempts"] == 3
    assert published["metadata"]["failure_reason"] == "provider timeout"