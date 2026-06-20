from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import channel_sandbox_smoke, core_role_journey_smoke


class PilotValidationFailure(Exception):
    pass


def _url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def _request(
    method: str,
    base_url: str,
    path: str,
    *,
    api_key: str | None = None,
    expected_status: int = 200,
    **kwargs: Any,
) -> Any:
    headers = dict(kwargs.pop("headers", {}) or {})
    if api_key:
        headers["x-api-key"] = api_key
    response = requests.request(
        method,
        _url(base_url, path),
        headers=headers,
        timeout=30,
        **kwargs,
    )
    if response.status_code != expected_status:
        raise PilotValidationFailure(
            f"{method} {path} returned {response.status_code}; expected {expected_status}. "
            f"Body: {response.text[:1000]}"
        )
    if not response.content:
        return None
    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        return response.text
    return response.json()


def _assert_ready(base_url: str) -> None:
    health = _request("GET", base_url, "/health")
    readyz = _request("GET", base_url, "/readyz")
    if health.get("status") != "ok" or readyz.get("status") != "ok":
        raise PilotValidationFailure("Health or readiness is not ok")


def _assert_admin_operations(base_url: str, admin_key: str) -> None:
    admin = _request("GET", base_url, "/v1/experience/admin-command-centre", api_key=admin_key)
    if admin.get("status") != "ok":
        raise PilotValidationFailure("Admin command-centre BFF is not ok")
    channels = _request("GET", base_url, "/admin/channels/deliveries", api_key=admin_key)
    if channels.get("status") != "ok":
        raise PilotValidationFailure("Channel operations endpoint is not ok")


def _assert_preferences(
    *,
    base_url: str,
    consumer_key: str,
    distributor_key: str,
    tenant_code: str,
    referrer_ucn: str,
    distributor_code: str,
) -> None:
    _request(
        "PUT",
        base_url,
        f"/channels/preferences/CONSUMER/{referrer_ucn}",
        api_key=consumer_key,
        json={
            "tenant_code": tenant_code,
            "preferred_channels": ["WHATSAPP", "SMS"],
            "consent_channels": ["WHATSAPP", "SMS"],
            "opt_out_channels": [],
        },
    )
    _request(
        "PUT",
        base_url,
        f"/channels/preferences/DISTRIBUTOR/{distributor_code}",
        api_key=distributor_key,
        json={
            "tenant_code": tenant_code,
            "preferred_channels": ["WHATSAPP", "USSD"],
            "consent_channels": ["WHATSAPP", "USSD"],
            "opt_out_channels": [],
        },
    )


def run_validation(
    *,
    base_url: str,
    admin_key: str,
    consumer_key: str,
    producer_key: str,
    distributor_key: str,
    tenant_code: str,
    referrer_ucn: str,
    producer_code: str,
    distributor_code: str,
    whatsapp_recipient: str | None,
    sms_recipient: str | None,
) -> None:
    print("[pilot-validation] checking platform readiness")
    _assert_ready(base_url)
    print("[pilot-validation] checking role journeys")
    core_role_journey_smoke.run_smoke(
        base_url=base_url,
        admin_key=admin_key,
        consumer_key=consumer_key,
        producer_key=producer_key,
        distributor_key=distributor_key,
        tenant_code=tenant_code,
        referrer_ucn=referrer_ucn,
        producer_code=producer_code,
        distributor_code=distributor_code,
    )
    print("[pilot-validation] checking admin operations")
    _assert_admin_operations(base_url, admin_key)
    print("[pilot-validation] checking channel preferences")
    _assert_preferences(
        base_url=base_url,
        consumer_key=consumer_key,
        distributor_key=distributor_key,
        tenant_code=tenant_code,
        referrer_ucn=referrer_ucn,
        distributor_code=distributor_code,
    )
    if whatsapp_recipient and sms_recipient:
        print("[pilot-validation] checking WhatsApp/SMS sandbox proof")
        channel_sandbox_smoke.run_smoke(
            base_url=base_url,
            admin_key=admin_key,
            tenant_code=tenant_code,
            whatsapp_recipient=whatsapp_recipient,
            sms_recipient=sms_recipient,
        )
    print("[pilot-validation] pilot tenant validation passed")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate one pilot tenant end to end.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--admin-key", required=True)
    parser.add_argument("--consumer-key", required=True)
    parser.add_argument("--producer-key", required=True)
    parser.add_argument("--distributor-key", required=True)
    parser.add_argument("--tenant-code", default="FNB")
    parser.add_argument("--referrer-ucn", required=True)
    parser.add_argument("--producer-code", required=True)
    parser.add_argument("--distributor-code", required=True)
    parser.add_argument("--whatsapp-recipient")
    parser.add_argument("--sms-recipient")
    args = parser.parse_args()
    run_validation(
        base_url=args.base_url,
        admin_key=args.admin_key,
        consumer_key=args.consumer_key,
        producer_key=args.producer_key,
        distributor_key=args.distributor_key,
        tenant_code=args.tenant_code,
        referrer_ucn=args.referrer_ucn,
        producer_code=args.producer_code,
        distributor_code=args.distributor_code,
        whatsapp_recipient=args.whatsapp_recipient,
        sms_recipient=args.sms_recipient,
    )


if __name__ == "__main__":
    main()
