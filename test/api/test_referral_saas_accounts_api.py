from __future__ import annotations

from types import SimpleNamespace

import pytest
from httpx import AsyncClient

from apps.api.main import app
from apps.api.routers import referral_saas_accounts
from services.referral_saas_account_foundation_service import (
    AccountFoundationContext,
    AccountFoundationListItem,
    AccountNotResolvable,
    AccountProfileMaintenanceResult,
    AccountProfileNotFound,
    ExternalReferenceConflict,
    ExternalReferenceNotActive,
    ExternalReferenceNotFound,
    InvalidExternalReferenceType,
    TenantLinkNotResolvable,
)
from services.referral_saas_account_setup_service import (
    AccountSetupDraftNotFound,
    AccountSetupDuplicateInternalTenantScope,
    AccountSetupDuplicateReference,
    AccountSetupInvalidDraftState,
    DurableAccountSetupResult,
)
from services.referral_saas_campaign_service import ReferralSaasCampaignSummary
from services.referral_saas_campaign_service import ReferralSaasCampaignSetupResult
from services.referral_saas_campaign_service import (
    ReferralSaasCampaignPolicySettingsResult,
)
from services.referral_saas_campaign_service import ReferralSaasCampaignReviewResult
from services.referral_saas_campaign_service import ReferralSaasCampaignActivationResult
from services.referral_saas_account_membership_service import (
    MembershipActivationRequestResult,
    MembershipInvitationDuplicate,
    MembershipInvitationDeliveryRequestResult,
    MembershipInvitationIntentResult,
)

pytestmark = pytest.mark.asyncio

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}
PARTNER_HEADERS = {"x-api-key": "test-partner-key"}


def _context(**overrides) -> AccountFoundationContext:
    values = {
        "account_id": "acct-1",
        "account_code": "ACCT_FNB",
        "account_name": "FNB Referral SaaS",
        "account_type": "ORGANISATION",
        "account_status": "ACTIVE",
        "onboarding_status": "APPROVED",
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
    assert detail["no_invite_delivery_confirmed"] is True
    assert detail["no_auth_claim_change_confirmed"] is True


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

    monkeypatch.setattr(
        referral_saas_accounts,
        "resolve_setup_account_by_external_reference",
        fake_resolve_setup_account_by_external_reference,
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
    assert "tenant_code" not in str(body)
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
    assert "tenant_code" not in str(body)
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
    assert calls == [
        {
            "ref_type": "external_tenant_ref",
            "external_ref": "fnb-referrals",
        }
    ]


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
