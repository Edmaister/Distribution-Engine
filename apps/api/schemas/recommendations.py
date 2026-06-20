from __future__ import annotations

import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RewardPreview(BaseModel):
    amount: int = Field(..., ge=0)
    currency: str = "ZAR"
    isConditional: bool = True
    conditionSummary: str


class ComplianceMetadata(BaseModel):
    isAdvice: bool = False
    isCreditRelated: bool = False
    requiresDisclaimer: bool = True
    disclaimerCodes: List[str] = []
    regulatoryTags: List[str] = []
    pressureScore: int = Field(default=0, ge=0)
    fairnessScore: int = Field(default=100, ge=0, le=100)
    transparencyScore: int = Field(default=100, ge=0, le=100)
    blocked: bool = False
    blockedReason: Optional[str] = None


class RecommendationItemResponse(BaseModel):
    recommendationId: str
    category: str
    title: str
    body: str
    ctaLabel: str
    ctaAction: str
    priority: int = Field(..., ge=1)
    rewardPreview: Optional[RewardPreview] = None
    disclosures: List[str] = []
    compliance: ComplianceMetadata
    templateCode: str
    templateVersion: str
    policyVersion: str


class RecommendationListResponse(BaseModel):
    referralTrackId: str
    generatedAt: datetime.datetime
    count: int
    items: List[RecommendationItemResponse]