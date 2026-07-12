from __future__ import annotations

from dataclasses import dataclass
from typing import Any

INTERNAL_TENANT_SCOPE = "INTERNAL"
INTERNAL_SCOPE_ROLES = {"ADMIN", "SYSTEM_ADMIN", "DISTRIBUTION_ADMIN", "PLATFORM_ADMIN"}


@dataclass(frozen=True)
class ReferralSaasAccountScope:
    tenant_code: str
    source: str
    external_tenant_ref: str | None = None


def _normalise(value: Any) -> str:
    return str(value or "").strip().upper()


def resolve_referral_saas_account_scope(
    *,
    identity: dict[str, Any],
    requested_tenant_code: str | None = None,
) -> ReferralSaasAccountScope:
    identity_tenant = _normalise(
        identity.get("tenant_code") or identity.get("tenant") or None
    )
    requested_tenant = _normalise(requested_tenant_code)
    role = _normalise(identity.get("role"))

    if requested_tenant:
        if (
            identity_tenant
            and identity_tenant != INTERNAL_TENANT_SCOPE
            and requested_tenant != identity_tenant
        ):
            raise PermissionError("Requested tenant scope is not available.")
        return ReferralSaasAccountScope(
            tenant_code=requested_tenant,
            source="explicit_tenant_code",
        )

    if identity_tenant and identity_tenant != INTERNAL_TENANT_SCOPE:
        return ReferralSaasAccountScope(
            tenant_code=identity_tenant,
            source="identity_tenant",
        )

    if role in INTERNAL_SCOPE_ROLES:
        raise ValueError(
            "tenant_code is required until Referral SaaS account scope resolution "
            "is implemented for internal report readers"
        )

    raise PermissionError("Referral SaaS account scope could not be resolved.")
