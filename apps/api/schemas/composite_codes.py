from __future__ import annotations

from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class CompositeCodeValidateRequest(BaseModel):
    composite_code: str = Field(
        ...,
        min_length=6,
        description="Composite code string used for interim campaign and referral validation.",
    )
    tenant_code: Optional[str] = Field(
        None,
        description="Optional tenant/brand code. If omitted, derived from composite_code where possible.",
    )
    channel: Optional[Literal["APP", "WEB", "WHATSAPP", "OTHER"]] = Field(
        None,
        description="Originating channel for telemetry/audit context.",
    )
    attributes: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata passed through for validation context.",
    )


class CompositeCampaignResult(BaseModel):
    valid: bool
    campaignCode: Optional[str] = None
    campaignTrackId: Optional[str] = None
    message: Optional[str] = None
    errorCode: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class CompositeReferralResult(BaseModel):
    valid: bool
    referralCode: Optional[str] = None
    referralTrackId: Optional[str] = None
    message: Optional[str] = None
    errorCode: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class CompositeCodeValidateResponse(BaseModel):
    ok: bool
    tenant_code: str
    composite_code: Optional[str] = None
    campaign: CompositeCampaignResult
    referral: CompositeReferralResult