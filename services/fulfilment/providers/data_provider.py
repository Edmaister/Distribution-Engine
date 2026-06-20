from __future__ import annotations

from services.fulfilment.base import (
    FulfilmentProvider,
    FulfilmentRequest,
    FulfilmentResult,
    FulfilmentStatus,
)


class DataProvider(FulfilmentProvider):
    provider_key = "DATA_PROVIDER"

    async def fulfil(self, request: FulfilmentRequest) -> FulfilmentResult:
        return FulfilmentResult(
            status=FulfilmentStatus.PENDING,
            provider_reference=f"DATA-STUB-{request.reward_id}",
            message="Data fulfilment stubbed pending telco/provider integration.",
            metadata={"provider_key": self.provider_key},
        )