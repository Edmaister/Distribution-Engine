from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FulfilmentRouteConfig:
    reward_type: str
    provider_key: str
    execution_model: str
    settlement_model: str

    def as_dict(self) -> dict[str, str]:
        return {
            "reward_type": self.reward_type,
            "provider_key": self.provider_key,
            "execution_model": self.execution_model,
            "settlement_model": self.settlement_model,
        }


@dataclass(frozen=True)
class VerticalConfig:
    vertical_code: str
    name: str
    product: str
    reward_policy: str
    leaderboard_code: str
    fulfilment_route: FulfilmentRouteConfig
    journey_code: str
    journey_version: str
    identifier_model: str
    regulatory_overlay: str

    @property
    def journey_key(self) -> str:
        return f"{self.journey_code}:{self.journey_version}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "vertical_code": self.vertical_code,
            "name": self.name,
            "product": self.product,
            "reward_policy": self.reward_policy,
            "leaderboard_code": self.leaderboard_code,
            "fulfilment_route": self.fulfilment_route.as_dict(),
            "journey_code": self.journey_code,
            "journey_version": self.journey_version,
            "identifier_model": self.identifier_model,
            "regulatory_overlay": self.regulatory_overlay,
        }


VERTICAL_CATALOG: dict[str, VerticalConfig] = {
    "BANKING": VerticalConfig(
        vertical_code="BANKING",
        name="Banking",
        product="TRANSACTIONAL",
        reward_policy="TRANSACTIONAL / EASY_ACCOUNT",
        leaderboard_code="GLOBAL_TRANSACTIONAL",
        fulfilment_route=FulfilmentRouteConfig(
            reward_type="CASH",
            provider_key="CASH_PROVIDER",
            execution_model="PLATFORM_EXECUTES",
            settlement_model="REAL_TIME",
        ),
        journey_code="BANKING_TRANSACTIONAL",
        journey_version="v1",
        identifier_model="UCN and account signals",
        regulatory_overlay="Banking onboarding and transactional activation",
    ),
    "INSURANCE": VerticalConfig(
        vertical_code="INSURANCE",
        name="Insurance",
        product="INSURANCE",
        reward_policy="INSURANCE / FUNERAL_PLAN",
        leaderboard_code="GLOBAL_INSURANCE",
        fulfilment_route=FulfilmentRouteConfig(
            reward_type="CASH",
            provider_key="TENANT_INSTRUCTION_PROVIDER",
            execution_model="TENANT_EXECUTES",
            settlement_model="BATCH_SETTLEMENT",
        ),
        journey_code="INSURANCE_POLICY",
        journey_version="v1",
        identifier_model="Customer reference and policy lifecycle signals",
        regulatory_overlay="Policy issue and first-premium activation controls",
    ),
    "RETAIL": VerticalConfig(
        vertical_code="RETAIL",
        name="Retail Loyalty",
        product="LOYALTY",
        reward_policy="RETAIL / FIRST_PURCHASE",
        leaderboard_code="GLOBAL_RETAIL",
        fulfilment_route=FulfilmentRouteConfig(
            reward_type="VOUCHER",
            provider_key="VOUCHER_PROVIDER",
            execution_model="PROVIDER_EXECUTES",
            settlement_model="BATCH_SETTLEMENT",
        ),
        journey_code="RETAIL_LOYALTY",
        journey_version="v1",
        identifier_model="Customer reference, basket, and order lifecycle signals",
        regulatory_overlay="Voucher disclosure and purchase-completion controls",
    ),
}


def list_vertical_configs() -> list[VerticalConfig]:
    return list(VERTICAL_CATALOG.values())


def get_vertical_config(vertical_code: str) -> VerticalConfig | None:
    return VERTICAL_CATALOG.get(vertical_code.strip().upper())
