from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CreateOpportunityRequest(BaseModel):
    tenant_code: str
    sponsor_code: str
    opportunity_code: str
    title: str
    description: str | None = None
    campaign_code: str | None = None
    funding_contract_id: str | None = None
    product_code: str | None = None
    product_name: str | None = None
    target_segments: list[str] | None = None
    target_regions: list[str] | None = None
    target_channels: list[str] | None = None
    distributor_types: list[str] | None = None
    commission_rule_id: str | None = None
    estimated_reward_amount: Decimal | None = Field(default=None, ge=0)
    estimated_commission_amount: Decimal | None = Field(default=None, ge=0)
    total_budget: Decimal | None = Field(default=None, ge=0)
    max_allocations: int | None = Field(default=None, ge=0)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class UpdateOpportunityRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    product_code: str | None = None
    product_name: str | None = None
    target_segments: list[str] | None = None
    target_regions: list[str] | None = None
    target_channels: list[str] | None = None
    distributor_types: list[str] | None = None
    commission_rule_id: str | None = None
    estimated_reward_amount: Decimal | None = Field(default=None, ge=0)
    estimated_commission_amount: Decimal | None = Field(default=None, ge=0)
    total_budget: Decimal | None = Field(default=None, ge=0)
    max_allocations: int | None = Field(default=None, ge=0)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class OpportunityResponse(BaseModel):
    opportunity_id: UUID
    tenant_code: str
    sponsor_code: str
    campaign_code: str | None = None
    funding_contract_id: UUID | None = None
    opportunity_code: str
    title: str
    description: str | None = None
    product_code: str | None = None
    product_name: str | None = None
    opportunity_status: str
    target_segments: list[str]
    target_regions: list[str]
    target_channels: list[str]
    distributor_types: list[str]
    commission_rule_id: UUID | None = None
    estimated_reward_amount: Decimal | None = None
    estimated_commission_amount: Decimal | None = None
    total_budget: Decimal | None = None
    remaining_budget: Decimal | None = None
    max_allocations: int | None = None
    remaining_allocations: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    published_at: datetime | None = None
    closed_at: datetime | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
