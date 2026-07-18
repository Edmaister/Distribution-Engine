from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT
    / "docs"
    / "sa"
    / "referral-saas"
    / "REFERRAL_SAAS_MEMBERSHIP_ACTIVATION_DELIVERY_BOUNDARY.md"
)


def _contract() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def test_activation_delivery_boundary_is_contract_only_and_referral_saas_scoped() -> None:
    contract = _contract()

    assert "TASK ID: TASK-214" in contract
    assert "Product boundary: Referral SaaS." in contract
    assert "Status: Command-boundary contract only." in contract
    assert "source-code forks" in contract


def test_activation_delivery_boundary_separates_intent_delivery_and_activation() -> None:
    contract = _contract()

    for phrase in (
        "Invitation intent",
        "Invitation delivery",
        "Membership activation",
        "communication side effect",
        "authorization side effect",
    ):
        assert phrase in contract


def test_activation_delivery_boundary_defines_future_route_family() -> None:
    contract = _contract()

    for route in (
        "/v1/referral-saas/accounts/{accountRef}/membership-invitations/{membershipRef}/delivery",
        "/v1/referral-saas/accounts/{accountRef}/memberships/{membershipRef}/activation",
        "/v1/referral-saas/accounts/{accountRef}/memberships/{membershipRef}",
    ):
        assert route in contract


def test_delivery_command_requires_provider_and_invited_membership_gates() -> None:
    contract = _contract()

    for phrase in (
        "Membership exists, belongs to the resolved account, and has status `INVITED`.",
        "Delivery provider is configured, approved, and scoped for Referral SaaS.",
        "recipientHash",
        "INVITATION_DELIVERY_REQUESTED",
        "DELIVERY_PROVIDER_NOT_CONFIGURED",
        "DELIVERY_REJECTED_MEMBERSHIP_NOT_INVITED",
        "DELIVERY_REJECTED_UNSAFE_PAYLOAD",
        "IDEMPOTENCY_CONFLICT",
    ):
        assert phrase in contract


def test_activation_command_requires_identity_and_active_runtime_gates() -> None:
    contract = _contract()

    for phrase in (
        "acceptedSubject",
        "ACTIVATION_REJECTED_IDENTITY_NOT_ACCEPTED",
        "ACTIVATION_REJECTED_ACCOUNT_NOT_ACTIVE",
        "ACTIVATION_REJECTED_TENANT_LINK_NOT_ACTIVE",
        "ACTIVATION_REJECTED_EXTERNAL_REFERENCE_NOT_ACTIVE",
        "ACTIVATION_REJECTED_DUPLICATE_ACTIVE_MEMBERSHIP",
        "MEMBERSHIP_ACTIVATED",
        "MEMBERSHIP_ACTIVATION_REPLAYED",
    ):
        assert phrase in contract


def test_activation_delivery_boundary_preserves_audit_idempotency_and_redactions() -> None:
    contract = _contract()

    for phrase in (
        "require `idempotencyKey`",
        "require `correlationId`",
        "hash idempotency keys",
        "hash effective payloads",
        "record account audit events",
    ):
        assert phrase in contract

    for redaction in (
        "internal_tenant_identifier",
        "user_identifier",
        "client_identifier",
        "email_hash",
        "recipient_hash",
        "idempotency_key_hash",
        "provider_secret",
    ):
        assert redaction in contract


def test_activation_delivery_boundary_keeps_adjacent_actions_out_of_scope() -> None:
    contract = _contract()

    for guardrail in (
        "NO_PROVIDER_SECRET_EXPOSURE",
        "NO_AUTH_CLAIM_CHANGE",
        "NO_SEAT_ASSIGNMENT",
        "NO_TENANT_CODE_EXPOSURE",
        "NO_CAMPAIGN_ACTIVATION",
        "NO_GO_LIVE_CHANGE",
        "NO_MONEY_MOVEMENT",
        "NO_DLAAS_MARKETPLACE_EXPANSION",
    ):
        assert guardrail in contract

    for phrase in (
        "backend routes",
        "frontend controls",
        "schema or migrations",
        "invitation provider integration",
        "identity-provider integration",
        "auth/session claim changes",
        "seat assignment",
        "campaign activation",
        "go-live",
        "money behavior",
    ):
        assert phrase in contract


def test_activation_delivery_boundary_sets_account_setup_ux_posture() -> None:
    contract = _contract()

    for phrase in (
        'Step 2 can show "Role intent recorded"',
        '"Send invite" must remain disabled',
        '"Activate access" must remain disabled',
        "membership activation does not automatically launch campaigns or enable go-live",
    ):
        assert phrase in contract
