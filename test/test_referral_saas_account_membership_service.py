from __future__ import annotations

from contextlib import asynccontextmanager

import pytest

from services import referral_saas_account_membership_service as svc

pytestmark = pytest.mark.asyncio


def _row(**overrides):
    row = {
        "membership_id": "membership-1",
        "role_family": "PLATFORM_ADMIN",
        "permission_set": "ACCOUNT_SETUP",
        "status": "ACTIVE",
        "actor_type": "CLIENT",
        "delivery_status": "DELIVERY_NOT_CONFIGURED",
        "user_subject": None,
        "user_display_name": None,
        "recipient_contact_status": "CONTACT_REFERENCE_MISSING",
        "client_id": "client-1",
        "is_current_actor": False,
    }
    row.update(overrides)
    return row


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    async def fetch(self, query, *args):
        self.calls.append((query, args))
        return self.rows


class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeCommandConnection:
    def __init__(self, fetchrow_results):
        self.fetchrow_results = list(fetchrow_results)
        self.fetchrow_calls = []

    async def fetchrow(self, query, *args):
        self.fetchrow_calls.append((query, args))
        if not self.fetchrow_results:
            raise AssertionError(f"Unexpected fetchrow call: {query}")
        return self.fetchrow_results.pop(0)

    def transaction(self):
        return FakeTransaction()


def patch_db(monkeypatch, connection):
    @asynccontextmanager
    async def fake_db_connection():
        yield connection

    monkeypatch.setattr(svc, "db_connection", fake_db_connection)


async def test_membership_posture_reports_no_actor_evidence_without_writes(monkeypatch):
    conn = FakeConnection([])
    patch_db(monkeypatch, conn)

    posture = await svc.get_referral_saas_account_membership_posture(
        account_id="acct-1",
        tenant_code="FNB",
        actor_ref="operator-1",
    )

    safe_payload = posture.to_safe_dict()
    assert safe_payload["totalMemberships"] == 0
    assert safe_payload["currentActor"]["status"] == "NO_MEMBERSHIP_EVIDENCE"
    assert safe_payload["currentActor"]["canOperateSetup"] is False
    assert safe_payload["noMembershipWriteConfirmed"] is True
    assert safe_payload["noInviteDeliveryConfirmed"] is True
    assert "NO_INVITE_DELIVERY" in safe_payload["guardrails"]
    assert "internal_tenant_identifier" in safe_payload["redactions"]
    assert "tenantCode" not in safe_payload
    assert conn.calls[0][1] == ("acct-1", "FNB", "", "operator-1")
    assert "platform_memberships" in conn.calls[0][0]
    upper_query = conn.calls[0][0].upper()
    assert "INSERT INTO" not in upper_query
    assert "UPDATE " not in upper_query
    assert "DELETE FROM" not in upper_query


async def test_membership_posture_confirms_active_current_actor(monkeypatch):
    patch_db(
        monkeypatch,
        FakeConnection(
            [
                _row(
                    role_family="DISTRIBUTION_ADMIN",
                    permission_set="ACCOUNT_SETUP_ADMIN",
                    status="ACTIVE",
                    actor_type="USER",
                    user_subject="owner@example.test",
                    user_display_name="Setup Owner",
                    recipient_contact_status="CONTACT_REFERENCE_PRESENT",
                    is_current_actor=True,
                ),
                _row(role_family="SUPPORT", status="INVITED"),
            ]
        ),
    )

    posture = await svc.get_referral_saas_account_membership_posture(
        account_id="acct-1",
        tenant_code="FNB",
        actor_client_id="admin-client",
    )

    safe_payload = posture.to_safe_dict()
    assert safe_payload["totalMemberships"] == 2
    assert safe_payload["activeCount"] == 1
    assert safe_payload["invitedCount"] == 1
    assert safe_payload["currentActor"] == {
        "status": "MEMBERSHIP_CONFIRMED",
        "roleFamily": "DISTRIBUTION_ADMIN",
        "permissionSet": "ACCOUNT_SETUP_ADMIN",
        "canOperateSetup": True,
        "evidence": "Active account membership matched the current actor.",
    }
    assert safe_payload["roleFamilies"] == [
        {
            "roleFamily": "DISTRIBUTION_ADMIN",
            "invitedCount": 0,
            "activeCount": 1,
            "suspendedCount": 0,
            "disabledCount": 0,
            "archivedCount": 0,
        },
        {
            "roleFamily": "SUPPORT",
            "invitedCount": 1,
            "activeCount": 0,
            "suspendedCount": 0,
            "disabledCount": 0,
            "archivedCount": 0,
        },
    ]
    assert safe_payload["memberships"][0] == {
        "actorType": "USER",
        "membershipRef": "membership-1",
        "subject": "owner@example.test",
        "displayName": "Setup Owner",
        "roleFamily": "DISTRIBUTION_ADMIN",
        "permissionSet": "ACCOUNT_SETUP_ADMIN",
        "status": "ACTIVE",
        "deliveryStatus": "DELIVERY_NOT_CONFIGURED",
        "recipientContactStatus": "CONTACT_REFERENCE_PRESENT",
        "seatAssignmentStatus": "SEAT_NOT_ASSIGNED",
        "authClaimStatus": "AUTH_CLAIMS_NOT_PROPAGATED",
    }


async def test_membership_posture_keeps_invited_actor_non_operational(monkeypatch):
    patch_db(
        monkeypatch,
        FakeConnection(
            [
                _row(
                    role_family="SUPPORT",
                    permission_set="READ_ONLY_SUPPORT",
                    status="INVITED",
                    is_current_actor=True,
                )
            ]
        ),
    )

    posture = await svc.get_referral_saas_account_membership_posture(
        account_id="acct-1",
        tenant_code="FNB",
        actor_ref="user-1",
    )

    assert posture.to_safe_dict()["currentActor"] == {
        "status": "INVITED_NOT_ACTIVE",
        "roleFamily": "SUPPORT",
        "permissionSet": "READ_ONLY_SUPPORT",
        "canOperateSetup": False,
        "evidence": (
            "The current actor has invited membership evidence, but it is not active."
        ),
    }


def _posture_with_memberships(*memberships):
    return svc.ReferralSaasAccountMembershipPosture(
        account_id="acct-1",
        total_memberships=len(memberships),
        invited_count=sum(1 for item in memberships if item.status == "INVITED"),
        active_count=sum(1 for item in memberships if item.status == "ACTIVE"),
        suspended_count=0,
        disabled_count=0,
        archived_count=0,
        role_families=(),
        memberships=memberships,
        current_actor=svc.MembershipActorPosture(
            status="NO_MEMBERSHIP_EVIDENCE",
            role_family=None,
            permission_set=None,
            can_operate_setup=False,
            evidence="No active account membership matched the current actor.",
        ),
        guardrails=("READ_ONLY_MEMBERSHIP_POSTURE",),
        redactions=("internal_tenant_identifier",),
    )


