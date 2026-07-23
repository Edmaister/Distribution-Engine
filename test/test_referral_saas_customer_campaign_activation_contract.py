from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT
    / "docs"
    / "sa"
    / "referral-saas"
    / "REFERRAL_SAAS_CUSTOMER_CAMPAIGN_ACTIVATION_CONTRACT.md"
)


def _contract() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def test_customer_campaign_activation_contract_is_referral_saas_scoped() -> None:
    contract = _contract()

    assert "TASK ID: TASK-264" in contract
    assert "Product boundary: Referral SaaS." in contract
    assert "Status: Command-boundary contract only." in contract
    assert "source-code forks" in contract


def test_customer_campaign_activation_contract_uses_real_sources() -> None:
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
        "test/test_referral_saas_campaign_service.py",
    ):
        assert source in contract

    for table_or_field in (
        "marketing_campaigns",
        "marketing_campaign_policies",
        "platform_account_audit_events",
        "campaign_code",
        "tenant_code",
        "is_active",
        "referral_saas_review",
        "idempotency_key_hash",
        "payload_hash",
    ):
        assert table_or_field in contract


def test_customer_campaign_activation_contract_defines_activation_command() -> None:
    contract = _contract()

    assert (
        "POST /v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/activation-requests"
        in contract
    )
    assert "accountScope" in contract
    assert "activationRequest" in contract
    assert "requestedLifecycleStatus" in contract
    assert "goLiveReason" in contract
    assert "idempotencyKey" in contract
    assert "correlationId" in contract


def test_customer_campaign_activation_contract_requires_review_and_readiness() -> None:
    contract = _contract()

    for precondition in (
        "Validate campaign policy/settings evidence exists.",
        "Validate campaign review evidence exists and is `REVIEW_APPROVED`.",
        "ELIGIBLE_FOR_FUTURE_ACTIVATION",
        "Validate readiness evidence is sufficient for activation and is not blocked.",
        "CAMPAIGN_REVIEW_NOT_APPROVED",
        "CAMPAIGN_READINESS_BLOCKED",
    ):
        assert precondition in contract


def test_customer_campaign_activation_contract_defines_status_vocabulary() -> None:
    contract = _contract()

    for status in (
        "NOT_ACTIVATED",
        "ACTIVATION_BLOCKED",
        "READY_TO_ACTIVATE",
        "ACTIVATION_REQUEST_ACCEPTED",
        "ACTIVE",
        "CAMPAIGN_ACTIVATION_ACCEPTED",
        "CAMPAIGN_ACTIVATION_REPLAYED",
    ):
        assert status in contract


def test_customer_campaign_activation_contract_preserves_guardrails() -> None:
    contract = _contract()

    for guardrail in (
        "NO_TENANT_CODE_EXPOSURE",
        "NO_LINK_GENERATION",
        "NO_VALIDATION_TRACK_CREATED",
        "NO_WEBHOOK_DELIVERY",
        "NO_INVITE_OR_SEAT_CHANGE",
        "NO_CREDENTIAL_CREATION",
        "NO_BILLING_OR_MONEY_MOVEMENT",
    ):
        assert guardrail in contract

    for redaction in (
        "internal_tenant_identifier",
        "idempotency_key_hash",
        "payload_hash",
    ):
        assert redaction in contract


def test_customer_campaign_activation_contract_keeps_adjacent_work_out_of_scope() -> None:
    contract = _contract()

    for phrase in (
        "backend routes",
        "schema or migrations",
        "runtime campaign activation writes",
        "frontend screens",
        "link/code generation",
        "campaign validation or `campaign_track_id` creation",
        "webhook delivery",
        "credential creation",
        "seat assignment",
        "auth/session claim changes",
        "report/export creation",
        "billing",
        "rewards payment",
        "funding",
        "fulfilment",
        "settlement",
        "broad DLaaS marketplace behavior",
    ):
        assert phrase in contract
