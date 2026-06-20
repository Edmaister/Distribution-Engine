from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class SponsorWalletCreate(BaseModel):
    tenant_code: str = Field(..., min_length=1)
    sponsor_code: str = Field(..., min_length=1)
    sponsor_name: str = Field(..., min_length=1)
    currency: str = Field(default="ZAR", min_length=3, max_length=3)


class SponsorWalletResponse(BaseModel):
    wallet_id: UUID
    tenant_code: str
    sponsor_code: str
    sponsor_name: str
    currency: str

    current_balance: Decimal
    reserved_balance: Decimal
    available_balance: Decimal

    status: str

    created_at: datetime
    updated_at: datetime