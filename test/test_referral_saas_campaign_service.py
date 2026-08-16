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


class FakeReadConnection:
    def __init__(self, fetch_results):
        self.fetch_results = list(fetch_results)
        self.fetch_calls = []

    async def fetch(self, query, *args):
        self.fetch_calls.append((query, args))
        if not self.fetch_results:
            raise AssertionError(f"Unexpected fetch call: {query}")
        return self.fetch_results.pop(0)


def patch_db(monkeypatch, connection):
    @asynccontextmanager
    async def fake_db_connection():
        yield connection

    monkeypatch.setattr(svc, "db_connection", fake_db_connection)


def _allowed_production_activation_decision():
    return {
        "decisionStatus": "PRODUCTION_ACTIVATION_ALLOWED",
        "launchAllowed": True,
        "disabledReasons": [],
        "guardrails": ["BACKEND_PRODUCTION_ACTIVATION_DECISION_REQUIRED"],
        "noUiOnlyActivationConfirmed": True,
        "noCampaignActivationConfirmed": True,
        "noGoLiveActionConfirmed": True,
        "noBillingOrMoneyMovementConfirmed": True,
    }


def _approved_review_state() -> dict[str, object]:
    return {
        "review_status": "REVIEW_APPROVED",
        "activation_eligibility": "ELIGIBLE_FOR_FUTURE_ACTIVATION",
        "sod_status": svc.CAMPAIGN_REVIEW_SOD_CONFIRMED,
        "submitted_by_ref": "submitter-1",
        "decision_by_ref": "reviewer-1",
        "decision_at": datetime(2026, 8, 1, tzinfo=timezone.utc).isoformat(),
        "review_decision_payload_hash": "decision-payload-hash",
        "policy_evidence_status": svc.CAMPAIGN_POLICY_EVIDENCE_CURRENT,
        "policy_evidence_updated_at": datetime(
            2026, 7, 31, tzinfo=timezone.utc
        ).isoformat(),
    }


def _published_journey_binding_row() -> dict[str, object]:
    return {
        "campaign_journey_binding_id": "binding-1",
        "customer_journey_version_id": "journey-version-1",
        "binding_status": "ACTIVE",
        "customer_journey_code": "customer-journey",
        "version_number": 1,
        "version_status": "PUBLISHED",
        "archived_at": None,
    }


def _published_programme_binding() -> dict[str, object]:
    return {
        "programmeVersionId": "programme-version-1",
        "programmeCode": "PROGRAMME-1",
        "programmeName": "Programme 1",
        "versionNumber": 1,
        "versionStatus": "PUBLISHED",
        "customerJourneyVersionId": "journey-version-1",
        "source": "PUBLISHED_PROGRAMME_VERSION",
    }


def _published_programme_version_row() -> dict[str, object]:
    return {
        "programme_version_id": "programme-version-1",
        "account_id": "acct-1",
        "programme_code": "PROGRAMME-1",
        "programme_name": "Programme 1",
        "version_number": 1,
        "version_status": "PUBLISHED",
        "customer_journey_version_id": "journey-version-1",
        "effective_from": None,
        "effective_to": None,
        "retired_at": None,
    }


