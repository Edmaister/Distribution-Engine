from __future__ import annotations

from types import SimpleNamespace
import hashlib
import hmac
import json

import pytest

from services import channel_readiness_service as service


@pytest.fixture(autouse=True)
def reset_channel_delivery_state():
    service._reset_channel_delivery_state_for_tests()
    yield
    service._reset_channel_delivery_state_for_tests()


def test_channel_readiness_reports_attention_when_providers_missing(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            channel_email_provider_url=None,
            channel_email_provider_secret=None,
            channel_whatsapp_provider_url=None,
            channel_whatsapp_provider_secret=None,
            channel_sms_provider_url=None,
            channel_sms_provider_secret=None,
            channel_ussd_provider_url=None,
            channel_ussd_provider_secret=None,
        ),
    )

    readiness = service.get_channel_readiness()

    assert readiness["status"] == "ATTENTION"
    assert readiness["configuration_source"] == "channel_catalog"
    assert readiness["summary"]["count"] == 4
    assert readiness["summary"]["attention_count"] == 4
    assert {item["channel_code"] for item in readiness["items"]} == {
        "EMAIL",
        "WHATSAPP",
        "SMS",
        "USSD",
    }
    assert readiness["items"][0]["missing_components"] == [
        "provider_url",
        "provider_secret",
    ]


def test_channel_readiness_reports_ready_when_all_providers_configured(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            channel_email_provider_url="https://channels.example/email",
            channel_email_provider_secret="email-secret",
            channel_email_provider_ref="email-provider-1",
            channel_email_provider_approved=True,
            channel_email_provider_scopes="REFERRAL_SAAS",
            channel_whatsapp_provider_url="https://channels.example/whatsapp",
            channel_whatsapp_provider_secret="whatsapp-secret",
            channel_sms_provider_url="https://channels.example/sms",
            channel_sms_provider_secret="sms-secret",
            channel_ussd_provider_url="https://channels.example/ussd",
            channel_ussd_provider_secret="ussd-secret",
        ),
    )

    readiness = service.get_channel_readiness()

    assert readiness["status"] == "READY"
    assert readiness["summary"]["ready_count"] == 4
    assert all(item["provider_configured"] for item in readiness["items"])
    email = next(item for item in readiness["items"] if item["channel_code"] == "EMAIL")
    assert email["provider_ref"] == "email-provider-1"
    assert email["provider_approved"] is True
    assert email["provider_scopes"] == ["REFERRAL_SAAS"]
    assert email["approved_for_referral_saas"] is True


def test_recommend_channels_scores_event_audience_and_provider_fit(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            channel_email_provider_url=None,
            channel_email_provider_secret=None,
            channel_whatsapp_provider_url="https://channels.example/whatsapp",
            channel_whatsapp_provider_secret="whatsapp-secret",
            channel_sms_provider_url=None,
            channel_sms_provider_secret=None,
            channel_ussd_provider_url="https://channels.example/ussd",
            channel_ussd_provider_secret="ussd-secret",
        ),
    )

    result = service.recommend_channels(
        event_type="REFERRAL_STARTED",
        audience="CONSUMER",
        target_channels=["USSD", "WHATSAPP"],
        distributor_channels=["USSD"],
    )

    assert result["status"] == "READY"
    assert result["top_channel"]["channel_code"] == "USSD"
    assert result["top_channel"]["provider_configured"] is True
    assert "event: supports REFERRAL_STARTED" in result["top_channel"]["reasons"]
    assert "distributor: supported channel" in result["top_channel"]["reasons"]
    assert result["guardrail"].startswith("Channel recommendations are explainable")


def test_recommend_channels_keeps_unconfigured_channels_visible(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            channel_email_provider_url=None,
            channel_email_provider_secret=None,
            channel_whatsapp_provider_url=None,
            channel_whatsapp_provider_secret=None,
            channel_sms_provider_url=None,
            channel_sms_provider_secret=None,
            channel_ussd_provider_url=None,
            channel_ussd_provider_secret=None,
        ),
    )

    result = service.recommend_channels(
        event_type="OUTCOME_COMPLETED",
        audience="DISTRIBUTOR",
        target_channels=["SMS"],
    )

    assert result["status"] == "ATTENTION"
    assert result["top_channel"]["channel_code"] in {"SMS", "WHATSAPP"}
    assert any(
        item["provider_configured"] is False and item["provider_status"] == "ATTENTION"
        for item in result["items"]
    )


