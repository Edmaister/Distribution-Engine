from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
from urllib.parse import urlparse

from utils.db import db_connection


INTEGRATION_CONFIGURATION_RECORDED_EVENT = "INTEGRATION_CONFIGURATION_RECORDED"
INTEGRATION_CONFIGURATION_VALIDATED = "INTEGRATION_CONFIGURATION_VALIDATED"
INTEGRATION_CONFIGURATION_SAVED = "INTEGRATION_CONFIGURATION_SAVED"
INTEGRATION_CONFIGURATION_REPLAYED = "INTEGRATION_CONFIGURATION_REPLAYED"
INTEGRATION_CONFIGURATION_DRAFT_ONLY = "INTEGRATION_CONFIGURATION_DRAFT_ONLY"
INTEGRATION_CONFIGURATION_BLOCKED_ACCOUNT_NOT_ACTIVE = (
    "INTEGRATION_CONFIGURATION_BLOCKED_ACCOUNT_NOT_ACTIVE"
)
INTEGRATION_CONFIGURATION_BLOCKED_PROVIDER_NOT_APPROVED = (
    "INTEGRATION_CONFIGURATION_BLOCKED_PROVIDER_NOT_APPROVED"
)
INTEGRATION_CONFIGURATION_BLOCKED_UNSAFE_PAYLOAD = (
    "INTEGRATION_CONFIGURATION_BLOCKED_UNSAFE_PAYLOAD"
)
INTEGRATION_EXECUTION_READY = "INTEGRATION_EXECUTION_READY"
INTEGRATION_EXECUTION_BLOCKED_ACCOUNT_NOT_ACTIVE = (
    "INTEGRATION_EXECUTION_BLOCKED_ACCOUNT_NOT_ACTIVE"
)
INTEGRATION_EXECUTION_BLOCKED_CONFIGURATION_MISSING = (
    "INTEGRATION_EXECUTION_BLOCKED_CONFIGURATION_MISSING"
)
INTEGRATION_EXECUTION_BLOCKED_PROVIDER_NOT_APPROVED = (
    "INTEGRATION_EXECUTION_BLOCKED_PROVIDER_NOT_APPROVED"
)
INTEGRATION_API_ACCESS_VERIFICATION_EVENT = (
    "INTEGRATION_API_ACCESS_VERIFICATION_RECORDED"
)
API_ACCESS_VERIFICATION_RECORDED = "API_ACCESS_VERIFICATION_RECORDED"
API_ACCESS_VERIFICATION_REPLAYED = "API_ACCESS_VERIFICATION_REPLAYED"
API_ACCESS_VERIFICATION_BLOCKED = "API_ACCESS_VERIFICATION_BLOCKED"
INTEGRATION_WEBHOOK_TEST_DISPATCH_EVENT = "INTEGRATION_WEBHOOK_TEST_DISPATCH_RECORDED"
WEBHOOK_TEST_DISPATCH_RECORDED = "WEBHOOK_TEST_DISPATCH_RECORDED"
WEBHOOK_TEST_DISPATCH_REPLAYED = "WEBHOOK_TEST_DISPATCH_REPLAYED"
WEBHOOK_TEST_DISPATCH_BLOCKED = "WEBHOOK_TEST_DISPATCH_BLOCKED"
INTEGRATION_MESSAGE_PROVIDER_TEST_EVENT = "INTEGRATION_MESSAGE_PROVIDER_TEST_RECORDED"
MESSAGE_PROVIDER_TEST_RECORDED = "MESSAGE_PROVIDER_TEST_RECORDED"
MESSAGE_PROVIDER_TEST_REPLAYED = "MESSAGE_PROVIDER_TEST_REPLAYED"
MESSAGE_PROVIDER_TEST_BLOCKED = "MESSAGE_PROVIDER_TEST_BLOCKED"
INTEGRATION_CREDENTIAL_REQUEST_EVENT = "INTEGRATION_CREDENTIAL_REQUEST_RECORDED"
INTEGRATION_CREDENTIAL_REQUEST_REVIEW_EVENT = (
    "INTEGRATION_CREDENTIAL_REQUEST_REVIEW_DECISION_RECORDED"
)
CREDENTIAL_REQUEST_RECORDED = "CREDENTIAL_REQUEST_RECORDED"
CREDENTIAL_REQUEST_REPLAYED = "CREDENTIAL_REQUEST_REPLAYED"
CREDENTIAL_REQUEST_READY_FOR_REVIEW = "CREDENTIAL_REQUEST_READY_FOR_REVIEW"
CREDENTIAL_REQUEST_REVIEW_RECORDED = "CREDENTIAL_REQUEST_REVIEW_RECORDED"
CREDENTIAL_REQUEST_REVIEW_REPLAYED = "CREDENTIAL_REQUEST_REVIEW_REPLAYED"

INTEGRATION_CONFIGURATION_GUARDRAILS = [
    "CUSTOMER_SCOPED_INTEGRATIONS_CONFIGURATION",
    "ACCOUNT_SCOPE_RESOLVED_INTERNALLY",
    "NO_TENANT_CODE_EXPOSURE",
    "NO_SECRET_OR_CREDENTIAL_STORAGE",
    "NO_CREDENTIAL_CREATION",
    "NO_WEBHOOK_DISPATCH",
    "NO_INVITE_DELIVERY",
    "NO_MEMBERSHIP_ACTIVATION",
    "NO_SEAT_ASSIGNMENT",
    "NO_AUTH_CLAIM_CHANGE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_GO_LIVE_ACTION",
    "NO_BILLING_OR_MONEY_MOVEMENT",
]
INTEGRATION_CONFIGURATION_REDACTIONS = [
    "internal_tenant_identifier",
    "tenant_code",
    "provider_secret",
    "token",
    "credential",
    "api_key",
    "signing_secret",
    "raw_provider_payload",
    "raw_webhook_payload",
    "raw_recipient",
    "idempotency_key_hash",
    "payload_hash",
]
INTEGRATION_EXECUTION_GUARDRAILS = list(
    dict.fromkeys(
        [
            *INTEGRATION_CONFIGURATION_GUARDRAILS,
            "CUSTOMER_SCOPED_INTEGRATIONS_EXECUTION_READINESS",
            "SAVED_CONFIGURATION_REQUIRED",
            "ACTIVE_ACCOUNT_LINK_REFERENCE_REQUIRED",
            "NO_LIVE_PROVIDER_EXECUTION",
            "NO_WEBHOOK_TEST_DISPATCH",
            "NO_MESSAGE_PROVIDER_DELIVERY",
            "NO_CREDENTIAL_LIFECYCLE",
        ]
    )
)
INTEGRATION_EXECUTION_REDACTIONS = list(
    dict.fromkeys(
        [
            *INTEGRATION_CONFIGURATION_REDACTIONS,
            "webhook_signing_material",
            "credential_material",
            "provider_runtime_payload",
        ]
    )
)
CREDENTIAL_REQUEST_GUARDRAILS = list(
    dict.fromkeys(
        [
            *INTEGRATION_EXECUTION_GUARDRAILS,
            "CUSTOMER_SCOPED_CREDENTIAL_REQUEST",
            "CREDENTIAL_REQUEST_REVIEW_REQUIRED",
            "NO_SECRET_CAPTURE",
            "NO_CREDENTIAL_MATERIAL_STORAGE",
            "NO_VAULT_WRITE",
            "NO_CREDENTIAL_REVEAL_OR_DOWNLOAD",
            "NO_CREDENTIAL_ROTATION_OR_REVOCATION_EXECUTION",
        ]
    )
)
CREDENTIAL_REQUEST_REDACTIONS = list(
    dict.fromkeys(
        [
            *INTEGRATION_EXECUTION_REDACTIONS,
            "credential_request_payload",
            "credential_request_material",
            "vault_reference",
            "api_key_value",
            "signing_key_value",
        ]
    )
)

API_ENVIRONMENTS = frozenset({"LOCAL_DEVELOPMENT", "SANDBOX", "PRODUCTION_INTENT"})
CREDENTIAL_REQUEST_ENVIRONMENTS = frozenset({"SANDBOX", "STAGING", "PRODUCTION"})
AUTH_METHODS = frozenset({"API_KEY", "OAUTH_CLIENT_CREDENTIALS", "SIGNED_WEBHOOK"})
EVENT_CATEGORIES = frozenset(
    {"CAMPAIGN", "REFERRAL", "PROGRESS", "ATTRIBUTION", "REPORTING", "SUPPORT"}
)
MESSAGE_CHANNELS = frozenset({"EMAIL", "SMS", "WHATSAPP", "USSD"})
INTEGRATION_USE_CASES = frozenset(
    {
        "CAMPAIGN_READ",
        "CAMPAIGN_WRITE",
        "REFERRAL_CODE_ISSUE",
        "REFERRAL_CODE_VALIDATE",
        "PROGRESS_EVENT_INGEST",
        "ATTRIBUTION_READ",
        "REPORT_READ",
        "INVITE_DELIVERY",
        "REFERRAL_MESSAGE_DELIVERY",
    }
)
CREDENTIAL_REQUEST_TYPES = frozenset(
    {
        "API_KEY_CREATE",
        "API_KEY_ROTATE",
        "API_KEY_REVOKE",
        "WEBHOOK_SIGNING_KEY_CREATE",
        "WEBHOOK_SIGNING_KEY_ROTATE",
        "PROVIDER_CREDENTIAL_REFERENCE_CREATE",
    }
)
CREDENTIAL_REQUEST_CAPABILITIES = frozenset(
    {
        "REFERRAL_SAAS_API_ACCESS",
        "REFERRAL_SAAS_WEBHOOK_SIGNING",
        "REFERRAL_SAAS_PROVIDER_REFERENCE",
    }
)
CREDENTIAL_REQUEST_REVIEW_STATUSES = frozenset(
    {"REVIEW_APPROVED", "REVIEW_REJECTED"}
)
FORBIDDEN_CONFIGURATION_KEYS = {
    "tenant_code",
    "tenantCode",
    "internal_tenant_code",
    "internalTenantCode",
    "secret",
    "providerSecret",
    "signingSecret",
    "token",
    "bearerToken",
    "authorization",
    "apiKey",
    "credential",
    "credentials",
    "password",
    "privateKey",
    "rawPayload",
    "providerPayload",
    "rawRecipient",
    "raw_ucn",
    "rawUcn",
}


