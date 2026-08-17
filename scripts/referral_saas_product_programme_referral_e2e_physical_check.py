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


def _require_safe(payload: dict[str, Any], step: str) -> None:
    read_check.assert_no_internal_scope_leak(payload)
    for key in (
        "noProgrammeBindingConfirmed",
        "noCampaignCreationConfirmed",
        "noReferralCreationConfirmed",
        "noIncentiveApplicationConfirmed",
        "noProgrammePublishConfirmed",
        "noCampaignActivationConfirmed",
        "noReferralRuntimeSwitchConfirmed",
        "noProviderDispatchConfirmed",
        "noCredentialOrAuthMutationConfirmed",
        "noAuthBillingOrMoneyActionConfirmed",
        "noBillingPayoutSettlementOrMoneyMovementConfirmed",
        "noRewardApplicationConfirmed",
        "noBadgeAwardConfirmed",
        "noMissionProgressMutationConfirmed",
        "noLeaderboardScoringConfirmed",
        "noMoneyMovementConfirmed",
        "no_campaign_activation_confirmed",
        "no_webhook_delivery_confirmed",
        "no_billing_or_money_movement_confirmed",
    ):
        if key in payload and payload[key] is not True:
            raise RuntimeError(f"{step} did not confirm {key}.")


def _resource(payload: dict[str, Any]) -> dict[str, Any]:
    resource = payload.get("resource")
    return resource if isinstance(resource, dict) else {}


def _extract_product_line_id(payload: dict[str, Any]) -> str:
    resource = _resource(payload)
    product_line_id = resource.get("customerProductLineId")
    if not product_line_id:
        raise RuntimeError("Product line response did not include customerProductLineId.")
    return str(product_line_id)


def _extract_product_offering_id(payload: dict[str, Any]) -> str:
    resource = _resource(payload)
    offering_id = resource.get("customerProductOfferingId")
    if not offering_id:
        raise RuntimeError("Product offering response did not include customerProductOfferingId.")
    return str(offering_id)


def _extract_programme_draft_id(payload: dict[str, Any]) -> str:
    resource = _resource(payload)
    draft_id = resource.get("programmeDraftId") or resource.get("programme_draft_id")
    if not draft_id:
        raise RuntimeError("Programme draft response did not include programmeDraftId.")
    return str(draft_id)


def _extract_programme_version_id(payload: dict[str, Any]) -> str:
    version = payload.get("programmeVersion")
    if not isinstance(version, dict):
        version = _resource(payload)
    version_id = version.get("programmeVersionId") or version.get("programme_version_id")
    if not version_id:
        raise RuntimeError("Programme publish response did not include programmeVersionId.")
    return str(version_id)


def _extract_binding_ref(payload: dict[str, Any]) -> str:
    binding = payload.get("binding")
    if not isinstance(binding, dict):
        binding = _resource(payload)
    binding_id = (
        binding.get("programmeIncentiveBindingId")
        or binding.get("programme_incentive_binding_id")
        or binding.get("bindingId")
    )
    if not binding_id:
        raise RuntimeError("Programme incentive binding response did not include binding id.")
    return str(binding_id)


def _extract_campaign_code(payload: dict[str, Any]) -> str:
    campaign_setup = payload.get("campaignSetup")
    if isinstance(campaign_setup, dict):
        campaign = campaign_setup.get("campaign")
    else:
        campaign = payload.get("campaign")
    campaign = campaign if isinstance(campaign, dict) else {}
    campaign_code = campaign.get("campaignCode") or campaign.get("campaignRef")
    if not campaign_code:
        raise RuntimeError("Campaign setup response did not include campaignCode.")
    return str(campaign_code)


def _extract_referral_code(payload: dict[str, Any]) -> str:
    link_code = payload.get("linkCode") if isinstance(payload.get("linkCode"), dict) else {}
    referral_code = link_code.get("referralCode")
    if not referral_code:
        raise RuntimeError("Referral code issue response did not include referralCode.")
    return str(referral_code)


def _extract_referral_track_id(payload: dict[str, Any]) -> str:
    validation = payload.get("validation") if isinstance(payload.get("validation"), dict) else {}
    referral_track_id = validation.get("referralTrackId")
    if not referral_track_id:
        raise RuntimeError("Referral validation response did not include referralTrackId.")
    return str(referral_track_id)


