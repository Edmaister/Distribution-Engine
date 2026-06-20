from __future__ import annotations

import json

import services.dlq_service as dlq


def test_publish_to_dlq_logs_stub_when_no_dlq_url(monkeypatch, caplog):
    class Settings:
        app_sqs_dlq_url = None
        aws_region = "eu-west-1"

    monkeypatch.setattr(dlq, "get_settings", lambda: Settings())

    event = {
        "eventType": "LEADERBOARD_REBUILD_REQUESTED",
        "tenantCode": "FNB",
        "referrerUcn": "123",
    }

    with caplog.at_level("ERROR"):
        dlq.publish_to_dlq(event=event, error="boom")

    assert "DLQ_STUB_EVENT" in caplog.text


def test_publish_to_dlq_sends_to_sqs_when_configured(monkeypatch):
    class Settings:
        app_sqs_dlq_url = "https://sqs.example.com/dlq"
        aws_region = "eu-west-1"

    sent = {}

    class FakeSQS:
        def send_message(self, **kwargs):
            sent.update(kwargs)
            return {"MessageId": "msg-123"}

    class FakeBoto3:
        @staticmethod
        def client(service_name, region_name=None):
            assert service_name == "sqs"
            assert region_name == "eu-west-1"
            return FakeSQS()

    monkeypatch.setattr(dlq, "get_settings", lambda: Settings())
    monkeypatch.setattr(dlq, "boto3", FakeBoto3)

    event = {
        "eventType": "REFERRAL_PROGRESS_RECORDED",
        "tenantCode": "FNB",
        "referralTrackId": "track-123",
    }

    dlq.publish_to_dlq(event=event, error="worker failed")

    assert sent["QueueUrl"] == "https://sqs.example.com/dlq"

    body = json.loads(sent["MessageBody"])
    assert body == {
        "originalEvent": event,
        "error": "worker failed",
    }


def test_publish_to_dlq_handles_sqs_failure(monkeypatch, caplog):
    class Settings:
        app_sqs_dlq_url = "https://sqs.example.com/dlq"
        aws_region = "eu-west-1"

    class BrokenSQS:
        def send_message(self, **kwargs):
            raise RuntimeError("sqs unavailable")

    class FakeBoto3:
        @staticmethod
        def client(service_name, region_name=None):
            return BrokenSQS()

    monkeypatch.setattr(dlq, "get_settings", lambda: Settings())
    monkeypatch.setattr(dlq, "boto3", FakeBoto3)

    with caplog.at_level("ERROR"):
        dlq.publish_to_dlq(
            event={"eventType": "BROKEN_EVENT"},
            error="boom",
        )

    assert "Failed to publish event to DLQ" in caplog.text