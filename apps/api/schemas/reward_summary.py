from __future__ import annotations

import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RewardSummaryComplianceMetadata(BaseModel):
    isAdvice: bool = False
    requiresDisclaimer: bool = True
    disclaimerCodes: List[str] = []
    regulatoryTags: List[str] = []


class RewardSummaryTotals(BaseModel):
    earned: int = Field(..., ge=0)
    pending: int = Field(..., ge=0)
    nextEligibleReward: int = Field(..., ge=0)
    totalPotential: int = Field(..., ge=0)


class RewardSummaryItem(BaseModel):
    beneficiaryType: str
    rewardType: str
    rewardSource: str
    status: str
    amount: int = Field(..., ge=0)
    description: str
    missionCode: Optional[str] = None


class RewardSummaryResponse(BaseModel):
    referralTrackId: str
    currency: str = "ZAR"
    generatedAt: datetime.datetime
    referrer: RewardSummaryTotals
    referee: RewardSummaryTotals
    count: int
    items: List[RewardSummaryItem]
    disclosures: List[str] = []
    compliance: RewardSummaryComplianceMetadata

class ReferrerRewardSummaryResponse(BaseModel):
    referrerUcn: str
    currency: str = "ZAR"
    generatedAt: datetime.datetime
    totals: RewardSummaryTotals
    referralsCount: int = Field(..., ge=0)
    completedReferralsCount: int = Field(..., ge=0)
    pendingBonusesCount: int = Field(..., ge=0)
    count: int = Field(..., ge=0)
    disclosures: List[str] = Field(default_factory=list)
    compliance: RewardSummaryComplianceMetadata