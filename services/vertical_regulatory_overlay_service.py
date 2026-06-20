from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegulatoryOverlay:
    journey_code: str
    journey_version: str
    policy_code: str
    disclosure_codes: tuple[str, ...]
    template_codes: tuple[str, ...]
    regulatory_tags: tuple[str, ...]


REGULATORY_OVERLAYS: dict[str, RegulatoryOverlay] = {
    "BANKING_TRANSACTIONAL:v1": RegulatoryOverlay(
        journey_code="BANKING_TRANSACTIONAL",
        journey_version="v1",
        policy_code="DEFAULT_RECOMMENDATION_POLICY",
        disclosure_codes=("GENERAL_INFO_ONLY", "REWARD_CONDITIONAL"),
        template_codes=(
            "SALARY_SWITCH_INFO",
            "DEBIT_ORDER_SWITCH_INFO",
            "FIRST_TRANSACTION_INFO",
            "PROGRESS_INFO",
            "PROGRESS_COMPLETE_INFO",
        ),
        regulatory_tags=("TCF", "FAIS", "MARKET_CONDUCT", "BANKING_CODE"),
    ),
    "INSURANCE_POLICY:v1": RegulatoryOverlay(
        journey_code="INSURANCE_POLICY",
        journey_version="v1",
        policy_code="DEFAULT_RECOMMENDATION_POLICY",
        disclosure_codes=(
            "GENERAL_INFO_ONLY",
            "REWARD_CONDITIONAL",
            "INSURANCE_PRODUCT_INFO",
        ),
        template_codes=(
            "INSURANCE_QUOTE_ACCEPTANCE_INFO",
            "INSURANCE_POLICY_ACTIVATION_INFO",
            "INSURANCE_PROGRESS_INFO",
            "INSURANCE_POLICY_COMPLETE_INFO",
        ),
        regulatory_tags=("TCF", "FAIS", "MARKET_CONDUCT", "INSURANCE_CONDUCT"),
    ),
    "RETAIL_LOYALTY:v1": RegulatoryOverlay(
        journey_code="RETAIL_LOYALTY",
        journey_version="v1",
        policy_code="DEFAULT_RECOMMENDATION_POLICY",
        disclosure_codes=(
            "GENERAL_INFO_ONLY",
            "REWARD_CONDITIONAL",
            "VOUCHER_TERMS_APPLY",
        ),
        template_codes=(
            "RETAIL_BASKET_CREATED_INFO",
            "RETAIL_ORDER_PLACED_INFO",
            "RETAIL_PURCHASE_COMPLETE_INFO",
        ),
        regulatory_tags=("TCF", "MARKET_CONDUCT", "VOUCHER_TERMS"),
    ),
}


def get_regulatory_overlay(
    journey_code: str,
    journey_version: str,
) -> RegulatoryOverlay | None:
    return REGULATORY_OVERLAYS.get(f"{journey_code}:{journey_version}")
