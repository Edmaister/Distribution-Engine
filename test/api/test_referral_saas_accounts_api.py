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
from services.referral_saas_account_membership_service import (
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
