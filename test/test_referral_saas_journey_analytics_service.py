from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest

from services import referral_saas_journey_analytics_service as svc


class FakeConn:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    async def fetch(self, query, *params):
        self.calls.append(("fetch", query, params))
        return self.rows


def patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(svc, "db_connection", fake_db_connection)


@pytest.mark.asyncio
async def test_journey_analytics_returns_safe_version_comparison(monkeypatch):
    published_at = datetime(2026, 8, 15, 10, 30, tzinfo=timezone.utc)
    conn = FakeConn(
        rows=[
            {
                "customer_journey_version_id": "version-1",
                "customer_journey_code": "FNB_REFERRAL",
                "version_number": 2,
                "version_status": "PUBLISHED",
                "template_code": "STANDARD_REFERRAL",
                "template_version": "1.0.0",
                "published_at": published_at,
                "campaign_count": 2,
                "active_campaign_count": 1,
                "referral_count": 10,
                "attributed_referral_count": 7,
                "completed_referral_count": 4,
                "progress_event_count": 22,
                "high_value_event_count": 5,
            }
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.build_referral_saas_journey_analytics_read_model(
        account_id="acct-1",
        tenant_code="FNB",
        limit=25,
    )

    safe = result.to_safe_dict()
    version = safe["versions"][0]
    assert safe["versionCount"] == 1
    assert version["customerJourneyCode"] == "FNB_REFERRAL"
    assert version["campaignCount"] == 2
    assert version["attributionRate"] == 0.7
    assert version["completionRate"] == 0.4
    assert version["attributionGapCount"] == 3
    assert version["completionGapCount"] == 6
    assert version["performanceSignal"] == "OPTIMISE_COMPLETION"
    assert safe["summary"]["journeyVersionsCompared"] == 1
    assert safe["summary"]["analyticsSignal"] == "OPTIMISE_COMPLETION"
    assert "accountId" not in safe
    assert "tenantCode" not in safe
    assert "accountId" not in version
    assert "tenantCode" not in version
    assert "raw_event_payload" in safe["redactions"]
    assert "reward_amount" in safe["redactions"]
    assert safe["noAuthBillingSettlementOrMoneyActionConfirmed"] is True

    query = conn.calls[0][1]
    assert "referral_saas_customer_journey_versions" in query
    assert "referral_saas_campaign_journey_bindings" in query
    assert "referral_progress_events" in query
    assert "campaign_attributions" in query
    assert conn.calls[0][2][0] == "acct-1"
    assert conn.calls[0][2][1] == "FNB"


@pytest.mark.asyncio
async def test_journey_analytics_handles_published_versions_without_traffic(monkeypatch):
    conn = FakeConn(
        rows=[
            {
                "customer_journey_version_id": "version-1",
                "customer_journey_code": "FNB_REFERRAL",
                "version_number": 1,
                "version_status": "PUBLISHED",
                "template_code": "STANDARD_REFERRAL",
                "template_version": "1.0.0",
                "published_at": None,
                "campaign_count": 0,
                "active_campaign_count": 0,
                "referral_count": 0,
                "attributed_referral_count": 0,
                "completed_referral_count": 0,
                "progress_event_count": 0,
                "high_value_event_count": 0,
            }
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.build_referral_saas_journey_analytics_read_model(
        account_id="acct-1",
        tenant_code="FNB",
        limit=200,
    )

    safe = result.to_safe_dict()
    assert safe["versions"][0]["performanceSignal"] == "NO_TRAFFIC"
    assert safe["summary"]["analyticsSignal"] == "NO_TRAFFIC"
    assert conn.calls[0][2][3] == svc.MAX_JOURNEY_ANALYTICS_LIMIT
