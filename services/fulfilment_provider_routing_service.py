from __future__ import annotations

from dataclasses import dataclass

from services.fulfilment_circuit_breaker_service import (
    can_execute_provider,
)


@dataclass(frozen=True)
class ProviderRoutingResult:
    requested_provider_key: str
    selected_provider_key: str
    reason: str
    fallback_used: bool = False


PROVIDER_FALLBACKS = {
    "CASH_PROVIDER": "CASH_PROVIDER_SECONDARY",
    "VOUCHER_PROVIDER": "VOUCHER_PROVIDER_SECONDARY",
    "EBUCKS_PROVIDER": "EBUCKS_PROVIDER_SECONDARY",
}


def get_fallback_provider(
    provider_key: str,
) -> str | None:
    return PROVIDER_FALLBACKS.get(
        provider_key.upper(),
    )


def resolve_provider(
    provider_key: str,
) -> ProviderRoutingResult:
    requested_provider = provider_key.upper()

    if can_execute_provider(
        provider_key=requested_provider,
    ):
        return ProviderRoutingResult(
            requested_provider_key=requested_provider,
            selected_provider_key=requested_provider,
            reason="PRIMARY_AVAILABLE",
            fallback_used=False,
        )

    fallback_provider = get_fallback_provider(
        requested_provider,
    )

    if fallback_provider and can_execute_provider(
        provider_key=fallback_provider,
    ):
        return ProviderRoutingResult(
            requested_provider_key=requested_provider,
            selected_provider_key=fallback_provider,
            reason="PRIMARY_CIRCUIT_OPEN_FALLBACK_AVAILABLE",
            fallback_used=True,
        )

    return ProviderRoutingResult(
        requested_provider_key=requested_provider,
        selected_provider_key=requested_provider,
        reason="NO_AVAILABLE_PROVIDER",
        fallback_used=False,
    )