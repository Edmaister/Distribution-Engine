from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

import utils.queue as queue


@pytest.mark.asyncio
async def test_write_to_local_queue_writes_jsonl(tmp_path, monkeypatch):
    queue_file = tmp_path / "local_events.jsonl"

    monkeypatch.setattr(queue, "LOCAL_QUEUE_FILE", str(queue_file))

    log_mock = MagicMock()
    monkeypatch.setattr(queue, "log_event", log_mock)

    payload = {
        "eventType": "REFERRAL_PROGRESS_RECORDED",
        "referralTrackId": "track-123",
        "tenantCode": "FNB",
    }

    await queue._write_to_local_queue(payload)

    assert queue_file.exists()

    lines = queue_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

    written_payload = json.loads(lines[0])
    assert written_payload == payload

    log_mock.assert_called_once()
    assert log_mock.call_args.kwargs["message"] == "LOCAL_EVENT_QUEUED"
    assert log_mock.call_args.kwargs["component"] == "queue"


@pytest.mark.asyncio
async def test_enqueue_event_uses_local_queue_when_sqs_url_missing(
    tmp_path,
    monkeypatch,
):
    queue_file = tmp_path / "local_events.jsonl"

    monkeypatch.setattr(queue, "SQS_QUEUE_URL", "")
    monkeypatch.setattr(queue, "LOCAL_QUEUE_FILE", str(queue_file))
    monkeypatch.setattr(queue, "log_event", MagicMock())

    payload = {
        "eventType": "TEST_EVENT",
        "referralTrackId": "track-local",
        "tenantCode": "FNB",
    }

    await queue.enqueue_event(payload)

    lines = queue_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == payload


@pytest.mark.asyncio
async def test_enqueue_event_sends_message_to_sqs_when_queue_url_present(
    monkeypatch,
):
    monkeypatch.setattr(queue, "SQS_QUEUE_URL", "https://sqs.test/queue")
    monkeypatch.setattr(queue, "AWS_REGION", "af-south-1")

    log_mock = MagicMock()
    monkeypatch.setattr(queue, "log_event", log_mock)

    send_message_mock = AsyncMock()

    sqs_client = MagicMock()
    sqs_client.send_message = send_message_mock

    async_context_manager = AsyncMock()
    async_context_manager.__aenter__.return_value = sqs_client
    async_context_manager.__aexit__.return_value = None

    session_mock = MagicMock()
    session_mock.client.return_value = async_context_manager

    session_class_mock = MagicMock(return_value=session_mock)
    monkeypatch.setattr(queue.aioboto3, "Session", session_class_mock)

    payload = {
        "eventType": "REWARD_FULFILMENT_REQUESTED",
        "rewardId": "reward-123",
        "referralTrackId": "track-456",
        "tenantCode": "FNB",
        "sourceSystem": "pytest",
        "sourceEventId": "event-789",
    }

    await queue.enqueue_event(payload)

    session_class_mock.assert_called_once()

    session_mock.client.assert_called_once_with(
        "sqs",
        region_name="af-south-1",
    )

    send_message_mock.assert_awaited_once_with(
        QueueUrl="https://sqs.test/queue",
        MessageBody=json.dumps(payload, default=str),
    )

    log_mock.assert_called_once()
    assert log_mock.call_args.kwargs["message"] == "SQS_MESSAGE_SENT"
    assert log_mock.call_args.kwargs["component"] == "queue"


@pytest.mark.asyncio
async def test_enqueue_event_serialises_non_json_values_in_sqs(monkeypatch):
    from datetime import datetime

    monkeypatch.setattr(queue, "SQS_QUEUE_URL", "https://sqs.test/queue")
    monkeypatch.setattr(queue, "AWS_REGION", "af-south-1")
    monkeypatch.setattr(queue, "log_event", MagicMock())

    send_message_mock = AsyncMock()

    sqs_client = MagicMock()
    sqs_client.send_message = send_message_mock

    async_context_manager = AsyncMock()
    async_context_manager.__aenter__.return_value = sqs_client
    async_context_manager.__aexit__.return_value = None

    session_mock = MagicMock()
    session_mock.client.return_value = async_context_manager

    monkeypatch.setattr(
        queue.aioboto3,
        "Session",
        MagicMock(return_value=session_mock),
    )

    payload = {
        "eventType": "TEST_EVENT",
        "createdAt": datetime(2026, 5, 25, 12, 0, 0),
    }

    await queue.enqueue_event(payload)

    sent_body = send_message_mock.await_args.kwargs["MessageBody"]
    decoded = json.loads(sent_body)

    assert decoded["eventType"] == "TEST_EVENT"
    assert decoded["createdAt"] == "2026-05-25 12:00:00"