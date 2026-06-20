from __future__ import annotations

import datetime

from services.journey_definitions import get_journey_definition
from services.journey_orchestrator import apply_progress_event_to_instance
from services.progress_definitions import get_progress_definition
from services.vertical_catalog_service import get_vertical_config, list_vertical_configs
from services.vertical_readiness_service import get_vertical_readiness


def test_insurance_policy_journey_is_configured():
    journey = get_journey_definition("INSURANCE_POLICY", "v1")
    progress = get_progress_definition("INSURANCE_POLICY", "v1")

    assert journey.core_sequence == [
        "VALIDATED",
        "QUOTE_REQUESTED",
        "QUOTE_ACCEPTED",
        "POLICY_ISSUED",
        "FIRST_PREMIUM_PAID",
    ]
    assert journey.completion_events == {"FIRST_PREMIUM_PAID"}
    assert progress.milestones["POLICY_ISSUED"].next_milestone == "FIRST_PREMIUM_PAID"


def test_insurance_policy_progresses_to_completion_without_banking_events():
    journey = get_journey_definition("INSURANCE_POLICY", "v1")
    instance = {
        "status": "VALIDATED",
        "ucn_captured_at": None,
        "account_opened_at": None,
        "account_activated_at": None,
        "funded_at": None,
        "completed_at": None,
        "is_complete": False,
    }

    for event in [
        "QUOTE_REQUESTED",
        "QUOTE_ACCEPTED",
        "POLICY_ISSUED",
        "FIRST_PREMIUM_PAID",
    ]:
        result = apply_progress_event_to_instance(
            instance=instance,
            incoming_event=event,
            occurred_at=datetime.datetime.now(datetime.timezone.utc),
            journey_definition=journey,
            journey_code="INSURANCE_POLICY",
            journey_version="v1",
        )
        assert result == "valid"

    assert instance["status"] == "FIRST_PREMIUM_PAID"
    assert instance["is_complete"] is True
    assert instance["progress_percent"] == 100
    assert instance["display_status"] == "Policy activated"


def test_vertical_readiness_reports_two_configured_verticals():
    readiness = get_vertical_readiness()

    assert readiness["agnostic_ready"] is True
    assert readiness["configuration_source"] == "vertical_catalog"
    assert readiness["configured_count"] >= 3
    assert {vertical.vertical_code for vertical in list_vertical_configs()} >= {
        "BANKING",
        "INSURANCE",
        "RETAIL",
    }
    insurance = next(
        item for item in readiness["items"] if item["vertical_code"] == "INSURANCE"
    )
    assert insurance["status"] == "CONFIGURED"
    assert insurance["configuration_source"] == "vertical_catalog"
    assert insurance["missing_components"] == []
    assert insurance["commercial_status"] == "CONFIGURED"
    assert insurance["identifier_validation_configured"] is True
    assert insurance["fulfilment_route_configured"] is True
    assert insurance["regulatory_overlay_configured"] is True
    assert insurance["journey_code"] == "INSURANCE_POLICY"
    assert insurance["reward_policy"] == "INSURANCE / FUNERAL_PLAN"
    assert insurance["leaderboard_code"] == "GLOBAL_INSURANCE"
    assert (
        insurance["fulfilment_route"]["provider_key"] == "TENANT_INSTRUCTION_PROVIDER"
    )
    assert insurance["regulatory_policy_code"] == "DEFAULT_RECOMMENDATION_POLICY"
    assert "INSURANCE_PRODUCT_INFO" in insurance["regulatory_disclosure_codes"]
    retail = next(
        item for item in readiness["items"] if item["vertical_code"] == "RETAIL"
    )
    assert retail["status"] == "CONFIGURED"
    assert retail["missing_components"] == []
    assert retail["journey_code"] == "RETAIL_LOYALTY"
    assert retail["reward_policy"] == "RETAIL / FIRST_PURCHASE"
    assert retail["leaderboard_code"] == "GLOBAL_RETAIL"
    assert retail["fulfilment_route"]["provider_key"] == "VOUCHER_PROVIDER"
    assert retail["regulatory_policy_code"] == "DEFAULT_RECOMMENDATION_POLICY"
    assert "VOUCHER_TERMS_APPLY" in retail["regulatory_disclosure_codes"]


def test_vertical_catalog_keeps_verticals_as_config_not_defaults():
    banking = get_vertical_config("BANKING")
    insurance = get_vertical_config("INSURANCE")
    retail = get_vertical_config("RETAIL")

    assert banking is not None
    assert insurance is not None
    assert retail is not None
    assert banking.journey_code == "BANKING_TRANSACTIONAL"
    assert insurance.journey_code == "INSURANCE_POLICY"
    assert retail.journey_code == "RETAIL_LOYALTY"
    assert banking.product != insurance.product
    assert retail.product not in {banking.product, insurance.product}
    assert (
        banking.fulfilment_route.provider_key != insurance.fulfilment_route.provider_key
    )
    assert retail.fulfilment_route.provider_key not in {
        banking.fulfilment_route.provider_key,
        insurance.fulfilment_route.provider_key,
    }
    assert insurance.leaderboard_code == "GLOBAL_INSURANCE"
    assert retail.leaderboard_code == "GLOBAL_RETAIL"


def test_retail_loyalty_progresses_to_completion_as_clean_room_vertical():
    journey = get_journey_definition("RETAIL_LOYALTY", "v1")
    progress = get_progress_definition("RETAIL_LOYALTY", "v1")
    instance = {
        "status": "VALIDATED",
        "completed_at": None,
        "is_complete": False,
    }

    assert (
        progress.milestones["ORDER_PLACED"].next_milestone == "FIRST_PURCHASE_COMPLETED"
    )

    for event in ["BASKET_CREATED", "ORDER_PLACED", "FIRST_PURCHASE_COMPLETED"]:
        result = apply_progress_event_to_instance(
            instance=instance,
            incoming_event=event,
            occurred_at=datetime.datetime.now(datetime.timezone.utc),
            journey_definition=journey,
            journey_code="RETAIL_LOYALTY",
            journey_version="v1",
        )
        assert result == "valid"

    assert instance["status"] == "FIRST_PURCHASE_COMPLETED"
    assert instance["is_complete"] is True
    assert instance["progress_percent"] == 100
    assert instance["display_status"] == "First purchase completed"
