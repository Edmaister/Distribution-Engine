from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field

from services.channel_readiness_service import (
    get_channel_preferences,
    process_inbound_channel_webhook,
    set_channel_preferences,
)
from utils.permissions import require_consumer_scope, require_distributor_scope
from utils.security import require_session_key


router = APIRouter(
    prefix="/channels",
    tags=["Channels"],
)


class ChannelPreferenceRequest(BaseModel):
    tenant_code: str = Field(..., min_length=1)
    preferred_channels: list[str] = Field(default_factory=list)
    consent_channels: list[str] = Field(default_factory=list)
    opt_out_channels: list[str] = Field(default_factory=list)


@router.post("/webhooks/{channel_code}")
async def receive_channel_webhook(
    channel_code: str,
    request: Request,
    x_amplifi_signature: str | None = Header(default=None),
):
    result = await process_inbound_channel_webhook(
        channel_code=channel_code,
        raw_body=await request.body(),
        signature=x_amplifi_signature,
    )
    return result


@router.get("/preferences/{audience}/{subject_id}")
async def read_channel_preferences(
    audience: str,
    subject_id: str,
    tenant_code: str,
    identity: dict = Depends(require_session_key),
):
    _enforce_preference_scope(
        identity=identity,
        tenant_code=tenant_code,
        audience=audience,
        subject_id=subject_id,
    )
    return {
        "status": "ok",
        "preferences": get_channel_preferences(
            tenant_code=tenant_code,
            audience=audience,
            subject_id=subject_id,
        ),
    }


@router.put("/preferences/{audience}/{subject_id}")
async def write_channel_preferences(
    audience: str,
    subject_id: str,
    request: ChannelPreferenceRequest,
    identity: dict = Depends(require_session_key),
):
    _enforce_preference_scope(
        identity=identity,
        tenant_code=request.tenant_code,
        audience=audience,
        subject_id=subject_id,
    )
    return {
        "status": "ok",
        "preferences": set_channel_preferences(
            tenant_code=request.tenant_code,
            audience=audience,
            subject_id=subject_id,
            preferred_channels=request.preferred_channels,
            consent_channels=request.consent_channels,
            opt_out_channels=request.opt_out_channels,
        ),
    }


def _enforce_preference_scope(
    *,
    identity: dict,
    tenant_code: str,
    audience: str,
    subject_id: str,
) -> None:
    normalized_audience = audience.strip().upper()
    if normalized_audience == "DISTRIBUTOR":
        require_distributor_scope(
            identity,
            tenant_code=tenant_code,
            distributor_code=subject_id,
        )
        return

    if normalized_audience == "CONSUMER":
        require_consumer_scope(identity, tenant_code=tenant_code)
        return

    from fastapi import HTTPException

    raise HTTPException(
        status_code=400,
        detail="Channel preferences support CONSUMER and DISTRIBUTOR audiences",
    )
