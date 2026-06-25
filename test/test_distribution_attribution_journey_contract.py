from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest

import services.distribution.distributor_portal_service as portal_service
import services.distribution.reporting_service as reporting_service

pytestmark = pytest.mark.asyncio


class FakeDbConnection(AbstractAsyncContextManager):
    def __init__(self, conn: Any):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return None


class FakePortalConnection:
    def __init__(
        self, *, distributor: dict[str, Any], conversions: list[dict[str, Any]]
    ):
        self.distributor = distributor
        self.conversions = conversions

    async def fetchrow(self, query: str, *args):
        return self.distributor

    async def fetch(self, query: str, *args):
        return self.conversions


class FakeReportingConnection:
    def __init__(self, rows: list[Any]):
        self.rows = rows
        self.index = 0

    async def fetchrow(self, query: str, *args):
        row = self.rows[self.index]
        self.index += 1
        return row

    async def fetch(self, query: str, *args):
        row = self.rows[self.index]
        self.index += 1
        return row


def conversion_row(
    *,
    route_id: str | None,
    referral_track_id: str | None = None,
    is_complete: bool = False,
) -> dict[str, Any]:
    return {
        "referral_track_id": referral_track_id or str(uuid4()),
        "tenant_code": "FNB",
        "distributor_code": "AGENCY_001",
        "route_id": route_id,
        "opportunity_id": str(uuid4()) if route_id else None,
        "opportunity_code": "BOXER_HOME_LOANS" if route_id else None,
        "opportunity_title": "Boxer Home Loans" if route_id else None,
        "sponsor_code": "BOXER" if route_id else None,
        "campaign_code": "BOXER_ACQ" if route_id else None,
        "product": "HOME_LOAN",
        "sub_product": "SWITCH",
        "status": "COMPLETED" if is_complete else "FUNDED",
        "display_status": "Completed" if is_complete else "Almost there",
        "progress_percent": 100 if is_complete else 80,
        "progress_band": "DONE" if is_complete else "ACTIVE",
        "next_milestone": (
            None if is_complete else "Salary switch or debit order switch"
        ),
        "is_complete": is_complete,
        "completed_at": "2026-06-12T11:00:00" if is_complete else None,
        "validated_at": "2026-06-12T10:00:00",
        "ucn_captured_at": "2026-06-12T10:05:00",
        "account_opened_at": "2026-06-12T10:10:00",
        "account_activated_at": "2026-06-12T10:20:00",
        "funded_at": "2026-06-12T10:30:00",
        "debit_order_switched_at": None,
        "salary_switched_at": None,
        "first_transaction_completed_at": None,
        "created_at": "2026-06-12T10:00:00",
        "updated_at": "2026-06-12T10:30:00",
    }


async def test_distributor_conversion_summary_tracks_attribution(monkeypatch):
    distributor_id = str(uuid4())
    conn = FakePortalConnection(
        distributor={
            "distributor_id": distributor_id,
            "tenant_code": "FNB",
            "distributor_code": "AGENCY_001",
        },
        conversions=[
            conversion_row(route_id=str(uuid4()), is_complete=True),
            conversion_row(route_id=str(uuid4()), is_complete=False),
            conversion_row(route_id=None, is_complete=False),
        ],
    )

    monkeypatch.setattr(
        portal_service,
        "db_connection",
        lambda: FakeDbConnection(conn),
    )

    result = await portal_service.list_portal_conversions(
        tenant_code="FNB",
        distributor_code="AGENCY_001",
    )

    assert result["distributor_id"] == distributor_id
    assert result["count"] == 3
    assert result["completed_count"] == 1
    assert result["completion_rate"] == Decimal("0.3333")
    assert result["attributed_count"] == 2
    assert result["unlinked_count"] == 1
    assert result["attribution_rate"] == Decimal("0.6667")
    assert result["items"][0]["opportunity_title"] == "Boxer Home Loans"
    assert result["items"][0]["distributor_safe_status"]["status"] == "FULFILLED"
    assert result["items"][0]["distributor_safe_status"]["action_category"] == "NONE"
    assert result["items"][1]["distributor_safe_status"]["status"] == "IN_PROGRESS"
    assert result["items"][1]["distributor_safe_status"]["source_families"] == [
        "outcome"
    ]
    assert result["items"][2]["route_id"] is None
    assert result["items"][2]["distributor_safe_status"]["status"] == "IN_PROGRESS"
    assert result["items"][2]["distributor_safe_status"]["missing_evidence"] == [
        {
            "code": "NO_SOURCE_EVIDENCE",
            "severity": "INFO",
            "section": "attribution",
        }
    ]
    assert "tenant_code" not in str(result["items"][0]["distributor_safe_status"])
    assert "ucn" not in str(result["items"][0]["distributor_safe_status"]).lower()


async def test_admin_reporting_overview_tracks_network_attribution(monkeypatch):
    conn = FakeReportingConnection(
        [
            {
                "total_count": 2,
                "active_count": 2,
                "suspended_count": 0,
                "terminated_count": 0,
            },
            {
                "total_count": 1,
                "draft_count": 0,
                "published_count": 1,
                "closed_count": 0,
                "total_budget": Decimal("10000.00"),
                "remaining_budget": Decimal("8000.00"),
            },
            {
                "total_count": 3,
                "routed_count": 1,
                "accepted_count": 2,
                "declined_count": 0,
                "average_route_score": Decimal("91.50"),
            },
            {
                "event_count": 2,
                "total_commission_amount": Decimal("150.00"),
                "credited_count": 2,
            },
            {
                "linked_count": 2,
                "completed_count": 1,
                "linked_route_count": 2,
                "linked_opportunity_count": 1,
                "completion_rate": Decimal("0.5000"),
            },
            {
                "total_referral_count": 3,
                "attributed_count": 2,
                "unlinked_count": 1,
                "attribution_rate": Decimal("0.6667"),
            },
            {
                "wallet_count": 1,
                "current_balance": Decimal("150.00"),
                "available_balance": Decimal("100.00"),
                "held_balance": Decimal("50.00"),
                "paid_out_balance": Decimal("0.00"),
                "reversed_balance": Decimal("0.00"),
            },
            {
                "compliance_review_count": 1,
                "open_compliance_review_count": 0,
                "dispute_count": 0,
                "open_dispute_count": 0,
                "governance_action_count": 1,
            },
        ]
    )

    monkeypatch.setattr(
        reporting_service,
        "db_connection",
        lambda: FakeDbConnection(conn),
    )

    result = await reporting_service.get_marketplace_overview(
        tenant_code="FNB",
        sponsor_code="BOXER",
        campaign_code="BOXER_ACQ",
    )

    assert result["routes"]["acceptance_rate"] == Decimal("0.6667")
    assert result["conversions"]["linked_count"] == 2
    assert result["conversions"]["completed_count"] == 1
    assert result["conversions"]["completion_rate"] == Decimal("0.5000")
    assert result["conversions"]["total_referral_count"] == 3
    assert result["conversions"]["attributed_count"] == 2
    assert result["conversions"]["unlinked_count"] == 1
    assert result["conversions"]["attribution_rate"] == Decimal("0.6667")
