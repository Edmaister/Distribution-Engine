from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ProducerSupplyLaunchRequest(BaseModel):
    campaign_name: str
    segment: str
    opportunity_title: str
    campaign_code: str | None = None
    opportunity_code: str | None = None
    description: str | None = None
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
    publish_now: bool = False
    metadata: dict[str, Any] | None = None


class ProducerSupplyConversionResponse(BaseModel):
    referral_track_id: UUID
    tenant_code: str
    producer_code: str
    campaign_code: str | None = None
    opportunity_id: UUID
    opportunity_code: str
    opportunity_title: str
    route_id: UUID
    distributor_id: UUID
    distributor_code: str
    distributor_name: str
    distributor_type: str
    product: str | None = None
    sub_product: str | None = None
    status: str
    display_status: str | None = None
    progress_percent: int | None = None
    progress_band: str | None = None
    next_milestone: str | None = None
    is_complete: bool
    completed_at: datetime | None = None
    validated_at: datetime | None = None
    ucn_captured_at: datetime | None = None
    account_opened_at: datetime | None = None
    account_activated_at: datetime | None = None
    funded_at: datetime | None = None
    debit_order_switched_at: datetime | None = None
    salary_switched_at: datetime | None = None
    first_transaction_completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ProducerSupplyConversionListResponse(BaseModel):
    tenant_code: str
    producer_code: str
    campaign_code: str | None = None
    opportunity_id: str | None = None
    count: int
    completed_count: int
    completion_rate: Decimal = Decimal("0")
    items: list[ProducerSupplyConversionResponse]
