from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import referral_saas_account_setup_ui_physical_check as setup_check
from scripts import referral_saas_selected_customer_e2e_physical_check as read_check
from scripts import referral_saas_selected_customer_mutation_e2e_physical_check as mutation_check


DEFAULT_BASE_URL = setup_check.DEFAULT_BASE_URL
DEFAULT_ADMIN_KEY = setup_check.DEFAULT_ADMIN_KEY
DEFAULT_TENANT_CODE = os.environ.get("TENANT_CODE", "FNB")
DEFAULT_JOURNEY_CODE = "BANKING_TRANSACTIONAL"
DEFAULT_JOURNEY_VERSION = "v1"

SECRET_OR_ADJACENT_KEYS = {
    "api_key",
    "apiKey",
    "bearerToken",
    "client_secret",
    "clientSecret",
    "credential",
    "credentials",
    "invoiceId",
    "password",
    "private_key",
    "privateKey",
    "secret",
    "settlementId",
    "walletId",
}


def _require_no_secret_or_adjacent_payload(value: Any, *, path: str = "") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            dotted = f"{path}.{key}" if path else str(key)
            if key in SECRET_OR_ADJACENT_KEYS:
                raise RuntimeError(f"Proof payload exposed unsafe adjacent field {dotted}.")
            _require_no_secret_or_adjacent_payload(item, path=dotted)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _require_no_secret_or_adjacent_payload(item, path=f"{path}[{index}]")


def _require_progress_result(
    result: setup_check.ApiResult,
    *,
    step: str,
    referral_track_id: str,
    event_type: str,
    expected_deduped: bool,
) -> None:
    setup_check.require_success(step, result, allowed={200, 201})
    read_check.assert_no_internal_scope_leak(result.payload)
    _require_no_secret_or_adjacent_payload(result.payload)
    if result.payload.get("referralTrackId") != referral_track_id:
        raise RuntimeError(f"{step} returned a different referralTrackId.")
    if result.payload.get("eventType") != event_type:
        raise RuntimeError(f"{step} returned a different eventType.")
    if result.payload.get("deduped") is not expected_deduped:
        raise RuntimeError(
            f"{step} expected deduped={expected_deduped}, got {result.payload.get('deduped')!r}."
        )


def _require_operator_read_result(result: setup_check.ApiResult, *, step: str) -> None:
    setup_check.require_success(step, result)
    _require_no_secret_or_adjacent_payload(result.payload)


def _progress_payload(
    *,
    referral_track_id: str,
    event_type: str,
    suffix: str,
    source_event_suffix: str,
    referee_ucn: str,
    account_number: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "referralTrackId": referral_track_id,
        "eventType": event_type,
        "journeyCode": DEFAULT_JOURNEY_CODE,
        "journeyVersion": DEFAULT_JOURNEY_VERSION,
        "refereeUCN": referee_ucn,
        "sourceSystem": f"task-340-progress-proof-{suffix}",
        "sourceEventId": f"task-340-{source_event_suffix}-{suffix}",
        "meta": {
            "proofTask": "TASK-340",
            "proofSuffix": suffix,
            "sideEffectBoundary": "no-provider-webhook-invite-credential-auth-billing-money-dlaas",
        },
    }
    if account_number:
        payload["accountNumber"] = account_number
    if event_type == "ACCOUNT_OPENED":
        payload["product"] = "TRANSACTIONAL"
        payload["subProduct"] = "CURRENT_ACCOUNT"
    return payload