def test_recommend_channels_prefers_email_for_membership_invitation(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            channel_email_provider_url="https://channels.example/email",
            channel_email_provider_secret="email-secret",
            channel_whatsapp_provider_url=None,
            channel_whatsapp_provider_secret=None,
            channel_sms_provider_url=None,
            channel_sms_provider_secret=None,
            channel_ussd_provider_url=None,
            channel_ussd_provider_secret=None,
        ),
    )

    result = service.recommend_channels(
        event_type="MEMBERSHIP_INVITATION",
        audience="ADMIN",
        target_channels=["EMAIL"],
    )

    assert result["status"] == "READY"
    assert result["top_channel"]["channel_code"] == "EMAIL"
    assert result["top_channel"]["provider_configured"] is True
    assert "event: supports MEMBERSHIP_INVITATION" in result["top_channel"]["reasons"]


@pytest.mark.asyncio
async def test_dispatch_channel_message_posts_signed_payload(monkeypatch):
    class FakeResponse:
        status_code = 202
        text = "queued"

    sent = []
    metric_calls = []
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            channel_whatsapp_provider_url="https://channels.example/whatsapp",
            channel_whatsapp_provider_secret="whatsapp-secret",
        ),
    )

    async def fake_post_channel_payload(url, payload, secret):
        sent.append((url, payload, secret))
        return FakeResponse()

    monkeypatch.setattr(service, "_post_channel_payload", fake_post_channel_payload)
    monkeypatch.setattr(
        service,
        "channel_dispatch_observe",
        lambda **kwargs: metric_calls.append(kwargs),
    )

    result = await service.dispatch_channel_message(
        channel_code="whatsapp",
        tenant_code="fnb",
        recipient="+27123456789",
        message="Your referral is ready",
        context={"referral_track_id": "track-1", "consent_verified": True},
    )

    assert result["status"] == "SENT"
    assert result["delivery_id"].startswith("CHD-")
    assert result["channel_code"] == "WHATSAPP"
    assert result["recipient_ref"].startswith("recipient:")
    assert sent[0][0] == "https://channels.example/whatsapp"
    assert sent[0][1]["tenant_code"] == "FNB"
    assert sent[0][2] == "whatsapp-secret"
    assert metric_calls == [
        {
            "tenant": "FNB",
            "channel": "WHATSAPP",
            "adapter": "MESSAGING",
            "delivery_status": "SENT",
            "provider_status": 202,
            "latency_seconds": metric_calls[0]["latency_seconds"],
        }
    ]
    assert metric_calls[0]["latency_seconds"] >= 0
    assert "+27123456789" not in str(metric_calls[0])
    assert "Your referral is ready" not in str(metric_calls[0])
    deliveries = service.list_channel_deliveries()
    assert deliveries["summary"]["sent"] == 1
    assert deliveries["items"][0]["status"] == "SENT"
    assert "+27123456789" not in str(deliveries)
    assert "Your referral is ready" not in str(deliveries)
    audit = service.list_channel_audit()
    assert [item["event_type"] for item in audit["items"]] == [
        "QUEUED",
        "SENT",
    ]


@pytest.mark.asyncio
async def test_dispatch_channel_message_requires_consent(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            channel_sms_provider_url="https://channels.example/sms",
            channel_sms_provider_secret="sms-secret",
        ),
    )

    with pytest.raises(Exception) as exc:
        await service.dispatch_channel_message(
            channel_code="SMS",
            tenant_code="FNB",
            recipient="+27123456789",
            message="Your payout is ready",
            context={"referral_track_id": "track-1"},
        )

    assert getattr(exc.value, "status_code") == 403
    assert service.list_channel_deliveries()["summary"]["count"] == 0


@pytest.mark.asyncio
async def test_dispatch_channel_message_rejects_opted_out_recipient(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            channel_whatsapp_provider_url="https://channels.example/whatsapp",
            channel_whatsapp_provider_secret="whatsapp-secret",
        ),
    )

    with pytest.raises(Exception) as exc:
        await service.dispatch_channel_message(
            channel_code="WHATSAPP",
            tenant_code="FNB",
            recipient="+27123456789",
            message="Your referral is ready",
            context={"consent_verified": True, "opted_out": True},
        )

    assert getattr(exc.value, "status_code") == 409
    assert "opted out" in exc.value.detail


