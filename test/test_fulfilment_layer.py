from __future__ import annotations

import pytest

from services.fulfilment.base import (
    FulfilmentProvider,
    FulfilmentRequest,
    FulfilmentResult,
    FulfilmentStatus,
)
from services.fulfilment.factory import (
    FulfilmentProviderFactory,
    get_fulfilment_provider,
)
from services.fulfilment.providers.cash_provider import CashProvider
from services.fulfilment.providers.data_provider import DataProvider
from services.fulfilment.providers.ebucks_provider import EBucksProvider
from services.fulfilment.providers.tenant_instruction_provider import (
    TenantInstructionProvider,
)
from services.fulfilment.providers.voucher_provider import VoucherProvider


def _request(reward_type: str = "CASH") -> FulfilmentRequest:
    return FulfilmentRequest(
        tenant_code="FNB",
        reward_id="reward-123",
        reward_type=reward_type,
        reward_value=100.0,
        recipient_ucn="123456789",
        currency="ZAR",
        journey_code="MAIN_BANK_SWITCH",
        milestone_code="ACCOUNT_OPENED",
        product_code="DDA13",
        provider_key="CASH_PROVIDER",
        execution_model="PLATFORM_EXECUTES",
        funding_model="PRE_FUNDED_WALLET",
        settlement_model="REAL_TIME",
        metadata={"correlation_id": "corr-123"},
    )


def test_fulfilment_request_defaults():
    request = FulfilmentRequest(
        tenant_code="FNB",
        reward_id="reward-1",
        reward_type="CASH",
        reward_value=50.0,
    )

    assert request.recipient_ucn is None
    assert request.currency is None
    assert request.journey_code is None
    assert request.milestone_code is None
    assert request.product_code is None
    assert request.provider_key is None
    assert request.execution_model is None
    assert request.funding_model is None
    assert request.settlement_model is None
    assert request.metadata == {}


def test_fulfilment_result_defaults():
    result = FulfilmentResult(status=FulfilmentStatus.SUCCESS)

    assert result.status == FulfilmentStatus.SUCCESS
    assert result.provider_reference is None
    assert result.message is None
    assert result.metadata == {}


def test_base_provider_cannot_be_instantiated():
    with pytest.raises(TypeError):
        FulfilmentProvider()


def test_factory_returns_cash_provider():
    provider = FulfilmentProviderFactory().get("CASH_PROVIDER")

    assert isinstance(provider, CashProvider)
    assert provider.provider_key == "CASH_PROVIDER"


def test_factory_returns_ebucks_provider():
    provider = FulfilmentProviderFactory().get("EBUCKS_PROVIDER")

    assert isinstance(provider, EBucksProvider)
    assert provider.provider_key == "EBUCKS_PROVIDER"


def test_factory_returns_data_provider():
    provider = FulfilmentProviderFactory().get("DATA_PROVIDER")

    assert isinstance(provider, DataProvider)
    assert provider.provider_key == "DATA_PROVIDER"


def test_factory_returns_voucher_provider():
    provider = FulfilmentProviderFactory().get("VOUCHER_PROVIDER")

    assert isinstance(provider, VoucherProvider)
    assert provider.provider_key == "VOUCHER_PROVIDER"


def test_factory_returns_tenant_instruction_provider():
    provider = FulfilmentProviderFactory().get("TENANT_INSTRUCTION_PROVIDER")

    assert isinstance(provider, TenantInstructionProvider)
    assert provider.provider_key == "TENANT_INSTRUCTION_PROVIDER"


def test_factory_unknown_provider_raises_value_error():
    with pytest.raises(ValueError, match="No fulfilment provider registered"):
        FulfilmentProviderFactory().get("UNKNOWN_PROVIDER")


def test_default_factory_helper_returns_provider():
    provider = get_fulfilment_provider("CASH_PROVIDER")

    assert isinstance(provider, CashProvider)

from services.fulfilment.base import (
    FulfilmentProvider,
    FulfilmentRequest,
)


class DummyProvider(FulfilmentProvider):
    provider_key = "DUMMY"

    async def fulfil(self, request):
        return await super().fulfil(request)


@pytest.mark.asyncio
async def test_base_provider_not_implemented():

    provider = DummyProvider()

    request = FulfilmentRequest(
        tenant_code="FNB",
        reward_id="1",
        reward_type="CASH",
        reward_value=100,
    )

    with pytest.raises(NotImplementedError):
        await provider.fulfil(request)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("provider", "reward_type", "expected_reference_prefix", "expected_message"),
    [
        (
            CashProvider(),
            "CASH",
            "CASH-STUB-reward-123",
            "Cash fulfilment stubbed pending real disbursement integration.",
        ),
        (
            EBucksProvider(),
            "EBUCKS",
            "EBUCKS-STUB-reward-123",
            "eBucks fulfilment instruction stubbed pending tenant API integration.",
        ),
        (
            DataProvider(),
            "DATA",
            "DATA-STUB-reward-123",
            "Data fulfilment stubbed pending telco/provider integration.",
        ),
        (
            VoucherProvider(),
            "VOUCHER",
            "VOUCHER-STUB-reward-123",
            "Voucher fulfilment stubbed pending voucher provider integration.",
        ),
        (
            TenantInstructionProvider(),
            "CASH",
            "TENANT-INSTRUCTION-reward-123",
            "Tenant fulfilment instruction created pending tenant execution.",
        ),
    ],
)
async def test_stub_providers_return_pending_result(
    provider,
    reward_type,
    expected_reference_prefix,
    expected_message,
):
    request = _request(reward_type=reward_type)

    result = await provider.fulfil(request)

    assert result.status == FulfilmentStatus.PENDING
    assert result.provider_reference == expected_reference_prefix
    assert result.message == expected_message
    assert result.metadata == {"provider_key": provider.provider_key}