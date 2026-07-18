from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT
    / "docs"
    / "sa"
    / "referral-saas"
    / "REFERRAL_SAAS_MEMBERSHIP_INVITATION_BOUNDARY.md"
)


def _contract() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def test_membership_invitation_boundary_is_referral_saas_scoped() -> None:
    contract = _contract()

    assert "TASK ID: TASK-210" in contract
    assert "Product boundary: Referral SaaS." in contract
    assert "Status: Command-boundary contract only." in contract
    assert "source-code forks" in contract


def test_membership_invitation_boundary_uses_real_account_foundation_tables() -> None:
    contract = _contract()

    for table_name in (
        "platform_accounts",
        "platform_account_tenants",
        "platform_external_tenant_refs",
        "platform_users",
        "platform_memberships",
        "platform_seats",
        "platform_account_audit_events",
    ):
        assert table_name in contract


def test_membership_invitation_boundary_defines_command_contract() -> None:
    contract = _contract()

    assert (
        "/v1/referral-saas/accounts/{accountRef}/membership-invitations"
        in contract
    )
    assert "idempotencyKey" in contract
    assert "correlationId" in contract
    assert "roleFamily" in contract
    assert "permissionSet" in contract
    assert "INVITATION_INTENT_RECORDED" in contract
    assert "INVITATION_INTENT_REPLAYED" in contract
    assert "IDEMPOTENCY_CONFLICT" in contract
    assert "MEMBERSHIP_ALREADY_EXISTS" in contract


def test_membership_invitation_boundary_preserves_redactions_and_guardrails() -> None:
    contract = _contract()

    for guardrail in (
        "NO_RAW_EMAIL_STORAGE",
        "NO_EMAIL_DELIVERY_WITHOUT_PROVIDER",
        "NO_AUTH_CLAIM_CHANGE",
        "NO_SEAT_ASSIGNMENT",
        "NO_TENANT_CODE_EXPOSURE",
        "NO_MONEY_MOVEMENT",
    ):
        assert guardrail in contract

    for redaction in (
        "internal_tenant_identifier",
        "user_identifier",
        "client_identifier",
        "email_hash",
        "idempotency_key_hash",
    ):
        assert redaction in contract


def test_membership_invitation_boundary_keeps_delivery_and_activation_out_of_scope() -> None:
    contract = _contract()

    for phrase in (
        "No runtime route",
        "email or messaging invitation delivery",
        "identity-provider integration",
        "auth/session claim changes",
        "membership activation",
        "seat assignment",
        "account lifecycle commands",
        "account maintenance commands",
        "campaign activation",
        "go-live",
        "money behavior",
    ):
        assert phrase in contract
