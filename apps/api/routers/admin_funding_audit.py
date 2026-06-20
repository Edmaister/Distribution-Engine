from __future__ import annotations

from fastapi import APIRouter, Depends

from services.funding.resolution_audit import (
    list_funding_resolution_audit,
)
from utils.security import require_finance_admin_key as require_admin_key

router = APIRouter(
    prefix="/admin/funding/audit",
    tags=["Funding Audit"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("")
async def get_funding_resolution_audit(
    tenant_code: str | None = None,
    limit: int = 100,
) -> dict:
    items = await list_funding_resolution_audit(
        tenant_code=tenant_code,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(items),
        "items": items,
    }