async def test_campaign_attribution_projection_builds_high_confidence_summary(
    monkeypatch,
):
    conn = FakeReadConnection(
        [
            [
                {
                    "campaign_code": "SUMMER-2026",
                    "campaign_name": "Summer referral",
                    "segment": "Retail",
                    "campaign_status": "ACTIVE",
                    "source_channel": "EMAIL",
                    "interaction_count": 4,
                    "validated_count": 1,
                    "attributed_count": 2,
                    "completed_count": 1,
                    "conflict_count": 0,
                    "linked_referral_count": 3,
                    "event_count": 5,
                    "first_seen_at": datetime(2026, 8, 1, tzinfo=timezone.utc),
                    "last_seen_at": datetime(2026, 8, 2, tzinfo=timezone.utc),
                    "status_values": ["VALIDATED", "ATTRIBUTED", "COMPLETED"],
                }
            ]
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.build_referral_saas_account_campaign_attribution_projection(
        tenant_code="FNB",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["status"] == "READY"
    assert safe_payload["campaignCount"] == 1
    assert safe_payload["sourceCount"] == 1
    assert safe_payload["totalInteractions"] == 4
    assert safe_payload["highConfidenceCount"] == 1
    assert safe_payload["projections"][0]["confidence"] == "HIGH"
    assert safe_payload["projections"][0]["attributionStatus"] == "ATTRIBUTED"
    assert "tenant_code" not in safe_payload["projections"][0]
    assert conn.fetch_calls[0][1] == ("FNB", 50)


async def test_campaign_attribution_projection_marks_missing_evidence(monkeypatch):
    conn = FakeReadConnection(
        [
            [
                {
                    "campaign_code": "EMPTY-2026",
                    "campaign_name": "Empty campaign",
                    "segment": "Retail",
                    "campaign_status": "DRAFT",
                    "source_channel": "Unknown source",
                    "interaction_count": 0,
                    "validated_count": 0,
                    "attributed_count": 0,
                    "completed_count": 0,
                    "conflict_count": 0,
                    "linked_referral_count": 0,
                    "event_count": 0,
                    "first_seen_at": None,
                    "last_seen_at": None,
                    "status_values": [],
                }
            ]
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.build_referral_saas_account_campaign_attribution_projection(
        tenant_code="FNB",
    )

    projection = result.to_safe_dict()["projections"][0]
    assert result.status == "NO_ATTRIBUTION_EVIDENCE"
    assert projection["confidence"] == "MISSING"
    assert projection["attributionStatus"] == "MISSING_EVIDENCE"
    assert "No campaign interactions found." in projection["gaps"]


async def test_campaign_attribution_projection_marks_conflicting_evidence(
    monkeypatch,
):
    conn = FakeReadConnection(
        [
            [
                {
                    "campaign_code": "BLOCKED-2026",
                    "campaign_name": "Blocked campaign",
                    "segment": "Retail",
                    "campaign_status": "ACTIVE",
                    "source_channel": "QR",
                    "interaction_count": 1,
                    "validated_count": 0,
                    "attributed_count": 0,
                    "completed_count": 0,
                    "conflict_count": 1,
                    "linked_referral_count": 0,
                    "event_count": 1,
                    "first_seen_at": datetime(2026, 8, 1, tzinfo=timezone.utc),
                    "last_seen_at": datetime(2026, 8, 1, tzinfo=timezone.utc),
                    "status_values": ["BLOCKED"],
                }
            ]
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.build_referral_saas_account_campaign_attribution_projection(
        tenant_code="FNB",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["status"] == "REVIEW_REQUIRED"
    assert safe_payload["conflictCount"] == 1
    assert safe_payload["projections"][0]["confidence"] == "CONFLICT"
    assert "blocked or invalid" in safe_payload["projections"][0]["explanation"]


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
            {
                "active_policy_count": 1,
                "latest_policy_updated_at": datetime(
                    2026, 8, 1, tzinfo=timezone.utc
                ),
            },
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
                        "review_status": "READY_FOR_REVIEW",
                        "submitted_by_ref": "operator-1",
                    },
                    "referral_saas_programme_binding": _published_programme_binding(),
                },
            },
            _published_programme_version_row(),
            {
                "active_policy_count": 1,
                "latest_policy_updated_at": datetime(
                    2026, 8, 1, tzinfo=timezone.utc
                ),
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
        command_actor_ref="reviewer-1",
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


async def test_campaign_review_decision_blocks_same_submitter_and_approver(
    monkeypatch,
):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                None,
                {
                    "campaign_code": "CAMP001",
                    "is_active": False,
                    "attributes": {
                        "referral_saas_review": {
                            "review_status": "READY_FOR_REVIEW",
                            "submitted_by_ref": "operator-1",
                        }
                    },
                },
            ]
        ),
    )

    with pytest.raises(svc.CampaignReviewInvalidState) as exc_info:
        await svc.record_referral_saas_account_campaign_review_decision(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            campaign_code="CAMP001",
            decision="APPROVED",
            reason="Reviewed campaign setup evidence.",
            reviewer_ref="operator-1",
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_REVIEW_DECISION",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="payload-hash",
            command_actor_ref="operator-1",
            command_actor_role="ADMIN",
        )

    assert "separation of duties" in str(exc_info.value)


async def test_campaign_activation_request_activates_only_campaign_posture(
    monkeypatch,
):
    conn = FakeCommandConnection(
        [
            None,
            {
                "campaign_code": "CAMP001",
                "is_active": False,
                "starts_at": None,
                "ends_at": None,
                "attributes": {
                    "referral_saas_review": {
                        "review_status": "REVIEW_APPROVED",
                        **_approved_review_state(),
                    },
                    "referral_saas_programme_binding": _published_programme_binding(),
                },
            },
            _published_journey_binding_row(),
            {
                "active_policy_count": 1,
                "latest_policy_updated_at": datetime(
                    2026, 7, 31, tzinfo=timezone.utc
                ),
            },
            _published_programme_version_row(),
            {
                "campaign_code": "CAMP001",
                "is_active": True,
                "starts_at": None,
                "ends_at": None,
                "attributes": {
                    "referral_saas_review": {
                        "review_status": "REVIEW_APPROVED",
                        **_approved_review_state(),
                        "activation_status": "ACTIVATION_REQUEST_ACCEPTED",
                    }
                },
            },
            {"account_audit_event_id": "audit-activation-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.request_referral_saas_account_campaign_activation(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        campaign_code="CAMP001",
        requested_lifecycle_status="ACTIVE",
        review_status="REVIEW_APPROVED",
        go_live_reason="Approved for referral campaign testing.",
        reason_code="CUSTOMER_PROFILE_CAMPAIGN_ACTIVATION",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
        production_activation_decision=_allowed_production_activation_decision(),
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "CAMPAIGN_ACTIVATION_ACCEPTED"
    assert safe_payload["campaignActivation"]["lifecycle"] == "ACTIVE"
    assert (
        safe_payload["campaignActivation"]["activationStatus"]
        == "ACTIVATION_REQUEST_ACCEPTED"
    )
    assert (
        safe_payload["campaignActivation"]["preActivationDecision"]["sodStatus"]
        == svc.CAMPAIGN_REVIEW_SOD_CONFIRMED
    )
    assert "NO_LINK_GENERATION" in safe_payload["guardrails"]
    assert "NO_WEBHOOK_DELIVERY" in safe_payload["guardrails"]
    assert "NO_BILLING_OR_MONEY_MOVEMENT" in safe_payload["guardrails"]
    joined_queries = "\n".join(query for query, _ in conn.fetchrow_calls)
    assert "UPDATE marketing_campaigns" in joined_queries
    assert "SET is_active = TRUE" in joined_queries
    assert "INSERT INTO platform_account_audit_events" in joined_queries


async def test_campaign_activation_requires_production_activation_decision(monkeypatch):
    conn = FakeCommandConnection([])
    patch_db(monkeypatch, conn)

    with pytest.raises(svc.CampaignActivationNotReady) as exc_info:
        await svc.request_referral_saas_account_campaign_activation(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            campaign_code="CAMP001",
            requested_lifecycle_status="ACTIVE",
            review_status="REVIEW_APPROVED",
            go_live_reason="Approved for referral campaign testing.",
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_ACTIVATION",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="payload-hash",
        )

    assert "Production activation decision evidence is required" in str(exc_info.value)
    assert conn.fetchrow_calls == []


async def test_campaign_activation_blocks_failed_production_activation_decision(monkeypatch):
    conn = FakeCommandConnection([])
    patch_db(monkeypatch, conn)

    with pytest.raises(svc.CampaignActivationNotReady) as exc_info:
        await svc.request_referral_saas_account_campaign_activation(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            campaign_code="CAMP001",
            requested_lifecycle_status="ACTIVE",
            review_status="REVIEW_APPROVED",
            go_live_reason="Approved for referral campaign testing.",
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_ACTIVATION",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="payload-hash",
            production_activation_decision={
                "decisionStatus": "PRODUCTION_ACTIVATION_BLOCKED",
                "launchAllowed": False,
                "disabledReasons": ["COMMERCIAL_ENTITLEMENT", "EVIDENCE_FRESHNESS"],
            },
        )

    assert "COMMERCIAL_ENTITLEMENT" in str(exc_info.value)
    assert "EVIDENCE_FRESHNESS" in str(exc_info.value)
    assert conn.fetchrow_calls == []


async def test_campaign_activation_requires_review_approval(monkeypatch):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                None,
                {
                    "campaign_code": "CAMP001",
                    "is_active": False,
                    "starts_at": None,
                    "ends_at": None,
                    "attributes": {
                        "referral_saas_review": {
                            "review_status": "READY_FOR_REVIEW",
                            "activation_eligibility": (
                                "NOT_ELIGIBLE_UNTIL_REVIEW_APPROVED"
                            ),
                        }
                    },
                },
                _published_journey_binding_row(),
                {
                    "active_policy_count": 1,
                    "latest_policy_updated_at": datetime(
                        2026, 7, 31, tzinfo=timezone.utc
                    ),
                },
            ]
        ),
    )

    with pytest.raises(svc.CampaignActivationNotReady):
        await svc.request_referral_saas_account_campaign_activation(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            campaign_code="CAMP001",
            requested_lifecycle_status="ACTIVE",
            review_status="REVIEW_APPROVED",
            go_live_reason="Approved for referral campaign testing.",
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_ACTIVATION",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="payload-hash",
        )


async def test_campaign_activation_blocks_stale_policy_after_review(monkeypatch):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                None,
                {
                    "campaign_code": "CAMP001",
                    "is_active": False,
                    "starts_at": None,
                    "ends_at": None,
                    "attributes": {
                        "referral_saas_review": _approved_review_state(),
                    },
                },
                _published_journey_binding_row(),
                {
                    "active_policy_count": 1,
                    "latest_policy_updated_at": datetime(
                        2026, 8, 2, tzinfo=timezone.utc
                    ),
                },
            ]
        ),
    )

    with pytest.raises(svc.CampaignActivationNotReady) as exc_info:
        await svc.request_referral_saas_account_campaign_activation(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            campaign_code="CAMP001",
            requested_lifecycle_status="ACTIVE",
            review_status="REVIEW_APPROVED",
            go_live_reason="Approved for referral campaign testing.",
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_ACTIVATION",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="payload-hash",
            production_activation_decision=_allowed_production_activation_decision(),
        )

    assert "changed after review approval" in str(exc_info.value)


