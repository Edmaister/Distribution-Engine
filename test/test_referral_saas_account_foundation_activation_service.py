from __future__ import annotations

from contextlib import asynccontextmanager

import pytest

from services import referral_saas_account_foundation_service as svc

pytestmark = pytest.mark.asyncio


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


async def test_account_foundation_activation_moves_foundation_to_active(monkeypatch):
    conn = FakeCommandConnection(
        [
            None,
            {
                "account_id": "acct-1",
                "account_code": "ACCT_FNB",
                "account_name": "FNB Referral SaaS",
                "account_status": "PENDING_ONBOARDING",
                "onboarding_status": "READY_FOR_REVIEW",
                "account_tenant_id": "acct-tenant-1",
                "tenant_link_status": "PENDING_SETUP",
                "external_ref_id": "external-ref-1",
                "reference_status": "ACTIVE",
            },
            {
                "account_id": "acct-1",
                "account_code": "ACCT_FNB",
                "account_name": "FNB Referral SaaS",
                "status": "ACTIVE",
                "onboarding_status": "APPROVED",
            },
            {"account_tenant_id": "acct-tenant-1", "status": "ACTIVE"},
            {"created_seat_types": ["ADMIN", "OPERATOR"], "created_seat_count": 2},
            {"account_audit_event_id": "audit-account-activation-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.activate_referral_saas_account_foundation(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        seat_types=["ADMIN", "OPERATOR"],
        actor_ref="operator-1",
        actor_role="ADMIN",
        reason_code="CUSTOMER_ACCOUNT_FOUNDATION_ACTIVATION",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
    )

    payload = result.to_safe_dict()
    assert payload["commandStatus"] == "ACCOUNT_FOUNDATION_ACTIVATED"
    assert payload["accountStatus"] == "ACTIVE"
    assert payload["onboardingStatus"] == "APPROVED"
    assert payload["tenantLinkStatus"] == "ACTIVE"
    assert payload["seatCapacity"] == {
        "seatTypes": ["ADMIN", "OPERATOR"],
        "createdSeatCount": 2,
    }
    assert payload["noMembershipWriteConfirmed"] is True
    assert payload["noSeatAssignmentConfirmed"] is True
    assert payload["noAuthClaimChangeConfirmed"] is True
    assert payload["noBillingOrMoneyMovementConfirmed"] is True

    joined_queries = "\n".join(call[0] for call in conn.fetchrow_calls)
    assert "UPDATE platform_accounts" in joined_queries
    assert "UPDATE platform_account_tenants" in joined_queries
    assert "INSERT INTO platform_seats" in joined_queries
    assert "INSERT INTO platform_account_audit_events" in joined_queries
    assert "UPDATE platform_memberships" not in joined_queries
    assert "assigned_membership_id = " not in joined_queries
    assert "auth_claim" not in joined_queries.lower().replace("no_auth_claim", "")


async def test_account_foundation_activation_replays_matching_idempotency(monkeypatch):
    conn = FakeCommandConnection(
        [
            {
                "account_audit_event_id": "audit-account-activation-1",
                "evidence_summary": {
                    "account_id": "acct-1",
                    "account_code": "ACCT_FNB",
                    "account_name": "FNB Referral SaaS",
                    "previous_account_status": "PENDING_ONBOARDING",
                    "account_status": "ACTIVE",
                    "previous_onboarding_status": "READY_FOR_REVIEW",
                    "onboarding_status": "APPROVED",
                    "previous_tenant_link_status": "PENDING_SETUP",
                    "tenant_link_status": "ACTIVE",
                    "requested_seat_types": ["ADMIN", "OPERATOR"],
                    "created_seat_count": 2,
                    "command_status": "ACCOUNT_FOUNDATION_ACTIVATED",
                    "command_payload_hash": "payload-hash",
                },
            }
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.activate_referral_saas_account_foundation(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        seat_types=["ADMIN", "OPERATOR"],
        actor_ref="operator-1",
        actor_role="ADMIN",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
    )

    payload = result.to_safe_dict()
    assert payload["idempotency"]["status"] == "REPLAYED"
    assert payload["commandStatus"] == "ACCOUNT_FOUNDATION_ACTIVATED"
    joined_queries = "\n".join(call[0] for call in conn.fetchrow_calls)
    assert "UPDATE platform_accounts" not in joined_queries
    assert "INSERT INTO platform_seats" not in joined_queries


async def test_account_foundation_activation_rejects_idempotency_conflict(monkeypatch):
    conn = FakeCommandConnection(
        [
            {
                "account_audit_event_id": "audit-account-activation-1",
                "evidence_summary": {
                    "command_payload_hash": "previous-payload-hash",
                },
            }
        ]
    )
    patch_db(monkeypatch, conn)

    with pytest.raises(svc.AccountFoundationActivationIdempotencyConflict):
        await svc.activate_referral_saas_account_foundation(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            actor_ref="operator-1",
            actor_role="ADMIN",
            idempotency_key_hash="idem-hash",
            command_payload_hash="new-payload-hash",
        )


async def test_account_foundation_activation_rejects_unsupported_seat_type():
    with pytest.raises(svc.AccountFoundationActivationValidationError):
        await svc.activate_referral_saas_account_foundation(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            seat_types=["ROOT"],
            actor_ref="operator-1",
            actor_role="ADMIN",
        )
