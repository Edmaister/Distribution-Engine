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
        "subject": "owner@example.test",
        "displayName": "Setup Owner",
        "roleFamily": "DISTRIBUTION_ADMIN",
        "permissionSet": "ACCOUNT_SETUP_ADMIN",
        "status": "ACTIVE",
        "deliveryStatus": "DELIVERY_NOT_CONFIGURED",
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
