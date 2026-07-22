from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT
    / "docs"
    / "sa"
    / "referral-saas"
    / "REFERRAL_SAAS_CUSTOMER_CAMPAIGN_SUBMIT_REVIEW_CONTRACT.md"
)


def _contract() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def test_customer_campaign_submit_review_contract_is_referral_saas_scoped() -> None:
    contract = _contract()

    assert "TASK ID: TASK-261" in contract
    assert "Product boundary: Referral SaaS." in contract
    assert "Status: Command-boundary contract only." in contract
    assert "source-code forks" in contract


def test_customer_campaign_submit_review_contract_uses_real_sources() -> None:
    contract = _contract()

    for source in (
        "dp/migrations/002_campaigns.sql",
        "dp/migrations/082_referral_saas_account_foundation.sql",
        "services/campaign_service.py",
        "services/campaign_policy_service.py",
        "services/campaign_readiness_service.py",
        "services/referral_saas_campaign_service.py",
        "apps/api/routers/campaigns.py",
        "apps/api/routers/referral_saas_accounts.py",
        "apps/api/schemas/campaigns.py",
        "services/onboarding/onboarding_submit_for_review_service.py",
        "services/onboarding/onboarding_review_decision_service.py",
    ):
        assert source in contract

    for table_or_field in (
        "marketing_campaigns",
        "marketing_campaign_policies",
        "platform_account_audit_events",
        "campaign_code",
        "tenant_code",
        "is_active",
        "event_status",
        "idempotency_key_hash",
        "payload_hash",
    ):
        assert table_or_field in contract


def test_customer_campaign_submit_review_contract_defines_review_commands() -> None:
    contract = _contract()

    assert (
        "POST /v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/review-submissions"
        in contract
    )
    assert (
        "POST /v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/review-decisions"
        in contract
    )
    assert "accountScope" in contract
    assert "reviewSubmission" in contract
    assert "reviewDecision" in contract
    assert "idempotencyKey" in contract
    assert "correlationId" in contract


def test_customer_campaign_submit_review_contract_defines_status_vocabulary() -> None:
    contract = _contract()

    for status in (
        "NEEDS_REVIEW_SUBMISSION",
        "READY_FOR_REVIEW",
        "REVIEW_APPROVED",
        "REVIEW_BLOCKED",
        "READY_TO_ACTIVATE",
        "ACTIVE",
        "CAMPAIGN_REVIEW_SUBMITTED",
        "CAMPAIGN_REVIEW_APPROVED",
    ):
        assert status in contract


def test_customer_campaign_submit_review_contract_preserves_guardrails() -> None:
    contract = _contract()

    for guardrail in (
        "NO_TENANT_CODE_EXPOSURE",
        "NO_CAMPAIGN_ACTIVATION",
        "NO_LINK_GENERATION",
        "NO_VALIDATION_TRACK_CREATED",
        "NO_WEBHOOK_DELIVERY",
        "NO_INVITE_OR_SEAT_CHANGE",
        "NO_MONEY_MOVEMENT",
    ):
        assert guardrail in contract

    for redaction in (
        "internal_tenant_identifier",
        "idempotency_key_hash",
        "payload_hash",
    ):
        assert redaction in contract


def test_customer_campaign_submit_review_contract_keeps_activation_out_of_scope() -> None:
    contract = _contract()

    for phrase in (
        "backend routes",
        "schema or migrations",
        "runtime campaign review writes",
        "frontend screens",
        "campaign activation",
        "campaign validation or `campaign_track_id` creation",
        "link/code generation",
        "webhook delivery",
        "billing",
        "rewards payment",
        "funding",
        "fulfilment",
        "settlement",
        "broad DLaaS marketplace behavior",
    ):
        assert phrase in contract
