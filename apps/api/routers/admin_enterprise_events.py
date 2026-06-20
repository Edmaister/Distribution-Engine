from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from services.admin_audit_service import try_write_admin_audit
from services.enterprise_event_inbox_service import (
    get_enterprise_event_dashboard,
    get_enterprise_event_summary,
    list_enterprise_events,
    replay_enterprise_event,
)
from utils.security import require_system_admin_key as require_admin_key

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/enterprise-events",
    tags=["Admin Enterprise Events"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("/summary")
async def enterprise_event_summary():
    return await get_enterprise_event_summary()


@router.get("/dashboard")
async def enterprise_event_dashboard(
    tenantCode: Optional[str] = Query(default=None),
    days: int = Query(default=7, ge=1, le=90),
    problemLimit: int = Query(default=25, ge=1, le=100),
):
    normalized_tenant = (
        tenantCode.strip().upper()
        if tenantCode and tenantCode.strip()
        else None
    )

    return await get_enterprise_event_dashboard(
        tenant_code=normalized_tenant,
        days=days,
        problem_limit=problemLimit,
    )


@router.get("")
async def enterprise_event_list(
    processingStatus: Optional[str] = Query(default=None),
    sourceSystem: Optional[str] = Query(default=None),
    referralTrackId: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    normalized_status = (
        processingStatus.strip().upper()
        if processingStatus and processingStatus.strip()
        else None
    )
    normalized_source = (
        sourceSystem.strip().upper()
        if sourceSystem and sourceSystem.strip()
        else None
    )

    return await list_enterprise_events(
        processing_status=normalized_status,
        source_system=normalized_source,
        referral_track_id=referralTrackId,
        limit=limit,
    )


@router.post("/{inbox_event_id}/replay")
async def enterprise_event_replay(
    inbox_event_id: str,
    dryRun: bool = Query(default=True),
    identity: dict = Depends(require_admin_key),
):
    try:
        result = await replay_enterprise_event(
            inbox_event_id=inbox_event_id,
            dry_run=dryRun,
        )
        await try_write_admin_audit(
            action_type="ENTERPRISE_EVENT_REPLAY",
            action_domain="SYSTEM",
            identity=identity,
            target_type="enterprise_event_inbox",
            target_id=inbox_event_id,
            request_payload={"dry_run": dryRun},
            result_payload={
                "status": result.get("status") if isinstance(result, dict) else None,
                "queued": result.get("queued") if isinstance(result, dict) else None,
            },
        )
        return result
    except ValueError as exc:
        logger.warning("Enterprise event replay rejected: %s", exc)
        await try_write_admin_audit(
            action_type="ENTERPRISE_EVENT_REPLAY",
            action_domain="SYSTEM",
            action_status="FAILED",
            identity=identity,
            target_type="enterprise_event_inbox",
            target_id=inbox_event_id,
            request_payload={"dry_run": dryRun},
            error_message=str(exc),
        )
        raise HTTPException(status_code=404, detail=str(exc))
