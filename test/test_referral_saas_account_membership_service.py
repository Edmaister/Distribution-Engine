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
