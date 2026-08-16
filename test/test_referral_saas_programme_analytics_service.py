from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest

from services import referral_saas_programme_analytics_service as svc


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
async def test_programme_analytics_returns_safe_version_comparison(monkeypatch):
    published_at = datetime(2026, 8, 15, 10, 30, tzinfo=timezone.utc)
    conn = FakeConn(
        rows=[
            {
                "programme_version_id": "programme-version-2",
                "programme_code": "HOME_LOANS",
                "programme_name": "Home Loans Referral Programme",
                "version_number": 2,
                "version_status": "PUBLISHED",
                "customer_journey_version_id": "journey-version-2",
                "sub_product_code": "RMCA_BUNDLE",
                "published_at": published_at,
                "campaign_count": 2,
                "active_campaign_count": 1,
                "referral_count": 10,
                "attributed_referral_count": 7,
                "completed_referral_count": 4,
                "progress_event_count": 22,
                "high_value_event_count": 5,
                "incentive_binding_count": 3,
                "engagement_binding_count": 2,
            },
            {
                "programme_version_id": "programme-version-1",
                "programme_code": "HOME_LOANS",
                "programme_name": "Home Loans Referral Programme",
                "version_number": 1,
                "version_status": "RETIRED",
                "customer_journey_version_id": "journey-version-1",
                "sub_product_code": "RMCA_BUNDLE",
                "published_at": published_at,
                "campaign_count": 1,
                "active_campaign_count": 0,
                "referral_count": 8,
                "attributed_referral_count": 4,
                "completed_referral_count": 2,
                "progress_event_count": 12,
                "high_value_event_count": 2,
                "incentive_binding_count": 1,
                "engagement_binding_count": 1,
            },
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.build_referral_saas_programme_analytics_read_model(
        account_id="acct-1",
        tenant_code="FNB",
        limit=25,
    )

    safe = result.to_safe_dict()
    latest = safe["versions"][0]
    assert safe["versionCount"] == 2
    assert latest["programmeCode"] == "HOME_LOANS"
    assert latest["campaignCount"] == 2
    assert latest["attributionRate"] == 0.7
    assert latest["completionRate"] == 0.4
    assert latest["highValueEventRate"] == 0.2273
    assert latest["incentiveBindingCount"] == 3
    assert latest["engagementBindingCount"] == 2
    assert latest["performanceSignal"] == "OPTIMISE_COMPLETION"
    assert safe["summary"]["programmeVersionsCompared"] == 2
    assert safe["summary"]["analyticsSignal"] == "OPTIMISE_COMPLETION"
    assert safe["summary"]["latestProgrammeVersionId"] == "programme-version-2"
    assert safe["summary"]["previousProgrammeVersionId"] == "programme-version-1"
    assert safe["summary"]["latestVsPrevious"]["comparisonSignal"] == "IMPROVED"
    assert safe["summary"]["latestVsPrevious"]["completionRateChange"] == 0.15
    assert "accountId" not in safe
    assert "tenantCode" not in safe
    assert "accountId" not in latest
    assert "tenantCode" not in latest
    assert "raw_event_payload" in safe["redactions"]
    assert "reward_amount" in safe["redactions"]
    assert safe["noIncentiveRewardPayoutDetailConfirmed"] is True
    assert safe["noAuthBillingSettlementOrMoneyActionConfirmed"] is True

    query = conn.calls[0][1]
    assert "referral_saas_programme_versions" in query
    assert "referral_saas_programme_binding" in query
    assert "referral_instances" in query
    assert "referral_progress_events" in query
    assert "campaign_attributions" in query
    assert conn.calls[0][2][0] == "acct-1"
    assert conn.calls[0][2][1] == "FNB"


@pytest.mark.asyncio
async def test_programme_analytics_handles_versions_without_traffic(monkeypatch):
    conn = FakeConn(
        rows=[
            {
                "programme_version_id": "programme-version-1",
                "programme_code": "HOME_LOANS",
                "programme_name": "Home Loans Referral Programme",
                "version_number": 1,
                "version_status": "PUBLISHED",
                "customer_journey_version_id": "journey-version-1",
                "sub_product_code": "RMCA_BUNDLE",
                "published_at": None,
                "campaign_count": 0,
                "active_campaign_count": 0,
                "referral_count": 0,
                "attributed_referral_count": 0,
                "completed_referral_count": 0,
                "progress_event_count": 0,
                "high_value_event_count": 0,
                "incentive_binding_count": 0,
                "engagement_binding_count": 0,
            }
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.build_referral_saas_programme_analytics_read_model(
        account_id="acct-1",
        tenant_code="FNB",
        limit=200,
    )

    safe = result.to_safe_dict()
    assert safe["versions"][0]["performanceSignal"] == "NO_TRAFFIC"
    assert safe["summary"]["analyticsSignal"] == "NO_TRAFFIC"
    assert safe["summary"]["latestVsPrevious"]["comparisonSignal"] == "BASELINE_ONLY"
    assert conn.calls[0][2][3] == svc.MAX_PROGRAMME_ANALYTICS_LIMIT
