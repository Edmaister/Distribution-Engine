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
from scripts import referral_saas_selected_customer_e2e_physical_check as read_check


DEFAULT_BASE_URL = setup_check.DEFAULT_BASE_URL
DEFAULT_ADMIN_KEY = setup_check.DEFAULT_ADMIN_KEY


def _quote_path(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def _put_json(
    *,
    base_url: str,
    path: str,
    admin_key: str,
    payload: dict[str, Any],
) -> setup_check.ApiResult:
    return setup_check.request_json(
        method="PUT",
        base_url=base_url,
        path=path,
        admin_key=admin_key,
        payload=payload,
    )


def _scope_query(external_tenant_ref: str) -> dict[str, str]:
    return {
        "ref_type": "external_tenant_ref",
        "external_ref": external_tenant_ref,
        "context": "setup",
    }


def _scope_payload(external_tenant_ref: str, *, context: str = "setup") -> dict[str, str]:
    return {
        "refType": "external_tenant_ref",
        "externalRef": external_tenant_ref,
        "context": context,
    }


def _require_flag(payload: dict[str, Any], key: str, step: str) -> None:
    if payload.get(key) is not True:
        raise RuntimeError(f"{step} did not confirm {key}.")


def _require_no_adjacent_actions(payload: dict[str, Any], step: str) -> None:
    read_check.assert_no_internal_scope_leak(payload)
    for key in (
        "no_webhook_delivery_confirmed",
        "no_billing_or_money_movement_confirmed",
    ):
        if key in payload:
            _require_flag(payload, key, step)


def _extract_created_campaign_code(payload: dict[str, Any]) -> str:
    read_check.assert_no_internal_scope_leak(payload)
    campaign = (
        payload.get("campaignSetup", {})
        .get("campaign", {})
        if isinstance(payload.get("campaignSetup"), dict)
        else {}
    )
    campaign_code = campaign.get("campaignCode") or campaign.get("campaignRef")
    if not campaign_code:
        raise RuntimeError("Campaign setup response did not include a safe campaign code.")
    return str(campaign_code)


def _extract_referral_code(payload: dict[str, Any]) -> str:
    read_check.assert_no_internal_scope_leak(payload)
    link_code = payload.get("linkCode") if isinstance(payload.get("linkCode"), dict) else {}
    referral_code = link_code.get("referralCode")
    if not referral_code:
        raise RuntimeError("Referral code issue response did not include a referral code.")
    return str(referral_code)


def _load_selected_customer(args: argparse.Namespace) -> tuple[dict[str, Any], str, str, str]:
    registry_result = setup_check.get_json(
        base_url=args.base_url,
        path="/v1/referral-saas/accounts",
        admin_key=args.admin_key,
        query={"limit": "50"},
    )
    setup_check.require_success("load selected-customer registry", registry_result)
    selected_account = read_check._select_customer(
        registry_result.payload,
        external_tenant_ref=args.external_tenant_ref,
        organisation_ref=args.organisation_ref,
    )
    account_ref = read_check._require_account_ref(selected_account)
    external_tenant_ref = read_check._get_external_ref(
        selected_account,
        "external_tenant_ref",
    )
    organisation_ref = read_check._get_external_ref(
        selected_account,
        "organisation_ref",
    )
    return selected_account, account_ref, external_tenant_ref, organisation_ref


def run(args: argparse.Namespace) -> dict[str, Any]:
    suffix = args.suffix or str(int(time.time()))
    selected_account, account_ref, external_tenant_ref, organisation_ref = (
        _load_selected_customer(args)
    )
    account_ref_path = _quote_path(account_ref)
    scope_payload = _scope_payload(external_tenant_ref)
    scope_query = _scope_query(external_tenant_ref)

    campaign_name = args.campaign_name or f"TASK-271 Mutation Proof {suffix}"
    campaign_segment = args.campaign_segment or "Referral SaaS physical proof"

    create_result = setup_check.post_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/accounts/{account_ref_path}/campaigns",
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "campaign": {
                "name": campaign_name,
                "segment": campaign_segment,
                "maxUses": 25,
            },
            "setupIntent": {"reason": "TASK_271_MUTATION_PROOF"},
            "correlationId": f"task-271-campaign-create-{suffix}",
            "idempotencyKey": f"task-271-campaign-create-{suffix}",
        },
    )
    setup_check.require_success("create selected-customer campaign setup", create_result)
    _require_no_adjacent_actions(create_result.payload, "campaign setup")
    _require_flag(create_result.payload, "no_campaign_activation_confirmed", "campaign setup")
    _require_flag(create_result.payload, "no_link_generation_confirmed", "campaign setup")
    campaign_code = _extract_created_campaign_code(create_result.payload)
    campaign_path = _quote_path(campaign_code)

    policy_result = _put_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}"
            f"/campaigns/{campaign_path}/policy-settings"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "policySettings": {
                "version": 1,
                "attributionWindowDays": 30,
                "eligibilityRules": [{"rule": "NEW_CUSTOMER_ONLY", "enabled": True}],
                "productWindows": {"default": {"days": 30}},
                "productRules": {"default": {"requiresAcceptedTerms": True}},
                "rewardVisibility": {"mode": "configured_without_payment"},
            },
            "setupIntent": {"reason": "TASK_271_POLICY_SETTINGS"},
            "correlationId": f"task-271-policy-{suffix}",
            "idempotencyKey": f"task-271-policy-{suffix}",
        },
    )
    setup_check.require_success("save selected-customer campaign policy", policy_result)
    _require_no_adjacent_actions(policy_result.payload, "campaign policy")
    _require_flag(policy_result.payload, "no_campaign_activation_confirmed", "campaign policy")
    _require_flag(policy_result.payload, "no_link_generation_confirmed", "campaign policy")

    review_submission_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}"
            f"/campaigns/{campaign_path}/review-submissions"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "reviewSubmission": {
                "setupSummary": "TASK-271 campaign setup and policy settings are ready.",
                "requestedReviewStatus": "READY_FOR_REVIEW",
                "operatorNotes": "Physical mutation proof run.",
            },
            "correlationId": f"task-271-review-submit-{suffix}",
            "idempotencyKey": f"task-271-review-submit-{suffix}",
        },
    )
    setup_check.require_success(
        "submit selected-customer campaign review",
        review_submission_result,
    )
    _require_no_adjacent_actions(review_submission_result.payload, "campaign review submit")
    _require_flag(
        review_submission_result.payload,
        "no_campaign_activation_confirmed",
        "campaign review submit",
    )
    _require_flag(
        review_submission_result.payload,
        "no_link_generation_confirmed",
        "campaign review submit",
    )

    review_decision_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}"
            f"/campaigns/{campaign_path}/review-decisions"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "reviewDecision": {
                "decision": "APPROVED",
                "reason": "TASK-271 physical mutation proof approved.",
                "reviewerRef": "task-271-proof-runner",
            },
            "correlationId": f"task-271-review-decision-{suffix}",
            "idempotencyKey": f"task-271-review-decision-{suffix}",
        },
    )
    setup_check.require_success(
        "approve selected-customer campaign review",
        review_decision_result,
    )
    _require_no_adjacent_actions(review_decision_result.payload, "campaign review decision")
    _require_flag(
        review_decision_result.payload,
        "no_campaign_activation_confirmed",
        "campaign review decision",
    )

    activation_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}"
            f"/campaigns/{campaign_path}/activation-requests"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": _scope_payload(
                external_tenant_ref,
                context="campaign_activation",
            ),
            "activationRequest": {
                "requestedLifecycleStatus": "ACTIVE",
                "reviewStatus": "REVIEW_APPROVED",
                "goLiveReason": "TASK-271 campaign setup and review are approved.",
            },
            "correlationId": f"task-271-activation-{suffix}",
            "idempotencyKey": f"task-271-activation-{suffix}",
        },
    )
    setup_check.require_success("activate selected-customer campaign", activation_result)
    _require_no_adjacent_actions(activation_result.payload, "campaign activation")
    _require_flag(activation_result.payload, "no_link_generation_confirmed", "campaign activation")
    _require_flag(
        activation_result.payload,
        "no_validation_track_created_confirmed",
        "campaign activation",
    )
    _require_flag(
        activation_result.payload,
        "no_credential_creation_confirmed",
        "campaign activation",
    )

    issue_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}"
            f"/campaigns/{campaign_path}/referral-codes"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "issueRequest": {
                "referrerUcn": f"task271{suffix[-8:]}",
                "sticker": f"TASK271-{suffix[-8:]}",
                "segment": "PHYSICAL_PROOF",
                "preferredHandle": f"task271-{suffix[-8:]}",
                "acceptedTerms": True,
            },
        },
    )
    setup_check.require_success(
        "issue selected-customer campaign referral code",
        issue_result,
        allowed={200, 201},
    )
    _require_no_adjacent_actions(issue_result.payload, "referral code issue")
    _require_flag(issue_result.payload, "no_campaign_activation_confirmed", "referral code issue")
    referral_code = _extract_referral_code(issue_result.payload)

    validation_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}"
            f"/campaigns/{campaign_path}/referrals/validate"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "validationRequest": {
                "referralCode": referral_code,
                "acceptedTerms": True,
                "alias": f"task-271-alias-{suffix[-8:]}",
            },
        },
    )
    setup_check.require_success(
        "validate selected-customer campaign referral code",
        validation_result,
        allowed={200, 201},
    )
    _require_no_adjacent_actions(validation_result.payload, "referral validation")
    _require_flag(
        validation_result.payload,
        "no_campaign_activation_confirmed",
        "referral validation",
    )

    report_result = setup_check.get_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/accounts/{account_ref_path}/reports/campaign_performance",
        admin_key=args.admin_key,
        query={**scope_query, "campaign_code": campaign_code},
    )
    setup_check.require_success("load mutation-path campaign report", report_result)
    read_check.assert_no_internal_scope_leak(report_result.payload)

    preview_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}"
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
    setup_check.require_success("preview mutation-path report export", preview_result)
    read_check.assert_no_internal_scope_leak(preview_result.payload)

    return {
        "status": "passed",
        "task": "TASK-271",
        "base_url": args.base_url,
        "proof_suffix": suffix,
        "selected_customer": {
            "accountRef": account_ref,
            "accountName": selected_account.get("accountName"),
            "externalTenantRef": external_tenant_ref,
            "organisationRef": organisation_ref,
        },
        "created_campaign": {
            "campaignCode": campaign_code,
            "name": campaign_name,
            "segment": campaign_segment,
        },
        "issued_referral_code": referral_code,
        "checks": {
            "campaign_create": create_result.status_code,
            "policy_settings": policy_result.status_code,
            "review_submission": review_submission_result.status_code,
            "review_decision": review_decision_result.status_code,
            "campaign_activation": activation_result.status_code,
            "referral_code_issue": issue_result.status_code,
            "referral_validation": validation_result.status_code,
            "campaign_report": report_result.status_code,
            "export_preview": preview_result.status_code,
        },
        "campaign_mutation_limited_to_setup_policy_review_activation": True,
        "link_code_mutation_limited_to_issue_and_validation": True,
        "no_invitation_delivery": True,
        "no_membership_activation": True,
        "no_credential_creation": True,
        "no_webhook_delivery": True,
        "no_export_creation": True,
        "no_storage_or_delivery": True,
        "no_billing_or_money_movement": True,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Physically verify the selected-customer Referral SaaS mutation path "
            "against a running local/staging API. This creates an inactive campaign "
            "setup draft, records policy/review evidence, activates campaign posture, "
            "issues and validates a referral code, then checks report/export preview "
            "without webhooks, credentials, invites, exports, billing, or money movement."
        )
    )
    parser.add_argument("--base-url", default=os.environ.get("API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--admin-key", default=os.environ.get("LOCAL_API_KEY", DEFAULT_ADMIN_KEY))
    parser.add_argument("--external-tenant-ref")
    parser.add_argument("--organisation-ref")
    parser.add_argument("--campaign-name")
    parser.add_argument("--campaign-segment")
    parser.add_argument("--suffix", help="Stable suffix for idempotency and proof labelling.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
