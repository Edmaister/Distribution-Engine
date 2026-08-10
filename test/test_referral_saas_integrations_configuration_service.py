from __future__ import annotations

import pytest

from services.referral_saas_integrations_configuration_service import (
    ReferralSaasApiAccessVerificationResult,
    ReferralSaasWebhookTestDispatchResult,
    ReferralSaasIntegrationConfiguration,
    ReferralSaasIntegrationCredentialRequest,
    ReferralSaasMessageProviderTestResult,
    ReferralSaasProviderVaultExecutionResult,
    build_referral_saas_integration_client_binding,
    build_referral_saas_integration_execution_readiness,
    build_referral_saas_provider_vault_readiness,
    IntegrationConfigurationUnsafePayload,
    IntegrationConfigurationValidationError,
    validate_referral_saas_integration_configuration,
)
from services.referral_saas_integration_test_runtime import (
    INTEGRATION_TEST_EXECUTION_PROOF_BLOCKED,
    INTEGRATION_TEST_EXECUTION_PROOF_READY,
    IntegrationTestRuntimeRequest,
    execute_integration_test_runtime,
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


def _approved_credential_request() -> ReferralSaasIntegrationCredentialRequest:
    return ReferralSaasIntegrationCredentialRequest(
        credential_request_ref="credreq-1",
        account_ref="acct-1",
        configuration_ref="config-1",
        credential_request_status="CREDENTIAL_REQUEST_READY_FOR_REVIEW",
        review_status="REVIEW_APPROVED",
        request_type="PROVIDER_CREDENTIAL_REFERENCE_CREATE",
        capability="REFERRAL_SAAS_PROVIDER_REFERENCE",
        environment="SANDBOX",
        intended_use=["INVITE_DELIVERY"],
        requested_for={"providerKey": "approved-email-provider"},
        safe_request_posture={"requestVersion": "safe-version-1"},
        reason_code="CREDENTIAL_SETUP",
        correlation_id="corr-1",
        created_by_ref="admin",
        created_by_role="ADMIN",
        created_at="2026-08-10T00:00:00Z",
        updated_at="2026-08-10T00:00:00Z",
        redactions=["credential_request_payload"],
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


def test_provider_vault_execution_result_includes_ready_lifecycle_proof() -> None:
    result = ReferralSaasProviderVaultExecutionResult(
        command_status="PROVIDER_VAULT_EXECUTION_READY",
        execution_ref="audit-1",
        credential_request=_approved_credential_request(),
        provider_key="approved-email-provider",
        environment="SANDBOX",
        capability="REFERRAL_SAAS_PROVIDER_REFERENCE",
        blocked_reason=None,
        next_action="Use the recorded proof.",
        idempotency_status="PROVIDER_VAULT_EXECUTION_READY",
        audit_event_id="audit-1",
        plain_language_summary="Provider/vault references were recorded safely.",
        guardrails=["CUSTOMER_SCOPED_PROVIDER_VAULT_EXECUTION_COMMAND"],
        redactions=["credential_request_payload", "vault_reference"],
        provider_runtime_reference="prv_ref_opaque",
        opaque_vault_reference="vault_ref_opaque",
        adapter_ref="PLATFORM_REFERENCE",
        vault_adapter_ref="PLATFORM_VAULT_REFERENCE",
        approved_request_version="safe-version-1",
    )

    safe = result.to_safe_dict()
    proof = safe["credentialVaultLifecycleProof"]

    assert proof["proofStatus"] == "PROVIDER_VAULT_LIFECYCLE_PROOF_READY"
    assert proof["approvedRequestVersionMatched"] is True
    assert proof["auditEvidencePresent"] is True
    assert proof["runtimeEvidence"] == {
        "providerRuntimeReferencePresent": True,
        "opaqueVaultReferencePresent": True,
        "adapterRefPresent": True,
        "vaultAdapterRefPresent": True,
    }
    assert proof["safeForFrontendDisplay"] is True
    assert proof["noRawSecretExposureConfirmed"] is True


def test_provider_vault_execution_result_marks_stale_request_proof_blocked() -> None:
    result = ReferralSaasProviderVaultExecutionResult(
        command_status="PROVIDER_VAULT_EXECUTION_BLOCKED",
        execution_ref="audit-1",
        credential_request=_approved_credential_request(),
        provider_key="approved-email-provider",
        environment="SANDBOX",
        capability="REFERRAL_SAAS_PROVIDER_REFERENCE",
        blocked_reason="PROVIDER_VAULT_BLOCKED_REQUEST_VERSION_MISMATCH",
        next_action="Resolve the listed blocker before trying again.",
        idempotency_status="PROVIDER_VAULT_EXECUTION_BLOCKED",
        audit_event_id="audit-1",
        plain_language_summary="Provider/vault execution was blocked safely.",
        guardrails=["CUSTOMER_SCOPED_PROVIDER_VAULT_EXECUTION_COMMAND"],
        redactions=["credential_request_payload", "vault_reference"],
        approved_request_version="stale-version",
    )

    safe = result.to_safe_dict()
    proof = safe["credentialVaultLifecycleProof"]

    assert proof["proofStatus"] == "PROVIDER_VAULT_LIFECYCLE_PROOF_BLOCKED"
    assert proof["blockedReason"] == "PROVIDER_VAULT_BLOCKED_REQUEST_VERSION_MISMATCH"
    assert proof["approvedRequestVersionMatched"] is False
    assert proof["runtimeEvidence"]["providerRuntimeReferencePresent"] is False
    assert proof["noUnsupportedProviderDispatchConfirmed"] is True


def test_provider_vault_lifecycle_proof_does_not_expose_raw_secret_fields() -> None:
    result = ReferralSaasProviderVaultExecutionResult(
        command_status="PROVIDER_VAULT_EXECUTION_READY",
        execution_ref="audit-1",
        credential_request=_approved_credential_request(),
        provider_key="approved-email-provider",
        environment="SANDBOX",
        capability="REFERRAL_SAAS_PROVIDER_REFERENCE",
        blocked_reason=None,
        next_action="Use the recorded proof.",
        idempotency_status="PROVIDER_VAULT_EXECUTION_READY",
        audit_event_id="audit-1",
        plain_language_summary="Provider/vault references were recorded safely.",
        guardrails=["CUSTOMER_SCOPED_PROVIDER_VAULT_EXECUTION_COMMAND"],
        redactions=["credential_request_payload", "vault_reference"],
        provider_runtime_reference="prv_ref_opaque",
        opaque_vault_reference="vault_ref_opaque",
        adapter_ref="PLATFORM_REFERENCE",
        vault_adapter_ref="PLATFORM_VAULT_REFERENCE",
        approved_request_version="safe-version-1",
    )

    proof = result.to_safe_dict()["credentialVaultLifecycleProof"]
    proof_text = str(proof)

    assert "super-secret-api-key" not in proof_text
    assert "raw-signing-secret" not in proof_text
    assert "raw-credential-fingerprint" not in proof_text
    assert "raw-vault-object-path" not in proof_text
    assert "api_key_value" in proof["redactions"]
    assert "signing_key_value" in proof["redactions"]
    assert "vault_reference" in proof["redactions"]


@pytest.mark.asyncio
async def test_api_access_test_runtime_returns_safe_execution_proof() -> None:
    result = await execute_integration_test_runtime(
        IntegrationTestRuntimeRequest(
            test_type="API_ACCESS_VERIFICATION",
            account_id="acct-1",
            tenant_code="FNB",
            configuration_ref="config-1",
            request_payload_hash="payload-hash",
            environment="SANDBOX",
            verified_use_cases=["CAMPAIGN_READ"],
        )
    )

    safe = result.to_safe_dict()
    assert safe["proofStatus"] == INTEGRATION_TEST_EXECUTION_PROOF_READY
    assert safe["adapterRef"] == "API_ACCESS_TEST_EVIDENCE_ADAPTER"
    assert safe["runtimeEvidence"]["apiAccessEvidencePresent"] is True
    assert safe["noProviderCallConfirmed"] is True
    assert safe["noCredentialCreationConfirmed"] is True


@pytest.mark.asyncio
async def test_message_provider_runtime_tracks_invite_and_referral_message_evidence() -> None:
    result = await execute_integration_test_runtime(
        IntegrationTestRuntimeRequest(
            test_type="MESSAGE_PROVIDER_TEST",
            account_id="acct-1",
            tenant_code="FNB",
            configuration_ref="config-1",
            request_payload_hash="payload-hash",
            channels=["EMAIL", "SMS"],
            provider_refs_count=1,
        )
    )

    safe = result.to_safe_dict()
    assert safe["proofStatus"] == INTEGRATION_TEST_EXECUTION_PROOF_READY
    assert safe["adapterRef"] == "MESSAGE_PROVIDER_TEST_EVIDENCE_ADAPTER"
    assert safe["runtimeEvidence"]["inviteProviderEvidencePresent"] is True
    assert safe["runtimeEvidence"]["referralMessageProviderEvidencePresent"] is True
    assert safe["noInviteDeliveryConfirmed"] is True
    assert safe["noMessageProviderDeliveryConfirmed"] is True


@pytest.mark.asyncio
async def test_webhook_test_runtime_blocks_incomplete_evidence_without_dispatch() -> None:
    result = await execute_integration_test_runtime(
        IntegrationTestRuntimeRequest(
            test_type="WEBHOOK_TEST_DISPATCH",
            account_id="acct-1",
            tenant_code="FNB",
            configuration_ref="config-1",
            request_payload_hash="payload-hash",
            callback_url_present=True,
            event_categories=[],
        )
    )

    safe = result.to_safe_dict()
    assert safe["proofStatus"] == INTEGRATION_TEST_EXECUTION_PROOF_BLOCKED
    assert safe["blockedReason"] == "WEBHOOK_TEST_EVIDENCE_MISSING"
    assert safe["runtimeEvidence"]["webhookTestEvidencePresent"] is False
    assert safe["noWebhookDispatchConfirmed"] is True


def test_integration_command_results_include_test_execution_evidence() -> None:
    proof = {
        "proofStatus": "INTEGRATION_TEST_EXECUTION_PROOF_READY",
        "adapterRef": "API_ACCESS_TEST_EVIDENCE_ADAPTER",
        "runtimeEvidence": {"apiAccessEvidencePresent": True},
        "safeForFrontendDisplay": True,
    }

    api_result = ReferralSaasApiAccessVerificationResult(
        verification_status="API_ACCESS_VERIFICATION_RECORDED",
        configuration_ref="config-1",
        account_ref="acct-1",
        api_environment="SANDBOX",
        verified_use_cases=["CAMPAIGN_READ"],
        idempotency_status="API_ACCESS_VERIFICATION_RECORDED",
        audit_event_id="audit-1",
        plain_language_summary="API evidence recorded.",
        guardrails=["NO_LIVE_PROVIDER_EXECUTION"],
        redactions=["provider_runtime_payload"],
        test_execution_evidence=proof,
    )
    webhook_result = ReferralSaasWebhookTestDispatchResult(
        dispatch_status="WEBHOOK_TEST_DISPATCH_RECORDED",
        configuration_ref="config-1",
        account_ref="acct-1",
        callback_url_present=True,
        event_categories=["REFERRAL"],
        idempotency_status="WEBHOOK_TEST_DISPATCH_RECORDED",
        audit_event_id="audit-2",
        plain_language_summary="Webhook evidence recorded.",
        guardrails=["NO_WEBHOOK_TEST_DISPATCH"],
        redactions=["webhook_signing_material"],
        test_execution_evidence={**proof, "adapterRef": "WEBHOOK_TEST_EVIDENCE_ADAPTER"},
    )
    message_result = ReferralSaasMessageProviderTestResult(
        test_status="MESSAGE_PROVIDER_TEST_RECORDED",
        configuration_ref="config-1",
        account_ref="acct-1",
        channels=["EMAIL"],
        provider_refs=["approved-email-provider"],
        idempotency_status="MESSAGE_PROVIDER_TEST_RECORDED",
        audit_event_id="audit-3",
        plain_language_summary="Message provider evidence recorded.",
        guardrails=["NO_MESSAGE_PROVIDER_DELIVERY"],
        redactions=["provider_runtime_payload"],
        test_execution_evidence={
            **proof,
            "adapterRef": "MESSAGE_PROVIDER_TEST_EVIDENCE_ADAPTER",
            "runtimeEvidence": {
                "inviteProviderEvidencePresent": True,
                "referralMessageProviderEvidencePresent": True,
            },
        },
    )

    assert (
        api_result.to_safe_dict()["testExecutionEvidence"]["adapterRef"]
        == "API_ACCESS_TEST_EVIDENCE_ADAPTER"
    )
    assert (
        webhook_result.to_safe_dict()["testExecutionEvidence"]["adapterRef"]
        == "WEBHOOK_TEST_EVIDENCE_ADAPTER"
    )
    message_proof = message_result.to_safe_dict()["testExecutionEvidence"]
    assert message_proof["runtimeEvidence"]["inviteProviderEvidencePresent"] is True
    assert message_result.to_safe_dict()["noMessageProviderDeliveryConfirmed"] is True
