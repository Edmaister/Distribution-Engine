from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CreateFxRateRequest(BaseModel):
    tenant_code: str
    base_currency: str = Field(min_length=3, max_length=3)
    quote_currency: str = Field(min_length=3, max_length=3)
    rate: Decimal = Field(gt=0)
    rate_date: date
    source_system: str
    source_reference: str | None = None
    metadata: dict[str, Any] | None = None


class FxRateResponse(BaseModel):
    fx_rate_id: UUID
    tenant_code: str
    base_currency: str
    quote_currency: str
    rate: Decimal
    rate_date: date
    source_system: str
    source_reference: str | None = None
    rate_status: str
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class QuoteConversionRequest(BaseModel):
    tenant_code: str
    source_currency: str = Field(min_length=3, max_length=3)
    target_currency: str = Field(min_length=3, max_length=3)
    source_amount: Decimal = Field(gt=0)
    as_of_date: date | None = None
    persist_quote: bool = True
    metadata: dict[str, Any] | None = None


class ConversionQuoteResponse(BaseModel):
    quote_id: UUID | None = None
    tenant_code: str
    source_currency: str
    target_currency: str
    source_amount: Decimal
    target_amount: Decimal
    fx_rate_id: UUID
    rate: Decimal
    rate_date: date
    conversion_direction: str
    metadata: dict[str, Any]
    created_at: datetime | None = None


class CreateCrossBorderSettlementRequest(BaseModel):
    tenant_code: str
    source_currency: str = Field(min_length=3, max_length=3)
    target_currency: str = Field(min_length=3, max_length=3)
    source_amount: Decimal = Field(gt=0)
    settlement_id: str | None = None
    sponsor_code: str | None = None
    distributor_id: str | None = None
    as_of_date: date | None = None
    corridor: str | None = None
    provider_key: str | None = None
    provider_reference: str | None = None
    compliance_status: str = "PENDING"
    metadata: dict[str, Any] | None = None


class CrossBorderSettlementResponse(BaseModel):
    cross_border_settlement_id: UUID
    tenant_code: str
    settlement_id: UUID | None = None
    sponsor_code: str | None = None
    distributor_id: UUID | None = None
    source_currency: str
    target_currency: str
    source_amount: Decimal
    target_amount: Decimal
    fx_rate_id: UUID
    rate: Decimal
    rate_date: date
    settlement_status: str
    corridor: str | None = None
    provider_key: str | None = None
    provider_reference: str | None = None
    compliance_status: str
    failure_reason: str | None = None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    settled_at: datetime | None = None
    failed_at: datetime | None = None
