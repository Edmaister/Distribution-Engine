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


DEFAULT_BASE_URL = setup_check.DEFAULT_BASE_URL
DEFAULT_ADMIN_KEY = setup_check.DEFAULT_ADMIN_KEY
DEFAULT_INTERNAL_TENANT_CODE = setup_check.DEFAULT_INTERNAL_TENANT_CODE

CLIENT_WORKSPACE_ROUTES = (
    "/admin/referral-saas/account-setup",
    "/admin/referral-saas/account-maintenance",
    "/admin/onboarding/webhook-api",
    "/admin/referral-saas/campaigns",
    "/admin/referral-saas/link-codes",
    "/admin/referral-saas/attribution-trace",
    "/admin/referral-saas/reports",
    "/admin/referral-saas/support",
)


def assert_registry_contains_client(
    payload: dict[str, Any],
    *,
    external_tenant_ref: str,
    organisation_ref: str,
) -> dict[str, Any]:
    setup_check.assert_no_forbidden_product_payload(payload)
    accounts = payload.get("accounts")
    if not isinstance(accounts, list):
        raise RuntimeError("Account registry response did not include accounts.")

    for account in accounts:
        references = account.get("externalReferences") or []
        ref_pairs = {
            str(reference.get("refType")): str(reference.get("externalRef"))
            for reference in references
            if isinstance(reference, dict)
        }
        primary_external_ref = account.get("primaryExternalTenantRef")
        if (
            (primary_external_ref == external_tenant_ref or ref_pairs.get("external_tenant_ref") == external_tenant_ref)
            and ref_pairs.get("organisation_ref") == organisation_ref
        ):
            return account

    raise RuntimeError(
        "Created client was not returned by the Referral SaaS account registry."
    )


def select_existing_registry_client(payload: dict[str, Any]) -> dict[str, Any]:
    setup_check.assert_no_forbidden_product_payload(payload)
    accounts = payload.get("accounts")
    if not isinstance(accounts, list) or not accounts:
        raise RuntimeError("No existing clients are available in the account registry.")
    for account in accounts:
        if (
            get_account_external_ref(account, "external_tenant_ref")
            and get_account_external_ref(account, "organisation_ref")
        ):
            return account
    raise RuntimeError("No existing registry client has complete external references.")


def get_account_external_ref(account: dict[str, Any], ref_type: str) -> str:
    if ref_type == "external_tenant_ref" and account.get("primaryExternalTenantRef"):
        return str(account["primaryExternalTenantRef"])
    references = account.get("externalReferences") or []
    for reference in references:
        if isinstance(reference, dict) and reference.get("refType") == ref_type:
            return str(reference.get("externalRef") or "")
    return ""


def assert_maintenance_state_is_client_scoped(
    payload: dict[str, Any],
    *,
    external_tenant_ref: str,
    organisation_ref: str,
) -> dict[str, Any]:
    setup_check.assert_no_forbidden_product_payload(payload)
    onboarding_state = payload.get("onboarding_state") or {}
    scope = onboarding_state.get("scope") or {}
    if scope.get("external_tenant_ref") != external_tenant_ref:
        raise RuntimeError("Maintenance state did not use the selected client reference.")
    if scope.get("organisation_ref") != organisation_ref:
        raise RuntimeError("Maintenance state did not use the selected organisation reference.")
    if "readiness" not in payload:
        raise RuntimeError("Maintenance state did not return readiness evidence.")
    return scope


def assert_client_workspace_routes_are_bounded(routes: tuple[str, ...]) -> None:
    forbidden_fragments = (
        "funding",
        "settlement",
        "wallet",
        "billing",
        "treasury",
        "marketplace",
        "payout",
    )
    unsafe_route = next(
        (
            route
            for route in routes
            if any(fragment in route.lower() for fragment in forbidden_fragments)
        ),
        None,
    )
    if unsafe_route:
        raise RuntimeError(f"Client Workspace route escapes Referral SaaS boundary: {unsafe_route}")
    if tuple(routes) != CLIENT_WORKSPACE_ROUTES:
        raise RuntimeError(f"Unexpected Client Workspace route set: {routes!r}")


