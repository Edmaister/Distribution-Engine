from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BadgeCompliance(BaseModel):
    isAdvice: bool = False
    requiresDisclaimer: bool = False
    regulatoryTags: List[str] = Field(default_factory=list)
    blocked: bool = False
    blockedReason: Optional[str] = None


class BadgeItem(BaseModel):
    badgeCode: str
    badgeName: str
    badgeDescription: str
    badgeCategory: str
    iconName: Optional[str] = None
    awardedAt: datetime.datetime
    awardReason: Optional[str] = None

    # 🔥 NEW (lightweight but powerful)
    badgeType: Optional[str] = None  # ACTIVATION / MOMENTUM / VALUE
    metadata: Dict[str, Any] = Field(default_factory=dict)

    compliance: BadgeCompliance


class BadgeListResponse(BaseModel):
    count: int
    items: List[BadgeItem] = Field(default_factory=list)