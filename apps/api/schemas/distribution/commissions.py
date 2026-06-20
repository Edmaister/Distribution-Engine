from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from apps.api.schemas.distribution.wallets import DistributorWalletResponse


class CreateCommissionRuleRequest(BaseModel):
    tenant_code: str
    commission_type: str
    sponsor_code: str | None = None
    campaign_code: str | None = None
    distributor_type: str | None = None
    rate: Decimal | None = Field(default=None, ge=0)
    fixed_amount: Decimal | None = Field(default=None, ge=0)
    min_commission: Decimal | None = Field(default=None, ge=0)
    max_commission: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="ZAR", min_length=3, max_length=3)
    priority: int = Field(default=100, ge=0)
    description: str | None = None
    metadata: dict[str, Any] | None = None


class CommissionRuleResponse(BaseModel):
    rule_id: UUID
    tenant_code: str
    sponsor_code: str | None = None
    campaign_code: str | None = None
    distributor_type: str | None = None
    commission_type: str
    rate: Decimal | None = None
    fixed_amount: Decimal | None = None
    min_commission: Decimal | None = None
    max_commission: Decimal | None = None
    currency: str
    rule_status: str
    priority: int
    description: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class CalculateCommissionRequest(BaseModel):
    tenant_code: str
    distributor_id: str
    activity_type: str
    sale_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    sponsor_code: str | None = None
    campaign_code: str | None = None
    source_event_id: str | None = None
    wallet_id: str | None = None
    credit_wallet: bool = False
    correlation_id: str | None = None
    metadata: dict[str, Any] | None = None


class CommissionEventResponse(BaseModel):
    commission_event_id: UUID
    tenant_code: str
    distributor_id: UUID
    distributor_code: str
    wallet_id: UUID | None = None
    rule_id: UUID | None = None
    sponsor_code: str | None = None
    campaign_code: str | None = None
    source_event_id: str | None = None
    activity_type: str
    sale_amount: Decimal
    commission_amount: Decimal
    currency: str
    commission_status: str
    credited_at: datetime | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class CalculateCommissionResponse(BaseModel):
    commission_event: CommissionEventResponse
    rule: CommissionRuleResponse
    wallet: DistributorWalletResponse | None = None
