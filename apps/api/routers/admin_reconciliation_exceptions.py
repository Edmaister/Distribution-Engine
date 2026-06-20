from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, Query

from services.reconciliation_exception_service import (
    assign_exception,
    get_exception,
    list_exceptions,
    reopen_exception,
    resolve_exception,
)
from utils.security import require_admin_key


router = APIRouter(
    prefix="/admin/reconciliation/exceptions",
    tags=["Admin - Reconciliation Exceptions"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("")
async def get_exceptions(
    status: Optional[str] = Query(default=None),
    assigned_to: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    exceptions = await list_exceptions(
        status=status,
        assigned_to=assigned_to,
        limit=limit,
    )

    return {
        "status": "ok",
        "count": len(exceptions),
        "items": exceptions,
    }


@router.get("/{exception_id}")
async def get_reconciliation_exception(
    exception_id: str,
):
    exception = await get_exception(
        exception_id=exception_id,
    )

    if not exception:
        return {
            "status": "not_found",
            "exception_id": exception_id,
        }

    return {
        "status": "ok",
        "item": exception,
    }


@router.post("/{exception_id}/assign")
async def assign_reconciliation_exception(
    exception_id: str,
    assigned_to: str = Body(..., embed=True),
):
    exception = await assign_exception(
        exception_id=exception_id,
        assigned_to=assigned_to,
    )

    if not exception:
        return {
            "status": "not_found",
            "exception_id": exception_id,
        }

    return {
        "status": "ok",
        "item": exception,
    }


@router.post("/{exception_id}/resolve")
async def resolve_reconciliation_exception(
    exception_id: str,
    resolution_notes: str = Body(..., embed=True),
):
    exception = await resolve_exception(
        exception_id=exception_id,
        resolution_notes=resolution_notes,
    )

    if not exception:
        return {
            "status": "not_found",
            "exception_id": exception_id,
        }

    return {
        "status": "ok",
        "item": exception,
    }


@router.post("/{exception_id}/reopen")
async def reopen_reconciliation_exception(
    exception_id: str,
):
    exception = await reopen_exception(
        exception_id=exception_id,
    )

    if not exception:
        return {
            "status": "not_found",
            "exception_id": exception_id,
        }

    return {
        "status": "ok",
        "item": exception,
    }