def run(args: argparse.Namespace) -> dict[str, Any]:
    suffix = args.suffix or str(int(time.time()))
    mutation_result = mutation_check.run(args)
    referral_track_id = mutation_result.get("referral_track_id")
    if not referral_track_id:
        raise RuntimeError("Selected-customer mutation proof did not return referral_track_id.")

    selected_customer = mutation_result["selected_customer"]
    account_ref = selected_customer["accountRef"]
    account_ref_path = mutation_check._quote_path(account_ref)
    external_tenant_ref = selected_customer["externalTenantRef"]
    campaign_code = mutation_result["created_campaign"]["campaignCode"]
    scope_query = mutation_check._scope_query(external_tenant_ref)
    referee_ucn = args.referee_ucn or f"task340{suffix[-8:]}"
    account_number = args.account_number or f"340{suffix[-8:]}0001"

    first_payload = _progress_payload(
        referral_track_id=referral_track_id,
        event_type="UCN_CAPTURED",
        suffix=suffix,
        source_event_suffix="ucn-captured",
        referee_ucn=referee_ucn,
    )
    first_progress_result = setup_check.post_json(
        base_url=args.base_url,
        path="/v1/progress",
        admin_key=args.admin_key,
        payload=first_payload,
    )
    _require_progress_result(
        first_progress_result,
        step="record first progress event",
        referral_track_id=referral_track_id,
        event_type="UCN_CAPTURED",
        expected_deduped=False,
    )

    replay_progress_result = setup_check.post_json(
        base_url=args.base_url,
        path="/v1/progress",
        admin_key=args.admin_key,
        payload=first_payload,
    )
    _require_progress_result(
        replay_progress_result,
        step="replay first progress event",
        referral_track_id=referral_track_id,
        event_type="UCN_CAPTURED",
        expected_deduped=True,
    )

    later_payload = _progress_payload(
        referral_track_id=referral_track_id,
        event_type="ACCOUNT_OPENED",
        suffix=suffix,
        source_event_suffix="account-opened",
        referee_ucn=referee_ucn,
        account_number=account_number,
    )
    later_progress_result = setup_check.post_json(
        base_url=args.base_url,
        path="/v1/progress",
        admin_key=args.admin_key,
        payload=later_payload,
    )
    _require_progress_result(
        later_progress_result,
        step="record later progress event",
        referral_track_id=referral_track_id,
        event_type="ACCOUNT_OPENED",
        expected_deduped=False,
    )

    progress_status_result = setup_check.get_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/operator/referrals/{referral_track_id}/progress-status",
        admin_key=args.admin_key,
        query={"tenant_code": args.tenant_code, "viewer_role": "referrer"},
    )
    _require_operator_read_result(progress_status_result, step="read progress status")

    trace_result = setup_check.get_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/operator/outcomes/{referral_track_id}/trace",
        admin_key=args.admin_key,
        query={"tenant_code": args.tenant_code},
    )
    _require_operator_read_result(trace_result, step="read attribution trace")
    trace_status = (
        trace_result.payload.get("attributionTrace", {}).get("traceStatus")
        if isinstance(trace_result.payload.get("attributionTrace"), dict)
        else None
    )
    if trace_status == "UNAVAILABLE":
        raise RuntimeError("Attribution trace returned UNAVAILABLE.")

    report_result = setup_check.get_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/accounts/{account_ref_path}/reports/campaign_performance",
        admin_key=args.admin_key,
        query={**scope_query, "campaign_code": campaign_code},
    )
    setup_check.require_success("read customer-scoped campaign report", report_result)
    read_check.assert_no_internal_scope_leak(report_result.payload)
    _require_no_secret_or_adjacent_payload(report_result.payload)

    return {
        "status": "passed",
        "task": "TASK-340",
        "base_url": args.base_url,
        "proof_suffix": suffix,
        "selected_customer": selected_customer,
        "created_campaign": mutation_result["created_campaign"],
        "issued_referral_code": mutation_result["issued_referral_code"],
        "referral_track_id": referral_track_id,
        "progress_events": {
            "first": {
                "eventType": "UCN_CAPTURED",
                "status": first_progress_result.status_code,
                "deduped": first_progress_result.payload.get("deduped"),
                "sourceEventId": first_payload["sourceEventId"],
            },
            "replay": {
                "eventType": "UCN_CAPTURED",
                "status": replay_progress_result.status_code,
                "deduped": replay_progress_result.payload.get("deduped"),
                "sourceEventId": first_payload["sourceEventId"],
            },
            "later": {
                "eventType": "ACCOUNT_OPENED",
                "status": later_progress_result.status_code,
                "deduped": later_progress_result.payload.get("deduped"),
                "sourceEventId": later_payload["sourceEventId"],
            },
        },
        "readbacks": {
            "progress_status": progress_status_result.status_code,
            "attribution_trace": trace_result.status_code,
            "trace_status": trace_status,
            "campaign_report": report_result.status_code,
        },
        "no_provider_call": True,
        "no_webhook_delivery": True,
        "no_invitation_delivery": True,
        "no_credential_creation": True,
        "no_auth_claim_change": True,
        "no_login_activation": True,
        "no_billing_or_money_movement": True,
        "no_dlaas_marketplace_mutation": True,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run TASK-340 Referral SaaS progress/attribution mutation proof. "
            "This reuses the selected-customer campaign/link/code mutation proof, "
            "records and replays progress events, then reads progress status, "
            "attribution trace, and customer-scoped report evidence without "
            "provider, webhook, invite, credential, auth, billing, money, or DLaaS side effects."
        )
    )
    parser.add_argument("--base-url", default=os.environ.get("API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--admin-key", default=os.environ.get("LOCAL_API_KEY", DEFAULT_ADMIN_KEY))
    parser.add_argument("--tenant-code", default=DEFAULT_TENANT_CODE)
    parser.add_argument("--external-tenant-ref")
    parser.add_argument("--organisation-ref")
    parser.add_argument("--campaign-name")
    parser.add_argument("--campaign-segment")
    parser.add_argument("--suffix", help="Stable suffix for idempotency and proof labelling.")
    parser.add_argument("--referee-ucn")
    parser.add_argument("--account-number")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