def _membership(**overrides):
    values = {
        "membership_id": "membership-1",
        "actor_type": "USER",
        "subject": "owner@example.test",
        "display_name": "Setup Owner",
        "role_family": "DISTRIBUTION_ADMIN",
        "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
        "status": "INVITED",
        "delivery_status": "DELIVERY_NOT_CONFIGURED",
        "recipient_contact_status": "CONTACT_REFERENCE_PRESENT",
        "seat_assignment_status": "SEAT_NOT_ASSIGNED",
        "auth_claim_status": "AUTH_CLAIMS_NOT_PROPAGATED",
    }
    values.update(overrides)
    return svc.MembershipPersonSummary(**values)


async def test_membership_activation_readiness_explains_invited_blockers():
    readiness = svc.build_membership_activation_readiness(
        posture=_posture_with_memberships(
            _membership(),
            _membership(
                subject="campaign@example.test",
                display_name="Campaign Manager",
                role_family="CAMPAIGN_MANAGER",
                permission_set="REFERRAL_SAAS_CAMPAIGN_MANAGER",
                delivery_status="INVITATION_DELIVERY_REQUESTED",
            ),
        ),
        account_status="PENDING_ONBOARDING",
        tenant_link_status="PENDING_SETUP",
        external_reference_status="ACTIVE",
    )

    safe_payload = readiness.to_safe_dict()

    assert safe_payload["overallStatus"] == "ACTION_REQUIRED"
    assert safe_payload["missingRoleFamilies"] == []
    assert safe_payload["invitedCount"] == 2
    assert safe_payload["deliveryReadyCount"] == 1
    assert safe_payload["activationReadyCount"] == 0
    assert safe_payload["noInviteDeliveryConfirmed"] is True
    assert safe_payload["noMembershipActivationConfirmed"] is True
    assert safe_payload["noSeatAssignmentConfirmed"] is True
    assert safe_payload["noAuthClaimChangeConfirmed"] is True
    assert "tenantCode" not in safe_payload
    assert safe_payload["items"][0]["blockers"] == [
        "DELIVERY_PROVIDER_NOT_CONFIGURED",
        "ACCOUNT_NOT_ACTIVE",
        "TENANT_LINK_NOT_ACTIVE",
        "IDENTITY_ACCEPTANCE_NOT_RECORDED",
        "INVITATION_NOT_DELIVERED",
    ]
    assert (
        safe_payload["items"][0]["nextAction"]
        == "Configure an approved invitation delivery provider before sending invites."
    )
    assert safe_payload["items"][0]["recipientContactStatus"] == "CONTACT_REFERENCE_PRESENT"
    assert safe_payload["items"][0]["provisioningReadiness"] == "WAITING_FOR_MEMBERSHIP_ACTIVATION"
    assert safe_payload["items"][0]["seatAssignmentStatus"] == "SEAT_NOT_ASSIGNED"
    assert safe_payload["items"][0]["authClaimStatus"] == "AUTH_CLAIMS_NOT_PROPAGATED"
    assert safe_payload["items"][1]["blockers"] == [
        "ACCOUNT_NOT_ACTIVE",
        "TENANT_LINK_NOT_ACTIVE",
        "IDENTITY_ACCEPTANCE_NOT_RECORDED",
    ]


async def test_membership_activation_readiness_blocks_missing_contact_reference():
    readiness = svc.build_membership_activation_readiness(
        posture=_posture_with_memberships(
            _membership(
                subject="owner@example.test",
                display_name="Setup Owner",
                recipient_contact_status="CONTACT_REFERENCE_MISSING",
            ),
        ),
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
    )

    item = readiness.to_safe_dict()["items"][0]

    assert item["recipientContactStatus"] == "CONTACT_REFERENCE_MISSING"
    assert item["deliveryReadiness"] == "BLOCKED"
    assert item["blockers"] == [
        "DELIVERY_PROVIDER_NOT_CONFIGURED",
        "RECIPIENT_CONTACT_REFERENCE_MISSING",
        "IDENTITY_ACCEPTANCE_NOT_RECORDED",
        "INVITATION_NOT_DELIVERED",
    ]
    assert (
        item["nextAction"]
        == "Add a safe work email contact reference before invite delivery can be requested."
    )
    assert item["provisioningReadiness"] == "WAITING_FOR_MEMBERSHIP_ACTIVATION"


async def test_membership_activation_readiness_keeps_active_membership_provisioning_separate():
    readiness = svc.build_membership_activation_readiness(
        posture=_posture_with_memberships(
            _membership(
                status="ACTIVE",
                delivery_status="INVITATION_DELIVERY_REQUESTED",
            ),
            _membership(
                subject="campaign@example.test",
                display_name="Campaign Manager",
                role_family="CAMPAIGN_MANAGER",
                permission_set="REFERRAL_SAAS_CAMPAIGN_MANAGER",
                status="ACTIVE",
                delivery_status="INVITATION_DELIVERY_REQUESTED",
            ),
        ),
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
    )

    safe_payload = readiness.to_safe_dict()

    assert safe_payload["overallStatus"] == "ACCESS_READY"
    assert safe_payload["items"][0]["activationReadiness"] == "ACTIVE"
    assert (
        safe_payload["items"][0]["provisioningReadiness"]
        == "READY_TO_PROVISION_SEAT"
    )
    assert safe_payload["items"][0]["seatAssignmentStatus"] == "SEAT_NOT_ASSIGNED"
    assert safe_payload["items"][0]["authClaimStatus"] == "AUTH_CLAIMS_NOT_PROPAGATED"
    assert (
        safe_payload["items"][0]["nextAction"]
        == "Membership is active. Provision a seat before login access is live; auth claims remain a separate governed workflow."
    )
    assert safe_payload["noSeatAssignmentConfirmed"] is True
    assert safe_payload["noAuthClaimChangeConfirmed"] is True