@pytest.mark.asyncio
async def test_channel_delivery_failure_is_retryable_for_transient_provider_error(monkeypatch):
    class FakeResponse:
        status_code = 503
        text = "temporary outage"

    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            channel_sms_provider_url="https://channels.example/sms",
            channel_sms_provider_secret="sms-secret",
        ),
    )

    async def fake_post_channel_payload(url, payload, secret):
        return FakeResponse()

    monkeypatch.setattr(service, "_post_channel_payload", fake_post_channel_payload)

    result = await service.dispatch_channel_message(
        channel_code="SMS",
        tenant_code="FNB",
        recipient="+27123456789",
        message="Your payout is ready",
        context={"consent_verified": True},
    )

    assert result["status"] == "FAILED"
    delivery = service.list_channel_deliveries()["items"][0]
    assert delivery["retryable"] is True
    assert delivery["attempt_count"] == 1
    assert delivery["next_retry_at"] is not None
    assert delivery["dead_letter_reason"] is None


@pytest.mark.asyncio
async def test_channel_delivery_dead_letters_non_retryable_provider_error(monkeypatch):
    class FakeResponse:
        status_code = 400
        text = "bad recipient"

    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            channel_sms_provider_url="https://channels.example/sms",
            channel_sms_provider_secret="sms-secret",
        ),
    )

    async def fake_post_channel_payload(url, payload, secret):
        return FakeResponse()

    monkeypatch.setattr(service, "_post_channel_payload", fake_post_channel_payload)

    result = await service.dispatch_channel_message(
        channel_code="SMS",
        tenant_code="FNB",
        recipient="+27123456789",
        message="Your payout is ready",
        context={"consent_verified": True},
    )

    assert result["status"] == "DEAD_LETTERED"
    deliveries = service.list_channel_deliveries()
    assert deliveries["summary"]["dead_lettered"] == 1
    assert deliveries["items"][0]["retryable"] is False
    assert deliveries["items"][0]["dead_letter_reason"] == "non_retryable_provider_status"
    audit_events = [item["event_type"] for item in service.list_channel_audit()["items"]]
    assert audit_events == ["QUEUED", "FAILED", "DEAD_LETTERED"]


@pytest.mark.asyncio
async def test_retry_channel_delivery_resends_failed_delivery(monkeypatch):
    class FakeFailedResponse:
        status_code = 503
        text = "temporary outage"

    class FakeSuccessResponse:
        status_code = 202
        text = "accepted"

    responses = [FakeFailedResponse(), FakeSuccessResponse()]
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            channel_whatsapp_provider_url="https://channels.example/whatsapp",
            channel_whatsapp_provider_secret="whatsapp-secret",
        ),
    )

    async def fake_post_channel_payload(url, payload, secret):
        return responses.pop(0)

    monkeypatch.setattr(service, "_post_channel_payload", fake_post_channel_payload)

    result = await service.dispatch_channel_message(
        channel_code="WHATSAPP",
        tenant_code="FNB",
        recipient="+27123456789",
        message="Your referral is ready",
        context={"consent_verified": True},
    )
    retry = await service.retry_channel_delivery(delivery_id=result["delivery_id"])

    assert retry["status"] == "SENT"
    assert retry["delivery"]["attempt_count"] == 2
    assert retry["delivery"]["retryable"] is False
    audit_events = [item["event_type"] for item in service.list_channel_audit()["items"]]
    assert audit_events == ["QUEUED", "FAILED", "RETRY_QUEUED", "SENT"]


@pytest.mark.asyncio
async def test_retry_channel_delivery_stops_after_max_attempts(monkeypatch):
    class FakeResponse:
        status_code = 503
        text = "temporary outage"

    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            channel_sms_provider_url="https://channels.example/sms",
            channel_sms_provider_secret="sms-secret",
        ),
    )

    async def fake_post_channel_payload(url, payload, secret):
        return FakeResponse()

    monkeypatch.setattr(service, "_post_channel_payload", fake_post_channel_payload)

    result = await service.dispatch_channel_message(
        channel_code="SMS",
        tenant_code="FNB",
        recipient="+27123456789",
        message="Your payout is ready",
        context={"consent_verified": True},
    )
    await service.retry_channel_delivery(delivery_id=result["delivery_id"])
    retry = await service.retry_channel_delivery(delivery_id=result["delivery_id"])

    assert retry["status"] == "DEAD_LETTERED"
    assert retry["delivery"]["attempt_count"] == 3
    assert retry["delivery"]["retryable"] is False
    assert retry["delivery"]["dead_letter_reason"] == "max_attempts_exhausted"

    with pytest.raises(Exception) as exc:
        await service.retry_channel_delivery(delivery_id=result["delivery_id"])

    assert getattr(exc.value, "status_code") == 409


