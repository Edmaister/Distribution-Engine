import pytest

import services.leaderboard_events as mod


@pytest.mark.asyncio
async def test_publish_leaderboard_rebuild_requested_stub(
    monkeypatch,
):
    class Settings:
        app_sqs_queue_url = None
        aws_region = "af-south-1"

    called = {}

    async def fake_rebuild(
        *,
        tenant_code,
        referrer_ucn,
    ):
        called["tenant_code"] = tenant_code
        called["referrer_ucn"] = referrer_ucn

    monkeypatch.setattr(
        mod,
        "get_settings",
        lambda: Settings(),
    )

    monkeypatch.setattr(
        mod,
        "rebuild_leaderboard_for_referrer",
        fake_rebuild,
    )

    result = await mod.publish_leaderboard_rebuild_requested(
        tenant_code="FNB",
        referrer_ucn="123",
        correlation_id="corr-1",
        referral_track_id="track-1",
    )

    assert result["status"] == "stubbed"

    assert (
        result["event"]["eventType"]
        ==
        mod.EVENT_TYPE_LEADERBOARD_REBUILD_REQUESTED
    )

    assert called == {
        "tenant_code": "FNB",
        "referrer_ucn": "123",
    }


@pytest.mark.asyncio
async def test_publish_leaderboard_rebuild_requested_sqs(
    monkeypatch,
):
    class Settings:
        app_sqs_queue_url = (
            "https://sqs.test/queue"
        )
        aws_region = "af-south-1"

    class FakeSqs:
        def send_message(
            self,
            QueueUrl,
            MessageBody,
        ):
            return {
                "MessageId":
                "msg-1"
            }

    monkeypatch.setattr(
        mod,
        "get_settings",
        lambda: Settings(),
    )

    monkeypatch.setattr(
        mod.boto3,
        "client",
        lambda *a,
        **k:
        FakeSqs(),
    )

    result = (
        await
        mod.publish_leaderboard_rebuild_requested(
            tenant_code="FNB",
            referrer_ucn="123",
            correlation_id="corr-1",
            referral_track_id="track-1",
        )
    )

    assert (
        result["status"]
        == "published"
    )

    assert (
        result["message_id"]
        == "msg-1"
    )


@pytest.mark.asyncio
async def test_send_sqs_message_async(
    monkeypatch,
):
    class FakeSqs:
        def send_message(
            self,
            QueueUrl,
            MessageBody,
        ):
            return {
                "MessageId":
                "abc"
            }

    monkeypatch.setattr(
        mod.boto3,
        "client",
        lambda *a,
        **k:
        FakeSqs(),
    )

    result = (
        await
        mod._send_sqs_message_async(
            queue_url=
            "queue",
            event=
            {"x": 1},
            aws_region=
            "af-south-1",
        )
    )

    assert (
        result["MessageId"]
        == "abc"
    )


def test_build_event():
    result = (
        mod
        ._build_leaderboard_rebuild_event(
            tenant_code=
            "FNB",
            referrer_ucn=
            "123",
            correlation_id=
            "corr",
            referral_track_id=
            "track",
        )
    )

    assert (
        result["eventType"]
        ==
        mod
        .EVENT_TYPE_LEADERBOARD_REBUILD_REQUESTED
    )

    assert (
        result["tenantCode"]
        == "FNB"
    )

    assert (
        result["referrerUcn"]
        == "123"
    )

    assert (
        result["correlationId"]
        == "corr"
    )

    assert (
        result["referralTrackId"]
        == "track"
    )


def test_build_event_generates_uuid():
    result = (
        mod
        ._build_leaderboard_rebuild_event(
            tenant_code=
            "FNB",
            referrer_ucn=
            "123",
        )
    )

    assert (
        result["correlationId"]
        is not None
    )