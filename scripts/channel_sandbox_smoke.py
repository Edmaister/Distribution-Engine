from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


class ChannelSandboxFailure(Exception):
    pass


def _url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def _request(
    method: str,
    base_url: str,
    path: str,
    *,
    admin_key: str,
    expected_status: int = 200,
    **kwargs: Any,
) -> Any:
    headers = dict(kwargs.pop("headers", {}) or {})
    headers["x-api-key"] = admin_key
    response = requests.request(
        method,
        _url(base_url, path),
        headers=headers,
        timeout=30,
        **kwargs,
    )
    if response.status_code != expected_status:
        raise ChannelSandboxFailure(
            f"{method} {path} returned {response.status_code}; expected {expected_status}. "
            f"Body: {response.text[:1000]}"
        )
    if not response.content:
        return None
    return response.json()


def _assert_ready(base_url: str, admin_key: str, channels: list[str]) -> None:
    readiness = _request("GET", base_url, "/admin/channels/readiness", admin_key=admin_key)
    items = {
        item.get("channel_code"): item
        for item in readiness.get("readiness", {}).get("items", [])
    }
    missing = [
        channel
        for channel in channels
        if not items.get(channel, {}).get("provider_configured")
    ]
    if missing:
        raise ChannelSandboxFailure(
            "Sandbox providers are not configured for: " + ", ".join(missing)
        )


def _dispatch_channel(
    *,
    base_url: str,
    admin_key: str,
    tenant_code: str,
    channel_code: str,
    recipient: str,
) -> str:
    body = {
        "channel_code": channel_code,
        "tenant_code": tenant_code,
        "recipient": recipient,
        "message": f"Amplifi sandbox proof {channel_code} {datetime.now(timezone.utc).isoformat()}",
        "context": {
            "consent_verified": True,
            "sandbox_proof": True,
            "template_code": "SANDBOX_PROOF",
        },
    }
    response = _request(
        "POST",
        base_url,
        "/admin/channels/dispatch",
        admin_key=admin_key,
        json=body,
    )
    dispatch = response.get("dispatch", {})
    status = dispatch.get("status")
    if status not in {"SENT", "DELIVERED"}:
        raise ChannelSandboxFailure(
            f"{channel_code} sandbox dispatch did not send. Status: {status}"
        )
    delivery_id = str(dispatch.get("delivery_id") or "")
    if not delivery_id:
        raise ChannelSandboxFailure(f"{channel_code} dispatch did not return a delivery id")
    print(f"[channel-sandbox] {channel_code} delivery_id={delivery_id} status={status}")
    return delivery_id


def run_smoke(
    *,
    base_url: str,
    admin_key: str,
    tenant_code: str,
    whatsapp_recipient: str,
    sms_recipient: str,
) -> None:
    channels = ["WHATSAPP", "SMS"]
    _assert_ready(base_url, admin_key, channels)
    delivery_ids = [
        _dispatch_channel(
            base_url=base_url,
            admin_key=admin_key,
            tenant_code=tenant_code,
            channel_code="WHATSAPP",
            recipient=whatsapp_recipient,
        ),
        _dispatch_channel(
            base_url=base_url,
            admin_key=admin_key,
            tenant_code=tenant_code,
            channel_code="SMS",
            recipient=sms_recipient,
        ),
    ]
    deliveries = _request(
        "GET",
        base_url,
        "/admin/channels/deliveries",
        admin_key=admin_key,
        params={"limit": 50},
    )
    evidence = str(deliveries)
    missing = [delivery_id for delivery_id in delivery_ids if delivery_id not in evidence]
    if missing:
        raise ChannelSandboxFailure(
            "Sandbox delivery evidence missing ids: " + ", ".join(missing)
        )
    print("[channel-sandbox] WhatsApp/SMS sandbox proof passed")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prove WhatsApp/SMS sandbox sends.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--admin-key", required=True)
    parser.add_argument("--tenant-code", default="FNB")
    parser.add_argument("--whatsapp-recipient", required=True)
    parser.add_argument("--sms-recipient", required=True)
    args = parser.parse_args()
    run_smoke(
        base_url=args.base_url,
        admin_key=args.admin_key,
        tenant_code=args.tenant_code,
        whatsapp_recipient=args.whatsapp_recipient,
        sms_recipient=args.sms_recipient,
    )


if __name__ == "__main__":
    main()