@pytest.mark.asyncio
async def test_whatsapp_provider_adapter_shapes_and_signs_payload(monkeypatch):
    class FakeResponse:
        status_code = 202
        text = "queued"

    captured = {}

    def fake_post(url, data, headers, timeout):
        captured.update(
            {
                "url": url,
                "data": data,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return FakeResponse()

    monkeypatch.setattr(service.requests, "post", fake_post)

    response = await service._post_channel_payload(
        "https://channels.example/whatsapp",
        {
            "channel_code": "WHATSAPP",
            "tenant_code": "FNB",
            "recipient": "+27123456789",
            "message": "Your referral is ready",
            "context": {"referral_track_id": "track-1"},
            "sent_at": 1_700_000_000,
        },
        "whatsapp-secret",
    )

    body = json.loads(captured["data"])
    expected_signature = hmac.new(
        b"whatsapp-secret",
        captured["data"].encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    assert response.status_code == 202
    assert captured["url"] == "https://channels.example/whatsapp"
    assert captured["headers"]["X-Amplifi-Adapter"] == "WHATSAPP_PROVIDER"
    assert captured["headers"]["X-Amplifi-Signature"] == expected_signature
    assert body["to"] == "+27123456789"
    assert body["type"] == "text"
    assert body["text"]["body"] == "Your referral is ready"
    assert body["metadata"]["tenant_code"] == "FNB"
    assert body["metadata"]["context"]["referral_track_id"] == "track-1"


@pytest.mark.asyncio
async def test_sms_provider_adapter_shapes_and_signs_payload(monkeypatch):
    class FakeResponse:
        status_code = 202
        text = "accepted"

    captured = {}

    def fake_post(url, data, headers, timeout):
        captured.update(
            {
                "url": url,
                "data": data,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return FakeResponse()

    monkeypatch.setattr(service.requests, "post", fake_post)

    response = await service._post_channel_payload(
        "https://channels.example/sms",
        {
            "channel_code": "SMS",
            "tenant_code": "FNB",
            "recipient": "+27123456789",
            "message": "Your payout is ready",
            "context": {"wallet_id": "wallet-1"},
            "sent_at": 1_700_000_001,
        },
        "sms-secret",
    )

    body = json.loads(captured["data"])
    expected_signature = hmac.new(
        b"sms-secret",
        captured["data"].encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    assert response.status_code == 202
    assert captured["url"] == "https://channels.example/sms"
    assert captured["headers"]["X-Amplifi-Adapter"] == "SMS_PROVIDER"
    assert captured["headers"]["X-Amplifi-Signature"] == expected_signature
    assert body["to"] == "+27123456789"
    assert body["body"] == "Your payout is ready"
    assert body["metadata"]["tenant_code"] == "FNB"
    assert body["metadata"]["context"]["wallet_id"] == "wallet-1"


@pytest.mark.asyncio
async def test_ussd_provider_adapter_shapes_and_signs_payload(monkeypatch):
    class FakeResponse:
        status_code = 202
        text = "session accepted"

    captured = {}

    def fake_post(url, data, headers, timeout):
        captured.update(
            {
                "url": url,
                "data": data,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return FakeResponse()

    monkeypatch.setattr(service.requests, "post", fake_post)

    response = await service._post_channel_payload(
        "https://channels.example/ussd",
        {
            "channel_code": "USSD",
            "tenant_code": "FNB",
            "recipient": "+27123456789",
            "message": "1",
            "context": {"session_id": "session-1"},
            "sent_at": 1_700_000_002,
        },
        "ussd-secret",
    )

    body = json.loads(captured["data"])
    expected_signature = hmac.new(
        b"ussd-secret",
        captured["data"].encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    assert response.status_code == 202
    assert captured["url"] == "https://channels.example/ussd"
    assert captured["headers"]["X-Amplifi-Adapter"] == "USSD_PROVIDER"
    assert captured["headers"]["X-Amplifi-Signature"] == expected_signature
    assert body["session_id"] == "session-1"
    assert body["msisdn"] == "+27123456789"
    assert body["text"] == "1"
    assert body["metadata"]["channel_code"] == "USSD"


@pytest.mark.asyncio
async def test_dispatch_ussd_channel_uses_sessional_lifecycle(monkeypatch):
    class FakeResponse:
        status_code = 202
        text = "session queued"

    sent = []
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            channel_ussd_provider_url="https://channels.example/ussd",
            channel_ussd_provider_secret="ussd-secret",
        ),
    )

    async def fake_post_channel_payload(url, payload, secret):
        sent.append((url, payload, secret))
        return FakeResponse()

    monkeypatch.setattr(service, "_post_channel_payload", fake_post_channel_payload)

    result = await service.dispatch_channel_message(
        channel_code="USSD",
        tenant_code="FNB",
        recipient="+27123456789",
        message="1",
        context={"session_id": "session-1"},
    )

    assert result["status"] == "SENT"
    assert result["adapter_type"] == "SESSIONAL"
    assert result["delivery_id"].startswith("CHD-")
    assert sent[0][0] == "https://channels.example/ussd"
    assert sent[0][1]["context"]["session_id"] == "session-1"


@pytest.mark.asyncio
async def test_dispatch_channel_message_rejects_unconfigured_provider(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            channel_sms_provider_url=None,
            channel_sms_provider_secret=None,
        ),
    )

    with pytest.raises(Exception) as exc:
        await service.dispatch_channel_message(
            channel_code="SMS",
            recipient="+27123456789",
            message="Hello",
        )

    assert getattr(exc.value, "status_code") == 409


@pytest.mark.asyncio
async def test_process_inbound_channel_webhook_validates_signature(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(channel_whatsapp_provider_secret="whatsapp-secret"),
    )
    raw_body = json.dumps(
        {
            "message_id": "msg-1",
            "from": "+27123456789",
            "message": "YES",
            "context": {"referral_track_id": "track-1"},
        },
        separators=(",", ":"),
    ).encode("utf-8")
    signature = hmac.new(b"whatsapp-secret", raw_body, hashlib.sha256).hexdigest()

    result = await service.process_inbound_channel_webhook(
        channel_code="WHATSAPP",
        raw_body=raw_body,
        signature=signature,
    )

    assert result["status"] == "accepted"
    assert result["channel_code"] == "WHATSAPP"
    assert result["inbound"]["message_id"] == "msg-1"
    assert result["inbound"]["message"] == "YES"


@pytest.mark.asyncio
async def test_process_inbound_channel_webhook_updates_delivery_status(monkeypatch):
    class FakeResponse:
        status_code = 202
        text = "queued"

    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            channel_whatsapp_provider_url="https://channels.example/whatsapp",
            channel_whatsapp_provider_secret="whatsapp-secret",
        ),
    )
    async def fake_post_channel_payload(url, payload, secret):
        return FakeResponse()

    monkeypatch.setattr(service, "_post_channel_payload", fake_post_channel_payload)

    dispatch = await service.dispatch_channel_message(
        channel_code="WHATSAPP",
        tenant_code="FNB",
        recipient="+27123456789",
        message="Your referral is ready",
        context={"consent_verified": True, "referral_track_id": "track-1"},
    )
    raw_body = json.dumps(
        {
            "delivery_id": dispatch["delivery_id"],
            "delivery_status": "delivered",
            "provider_status": 200,
            "message_id": "provider-message-1",
        },
        separators=(",", ":"),
    ).encode("utf-8")
    signature = hmac.new(b"whatsapp-secret", raw_body, hashlib.sha256).hexdigest()

    result = await service.process_inbound_channel_webhook(
        channel_code="WHATSAPP",
        raw_body=raw_body,
        signature=signature,
    )

    assert result["status"] == "accepted"
    assert result["delivery_update"]["delivery_id"] == dispatch["delivery_id"]
    assert result["delivery_update"]["status"] == "DELIVERED"
    deliveries = service.list_channel_deliveries(status_filter="DELIVERED")
    assert deliveries["summary"]["delivered"] == 1
    assert deliveries["items"][0]["status"] == "DELIVERED"


@pytest.mark.asyncio
async def test_process_inbound_ussd_returns_menu_reply(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(channel_ussd_provider_secret="ussd-secret"),
    )
    raw_body = json.dumps(
        {
            "session_id": "session-1",
            "msisdn": "+27123456789",
            "text": "",
        },
        separators=(",", ":"),
    ).encode("utf-8")
    signature = hmac.new(b"ussd-secret", raw_body, hashlib.sha256).hexdigest()

    result = await service.process_inbound_channel_webhook(
        channel_code="USSD",
        raw_body=raw_body,
        signature=signature,
    )

    assert result["status"] == "accepted"
    assert result["inbound"]["session_state"] == "START"
    assert "Check referral progress" in result["inbound"]["reply"]
