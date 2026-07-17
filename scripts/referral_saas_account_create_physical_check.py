from __future__ import annotations

import argparse
import asyncio
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


@dataclass(frozen=True)
class ApiResult:
    status_code: int
    payload: dict[str, Any]


def build_seed_sections(
    *,
    external_tenant_ref: str,
    organisation_ref: str,
    producer_ref: str,
    sponsor_ref: str,
    distributor_ref: str,
    campaign_code: str,
    opportunity_ref: str,
    organisation_name: str,
    admin_contact: str,
) -> dict[str, dict[str, Any]]:
    return {
        "company": {
            "organisation_name": organisation_name,
            "external_tenant_ref": external_tenant_ref,
            "organisation_ref": organisation_ref,
            "country": "South Africa",
            "organisation_type": "Partner",
            "industry": "Banking",
            "admin_contact": admin_contact,
            "intended_role": "Platform admin",
        },
        "producer_sponsor": {
            "producer_sponsor_name": f"{organisation_name} Sponsor",
            "external_tenant_ref": external_tenant_ref,
            "producer_ref": producer_ref,
            "sponsor_ref": sponsor_ref,
            "organisation_ref": organisation_ref,
            "industry": "Banking",
            "funding_model_intention": "Referral SaaS setup proof only",
            "admin_contact": admin_contact,
            "campaign_opportunity_role": "Sponsor owner",
        },
        "distributor": {
            "distributor_name": f"{organisation_name} Distribution",
            "external_tenant_ref": external_tenant_ref,
            "distributor_ref": distributor_ref,
            "organisation_ref": organisation_ref,
            "channel_type": "Partner channel",
            "market_country": "South Africa",
            "admin_contact": admin_contact,
            "distribution_model": "Referral SaaS direct",
            "campaign_opportunity_participation": "Referral attribution testing",
        },
        "member_role": {
            "organisation_ref": organisation_ref,
            "external_tenant_ref": external_tenant_ref,
            "user_email": admin_contact,
            "display_name": "Referral SaaS Operator",
            "role_family": "PLATFORM_ADMIN",
            "participant_type": "operator",
            "access_scope": "account_setup",
            "invite_status": "draft_only",
        },
        "campaign_opportunity": {
            "organisation_ref": organisation_ref,
            "producer_ref": producer_ref,
            "sponsor_ref": sponsor_ref,
            "campaign_code": campaign_code,
            "opportunity_ref": opportunity_ref,
            "campaign_name": "Referral SaaS physical account proof",
            "market_country": "South Africa",
            "distribution_model": "Referral SaaS direct",
            "eligible_distributor_type": "Partner",
            "intended_outcome_event": "ACCOUNT_OPENED",
            "reward_commission_policy_intention": "No money movement in proof",
            "funding_model_intention": "No funding movement in proof",
            "go_live_target_status": "disabled",
            "link_code_intent": "Issue referral codes after account setup",
        },
        "webhook_api": {
            "organisation_ref": organisation_ref,
            "external_tenant_ref": external_tenant_ref,
            "integration_owner_contact": admin_contact,
            "api_environment_intention": "local",
            "callback_url_placeholder": "https://example.test/referral-saas/webhooks",
            "selected_webhook_event_categories": ["progress", "attribution"],
            "intended_authentication_method": "future credential setup",
            "ip_allowlist_notes": "not configured in physical proof",
            "payload_format_version": "referral-saas.v1",
            "go_live_readiness_status": "disabled",
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
    encoded = urllib.parse.urlencode(query)
    return request_json(
        method="GET",
        base_url=base_url,
        path=f"{path}?{encoded}",
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
        headers={
            "Content-Type": "application/json",
            "x-api-key": admin_key,
        },
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


def assert_no_internal_tenant_identifier(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, sort_keys=True).lower()
    forbidden = ("tenantcode", "tenant_code")
    if any(item in rendered for item in forbidden):
        raise RuntimeError("Safe product payload exposed an internal tenant identifier.")


async def verify_db_rows(*, dsn: str, external_tenant_ref: str, organisation_ref: str) -> dict[str, Any]:
    import asyncpg

    conn = await asyncpg.connect(dsn)
    try:
        row = await conn.fetchrow(
            """
            SELECT
                account.account_id,
                account.account_code,
                account.status AS account_status,
                account.onboarding_status,
                account_tenant.account_tenant_id,
                account_tenant.status AS tenant_link_status,
                COUNT(DISTINCT external_ref.external_ref_id) AS external_ref_count,
                COUNT(DISTINCT audit.account_audit_event_id) AS audit_event_count
            FROM platform_accounts account
            JOIN platform_account_tenants account_tenant
                ON account_tenant.account_id = account.account_id
            JOIN platform_external_tenant_refs external_ref
                ON external_ref.account_id = account.account_id
            LEFT JOIN platform_account_audit_events audit
                ON audit.account_id = account.account_id
            WHERE account.primary_external_tenant_ref = $1
              AND external_ref.external_ref IN ($1, $2)
            GROUP BY
                account.account_id,
                account.account_code,
                account.status,
                account.onboarding_status,
                account_tenant.account_tenant_id,
                account_tenant.status
            """,
            external_tenant_ref,
            organisation_ref,
        )
    finally:
        await conn.close()

    if not row:
        raise RuntimeError("DB verification did not find the created account foundation.")
    payload = dict(row)
    if payload["external_ref_count"] < 2:
        raise RuntimeError("DB verification found fewer than two external references.")
    if payload["audit_event_count"] < 1:
        raise RuntimeError("DB verification did not find an account audit event.")
    return {key: str(value) for key, value in payload.items()}


async def seed_ready_for_review_draft_db(
    *,
    dsn: str,
    draft_ref: str,
    external_tenant_ref: str,
    organisation_ref: str,
    sections: dict[str, dict[str, Any]],
    correlation_id: str,
) -> dict[str, Any]:
    import asyncpg

    conn = await asyncpg.connect(dsn)
    try:
        async with conn.transaction():
            draft = await conn.fetchrow(
                """
                INSERT INTO onboarding_drafts (
                    draft_ref,
                    contract_version,
                    status,
                    external_tenant_ref,
                    organisation_ref,
                    created_by_ref,
                    created_by_role,
                    source,
                    correlation_id,
                    safe_summary,
                    metadata,
                    redactions
                )
                VALUES (
                    $1, 'onboarding.v1', 'READY_FOR_REVIEW', $2, $3,
                    'TASK_206_PHYSICAL_CHECK', 'PLATFORM_ADMIN',
                    'TASK_206_PHYSICAL_CHECK', $4, $5::jsonb, $6::jsonb,
                    '["internal_identifier"]'::jsonb
                )
                ON CONFLICT (draft_ref)
                DO UPDATE SET
                    status = 'READY_FOR_REVIEW',
                    external_tenant_ref = EXCLUDED.external_tenant_ref,
                    organisation_ref = EXCLUDED.organisation_ref,
                    safe_summary = EXCLUDED.safe_summary,
                    metadata = EXCLUDED.metadata,
                    redactions = EXCLUDED.redactions,
                    updated_by_ref = 'TASK_206_PHYSICAL_CHECK',
                    correlation_id = EXCLUDED.correlation_id,
                    draft_version = onboarding_drafts.draft_version + 1,
                    updated_at = NOW()
                RETURNING draft_id, draft_ref, draft_version, status
                """,
                draft_ref,
                external_tenant_ref,
                organisation_ref,
                correlation_id,
                json.dumps(
                    {
                        "organisation_name": sections["company"]["organisation_name"],
                        "validation_status": "VALID",
                        "readiness_status": "READY_FOR_REVIEW",
                        "no_live_action_confirmed": True,
                    },
                    sort_keys=True,
                ),
                json.dumps(
                    {
                        "source": "TASK-206",
                        "seeded_reviewed_draft": True,
                    },
                    sort_keys=True,
                ),
            )
            for section_key, section_payload in sections.items():
                await conn.execute(
                    """
                    INSERT INTO onboarding_draft_sections (
                        draft_id,
                        section_key,
                        section_status,
                        section_payload,
                        redaction_summary,
                        missing_evidence,
                        source_warnings
                    )
                    VALUES (
                        $1, $2, 'READY', $3::jsonb,
                        '{}'::jsonb, '[]'::jsonb, '[]'::jsonb
                    )
                    ON CONFLICT (draft_id, section_key)
                    DO UPDATE SET
                        section_status = 'READY',
                        section_payload = EXCLUDED.section_payload,
                        redaction_summary = EXCLUDED.redaction_summary,
                        missing_evidence = EXCLUDED.missing_evidence,
                        source_warnings = EXCLUDED.source_warnings,
                        section_version = onboarding_draft_sections.section_version + 1,
                        updated_at = NOW()
                    """,
                    draft["draft_id"],
                    section_key,
                    json.dumps(section_payload, sort_keys=True),
                )
    finally:
        await conn.close()

    return {key: str(value) for key, value in dict(draft).items()}


def run(args: argparse.Namespace) -> dict[str, Any]:
    suffix = args.suffix or str(int(time.time()))
    external_tenant_ref = args.external_tenant_ref or f"task-206-{suffix}"
    organisation_ref = args.organisation_ref or f"org-task-206-{suffix}"
    producer_ref = f"producer-{suffix}"
    sponsor_ref = f"sponsor-{suffix}"
    distributor_ref = f"distributor-{suffix}"
    campaign_code = f"CMP-{suffix}"
    opportunity_ref = f"opp-{suffix}"
    organisation_name = args.organisation_name or f"Task 206 Account {suffix}"
    admin_contact = args.admin_contact or "referral-saas-proof@example.test"
    correlation_id = f"task-206-account-create-proof-{suffix}"

    sections = build_seed_sections(
        external_tenant_ref=external_tenant_ref,
        organisation_ref=organisation_ref,
        producer_ref=producer_ref,
        sponsor_ref=sponsor_ref,
        distributor_ref=distributor_ref,
        campaign_code=campaign_code,
        opportunity_ref=opportunity_ref,
        organisation_name=organisation_name,
        admin_contact=admin_contact,
    )
    direct_seed_payload = None

    if args.draft_ref:
        draft_ref = args.draft_ref
        save_payload: dict[str, Any] | None = None
        submit_payload: dict[str, Any] | None = None
    elif args.seed_reviewed_draft_db:
        if not args.db_dsn:
            raise RuntimeError("--seed-reviewed-draft-db requires --db-dsn.")
        draft_ref = f"draft_task_206_{suffix}".replace("-", "_")
        direct_seed_payload = asyncio.run(
            seed_ready_for_review_draft_db(
                dsn=args.db_dsn,
                draft_ref=draft_ref,
                external_tenant_ref=external_tenant_ref,
                organisation_ref=organisation_ref,
                sections=sections,
                correlation_id=correlation_id,
            )
        )
        save_payload = None
        submit_payload = None
    else:
        save_payload = {
            "external_tenant_ref": external_tenant_ref,
            "organisation_ref": organisation_ref,
            "producer_ref": producer_ref,
            "sponsor_ref": sponsor_ref,
            "distributor_ref": distributor_ref,
            "campaign_code": campaign_code,
            "opportunity_ref": opportunity_ref,
            "sections": sections,
            "idempotency_key": f"task-206-save-{suffix}",
            "correlation_id": correlation_id,
        }
        save_result = post_json(
            base_url=args.base_url,
            path="/admin/onboarding/drafts",
            admin_key=args.admin_key,
            payload=save_payload,
        )
        require_success("save onboarding draft", save_result)
        draft_ref = str(save_result.payload["draft_ref"])
        submit_payload = {
            "external_tenant_ref": external_tenant_ref,
            "organisation_ref": organisation_ref,
            "expected_version": save_result.payload.get("draft_version", 1),
            "idempotency_key": f"task-206-submit-{suffix}",
            "correlation_id": correlation_id,
        }
        submit_result = post_json(
            base_url=args.base_url,
            path=f"/admin/onboarding/drafts/{urllib.parse.quote(draft_ref)}/submit-for-review",
            admin_key=args.admin_key,
            payload=submit_payload,
        )
        try:
            require_success("submit onboarding draft for review", submit_result)
        except RuntimeError as exc:
            raise RuntimeError(
                f"{exc} Use --seed-reviewed-draft-db with --db-dsn when the "
                "goal is TASK-206 account creation API physical proof."
            ) from exc

    create_payload = {
        "draft_ref": draft_ref,
        "internal_tenant_code": args.internal_tenant_code,
        "idempotency_key": f"task-206-create-{suffix}",
        "correlation_id": correlation_id,
    }
    create_result = post_json(
        base_url=args.base_url,
        path="/v1/referral-saas/accounts/from-draft",
        admin_key=args.admin_key,
        payload=create_payload,
    )
    require_success("create account from draft", create_result)
    assert_no_internal_tenant_identifier(create_result.payload)

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
    require_success("resolve created account", resolve_result)
    assert_no_internal_tenant_identifier(resolve_result.payload)

    db_payload = None
    if args.db_dsn:
        db_payload = asyncio.run(
            verify_db_rows(
                dsn=args.db_dsn,
                external_tenant_ref=external_tenant_ref,
                organisation_ref=organisation_ref,
            )
        )

    return {
        "status": "passed",
        "task": "TASK-206",
        "base_url": args.base_url,
        "draft_ref": draft_ref,
        "external_tenant_ref": external_tenant_ref,
        "organisation_ref": organisation_ref,
        "internal_tenant_code_used_for_command": args.internal_tenant_code,
        "created_account": create_result.payload.get("account"),
        "resolved_account": resolve_result.payload.get("account"),
        "db_verification": db_payload,
        "guardrails": create_result.payload.get("guardrails", []),
        "redactions": create_result.payload.get("redactions", []),
        "no_adjacent_live_action_confirmed": create_result.payload.get(
            "no_adjacent_live_action_confirmed"
        ),
        "seeded_draft": save_payload is not None,
        "seeded_reviewed_draft_db": direct_seed_payload,
        "no_money_movement": True,
        "no_campaign_activation": True,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Physically verify Referral SaaS account creation from a reviewed "
            "onboarding draft against a local/staging API."
        )
    )
    parser.add_argument("--base-url", default=os.environ.get("API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--admin-key", default=os.environ.get("LOCAL_API_KEY", DEFAULT_ADMIN_KEY))
    parser.add_argument(
        "--internal-tenant-code",
        default=os.environ.get("TASK_206_INTERNAL_TENANT_CODE", DEFAULT_INTERNAL_TENANT_CODE),
    )
    parser.add_argument("--db-dsn", default=os.environ.get("APP_DB_DSN"))
    parser.add_argument("--draft-ref", help="Use an existing READY_FOR_REVIEW draft.")
    parser.add_argument(
        "--seed-reviewed-draft-db",
        action="store_true",
        help=(
            "Create or update a local READY_FOR_REVIEW draft directly in the DB "
            "before calling the real account creation API."
        ),
    )
    parser.add_argument("--external-tenant-ref")
    parser.add_argument("--organisation-ref")
    parser.add_argument("--organisation-name")
    parser.add_argument("--admin-contact")
    parser.add_argument("--suffix", help="Stable suffix for repeatable seeded references.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