async def test_campaign_activation_requires_published_journey_binding(monkeypatch):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                None,
                {
                    "campaign_code": "CAMP001",
                    "is_active": False,
                    "starts_at": None,
                    "ends_at": None,
                    "attributes": {
                        "referral_saas_review": _approved_review_state(),
                    },
                },
                None,
            ]
        ),
    )

    with pytest.raises(svc.CampaignActivationNotReady) as exc_info:
        await svc.request_referral_saas_account_campaign_activation(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            campaign_code="CAMP001",
            requested_lifecycle_status="ACTIVE",
            review_status="REVIEW_APPROVED",
            go_live_reason="Approved for referral campaign testing.",
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_ACTIVATION",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="payload-hash",
            production_activation_decision=_allowed_production_activation_decision(),
        )

    assert "published customer journey version" in str(exc_info.value)


async def test_campaign_activation_replays_matching_idempotency(monkeypatch):
    conn = FakeCommandConnection(
        [
            {
                "account_audit_event_id": "audit-activation-1",
                "event_status": "RECORDED",
                "evidence_summary": {
                    "campaign_code": "CAMP001",
                    "previous_lifecycle": "READY_TO_ACTIVATE",
                    "lifecycle": "ACTIVE",
                    "review_status": "REVIEW_APPROVED",
                    "activation_eligibility": "ELIGIBLE_FOR_FUTURE_ACTIVATION",
                    "activation_status": "ACTIVATION_REQUEST_ACCEPTED",
                    "readiness_status": "READY_TO_ACTIVATE",
                    "command_payload_hash": "payload-hash",
                },
            }
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.request_referral_saas_account_campaign_activation(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        campaign_code="CAMP001",
        requested_lifecycle_status="ACTIVE",
        review_status="REVIEW_APPROVED",
        go_live_reason="Approved for referral campaign testing.",
        reason_code="CUSTOMER_PROFILE_CAMPAIGN_ACTIVATION",
        correlation_id="corr-1",
        idempotency_key_hash="idem-hash",
        command_payload_hash="payload-hash",
        production_activation_decision=_allowed_production_activation_decision(),
    )

    assert result.command_status == "CAMPAIGN_ACTIVATION_REPLAYED"
    assert result.idempotency_status == "REPLAYED"
    assert len(conn.fetchrow_calls) == 1


async def test_campaign_activation_conflicts_on_idempotency_payload_mismatch(
    monkeypatch,
):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                {
                    "account_audit_event_id": "audit-activation-1",
                    "evidence_summary": {
                        "campaign_code": "CAMP001",
                        "command_payload_hash": "original-hash",
                    },
                }
            ]
        ),
    )

    with pytest.raises(svc.CampaignActivationIdempotencyConflict):
        await svc.request_referral_saas_account_campaign_activation(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            campaign_code="CAMP001",
            requested_lifecycle_status="ACTIVE",
            review_status="REVIEW_APPROVED",
            go_live_reason="Approved for referral campaign testing.",
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_ACTIVATION",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="new-hash",
            production_activation_decision=_allowed_production_activation_decision(),
        )


