from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT
    / "docs"
    / "sa"
    / "referral-saas"
    / "REFERRAL_SAAS_CUSTOMER_CAMPAIGN_CREATE_CONTRACT.md"
)


def _contract() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def test_customer_campaign_create_contract_is_referral_saas_scoped() -> None:
    contract = _contract()

    assert "TASK ID: TASK-255" in contract
    assert "Product boundary: Referral SaaS." in contract
    assert "Status: Command-boundary contract only." in contract
    assert "source-code forks" in contract


def test_customer_campaign_create_contract_uses_real_campaign_sources() -> None:
    contract = _contract()

    for source in (
        "dp/migrations/002_campaigns.sql",
        "services/campaign_service.py",
        "services/campaign_policy_service.py",
        "services/campaign_readiness_service.py",
        "services/referral_saas_campaign_service.py",
        "apps/api/routers/campaigns.py",
        "apps/api/routers/referral_saas_accounts.py",
    ):
        assert source in contract

    for table_or_field in (
        "marketing_campaigns",
        "marketing_campaign_policies",
        "campaign_attributions",
        "campaign_code",
        "tenant_code",
        "is_active",
    ):
        assert table_or_field in contract


def test_customer_campaign_create_contract_defines_customer_scoped_command() -> None:
    contract = _contract()

    assert "POST /v1/referral-saas/accounts/{accountRef}/campaigns" in contract
    assert "externalTenantRef" in contract
    assert "organisationRef" in contract
    assert "idempotencyKey" in contract
    assert "correlationId" in contract
    assert "DRAFT" in contract
    assert "NEEDS_POLICY" in contract
    assert "READY_FOR_REVIEW" in contract
    assert "READY_TO_ACTIVATE" in contract
    assert "ACTIVE" in contract


def test_customer_campaign_create_contract_preserves_guardrails() -> None:
    contract = _contract()

    for guardrail in (
        "NO_TENANT_CODE_EXPOSURE",
        "NO_CAMPAIGN_ACTIVATION",
        "NO_LINK_GENERATION",
        "NO_VALIDATION_TRACK_CREATED",
        "NO_POLICY_WRITE",
        "NO_WEBHOOK_DELIVERY",
        "NO_MONEY_MOVEMENT",
    ):
        assert guardrail in contract

    for redaction in (
        "internal_tenant_identifier",
        "idempotency_key_hash",
        "payload_hash",
    ):
        assert redaction in contract


def test_customer_campaign_create_contract_keeps_live_writes_out_of_scope() -> None:
    contract = _contract()

    for phrase in (
        "runtime route behavior",
        "schema migration",
        "campaign write implementation",
        "policy write implementation",
        "campaign activation",
        "go-live",
        "link/code generation",
        "campaign validation or `campaign_track_id` creation",
        "billing",
        "rewards",
        "funding",
        "fulfilment",
        "settlement",
        "broad DLaaS marketplace behavior",
    ):
        assert phrase in contract
