from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProgressEventType(str, Enum):
    UCN_CAPTURED = "UCN_CAPTURED"
    ACCOUNT_OPENED = "ACCOUNT_OPENED"
    ACCOUNT_ACTIVATED = "ACCOUNT_ACTIVATED"
    FUNDED = "FUNDED"
    DEBIT_ORDER_SWITCHED = "DEBIT_ORDER_SWITCHED"
    SALARY_SWITCHED = "SALARY_SWITCHED"
    FIRST_TRANSACTION_COMPLETED = "FIRST_TRANSACTION_COMPLETED"


class ProgressPostRequest(BaseModel):
    referralTrackId: str = Field(..., min_length=1)
    product: Optional[str] = None
    subProduct: Optional[str] = None
    eventType: str = Field(..., min_length=1)
    journeyCode: Optional[str] = None
    journeyVersion: Optional[str] = None
    refereeUCN: Optional[str] = None
    accountNumber: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    sourceSystem: Optional[str] = Field(None, alias="sourceSystem")
    sourceEventId: Optional[str] = Field(None, alias="sourceEventId")


class ProgressPostResponse(BaseModel):
    status: str
    referralTrackId: str
    product: Optional[str] = None
    subProduct: Optional[str] = None
    eventType: str
    journeyCode: Optional[str] = None
    journeyVersion: Optional[str] = None
    deduped: bool
    message: str
    sourceSystem: Optional[str] = None
    sourceEventId: Optional[str] = None
    occurredAt: str
    dedupeKey: Optional[str] = None
    
class ReferralProgressItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    referral_track_id: str = Field(..., alias="referralTrackId")
    alias: Optional[str] = Field(None, alias="alias")
    product: Optional[str] = None
    sub_product: Optional[str] = Field(None, alias="subProduct")
    progress_percent: int = Field(..., alias="progressPercent")
    current_milestone: str = Field(..., alias="currentMilestone")
    next_milestone: Optional[str] = Field(None, alias="nextMilestone")
    status: Optional[str] = None
    last_updated_at: Optional[datetime] = Field(None, alias="lastUpdatedAt")


class ReferrerReferralProgressResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    referrer_ucn: str = Field(..., alias="referrerUcn")
    total_referrals: int = Field(..., alias="totalReferrals")
    completed_referrals_count: int = Field(..., alias="completedReferralsCount")
    in_progress_referrals_count: int = Field(..., alias="inProgressReferralsCount")
    has_active_referrals: bool = Field(..., alias="hasActiveReferrals")
    items: List[ReferralProgressItem]
