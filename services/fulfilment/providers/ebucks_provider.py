from __future__ import annotations

from services.fulfilment.base import (
    FulfilmentProvider,
    FulfilmentRequest,
    FulfilmentResult,
    FulfilmentStatus,
)


class EBucksProvider(FulfilmentProvider):
    provider_key = "EBUCKS_PROVIDER"

    async def fulfil(self, request: FulfilmentRequest) -> FulfilmentResult:
        return FulfilmentResult(
            status=FulfilmentStatus.PENDING,
            provider_reference=f"EBUCKS-STUB-{request.reward_id}",
            message="eBucks fulfilment instruction stubbed pending tenant API integration.",
            metadata={"provider_key": self.provider_key},
        )