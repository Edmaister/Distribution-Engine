from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from apps.api.schemas.distribution.distributors import CreateDistributorRequest
from apps.api.schemas.distribution.wallets import (
    DistributorWalletLedgerEntry,
    DistributorWalletResponse,
)


class DistributorPortalProfileResponse(CreateDistributorRequest):
    distributor_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    status_changed_at: datetime


class DistributorPortalOfferResponse(BaseModel):
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
    sponsor_code: str
    campaign_code: str | None = None
    opportunity_code: str
    title: str
    description: str | None = None
    product_code: str | None = None
    product_name: str | None = None
    estimated_reward_amount: Decimal | None = None
    estimated_commission_amount: Decimal | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    referral_link_count: int = 0
    latest_referral_track_id: UUID | None = None
    has_referral_link: bool = False


class DistributorPortalRouteResponse(BaseModel):
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


class LinkDistributorPortalReferralRequest(BaseModel):
    referral_track_id: str
    metadata: dict[str, Any] | None = None


class DistributorPortalRouteReferralLinkResponse(BaseModel):
    route_id: UUID
    referral_track_id: UUID
    tenant_code: str
    distributor_id: UUID
    distributor_code: str
    opportunity_id: UUID
    link_status: str
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class DistributorPortalOfferListResponse(BaseModel):
    tenant_code: str
    distributor_id: UUID
    distributor_code: str
    count: int
    items: list[DistributorPortalOfferResponse]


class DistributorPortalWalletListResponse(BaseModel):
    tenant_code: str
    distributor_id: UUID
    distributor_code: str
    count: int
    items: list[DistributorWalletResponse]


class DistributorPortalWalletLedgerResponse(BaseModel):
    tenant_code: str
    distributor_id: UUID
    distributor_code: str
    wallet_id: UUID
    count: int
    items: list[DistributorWalletLedgerEntry]


class DistributorPortalPerformanceResponse(BaseModel):
    tenant_code: str
    distributor_id: UUID
    distributor_code: str
    routed_count: int
    accepted_count: int
    declined_count: int
    acceptance_rate: Decimal
    conversion_count: int = 0
    completed_conversion_count: int = 0
    conversion_completion_rate: Decimal = Decimal("0")
    commission_event_count: int
    total_commission_amount: Decimal
    wallet_current_balance: Decimal
    wallet_available_balance: Decimal
    wallet_held_balance: Decimal
    wallet_paid_out_balance: Decimal
    wallet_reversed_balance: Decimal


class DistributorPortalConversionResponse(BaseModel):
    referral_track_id: UUID
    tenant_code: str
    distributor_code: str
    route_id: UUID | None = None
    opportunity_id: UUID | None = None
    opportunity_code: str | None = None
    opportunity_title: str | None = None
    sponsor_code: str | None = None
    campaign_code: str | None = None
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


class DistributorPortalConversionListResponse(BaseModel):
    tenant_code: str
    distributor_id: UUID
    distributor_code: str
    count: int
    completed_count: int
    completion_rate: Decimal = Decimal("0")
    attributed_count: int = 0
    unlinked_count: int = 0
    attribution_rate: Decimal = Decimal("0")
    items: list[DistributorPortalConversionResponse]
