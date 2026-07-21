from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Literal

SmokeClass = Literal["read_only", "seeded_write"]


@dataclass(frozen=True)
class SmokeRoute:
    name: str
    method: str
    path: str
    smoke_class: SmokeClass
    auth_hint: str
    environment_rule: str
    seeded_subjects: list[str]
    expected_state_change: str
    curl_template: str


READ_ONLY_ROUTES = [
    SmokeRoute(
        name="campaign_readiness",
        method="GET",
        path="/admin/campaigns/{campaign_code}/readiness",
        smoke_class="read_only",
        auth_hint="distribution admin key",
        environment_rule="local/staging/production read-only where auth permits",
        seeded_subjects=["base_url", "admin_token", "tenant_code", "campaign_code"],
        expected_state_change="none",
        curl_template=(
            'curl -sS -H "Authorization: Bearer {admin_token}" '
            '"{base_url}/admin/campaigns/{campaign_code}/readiness?tenant_code={tenant_code}"'
        ),
    ),
    SmokeRoute(
        name="link_code_inspect",
        method="GET",
        path="/admin/links/inspect",
        smoke_class="read_only",
        auth_hint="distribution admin key",
        environment_rule="local/staging/production read-only where auth permits",
        seeded_subjects=[
            "base_url",
            "admin_token",
            "tenant_code",
            "source_type",
            "code_or_ref",
        ],
        expected_state_change="none",
        curl_template=(
            'curl -sS -H "Authorization: Bearer {admin_token}" '
            '"{base_url}/admin/links/inspect?tenant_code={tenant_code}'
            '&source_type={source_type}&code_or_ref={code_or_ref}"'
        ),
    ),
    SmokeRoute(
        name="outcome_trace",
        method="GET",
        path="/admin/outcomes/{referral_track_id}/trace",
        smoke_class="read_only",
        auth_hint="operator/admin session key",
        environment_rule="local/staging/production read-only where auth permits",
        seeded_subjects=["base_url", "admin_token", "tenant_code", "referral_track_id"],
        expected_state_change="none",
        curl_template=(
            'curl -sS -H "Authorization: Bearer {admin_token}" '
            '"{base_url}/admin/outcomes/{referral_track_id}/trace?tenant_code={tenant_code}"'
        ),
    ),
    SmokeRoute(
        name="tenant_safe_analytics",
        method="GET",
        path="/admin/analytics/reports/{report_type}",
        smoke_class="read_only",
        auth_hint="admin analytics role",
        environment_rule="local/staging/production read-only where auth permits",
        seeded_subjects=["base_url", "admin_token", "tenant_code", "report_type"],
        expected_state_change="none",
        curl_template=(
            'curl -sS -H "Authorization: Bearer {admin_token}" '
            '"{base_url}/admin/analytics/reports/{report_type}?tenant_code={tenant_code}"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_operator_link_code_inspect",
        method="GET",
        path="/v1/referral-saas/operator/links/inspect",
        smoke_class="read_only",
        auth_hint="Referral SaaS operator/support role",
        environment_rule="local/staging/production read-only where auth permits",
        seeded_subjects=[
            "base_url",
            "admin_token",
            "tenant_code",
            "source_type",
            "code_or_ref",
        ],
        expected_state_change="none",
        curl_template=(
            'curl -sS -H "Authorization: Bearer {admin_token}" '
            '"{base_url}/v1/referral-saas/operator/links/inspect'
            '?tenant_code={tenant_code}&source_type={source_type}'
            '&code_or_ref={code_or_ref}"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_operator_attribution_trace",
        method="GET",
        path="/v1/referral-saas/operator/outcomes/{referral_track_id}/trace",
        smoke_class="read_only",
        auth_hint="Referral SaaS operator/support role",
        environment_rule="local/staging/production read-only where auth permits",
        seeded_subjects=[
            "base_url",
            "admin_token",
            "tenant_code",
            "referral_track_id",
        ],
        expected_state_change="none",
        curl_template=(
            'curl -sS -H "Authorization: Bearer {admin_token}" '
            '"{base_url}/v1/referral-saas/operator/outcomes'
            '/{referral_track_id}/trace?tenant_code={tenant_code}"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_operator_progress_status",
        method="GET",
        path="/v1/referral-saas/operator/referrals/{referral_track_id}/progress-status",
        smoke_class="read_only",
        auth_hint="Referral SaaS operator/support role",
        environment_rule="local/staging/production read-only where auth permits",
        seeded_subjects=[
            "base_url",
            "admin_token",
            "tenant_code",
            "referral_track_id",
        ],
        expected_state_change="none",
        curl_template=(
            'curl -sS -H "Authorization: Bearer {admin_token}" '
            '"{base_url}/v1/referral-saas/operator/referrals'
            '/{referral_track_id}/progress-status?tenant_code={tenant_code}"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_account_registry",
        method="GET",
        path="/v1/referral-saas/accounts",
        smoke_class="read_only",
        auth_hint="Referral SaaS account reader role",
        environment_rule="local/staging/production read-only where auth permits",
        seeded_subjects=[
            "base_url",
            "admin_token",
        ],
        expected_state_change="none",
        curl_template=(
            'curl -sS -H "Authorization: Bearer {admin_token}" '
            '"{base_url}/v1/referral-saas/accounts?limit=50"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_account_resolve",
        method="GET",
        path="/v1/referral-saas/accounts/resolve",
        smoke_class="read_only",
        auth_hint="Referral SaaS account reader role",
        environment_rule="local/staging/production read-only where auth permits",
        seeded_subjects=[
            "base_url",
            "admin_token",
            "ref_type",
            "external_ref",
        ],
        expected_state_change="none",
        curl_template=(
            'curl -sS -H "Authorization: Bearer {admin_token}" '
            '"{base_url}/v1/referral-saas/accounts/resolve'
            '?ref_type={ref_type}&external_ref={external_ref}&context=setup"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_account_membership_posture",
        method="GET",
        path="/v1/referral-saas/accounts/membership-posture",
        smoke_class="read_only",
        auth_hint="Referral SaaS account reader role",
        environment_rule="local/staging/production read-only where auth permits",
        seeded_subjects=[
            "base_url",
            "admin_token",
            "ref_type",
            "external_ref",
        ],
        expected_state_change="none",
        curl_template=(
            'curl -sS -H "Authorization: Bearer {admin_token}" '
            '"{base_url}/v1/referral-saas/accounts/membership-posture'
            '?ref_type={ref_type}&external_ref={external_ref}&context=setup"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_membership_activation_readiness",
        method="GET",
        path="/v1/referral-saas/accounts/{account_ref}/membership-activation-readiness",
        smoke_class="read_only",
        auth_hint="Referral SaaS account reader role",
        environment_rule="local/staging/production read-only where auth permits",
        seeded_subjects=[
            "base_url",
            "admin_token",
            "account_ref",
            "ref_type",
            "external_ref",
        ],
        expected_state_change="none",
        curl_template=(
            'curl -sS -H "Authorization: Bearer {admin_token}" '
            '"{base_url}/v1/referral-saas/accounts/{account_ref}'
            '/membership-activation-readiness?ref_type={ref_type}'
            '&external_ref={external_ref}&context=setup"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_technical_setup_readiness",
        method="GET",
        path="/v1/referral-saas/accounts/{account_ref}/technical-setup-readiness",
        smoke_class="read_only",
        auth_hint="Referral SaaS account reader role",
        environment_rule="local/staging/production read-only where auth permits",
        seeded_subjects=[
            "base_url",
            "admin_token",
            "account_ref",
            "ref_type",
            "external_ref",
        ],
        expected_state_change="none",
        curl_template=(
            'curl -sS -H "Authorization: Bearer {admin_token}" '
            '"{base_url}/v1/referral-saas/accounts/{account_ref}'
            '/technical-setup-readiness?ref_type={ref_type}'
            '&external_ref={external_ref}&context=setup"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_campaign_performance_report",
        method="GET",
        path="/v1/referral-saas/reports/{report_type}",
        smoke_class="read_only",
        auth_hint="Referral SaaS report reader role",
        environment_rule="local/staging/production read-only where auth permits",
        seeded_subjects=[
            "base_url",
            "admin_token",
            "tenant_code",
            "campaign_code",
        ],
        expected_state_change="none",
        curl_template=(
            'curl -sS -H "Authorization: Bearer {admin_token}" '
            '"{base_url}/v1/referral-saas/reports/campaign_performance'
            '?tenant_code={tenant_code}&campaign_code={campaign_code}"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_campaign_performance_export_validate",
        method="POST",
        path="/v1/referral-saas/reports/{report_type}/exports/validate",
        smoke_class="read_only",
        auth_hint="Referral SaaS report reader role",
        environment_rule="local/staging/production side-effect-free where auth permits",
        seeded_subjects=[
            "base_url",
            "admin_token",
            "tenant_code",
            "campaign_code",
        ],
        expected_state_change="none",
        curl_template=(
            'curl -sS -X POST -H "Authorization: Bearer {admin_token}" '
            '-H "Content-Type: application/json" '
            '-d \'{"format":"json","redaction_profile":"tenant_safe",'
            '"filters":{"campaign_code":"{campaign_code}"},"row_limit":10}\' '
            '"{base_url}/v1/referral-saas/reports/campaign_performance'
            '/exports/validate?tenant_code={tenant_code}"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_campaign_performance_export_preview",
        method="POST",
        path="/v1/referral-saas/reports/{report_type}/exports/preview",
        smoke_class="read_only",
        auth_hint="Referral SaaS report reader role",
        environment_rule="local/staging/production side-effect-free where auth permits",
        seeded_subjects=[
            "base_url",
            "admin_token",
            "tenant_code",
            "campaign_code",
        ],
        expected_state_change="none",
        curl_template=(
            'curl -sS -X POST -H "Authorization: Bearer {admin_token}" '
            '-H "Content-Type: application/json" '
            '-d \'{"format":"csv","redaction_profile":"tenant_safe",'
            '"filters":{"campaign_code":"{campaign_code}"},"row_limit":10}\' '
            '"{base_url}/v1/referral-saas/reports/campaign_performance'
            '/exports/preview?tenant_code={tenant_code}"'
        ),
    ),
]


SEEDED_WRITE_ROUTES = [
    SmokeRoute(
        name="referral_code_issue",
        method="POST",
        path="/referrals/codes",
        smoke_class="seeded_write",
        auth_hint="partner/integration key",
        environment_rule="local/staging seeded tenant only",
        seeded_subjects=[
            "base_url",
            "partner_token",
            "tenant_code",
            "referrer_ucn",
            "sticker",
            "segment",
        ],
        expected_state_change="may create or reuse referrer_codes row",
        curl_template=(
            'curl -sS -X POST -H "Authorization: Bearer {partner_token}" '
            '-H "Content-Type: application/json" '
            '-d \'{"referrer_ucn":"{referrer_ucn}","tenant":"{tenant_code}",'
            '"sticker":"{sticker}","segment":"{segment}","accepted_terms":true}\' '
            '"{base_url}/referrals/codes"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_referral_code_issue",
        method="POST",
        path="/v1/referral-saas/referral-codes",
        smoke_class="seeded_write",
        auth_hint="Referral SaaS partner/integration key",
        environment_rule="local/staging seeded tenant only",
        seeded_subjects=[
            "base_url",
            "partner_token",
            "referrer_ucn",
            "sticker",
            "segment",
        ],
        expected_state_change="may create or reuse referrer_codes row through product wrapper",
        curl_template=(
            'curl -sS -X POST -H "Authorization: Bearer {partner_token}" '
            '-H "Content-Type: application/json" '
            '-d \'{"referrerUcn":"{referrer_ucn}",'
            '"sticker":"{sticker}","segment":"{segment}",'
            '"acceptedTerms":true}\' '
            '"{base_url}/v1/referral-saas/referral-codes"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_account_create_from_draft",
        method="POST",
        path="/v1/referral-saas/accounts/from-draft",
        smoke_class="seeded_write",
        auth_hint="Referral SaaS account admin role",
        environment_rule="local/staging seeded tenant and reviewed draft only",
        seeded_subjects=[
            "base_url",
            "admin_token",
            "draft_ref",
            "internal_tenant_code",
            "idempotency_key",
        ],
        expected_state_change=(
            "creates platform account foundation, tenant link, external references, "
            "and account audit event"
        ),
        curl_template=(
            'curl -sS -X POST -H "Authorization: Bearer {admin_token}" '
            '-H "Content-Type: application/json" '
            '-d \'{"draft_ref":"{draft_ref}",'
            '"internal_tenant_code":"{internal_tenant_code}",'
            '"idempotency_key":"{idempotency_key}"}\' '
            '"{base_url}/v1/referral-saas/accounts/from-draft"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_account_profile_update",
        method="PATCH",
        path="/v1/referral-saas/accounts/{account_ref}/profile",
        smoke_class="seeded_write",
        auth_hint="Referral SaaS account admin role",
        environment_rule="local/staging seeded account only; profile fields only",
        seeded_subjects=[
            "base_url",
            "admin_token",
            "account_ref",
            "account_name",
            "operating_jurisdiction_code",
            "idempotency_key",
        ],
        expected_state_change=(
            "updates durable profile fields and records account audit evidence; "
            "does not rotate external references, activate accounts, write "
            "memberships, create credentials, publish campaigns, or move money"
        ),
        curl_template=(
            'curl -sS -X PATCH -H "Authorization: Bearer {admin_token}" '
            '-H "Content-Type: application/json" '
            '-d \'{"profile":{"accountName":"{account_name}",'
            '"accountType":"ORGANISATION",'
            '"operatingJurisdictionCode":"{operating_jurisdiction_code}",'
            '"customerType":"DIRECT_CUSTOMER",'
            '"industry":"BANKING_FINANCIAL_SERVICES"},'
            '"correlationId":"smoke-profile-update",'
            '"idempotencyKey":"{idempotency_key}"}\' '
            '"{base_url}/v1/referral-saas/accounts/{account_ref}/profile"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_membership_invitation_intent",
        method="POST",
        path="/v1/referral-saas/accounts/{account_ref}/membership-invitations",
        smoke_class="seeded_write",
        auth_hint="Referral SaaS account admin role",
        environment_rule="local/staging seeded account only; no invite delivery",
        seeded_subjects=[
            "base_url",
            "admin_token",
            "account_ref",
            "ref_type",
            "external_ref",
            "subject",
            "idempotency_key",
        ],
        expected_state_change=(
            "records platform user and invited membership intent plus account "
            "audit event; does not send invitations, activate membership, assign "
            "seats, mutate auth claims, or move money"
        ),
        curl_template=(
            'curl -sS -X POST -H "Authorization: Bearer {admin_token}" '
            '-H "Content-Type: application/json" '
            '-d \'{"accountScope":{"refType":"{ref_type}",'
            '"externalRef":"{external_ref}","context":"setup"},'
            '"actor":{"actorType":"USER","subject":"{subject}"},'
            '"membership":{"roleFamily":"DISTRIBUTION_ADMIN",'
            '"permissionSet":"REFERRAL_SAAS_ACCOUNT_ADMIN",'
            '"tenantScope":"PRIMARY_ACCOUNT_TENANT"},'
            '"reasonCode":"ACCOUNT_SETUP_USER_ROLE",'
            '"correlationId":"smoke-membership-invite",'
            '"idempotencyKey":"{idempotency_key}"}\' '
            '"{base_url}/v1/referral-saas/accounts/{account_ref}'
            '/membership-invitations"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_membership_invitation_delivery_request",
        method="POST",
        path="/v1/referral-saas/accounts/{account_ref}/membership-invitations/{membership_ref}/delivery",
        smoke_class="seeded_write",
        auth_hint="Referral SaaS account admin role",
        environment_rule="local/staging seeded account only; records blocked delivery request when provider is absent",
        seeded_subjects=[
            "base_url",
            "admin_token",
            "account_ref",
            "membership_ref",
            "ref_type",
            "external_ref",
            "provider_ref",
            "recipient_hash",
            "idempotency_key",
        ],
        expected_state_change=(
            "records account audit evidence for an invitation delivery request "
            "boundary; does not send email, activate membership, assign seats, "
            "mutate auth claims, create credentials, or move money"
        ),
        curl_template=(
            'curl -sS -X POST -H "Authorization: Bearer {admin_token}" '
            '-H "Content-Type: application/json" '
            '-d \'{"accountScope":{"refType":"{ref_type}",'
            '"externalRef":"{external_ref}","context":"setup"},'
            '"delivery":{"providerRef":"{provider_ref}",'
            '"channel":"EMAIL",'
            '"templateRef":"referral-saas-account-invite-v1",'
            '"recipientHash":"{recipient_hash}"},'
            '"reasonCode":"CUSTOMER_PROFILE_INVITE_DELIVERY_REQUEST",'
            '"correlationId":"smoke-membership-delivery",'
            '"idempotencyKey":"{idempotency_key}"}\' '
            '"{base_url}/v1/referral-saas/accounts/{account_ref}'
            '/membership-invitations/{membership_ref}/delivery"'
        ),
    ),
    SmokeRoute(
        name="public_referral_validate",
        method="POST",
        path="/public/referrals/validate",
        smoke_class="seeded_write",
        auth_hint="public validation request",
        environment_rule="local/staging seeded tenant only",
        seeded_subjects=["base_url", "tenant_code", "referral_code"],
        expected_state_change="may create referral_instances and QR evidence",
        curl_template=(
            'curl -sS -X POST -H "Content-Type: application/json" '
            '-d \'{"tenant_code":"{tenant_code}","referral_code":"{referral_code}",'
            '"accepted_terms":true}\' "{base_url}/public/referrals/validate"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_public_referral_validate",
        method="POST",
        path="/v1/referral-saas/public/referrals/validate",
        smoke_class="seeded_write",
        auth_hint="Referral SaaS public validation request",
        environment_rule="local/staging seeded tenant only",
        seeded_subjects=["base_url", "tenant_code", "referral_code"],
        expected_state_change="may create referral_instances and QR evidence through product wrapper",
        curl_template=(
            'curl -sS -X POST -H "Content-Type: application/json" '
            '-d \'{"tenantCode":"{tenant_code}","referralCode":"{referral_code}",'
            '"acceptedTerms":true}\' '
            '"{base_url}/v1/referral-saas/public/referrals/validate"'
        ),
    ),
    SmokeRoute(
        name="referral_saas_referee_ucn_capture",
        method="POST",
        path="/v1/referral-saas/referrals/{referral_track_id}/referee-ucn",
        smoke_class="seeded_write",
        auth_hint="Referral SaaS partner/integration key",
        environment_rule="local/staging seeded tenant only",
        seeded_subjects=[
            "base_url",
            "partner_token",
            "referral_track_id",
            "referee_ucn",
        ],
        expected_state_change="may update referral_instances and enqueue UCN_CAPTURED progress event through product wrapper",
        curl_template=(
            'curl -sS -X POST -H "Authorization: Bearer {partner_token}" '
            '-H "Content-Type: application/json" '
            '-d \'{"refereeUcn":"{referee_ucn}"}\' '
            '"{base_url}/v1/referral-saas/referrals/{referral_track_id}/referee-ucn"'
        ),
    ),
    SmokeRoute(
        name="progress_ingest",
        method="POST",
        path="/v1/progress",
        smoke_class="seeded_write",
        auth_hint="partner/integration key",
        environment_rule="local/staging seeded tenant only",
        seeded_subjects=[
            "base_url",
            "partner_token",
            "tenant_code",
            "referral_track_id",
            "source_event_id",
        ],
        expected_state_change="may insert or dedupe referral_progress_events row",
        curl_template=(
            'curl -sS -X POST -H "Authorization: Bearer {partner_token}" '
            '-H "Content-Type: application/json" '
            '-d \'{"referralTrackId":"{referral_track_id}",'
            '"product":"Transactional","subProduct":"DDA13",'
            '"eventType":"ACCOUNT_OPENED","sourceSystem":"SMOKE_TEST",'
            '"sourceEventId":"{source_event_id}","refereeUCN":"{referee_ucn}",'
            '"accountNumber":"{account_number}"}\' "{base_url}/v1/progress"'
        ),
    ),
]


def build_plan(include_seeded_writes: bool = False) -> dict:
    routes = list(READ_ONLY_ROUTES)
    if include_seeded_writes:
        routes.extend(SEEDED_WRITE_ROUTES)

    return {
        "mode": "dry_run",
        "safety": {
            "default": "read-only routes only",
            "seededWrites": (
                "local/staging only; never production without separate approval"
            ),
            "productionRule": "production smoke must stay read-only",
        },
        "routes": [asdict(route) for route in routes],
        "omittedSeededWriteRoutes": [] if include_seeded_writes else [
            route.name for route in SEEDED_WRITE_ROUTES
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Referral SaaS route smoke plan templates."
    )
    parser.add_argument(
        "--include-seeded-writes",
        action="store_true",
        help="Include local/staging-only write route templates in the plan.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(
        json.dumps(
            build_plan(include_seeded_writes=args.include_seeded_writes),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
