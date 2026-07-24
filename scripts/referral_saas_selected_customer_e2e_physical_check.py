from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import referral_saas_account_setup_ui_physical_check as setup_check
from scripts import referral_saas_client_workspace_physical_check as workspace_check


DEFAULT_BASE_URL = setup_check.DEFAULT_BASE_URL
DEFAULT_ADMIN_KEY = setup_check.DEFAULT_ADMIN_KEY

SAFE_CONFIRMATION_KEYS = {
    "no_tenant_code_exposure_confirmed",
    "noTenantCodeExposureConfirmed",
}
FORBIDDEN_RESPONSE_KEYS = {
    "tenant_code",
    "tenantCode",
    "internal_tenant_code",
    "internalTenantCode",
    "tenant_scope",
    "tenantScope",
}


def _quote_path(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def assert_no_internal_scope_leak(value: Any, *, path: str = "") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in SAFE_CONFIRMATION_KEYS:
                continue
            dotted = f"{path}.{key}" if path else str(key)
            if key in FORBIDDEN_RESPONSE_KEYS:
                raise RuntimeError(f"Selected-customer E2E payload exposed {dotted}.")
            assert_no_internal_scope_leak(item, path=dotted)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_no_internal_scope_leak(item, path=f"{path}[{index}]")


def _get_external_ref(account: dict[str, Any], ref_type: str) -> str:
    return workspace_check.get_account_external_ref(account, ref_type)


def _select_customer(
    registry_payload: dict[str, Any],
    *,
    external_tenant_ref: str | None,
    organisation_ref: str | None,
) -> dict[str, Any]:
    assert_no_internal_scope_leak(registry_payload)
    accounts = registry_payload.get("accounts")
    if not isinstance(accounts, list) or not accounts:
        raise RuntimeError("No selected-customer accounts are available for E2E proof.")

    for account in accounts:
        if not isinstance(account, dict):
            continue
        account_external_ref = _get_external_ref(account, "external_tenant_ref")
        account_organisation_ref = _get_external_ref(account, "organisation_ref")
        if external_tenant_ref and account_external_ref != external_tenant_ref:
            continue
        if organisation_ref and account_organisation_ref != organisation_ref:
            continue
        if account_external_ref and account_organisation_ref:
            return account

    raise RuntimeError("No account matched the requested selected-customer references.")


def _require_account_ref(account: dict[str, Any]) -> str:
    account_ref = account.get("accountId") or account.get("accountCode")
    if not account_ref:
        raise RuntimeError("Selected account did not include a safe account reference.")
    return str(account_ref)


def _first_campaign(campaigns_payload: dict[str, Any]) -> dict[str, Any]:
    assert_no_internal_scope_leak(campaigns_payload)
    campaigns = campaigns_payload.get("campaigns")
    if not isinstance(campaigns, list) or not campaigns:
        raise RuntimeError(
            "Selected customer has no campaigns. Create a customer-scoped campaign "
            "before running full selected-customer E2E proof."
        )
    first = campaigns[0]
    if not isinstance(first, dict) or not first.get("campaignCode"):
        raise RuntimeError("Selected-customer campaign list did not return a safe campaign code.")
    return first


def run(args: argparse.Namespace) -> dict[str, Any]:
    suffix = args.suffix or str(int(time.time()))

    registry_result = setup_check.get_json(
        base_url=args.base_url,
        path="/v1/referral-saas/accounts",
        admin_key=args.admin_key,
        query={"limit": "50"},
    )
    setup_check.require_success("load selected-customer registry", registry_result)
    selected_account = _select_customer(
        registry_result.payload,
        external_tenant_ref=args.external_tenant_ref,
        organisation_ref=args.organisation_ref,
    )

    account_ref = _require_account_ref(selected_account)
    external_tenant_ref = _get_external_ref(selected_account, "external_tenant_ref")
    organisation_ref = _get_external_ref(selected_account, "organisation_ref")

    scope_query = {
        "ref_type": "external_tenant_ref",
        "external_ref": external_tenant_ref,
        "context": "setup",
    }

    resolve_result = setup_check.get_json(
        base_url=args.base_url,
        path="/v1/referral-saas/accounts/resolve",
        admin_key=args.admin_key,
        query=scope_query,
    )
    setup_check.require_success("resolve selected customer account", resolve_result)
    assert_no_internal_scope_leak(resolve_result.payload)

    membership_result = setup_check.get_json(
        base_url=args.base_url,
        path="/v1/referral-saas/accounts/membership-posture",
        admin_key=args.admin_key,
        query=scope_query,
    )
    setup_check.require_success("load selected-customer people/access posture", membership_result)
    assert_no_internal_scope_leak(membership_result.payload)

    technical_result = setup_check.get_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/accounts/{_quote_path(account_ref)}/technical-setup-readiness",
        admin_key=args.admin_key,
        query=scope_query,
    )
    setup_check.require_success("load selected-customer technical readiness", technical_result)
    assert_no_internal_scope_leak(technical_result.payload)

    campaigns_result = setup_check.get_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/accounts/{_quote_path(account_ref)}/campaigns",
        admin_key=args.admin_key,
        query={**scope_query, "limit": "25"},
    )
    setup_check.require_success("load selected-customer campaigns", campaigns_result)
    selected_campaign = _first_campaign(campaigns_result.payload)
    campaign_code = str(selected_campaign["campaignCode"])

    readiness_result = setup_check.get_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{_quote_path(account_ref)}"
            f"/campaigns/{_quote_path(campaign_code)}/readiness"
        ),
        admin_key=args.admin_key,
        query=scope_query,
    )
    setup_check.require_success("load selected-customer campaign readiness", readiness_result)
    assert_no_internal_scope_leak(readiness_result.payload)

    report_result = setup_check.get_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{_quote_path(account_ref)}"
            "/reports/campaign_performance"
        ),
        admin_key=args.admin_key,
        query={**scope_query, "campaign_code": campaign_code},
    )
    setup_check.require_success("load selected-customer campaign performance report", report_result)
    assert_no_internal_scope_leak(report_result.payload)

    preview_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{_quote_path(account_ref)}"
            "/reports/campaign_performance/exports/preview"
            f"?{urllib.parse.urlencode(scope_query)}"
        ),
        admin_key=args.admin_key,
        payload={
            "format": "json",
            "redaction_profile": "tenant_safe",
            "filters": {"campaign_code": campaign_code},
            "row_limit": 25,
        },
    )
    setup_check.require_success("preview selected-customer report export", preview_result)
    assert_no_internal_scope_leak(preview_result.payload)

    return {
        "status": "passed",
        "task": "TASK-269",
        "base_url": args.base_url,
        "proof_suffix": suffix,
        "selected_customer": {
            "accountRef": account_ref,
            "accountName": selected_account.get("accountName"),
            "externalTenantRef": external_tenant_ref,
            "organisationRef": organisation_ref,
        },
        "selected_campaign": {
            "campaignCode": campaign_code,
            "status": selected_campaign.get("status"),
            "lifecycle": selected_campaign.get("lifecycle"),
        },
        "checks": {
            "account_registry": registry_result.status_code,
            "account_resolve": resolve_result.status_code,
            "people_access_posture": membership_result.status_code,
            "technical_readiness": technical_result.status_code,
            "campaign_list": campaigns_result.status_code,
            "campaign_readiness": readiness_result.status_code,
            "campaign_report": report_result.status_code,
            "export_preview": preview_result.status_code,
        },
        "no_invitation_delivery": True,
        "no_membership_activation": True,
        "no_campaign_mutation": True,
        "no_link_generation": True,
        "no_export_creation": True,
        "no_storage_or_delivery": True,
        "no_billing_or_money_movement": True,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Physically verify selected-customer Referral SaaS E2E readiness "
            "against a running local/staging API without mutating customer, "
            "campaign, link/code, export, invite, billing, or money state."
        )
    )
    parser.add_argument("--base-url", default=os.environ.get("API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--admin-key", default=os.environ.get("LOCAL_API_KEY", DEFAULT_ADMIN_KEY))
    parser.add_argument("--external-tenant-ref")
    parser.add_argument("--organisation-ref")
    parser.add_argument("--suffix", help="Stable suffix for proof result labelling.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
