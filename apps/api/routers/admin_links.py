from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from services.link_code_service import inspect_link_code
from utils.security import require_distribution_admin_key

router = APIRouter(
    prefix="/admin/links",
    tags=["Admin - Links"],
)


def _normalise_tenant_code(tenant_code: str) -> str:
    tenant = str(tenant_code or "").strip().upper()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "tenant_code is required",
            },
        )
    return tenant


@router.get("/inspect")
async def inspect_admin_link_code(
    tenant_code: Annotated[str, Query(min_length=1)],
    source_type: Annotated[str, Query(min_length=1)],
    link_code_id: str | None = Query(default=None),
    code_or_ref: str | None = Query(default=None),
    include_evidence: bool = Query(default=True),
    identity: dict = Depends(require_distribution_admin_key),
) -> dict[str, Any]:
    resolved_tenant = _normalise_tenant_code(tenant_code)

    try:
        link_code = await inspect_link_code(
            tenant_code=resolved_tenant,
            source_type=source_type,
            link_code_id=link_code_id,
            code_or_ref=code_or_ref,
            include_evidence=include_evidence,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": str(exc),
            },
        ) from exc

    return {
        "status": "ok",
        "link_code": link_code,
        "guardrail": (
            "Read-only admin link/code inspection. This endpoint does not "
            "issue, resolve, void, rotate, mutate, or generate codes."
        ),
    }
