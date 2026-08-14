from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest

import services.referral_saas_journey_configuration_service as service


pytestmark = pytest.mark.asyncio


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

    monkeypatch.setattr(service, "db_connection", fake_db_connection)


def _template_row(**overrides):
    values = {
        "journey_template_id": "template-1",
        "template_code": "REFERRAL_STANDARD",
        "template_name": "Referral standard",
        "template_family": "REFERRAL",
        "owner_scope": "AMPLIFI_GOVERNED",
        "template_status": "APPROVED",
        "safe_summary": {
            "plainLanguageName": "Referral standard",
            "tenant_code": "hidden",
            "nested": {"secret": "hidden", "visible": "kept"},
        },
        "governance_metadata": {
            "riskTier": "LOW",
            "auth_claim": "hidden",
        },
        "template_created_by_ref": "amplifi-admin",
        "template_updated_by_ref": "amplifi-admin",
        "template_created_at": datetime(2026, 8, 14, tzinfo=timezone.utc),
        "template_updated_at": datetime(2026, 8, 14, tzinfo=timezone.utc),
        "template_archived_at": None,
        "journey_template_version_id": "version-1",
        "template_version": "1.0.0",
        "version_status": "APPROVED",
        "milestone_schema": [{"code": "SIGNED_UP"}, {"code": "FUNDED"}],
        "transition_rules": [{"from": "SIGNED_UP", "to": "FUNDED"}],
        "evidence_requirements": [{"code": "TERMS_ACCEPTED"}],
        "allowed_configuration_schema": {
            "milestones": {},
            "labels": {},
            "credential": "hidden-source-but-key-count-only",
        },
        "approved_by_ref": "amplifi-reviewer",
        "approved_at": datetime(2026, 8, 14, tzinfo=timezone.utc),
        "version_created_by_ref": "amplifi-admin",
        "version_created_at": datetime(2026, 8, 14, tzinfo=timezone.utc),
        "version_updated_at": datetime(2026, 8, 14, tzinfo=timezone.utc),
        "version_archived_at": None,
    }
    values.update(overrides)
    return values


async def test_list_journey_templates_returns_safe_catalogue(monkeypatch):
    conn = FakeConn([_template_row()])
    patch_db(monkeypatch, conn)

    catalogue = await service.list_referral_saas_journey_templates(limit=25)

    body = catalogue.to_safe_dict()
    assert body["status"] == "READY"
    assert body["templateCount"] == 1
    assert body["statusFilter"] == ["APPROVED", "DRAFT"]
    assert body["noTenantDataConfirmed"] is True
    assert body["noRuntimeExecutionConfirmed"] is True

    template = body["templates"][0]
    assert template["templateCode"] == "REFERRAL_STANDARD"
    assert template["safeSummary"] == {
        "plainLanguageName": "Referral standard",
        "nested": {"visible": "kept"},
    }
    assert template["governanceMetadata"] == {"riskTier": "LOW"}

    version = template["versions"][0]
    assert version["templateVersion"] == "1.0.0"
    assert version["milestoneCount"] == 2
    assert version["transitionRuleCount"] == 1
    assert version["evidenceRequirementCount"] == 1
    assert version["allowedConfigurationSections"] == ["labels", "milestones"]
    assert "definitionPayload" not in version
    assert "transitionRules" not in version
    assert "payloadHash" not in version
    assert "tenantCode" not in str(template)

    _, _, params = conn.calls[0]
    assert params[0] == ["APPROVED", "DRAFT"]
    assert params[1] == ["APPROVED", "DRAFT"]
    assert params[2] == 25


async def test_list_journey_templates_filters_archived_when_requested(monkeypatch):
    conn = FakeConn([])
    patch_db(monkeypatch, conn)

    catalogue = await service.list_referral_saas_journey_templates(
        statuses=["approved", "archived"],
        include_archived=True,
        limit=250,
    )

    assert catalogue.to_safe_dict()["statusFilter"] == ["APPROVED", "ARCHIVED"]
    _, _, params = conn.calls[0]
    assert params[0] == ["APPROVED", "ARCHIVED"]
    assert params[2] == service.MAX_TEMPLATE_CATALOGUE_LIMIT


async def test_list_journey_templates_rejects_unknown_status(monkeypatch):
    conn = FakeConn([])
    patch_db(monkeypatch, conn)

    with pytest.raises(service.JourneyTemplateCatalogueValidationError):
        await service.list_referral_saas_journey_templates(statuses=["LIVE"])


