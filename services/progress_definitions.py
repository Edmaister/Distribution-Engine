from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from services.journey_definitions import DEFAULT_JOURNEY_CODE, DEFAULT_JOURNEY_VERSION


@dataclass(frozen=True)
class ProgressMilestoneDefinition:
    """
    Describes how a single journey milestone should be represented
    on the progress snapshot stored on referral_instances.
    """

    progress_percent: int
    progress_band: str
    display_status: str
    next_milestone: Optional[str]


@dataclass(frozen=True)
class ProgressDefinition:
    """
    Progress configuration for a specific journey_code + journey_version.
    """

    journey_code: str
    journey_version: str
    milestones: dict[str, ProgressMilestoneDefinition]
    complete_band: str = "COMPLETE"
    complete_display_status: str = "Journey complete"


BANKING_TRANSACTIONAL_V1 = ProgressDefinition(
    journey_code=DEFAULT_JOURNEY_CODE,
    journey_version=DEFAULT_JOURNEY_VERSION,
    milestones={
        "VALIDATED": ProgressMilestoneDefinition(
            progress_percent=10,
            progress_band="STARTED",
            display_status="Referral validated",
            next_milestone="UCN_CAPTURED",
        ),
        "UCN_CAPTURED": ProgressMilestoneDefinition(
            progress_percent=20,
            progress_band="STARTED",
            display_status="Customer linked",
            next_milestone="ACCOUNT_OPENED",
        ),
        "ACCOUNT_OPENED": ProgressMilestoneDefinition(
            progress_percent=40,
            progress_band="IN_PROGRESS",
            display_status="Account opened",
            next_milestone="ACCOUNT_ACTIVATED",
        ),
        "ACCOUNT_ACTIVATED": ProgressMilestoneDefinition(
            progress_percent=60,
            progress_band="IN_PROGRESS",
            display_status="Account activated",
            next_milestone="FUNDED",
        ),
        "FUNDED": ProgressMilestoneDefinition(
            progress_percent=80,
            progress_band="NEAR_COMPLETE",
            display_status="Account funded",
            next_milestone="DEBIT_ORDER_SWITCHED",
        ),
    },
    complete_band="COMPLETE",
    complete_display_status="Journey complete",
)

INSURANCE_POLICY_V1 = ProgressDefinition(
    journey_code="INSURANCE_POLICY",
    journey_version="v1",
    milestones={
        "VALIDATED": ProgressMilestoneDefinition(
            progress_percent=10,
            progress_band="STARTED",
            display_status="Referral validated",
            next_milestone="QUOTE_REQUESTED",
        ),
        "QUOTE_REQUESTED": ProgressMilestoneDefinition(
            progress_percent=25,
            progress_band="IN_PROGRESS",
            display_status="Insurance quote requested",
            next_milestone="QUOTE_ACCEPTED",
        ),
        "QUOTE_ACCEPTED": ProgressMilestoneDefinition(
            progress_percent=50,
            progress_band="IN_PROGRESS",
            display_status="Insurance quote accepted",
            next_milestone="POLICY_ISSUED",
        ),
        "POLICY_ISSUED": ProgressMilestoneDefinition(
            progress_percent=75,
            progress_band="NEAR_COMPLETE",
            display_status="Policy issued",
            next_milestone="FIRST_PREMIUM_PAID",
        ),
        "FIRST_PREMIUM_PAID": ProgressMilestoneDefinition(
            progress_percent=100,
            progress_band="COMPLETE",
            display_status="First premium paid",
            next_milestone=None,
        ),
    },
    complete_band="COMPLETE",
    complete_display_status="Policy activated",
)

RETAIL_LOYALTY_V1 = ProgressDefinition(
    journey_code="RETAIL_LOYALTY",
    journey_version="v1",
    milestones={
        "VALIDATED": ProgressMilestoneDefinition(
            progress_percent=10,
            progress_band="STARTED",
            display_status="Referral validated",
            next_milestone="BASKET_CREATED",
        ),
        "BASKET_CREATED": ProgressMilestoneDefinition(
            progress_percent=35,
            progress_band="IN_PROGRESS",
            display_status="Basket created",
            next_milestone="ORDER_PLACED",
        ),
        "ORDER_PLACED": ProgressMilestoneDefinition(
            progress_percent=70,
            progress_band="NEAR_COMPLETE",
            display_status="Order placed",
            next_milestone="FIRST_PURCHASE_COMPLETED",
        ),
        "FIRST_PURCHASE_COMPLETED": ProgressMilestoneDefinition(
            progress_percent=100,
            progress_band="COMPLETE",
            display_status="First purchase completed",
            next_milestone=None,
        ),
    },
    complete_band="COMPLETE",
    complete_display_status="First purchase completed",
)

PROGRESS_DEFINITIONS: dict[str, ProgressDefinition] = {
    f"{DEFAULT_JOURNEY_CODE}:{DEFAULT_JOURNEY_VERSION}": BANKING_TRANSACTIONAL_V1,
    "INSURANCE_POLICY:v1": INSURANCE_POLICY_V1,
    "RETAIL_LOYALTY:v1": RETAIL_LOYALTY_V1,
}


def get_progress_definition(
    journey_code: str, journey_version: str
) -> ProgressDefinition:
    key = f"{journey_code}:{journey_version}"
    if key not in PROGRESS_DEFINITIONS:
        raise ValueError(f"Unsupported progress definition: {key}")
    return PROGRESS_DEFINITIONS[key]
