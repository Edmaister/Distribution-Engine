from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from services.admin_audit_service import get_admin_audit_summary, list_admin_audit
from utils.security import require_system_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/audit",
    tags=["Admin Audit"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("/summary")
async def get_admin_audit_log_summary(
    action_domain: str | None = Query(default=None),
    tenant_code: str | None = Query(default=None),
    hours: int = Query(default=24, ge=1, le=168),
) -> dict:
    summary = await get_admin_audit_summary(
        action_domain=action_domain,
        tenant_code=tenant_code,
        hours=hours,
    )

    return {
        "status": "ok",
        "summary": summary,
    }


@router.get("")
async def list_admin_audit_log(
    action_domain: str | None = Query(default=None),
    action_type: str | None = Query(default=None),
    tenant_code: str | None = Query(default=None),
    target_type: str | None = Query(default=None),
    target_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    items = await list_admin_audit(
        action_domain=action_domain,
        action_type=action_type,
        tenant_code=tenant_code,
        target_type=target_type,
        target_id=target_id,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(items),
        "items": items,
    }
