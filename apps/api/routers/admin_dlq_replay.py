from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from services.dlq_replay_service import replay_dlq_event
from utils.security import require_system_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/dlq",
    tags=["Admin DLQ Replay"],
    dependencies=[Depends(require_admin_key)],
)


@router.post("/replay")
def replay_dlq(payload: Dict[str, Any]):
    try:
        return replay_dlq_event(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
