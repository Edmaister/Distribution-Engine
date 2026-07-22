from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest

from services import referral_saas_campaign_service as svc

pytestmark = pytest.mark.asyncio


class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeCommandConnection:
    def __init__(self, fetchrow_results):
        self.fetchrow_results = list(fetchrow_results)
        self.fetchrow_calls = []

    async def fetchrow(self, query, *args):
        self.fetchrow_calls.append((query, args))
        if not self.fetchrow_results:
            raise AssertionError(f"Unexpected fetchrow call: {query}")
        return self.fetchrow_results.pop(0)

    def transaction(self):
        return FakeTransaction()


def patch_db(monkeypatch, connection):
    @asynccontextmanager
    async def fake_db_connection():
        yield connection

    monkeypatch.setattr(svc, "db_connection", fake_db_connection)


async def test_campaign_setup_create_records_inactive_campaign_and_audit(monkeypatch):
    conn = FakeCommandConnection(
        [
            None,
            None,
            {
                "campaign_code": "FNB-RETAIL-SUMMER-1234",
                "name": "Summer Referral",
                "segment": "Retail",
                "is_active": False,
                "starts_at": datetime(2026, 8, 1, tzinfo=timezone.utc),
                "ends_at": None,
                "max_uses": 100,
            },
            {"account_audit_event_id": "audit-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.create_referral_saas_account_campaign_setup(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
        name="Summer Referral",
        segment="Retail",
        starts_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        max_uses=100,
        reason_code="CUSTOMER_PROFILE_CAMPAIGN_SETUP",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "CAMPAIGN_SETUP_DRAFT_RECORDED"
    assert safe_payload["campaign"]["setupStatus"] == "DRAFT"
    assert safe_payload["campaign"]["isActive"] is False
    assert safe_payload["idempotency"]["status"] == "RECORDED"
    assert "NO_CAMPAIGN_ACTIVATION" in safe_payload["guardrails"]
    joined_queries = "\n".join(query for query, _ in conn.fetchrow_calls)
    assert "INSERT INTO marketing_campaigns" in joined_queries
    assert "FALSE" in joined_queries
    assert "INSERT INTO platform_account_audit_events" in joined_queries
    assert "tenant_code" in joined_queries


async def test_campaign_setup_create_replays_matching_idempotency(monkeypatch):
    conn = FakeCommandConnection(
        [
            {
                "account_audit_event_id": "audit-1",
                "event_status": "RECORDED",
                "evidence_summary": {
                    "campaign_code": "FNB-RETAIL-SUMMER-1234",
                    "name": "Summer Referral",
                    "segment": "Retail",
                    "setup_status": "DRAFT",
                    "is_active": False,
                    "command_payload_hash": "payload-hash",
                },
            }
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.create_referral_saas_account_campaign_setup(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
        name="Summer Referral",
        segment="Retail",
        reason_code="CUSTOMER_PROFILE_CAMPAIGN_SETUP",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "CAMPAIGN_SETUP_DRAFT_REPLAYED"
    assert safe_payload["campaign"]["campaignCode"] == "FNB-RETAIL-SUMMER-1234"
    assert safe_payload["idempotency"]["status"] == "REPLAYED"
    assert len(conn.fetchrow_calls) == 1


async def test_campaign_setup_create_conflicts_on_idempotency_payload_mismatch(
    monkeypatch,
):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                {
                    "account_audit_event_id": "audit-1",
                    "evidence_summary": {
                        "campaign_code": "FNB-RETAIL-SUMMER-1234",
                        "command_payload_hash": "original-hash",
                    },
                }
            ]
        ),
    )

    with pytest.raises(svc.CampaignSetupIdempotencyConflict):
        await svc.create_referral_saas_account_campaign_setup(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            external_reference_status="ACTIVE",
            name="Summer Referral",
            segment="Retail",
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_SETUP",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="new-hash",
        )


async def test_campaign_setup_create_rejects_duplicate_campaign(monkeypatch):
    patch_db(
        monkeypatch,
        FakeCommandConnection([None, {"campaign_code": "FNB-EXISTING"}]),
    )

    with pytest.raises(svc.CampaignSetupDuplicate):
        await svc.create_referral_saas_account_campaign_setup(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            external_reference_status="ACTIVE",
            name="Summer Referral",
            segment="Retail",
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_SETUP",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="payload-hash",
        )


async def test_campaign_policy_settings_records_active_policy_and_audit(monkeypatch):
    conn = FakeCommandConnection(
        [
            None,
            {"campaign_code": "CAMP001", "is_active": False},
            {
                "campaign_code": "CAMP001",
                "version": 1,
                "rolling_window_days": 30,
            },
            {"account_audit_event_id": "audit-policy-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.upsert_referral_saas_account_campaign_policy_settings(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
        campaign_code="CAMP001",
        version=1,
        attribution_window_days=30,
        eligibility_rules=[{"rule": "NEW_CUSTOMER_ONLY", "enabled": True}],
        product_windows={"default": {"days": 30}},
        product_rules={"default": {"requiresAcceptedTerms": True}},
        reward_visibility={"mode": "configured_without_payment"},
        reason_code="CUSTOMER_PROFILE_CAMPAIGN_POLICY_SETTINGS",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "POLICY_SETTINGS_RECORDED"
    assert safe_payload["policySettings"]["setupStatus"] == "POLICY_SETTINGS_RECORDED"
    assert safe_payload["policySettings"]["attributionWindowDays"] == 30
    assert safe_payload["policySettings"]["eligibilityRuleCount"] == 1
    assert safe_payload["policySettings"]["productWindowCount"] == 1
    assert safe_payload["policySettings"]["productRuleCount"] == 1
    assert (
        safe_payload["policySettings"]["rewardVisibilityStatus"]
        == "CONFIGURED_WITHOUT_PAYMENT"
    )
    assert "NO_CAMPAIGN_ACTIVATION" in safe_payload["guardrails"]
    joined_queries = "\n".join(query for query, _ in conn.fetchrow_calls)
    assert "INSERT INTO marketing_campaign_policies" in joined_queries
    assert "is_active = TRUE" in joined_queries
    assert "INSERT INTO platform_account_audit_events" in joined_queries
    assert "tenant_code" in joined_queries


async def test_campaign_policy_settings_replays_matching_idempotency(monkeypatch):
    conn = FakeCommandConnection(
        [
            {
                "account_audit_event_id": "audit-policy-1",
                "event_status": "RECORDED",
                "evidence_summary": {
                    "campaign_code": "CAMP001",
                    "version": 1,
                    "setup_status": "POLICY_SETTINGS_RECORDED",
                    "attribution_window_days": 30,
                    "eligibility_rule_count": 1,
                    "product_window_count": 1,
                    "product_rule_count": 1,
                    "reward_visibility_status": "CONFIGURED_WITHOUT_PAYMENT",
                    "command_payload_hash": "payload-hash",
                },
            }
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.upsert_referral_saas_account_campaign_policy_settings(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
        campaign_code="CAMP001",
        version=1,
        attribution_window_days=30,
        eligibility_rules=[{"rule": "NEW_CUSTOMER_ONLY", "enabled": True}],
        reward_visibility={"mode": "configured_without_payment"},
        reason_code="CUSTOMER_PROFILE_CAMPAIGN_POLICY_SETTINGS",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
    )

    assert result.command_status == "POLICY_SETTINGS_REPLAYED"
    assert result.idempotency_status == "REPLAYED"
    assert len(conn.fetchrow_calls) == 1


async def test_campaign_policy_settings_conflicts_on_idempotency_payload_mismatch(
    monkeypatch,
):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                {
                    "account_audit_event_id": "audit-policy-1",
                    "evidence_summary": {
                        "campaign_code": "CAMP001",
                        "command_payload_hash": "original-hash",
                    },
                }
            ]
        ),
    )

    with pytest.raises(svc.CampaignPolicySettingsIdempotencyConflict):
        await svc.upsert_referral_saas_account_campaign_policy_settings(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            external_reference_status="ACTIVE",
            campaign_code="CAMP001",
            version=1,
            attribution_window_days=30,
            reward_visibility={"mode": "configured_without_payment"},
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_POLICY_SETTINGS",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="new-hash",
        )


async def test_campaign_policy_settings_rejects_missing_campaign(monkeypatch):
    patch_db(monkeypatch, FakeCommandConnection([None, None]))

    with pytest.raises(svc.CampaignPolicySettingsCampaignNotFound):
        await svc.upsert_referral_saas_account_campaign_policy_settings(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            external_reference_status="ACTIVE",
            campaign_code="CAMP404",
            version=1,
            attribution_window_days=30,
            reward_visibility={"mode": "configured_without_payment"},
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_POLICY_SETTINGS",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="payload-hash",
        )


async def test_campaign_policy_settings_rejects_payment_reward_visibility():
    with pytest.raises(svc.CampaignPolicySettingsValidationError):
        await svc.upsert_referral_saas_account_campaign_policy_settings(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            external_reference_status="ACTIVE",
            campaign_code="CAMP001",
            version=1,
            attribution_window_days=30,
            reward_visibility={"mode": "pay_now"},
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_POLICY_SETTINGS",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="payload-hash",
        )


async def test_campaign_review_submit_records_review_state_and_audit(monkeypatch):
    conn = FakeCommandConnection(
        [
            None,
            {"campaign_code": "CAMP001", "is_active": False, "attributes": {}},
            {"active_policy_count": 1},
            {
                "campaign_code": "CAMP001",
                "is_active": False,
                "attributes": {
                    "referral_saas_review": {
                        "review_status": "READY_FOR_REVIEW"
                    }
                },
            },
            {"account_audit_event_id": "audit-review-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.submit_referral_saas_account_campaign_review(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        campaign_code="CAMP001",
        setup_summary="Policy settings ready for review.",
        requested_review_status="READY_FOR_REVIEW",
        reason_code="CUSTOMER_PROFILE_CAMPAIGN_REVIEW_SUBMIT",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "CAMPAIGN_REVIEW_SUBMITTED"
    assert safe_payload["campaignReview"]["reviewStatus"] == "READY_FOR_REVIEW"
    assert safe_payload["campaignReview"]["activationStatus"] == "NOT_ACTIVATED"
    assert "NO_CAMPAIGN_ACTIVATION" in safe_payload["guardrails"]
    joined_queries = "\n".join(query for query, _ in conn.fetchrow_calls)
    assert "marketing_campaign_policies" in joined_queries
    assert "UPDATE marketing_campaigns" in joined_queries
    assert "INSERT INTO platform_account_audit_events" in joined_queries


async def test_campaign_review_submit_requires_policy_evidence(monkeypatch):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                None,
                {"campaign_code": "CAMP001", "is_active": False, "attributes": {}},
                {"active_policy_count": 0},
            ]
        ),
    )

    with pytest.raises(svc.CampaignReviewNotReady):
        await svc.submit_referral_saas_account_campaign_review(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            campaign_code="CAMP001",
            setup_summary="Policy settings ready for review.",
            requested_review_status="READY_FOR_REVIEW",
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_REVIEW_SUBMIT",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="payload-hash",
        )


async def test_campaign_review_submit_replays_matching_idempotency(monkeypatch):
    conn = FakeCommandConnection(
        [
            {
                "account_audit_event_id": "audit-review-1",
                "event_status": "RECORDED",
                "evidence_summary": {
                    "campaign_code": "CAMP001",
                    "review_status": "READY_FOR_REVIEW",
                    "setup_status": "POLICY_SETTINGS_RECORDED",
                    "readiness_status": "NEEDS_REVIEW",
                    "command_payload_hash": "payload-hash",
                },
            }
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.submit_referral_saas_account_campaign_review(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        campaign_code="CAMP001",
        setup_summary="Policy settings ready for review.",
        requested_review_status="READY_FOR_REVIEW",
        reason_code="CUSTOMER_PROFILE_CAMPAIGN_REVIEW_SUBMIT",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
    )

    assert result.command_status == "CAMPAIGN_REVIEW_SUBMISSION_REPLAYED"
    assert result.idempotency_status == "REPLAYED"
    assert len(conn.fetchrow_calls) == 1


async def test_campaign_review_submit_conflicts_on_idempotency_payload_mismatch(
    monkeypatch,
):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                {
                    "account_audit_event_id": "audit-review-1",
                    "evidence_summary": {
                        "campaign_code": "CAMP001",
                        "command_payload_hash": "original-hash",
                    },
                }
            ]
        ),
    )

    with pytest.raises(svc.CampaignReviewIdempotencyConflict):
        await svc.submit_referral_saas_account_campaign_review(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            campaign_code="CAMP001",
            setup_summary="Policy settings ready for review.",
            requested_review_status="READY_FOR_REVIEW",
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_REVIEW_SUBMIT",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="new-hash",
        )


async def test_campaign_review_decision_records_approval_without_activation(monkeypatch):
    conn = FakeCommandConnection(
        [
            None,
            {
                "campaign_code": "CAMP001",
                "is_active": False,
                "attributes": {
                    "referral_saas_review": {
                        "review_status": "READY_FOR_REVIEW"
                    }
                },
            },
            {
                "campaign_code": "CAMP001",
                "is_active": False,
                "attributes": {
                    "referral_saas_review": {
                        "review_status": "REVIEW_APPROVED"
                    }
                },
            },
            {"account_audit_event_id": "audit-review-decision-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.record_referral_saas_account_campaign_review_decision(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        campaign_code="CAMP001",
        decision="APPROVED",
        reason="Reviewed campaign setup evidence.",
        reviewer_ref="reviewer-1",
        reason_code="CUSTOMER_PROFILE_CAMPAIGN_REVIEW_DECISION",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "CAMPAIGN_REVIEW_APPROVED"
    assert safe_payload["campaignReview"]["reviewStatus"] == "REVIEW_APPROVED"
    assert (
        safe_payload["campaignReview"]["activationEligibility"]
        == "ELIGIBLE_FOR_FUTURE_ACTIVATION"
    )
    assert safe_payload["campaignReview"]["activationStatus"] == "NOT_ACTIVATED"
    joined_queries = "\n".join(query for query, _ in conn.fetchrow_calls)
    assert "UPDATE marketing_campaigns" in joined_queries
    assert "INSERT INTO platform_account_audit_events" in joined_queries


async def test_campaign_review_decision_requires_review_submission(monkeypatch):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                None,
                {"campaign_code": "CAMP001", "is_active": False, "attributes": {}},
            ]
        ),
    )

    with pytest.raises(svc.CampaignReviewInvalidState):
        await svc.record_referral_saas_account_campaign_review_decision(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            campaign_code="CAMP001",
            decision="APPROVED",
            reason="Reviewed campaign setup evidence.",
            reviewer_ref="reviewer-1",
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_REVIEW_DECISION",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="payload-hash",
        )