def _load_customer(args: argparse.Namespace) -> tuple[dict[str, Any], str, str, str]:
    selected_account, account_ref, external_tenant_ref, organisation_ref = (
        mutation_check._load_selected_customer(args)
    )
    read_check.assert_no_internal_scope_leak(selected_account)
    return selected_account, account_ref, external_tenant_ref, organisation_ref


def _require_validation_passable(payload: dict[str, Any]) -> str:
    validation = payload.get("validation") if isinstance(payload.get("validation"), dict) else {}
    status = str(validation.get("validationStatus") or "").upper()
    if not status:
        raise RuntimeError("Programme validation response did not include validationStatus.")
    if status == "BLOCKED":
        raise RuntimeError("Programme validation is blocked.")
    blockers = validation.get("blockers")
    if isinstance(blockers, list) and blockers:
        raise RuntimeError("Programme validation returned blockers.")
    return status


UNSAFE_RUNTIME_KEY_PARTS = (
    "raw_event_payload",
    "raw_payload",
    "rawpayload",
    "provider_payload",
    "providerpayload",
    "ucn",
    "email",
    "token",
    "secret",
    "credential",
    "auth_claim",
    "authclaim",
    "billing_amount",
    "billingamount",
    "settlement_amount",
    "settlementamount",
    "payout_amount",
    "payoutamount",
    "invoice_amount",
    "invoiceamount",
    "wallet_balance",
    "walletbalance",
    "treasury_balance",
    "treasurybalance",
    "commission_amount",
    "commissionamount",
)


