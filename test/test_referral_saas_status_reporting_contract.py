from __future__ import annotations

from decimal import Decimal

import pytest

from services import referral_saas_reporting_service as reporting
from services import tenant_safe_analytics_service as analytics
from services.referral_saas_reporting_service import (
    get_referral_saas_report,
    validate_referral_saas_report_export_request,
)
from services.referral_saas_safe_status_service import (
    project_referral_saas_safe_status,
)

SAFE_REFERRAL_SUBJECT = {
    "type": "referral",
    "safe_ref": "referral:track:11111111-1111-4111-8111-111111111111",
}


class FakeDbConnection:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _overview() -> dict:
    return {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "campaign_code": "CAMP001",
        "distributors": {"total_count": 0, "active_count": 0},
        "opportunities": {"total_count": 1, "published_count": 1},
        "routes": {
            "total_count": 3,
            "accepted_count": 2,
            "acceptance_rate": Decimal("0.6667"),
        },
        "commissions": {
            "event_count": 4,
            "total_commission_amount": Decimal("250.00"),
        },
        "conversions": {
            "linked_count": 2,
            "completed_count": 1,
            "completion_rate": Decimal("0.5000"),
            "attribution_rate": Decimal("0.7500"),
        },
        "wallets": {
            "wallet_count": 1,
            "current_balance": Decimal("999.99"),
        },
        "governance": {"open_dispute_count": 0},
    }


def test_referral_saas_referrer_customer_safe_status_contract():
    referrer_statuses = [
        project_referral_saas_safe_status(
            viewer_role="referrer",
            subject=SAFE_REFERRAL_SUBJECT,
            evidence={
                "source_family": "outcome",
                "status": "ACCOUNT_OPENED",
                "source_confidence": "MEDIUM",
            },
            redactions=["referrer_ucn", "tenant_code"],
        ),
        project_referral_saas_safe_status(
            viewer_role="referrer",
            subject=SAFE_REFERRAL_SUBJECT,
            evidence={
                "source_family": "reward",
                "status": "PENDING_FULFILMENT",
                "source_confidence": "LOW",
            },
            redactions=["referrer_ucn", "tenant_code"],
        ),
    ]

    assert [item["safe_status"]["status"] for item in referrer_statuses] == [
        "IN_PROGRESS",
        "IN_PROGRESS",
    ]
    assert [item["safe_status"]["product_status"] for item in referrer_statuses] == [
        "IN_PROGRESS",
        "IN_PROGRESS",
    ]
    assert all(
        item["subject"]["safe_ref"] == SAFE_REFERRAL_SUBJECT["safe_ref"]
        for item in referrer_statuses
    )
    assert "ACCOUNT_OPENED" not in str(referrer_statuses)
    assert "PENDING_FULFILMENT" not in str(referrer_statuses)
    assert "tenant_code" in referrer_statuses[0]["safe_status"]["redactions"]
    assert "referrer_ucn" in referrer_statuses[0]["safe_status"]["redactions"]

    customer_status = project_referral_saas_safe_status(
        viewer_role="customer",
        subject=SAFE_REFERRAL_SUBJECT,
        evidence={"source_family": "settlement", "status": "SETTLED"},
    )

    assert customer_status["safe_status"]["status"] == "UNAVAILABLE"
    assert customer_status["safe_status"]["action_category"] == "NOT_AVAILABLE"
    assert "SETTLED" not in str(customer_status)


@pytest.mark.asyncio
async def test_referral_saas_reporting_contract_stays_operational_and_redacted(
    monkeypatch,
):
    calls: list[dict] = []

    async def fake_get_marketplace_overview(**kwargs):
        calls.append(kwargs)
        return _overview()

    monkeypatch.setattr(
        analytics,
        "get_marketplace_overview",
        fake_get_marketplace_overview,
    )

    report = await analytics.get_tenant_safe_analytics_report(
        tenant_code="fnb",
        report_type="distribution_overview",
        dimensions=["tenant_code", "campaign_code", "metric_name"],
        filters={
            "campaign_code": "CAMP001",
            "referrer_ucn": "900001",
            "raw_customer_identifier": "secret-customer",
        },
    )

    assert calls == [
        {
            "tenant_code": "FNB",
            "sponsor_code": None,
            "campaign_code": "CAMP001",
        }
    ]
    assert report["tenant_scope"] == "FNB"
    assert report["metric_class"] == "OPERATIONAL"
    assert report["reconciliation_status"] == "NOT_APPLICABLE"
    assert set(report["redactions"]) == {
        "raw_customer_identifier",
        "referrer_ucn",
    }

    metric_names = {metric["name"] for metric in report["metrics"]}
    assert "conversions.linked_count" in metric_names
    assert "conversions.attribution_rate" in metric_names
    assert "commissions.total_commission_amount" not in metric_names
    assert "wallets.current_balance" not in metric_names
    assert "900001" not in str(report)
    assert "secret-customer" not in str(report)


