from __future__ import annotations

from services.fulfilment.base import (
    FulfilmentProvider,
    FulfilmentRequest,
    FulfilmentResult,
    FulfilmentStatus,
)


class CashProvider(FulfilmentProvider):
    provider_key = "CASH_PROVIDER"

    async def fulfil(self, request: FulfilmentRequest) -> FulfilmentResult:
        return FulfilmentResult(
            status=FulfilmentStatus.PENDING,
            provider_reference=f"CASH-STUB-{request.reward_id}",
            message="Cash fulfilment stubbed pending real disbursement integration.",
            metadata={"provider_key": self.provider_key},
        )