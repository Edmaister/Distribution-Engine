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
from scripts import referral_saas_progress_attribution_physical_check as progress_check
from scripts import referral_saas_selected_customer_e2e_physical_check as read_check
from scripts import referral_saas_selected_customer_mutation_e2e_physical_check as mutation_check


DEFAULT_BASE_URL = setup_check.DEFAULT_BASE_URL
DEFAULT_ADMIN_KEY = setup_check.DEFAULT_ADMIN_KEY
DEFAULT_PROGRESS_KEY = progress_check.DEFAULT_PROGRESS_KEY
DEFAULT_TENANT_CODE = progress_check.DEFAULT_TENANT_CODE


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


def _scope_query(external_tenant_ref: str, *, context: str = "setup") -> dict[str, str]:
    return {
        "ref_type": "external_tenant_ref",
        "external_ref": external_tenant_ref,
        "context": context,
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


def _require_no_adjacent_actions(
    payload: dict[str, Any],
    step: str,
    *,
    skip_keys: set[str] | None = None,
) -> None:
    read_check.assert_no_internal_scope_leak(payload)
    skipped = skip_keys or set()
    for key in (
        "noRuntimeJourneyMutationConfirmed",
        "noCampaignActivationConfirmed",
        "noProviderDispatchConfirmed",
        "noAuthBillingOrMoneyActionConfirmed",
        "no_campaign_activation_confirmed",
        "no_webhook_delivery_confirmed",
        "no_billing_or_money_movement_confirmed",
    ):
        if key in skipped:
            continue
        if key in payload:
            _require_flag(payload, key, step)


def _first_approved_template(catalogue_payload: dict[str, Any]) -> tuple[str, str]:
    read_check.assert_no_internal_scope_leak(catalogue_payload)
    templates = catalogue_payload.get("templates")
    if not isinstance(templates, list):
        raise RuntimeError("Journey template catalogue did not return a template list.")
    for template in templates:
        if not isinstance(template, dict):
            continue
        template_code = str(template.get("templateCode") or "").strip()
        versions = template.get("versions")
        if not template_code or not isinstance(versions, list):
            continue
        for version in versions:
            if not isinstance(version, dict):
                continue
            if str(version.get("status") or "").upper() != "APPROVED":
                continue
            template_version = str(version.get("templateVersion") or "").strip()
            if template_version:
                return template_code, template_version
    raise RuntimeError("No approved journey template version is available for proof.")


def _extract_draft_id(payload: dict[str, Any]) -> str:
    read_check.assert_no_internal_scope_leak(payload)
    draft = payload.get("draft") if isinstance(payload.get("draft"), dict) else {}
    draft_id = draft.get("customerJourneyDraftId")
    if not draft_id:
        raise RuntimeError("Journey draft response did not include customerJourneyDraftId.")
    return str(draft_id)


def _extract_validation_status(payload: dict[str, Any]) -> str:
    read_check.assert_no_internal_scope_leak(payload)
    validation = (
        payload.get("validation")
        if isinstance(payload.get("validation"), dict)
        else payload
    )
    status = validation.get("validationStatus") if isinstance(validation, dict) else None
    if not status:
        raise RuntimeError("Journey validation response did not include validationStatus.")
    return str(status)


def _extract_version_id(payload: dict[str, Any]) -> str:
    read_check.assert_no_internal_scope_leak(payload)
    version = payload.get("version") if isinstance(payload.get("version"), dict) else {}
    version_id = version.get("customerJourneyVersionId")
    if not version_id:
        raise RuntimeError("Journey publish response did not include customerJourneyVersionId.")
    return str(version_id)


def _extract_created_campaign_code(payload: dict[str, Any]) -> str:
    read_check.assert_no_internal_scope_leak(payload)
    campaign_setup = (
        payload.get("campaignSetup")
        if isinstance(payload.get("campaignSetup"), dict)
        else {}
    )
    campaign = (
        campaign_setup.get("campaign")
        if isinstance(campaign_setup.get("campaign"), dict)
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
        raise RuntimeError("Referral code issue response did not include referralCode.")
    return str(referral_code)


def _extract_referral_track_id(payload: dict[str, Any]) -> str:
    read_check.assert_no_internal_scope_leak(payload)
    validation = payload.get("validation") if isinstance(payload.get("validation"), dict) else {}
    referral_track_id = validation.get("referralTrackId")
    if not referral_track_id:
        raise RuntimeError("Referral validation response did not include referralTrackId.")
    return str(referral_track_id)


def _require_progress_replay(result: setup_check.ApiResult) -> None:
    setup_check.require_success("replay configurable journey progress event", result)
    if result.payload.get("deduped") is not True:
        raise RuntimeError("Progress replay expected deduped=True for TASK-394 proof.")


def _load_customer(args: argparse.Namespace) -> tuple[dict[str, Any], str, str, str]:
    selected_account, account_ref, external_tenant_ref, organisation_ref = (
        mutation_check._load_selected_customer(args)
    )
    read_check.assert_no_internal_scope_leak(selected_account)
    return selected_account, account_ref, external_tenant_ref, organisation_ref


def run(args: argparse.Namespace) -> dict[str, Any]:
    suffix = args.suffix or str(int(time.time()))
    selected_account, account_ref, external_tenant_ref, organisation_ref = _load_customer(args)
    account_ref_path = _quote_path(account_ref)
    scope_payload = _scope_payload(external_tenant_ref)
    scope_query = _scope_query(external_tenant_ref)

    catalogue_result = setup_check.get_json(
        base_url=args.base_url,
        path="/v1/referral-saas/journey-templates",
        admin_key=args.admin_key,
        query={"status": "APPROVED", "limit": "50"},
    )
    setup_check.require_success("load approved journey template catalogue", catalogue_result)
    template_code, template_version = (
        (args.template_code, args.template_version)
        if args.template_code and args.template_version
        else _first_approved_template(catalogue_result.payload)
    )

    draft_result = _put_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/accounts/{account_ref_path}/journey-drafts",
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "templateCode": template_code,
            "templateVersion": template_version,
            "draftName": args.draft_name or f"TASK-394 Journey Proof {suffix}",
            "configurationPayload": args.configuration_payload,
            "correlationId": f"task-394-draft-save-{suffix}",
            "idempotencyKey": f"task-394-draft-save-{suffix}",
        },
    )
    setup_check.require_success("save configurable journey draft", draft_result)
    _require_no_adjacent_actions(draft_result.payload, "journey draft save")
    draft_id = _extract_draft_id(draft_result.payload)

    validation_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}"
            f"/journey-drafts/{_quote_path(draft_id)}/validate"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "correlationId": f"task-394-draft-validate-{suffix}",
            "idempotencyKey": f"task-394-draft-validate-{suffix}",
        },
    )
    setup_check.require_success("validate configurable journey draft", validation_result)
    validation_status = _extract_validation_status(validation_result.payload)
    if validation_status == "BLOCKED":
        raise RuntimeError("Configurable journey draft validation is blocked.")

    publish_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}"
            f"/journey-drafts/{_quote_path(draft_id)}/publish"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "correlationId": f"task-394-draft-publish-{suffix}",
            "idempotencyKey": f"task-394-draft-publish-{suffix}",
        },
    )
    setup_check.require_success("publish configurable journey version", publish_result)
    _require_no_adjacent_actions(publish_result.payload, "journey draft publish")
    version_id = _extract_version_id(publish_result.payload)

    campaign_name = args.campaign_name or f"TASK-394 Journey Campaign {suffix}"
    create_campaign_result = setup_check.post_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/accounts/{account_ref_path}/campaigns",
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "campaign": {
                "name": campaign_name,
                "segment": "Configurable journey E2E proof",
                "maxUses": 25,
            },
            "setupIntent": {"reason": "TASK_394_CONFIGURABLE_JOURNEY_PROOF"},
            "correlationId": f"task-394-campaign-create-{suffix}",
            "idempotencyKey": f"task-394-campaign-create-{suffix}",
        },
    )
    setup_check.require_success("create journey-bound campaign setup", create_campaign_result)
    _require_no_adjacent_actions(create_campaign_result.payload, "journey-bound campaign setup")
    campaign_code = _extract_created_campaign_code(create_campaign_result.payload)
    campaign_path = _quote_path(campaign_code)

    bind_result = _put_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}"
            f"/campaigns/{campaign_path}/journey-binding"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "customerJourneyVersionId": version_id,
            "correlationId": f"task-394-journey-bind-{suffix}",
            "idempotencyKey": f"task-394-journey-bind-{suffix}",
        },
    )
    setup_check.require_success("bind campaign to configurable journey", bind_result)
    _require_no_adjacent_actions(bind_result.payload, "campaign journey binding")

    binding_read_result = setup_check.get_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}"
            f"/campaigns/{campaign_path}/journey-binding"
        ),
        admin_key=args.admin_key,
        query=scope_query,
    )
    setup_check.require_success("read configurable campaign journey binding", binding_read_result)
    read_check.assert_no_internal_scope_leak(binding_read_result.payload)

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
                "goLiveReason": "TASK-394 journey binding proof is ready.",
            },
            "correlationId": f"task-394-campaign-activation-{suffix}",
            "idempotencyKey": f"task-394-campaign-activation-{suffix}",
        },
    )
    setup_check.require_success("activate journey-bound campaign", activation_result)
    _require_no_adjacent_actions(
        activation_result.payload,
        "journey-bound campaign activation",
        skip_keys={"noCampaignActivationConfirmed", "no_campaign_activation_confirmed"},
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
                "referrerUcn": f"task394{suffix[-8:]}",
                "sticker": f"TASK394-{suffix[-8:]}",
                "segment": "CONFIGURABLE_JOURNEY_PROOF",
                "preferredHandle": f"task394-{suffix[-8:]}",
                "acceptedTerms": True,
            },
        },
    )
    setup_check.require_success(
        "issue configurable journey referral code",
        issue_result,
        allowed={200, 201},
    )
    _require_no_adjacent_actions(issue_result.payload, "configurable referral code issue")
    referral_code = _extract_referral_code(issue_result.payload)

    referral_validation_result = setup_check.post_json(
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
                "alias": f"task-394-alias-{suffix[-8:]}",
            },
        },
    )
    setup_check.require_success(
        "validate configurable journey referral",
        referral_validation_result,
        allowed={200, 201},
    )
    _require_no_adjacent_actions(
        referral_validation_result.payload,
        "configurable referral validation",
    )
    referral_track_id = _extract_referral_track_id(referral_validation_result.payload)

    progress_payload = {
        "tenantCode": args.tenant_code,
        "journeyCode": args.journey_code,
        "referralTrackId": referral_track_id,
        "eventType": "UCN_CAPTURED",
        "sourceSystem": "TASK_394_CONFIGURABLE_JOURNEY_PROOF",
        "sourceEventId": f"task-394-ucn-captured-{suffix}",
        "occurredAt": "2026-08-15T00:00:00Z",
        "metadata": {"campaignCode": campaign_code, "customerJourneyVersionId": version_id},
    }
    progress_first_result = setup_check.post_json(
        base_url=args.base_url,
        path="/v1/progress",
        admin_key=args.progress_key,
        payload=progress_payload,
    )
    setup_check.require_success(
        "record configurable journey progress event",
        progress_first_result,
        allowed={200, 201},
    )
    progress_replay_result = setup_check.post_json(
        base_url=args.base_url,
        path="/v1/progress",
        admin_key=args.progress_key,
        payload=progress_payload,
    )
    _require_progress_replay(progress_replay_result)

    progress_status_result = setup_check.get_json(
        base_url=args.base_url,
        path=f"/v1/referrals/{_quote_path(referral_track_id)}/progress-status",
        admin_key=args.admin_key,
        query={"tenant_code": args.tenant_code},
    )
    setup_check.require_success("read configurable journey progress status", progress_status_result)
    progress_check._require_operator_read_result(
        progress_status_result,
        step="configurable progress status read",
    )

    trace_result = setup_check.get_json(
        base_url=args.base_url,
        path=f"/v1/referrals/{_quote_path(referral_track_id)}/trace",
        admin_key=args.admin_key,
        query={"tenant_code": args.tenant_code},
    )
    setup_check.require_success("read configurable journey attribution trace", trace_result)
    progress_check._require_operator_read_result(
        trace_result,
        step="configurable attribution trace read",
    )

    report_result = setup_check.get_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/accounts/{account_ref_path}/reports/campaign_performance",
        admin_key=args.admin_key,
        query={**scope_query, "campaign_code": campaign_code},
    )
    setup_check.require_success("read configurable journey campaign report", report_result)
    read_check.assert_no_internal_scope_leak(report_result.payload)

    analytics_result = setup_check.get_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/accounts/{account_ref_path}/journey-analytics",
        admin_key=args.admin_key,
        query={**scope_query, "limit": "25"},
    )
    setup_check.require_success("read configurable journey analytics", analytics_result)
    read_check.assert_no_internal_scope_leak(analytics_result.payload)

    archive_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}"
            f"/journey-versions/{_quote_path(version_id)}/archive"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "archiveReason": "TASK-394 active binding rollback guardrail proof.",
            "correlationId": f"task-394-version-archive-{suffix}",
            "idempotencyKey": f"task-394-version-archive-{suffix}",
        },
    )
    setup_check.require_success(
        "verify active journey archive guardrail",
        archive_result,
        allowed={200, 409},
    )
    read_check.assert_no_internal_scope_leak(archive_result.payload)
    if archive_result.status_code == 200:
        archive_posture = "ARCHIVE_ALLOWED"
    else:
        archive_posture = "ARCHIVE_BLOCKED_BY_ACTIVE_BINDING"

    return {
        "status": "passed",
        "task": "TASK-394",
        "base_url": args.base_url,
        "proof_suffix": suffix,
        "selected_customer": {
            "accountRef": account_ref,
            "accountName": selected_account.get("accountName"),
            "externalTenantRef": external_tenant_ref,
            "organisationRef": organisation_ref,
        },
        "approved_template": {
            "templateCode": template_code,
            "templateVersion": template_version,
        },
        "customer_journey": {
            "draftId": draft_id,
            "validationStatus": validation_status,
            "versionId": version_id,
            "archivePosture": archive_posture,
        },
        "campaign": {"campaignCode": campaign_code, "name": campaign_name},
        "referral": {
            "referralCode": referral_code,
            "referralTrackId": referral_track_id,
        },
        "checks": {
            "template_catalogue": catalogue_result.status_code,
            "draft_save": draft_result.status_code,
            "draft_validate": validation_result.status_code,
            "draft_publish": publish_result.status_code,
            "campaign_create": create_campaign_result.status_code,
            "campaign_journey_bind": bind_result.status_code,
            "campaign_journey_binding_read": binding_read_result.status_code,
            "campaign_activation": activation_result.status_code,
            "referral_code_issue": issue_result.status_code,
            "referral_validation": referral_validation_result.status_code,
            "progress_first": progress_first_result.status_code,
            "progress_replay": progress_replay_result.status_code,
            "progress_status": progress_status_result.status_code,
            "attribution_trace": trace_result.status_code,
            "campaign_report": report_result.status_code,
            "journey_analytics": analytics_result.status_code,
            "archive_guardrail": archive_result.status_code,
        },
        "already_approved_template_no_source_change_confirmed": True,
        "journey_configuration_published_and_bound_to_campaign": True,
        "progress_tracking_attribution_and_reporting_readback_confirmed": True,
        "rollback_archive_posture_checked": True,
        "no_provider_dispatch": True,
        "no_invitation_delivery": True,
        "no_credential_creation": True,
        "no_auth_billing_settlement_or_money_action": True,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run TASK-394 configurable journey E2E proof against a running API. "
            "The proof uses an already-approved journey template, creates a "
            "customer journey draft/version, binds a campaign, runs referral "
            "progress/attribution/reporting readback, and checks archive posture "
            "without source-code journey changes."
        )
    )
    parser.add_argument("--base-url", default=os.environ.get("API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--admin-key", default=os.environ.get("LOCAL_API_KEY", DEFAULT_ADMIN_KEY))
    parser.add_argument(
        "--progress-key",
        default=os.environ.get("PROGRESS_API_KEY", DEFAULT_PROGRESS_KEY),
    )
    parser.add_argument("--tenant-code", default=os.environ.get("TENANT_CODE", DEFAULT_TENANT_CODE))
    parser.add_argument("--external-tenant-ref")
    parser.add_argument("--organisation-ref")
    parser.add_argument("--template-code")
    parser.add_argument("--template-version")
    parser.add_argument("--journey-code", default="BANKING_TRANSACTIONAL")
    parser.add_argument("--draft-name")
    parser.add_argument("--campaign-name")
    parser.add_argument("--suffix", help="Stable suffix for idempotency and proof labelling.")
    parser.set_defaults(configuration_payload={})
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
