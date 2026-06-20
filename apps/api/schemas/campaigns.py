from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class CampaignCreateRequest(BaseModel):
    tenant_code: Optional[str] = Field(None, description="Tenant/brand code, e.g., FNB (optional)")
    segment: str = Field(..., description="Target segment: EASY/ASPIRE/PREMIER/...")
    name: str = Field(..., description="Human-friendly campaign name")
    campaign_code: Optional[str] = Field(
        None,
        description="Optional campaign code override. If omitted, the service generates one.",
    )
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    max_uses: Optional[int] = Field(None, ge=1, description="Optional hard cap on total uses")
    attributes: Optional[Dict[str, Any]] = None


class CampaignCreateResponse(BaseModel):
    campaignCode: str
    mode: Optional[str] = None


class CampaignValidateRequest(BaseModel):
    tenant_code: Optional[str] = None
    campaign_code: str
    user_ucn_encrypted: Optional[str] = None
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
    qr_payload: Optional[str] = None
    source_channel: Optional[str] = Field(None, description="e.g. QR, WhatsApp, Web")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Arbitrary validation context")


class CampaignValidateResponse(BaseModel):
    valid: bool
    reason: Optional[str] = None
    campaignCode: str
    campaignTrackId: Optional[str] = None


CampaignTrackStatus = Literal[
    "SCANNED",
    "VALIDATED",
    "ATTRIBUTED",
    "COMPLETED",
    "BLOCKED",
    "EXPIRED",
    "INVALID",
]


class CampaignTrackUpdateRequest(BaseModel):
    status: CampaignTrackStatus


class CampaignTrackUpdateResponse(BaseModel):
    campaignTrackId: str
    newStatus: CampaignTrackStatus


class CampaignPolicyUpsertRequest(BaseModel):
    tenant_code: Optional[str] = Field(None, description="If omitted, treated as global policy")
    version: int = Field(1, ge=1)
    is_active: bool = True
    rolling_window_days: Optional[int] = Field(None, ge=1)
    rules_json: Optional[Any] = None
    product_windows_json: Optional[Dict[str, Any]] = None
    reward_amounts_json: Optional[Dict[str, Any]] = None
    product_rules_json: Optional[Dict[str, Any]] = None