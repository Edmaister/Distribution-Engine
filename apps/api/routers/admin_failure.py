from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from services.failure_admin_service import (
    get_failure_summary,
    list_failures,
    reprocess_failure,
    resolve_failure,
)
from utils.security import require_admin_key

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/failures",
    tags=["Admin Failures"],
    dependencies=[Depends(require_admin_key)],
)


class ResolveFailureRequest(BaseModel):
    resolutionNote: Optional[str] = Field(default=None, max_length=1000)


@router.get("")
async def get_failures(
    status: Optional[str] = Query(default="OPEN"),
    failureCategory: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    normalized_status = status.strip().upper() if status and status.strip() else None
    normalized_failure_category = (
        failureCategory.strip().upper()
        if failureCategory and failureCategory.strip()
        else None
    )

    items = await list_failures(
        status=normalized_status,
        failure_category=normalized_failure_category,
        limit=limit,
    )

    return {
        "count": len(items),
        "items": items,
    }


@router.post("/{failure_id}/resolve")
async def resolve_failure_endpoint(
    failure_id: int,
    request: ResolveFailureRequest,
):
    updated = await resolve_failure(
        failure_id=failure_id,
        resolution_note=request.resolutionNote,
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Failure not found or already resolved",
        )

    return {
        "status": "ok",
        "failureId": failure_id,
        "resolved": True,
    }


@router.post("/{failure_id}/reprocess")
async def reprocess_failure_endpoint(failure_id: int):
    try:
        return await reprocess_failure(failure_id=failure_id)
    except ValueError as exc:
        logger.warning("Failure reprocess rejected: %s", exc)
        raise HTTPException(
            status_code=400,
            detail="Invalid request",
        )


@router.get("/summary")
async def get_failures_summary():
    return await get_failure_summary()
