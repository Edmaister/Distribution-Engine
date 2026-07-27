from __future__ import annotations

import pytest

from services.referral_saas_integrations_configuration_service import (
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