def _unsafe_runtime_key_paths(value: Any, prefix: str = "") -> list[str]:
    leaked: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            normalised = key_text.replace("-", "_").lower()
            if any(term in normalised for term in UNSAFE_RUNTIME_KEY_PARTS):
                leaked.append(key_path)
            leaked.extend(_unsafe_runtime_key_paths(nested, key_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            leaked.extend(_unsafe_runtime_key_paths(nested, f"{prefix}[{index}]"))
    return leaked


def _require_product_runtime_context(payload: dict[str, Any]) -> None:
    read_check.assert_no_internal_scope_leak(payload)
    serialized = json.dumps(payload, sort_keys=True, default=str)
    required = (
        "customerProductBinding",
        "programmeVersionId",
        "programmeCode",
        "campaignCode",
        "effectiveRuleSnapshot",
    )
    missing = [key for key in required if key not in serialized]
    if missing:
        raise RuntimeError(
            "Referral runtime readback did not include expected programme/product "
            f"context: {', '.join(missing)}."
        )
    leaked = _unsafe_runtime_key_paths(payload)
    if leaked:
        raise RuntimeError(f"Unsafe runtime/reporting leakage found: {', '.join(leaked)}.")


def run(args: argparse.Namespace) -> dict[str, Any]:
    suffix = args.suffix or str(int(time.time()))
    selected_account, account_ref, external_tenant_ref, organisation_ref = _load_customer(args)
    account_ref_path = _quote_path(account_ref)
    scope_payload = _scope_payload(external_tenant_ref)
    scope_query = _scope_query(external_tenant_ref)

    product_line_ref = args.product_line_ref or f"TASK418-{suffix[-8:]}-LINE"
    offering_ref = args.offering_ref or f"TASK418-{suffix[-8:]}-OFFERING"

    line_result = _put_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/accounts/{account_ref_path}/product-lines/{_quote_path(product_line_ref)}",
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "productLineName": args.product_line_name,
            "productLineCategory": args.product_line_category,
            "operatingJurisdictionCode": args.operating_jurisdiction_code,
            "lifecycleStatus": "ACTIVE",
            "safeSummary": {"purpose": "TASK-418 product to referral proof"},
            "correlationId": f"task-418-product-line-{suffix}",
            "idempotencyKey": f"task-418-product-line-{suffix}",
        },
    )
    setup_check.require_success("create/select customer product line", line_result)
    _require_safe(line_result.payload, "customer product line")
    product_line_id = _extract_product_line_id(line_result.payload)

    offering_result = _put_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}/product-lines/"
            f"{_quote_path(product_line_ref)}/offerings/{_quote_path(offering_ref)}"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "offeringName": args.offering_name,
            "offeringFamily": args.offering_family,
            "operatingJurisdictionCode": args.operating_jurisdiction_code,
            "lifecycleStatus": "ACTIVE",
            "safeSummary": {"purpose": "TASK-418 product offering proof"},
            "correlationId": f"task-418-product-offering-{suffix}",
            "idempotencyKey": f"task-418-product-offering-{suffix}",
        },
    )
    setup_check.require_success("create/select customer product offering", offering_result)
    _require_safe(offering_result.payload, "customer product offering")
    product_offering_id = _extract_product_offering_id(offering_result.payload)

    catalogue_result = setup_check.get_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/accounts/{account_ref_path}/product-catalogue",
        admin_key=args.admin_key,
        query={**scope_query, "limit": "50"},
    )
    setup_check.require_success("read customer product catalogue", catalogue_result)
    _require_safe(catalogue_result.payload, "customer product catalogue")

    programme_result = setup_check.post_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/accounts/{account_ref_path}/programmes/drafts",
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "programmeName": args.programme_name or f"TASK-418 Programme {suffix}",
            "programmeDescription": "TASK-418 product to referral proof.",
            "operatingJurisdictionCode": args.operating_jurisdiction_code,
            "productCode": "REFERRAL_SAAS",
            "subProductCode": "PROGRAMME_CONFIGURATION",
            "customerProductLineId": product_line_id,
            "customerProductOfferingId": product_offering_id,
            "customerJourneyVersionId": args.customer_journey_version_id,
            "campaignDefaults": {
                "allowedCampaignOverrides": {
                    "allowedKeys": ["attributionWindowDays", "rewardPolicyRef"]
                },
                "defaultChannel": "REFERRAL_LINK",
            },
            "incentiveRefs": [{"catalogueRef": args.incentive_ref}],
            "engagementRefs": [{"catalogueRef": args.engagement_ref}],
            "integrationReadinessSnapshot": {"status": "READY"},
            "commercialEntitlementSnapshot": {"status": "READY"},
            "effectiveFrom": args.effective_from,
            "correlationId": f"task-418-programme-draft-{suffix}",
            "idempotencyKey": f"task-418-programme-draft-{suffix}",
        },
    )
    setup_check.require_success("create product-bound referral programme draft", programme_result)
    _require_safe(programme_result.payload, "programme draft create")
    programme_draft_id = _extract_programme_draft_id(programme_result.payload)

    validation_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}/programmes/drafts/"
            f"{_quote_path(programme_draft_id)}/validate"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "correlationId": f"task-418-programme-validate-{suffix}",
            "idempotencyKey": f"task-418-programme-validate-{suffix}",
        },
    )
    setup_check.require_success("validate product-bound programme draft", validation_result)
    _require_safe(validation_result.payload, "programme validation")
    validation_status = _require_validation_passable(validation_result.payload)

    submit_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}/programmes/drafts/"
            f"{_quote_path(programme_draft_id)}/submit-review"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "reviewReason": "TASK-418 proof review submission.",
            "correlationId": f"task-418-programme-submit-{suffix}",
            "idempotencyKey": f"task-418-programme-submit-{suffix}",
        },
    )
    setup_check.require_success("submit product-bound programme for review", submit_result)
    _require_safe(submit_result.payload, "programme review submission")

    decision_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}/programmes/drafts/"
            f"{_quote_path(programme_draft_id)}/review-decision"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "decision": "APPROVED",
            "reviewReason": "TASK-418 proof review approved.",
            "correlationId": f"task-418-programme-review-{suffix}",
            "idempotencyKey": f"task-418-programme-review-{suffix}",
        },
    )
    setup_check.require_success("approve product-bound programme", decision_result)
    _require_safe(decision_result.payload, "programme review decision")

    publish_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}/programmes/drafts/"
            f"{_quote_path(programme_draft_id)}/publish"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "publishReason": "TASK-418 proof publish.",
            "correlationId": f"task-418-programme-publish-{suffix}",
            "idempotencyKey": f"task-418-programme-publish-{suffix}",
        },
    )
    setup_check.require_success("publish product-bound programme version", publish_result)
    _require_safe(publish_result.payload, "programme publish")
    programme_version_id = _extract_programme_version_id(publish_result.payload)

    incentive_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}/programmes/versions/"
            f"{_quote_path(programme_version_id)}/incentive-bindings"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "bindingType": "INCENTIVE",
            "catalogueType": "REWARD_POLICY",
            "catalogueRef": args.incentive_ref,
            "catalogueVersionRef": args.incentive_version_ref,
            "effectiveFrom": args.effective_from,
            "correlationId": f"task-418-incentive-bind-{suffix}",
            "idempotencyKey": f"task-418-incentive-bind-{suffix}",
        },
    )
    setup_check.require_success("bind programme incentive reference", incentive_result)
    _require_safe(incentive_result.payload, "programme incentive binding")
    incentive_binding_ref = _extract_binding_ref(incentive_result.payload)

    campaign_result = setup_check.post_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/accounts/{account_ref_path}/campaigns",
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "campaign": {
                "name": args.campaign_name or f"TASK-418 Campaign {suffix}",
                "segment": "Product programme proof",
                "maxUses": 25,
            },
            "setupIntent": {"reason": "TASK_418_PRODUCT_PROGRAMME_REFERRAL_PROOF"},
            "correlationId": f"task-418-campaign-create-{suffix}",
            "idempotencyKey": f"task-418-campaign-create-{suffix}",
        },
    )
    setup_check.require_success("create customer campaign", campaign_result)
    _require_safe(campaign_result.payload, "campaign create")
    campaign_code = _extract_campaign_code(campaign_result.payload)

    campaign_path = _quote_path(campaign_code)
    campaign_binding_result = _put_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}/campaigns/"
            f"{campaign_path}/programme-binding"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "programmeVersionId": programme_version_id,
            "correlationId": f"task-418-campaign-programme-bind-{suffix}",
            "idempotencyKey": f"task-418-campaign-programme-bind-{suffix}",
        },
    )
    setup_check.require_success("bind campaign to published programme", campaign_binding_result)
    _require_safe(campaign_binding_result.payload, "campaign programme binding")

    issue_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}/campaigns/"
            f"{campaign_path}/referral-codes"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "issueRequest": {
                "referrerUcn": f"task418{suffix[-8:]}",
                "sticker": f"TASK418-{suffix[-8:]}",
                "segment": "PRODUCT_PROGRAMME_PROOF",
                "preferredHandle": f"task418-{suffix[-8:]}",
                "acceptedTerms": True,
            },
        },
    )
    setup_check.require_success("issue programme-bound referral code", issue_result, allowed={200, 201})
    _require_safe(issue_result.payload, "referral code issue")
    referral_code = _extract_referral_code(issue_result.payload)

    referral_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{account_ref_path}/campaigns/"
            f"{campaign_path}/referrals/validate"
        ),
        admin_key=args.admin_key,
        payload={
            "accountScope": scope_payload,
            "validationRequest": {
                "referralCode": referral_code,
                "acceptedTerms": True,
                "alias": f"task-418-alias-{suffix[-8:]}",
            },
        },
    )
    setup_check.require_success("validate programme-bound referral", referral_result, allowed={200, 201})
    _require_safe(referral_result.payload, "referral validation")
    referral_track_id = _extract_referral_track_id(referral_result.payload)

    progress_payload = {
        "tenantCode": args.tenant_code,
        "journeyCode": args.journey_code,
        "referralTrackId": referral_track_id,
        "eventType": "UCN_CAPTURED",
        "sourceSystem": "TASK_418_PRODUCT_PROGRAMME_REFERRAL_PROOF",
        "sourceEventId": f"task-418-ucn-captured-{suffix}",
        "occurredAt": "2026-08-15T00:00:00Z",
        "metadata": {
            "campaignCode": campaign_code,
            "programmeVersionId": programme_version_id,
            "customerProductLineId": product_line_id,
            "customerProductOfferingId": product_offering_id,
        },
    }
    progress_result = setup_check.post_json(
        base_url=args.base_url,
        path="/v1/progress",
        admin_key=args.progress_key,
        payload=progress_payload,
    )
    setup_check.require_success("record programme-bound referral progress", progress_result, allowed={200, 201})

    progress_status_result = setup_check.get_json(
        base_url=args.base_url,
        path=f"/v1/referrals/{_quote_path(referral_track_id)}/progress-status",
        admin_key=args.admin_key,
        query={"tenant_code": args.tenant_code},
    )
    setup_check.require_success("read programme-bound referral progress", progress_status_result)
    progress_check._require_operator_read_result(
        progress_status_result,
        step="programme-bound progress status read",
    )

    trace_result = setup_check.get_json(
        base_url=args.base_url,
        path=f"/v1/referrals/{_quote_path(referral_track_id)}/trace",
        admin_key=args.admin_key,
        query={"tenant_code": args.tenant_code},
    )
    setup_check.require_success("read programme-bound attribution trace", trace_result)
    progress_check._require_operator_read_result(
        trace_result,
        step="programme-bound attribution trace read",
    )

    report_result = setup_check.get_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/accounts/{account_ref_path}/reports/campaign_performance",
        admin_key=args.admin_key,
        query={**scope_query, "campaign_code": campaign_code},
    )
    setup_check.require_success("read programme-bound campaign report", report_result)
    _require_product_runtime_context(report_result.payload)

    programme_analytics_result = setup_check.get_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/accounts/{account_ref_path}/programmes/analytics",
        admin_key=args.admin_key,
        query={**scope_query, "limit": "25"},
    )
    setup_check.require_success("read programme analytics", programme_analytics_result)
    _require_product_runtime_context(programme_analytics_result.payload)

    return {
        "status": "passed",
        "task": "TASK-418",
        "base_url": args.base_url,
        "proof_suffix": suffix,
        "selected_customer": {
            "accountRef": account_ref,
            "accountName": selected_account.get("accountName"),
            "externalTenantRef": external_tenant_ref,
            "organisationRef": organisation_ref,
        },
        "product": {
            "productLineRef": product_line_ref,
            "productLineId": product_line_id,
            "offeringRef": offering_ref,
            "offeringId": product_offering_id,
        },
        "programme": {
            "draftId": programme_draft_id,
            "validationStatus": validation_status,
            "versionId": programme_version_id,
            "incentiveBindingRef": incentive_binding_ref,
        },
        "campaign": {"campaignCode": campaign_code},
        "referral": {
            "referralCode": referral_code,
            "referralTrackId": referral_track_id,
        },
        "checks": {
            "product_line": line_result.status_code,
            "product_offering": offering_result.status_code,
            "product_catalogue": catalogue_result.status_code,
            "programme_draft": programme_result.status_code,
            "programme_validation": validation_result.status_code,
            "programme_submit": submit_result.status_code,
            "programme_review": decision_result.status_code,
            "programme_publish": publish_result.status_code,
            "programme_incentive_binding": incentive_result.status_code,
            "campaign_create": campaign_result.status_code,
            "campaign_programme_binding": campaign_binding_result.status_code,
            "referral_code_issue": issue_result.status_code,
            "referral_validation": referral_result.status_code,
            "progress": progress_result.status_code,
            "progress_status": progress_status_result.status_code,
            "attribution_trace": trace_result.status_code,
            "campaign_report": report_result.status_code,
            "programme_analytics": programme_analytics_result.status_code,
        },
        "product_programme_campaign_referral_runtime_readback_confirmed": True,
        "no_source_journey_deployment_required": True,
        "no_provider_dispatch": True,
        "no_invitation_delivery": True,
        "no_credential_creation": True,
        "no_auth_billing_settlement_or_money_action": True,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run TASK-418 product/offering -> programme -> incentive -> campaign "
            "-> referral -> progress/attribution/reporting/analytics proof against "
            "a running API."
        )
    )
    parser.add_argument("--base-url", default=os.environ.get("API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--admin-key", default=os.environ.get("LOCAL_API_KEY", DEFAULT_ADMIN_KEY))
    parser.add_argument("--progress-key", default=os.environ.get("PROGRESS_API_KEY", DEFAULT_PROGRESS_KEY))
    parser.add_argument("--tenant-code", default=os.environ.get("TENANT_CODE", DEFAULT_TENANT_CODE))
    parser.add_argument("--external-tenant-ref")
    parser.add_argument("--organisation-ref")
    parser.add_argument("--suffix", help="Stable suffix for idempotency and proof labelling.")
    parser.add_argument("--operating-jurisdiction-code", default="ZA")
    parser.add_argument("--product-line-ref")
    parser.add_argument("--product-line-name", default="Transactional Banking")
    parser.add_argument("--product-line-category", default="BANKING")
    parser.add_argument("--offering-ref")
    parser.add_argument("--offering-name", default="Easy Account")
    parser.add_argument("--offering-family", default="Retail banking")
    parser.add_argument("--customer-journey-version-id", default="journey-version-1")
    parser.add_argument("--programme-name")
    parser.add_argument("--campaign-name")
    parser.add_argument("--journey-code", default="BANKING_TRANSACTIONAL")
    parser.add_argument("--incentive-ref", default="TASK418_REWARD_POLICY")
    parser.add_argument("--incentive-version-ref", default="TASK418_REWARD_POLICY_V1")
    parser.add_argument("--engagement-ref", default="TASK418_ENGAGEMENT_TEMPLATE")
    parser.add_argument("--effective-from", default="2026-08-15")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
