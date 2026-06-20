from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from services.channel_readiness_service import (
    dispatch_channel_message,
    list_channel_audit,
    list_channel_deliveries,
    get_channel_readiness,
    recommend_channels,
    retry_channel_delivery,
)
from utils.security import require_distribution_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/channels",
    tags=["Admin - Channels"],
    dependencies=[Depends(require_admin_key)],
)


class ChannelDispatchRequest(BaseModel):
    channel_code: str = Field(..., min_length=1)
    recipient: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    tenant_code: str | None = None
    context: dict | None = None


class ChannelRecommendationRequest(BaseModel):
    event_type: str = Field(..., min_length=1)
    audience: str = Field(..., min_length=1)
    target_channels: list[str] = Field(default_factory=list)
    distributor_channels: list[str] = Field(default_factory=list)


@router.get("/readiness")
async def get_admin_channel_readiness():
    return {
        "status": "ok",
        "readiness": get_channel_readiness(),
    }


@router.post("/recommendations")
async def get_admin_channel_recommendations(request: ChannelRecommendationRequest):
    return {
        "status": "ok",
        "recommendations": recommend_channels(
            event_type=request.event_type,
            audience=request.audience,
            target_channels=request.target_channels,
            distributor_channels=request.distributor_channels,
        ),
    }


@router.get("/deliveries")
async def get_admin_channel_deliveries(
    status: str | None = None,
    limit: int = 50,
):
    return {
        "status": "ok",
        "deliveries": list_channel_deliveries(status_filter=status, limit=limit),
    }


@router.get("/audit")
async def get_admin_channel_audit(limit: int = 50):
    return {
        "status": "ok",
        "audit": list_channel_audit(limit=limit),
    }


@router.post("/dispatch")
async def dispatch_admin_channel_message(request: ChannelDispatchRequest):
    result = await dispatch_channel_message(
        channel_code=request.channel_code,
        recipient=request.recipient,
        message=request.message,
        tenant_code=request.tenant_code,
        context=request.context,
    )
    return {
        "status": result["status"].lower(),
        "dispatch": result,
    }


@router.post("/deliveries/{delivery_id}/retry")
async def retry_admin_channel_delivery(delivery_id: str):
    result = await retry_channel_delivery(delivery_id=delivery_id)
    return {
        "status": result["status"].lower(),
        "retry": result,
    }