async def test_campaign_activation_rejects_already_active(monkeypatch):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                None,
                {
                    "campaign_code": "CAMP001",
                    "is_active": True,
                    "starts_at": None,
                    "ends_at": None,
                    "attributes": {},
                },
            ]
        ),
    )

    with pytest.raises(svc.CampaignActivationAlreadyActive):
        await svc.request_referral_saas_account_campaign_activation(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            campaign_code="CAMP001",
            requested_lifecycle_status="ACTIVE",
            review_status="REVIEW_APPROVED",
            go_live_reason="Approved for referral campaign testing.",
            reason_code="CUSTOMER_PROFILE_CAMPAIGN_ACTIVATION",
            correlation_id="corr-1",
            idempotency_key_hash="idem-hash",
            command_payload_hash="payload-hash",
            production_activation_decision=_allowed_production_activation_decision(),
        )


async def test_campaign_lifecycle_command_pauses_active_campaign_with_audit(monkeypatch):
    conn = FakeCommandConnection(
        [
            None,
            {
                "campaign_code": "CAMP001",
                "is_active": True,
                "starts_at": None,
                "ends_at": None,
                "attributes": {
                    "referral_saas_lifecycle": {
                        "lifecycle": "ACTIVE",
                        "action": "ACTIVATE",
                    }
                },
            },
            {
                "campaign_code": "CAMP001",
                "is_active": False,
            },
            {"account_audit_event_id": "audit-lifecycle-1"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.record_referral_saas_account_campaign_lifecycle_command(
        account_id="acct-1",
        tenant_code="FNB",
        account_tenant_id="acct-tenant-1",
        external_ref_id="external-ref-1",
        campaign_code="CAMP001",
        action="PAUSE",
        reason="Pause while compliance content is updated.",
        operator_notes="Operator note",
        reason_code="CUSTOMER_PROFILE_CAMPAIGN_LIFECYCLE",
        correlation_id="corr-lifecycle-1",
        idempotency_key_hash="idem-lifecycle-hash",
        command_payload_hash="payload-lifecycle-hash",
        command_actor_ref="operator-1",
        command_actor_role="ADMIN",
    )

    safe_payload = result.to_safe_dict()
    assert safe_payload["commandStatus"] == "CAMPAIGN_LIFECYCLE_RECORDED"
    assert safe_payload["campaignLifecycle"]["previousLifecycle"] == "ACTIVE"
    assert safe_payload["campaignLifecycle"]["lifecycle"] == "PAUSED"
    assert safe_payload["campaignLifecycle"]["isActive"] is False
    assert "RESUME" in safe_payload["campaignLifecycle"]["allowedActions"]
    assert "NO_LINK_GENERATION" in safe_payload["guardrails"]
    assert "NO_WEBHOOK_DELIVERY" in safe_payload["guardrails"]
    assert "NO_BILLING_OR_MONEY_MOVEMENT" in safe_payload["guardrails"]
    joined_queries = "\n".join(query for query, _ in conn.fetchrow_calls)
    assert "UPDATE marketing_campaigns" in joined_queries
    assert "SET is_active = $3" in joined_queries
    assert "INSERT INTO platform_account_audit_events" in joined_queries


async def test_campaign_lifecycle_command_blocks_invalid_transition(monkeypatch):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                None,
                {
                    "campaign_code": "CAMP001",
                    "is_active": False,
                    "starts_at": None,
                    "ends_at": None,
                    "attributes": {
                        "referral_saas_lifecycle": {
                            "lifecycle": "ARCHIVED",
                            "action": "ARCHIVE",
                        }
                    },
                },
            ]
        ),
    )

    with pytest.raises(svc.CampaignLifecycleInvalidTransition) as exc_info:
        await svc.record_referral_saas_account_campaign_lifecycle_command(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            campaign_code="CAMP001",
            action="RESUME",
            reason="Resume after accidental archive.",
            correlation_id="corr-lifecycle-1",
            idempotency_key_hash="idem-lifecycle-hash",
            command_payload_hash="payload-lifecycle-hash",
        )

    assert "Cannot resume a campaign while lifecycle is ARCHIVED" in str(
        exc_info.value
    )


async def test_campaign_lifecycle_command_conflicts_on_idempotency_payload_mismatch(
    monkeypatch,
):
    patch_db(
        monkeypatch,
        FakeCommandConnection(
            [
                {
                    "account_audit_event_id": "audit-lifecycle-1",
                    "evidence_summary": {
                        "campaign_code": "CAMP001",
                        "action": "PAUSE",
                        "lifecycle": "PAUSED",
                        "command_payload_hash": "original-payload-hash",
                    },
                }
            ]
        ),
    )

    with pytest.raises(svc.CampaignLifecycleIdempotencyConflict):
        await svc.record_referral_saas_account_campaign_lifecycle_command(
            account_id="acct-1",
            tenant_code="FNB",
            account_tenant_id="acct-tenant-1",
            external_ref_id="external-ref-1",
            campaign_code="CAMP001",
            action="PAUSE",
            reason="Pause while compliance content is updated.",
            correlation_id="corr-lifecycle-1",
            idempotency_key_hash="idem-lifecycle-hash",
            command_payload_hash="changed-payload-hash",
        )