async def test_get_journey_template_returns_safe_detail(monkeypatch):
    conn = FakeConn(
        [
            _template_row(template_version="2.0.0", journey_template_version_id="version-2"),
            _template_row(template_version="1.0.0", journey_template_version_id="version-1"),
        ]
    )
    patch_db(monkeypatch, conn)

    template = await service.get_referral_saas_journey_template(
        template_code="referral_standard",
    )

    body = template.to_safe_dict()
    assert body["templateCode"] == "REFERRAL_STANDARD"
    assert body["versionCount"] == 2
    _, _, params = conn.calls[0]
    assert params[2] == "referral_standard"


async def test_get_journey_template_raises_not_found(monkeypatch):
    conn = FakeConn([])
    patch_db(monkeypatch, conn)

    with pytest.raises(service.JourneyTemplateNotFound):
        await service.get_referral_saas_journey_template(
            template_code="missing-template",
        )


async def test_customer_journey_validation_simulates_safe_template_defaults():
    status, blockers, warnings, summary = service._validate_configuration_against_schema(
        {"labels": {"title": "Mortgage application referral"}},
        {"labels": {}, "milestones": {}, "evidence": {}, "attribution": {}},
        [{"code": "SIGNED_UP"}, {"code": "APPLICATION_SUBMITTED"}],
        [{"from": "SIGNED_UP", "to": "APPLICATION_SUBMITTED"}],
        [{"code": "TERMS_ACCEPTED", "required": True}],
    )

    assert status == "PASSED_WITH_WARNINGS"
    assert blockers == []
    assert [warning["code"] for warning in warnings] == [
        "REQUIRED_EVIDENCE_USES_TEMPLATE_DEFAULTS"
    ]
    assert summary["templateMilestoneCount"] == 2
    assert summary["templateTransitionCount"] == 1
    assert summary["simulation"] == {
        "status": "PASSED_WITH_WARNINGS",
        "canPublish": True,
        "canBindCampaign": False,
        "simulatedMilestonePath": ["SIGNED_UP", "APPLICATION_SUBMITTED"],
        "customerReadableSummary": (
            "This journey draft can be reviewed for publish readiness."
        ),
        "nextAction": "Review warnings and continue to governed publish controls.",
    }
    assert summary["noRuntimeJourneyMutationConfirmed"] is True
    assert summary["noProviderDispatchConfirmed"] is True
    assert summary["noAuthBillingOrMoneyActionConfirmed"] is True


async def test_customer_journey_validation_blocks_invalid_customer_transition_and_evidence():
    status, blockers, warnings, summary = service._validate_configuration_against_schema(
        {
            "milestones": [{"code": "SIGNED_UP"}, {"code": "FUNDED"}],
            "transitions": [{"from": "SIGNED_UP", "to": "FUNDED"}],
            "evidence": [{"code": "TERMS_ACCEPTED"}],
        },
        {"milestones": {}, "transitions": {}, "evidence": {}},
        [{"code": "SIGNED_UP"}, {"code": "APPLICATION_SUBMITTED"}],
        [{"from": "SIGNED_UP", "to": "APPLICATION_SUBMITTED"}],
        [
            {"code": "TERMS_ACCEPTED", "required": True},
            {"code": "APPLICATION_COMPLETE", "required": True},
        ],
    )

    blocker_codes = {blocker["code"] for blocker in blockers}
    assert status == "BLOCKED"
    assert warnings == []
    assert blocker_codes == {
        "UNKNOWN_MILESTONE",
        "INVALID_CUSTOMER_TRANSITION",
        "REQUIRED_EVIDENCE_MISSING",
    }
    assert summary["transitionCheckStatus"] == "BLOCKED"
    assert summary["evidenceCheckStatus"] == "BLOCKED"
    assert summary["simulation"]["canPublish"] is False
    assert summary["simulation"]["canBindCampaign"] is False


async def test_customer_journey_validation_blocks_unsafe_reward_and_attribution_settings():
    status, blockers, warnings, summary = service._validate_configuration_against_schema(
        {
            "rewards": [{"policyCode": "SAFE_POLICY", "amount": 100}],
            "attribution": {"windowDays": 120, "manualOverride": True},
        },
        {"rewards": {}, "attribution": {}},
        [{"code": "SIGNED_UP"}],
        [],
        [],
    )

    blocker_codes = {blocker["code"] for blocker in blockers}
    assert status == "BLOCKED"
    assert warnings == []
    assert blocker_codes == {
        "UNSAFE_REWARD_SETTING",
        "UNSAFE_ATTRIBUTION_SETTING",
        "ATTRIBUTION_WINDOW_OUT_OF_RANGE",
    }
    assert summary["rewardSafetyStatus"] == "BLOCKED"
    assert summary["attributionSafetyStatus"] == "BLOCKED"
    assert summary["noCampaignActivationConfirmed"] is True
