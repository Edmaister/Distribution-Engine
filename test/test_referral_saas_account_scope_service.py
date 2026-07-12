from __future__ import annotations

import pytest

from services.referral_saas_account_scope_service import (
    resolve_referral_saas_account_scope,
)


def test_report_scope_can_derive_tenant_from_identity():
    scope = resolve_referral_saas_account_scope(
        identity={"role": "ADMIN", "tenant_code": "fnb"},
    )

    assert scope.tenant_code == "FNB"
    assert scope.source == "identity_tenant"
    assert scope.external_tenant_ref is None


def test_internal_report_reader_may_use_explicit_tenant_scope():
    scope = resolve_referral_saas_account_scope(
        identity={"role": "DISTRIBUTION_ADMIN", "tenant_code": "INTERNAL"},
        requested_tenant_code=" fnb ",
    )

    assert scope.tenant_code == "FNB"
    assert scope.source == "explicit_tenant_code"


def test_internal_report_reader_without_scope_is_rejected():
    with pytest.raises(ValueError, match="tenant_code is required"):
        resolve_referral_saas_account_scope(
            identity={"role": "ADMIN", "tenant_code": "INTERNAL"},
        )


def test_cross_tenant_override_is_rejected():
    with pytest.raises(PermissionError, match="Requested tenant scope"):
        resolve_referral_saas_account_scope(
            identity={"role": "ADMIN", "tenant_code": "FNB"},
            requested_tenant_code="PNP",
        )


def test_missing_identity_scope_is_rejected():
    with pytest.raises(PermissionError, match="could not be resolved"):
        resolve_referral_saas_account_scope(identity={"role": "ANALYST"})
