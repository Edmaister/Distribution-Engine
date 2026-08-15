from __future__ import annotations

from types import SimpleNamespace

import pytest
from httpx import AsyncClient

from apps.api.main import app
from apps.api.routers import referral_saas_accounts
from services.referral_saas_account_foundation_service import (
    AccountFoundationContext,
    AccountFoundationActivationResult,
    AccountFoundationListItem,
    AccountNotResolvable,
    AccountProfileMaintenanceResult,
    AccountProfileNotFound,
    ExternalReferenceConflict,
    ExternalReferenceNotActive,
    ExternalReferenceNotFound,
    InvalidExternalReferenceType,
    PartnerWorkspaceAccountContext,
    PartnerWorkspaceAccountContextItem,
    TenantLinkNotResolvable,
)
from services.referral_saas_account_membership_service import (
    AccessProvisioningRequestResult,
    IdentityLoginReconciliation,
    IdentityLoginReconciliationPerson,
    LoginCompletionIntentResult,
    LoginCompletionReadiness,
    MembershipAcceptanceTokenAcceptResult,
    MembershipAcceptanceTokenIssueResult,
    MembershipAcceptanceTokenValidationResult,
    MembershipActivationRequestResult,
    MembershipInvitationDeliveryRequestResult,
    MembershipInvitationDuplicate,
    MembershipInvitationIntentResult,
    MembershipInvitationLifecycleResult,
)
from services.referral_saas_account_setup_service import (
    AccountSetupDraftNotFound,
    AccountSetupDuplicateInternalTenantScope,
    AccountSetupDuplicateReference,
    AccountSetupInvalidDraftState,
    DurableAccountSetupResult,
)
from services.referral_saas_campaign_service import (
    ReferralSaasCampaignAttributionProjection,
    ReferralSaasCampaignAttributionSummary,
    ReferralSaasCampaignActivationResult,
    ReferralSaasCampaignPolicySettingsResult,
    ReferralSaasCampaignReviewResult,
    ReferralSaasCampaignSetupResult,
    ReferralSaasCampaignSummary,
)
from services.referral_saas_referral_attribution_service import (
    ReferralSaasReferralAttributionSummary,
    ReferralSaasReferralCreditProjection,
    ReferralSaasReferrerCreditProjection,
)
from services.referral_saas_integrations_configuration_service import (
    IntegrationConfigurationIdempotencyConflict,
    IntegrationCredentialRequestNotFound,
)
from services.referral_saas_support_case_service import (
    SupportCaseIdempotencyConflict,
)

pytestmark = pytest.mark.asyncio

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}
PARTNER_HEADERS = {"x-api-key": "test-partner-key"}


class _FakeIntegrationClientBinding:
    binding_status = "CLIENT_BINDING_READY"
    blockers: list[dict] = []

    @property
    def is_ready(self):
        return True

    def to_safe_dict(self):
        return {
            "bindingStatus": "CLIENT_BINDING_READY",
            "accountRef": "acct-1",
            "clientRefPresent": True,
            "activeClientCount": 1,
            "boundRoleFamilies": ["DISTRIBUTION_ADMIN"],
            "providerRefsCount": 1,
            "environment": "SANDBOX",
            "blockers": [],
            "guardrails": ["ACCOUNT_INTEGRATION_CLIENT_BINDING_REQUIRED"],
            "redactions": ["client_id", "client_secret_hash", "tenant_code"],
        }


@pytest.fixture(autouse=True)
def _default_integration_client_binding(monkeypatch):
    async def fake_get_referral_saas_integration_client_binding(**kwargs):
        return _FakeIntegrationClientBinding()

    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_client_binding",
        fake_get_referral_saas_integration_client_binding,
    )


def _context(**overrides) -> AccountFoundationContext:
    values = {
        "account_id": "acct-1",
        "account_code": "ACCT_FNB",
        "account_name": "FNB Referral SaaS",
        "account_type": "ORGANISATION",
        "account_status": "ACTIVE",
        "onboarding_status": "APPROVED",
        "operating_jurisdiction_code": "ZA",
        "external_ref_id": "ref-1",
        "ref_type": "external_tenant_ref",
        "external_ref": "fnb-referrals",
        "reference_status": "ACTIVE",
        "tenant_code": "FNB",
        "account_tenant_id": "acct-tenant-1",
        "relationship_type": "OWNER",
        "tenant_link_status": "ACTIVE",
        "is_primary": True,
    }
    values.update(overrides)
    return AccountFoundationContext(**values)


def _setup_result(**overrides) -> DurableAccountSetupResult:
    values = {
        "account_id": "acct-1",
        "account_code": "ACCT_FNB",
        "account_name": "FNB Referral SaaS",
        "account_status": "PENDING_ONBOARDING",
        "onboarding_status": "READY_FOR_REVIEW",
        "account_tenant_id": "acct-tenant-1",
        "tenant_link_status": "PENDING_SETUP",
        "external_ref_id": "external-ref-1",
        "organisation_ref_id": "organisation-ref-1",
        "draft_ref": "draft_001",
        "audit_event_id": "audit-1",
        "guardrails": ["DURABLE_ACCOUNT_FOUNDATION_ONLY"],
    }
    values.update(overrides)
    return DurableAccountSetupResult(**values)


def _invitation_result(**overrides) -> MembershipInvitationIntentResult:
    values = {
        "command_status": "INVITATION_INTENT_RECORDED",
        "account_id": "acct-1",
        "membership_id": "membership-1",
        "membership_status": "INVITED",
        "role_family": "DISTRIBUTION_ADMIN",
        "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
        "can_operate_setup": False,
        "delivery_status": "DELIVERY_NOT_CONFIGURED",
        "delivery_next_action": "Configure approved invitation delivery provider",
        "idempotency_status": "RECORDED",
        "audit_event_id": "audit-1",
    }
    values.update(overrides)
    return MembershipInvitationIntentResult(**values)


def _invitation_lifecycle_result(**overrides) -> MembershipInvitationLifecycleResult:
    values = {
        "command_status": "INVITATION_INTENT_UPDATED",
        "account_id": "acct-1",
        "membership_id": "membership-1",
        "previous_membership_status": "INVITED",
        "membership_status": "INVITED",
        "role_family": "CAMPAIGN_MANAGER",
        "permission_set": "REFERRAL_SAAS_CAMPAIGN_MANAGER",
        "idempotency_status": "RECORDED",
        "audit_event_id": "audit-1",
        "lifecycle_next_action": "Review the updated access intent before invite delivery or activation.",
    }
    values.update(overrides)
    return MembershipInvitationLifecycleResult(**values)


def _delivery_request_result(**overrides) -> MembershipInvitationDeliveryRequestResult:
    values = {
        "command_status": "DELIVERY_PROVIDER_NOT_CONFIGURED",
        "account_id": "acct-1",
        "membership_id": "membership-1",
        "membership_status": "INVITED",
        "role_family": "DISTRIBUTION_ADMIN",
        "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
        "delivery_status": "DELIVERY_PROVIDER_NOT_CONFIGURED",
        "delivery_next_action": "Configure approved invitation delivery provider before sending email invites.",
        "recipient_contact_status": "CONTACT_REFERENCE_PRESENT",
        "provider_ref": "mail-provider-1",
        "channel": "EMAIL",
        "template_ref": "referral-saas-account-invite-v1",
        "idempotency_status": "RECORDED",
        "audit_event_id": "audit-delivery-1",
    }
    values.update(overrides)
    return MembershipInvitationDeliveryRequestResult(**values)


def _acceptance_token_issue_result(**overrides) -> MembershipAcceptanceTokenIssueResult:
    values = {
        "command_status": "ACCEPTANCE_TOKEN_ISSUED",
        "account_id": "acct-1",
        "membership_id": "membership-1",
        "role_family": "DISTRIBUTION_ADMIN",
        "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
        "acceptance_token": "accept-token-123456",
        "token_hint": "123456",
        "expires_at": "2026-08-13T10:00:00+00:00",
        "idempotency_status": "RECORDED",
        "audit_event_id": "audit-acceptance-token-1",
    }
    values.update(overrides)
    return MembershipAcceptanceTokenIssueResult(**values)


def _acceptance_token_validation_result(
    **overrides,
) -> MembershipAcceptanceTokenValidationResult:
    values = {
        "token_status": "ISSUED",
        "account_id": "acct-1",
        "membership_id": "membership-1",
        "role_family": "DISTRIBUTION_ADMIN",
        "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
        "account_name": "FNB Referral SaaS",
        "display_name": "FNB Owner",
        "expires_at": "2026-08-13T10:00:00+00:00",
        "next_action": "Review and accept access before the link expires.",
    }
    values.update(overrides)
    return MembershipAcceptanceTokenValidationResult(**values)


def _acceptance_token_accept_result(
    **overrides,
) -> MembershipAcceptanceTokenAcceptResult:
    values = {
        "command_status": "MEMBERSHIP_ACTIVATED",
        "token_status": "ACCEPTED",
        "account_id": "acct-1",
        "membership_id": "membership-1",
        "role_family": "DISTRIBUTION_ADMIN",
        "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
        "activation_status": "MEMBERSHIP_ACTIVATED",
        "idempotency_status": "RECORDED",
        "audit_event_id": "audit-activation-1",
    }
    values.update(overrides)
    return MembershipAcceptanceTokenAcceptResult(**values)


def _activation_request_result(**overrides) -> MembershipActivationRequestResult:
    values = {
        "command_status": "ACTIVATION_REJECTED_IDENTITY_NOT_ACCEPTED",
        "account_id": "acct-1",
        "membership_id": "membership-1",
        "previous_membership_status": "INVITED",
        "membership_status": "INVITED",
        "role_family": "DISTRIBUTION_ADMIN",
        "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
        "accepted_subject_status": "ACCEPTED_SUBJECT_MISSING_OR_MISMATCHED",
        "activation_next_action": (
            "Wait for identity acceptance evidence that matches the invited person."
        ),
        "idempotency_status": "RECORDED",
        "audit_event_id": "audit-activation-1",
    }
    values.update(overrides)
    return MembershipActivationRequestResult(**values)


def _access_provisioning_result(**overrides) -> AccessProvisioningRequestResult:
    values = {
        "command_status": "PROVISIONING_REQUEST_RECORDED",
        "account_id": "acct-1",
        "membership_id": "membership-1",
        "role_family": "DISTRIBUTION_ADMIN",
        "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
        "seat_type": "ADMIN",
        "seat_assignment_status": "SEAT_ASSIGNED",
        "seat_ref": "seat-1",
        "auth_claim_status": "AUTH_CLAIMS_NOT_PROPAGATED",
        "provisioning_next_action": (
            "Seat assignment is recorded. Configure login permissions and auth "
            "claims only through the separate identity-provider workflow."
        ),
        "idempotency_status": "RECORDED",
        "audit_event_id": "audit-provisioning-1",
    }
    values.update(overrides)
    return AccessProvisioningRequestResult(**values)


def _login_completion_readiness(**overrides) -> LoginCompletionReadiness:
    values = {
        "login_completion_status": "LOGIN_COMPLETION_READY",
        "account_id": "acct-1",
        "membership_id": "membership-1",
        "subject": "owner@example.test",
        "display_name": "FNB Owner",
        "role_family": "DISTRIBUTION_ADMIN",
        "permission_profile": "REFERRAL_SAAS_ACCOUNT_ADMIN",
        "membership_status": "ACTIVE",
        "seat_assignment_status": "SEAT_ASSIGNED",
        "identity_provider_status": "NOT_RECORDED",
        "auth_claim_status": "AUTH_CLAIMS_NOT_PROPAGATED",
        "blockers": (),
        "next_actions": ("Record login completion intent.",),
    }
    values.update(overrides)
    return LoginCompletionReadiness(**values)


def _login_completion_result(**overrides) -> LoginCompletionIntentResult:
    values = {
        "command_status": "LOGIN_COMPLETION_RECORDED",
        "account_id": "acct-1",
        "membership_id": "membership-1",
        "role_family": "DISTRIBUTION_ADMIN",
        "permission_profile": "REFERRAL_SAAS_ACCOUNT_ADMIN",
        "intent": "PLATFORM_LOGIN_REQUIRED",
        "seat_assignment_status": "SEAT_ASSIGNED",
        "identity_provider_status": "APPROVED_EVIDENCE_RECORDED",
        "auth_claim_status": "AUTH_CLAIMS_NOT_PROPAGATED",
        "login_next_action": (
            "Login completion evidence is recorded. Real credentials and auth "
            "claims remain in the governed identity-provider workflow."
        ),
        "idempotency_status": "RECORDED",
        "audit_event_id": "audit-login-1",
    }
    values.update(overrides)
    return LoginCompletionIntentResult(**values)


def _identity_login_reconciliation(**overrides) -> IdentityLoginReconciliation:
    person = IdentityLoginReconciliationPerson(
        membership_id="membership-1",
        subject="owner@example.test",
        display_name="FNB Owner",
        role_family="DISTRIBUTION_ADMIN",
        permission_profile="REFERRAL_SAAS_ACCOUNT_ADMIN",
        access_status="CUSTOMER_ACCESS_ACCEPTED",
        login_status="WAITING_FOR_IDENTITY_PROVIDER_EVIDENCE",
        seat_assignment_status="SEAT_ASSIGNED",
        identity_provider_status="NOT_RECORDED",
        auth_claim_status="AUTH_CLAIMS_NOT_PROPAGATED",
        revocation_status="NOT_REVOKED",
        blockers=(),
        warnings=(),
        next_action=(
            "Record approved identity provider evidence in Integrations before "
            "login permissions are trusted."
        ),
        steps=(
            {
                "label": "Customer access",
                "status": "DONE",
                "description": "Person is confirmed for this customer.",
            },
            {
                "label": "Platform login seat",
                "status": "DONE",
                "description": "Needed only when this person signs in to Amplifi.",
            },
            {
                "label": "Identity provider",
                "status": "WAITING",
                "description": "Evidence comes from the governed identity workflow.",
            },
        ),
    )
    values = {
        "account_id": "acct-1",
        "reconciliation_status": "LOGIN_RECONCILIATION_ACTION_REQUIRED",
        "people": (person,),
        "accepted_count": 1,
        "named_count": 1,
        "seat_assigned_count": 1,
        "provider_evidence_count": 0,
        "auth_claim_ready_count": 0,
        "revoked_count": 0,
        "action_required_count": 1,
        "claim_mismatch_count": 0,
        "stale_provider_evidence_count": 0,
    }
    values.update(overrides)
    return IdentityLoginReconciliation(**values)


def _account_activation_result(**overrides) -> AccountFoundationActivationResult:
    values = {
        "account_id": "acct-1",
        "account_code": "ACCT_FNB",
        "account_name": "FNB Referral SaaS",
        "previous_account_status": "PENDING_ONBOARDING",
        "account_status": "ACTIVE",
        "previous_onboarding_status": "READY_FOR_REVIEW",
        "onboarding_status": "APPROVED",
        "previous_tenant_link_status": "PENDING_SETUP",
        "tenant_link_status": "ACTIVE",
        "activated_seat_types": ("ADMIN", "OPERATOR"),
        "created_seat_count": 2,
        "command_status": "ACCOUNT_FOUNDATION_ACTIVATED",
        "audit_event_id": "audit-account-activation-1",
        "idempotency_status": "RECORDED",
        "guardrails": ["ACCOUNT_FOUNDATION_ONLY", "NO_MEMBERSHIP_WRITE"],
        "redactions": ["internal_tenant_identifier"],
    }
    values.update(overrides)
    return AccountFoundationActivationResult(**values)


def _profile_result(**overrides) -> AccountProfileMaintenanceResult:
    values = {
        "account_id": "acct-1",
        "account_code": "ACCT_FNB",
        "account_name": "FNB Referral SaaS Updated",
        "account_type": "ORGANISATION",
        "account_status": "PENDING_ONBOARDING",
        "onboarding_status": "READY_FOR_REVIEW",
        "operating_jurisdiction_code": "ZA",
        "customer_type": "ENTERPRISE_CUSTOMER",
        "industry": "AUTOMOTIVE",
        "audit_event_id": "audit-1",
        "guardrails": ["DURABLE_PROFILE_FIELDS_ONLY", "NO_EXTERNAL_REFERENCE_ROTATION"],
        "redactions": ["internal_tenant_identifier"],
    }
    values.update(overrides)
    return AccountProfileMaintenanceResult(**values)


def _campaign_summary(**overrides) -> ReferralSaasCampaignSummary:
    values = {
        "campaign_code": "CAMP001",
        "name": "Summer Referrals",
        "segment": "REFERRAL",
        "status": "ACTIVE",
        "lifecycle": "ACTIVE",
        "starts_at": "2026-07-01T00:00:00+00:00",
        "ends_at": None,
        "max_uses": 100,
        "uses_count": 7,
        "policy_status": "ACTIVE_POLICY",
        "created_at": "2026-07-01T00:00:00+00:00",
        "updated_at": "2026-07-02T00:00:00+00:00",
    }
    values.update(overrides)
    return ReferralSaasCampaignSummary(**values)


def _campaign_attribution_summary(**overrides) -> ReferralSaasCampaignAttributionSummary:
    values = {
        "status": "READY",
        "campaign_count": 1,
        "source_count": 1,
        "total_interactions": 4,
        "high_confidence_count": 1,
        "missing_evidence_count": 0,
        "conflict_count": 0,
        "plain_language": "4 campaign interaction(s) found. 1 source(s) have high-confidence attribution evidence.",
        "projections": [
            ReferralSaasCampaignAttributionProjection(
                campaign_code="CAMP001",
                campaign_name="Summer Referrals",
                segment="REFERRAL",
                campaign_status="ACTIVE",
                source_channel="EMAIL",
                attribution_status="ATTRIBUTED",
                confidence="HIGH",
                interaction_count=4,
                linked_referral_count=3,
                event_count=5,
                first_seen_at="2026-07-01T00:00:00+00:00",
                last_seen_at="2026-07-02T00:00:00+00:00",
                evidence=["3 linked referral record(s)."],
                gaps=[],
                explanation="Summer Referrals has campaign attribution evidence from EMAIL and 3 linked referral record(s).",
            )
        ],
    }
    values.update(overrides)
    return ReferralSaasCampaignAttributionSummary(**values)


def _referral_attribution_summary(**overrides) -> ReferralSaasReferralAttributionSummary:
    values = {
        "status": "READY",
        "referral_count": 1,
        "referrer_count": 1,
        "credited_referral_count": 1,
        "high_confidence_count": 1,
        "missing_evidence_count": 0,
        "plain_language": "1 of 1 referral record(s) can be explained across 1 safe referrer dimension(s). 0 referral record(s) still need evidence before credit can be explained safely.",
        "referral_projections": [
            ReferralSaasReferralCreditProjection(
                referral_track_id="track-1",
                referral_code="REF-001",
                public_referrer_handle="safe-handle",
                campaign_code="CAMP001",
                credit_status="CREDITED",
                confidence="HIGH",
                progress_event_count=2,
                accepted_terms_confirmed=True,
                attribution_evidence_present=True,
                evidence=["Referral code is present."],
                gaps=[],
                explanation="safe-handle has high confidence credit evidence for CAMP001.",
            )
        ],
        "referrer_projections": [
            ReferralSaasReferrerCreditProjection(
                safe_referrer_key="REFERRER_SAFE",
                display_label="safe-handle",
                masked_referrer_identifier="referrer-...SAFE",
                credit_status="CREDITED",
                confidence="HIGH",
                referral_count=1,
                attributed_referral_count=1,
                completed_referral_count=0,
                campaign_count=1,
                evidence=["1 referral record(s)."],
                gaps=[],
                explanation="safe-handle can be explained as a credited referrer across 1 attributed referral record(s).",
            )
        ],
        "guardrails": ["CUSTOMER_SCOPED_REFERRAL_ATTRIBUTION_ONLY"],
        "redactions": ["internal_tenant_identifier", "raw_referrer_ucn"],
    }
    values.update(overrides)
    return ReferralSaasReferralAttributionSummary(**values)


def _campaign_setup_result(**overrides) -> ReferralSaasCampaignSetupResult:
    values = {
        "command_status": "CAMPAIGN_SETUP_DRAFT_RECORDED",
        "account_id": "acct-1",
        "campaign_code": "FNB-RETAIL-SUMMER-1234",
        "name": "Summer Referral",
        "segment": "Retail",
        "setup_status": "DRAFT",
        "is_active": False,
        "starts_at": "2026-08-01T00:00:00+00:00",
        "ends_at": None,
        "max_uses": 100,
        "idempotency_status": "RECORDED",
        "audit_event_id": "audit-1",
    }
    values.update(overrides)
    return ReferralSaasCampaignSetupResult(**values)


def _campaign_policy_settings_result(
    **overrides,
) -> ReferralSaasCampaignPolicySettingsResult:
    values = {
        "command_status": "POLICY_SETTINGS_RECORDED",
        "account_id": "acct-1",
        "campaign_code": "CAMP001",
        "version": 1,
        "setup_status": "POLICY_SETTINGS_RECORDED",
        "attribution_window_days": 30,
        "eligibility_rule_count": 1,
        "product_window_count": 1,
        "product_rule_count": 1,
        "reward_visibility_status": "CONFIGURED_WITHOUT_PAYMENT",
        "idempotency_status": "RECORDED",
        "audit_event_id": "audit-policy-1",
    }
    values.update(overrides)
    return ReferralSaasCampaignPolicySettingsResult(**values)


def _campaign_review_result(**overrides) -> ReferralSaasCampaignReviewResult:
    values = {
        "command_status": "CAMPAIGN_REVIEW_SUBMITTED",
        "account_id": "acct-1",
        "campaign_code": "CAMP001",
        "review_status": "READY_FOR_REVIEW",
        "setup_status": "POLICY_SETTINGS_RECORDED",
        "readiness_status": "NEEDS_REVIEW",
        "activation_eligibility": "NOT_ELIGIBLE_UNTIL_REVIEW_APPROVED",
        "activation_status": "NOT_ACTIVATED",
        "reviewer_action": "Record approval or block decision",
        "idempotency_status": "RECORDED",
        "audit_event_id": "audit-review-1",
    }
    values.update(overrides)
    return ReferralSaasCampaignReviewResult(**values)


def _campaign_activation_result(**overrides) -> ReferralSaasCampaignActivationResult:
    values = {
        "command_status": "CAMPAIGN_ACTIVATION_ACCEPTED",
        "account_id": "acct-1",
        "campaign_code": "CAMP001",
        "previous_lifecycle": "READY_TO_ACTIVATE",
        "lifecycle": "ACTIVE",
        "review_status": "REVIEW_APPROVED",
        "activation_eligibility": "ELIGIBLE_FOR_FUTURE_ACTIVATION",
        "activation_status": "ACTIVATION_REQUEST_ACCEPTED",
        "readiness_status": "READY_TO_ACTIVATE",
        "idempotency_status": "RECORDED",
        "audit_event_id": "audit-activation-1",
    }
    values.update(overrides)
    return ReferralSaasCampaignActivationResult(**values)


def _campaign_scoped_identity_with_capabilities(*capabilities: str) -> dict:
    return {
        "role": "DISTRIBUTION_ADMIN",
        "account_ref": "acct-1",
        "allowed_jurisdictions": ["ZA"],
        "scopes": list(capabilities),
    }


def _assert_campaign_capability_forbidden(response) -> None:
    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["code"] == "account_boundary_forbidden"
    assert "SERVER_SIDE_ACCOUNT_CAPABILITY_ENFORCEMENT" in detail["guardrails"]
    assert detail["no_capability_bypass_confirmed"] is True
    assert "tenantCode" not in str(detail)
    assert "FNB" not in str(detail)