async def test_membership_activation_readiness_shows_assigned_seat_separately_from_auth_claims():
    readiness = svc.build_membership_activation_readiness(
        posture=_posture_with_memberships(
            _membership(
                status="ACTIVE",
                delivery_status="INVITATION_DELIVERY_REQUESTED",
                seat_assignment_status="SEAT_ASSIGNED",
                auth_claim_status="AUTH_CLAIMS_NOT_PROPAGATED",
            ),
        ),
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
    )

    item = readiness.to_safe_dict()["items"][0]

    assert item["activationReadiness"] == "ACTIVE"
    assert item["provisioningReadiness"] == "SEAT_ASSIGNED"
    assert item["seatAssignmentStatus"] == "SEAT_ASSIGNED"
    assert item["authClaimStatus"] == "AUTH_CLAIMS_NOT_PROPAGATED"
    assert item["nextAction"] == (
        "Seat is assigned. Configure auth claims through the separate governed "
        "workflow before login access is live."
    )


async def test_membership_activation_readiness_reports_missing_required_roles():
    readiness = svc.build_membership_activation_readiness(
        posture=_posture_with_memberships(),
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
    )

    safe_payload = readiness.to_safe_dict()

    assert safe_payload["overallStatus"] == "ACTION_REQUIRED"
    assert safe_payload["missingRoleFamilies"] == [
        "DISTRIBUTION_ADMIN",
        "CAMPAIGN_MANAGER",
    ]
    assert safe_payload["items"] == []


async def test_membership_activation_readiness_marks_active_roles_ready():
    readiness = svc.build_membership_activation_readiness(
        posture=_posture_with_memberships(
            _membership(status="ACTIVE", delivery_status="DELIVERED"),
            _membership(
                subject="campaign@example.test",
                display_name="Campaign Manager",
                role_family="CAMPAIGN_MANAGER",
                permission_set="REFERRAL_SAAS_CAMPAIGN_MANAGER",
                status="ACTIVE",
                delivery_status="DELIVERED",
            ),
        ),
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
    )

    safe_payload = readiness.to_safe_dict()

    assert safe_payload["overallStatus"] == "ACCESS_READY"
    assert safe_payload["activeCount"] == 2
    assert safe_payload["missingRoleFamilies"] == []
    assert all(item["activationReadiness"] == "ACTIVE" for item in safe_payload["items"])


