from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class SponsorWalletLedgerEntry(BaseModel):
    ledger_id: UUID
    wallet_id: UUID
    tenant_code: str

    transaction_type: str
    amount: Decimal

    balance_before: Decimal
    balance_after: Decimal

    correlation_id: str | None = None
    metadata: dict[str, Any] | None = None

    created_at: datetime