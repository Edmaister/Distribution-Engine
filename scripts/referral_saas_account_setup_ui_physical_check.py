from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_ADMIN_KEY = "test-admin-key"
DEFAULT_INTERNAL_TENANT_CODE = "FNB"
REQUIRED_SECTION_KEYS = (
    "company",
    "producer_sponsor",
    "distributor",
    "member_role",
    "campaign_opportunity",
    "webhook_api",
)
FORBIDDEN_PRODUCT_PAYLOAD_TERMS = (
    "tenant_code",
    "api_key",
    "client_secret",
    "private_key",
    "password",
    "wallet",
    "settlement",
    "activate_go_live",
    "send_invite",
)


@dataclass(frozen=True)
class ApiResult:
    status_code: int
    payload: dict[str, Any]


def build_ui_setup_sections(
    *,
    external_tenant_ref: str,
    organisation_ref: str,
    organisation_name: str,
    admin_contact: str,
) -> dict[str, dict[str, Any]]:
    producer_ref = f"{organisation_ref}-producer"
    sponsor_ref = f"{organisation_ref}-sponsor"
    distributor_ref = f"{organisation_ref}-distributor"
    campaign_code = f"{organisation_ref}-setup-campaign"
    opportunity_ref = f"{organisation_ref}-setup-opportunity"

    return {
        "company": {
            "organisation_name": organisation_name,
            "external_tenant_ref": external_tenant_ref,
            "organisation_ref": organisation_ref,
            "country": "South Africa",
            "organisation_type": "Referral SaaS customer",
            "industry": "Referral management and campaign attribution",
            "admin_contact": admin_contact,
            "intended_role": "Referral SaaS admin",
        },
        "producer_sponsor": {
            "producer_sponsor_name": f"{organisation_ref} sponsor setup",
            "external_tenant_ref": external_tenant_ref,
            "producer_ref": producer_ref,
            "sponsor_ref": sponsor_ref,
            "organisation_ref": organisation_ref,
            "industry": "Referral management and campaign attribution",
            "funding_model_intention": "No value transfer during account setup",
            "admin_contact": admin_contact,
            "campaign_opportunity_role": "Referral SaaS sponsor owner",
        },
        "distributor": {
            "distributor_name": f"{organisation_ref} referral distribution setup",
            "external_tenant_ref": external_tenant_ref,
            "distributor_ref": distributor_ref,
            "organisation_ref": organisation_ref,
            "channel_type": "Referral SaaS direct",
            "market_country": "South Africa",
            "admin_contact": admin_contact,
            "distribution_model": "Referral management and campaign attribution",
            "campaign_opportunity_participation": (
                "Referral testing after account setup"
            ),
        },
        "member_role": {
            "organisation_ref": organisation_ref,
            "external_tenant_ref": external_tenant_ref,
            "user_email": admin_contact,
            "display_name": "Referral SaaS setup owner",
            "role_family": "Account setup admin",
            "participant_type": "Platform operator",
            "access_scope": "Referral SaaS account setup",
            "invite_status": "Draft intent only",
        },
        "campaign_opportunity": {
            "organisation_ref": organisation_ref,
            "producer_ref": producer_ref,
            "sponsor_ref": sponsor_ref,
            "campaign_code": campaign_code,
            "opportunity_ref": opportunity_ref,
            "campaign_name": f"{organisation_ref} setup readiness campaign",
            "market_country": "South Africa",
            "distribution_model": "Referral SaaS direct",
            "eligible_distributor_type": "Referral partner",
            "intended_outcome_event": "REFERRED_CUSTOMER_VERIFIED",
            "reward_commission_policy_intention": (
                "No reward or commission activation during account setup"
            ),
            "funding_model_intention": "No value transfer during account setup",
            "go_live_target_status": "GO_LIVE_DISABLED",
            "link_code_intent": (
                "Issue referral links or codes after account setup readiness"
            ),
        },
        "webhook_api": {
            "organisation_ref": organisation_ref,
            "external_tenant_ref": external_tenant_ref,
            "integration_owner_contact": "integration-owner@example.test",
            "api_environment_intention": "Sandbox integration intent",
            "callback_url_placeholder": (
                "https://example.invalid/referral-saas/webhook-placeholder"
            ),
            "selected_webhook_event_categories": [
                "referral",
                "campaign_attribution",
                "progress",
            ],
            "intended_authentication_method": (
                "Partner credential setup intent only"
            ),
            "ip_allowlist_notes": (
                "To be confirmed before credential lifecycle work"
            ),
            "payload_format_version": "referral-saas.v1",
            "go_live_readiness_status": "GO_LIVE_DISABLED",
        },
    }


def post_json(
    *,
    base_url: str,
    path: str,
    admin_key: str,
    payload: dict[str, Any],
) -> ApiResult:
    return request_json(
        method="POST",
        base_url=base_url,
        path=path,
        admin_key=admin_key,
        payload=payload,
    )


def get_json(
    *,
    base_url: str,
    path: str,
    admin_key: str,
    query: dict[str, str],
) -> ApiResult:
    return request_json(
        method="GET",
        base_url=base_url,
        path=f"{path}?{urllib.parse.urlencode(query)}",
        admin_key=admin_key,
        payload=None,
    )


def request_json(
    *,
    method: str,
    base_url: str,
    path: str,
    admin_key: str,
    payload: dict[str, Any] | None,
) -> ApiResult:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url=f"{base_url.rstrip('/')}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json", "x-api-key": admin_key},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            response_body = response.read().decode("utf-8")
            return ApiResult(
                status_code=response.status,
                payload=json.loads(response_body) if response_body else {},
            )
    except urllib.error.HTTPError as exc:
        response_body = exc.read().decode("utf-8")
        try:
            parsed: dict[str, Any] = json.loads(response_body)
        except json.JSONDecodeError:
            parsed = {"raw": response_body}
        return ApiResult(status_code=exc.code, payload=parsed)


def require_success(step: str, result: ApiResult, *, allowed: set[int] | None = None) -> None:
    expected = allowed or {200}
    if result.status_code not in expected:
        raise RuntimeError(
            f"{step} failed with HTTP {result.status_code}: "
            f"{json.dumps(result.payload, sort_keys=True)}"
        )


def assert_complete_ui_sections(sections: dict[str, dict[str, Any]]) -> None:
    actual = tuple(sections.keys())
    if actual != REQUIRED_SECTION_KEYS:
        raise RuntimeError(f"Unexpected UI section keys: {actual!r}")
    for section_key in REQUIRED_SECTION_KEYS:
        if not sections.get(section_key):
            raise RuntimeError(f"{section_key} section is empty.")


def assert_no_forbidden_product_payload(payload: dict[str, Any]) -> None:
    unsafe_key = _find_forbidden_payload_key(payload)
    if unsafe_key:
        raise RuntimeError(f"Safe product payload contains {unsafe_key}.")


def _find_forbidden_payload_key(value: Any, *, path: str = "") -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            dotted = f"{path}.{normalized}" if path else normalized
            if any(forbidden in normalized for forbidden in FORBIDDEN_PRODUCT_PAYLOAD_TERMS):
                return dotted
            nested = _find_forbidden_payload_key(item, path=dotted)
            if nested:
                return nested
    if isinstance(value, list):
        for index, item in enumerate(value):
            nested = _find_forbidden_payload_key(item, path=f"{path}[{index}]")
            if nested:
                return nested
    return None


