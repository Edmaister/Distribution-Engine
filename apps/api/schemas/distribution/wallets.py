from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CreateDistributorWalletRequest(BaseModel):
    distributor_id: str
    currency: str = Field(default="ZAR", min_length=3, max_length=3)
    metadata: dict[str, Any] | None = None


class DistributorWalletMovementRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    correlation_id: str | None = None
    metadata: dict[str, Any] | None = None


class DistributorWalletResponse(BaseModel):
    wallet_id: UUID
    distributor_id: UUID
    tenant_code: str
    distributor_code: str
    currency: str
    current_balance: Decimal
    available_balance: Decimal
    held_balance: Decimal
    paid_out_balance: Decimal
    reversed_balance: Decimal
    status: str
    metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class DistributorWalletLedgerEntry(BaseModel):
    ledger_id: UUID
    wallet_id: UUID
    distributor_id: UUID
    tenant_code: str
    transaction_type: str
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    correlation_id: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime
