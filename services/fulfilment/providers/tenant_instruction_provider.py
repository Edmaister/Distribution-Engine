from __future__ import annotations

from services.fulfilment.base import (
    FulfilmentProvider,
    FulfilmentRequest,
    FulfilmentResult,
    FulfilmentStatus,
)


class TenantInstructionProvider(FulfilmentProvider):
    provider_key = "TENANT_INSTRUCTION_PROVIDER"

    async def fulfil(self, request: FulfilmentRequest) -> FulfilmentResult:
        return FulfilmentResult(
            status=FulfilmentStatus.PENDING,
            provider_reference=f"TENANT-INSTRUCTION-{request.reward_id}",
            message="Tenant fulfilment instruction created pending tenant execution.",
            metadata={"provider_key": self.provider_key},
        )