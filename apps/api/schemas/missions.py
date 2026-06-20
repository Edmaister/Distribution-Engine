from __future__ import annotations

import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MissionComplianceMetadata(BaseModel):
    isAdvice: bool = False
    isCreditRelated: bool = False
    requiresDisclaimer: bool = True
    disclaimerCodes: List[str] = Field(default_factory=list)
    regulatoryTags: List[str] = Field(default_factory=list)
    blocked: bool = False
    blockedReason: Optional[str] = None


class MissionItemResponse(BaseModel):
    missionCode: str
    category: str = "CORE"
    scope: str = "REFERRAL"

    displayOrder: int = Field(default=999, ge=0)

    beneficiaryType: str
    beneficiaryRef: str

    title: str
    body: str

    progressCount: int = Field(..., ge=0)
    goalCount: int = Field(..., ge=1)
    progressLabel: str

    status: str = "IN_PROGRESS"
    isComplete: bool = False
    completedAt: Optional[datetime.datetime] = None

    bonusRewardAmount: int = Field(..., ge=0)
    rewardLabel: str
    currency: str = "ZAR"

    associatedReferralTrackIds: List[str] = Field(default_factory=list)

    disclosures: List[str] = Field(default_factory=list)
    compliance: MissionComplianceMetadata


class MissionListResponse(BaseModel):
    referralTrackId: str
    generatedAt: datetime.datetime
    count: int
    items: List[MissionItemResponse]


class GroupedMissionListResponse(BaseModel):
    generatedAt: datetime.datetime
    totalCount: int

    core: List[MissionItemResponse] = Field(default_factory=list)
    boost: List[MissionItemResponse] = Field(default_factory=list)
    milestone: List[MissionItemResponse] = Field(default_factory=list)


class ReferrerMissionListResponse(BaseModel):
    referrerUCN: str
    generatedAt: datetime.datetime
    totalCount: int

    core: List[MissionItemResponse] = Field(default_factory=list)
    boost: List[MissionItemResponse] = Field(default_factory=list)
    milestone: List[MissionItemResponse] = Field(default_factory=list)