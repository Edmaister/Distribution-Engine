from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.Workers.ids_consumer import ingest_event
from apps.api.schemas.enterprise_events import (
    EnterpriseEventIngestRequest,
    EnterpriseEventIngestResponse,
)
from utils.security import require_admin_or_partner_key

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/enterprise",
    tags=["Enterprise Events"],
    dependencies=[Depends(require_admin_or_partner_key)],
)


@router.post("/events", response_model=EnterpriseEventIngestResponse)
async def ingest_enterprise_event(
    payload: EnterpriseEventIngestRequest,
    request: Request,
    identity=Depends(require_admin_or_partner_key),
):
    event = payload.model_dump(by_alias=True, exclude_none=True)

    tenant_code = identity.get("tenant_code")
    if tenant_code and tenant_code != "INTERNAL":
        event.setdefault("tenantCode", tenant_code)

    try:
        return await ingest_event(event)
    except Exception:
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        logger.exception(
            "Enterprise event ingestion failed | correlation_id=%s | event_type=%s",
            correlation_id,
            event.get("eventType"),
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ENTERPRISE_EVENT_INGESTION_FAILED",
                "correlation_id": correlation_id,
            },
        )
