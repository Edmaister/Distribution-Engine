from __future__ import annotations

import datetime
from typing import List, Optional

from pydantic import BaseModel


class LeaderboardEntryResponse(BaseModel):
    leaderboardCode: str
    displayName: str
    totalScore: int
    referralScore: int
    milestoneScore: int
    bonusScore: int
    referralsCount: int
    completedReferralsCount: int
    lastEventAt: Optional[datetime.datetime]
    rankPosition: Optional[int]
    rankedTier: str


class LeaderboardListResponse(BaseModel):
    leaderboardCode: str
    count: int
    totalCount: int
    offset: int
    limit: int
    generatedAt: datetime.datetime
    items: List[LeaderboardEntryResponse]


class MyLeaderboardEntryResponse(BaseModel):
    leaderboardCode: str
    displayName: str
    totalScore: int
    referralScore: int
    milestoneScore: int
    bonusScore: int
    referralsCount: int
    completedReferralsCount: int
    lastEventAt: Optional[datetime.datetime]
    rankPosition: Optional[int]
    rankedTier: str
    nextRankPosition: Optional[int] = None
    nextRankScore: Optional[int] = None
    pointsToNextRank: Optional[int] = None