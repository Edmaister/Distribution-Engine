from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class SponsorWalletTopupRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    correlation_id: str | None = None
    metadata: dict[str, Any] | None = None