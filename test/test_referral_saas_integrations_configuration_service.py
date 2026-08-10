from __future__ import annotations

import pytest

from services.referral_saas_integrations_configuration_service import (
    ReferralSaasIntegrationConfiguration,
    build_referral_saas_integration_client_binding,
    build_referral_saas_integration_execution_readiness,
    build_referral_saas_provider_vault_readiness,
    IntegrationConfigurationUnsafePayload,
    IntegrationConfigurationValidationError,
    validate_referral_saas_integration_configuration,
)


def test_integrations_configuration_validation_accepts_safe_runtime_intent() -> None:
    result = validate_referral_saas_integration_configuration(
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
        api_environment={
            "environment": "SANDBOX",
            "authMethod": "API_KEY",
            "useCases": ["campaign_read", "referral_code_validate"],
        },
        webhook_intent={
            "callbackUrl": "https://example.com/referral-events",
            "eventCategories": ["referral", "progress"],
        },
        message_providers={
            "channels": ["email", "sms"],
            "providerRefs": ["approved-email-provider"],
        },
    )

    assert result.command_status == "INTEGRATION_CONFIGURATION_VALIDATED"
    assert result.safe_setup_posture["blockers"] == []
    assert result.safe_setup_posture["apiEnvironment"]["environment"] == "SANDBOX"
    assert result.safe_setup_posture["webhookIntent"]["eventCategories"] == [
        "REFERRAL",
        "PROGRESS",
    ]
    assert result.to_safe_dict()["noCredentialCreationConfirmed"] is True
    assert result.to_safe_dict()["noWebhookDispatchConfirmed"] is True


def test_integrations_configuration_validation_blocks_inactive_account_as_draft() -> None:
    result = validate_referral_saas_integration_configuration(
        account_status="PENDING_ONBOARDING",
        tenant_link_status="PENDING_SETUP",
        external_reference_status="ACTIVE",
        api_environment={"environment": "SANDBOX"},
        webhook_intent={},
        message_providers={},
    )

    assert (
        result.command_status
        == "INTEGRATION_CONFIGURATION_BLOCKED_ACCOUNT_NOT_ACTIVE"
    )
    assert result.safe_setup_posture["blockers"] == [
        "ACCOUNT_NOT_ACTIVE",
        "TENANT_LINK_NOT_ACTIVE",
    ]


def test_integrations_configuration_validation_rejects_secrets() -> None:
    with pytest.raises(IntegrationConfigurationUnsafePayload) as exc:
        validate_referral_saas_integration_configuration(
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            external_reference_status="ACTIVE",
            api_environment={"environment": "SANDBOX", "apiKey": "secret"},
            webhook_intent={},
            message_providers={},
        )

    assert "apiKey is not allowed" in str(exc.value)


def test_integrations_configuration_validation_rejects_non_https_callback() -> None:
    with pytest.raises(IntegrationConfigurationValidationError) as exc:
        validate_referral_saas_integration_configuration(
            account_status="ACTIVE",
            tenant_link_status="ACTIVE",
            external_reference_status="ACTIVE",
            api_environment={"environment": "SANDBOX"},
            webhook_intent={"callbackUrl": "http://example.com/events"},
            message_providers={},
        )

    assert "must use HTTPS" in str(exc.value)


def _saved_configuration() -> ReferralSaasIntegrationConfiguration:
    return ReferralSaasIntegrationConfiguration(
        configuration_ref="config-1",
        account_ref="acct-1",
        configuration_status="INTEGRATION_CONFIGURATION_SAVED",
        api_environment={
            "environment": "SANDBOX",
            "authMethod": "API_KEY",
            "useCases": ["CAMPAIGN_READ"],
        },
        webhook_intent={
            "callbackUrl": "https://example.com/events",
            "eventCategories": ["REFERRAL"],
        },
        message_providers={
            "channels": ["EMAIL"],
            "providerRefs": ["approved-email-provider"],
        },
        safe_setup_posture={"blockers": []},
        reason_code="CUSTOMER_INTEGRATION_CONFIGURATION",
        correlation_id="corr-1",
        created_by_ref="admin",
        created_by_role="ADMIN",
        created_at="2026-08-10T00:00:00Z",
        updated_at="2026-08-10T00:00:00Z",
        redactions=["provider_secret"],
    )


def test_integration_client_binding_ready_from_active_membership_client() -> None:
    configuration = _saved_configuration()
    binding = build_referral_saas_integration_client_binding(
        account_id="acct-1",
        tenant_code="FNB",
        configuration=configuration,
        partner_client_rows=[
            {
                "client_id": "client-secret-ref",
                "client_tenant_code": "FNB",
                "client_status": "ACTIVE",
                "membership_status": "ACTIVE",
                "role_family": "DISTRIBUTION_ADMIN",
            }
        ],
    )

    safe = binding.to_safe_dict()
    assert binding.is_ready is True
    assert safe["bindingStatus"] == "CLIENT_BINDING_READY"
    assert safe["activeClientCount"] == 1
    assert safe["providerRefsCount"] == 1
    assert "client-secret-ref" not in str(safe)
    assert "client_secret_hash" in safe["redactions"]


def test_execution_readiness_blocks_missing_integration_client_binding() -> None:
    configuration = _saved_configuration()
    binding = build_referral_saas_integration_client_binding(
        account_id="acct-1",
        tenant_code="FNB",
        configuration=configuration,
        partner_client_rows=[],
    )

    readiness = build_referral_saas_integration_execution_readiness(
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
        configuration=configuration,
        client_binding=binding,
    )

    assert (
        readiness.execution_status
        == "INTEGRATION_EXECUTION_BLOCKED_CLIENT_BINDING_MISSING"
    )
    assert readiness.blockers[0]["code"] == "CLIENT_BINDING_MISSING"
    assert readiness.to_safe_dict()["integrationClientBinding"]["clientRefPresent"] is False


def test_execution_readiness_blocks_integration_client_tenant_mismatch() -> None:
    configuration = _saved_configuration()
    binding = build_referral_saas_integration_client_binding(
        account_id="acct-1",
        tenant_code="FNB",
        configuration=configuration,
        partner_client_rows=[
            {
                "client_id": "wrong-client",
                "client_tenant_code": "OTHER",
                "client_status": "ACTIVE",
                "membership_status": "ACTIVE",
                "role_family": "DISTRIBUTION_ADMIN",
            }
        ],
    )

    readiness = build_referral_saas_integration_execution_readiness(
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
        configuration=configuration,
        client_binding=binding,
    )

    assert (
        readiness.execution_status
        == "INTEGRATION_EXECUTION_BLOCKED_CLIENT_BINDING_MISMATCH"
    )
    assert readiness.blockers[0]["code"] == "CLIENT_BINDING_TENANT_MISMATCH"
    assert "wrong-client" not in str(readiness.to_safe_dict())


def test_provider_vault_readiness_inherits_integration_client_binding_blocker() -> None:
    configuration = _saved_configuration()
    binding = build_referral_saas_integration_client_binding(
        account_id="acct-1",
        tenant_code="FNB",
        configuration=configuration,
        partner_client_rows=[],
    )

    readiness = build_referral_saas_provider_vault_readiness(
        account_status="ACTIVE",
        tenant_link_status="ACTIVE",
        external_reference_status="ACTIVE",
        configuration=configuration,
        client_binding=binding,
        credential_requests=[],
    )

    assert (
        readiness.readiness_status
        == "PROVIDER_VAULT_BLOCKED_CLIENT_BINDING_MISSING"
    )
    assert any(
        blocker["code"] == "CLIENT_BINDING_MISSING"
        for blocker in readiness.blockers
    )
