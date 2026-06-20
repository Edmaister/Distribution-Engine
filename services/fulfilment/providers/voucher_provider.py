from __future__ import annotations

from services.fulfilment.base import (
    FulfilmentProvider,
    FulfilmentRequest,
    FulfilmentResult,
    FulfilmentStatus,
)


class VoucherProvider(FulfilmentProvider):
    provider_key = "VOUCHER_PROVIDER"

    async def fulfil(self, request: FulfilmentRequest) -> FulfilmentResult:
        return FulfilmentResult(
            status=FulfilmentStatus.PENDING,
            provider_reference=f"VOUCHER-STUB-{request.reward_id}",
            message="Voucher fulfilment stubbed pending voucher provider integration.",
            metadata={"provider_key": self.provider_key},
        )