async def test_membership_invitation_intent_records_user_membership_and_audit(
    monkeypatch,
):
    conn = FakeCommandConnection(
        [
            None,
            None,
            {"user_id": "user-1", "status": "INVITED"},
            {
                "membership_id": "membership-1",
                "status": "INVITED",
                "role_family": "DISTRIBUTION_ADMIN",
                "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
            },
            {"account_audit_event_id": "audit-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.record_referral_saas_membership_invitation_intent(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        actor_type="USER",
        subject="user-subject-1",
        email_hash="email-hash-only",
        display_name="Setup Owner",
        role_family="DISTRIBUTION_ADMIN",
        permission_set="REFERRAL_SAAS_ACCOUNT_ADMIN",
        tenant_scope="PRIMARY_ACCOUNT_TENANT",
        reason_code="ACCOUNT_SETUP_USER_ROLE",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        command_payload={
            "actor": {"actorType": "USER", "subject": "user-subject-1"},
            "membership": {"roleFamily": "DISTRIBUTION_ADMIN"},
        },
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "INVITATION_INTENT_RECORDED"
    assert safe_payload["membership"] == {
        "membershipRef": "membership-1",
        "status": "INVITED",
        "roleFamily": "DISTRIBUTION_ADMIN",
        "permissionSet": "REFERRAL_SAAS_ACCOUNT_ADMIN",
        "canOperateSetup": False,
    }
    assert safe_payload["delivery"]["status"] == "DELIVERY_NOT_CONFIGURED"
    assert safe_payload["idempotency"]["status"] == "RECORDED"
    assert safe_payload["noInviteDeliveryConfirmed"] is True
    assert safe_payload["noAuthClaimChangeConfirmed"] is True
    assert safe_payload["noSeatAssignmentConfirmed"] is True
    assert safe_payload["noMoneyMovementConfirmed"] is True
    assert "NO_EMAIL_DELIVERY_WITHOUT_PROVIDER" in safe_payload["guardrails"]
    assert "internal_tenant_identifier" in safe_payload["redactions"]
    assert "tenantCode" not in safe_payload

    joined_queries = "\n".join(call[0] for call in conn.fetchrow_calls)
    assert "INSERT INTO platform_users" in joined_queries
    assert "INSERT INTO platform_memberships" in joined_queries
    assert "INSERT INTO platform_account_audit_events" in joined_queries
    assert "platform_seats" not in joined_queries


async def test_membership_invitation_intent_accepts_campaign_manager_role(
    monkeypatch,
):
    conn = FakeCommandConnection(
        [
            None,
            None,
            {"user_id": "user-1", "status": "INVITED"},
            {
                "membership_id": "membership-1",
                "status": "INVITED",
                "role_family": "CAMPAIGN_MANAGER",
                "permission_set": "REFERRAL_SAAS_CAMPAIGN_MANAGER",
            },
            {"account_audit_event_id": "audit-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.record_referral_saas_membership_invitation_intent(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        actor_type="USER",
        subject="campaign.manager@example.com",
        display_name="Campaign Manager",
        role_family="CAMPAIGN_MANAGER",
        permission_set="REFERRAL_SAAS_CAMPAIGN_MANAGER",
        tenant_scope="PRIMARY_ACCOUNT_TENANT",
        reason_code="CUSTOMER_PROFILE_ACCESS_MAINTENANCE",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        command_payload={
            "actor": {"actorType": "USER", "subject": "campaign.manager@example.com"},
            "membership": {"roleFamily": "CAMPAIGN_MANAGER"},
        },
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["membership"]["roleFamily"] == "CAMPAIGN_MANAGER"
    assert safe_payload["membership"]["permissionSet"] == "REFERRAL_SAAS_CAMPAIGN_MANAGER"
    assert safe_payload["membership"]["status"] == "INVITED"


async def test_membership_invitation_update_edits_invited_intent_only(
    monkeypatch,
):
    conn = FakeCommandConnection(
        [
            None,
            {
                "membership_id": "membership-1",
                "status": "INVITED",
                "role_family": "DISTRIBUTION_ADMIN",
                "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                "user_id": "00000000-0000-0000-0000-000000000001",
                "client_id": None,
                "subject": "owner@example.test",
                "display_name": "Owner",
            },
            None,
            {"user_id": "00000000-0000-0000-0000-000000000001"},
            {
                "membership_id": "membership-1",
                "status": "INVITED",
                "role_family": "CAMPAIGN_MANAGER",
                "permission_set": "REFERRAL_SAAS_CAMPAIGN_MANAGER",
            },
            {"account_audit_event_id": "audit-update-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.update_referral_saas_membership_invitation_intent(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        membership_id="membership-1",
        email_hash="safe-email-hash",
        display_name="Campaign Manager",
        role_family="CAMPAIGN_MANAGER",
        permission_set="REFERRAL_SAAS_CAMPAIGN_MANAGER",
        reason_code="CUSTOMER_PROFILE_ACCESS_INTENT_UPDATE",
        correlation_id="corr-1",
        idempotency_key_hash="idem-update",
        command_payload_hash="payload-update",
        command_payload={"membership": {"roleFamily": "CAMPAIGN_MANAGER"}},
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "INVITATION_INTENT_UPDATED"
    assert safe_payload["membership"]["previousStatus"] == "INVITED"
    assert safe_payload["membership"]["status"] == "INVITED"
    assert safe_payload["membership"]["roleFamily"] == "CAMPAIGN_MANAGER"
    assert safe_payload["noInviteDeliveryConfirmed"] is True
    assert safe_payload["noMembershipActivationConfirmed"] is True
    assert safe_payload["noAuthClaimChangeConfirmed"] is True
    assert safe_payload["noSeatAssignmentConfirmed"] is True

    joined_queries = "\n".join(call[0] for call in conn.fetchrow_calls)
    assert "UPDATE platform_users" in joined_queries
    assert "UPDATE platform_memberships" in joined_queries
    assert "INSERT INTO platform_account_audit_events" in joined_queries
    assert "DELETE FROM" not in joined_queries
    assert "platform_seats" not in joined_queries


async def test_membership_invitation_update_rejects_active_membership(
    monkeypatch,
):
    conn = FakeCommandConnection(
        [
            None,
            {
                "membership_id": "membership-1",
                "status": "ACTIVE",
                "role_family": "DISTRIBUTION_ADMIN",
                "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                "user_id": "00000000-0000-0000-0000-000000000001",
                "client_id": None,
                "subject": "owner@example.test",
                "display_name": "Owner",
            },
        ]
    )
    patch_db(monkeypatch, conn)

    with pytest.raises(svc.MembershipInvitationNotEditable):
        await svc.update_referral_saas_membership_invitation_intent(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            membership_id="membership-1",
            role_family="CAMPAIGN_MANAGER",
            permission_set="REFERRAL_SAAS_CAMPAIGN_MANAGER",
            reason_code="CUSTOMER_PROFILE_ACCESS_INTENT_UPDATE",
            correlation_id="corr-1",
            idempotency_key_hash="idem-update",
            command_payload_hash="payload-update",
            command_payload={"membership": {"roleFamily": "CAMPAIGN_MANAGER"}},
        )

    joined_queries = "\n".join(call[0] for call in conn.fetchrow_calls)
    assert "UPDATE platform_memberships" not in joined_queries
    assert "INSERT INTO platform_account_audit_events" not in joined_queries


async def test_membership_invitation_cancel_disables_invited_intent_without_delete(
    monkeypatch,
):
    conn = FakeCommandConnection(
        [
            None,
            {
                "membership_id": "membership-1",
                "status": "INVITED",
                "role_family": "DISTRIBUTION_ADMIN",
                "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
            },
            {
                "membership_id": "membership-1",
                "status": "DISABLED",
                "role_family": "DISTRIBUTION_ADMIN",
                "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
            },
            {"account_audit_event_id": "audit-cancel-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.cancel_referral_saas_membership_invitation_intent(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        membership_id="membership-1",
        reason_code="CUSTOMER_PROFILE_ACCESS_INTENT_CANCEL",
        correlation_id="corr-1",
        idempotency_key_hash="idem-cancel",
        command_payload_hash="payload-cancel",
        command_payload={"membershipRef": "membership-1"},
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "INVITATION_INTENT_CANCELLED"
    assert safe_payload["membership"]["previousStatus"] == "INVITED"
    assert safe_payload["membership"]["status"] == "DISABLED"
    assert safe_payload["noInviteDeliveryConfirmed"] is True
    assert safe_payload["noMembershipActivationConfirmed"] is True
    assert safe_payload["noAuthClaimChangeConfirmed"] is True
    assert safe_payload["noSeatAssignmentConfirmed"] is True
    assert safe_payload["noMoneyMovementConfirmed"] is True

    joined_queries = "\n".join(call[0] for call in conn.fetchrow_calls)
    assert "UPDATE platform_memberships" in joined_queries
    assert "status = 'DISABLED'" in joined_queries
    assert "INSERT INTO platform_account_audit_events" in joined_queries
    assert "DELETE FROM" not in joined_queries


async def test_membership_invitation_delivery_request_records_blocked_audit(
    monkeypatch,
):
    conn = FakeCommandConnection(
        [
            None,
            {
                "membership_id": "membership-1",
                "status": "INVITED",
                "role_family": "DISTRIBUTION_ADMIN",
                "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                "delivery_status": "DELIVERY_NOT_CONFIGURED",
                "recipient_contact_status": "CONTACT_REFERENCE_PRESENT",
            },
            {"account_audit_event_id": "audit-delivery-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.request_referral_saas_membership_invitation_delivery(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        membership_id="membership-1",
        provider_ref="mail-provider-1",
        channel="EMAIL",
        template_ref="referral-saas-account-invite-v1",
        recipient_hash="recipient-hash",
        reason_code="CUSTOMER_PROFILE_INVITE_DELIVERY_REQUEST",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        command_payload={
            "delivery": {
                "providerRef": "mail-provider-1",
                "channel": "EMAIL",
                "templateRef": "referral-saas-account-invite-v1",
                "recipientHash": "recipient-hash",
            }
        },
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "DELIVERY_PROVIDER_NOT_CONFIGURED"
    assert safe_payload["membership"]["membershipRef"] == "membership-1"
    assert safe_payload["membership"]["status"] == "INVITED"
    assert safe_payload["delivery"] == {
        "status": "DELIVERY_PROVIDER_NOT_CONFIGURED",
        "nextAction": "Configure Email provider URL and signing secret before sending invite emails.",
        "recipientContactStatus": "CONTACT_REFERENCE_PRESENT",
        "providerRef": "mail-provider-1",
        "channel": "EMAIL",
        "templateRef": "referral-saas-account-invite-v1",
        "providerDeliveryRef": None,
        "providerStatus": None,
    }
    assert safe_payload["idempotency"]["status"] == "RECORDED"
    assert safe_payload["noInviteDeliveryConfirmed"] is True
    assert safe_payload["noMembershipActivationConfirmed"] is True
    assert safe_payload["noAuthClaimChangeConfirmed"] is True
    assert safe_payload["noSeatAssignmentConfirmed"] is True
    assert safe_payload["noMoneyMovementConfirmed"] is True
    assert "recipient_hash" in safe_payload["redactions"]
    assert "provider_secret" in safe_payload["redactions"]

    joined_queries = "\n".join(call[0] for call in conn.fetchrow_calls)
    assert "INSERT INTO platform_account_audit_events" in joined_queries
    assert "UPDATE platform_memberships" not in joined_queries
    assert "platform_seats" not in joined_queries


async def test_membership_invitation_delivery_request_sends_with_approved_provider(
    monkeypatch,
):
    conn = FakeCommandConnection(
        [
            None,
            {
                "membership_id": "membership-1",
                "status": "INVITED",
                "role_family": "DISTRIBUTION_ADMIN",
                "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                "delivery_status": "DELIVERY_NOT_CONFIGURED",
                "recipient_contact_status": "CONTACT_REFERENCE_PRESENT",
                "recipient_subject": "owner@example.test",
            },
            {"membership_id": "membership-1"},
            {"account_audit_event_id": "audit-delivery-1"},
        ]
    )
    patch_db(monkeypatch, conn)
    monkeypatch.setattr(
        svc,
        "get_channel_readiness",
        lambda: {
            "items": [
                {
                    "channel_code": "EMAIL",
                    "provider_configured": True,
                    "provider_ref": "mail-provider-1",
                    "provider_approved": True,
                    "approved_for_referral_saas": True,
                }
            ]
        },
    )

    async def fake_dispatch_channel_message(**kwargs):
        assert kwargs["channel_code"] == "EMAIL"
        assert kwargs["tenant_code"] == "FNB"
        assert kwargs["recipient"] == "owner@example.test"
        assert kwargs["context"]["event_type"] == "MEMBERSHIP_INVITATION"
        assert kwargs["context"]["no_auth_claim_change_confirmed"] is True
        assert kwargs["context"]["no_seat_assignment_confirmed"] is True
        return {
            "status": "SENT",
            "delivery_id": "CHD-123",
            "provider_status": 202,
        }

    monkeypatch.setattr(
        svc,
        "dispatch_channel_message",
        fake_dispatch_channel_message,
    )

    result = await svc.request_referral_saas_membership_invitation_delivery(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        membership_id="membership-1",
        provider_ref="mail-provider-1",
        channel="EMAIL",
        template_ref="referral-saas-account-invite-v1",
        recipient_hash="recipient-hash",
        reason_code="CUSTOMER_PROFILE_INVITE_DELIVERY_REQUEST",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        command_payload={
            "delivery": {
                "providerRef": "mail-provider-1",
                "channel": "EMAIL",
                "templateRef": "referral-saas-account-invite-v1",
                "recipientHash": "recipient-hash",
            }
        },
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "INVITATION_DELIVERY_SENT"
    assert safe_payload["delivery"]["providerDeliveryRef"] == "CHD-123"
    assert safe_payload["delivery"]["providerStatus"] == 202
    assert safe_payload["noInviteDeliveryConfirmed"] is False

    joined_queries = "\n".join(call[0] for call in conn.fetchrow_calls)
    assert "UPDATE platform_memberships" in joined_queries
    assert "INSERT INTO platform_account_audit_events" in joined_queries
    assert "platform_seats" not in joined_queries
    assert conn.fetchrow_calls[-1][1][6] == "RECORDED"


async def test_membership_invitation_delivery_request_records_provider_failure(
    monkeypatch,
):
    conn = FakeCommandConnection(
        [
            None,
            {
                "membership_id": "membership-1",
                "status": "INVITED",
                "role_family": "CAMPAIGN_MANAGER",
                "permission_set": "REFERRAL_SAAS_CAMPAIGN_MANAGER",
                "delivery_status": "DELIVERY_NOT_CONFIGURED",
                "recipient_contact_status": "CONTACT_REFERENCE_PRESENT",
                "recipient_subject": "campaign@example.test",
            },
            {"membership_id": "membership-1"},
            {"account_audit_event_id": "audit-delivery-1"},
        ]
    )
    patch_db(monkeypatch, conn)
    monkeypatch.setattr(
        svc,
        "get_channel_readiness",
        lambda: {
            "items": [
                {
                    "channel_code": "EMAIL",
                    "provider_configured": True,
                    "provider_ref": "mail-provider-1",
                    "provider_approved": True,
                    "approved_for_referral_saas": True,
                }
            ]
        },
    )

    async def fake_dispatch_channel_message(**kwargs):
        return {
            "status": "FAILED",
            "delivery_id": "CHD-failed",
            "provider_status": 503,
        }

    monkeypatch.setattr(
        svc,
        "dispatch_channel_message",
        fake_dispatch_channel_message,
    )

    result = await svc.request_referral_saas_membership_invitation_delivery(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        membership_id="membership-1",
        provider_ref="mail-provider-1",
        channel="EMAIL",
        template_ref="referral-saas-account-invite-v1",
        recipient_hash="recipient-hash",
        reason_code="CUSTOMER_PROFILE_INVITE_DELIVERY_REQUEST",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "INVITATION_DELIVERY_FAILED"
    assert safe_payload["delivery"]["providerDeliveryRef"] == "CHD-failed"
    assert safe_payload["delivery"]["providerStatus"] == 503
    assert safe_payload["noInviteDeliveryConfirmed"] is False
    assert conn.fetchrow_calls[-1][1][6] == "FAILED"


async def test_membership_invitation_delivery_request_blocks_missing_recipient_contact(
    monkeypatch,
):
    conn = FakeCommandConnection(
        [
            None,
            {
                "membership_id": "membership-1",
                "status": "INVITED",
                "role_family": "DISTRIBUTION_ADMIN",
                "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                "delivery_status": "DELIVERY_NOT_CONFIGURED",
                "recipient_contact_status": "CONTACT_REFERENCE_MISSING",
            },
            {"account_audit_event_id": "audit-delivery-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.request_referral_saas_membership_invitation_delivery(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        membership_id="membership-1",
        provider_ref="mail-provider-1",
        channel="EMAIL",
        template_ref="referral-saas-account-invite-v1",
        recipient_hash=None,
        reason_code="CUSTOMER_PROFILE_INVITE_DELIVERY_REQUEST",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        command_payload={
            "delivery": {
                "providerRef": "mail-provider-1",
                "channel": "EMAIL",
                "templateRef": "referral-saas-account-invite-v1",
            }
        },
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "DELIVERY_RECIPIENT_CONTACT_MISSING"
    assert safe_payload["delivery"]["recipientContactStatus"] == "CONTACT_REFERENCE_MISSING"
    assert (
        safe_payload["delivery"]["nextAction"]
        == "Add a safe work email contact reference before invite delivery can be requested."
    )
    assert conn.fetchrow_calls[-1][1][10] == "DELIVERY_RECIPIENT_CONTACT_MISSING"


async def test_membership_invitation_delivery_request_replays_matching_idempotency(
    monkeypatch,
):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                {
                    "account_audit_event_id": "audit-delivery-1",
                    "membership_id": "membership-1",
                    "evidence_summary": {
                        "membership_id": "membership-1",
                        "membership_status": "INVITED",
                        "role_family": "DISTRIBUTION_ADMIN",
                        "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                        "provider_ref": "mail-provider-1",
                        "channel": "EMAIL",
                        "template_ref": "referral-saas-account-invite-v1",
                        "command_payload_hash": "payload-hash",
                    },
                }
            ]
        ),
    )

    result = await svc.request_referral_saas_membership_invitation_delivery(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        membership_id="membership-1",
        provider_ref="mail-provider-1",
        channel="EMAIL",
        template_ref="referral-saas-account-invite-v1",
        recipient_hash="recipient-hash",
        reason_code="CUSTOMER_PROFILE_INVITE_DELIVERY_REQUEST",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
    )

    assert result.to_safe_dict()["idempotency"]["status"] == "REPLAYED"


async def test_membership_invitation_delivery_request_rejects_active_membership(
    monkeypatch,
):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                None,
                {
                    "membership_id": "membership-1",
                    "status": "ACTIVE",
                    "role_family": "DISTRIBUTION_ADMIN",
                    "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                    "delivery_status": "DELIVERED",
                },
            ]
        ),
    )

    with pytest.raises(svc.MembershipInvitationDeliveryNotInvited):
        await svc.request_referral_saas_membership_invitation_delivery(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            membership_id="membership-1",
            provider_ref="mail-provider-1",
            channel="EMAIL",
            template_ref="referral-saas-account-invite-v1",
            recipient_hash="recipient-hash",
            reason_code="CUSTOMER_PROFILE_INVITE_DELIVERY_REQUEST",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="payload-hash",
        )


async def test_membership_activation_request_blocks_missing_identity_acceptance(
    monkeypatch,
):
    conn = FakeCommandConnection(
        [
            None,
            {
                "membership_id": "membership-1",
                "status": "INVITED",
                "role_family": "DISTRIBUTION_ADMIN",
                "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                "user_id": "user-1",
                "client_id": None,
                "delivery_status": "INVITATION_DELIVERY_REQUESTED",
                "user_subject": "owner@example.test",
            },
            None,
            {"account_audit_event_id": "audit-activation-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.request_referral_saas_membership_activation(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
        membership_id="membership-1",
        accepted_subject=None,
        acceptance_evidence_ref=None,
        reason_code="CUSTOMER_PROFILE_MEMBERSHIP_ACTIVATION_REQUEST",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        command_payload={"activation": {}},
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "ACTIVATION_REJECTED_IDENTITY_NOT_ACCEPTED"
    assert safe_payload["membership"]["previousStatus"] == "INVITED"
    assert safe_payload["membership"]["status"] == "INVITED"
    assert safe_payload["activation"]["acceptedSubjectStatus"] == (
        "ACCEPTED_SUBJECT_MISSING_OR_MISMATCHED"
    )
    assert safe_payload["idempotency"]["status"] == "RECORDED"
    assert safe_payload["noInviteDeliveryConfirmed"] is True
    assert safe_payload["noAuthClaimChangeConfirmed"] is True
    assert safe_payload["noSeatAssignmentConfirmed"] is True
    assert safe_payload["noMoneyMovementConfirmed"] is True
    assert "accepted_subject" in safe_payload["redactions"]

    joined_queries = "\n".join(call[0] for call in conn.fetchrow_calls)
    assert "INSERT INTO platform_account_audit_events" in joined_queries
    assert "UPDATE platform_memberships" not in joined_queries
    assert "platform_seats" not in joined_queries


async def test_membership_activation_request_activates_only_membership_lifecycle(
    monkeypatch,
):
    conn = FakeCommandConnection(
        [
            None,
            {
                "membership_id": "membership-1",
                "status": "INVITED",
                "role_family": "DISTRIBUTION_ADMIN",
                "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                "user_id": "user-1",
                "client_id": None,
                "delivery_status": "INVITATION_DELIVERY_REQUESTED",
                "user_subject": "owner@example.test",
            },
            None,
            {"status": "ACTIVE"},
            {"account_audit_event_id": "audit-activation-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.request_referral_saas_membership_activation(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
        membership_id="membership-1",
        accepted_subject="owner@example.test",
        acceptance_evidence_ref="identity-acceptance-1",
        reason_code="CUSTOMER_PROFILE_MEMBERSHIP_ACTIVATION_REQUEST",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        command_payload={
            "activation": {
                "acceptedSubject": "owner@example.test",
                "acceptanceEvidenceRef": "identity-acceptance-1",
            }
        },
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "MEMBERSHIP_ACTIVATED"
    assert safe_payload["membership"]["status"] == "ACTIVE"
    assert safe_payload["activation"]["acceptedSubjectStatus"] == (
        "ACCEPTED_SUBJECT_MATCHED"
    )
    assert safe_payload["noInviteDeliveryConfirmed"] is True
    assert safe_payload["noAuthClaimChangeConfirmed"] is True
    assert safe_payload["noSeatAssignmentConfirmed"] is True

    joined_queries = "\n".join(call[0] for call in conn.fetchrow_calls)
    assert "UPDATE platform_memberships" in joined_queries
    assert "accepted_by_ref" in joined_queries
    assert "$5::uuid IS NOT NULL AND user_id = $5::uuid" in joined_queries
    assert "$6::text IS NOT NULL AND client_id = $6::text" in joined_queries
    assert "platform_seats" not in joined_queries
    assert "auth" not in joined_queries.lower().replace("no_auth", "")


async def test_manual_access_acceptance_records_accepted_membership_during_setup(
    monkeypatch,
):
    conn = FakeCommandConnection(
        [
            None,
            {
                "membership_id": "membership-1",
                "status": "INVITED",
                "role_family": "DISTRIBUTION_ADMIN",
                "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                "user_id": "user-1",
                "client_id": None,
                "delivery_status": "DELIVERY_NOT_CONFIGURED",
                "user_subject": "owner@example.test",
            },
            None,
            {"status": "ACTIVE"},
            {"account_audit_event_id": "audit-activation-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.request_referral_saas_membership_activation(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        account_status="PENDING_ONBOARDING",
        tenant_link_status="PENDING_SETUP",
        external_reference_status="ACTIVE",
        membership_id="membership-1",
        accepted_subject="owner@example.test",
        acceptance_evidence_ref="manual-acceptance-1",
        reason_code="AMPLIFI_ADMIN_MANUAL_ACCESS_ACCEPTANCE",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        command_payload={
            "activation": {
                "acceptedSubject": "owner@example.test",
                "acceptanceEvidenceRef": "manual-acceptance-1",
            }
        },
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "MEMBERSHIP_ACTIVATED"
    assert safe_payload["membership"]["status"] == "ACTIVE"
    assert safe_payload["activation"]["acceptedSubjectStatus"] == (
        "ACCEPTED_SUBJECT_MATCHED"
    )
    assert safe_payload["noInviteDeliveryConfirmed"] is True
    assert safe_payload["noAuthClaimChangeConfirmed"] is True
    assert safe_payload["noSeatAssignmentConfirmed"] is True
    assert safe_payload["noMoneyMovementConfirmed"] is True

    joined_queries = "\n".join(call[0] for call in conn.fetchrow_calls)
    assert "UPDATE platform_memberships" in joined_queries
    assert "manual_access_acceptance_confirmed" in joined_queries
    assert "'acceptance_evidence_ref_present', $2::boolean" in joined_queries
    assert "'manual_access_acceptance_confirmed', $5::boolean" in joined_queries
    assert "'account_status_at_acceptance', $6::text" in joined_queries
    audit_evidence = conn.fetchrow_calls[-1][1][14]
    assert '"manual_access_acceptance_confirmed": true' in audit_evidence
    assert '"account_status_at_acceptance": "PENDING_ONBOARDING"' in audit_evidence
    assert "platform_seats" not in joined_queries
    assert "auth" not in joined_queries.lower().replace("no_auth", "")


async def test_membership_activation_request_replays_matching_idempotency(
    monkeypatch,
):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                {
                    "account_audit_event_id": "audit-activation-1",
                    "membership_id": "membership-1",
                    "previous_status": "INVITED",
                    "next_status": "MEMBERSHIP_ACTIVATED",
                    "evidence_summary": {
                        "membership_id": "membership-1",
                        "previous_membership_status": "INVITED",
                        "membership_status": "ACTIVE",
                        "role_family": "DISTRIBUTION_ADMIN",
                        "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                        "activation_status": "MEMBERSHIP_ACTIVATED",
                        "accepted_subject_status": "ACCEPTED_SUBJECT_MATCHED",
                        "activation_next_action": (
                            "Membership lifecycle is active. Configure seats and "
                            "auth claims only through their separate governed workflows."
                        ),
                        "command_payload_hash": "payload-hash",
                    },
                }
            ]
        ),
    )

    result = await svc.request_referral_saas_membership_activation(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
        membership_id="membership-1",
        accepted_subject="owner@example.test",
        acceptance_evidence_ref="identity-acceptance-1",
        reason_code="CUSTOMER_PROFILE_MEMBERSHIP_ACTIVATION_REQUEST",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "MEMBERSHIP_ACTIVATION_REPLAYED"
    assert safe_payload["membership"]["status"] == "ACTIVE"
    assert safe_payload["idempotency"]["status"] == "REPLAYED"


async def test_membership_activation_request_conflicts_on_idempotency_payload_mismatch(
    monkeypatch,
):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                {
                    "account_audit_event_id": "audit-activation-1",
                    "membership_id": "membership-1",
                    "evidence_summary": {"command_payload_hash": "original-hash"},
                }
            ]
        ),
    )

    with pytest.raises(svc.MembershipInvitationIdempotencyConflict):
        await svc.request_referral_saas_membership_activation(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            external_reference_status="ACTIVE",
            membership_id="membership-1",
            accepted_subject="owner@example.test",
            acceptance_evidence_ref="identity-acceptance-1",
            reason_code="CUSTOMER_PROFILE_MEMBERSHIP_ACTIVATION_REQUEST",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="new-hash",
        )


async def test_membership_invitation_intent_replays_matching_idempotency_key(
    monkeypatch,
):
    conn = FakeCommandConnection(
        [
            {
                "account_audit_event_id": "audit-1",
                "event_status": "RECORDED",
                "membership_id": "membership-1",
                "evidence_summary": {
                    "membership_id": "membership-1",
                    "role_family": "SUPPORT",
                    "permission_set": "REFERRAL_SAAS_SUPPORT",
                    "command_payload_hash": "payload-hash",
                },
            }
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.record_referral_saas_membership_invitation_intent(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        actor_type="USER",
        subject="support-subject",
        role_family="SUPPORT",
        permission_set="REFERRAL_SAAS_SUPPORT",
        tenant_scope="PRIMARY_ACCOUNT_TENANT",
        reason_code="ACCOUNT_SETUP_USER_ROLE",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "INVITATION_INTENT_REPLAYED"
    assert safe_payload["membership"]["membershipRef"] == "membership-1"
    assert safe_payload["idempotency"]["status"] == "REPLAYED"
    assert len(conn.fetchrow_calls) == 1


async def test_membership_invitation_intent_conflicts_on_idempotency_payload_mismatch(
    monkeypatch,
):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                {
                    "account_audit_event_id": "audit-1",
                    "membership_id": "membership-1",
                    "evidence_summary": {
                        "membership_id": "membership-1",
                        "command_payload_hash": "original-hash",
                    },
                }
            ]
        ),
    )

    with pytest.raises(svc.MembershipInvitationIdempotencyConflict):
        await svc.record_referral_saas_membership_invitation_intent(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            actor_type="USER",
            subject="support-subject",
            role_family="SUPPORT",
            permission_set="REFERRAL_SAAS_SUPPORT",
            tenant_scope="PRIMARY_ACCOUNT_TENANT",
            reason_code="ACCOUNT_SETUP_USER_ROLE",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="new-hash",
        )


async def test_membership_invitation_intent_rejects_duplicate_membership(
    monkeypatch,
):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                None,
                {"membership_id": "membership-existing", "status": "INVITED"},
            ]
        ),
    )

    with pytest.raises(svc.MembershipInvitationDuplicate):
        await svc.record_referral_saas_membership_invitation_intent(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            actor_type="USER",
            subject="setup-owner",
            role_family="DISTRIBUTION_ADMIN",
            permission_set="REFERRAL_SAAS_ACCOUNT_ADMIN",
            tenant_scope="PRIMARY_ACCOUNT_TENANT",
            reason_code="ACCOUNT_SETUP_USER_ROLE",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="payload-hash",
        )


async def test_membership_invitation_intent_rejects_unsafe_payload(monkeypatch):
    patch_db(monkeypatch, FakeCommandConnection([]))

    with pytest.raises(svc.MembershipInvitationUnsafePayload):
        await svc.record_referral_saas_membership_invitation_intent(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            actor_type="USER",
            subject="setup-owner",
            role_family="DISTRIBUTION_ADMIN",
            permission_set="REFERRAL_SAAS_ACCOUNT_ADMIN",
            tenant_scope="PRIMARY_ACCOUNT_TENANT",
            reason_code="ACCOUNT_SETUP_USER_ROLE",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="payload-hash",
            command_payload={"delivery": {"sendInvite": True}},
        )


async def test_access_provisioning_assigns_available_seat_and_audits(monkeypatch):
    conn = FakeCommandConnection(
        [
            None,
            {
                "membership_id": "membership-1",
                "status": "ACTIVE",
                "role_family": "DISTRIBUTION_ADMIN",
                "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                "seat_id": None,
            },
            {"seat_id": "seat-1", "seat_type": "ADMIN", "status": "AVAILABLE"},
            {"seat_id": "seat-1", "seat_type": "ADMIN", "status": "ASSIGNED"},
            {"membership_id": "membership-1", "seat_id": "seat-1"},
            {"account_audit_event_id": "audit-provisioning-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.request_referral_saas_access_provisioning(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
        membership_id="membership-1",
        seat_type="ADMIN",
        seat_assignment_evidence_ref="seat-evidence-1",
        auth_provider_ref="identity-provider-review-1",
        auth_claim_evidence_ref="claims-review-1",
        operator_notes="Provision account owner seat.",
        reason_code="CUSTOMER_PROFILE_ACCESS_PROVISIONING_REQUEST",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        command_payload={
            "provisioning": {
                "seatType": "ADMIN",
                "authProviderRef": "identity-provider-review-1",
            }
        },
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "PROVISIONING_REQUEST_RECORDED"
    assert safe_payload["seat"] == {
        "seatType": "ADMIN",
        "seatAssignmentStatus": "SEAT_ASSIGNED",
        "seatRef": "seat-1",
    }
    assert safe_payload["authClaims"]["authClaimStatus"] == (
        "AUTH_CLAIMS_NOT_PROPAGATED"
    )
    assert safe_payload["noInviteDeliveryConfirmed"] is True
    assert safe_payload["noAuthClaimChangeConfirmed"] is True
    assert safe_payload["noCredentialCreationConfirmed"] is True
    assert safe_payload["noCampaignActivationConfirmed"] is True
    assert safe_payload["noMoneyMovementConfirmed"] is True
    joined_queries = "\n".join(query for query, _ in conn.fetchrow_calls)
    assert "UPDATE platform_seats" in joined_queries
    assert "assigned_membership_id" in joined_queries
    assert "UPDATE platform_memberships" in joined_queries
    assert "INSERT INTO platform_account_audit_events" in joined_queries
    assert "UPDATE auth_claims" not in joined_queries
    assert "INSERT INTO auth_claims" not in joined_queries
    assert "auth_session" not in joined_queries.lower()
    assert "marketing_campaigns" not in joined_queries.lower()
    assert "invoice" not in joined_queries.lower()


async def test_access_provisioning_blocks_pending_account_without_seat_write(
    monkeypatch,
):
    conn = FakeCommandConnection(
        [
            None,
            {
                "membership_id": "membership-1",
                "status": "ACTIVE",
                "role_family": "DISTRIBUTION_ADMIN",
                "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                "seat_id": None,
            },
            {"account_audit_event_id": "audit-blocked-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.request_referral_saas_access_provisioning(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        account_status="PENDING_ONBOARDING",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
        membership_id="membership-1",
        seat_type="ADMIN",
        seat_assignment_evidence_ref=None,
        auth_provider_ref=None,
        auth_claim_evidence_ref=None,
        operator_notes=None,
        reason_code="CUSTOMER_PROFILE_ACCESS_PROVISIONING_REQUEST",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    assert result.command_status == "PROVISIONING_REJECTED_ACCOUNT_NOT_ACTIVE"
    assert result.seat_assignment_status == "SEAT_NOT_ASSIGNED"
    joined_queries = "\n".join(query for query, _ in conn.fetchrow_calls)
    assert "UPDATE platform_seats" not in joined_queries
    assert "INSERT INTO platform_account_audit_events" in joined_queries


async def test_access_provisioning_replays_matching_idempotency_key(monkeypatch):
    conn = FakeCommandConnection(
        [
            {
                "account_audit_event_id": "audit-provisioning-1",
                "membership_id": "membership-1",
                "next_status": "SEAT_ASSIGNED",
                "evidence_summary": {
                    "membership_id": "membership-1",
                    "role_family": "DISTRIBUTION_ADMIN",
                    "permission_set": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                    "seat_type": "ADMIN",
                    "seat_ref": "seat-1",
                    "seat_assignment_status": "SEAT_ASSIGNED",
                    "auth_claim_status": "AUTH_CLAIMS_NOT_PROPAGATED",
                    "provisioning_status": "PROVISIONING_REQUEST_RECORDED",
                    "command_payload_hash": "payload-hash",
                },
            }
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.request_referral_saas_access_provisioning(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
        membership_id="membership-1",
        seat_type="ADMIN",
        seat_assignment_evidence_ref=None,
        auth_provider_ref=None,
        auth_claim_evidence_ref=None,
        operator_notes=None,
        reason_code="CUSTOMER_PROFILE_ACCESS_PROVISIONING_REQUEST",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    assert result.command_status == "PROVISIONING_REPLAYED"
    assert result.idempotency_status == "REPLAYED"
    assert result.seat_ref == "seat-1"
    assert len(conn.fetchrow_calls) == 1


async def test_access_provisioning_conflicts_on_idempotency_payload_mismatch(
    monkeypatch,
):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                {
                    "account_audit_event_id": "audit-provisioning-1",
                    "membership_id": "membership-1",
                    "evidence_summary": {
                        "membership_id": "membership-1",
                        "command_payload_hash": "original-hash",
                    },
                }
            ]
        ),
    )

    with pytest.raises(svc.MembershipInvitationIdempotencyConflict):
        await svc.request_referral_saas_access_provisioning(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            external_reference_status="ACTIVE",
            membership_id="membership-1",
            seat_type="ADMIN",
            seat_assignment_evidence_ref=None,
            auth_provider_ref=None,
            auth_claim_evidence_ref=None,
            operator_notes=None,
            reason_code="CUSTOMER_PROFILE_ACCESS_PROVISIONING_REQUEST",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="new-hash",
            command_actor_ref="operator-1",
            command_actor_role="ADMIN",
        )
