from __future__ import annotations

import json
from contextlib import asynccontextmanager

import pytest

from services import referral_saas_account_setup_service as service

pytestmark = pytest.mark.asyncio


def _draft(**overrides):
    row = {
        "draft_id": "draft-uuid",
        "draft_ref": "draft_001",
        "draft_version": 3,
        "status": "READY_FOR_REVIEW",
        "external_tenant_ref": "fnb-referrals",
        "organisation_ref": "fnb-org",
        "safe_summary": {"organisation_name": "FNB Referral SaaS"},
    }
    row.update(overrides)
    return row


class FakeTransaction:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        self.conn.transaction_entered = True
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.conn.transaction_exited = True
        return False


class FakeConnection:
    def __init__(self, *, duplicate_ref=None, duplicate_owner_link=None):
        self.duplicate_ref = duplicate_ref
        self.duplicate_owner_link = duplicate_owner_link
        self.fetchrow_calls = []
        self.transaction_entered = False
        self.transaction_exited = False
        self.inserted = {
            "account": {
                "account_id": "acct-uuid",
                "account_code": "ACCT_GENERATED",
                "account_name": "FNB Referral SaaS",
                "status": "PENDING_ONBOARDING",
                "onboarding_status": "READY_FOR_REVIEW",
            },
            "organisation": {"organisation_id": "org-uuid"},
            "tenant": {
                "account_tenant_id": "acct-tenant-uuid",
                "status": "PENDING_SETUP",
            },
            "external_ref": {
                "external_ref_id": "external-ref-uuid",
                "ref_type": "external_tenant_ref",
                "external_ref": "fnb-referrals",
                "status": "ACTIVE",
            },
            "organisation_ref": {
                "external_ref_id": "organisation-ref-uuid",
                "ref_type": "organisation_ref",
                "external_ref": "fnb-org",
                "status": "ACTIVE",
            },
            "audit": {"account_audit_event_id": "audit-uuid"},
        }

    def transaction(self):
        return FakeTransaction(self)

    async def fetchrow(self, query, *params):
        self.fetchrow_calls.append((query, params))
        if "SELECT external_ref_id" in query:
            return self.duplicate_ref
        if "SELECT account_tenant_id" in query:
            return self.duplicate_owner_link
        if "INSERT INTO platform_accounts" in query:
            return self.inserted["account"]
        if "INSERT INTO platform_organisations" in query:
            return self.inserted["organisation"]
        if "INSERT INTO platform_account_tenants" in query:
            return self.inserted["tenant"]
        if "INSERT INTO platform_external_tenant_refs" in query:
            if params[3] == "organisation_ref":
                return self.inserted["organisation_ref"]
            return self.inserted["external_ref"]
        if "INSERT INTO platform_account_audit_events" in query:
            return self.inserted["audit"]
        raise AssertionError(f"Unexpected query: {query}")


def patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(service, "db_connection", fake_db_connection)


def patch_draft(monkeypatch, draft):
    async def fake_get_draft_by_ref(draft_ref):
        assert draft_ref == "draft_001"
        return draft

    monkeypatch.setattr(service.draft_repo, "get_draft_by_ref", fake_get_draft_by_ref)


async def test_create_durable_account_from_ready_draft(monkeypatch):
    conn = FakeConnection()
    patch_db(monkeypatch, conn)
    patch_draft(monkeypatch, _draft())

    result = await service.create_durable_account_from_onboarding_draft(
        draft_ref="draft_001",
        tenant_code="fnb",
        actor_ref="ops-user",
        actor_role="PLATFORM_ADMIN",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
    )

    safe = result.to_safe_dict()
    assert safe["accountStatus"] == "PENDING_ONBOARDING"
    assert safe["onboardingStatus"] == "READY_FOR_REVIEW"
    assert safe["tenantLinkStatus"] == "PENDING_SETUP"
    assert safe["draftRef"] == "draft_001"
    assert "tenantCode" not in safe
    assert safe["redactions"] == ["internal_tenant_identifier"]
    assert conn.transaction_entered is True
    assert conn.transaction_exited is True

    account_query, account_params = conn.fetchrow_calls[2]
    assert "INSERT INTO platform_accounts" in account_query
    assert account_params[2] == "ORGANISATION"
    assert account_params[3] == "PENDING_ONBOARDING"
    assert account_params[4] == "READY_FOR_REVIEW"
    assert json.loads(account_params[6])["draft_ref"] == "draft_001"

    tenant_query, tenant_params = conn.fetchrow_calls[4]
    assert "INSERT INTO platform_account_tenants" in tenant_query
    assert tenant_params[1] == "FNB"
    assert tenant_params[2] == "OWNER"

    external_ref_query, external_ref_params = conn.fetchrow_calls[5]
    assert "INSERT INTO platform_external_tenant_refs" in external_ref_query
    assert external_ref_params[3] == "external_tenant_ref"
    assert external_ref_params[5] == "ACTIVE"

    audit_query, audit_params = conn.fetchrow_calls[7]
    assert "INSERT INTO platform_account_audit_events" in audit_query
    assert audit_params[4] == "ACCOUNT_FOUNDATION_CREATED"
    assert audit_params[5] == "RECORDED"
    assert audit_params[11] == "idem-hash"


