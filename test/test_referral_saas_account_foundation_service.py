from __future__ import annotations

from contextlib import asynccontextmanager

import pytest

from services import referral_saas_account_foundation_service as svc

pytestmark = pytest.mark.asyncio


def _row(**overrides):
    row = {
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
    row.update(overrides)
    return row


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    async def fetch(self, query, *args):
        self.calls.append((query, args))
        return self.rows


class FakeDbConnection:
    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, exc_type, exc, tb):
        return False


def patch_db(monkeypatch, connection):
    @asynccontextmanager
    async def fake_db_connection():
        yield connection

    monkeypatch.setattr(svc, "db_connection", fake_db_connection)


async def test_resolves_active_external_reference_to_account_context(monkeypatch):
    conn = FakeConnection([_row()])
    patch_db(monkeypatch, conn)

    context = await svc.resolve_account_by_external_reference(
        ref_type="external_tenant_ref",
        external_ref=" fnb-referrals ",
    )

    assert context.account_code == "ACCT_FNB"
    assert context.tenant_code == "FNB"
    assert context.account_tenant_id == "acct-tenant-1"
    assert conn.calls[0][1] == ("external_tenant_ref", "fnb-referrals")


async def test_safe_summary_hides_internal_tenant_code(monkeypatch):
    patch_db(monkeypatch, FakeConnection([_row()]))

    context = await svc.resolve_account_by_external_reference(
        ref_type="external_tenant_ref",
        external_ref="fnb-referrals",
    )

    safe_payload = context.to_safe_dict()
    internal_payload = context.to_safe_dict(include_internal=True)

    assert "tenantCode" not in safe_payload
    assert internal_payload["tenantCode"] == "FNB"


async def test_rejects_unsupported_reference_type_before_query(monkeypatch):
    conn = FakeConnection([_row()])
    patch_db(monkeypatch, conn)

    with pytest.raises(svc.InvalidExternalReferenceType):
        await svc.resolve_account_by_external_reference(
            ref_type="tenant_code",
            external_ref="FNB",
        )

    assert conn.calls == []


async def test_missing_reference_is_rejected(monkeypatch):
    patch_db(monkeypatch, FakeConnection([]))

    with pytest.raises(svc.ExternalReferenceNotFound):
        await svc.resolve_account_by_external_reference(
            ref_type="external_tenant_ref",
            external_ref="missing-ref",
        )


async def test_disabled_reference_is_not_resolved(monkeypatch):
    patch_db(monkeypatch, FakeConnection([_row(reference_status="DISABLED")]))

    with pytest.raises(svc.ExternalReferenceNotActive):
        await svc.resolve_account_by_external_reference(
            ref_type="external_tenant_ref",
            external_ref="disabled-ref",
        )


async def test_duplicate_active_reference_rows_are_rejected(monkeypatch):
    patch_db(monkeypatch, FakeConnection([_row(), _row(account_id="acct-2")]))

    with pytest.raises(svc.ExternalReferenceConflict):
        await svc.resolve_account_by_external_reference(
            ref_type="external_tenant_ref",
            external_ref="duplicate-ref",
        )


async def test_suspended_account_is_not_resolved_for_runtime(monkeypatch):
    patch_db(monkeypatch, FakeConnection([_row(account_status="SUSPENDED")]))

    with pytest.raises(svc.AccountNotResolvable):
        await svc.resolve_account_by_external_reference(
            ref_type="external_tenant_ref",
            external_ref="suspended-account",
        )


async def test_suspended_account_can_be_read_for_setup_context(monkeypatch):
    patch_db(
        monkeypatch,
        FakeConnection(
            [
                _row(
                    account_status="SUSPENDED",
                    tenant_link_status="SUSPENDED",
                    onboarding_status="BLOCKED",
                )
            ]
        ),
    )

    context = await svc.resolve_setup_account_by_external_reference(
        ref_type="external_tenant_ref",
        external_ref="setup-ref",
    )

    assert context.account_status == "SUSPENDED"
    assert context.tenant_link_status == "SUSPENDED"


async def test_missing_tenant_link_is_rejected(monkeypatch):
    patch_db(
        monkeypatch,
        FakeConnection([_row(account_tenant_id=None, tenant_link_status=None)]),
    )

    with pytest.raises(svc.TenantLinkNotResolvable):
        await svc.resolve_account_by_external_reference(
            ref_type="external_tenant_ref",
            external_ref="missing-link",
        )


async def test_disabled_tenant_link_is_rejected(monkeypatch):
    patch_db(monkeypatch, FakeConnection([_row(tenant_link_status="DISABLED")]))

    with pytest.raises(svc.TenantLinkNotResolvable):
        await svc.resolve_account_by_external_reference(
            ref_type="external_tenant_ref",
            external_ref="disabled-link",
        )
