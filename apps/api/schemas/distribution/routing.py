from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class MatchOpportunityRequest(BaseModel):
    minimum_score: Decimal = Field(default=1, ge=0)
    limit: int = Field(default=25, ge=1, le=500)


class RouteOpportunityRequest(BaseModel):
    minimum_score: Decimal = Field(default=1, ge=0)
    limit: int = Field(default=25, ge=1, le=500)
    expires_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class OpportunityMatchResponse(BaseModel):
    opportunity_id: UUID
    distributor_id: UUID
    distributor_code: str
    distributor_name: str
    distributor_type: str
    route_score: Decimal
    route_reasons: list[str]


class OpportunityMatchListResponse(BaseModel):
    opportunity_id: UUID
    tenant_code: str
    count: int
    items: list[OpportunityMatchResponse]


class OfferRouteResponse(BaseModel):
    route_id: UUID
    tenant_code: str
    opportunity_id: UUID
    distributor_id: UUID
    route_status: str
    route_score: Decimal
    route_reasons: list[str]
    routed_at: datetime
    expires_at: datetime | None = None
    accepted_at: datetime | None = None
    declined_at: datetime | None = None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class OfferRouteListResponse(BaseModel):
    tenant_code: str
    count: int
    items: list[OfferRouteResponse]


class OpportunityRouteListResponse(BaseModel):
    opportunity_id: UUID
    tenant_code: str
    count: int
    items: list[OfferRouteResponse]
