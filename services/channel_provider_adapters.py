from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ChannelProviderRequest:
    body: str
    headers: dict[str, str]


class ChannelProviderAdapter(Protocol):
    adapter_name: str

    def build_request(self, payload: dict[str, Any], secret: str) -> ChannelProviderRequest:
        ...


class WhatsAppProviderAdapter:
    adapter_name = "WHATSAPP_PROVIDER"

    def build_request(self, payload: dict[str, Any], secret: str) -> ChannelProviderRequest:
        provider_payload = {
            "to": payload["recipient"],
            "type": "text",
            "text": {"body": payload["message"]},
            "metadata": _metadata(payload),
        }
        return _signed_request(
            channel_code=str(payload["channel_code"]),
            adapter_name=self.adapter_name,
            provider_payload=provider_payload,
            secret=secret,
        )


class SmsProviderAdapter:
    adapter_name = "SMS_PROVIDER"

    def build_request(self, payload: dict[str, Any], secret: str) -> ChannelProviderRequest:
        provider_payload = {
            "to": payload["recipient"],
            "body": payload["message"],
            "metadata": _metadata(payload),
        }
        return _signed_request(
            channel_code=str(payload["channel_code"]),
            adapter_name=self.adapter_name,
            provider_payload=provider_payload,
            secret=secret,
        )


class UssdProviderAdapter:
    adapter_name = "USSD_PROVIDER"

    def build_request(self, payload: dict[str, Any], secret: str) -> ChannelProviderRequest:
        context = payload.get("context") or {}
        provider_payload = {
            "session_id": context.get("session_id") or context.get("sessionId"),
            "msisdn": payload["recipient"],
            "text": payload["message"],
            "metadata": _metadata(payload),
        }
        return _signed_request(
            channel_code=str(payload["channel_code"]),
            adapter_name=self.adapter_name,
            provider_payload=provider_payload,
            secret=secret,
        )


class GenericChannelProviderAdapter:
    adapter_name = "GENERIC_CHANNEL_PROVIDER"

    def build_request(self, payload: dict[str, Any], secret: str) -> ChannelProviderRequest:
        return _signed_request(
            channel_code=str(payload["channel_code"]),
            adapter_name=self.adapter_name,
            provider_payload=payload,
            secret=secret,
        )


def adapter_for_channel(channel_code: str) -> ChannelProviderAdapter:
    normalized = channel_code.strip().upper()
    if normalized == "WHATSAPP":
        return WhatsAppProviderAdapter()
    if normalized == "SMS":
        return SmsProviderAdapter()
    if normalized == "USSD":
        return UssdProviderAdapter()
    return GenericChannelProviderAdapter()


def _metadata(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "channel_code": payload["channel_code"],
        "tenant_code": payload.get("tenant_code"),
        "context": payload.get("context") or {},
        "sent_at": payload.get("sent_at"),
    }


def _signed_request(
    *,
    channel_code: str,
    adapter_name: str,
    provider_payload: dict[str, Any],
    secret: str,
) -> ChannelProviderRequest:
    body = json.dumps(provider_payload, default=str, separators=(",", ":"))
    signature = hmac.new(
        secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return ChannelProviderRequest(
        body=body,
        headers={
            "Content-Type": "application/json",
            "X-Amplifi-Channel": channel_code,
            "X-Amplifi-Adapter": adapter_name,
            "X-Amplifi-Signature": signature,
        },
    )
