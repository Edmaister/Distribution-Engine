from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest

from services import referral_saas_operations_service as service


class _Connection:
    async def fetchrow(
        self, _query, jurisdictions, priority, customer, category, status, owner, service_target
    ):
        assert jurisdictions == ["BW", "ZA"]
        assert priority == "HIGH"
        assert (customer, category, status, owner, service_target) == (
            None,
            None,
            None,
            None,
            None,
        )
        return {"awaiting_action": 2, "customers_needing_attention": 1, "production_incidents": 0}

    async def fetch(
        self,
        _query,
        jurisdictions,
        priority,
        customer,
        category,
        status,
        owner,
        service_target,
        limit,
        offset,
    ):
        assert (jurisdictions, priority, limit, offset) == (["BW", "ZA"], "HIGH", 2, 0)
        return [
            {
                "support_case_id": "case-1",
                "account_id": "account-1",
                "account_code": "ACC-1",
                "account_name": "Customer One",
                "jurisdiction": "ZA",
                "title": "Review attribution evidence",
                "category": "ATTRIBUTION_REVIEW",
                "priority": "HIGH",
                "status": "OPEN",
                "assignee_ref": "operator-1",
                "updated_at": datetime(2026, 8, 19, tzinfo=timezone.utc),
            }
        ]


@pytest.mark.asyncio
async def test_operations_read_model_is_permission_filtered_and_explainable(monkeypatch):
    @asynccontextmanager
    async def _db():
        yield _Connection()

    monkeypatch.setattr(service, "db_connection", _db)
    result = await service.read_referral_saas_operations(
        jurisdictions=["za", "BW"], priority="high", limit=1
    )
    payload = result.to_safe_dict()
    assert payload["metrics"]["awaitingYourAction"] == 2
    assert payload["metrics"]["withinServiceTargetPercent"] is None
    assert payload["workItems"][0]["destination"].endswith("/account-1/support?case=case-1")
    assert payload["filters"]["jurisdictions"] == ["BW", "ZA"]
    assert "NO_SYNTHETIC_SERVICE_TARGET" in payload["guardrails"]


@pytest.mark.asyncio
async def test_operations_read_model_rejects_invalid_cursor():
    with pytest.raises(service.ReferralSaasOperationsReadError):
        await service.read_referral_saas_operations(jurisdictions=None, cursor="bad")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("filters", "message"),
    [
        ({"status": "CLOSED"}, "Status"),
        ({"work_type": "CAMPAIGN"}, "Work type"),
        ({"service_target": "LATE"}, "Service-target"),
        ({"sort": "TITLE"}, "Sort"),
    ],
)
async def test_operations_read_model_rejects_unsupported_filters(filters, message):
    with pytest.raises(service.ReferralSaasOperationsReadError, match=message):
        await service.read_referral_saas_operations(jurisdictions=None, **filters)
