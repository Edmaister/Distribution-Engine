from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DashboardCompliance(BaseModel):
    isAdvice: bool = False
    requiresDisclaimer: bool = True
    disclaimerCodes: List[str] = Field(default_factory=list)
    regulatoryTags: List[str] = Field(default_factory=list)
    blocked: bool = False
    blockedReason: Optional[str] = None


class DashboardMissionCompliance(BaseModel):
    isAdvice: bool = False
    isCreditRelated: bool = False
    requiresDisclaimer: bool = True
    disclaimerCodes: List[str] = Field(default_factory=list)
    regulatoryTags: List[str] = Field(default_factory=list)
    blocked: bool = False
    blockedReason: Optional[str] = None


class DashboardBadgeCompliance(BaseModel):
    isAdvice: bool = False
    requiresDisclaimer: bool = False
    regulatoryTags: List[str] = Field(default_factory=list)
    blocked: bool = False
    blockedReason: Optional[str] = None


class ReferrerRewardTotals(BaseModel):
    earned: int
    pending: int
    nextEligibleReward: int
    totalPotential: int


class ReferrerRewardSummary(BaseModel):
    currency: str
    generatedAt: datetime
    totals: ReferrerRewardTotals
    referralsCount: int
    completedReferralsCount: int
    pendingBonusesCount: int
    count: int
    disclosures: List[str] = Field(default_factory=list)
    compliance: DashboardCompliance


class ReferrerDashboardSummary(BaseModel):
    referrerUcn: str
    currency: str = "ZAR"
    generatedAt: datetime
    totalEarned: int
    totalPending: int
    totalPotential: int
    nextEligibleReward: int
    referralsCount: int
    completedReferralsCount: int
    pendingBonusesCount: int
    badgeCount: int
    leaderboardRank: Optional[int] = None
    leaderboardTier: Optional[str] = None
    totalScore: Optional[int] = None
    pointsToNextRank: Optional[int] = None


class DashboardReferralCard(BaseModel):
    referralTrackId: str
    product: Optional[str] = None
    subProduct: Optional[str] = None
    progressPercent: int = 0
    progressBand: Optional[str] = None
    displayStatus: Optional[str] = None
    nextMilestone: Optional[str] = None
    isComplete: bool = False
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class DashboardMissionItem(BaseModel):
    missionCode: str
    category: str
    scope: str
    displayOrder: int
    beneficiaryType: str
    beneficiaryRef: str
    title: str
    body: str
    progressCount: int
    goalCount: int
    progressLabel: str
    status: str
    isComplete: bool
    completedAt: Optional[datetime] = None
    bonusRewardAmount: int
    rewardLabel: str
    currency: str
    associatedReferralTrackIds: List[str] = Field(default_factory=list)
    disclosures: List[str] = Field(default_factory=list)
    compliance: DashboardMissionCompliance


class DashboardMissionGroups(BaseModel):
    core: List[DashboardMissionItem] = Field(default_factory=list)
    boost: List[DashboardMissionItem] = Field(default_factory=list)
    milestone: List[DashboardMissionItem] = Field(default_factory=list)


class DashboardBadgeItem(BaseModel):
    badgeCode: str
    badgeName: str
    badgeDescription: str
    badgeCategory: str
    iconName: Optional[str] = None
    awardedAt: datetime
    awardReason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    compliance: DashboardBadgeCompliance


class DashboardLeaderboard(BaseModel):
    leaderboardCode: Optional[str] = None
    displayName: Optional[str] = None
    totalScore: Optional[int] = None
    referralScore: Optional[int] = None
    milestoneScore: Optional[int] = None
    bonusScore: Optional[int] = None
    referralsCount: Optional[int] = None
    completedReferralsCount: Optional[int] = None
    lastEventAt: Optional[datetime] = None
    rankPosition: Optional[int] = None
    rankTier: Optional[str] = None
    nextRankPosition: Optional[int] = None
    nextRankScore: Optional[int] = None
    pointsToNextRank: Optional[int] = None


class ReferrerDashboardResponse(BaseModel):
    summary: ReferrerDashboardSummary
    rewards: ReferrerRewardSummary
    missions: DashboardMissionGroups
    badges: List[DashboardBadgeItem] = Field(default_factory=list)
    leaderboard: DashboardLeaderboard
    referrals: List[DashboardReferralCard] = Field(default_factory=list)


class DashboardProgress(BaseModel):
    status: str
    isComplete: bool
    progressPercent: int
    progressBand: Optional[str] = None
    displayStatus: Optional[str] = None
    nextMilestone: Optional[str] = None


class ReferralRewardPartySummary(BaseModel):
    earned: int
    pending: int
    nextEligibleReward: int
    totalPotential: int


class ReferralRewardItem(BaseModel):
    beneficiaryType: str
    rewardType: str
    rewardSource: str
    status: str
    amount: int
    description: str
    missionCode: Optional[str] = None


class ReferralRewardSummary(BaseModel):
    referralTrackId: str
    currency: str
    generatedAt: datetime
    referrer: ReferralRewardPartySummary
    referee: ReferralRewardPartySummary
    count: int
    items: List[ReferralRewardItem] = Field(default_factory=list)
    disclosures: List[str] = Field(default_factory=list)
    compliance: DashboardCompliance


class ReferralDashboardResponse(BaseModel):
    referralTrackId: str
    referrerUcn: str
    progress: DashboardProgress
    rewards: ReferralRewardSummary
    missions: DashboardMissionGroups