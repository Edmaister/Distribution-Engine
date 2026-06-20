from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class JourneyDefinition:
    journey_code: str
    journey_version: str
    core_sequence: list[str]
    allowed_transitions: dict[Optional[str], set[str]]
    event_to_timestamp_field: dict[str, str]
    completion_events: set[str]
    completion_minimum_milestone: Optional[str] = None


DEFAULT_JOURNEY_CODE = "BANKING_TRANSACTIONAL"
DEFAULT_JOURNEY_VERSION = "v1"


BANKING_TRANSACTIONAL_V1 = JourneyDefinition(
    journey_code=DEFAULT_JOURNEY_CODE,
    journey_version=DEFAULT_JOURNEY_VERSION,
    core_sequence=[
        # Referral was successfully validated and a referral instance exists.
        "VALIDATED",
        # Referee UCN has been linked/captured against the referral.
        # This is the bridge between validation and actual account onboarding.
        "UCN_CAPTURED",
        # Core banking/customer platform has confirmed account opening.
        "ACCOUNT_OPENED",
        # Account has been activated and is usable.
        "ACCOUNT_ACTIVATED",
        # Funding milestone reached.
        # In this journey FUNDED is treated as the highest core milestone.
        "FUNDED",
    ],
    allowed_transitions={
        # Initial state before any milestone has been applied.
        None: {"VALIDATED"},
        # After validation, the next expected step is that the referee is linked
        # through UCN capture. This makes the journey explicit and traceable.
        "VALIDATED": {"UCN_CAPTURED"},
        # Once UCN is captured, the account can then be opened.
        "UCN_CAPTURED": {"ACCOUNT_OPENED"},
        # After account open, activation may occur first,
        # but funding is also allowed directly because some source systems
        # may emit funding as the first reliable post-open signal.
        "ACCOUNT_OPENED": {"ACCOUNT_ACTIVATED", "FUNDED"},
        # Once activated, the next core milestone is funding.
        "ACCOUNT_ACTIVATED": {"FUNDED"},
        # After funding, the customer can complete main-banked behaviours
        # in any order. These are treated as side milestones after the core flow.
        "FUNDED": {
            "DEBIT_ORDER_SWITCHED",
            "SALARY_SWITCHED",
            "FIRST_TRANSACTION_COMPLETED",
        },
    },
    event_to_timestamp_field={
        # Referee UCN successfully captured / linked to referral instance.
        "UCN_CAPTURED": "ucn_captured_at",
        # Core onboarding/account lifecycle timestamps.
        "ACCOUNT_OPENED": "account_opened_at",
        "ACCOUNT_ACTIVATED": "account_activated_at",
        "FUNDED": "funded_at",
        # Post-funding habit-formation / main-banked behaviour timestamps.
        "DEBIT_ORDER_SWITCHED": "debit_order_switched_at",
        "SALARY_SWITCHED": "salary_switched_at",
        "FIRST_TRANSACTION_COMPLETED": "first_transaction_completed_at",
    },
    completion_events={
        "DEBIT_ORDER_SWITCHED",
        "SALARY_SWITCHED",
        "FIRST_TRANSACTION_COMPLETED",
    },
    completion_minimum_milestone="FUNDED",
)


INSURANCE_POLICY_V1 = JourneyDefinition(
    journey_code="INSURANCE_POLICY",
    journey_version="v1",
    core_sequence=[
        "VALIDATED",
        "QUOTE_REQUESTED",
        "QUOTE_ACCEPTED",
        "POLICY_ISSUED",
        "FIRST_PREMIUM_PAID",
    ],
    allowed_transitions={
        None: {"VALIDATED"},
        "VALIDATED": {"QUOTE_REQUESTED"},
        "QUOTE_REQUESTED": {"QUOTE_ACCEPTED"},
        "QUOTE_ACCEPTED": {"POLICY_ISSUED"},
        "POLICY_ISSUED": {"FIRST_PREMIUM_PAID"},
    },
    event_to_timestamp_field={
        "QUOTE_REQUESTED": "ucn_captured_at",
        "QUOTE_ACCEPTED": "account_opened_at",
        "POLICY_ISSUED": "account_activated_at",
        "FIRST_PREMIUM_PAID": "funded_at",
    },
    completion_events={"FIRST_PREMIUM_PAID"},
)

RETAIL_LOYALTY_V1 = JourneyDefinition(
    journey_code="RETAIL_LOYALTY",
    journey_version="v1",
    core_sequence=[
        "VALIDATED",
        "BASKET_CREATED",
        "ORDER_PLACED",
        "FIRST_PURCHASE_COMPLETED",
    ],
    allowed_transitions={
        None: {"VALIDATED"},
        "VALIDATED": {"BASKET_CREATED"},
        "BASKET_CREATED": {"ORDER_PLACED"},
        "ORDER_PLACED": {"FIRST_PURCHASE_COMPLETED"},
    },
    event_to_timestamp_field={
        "BASKET_CREATED": "basket_created_at",
        "ORDER_PLACED": "order_placed_at",
        "FIRST_PURCHASE_COMPLETED": "first_purchase_completed_at",
    },
    completion_events={"FIRST_PURCHASE_COMPLETED"},
)

JOURNEY_DEFINITIONS: dict[str, JourneyDefinition] = {
    f"{DEFAULT_JOURNEY_CODE}:{DEFAULT_JOURNEY_VERSION}": BANKING_TRANSACTIONAL_V1,
    "INSURANCE_POLICY:v1": INSURANCE_POLICY_V1,
    "RETAIL_LOYALTY:v1": RETAIL_LOYALTY_V1,
}


def get_journey_definition(
    journey_code: str, journey_version: str
) -> JourneyDefinition:
    key = f"{journey_code}:{journey_version}"
    if key not in JOURNEY_DEFINITIONS:
        raise ValueError(f"Unsupported journey definition: {key}")
    return JOURNEY_DEFINITIONS[key]
