from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, status

from apps.api.settings import settings
from services.privacy_purge_scheduler import run_privacy_purge
from services.privacy_service import erase_referrer_by_ucn
from utils.db import db_connection
from utils.security import require_admin_key


router = APIRouter(prefix="/v1/privacy", tags=["privacy"])


@router.delete("/referrers/{ucn}")
async def erase_referrer(
    ucn: str = Path(...),
    tenant_code: str | None = Query(default=None),
    jurisdiction_code: str | None = Query(default=None),
    x_requested_by: str | None = Header(default="admin"),
    _: None = Depends(require_admin_key),
):
    correlation_id = str(uuid4())
    resolved_tenant = tenant_code or settings.tenant_default

    try:
        result = await erase_referrer_by_ucn(
            referrer_ucn=ucn,
            tenant_code=resolved_tenant,
            requested_by=x_requested_by or "admin",
            correlation_id=correlation_id,
            jurisdiction_code=jurisdiction_code,
        )

        if result.get("status") == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result,
            )

        return result

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "Failed to process erasure request",
                "correlation_id": correlation_id,
            },
        )


@router.get("/audit/{correlation_id}")
async def get_privacy_audit_by_correlation_id(
    correlation_id: str = Path(..., description="Privacy erasure correlation ID"),
    _: None = Depends(require_admin_key),
):
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT audit_id,
                   correlation_id,
                   tenant_code,
                   referrer_code_id,
                   requested_by,
                   status,
                   referral_instances_anonymised,
                   referrer_codes_anonymised,
                   created_at
              FROM privacy_erasure_audit
             WHERE correlation_id = $1
            """,
            correlation_id,
        )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit record not found",
        )

    return dict(row)


@router.get("/audit")
async def search_privacy_audit(
    tenant_code: str | None = Query(default=None),
    requested_by: str | None = Query(default=None),
    audit_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    _: None = Depends(require_admin_key),
):
    query = """
        SELECT audit_id,
               correlation_id,
               tenant_code,
               referrer_code_id,
               requested_by,
               status,
               referral_instances_anonymised,
               referrer_codes_anonymised,
               created_at
          FROM privacy_erasure_audit
         WHERE 1 = 1
    """

    params = []
    param_index = 1

    if tenant_code:
        query += f" AND tenant_code = ${param_index}"
        params.append(tenant_code)
        param_index += 1

    if requested_by:
        query += f" AND requested_by = ${param_index}"
        params.append(requested_by)
        param_index += 1

    if audit_status:
        query += f" AND status = ${param_index}"
        params.append(audit_status)
        param_index += 1

    query += f" ORDER BY created_at DESC LIMIT ${param_index}"
    params.append(limit)

    async with db_connection() as conn:
        rows = await conn.fetch(query, *params)

    return [dict(row) for row in rows]


@router.post("/purge/run")
async def run_privacy_purge_now(
    _: None = Depends(require_admin_key),
):
    return await run_privacy_purge()