class ReferralSaasIntegrationConfigurationCommandError(Exception):
    safe_code = "INTEGRATION_CONFIGURATION_COMMAND_ERROR"


class IntegrationConfigurationValidationError(
    ReferralSaasIntegrationConfigurationCommandError
):
    safe_code = "VALIDATION_ERROR"


class IntegrationConfigurationUnsafePayload(
    ReferralSaasIntegrationConfigurationCommandError
):
    safe_code = "REJECTED_UNSAFE_PAYLOAD"


class IntegrationConfigurationIdempotencyConflict(
    ReferralSaasIntegrationConfigurationCommandError
):
    safe_code = "IDEMPOTENCY_CONFLICT"


class IntegrationCredentialRequestNotFound(
    ReferralSaasIntegrationConfigurationCommandError
):
    safe_code = "CREDENTIAL_REQUEST_NOT_FOUND"


@dataclass(frozen=True)
class ReferralSaasIntegrationConfigurationValidation:
    command_status: str
    safe_setup_posture: dict[str, Any]
    guardrails: list[str]
    redactions: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "safeSetupPosture": self.safe_setup_posture,
            "guardrails": self.guardrails,
            "redactions": self.redactions,
            "noSecretOrCredentialStorageConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noWebhookDispatchConfirmed": True,
            "noInviteDeliveryConfirmed": True,
            "noMembershipActivationConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noGoLiveActionConfirmed": True,
            "noBillingOrMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class ReferralSaasIntegrationConfiguration:
    configuration_ref: str
    account_ref: str
    configuration_status: str
    api_environment: dict[str, Any]
    webhook_intent: dict[str, Any]
    message_providers: dict[str, Any]
    safe_setup_posture: dict[str, Any]
    reason_code: str | None
    correlation_id: str | None
    created_by_ref: str
    created_by_role: str | None
    created_at: str | None
    updated_at: str | None
    redactions: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "configurationRef": self.configuration_ref,
            "accountRef": self.account_ref,
            "configurationStatus": self.configuration_status,
            "apiEnvironment": self.api_environment,
            "webhookIntent": self.webhook_intent,
            "messageProviders": self.message_providers,
            "safeSetupPosture": self.safe_setup_posture,
            "reasonCode": self.reason_code,
            "correlationId": self.correlation_id,
            "createdByRef": self.created_by_ref,
            "createdByRole": self.created_by_role,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "redactions": self.redactions,
        }


@dataclass(frozen=True)
class ReferralSaasIntegrationExecutionReadiness:
    execution_status: str
    plain_language_summary: str
    blockers: list[dict[str, Any]]
    ready_actions: list[dict[str, Any]]
    execution_actions: list[dict[str, Any]]
    guardrails: list[str]
    redactions: list[str]
    configuration_ref: str | None = None
    configuration_status: str | None = None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "executionStatus": self.execution_status,
            "plainLanguageSummary": self.plain_language_summary,
            "blockers": self.blockers,
            "readyActions": self.ready_actions,
            "executionActions": self.execution_actions,
            "configurationRef": self.configuration_ref,
            "configurationStatus": self.configuration_status,
            "guardrails": self.guardrails,
            "redactions": self.redactions,
            "noSecretOrCredentialStorageConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noCredentialLifecycleConfirmed": True,
            "noWebhookDispatchConfirmed": True,
            "noInviteDeliveryConfirmed": True,
            "noMessageProviderDeliveryConfirmed": True,
            "noMembershipActivationConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noGoLiveActionConfirmed": True,
            "noBillingOrMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class ReferralSaasIntegrationConfigurationSaveResult:
    command_status: str
    configuration: ReferralSaasIntegrationConfiguration
    validation: ReferralSaasIntegrationConfigurationValidation
    idempotency_status: str
    audit_event_id: str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "configuration": self.configuration.to_safe_dict(),
            "validation": self.validation.to_safe_dict(),
            "idempotency": {"status": self.idempotency_status},
            "audit": {"accountAuditEventId": self.audit_event_id},
            "guardrails": INTEGRATION_CONFIGURATION_GUARDRAILS,
            "redactions": INTEGRATION_CONFIGURATION_REDACTIONS,
        }


@dataclass(frozen=True)
class ReferralSaasApiAccessVerificationResult:
    verification_status: str
    configuration_ref: str
    account_ref: str
    api_environment: str
    verified_use_cases: list[str]
    idempotency_status: str
    audit_event_id: str | None
    plain_language_summary: str
    guardrails: list[str]
    redactions: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "verificationStatus": self.verification_status,
            "configurationRef": self.configuration_ref,
            "accountRef": self.account_ref,
            "apiEnvironment": self.api_environment,
            "verifiedUseCases": self.verified_use_cases,
            "idempotency": {"status": self.idempotency_status},
            "audit": {"accountAuditEventId": self.audit_event_id},
            "plainLanguageSummary": self.plain_language_summary,
            "guardrails": self.guardrails,
            "redactions": self.redactions,
            "noSecretOrCredentialStorageConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noCredentialLifecycleConfirmed": True,
            "noWebhookDispatchConfirmed": True,
            "noInviteDeliveryConfirmed": True,
            "noMessageProviderDeliveryConfirmed": True,
            "noMembershipActivationConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noGoLiveActionConfirmed": True,
            "noBillingOrMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class ReferralSaasWebhookTestDispatchResult:
    dispatch_status: str
    configuration_ref: str
    account_ref: str
    callback_url_present: bool
    event_categories: list[str]
    idempotency_status: str
    audit_event_id: str | None
    plain_language_summary: str
    guardrails: list[str]
    redactions: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "dispatchStatus": self.dispatch_status,
            "configurationRef": self.configuration_ref,
            "accountRef": self.account_ref,
            "callbackUrlPresent": self.callback_url_present,
            "eventCategories": self.event_categories,
            "idempotency": {"status": self.idempotency_status},
            "audit": {"accountAuditEventId": self.audit_event_id},
            "plainLanguageSummary": self.plain_language_summary,
            "guardrails": self.guardrails,
            "redactions": self.redactions,
            "noSecretOrCredentialStorageConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noCredentialLifecycleConfirmed": True,
            "noWebhookDispatchConfirmed": True,
            "noInviteDeliveryConfirmed": True,
            "noMessageProviderDeliveryConfirmed": True,
            "noMembershipActivationConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noGoLiveActionConfirmed": True,
            "noBillingOrMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class ReferralSaasMessageProviderTestResult:
    test_status: str
    configuration_ref: str
    account_ref: str
    channels: list[str]
    provider_refs: list[str]
    idempotency_status: str
    audit_event_id: str | None
    plain_language_summary: str
    guardrails: list[str]
    redactions: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "testStatus": self.test_status,
            "configurationRef": self.configuration_ref,
            "accountRef": self.account_ref,
            "channels": self.channels,
            "providerRefs": self.provider_refs,
            "idempotency": {"status": self.idempotency_status},
            "audit": {"accountAuditEventId": self.audit_event_id},
            "plainLanguageSummary": self.plain_language_summary,
            "guardrails": self.guardrails,
            "redactions": self.redactions,
            "noSecretOrCredentialStorageConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noCredentialLifecycleConfirmed": True,
            "noWebhookDispatchConfirmed": True,
            "noInviteDeliveryConfirmed": True,
            "noMessageProviderDeliveryConfirmed": True,
            "noMembershipActivationConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noGoLiveActionConfirmed": True,
            "noBillingOrMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class ReferralSaasIntegrationCredentialRequest:
    credential_request_ref: str
    account_ref: str
    configuration_ref: str | None
    credential_request_status: str
    review_status: str
    request_type: str
    capability: str
    environment: str
    intended_use: list[str]
    requested_for: dict[str, Any]
    safe_request_posture: dict[str, Any]
    reason_code: str | None
    correlation_id: str | None
    created_by_ref: str
    created_by_role: str | None
    created_at: str | None
    updated_at: str | None
    redactions: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "credentialRequestRef": self.credential_request_ref,
            "accountRef": self.account_ref,
            "configurationRef": self.configuration_ref,
            "credentialRequestStatus": self.credential_request_status,
            "reviewStatus": self.review_status,
            "requestType": self.request_type,
            "capability": self.capability,
            "environment": self.environment,
            "intendedUse": self.intended_use,
            "requestedFor": self.requested_for,
            "safeRequestPosture": self.safe_request_posture,
            "reasonCode": self.reason_code,
            "correlationId": self.correlation_id,
            "createdByRef": self.created_by_ref,
            "createdByRole": self.created_by_role,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "redactions": self.redactions,
            "noSecretOrCredentialStorageConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noCredentialLifecycleExecutionConfirmed": True,
            "noCredentialRevealOrDownloadConfirmed": True,
            "noVaultWriteConfirmed": True,
            "noProviderCallConfirmed": True,
            "noWebhookDispatchConfirmed": True,
            "noInviteDeliveryConfirmed": True,
            "noMessageProviderDeliveryConfirmed": True,
            "noMembershipActivationConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noGoLiveActionConfirmed": True,
            "noBillingOrMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class ReferralSaasIntegrationCredentialRequestResult:
    command_status: str
    credential_request: ReferralSaasIntegrationCredentialRequest
    idempotency_status: str
    audit_event_id: str | None
    plain_language_summary: str
    guardrails: list[str]
    redactions: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "credentialRequest": self.credential_request.to_safe_dict(),
            "idempotency": {"status": self.idempotency_status},
            "audit": {"accountAuditEventId": self.audit_event_id},
            "plainLanguageSummary": self.plain_language_summary,
            "guardrails": self.guardrails,
            "redactions": self.redactions,
            "noSecretOrCredentialStorageConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noCredentialLifecycleExecutionConfirmed": True,
            "noCredentialRevealOrDownloadConfirmed": True,
            "noVaultWriteConfirmed": True,
            "noProviderCallConfirmed": True,
            "noWebhookDispatchConfirmed": True,
            "noInviteDeliveryConfirmed": True,
            "noMessageProviderDeliveryConfirmed": True,
            "noMembershipActivationConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noGoLiveActionConfirmed": True,
            "noBillingOrMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class ReferralSaasIntegrationCredentialReviewDecisionResult:
    command_status: str
    credential_request: ReferralSaasIntegrationCredentialRequest
    review_status: str
    idempotency_status: str
    audit_event_id: str | None
    plain_language_summary: str
    guardrails: list[str]
    redactions: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "credentialRequest": self.credential_request.to_safe_dict(),
            "reviewStatus": self.review_status,
            "idempotency": {"status": self.idempotency_status},
            "audit": {"accountAuditEventId": self.audit_event_id},
            "plainLanguageSummary": self.plain_language_summary,
            "guardrails": self.guardrails,
            "redactions": self.redactions,
            "noSecretOrCredentialStorageConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noCredentialLifecycleExecutionConfirmed": True,
            "noCredentialRevealOrDownloadConfirmed": True,
            "noVaultWriteConfirmed": True,
            "noProviderCallConfirmed": True,
            "noWebhookDispatchConfirmed": True,
            "noInviteDeliveryConfirmed": True,
            "noMessageProviderDeliveryConfirmed": True,
            "noMembershipActivationConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noGoLiveActionConfirmed": True,
            "noBillingOrMoneyMovementConfirmed": True,
        }