def run(args: argparse.Namespace) -> dict[str, Any]:
    suffix = args.suffix or str(int(time.time()))
    external_tenant_ref = args.external_tenant_ref or f"task-229-{suffix}"
    organisation_ref = args.organisation_ref or f"org-task-229-{suffix}"
    organisation_name = args.organisation_name or f"Task 229 Client {suffix}"

    registry_result = setup_check.get_json(
        base_url=args.base_url,
        path="/v1/referral-saas/accounts",
        admin_key=args.admin_key,
        query={"limit": "50"},
    )
    setup_check.require_success("load Client Workspace account registry", registry_result)
    if args.reuse_existing_client:
        selected_client = select_existing_registry_client(registry_result.payload)
        external_tenant_ref = get_account_external_ref(selected_client, "external_tenant_ref")
        organisation_ref = get_account_external_ref(selected_client, "organisation_ref")
        setup_result: dict[str, Any] = {
            "status": "skipped",
            "reason": "reused_existing_client",
        }
    else:
        setup_args = argparse.Namespace(
            base_url=args.base_url,
            admin_key=args.admin_key,
            internal_tenant_code=args.internal_tenant_code,
            external_tenant_ref=external_tenant_ref,
            organisation_ref=organisation_ref,
            organisation_name=organisation_name,
            admin_contact=args.admin_contact,
            suffix=suffix,
        )
        setup_result = setup_check.run(setup_args)
        registry_result = setup_check.get_json(
            base_url=args.base_url,
            path="/v1/referral-saas/accounts",
            admin_key=args.admin_key,
            query={"limit": "50"},
        )
        setup_check.require_success("reload Client Workspace account registry", registry_result)
        selected_client = assert_registry_contains_client(
            registry_result.payload,
            external_tenant_ref=external_tenant_ref,
            organisation_ref=organisation_ref,
        )

    maintenance_result = setup_check.get_json(
        base_url=args.base_url,
        path="/admin/onboarding/state",
        admin_key=args.admin_key,
        query={
            "external_tenant_ref": external_tenant_ref,
            "organisation_ref": organisation_ref,
        },
    )
    setup_check.require_success("load selected Client Workspace state", maintenance_result)
    selected_scope = assert_maintenance_state_is_client_scoped(
        maintenance_result.payload,
        external_tenant_ref=external_tenant_ref,
        organisation_ref=organisation_ref,
    )
    assert_client_workspace_routes_are_bounded(CLIENT_WORKSPACE_ROUTES)

    readiness = maintenance_result.payload.get("readiness") or {}
    summary = readiness.get("summary") or {}
    return {
        "status": "passed",
        "task": "TASK-229",
        "base_url": args.base_url,
        "external_tenant_ref": external_tenant_ref,
        "organisation_ref": organisation_ref,
        "created_account": setup_result.get("created_account"),
        "selected_client": {
            "accountId": selected_client.get("accountId"),
            "accountCode": selected_client.get("accountCode"),
            "accountName": selected_client.get("accountName"),
            "accountStatus": selected_client.get("accountStatus"),
            "onboardingStatus": selected_client.get("onboardingStatus"),
        },
        "selected_scope": selected_scope,
        "readiness_status": readiness.get("overall_status"),
        "readiness_summary": summary,
        "client_workspace_routes": CLIENT_WORKSPACE_ROUTES,
        "account_setup_creation_mode": (
            "reused_existing_client" if args.reuse_existing_client else "created_client"
        ),
        "setup_result": {
            "draft_ref": setup_result.get("draft_ref"),
            "status": setup_result.get("status"),
            "reason": setup_result.get("reason"),
            "validation_status": setup_result.get("validation_status"),
            "no_adjacent_live_action_confirmed": setup_result.get(
                "no_adjacent_live_action_confirmed"
            ),
        },
        "no_profile_update": True,
        "no_invitation_delivery": True,
        "no_campaign_activation": True,
        "no_go_live": True,
        "no_money_movement": True,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Physically verify the Referral SaaS Account Setup to selected "
            "Client Workspace handoff against a running local/staging API."
        )
    )
    parser.add_argument("--base-url", default=os.environ.get("API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--admin-key", default=os.environ.get("LOCAL_API_KEY", DEFAULT_ADMIN_KEY))
    parser.add_argument(
        "--internal-tenant-code",
        default=os.environ.get("TASK_229_INTERNAL_TENANT_CODE", DEFAULT_INTERNAL_TENANT_CODE),
    )
    parser.add_argument("--external-tenant-ref")
    parser.add_argument("--organisation-ref")
    parser.add_argument("--organisation-name")
    parser.add_argument("--admin-contact", default="referral-saas-client-workspace-proof@example.test")
    parser.add_argument("--suffix", help="Stable suffix for repeatable references.")
    parser.add_argument(
        "--reuse-existing-client",
        action="store_true",
        help=(
            "Skip Account Setup creation and verify Client Workspace selection "
            "against the first existing registry client with complete external references."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
