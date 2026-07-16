from __future__ import annotations

import pytest
from httpx import AsyncClient

from apps.api.main import app
from apps.api.routers import referral_saas_accounts
from services.referral_saas_account_foundation_service import (
    AccountFoundationContext,
    AccountNotResolvable,
    ExternalReferenceConflict,
    ExternalReferenceNotActive,
    ExternalReferenceNotFound,
    InvalidExternalReferenceType,
    TenantLinkNotResolvable,
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
