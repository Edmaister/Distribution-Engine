from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class MarketplaceOverviewResponse(BaseModel):
    tenant_code: str
    sponsor_code: str | None = None
    campaign_code: str | None = None
    distributors: dict[str, Any]
    opportunities: dict[str, Any]
    routes: dict[str, Any]
    commissions: dict[str, Any]
    conversions: dict[str, Any] = Field(default_factory=dict)
    wallets: dict[str, Any]
    governance: dict[str, Any]


class OpportunityPerformanceResponse(BaseModel):
    opportunity_id: UUID
    tenant_code: str
    sponsor_code: str
    campaign_code: str | None = None
    opportunity_code: str
    title: str
    opportunity_status: str
    total_budget: Decimal | None = None
    remaining_budget: Decimal | None = None
    routed_count: int
    accepted_count: int
    declined_count: int
    average_route_score: Decimal
    conversion_count: int = 0
    completed_conversion_count: int = 0
    conversion_completion_rate: Decimal = Decimal("0")
    dispute_count: int


class DistributorPerformanceResponse(BaseModel):
    distributor_id: UUID
    tenant_code: str
    distributor_code: str
    distributor_name: str
    distributor_type: str
    status: str
    routed_count: int
    accepted_count: int
    declined_count: int
    conversion_count: int = 0
    completed_conversion_count: int = 0
    conversion_completion_rate: Decimal = Decimal("0")
    commission_event_count: int
    total_commission_amount: Decimal
    wallet_current_balance: Decimal
    wallet_available_balance: Decimal
    dispute_count: int
    open_compliance_review_count: int


class AttributionExceptionItem(BaseModel):
    referral_track_id: UUID
    tenant_code: str
    distributor_code: str | None = None
    product: str | None = None
    sub_product: str | None = None
    status: str | None = None
    display_status: str | None = None
    progress_percent: int | None = None
    progress_band: str | None = None
    next_milestone: str | None = None
    is_complete: bool = False
    validated_at: Any | None = None
    ucn_captured_at: Any | None = None
    account_opened_at: Any | None = None
    account_activated_at: Any | None = None
    funded_at: Any | None = None
    debit_order_switched_at: Any | None = None
    salary_switched_at: Any | None = None
    first_transaction_completed_at: Any | None = None
    completed_at: Any | None = None
    created_at: Any | None = None
    updated_at: Any | None = None


class AttributionExceptionListResponse(BaseModel):
    tenant_code: str
    count: int
    completed_count: int = 0
    items: list[AttributionExceptionItem]


class ReportCountItem(BaseModel):
    status: str | None = None
    action_type: str | None = None
    count: int


class GovernanceReportResponse(BaseModel):
    tenant_code: str
    compliance_reviews: list[ReportCountItem]
    disputes: list[ReportCountItem]
    governance_actions: list[ReportCountItem]