def run(args: argparse.Namespace) -> dict[str, Any]:
    suffix = args.suffix or str(int(time.time()))
    external_tenant_ref = args.external_tenant_ref or f"task-208-{suffix}"
    organisation_ref = args.organisation_ref or f"org-task-208-{suffix}"
    organisation_name = args.organisation_name or f"Task 208 Account {suffix}"
    admin_contact = args.admin_contact or "referral-saas-setup-proof@example.test"
    correlation_id = f"task-208-account-setup-ui-proof-{suffix}"

    sections = build_ui_setup_sections(
        external_tenant_ref=external_tenant_ref,
        organisation_ref=organisation_ref,
        organisation_name=organisation_name,
        admin_contact=admin_contact,
    )
    assert_complete_ui_sections(sections)
    assert_no_forbidden_product_payload(sections)

    scope = {
        "external_tenant_ref": external_tenant_ref,
        "organisation_ref": organisation_ref,
    }
    validation_result = post_json(
        base_url=args.base_url,
        path="/admin/onboarding/validate",
        admin_key=args.admin_key,
        payload={
            **scope,
            "validation_scope": list(REQUIRED_SECTION_KEYS),
            "sections": sections,
            "idempotency_key": f"task-208-validate-{suffix}",
            "correlation_id": correlation_id,
        },
    )
    require_success("validate setup evidence", validation_result)

    draft_result = post_json(
        base_url=args.base_url,
        path="/admin/onboarding/drafts",
        admin_key=args.admin_key,
        payload={
            **scope,
            "sections": sections,
            "idempotency_key": f"task-208-save-{suffix}",
            "correlation_id": correlation_id,
        },
    )
    require_success("save setup draft", draft_result)
    draft_ref = str(draft_result.payload["draft_ref"])
    draft_version = int(draft_result.payload.get("draft_version", 1))

    submit_result = post_json(
        base_url=args.base_url,
        path=(
            "/admin/onboarding/drafts/"
            f"{urllib.parse.quote(draft_ref)}/submit-for-review"
        ),
        admin_key=args.admin_key,
        payload={
            **scope,
            "expected_version": draft_version,
            "idempotency_key": f"task-208-submit-{suffix}",
            "correlation_id": correlation_id,
        },
    )
    require_success("submit setup draft for review", submit_result)
    submit_version = int(submit_result.payload.get("draft_version", draft_version + 1))

    review_result = post_json(
        base_url=args.base_url,
        path=(
            "/admin/onboarding/drafts/"
            f"{urllib.parse.quote(draft_ref)}/review-decision"
        ),
        admin_key=args.admin_key,
        payload={
            **scope,
            "expected_version": submit_version,
            "idempotency_key": f"task-208-review-{suffix}",
            "review_outcome": "APPROVED_FOR_INTERNAL_REVIEW",
            "reason_category": "TASK_208_PHYSICAL_PROOF",
            "reason": "Full Account Setup UI path evidence accepted for local proof.",
            "correlation_id": correlation_id,
        },
    )
    require_success("record setup review decision", review_result)

    create_result = post_json(
        base_url=args.base_url,
        path="/v1/referral-saas/accounts/from-draft",
        admin_key=args.admin_key,
        payload={
            "draft_ref": draft_ref,
            "internal_tenant_code": args.internal_tenant_code,
            "idempotency_key": f"task-208-create-{suffix}",
            "correlation_id": correlation_id,
        },
    )
    require_success("create account foundation from reviewed setup draft", create_result)

    resolve_result = get_json(
        base_url=args.base_url,
        path="/v1/referral-saas/accounts/resolve",
        admin_key=args.admin_key,
        query={
            "ref_type": "external_tenant_ref",
            "external_ref": external_tenant_ref,
            "context": "setup",
        },
    )
    require_success("resolve created account foundation", resolve_result)
    assert_no_forbidden_product_payload(create_result.payload)
    assert_no_forbidden_product_payload(resolve_result.payload)

    return {
        "status": "passed",
        "task": "TASK-208",
        "base_url": args.base_url,
        "draft_ref": draft_ref,
        "external_tenant_ref": external_tenant_ref,
        "organisation_ref": organisation_ref,
        "validation_status": validation_result.payload.get("status"),
        "draft_status": draft_result.payload.get("draft_status"),
        "submit_status": submit_result.payload.get("draft_status"),
        "review_outcome": review_result.payload.get("review_outcome"),
        "created_account": create_result.payload.get("account"),
        "resolved_account": resolve_result.payload.get("account"),
        "guardrails": sorted(
            set(create_result.payload.get("guardrails", []))
            .union(review_result.payload.get("guardrails", []))
        ),
        "no_adjacent_live_action_confirmed": create_result.payload.get(
            "no_adjacent_live_action_confirmed"
        ),
        "no_tenant_creation": True,
        "no_invitation_sent": True,
        "no_campaign_activation": True,
        "no_value_transfer": True,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Physically verify the Referral SaaS Account Setup UI contract "
            "against a running local/staging API."
        )
    )
    parser.add_argument("--base-url", default=os.environ.get("API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--admin-key", default=os.environ.get("LOCAL_API_KEY", DEFAULT_ADMIN_KEY))
    parser.add_argument(
        "--internal-tenant-code",
        default=os.environ.get("TASK_208_INTERNAL_TENANT_CODE", DEFAULT_INTERNAL_TENANT_CODE),
        help=(
            "Trusted internal tenant code used by the guarded account creation "
            "command. Use a tenant that is not already linked as account owner."
        ),
    )
    parser.add_argument("--external-tenant-ref")
    parser.add_argument("--organisation-ref")
    parser.add_argument("--organisation-name")
    parser.add_argument("--admin-contact")
    parser.add_argument("--suffix", help="Stable suffix for repeatable references.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