def _jsonb(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _safe_json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def _safe_json_list(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _optional_text(value: Any) -> str | None:
    safe_value = _clean_text(value)
    return safe_value or None


def _as_iso(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _require_bounded_text(
    value: Any, field_name: str, *, min_length: int, max_length: int
) -> str:
    safe_value = _clean_text(value)
    if not (min_length <= len(safe_value) <= max_length):
        raise IntegrationConfigurationValidationError(
            f"{field_name} must be between {min_length} and {max_length} characters."
        )
    return safe_value


def _normalise_choice(value: Any, allowed: frozenset[str], field_name: str) -> str:
    safe_value = _clean_text(value).upper()
    if safe_value not in allowed:
        raise IntegrationConfigurationValidationError(
            f"{field_name} must be one of: {', '.join(sorted(allowed))}."
        )
    return safe_value


def _normalise_choice_list(
    value: Any, allowed: frozenset[str], field_name: str
) -> list[str]:
    if value is None:
        return []
    raw_values = value if isinstance(value, list) else [value]
    return [_normalise_choice(item, allowed, field_name) for item in raw_values]


def _assert_safe_payload(value: Any, path: str = "configuration") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key) in FORBIDDEN_CONFIGURATION_KEYS:
                raise IntegrationConfigurationUnsafePayload(
                    f"{path}.{key} is not allowed in integrations configuration."
                )
            _assert_safe_payload(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _assert_safe_payload(nested, f"{path}[{index}]")


def assert_safe_referral_saas_integration_execution_payload(value: Any) -> None:
    _assert_safe_payload(value, "execution")


def _normalise_callback_url(value: Any, environment: str) -> str | None:
    url = _optional_text(value)
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme == "https":
        return url
    if (
        environment == "LOCAL_DEVELOPMENT"
        and parsed.scheme == "http"
        and parsed.hostname in {"localhost", "127.0.0.1"}
    ):
        return url
    raise IntegrationConfigurationValidationError(
        "webhookIntent.callbackUrl must use HTTPS unless LOCAL_DEVELOPMENT uses localhost."
    )


def _normalise_api_environment(value: dict[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise IntegrationConfigurationValidationError("apiEnvironment must be an object.")
    _assert_safe_payload(value, "apiEnvironment")
    environment = _normalise_choice(
        value.get("environment") or "SANDBOX", API_ENVIRONMENTS, "apiEnvironment.environment"
    )
    auth_method = _optional_text(value.get("authMethod"))
    return {
        "environment": environment,
        "authMethod": (
            _normalise_choice(auth_method, AUTH_METHODS, "apiEnvironment.authMethod")
            if auth_method
            else None
        ),
        "useCases": _normalise_choice_list(
            value.get("useCases"), INTEGRATION_USE_CASES, "apiEnvironment.useCases"
        ),
    }


def _normalise_webhook_intent(
    value: dict[str, Any] | None, *, environment: str
) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise IntegrationConfigurationValidationError("webhookIntent must be an object.")
    _assert_safe_payload(value, "webhookIntent")
    return {
        "callbackUrl": _normalise_callback_url(value.get("callbackUrl"), environment),
        "eventCategories": _normalise_choice_list(
            value.get("eventCategories"),
            EVENT_CATEGORIES,
            "webhookIntent.eventCategories",
        ),
        "deliveryMode": _optional_text(value.get("deliveryMode")) or "DRAFT_ONLY",
    }


def _normalise_message_providers(value: dict[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise IntegrationConfigurationValidationError("messageProviders must be an object.")
    _assert_safe_payload(value, "messageProviders")
    return {
        "channels": _normalise_choice_list(
            value.get("channels"), MESSAGE_CHANNELS, "messageProviders.channels"
        ),
        "providerRefs": [
            _require_bounded_text(item, "messageProviders.providerRefs", min_length=1, max_length=120)
            for item in (value.get("providerRefs") or [])
        ]
        if isinstance(value.get("providerRefs") or [], list)
        else [],
        "approvalIntent": _optional_text(value.get("approvalIntent")) or "DRAFT_ONLY",
    }


def _configuration_from_row(row: Any) -> ReferralSaasIntegrationConfiguration:
    return ReferralSaasIntegrationConfiguration(
        configuration_ref=str(row["integration_configuration_id"]),
        account_ref=str(row["account_id"]),
        configuration_status=str(row["configuration_status"]),
        api_environment=_safe_json_dict(row.get("api_environment")),
        webhook_intent=_safe_json_dict(row.get("webhook_intent")),
        message_providers=_safe_json_dict(row.get("message_providers")),
        safe_setup_posture=_safe_json_dict(row.get("safe_setup_posture")),
        reason_code=_optional_text(row.get("reason_code")),
        correlation_id=_optional_text(row.get("correlation_id")),
        created_by_ref=str(row["created_by_ref"]),
        created_by_role=_optional_text(row.get("created_by_role")),
        created_at=_as_iso(row.get("created_at")),
        updated_at=_as_iso(row.get("updated_at")),
        redactions=_safe_json_list(row.get("redactions")),
    )


def _credential_request_from_row(row: Any) -> ReferralSaasIntegrationCredentialRequest:
    return ReferralSaasIntegrationCredentialRequest(
        credential_request_ref=str(row["integration_credential_request_id"]),
        account_ref=str(row["account_id"]),
        configuration_ref=(
            str(row["integration_configuration_id"])
            if row.get("integration_configuration_id")
            else None
        ),
        credential_request_status=str(row["credential_request_status"]),
        review_status=str(row["review_status"]),
        request_type=str(row["request_type"]),
        capability=str(row["capability"]),
        environment=str(row["environment"]),
        intended_use=_safe_json_list(row.get("intended_use")),
        requested_for=_safe_json_dict(row.get("requested_for")),
        safe_request_posture=_safe_json_dict(row.get("safe_request_posture")),
        reason_code=_optional_text(row.get("reason_code")),
        correlation_id=_optional_text(row.get("correlation_id")),
        created_by_ref=str(row["created_by_ref"]),
        created_by_role=_optional_text(row.get("created_by_role")),
        created_at=_as_iso(row.get("created_at")),
        updated_at=_as_iso(row.get("updated_at")),
        redactions=_safe_json_list(row.get("redactions")),
    )


def _normalise_requested_for(value: dict[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise IntegrationConfigurationValidationError("requestedFor must be an object.")
    _assert_safe_payload(value, "requestedFor")
    return {
        "integrationOwnerRef": _optional_text(value.get("integrationOwnerRef")),
        "displayName": _optional_text(value.get("displayName")),
        "businessReason": _optional_text(value.get("businessReason")),
    }


def validate_referral_saas_integration_configuration(
    *,
    account_status: str | None,
    tenant_link_status: str | None,
    external_reference_status: str | None,
    api_environment: dict[str, Any] | None,
    webhook_intent: dict[str, Any] | None,
    message_providers: dict[str, Any] | None,
) -> ReferralSaasIntegrationConfigurationValidation:
    safe_api_environment = _normalise_api_environment(api_environment)
    environment = safe_api_environment.get("environment") or "SANDBOX"
    safe_webhook_intent = _normalise_webhook_intent(
        webhook_intent, environment=str(environment)
    )
    safe_message_providers = _normalise_message_providers(message_providers)

    blockers: list[str] = []
    if str(account_status or "").upper() != "ACTIVE":
        blockers.append("ACCOUNT_NOT_ACTIVE")
    if str(tenant_link_status or "").upper() != "ACTIVE":
        blockers.append("TENANT_LINK_NOT_ACTIVE")
    if str(external_reference_status or "").upper() != "ACTIVE":
        blockers.append("EXTERNAL_REFERENCE_NOT_ACTIVE")

    status = (
        INTEGRATION_CONFIGURATION_VALIDATED
        if not blockers
        else INTEGRATION_CONFIGURATION_BLOCKED_ACCOUNT_NOT_ACTIVE
    )
    return ReferralSaasIntegrationConfigurationValidation(
        command_status=status,
        safe_setup_posture={
            "accountStatus": str(account_status or "").upper() or "UNKNOWN",
            "tenantLinkStatus": str(tenant_link_status or "").upper() or "UNKNOWN",
            "externalReferenceStatus": str(external_reference_status or "").upper()
            or "UNKNOWN",
            "blockers": blockers,
            "apiEnvironment": safe_api_environment,
            "webhookIntent": safe_webhook_intent,
            "messageProviders": safe_message_providers,
        },
        guardrails=INTEGRATION_CONFIGURATION_GUARDRAILS,
        redactions=INTEGRATION_CONFIGURATION_REDACTIONS,
    )


def _execution_blocker(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _execution_action(
    *,
    action_ref: str,
    label: str,
    status: str,
    next_step: str,
    reason: str,
) -> dict[str, str]:
    return {
        "actionRef": action_ref,
        "label": label,
        "status": status,
        "nextStep": next_step,
        "reason": reason,
    }


def build_referral_saas_integration_execution_readiness(
    *,
    account_status: str | None,
    tenant_link_status: str | None,
    external_reference_status: str | None,
    configuration: ReferralSaasIntegrationConfiguration | None,
) -> ReferralSaasIntegrationExecutionReadiness:
    blockers: list[dict[str, str]] = []
    account_posture = {
        "accountStatus": str(account_status or "").upper() or "UNKNOWN",
        "tenantLinkStatus": str(tenant_link_status or "").upper() or "UNKNOWN",
        "externalReferenceStatus": str(external_reference_status or "").upper()
        or "UNKNOWN",
    }
    if account_posture["accountStatus"] != "ACTIVE":
        blockers.append(
            _execution_blocker(
                "ACCOUNT_NOT_ACTIVE",
                "Activate the customer account foundation before live verification.",
            )
        )
    if account_posture["tenantLinkStatus"] != "ACTIVE":
        blockers.append(
            _execution_blocker(
                "TENANT_LINK_NOT_ACTIVE",
                "Activate the tenant link before live verification.",
            )
        )
    if account_posture["externalReferenceStatus"] != "ACTIVE":
        blockers.append(
            _execution_blocker(
                "EXTERNAL_REFERENCE_NOT_ACTIVE",
                "Activate the selected customer reference before live verification.",
            )
        )

    if configuration is None:
        blockers.append(
            _execution_blocker(
                "CONFIGURATION_MISSING",
                "Save the customer's Integrations setup before live verification.",
            )
        )
        return ReferralSaasIntegrationExecutionReadiness(
            execution_status=(
                INTEGRATION_EXECUTION_BLOCKED_ACCOUNT_NOT_ACTIVE
                if len(blockers) > 1
                else INTEGRATION_EXECUTION_BLOCKED_CONFIGURATION_MISSING
            ),
            plain_language_summary=(
                "Save Integrations setup evidence before API, webhook, or message "
                "provider verification can start."
            ),
            blockers=blockers,
            ready_actions=[],
            execution_actions=[
                _execution_action(
                    action_ref="SAVE_INTEGRATION_CONFIGURATION",
                    label="Save Integrations setup",
                    status="BLOCKED",
                    next_step="Open Integrations and save non-secret setup evidence.",
                    reason="No saved configuration exists for this customer.",
                )
            ],
            guardrails=INTEGRATION_EXECUTION_GUARDRAILS,
            redactions=INTEGRATION_EXECUTION_REDACTIONS,
        )

    if configuration.configuration_status != INTEGRATION_CONFIGURATION_SAVED:
        blockers.append(
            _execution_blocker(
                "CONFIGURATION_NOT_SAVED",
                "Save the Integrations configuration before live verification.",
            )
        )

    api_environment = configuration.api_environment or {}
    webhook_intent = configuration.webhook_intent or {}
    message_providers = configuration.message_providers or {}

    execution_actions = [
        _execution_action(
            action_ref="API_ACCESS_VERIFICATION",
            label="Verify API access",
            status=(
                "READY"
                if api_environment.get("environment")
                and api_environment.get("authMethod")
                and api_environment.get("useCases")
                else "MISSING_EVIDENCE"
            ),
            next_step="Run a governed API-access verification command in a later task.",
            reason="Requires saved environment, auth method, and intended API use cases.",
        ),
        _execution_action(
            action_ref="WEBHOOK_TEST_DISPATCH",
            label="Run webhook test dispatch",
            status=(
                "READY"
                if webhook_intent.get("callbackUrl")
                and webhook_intent.get("eventCategories")
                else "MISSING_EVIDENCE"
            ),
            next_step="Run a guarded webhook test-dispatch command in a later task.",
            reason="Requires an approved callback URL and selected event categories.",
        ),
        _execution_action(
            action_ref="MESSAGE_PROVIDER_TEST",
            label="Check message provider delivery",
            status=(
                "READY"
                if message_providers.get("channels")
                and message_providers.get("providerRefs")
                else "MISSING_EVIDENCE"
            ),
            next_step="Run a governed provider delivery check in a later task.",
            reason="Requires selected channels and approved provider references.",
        ),
        _execution_action(
            action_ref="CREDENTIAL_REQUEST",
            label="Request governed credentials",
            status="READY" if api_environment.get("authMethod") else "MISSING_EVIDENCE",
            next_step="Submit a governed credential lifecycle request in a later task.",
            reason="Requires the selected auth method without browser-supplied secrets.",
        ),
    ]

    provider_gap = (
        bool(message_providers.get("channels")) and not message_providers.get("providerRefs")
    )
    if provider_gap:
        blockers.append(
            _execution_blocker(
                "PROVIDER_NOT_APPROVED",
                "Approve provider references before live provider checks.",
            )
        )

    ready_actions = [
        action for action in execution_actions if action["status"] == "READY"
    ]
    if any(item["code"].endswith("NOT_ACTIVE") for item in blockers):
        execution_status = INTEGRATION_EXECUTION_BLOCKED_ACCOUNT_NOT_ACTIVE
        plain_language_summary = (
            "Activate the customer account foundation before Integrations live "
            "verification can start."
        )
    elif any(
        item["code"] in {"CONFIGURATION_NOT_SAVED", "CONFIGURATION_MISSING"}
        for item in blockers
    ):
        execution_status = INTEGRATION_EXECUTION_BLOCKED_CONFIGURATION_MISSING
        plain_language_summary = (
            "Save Integrations setup evidence before live verification can start."
        )
    elif any(item["code"] == "PROVIDER_NOT_APPROVED" for item in blockers):
        execution_status = INTEGRATION_EXECUTION_BLOCKED_PROVIDER_NOT_APPROVED
        plain_language_summary = (
            "Approve the customer provider references before live provider checks."
        )
    else:
        execution_status = INTEGRATION_EXECUTION_READY
        plain_language_summary = (
            "Saved Integrations setup can move into governed live verification "
            "checks. No live action has been run by this endpoint."
        )

    return ReferralSaasIntegrationExecutionReadiness(
        execution_status=execution_status,
        plain_language_summary=plain_language_summary,
        blockers=blockers,
        ready_actions=ready_actions,
        execution_actions=execution_actions,
        configuration_ref=configuration.configuration_ref,
        configuration_status=configuration.configuration_status,
        guardrails=INTEGRATION_EXECUTION_GUARDRAILS,
        redactions=INTEGRATION_EXECUTION_REDACTIONS,
    )


async def get_referral_saas_integration_configuration(
    *,
    account_id: str,
) -> ReferralSaasIntegrationConfiguration | None:
    safe_account_id = _require_bounded_text(
        account_id, "account_id", min_length=1, max_length=80
    )
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_integration_configurations
            WHERE account_id = $1
              AND archived_at IS NULL
            ORDER BY created_at DESC, integration_configuration_id DESC
            LIMIT 1
            """,
            safe_account_id,
        )
    return _configuration_from_row(row) if row else None


async def upsert_referral_saas_integration_configuration(
    *,
    account_id: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    tenant_code: str,
    account_status: str | None,
    tenant_link_status: str | None,
    external_reference_status: str | None,
    api_environment: dict[str, Any] | None,
    webhook_intent: dict[str, Any] | None,
    message_providers: dict[str, Any] | None,
    reason_code: str | None,
    correlation_id: str | None,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
) -> ReferralSaasIntegrationConfigurationSaveResult:
    safe_account_id = _require_bounded_text(
        account_id, "account_id", min_length=1, max_length=80
    )
    safe_tenant_code = _require_bounded_text(
        tenant_code, "tenant_code", min_length=1, max_length=120
    )
    safe_idempotency_hash = _require_bounded_text(
        idempotency_key_hash, "idempotency_key_hash", min_length=1, max_length=256
    )
    safe_payload_hash = _require_bounded_text(
        request_payload_hash, "request_payload_hash", min_length=1, max_length=256
    )
    safe_actor_ref = _require_bounded_text(
        actor_ref, "actor_ref", min_length=1, max_length=160
    )
    safe_actor_role = _optional_text(actor_role)
    safe_reason_code = _optional_text(reason_code) or "CUSTOMER_INTEGRATION_CONFIGURATION"
    safe_correlation_id = _optional_text(correlation_id)
    validation = validate_referral_saas_integration_configuration(
        account_status=account_status,
        tenant_link_status=tenant_link_status,
        external_reference_status=external_reference_status,
        api_environment=api_environment,
        webhook_intent=webhook_intent,
        message_providers=message_providers,
    )
    safe_status = (
        INTEGRATION_CONFIGURATION_SAVED
        if validation.command_status == INTEGRATION_CONFIGURATION_VALIDATED
        else INTEGRATION_CONFIGURATION_DRAFT_ONLY
    )
    posture = validation.safe_setup_posture
    safe_api_environment = posture["apiEnvironment"]
    safe_webhook_intent = posture["webhookIntent"]
    safe_message_providers = posture["messageProviders"]

    async with db_connection() as conn:
        existing = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_integration_configurations
            WHERE account_id = $1
              AND idempotency_key_hash = $2
              AND archived_at IS NULL
            LIMIT 1
            """,
            safe_account_id,
            safe_idempotency_hash,
        )
        if existing:
            if _optional_text(existing.get("request_payload_hash")) != safe_payload_hash:
                raise IntegrationConfigurationIdempotencyConflict(
                    "Idempotency key was reused with different integrations configuration content."
                )
            return ReferralSaasIntegrationConfigurationSaveResult(
                command_status=INTEGRATION_CONFIGURATION_REPLAYED,
                configuration=_configuration_from_row(existing),
                validation=validation,
                idempotency_status=INTEGRATION_CONFIGURATION_REPLAYED,
                audit_event_id=None,
            )

        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO referral_saas_integration_configurations (
                    account_id,
                    account_tenant_id,
                    external_ref_id,
                    tenant_code,
                    configuration_status,
                    api_environment,
                    webhook_intent,
                    message_providers,
                    safe_setup_posture,
                    reason_code,
                    correlation_id,
                    idempotency_key_hash,
                    request_payload_hash,
                    created_by_ref,
                    created_by_role,
                    updated_by_ref,
                    redactions
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8::jsonb,
                    $9::jsonb, $10, $11, $12, $13, $14, $15, $14, $16::jsonb
                )
                RETURNING *
                """,
                safe_account_id,
                _optional_text(account_tenant_id),
                _optional_text(external_ref_id),
                safe_tenant_code,
                safe_status,
                _jsonb(safe_api_environment),
                _jsonb(safe_webhook_intent),
                _jsonb(safe_message_providers),
                _jsonb(posture),
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                safe_payload_hash,
                safe_actor_ref,
                safe_actor_role,
                _jsonb(INTEGRATION_CONFIGURATION_REDACTIONS),
            )

            audit_event = await conn.fetchrow(
                """
                INSERT INTO platform_account_audit_events (
                    account_id,
                    account_tenant_id,
                    external_ref_id,
                    tenant_code,
                    event_type,
                    event_status,
                    actor_ref,
                    actor_role,
                    previous_status,
                    next_status,
                    reason_code,
                    correlation_id,
                    idempotency_key_hash,
                    evidence_summary,
                    redactions
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8,
                    NULL, $9, $10, $11, $12, $13::jsonb, $14::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                _optional_text(account_tenant_id),
                _optional_text(external_ref_id),
                safe_tenant_code,
                INTEGRATION_CONFIGURATION_RECORDED_EVENT,
                safe_status,
                safe_actor_ref,
                safe_actor_role,
                safe_status,
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(
                    {
                        "integration_configuration_id": str(
                            row["integration_configuration_id"]
                        ),
                        "configuration_status": safe_status,
                        "request_payload_hash": safe_payload_hash,
                        "no_secret_or_credential_storage_confirmed": True,
                        "no_webhook_dispatch_confirmed": True,
                        "no_billing_or_money_movement_confirmed": True,
                    }
                ),
                _jsonb(INTEGRATION_CONFIGURATION_REDACTIONS),
            )

    return ReferralSaasIntegrationConfigurationSaveResult(
        command_status=safe_status,
        configuration=_configuration_from_row(row),
        validation=validation,
        idempotency_status=safe_status,
        audit_event_id=str(audit_event["account_audit_event_id"]) if audit_event else None,
    )


async def record_referral_saas_api_access_verification(
    *,
    account_id: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    tenant_code: str,
    account_status: str | None,
    tenant_link_status: str | None,
    external_reference_status: str | None,
    configuration: ReferralSaasIntegrationConfiguration | None,
    reason_code: str | None,
    correlation_id: str | None,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
) -> ReferralSaasApiAccessVerificationResult:
    safe_account_id = _require_bounded_text(
        account_id, "account_id", min_length=1, max_length=80
    )
    safe_tenant_code = _require_bounded_text(
        tenant_code, "tenant_code", min_length=1, max_length=120
    )
    safe_idempotency_hash = _require_bounded_text(
        idempotency_key_hash, "idempotency_key_hash", min_length=1, max_length=256
    )
    safe_payload_hash = _require_bounded_text(
        request_payload_hash, "request_payload_hash", min_length=1, max_length=256
    )
    safe_actor_ref = _require_bounded_text(
        actor_ref, "actor_ref", min_length=1, max_length=160
    )
    safe_actor_role = _optional_text(actor_role)
    safe_reason_code = _optional_text(reason_code) or "CUSTOMER_API_ACCESS_VERIFICATION"
    safe_correlation_id = _optional_text(correlation_id)

    readiness = build_referral_saas_integration_execution_readiness(
        account_status=account_status,
        tenant_link_status=tenant_link_status,
        external_reference_status=external_reference_status,
        configuration=configuration,
    )
    api_action = next(
        (
            action
            for action in readiness.execution_actions
            if action.get("actionRef") == "API_ACCESS_VERIFICATION"
        ),
        None,
    )
    if (
        readiness.execution_status != INTEGRATION_EXECUTION_READY
        or not api_action
        or api_action.get("status") != "READY"
        or configuration is None
    ):
        blocker_codes = [
            str(item.get("code"))
            for item in readiness.blockers
            if isinstance(item, dict) and item.get("code")
        ]
        if api_action and api_action.get("status") != "READY":
            blocker_codes.append("API_ACCESS_EVIDENCE_MISSING")
        raise IntegrationConfigurationValidationError(
            "API access verification requires an active account, active tenant link, "
            "active external reference, saved Integrations configuration, API "
            f"environment, auth method, and use cases. Blockers: {', '.join(blocker_codes) or 'UNKNOWN'}."
        )

    api_environment = configuration.api_environment or {}
    environment = str(api_environment.get("environment") or "UNKNOWN")
    verified_use_cases = [
        str(item)
        for item in (api_environment.get("useCases") or [])
        if str(item).strip()
    ]
    evidence_summary = {
        "integration_configuration_id": configuration.configuration_ref,
        "verification_status": API_ACCESS_VERIFICATION_RECORDED,
        "api_environment": environment,
        "verified_use_cases": verified_use_cases,
        "request_payload_hash": safe_payload_hash,
        "no_secret_or_credential_storage_confirmed": True,
        "no_credential_creation_confirmed": True,
        "no_credential_lifecycle_confirmed": True,
        "no_webhook_dispatch_confirmed": True,
        "no_invite_delivery_confirmed": True,
        "no_message_provider_delivery_confirmed": True,
        "no_membership_activation_confirmed": True,
        "no_seat_assignment_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_campaign_activation_confirmed": True,
        "no_go_live_action_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }

    async with db_connection() as conn:
        existing = await conn.fetchrow(
            """
            SELECT account_audit_event_id, evidence_summary
            FROM platform_account_audit_events
            WHERE account_id = $1
              AND event_type = $2
              AND idempotency_key_hash = $3
            ORDER BY created_at DESC, account_audit_event_id DESC
            LIMIT 1
            """,
            safe_account_id,
            INTEGRATION_API_ACCESS_VERIFICATION_EVENT,
            safe_idempotency_hash,
        )
        if existing:
            existing_evidence = _safe_json_dict(existing.get("evidence_summary"))
            if _optional_text(existing_evidence.get("request_payload_hash")) != safe_payload_hash:
                raise IntegrationConfigurationIdempotencyConflict(
                    "Idempotency key was reused with different API-access verification content."
                )
            return ReferralSaasApiAccessVerificationResult(
                verification_status=API_ACCESS_VERIFICATION_REPLAYED,
                configuration_ref=configuration.configuration_ref,
                account_ref=safe_account_id,
                api_environment=environment,
                verified_use_cases=verified_use_cases,
                idempotency_status=API_ACCESS_VERIFICATION_REPLAYED,
                audit_event_id=str(existing["account_audit_event_id"]),
                plain_language_summary=(
                    "API-access verification evidence was replayed from the same "
                    "idempotency key and payload. No credential was created, no "
                    "provider was called, and no adjacent workflow changed."
                ),
                guardrails=INTEGRATION_EXECUTION_GUARDRAILS,
                redactions=INTEGRATION_EXECUTION_REDACTIONS,
            )

        audit_event = await conn.fetchrow(
            """
            INSERT INTO platform_account_audit_events (
                account_id,
                account_tenant_id,
                external_ref_id,
                tenant_code,
                event_type,
                event_status,
                actor_ref,
                actor_role,
                previous_status,
                next_status,
                reason_code,
                correlation_id,
                idempotency_key_hash,
                evidence_summary,
                redactions
            )
            VALUES (
                $1, $2, $3, $4, $5, 'RECORDED', $6, $7,
                NULL, $8, $9, $10, $11, $12::jsonb, $13::jsonb
            )
            RETURNING account_audit_event_id
            """,
            safe_account_id,
            _optional_text(account_tenant_id),
            _optional_text(external_ref_id),
            safe_tenant_code,
            INTEGRATION_API_ACCESS_VERIFICATION_EVENT,
            safe_actor_ref,
            safe_actor_role,
            API_ACCESS_VERIFICATION_RECORDED,
            safe_reason_code,
            safe_correlation_id,
            safe_idempotency_hash,
            _jsonb(evidence_summary),
            _jsonb(INTEGRATION_EXECUTION_REDACTIONS),
        )

    return ReferralSaasApiAccessVerificationResult(
        verification_status=API_ACCESS_VERIFICATION_RECORDED,
        configuration_ref=configuration.configuration_ref,
        account_ref=safe_account_id,
        api_environment=environment,
        verified_use_cases=verified_use_cases,
        idempotency_status=API_ACCESS_VERIFICATION_RECORDED,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
        plain_language_summary=(
            "API-access verification evidence was recorded for the selected "
            "customer. No credential was created, no token was revealed, no "
            "provider was called, and no adjacent workflow changed."
        ),
        guardrails=INTEGRATION_EXECUTION_GUARDRAILS,
        redactions=INTEGRATION_EXECUTION_REDACTIONS,
    )


async def record_referral_saas_webhook_test_dispatch(
    *,
    account_id: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    tenant_code: str,
    account_status: str | None,
    tenant_link_status: str | None,
    external_reference_status: str | None,
    configuration: ReferralSaasIntegrationConfiguration | None,
    reason_code: str | None,
    correlation_id: str | None,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
) -> ReferralSaasWebhookTestDispatchResult:
    safe_account_id = _require_bounded_text(
        account_id, "account_id", min_length=1, max_length=80
    )
    safe_tenant_code = _require_bounded_text(
        tenant_code, "tenant_code", min_length=1, max_length=120
    )
    safe_idempotency_hash = _require_bounded_text(
        idempotency_key_hash, "idempotency_key_hash", min_length=1, max_length=256
    )
    safe_payload_hash = _require_bounded_text(
        request_payload_hash, "request_payload_hash", min_length=1, max_length=256
    )
    safe_actor_ref = _require_bounded_text(
        actor_ref, "actor_ref", min_length=1, max_length=160
    )
    safe_actor_role = _optional_text(actor_role)
    safe_reason_code = _optional_text(reason_code) or "CUSTOMER_WEBHOOK_TEST_DISPATCH"
    safe_correlation_id = _optional_text(correlation_id)

    readiness = build_referral_saas_integration_execution_readiness(
        account_status=account_status,
        tenant_link_status=tenant_link_status,
        external_reference_status=external_reference_status,
        configuration=configuration,
    )
    webhook_action = next(
        (
            action
            for action in readiness.execution_actions
            if action.get("actionRef") == "WEBHOOK_TEST_DISPATCH"
        ),
        None,
    )
    if (
        readiness.execution_status != INTEGRATION_EXECUTION_READY
        or not webhook_action
        or webhook_action.get("status") != "READY"
        or configuration is None
    ):
        blocker_codes = [
            str(item.get("code"))
            for item in readiness.blockers
            if isinstance(item, dict) and item.get("code")
        ]
        if webhook_action and webhook_action.get("status") != "READY":
            blocker_codes.append("WEBHOOK_EVIDENCE_MISSING")
        raise IntegrationConfigurationValidationError(
            "Webhook test-dispatch evidence requires an active account, active "
            "tenant link, active external reference, saved Integrations "
            "configuration, callback URL, and event categories. Blockers: "
            f"{', '.join(blocker_codes) or 'UNKNOWN'}."
        )

    webhook_intent = configuration.webhook_intent or {}
    event_categories = [
        str(item)
        for item in (webhook_intent.get("eventCategories") or [])
        if str(item).strip()
    ]
    evidence_summary = {
        "integration_configuration_id": configuration.configuration_ref,
        "dispatch_status": WEBHOOK_TEST_DISPATCH_RECORDED,
        "callback_url_present": bool(webhook_intent.get("callbackUrl")),
        "event_categories": event_categories,
        "request_payload_hash": safe_payload_hash,
        "no_secret_or_credential_storage_confirmed": True,
        "no_credential_creation_confirmed": True,
        "no_credential_lifecycle_confirmed": True,
        "no_webhook_dispatch_confirmed": True,
        "no_invite_delivery_confirmed": True,
        "no_message_provider_delivery_confirmed": True,
        "no_membership_activation_confirmed": True,
        "no_seat_assignment_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_campaign_activation_confirmed": True,
        "no_go_live_action_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }

    async with db_connection() as conn:
        existing = await conn.fetchrow(
            """
            SELECT account_audit_event_id, evidence_summary
            FROM platform_account_audit_events
            WHERE account_id = $1
              AND event_type = $2
              AND idempotency_key_hash = $3
            ORDER BY created_at DESC, account_audit_event_id DESC
            LIMIT 1
            """,
            safe_account_id,
            INTEGRATION_WEBHOOK_TEST_DISPATCH_EVENT,
            safe_idempotency_hash,
        )
        if existing:
            existing_evidence = _safe_json_dict(existing.get("evidence_summary"))
            if _optional_text(existing_evidence.get("request_payload_hash")) != safe_payload_hash:
                raise IntegrationConfigurationIdempotencyConflict(
                    "Idempotency key was reused with different webhook test-dispatch content."
                )
            return ReferralSaasWebhookTestDispatchResult(
                dispatch_status=WEBHOOK_TEST_DISPATCH_REPLAYED,
                configuration_ref=configuration.configuration_ref,
                account_ref=safe_account_id,
                callback_url_present=bool(webhook_intent.get("callbackUrl")),
                event_categories=event_categories,
                idempotency_status=WEBHOOK_TEST_DISPATCH_REPLAYED,
                audit_event_id=str(existing["account_audit_event_id"]),
                plain_language_summary=(
                    "Webhook test-dispatch evidence was replayed from the same "
                    "idempotency key and payload. No webhook was dispatched and "
                    "no adjacent workflow changed."
                ),
                guardrails=INTEGRATION_EXECUTION_GUARDRAILS,
                redactions=INTEGRATION_EXECUTION_REDACTIONS,
            )

        audit_event = await conn.fetchrow(
            """
            INSERT INTO platform_account_audit_events (
                account_id,
                account_tenant_id,
                external_ref_id,
                tenant_code,
                event_type,
                event_status,
                actor_ref,
                actor_role,
                previous_status,
                next_status,
                reason_code,
                correlation_id,
                idempotency_key_hash,
                evidence_summary,
                redactions
            )
            VALUES (
                $1, $2, $3, $4, $5, 'RECORDED', $6, $7,
                NULL, $8, $9, $10, $11, $12::jsonb, $13::jsonb
            )
            RETURNING account_audit_event_id
            """,
            safe_account_id,
            _optional_text(account_tenant_id),
            _optional_text(external_ref_id),
            safe_tenant_code,
            INTEGRATION_WEBHOOK_TEST_DISPATCH_EVENT,
            safe_actor_ref,
            safe_actor_role,
            WEBHOOK_TEST_DISPATCH_RECORDED,
            safe_reason_code,
            safe_correlation_id,
            safe_idempotency_hash,
            _jsonb(evidence_summary),
            _jsonb(INTEGRATION_EXECUTION_REDACTIONS),
        )

    return ReferralSaasWebhookTestDispatchResult(
        dispatch_status=WEBHOOK_TEST_DISPATCH_RECORDED,
        configuration_ref=configuration.configuration_ref,
        account_ref=safe_account_id,
        callback_url_present=bool(webhook_intent.get("callbackUrl")),
        event_categories=event_categories,
        idempotency_status=WEBHOOK_TEST_DISPATCH_RECORDED,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
        plain_language_summary=(
            "Webhook test-dispatch evidence was recorded for the selected "
            "customer. No webhook was dispatched, no signing material was "
            "created or revealed, and no adjacent workflow changed."
        ),
        guardrails=INTEGRATION_EXECUTION_GUARDRAILS,
        redactions=INTEGRATION_EXECUTION_REDACTIONS,
    )


async def record_referral_saas_message_provider_test(
    *,
    account_id: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    tenant_code: str,
    account_status: str | None,
    tenant_link_status: str | None,
    external_reference_status: str | None,
    configuration: ReferralSaasIntegrationConfiguration | None,
    reason_code: str | None,
    correlation_id: str | None,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
) -> ReferralSaasMessageProviderTestResult:
    safe_account_id = _require_bounded_text(
        account_id, "account_id", min_length=1, max_length=80
    )
    safe_tenant_code = _require_bounded_text(
        tenant_code, "tenant_code", min_length=1, max_length=120
    )
    safe_idempotency_hash = _require_bounded_text(
        idempotency_key_hash, "idempotency_key_hash", min_length=1, max_length=256
    )
    safe_payload_hash = _require_bounded_text(
        request_payload_hash, "request_payload_hash", min_length=1, max_length=256
    )
    safe_actor_ref = _require_bounded_text(
        actor_ref, "actor_ref", min_length=1, max_length=160
    )
    safe_actor_role = _optional_text(actor_role)
    safe_reason_code = _optional_text(reason_code) or "CUSTOMER_MESSAGE_PROVIDER_TEST"
    safe_correlation_id = _optional_text(correlation_id)

    readiness = build_referral_saas_integration_execution_readiness(
        account_status=account_status,
        tenant_link_status=tenant_link_status,
        external_reference_status=external_reference_status,
        configuration=configuration,
    )
    message_action = next(
        (
            action
            for action in readiness.execution_actions
            if action.get("actionRef") == "MESSAGE_PROVIDER_TEST"
        ),
        None,
    )
    if (
        readiness.execution_status != INTEGRATION_EXECUTION_READY
        or not message_action
        or message_action.get("status") != "READY"
        or configuration is None
    ):
        blocker_codes = [
            str(item.get("code"))
            for item in readiness.blockers
            if isinstance(item, dict) and item.get("code")
        ]
        if message_action and message_action.get("status") != "READY":
            blocker_codes.append("MESSAGE_PROVIDER_EVIDENCE_MISSING")
        raise IntegrationConfigurationValidationError(
            "Message-provider test evidence requires an active account, active "
            "tenant link, active external reference, saved Integrations "
            "configuration, message channels, and approved provider references. "
            f"Blockers: {', '.join(blocker_codes) or 'UNKNOWN'}."
        )

    message_providers = configuration.message_providers or {}
    channels = [
        str(item)
        for item in (message_providers.get("channels") or [])
        if str(item).strip()
    ]
    provider_refs = [
        str(item)
        for item in (message_providers.get("providerRefs") or [])
        if str(item).strip()
    ]
    evidence_summary = {
        "integration_configuration_id": configuration.configuration_ref,
        "test_status": MESSAGE_PROVIDER_TEST_RECORDED,
        "channels": channels,
        "provider_refs_count": len(provider_refs),
        "request_payload_hash": safe_payload_hash,
        "no_secret_or_credential_storage_confirmed": True,
        "no_credential_creation_confirmed": True,
        "no_credential_lifecycle_confirmed": True,
        "no_webhook_dispatch_confirmed": True,
        "no_invite_delivery_confirmed": True,
        "no_message_provider_delivery_confirmed": True,
        "no_membership_activation_confirmed": True,
        "no_seat_assignment_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_campaign_activation_confirmed": True,
        "no_go_live_action_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }

    async with db_connection() as conn:
        existing = await conn.fetchrow(
            """
            SELECT account_audit_event_id, evidence_summary
            FROM platform_account_audit_events
            WHERE account_id = $1
              AND event_type = $2
              AND idempotency_key_hash = $3
            ORDER BY created_at DESC, account_audit_event_id DESC
            LIMIT 1
            """,
            safe_account_id,
            INTEGRATION_MESSAGE_PROVIDER_TEST_EVENT,
            safe_idempotency_hash,
        )
        if existing:
            existing_evidence = _safe_json_dict(existing.get("evidence_summary"))
            if _optional_text(existing_evidence.get("request_payload_hash")) != safe_payload_hash:
                raise IntegrationConfigurationIdempotencyConflict(
                    "Idempotency key was reused with different message-provider test content."
                )
            return ReferralSaasMessageProviderTestResult(
                test_status=MESSAGE_PROVIDER_TEST_REPLAYED,
                configuration_ref=configuration.configuration_ref,
                account_ref=safe_account_id,
                channels=channels,
                provider_refs=provider_refs,
                idempotency_status=MESSAGE_PROVIDER_TEST_REPLAYED,
                audit_event_id=str(existing["account_audit_event_id"]),
                plain_language_summary=(
                    "Message-provider test evidence was replayed from the same "
                    "idempotency key and payload. No provider was called, no "
                    "message was sent, and no adjacent workflow changed."
                ),
                guardrails=INTEGRATION_EXECUTION_GUARDRAILS,
                redactions=INTEGRATION_EXECUTION_REDACTIONS,
            )

        audit_event = await conn.fetchrow(
            """
            INSERT INTO platform_account_audit_events (
                account_id,
                account_tenant_id,
                external_ref_id,
                tenant_code,
                event_type,
                event_status,
                actor_ref,
                actor_role,
                previous_status,
                next_status,
                reason_code,
                correlation_id,
                idempotency_key_hash,
                evidence_summary,
                redactions
            )
            VALUES (
                $1, $2, $3, $4, $5, 'RECORDED', $6, $7,
                NULL, $8, $9, $10, $11, $12::jsonb, $13::jsonb
            )
            RETURNING account_audit_event_id
            """,
            safe_account_id,
            _optional_text(account_tenant_id),
            _optional_text(external_ref_id),
            safe_tenant_code,
            INTEGRATION_MESSAGE_PROVIDER_TEST_EVENT,
            safe_actor_ref,
            safe_actor_role,
            MESSAGE_PROVIDER_TEST_RECORDED,
            safe_reason_code,
            safe_correlation_id,
            safe_idempotency_hash,
            _jsonb(evidence_summary),
            _jsonb(INTEGRATION_EXECUTION_REDACTIONS),
        )

    return ReferralSaasMessageProviderTestResult(
        test_status=MESSAGE_PROVIDER_TEST_RECORDED,
        configuration_ref=configuration.configuration_ref,
        account_ref=safe_account_id,
        channels=channels,
        provider_refs=provider_refs,
        idempotency_status=MESSAGE_PROVIDER_TEST_RECORDED,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
        plain_language_summary=(
            "Message-provider test evidence was recorded for the selected "
            "customer. No provider was called, no invite or referral message "
            "was sent, and no adjacent workflow changed."
        ),
        guardrails=INTEGRATION_EXECUTION_GUARDRAILS,
        redactions=INTEGRATION_EXECUTION_REDACTIONS,
    )


async def create_referral_saas_integration_credential_request(
    *,
    account_id: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    tenant_code: str,
    account_status: str | None,
    tenant_link_status: str | None,
    external_reference_status: str | None,
    configuration: ReferralSaasIntegrationConfiguration | None,
    request_type: str | None,
    capability: str | None,
    environment: str | None,
    intended_use: list[str] | None,
    requested_for: dict[str, Any] | None,
    reason_code: str | None,
    correlation_id: str | None,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
) -> ReferralSaasIntegrationCredentialRequestResult:
    safe_account_id = _require_bounded_text(
        account_id, "account_id", min_length=1, max_length=80
    )
    safe_tenant_code = _require_bounded_text(
        tenant_code, "tenant_code", min_length=1, max_length=120
    )
    safe_idempotency_hash = _require_bounded_text(
        idempotency_key_hash, "idempotency_key_hash", min_length=1, max_length=256
    )
    safe_payload_hash = _require_bounded_text(
        request_payload_hash, "request_payload_hash", min_length=1, max_length=256
    )
    safe_actor_ref = _require_bounded_text(
        actor_ref, "actor_ref", min_length=1, max_length=160
    )
    safe_actor_role = _optional_text(actor_role)
    safe_reason_code = _optional_text(reason_code) or "CUSTOMER_CREDENTIAL_REQUEST"
    safe_correlation_id = _optional_text(correlation_id)
    safe_request_type = _normalise_choice(
        request_type, CREDENTIAL_REQUEST_TYPES, "credentialRequest.requestType"
    )
    safe_capability = _normalise_choice(
        capability, CREDENTIAL_REQUEST_CAPABILITIES, "credentialRequest.capability"
    )
    safe_environment = _normalise_choice(
        environment or "SANDBOX",
        CREDENTIAL_REQUEST_ENVIRONMENTS,
        "credentialRequest.environment",
    )
    safe_intended_use = _normalise_choice_list(
        intended_use, INTEGRATION_USE_CASES, "credentialRequest.intendedUse"
    )
    safe_requested_for = _normalise_requested_for(requested_for)

    readiness = build_referral_saas_integration_execution_readiness(
        account_status=account_status,
        tenant_link_status=tenant_link_status,
        external_reference_status=external_reference_status,
        configuration=configuration,
    )
    if (
        readiness.execution_status != INTEGRATION_EXECUTION_READY
        or configuration is None
        or configuration.configuration_status != INTEGRATION_CONFIGURATION_SAVED
    ):
        blocker_codes = [
            str(item.get("code"))
            for item in readiness.blockers
            if isinstance(item, dict) and item.get("code")
        ]
        if configuration is None:
            blocker_codes.append("CONFIGURATION_MISSING")
        raise IntegrationConfigurationValidationError(
            "Credential requests require an active account, active tenant link, "
            "active external reference, and saved Integrations configuration. "
            f"Blockers: {', '.join(blocker_codes) or 'UNKNOWN'}."
        )

    posture = {
        "requestStatus": CREDENTIAL_REQUEST_RECORDED,
        "reviewStatus": "READY_FOR_REVIEW",
        "configurationRef": configuration.configuration_ref,
        "requestType": safe_request_type,
        "capability": safe_capability,
        "environment": safe_environment,
        "intendedUse": safe_intended_use,
        "requestedFor": safe_requested_for,
        "no_secret_or_credential_storage_confirmed": True,
        "no_credential_creation_confirmed": True,
        "no_credential_lifecycle_execution_confirmed": True,
        "no_credential_reveal_or_download_confirmed": True,
        "no_vault_write_confirmed": True,
        "no_provider_call_confirmed": True,
        "no_webhook_dispatch_confirmed": True,
        "no_invite_delivery_confirmed": True,
        "no_message_provider_delivery_confirmed": True,
        "no_membership_activation_confirmed": True,
        "no_seat_assignment_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_campaign_activation_confirmed": True,
        "no_go_live_action_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }

    async with db_connection() as conn:
        existing = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_integration_credential_requests
            WHERE account_id = $1
              AND idempotency_key_hash = $2
              AND archived_at IS NULL
            LIMIT 1
            """,
            safe_account_id,
            safe_idempotency_hash,
        )
        if existing:
            if _optional_text(existing.get("request_payload_hash")) != safe_payload_hash:
                raise IntegrationConfigurationIdempotencyConflict(
                    "Idempotency key was reused with different credential request content."
                )
            return ReferralSaasIntegrationCredentialRequestResult(
                command_status=CREDENTIAL_REQUEST_REPLAYED,
                credential_request=_credential_request_from_row(existing),
                idempotency_status=CREDENTIAL_REQUEST_REPLAYED,
                audit_event_id=None,
                plain_language_summary=(
                    "Credential request was replayed from the same idempotency "
                    "key and payload. No secret was created, revealed, stored, "
                    "downloaded, rotated, revoked, or sent."
                ),
                guardrails=CREDENTIAL_REQUEST_GUARDRAILS,
                redactions=CREDENTIAL_REQUEST_REDACTIONS,
            )

        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO referral_saas_integration_credential_requests (
                    account_id,
                    account_tenant_id,
                    external_ref_id,
                    tenant_code,
                    integration_configuration_id,
                    credential_request_status,
                    review_status,
                    request_type,
                    capability,
                    environment,
                    intended_use,
                    requested_for,
                    safe_request_posture,
                    reason_code,
                    correlation_id,
                    idempotency_key_hash,
                    request_payload_hash,
                    created_by_ref,
                    created_by_role,
                    updated_by_ref,
                    redactions
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, 'READY_FOR_REVIEW', $7, $8,
                    $9, $10::jsonb, $11::jsonb, $12::jsonb, $13, $14,
                    $15, $16, $17, $18, $17, $19::jsonb
                )
                RETURNING *
                """,
                safe_account_id,
                _optional_text(account_tenant_id),
                _optional_text(external_ref_id),
                safe_tenant_code,
                configuration.configuration_ref,
                CREDENTIAL_REQUEST_RECORDED,
                safe_request_type,
                safe_capability,
                safe_environment,
                _jsonb(safe_intended_use),
                _jsonb(safe_requested_for),
                _jsonb(posture),
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                safe_payload_hash,
                safe_actor_ref,
                safe_actor_role,
                _jsonb(CREDENTIAL_REQUEST_REDACTIONS),
            )

            audit_event = await conn.fetchrow(
                """
                INSERT INTO platform_account_audit_events (
                    account_id,
                    account_tenant_id,
                    external_ref_id,
                    tenant_code,
                    event_type,
                    event_status,
                    actor_ref,
                    actor_role,
                    previous_status,
                    next_status,
                    reason_code,
                    correlation_id,
                    idempotency_key_hash,
                    evidence_summary,
                    redactions
                )
                VALUES (
                    $1, $2, $3, $4, $5, 'RECORDED', $6, $7,
                    NULL, $8, $9, $10, $11, $12::jsonb, $13::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                _optional_text(account_tenant_id),
                _optional_text(external_ref_id),
                safe_tenant_code,
                INTEGRATION_CREDENTIAL_REQUEST_EVENT,
                safe_actor_ref,
                safe_actor_role,
                CREDENTIAL_REQUEST_RECORDED,
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(
                    {
                        "integration_credential_request_id": str(
                            row["integration_credential_request_id"]
                        ),
                        "integration_configuration_id": configuration.configuration_ref,
                        "request_type": safe_request_type,
                        "capability": safe_capability,
                        "environment": safe_environment,
                        "request_payload_hash": safe_payload_hash,
                        "no_secret_or_credential_storage_confirmed": True,
                        "no_credential_creation_confirmed": True,
                        "no_credential_lifecycle_execution_confirmed": True,
                        "no_vault_write_confirmed": True,
                        "no_provider_call_confirmed": True,
                        "no_webhook_dispatch_confirmed": True,
                        "no_billing_or_money_movement_confirmed": True,
                    }
                ),
                _jsonb(CREDENTIAL_REQUEST_REDACTIONS),
            )

    return ReferralSaasIntegrationCredentialRequestResult(
        command_status=CREDENTIAL_REQUEST_RECORDED,
        credential_request=_credential_request_from_row(row),
        idempotency_status=CREDENTIAL_REQUEST_RECORDED,
        audit_event_id=str(audit_event["account_audit_event_id"]) if audit_event else None,
        plain_language_summary=(
            "Credential request was recorded for review for the selected customer. "
            "No secret was created, revealed, stored, downloaded, rotated, revoked, "
            "or sent."
        ),
        guardrails=CREDENTIAL_REQUEST_GUARDRAILS,
        redactions=CREDENTIAL_REQUEST_REDACTIONS,
    )


async def list_referral_saas_integration_credential_requests(
    *,
    account_id: str,
    limit: int = 50,
) -> list[ReferralSaasIntegrationCredentialRequest]:
    safe_account_id = _require_bounded_text(
        account_id, "account_id", min_length=1, max_length=80
    )
    safe_limit = max(1, min(int(limit or 50), 100))
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM referral_saas_integration_credential_requests
            WHERE account_id = $1
              AND archived_at IS NULL
            ORDER BY created_at DESC, integration_credential_request_id DESC
            LIMIT $2
            """,
            safe_account_id,
            safe_limit,
        )
    return [_credential_request_from_row(row) for row in rows]


async def get_referral_saas_integration_credential_request(
    *,
    account_id: str,
    credential_request_ref: str,
) -> ReferralSaasIntegrationCredentialRequest:
    safe_account_id = _require_bounded_text(
        account_id, "account_id", min_length=1, max_length=80
    )
    safe_credential_request_ref = _require_bounded_text(
        credential_request_ref,
        "credential_request_ref",
        min_length=1,
        max_length=80,
    )
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_integration_credential_requests
            WHERE account_id = $1
              AND integration_credential_request_id = $2
              AND archived_at IS NULL
            LIMIT 1
            """,
            safe_account_id,
            safe_credential_request_ref,
        )
    if not row:
        raise IntegrationCredentialRequestNotFound(
            "Credential request was not found for the selected customer."
        )
    return _credential_request_from_row(row)


async def record_referral_saas_integration_credential_review_decision(
    *,
    account_id: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    tenant_code: str,
    credential_request_ref: str,
    review_status: str | None,
    review_reason: str | None,
    reason_code: str | None,
    correlation_id: str | None,
    idempotency_key_hash: str,
    command_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
) -> ReferralSaasIntegrationCredentialReviewDecisionResult:
    safe_account_id = _require_bounded_text(
        account_id, "account_id", min_length=1, max_length=80
    )
    safe_tenant_code = _require_bounded_text(
        tenant_code, "tenant_code", min_length=1, max_length=120
    )
    safe_credential_request_ref = _require_bounded_text(
        credential_request_ref,
        "credential_request_ref",
        min_length=1,
        max_length=80,
    )
    safe_review_status = _normalise_choice(
        review_status,
        CREDENTIAL_REQUEST_REVIEW_STATUSES,
        "reviewDecision.reviewStatus",
    )
    safe_review_reason = _require_bounded_text(
        review_reason,
        "reviewDecision.reason",
        min_length=3,
        max_length=1000,
    )
    safe_reason_code = (
        _optional_text(reason_code) or "CUSTOMER_CREDENTIAL_REVIEW_DECISION"
    )
    safe_correlation_id = _require_bounded_text(
        correlation_id, "correlation_id", min_length=1, max_length=160
    )
    safe_idempotency_hash = _require_bounded_text(
        idempotency_key_hash, "idempotency_key_hash", min_length=1, max_length=256
    )
    safe_payload_hash = _require_bounded_text(
        command_payload_hash, "command_payload_hash", min_length=1, max_length=256
    )
    safe_actor_ref = _require_bounded_text(
        actor_ref, "actor_ref", min_length=1, max_length=160
    )
    safe_actor_role = _optional_text(actor_role)

    async with db_connection() as conn:
        existing_audit = await conn.fetchrow(
            """
            SELECT account_audit_event_id, evidence_summary
            FROM platform_account_audit_events
            WHERE account_id = $1
              AND event_type = $2
              AND idempotency_key_hash = $3
            ORDER BY created_at DESC
            LIMIT 1
            """,
            safe_account_id,
            INTEGRATION_CREDENTIAL_REQUEST_REVIEW_EVENT,
            safe_idempotency_hash,
        )
        if existing_audit:
            evidence = existing_audit.get("evidence_summary") or {}
            if isinstance(evidence, str):
                evidence = json.loads(evidence)
            if _optional_text(evidence.get("command_payload_hash")) != safe_payload_hash:
                raise IntegrationConfigurationIdempotencyConflict(
                    "Idempotency key was reused with different credential review content."
                )
            replayed_request = await conn.fetchrow(
                """
                SELECT *
                FROM referral_saas_integration_credential_requests
                WHERE account_id = $1
                  AND integration_credential_request_id = $2
                  AND archived_at IS NULL
                LIMIT 1
                """,
                safe_account_id,
                _optional_text(evidence.get("credential_request_ref"))
                or safe_credential_request_ref,
            )
            if not replayed_request:
                raise IntegrationCredentialRequestNotFound(
                    "Credential request was not found for the selected customer."
                )
            return ReferralSaasIntegrationCredentialReviewDecisionResult(
                command_status=CREDENTIAL_REQUEST_REVIEW_REPLAYED,
                credential_request=_credential_request_from_row(replayed_request),
                review_status=_optional_text(evidence.get("review_status"))
                or safe_review_status,
                idempotency_status=CREDENTIAL_REQUEST_REVIEW_REPLAYED,
                audit_event_id=str(existing_audit["account_audit_event_id"]),
                plain_language_summary=(
                    "Credential request review decision was replayed from the "
                    "same idempotency key and payload. No credential was created, "
                    "revealed, stored, downloaded, rotated, revoked, or sent."
                ),
                guardrails=CREDENTIAL_REQUEST_GUARDRAILS,
                redactions=CREDENTIAL_REQUEST_REDACTIONS,
            )

        current = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_integration_credential_requests
            WHERE account_id = $1
              AND integration_credential_request_id = $2
              AND archived_at IS NULL
            LIMIT 1
            """,
            safe_account_id,
            safe_credential_request_ref,
        )
        if not current:
            raise IntegrationCredentialRequestNotFound(
                "Credential request was not found for the selected customer."
            )

        previous_review_status = str(current["review_status"])
        if previous_review_status != "READY_FOR_REVIEW":
            raise IntegrationConfigurationValidationError(
                "Credential request review decisions can only be recorded while the request is READY_FOR_REVIEW."
            )

        posture = _safe_json_dict(current.get("safe_request_posture"))
        posture.update(
            {
                "reviewStatus": safe_review_status,
                "reviewReasonHash": safe_payload_hash,
                "reviewedByRef": safe_actor_ref,
                "reviewedByRole": safe_actor_role,
                "no_secret_or_credential_storage_confirmed": True,
                "no_credential_creation_confirmed": True,
                "no_credential_lifecycle_execution_confirmed": True,
                "no_credential_reveal_or_download_confirmed": True,
                "no_vault_write_confirmed": True,
                "no_provider_call_confirmed": True,
                "no_webhook_dispatch_confirmed": True,
                "no_invite_delivery_confirmed": True,
                "no_message_provider_delivery_confirmed": True,
                "no_auth_claim_change_confirmed": True,
                "no_campaign_activation_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            }
        )

        async with conn.transaction():
            updated = await conn.fetchrow(
                """
                UPDATE referral_saas_integration_credential_requests
                SET review_status = $3,
                    safe_request_posture = $4::jsonb,
                    updated_by_ref = $5,
                    updated_at = NOW()
                WHERE account_id = $1
                  AND integration_credential_request_id = $2
                  AND archived_at IS NULL
                RETURNING *
                """,
                safe_account_id,
                safe_credential_request_ref,
                safe_review_status,
                _jsonb(posture),
                safe_actor_ref,
            )
            audit_event = await conn.fetchrow(
                """
                INSERT INTO platform_account_audit_events (
                    account_id,
                    account_tenant_id,
                    external_ref_id,
                    tenant_code,
                    event_type,
                    event_status,
                    actor_ref,
                    actor_role,
                    previous_status,
                    next_status,
                    reason_code,
                    correlation_id,
                    idempotency_key_hash,
                    evidence_summary,
                    redactions
                )
                VALUES (
                    $1, $2, $3, $4, $5, 'RECORDED', $6, $7,
                    $8, $9, $10, $11, $12, $13::jsonb, $14::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                _optional_text(account_tenant_id),
                _optional_text(external_ref_id),
                safe_tenant_code,
                INTEGRATION_CREDENTIAL_REQUEST_REVIEW_EVENT,
                safe_actor_ref,
                safe_actor_role,
                previous_review_status,
                safe_review_status,
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(
                    {
                        "credential_request_ref": safe_credential_request_ref,
                        "review_status": safe_review_status,
                        "review_reason_hash": safe_payload_hash,
                        "command_payload_hash": safe_payload_hash,
                        "reason_present": bool(safe_review_reason),
                        "no_secret_or_credential_storage_confirmed": True,
                        "no_credential_creation_confirmed": True,
                        "no_credential_lifecycle_execution_confirmed": True,
                        "no_credential_reveal_or_download_confirmed": True,
                        "no_vault_write_confirmed": True,
                        "no_provider_call_confirmed": True,
                        "no_webhook_dispatch_confirmed": True,
                        "no_billing_or_money_movement_confirmed": True,
                    }
                ),
                _jsonb(CREDENTIAL_REQUEST_REDACTIONS),
            )

    review_word = "approved" if safe_review_status == "REVIEW_APPROVED" else "blocked"
    return ReferralSaasIntegrationCredentialReviewDecisionResult(
        command_status=CREDENTIAL_REQUEST_REVIEW_RECORDED,
        credential_request=_credential_request_from_row(updated),
        review_status=safe_review_status,
        idempotency_status=CREDENTIAL_REQUEST_REVIEW_RECORDED,
        audit_event_id=str(audit_event["account_audit_event_id"]) if audit_event else None,
        plain_language_summary=(
            f"Credential request was {review_word} for later governed execution. "
            "No secret was created, revealed, stored, downloaded, rotated, "
            "revoked, written to a vault, or sent to a provider."
        ),
        guardrails=CREDENTIAL_REQUEST_GUARDRAILS,
        redactions=CREDENTIAL_REQUEST_REDACTIONS,
    )
