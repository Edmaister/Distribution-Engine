from __future__ import annotations

from services.fulfilment.base import FulfilmentProvider
from services.fulfilment.providers.cash_provider import CashProvider
from services.fulfilment.providers.data_provider import DataProvider
from services.fulfilment.providers.ebucks_provider import EBucksProvider
from services.fulfilment.providers.tenant_instruction_provider import (
    TenantInstructionProvider,
)
from services.fulfilment.providers.voucher_provider import VoucherProvider


class FulfilmentProviderFactory:
    def __init__(self) -> None:
        providers: list[FulfilmentProvider] = [
            CashProvider(),
            EBucksProvider(),
            DataProvider(),
            VoucherProvider(),
            TenantInstructionProvider(),
        ]
        self._providers = {provider.provider_key: provider for provider in providers}

    def get(self, provider_key: str) -> FulfilmentProvider:
        provider = self._providers.get(provider_key)
        if provider is None:
            raise ValueError(f"No fulfilment provider registered for {provider_key}")
        return provider


_default_factory = FulfilmentProviderFactory()


def get_fulfilment_provider(provider_key: str) -> FulfilmentProvider:
    return _default_factory.get(provider_key)