async def test_referral_saas_account_admin_can_create_account_from_draft(monkeypatch):
    calls: list[dict] = []

    async def fake_create_durable_account_from_onboarding_draft(**kwargs):
        calls.append(kwargs)
        return _setup_result()

    monkeypatch.setattr(
        referral_saas_accounts,
        "create_durable_account_from_onboarding_draft",
        fake_create_durable_account_from_onboarding_draft,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/from-draft",
            json={
                "draft_ref": "draft_001",
                "internal_tenant_code": "FNB",
                "idempotency_key": "account-create-1",
                "correlation_id": "corr-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "created"
    assert body["account"]["accountCode"] == "ACCT_FNB"
    assert body["account"]["draftRef"] == "draft_001"
    assert "tenantCode" not in body["account"]
    assert body["redactions"] == ["internal_tenant_identifier"]
    assert body["no_adjacent_live_action_confirmed"] is True
    assert calls[0]["draft_ref"] == "draft_001"
    assert calls[0]["tenant_code"] == "FNB"
    assert calls[0]["actor_role"] == "ADMIN"
    assert calls[0]["correlation_id"] == "corr-1"
    assert calls[0]["idempotency_key_hash"]


async def test_referral_saas_account_create_rejects_missing_required_fields():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/from-draft",
            json={"draft_ref": "draft_001"},
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "validation_error"
    assert "BOUNDED_INTERNAL_TENANT_SEED" in detail["guardrails"]
    assert detail["redactions"] == ["internal_tenant_identifier"]


async def test_referral_saas_account_create_rejects_adjacent_role():
    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/from-draft",
            json={
                "draft_ref": "draft_001",
                "internal_tenant_code": "FNB",
                "idempotency_key": "account-create-1",
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "permission_denied"


@pytest.mark.parametrize(
    ("error", "status_code", "safe_code"),
    [
        (
            AccountSetupDraftNotFound("Draft missing."),
            404,
            "DRAFT_NOT_FOUND",
        ),
        (
            AccountSetupInvalidDraftState("Draft not ready."),
            409,
            "INVALID_DRAFT_STATE",
        ),
        (
            AccountSetupDuplicateReference("Duplicate reference."),
            409,
            "DUPLICATE_EXTERNAL_REFERENCE",
        ),
        (
            AccountSetupDuplicateInternalTenantScope("Internal tenant scope is already attached to an account owner."),
            409,
            "DUPLICATE_INTERNAL_TENANT_SCOPE",
        ),
    ],
)
async def test_referral_saas_account_create_maps_safe_command_errors(
    monkeypatch,
    error,
    status_code,
    safe_code,
):
    async def fake_create_durable_account_from_onboarding_draft(**kwargs):
        raise error

    monkeypatch.setattr(
        referral_saas_accounts,
        "create_durable_account_from_onboarding_draft",
        fake_create_durable_account_from_onboarding_draft,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/from-draft",
            json={
                "draft_ref": "draft_001",
                "internal_tenant_code": "FNB",
                "idempotency_key": "account-create-1",
            },
        )

    assert response.status_code == status_code
    detail = response.json()["detail"]
    assert detail["code"] == safe_code
    assert detail["redactions"] == ["internal_tenant_identifier"]
    assert detail["no_adjacent_live_action_confirmed"] is True


async def test_referral_saas_account_reader_can_resolve_runtime_account(monkeypatch):
    calls: list[dict] = []

    async def fake_resolve_account_by_external_reference(**kwargs):
        calls.append(kwargs)
        return _context()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_account_by_external_reference",
        fake_resolve_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/resolve",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["context"] == "runtime"
    assert body["account"]["accountCode"] == "ACCT_FNB"
    assert body["account"]["externalRef"] == "fnb-referrals"
    assert "tenantCode" not in body["account"]
    assert body["guardrail"].startswith("Read-only Referral SaaS account resolver")
    assert calls == [
        {
            "ref_type": "external_tenant_ref",
            "external_ref": "fnb-referrals",
        }
    ]


async def test_referral_saas_account_reader_can_list_safe_account_registry(monkeypatch):
    calls: list[dict] = []

    async def fake_list_referral_saas_accounts(**kwargs):
        calls.append(kwargs)
        return [
            AccountFoundationListItem(
                account_id="acct-1",
                account_code="ACCT_FNB",
                account_name="FNB Referral SaaS",
                account_type="ORGANISATION",
                account_status="PENDING_ONBOARDING",
                onboarding_status="READY_FOR_REVIEW",
                operating_jurisdiction_code="ZA",
                primary_external_tenant_ref="fnb-referrals",
                external_references=(
                    {
                        "refType": "external_tenant_ref",
                        "externalRef": "fnb-referrals",
                        "referenceStatus": "ACTIVE",
                    },
                    {
                        "refType": "organisation_ref",
                        "externalRef": "fnb-org",
                        "referenceStatus": "ACTIVE",
                    },
                ),
                created_at="2026-07-19T00:00:00",
                updated_at="2026-07-19T01:00:00",
            )
        ]

    monkeypatch.setattr(
        referral_saas_accounts,
        "list_referral_saas_accounts",
        fake_list_referral_saas_accounts,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get("/v1/referral-saas/accounts", params={"limit": 20})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["count"] == 1
    assert body["accounts"][0]["accountCode"] == "ACCT_FNB"
    assert body["accounts"][0]["operatingJurisdictionCode"] == "ZA"
    assert body["accounts"][0]["externalReferences"][0]["externalRef"] == "fnb-referrals"
    assert body["redactions"] == ["internal_tenant_identifier"]
    assert "tenantCode" not in str(body)
    assert calls == [{"limit": 20}]


async def test_referral_saas_admin_can_list_journey_template_catalogue(monkeypatch):
    calls: list[dict] = []

    async def fake_list_referral_saas_journey_templates(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            to_safe_dict=lambda: {
                "status": "READY",
                "templateCount": 1,
                "statusFilter": ["APPROVED", "DRAFT"],
                "templates": [
                    {
                        "templateCode": "REFERRAL_STANDARD",
                        "templateName": "Referral standard",
                        "templateFamily": "REFERRAL",
                        "status": "APPROVED",
                        "safeSummary": {"plainLanguageName": "Referral standard"},
                        "versionCount": 1,
                        "versions": [
                            {
                                "templateVersion": "1.0.0",
                                "status": "APPROVED",
                                "milestoneCount": 2,
                                "transitionRuleCount": 1,
                                "evidenceRequirementCount": 1,
                            }
                        ],
                    }
                ],
                "guardrails": ["READ_ONLY_TEMPLATE_CATALOGUE"],
                "redactions": ["definition_payload", "tenant_code"],
                "noTenantDataConfirmed": True,
                "noCustomerConfigurationWriteConfirmed": True,
                "noRuntimeExecutionConfirmed": True,
                "noCampaignBindingConfirmed": True,
                "noProviderAuthBillingOrMoneyActionConfirmed": True,
            }
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "list_referral_saas_journey_templates",
        fake_list_referral_saas_journey_templates,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/journey-templates",
            params={"status": ["APPROVED", "DRAFT"], "limit": 10},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["templateCount"] == 1
    assert body["templates"][0]["templateCode"] == "REFERRAL_STANDARD"
    assert body["noCustomerConfigurationWriteConfirmed"] is True
    assert body["noRuntimeExecutionConfirmed"] is True
    assert body["noProviderAuthBillingOrMoneyActionConfirmed"] is True
    assert "definitionPayload" not in str(body["templates"][0])
    assert calls == [
        {
            "statuses": ["APPROVED", "DRAFT"],
            "include_archived": False,
            "limit": 10,
        }
    ]


async def test_referral_saas_admin_can_get_journey_template_catalogue_detail(
    monkeypatch,
):
    calls: list[dict] = []

    async def fake_get_referral_saas_journey_template(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            to_safe_dict=lambda: {
                "templateCode": "REFERRAL_STANDARD",
                "templateName": "Referral standard",
                "templateFamily": "REFERRAL",
                "status": "APPROVED",
                "versions": [
                    {
                        "templateVersion": "1.0.0",
                        "milestoneCount": 2,
                    }
                ],
            }
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_journey_template",
        fake_get_referral_saas_journey_template,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/journey-templates/REFERRAL_STANDARD",
            params={"includeArchived": "true"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "READY"
    assert body["template"]["templateCode"] == "REFERRAL_STANDARD"
    assert body["noCampaignBindingConfirmed"] is True
    assert calls == [
        {
            "template_code": "REFERRAL_STANDARD",
            "statuses": None,
            "include_archived": True,
        }
    ]


async def test_referral_saas_journey_template_catalogue_rejects_bad_status(
    monkeypatch,
):
    async def fake_list_referral_saas_journey_templates(**kwargs):
        raise referral_saas_accounts.JourneyTemplateCatalogueValidationError(
            "Unsupported journey template status: LIVE"
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "list_referral_saas_journey_templates",
        fake_list_referral_saas_journey_templates,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/journey-templates",
            params={"status": "LIVE"},
        )

    assert response.status_code == 422
    body = response.json()["detail"]
    assert body["code"] == "journey_template_catalogue_validation_error"
    assert body["noCustomerConfigurationWriteConfirmed"] is True


async def test_referral_saas_journey_template_detail_returns_404_for_missing(
    monkeypatch,
):
    async def fake_get_referral_saas_journey_template(**kwargs):
        raise referral_saas_accounts.JourneyTemplateNotFound("UNKNOWN")

    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_journey_template",
        fake_get_referral_saas_journey_template,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get("/v1/referral-saas/journey-templates/UNKNOWN")

    assert response.status_code == 404
    body = response.json()["detail"]
    assert body["code"] == "journey_template_not_found"
    assert body["noTenantDataConfirmed"] is True


async def test_referral_saas_admin_can_list_customer_journey_drafts(monkeypatch):
    resolve_calls: list[dict] = []
    list_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    async def fake_list_referral_saas_customer_journey_drafts(**kwargs):
        list_calls.append(kwargs)
        return (
            SimpleNamespace(
                to_safe_dict=lambda: {
                    "customerJourneyDraftId": "draft-1",
                    "draftStatus": "DRAFT",
                    "templateCode": "REFERRAL_STANDARD",
                    "configurationPayload": {"milestones": []},
                    "noRuntimeJourneyMutationConfirmed": True,
                    "noCampaignActivationConfirmed": True,
                }
            ),
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "list_referral_saas_customer_journey_drafts",
        fake_list_referral_saas_customer_journey_drafts,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/journey-drafts",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
                "limit": 10,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["count"] == 1
    assert body["drafts"][0]["customerJourneyDraftId"] == "draft-1"
    assert body["noRuntimeJourneyMutationConfirmed"] is True
    assert body["noProviderDispatchConfirmed"] is True
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert list_calls == [
        {"account_id": "acct-1", "include_archived": False, "limit": 10}
    ]


async def test_referral_saas_admin_can_save_customer_journey_draft(monkeypatch):
    resolve_calls: list[dict] = []
    save_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    async def fake_save_referral_saas_customer_journey_draft(**kwargs):
        save_calls.append(kwargs)
        return SimpleNamespace(
            to_safe_dict=lambda: {
                "commandStatus": "DRAFT_SAVED",
                "idempotencyStatus": "NEW_REQUEST",
                "draft": {
                    "customerJourneyDraftId": "draft-1",
                    "draftStatus": "DRAFT",
                    "templateCode": "REFERRAL_STANDARD",
                },
                "noRuntimeJourneyMutationConfirmed": True,
                "noCampaignBindingConfirmed": True,
                "noAuthBillingOrMoneyActionConfirmed": True,
            }
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "save_referral_saas_customer_journey_draft",
        fake_save_referral_saas_customer_journey_draft,
    )

    payload = {
        "accountScope": {
            "refType": "external_tenant_ref",
            "externalRef": "fnb-referrals",
            "context": "setup",
        },
        "templateCode": "REFERRAL_STANDARD",
        "templateVersion": "1.0.0",
        "draftName": "FNB referral journey",
        "configurationPayload": {"milestones": [{"code": "REFERRED"}]},
        "idempotencyKey": "draft-save-1",
    }
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.put(
            "/v1/referral-saas/accounts/acct-1/journey-drafts",
            json=payload,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["commandStatus"] == "DRAFT_SAVED"
    assert body["draft"]["customerJourneyDraftId"] == "draft-1"
    assert body["noCampaignBindingConfirmed"] is True
    assert body["noAuthBillingOrMoneyActionConfirmed"] is True
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert save_calls[0]["account_id"] == "acct-1"
    assert save_calls[0]["template_code"] == "REFERRAL_STANDARD"
    assert save_calls[0]["configuration_payload"] == {
        "milestones": [{"code": "REFERRED"}]
    }
    assert save_calls[0]["idempotency_key_hash"]
    assert save_calls[0]["request_payload_hash"]


async def test_referral_saas_customer_journey_draft_save_rejects_conflict(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    async def fake_save_referral_saas_customer_journey_draft(**kwargs):
        raise referral_saas_accounts.CustomerJourneyDraftIdempotencyConflict(
            "Idempotency key was reused with different journey draft content."
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "save_referral_saas_customer_journey_draft",
        fake_save_referral_saas_customer_journey_draft,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.put(
            "/v1/referral-saas/accounts/acct-1/journey-drafts",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                },
                "templateCode": "REFERRAL_STANDARD",
                "draftName": "FNB referral journey",
                "configurationPayload": {},
                "idempotencyKey": "draft-save-1",
            },
        )

    assert response.status_code == 409
    body = response.json()["detail"]
    assert body["code"] == "IDEMPOTENCY_CONFLICT"
    assert "NO_CAMPAIGN_ACTIVATION" in body["guardrails"]


async def test_referral_saas_customer_journey_draft_save_rejects_unsafe_payload(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    async def fake_save_referral_saas_customer_journey_draft(**kwargs):
        raise referral_saas_accounts.CustomerJourneyDraftUnsafePayload(
            "Unsafe customer journey configuration field is not allowed."
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "save_referral_saas_customer_journey_draft",
        fake_save_referral_saas_customer_journey_draft,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.put(
            "/v1/referral-saas/accounts/acct-1/journey-drafts",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                },
                "templateCode": "REFERRAL_STANDARD",
                "draftName": "FNB referral journey",
                "configurationPayload": {"api_key": "secret"},
                "idempotencyKey": "draft-save-unsafe",
            },
        )

    assert response.status_code == 422
    body = response.json()["detail"]
    assert body["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert body["noProviderDispatchConfirmed"] is True
    assert body["noAuthBillingOrMoneyActionConfirmed"] is True


async def test_referral_saas_admin_can_validate_customer_journey_draft(
    monkeypatch,
):
    resolve_calls: list[dict] = []
    validate_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    async def fake_validate_referral_saas_customer_journey_draft(**kwargs):
        validate_calls.append(kwargs)
        return SimpleNamespace(
            to_safe_dict=lambda: {
                "journeyValidationResultId": "validation-1",
                "customerJourneyDraftId": "draft-1",
                "validationStatus": "PASSED_WITH_WARNINGS",
                "blockers": [],
                "warnings": [{"code": "EMPTY_CONFIGURATION"}],
                "safeSummary": {"blockerCount": 0, "warningCount": 1},
                "noRuntimeJourneyMutationConfirmed": True,
                "noCampaignActivationConfirmed": True,
            }
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "validate_referral_saas_customer_journey_draft",
        fake_validate_referral_saas_customer_journey_draft,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/journey-drafts/draft-1/validate",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "idempotencyKey": "draft-validate-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["validation"]["validationStatus"] == "PASSED_WITH_WARNINGS"
    assert body["noRuntimeJourneyMutationConfirmed"] is True
    assert body["noCampaignActivationConfirmed"] is True
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert validate_calls[0]["account_id"] == "acct-1"
    assert validate_calls[0]["customer_journey_draft_id"] == "draft-1"
    assert validate_calls[0]["idempotency_key_hash"]
    assert validate_calls[0]["request_payload_hash"]


async def test_referral_saas_admin_can_publish_customer_journey_version(
    monkeypatch,
):
    resolve_calls: list[dict] = []
    publish_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    async def fake_publish_referral_saas_customer_journey_version(**kwargs):
        publish_calls.append(kwargs)
        return SimpleNamespace(
            to_safe_dict=lambda: {
                "commandStatus": "VERSION_PUBLISHED",
                "idempotencyStatus": "NEW_REQUEST",
                "version": {
                    "customerJourneyVersionId": "version-1",
                    "customerJourneyDraftId": "draft-1",
                    "versionStatus": "PUBLISHED",
                    "customerJourneyCode": "FNB_REFERRAL_JOURNEY",
                    "versionNumber": 1,
                },
                "noRuntimeJourneyMutationConfirmed": True,
                "noCampaignBindingConfirmed": True,
                "noCampaignActivationConfirmed": True,
                "noProviderDispatchConfirmed": True,
                "noAuthBillingOrMoneyActionConfirmed": True,
            }
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "publish_referral_saas_customer_journey_version",
        fake_publish_referral_saas_customer_journey_version,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/journey-drafts/draft-1/publish",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "idempotencyKey": "draft-publish-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["commandStatus"] == "VERSION_PUBLISHED"
    assert body["version"]["versionStatus"] == "PUBLISHED"
    assert body["noCampaignBindingConfirmed"] is True
    assert body["noProviderDispatchConfirmed"] is True
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert publish_calls[0]["account_id"] == "acct-1"
    assert publish_calls[0]["customer_journey_draft_id"] == "draft-1"
    assert publish_calls[0]["idempotency_key_hash"]
    assert publish_calls[0]["request_payload_hash"]


async def test_referral_saas_customer_journey_publish_blocks_unvalidated_draft(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    async def fake_publish_referral_saas_customer_journey_version(**kwargs):
        raise referral_saas_accounts.CustomerJourneyDraftValidationError(
            "Journey draft must pass validation before it can be published."
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "publish_referral_saas_customer_journey_version",
        fake_publish_referral_saas_customer_journey_version,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/journey-drafts/draft-1/publish",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                },
                "idempotencyKey": "draft-publish-unvalidated",
            },
        )

    assert response.status_code == 422
    body = response.json()["detail"]
    assert body["code"] == "VALIDATION_ERROR"
    assert "VALIDATED_DRAFT_REQUIRED" in body["guardrails"]


async def test_referral_saas_admin_can_archive_customer_journey_version(
    monkeypatch,
):
    archive_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    async def fake_archive_referral_saas_customer_journey_version(**kwargs):
        archive_calls.append(kwargs)
        return SimpleNamespace(
            to_safe_dict=lambda: {
                "commandStatus": "VERSION_ARCHIVED",
                "idempotencyStatus": "NEW_REQUEST",
                "version": {
                    "customerJourneyVersionId": "version-1",
                    "versionStatus": "ARCHIVED",
                    "archiveReason": "Superseded by a safer journey.",
                },
                "archiveBlockers": [],
                "noRuntimeJourneyMutationConfirmed": True,
                "noCampaignBindingConfirmed": True,
                "noCampaignActivationConfirmed": True,
                "noProviderDispatchConfirmed": True,
                "noAuthBillingOrMoneyActionConfirmed": True,
            }
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "archive_referral_saas_customer_journey_version",
        fake_archive_referral_saas_customer_journey_version,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/journey-versions/version-1/archive",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "archiveReason": "Superseded by a safer journey.",
                "idempotencyKey": "version-archive-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["commandStatus"] == "VERSION_ARCHIVED"
    assert body["version"]["versionStatus"] == "ARCHIVED"
    assert body["noRuntimeJourneyMutationConfirmed"] is True
    assert archive_calls[0]["customer_journey_version_id"] == "version-1"
    assert archive_calls[0]["archive_reason"] == "Superseded by a safer journey."


async def test_referral_saas_customer_journey_archive_blocks_active_binding(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    async def fake_archive_referral_saas_customer_journey_version(**kwargs):
        raise referral_saas_accounts.CustomerJourneyVersionArchiveBlocked(
            "Journey version cannot be archived while active campaign bindings exist."
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "archive_referral_saas_customer_journey_version",
        fake_archive_referral_saas_customer_journey_version,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/journey-versions/version-1/archive",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                },
                "archiveReason": "Superseded",
                "idempotencyKey": "version-archive-blocked",
            },
        )

    assert response.status_code == 409
    body = response.json()["detail"]
    assert body["code"] == "CUSTOMER_JOURNEY_VERSION_ARCHIVE_BLOCKED"
    assert "ARCHIVE_ACTIVE_BINDING_BLOCKED" in body["guardrails"]
    assert body["noCampaignBindingMutationConfirmed"] is True


async def test_referral_saas_admin_can_list_customer_journey_incentive_bindings(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    async def fake_list_referral_saas_customer_journey_incentive_bindings(**kwargs):
        assert kwargs["account_id"] == "acct-1"
        assert kwargs["customer_journey_version_id"] == "version-1"
        return (
            SimpleNamespace(
                to_safe_dict=lambda: {
                    "customerJourneyIncentiveBindingId": "binding-1",
                    "incentiveType": "MISSION",
                    "catalogueRef": "WELCOME_MISSION",
                    "bindingStatus": "ACTIVE",
                    "noRewardApplicationConfirmed": True,
                    "noBadgeAwardConfirmed": True,
                    "noMissionProgressMutationConfirmed": True,
                    "noLeaderboardScoringConfirmed": True,
                    "noCampaignActivationConfirmed": True,
                    "noProviderDispatchConfirmed": True,
                    "noAuthBillingOrMoneyActionConfirmed": True,
                }
            ),
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "list_referral_saas_customer_journey_incentive_bindings",
        fake_list_referral_saas_customer_journey_incentive_bindings,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/journey-versions/version-1/incentive-bindings",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["incentiveBindings"][0]["incentiveType"] == "MISSION"
    assert body["noRewardApplicationConfirmed"] is True
    assert body["noLeaderboardScoringConfirmed"] is True
    assert "NO_AUTH_BILLING_OR_MONEY_ACTION" in body["guardrails"]


async def test_referral_saas_admin_can_bind_customer_journey_incentive(
    monkeypatch,
):
    bind_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    async def fake_bind_referral_saas_customer_journey_incentive(**kwargs):
        bind_calls.append(kwargs)
        return SimpleNamespace(
            to_safe_dict=lambda: {
                "commandStatus": "CUSTOMER_JOURNEY_INCENTIVE_BOUND",
                "idempotencyStatus": "NEW_REQUEST",
                "binding": {
                    "customerJourneyIncentiveBindingId": "binding-1",
                    "incentiveType": "REWARD_POLICY",
                    "catalogueRef": "42",
                    "bindingStatus": "ACTIVE",
                },
                "noRewardApplicationConfirmed": True,
                "noBadgeAwardConfirmed": True,
                "noMissionProgressMutationConfirmed": True,
                "noLeaderboardScoringConfirmed": True,
                "noCampaignActivationConfirmed": True,
                "noProviderDispatchConfirmed": True,
                "noAuthBillingOrMoneyActionConfirmed": True,
            }
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "bind_referral_saas_customer_journey_incentive",
        fake_bind_referral_saas_customer_journey_incentive,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/journey-versions/version-1/incentive-bindings",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "incentiveType": "REWARD_POLICY",
                "catalogueRef": "42",
                "idempotencyKey": "incentive-binding-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["commandStatus"] == "CUSTOMER_JOURNEY_INCENTIVE_BOUND"
    assert body["binding"]["incentiveType"] == "REWARD_POLICY"
    assert body["noRewardApplicationConfirmed"] is True
    assert body["noCampaignActivationConfirmed"] is True
    assert bind_calls[0]["customer_journey_version_id"] == "version-1"
    assert bind_calls[0]["incentive_type"] == "REWARD_POLICY"
    assert bind_calls[0]["catalogue_ref"] == "42"
    assert bind_calls[0]["idempotency_key_hash"]
    assert bind_calls[0]["request_payload_hash"]


async def test_referral_saas_customer_journey_incentive_binding_rejects_unapproved_catalogue(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    async def fake_bind_referral_saas_customer_journey_incentive(**kwargs):
        raise referral_saas_accounts.CustomerJourneyIncentiveBindingValidationError(
            "Active reward policy was not found for this catalogue reference."
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "bind_referral_saas_customer_journey_incentive",
        fake_bind_referral_saas_customer_journey_incentive,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/journey-versions/version-1/incentive-bindings",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                },
                "incentiveType": "REWARD_POLICY",
                "catalogueRef": "999",
                "idempotencyKey": "incentive-binding-unapproved",
            },
        )

    assert response.status_code == 422
    body = response.json()["detail"]
    assert body["code"] == "validation_error"
    assert "APPROVED_INCENTIVE_CATALOGUE_REFERENCE_REQUIRED" in body["guardrails"]


async def test_referral_saas_customer_journey_incentive_binding_idempotency_conflict(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    async def fake_bind_referral_saas_customer_journey_incentive(**kwargs):
        raise referral_saas_accounts.CustomerJourneyIncentiveBindingIdempotencyConflict(
            "Idempotency key was reused with different customer journey incentive binding content."
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "bind_referral_saas_customer_journey_incentive",
        fake_bind_referral_saas_customer_journey_incentive,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/journey-versions/version-1/incentive-bindings",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                },
                "incentiveType": "MISSION",
                "catalogueRef": "WELCOME_MISSION",
                "idempotencyKey": "incentive-binding-conflict",
            },
        )

    assert response.status_code == 409
    body = response.json()["detail"]
    assert body["code"] == "idempotency_conflict"
    assert "IDEMPOTENT_INCENTIVE_BINDING_COMMANDS" in body["guardrails"]


async def test_referral_saas_account_reader_can_read_journey_analytics(monkeypatch):
    calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", tenant_code="FNB")

    async def fake_build_referral_saas_journey_analytics_read_model(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            to_safe_dict=lambda: {
                "versionCount": 1,
                "versions": [
                    {
                        "customerJourneyVersionId": "version-1",
                        "customerJourneyCode": "FNB_REFERRAL",
                        "versionNumber": 2,
                        "versionStatus": "PUBLISHED",
                        "campaignCount": 1,
                        "referralCount": 10,
                        "attributionRate": 0.7,
                        "completionRate": 0.4,
                        "guardrails": ["ACCOUNT_SCOPED_JOURNEY_ANALYTICS"],
                        "redactions": ["tenant_code", "raw_event_payload"],
                    }
                ],
                "summary": {
                    "journeyVersionsCompared": 1,
                    "analyticsSignal": "OPTIMISE_COMPLETION",
                },
                "guardrails": ["ACCOUNT_SCOPED_JOURNEY_ANALYTICS"],
                "redactions": ["tenant_code", "raw_event_payload"],
                "noRawIdentityOrEventPayloadConfirmed": True,
                "noRewardPayoutDetailConfirmed": True,
                "noProviderDispatchConfirmed": True,
                "noAuthBillingSettlementOrMoneyActionConfirmed": True,
            }
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "build_referral_saas_journey_analytics_read_model",
        fake_build_referral_saas_journey_analytics_read_model,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/journey-analytics",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
                "limit": 10,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["account"]["accountCode"] == "ACCT_FNB"
    assert "tenantCode" not in body["account"]
    assert body["journeyAnalytics"]["summary"]["analyticsSignal"] == (
        "OPTIMISE_COMPLETION"
    )
    assert body["journeyAnalytics"]["versions"][0]["completionRate"] == 0.4
    assert body["noRawIdentityOrEventPayloadConfirmed"] is True
    assert body["noAuthBillingSettlementOrMoneyActionConfirmed"] is True
    assert calls == [
        {
            "account_id": "acct-1",
            "tenant_code": "FNB",
            "limit": 10,
            "data_window_start": None,
            "data_window_end": None,
        }
    ]


async def test_referral_saas_partner_cannot_list_global_journey_templates():
    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get("/v1/referral-saas/journey-templates")

    assert response.status_code == 403


async def test_referral_saas_partner_workspace_account_context_is_account_scoped(
    monkeypatch,
):
    calls: list[dict] = []

    async def fake_build_referral_saas_partner_workspace_account_context(**kwargs):
        calls.append(kwargs)
        return PartnerWorkspaceAccountContext(
            actor_role="PARTNER",
            accounts=(
                PartnerWorkspaceAccountContextItem(
                    account_id="acct-1",
                    account_code="ACCT_FNB",
                    account_name="FNB Referral SaaS",
                    account_type="ORGANISATION",
                    account_status="ACTIVE",
                    onboarding_status="APPROVED",
                    operating_jurisdiction_code="ZA",
                    primary_external_tenant_ref="fnb-referrals",
                    external_references=(
                        {
                            "refType": "external_tenant_ref",
                            "externalRef": "fnb-referrals",
                            "referenceStatus": "ACTIVE",
                        },
                    ),
                    role_families=("DISTRIBUTION_ADMIN",),
                    permission_sets=("REFERRAL_SAAS_ACCOUNT_ADMIN",),
                    membership_statuses=("ACTIVE",),
                    source="membership",
                ),
            ),
            guardrails=("PARTNER_WORKSPACE_ACCOUNT_CONTEXT",),
            redactions=("internal_tenant_identifier", "tenant_code"),
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "build_referral_saas_partner_workspace_account_context",
        fake_build_referral_saas_partner_workspace_account_context,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PARTNER_HEADERS
    ) as client:
        response = await client.get(
            "/v1/referral-saas/workspace/account-context",
            params={"limit": 10},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["count"] == 1
    assert body["workspaceContext"]["actor"] == {
        "role": "PARTNER",
        "accountCount": 1,
    }
    assert body["workspaceContext"]["accounts"][0]["accountCode"] == "ACCT_FNB"
    assert "tenantCode" not in body["workspaceContext"]["accounts"][0]
    assert "tenant_code" not in str(body["workspaceContext"]["accounts"])
    assert body["no_internal_tenant_identifier_exposure_confirmed"] is True
    assert body["no_unscoped_account_enumeration_confirmed"] is True
    assert calls == [
        {
            "actor_role": "PARTNER",
            "actor_tenant_code": "FNB",
            "actor_subjects": set(),
            "actor_client_ids": set(),
            "account_refs": set(),
            "external_tenant_refs": set(),
            "organisation_refs": set(),
            "operating_jurisdictions": set(),
            "limit": 10,
        }
    ]


async def test_referral_saas_partner_workspace_account_context_forwards_jwt_claims(
    monkeypatch,
):
    calls: list[dict] = []

    async def fake_build_referral_saas_partner_workspace_account_context(**kwargs):
        calls.append(kwargs)
        return PartnerWorkspaceAccountContext(
            actor_role="DISTRIBUTOR",
            accounts=(),
            guardrails=("PARTNER_WORKSPACE_ACCOUNT_CONTEXT",),
            redactions=("internal_tenant_identifier", "tenant_code"),
        )

    def fake_require_referral_saas_workspace_actor(identity):
        return {
            "role": "DISTRIBUTOR",
            "tenant_code": "FNB",
            "subject": "operator@example.test",
            "client_id": "client-1",
            "account_ref": "ACCT_FNB",
            "external_tenant_ref": "fnb-referrals",
            "organisation_ref": "fnb-org",
            "operating_jurisdiction_code": "ZA",
            "capabilities": ["REFERRAL_SAAS_WORKSPACE_READ"],
        }

    monkeypatch.setattr(
        referral_saas_accounts,
        "build_referral_saas_partner_workspace_account_context",
        fake_build_referral_saas_partner_workspace_account_context,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "_require_referral_saas_workspace_actor",
        fake_require_referral_saas_workspace_actor,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PARTNER_HEADERS
    ) as client:
        response = await client.get("/v1/referral-saas/workspace/account-context")

    assert response.status_code == 200
    assert calls == [
        {
            "actor_role": "DISTRIBUTOR",
            "actor_tenant_code": "FNB",
            "actor_subjects": {"operator@example.test"},
            "actor_client_ids": {"client-1"},
            "account_refs": {"ACCT_FNB"},
            "external_tenant_refs": {"fnb-referrals"},
            "organisation_refs": {"fnb-org"},
            "operating_jurisdictions": {"ZA"},
            "limit": 50,
        }
    ]


async def test_referral_saas_partner_workspace_account_context_rejects_admin_registry_role():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get("/v1/referral-saas/workspace/account-context")

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["code"] == "permission_denied"
    assert "NO_ADMIN_REGISTRY_REUSE" in detail["guardrails"]


async def test_referral_saas_partner_workspace_account_context_rejects_missing_capability(
    monkeypatch,
):
    def fake_require_session_key():
        return {
            "role": "PARTNER",
            "tenant_code": "FNB",
            "capabilities": ["CAMPAIGN_WRITE"],
        }

    app.dependency_overrides[referral_saas_accounts.require_session_key] = (
        fake_require_session_key
    )
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/referral-saas/workspace/account-context")
    finally:
        app.dependency_overrides.pop(referral_saas_accounts.require_session_key, None)

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["code"] == "permission_denied"
    assert "SERVER_SIDE_ACCOUNT_CAPABILITY_ENFORCEMENT" in detail["guardrails"]


async def test_referral_saas_workspace_overview_requires_selected_admin_account():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get("/v1/referral-saas/workspace/overview")

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "selected_account_required"
    assert "NO_UNSCOPED_ACCOUNT_ENUMERATION" in detail["guardrails"]


async def test_referral_saas_workspace_overview_returns_admin_selected_summary(
    monkeypatch,
):
    async def fake_list_referral_saas_accounts(**kwargs):
        assert kwargs == {"limit": 50}
        return [
            AccountFoundationListItem(
                account_id="acct-1",
                account_code="ACCT_FNB",
                account_name="FNB Referral SaaS",
                account_type="ORGANISATION",
                account_status="ACTIVE",
                onboarding_status="APPROVED",
                operating_jurisdiction_code="ZA",
                primary_external_tenant_ref="fnb-referrals",
                external_references=(
                    {
                        "refType": "external_tenant_ref",
                        "externalRef": "fnb-referrals",
                        "referenceStatus": "ACTIVE",
                    },
                ),
                created_at="2026-01-01T00:00:00+00:00",
                updated_at="2026-01-01T00:00:00+00:00",
            ),
        ]

    monkeypatch.setattr(
        referral_saas_accounts,
        "list_referral_saas_accounts",
        fake_list_referral_saas_accounts,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/workspace/overview",
            params={"selected_account_ref": "ACCT_FNB"},
        )

    assert response.status_code == 200
    body = response.json()
    overview = body["workspaceOverview"]
    assert overview["selectedAccount"]["accountCode"] == "ACCT_FNB"
    assert overview["primaryAction"]["label"] == "Review people and access"
    assert overview["safeToLeave"]["canLeaveSafely"] is True
    assert "tenantCode" not in overview["selectedAccount"]
    assert "tenant_code" not in str(overview["selectedAccount"])
    assert body["no_membership_write_confirmed"] is True
    assert body["no_invite_delivery_confirmed"] is True
    assert body["no_money_movement_confirmed"] is True


async def test_referral_saas_workspace_overview_uses_partner_account_context(
    monkeypatch,
):
    calls: list[dict] = []

    async def fake_build_referral_saas_partner_workspace_account_context(**kwargs):
        calls.append(kwargs)
        return PartnerWorkspaceAccountContext(
            actor_role="PARTNER",
            accounts=(
                PartnerWorkspaceAccountContextItem(
                    account_id="acct-1",
                    account_code="ACCT_FNB",
                    account_name="FNB Referral SaaS",
                    account_type="ORGANISATION",
                    account_status="ACTIVE",
                    onboarding_status="APPROVED",
                    operating_jurisdiction_code="ZA",
                    primary_external_tenant_ref="fnb-referrals",
                    external_references=(
                        {
                            "refType": "external_tenant_ref",
                            "externalRef": "fnb-referrals",
                            "referenceStatus": "ACTIVE",
                        },
                    ),
                    role_families=("CAMPAIGN_MANAGER",),
                    permission_sets=("REFERRAL_SAAS_CAMPAIGN_MANAGER",),
                    membership_statuses=("ACTIVE",),
                    source="membership",
                ),
            ),
            guardrails=("PARTNER_WORKSPACE_ACCOUNT_CONTEXT",),
            redactions=("internal_tenant_identifier", "tenant_code"),
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "build_referral_saas_partner_workspace_account_context",
        fake_build_referral_saas_partner_workspace_account_context,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PARTNER_HEADERS
    ) as client:
        response = await client.get("/v1/referral-saas/workspace/overview")

    assert response.status_code == 200
    body = response.json()
    overview = body["workspaceOverview"]
    assert overview["actor"] == {"role": "PARTNER", "visibleAccountCount": 1}
    assert overview["readiness"]["red"] == 0
    assert overview["primaryAction"]["actionRef"] == "check_integrations"
    assert [action["actionRef"] for action in overview["worklist"]] == [
        "check_integrations",
        "open_campaigns",
    ]
    assert "tenantCode" not in overview["selectedAccount"]
    assert "tenant_code" not in str(overview["selectedAccount"])
    assert calls[0]["actor_role"] == "PARTNER"


async def test_referral_saas_account_admin_can_activate_account_foundation(monkeypatch):
    resolve_calls: list[dict] = []
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context(
            account_status="PENDING_ONBOARDING",
            onboarding_status="READY_FOR_REVIEW",
            tenant_link_status="PENDING_SETUP",
        )

    async def fake_activate_referral_saas_account_foundation(**kwargs):
        command_calls.append(kwargs)
        return _account_activation_result()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "activate_referral_saas_account_foundation",
        fake_activate_referral_saas_account_foundation,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/activation-requests",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "activation": {"seatTypes": ["ADMIN", "OPERATOR"]},
                "reasonCode": "CUSTOMER_ACCOUNT_FOUNDATION_ACTIVATION",
                "correlationId": "corr-activation-1",
                "idempotencyKey": "account-activation-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["activation"]["commandStatus"] == "ACCOUNT_FOUNDATION_ACTIVATED"
    assert body["activation"]["accountStatus"] == "ACTIVE"
    assert body["activation"]["tenantLinkStatus"] == "ACTIVE"
    assert body["activation"]["seatCapacity"] == {
        "seatTypes": ["ADMIN", "OPERATOR"],
        "createdSeatCount": 2,
    }
    assert body["no_membership_write_confirmed"] is True
    assert body["no_seat_assignment_confirmed"] is True
    assert body["no_auth_claim_change_confirmed"] is True
    assert body["no_billing_or_money_movement_confirmed"] is True
    assert "tenantCode" not in body["account"]
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert command_calls[0]["account_id"] == "acct-1"
    assert command_calls[0]["tenant_code"] == "FNB"
    assert command_calls[0]["seat_types"] == ["ADMIN", "OPERATOR"]
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["command_payload_hash"]


async def test_referral_saas_account_activation_rejects_runtime_context():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/activation-requests",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "runtime",
                },
                "correlationId": "corr-activation-1",
                "idempotencyKey": "account-activation-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "validation_error"
    assert "setup" in detail["message"]


async def test_referral_saas_account_admin_can_update_customer_profile(monkeypatch):
    calls: list[dict] = []

    async def fake_update_referral_saas_account_profile(**kwargs):
        calls.append(kwargs)
        return _profile_result()

    monkeypatch.setattr(
        referral_saas_accounts,
        "update_referral_saas_account_profile",
        fake_update_referral_saas_account_profile,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.patch(
            "/v1/referral-saas/accounts/acct-1/profile",
            json={
                "profile": {
                    "accountName": " FNB Referral SaaS Updated ",
                    "accountType": "ORGANISATION",
                    "operatingJurisdictionCode": "ZA",
                    "customerType": "ENTERPRISE_CUSTOMER",
                    "industry": "AUTOMOTIVE",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "profile-update-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["profile"]["accountName"] == "FNB Referral SaaS Updated"
    assert body["profile"]["customerType"] == "ENTERPRISE_CUSTOMER"
    assert body["no_external_reference_rotation_confirmed"] is True
    assert body["no_account_activation_confirmed"] is True
    assert body["no_membership_write_confirmed"] is True
    assert body["no_money_movement_confirmed"] is True
    assert "tenantCode" not in str(body)
    assert calls[0]["account_ref"] == "acct-1"
    assert calls[0]["account_name"] == "FNB Referral SaaS Updated"
    assert calls[0]["customer_type"] == "ENTERPRISE_CUSTOMER"
    assert calls[0]["industry"] == "AUTOMOTIVE"
    assert calls[0]["idempotency_key_hash"]
    assert calls[0]["command_payload_hash"]


async def test_referral_saas_profile_update_rejects_unsafe_reference_rotation_payload():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.patch(
            "/v1/referral-saas/accounts/acct-1/profile",
            json={
                "profile": {
                    "accountName": "FNB Referral SaaS Updated",
                    "accountType": "ORGANISATION",
                    "operatingJurisdictionCode": "ZA",
                    "externalTenantRef": "new-ref",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "profile-update-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert detail["no_external_reference_rotation_confirmed"] is True


async def test_referral_saas_profile_update_maps_safe_not_found(monkeypatch):
    async def fake_update_referral_saas_account_profile(**kwargs):
        raise AccountProfileNotFound("Account missing.")

    monkeypatch.setattr(
        referral_saas_accounts,
        "update_referral_saas_account_profile",
        fake_update_referral_saas_account_profile,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.patch(
            "/v1/referral-saas/accounts/acct-missing/profile",
            json={
                "profile": {
                    "accountName": "FNB Referral SaaS Updated",
                    "accountType": "ORGANISATION",
                    "operatingJurisdictionCode": "ZA",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "profile-update-1",
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "ACCOUNT_NOT_FOUND"


async def test_referral_saas_profile_update_rejects_adjacent_role():
    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.patch(
            "/v1/referral-saas/accounts/acct-1/profile",
            json={},
        )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "permission_denied"


async def test_referral_saas_account_registry_rejects_adjacent_role():
    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get("/v1/referral-saas/accounts")

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "permission_denied"


async def test_referral_saas_account_admin_can_record_membership_invitation_intent(
    monkeypatch,
):
    resolve_calls: list[dict] = []
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context(
            account_status="PENDING_ONBOARDING",
            tenant_link_status="PENDING_SETUP",
        )

    async def fake_record_referral_saas_membership_invitation_intent(**kwargs):
        command_calls.append(kwargs)
        return _invitation_result()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "record_referral_saas_membership_invitation_intent",
        fake_record_referral_saas_membership_invitation_intent,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/membership-invitations",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "actor": {
                    "actorType": "USER",
                    "subject": "setup-owner-subject",
                    "emailHash": "email-hash-only",
                    "displayName": "Setup Owner",
                },
                "membership": {
                    "roleFamily": "DISTRIBUTION_ADMIN",
                    "permissionSet": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                    "tenantScope": "PRIMARY_ACCOUNT_TENANT",
                },
                "reasonCode": "ACCOUNT_SETUP_USER_ROLE",
                "correlationId": "corr-1",
                "idempotencyKey": "invite-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["account"]["accountCode"] == "ACCT_FNB"
    assert "tenantCode" not in body["account"]
    assert body["invitation"]["commandStatus"] == "INVITATION_INTENT_RECORDED"
    assert body["invitation"]["membership"]["status"] == "INVITED"
    assert body["invitation"]["delivery"]["status"] == "DELIVERY_NOT_CONFIGURED"
    assert body["invitation"]["noInviteDeliveryConfirmed"] is True
    assert body["no_auth_claim_change_confirmed"] is True
    assert body["no_seat_assignment_confirmed"] is True
    assert body["no_money_movement_confirmed"] is True
    assert "NO_EMAIL_DELIVERY_WITHOUT_PROVIDER" in body["guardrails"]
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert command_calls[0]["account_id"] == "acct-1"
    assert command_calls[0]["tenant_code"] == "FNB"
    assert command_calls[0]["actor_type"] == "USER"
    assert command_calls[0]["subject"] == "setup-owner-subject"
    assert command_calls[0]["role_family"] == "DISTRIBUTION_ADMIN"
    assert command_calls[0]["permission_set"] == "REFERRAL_SAAS_ACCOUNT_ADMIN"
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["command_payload_hash"]


async def test_referral_saas_membership_invitation_rejects_path_scope_mismatch(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-other/membership-invitations",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                },
                "actor": {"actorType": "USER", "subject": "setup-owner-subject"},
                "membership": {
                    "roleFamily": "DISTRIBUTION_ADMIN",
                    "permissionSet": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "invite-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_SCOPE"
    assert detail["no_invite_delivery_confirmed"] is True


async def test_referral_saas_membership_invitation_rejects_adjacent_role():
    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/membership-invitations",
            json={},
        )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "permission_denied"


async def test_referral_saas_membership_invitation_rejects_unsafe_payload():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/membership-invitations",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                },
                "actor": {
                    "actorType": "USER",
                    "subject": "setup-owner-subject",
                    "email": "raw@example.test",
                },
                "membership": {
                    "roleFamily": "DISTRIBUTION_ADMIN",
                    "permissionSet": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "invite-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert "NO_RAW_EMAIL_STORAGE" in detail["guardrails"]


async def test_referral_saas_membership_invitation_maps_duplicate_safely(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_status="PENDING_ONBOARDING",
            tenant_link_status="PENDING_SETUP",
        )

    async def fake_record_referral_saas_membership_invitation_intent(**kwargs):
        raise MembershipInvitationDuplicate("Membership already exists.")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "record_referral_saas_membership_invitation_intent",
        fake_record_referral_saas_membership_invitation_intent,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/membership-invitations",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                },
                "actor": {"actorType": "USER", "subject": "setup-owner-subject"},
                "membership": {
                    "roleFamily": "DISTRIBUTION_ADMIN",
                    "permissionSet": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "invite-1",
            },
        )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "MEMBERSHIP_ALREADY_EXISTS"
    assert detail["no_seat_assignment_confirmed"] is True


async def test_referral_saas_account_admin_can_update_invited_access_intent(
    monkeypatch,
):
    resolve_calls: list[dict] = []
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context()

    async def fake_update_referral_saas_membership_invitation_intent(**kwargs):
        command_calls.append(kwargs)
        return _invitation_lifecycle_result()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "update_referral_saas_membership_invitation_intent",
        fake_update_referral_saas_membership_invitation_intent,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.patch(
            "/v1/referral-saas/accounts/acct-1/membership-invitations/membership-1",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "actor": {
                    "emailHash": "safe-email-hash",
                    "displayName": "Campaign Owner",
                },
                "membership": {
                    "roleFamily": "CAMPAIGN_MANAGER",
                    "permissionSet": "REFERRAL_SAAS_CAMPAIGN_MANAGER",
                },
                "reasonCode": "CUSTOMER_PROFILE_ACCESS_INTENT_UPDATE",
                "correlationId": "corr-1",
                "idempotencyKey": "update-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["invitation"]["commandStatus"] == "INVITATION_INTENT_UPDATED"
    assert body["invitation"]["membership"]["roleFamily"] == "CAMPAIGN_MANAGER"
    assert body["invitation"]["noInviteDeliveryConfirmed"] is True
    assert body["no_auth_claim_change_confirmed"] is True
    assert body["no_seat_assignment_confirmed"] is True
    assert body["no_money_movement_confirmed"] is True
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert command_calls[0]["membership_id"] == "membership-1"
    assert command_calls[0]["email_hash"] == "safe-email-hash"
    assert command_calls[0]["role_family"] == "CAMPAIGN_MANAGER"
    assert command_calls[0]["permission_set"] == "REFERRAL_SAAS_CAMPAIGN_MANAGER"
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["command_payload_hash"]


async def test_referral_saas_account_admin_can_cancel_invited_access_intent(
    monkeypatch,
):
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context()

    async def fake_cancel_referral_saas_membership_invitation_intent(**kwargs):
        command_calls.append(kwargs)
        return _invitation_lifecycle_result(
            command_status="INVITATION_INTENT_CANCELLED",
            membership_status="DISABLED",
            lifecycle_next_action="Record a new access intent if this person should manage the customer again.",
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "cancel_referral_saas_membership_invitation_intent",
        fake_cancel_referral_saas_membership_invitation_intent,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.request(
            "DELETE",
            "/v1/referral-saas/accounts/acct-1/membership-invitations/membership-1",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "reasonCode": "CUSTOMER_PROFILE_ACCESS_INTENT_CANCEL",
                "correlationId": "corr-1",
                "idempotencyKey": "cancel-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["invitation"]["commandStatus"] == "INVITATION_INTENT_CANCELLED"
    assert body["invitation"]["membership"]["status"] == "DISABLED"
    assert body["invitation"]["noMembershipActivationConfirmed"] is True
    assert body["no_invite_delivery_confirmed"] is True
    assert body["no_auth_claim_change_confirmed"] is True
    assert command_calls[0]["membership_id"] == "membership-1"
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["command_payload_hash"]


async def test_referral_saas_account_admin_can_request_invitation_delivery_boundary(
    monkeypatch,
):
    resolve_calls: list[dict] = []
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context()

    async def fake_request_referral_saas_membership_invitation_delivery(**kwargs):
        command_calls.append(kwargs)
        return _delivery_request_result()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "request_referral_saas_membership_invitation_delivery",
        fake_request_referral_saas_membership_invitation_delivery,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/membership-invitations/membership-1/delivery",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "delivery": {
                    "providerRef": "mail-provider-1",
                    "channel": "EMAIL",
                    "templateRef": "referral-saas-account-invite-v1",
                },
                "reasonCode": "CUSTOMER_PROFILE_INVITE_DELIVERY_REQUEST",
                "correlationId": "corr-1",
                "idempotencyKey": "delivery-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "blocked"
    assert body["deliveryRequest"]["commandStatus"] == "DELIVERY_PROVIDER_NOT_CONFIGURED"
    assert body["deliveryRequest"]["delivery"]["status"] == "DELIVERY_PROVIDER_NOT_CONFIGURED"
    assert body["deliveryRequest"]["membership"]["membershipRef"] == "membership-1"
    assert body["no_invite_delivery_confirmed"] is True
    assert body["no_membership_activation_confirmed"] is True
    assert body["no_auth_claim_change_confirmed"] is True
    assert body["no_seat_assignment_confirmed"] is True
    assert body["no_money_movement_confirmed"] is True
    assert "NO_PROVIDER_SECRET_EXPOSURE" in body["guardrails"]
    assert "recipient_hash" in body["redactions"]
    assert "tenantCode" not in body["account"]
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert command_calls[0]["account_id"] == "acct-1"
    assert command_calls[0]["membership_id"] == "membership-1"
    assert command_calls[0]["provider_ref"] == "mail-provider-1"
    assert command_calls[0]["channel"] == "EMAIL"
    assert command_calls[0]["recipient_hash"] == ""
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["command_payload_hash"]


async def test_referral_saas_invitation_delivery_rejects_path_scope_mismatch(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-other/membership-invitations/membership-1/delivery",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                },
                "delivery": {
                    "providerRef": "mail-provider-1",
                    "channel": "EMAIL",
                    "templateRef": "referral-saas-account-invite-v1",
                    "recipientHash": "recipient-hash",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "delivery-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_SCOPE"
    assert detail["no_invite_delivery_confirmed"] is True
    assert detail["no_auth_claim_change_confirmed"] is True


async def test_referral_saas_account_admin_can_issue_acceptance_token(monkeypatch):
    command_calls = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context()

    async def fake_issue_referral_saas_membership_acceptance_token(**kwargs):
        command_calls.append(kwargs)
        return _acceptance_token_issue_result()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "issue_referral_saas_membership_acceptance_token",
        fake_issue_referral_saas_membership_acceptance_token,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/membership-invitations/membership-1/acceptance-token",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "acceptance": {"acceptedSubject": "owner@example.test"},
                "ttlHours": 48,
                "correlationId": "corr-token-1",
                "idempotencyKey": "token-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "issued"
    assert body["acceptanceToken"]["acceptanceToken"]["token"] == "accept-token-123456"
    assert body["acceptanceToken"]["acceptanceToken"]["hint"] == "123456"
    assert body["no_membership_activation_confirmed"] is True
    assert body["no_credential_creation_confirmed"] is True
    assert command_calls[0]["membership_id"] == "membership-1"
    assert command_calls[0]["accepted_subject"] == "owner@example.test"


async def test_referral_saas_acceptance_token_validate_is_public(monkeypatch):
    command_calls = []

    async def fake_validate_referral_saas_membership_acceptance_token(**kwargs):
        command_calls.append(kwargs)
        return _acceptance_token_validation_result()

    monkeypatch.setattr(
        referral_saas_accounts,
        "validate_referral_saas_membership_acceptance_token",
        fake_validate_referral_saas_membership_acceptance_token,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/v1/referral-saas/membership-acceptance/validate",
            json={"token": "accept-token-123456"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["acceptance"]["tokenStatus"] == "ISSUED"
    assert body["acceptance"]["noMembershipActivationConfirmed"] is True
    assert command_calls[0]["acceptance_token"] == "accept-token-123456"


async def test_referral_saas_acceptance_token_accept_is_public_and_safe(monkeypatch):
    command_calls = []

    async def fake_accept_referral_saas_membership_acceptance_token(**kwargs):
        command_calls.append(kwargs)
        return _acceptance_token_accept_result()

    monkeypatch.setattr(
        referral_saas_accounts,
        "accept_referral_saas_membership_acceptance_token",
        fake_accept_referral_saas_membership_acceptance_token,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/v1/referral-saas/membership-acceptance/accept",
            json={
                "token": "accept-token-123456",
                "acceptanceEvidenceRef": "member-clicked-link",
                "correlationId": "corr-accept-1",
                "idempotencyKey": "accept-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert body["acceptance"]["tokenStatus"] == "ACCEPTED"
    assert body["acceptance"]["noSeatAssignmentConfirmed"] is True
    assert body["acceptance"]["noCredentialCreationConfirmed"] is True
    assert command_calls[0]["acceptance_token"] == "accept-token-123456"


async def test_referral_saas_account_admin_can_request_membership_activation_boundary(
    monkeypatch,
):
    resolve_calls: list[dict] = []
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context()

    async def fake_request_referral_saas_membership_activation(**kwargs):
        command_calls.append(kwargs)
        return _activation_request_result()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "request_referral_saas_membership_activation",
        fake_request_referral_saas_membership_activation,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/memberships/membership-1/activation",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "activation": {
                    "acceptedSubject": "owner@example.test",
                    "acceptanceEvidenceRef": "identity-acceptance-1",
                },
                "reasonCode": "CUSTOMER_PROFILE_MEMBERSHIP_ACTIVATION_REQUEST",
                "correlationId": "corr-1",
                "idempotencyKey": "activation-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "blocked"
    assert body["activationRequest"]["commandStatus"] == (
        "ACTIVATION_REJECTED_IDENTITY_NOT_ACCEPTED"
    )
    assert body["activationRequest"]["membership"]["membershipRef"] == "membership-1"
    assert body["activationRequest"]["activation"]["acceptedSubjectStatus"] == (
        "ACCEPTED_SUBJECT_MISSING_OR_MISMATCHED"
    )
    assert body["no_invite_delivery_confirmed"] is True
    assert body["no_auth_claim_change_confirmed"] is True
    assert body["no_seat_assignment_confirmed"] is True
    assert body["no_money_movement_confirmed"] is True
    assert "NO_AUTH_PROVIDER_WRITE" in body["guardrails"]
    assert "accepted_subject" in body["redactions"]
    assert "tenantCode" not in body["account"]
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert command_calls[0]["account_id"] == "acct-1"
    assert command_calls[0]["membership_id"] == "membership-1"
    assert command_calls[0]["account_status"] == "ACTIVE"
    assert command_calls[0]["accepted_subject"] == "owner@example.test"
    assert command_calls[0]["acceptance_evidence_ref"] == "identity-acceptance-1"
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["command_payload_hash"]


async def test_referral_saas_membership_activation_rejects_path_scope_mismatch(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-other/memberships/membership-1/activation",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                },
                "activation": {
                    "acceptedSubject": "owner@example.test",
                    "acceptanceEvidenceRef": "identity-acceptance-1",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "activation-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_SCOPE"
    assert detail["no_invite_delivery_confirmed"] is True
    assert detail["no_auth_claim_change_confirmed"] is True
    assert detail["no_seat_assignment_confirmed"] is True


async def test_referral_saas_account_admin_can_request_access_provisioning_boundary(
    monkeypatch,
):
    resolve_calls: list[dict] = []
    command_calls: list[dict] = []

    async def fake_resolve_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context()

    async def fake_request_referral_saas_access_provisioning(**kwargs):
        command_calls.append(kwargs)
        return _access_provisioning_result()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_account_by_external_reference",
        fake_resolve_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "request_referral_saas_access_provisioning",
        fake_request_referral_saas_access_provisioning,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/memberships/membership-1/access-provisioning",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "runtime",
                },
                "provisioning": {
                    "seatType": "ADMIN",
                    "seatAssignmentEvidenceRef": "seat-evidence-1",
                    "authProviderRef": "identity-provider-review-1",
                    "authClaimEvidenceRef": "claims-review-1",
                    "operatorNotes": "Provision account owner seat.",
                },
                "reasonCode": "CUSTOMER_PROFILE_ACCESS_PROVISIONING_REQUEST",
                "correlationId": "corr-1",
                "idempotencyKey": "provisioning-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["accessProvisioning"]["commandStatus"] == (
        "PROVISIONING_REQUEST_RECORDED"
    )
    assert body["accessProvisioning"]["seat"] == {
        "seatType": "ADMIN",
        "seatAssignmentStatus": "SEAT_ASSIGNED",
        "seatRef": "seat-1",
    }
    assert body["accessProvisioning"]["authClaims"]["authClaimStatus"] == (
        "AUTH_CLAIMS_NOT_PROPAGATED"
    )
    assert body["no_invite_delivery_confirmed"] is True
    assert body["no_auth_claim_change_confirmed"] is True
    assert body["no_credential_creation_confirmed"] is True
    assert body["no_campaign_activation_confirmed"] is True
    assert body["no_go_live_change_confirmed"] is True
    assert body["no_money_movement_confirmed"] is True
    assert "AVAILABLE_SEAT_REQUIRED" in body["guardrails"]
    assert "seat_assignment_evidence_ref" in body["redactions"]
    assert "tenantCode" not in body["account"]
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert command_calls[0]["account_id"] == "acct-1"
    assert command_calls[0]["membership_id"] == "membership-1"
    assert command_calls[0]["seat_type"] == "ADMIN"
    assert command_calls[0]["account_status"] == "ACTIVE"
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["command_payload_hash"]


async def test_referral_saas_access_provisioning_rejects_path_scope_mismatch(
    monkeypatch,
):
    async def fake_resolve_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_account_by_external_reference",
        fake_resolve_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-other/memberships/membership-1/access-provisioning",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                },
                "provisioning": {"seatType": "ADMIN"},
                "correlationId": "corr-1",
                "idempotencyKey": "provisioning-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_SCOPE"
    assert detail["no_invite_delivery_confirmed"] is True
    assert detail["no_auth_claim_change_confirmed"] is True
    assert detail["no_credential_creation_confirmed"] is True


async def test_referral_saas_account_admin_can_read_login_completion_readiness(
    monkeypatch,
):
    resolve_calls: list[dict] = []
    readiness_calls: list[dict] = []

    async def fake_resolve_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context()

    async def fake_get_referral_saas_login_completion_readiness(**kwargs):
        readiness_calls.append(kwargs)
        return _login_completion_readiness()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_account_by_external_reference",
        fake_resolve_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_login_completion_readiness",
        fake_get_referral_saas_login_completion_readiness,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/memberships/membership-1/login-completion-readiness",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "runtime",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["loginCompletionReadiness"]["loginCompletionStatus"] == (
        "LOGIN_COMPLETION_READY"
    )
    assert body["loginCompletionReadiness"]["membershipRef"] == "membership-1"
    assert body["no_credential_creation_confirmed"] is True
    assert body["no_auth_claim_change_confirmed"] is True
    assert body["no_campaign_activation_confirmed"] is True
    assert "NO_RAW_CREDENTIAL_STORAGE" in body["guardrails"]
    assert "provider_secret" in body["redactions"]
    assert "tenantCode" not in body["account"]
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert readiness_calls == [
        {
            "account_id": "acct-1",
            "tenant_code": "FNB",
            "account_status": "ACTIVE",
            "tenant_link_status": "ACTIVE",
            "external_reference_status": "ACTIVE",
            "membership_id": "membership-1",
        }
    ]


async def test_referral_saas_account_admin_can_read_identity_login_reconciliation(
    monkeypatch,
):
    resolve_calls: list[dict] = []
    reconciliation_calls: list[dict] = []

    async def fake_resolve_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context()

    async def fake_get_referral_saas_identity_login_reconciliation(**kwargs):
        reconciliation_calls.append(kwargs)
        return _identity_login_reconciliation()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_account_by_external_reference",
        fake_resolve_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_identity_login_reconciliation",
        fake_get_referral_saas_identity_login_reconciliation,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/identity-login-reconciliation",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "runtime",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["identityLoginReconciliation"]["reconciliationStatus"] == (
        "LOGIN_RECONCILIATION_ACTION_REQUIRED"
    )
    assert body["identityLoginReconciliation"]["summary"]["actionRequiredCount"] == 1
    assert body["identityLoginReconciliation"]["people"][0]["steps"][1]["status"] == "DONE"
    assert body["no_credential_creation_confirmed"] is True
    assert body["no_auth_claim_change_confirmed"] is True
    assert body["no_seat_assignment_confirmed"] is True
    assert "READ_ONLY_RECONCILIATION" in body["guardrails"]
    assert "identity_provider_evidence" in body["redactions"]
    assert "tenantCode" not in body["account"]
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert reconciliation_calls == [
        {
            "account_id": "acct-1",
            "tenant_code": "FNB",
            "account_status": "ACTIVE",
            "tenant_link_status": "ACTIVE",
            "external_reference_status": "ACTIVE",
        }
    ]


async def test_referral_saas_account_admin_can_record_login_completion_intent(
    monkeypatch,
):
    resolve_calls: list[dict] = []
    command_calls: list[dict] = []

    async def fake_resolve_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context()

    async def fake_request_referral_saas_login_completion_intent(**kwargs):
        command_calls.append(kwargs)
        return _login_completion_result()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_account_by_external_reference",
        fake_resolve_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "request_referral_saas_login_completion_intent",
        fake_request_referral_saas_login_completion_intent,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/memberships/membership-1/login-completion-intents",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "runtime",
                },
                "loginCompletion": {
                    "intent": "PLATFORM_LOGIN_REQUIRED",
                    "identitySubjectRef": "identity-subject-1",
                    "authProviderRef": "approved-provider-1",
                    "seatEvidenceRef": "seat-1",
                    "permissionProfile": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                    "operatorReason": "Owner needs Amplifi platform login.",
                },
                "reasonCode": "CUSTOMER_PROFILE_LOGIN_COMPLETION_INTENT",
                "correlationId": "corr-1",
                "idempotencyKey": "login-completion-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["loginCompletionIntent"]["commandStatus"] == (
        "LOGIN_COMPLETION_RECORDED"
    )
    assert body["loginCompletionIntent"]["loginCompletion"]["authClaimStatus"] == (
        "AUTH_CLAIMS_NOT_PROPAGATED"
    )
    assert body["no_invite_delivery_confirmed"] is True
    assert body["no_credential_creation_confirmed"] is True
    assert body["no_auth_claim_change_confirmed"] is True
    assert body["no_campaign_activation_confirmed"] is True
    assert "NO_TOKEN_EXPOSURE" in body["guardrails"]
    assert "raw_auth_claims" in body["redactions"]
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert command_calls[0]["account_id"] == "acct-1"
    assert command_calls[0]["membership_id"] == "membership-1"
    assert command_calls[0]["intent"] == "PLATFORM_LOGIN_REQUIRED"
    assert command_calls[0]["auth_provider_ref"] == "approved-provider-1"
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["command_payload_hash"]


async def test_referral_saas_login_completion_rejects_path_scope_mismatch(
    monkeypatch,
):
    async def fake_resolve_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_account_by_external_reference",
        fake_resolve_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-other/memberships/membership-1/login-completion-intents",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                },
                "loginCompletion": {"intent": "LOGIN_NOT_REQUIRED"},
                "correlationId": "corr-1",
                "idempotencyKey": "login-completion-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_SCOPE"
    assert detail["no_credential_creation_confirmed"] is True
    assert detail["no_auth_claim_change_confirmed"] is True
    assert detail["no_campaign_activation_confirmed"] is True


async def test_referral_saas_login_completion_rejects_unsafe_payload(
    monkeypatch,
):
    async def fake_resolve_account_by_external_reference(**kwargs):
        return _context()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_account_by_external_reference",
        fake_resolve_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/memberships/membership-1/login-completion-intents",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                },
                "loginCompletion": {
                    "intent": "PLATFORM_LOGIN_REQUIRED",
                    "authClaims": {"role": "admin"},
                },
                "correlationId": "corr-1",
                "idempotencyKey": "login-completion-unsafe",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert detail["no_credential_creation_confirmed"] is True
    assert detail["no_auth_claim_change_confirmed"] is True


async def test_referral_saas_account_admin_can_read_technical_setup_readiness(
    monkeypatch,
):
    resolve_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context(
            account_status="PENDING_ONBOARDING",
            tenant_link_status="PENDING_SETUP",
            reference_status="ACTIVE",
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        "services.channel_readiness_service.get_settings",
        lambda: SimpleNamespace(
            channel_email_provider_url=None,
            channel_email_provider_secret=None,
            channel_whatsapp_provider_url=None,
            channel_whatsapp_provider_secret=None,
            channel_sms_provider_url=None,
            channel_sms_provider_secret=None,
            channel_ussd_provider_url=None,
            channel_ussd_provider_secret=None,
        ),
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/technical-setup-readiness",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["account"]["accountCode"] == "ACCT_FNB"
    assert "tenantCode" not in body["account"]
    assert (
        body["technicalSetupReadiness"]["overallStatus"]
        == "PROVIDER_CONFIGURATION_REQUIRED"
    )
    assert body["technicalSetupReadiness"]["providerStatus"] == "ATTENTION"
    assert body["technicalSetupReadiness"]["capabilities"][0]["missingChannels"] == [
        "EMAIL"
    ]
    assert body["technicalSetupReadiness"]["capabilities"][0][
        "missingApprovalChannels"
    ] == []
    assert body["technicalSetupReadiness"]["channelSummary"][
        "approvedInviteProviderCount"
    ] == 0
    assert body["technicalSetupReadiness"]["noCredentialCreationConfirmed"] is True
    assert body["technicalSetupReadiness"]["noWebhookDispatchConfirmed"] is True
    assert body["technicalSetupReadiness"]["noInviteDeliveryConfirmed"] is True
    assert body["technicalSetupReadiness"]["noMembershipActivationConfirmed"] is True
    assert body["technicalSetupReadiness"]["noMoneyMovementConfirmed"] is True
    assert "NO_PROVIDER_SECRET_EXPOSURE" in body["technicalSetupReadiness"]["guardrails"]
    assert "provider_secret" in body["technicalSetupReadiness"]["redactions"]
    assert body["no_credential_creation_confirmed"] is True
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]


async def test_referral_saas_technical_setup_readiness_rejects_path_scope_mismatch(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-other/technical-setup-readiness",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_SCOPE"


async def test_referral_saas_account_reader_can_read_commercial_entitlement(
    monkeypatch,
):
    resolve_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/commercial-entitlement",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    entitlement = body["commercialEntitlement"]
    assert body["status"] == "ok"
    assert body["account"]["accountCode"] == "ACCT_FNB"
    assert "tenantCode" not in body["account"]
    assert "tenant_code" not in str(body["account"])
    assert entitlement["overallStatus"] == "COMMERCIAL_SETUP_REQUIRED"
    assert entitlement["launchAllowed"] is False
    assert entitlement["productionActivationBlocked"] is True
    assert entitlement["plan"]["contractSource"] == "NOT_CONFIGURED"
    assert entitlement["noBillingRecordCreatedConfirmed"] is True
    assert entitlement["noInvoiceCreatedConfirmed"] is True
    assert entitlement["noPaymentOrMoneyMovementConfirmed"] is True
    assert entitlement["noDlaasFinanceScopeConfirmed"] is True
    commercial_finance_boundary = entitlement["commercialFinanceBoundary"]
    assert commercial_finance_boundary["scope"] == "SEPARATELY_CONTRACTED"
    assert commercial_finance_boundary["h1EntitlementFields"] == [
        "planCode",
        "planName",
        "contractSource",
        "launchAllowed",
        "productionActivationBlocked",
        "referenceLimits",
    ]
    assert {
        "billingAccounts",
        "subscriptions",
        "invoices",
        "payments",
        "payouts",
        "funding",
        "settlement",
        "walletLedger",
        "commissionLedger",
        "treasuryMovement",
    } <= set(commercial_finance_boundary["h1DeferredCapabilities"])
    assert {
        "sponsorBilling",
        "fundingOperations",
        "settlementBatches",
        "commissionSettlement",
        "payoutExecution",
        "walletLedgerMovement",
    } <= set(commercial_finance_boundary["dlaasFinanceStartsAt"])
    assert body["no_billing_record_created_confirmed"] is True
    assert body["no_invoice_created_confirmed"] is True
    assert body["no_payment_or_money_movement_confirmed"] is True
    assert body["no_dlaas_finance_scope_confirmed"] is True
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]


async def test_referral_saas_commercial_entitlement_rejects_path_scope_mismatch(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-other/commercial-entitlement",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_SCOPE"


async def test_referral_saas_account_reader_can_read_production_activation(
    monkeypatch,
):
    resolve_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    async def fake_get_referral_saas_membership_activation_readiness(**kwargs):
        return SimpleNamespace(overall_status="ACCESS_READY")

    def fake_build_referral_saas_technical_setup_readiness(**kwargs):
        return SimpleNamespace(overall_status="READY")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_membership_activation_readiness",
        fake_get_referral_saas_membership_activation_readiness,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "build_referral_saas_technical_setup_readiness",
        fake_build_referral_saas_technical_setup_readiness,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/production-activation",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    activation = body["productionActivation"]
    assert body["status"] == "ok"
    assert body["account"]["accountCode"] == "ACCT_FNB"
    assert activation["launchAllowed"] is False
    assert activation["decisionStatus"] == "PRODUCTION_ACTIVATION_BLOCKED"
    assert "CAMPAIGN_READINESS" in activation["disabledReasons"]
    assert "COMMERCIAL_ENTITLEMENT" in activation["disabledReasons"]
    assert "EVIDENCE_FRESHNESS" in activation["disabledReasons"]
    assert body["no_ui_only_activation_confirmed"] is True
    assert body["no_campaign_activation_confirmed"] is True
    assert body["no_go_live_action_confirmed"] is True
    assert body["no_billing_or_money_movement_confirmed"] is True
    assert "tenantCode" not in body["account"]
    assert "tenant_code" not in str(body["account"])
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]


async def test_referral_saas_account_admin_can_read_integration_configuration(
    monkeypatch,
):
    read_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    class FakeIntegrationConfiguration:
        def to_safe_dict(self):
            return {
                "configurationRef": "config-1",
                "accountRef": "acct-1",
                "configurationStatus": "INTEGRATION_CONFIGURATION_SAVED",
                "apiEnvironment": {"environment": "SANDBOX"},
                "webhookIntent": {"eventCategories": ["REFERRAL"]},
                "messageProviders": {"channels": ["EMAIL"]},
                "safeSetupPosture": {"blockers": []},
                "redactions": ["provider_secret"],
            }

    async def fake_get_referral_saas_integration_configuration(**kwargs):
        read_calls.append(kwargs)
        return FakeIntegrationConfiguration()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_configuration",
        fake_get_referral_saas_integration_configuration,
    )
    monkeypatch.setattr(
        "services.channel_readiness_service.get_settings",
        lambda: SimpleNamespace(
            channel_email_provider_url=None,
            channel_email_provider_secret=None,
            channel_whatsapp_provider_url=None,
            channel_whatsapp_provider_secret=None,
            channel_sms_provider_url=None,
            channel_sms_provider_secret=None,
            channel_ussd_provider_url=None,
            channel_ussd_provider_secret=None,
        ),
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/integrations/configuration",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["integrationConfiguration"]["configurationRef"] == "config-1"
    assert body["integrationConfiguration"]["apiEnvironment"] == {
        "environment": "SANDBOX"
    }
    assert "tenantCode" not in body["account"]
    assert body["no_secret_or_credential_storage_confirmed"] is True
    assert body["no_webhook_dispatch_confirmed"] is True
    assert read_calls == [{"account_id": "acct-1"}]


async def test_referral_saas_account_admin_can_read_integration_execution_readiness(
    monkeypatch,
):
    read_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    class FakeIntegrationConfiguration:
        configuration_ref = "config-1"
        configuration_status = "INTEGRATION_CONFIGURATION_SAVED"
        api_environment = {
            "environment": "SANDBOX",
            "authMethod": "API_KEY",
            "useCases": ["CAMPAIGN_READ"],
        }
        webhook_intent = {
            "callbackUrl": "https://example.com/referral-events",
            "eventCategories": ["REFERRAL"],
        }
        message_providers = {
            "channels": ["EMAIL"],
            "providerRefs": ["approved-email-provider"],
        }

        def to_safe_dict(self):
            return {
                "configurationRef": self.configuration_ref,
                "accountRef": "acct-1",
                "configurationStatus": self.configuration_status,
                "apiEnvironment": self.api_environment,
                "webhookIntent": self.webhook_intent,
                "messageProviders": self.message_providers,
                "safeSetupPosture": {"blockers": []},
                "redactions": ["provider_secret"],
            }

    async def fake_get_referral_saas_integration_configuration(**kwargs):
        read_calls.append(kwargs)
        return FakeIntegrationConfiguration()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_configuration",
        fake_get_referral_saas_integration_configuration,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/integrations/execution-readiness",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    readiness = body["integrationExecutionReadiness"]
    assert readiness["executionStatus"] == "INTEGRATION_EXECUTION_READY"
    assert readiness["blockers"] == []
    assert {action["actionRef"] for action in readiness["readyActions"]} == {
        "API_ACCESS_VERIFICATION",
        "WEBHOOK_TEST_DISPATCH",
        "MESSAGE_PROVIDER_TEST",
        "CREDENTIAL_REQUEST",
    }
    assert body["integrationConfiguration"]["configurationRef"] == "config-1"
    assert body["no_credential_lifecycle_confirmed"] is True
    assert body["no_webhook_dispatch_confirmed"] is True
    assert body["no_message_provider_delivery_confirmed"] is True
    assert body["no_billing_or_money_movement_confirmed"] is True
    assert read_calls == [{"account_id": "acct-1"}]


async def test_referral_saas_account_execution_readiness_blocks_missing_configuration(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    async def fake_get_referral_saas_integration_configuration(**kwargs):
        return None

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_configuration",
        fake_get_referral_saas_integration_configuration,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/integrations/execution-readiness",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    readiness = body["integrationExecutionReadiness"]
    assert (
        readiness["executionStatus"]
        == "INTEGRATION_EXECUTION_BLOCKED_CONFIGURATION_MISSING"
    )
    assert readiness["blockers"][0]["code"] == "CONFIGURATION_MISSING"
    assert body["integrationConfiguration"] is None
    assert body["no_webhook_dispatch_confirmed"] is True
    assert body["no_message_provider_delivery_confirmed"] is True


async def test_referral_saas_account_provider_vault_readiness_blocks_missing_request(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    class FakeIntegrationConfiguration:
        configuration_ref = "config-1"
        configuration_status = "INTEGRATION_CONFIGURATION_SAVED"
        api_environment = {
            "environment": "SANDBOX",
            "authMethod": "API_KEY",
            "useCases": ["CAMPAIGN_READ"],
        }
        webhook_intent = {}
        message_providers = {"channels": ["EMAIL"], "providerRefs": ["provider-1"]}

        def to_safe_dict(self):
            return {"configurationRef": self.configuration_ref}

    async def fake_get_referral_saas_integration_configuration(**kwargs):
        return FakeIntegrationConfiguration()

    async def fake_list_referral_saas_integration_credential_requests(**kwargs):
        return []

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_configuration",
        fake_get_referral_saas_integration_configuration,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "list_referral_saas_integration_credential_requests",
        fake_list_referral_saas_integration_credential_requests,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/integrations/provider-vault/readiness",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    readiness = body["providerVaultReadiness"]
    assert (
        readiness["readinessStatus"]
        == "PROVIDER_VAULT_BLOCKED_REQUEST_NOT_APPROVED"
    )
    assert readiness["credentialRequests"] == []
    assert readiness["blockers"][0]["code"] == "CREDENTIAL_REQUEST_NOT_APPROVED"
    assert body["no_vault_write_confirmed"] is True
    assert body["no_provider_call_confirmed"] is True


async def test_referral_saas_account_provider_vault_readiness_blocks_unapproved_request(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    configuration = SimpleNamespace(
        configuration_ref="config-1",
        configuration_status="INTEGRATION_CONFIGURATION_SAVED",
        api_environment={
            "environment": "SANDBOX",
            "authMethod": "API_KEY",
            "useCases": ["CAMPAIGN_READ"],
        },
        webhook_intent={},
        message_providers={"channels": ["EMAIL"], "providerRefs": ["provider-1"]},
        to_safe_dict=lambda: {"configurationRef": "config-1"},
    )
    credential_request = SimpleNamespace(
        credential_request_ref="credreq-1",
        configuration_ref="config-1",
        review_status="READY_FOR_REVIEW",
        request_type="API_KEY_CREATE",
        capability="REFERRAL_SAAS_API_ACCESS",
        environment="SANDBOX",
    )

    async def fake_get_referral_saas_integration_configuration(**kwargs):
        return configuration

    async def fake_list_referral_saas_integration_credential_requests(**kwargs):
        return [credential_request]

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_configuration",
        fake_get_referral_saas_integration_configuration,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "list_referral_saas_integration_credential_requests",
        fake_list_referral_saas_integration_credential_requests,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/integrations/provider-vault/readiness",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    readiness = body["providerVaultReadiness"]
    assert (
        readiness["readinessStatus"]
        == "PROVIDER_VAULT_BLOCKED_REQUEST_NOT_APPROVED"
    )
    item = readiness["credentialRequests"][0]
    assert item["readyForExecution"] is False
    assert item["blockers"][0]["code"] == "CREDENTIAL_REQUEST_NOT_APPROVED"
    assert body["no_credential_creation_confirmed"] is True


async def test_referral_saas_account_provider_vault_readiness_blocks_config_mismatch(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    configuration = SimpleNamespace(
        configuration_ref="config-2",
        configuration_status="INTEGRATION_CONFIGURATION_SAVED",
        api_environment={
            "environment": "SANDBOX",
            "authMethod": "API_KEY",
            "useCases": ["CAMPAIGN_READ"],
        },
        webhook_intent={},
        message_providers={"channels": ["EMAIL"], "providerRefs": ["provider-1"]},
        to_safe_dict=lambda: {"configurationRef": "config-2"},
    )
    credential_request = SimpleNamespace(
        credential_request_ref="credreq-1",
        configuration_ref="config-1",
        review_status="REVIEW_APPROVED",
        request_type="API_KEY_CREATE",
        capability="REFERRAL_SAAS_API_ACCESS",
        environment="SANDBOX",
    )

    async def fake_get_referral_saas_integration_configuration(**kwargs):
        return configuration

    async def fake_list_referral_saas_integration_credential_requests(**kwargs):
        return [credential_request]

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_configuration",
        fake_get_referral_saas_integration_configuration,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "list_referral_saas_integration_credential_requests",
        fake_list_referral_saas_integration_credential_requests,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/integrations/provider-vault/readiness",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    readiness = body["providerVaultReadiness"]
    assert (
        readiness["readinessStatus"]
        == "PROVIDER_VAULT_BLOCKED_REQUEST_VERSION_MISMATCH"
    )
    assert (
        readiness["credentialRequests"][0]["blockers"][0]["code"]
        == "CREDENTIAL_REQUEST_VERSION_MISMATCH"
    )


async def test_referral_saas_account_provider_vault_readiness_returns_ready_state(
    monkeypatch,
):
    calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    configuration = SimpleNamespace(
        configuration_ref="config-1",
        configuration_status="INTEGRATION_CONFIGURATION_SAVED",
        api_environment={
            "environment": "SANDBOX",
            "authMethod": "API_KEY",
            "useCases": ["CAMPAIGN_READ"],
        },
        webhook_intent={
            "callbackUrl": "https://example.com/referral-events",
            "eventCategories": ["REFERRAL"],
        },
        message_providers={"channels": ["EMAIL"], "providerRefs": ["provider-1"]},
        to_safe_dict=lambda: {"configurationRef": "config-1"},
    )
    credential_request = SimpleNamespace(
        credential_request_ref="credreq-1",
        configuration_ref="config-1",
        review_status="REVIEW_APPROVED",
        request_type="API_KEY_CREATE",
        capability="REFERRAL_SAAS_API_ACCESS",
        environment="SANDBOX",
    )

    async def fake_get_referral_saas_integration_configuration(**kwargs):
        calls.append({"configuration": kwargs})
        return configuration

    async def fake_list_referral_saas_integration_credential_requests(**kwargs):
        calls.append({"credential_requests": kwargs})
        return [credential_request]

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_configuration",
        fake_get_referral_saas_integration_configuration,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "list_referral_saas_integration_credential_requests",
        fake_list_referral_saas_integration_credential_requests,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/integrations/provider-vault/readiness",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    readiness = body["providerVaultReadiness"]
    assert readiness["readinessStatus"] == "PROVIDER_VAULT_EXECUTION_READY"
    assert readiness["blockers"] == []
    assert readiness["credentialRequests"][0]["readyForExecution"] is True
    assert readiness["credentialRequests"][0]["readinessStatus"] == (
        "PROVIDER_VAULT_EXECUTION_READY"
    )
    assert readiness["readyActions"][0]["actionRef"] == "PROVIDER_VAULT_EXECUTOR_HANDOFF"
    assert "provider_secret" in body["redactions"]
    assert "vault_reference" in body["redactions"]
    assert body["no_vault_write_confirmed"] is True
    assert body["no_provider_call_confirmed"] is True
    assert calls == [
        {"configuration": {"account_id": "acct-1"}},
        {"credential_requests": {"account_id": "acct-1", "limit": 100}},
    ]


async def test_referral_saas_account_admin_can_validate_integration_configuration(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/configuration/validate",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "apiEnvironment": {
                    "environment": "SANDBOX",
                    "authMethod": "API_KEY",
                    "useCases": ["CAMPAIGN_READ"],
                },
                "webhookIntent": {
                    "callbackUrl": "https://example.com/referral-events",
                    "eventCategories": ["REFERRAL"],
                },
                "messageProviders": {
                    "channels": ["EMAIL"],
                    "providerRefs": ["approved-email-provider"],
                },
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["validation"]["commandStatus"] == "INTEGRATION_CONFIGURATION_VALIDATED"
    assert body["validation"]["safeSetupPosture"]["blockers"] == []
    assert body["no_configuration_saved_confirmed"] is True
    assert body["no_credential_creation_confirmed"] is True
    assert body["no_billing_or_money_movement_confirmed"] is True


async def test_referral_saas_account_admin_can_save_integration_configuration(
    monkeypatch,
):
    save_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    class FakeSaveResult:
        def to_safe_dict(self):
            return {
                "commandStatus": "INTEGRATION_CONFIGURATION_SAVED",
                "configuration": {
                    "configurationRef": "config-1",
                    "configurationStatus": "INTEGRATION_CONFIGURATION_SAVED",
                },
                "validation": {
                    "commandStatus": "INTEGRATION_CONFIGURATION_VALIDATED"
                },
                "idempotency": {"status": "INTEGRATION_CONFIGURATION_SAVED"},
                "audit": {"accountAuditEventId": "audit-1"},
            }

    async def fake_upsert_referral_saas_integration_configuration(**kwargs):
        save_calls.append(kwargs)
        return FakeSaveResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "upsert_referral_saas_integration_configuration",
        fake_upsert_referral_saas_integration_configuration,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.put(
            "/v1/referral-saas/accounts/acct-1/integrations/configuration",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "apiEnvironment": {
                    "environment": "SANDBOX",
                    "authMethod": "API_KEY",
                    "useCases": ["CAMPAIGN_READ"],
                },
                "webhookIntent": {
                    "callbackUrl": "https://example.com/referral-events",
                    "eventCategories": ["REFERRAL"],
                },
                "messageProviders": {
                    "channels": ["EMAIL"],
                    "providerRefs": ["approved-email-provider"],
                },
                "reasonCode": "CUSTOMER_INTEGRATION_CONFIGURATION",
                "correlationId": "corr-1",
                "idempotencyKey": "integration-config-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert (
        body["integrationConfigurationResult"]["commandStatus"]
        == "INTEGRATION_CONFIGURATION_SAVED"
    )
    assert body["no_secret_or_credential_storage_confirmed"] is True
    assert body["no_campaign_activation_confirmed"] is True
    assert save_calls[0]["account_id"] == "acct-1"
    assert save_calls[0]["tenant_code"] == "FNB"
    assert save_calls[0]["correlation_id"] == "corr-1"
    assert save_calls[0]["actor_role"] == "ADMIN"


async def test_referral_saas_account_integration_configuration_rejects_unsafe_payload(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/configuration/validate",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "apiEnvironment": {"environment": "SANDBOX", "apiKey": "secret"},
                "webhookIntent": {},
                "messageProviders": {},
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert detail["no_secret_or_credential_storage_confirmed"] is True
    assert detail["no_webhook_dispatch_confirmed"] is True


async def test_referral_saas_account_integration_configuration_idempotency_conflict(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    async def fake_upsert_referral_saas_integration_configuration(**kwargs):
        raise IntegrationConfigurationIdempotencyConflict(
            "Idempotency key was reused with different integrations configuration content."
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "upsert_referral_saas_integration_configuration",
        fake_upsert_referral_saas_integration_configuration,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.put(
            "/v1/referral-saas/accounts/acct-1/integrations/configuration",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "apiEnvironment": {"environment": "SANDBOX"},
                "webhookIntent": {},
                "messageProviders": {},
                "correlationId": "corr-1",
                "idempotencyKey": "integration-config-1",
            },
        )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "IDEMPOTENCY_CONFLICT"
    assert detail["no_credential_creation_confirmed"] is True
    assert detail["no_billing_or_money_movement_confirmed"] is True
    assert detail["no_invite_delivery_confirmed"] is True
    assert detail["no_auth_claim_change_confirmed"] is True


async def test_referral_saas_account_admin_can_record_api_access_verification(
    monkeypatch,
):
    verification_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    class FakeIntegrationConfiguration:
        configuration_ref = "config-1"
        configuration_status = "INTEGRATION_CONFIGURATION_SAVED"
        api_environment = {
            "environment": "SANDBOX",
            "authMethod": "API_KEY",
            "useCases": ["CAMPAIGN_READ"],
        }
        webhook_intent = {}
        message_providers = {}

        def to_safe_dict(self):
            return {
                "configurationRef": self.configuration_ref,
                "configurationStatus": self.configuration_status,
                "apiEnvironment": self.api_environment,
                "webhookIntent": self.webhook_intent,
                "messageProviders": self.message_providers,
            }

    class FakeVerificationResult:
        def to_safe_dict(self):
            return {
                "verificationStatus": "API_ACCESS_VERIFICATION_RECORDED",
                "configurationRef": "config-1",
                "accountRef": "acct-1",
                "apiEnvironment": "SANDBOX",
                "verifiedUseCases": ["CAMPAIGN_READ"],
                "idempotency": {"status": "API_ACCESS_VERIFICATION_RECORDED"},
                "audit": {"accountAuditEventId": "audit-1"},
                "noCredentialCreationConfirmed": True,
                "noWebhookDispatchConfirmed": True,
            }

    async def fake_get_referral_saas_integration_configuration(**kwargs):
        return FakeIntegrationConfiguration()

    async def fake_record_referral_saas_api_access_verification(**kwargs):
        verification_calls.append(kwargs)
        return FakeVerificationResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_configuration",
        fake_get_referral_saas_integration_configuration,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "record_referral_saas_api_access_verification",
        fake_record_referral_saas_api_access_verification,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/api-access/verification",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "verification": {"notes": "Verified saved API setup evidence."},
                "reasonCode": "CUSTOMER_API_ACCESS_VERIFICATION",
                "correlationId": "corr-1",
                "idempotencyKey": "api-access-verify-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert (
        body["integrationApiAccessVerification"]["verificationStatus"]
        == "API_ACCESS_VERIFICATION_RECORDED"
    )
    assert body["no_credential_creation_confirmed"] is True
    assert body["no_webhook_dispatch_confirmed"] is True
    assert body["no_message_provider_delivery_confirmed"] is True
    assert verification_calls[0]["account_id"] == "acct-1"
    assert verification_calls[0]["tenant_code"] == "FNB"
    assert verification_calls[0]["correlation_id"] == "corr-1"
    assert verification_calls[0]["actor_role"] == "ADMIN"


async def test_referral_saas_account_api_access_verification_requires_command_scope(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        raise AssertionError("account should not resolve without idempotency metadata")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/api-access/verification",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "correlationId": "corr-1",
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "validation_error"
    assert detail["no_verification_recorded_confirmed"] is True


async def test_referral_saas_account_api_access_verification_rejects_unsafe_payload(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        raise AssertionError("unsafe payload should fail before account lookup")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/api-access/verification",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "verification": {"apiKey": "secret"},
                "reasonCode": "CUSTOMER_API_ACCESS_VERIFICATION",
                "correlationId": "corr-1",
                "idempotencyKey": "api-access-verify-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert detail["no_credential_creation_confirmed"] is True
    assert detail["no_webhook_dispatch_confirmed"] is True


async def test_referral_saas_account_api_access_verification_idempotency_conflict(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    async def fake_get_referral_saas_integration_configuration(**kwargs):
        return SimpleNamespace(configuration_ref="config-1")

    async def fake_record_referral_saas_api_access_verification(**kwargs):
        raise IntegrationConfigurationIdempotencyConflict(
            "Idempotency key was reused with different API-access verification content."
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_configuration",
        fake_get_referral_saas_integration_configuration,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "record_referral_saas_api_access_verification",
        fake_record_referral_saas_api_access_verification,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/api-access/verification",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "verification": {"notes": "Changed verification evidence."},
                "correlationId": "corr-1",
                "idempotencyKey": "api-access-verify-1",
            },
        )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "IDEMPOTENCY_CONFLICT"
    assert detail["no_credential_creation_confirmed"] is True
    assert detail["no_auth_claim_change_confirmed"] is True


async def test_referral_saas_account_admin_can_record_webhook_test_dispatch(
    monkeypatch,
):
    dispatch_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    class FakeIntegrationConfiguration:
        configuration_ref = "config-1"
        configuration_status = "INTEGRATION_CONFIGURATION_SAVED"
        api_environment = {}
        webhook_intent = {
            "callbackUrl": "https://customer.example/webhooks/referral-saas",
            "eventCategories": ["REFERRAL", "ATTRIBUTION"],
        }
        message_providers = {}

        def to_safe_dict(self):
            return {
                "configurationRef": self.configuration_ref,
                "configurationStatus": self.configuration_status,
                "apiEnvironment": self.api_environment,
                "webhookIntent": self.webhook_intent,
                "messageProviders": self.message_providers,
            }

    class FakeDispatchResult:
        def to_safe_dict(self):
            return {
                "dispatchStatus": "WEBHOOK_TEST_DISPATCH_RECORDED",
                "configurationRef": "config-1",
                "accountRef": "acct-1",
                "callbackUrlPresent": True,
                "eventCategories": ["REFERRAL", "ATTRIBUTION"],
                "idempotency": {"status": "WEBHOOK_TEST_DISPATCH_RECORDED"},
                "audit": {"accountAuditEventId": "audit-1"},
                "noWebhookDispatchConfirmed": True,
                "noCredentialCreationConfirmed": True,
            }

    async def fake_get_referral_saas_integration_configuration(**kwargs):
        return FakeIntegrationConfiguration()

    async def fake_record_referral_saas_webhook_test_dispatch(**kwargs):
        dispatch_calls.append(kwargs)
        return FakeDispatchResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_configuration",
        fake_get_referral_saas_integration_configuration,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "record_referral_saas_webhook_test_dispatch",
        fake_record_referral_saas_webhook_test_dispatch,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/webhooks/test-dispatch",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "webhookTest": {"notes": "Recorded signed callback test evidence."},
                "reasonCode": "CUSTOMER_WEBHOOK_TEST_DISPATCH",
                "correlationId": "corr-1",
                "idempotencyKey": "webhook-test-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert (
        body["integrationWebhookTestDispatch"]["dispatchStatus"]
        == "WEBHOOK_TEST_DISPATCH_RECORDED"
    )
    assert body["no_webhook_dispatch_confirmed"] is True
    assert body["no_credential_creation_confirmed"] is True
    assert body["no_message_provider_delivery_confirmed"] is True
    assert dispatch_calls[0]["account_id"] == "acct-1"
    assert dispatch_calls[0]["tenant_code"] == "FNB"
    assert dispatch_calls[0]["correlation_id"] == "corr-1"
    assert dispatch_calls[0]["actor_role"] == "ADMIN"


async def test_referral_saas_account_webhook_test_dispatch_requires_command_scope(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        raise AssertionError("account should not resolve without idempotency metadata")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/webhooks/test-dispatch",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "correlationId": "corr-1",
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "validation_error"
    assert detail["no_webhook_test_recorded_confirmed"] is True


async def test_referral_saas_account_webhook_test_dispatch_rejects_unsafe_payload(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        raise AssertionError("unsafe payload should fail before account lookup")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/webhooks/test-dispatch",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "webhookTest": {"signingSecret": "secret"},
                "reasonCode": "CUSTOMER_WEBHOOK_TEST_DISPATCH",
                "correlationId": "corr-1",
                "idempotencyKey": "webhook-test-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert detail["no_credential_creation_confirmed"] is True
    assert detail["no_webhook_dispatch_confirmed"] is True


async def test_referral_saas_account_webhook_test_dispatch_idempotency_conflict(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    async def fake_get_referral_saas_integration_configuration(**kwargs):
        return SimpleNamespace(configuration_ref="config-1")

    async def fake_record_referral_saas_webhook_test_dispatch(**kwargs):
        raise IntegrationConfigurationIdempotencyConflict(
            "Idempotency key was reused with different webhook test-dispatch content."
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_configuration",
        fake_get_referral_saas_integration_configuration,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "record_referral_saas_webhook_test_dispatch",
        fake_record_referral_saas_webhook_test_dispatch,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/webhooks/test-dispatch",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "webhookTest": {"notes": "Changed webhook evidence."},
                "correlationId": "corr-1",
                "idempotencyKey": "webhook-test-1",
            },
        )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "IDEMPOTENCY_CONFLICT"
    assert detail["no_credential_creation_confirmed"] is True
    assert detail["no_auth_claim_change_confirmed"] is True


async def test_referral_saas_account_admin_can_record_message_provider_test(
    monkeypatch,
):
    message_test_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    class FakeIntegrationConfiguration:
        configuration_ref = "config-1"
        configuration_status = "INTEGRATION_CONFIGURATION_SAVED"
        api_environment = {}
        webhook_intent = {}
        message_providers = {
            "channels": ["EMAIL", "SMS"],
            "providerRefs": ["approved-email-provider"],
        }

        def to_safe_dict(self):
            return {
                "configurationRef": self.configuration_ref,
                "configurationStatus": self.configuration_status,
                "apiEnvironment": self.api_environment,
                "webhookIntent": self.webhook_intent,
                "messageProviders": self.message_providers,
            }

    class FakeMessageProviderTestResult:
        def to_safe_dict(self):
            return {
                "testStatus": "MESSAGE_PROVIDER_TEST_RECORDED",
                "configurationRef": "config-1",
                "accountRef": "acct-1",
                "channels": ["EMAIL", "SMS"],
                "providerRefs": ["approved-email-provider"],
                "idempotency": {"status": "MESSAGE_PROVIDER_TEST_RECORDED"},
                "audit": {"accountAuditEventId": "audit-1"},
                "noMessageProviderDeliveryConfirmed": True,
                "noCredentialCreationConfirmed": True,
            }

    async def fake_get_referral_saas_integration_configuration(**kwargs):
        return FakeIntegrationConfiguration()

    async def fake_record_referral_saas_message_provider_test(**kwargs):
        message_test_calls.append(kwargs)
        return FakeMessageProviderTestResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_configuration",
        fake_get_referral_saas_integration_configuration,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "record_referral_saas_message_provider_test",
        fake_record_referral_saas_message_provider_test,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/message-providers/test-check",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "messageProviderTest": {
                    "notes": "Recorded provider readiness evidence."
                },
                "reasonCode": "CUSTOMER_MESSAGE_PROVIDER_TEST",
                "correlationId": "corr-1",
                "idempotencyKey": "message-provider-test-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert (
        body["integrationMessageProviderTest"]["testStatus"]
        == "MESSAGE_PROVIDER_TEST_RECORDED"
    )
    assert body["no_message_provider_delivery_confirmed"] is True
    assert body["no_credential_creation_confirmed"] is True
    assert body["no_webhook_dispatch_confirmed"] is True
    assert message_test_calls[0]["account_id"] == "acct-1"
    assert message_test_calls[0]["tenant_code"] == "FNB"
    assert message_test_calls[0]["correlation_id"] == "corr-1"
    assert message_test_calls[0]["actor_role"] == "ADMIN"


async def test_referral_saas_account_message_provider_test_requires_command_scope(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        raise AssertionError("account should not resolve without idempotency metadata")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/message-providers/test-check",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "correlationId": "corr-1",
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "validation_error"
    assert detail["no_message_provider_test_recorded_confirmed"] is True


async def test_referral_saas_account_message_provider_test_rejects_unsafe_payload(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        raise AssertionError("unsafe payload should fail before account lookup")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/message-providers/test-check",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "messageProviderTest": {"rawRecipient": "+27000000000"},
                "reasonCode": "CUSTOMER_MESSAGE_PROVIDER_TEST",
                "correlationId": "corr-1",
                "idempotencyKey": "message-provider-test-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert detail["no_credential_creation_confirmed"] is True
    assert detail["no_webhook_dispatch_confirmed"] is True


async def test_referral_saas_account_message_provider_test_idempotency_conflict(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    async def fake_get_referral_saas_integration_configuration(**kwargs):
        return SimpleNamespace(configuration_ref="config-1")

    async def fake_record_referral_saas_message_provider_test(**kwargs):
        raise IntegrationConfigurationIdempotencyConflict(
            "Idempotency key was reused with different message-provider test content."
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_configuration",
        fake_get_referral_saas_integration_configuration,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "record_referral_saas_message_provider_test",
        fake_record_referral_saas_message_provider_test,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/message-providers/test-check",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "messageProviderTest": {"notes": "Changed message evidence."},
                "correlationId": "corr-1",
                "idempotencyKey": "message-provider-test-1",
            },
        )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "IDEMPOTENCY_CONFLICT"
    assert detail["no_credential_creation_confirmed"] is True
    assert detail["no_auth_claim_change_confirmed"] is True


async def test_referral_saas_account_admin_can_create_integration_credential_request(
    monkeypatch,
):
    request_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    class FakeIntegrationConfiguration:
        configuration_ref = "config-1"
        configuration_status = "INTEGRATION_CONFIGURATION_SAVED"
        api_environment = {
            "environment": "SANDBOX",
            "authMethod": "API_KEY",
            "useCases": ["CAMPAIGN_READ"],
        }
        webhook_intent = {}
        message_providers = {}

        def to_safe_dict(self):
            return {
                "configurationRef": self.configuration_ref,
                "configurationStatus": self.configuration_status,
                "apiEnvironment": self.api_environment,
                "webhookIntent": self.webhook_intent,
                "messageProviders": self.message_providers,
            }

    class FakeCredentialRequestResult:
        def to_safe_dict(self):
            return {
                "commandStatus": "INTEGRATION_CREDENTIAL_REQUEST_RECORDED",
                "credentialRequest": {
                    "credentialRequestRef": "credreq-1",
                    "requestType": "API_KEY_CREATE",
                    "capability": "REFERRAL_SAAS_API_ACCESS",
                    "reviewStatus": "READY_FOR_REVIEW",
                },
                "idempotency": {"status": "INTEGRATION_CREDENTIAL_REQUEST_RECORDED"},
                "audit": {"accountAuditEventId": "audit-1"},
                "noCredentialCreationConfirmed": True,
                "noVaultWriteConfirmed": True,
            }

    async def fake_get_referral_saas_integration_configuration(**kwargs):
        return FakeIntegrationConfiguration()

    async def fake_create_referral_saas_integration_credential_request(**kwargs):
        request_calls.append(kwargs)
        return FakeCredentialRequestResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_configuration",
        fake_get_referral_saas_integration_configuration,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "create_referral_saas_integration_credential_request",
        fake_create_referral_saas_integration_credential_request,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "credentialRequest": {
                    "requestType": "API_KEY_CREATE",
                    "capability": "REFERRAL_SAAS_API_ACCESS",
                    "environment": "SANDBOX",
                    "intendedUse": ["CAMPAIGN_READ"],
                    "requestedFor": {
                        "integrationOwnerRef": "ops-team",
                        "displayName": "Ops team",
                    },
                },
                "reasonCode": "CUSTOMER_CREDENTIAL_REQUEST",
                "correlationId": "corr-1",
                "idempotencyKey": "credential-request-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert (
        body["integrationCredentialRequestResult"]["commandStatus"]
        == "INTEGRATION_CREDENTIAL_REQUEST_RECORDED"
    )
    assert body["no_credential_creation_confirmed"] is True
    assert body["no_credential_reveal_or_download_confirmed"] is True
    assert body["no_vault_write_confirmed"] is True
    assert body["no_provider_call_confirmed"] is True
    assert request_calls[0]["account_id"] == "acct-1"
    assert request_calls[0]["tenant_code"] == "FNB"
    assert request_calls[0]["request_type"] == "API_KEY_CREATE"
    assert request_calls[0]["capability"] == "REFERRAL_SAAS_API_ACCESS"
    assert request_calls[0]["actor_role"] == "ADMIN"


async def test_referral_saas_account_credential_request_requires_command_scope(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        raise AssertionError("account should not resolve without command scope")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "credentialRequest": {
                    "requestType": "API_KEY_CREATE",
                    "capability": "REFERRAL_SAAS_API_ACCESS",
                },
                "correlationId": "corr-1",
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "validation_error"
    assert detail["no_credential_request_recorded_confirmed"] is True


async def test_referral_saas_account_credential_request_rejects_unsafe_payload(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        raise AssertionError("unsafe payload should fail before account lookup")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "credentialRequest": {
                    "requestType": "API_KEY_CREATE",
                    "capability": "REFERRAL_SAAS_API_ACCESS",
                    "apiKey": "secret",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "credential-request-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert detail["no_credential_creation_confirmed"] is True
    assert detail["no_credential_lifecycle_execution_confirmed"] is True


async def test_referral_saas_account_credential_request_idempotency_conflict(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    async def fake_get_referral_saas_integration_configuration(**kwargs):
        return SimpleNamespace(configuration_ref="config-1")

    async def fake_create_referral_saas_integration_credential_request(**kwargs):
        raise IntegrationConfigurationIdempotencyConflict(
            "Idempotency key was reused with different credential request content."
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_configuration",
        fake_get_referral_saas_integration_configuration,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "create_referral_saas_integration_credential_request",
        fake_create_referral_saas_integration_credential_request,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "credentialRequest": {
                    "requestType": "API_KEY_CREATE",
                    "capability": "REFERRAL_SAAS_API_ACCESS",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "credential-request-1",
            },
        )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "IDEMPOTENCY_CONFLICT"
    assert detail["no_credential_creation_confirmed"] is True
    assert detail["no_provider_call_confirmed"] is True


async def test_referral_saas_account_admin_can_review_integration_credential_request(
    monkeypatch,
):
    review_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    class FakeCredentialReviewResult:
        def to_safe_dict(self):
            return {
                "commandStatus": "CREDENTIAL_REQUEST_REVIEW_RECORDED",
                "credentialRequest": {
                    "credentialRequestRef": "credreq-1",
                    "requestType": "API_KEY_CREATE",
                    "capability": "REFERRAL_SAAS_API_ACCESS",
                    "reviewStatus": "REVIEW_APPROVED",
                },
                "reviewStatus": "REVIEW_APPROVED",
                "idempotency": {"status": "CREDENTIAL_REQUEST_REVIEW_RECORDED"},
                "audit": {"accountAuditEventId": "audit-1"},
                "noCredentialCreationConfirmed": True,
                "noVaultWriteConfirmed": True,
                "noProviderCallConfirmed": True,
            }

    async def fake_record_referral_saas_integration_credential_review_decision(
        **kwargs,
    ):
        review_calls.append(kwargs)
        return FakeCredentialReviewResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "record_referral_saas_integration_credential_review_decision",
        fake_record_referral_saas_integration_credential_review_decision,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests/credreq-1/review-decisions",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "reviewDecision": {
                    "decision": "approved",
                    "reason": "Integration request reviewed and safe to execute later.",
                },
                "reasonCode": "CREDENTIAL_REQUEST_REVIEW",
                "correlationId": "corr-1",
                "idempotencyKey": "credential-review-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert (
        body["integrationCredentialReviewDecisionResult"]["commandStatus"]
        == "CREDENTIAL_REQUEST_REVIEW_RECORDED"
    )
    assert body["no_credential_creation_confirmed"] is True
    assert body["no_credential_reveal_or_download_confirmed"] is True
    assert body["no_vault_write_confirmed"] is True
    assert body["no_provider_call_confirmed"] is True
    assert review_calls[0]["account_id"] == "acct-1"
    assert review_calls[0]["tenant_code"] == "FNB"
    assert review_calls[0]["credential_request_ref"] == "credreq-1"
    assert review_calls[0]["review_status"] == "REVIEW_APPROVED"
    assert review_calls[0]["actor_role"] == "ADMIN"


async def test_referral_saas_account_credential_request_review_requires_command_scope(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        raise AssertionError("account should not resolve without command scope")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests/credreq-1/review-decisions",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "reviewDecision": {"decision": "approved"},
                "correlationId": "corr-1",
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "validation_error"
    assert detail["no_credential_review_recorded_confirmed"] is True


async def test_referral_saas_account_credential_request_review_rejects_unsafe_payload(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        raise AssertionError("unsafe payload should fail before account lookup")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests/credreq-1/review-decisions",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "reviewDecision": {
                    "decision": "approved",
                    "reason": "Reviewed request.",
                    "apiKey": "secret",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "credential-review-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert detail["no_credential_creation_confirmed"] is True
    assert detail["no_provider_call_confirmed"] is True


async def test_referral_saas_account_credential_request_review_idempotency_conflict(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    async def fake_record_referral_saas_integration_credential_review_decision(
        **kwargs,
    ):
        raise IntegrationConfigurationIdempotencyConflict(
            "Idempotency key was reused with different credential review content."
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "record_referral_saas_integration_credential_review_decision",
        fake_record_referral_saas_integration_credential_review_decision,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests/credreq-1/review-decisions",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "reviewDecision": {
                    "decision": "approved",
                    "reason": "Integration request reviewed and safe to execute later.",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "credential-review-1",
            },
        )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "IDEMPOTENCY_CONFLICT"
    assert detail["no_credential_creation_confirmed"] is True
    assert detail["no_vault_write_confirmed"] is True


async def test_referral_saas_account_admin_can_check_integration_credential_execution(
    monkeypatch,
):
    execution_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    class FakeCredentialExecutionCheckResult:
        def to_safe_dict(self):
            return {
                "commandStatus": "CREDENTIAL_EXECUTION_CHECK_RECORDED",
                "credentialRequest": {
                    "credentialRequestRef": "credreq-1",
                    "requestType": "API_KEY_CREATE",
                    "capability": "REFERRAL_SAAS_API_ACCESS",
                    "reviewStatus": "REVIEW_APPROVED",
                },
                "executionCheckStatus": "CREDENTIAL_EXECUTION_CHECK_RECORDED",
                "idempotency": {"status": "CREDENTIAL_EXECUTION_CHECK_RECORDED"},
                "audit": {"accountAuditEventId": "audit-1"},
                "noCredentialCreationConfirmed": True,
                "noVaultWriteConfirmed": True,
                "noProviderCallConfirmed": True,
            }

    async def fake_record_referral_saas_integration_credential_execution_check(
        **kwargs,
    ):
        execution_calls.append(kwargs)
        return FakeCredentialExecutionCheckResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "record_referral_saas_integration_credential_execution_check",
        fake_record_referral_saas_integration_credential_execution_check,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests/credreq-1/execution-checks",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "executionCheck": {
                    "reason": "Approved credential request checked for later execution.",
                },
                "reasonCode": "CREDENTIAL_EXECUTION_CHECK",
                "correlationId": "corr-1",
                "idempotencyKey": "credential-execution-check-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert (
        body["integrationCredentialExecutionCheckResult"]["commandStatus"]
        == "CREDENTIAL_EXECUTION_CHECK_RECORDED"
    )
    assert body["no_credential_creation_confirmed"] is True
    assert body["no_credential_reveal_or_download_confirmed"] is True
    assert body["no_vault_write_confirmed"] is True
    assert body["no_provider_call_confirmed"] is True
    assert execution_calls[0]["account_id"] == "acct-1"
    assert execution_calls[0]["tenant_code"] == "FNB"
    assert execution_calls[0]["credential_request_ref"] == "credreq-1"
    assert execution_calls[0]["actor_role"] == "ADMIN"


async def test_referral_saas_account_credential_execution_check_requires_command_scope(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        raise AssertionError("account should not resolve without command scope")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests/credreq-1/execution-checks",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "executionCheck": {},
                "correlationId": "corr-1",
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "validation_error"
    assert detail["no_credential_execution_check_recorded_confirmed"] is True


async def test_referral_saas_account_credential_execution_check_rejects_unsafe_payload(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        raise AssertionError("unsafe payload should fail before account lookup")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests/credreq-1/execution-checks",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "executionCheck": {
                    "reason": "Ready to execute.",
                    "apiKey": "secret",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "credential-execution-check-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert detail["no_credential_creation_confirmed"] is True
    assert detail["no_provider_call_confirmed"] is True


async def test_referral_saas_account_credential_execution_check_idempotency_conflict(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    async def fake_record_referral_saas_integration_credential_execution_check(
        **kwargs,
    ):
        raise IntegrationConfigurationIdempotencyConflict(
            "Idempotency key was reused with different credential execution check content."
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "record_referral_saas_integration_credential_execution_check",
        fake_record_referral_saas_integration_credential_execution_check,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests/credreq-1/execution-checks",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "executionCheck": {
                    "reason": "Approved credential request checked for later execution.",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "credential-execution-check-1",
            },
        )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "IDEMPOTENCY_CONFLICT"
    assert detail["no_credential_creation_confirmed"] is True
    assert detail["no_vault_write_confirmed"] is True


async def test_referral_saas_account_admin_can_record_provider_vault_execution(
    monkeypatch,
):
    execution_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    async def fake_get_referral_saas_integration_configuration(**kwargs):
        return SimpleNamespace(configuration_ref="config-1")

    class FakeProviderVaultExecutionResult:
        def to_safe_dict(self):
            return {
                "commandStatus": "PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED",
                "executionRef": "audit-1",
                "credentialRequest": {
                    "credentialRequestRef": "credreq-1",
                    "requestType": "PROVIDER_CREDENTIAL_REFERENCE_CREATE",
                    "capability": "REFERRAL_SAAS_PROVIDER_REFERENCE",
                    "reviewStatus": "REVIEW_APPROVED",
                },
                "providerKey": "sendgrid",
                "environment": "SANDBOX",
                "capability": "REFERRAL_SAAS_PROVIDER_REFERENCE",
                "blockedReason": "PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED",
                "idempotency": {"status": "PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED"},
                "audit": {"accountAuditEventId": "audit-1"},
                "noCredentialCreationConfirmed": True,
                "noVaultWriteConfirmed": True,
                "noProviderCallConfirmed": True,
            }

    async def fake_record_referral_saas_provider_vault_execution(**kwargs):
        execution_calls.append(kwargs)
        return FakeProviderVaultExecutionResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_configuration",
        fake_get_referral_saas_integration_configuration,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "record_referral_saas_provider_vault_execution",
        fake_record_referral_saas_provider_vault_execution,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests/credreq-1/provider-vault-executions",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "providerVaultExecution": {
                    "approvedRequestVersion": "credreq-1",
                    "executionIntent": "CREATE_PROVIDER_VAULT_REFERENCE",
                    "executionMode": "SAFE_RUNTIME_EXECUTION",
                    "providerKey": "sendgrid",
                    "environment": "SANDBOX",
                    "capability": "REFERRAL_SAAS_PROVIDER_REFERENCE",
                    "reason": "Approved provider credential request is ready for runtime execution.",
                },
                "reasonCode": "PROVIDER_VAULT_RUNTIME_EXECUTION",
                "correlationId": "corr-1",
                "idempotencyKey": "provider-vault-execution-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert (
        body["providerVaultExecutionResult"]["commandStatus"]
        == "PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED"
    )
    assert body["no_credential_creation_confirmed"] is True
    assert body["no_vault_write_confirmed"] is True
    assert body["no_provider_call_confirmed"] is True
    assert execution_calls[0]["account_id"] == "acct-1"
    assert execution_calls[0]["credential_request_ref"] == "credreq-1"
    assert execution_calls[0]["actor_role"] == "ADMIN"


async def test_referral_saas_account_provider_vault_execution_requires_command_scope(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        raise AssertionError("account should not resolve without command scope")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests/credreq-1/provider-vault-executions",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "providerVaultExecution": {},
                "correlationId": "corr-1",
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "validation_error"
    assert detail["no_provider_vault_execution_recorded_confirmed"] is True


async def test_referral_saas_account_provider_vault_execution_rejects_unsafe_payload(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        raise AssertionError("unsafe payload should fail before account lookup")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests/credreq-1/provider-vault-executions",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "providerVaultExecution": {
                    "approvedRequestVersion": "credreq-1",
                    "providerKey": "sendgrid",
                    "environment": "SANDBOX",
                    "capability": "REFERRAL_SAAS_PROVIDER_REFERENCE",
                    "reason": "Execute approved request.",
                    "apiKey": "secret",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "provider-vault-execution-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert detail["no_credential_creation_confirmed"] is True
    assert detail["no_provider_call_confirmed"] is True


async def test_referral_saas_account_provider_vault_execution_idempotency_conflict(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    async def fake_get_referral_saas_integration_configuration(**kwargs):
        return SimpleNamespace(configuration_ref="config-1")

    async def fake_record_referral_saas_provider_vault_execution(**kwargs):
        raise IntegrationConfigurationIdempotencyConflict(
            "Idempotency key was reused with different provider/vault execution content."
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_configuration",
        fake_get_referral_saas_integration_configuration,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "record_referral_saas_provider_vault_execution",
        fake_record_referral_saas_provider_vault_execution,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests/credreq-1/provider-vault-executions",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "providerVaultExecution": {
                    "approvedRequestVersion": "credreq-1",
                    "providerKey": "sendgrid",
                    "environment": "SANDBOX",
                    "capability": "REFERRAL_SAAS_PROVIDER_REFERENCE",
                    "reason": "Execute approved request.",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "provider-vault-execution-1",
            },
        )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "IDEMPOTENCY_CONFLICT"
    assert detail["no_credential_creation_confirmed"] is True
    assert detail["no_vault_write_confirmed"] is True


async def test_referral_saas_account_admin_can_read_provider_vault_execution(
    monkeypatch,
):
    read_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    class FakeProviderVaultExecutionResult:
        def to_safe_dict(self):
            return {
                "commandStatus": "PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED",
                "executionRef": "audit-1",
                "credentialRequest": {"credentialRequestRef": "credreq-1"},
                "noCredentialCreationConfirmed": True,
                "noVaultWriteConfirmed": True,
                "noProviderCallConfirmed": True,
            }

    async def fake_get_referral_saas_provider_vault_execution(**kwargs):
        read_calls.append(kwargs)
        return FakeProviderVaultExecutionResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_provider_vault_execution",
        fake_get_referral_saas_provider_vault_execution,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/integrations/provider-vault/executions/audit-1",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["providerVaultExecutionResult"]["executionRef"] == "audit-1"
    assert body["no_credential_creation_confirmed"] is True
    assert body["no_vault_write_confirmed"] is True
    assert read_calls[0]["account_id"] == "acct-1"
    assert read_calls[0]["execution_ref"] == "audit-1"


async def test_referral_saas_account_admin_can_list_integration_credential_requests(
    monkeypatch,
):
    list_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    class FakeCredentialRequest:
        def to_safe_dict(self):
            return {
                "credentialRequestRef": "credreq-1",
                "requestType": "API_KEY_CREATE",
                "capability": "REFERRAL_SAAS_API_ACCESS",
                "reviewStatus": "READY_FOR_REVIEW",
            }

    async def fake_list_referral_saas_integration_credential_requests(**kwargs):
        list_calls.append(kwargs)
        return [FakeCredentialRequest()]

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "list_referral_saas_integration_credential_requests",
        fake_list_referral_saas_integration_credential_requests,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["credentialRequests"][0]["credentialRequestRef"] == "credreq-1"
    assert body["no_credential_reveal_or_download_confirmed"] is True
    assert list_calls[0]["account_id"] == "acct-1"
    assert list_calls[0]["limit"] == 25


async def test_referral_saas_account_admin_can_read_integration_credential_request(
    monkeypatch,
):
    read_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    class FakeCredentialRequest:
        def to_safe_dict(self):
            return {
                "credentialRequestRef": "credreq-1",
                "requestType": "API_KEY_CREATE",
                "capability": "REFERRAL_SAAS_API_ACCESS",
                "reviewStatus": "READY_FOR_REVIEW",
            }

    async def fake_get_referral_saas_integration_credential_request(**kwargs):
        read_calls.append(kwargs)
        return FakeCredentialRequest()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_credential_request",
        fake_get_referral_saas_integration_credential_request,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests/credreq-1",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["credentialRequest"]["credentialRequestRef"] == "credreq-1"
    assert body["no_secret_or_credential_storage_confirmed"] is True
    assert read_calls[0]["account_id"] == "acct-1"
    assert read_calls[0]["credential_request_ref"] == "credreq-1"


async def test_referral_saas_account_credential_request_read_returns_404(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    async def fake_get_referral_saas_integration_credential_request(**kwargs):
        raise IntegrationCredentialRequestNotFound("Credential request was not found.")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_integration_credential_request",
        fake_get_referral_saas_integration_credential_request,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/integrations/credential-requests/missing",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["code"] == "CREDENTIAL_REQUEST_NOT_FOUND"
    assert detail["no_credential_creation_confirmed"] is True


async def test_referral_saas_account_admin_can_read_customer_scoped_campaign_readiness(
    monkeypatch,
):
    resolve_calls: list[dict] = []
    readiness_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    async def fake_get_campaign_readiness(**kwargs):
        readiness_calls.append(kwargs)
        return {
            "tenant_code": "FNB",
            "tenantCode": "FNB",
            "campaign_code": "CAMP001",
            "readiness": "READY_WITH_WARNINGS",
            "can_proceed": True,
            "blockers": [],
            "warnings": [
                {
                    "code": "REPORTING_BASELINE_PENDING",
                    "message": "Reporting setup can follow after campaign checks.",
                }
            ],
            "evidence": {
                "campaign": {
                    "campaign_code": "CAMP001",
                    "tenant_code": "FNB",
                    "tenant_scope": {"tenantCode": "FNB"},
                }
            },
            "unknowns": [],
        }

    async def fake_get_referral_saas_campaign_journey_binding(**kwargs):
        return None

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_campaign_readiness",
        fake_get_campaign_readiness,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_campaign_journey_binding",
        fake_get_referral_saas_campaign_journey_binding,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/readiness",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
                "operation": "GENERATE_LINKS",
                "opportunity_id": "opp-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["context"] == "setup"
    assert body["account"]["accountCode"] == "ACCT_FNB"
    assert "tenantCode" not in body["account"]
    assert body["readiness"]["readiness"] == "READY_WITH_WARNINGS"
    assert body["readiness"]["warnings"][0]["code"] == "REPORTING_BASELINE_PENDING"
    assert "tenant_code" not in body["readiness"]
    assert "tenantCode" not in body["readiness"]
    assert "tenant_code" not in body["readiness"]["evidence"]["campaign"]
    assert "tenant_scope" not in body["readiness"]["evidence"]["campaign"]
    assert body["no_campaign_mutation_confirmed"] is True
    assert body["no_policy_write_confirmed"] is True
    assert body["no_link_generation_confirmed"] is True
    assert body["no_campaign_activation_confirmed"] is True
    assert body["no_money_movement_confirmed"] is True
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert readiness_calls == [
        {
            "tenant_code": "FNB",
            "campaign_code": "CAMP001",
            "operation": "GENERATE_LINKS",
            "opportunity_id": "opp-1",
            "include_evidence": True,
        }
    ]


async def test_referral_saas_account_admin_can_list_customer_scoped_campaigns(
    monkeypatch,
):
    resolve_calls: list[dict] = []
    campaign_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    async def fake_list_referral_saas_account_campaigns(**kwargs):
        campaign_calls.append(kwargs)
        return [_campaign_summary()]

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "list_referral_saas_account_campaigns",
        fake_list_referral_saas_account_campaigns,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/campaigns",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["count"] == 1
    assert body["campaigns"][0]["campaignCode"] == "CAMP001"
    assert body["campaigns"][0]["policyStatus"] == "ACTIVE_POLICY"
    assert body["no_campaign_mutation_confirmed"] is True
    assert body["no_policy_write_confirmed"] is True
    assert body["no_link_generation_confirmed"] is True
    assert body["no_campaign_activation_confirmed"] is True
    assert body["no_money_movement_confirmed"] is True
    assert "tenantCode" not in str(body)
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert campaign_calls == [{"tenant_code": "FNB", "limit": 25}]


async def test_referral_saas_account_admin_can_read_campaign_attribution_projection(
    monkeypatch,
):
    resolve_calls: list[dict] = []
    attribution_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    async def fake_build_referral_saas_account_campaign_attribution_projection(**kwargs):
        attribution_calls.append(kwargs)
        return _campaign_attribution_summary()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "build_referral_saas_account_campaign_attribution_projection",
        fake_build_referral_saas_account_campaign_attribution_projection,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/campaign-attribution",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["campaignAttribution"]["status"] == "READY"
    assert body["campaignAttribution"]["projections"][0]["campaignCode"] == "CAMP001"
    assert body["campaignAttribution"]["projections"][0]["confidence"] == "HIGH"
    assert body["no_tenant_code_exposure_confirmed"] is True
    assert body["no_raw_identity_exposure_confirmed"] is True
    assert body["no_raw_event_payload_exposure_confirmed"] is True
    assert body["no_attribution_mutation_confirmed"] is True
    assert body["no_campaign_activation_confirmed"] is True
    assert body["no_billing_or_money_movement_confirmed"] is True
    assert "tenantCode" not in str(body)
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert attribution_calls == [{"tenant_code": "FNB", "limit": 25}]


async def test_referral_saas_account_admin_can_read_referral_attribution_projection(
    monkeypatch,
):
    resolve_calls: list[dict] = []
    attribution_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    async def fake_build_referral_saas_account_referral_attribution_projection(**kwargs):
        attribution_calls.append(kwargs)
        return _referral_attribution_summary()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "build_referral_saas_account_referral_attribution_projection",
        fake_build_referral_saas_account_referral_attribution_projection,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/referral-attribution",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["referralAttribution"]["status"] == "READY"
    assert body["referralAttribution"]["referralProjections"][0]["creditStatus"] == "CREDITED"
    assert body["referralAttribution"]["referrerProjections"][0]["safeReferrerKey"] == "REFERRER_SAFE"
    assert body["no_tenant_code_exposure_confirmed"] is True
    assert body["no_raw_identity_exposure_confirmed"] is True
    assert body["no_raw_progress_payload_exposure_confirmed"] is True
    assert body["no_attribution_mutation_confirmed"] is True
    assert body["no_repair_replay_reassignment_confirmed"] is True
    assert body["no_campaign_activation_confirmed"] is True
    assert body["no_billing_or_money_movement_confirmed"] is True
    assert "tenantCode" not in str(body)
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert attribution_calls == [{"tenant_code": "FNB", "limit": 25}]


async def test_referral_saas_account_campaign_operations_reject_missing_campaign_capability(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
            operating_jurisdiction_code="ZA",
        )

    async def fail_if_campaign_service_called(**kwargs):
        pytest.fail("Campaign service should not be called without campaign capability")

    async def fail_if_referral_attribution_service_called(**kwargs):
        pytest.fail("Referral attribution service should not be called without referral capability")

    monkeypatch.setattr(
        referral_saas_accounts,
        "_require_referral_saas_account_reader",
        lambda identity: _campaign_scoped_identity_with_capabilities(
            "REFERRAL_SAAS_ACCOUNT_READ"
        ),
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "list_referral_saas_account_campaigns",
        fail_if_campaign_service_called,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "build_referral_saas_account_campaign_attribution_projection",
        fail_if_campaign_service_called,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "build_referral_saas_account_referral_attribution_projection",
        fail_if_referral_attribution_service_called,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_account_campaign",
        fail_if_campaign_service_called,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "create_referral_saas_account_campaign_setup",
        fail_if_campaign_service_called,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "upsert_referral_saas_account_campaign_policy_settings",
        fail_if_campaign_service_called,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "submit_referral_saas_account_campaign_review",
        fail_if_campaign_service_called,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "record_referral_saas_account_campaign_review_decision",
        fail_if_campaign_service_called,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "request_referral_saas_account_campaign_activation",
        fail_if_campaign_service_called,
    )

    account_scope = {
        "refType": "external_tenant_ref",
        "externalRef": "fnb-referrals",
        "context": "setup",
    }
    query_scope = {
        "ref_type": "external_tenant_ref",
        "external_ref": "fnb-referrals",
        "context": "setup",
    }
    cases = [
        (
            "get",
            "/v1/referral-saas/accounts/acct-1/campaigns",
            {"params": {**query_scope, "limit": 25}},
        ),
        (
            "get",
            "/v1/referral-saas/accounts/acct-1/campaign-attribution",
            {"params": {**query_scope, "limit": 25}},
        ),
        (
            "get",
            "/v1/referral-saas/accounts/acct-1/referral-attribution",
            {"params": {**query_scope, "limit": 25}},
        ),
        (
            "get",
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001",
            {"params": query_scope},
        ),
        (
            "post",
            "/v1/referral-saas/accounts/acct-1/campaigns",
            {
                "json": {
                    "accountScope": account_scope,
                    "campaign": {
                        "name": "Summer Referral",
                        "segment": "Retail",
                        "startsAt": "2026-08-01T00:00:00Z",
                        "maxUses": 100,
                    },
                    "correlationId": "corr-create-denied",
                    "idempotencyKey": "campaign-create-denied",
                }
            },
        ),
        (
            "put",
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/policy-settings",
            {
                "json": {
                    "accountScope": account_scope,
                    "policySettings": {
                        "version": 1,
                        "attributionWindowDays": 30,
                        "eligibilityRules": [
                            {"rule": "NEW_CUSTOMER_ONLY", "enabled": True}
                        ],
                        "productWindows": {"default": {"days": 30}},
                        "productRules": {
                            "default": {"requiresAcceptedTerms": True}
                        },
                        "rewardVisibility": {
                            "mode": "configured_without_payment"
                        },
                    },
                    "correlationId": "corr-policy-denied",
                    "idempotencyKey": "campaign-policy-denied",
                }
            },
        ),
        (
            "post",
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/review-submissions",
            {
                "json": {
                    "accountScope": account_scope,
                    "reviewSubmission": {
                        "setupSummary": "Campaign setup and policy settings are ready.",
                        "requestedReviewStatus": "READY_FOR_REVIEW",
                    },
                    "correlationId": "corr-review-submit-denied",
                    "idempotencyKey": "campaign-review-submit-denied",
                }
            },
        ),
        (
            "post",
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/review-decisions",
            {
                "json": {
                    "accountScope": account_scope,
                    "reviewDecision": {
                        "decision": "APPROVED",
                        "reason": "Campaign evidence reviewed.",
                        "reviewerRef": "operator-1",
                    },
                    "correlationId": "corr-review-decision-denied",
                    "idempotencyKey": "campaign-review-decision-denied",
                }
            },
        ),
        (
            "post",
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/activation-requests",
            {
                "json": {
                    "accountScope": {
                        **account_scope,
                        "context": "campaign_activation",
                    },
                    "activationRequest": {
                        "requestedLifecycleStatus": "ACTIVE",
                        "reviewStatus": "REVIEW_APPROVED",
                        "goLiveReason": "Approved for first referral campaign test.",
                    },
                    "correlationId": "corr-activation-denied",
                    "idempotencyKey": "campaign-activation-denied",
                }
            },
        ),
    ]

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        for method, url, request_kwargs in cases:
            response = await getattr(client, method)(url, **request_kwargs)
            _assert_campaign_capability_forbidden(response)


async def test_referral_saas_account_admin_can_read_customer_scoped_report(
    monkeypatch,
):
    report_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    def fake_get_referral_saas_report(**kwargs):
        report_calls.append(kwargs)
        return {
            "report_type": kwargs["report_type"],
            "tenant_scope": {"tenant_code": kwargs["tenant_code"]},
            "rows": [
                {
                    "campaign_code": "CAMP001",
                    "metric_name": "referrals.completed_count",
                    "value": 4,
                }
            ],
        }

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_report",
        fake_get_referral_saas_report,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/reports/campaign_performance",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
                "campaign_code": "CAMP001",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["account"]["accountId"] == "acct-1"
    assert body["account_scope"]["source"] == "selected_customer_account"
    assert body["report"]["rows"][0]["campaign_code"] == "CAMP001"
    assert body["no_tenant_code_exposure_confirmed"] is True
    assert body["no_report_mutation_confirmed"] is True
    assert body["no_export_creation_confirmed"] is True
    public_report_payload = {
        "account": body["account"],
        "account_scope": body["account_scope"],
        "report": body["report"],
        "redactions": body["redactions"],
    }
    assert "tenant_code" not in str(public_report_payload)
    assert "tenantCode" not in str(public_report_payload)
    assert report_calls == [
        {
            "tenant_code": "FNB",
            "report_type": "campaign_performance",
            "dimensions": None,
            "filters": {"campaign_code": "CAMP001"},
            "data_window_start": None,
            "data_window_end": None,
        }
    ]


async def test_referral_saas_account_admin_can_preview_customer_scoped_report_export(
    monkeypatch,
):
    preview_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    def fake_build_referral_saas_report_export_preview(**kwargs):
        preview_calls.append(kwargs)
        return {
            "status": "PREVIEW_READY",
            "tenant_scope": {"tenant_code": kwargs["tenant_code"]},
            "sample_rows": [{"campaign_code": "CAMP001", "value": 4}],
        }

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "build_referral_saas_report_export_preview",
        fake_build_referral_saas_report_export_preview,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/reports/link_code_performance/exports/preview",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
            json={
                "format": "csv",
                "redaction_profile": "tenant_safe",
                "filters": {"campaign_code": "CAMP001"},
                "row_limit": 50,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["export_preview"]["status"] == "PREVIEW_READY"
    assert body["export_preview"]["sample_rows"][0]["campaign_code"] == "CAMP001"
    assert body["no_export_creation_confirmed"] is True
    assert body["no_storage_or_delivery_confirmed"] is True
    public_export_payload = {
        "account": body["account"],
        "account_scope": body["account_scope"],
        "export_preview": body["export_preview"],
        "redactions": body["redactions"],
    }
    assert "tenant_code" not in str(public_export_payload)
    assert preview_calls == [
        {
            "tenant_code": "FNB",
            "report_type": "link_code_performance",
            "export_format": "csv",
            "redaction_profile": "tenant_safe",
            "dimensions": None,
            "filters": {"campaign_code": "CAMP001"},
            "row_limit": 50,
            "data_window_start": None,
            "data_window_end": None,
        }
    ]


async def test_referral_saas_account_admin_can_create_customer_scoped_report_export_request(
    monkeypatch,
):
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    class FakeExportRequestResult:
        def to_safe_dict(self):
            return {
                "commandStatus": "REPORT_EXPORT_REQUEST_RECORDED",
                "accountRef": "acct-1",
                "reportType": "campaign_performance",
                "exportRequest": {
                    "exportRequestId": "export-1",
                    "format": "csv",
                    "redactionProfile": "tenant_safe",
                    "rowLimit": 50,
                    "rowCount": 1,
                    "requestStatus": "READY_FOR_FILE_STORAGE",
                    "storageStatus": "NOT_STORED",
                    "deliveryStatus": "NOT_REQUESTED",
                    "downloadStatus": "NOT_AVAILABLE",
                    "downloadUrl": None,
                    "expiresAt": "2026-07-31T00:00:00+00:00",
                },
                "idempotency": {"status": "RECORDED"},
                "audit": {"accountAuditEventId": "audit-1"},
                "guardrails": ["NO_DOWNLOAD_URL_CREATED"],
                "redactions": ["internal_tenant_identifier"],
            }

    async def fake_create_referral_saas_report_export_request(**kwargs):
        command_calls.append(kwargs)
        return FakeExportRequestResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "create_referral_saas_report_export_request",
        fake_create_referral_saas_report_export_request,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/reports/campaign_performance/exports",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "format": "csv",
                "redaction_profile": "tenant_safe",
                "filters": {"campaign_code": "CAMP001"},
                "row_limit": 50,
                "idempotencyKey": "export-request-1",
                "correlationId": "corr-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert body["reportExport"]["commandStatus"] == "REPORT_EXPORT_REQUEST_RECORDED"
    assert body["reportExport"]["exportRequest"]["downloadUrl"] is None
    assert body["no_export_file_created_confirmed"] is True
    assert body["no_download_url_created_confirmed"] is True
    public_export_payload = {
        "account": body["account"],
        "account_scope": body["account_scope"],
        "reportExport": body["reportExport"],
        "redactions": body["redactions"],
    }
    assert "tenant_code" not in str(public_export_payload)
    assert command_calls
    assert command_calls[0]["tenant_code"] == "FNB"
    assert command_calls[0]["account_id"] == "acct-1"
    assert command_calls[0]["report_type"] == "campaign_performance"
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["request_payload_hash"]
    assert command_calls[0]["correlation_id"] == "corr-1"


async def test_referral_saas_account_report_export_request_rejects_unsafe_payload(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/reports/campaign_performance/exports",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "format": "json",
                "idempotencyKey": "export-request-1",
                "correlationId": "corr-1",
                "downloadUrl": "https://example.test/file.csv",
            },
        )

    assert response.status_code == 400
    body = response.json()
    assert body["detail"]["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert body["detail"]["no_download_url_created_confirmed"] is True
    assert body["detail"]["no_billing_or_money_movement_confirmed"] is True


async def test_referral_saas_account_admin_can_create_report_delivery_schedule(
    monkeypatch,
):
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    class FakeDeliveryScheduleResult:
        def to_safe_dict(self):
            return {
                "commandStatus": "REPORT_DELIVERY_SCHEDULE_RECORDED",
                "accountRef": "acct-1",
                "reportType": "campaign_performance",
                "deliverySchedule": {
                    "scheduleId": "schedule-1",
                    "scheduleStatus": "READY",
                    "cadence": "WEEKLY",
                    "recipientContactRefs": ["contact-owner"],
                },
                "readiness": {
                    "status": "READY",
                    "blockedReasons": [],
                    "warnings": ["LIVE_DELIVERY_WORKER_NOT_ENABLED"],
                },
                "idempotency": {"status": "RECORDED"},
                "audit": {"accountAuditEventId": "audit-1"},
                "guardrails": ["NO_LIVE_DELIVERY_EXECUTED"],
                "redactions": ["internal_tenant_identifier"],
                "noLiveDeliveryExecutedConfirmed": True,
                "noEmailSentConfirmed": True,
            }

    async def fake_create_referral_saas_report_delivery_schedule(**kwargs):
        command_calls.append(kwargs)
        return FakeDeliveryScheduleResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "create_referral_saas_report_delivery_schedule",
        fake_create_referral_saas_report_delivery_schedule,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/reports/campaign_performance/delivery-schedules",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "cadence": "weekly",
                "timezone": "Africa/Johannesburg",
                "format": "csv",
                "redactionProfile": "tenant_safe",
                "recipientContactRefs": ["contact-owner"],
                "retentionDays": 7,
                "idempotencyKey": "schedule-1",
                "correlationId": "corr-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert (
        body["reportDeliverySchedule"]["commandStatus"]
        == "REPORT_DELIVERY_SCHEDULE_RECORDED"
    )
    assert body["reportDeliverySchedule"]["deliverySchedule"]["scheduleStatus"] == "READY"
    assert body["no_live_delivery_executed_confirmed"] is True
    assert body["no_email_sent_confirmed"] is True
    public_payload = {
        "account": body["account"],
        "account_scope": body["account_scope"],
        "reportDeliverySchedule": body["reportDeliverySchedule"],
        "redactions": body["redactions"],
    }
    assert "tenant_code" not in str(public_payload)
    assert command_calls
    assert command_calls[0]["tenant_code"] == "FNB"
    assert command_calls[0]["account_id"] == "acct-1"
    assert command_calls[0]["report_type"] == "campaign_performance"
    assert command_calls[0]["correlation_id"] == "corr-1"
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["request_payload_hash"]


async def test_referral_saas_account_report_delivery_schedule_requires_scope(
    monkeypatch,
):
    async def fake_create_referral_saas_report_delivery_schedule(**kwargs):
        raise AssertionError("schedule service should not be called")

    monkeypatch.setattr(
        referral_saas_accounts,
        "create_referral_saas_report_delivery_schedule",
        fake_create_referral_saas_report_delivery_schedule,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/reports/campaign_performance/delivery-schedules",
            json={
                "cadence": "weekly",
                "timezone": "Africa/Johannesburg",
                "idempotencyKey": "schedule-1",
                "correlationId": "corr-1",
            },
        )

    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["code"] == "validation_error"
    assert body["detail"]["no_live_delivery_executed_confirmed"] is True


async def test_referral_saas_account_report_delivery_schedule_conflict_is_safe(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    async def fake_create_referral_saas_report_delivery_schedule(**kwargs):
        raise referral_saas_accounts.ReportDeliveryScheduleIdempotencyConflict(
            "Idempotency key was reused with different schedule content."
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "create_referral_saas_report_delivery_schedule",
        fake_create_referral_saas_report_delivery_schedule,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/reports/campaign_performance/delivery-schedules",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "cadence": "weekly",
                "timezone": "Africa/Johannesburg",
                "recipientContactRefs": ["contact-owner"],
                "idempotencyKey": "schedule-1",
                "correlationId": "corr-1",
            },
        )

    assert response.status_code == 409
    body = response.json()
    assert body["detail"]["code"] == "REPORT_DELIVERY_IDEMPOTENCY_CONFLICT"
    assert body["detail"]["no_live_delivery_executed_confirmed"] is True


async def test_referral_saas_account_admin_can_list_update_and_check_schedule(
    monkeypatch,
):
    service_calls: list[tuple[str, dict]] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    class FakeDeliveryScheduleResult:
        def __init__(self, command_status: str = "REPORT_DELIVERY_SCHEDULE_READ"):
            self.command_status = command_status

        def to_safe_dict(self):
            return {
                "commandStatus": self.command_status,
                "accountRef": "acct-1",
                "reportType": "campaign_performance",
                "deliverySchedule": {
                    "scheduleId": "schedule-1",
                    "scheduleStatus": "READY",
                    "cadence": "WEEKLY",
                    "recipientContactRefs": ["contact-owner"],
                },
                "readiness": {
                    "status": "READY",
                    "blockedReasons": [],
                    "warnings": ["LIVE_DELIVERY_WORKER_NOT_ENABLED"],
                },
                "guardrails": ["NO_LIVE_DELIVERY_EXECUTED"],
                "redactions": ["internal_tenant_identifier"],
            }

    async def fake_list_referral_saas_report_delivery_schedules(**kwargs):
        service_calls.append(("list", kwargs))
        return [FakeDeliveryScheduleResult()]

    async def fake_update_referral_saas_report_delivery_schedule(**kwargs):
        service_calls.append(("update", kwargs))
        return FakeDeliveryScheduleResult("REPORT_DELIVERY_SCHEDULE_UPDATED")

    async def fake_get_referral_saas_report_delivery_schedule_readiness(**kwargs):
        service_calls.append(("readiness", kwargs))
        return {
            "scheduleId": "schedule-1",
            "readiness": {
                "status": "READY",
                "blockedReasons": [],
                "warnings": ["LIVE_DELIVERY_WORKER_NOT_ENABLED"],
            },
            "guardrails": ["NO_LIVE_DELIVERY_EXECUTED"],
            "redactions": ["internal_tenant_identifier"],
        }

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "list_referral_saas_report_delivery_schedules",
        fake_list_referral_saas_report_delivery_schedules,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "update_referral_saas_report_delivery_schedule",
        fake_update_referral_saas_report_delivery_schedule,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_report_delivery_schedule_readiness",
        fake_get_referral_saas_report_delivery_schedule_readiness,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        list_response = await client.get(
            "/v1/referral-saas/accounts/acct-1/reports/campaign_performance/delivery-schedules",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )
        update_response = await client.patch(
            "/v1/referral-saas/accounts/acct-1/delivery-schedules/schedule-1",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "scheduleStatus": "paused",
                "idempotencyKey": "schedule-update-1",
                "correlationId": "corr-2",
            },
        )
        readiness_response = await client.get(
            "/v1/referral-saas/accounts/acct-1/delivery-schedules/schedule-1/readiness",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert list_response.status_code == 200
    assert list_response.json()["deliverySchedules"][0]["deliverySchedule"][
        "scheduleId"
    ] == "schedule-1"
    assert update_response.status_code == 200
    assert (
        update_response.json()["reportDeliverySchedule"]["commandStatus"]
        == "REPORT_DELIVERY_SCHEDULE_UPDATED"
    )
    assert update_response.json()["no_live_delivery_executed_confirmed"] is True
    assert readiness_response.status_code == 200
    assert readiness_response.json()["reportDeliveryScheduleReadiness"]["readiness"][
        "status"
    ] == "READY"
    assert [call[0] for call in service_calls] == ["list", "update", "readiness"]


async def test_referral_saas_account_admin_can_create_report_export_file(
    monkeypatch,
):
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    class FakeExportFileResult:
        def to_safe_dict(self):
            return {
                "commandStatus": "REPORT_EXPORT_FILE_STORED",
                "accountRef": "acct-1",
                "reportType": "campaign_performance",
                "exportRequest": {
                    "exportRequestId": "export-1",
                    "format": "json",
                    "redactionProfile": "tenant_safe",
                    "rowLimit": 50,
                    "rowCount": 1,
                    "requestStatus": "READY_FOR_FILE_STORAGE",
                    "storageStatus": "STORED",
                    "deliveryStatus": "NOT_REQUESTED",
                    "downloadStatus": "AVAILABLE",
                    "downloadUrl": (
                        "/v1/referral-saas/accounts/acct-1/exports/export-1/download"
                        "?download_token=signed&expires_at=2026-07-30T12:05:00+00:00"
                    ),
                    "expiresAt": "2026-07-31T00:00:00+00:00",
                },
                "file": {
                    "fileName": "report.json",
                    "contentType": "application/json",
                    "contentSha256": "sha",
                    "byteSize": 100,
                    "storageMode": "object_store_signed_url",
                    "storageRef": "export_object_abc123",
                    "signedUrlExpiresAt": "2026-07-30T12:05:00+00:00",
                },
                "idempotency": {"status": "RECORDED"},
                "audit": {"accountAuditEventId": "audit-1"},
                "guardrails": ["OPAQUE_OBJECT_STORAGE_REF_ONLY"],
                "redactions": ["internal_tenant_identifier"],
            }

    async def fake_create_referral_saas_report_export_file(**kwargs):
        command_calls.append(kwargs)
        return FakeExportFileResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "create_referral_saas_report_export_file",
        fake_create_referral_saas_report_export_file,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/reports/campaign_performance/exports/export-1/file",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "idempotencyKey": "export-file-1",
                "correlationId": "corr-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "stored"
    assert body["reportExport"]["commandStatus"] == "REPORT_EXPORT_FILE_STORED"
    assert body["reportExport"]["exportRequest"]["downloadStatus"] == "AVAILABLE"
    assert body["reportExport"]["exportRequest"]["downloadUrl"].startswith(
        "/v1/referral-saas/accounts/acct-1/exports/export-1/download"
    )
    assert body["signed_download_url_created_confirmed"] is True
    assert body["no_scheduled_delivery_created_confirmed"] is True
    public_export_payload = {
        "account": body["account"],
        "account_scope": body["account_scope"],
        "reportExport": body["reportExport"],
        "redactions": body["redactions"],
    }
    assert "tenant_code" not in str(public_export_payload)
    assert command_calls
    assert command_calls[0]["account_id"] == "acct-1"
    assert command_calls[0]["export_request_id"] == "export-1"
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["request_payload_hash"]


async def test_referral_saas_account_admin_can_download_report_export_file(
    monkeypatch,
):
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
        )

    class FakeExportDownloadResult:
        def to_safe_dict(self):
            return {
                "commandStatus": "REPORT_EXPORT_FILE_DOWNLOADED",
                "accountRef": "acct-1",
                "reportType": "campaign_performance",
                "exportRequest": {
                    "exportRequestId": "export-1",
                    "format": "csv",
                    "redactionProfile": "tenant_safe",
                    "rowLimit": 50,
                    "rowCount": 1,
                    "requestStatus": "READY_FOR_FILE_STORAGE",
                    "storageStatus": "STORED",
                    "deliveryStatus": "NOT_REQUESTED",
                    "downloadStatus": "AVAILABLE",
                    "downloadUrl": (
                        "/v1/referral-saas/accounts/acct-1/exports/export-1/download"
                        "?download_token=signed&expires_at=2026-07-30T12:05:00+00:00"
                    ),
                    "expiresAt": "2026-07-31T00:00:00+00:00",
                },
                "file": {
                    "fileName": "report.csv",
                    "contentType": "text/csv",
                    "contentSha256": "sha",
                    "byteSize": 20,
                    "storageMode": "object_store_signed_url",
                    "storageRef": "export_object_abc123",
                    "signedUrlExpiresAt": "2026-07-30T12:05:00+00:00",
                    "content": "metric_name,value\nready,1\n",
                },
                "idempotency": {"status": None},
                "audit": {"accountAuditEventId": "audit-1"},
                "guardrails": ["OPAQUE_OBJECT_STORAGE_REF_ONLY"],
                "redactions": ["internal_tenant_identifier"],
            }

    async def fake_download_referral_saas_report_export_file(**kwargs):
        command_calls.append(kwargs)
        return FakeExportDownloadResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "download_referral_saas_report_export_file",
        fake_download_referral_saas_report_export_file,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/exports/export-1/download",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
                "correlation_id": "corr-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "downloadable"
    assert body["reportExport"]["file"]["content"] == "metric_name,value\nready,1\n"
    assert body["reportExport"]["exportRequest"]["downloadUrl"].startswith(
        "/v1/referral-saas/accounts/acct-1/exports/export-1/download"
    )
    assert body["signed_download_route_used_confirmed"] is True
    assert command_calls[0]["account_id"] == "acct-1"
    assert command_calls[0]["export_request_id"] == "export-1"


async def test_referral_saas_account_admin_can_delete_report_export_file(
    monkeypatch,
):
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
        )

    class FakeExportDeleteResult:
        def to_safe_dict(self):
            return {
                "commandStatus": "REPORT_EXPORT_FILE_DELETED",
                "accountRef": "acct-1",
                "reportType": "campaign_performance",
                "exportRequest": {
                    "exportRequestId": "export-1",
                    "format": "csv",
                    "redactionProfile": "tenant_safe",
                    "rowLimit": 50,
                    "rowCount": 1,
                    "requestStatus": "READY_FOR_FILE_STORAGE",
                    "storageStatus": "DELETED",
                    "deliveryStatus": "NOT_REQUESTED",
                    "downloadStatus": "DELETED",
                    "downloadUrl": None,
                    "expiresAt": "2026-07-31T00:00:00+00:00",
                },
                "file": {
                    "fileName": "report.csv",
                    "contentType": "text/csv",
                    "contentSha256": "sha",
                    "byteSize": 20,
                    "storageMode": "deleted",
                    "storageRef": None,
                    "contentRemovedConfirmed": True,
                    "signedUrlRemovedConfirmed": True,
                    "downloadRouteDisabledConfirmed": True,
                },
                "idempotency": {"status": "RECORDED"},
                "audit": {"accountAuditEventId": "audit-delete-1"},
                "guardrails": [
                    "NO_RAW_STORAGE_REF_EXPOSURE",
                    "NO_PROVIDER_DELIVERY_TRIGGER",
                ],
                "redactions": ["internal_tenant_identifier"],
            }

    async def fake_delete_referral_saas_report_export_file(**kwargs):
        command_calls.append(kwargs)
        return FakeExportDeleteResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "delete_referral_saas_report_export_file",
        fake_delete_referral_saas_report_export_file,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.request(
            "DELETE",
            "/v1/referral-saas/accounts/acct-1/exports/export-1",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "idempotencyKey": "export-delete-1",
                "correlationId": "corr-delete",
                "reasonCode": "OPERATOR_REQUEST",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "deleted"
    assert body["reportExport"]["commandStatus"] == "REPORT_EXPORT_FILE_DELETED"
    assert body["reportExport"]["exportRequest"]["storageStatus"] == "DELETED"
    assert body["reportExport"]["exportRequest"]["downloadStatus"] == "DELETED"
    assert body["reportExport"]["exportRequest"]["downloadUrl"] is None
    assert body["reportExport"]["file"]["storageMode"] == "deleted"
    assert body["export_file_deleted_confirmed"] is True
    assert body["signed_download_metadata_removed_confirmed"] is True
    assert body["no_provider_delivery_triggered_confirmed"] is True
    assert body["no_billing_or_money_movement_confirmed"] is True
    public_export_payload = {
        "account": body["account"],
        "account_scope": body["account_scope"],
        "reportExport": body["reportExport"],
        "redactions": body["redactions"],
    }
    assert "tenant_code" not in str(public_export_payload)
    assert command_calls
    assert command_calls[0]["account_id"] == "acct-1"
    assert command_calls[0]["export_request_id"] == "export-1"
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["correlation_id"] == "corr-delete"


async def test_referral_saas_account_report_rejects_path_scope_mismatch(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-other/reports/campaign_performance",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 400


async def test_referral_saas_account_admin_can_create_customer_scoped_campaign_setup(
    monkeypatch,
):
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    async def fake_create_referral_saas_account_campaign_setup(**kwargs):
        command_calls.append(kwargs)
        return _campaign_setup_result()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "create_referral_saas_account_campaign_setup",
        fake_create_referral_saas_account_campaign_setup,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/campaigns",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "campaign": {
                    "name": "Summer Referral",
                    "segment": "Retail",
                    "startsAt": "2026-08-01T00:00:00Z",
                    "maxUses": 100,
                },
                "setupIntent": {"reason": "Initial campaign setup"},
                "correlationId": "corr-1",
                "idempotencyKey": "campaign-create-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "created"
    assert body["campaignSetup"]["commandStatus"] == "CAMPAIGN_SETUP_DRAFT_RECORDED"
    assert body["campaignSetup"]["campaign"]["setupStatus"] == "DRAFT"
    assert body["campaignSetup"]["campaign"]["isActive"] is False
    assert body["no_campaign_activation_confirmed"] is True
    assert body["no_link_generation_confirmed"] is True
    assert body["no_validation_track_created_confirmed"] is True
    assert body["no_policy_write_confirmed"] is True
    assert body["no_money_movement_confirmed"] is True
    assert "tenantCode" not in str(body)
    assert command_calls[0]["tenant_code"] == "FNB"
    assert command_calls[0]["account_id"] == "acct-1"
    assert command_calls[0]["name"] == "Summer Referral"
    assert command_calls[0]["segment"] == "Retail"
    assert command_calls[0]["max_uses"] == 100
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["command_payload_hash"]


async def test_referral_saas_account_campaign_create_rejects_unsafe_payload():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/campaigns",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "tenantCode": "FNB",
                },
                "campaign": {
                    "name": "Summer Referral",
                    "segment": "Retail",
                    "isActive": True,
                },
                "correlationId": "corr-1",
                "idempotencyKey": "campaign-create-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert "NO_TENANT_CODE_EXPOSURE" in detail["guardrails"]
    assert detail["no_campaign_activation_confirmed"] is True
    assert detail["no_policy_write_confirmed"] is True


async def test_referral_saas_account_campaign_create_rejects_missing_required_fields():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/campaigns",
            json={
                "accountScope": {"refType": "external_tenant_ref"},
                "campaign": {"name": "Summer Referral", "segment": "Retail"},
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "validation_error"
    assert "NO_CAMPAIGN_ACTIVATION" in detail["guardrails"]


async def test_referral_saas_account_admin_can_save_campaign_policy_settings(
    monkeypatch,
):
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    async def fake_upsert_policy_settings(**kwargs):
        command_calls.append(kwargs)
        return _campaign_policy_settings_result()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "upsert_referral_saas_account_campaign_policy_settings",
        fake_upsert_policy_settings,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.put(
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/policy-settings",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "policySettings": {
                    "version": 1,
                    "attributionWindowDays": 30,
                    "eligibilityRules": [
                        {"rule": "NEW_CUSTOMER_ONLY", "enabled": True}
                    ],
                    "productWindows": {"default": {"days": 30}},
                    "productRules": {"default": {"requiresAcceptedTerms": True}},
                    "rewardVisibility": {"mode": "configured_without_payment"},
                },
                "setupIntent": {
                    "requestedStatus": "POLICY_SETTINGS_RECORDED",
                    "reason": "Complete policy settings",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "campaign-policy-settings-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["policySettings"]["commandStatus"] == "POLICY_SETTINGS_RECORDED"
    assert body["policySettings"]["policySettings"]["attributionWindowDays"] == 30
    assert body["no_campaign_activation_confirmed"] is True
    assert body["no_link_generation_confirmed"] is True
    assert body["no_validation_track_created_confirmed"] is True
    assert body["no_webhook_delivery_confirmed"] is True
    assert body["no_money_movement_confirmed"] is True
    assert "tenantCode" not in str(body)
    assert command_calls[0]["tenant_code"] == "FNB"
    assert command_calls[0]["campaign_code"] == "CAMP001"
    assert command_calls[0]["version"] == 1
    assert command_calls[0]["attribution_window_days"] == 30
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["command_payload_hash"]


async def test_referral_saas_account_campaign_policy_settings_rejects_unsafe_payload():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.put(
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/policy-settings",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "tenantCode": "FNB",
                },
                "policySettings": {
                    "version": 1,
                    "attributionWindowDays": 30,
                    "isActive": True,
                },
                "correlationId": "corr-1",
                "idempotencyKey": "campaign-policy-settings-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert "NO_TENANT_CODE_EXPOSURE" in detail["guardrails"]
    assert detail["no_campaign_activation_confirmed"] is True
    assert detail["no_money_movement_confirmed"] is True


async def test_referral_saas_account_campaign_policy_settings_requires_scope_fields():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.put(
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/policy-settings",
            json={
                "accountScope": {"refType": "external_tenant_ref"},
                "policySettings": {"version": 1, "attributionWindowDays": 30},
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "validation_error"
    assert "NO_CAMPAIGN_ACTIVATION" in detail["guardrails"]


async def test_referral_saas_account_admin_can_submit_campaign_review(monkeypatch):
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    async def fake_submit_review(**kwargs):
        command_calls.append(kwargs)
        return _campaign_review_result()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "submit_referral_saas_account_campaign_review",
        fake_submit_review,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/review-submissions",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "reviewSubmission": {
                    "setupSummary": "Campaign setup and policy settings are ready.",
                    "requestedReviewStatus": "READY_FOR_REVIEW",
                    "operatorNotes": "Reviewed policy window and terms.",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "campaign-review-submit-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["campaignReview"]["commandStatus"] == "CAMPAIGN_REVIEW_SUBMITTED"
    assert body["campaignReview"]["campaignReview"]["reviewStatus"] == "READY_FOR_REVIEW"
    assert body["campaignReview"]["campaignReview"]["activationStatus"] == "NOT_ACTIVATED"
    assert body["no_campaign_activation_confirmed"] is True
    assert body["no_link_generation_confirmed"] is True
    assert body["no_validation_track_created_confirmed"] is True
    assert body["no_webhook_delivery_confirmed"] is True
    assert body["no_invite_or_seat_change_confirmed"] is True
    assert body["no_money_movement_confirmed"] is True
    assert "tenantCode" not in str(body)
    assert command_calls[0]["tenant_code"] == "FNB"
    assert command_calls[0]["campaign_code"] == "CAMP001"
    assert command_calls[0]["setup_summary"] == "Campaign setup and policy settings are ready."
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["command_payload_hash"]


async def test_referral_saas_account_admin_can_record_campaign_review_decision(
    monkeypatch,
):
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    async def fake_record_decision(**kwargs):
        command_calls.append(kwargs)
        return _campaign_review_result(
            command_status="CAMPAIGN_REVIEW_APPROVED",
            review_status="REVIEW_APPROVED",
            readiness_status="REVIEWED",
            activation_eligibility="ELIGIBLE_FOR_FUTURE_ACTIVATION",
            reviewer_action="Open activation checklist",
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "record_referral_saas_account_campaign_review_decision",
        fake_record_decision,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/review-decisions",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "reviewDecision": {
                    "decision": "APPROVED",
                    "reason": "Campaign evidence reviewed.",
                    "reviewerRef": "operator-1",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "campaign-review-decision-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["campaignReview"]["commandStatus"] == "CAMPAIGN_REVIEW_APPROVED"
    assert body["campaignReview"]["campaignReview"]["reviewStatus"] == "REVIEW_APPROVED"
    assert (
        body["campaignReview"]["campaignReview"]["activationEligibility"]
        == "ELIGIBLE_FOR_FUTURE_ACTIVATION"
    )
    assert body["campaignReview"]["campaignReview"]["activationStatus"] == "NOT_ACTIVATED"
    assert body["no_campaign_activation_confirmed"] is True
    assert body["no_money_movement_confirmed"] is True
    assert "tenantCode" not in str(body)
    assert command_calls[0]["tenant_code"] == "FNB"
    assert command_calls[0]["campaign_code"] == "CAMP001"
    assert command_calls[0]["decision"] == "APPROVED"
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["command_payload_hash"]


async def test_referral_saas_account_admin_can_request_campaign_activation(
    monkeypatch,
):
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    async def fake_request_activation(**kwargs):
        command_calls.append(kwargs)
        return _campaign_activation_result()

    async def fake_get_referral_saas_membership_activation_readiness(**kwargs):
        return SimpleNamespace(overall_status="ACCESS_READY")

    def fake_build_referral_saas_technical_setup_readiness(**kwargs):
        return SimpleNamespace(overall_status="READY")

    class FakeProductionActivationDecision:
        def to_safe_dict(self):
            return {
                "decisionStatus": "PRODUCTION_ACTIVATION_ALLOWED",
                "launchAllowed": True,
                "disabledReasons": [],
                "plainLanguageSummary": "Production activation is allowed.",
                "guardrails": ["BACKEND_PRODUCTION_ACTIVATION_DECISION_REQUIRED"],
                "redactions": ["internal_tenant_identifier"],
            }

    def fake_build_referral_saas_production_activation_decision(**kwargs):
        return FakeProductionActivationDecision()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_membership_activation_readiness",
        fake_get_referral_saas_membership_activation_readiness,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "build_referral_saas_technical_setup_readiness",
        fake_build_referral_saas_technical_setup_readiness,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "build_referral_saas_production_activation_decision",
        fake_build_referral_saas_production_activation_decision,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "request_referral_saas_account_campaign_activation",
        fake_request_activation,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/activation-requests",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "campaign_activation",
                },
                "activationRequest": {
                    "requestedLifecycleStatus": "ACTIVE",
                    "reviewStatus": "REVIEW_APPROVED",
                    "goLiveReason": "Approved for first referral campaign test.",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "campaign-activation-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["context"] == "campaign_activation"
    activation = body["campaignActivation"]
    assert activation["commandStatus"] == "CAMPAIGN_ACTIVATION_ACCEPTED"
    assert activation["campaignActivation"]["lifecycle"] == "ACTIVE"
    assert (
        activation["campaignActivation"]["activationStatus"]
        == "ACTIVATION_REQUEST_ACCEPTED"
    )
    assert body["no_link_generation_confirmed"] is True
    assert body["no_validation_track_created_confirmed"] is True
    assert body["no_webhook_delivery_confirmed"] is True
    assert body["no_invite_or_seat_change_confirmed"] is True
    assert body["no_credential_creation_confirmed"] is True
    assert body["no_billing_or_money_movement_confirmed"] is True
    assert "tenantCode" not in str(body)
    assert command_calls[0]["tenant_code"] == "FNB"
    assert command_calls[0]["campaign_code"] == "CAMP001"
    assert command_calls[0]["requested_lifecycle_status"] == "ACTIVE"
    assert command_calls[0]["review_status"] == "REVIEW_APPROVED"
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["command_payload_hash"]
    assert command_calls[0]["production_activation_decision"]["launchAllowed"] is True


async def test_referral_saas_account_campaign_activation_requires_production_gate(
    monkeypatch,
):
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(
            account_id="acct-1",
            account_code="ACCT_FNB",
            tenant_code="FNB",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            reference_status="ACTIVE",
        )

    async def fake_get_referral_saas_membership_activation_readiness(**kwargs):
        return SimpleNamespace(overall_status="ACCESS_READY")

    def fake_build_referral_saas_technical_setup_readiness(**kwargs):
        return SimpleNamespace(overall_status="READY")

    class FakeProductionActivationDecision:
        def to_safe_dict(self):
            return {
                "decisionStatus": "PRODUCTION_ACTIVATION_BLOCKED",
                "launchAllowed": False,
                "disabledReasons": ["COMMERCIAL_ENTITLEMENT"],
                "plainLanguageSummary": "Production activation is blocked.",
                "guardrails": ["BACKEND_PRODUCTION_ACTIVATION_DECISION_REQUIRED"],
                "redactions": ["internal_tenant_identifier"],
            }

    def fake_build_referral_saas_production_activation_decision(**kwargs):
        return FakeProductionActivationDecision()

    async def fake_request_activation(**kwargs):
        command_calls.append(kwargs)
        return _campaign_activation_result()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_membership_activation_readiness",
        fake_get_referral_saas_membership_activation_readiness,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "build_referral_saas_technical_setup_readiness",
        fake_build_referral_saas_technical_setup_readiness,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "build_referral_saas_production_activation_decision",
        fake_build_referral_saas_production_activation_decision,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "request_referral_saas_account_campaign_activation",
        fake_request_activation,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/activation-requests",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "campaign_activation",
                },
                "activationRequest": {
                    "requestedLifecycleStatus": "ACTIVE",
                    "reviewStatus": "REVIEW_APPROVED",
                    "goLiveReason": "Approved for first referral campaign test.",
                },
                "correlationId": "corr-1",
                "idempotencyKey": "campaign-activation-1",
            },
        )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "PRODUCTION_ACTIVATION_BLOCKED"
    assert detail["productionActivation"]["launchAllowed"] is False
    assert detail["productionActivation"]["disabledReasons"] == [
        "COMMERCIAL_ENTITLEMENT"
    ]
    assert detail["no_campaign_activation_confirmed"] is True
    assert detail["no_billing_or_money_movement_confirmed"] is True
    assert command_calls == []


async def test_referral_saas_account_campaign_activation_rejects_unsafe_payload():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/activation-requests",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                },
                "activationRequest": {
                    "requestedLifecycleStatus": "ACTIVE",
                    "reviewStatus": "REVIEW_APPROVED",
                    "goLiveReason": "Approved",
                    "generateLinks": True,
                },
                "correlationId": "corr-1",
                "idempotencyKey": "campaign-activation-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert "NO_LINK_GENERATION" in detail["guardrails"]
    assert detail["no_link_generation_confirmed"] is True
    assert detail["no_billing_or_money_movement_confirmed"] is True


async def test_referral_saas_account_campaign_activation_requires_scope_fields():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/activation-requests",
            json={
                "accountScope": {"refType": "external_tenant_ref"},
                "activationRequest": {
                    "requestedLifecycleStatus": "ACTIVE",
                    "reviewStatus": "REVIEW_APPROVED",
                    "goLiveReason": "Approved",
                },
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "validation_error"
    assert "NO_LINK_GENERATION" in detail["guardrails"]


async def test_referral_saas_account_campaign_review_rejects_unsafe_payload():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/review-submissions",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                },
                "reviewSubmission": {
                    "setupSummary": "Ready",
                    "requestedReviewStatus": "READY_FOR_REVIEW",
                    "activate": True,
                },
                "correlationId": "corr-1",
                "idempotencyKey": "campaign-review-submit-1",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert "NO_CAMPAIGN_ACTIVATION" in detail["guardrails"]
    assert detail["no_link_generation_confirmed"] is True
    assert detail["no_money_movement_confirmed"] is True


async def test_referral_saas_account_campaign_review_requires_scope_fields():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/review-submissions",
            json={
                "accountScope": {"refType": "external_tenant_ref"},
                "reviewSubmission": {
                    "setupSummary": "Ready",
                    "requestedReviewStatus": "READY_FOR_REVIEW",
                },
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "validation_error"
    assert "NO_CAMPAIGN_ACTIVATION" in detail["guardrails"]


async def test_referral_saas_account_admin_can_read_customer_scoped_campaign(
    monkeypatch,
):
    campaign_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(tenant_code="FNB")

    async def fake_get_referral_saas_account_campaign(**kwargs):
        campaign_calls.append(kwargs)
        return _campaign_summary(campaign_code="CAMP002", status="NEEDS_POLICY")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_account_campaign",
        fake_get_referral_saas_account_campaign,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP002",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["campaign"]["campaignCode"] == "CAMP002"
    assert body["campaign"]["status"] == "NEEDS_POLICY"
    assert body["redactions"] == ["internal_tenant_identifier"]
    assert body["no_campaign_mutation_confirmed"] is True
    assert "tenantCode" not in str(body)
    assert campaign_calls == [{"tenant_code": "FNB", "campaign_code": "CAMP002"}]


async def test_referral_saas_account_campaign_list_rejects_path_scope_mismatch(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-other/campaigns",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_SCOPE"
    assert detail["no_invite_delivery_confirmed"] is True
    assert detail["no_auth_claim_change_confirmed"] is True


async def test_referral_saas_account_campaign_code_issue_resolves_account_scope(
    monkeypatch,
):
    issue_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(tenant_code="FNB")

    async def fake_get_referral_saas_account_campaign(**kwargs):
        return _campaign_summary(campaign_code="CAMP001", status="ACTIVE", lifecycle="ACTIVE")

    async def fake_get_or_create_referrer_code(**kwargs):
        issue_calls.append(kwargs)
        return (
            {
                "referral_code": "REF123",
                "gaming_handle": "edwin",
                "created": True,
                "message": "Code created",
            },
            201,
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_account_campaign",
        fake_get_referral_saas_account_campaign,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_or_create_referrer_code",
        fake_get_or_create_referrer_code,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/referral-codes",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "issueRequest": {
                    "referrerUcn": "5555555555",
                    "sticker": "QR001",
                    "segment": "PERSONAL",
                    "preferredHandle": "edwin",
                    "acceptedTerms": True,
                },
            },
        )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ok"
    assert body["linkCode"]["issueStatus"] == "CREATED"
    assert body["linkCode"]["referralCode"] == "REF123"
    assert body["campaign"]["campaignCode"] == "CAMP001"
    assert body["no_tenant_code_exposure_confirmed"] is True
    assert body["no_campaign_activation_confirmed"] is True
    assert "tenantCode" not in str(body)
    assert "tenant_code" not in str(
        {
            "account": body["account"],
            "campaign": body["campaign"],
            "linkCode": body["linkCode"],
        }
    )
    assert issue_calls == [
        {
            "referrer_ucn": "5555555555",
            "tenant": "FNB",
            "sticker": "QR001",
            "segment": "PERSONAL",
            "preferred_handle": "edwin",
            "accepted_terms": True,
        }
    ]


async def test_referral_saas_account_campaign_code_validation_resolves_account_scope(
    monkeypatch,
):
    validation_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(tenant_code="FNB")

    async def fake_get_referral_saas_account_campaign(**kwargs):
        return _campaign_summary(campaign_code="CAMP001", status="ACTIVE", lifecycle="ACTIVE")

    async def fake_validate_referral_code(**kwargs):
        validation_calls.append(kwargs)
        return (
            {
                "valid": True,
                "referral_track_id": "11111111-1111-4111-8111-111111111111",
                "message": "Referral code validated",
            },
            200,
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_account_campaign",
        fake_get_referral_saas_account_campaign,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "validate_referral_code",
        fake_validate_referral_code,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/referrals/validate",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "validationRequest": {
                    "referralCode": "REF123",
                    "acceptedTerms": True,
                    "alias": "customer-alias",
                },
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["campaign"]["campaignCode"] == "CAMP001"
    assert body["validation"]["validationStatus"] == "VALIDATED"
    assert body["no_tenant_code_exposure_confirmed"] is True
    assert "tenantCode" not in str(body)
    assert "tenant_code" not in str(
        {
            "account": body["account"],
            "campaign": body["campaign"],
            "validation": body["validation"],
        }
    )
    assert validation_calls == [
        {
            "referral_code": "REF123",
            "tenant_code": "FNB",
            "accepted_terms": True,
            "alias": "customer-alias",
            "device_fingerprint": None,
            "ip_address": None,
            "qr_code": None,
        }
    ]


async def test_referral_saas_account_campaign_links_require_active_campaign(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(tenant_code="FNB")

    async def fake_get_referral_saas_account_campaign(**kwargs):
        return _campaign_summary(campaign_code="CAMP002", status="DRAFT", lifecycle="DRAFT")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_account_campaign",
        fake_get_referral_saas_account_campaign,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/campaigns/CAMP002/referral-codes",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "issueRequest": {
                    "referrerUcn": "5555555555",
                    "sticker": "QR001",
                    "segment": "PERSONAL",
                    "acceptedTerms": True,
                },
            },
        )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "campaign_not_active"
    assert "ACTIVE_CAMPAIGN_REQUIRED" in detail["guardrails"]
    assert detail["no_campaign_activation_confirmed"] is True
    assert "tenant_code" not in str(detail)


async def test_referral_saas_account_campaign_read_maps_missing_campaign(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(tenant_code="FNB")

    async def fake_get_referral_saas_account_campaign(**kwargs):
        return None

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_account_campaign",
        fake_get_referral_saas_account_campaign,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/campaigns/UNKNOWN",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["code"] == "campaign_not_found"
    assert detail["redactions"] == ["internal_tenant_identifier"]


async def test_referral_saas_account_campaign_readiness_rejects_path_scope_mismatch(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-other/campaigns/CAMP001/readiness",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_SCOPE"
    assert detail["no_invite_delivery_confirmed"] is True
    assert detail["no_auth_claim_change_confirmed"] is True


async def test_referral_saas_account_campaign_readiness_maps_missing_campaign(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(tenant_code="FNB")

    async def fake_get_campaign_readiness(**kwargs):
        return {
            "campaign_code": "UNKNOWN",
            "readiness": "BLOCKED",
            "can_proceed": False,
            "blockers": [
                {
                    "code": "CAMPAIGN_NOT_FOUND",
                    "message": "Campaign readiness was not found.",
                }
            ],
            "warnings": [],
            "unknowns": [],
        }

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_campaign_readiness",
        fake_get_campaign_readiness,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/campaigns/UNKNOWN/readiness",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["code"] == "campaign_readiness_not_found"
    assert detail["redactions"] == ["internal_tenant_identifier"]


async def test_referral_saas_invitation_delivery_rejects_missing_delivery_fields():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/membership-invitations/membership-1/delivery",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                },
                "delivery": {"channel": "EMAIL"},
                "correlationId": "corr-1",
                "idempotencyKey": "delivery-1",
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "validation_error"
    assert detail["no_invite_delivery_confirmed"] is True
    assert detail["no_membership_activation_confirmed"] is True


async def test_referral_saas_invitation_delivery_rejects_adjacent_role():
    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/membership-invitations/membership-1/delivery",
            json={},
        )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "permission_denied"


async def test_referral_saas_account_reader_can_resolve_setup_context(monkeypatch):
    calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        calls.append(kwargs)
        return _context(account_status="SUSPENDED", tenant_link_status="SUSPENDED")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/resolve",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["context"] == "setup"
    assert body["account"]["accountStatus"] == "SUSPENDED"
    assert body["account"]["operatingJurisdictionCode"] == "ZA"
    assert calls == [
        {
            "ref_type": "external_tenant_ref",
            "external_ref": "fnb-referrals",
        }
    ]


async def test_referral_saas_account_resolver_rejects_cross_account_identity(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context()

    monkeypatch.setattr(
        referral_saas_accounts,
        "_require_referral_saas_account_reader",
        lambda identity: {
            "role": "DISTRIBUTION_ADMIN",
            "account_ref": "acct-other",
            "scopes": ["REFERRAL_SAAS_ACCOUNT_READ"],
        },
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/resolve",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["code"] == "account_boundary_forbidden"
    assert "SERVER_SIDE_ACCOUNT_CONTEXT_ENFORCEMENT" in detail["guardrails"]
    assert detail["no_cross_account_access_confirmed"] is True


async def test_referral_saas_account_resolver_rejects_cross_jurisdiction_identity(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(operating_jurisdiction_code="ZA")

    monkeypatch.setattr(
        referral_saas_accounts,
        "_require_referral_saas_account_reader",
        lambda identity: {
            "role": "DISTRIBUTION_ADMIN",
            "allowed_jurisdictions": ["BW"],
            "scopes": ["REFERRAL_SAAS_ACCOUNT_READ"],
        },
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/resolve",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["code"] == "account_boundary_forbidden"
    assert "SERVER_SIDE_ACCOUNT_JURISDICTION_ENFORCEMENT" in detail["guardrails"]
    assert detail["no_cross_jurisdiction_access_confirmed"] is True
    assert "tenantCode" not in str(detail)


async def test_referral_saas_membership_posture_rejects_missing_account_capability(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context()

    monkeypatch.setattr(
        referral_saas_accounts,
        "_require_referral_saas_account_reader",
        lambda identity: {
            "role": "DISTRIBUTION_ADMIN",
            "account_ref": "acct-1",
            "allowed_jurisdictions": ["ZA"],
            "scopes": ["REFERRAL_SAAS_REPORT_READ"],
        },
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/membership-posture",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["code"] == "account_boundary_forbidden"
    assert "SERVER_SIDE_ACCOUNT_CAPABILITY_ENFORCEMENT" in detail["guardrails"]
    assert detail["no_capability_bypass_confirmed"] is True


async def test_referral_saas_account_reader_can_read_membership_posture(monkeypatch):
    resolve_calls: list[dict] = []
    posture_calls: list[dict] = []

    class FakePosture:
        def to_safe_dict(self):
            return {
                "accountId": "acct-1",
                "totalMemberships": 0,
                "activeCount": 0,
                "invitedCount": 0,
                "currentActor": {
                    "status": "NO_MEMBERSHIP_EVIDENCE",
                    "roleFamily": None,
                    "permissionSet": None,
                    "canOperateSetup": False,
                    "evidence": "No active account membership matched the current actor.",
                },
                "guardrails": [
                    "READ_ONLY_MEMBERSHIP_POSTURE",
                    "NO_MEMBERSHIP_WRITE",
                    "NO_INVITE_DELIVERY",
                ],
                "redactions": [
                    "internal_tenant_identifier",
                    "user_identifier",
                    "client_identifier",
                ],
                "noMembershipWriteConfirmed": True,
                "noInviteDeliveryConfirmed": True,
            }

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context()

    async def fake_get_referral_saas_account_membership_posture(**kwargs):
        posture_calls.append(kwargs)
        return FakePosture()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_account_membership_posture",
        fake_get_referral_saas_account_membership_posture,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/membership-posture",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["context"] == "setup"
    assert body["account"]["accountCode"] == "ACCT_FNB"
    assert "tenantCode" not in body["account"]
    assert body["membershipPosture"]["currentActor"]["status"] == "NO_MEMBERSHIP_EVIDENCE"
    assert body["membershipPosture"]["noMembershipWriteConfirmed"] is True
    assert body["membershipPosture"]["noInviteDeliveryConfirmed"] is True
    assert body["no_membership_write_confirmed"] is True
    assert body["no_invite_delivery_confirmed"] is True
    assert "tenantCode" not in body["membershipPosture"]
    assert "clientId" not in str(body)
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert posture_calls == [
        {
            "account_id": "acct-1",
            "tenant_code": "FNB",
            "actor_ref": None,
            "actor_client_id": None,
        }
    ]


async def test_referral_saas_account_reader_can_read_membership_activation_readiness(
    monkeypatch,
):
    resolve_calls: list[dict] = []
    readiness_calls: list[dict] = []

    class FakeReadiness:
        def to_safe_dict(self):
            return {
                "accountId": "acct-1",
                "overallStatus": "ACTION_REQUIRED",
                "activeCount": 0,
                "invitedCount": 1,
                "deliveryReadyCount": 0,
                "activationReadyCount": 0,
                "missingRoleFamilies": ["CAMPAIGN_MANAGER"],
                "items": [
                    {
                        "subject": "owner@example.test",
                        "displayName": "Setup Owner",
                        "roleFamily": "DISTRIBUTION_ADMIN",
                        "membershipStatus": "INVITED",
                        "deliveryStatus": "DELIVERY_NOT_CONFIGURED",
                        "recipientContactStatus": "CONTACT_REFERENCE_PRESENT",
                        "deliveryReadiness": "BLOCKED",
                        "activationReadiness": "BLOCKED",
                        "blockers": ["DELIVERY_PROVIDER_NOT_CONFIGURED"],
                        "nextAction": "Configure an approved invitation delivery provider before sending invites.",
                    }
                ],
                "guardrails": ["READ_ONLY_ACTIVATION_READINESS"],
                "redactions": ["internal_tenant_identifier"],
                "noInviteDeliveryConfirmed": True,
                "noMembershipActivationConfirmed": True,
                "noSeatAssignmentConfirmed": True,
                "noAuthClaimChangeConfirmed": True,
            }

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        resolve_calls.append(kwargs)
        return _context(
            account_status="PENDING_ONBOARDING",
            reference_status="ACTIVE",
            tenant_link_status="PENDING_SETUP",
        )

    async def fake_get_referral_saas_membership_activation_readiness(**kwargs):
        readiness_calls.append(kwargs)
        return FakeReadiness()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_membership_activation_readiness",
        fake_get_referral_saas_membership_activation_readiness,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/membership-activation-readiness",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["account"]["accountCode"] == "ACCT_FNB"
    assert body["activationReadiness"]["overallStatus"] == "ACTION_REQUIRED"
    assert body["activationReadiness"]["missingRoleFamilies"] == ["CAMPAIGN_MANAGER"]
    assert body["no_invite_delivery_confirmed"] is True
    assert body["no_membership_activation_confirmed"] is True
    assert body["no_auth_claim_change_confirmed"] is True
    assert body["no_seat_assignment_confirmed"] is True
    assert body["no_money_movement_confirmed"] is True
    assert "tenantCode" not in body["account"]
    assert "tenantCode" not in body["activationReadiness"]
    assert resolve_calls == [
        {"ref_type": "external_tenant_ref", "external_ref": "fnb-referrals"}
    ]
    assert readiness_calls == [
        {
            "account_id": "acct-1",
            "tenant_code": "FNB",
            "account_status": "PENDING_ONBOARDING",
            "tenant_link_status": "PENDING_SETUP",
            "external_reference_status": "ACTIVE",
        }
    ]


async def test_referral_saas_membership_activation_readiness_rejects_mismatched_account_ref(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/other-account/membership-activation-readiness",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "REJECTED_UNSAFE_SCOPE"
    assert detail["no_invite_delivery_confirmed"] is True
    assert detail["no_auth_claim_change_confirmed"] is True


async def test_referral_saas_membership_posture_rejects_adjacent_role():
    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/membership-posture",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "permission_denied"


async def test_referral_saas_account_reader_rejects_adjacent_role():
    async with AsyncClient(app=app, base_url="http://test", headers=PARTNER_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/resolve",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "permission_denied"


async def test_referral_saas_account_reader_rejects_invalid_context():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/resolve",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "maintenance",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "validation_error"


@pytest.mark.parametrize(
    ("error", "status_code", "safe_code"),
    [
        (
            InvalidExternalReferenceType("Unsupported reference type."),
            400,
            "INVALID_EXTERNAL_REFERENCE_TYPE",
        ),
        (
            ExternalReferenceNotFound("Missing reference."),
            404,
            "EXTERNAL_REFERENCE_NOT_FOUND",
        ),
        (
            ExternalReferenceConflict("Duplicate active reference."),
            409,
            "EXTERNAL_REFERENCE_CONFLICT",
        ),
        (
            ExternalReferenceNotActive("Reference is disabled."),
            409,
            "EXTERNAL_REFERENCE_NOT_ACTIVE",
        ),
        (
            AccountNotResolvable("Account is suspended."),
            409,
            "ACCOUNT_NOT_RESOLVABLE",
        ),
        (
            TenantLinkNotResolvable("Tenant link is disabled."),
            409,
            "TENANT_LINK_NOT_RESOLVABLE",
        ),
    ],
)
async def test_referral_saas_account_reader_maps_safe_resolution_errors(
    monkeypatch,
    error,
    status_code,
    safe_code,
):
    async def fake_resolve_account_by_external_reference(**kwargs):
        raise error

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_account_by_external_reference",
        fake_resolve_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/resolve",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
            },
        )

    assert response.status_code == status_code
    assert response.json()["detail"]["code"] == safe_code


async def test_referral_saas_account_admin_can_create_customer_scoped_support_case(
    monkeypatch,
):
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    class FakeSupportCaseResult:
        def to_safe_dict(self):
            return {
                "commandStatus": "SUPPORT_CASE_RECORDED",
                "supportCase": {
                    "caseRef": "case-1",
                    "accountRef": "acct-1",
                    "category": "READINESS_BLOCKER",
                    "priority": "HIGH",
                    "status": "OPEN",
                    "title": "Campaign setup is blocked",
                    "summary": "People and access setup needs review.",
                    "sourceSurface": "customer_home",
                    "evidenceLinks": [
                        {
                            "evidenceType": "PEOPLE_ACCESS",
                            "evidenceRef": "acct-1:people",
                            "safeStatus": "ACTION_REQUIRED",
                            "redactions": ["internal_tenant_identifier"],
                        }
                    ],
                    "redactions": ["internal_tenant_identifier"],
                },
                "idempotency": {"status": "RECORDED"},
                "audit": {"accountAuditEventId": "audit-1"},
                "guardrails": ["NO_REPAIR_REPLAY_RETRY"],
                "redactions": ["internal_tenant_identifier"],
            }

    async def fake_create_referral_saas_support_case(**kwargs):
        command_calls.append(kwargs)
        return FakeSupportCaseResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "create_referral_saas_support_case",
        fake_create_referral_saas_support_case,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/support-cases",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "support",
                },
                "category": "READINESS_BLOCKER",
                "priority": "HIGH",
                "title": "Campaign setup is blocked",
                "summary": "People and access setup needs review.",
                "sourceSurface": "customer_home",
                "evidenceLinks": [
                    {
                        "evidenceType": "PEOPLE_ACCESS",
                        "evidenceRef": "acct-1:people",
                        "safeStatus": "ACTION_REQUIRED",
                    }
                ],
                "idempotencyKey": "support-case-1",
                "correlationId": "corr-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert body["supportCase"]["commandStatus"] == "SUPPORT_CASE_RECORDED"
    assert body["supportCase"]["supportCase"]["caseRef"] == "case-1"
    assert body["no_repair_replay_retry_confirmed"] is True
    assert body["no_billing_or_money_movement_confirmed"] is True
    public_payload = {
        "account": body["account"],
        "account_scope": body["account_scope"],
        "supportCase": body["supportCase"],
    }
    assert "tenant_code" not in str(public_payload)
    assert command_calls
    assert command_calls[0]["account_id"] == "acct-1"
    assert command_calls[0]["tenant_code"] == "FNB"
    assert command_calls[0]["category"] == "READINESS_BLOCKER"
    assert command_calls[0]["priority"] == "HIGH"
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["request_payload_hash"]
    assert command_calls[0]["correlation_id"] == "corr-1"


async def test_referral_saas_account_support_case_rejects_unsafe_payload(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/support-cases",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "support",
                },
                "category": "READINESS_BLOCKER",
                "priority": "HIGH",
                "title": "Unsafe support case",
                "summary": "This should be rejected.",
                "evidenceLinks": [
                    {
                        "evidenceType": "PEOPLE_ACCESS",
                        "evidenceRef": "acct-1:people",
                        "metadata": {"raw_ucn": "1234567890"},
                    }
                ],
                "idempotencyKey": "support-case-1",
                "correlationId": "corr-1",
            },
        )

    assert response.status_code == 400
    body = response.json()
    assert body["detail"]["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert body["detail"]["no_repair_replay_retry_confirmed"] is True
    assert body["detail"]["no_billing_or_money_movement_confirmed"] is True


async def test_referral_saas_account_support_case_idempotency_conflict(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    async def fake_create_referral_saas_support_case(**kwargs):
        raise SupportCaseIdempotencyConflict(
            "Idempotency key was reused with different support-case content."
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "create_referral_saas_support_case",
        fake_create_referral_saas_support_case,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/support-cases",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "setup",
                },
                "category": "READINESS_BLOCKER",
                "priority": "HIGH",
                "title": "Campaign setup is blocked",
                "summary": "People and access setup needs review.",
                "idempotencyKey": "support-case-1",
                "correlationId": "corr-1",
            },
        )

    assert response.status_code == 409
    body = response.json()
    assert body["detail"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert body["detail"]["no_repair_replay_retry_confirmed"] is True


async def test_referral_saas_account_admin_can_list_customer_scoped_support_cases(
    monkeypatch,
):
    list_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    class FakeSupportCase:
        def to_safe_dict(self):
            return {
                "caseRef": "case-1",
                "accountRef": "acct-1",
                "category": "ACCESS_SCOPE",
                "priority": "MEDIUM",
                "status": "OPEN",
                "title": "People access check",
                "summary": "Confirm account owner.",
                "evidenceLinks": [],
                "redactions": ["internal_tenant_identifier"],
            }

    async def fake_list_referral_saas_support_cases(**kwargs):
        list_calls.append(kwargs)
        return [FakeSupportCase()]

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "list_referral_saas_support_cases",
        fake_list_referral_saas_support_cases,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/support-cases",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "support",
                "status": "OPEN",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["supportCases"][0]["caseRef"] == "case-1"
    assert body["no_product_state_mutation_confirmed"] is True
    assert list_calls == [
        {"account_id": "acct-1", "status_filter": "OPEN", "limit": 50}
    ]


async def test_referral_saas_account_admin_can_list_operator_support_queue(
    monkeypatch,
):
    queue_calls: list[dict] = []

    class FakeQueue:
        def to_safe_dict(self):
            return {
                "supportCases": [
                    {
                        "caseRef": "case-1",
                        "accountRef": "acct-1",
                        "customerLabel": "FNB Referral SaaS",
                        "externalTenantRef": "fnb-referrals",
                        "organisationRef": "fnb-org",
                        "category": "ACCESS_SCOPE",
                        "priority": "HIGH",
                        "status": "OPEN",
                        "title": "People access check",
                        "sourceSurface": "people_access",
                        "evidenceLinkCount": 1,
                        "noteCount": 0,
                        "latestActivity": "Case updated",
                        "redactions": ["internal_tenant_identifier"],
                        "nextAction": "Open customer support case",
                    }
                ],
                "filters": {"status": "OPEN", "limit": 25},
                "nextCursor": None,
                "guardrails": ["READ_ONLY_QUEUE"],
                "redactions": ["internal_tenant_identifier"],
            }

    async def fake_list_referral_saas_operator_support_queue(**kwargs):
        queue_calls.append(kwargs)
        return FakeQueue()

    monkeypatch.setattr(
        referral_saas_accounts,
        "list_referral_saas_operator_support_queue",
        fake_list_referral_saas_operator_support_queue,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/operator/support-cases",
            params={
                "status": "OPEN",
                "priority": "HIGH",
                "category": "ACCESS_SCOPE",
                "account_ref": "ACCT_FNB",
                "source_surface": "people_access",
                "assignee_ref": "operator-1",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["supportQueue"]["supportCases"][0]["caseRef"] == "case-1"
    assert body["supportQueue"]["supportCases"][0]["nextAction"] == (
        "Open customer support case"
    )
    assert body["operatorScope"]["surface"] == "operator_support_queue"
    assert body["no_assignment_from_queue_confirmed"] is True
    assert body["no_case_lifecycle_mutation_confirmed"] is True
    assert body["no_tenant_code_exposure_confirmed"] is True
    assert queue_calls == [
        {
            "status_filter": "OPEN",
            "priority": "HIGH",
            "category": "ACCESS_SCOPE",
            "account_ref": "ACCT_FNB",
            "source_surface": "people_access",
            "assignee_ref": "operator-1",
            "created_from": None,
            "created_to": None,
            "updated_from": None,
            "updated_to": None,
            "limit": 25,
            "cursor": None,
        }
    ]


async def test_referral_saas_account_admin_can_read_customer_scoped_support_case(
    monkeypatch,
):
    read_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    class FakeSupportCase:
        def to_safe_dict(self):
            return {
                "caseRef": "case-1",
                "accountRef": "acct-1",
                "category": "ACCESS_SCOPE",
                "priority": "MEDIUM",
                "status": "OPEN",
                "title": "People access check",
                "summary": "Confirm account owner.",
                "evidenceLinks": [{"evidenceType": "PEOPLE_ACCESS"}],
                "redactions": ["internal_tenant_identifier"],
            }

    async def fake_get_referral_saas_support_case(**kwargs):
        read_calls.append(kwargs)
        return FakeSupportCase()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_support_case",
        fake_get_referral_saas_support_case,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/support-cases/case-1",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["supportCase"]["caseRef"] == "case-1"
    assert body["no_product_state_mutation_confirmed"] is True
    assert read_calls == [{"account_id": "acct-1", "case_ref": "case-1"}]


async def test_referral_saas_account_admin_can_read_support_case_repair_replay_readiness(
    monkeypatch,
):
    readiness_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    class FakeReadiness:
        def to_safe_dict(self):
            return {
                "caseRef": "case-1",
                "accountRef": "acct-1",
                "category": "PROGRESS_DIAGNOSTIC",
                "overallStatus": "REVIEW_REQUIRED",
                "owningWorkflow": "progress_status",
                "allowedActions": [
                    {
                        "action": "READ_ONLY_DIAGNOSTIC",
                        "status": "AVAILABLE",
                        "label": "Review support evidence",
                    },
                    {
                        "action": "GOVERNED_REPLAY",
                        "status": "BLOCKED",
                        "reasonCode": "FUTURE_GOVERNED_COMMAND_REQUIRED",
                        "label": "Replay stored progress evidence",
                    },
                ],
                "requiredEvidence": [
                    "support_case_link",
                    "actor",
                    "reason",
                    "correlation_id",
                    "idempotency_key",
                    "target_evidence",
                    "before_state_hash",
                ],
                "guardrails": ["READINESS_ONLY", "NO_PROVIDER_DISPATCH"],
                "redactions": ["internal_tenant_identifier", "provider_payload"],
                "no_repair_replay_retry_confirmed": True,
                "no_provider_dispatch_confirmed": True,
                "no_credential_or_auth_claim_change_confirmed": True,
                "no_campaign_activation_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            }

    async def fake_get_referral_saas_support_case_repair_replay_readiness(**kwargs):
        readiness_calls.append(kwargs)
        return FakeReadiness()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "get_referral_saas_support_case_repair_replay_readiness",
        fake_get_referral_saas_support_case_repair_replay_readiness,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/v1/referral-saas/accounts/acct-1/support-cases/case-1/repair-replay-readiness",
            params={
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "context": "setup",
            },
        )

    assert response.status_code == 200
    body = response.json()
    readiness = body["repairReplayReadiness"]
    assert readiness["overallStatus"] == "REVIEW_REQUIRED"
    assert readiness["allowedActions"][1]["action"] == "GOVERNED_REPLAY"
    assert readiness["allowedActions"][1]["status"] == "BLOCKED"
    assert "before_state_hash" in readiness["requiredEvidence"]
    assert body["no_repair_replay_retry_confirmed"] is True
    assert body["no_provider_dispatch_confirmed"] is True
    assert body["no_credential_or_auth_claim_change_confirmed"] is True
    assert body["no_campaign_activation_confirmed"] is True
    assert body["no_billing_or_money_movement_confirmed"] is True
    assert "repairCommand" not in body
    assert "replayCommand" not in body
    assert readiness_calls == [{"account_id": "acct-1", "case_ref": "case-1"}]


async def test_referral_saas_account_admin_can_record_support_case_repair_command(
    monkeypatch,
):
    command_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    class FakeRepairCommandResult:
        def to_safe_dict(self):
            return {
                "commandStatus": "SUPPORT_CASE_REPAIR_COMMAND_RECORDED",
                "supportCase": {
                    "caseRef": "case-1",
                    "accountRef": "acct-1",
                    "status": "OPEN",
                    "redactions": ["internal_tenant_identifier"],
                },
                "repairCommand": {
                    "repairCommandRef": "cmd-1",
                    "caseRef": "case-1",
                    "accountRef": "acct-1",
                    "commandType": "GOVERNED_REPAIR",
                    "commandStatus": "RECORDED",
                    "targetEvidenceType": "LINK_CODE_INSPECTION",
                    "targetEvidenceRef": "evidence-1",
                    "beforeStateHash": "before-hash-123",
                    "impactPreview": {"expectedState": "validation evidence repaired"},
                    "approvalRef": "approval-1",
                    "rollbackPlan": "Revert to the before-state hash if validation fails.",
                },
                "idempotency": {"status": "RECORDED"},
                "audit": {"accountAuditEventId": "audit-1"},
                "guardrails": ["COMMAND_LEDGER_ONLY", "NO_BROAD_DB_MUTATION"],
                "redactions": ["internal_tenant_identifier"],
                "no_provider_dispatch_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            }

    async def fake_execute_referral_saas_support_case_repair_command(**kwargs):
        command_calls.append(kwargs)
        return FakeRepairCommandResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "execute_referral_saas_support_case_repair_command",
        fake_execute_referral_saas_support_case_repair_command,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/support-cases/case-1/repair-replay-commands",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "support",
                },
                "commandType": "GOVERNED_REPAIR",
                "targetEvidenceType": "LINK_CODE_INSPECTION",
                "targetEvidenceRef": "evidence-1",
                "beforeStateHash": "before-hash-123",
                "impactPreview": {"expectedState": "validation evidence repaired"},
                "approvalRef": "approval-1",
                "rollbackPlan": "Revert to the before-state hash if validation fails.",
                "idempotencyKey": "repair-command-1",
                "correlationId": "corr-repair-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    command = body["repairReplayCommand"]
    assert command["commandStatus"] == "SUPPORT_CASE_REPAIR_COMMAND_RECORDED"
    assert command["repairCommand"]["commandType"] == "GOVERNED_REPAIR"
    assert body["no_provider_dispatch_confirmed"] is True
    assert body["no_referral_or_campaign_mutation_confirmed"] is True
    assert body["no_billing_or_money_movement_confirmed"] is True
    assert command_calls
    assert command_calls[0]["account_id"] == "acct-1"
    assert command_calls[0]["tenant_code"] == "FNB"
    assert command_calls[0]["case_ref"] == "case-1"
    assert command_calls[0]["command_type"] == "GOVERNED_REPAIR"
    assert command_calls[0]["target_evidence_ref"] == "evidence-1"
    assert command_calls[0]["approval_ref"] == "approval-1"
    assert command_calls[0]["idempotency_key_hash"]
    assert command_calls[0]["request_payload_hash"]
    assert command_calls[0]["correlation_id"] == "corr-repair-1"


async def test_referral_saas_support_case_repair_command_rejects_unsafe_payload(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/support-cases/case-1/repair-replay-commands",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "support",
                },
                "commandType": "GOVERNED_REPAIR",
                "targetEvidenceType": "LINK_CODE_INSPECTION",
                "targetEvidenceRef": "evidence-1",
                "beforeStateHash": "before-hash-123",
                "impactPreview": {"providerPayload": {"raw": "blocked"}},
                "approvalRef": "approval-1",
                "rollbackPlan": "Revert to the before-state hash if validation fails.",
                "idempotencyKey": "repair-command-unsafe",
                "correlationId": "corr-repair-unsafe",
            },
        )

    assert response.status_code == 400
    body = response.json()
    assert body["detail"]["code"] == "REJECTED_UNSAFE_PAYLOAD"
    assert body["detail"]["no_billing_or_money_movement_confirmed"] is True


async def test_referral_saas_support_case_repair_command_idempotency_conflict_maps_409(
    monkeypatch,
):
    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    async def fake_execute_referral_saas_support_case_repair_command(**kwargs):
        raise referral_saas_accounts.SupportCaseIdempotencyConflict(
            "Idempotency key was reused with different support-case command content."
        )

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "execute_referral_saas_support_case_repair_command",
        fake_execute_referral_saas_support_case_repair_command,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/support-cases/case-1/repair-replay-commands",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "support",
                },
                "commandType": "GOVERNED_REPAIR",
                "targetEvidenceType": "LINK_CODE_INSPECTION",
                "targetEvidenceRef": "evidence-1",
                "beforeStateHash": "before-hash-123",
                "impactPreview": {"expectedState": "validation evidence repaired"},
                "approvalRef": "approval-1",
                "rollbackPlan": "Revert to the before-state hash if validation fails.",
                "idempotencyKey": "repair-command-conflict",
                "correlationId": "corr-repair-conflict",
            },
        )

    assert response.status_code == 409
    body = response.json()
    assert body["detail"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert body["detail"]["no_billing_or_money_movement_confirmed"] is True


async def test_referral_saas_account_admin_can_add_customer_scoped_support_case_note(
    monkeypatch,
):
    note_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    class FakeSupportCaseNoteResult:
        def to_safe_dict(self):
            return {
                "commandStatus": "SUPPORT_CASE_NOTE_RECORDED",
                "supportCase": {
                    "caseRef": "case-1",
                    "accountRef": "acct-1",
                    "status": "OPEN",
                    "notes": [{"noteRef": "note-1", "noteText": "Called customer."}],
                    "statusEvents": [],
                    "redactions": ["internal_tenant_identifier"],
                },
                "note": {
                    "noteRef": "note-1",
                    "caseRef": "case-1",
                    "noteType": "OPERATOR_NOTE",
                    "noteText": "Called customer.",
                },
                "idempotency": {"status": "RECORDED"},
                "audit": {"accountAuditEventId": "audit-1"},
                "guardrails": ["NO_REPAIR_REPLAY_RETRY"],
                "redactions": ["internal_tenant_identifier"],
            }

    async def fake_add_referral_saas_support_case_note(**kwargs):
        note_calls.append(kwargs)
        return FakeSupportCaseNoteResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "add_referral_saas_support_case_note",
        fake_add_referral_saas_support_case_note,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/support-cases/case-1/notes",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "support",
                },
                "noteType": "OPERATOR_NOTE",
                "noteText": "Called customer.",
                "idempotencyKey": "support-case-note-1",
                "correlationId": "corr-note-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert body["supportCaseLifecycle"]["commandStatus"] == "SUPPORT_CASE_NOTE_RECORDED"
    assert body["supportCaseLifecycle"]["note"]["noteRef"] == "note-1"
    assert body["no_repair_replay_retry_confirmed"] is True
    assert body["no_billing_or_money_movement_confirmed"] is True
    assert note_calls
    assert note_calls[0]["account_id"] == "acct-1"
    assert note_calls[0]["tenant_code"] == "FNB"
    assert note_calls[0]["case_ref"] == "case-1"
    assert note_calls[0]["note_type"] == "OPERATOR_NOTE"
    assert note_calls[0]["note_text"] == "Called customer."
    assert note_calls[0]["idempotency_key_hash"]
    assert note_calls[0]["request_payload_hash"]
    assert note_calls[0]["correlation_id"] == "corr-note-1"


async def test_referral_saas_account_admin_can_change_customer_scoped_support_case_status(
    monkeypatch,
):
    status_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    class FakeSupportCaseStatusResult:
        def to_safe_dict(self):
            return {
                "commandStatus": "SUPPORT_CASE_STATUS_RECORDED",
                "supportCase": {
                    "caseRef": "case-1",
                    "accountRef": "acct-1",
                    "status": "INVESTIGATING",
                    "notes": [],
                    "statusEvents": [
                        {
                            "statusEventRef": "status-event-1",
                            "fromStatus": "OPEN",
                            "toStatus": "INVESTIGATING",
                        }
                    ],
                    "redactions": ["internal_tenant_identifier"],
                },
                "statusEvent": {
                    "statusEventRef": "status-event-1",
                    "caseRef": "case-1",
                    "fromStatus": "OPEN",
                    "toStatus": "INVESTIGATING",
                    "transitionReason": "Operator picked up the case.",
                },
                "idempotency": {"status": "RECORDED"},
                "audit": {"accountAuditEventId": "audit-1"},
                "guardrails": ["NO_REPAIR_REPLAY_RETRY"],
                "redactions": ["internal_tenant_identifier"],
            }

    async def fake_change_referral_saas_support_case_status(**kwargs):
        status_calls.append(kwargs)
        return FakeSupportCaseStatusResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "change_referral_saas_support_case_status",
        fake_change_referral_saas_support_case_status,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/support-cases/case-1/status",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "support",
                },
                "status": "INVESTIGATING",
                "transitionReason": "Operator picked up the case.",
                "idempotencyKey": "support-case-status-1",
                "correlationId": "corr-status-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert body["supportCaseLifecycle"]["commandStatus"] == "SUPPORT_CASE_STATUS_RECORDED"
    assert body["supportCaseLifecycle"]["statusEvent"]["toStatus"] == "INVESTIGATING"
    assert body["no_repair_replay_retry_confirmed"] is True
    assert body["no_billing_or_money_movement_confirmed"] is True
    assert status_calls
    assert status_calls[0]["account_id"] == "acct-1"
    assert status_calls[0]["tenant_code"] == "FNB"
    assert status_calls[0]["case_ref"] == "case-1"
    assert status_calls[0]["to_status"] == "INVESTIGATING"
    assert status_calls[0]["transition_reason"] == "Operator picked up the case."
    assert status_calls[0]["idempotency_key_hash"]
    assert status_calls[0]["request_payload_hash"]
    assert status_calls[0]["correlation_id"] == "corr-status-1"


async def test_referral_saas_account_admin_can_assign_customer_scoped_support_case(
    monkeypatch,
):
    assignment_calls: list[dict] = []

    async def fake_resolve_setup_account_by_external_reference(**kwargs):
        return _context(account_id="acct-1", account_code="ACCT_FNB", tenant_code="FNB")

    class FakeSupportCaseAssignmentResult:
        def to_safe_dict(self):
            return {
                "commandStatus": "SUPPORT_CASE_ASSIGNED",
                "supportCase": {
                    "caseRef": "case-1",
                    "accountRef": "acct-1",
                    "status": "INVESTIGATING",
                    "title": "Referral code validation failed",
                    "summary": "Customer cannot validate a safe referral code.",
                    "assigneeRef": "amplifi-support",
                    "notes": [],
                    "statusEvents": [],
                    "redactions": ["internal_tenant_identifier"],
                },
                "assignment": {
                    "previousAssigneeRef": None,
                    "assigneeRef": "amplifi-support",
                },
                "idempotency": {"status": "RECORDED"},
                "audit": {"accountAuditEventId": "audit-1"},
                "guardrails": ["NO_REPAIR_REPLAY_RETRY"],
                "redactions": ["internal_tenant_identifier"],
                "no_repair_replay_retry_confirmed": True,
                "no_referral_or_campaign_mutation_confirmed": True,
                "no_progress_or_attribution_mutation_confirmed": True,
                "no_report_or_export_mutation_confirmed": True,
                "no_invite_delivery_confirmed": True,
                "no_credential_or_auth_claim_change_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            }

    async def fake_assign_referral_saas_support_case(**kwargs):
        assignment_calls.append(kwargs)
        return FakeSupportCaseAssignmentResult()

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
    )
    monkeypatch.setattr(
        referral_saas_accounts,
        "assign_referral_saas_support_case",
        fake_assign_referral_saas_support_case,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/v1/referral-saas/accounts/acct-1/support-cases/case-1/assignment",
            json={
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "fnb-referrals",
                    "context": "support",
                },
                "assigneeRef": "amplifi-support",
                "assignmentReason": "Operator owns customer recovery follow-up.",
                "idempotencyKey": "support-case-assignment-1",
                "correlationId": "corr-assignment-1",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert body["supportCaseAssignment"]["commandStatus"] == "SUPPORT_CASE_ASSIGNED"
    assert body["supportCaseAssignment"]["assignment"]["assigneeRef"] == "amplifi-support"
    assert body["supportCaseAssignment"]["supportCase"]["assigneeRef"] == "amplifi-support"
    assert body["no_repair_replay_retry_confirmed"] is True
    assert body["no_billing_or_money_movement_confirmed"] is True
    assert assignment_calls
    assert assignment_calls[0]["account_id"] == "acct-1"
    assert assignment_calls[0]["tenant_code"] == "FNB"
    assert assignment_calls[0]["case_ref"] == "case-1"
    assert assignment_calls[0]["assignee_ref"] == "amplifi-support"
    assert assignment_calls[0]["assignment_reason"] == "Operator owns customer recovery follow-up."
    assert assignment_calls[0]["idempotency_key_hash"]
    assert assignment_calls[0]["request_payload_hash"]
    assert assignment_calls[0]["correlation_id"] == "corr-assignment-1"
