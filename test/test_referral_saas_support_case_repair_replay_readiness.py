from __future__ import annotations

import pytest

from services import referral_saas_support_case_service as service
from services.referral_saas_support_case_service import (
    ReferralSaasSupportCase,
    SupportCaseEvidenceLink,
)

pytestmark = pytest.mark.asyncio


def _support_case(**overrides) -> ReferralSaasSupportCase:
    values = {
        "case_ref": "case-1",
        "account_ref": "acct-1",
        "category": "PROGRESS_DIAGNOSTIC",
        "priority": "HIGH",
        "status": "OPEN",
        "title": "Progress event stuck",
        "summary": "Inspect stored progress evidence.",
        "source_surface": "progress_status",
        "assignee_ref": None,
        "correlation_id": "corr-1",
        "created_by_ref": "operator-1",
        "created_by_role": "ADMIN",
        "created_at": "2026-08-03T10:00:00+00:00",
        "updated_at": "2026-08-03T10:00:00+00:00",
        "evidence_links": [
            SupportCaseEvidenceLink(
                evidence_link_id="evidence-1",
                evidence_type="PROGRESS_STATUS",
                evidence_ref="progress-1",
                safe_status="BLOCKED",
                warning_code="QUEUE_STUCK",
                missing_evidence_code=None,
                redactions=["provider_payload"],
            )
        ],
        "notes": [],
        "status_events": [],
        "redactions": ["internal_tenant_identifier"],
    }
    values.update(overrides)
    return ReferralSaasSupportCase(**values)


async def test_support_case_repair_replay_readiness_blocks_future_replay(
    monkeypatch,
):
    async def fake_get_referral_saas_support_case(**kwargs):
        assert kwargs == {"account_id": "acct-1", "case_ref": "case-1"}
        return _support_case()

    monkeypatch.setattr(
        service,
        "get_referral_saas_support_case",
        fake_get_referral_saas_support_case,
    )

    readiness = await service.get_referral_saas_support_case_repair_replay_readiness(
        account_id="acct-1",
        case_ref="case-1",
    )
    payload = readiness.to_safe_dict()

    assert payload["overallStatus"] == "REVIEW_REQUIRED"
    assert payload["owningWorkflow"] == "progress_status"
    assert {
        (action["action"], action["status"]) for action in payload["allowedActions"]
    } == {
        ("READ_ONLY_DIAGNOSTIC", "AVAILABLE"),
        ("GOVERNED_REPLAY", "BLOCKED"),
    }
    assert "before_state_hash" in payload["requiredEvidence"]
    assert "provider_payload" in payload["redactions"]
    assert payload["no_repair_replay_retry_confirmed"] is True
    assert payload["no_provider_dispatch_confirmed"] is True
    assert payload["no_credential_or_auth_claim_change_confirmed"] is True
    assert payload["no_campaign_activation_confirmed"] is True
    assert payload["no_billing_or_money_movement_confirmed"] is True


async def test_support_case_repair_replay_readiness_excludes_unsupported_category(
    monkeypatch,
):
    async def fake_get_referral_saas_support_case(**kwargs):
        return _support_case(category="INTEGRATION_HEALTH")

    monkeypatch.setattr(
        service,
        "get_referral_saas_support_case",
        fake_get_referral_saas_support_case,
    )

    readiness = await service.get_referral_saas_support_case_repair_replay_readiness(
        account_id="acct-1",
        case_ref="case-1",
    )
    payload = readiness.to_safe_dict()

    assert payload["overallStatus"] == "ACTION_NOT_SUPPORTED"
    assert payload["owningWorkflow"] == "integrations"
    assert {
        (action["action"], action["reasonCode"]) for action in payload["allowedActions"]
    } == {
        ("READ_ONLY_DIAGNOSTIC", "EVIDENCE_AVAILABLE"),
        ("HARD_EXCLUDED", "ACTION_NOT_SUPPORTED"),
    }