async def test_rejects_non_admin_actor_before_db_write(monkeypatch):
    conn = FakeConnection()
    patch_db(monkeypatch, conn)
    patch_draft(monkeypatch, _draft())

    with pytest.raises(service.AccountSetupPermissionDenied):
        await service.create_durable_account_from_onboarding_draft(
            draft_ref="draft_001",
            tenant_code="FNB",
            actor_ref="support-user",
            actor_role="SUPPORT",
        )

    assert conn.fetchrow_calls == []


async def test_rejects_missing_draft(monkeypatch):
    conn = FakeConnection()
    patch_db(monkeypatch, conn)
    patch_draft(monkeypatch, None)

    with pytest.raises(service.AccountSetupDraftNotFound):
        await service.create_durable_account_from_onboarding_draft(
            draft_ref="draft_001",
            tenant_code="FNB",
            actor_ref="ops-user",
            actor_role="ADMIN",
        )

    assert conn.fetchrow_calls == []


async def test_rejects_draft_not_ready_for_review(monkeypatch):
    conn = FakeConnection()
    patch_db(monkeypatch, conn)
    patch_draft(monkeypatch, _draft(status="DRAFT_CREATED"))

    with pytest.raises(service.AccountSetupInvalidDraftState):
        await service.create_durable_account_from_onboarding_draft(
            draft_ref="draft_001",
            tenant_code="FNB",
            actor_ref="ops-user",
            actor_role="ADMIN",
        )

    assert conn.fetchrow_calls == []


async def test_rejects_duplicate_external_reference_before_transaction(monkeypatch):
    conn = FakeConnection(duplicate_ref={"external_ref_id": "existing-ref"})
    patch_db(monkeypatch, conn)
    patch_draft(monkeypatch, _draft())

    with pytest.raises(service.AccountSetupDuplicateReference):
        await service.create_durable_account_from_onboarding_draft(
            draft_ref="draft_001",
            tenant_code="FNB",
            actor_ref="ops-user",
            actor_role="ADMIN",
        )

    assert len(conn.fetchrow_calls) == 1
    assert conn.transaction_entered is False


async def test_rejects_duplicate_internal_tenant_owner_before_transaction(monkeypatch):
    conn = FakeConnection(duplicate_owner_link={"account_tenant_id": "existing-link"})
    patch_db(monkeypatch, conn)
    patch_draft(monkeypatch, _draft())

    with pytest.raises(service.AccountSetupDuplicateReference):
        await service.create_durable_account_from_onboarding_draft(
            draft_ref="draft_001",
            tenant_code="FNB",
            actor_ref="ops-user",
            actor_role="ADMIN",
        )

    assert len(conn.fetchrow_calls) == 2
    assert conn.transaction_entered is False


async def test_rejects_missing_internal_tenant_scope_before_draft_lookup(monkeypatch):
    conn = FakeConnection()
    patch_db(monkeypatch, conn)

    async def fail_get_draft_by_ref(draft_ref):
        raise AssertionError("draft lookup should not run without tenant scope")

    monkeypatch.setattr(
        service.draft_repo,
        "get_draft_by_ref",
        fail_get_draft_by_ref,
    )

    with pytest.raises(service.AccountSetupMissingScope):
        await service.create_durable_account_from_onboarding_draft(
            draft_ref="draft_001",
            tenant_code="",
            actor_ref="ops-user",
            actor_role="ADMIN",
        )

    assert conn.fetchrow_calls == []


def test_service_does_not_define_routes_or_membership_commands():
    public_names = {
        name
        for name in dir(service)
        if not name.startswith("_") and callable(getattr(service, name))
    }

    assert "router" not in dir(service)
    for forbidden in (
        "invite",
        "membership",
        "campaign",
        "wallet",
        "fund",
        "fulfil",
        "settle",
        "webhook",
        "payout",
    ):
        assert all(forbidden not in name.lower() for name in public_names)
