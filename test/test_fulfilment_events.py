from __future__ import annotations

import pytest

from services import fulfilment_events as mod


@pytest.mark.asyncio
async def test_publish_reward_fulfilment_requested_builds_and_enqueues_event(
    monkeypatch,
):
    published = {}

    async def fake_enqueue_event(event):
        published["event"] = event

    monkeypatch.setattr(mod, "enqueue_event", fake_enqueue_event)

    event = await mod.publish_reward_fulfilment_requested(
        tenant_code="FNB",
        reward_id="reward-123",
        reward_type="CASH",
        reward_value=100.0,
        recipient_ucn="123456789",
        currency="ZAR",
        journey_code="MAIN_BANK_SWITCH",
        milestone_code="ACCOUNT_OPENED",
        product_code="DDA13",
        correlation_id="corr-123",
        metadata={"source": "unit-test"},
    )

    assert published["event"] == event
    assert event["eventType"] == mod.REWARD_FULFILMENT_REQUESTED
    assert event["eventId"]
    assert event["correlationId"] == "corr-123"
    assert event["tenantCode"] == "FNB"
    assert event["rewardId"] == "reward-123"
    assert event["rewardType"] == "CASH"
    assert event["rewardValue"] == 100.0
    assert event["recipientUcn"] == "123456789"
    assert event["currency"] == "ZAR"
    assert event["journeyCode"] == "MAIN_BANK_SWITCH"
    assert event["milestoneCode"] == "ACCOUNT_OPENED"
    assert event["productCode"] == "DDA13"
    assert event["metadata"] == {"source": "unit-test"}


@pytest.mark.asyncio
async def test_publish_reward_fulfilment_requested_defaults_optional_fields(
    monkeypatch,
):
    published = {}

    async def fake_enqueue_event(event):
        published["event"] = event

    monkeypatch.setattr(mod, "enqueue_event", fake_enqueue_event)

    event = await mod.publish_reward_fulfilment_requested(
        tenant_code="FNB",
        reward_id="reward-456",
        reward_type="EBUCKS",
        reward_value=500.0,
    )

    assert published["event"] == event
    assert event["eventType"] == mod.REWARD_FULFILMENT_REQUESTED
    assert event["eventId"]
    assert event["correlationId"]
    assert event["tenantCode"] == "FNB"
    assert event["rewardId"] == "reward-456"
    assert event["rewardType"] == "EBUCKS"
    assert event["rewardValue"] == 500.0
    assert event["recipientUcn"] is None
    assert event["currency"] is None
    assert event["journeyCode"] is None
    assert event["milestoneCode"] is None
    assert event["productCode"] is None
    assert event["metadata"] == {}