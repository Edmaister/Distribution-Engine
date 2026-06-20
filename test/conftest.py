import datetime
from dataclasses import dataclass
from typing import Optional

import pytest


@dataclass
class FakeMilestone:
    progress_percent: int
    progress_band: str
    display_status: str
    next_milestone: Optional[str]


@dataclass
class FakeProgressDefinition:
    milestones: dict
    complete_band: str = "100%"
    complete_display_status: str = "Completed"


@dataclass
class FakeJourneyDefinition:
    allowed_transitions: dict
    core_sequence: list[str]
    event_to_timestamp_field: dict[str, str]


@pytest.fixture
def fixed_now():
    return datetime.datetime(2026, 4, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)


@pytest.fixture
def fake_progress_definition():
    return FakeProgressDefinition(
        milestones={
            "VALIDATED": FakeMilestone(0, "0%", "Validated", "Open account"),
            "UCN_CAPTURED": FakeMilestone(10, "1-10%", "UCN captured", "Open account"),
            "ACCOUNT_OPENED": FakeMilestone(25, "11-25%", "Account opened", "Activate account"),
            "ACCOUNT_ACTIVATED": FakeMilestone(50, "26-50%", "Account activated", "Fund account"),
            "FUNDED": FakeMilestone(75, "51-75%", "Funded", "Build habit"),
        },
        complete_band="100%",
        complete_display_status="Completed",
    )


@pytest.fixture
def fake_journey_definition():
    return FakeJourneyDefinition(
        allowed_transitions={
            "VALIDATED": {"UCN_CAPTURED", "ACCOUNT_OPENED"},
            "UCN_CAPTURED": {"ACCOUNT_OPENED"},
            "ACCOUNT_OPENED": {"ACCOUNT_ACTIVATED"},
            "ACCOUNT_ACTIVATED": {"FUNDED"},
            "FUNDED": {
                "DEBIT_ORDER_SWITCHED",
                "SALARY_SWITCHED",
                "FIRST_TRANSACTION_COMPLETED",
            },
        },
        core_sequence=[
            "VALIDATED",
            "UCN_CAPTURED",
            "ACCOUNT_OPENED",
            "ACCOUNT_ACTIVATED",
            "FUNDED",
        ],
        event_to_timestamp_field={
            "UCN_CAPTURED": "ucn_captured_at",
            "ACCOUNT_OPENED": "account_opened_at",
            "ACCOUNT_ACTIVATED": "account_activated_at",
            "FUNDED": "funded_at",
            "DEBIT_ORDER_SWITCHED": "debit_order_switched_at",
            "SALARY_SWITCHED": "salary_switched_at",
            "FIRST_TRANSACTION_COMPLETED": "first_transaction_completed_at",
        },
    )


@pytest.fixture
def blank_instance():
    return {
        "referral_track_id": "track-1",
        "status": "VALIDATED",
        "journey_code": "BANKING_TRANSACTIONAL",
        "journey_version": "v1",
        "referee_ucn": None,
        "referee_ucn_hash": None,
        "ucn_captured_at": None,
        "account_opened_at": None,
        "account_activated_at": None,
        "funded_at": None,
        "debit_order_switched_at": None,
        "salary_switched_at": None,
        "first_transaction_completed_at": None,
        "progress_percent": None,
        "progress_band": None,
        "display_status": None,
        "next_milestone": None,
        "is_complete": False,
        "completed_at": None,
        "updated_at": None,
    }