@pytest.mark.asyncio
async def test_referral_saas_report_catalog_supports_initial_operational_reports(
    monkeypatch,
):
    async def fake_get_marketplace_overview(**kwargs):
        return _overview()

    monkeypatch.setattr(
        analytics,
        "get_marketplace_overview",
        fake_get_marketplace_overview,
    )

    report = await get_referral_saas_report(
        tenant_code="FNB",
        report_type="campaign_performance",
        filters={"campaign_code": "CAMP001"},
    )

    assert report["report_type"] == "campaign_performance"
    assert report["source_report_type"] == "distribution_overview"
    assert report["metric_class"] == "OPERATIONAL"
    assert report["export_status"] == "NOT_IMPLEMENTED"

    funnel_report = await get_referral_saas_report(
        tenant_code="FNB",
        report_type="referral_funnel",
        filters={"campaign_code": "CAMP001"},
    )

    assert funnel_report["report_type"] == "referral_funnel"
    assert funnel_report["source_report_type"] == "distribution_overview"
    assert funnel_report["metric_class"] == "OPERATIONAL"
    assert funnel_report["export_status"] == "NOT_IMPLEMENTED"
    assert {
        metric["name"] for metric in funnel_report["metrics"]
    } >= {
        "funnel.linked_route_count",
        "funnel.completed_referral_count",
        "funnel.attribution_rate",
    }
    assert funnel_report["source_warnings"] == [
        {
            "code": "PARTIAL_SOURCE_COVERAGE",
            "message": (
                "Referral funnel currently uses tenant-safe distribution "
                "overview metrics; validation-state and "
                "progress-milestone stage counts need dedicated follow-up "
                "report sources before they can be promised."
            ),
        }
    ]

    class LinkCodeConnection:
        async def fetch(self, query, *params):
            assert "WITH link_sources AS" in query
            assert params[:4] == ("FNB", "CAMP001", None, None)
            return [
                {
                    "source_type": "CAMPAIGN_REFERRAL_LINK",
                    "link_code_status": "LINKED",
                    "campaign_code": "CAMP001",
                    "issued_period": "2026-07-12",
                    "resolved_period": "2026-07-12",
                    "link_code_count": 2,
                }
            ]

    monkeypatch.setattr(
        reporting, "db_connection", lambda: FakeDbConnection(LinkCodeConnection())
    )

    link_report = await get_referral_saas_report(
        tenant_code="FNB",
        report_type="link_code_performance",
        filters={"campaign_code": "CAMP001"},
    )

    assert link_report["report_type"] == "link_code_performance"
    assert link_report["source_report_type"] == "referral_link_code_performance"
    assert link_report["metric_class"] == "OPERATIONAL"
    assert link_report["export_status"] == "NOT_IMPLEMENTED"
    assert link_report["metrics"][0]["name"] == "link_codes.linked_count"
    assert link_report["source_warnings"][0]["code"] == "PARTIAL_SOURCE_COVERAGE"

    class RewardVisibilityConnection:
        async def fetch(self, query, *params):
            assert "WITH reward_sources AS" in query
            assert params[:7] == (
                "FNB",
                None,
                "BASE",
                "APPLIED",
                None,
                None,
                None,
            )
            return [
                {
                    "source_family": "persisted_reward",
                    "beneficiary_type": "REFERRER",
                    "reward_source": "BASE",
                    "reward_type": "CASH",
                    "reward_status": "APPLIED",
                    "product": "TRANSACTIONAL",
                    "sub_product": "GOLD",
                    "visibility_period": "2026-07-12",
                    "reward_count": 1,
                }
            ]

    monkeypatch.setattr(
        reporting,
        "db_connection",
        lambda: FakeDbConnection(RewardVisibilityConnection()),
    )

    reward_report = await get_referral_saas_report(
        tenant_code="FNB",
        report_type="reward_visibility_summary",
        filters={"reward_source": "BASE", "reward_status": "APPLIED"},
    )

    assert reward_report["report_type"] == "reward_visibility_summary"
    assert reward_report["source_report_type"] == "referral_reward_visibility_summary"
    assert reward_report["metric_class"] == "OPERATIONAL"
    assert reward_report["export_status"] == "NOT_IMPLEMENTED"
    assert reward_report["metrics"][0]["name"] == "rewards.applied_count"
    assert {
        warning["code"] for warning in reward_report["source_warnings"]
    } == {
        "COUNT_ONLY_REWARD_VISIBILITY",
        "PENDING_MISSION_BONUS_DERIVED",
    }
    assert "999.99" not in str(reward_report)

    export_request = validate_referral_saas_report_export_request(
        tenant_code="FNB",
        report_type="campaign_performance",
        export_format="csv",
        dimensions=["campaign_ref", "metric_name"],
        filters={"campaign_ref": "CAMP001", "raw_ucn": "12345"},
    )

    assert export_request["export_status"] == "VALIDATED_NOT_CREATED"
    assert export_request["creation_status"] == "NOT_IMPLEMENTED"
    assert export_request["storage_status"] == "NOT_IMPLEMENTED"
    assert export_request["delivery_status"] == "NOT_IMPLEMENTED"
    assert export_request["audit_status"] == "NOT_IMPLEMENTED"
    assert export_request["redactions"] == ["raw_ucn"]

    with pytest.raises(ValueError, match="Unsupported analytics report_type"):
        await analytics.get_tenant_safe_analytics_report(
            tenant_code="FNB",
            report_type="campaign_performance",
        )
