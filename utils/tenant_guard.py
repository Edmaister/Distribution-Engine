from fastapi import HTTPException

from services.tenant_service import get_tenant


async def require_valid_tenant(tenant_code: str) -> str:
    tenant = await get_tenant(tenant_code)

    if not tenant:
        raise HTTPException(
            status_code=400,
            detail="Invalid tenant",
        )

    if not tenant["is_active"]:
        raise HTTPException(
            status_code=403,
            detail="Tenant inactive",
        )

    return tenant_code