from __future__ import annotations

from fastapi import HTTPException


def _role(identity: dict) -> str:
    return str(identity.get("role") or "").upper()


def _claim(identity: dict, name: str) -> str:
    return str(identity.get(name) or "").strip().upper()


def require_tenant_scope(identity: dict, tenant_code: str) -> None:
    if _role(identity) == "ADMIN":
        return

    if _claim(identity, "tenant_code") != tenant_code.strip().upper():
        raise HTTPException(
            status_code=403,
            detail="API key is not authorised for this tenant",
        )


def require_partner_tenant_scope(identity: dict, tenant_code: str) -> None:
    role = _role(identity)
    if role == "ADMIN":
        return

    if role not in {"PARTNER", "TENANT_ADMIN"}:
        raise HTTPException(
            status_code=403,
            detail="API key is not authorised for this tenant",
        )

    require_tenant_scope(identity, tenant_code)


def require_producer_scope(
    identity: dict,
    *,
    tenant_code: str,
    producer_code: str,
) -> None:
    role = _role(identity)
    if role == "ADMIN":
        return

    require_tenant_scope(identity, tenant_code)

    if role == "PRODUCER" and _claim(identity, "producer_code") != producer_code.strip().upper():
        raise HTTPException(
            status_code=403,
            detail="API key is not authorised for this producer",
        )

    if role not in {"PRODUCER", "PARTNER", "TENANT_ADMIN"}:
        raise HTTPException(
            status_code=403,
            detail="API key is not authorised for this producer",
        )


def require_distributor_scope(
    identity: dict,
    *,
    tenant_code: str,
    distributor_code: str,
) -> None:
    role = _role(identity)
    if role == "ADMIN":
        return

    require_tenant_scope(identity, tenant_code)

    if role == "DISTRIBUTOR" and _claim(identity, "distributor_code") != distributor_code.strip().upper():
        raise HTTPException(
            status_code=403,
            detail="API key is not authorised for this distributor",
        )

    if role not in {"DISTRIBUTOR", "PARTNER", "TENANT_ADMIN"}:
        raise HTTPException(
            status_code=403,
            detail="API key is not authorised for this distributor",
        )


def require_consumer_scope(
    identity: dict,
    *,
    tenant_code: str,
) -> None:
    role = _role(identity)
    if role == "ADMIN":
        return

    require_tenant_scope(identity, tenant_code)

    if role not in {"CONSUMER", "PARTNER", "TENANT_ADMIN"}:
        raise HTTPException(
            status_code=403,
            detail="API key is not authorised for this consumer experience",
        )
