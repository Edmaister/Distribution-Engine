from __future__ import annotations

import inspect
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from services.campaign_readiness_service import get_campaign_readiness
from services.onboarding.onboarding_draft_idempotency_service import hash_payload
from services.referral_code import (
    get_or_create_referrer_code,
    validate_referral_code,
)
from services.referral_saas_account_foundation_service import (
    ACCOUNT_FOUNDATION_ACTIVATION_GUARDRAILS,
    ACCOUNT_FOUNDATION_ACTIVATION_REDACTIONS,
    AccountFoundationActivationError,
    AccountFoundationActivationIdempotencyConflict,
    AccountFoundationActivationNotFound,
    AccountFoundationActivationNotReady,
    AccountFoundationActivationPermissionDenied,
    AccountFoundationActivationValidationError,
    AccountFoundationResolutionError,
    AccountNotResolvable,
    AccountProfileMaintenanceError,
    AccountProfileNotFound,
    AccountProfileNotMaintainable,
    AccountProfilePermissionDenied,
    AccountProfileUnsafePayload,
    AccountProfileValidationError,
    ExternalReferenceConflict,
    ExternalReferenceNotActive,
    ExternalReferenceNotFound,
    InvalidExternalReferenceType,
    TenantLinkNotResolvable,
    activate_referral_saas_account_foundation,
    list_referral_saas_accounts,
    resolve_account_by_external_reference,
    resolve_setup_account_by_external_reference,
    update_referral_saas_account_profile,
)
from services.referral_saas_account_membership_service import (
    ACCESS_PROVISIONING_GUARDRAILS,
    ACCESS_PROVISIONING_REDACTIONS,
    MembershipInvitationAccountNotReady,
    MembershipInvitationCommandError,
    MembershipInvitationDeliveryNotInvited,
    MembershipInvitationDeliveryProviderNotConfigured,
    MembershipInvitationDuplicate,
    MembershipInvitationIdempotencyConflict,
    MembershipInvitationNotEditable,
    MembershipInvitationNotFound,
    MembershipInvitationUnsafePayload,
    MembershipInvitationUnsafeScope,
    MembershipInvitationValidationError,
    cancel_referral_saas_membership_invitation_intent,
    get_referral_saas_account_membership_posture,
    get_referral_saas_membership_activation_readiness,
    record_referral_saas_membership_invitation_intent,
    request_referral_saas_access_provisioning,
    request_referral_saas_membership_activation,
    request_referral_saas_membership_invitation_delivery,
    update_referral_saas_membership_invitation_intent,
)
from services.referral_saas_account_setup_service import (
    AccountSetupCommandError,
    AccountSetupDraftNotFound,
    AccountSetupDuplicateInternalTenantScope,
    AccountSetupDuplicateReference,
    AccountSetupInvalidDraftState,
    AccountSetupMissingScope,
    AccountSetupPermissionDenied,
    create_durable_account_from_onboarding_draft,
)
from services.referral_saas_campaign_service import (
    CAMPAIGN_ACTIVATION_GUARDRAILS,
    CAMPAIGN_ACTIVATION_REDACTIONS,
    CAMPAIGN_POLICY_SETTINGS_GUARDRAILS,
    CAMPAIGN_POLICY_SETTINGS_REDACTIONS,
    CAMPAIGN_REVIEW_GUARDRAILS,
    CAMPAIGN_REVIEW_REDACTIONS,
    CAMPAIGN_SETUP_GUARDRAILS,
    CAMPAIGN_SETUP_REDACTIONS,
    CampaignActivationAlreadyActive,
    CampaignActivationCampaignNotFound,
    CampaignActivationIdempotencyConflict,
    CampaignActivationNotReady,
    CampaignActivationValidationError,
    CampaignPolicySettingsAccountNotReady,
    CampaignPolicySettingsCampaignNotFound,
    CampaignPolicySettingsIdempotencyConflict,
    CampaignPolicySettingsValidationError,
    CampaignReviewCampaignNotFound,
    CampaignReviewIdempotencyConflict,
    CampaignReviewInvalidState,
    CampaignReviewNotReady,
    CampaignReviewValidationError,
    CampaignSetupAccountNotReady,
    CampaignSetupDuplicate,
    CampaignSetupIdempotencyConflict,
    CampaignSetupValidationError,
    ReferralSaasCampaignCommandError,
    create_referral_saas_account_campaign_setup,
    get_referral_saas_account_campaign,
    list_referral_saas_account_campaigns,
    record_referral_saas_account_campaign_review_decision,
    request_referral_saas_account_campaign_activation,
    submit_referral_saas_account_campaign_review,
    upsert_referral_saas_account_campaign_policy_settings,
)
from services.referral_saas_reporting_service import (
    EXPORT_REQUEST_GUARDRAILS,
    EXPORT_REQUEST_REDACTIONS,
    ReferralSaasReportExportCommandError,
    ReportExportRequestIdempotencyConflict,
    build_referral_saas_report_export_preview,
    create_referral_saas_report_export_request,
    get_referral_saas_report,
    validate_referral_saas_report_export_request,
)
from services.referral_saas_support_case_service import (
    SUPPORT_CASE_GUARDRAILS,
    SUPPORT_CASE_QUEUE_GUARDRAILS,
    SUPPORT_CASE_REDACTIONS,
    ReferralSaasSupportCaseCommandError,
    SupportCaseIdempotencyConflict,
    SupportCaseNotFound,
    SupportCaseUnsafePayload,
    SupportCaseValidationError,
    add_referral_saas_support_case_note,
    change_referral_saas_support_case_status,
    create_referral_saas_support_case,
    get_referral_saas_support_case,
    list_referral_saas_operator_support_queue,
    list_referral_saas_support_cases,
)
from services.referral_saas_integrations_configuration_service import (
    CREDENTIAL_REQUEST_GUARDRAILS,
    CREDENTIAL_REQUEST_REDACTIONS,
    INTEGRATION_CONFIGURATION_GUARDRAILS,
    INTEGRATION_CONFIGURATION_REDACTIONS,
    INTEGRATION_EXECUTION_GUARDRAILS,
    INTEGRATION_EXECUTION_REDACTIONS,
    IntegrationCredentialRequestNotFound,
    IntegrationConfigurationIdempotencyConflict,
    IntegrationConfigurationUnsafePayload,
    IntegrationConfigurationValidationError,
    ReferralSaasIntegrationConfigurationCommandError,
    assert_safe_referral_saas_integration_execution_payload,
    build_referral_saas_integration_execution_readiness,
    create_referral_saas_integration_credential_request,
    get_referral_saas_integration_credential_request,
    get_referral_saas_integration_configuration,
    list_referral_saas_integration_credential_requests,
    record_referral_saas_integration_credential_execution_check,
    record_referral_saas_integration_credential_review_decision,
    record_referral_saas_api_access_verification,
    record_referral_saas_message_provider_test,
    record_referral_saas_webhook_test_dispatch,
    upsert_referral_saas_integration_configuration,
    validate_referral_saas_integration_configuration,
)
from services.referral_saas_technical_setup_service import (
    build_referral_saas_technical_setup_readiness,
)
from services.referral_saas_validation_service import (
    build_referral_saas_validation_result,
)
from utils.security import require_session_key

router = APIRouter(
    prefix="/v1/referral-saas",
    tags=["Referral SaaS"],
)

REFERRAL_SAAS_ACCOUNT_READER_ROLES = {
    "ADMIN",
    "SYSTEM_ADMIN",
    "DISTRIBUTION_ADMIN",
    "PLATFORM_ADMIN",
}

REFERRAL_SAAS_ACCOUNT_CONTEXTS = {"runtime", "setup"}
MAX_ACCOUNT_LIST_LIMIT = 100
CAMPAIGN_READINESS_NOT_FOUND_BLOCKERS = {"CAMPAIGN_NOT_FOUND", "TENANT_MISMATCH"}
LINK_CODE_GUARDRAILS = {
    "CUSTOMER_SCOPED_LINK_CODE_WRAPPER",
    "ACCOUNT_SCOPE_RESOLVED_INTERNALLY",
    "ACTIVE_CAMPAIGN_REQUIRED",
    "NO_TENANT_CODE_EXPOSURE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_WEBHOOK_DELIVERY",
    "NO_BILLING_OR_MONEY_MOVEMENT",
}
LINK_CODE_REDACTIONS = {
    "internal_tenant_identifier",
    "raw_ucn",
    "payload_hash",
    "reward",
    "funding",
    "settlement",
    "wallet",
}
REPORT_GUARDRAILS = {
    "CUSTOMER_SCOPED_REPORT_WRAPPER",
    "ACCOUNT_SCOPE_RESOLVED_INTERNALLY",
    "NO_TENANT_CODE_EXPOSURE",
    "NO_REPORT_MUTATION",
    "NO_EXPORT_CREATION",
    "NO_STORAGE_OR_DELIVERY",
    "NO_BILLING_OR_MONEY_MOVEMENT",
}
REPORT_EXPORT_REQUEST_GUARDRAILS = {
    "CUSTOMER_SCOPED_REPORT_EXPORT_REQUEST",
    "ACCOUNT_SCOPE_RESOLVED_INTERNALLY",
    *EXPORT_REQUEST_GUARDRAILS,
}
REPORT_REDACTIONS = {
    "internal_tenant_identifier",
    "internal_report_scope",
    "raw_ucn",
    "payload_hash",
    "provider_payload",
    "reward",
    "funding",
    "settlement",
    "wallet",
}
REPORT_EXPORT_REQUEST_REDACTIONS = {
    *REPORT_REDACTIONS,
    *EXPORT_REQUEST_REDACTIONS,
}
SUPPORT_CASE_ROUTE_GUARDRAILS = {
    *SUPPORT_CASE_GUARDRAILS,
}
SUPPORT_QUEUE_ROUTE_GUARDRAILS = {
    *SUPPORT_CASE_QUEUE_GUARDRAILS,
}
SUPPORT_CASE_ROUTE_REDACTIONS = {
    *SUPPORT_CASE_REDACTIONS,
}
INTEGRATION_CONFIGURATION_ROUTE_GUARDRAILS = {
    *INTEGRATION_CONFIGURATION_GUARDRAILS,
}
INTEGRATION_CONFIGURATION_ROUTE_REDACTIONS = {
    *INTEGRATION_CONFIGURATION_REDACTIONS,
}
INTEGRATION_EXECUTION_ROUTE_GUARDRAILS = {
    *INTEGRATION_EXECUTION_GUARDRAILS,
}
INTEGRATION_EXECUTION_ROUTE_REDACTIONS = {
    *INTEGRATION_EXECUTION_REDACTIONS,
}


class ReferralSaasAccountReportExportRequest(BaseModel):
    format: str | None = Field(default=None, description="json or csv.")
    redaction_profile: str | None = Field(default=None)
    dimensions: list[str] | None = Field(default=None)
    filters: dict[str, Any] | None = Field(default=None)
    row_limit: int | None = Field(default=None)
    data_window_start: datetime | None = Field(default=None)
    data_window_end: datetime | None = Field(default=None)


class ReferralSaasAccountFoundationActivationRequest(BaseModel):
    accountScope: dict[str, Any] = Field(default_factory=dict)
    activation: dict[str, Any] | None = Field(default=None)
    reasonCode: str | None = Field(default=None)
    correlationId: str | None = Field(default=None)
    idempotencyKey: str | None = Field(default=None)


class ReferralSaasSupportCaseEvidenceLinkRequest(BaseModel):
    evidenceType: str | None = Field(default=None)
    evidenceRef: str | None = Field(default=None)
    safeStatus: str | None = Field(default=None)
    warningCode: str | None = Field(default=None)
    missingEvidenceCode: str | None = Field(default=None)
    metadata: dict[str, Any] | None = Field(default=None)
    redactions: list[str] | None = Field(default=None)


class ReferralSaasSupportCaseCreateRequest(BaseModel):
    accountScope: dict[str, Any] = Field(default_factory=dict)
    category: str | None = Field(default=None)
    priority: str | None = Field(default=None)
    title: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    sourceSurface: str | None = Field(default=None)
    evidenceLinks: list[ReferralSaasSupportCaseEvidenceLinkRequest] | None = Field(
        default=None
    )
    reasonCode: str | None = Field(default=None)
    correlationId: str | None = Field(default=None)
    idempotencyKey: str | None = Field(default=None)


class ReferralSaasSupportCaseNoteRequest(BaseModel):
    accountScope: dict[str, Any] = Field(default_factory=dict)
    noteType: str | None = Field(default=None)
    noteText: str | None = Field(default=None)
    reasonCode: str | None = Field(default=None)
    correlationId: str | None = Field(default=None)
    idempotencyKey: str | None = Field(default=None)


class ReferralSaasSupportCaseStatusRequest(BaseModel):
    accountScope: dict[str, Any] = Field(default_factory=dict)
    status: str | None = Field(default=None)
    transitionReason: str | None = Field(default=None)
    reasonCode: str | None = Field(default=None)
    correlationId: str | None = Field(default=None)
    idempotencyKey: str | None = Field(default=None)


class ReferralSaasIntegrationConfigurationRequest(BaseModel):
    accountScope: dict[str, Any] = Field(default_factory=dict)
    apiEnvironment: dict[str, Any] | None = Field(default=None)
    webhookIntent: dict[str, Any] | None = Field(default=None)
    messageProviders: dict[str, Any] | None = Field(default=None)
    reasonCode: str | None = Field(default=None)
    correlationId: str | None = Field(default=None)
    idempotencyKey: str | None = Field(default=None)


class ReferralSaasApiAccessVerificationRequest(BaseModel):
    accountScope: dict[str, Any] = Field(default_factory=dict)
    verification: dict[str, Any] | None = Field(default=None)
    reasonCode: str | None = Field(default=None)
    correlationId: str | None = Field(default=None)
    idempotencyKey: str | None = Field(default=None)


class ReferralSaasWebhookTestDispatchRequest(BaseModel):
    accountScope: dict[str, Any] = Field(default_factory=dict)
    webhookTest: dict[str, Any] | None = Field(default=None)
    reasonCode: str | None = Field(default=None)
    correlationId: str | None = Field(default=None)
    idempotencyKey: str | None = Field(default=None)


class ReferralSaasMessageProviderTestRequest(BaseModel):
    accountScope: dict[str, Any] = Field(default_factory=dict)
    messageProviderTest: dict[str, Any] | None = Field(default=None)
    reasonCode: str | None = Field(default=None)
    correlationId: str | None = Field(default=None)
    idempotencyKey: str | None = Field(default=None)


class ReferralSaasCredentialRequestCreateRequest(BaseModel):
    accountScope: dict[str, Any] = Field(default_factory=dict)
    credentialRequest: dict[str, Any] | None = Field(default=None)
    reasonCode: str | None = Field(default=None)
    correlationId: str | None = Field(default=None)
    idempotencyKey: str | None = Field(default=None)


class ReferralSaasCredentialRequestReviewDecisionRequest(BaseModel):
    accountScope: dict[str, Any] = Field(default_factory=dict)
    reviewDecision: dict[str, Any] | None = Field(default=None)
    reasonCode: str | None = Field(default=None)
    correlationId: str | None = Field(default=None)
    idempotencyKey: str | None = Field(default=None)


class ReferralSaasCredentialExecutionCheckRequest(BaseModel):
    accountScope: dict[str, Any] = Field(default_factory=dict)
    executionCheck: dict[str, Any] | None = Field(default=None)
    reasonCode: str | None = Field(default=None)
    correlationId: str | None = Field(default=None)
    idempotencyKey: str | None = Field(default=None)


def _require_referral_saas_account_reader(identity: dict[str, Any]) -> dict[str, Any]:
    role = str(identity.get("role") or "").upper()
    if role not in REFERRAL_SAAS_ACCOUNT_READER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "permission_denied",
                "message": "API key is not authorised for Referral SaaS accounts.",
            },
        )
    return identity


def _has_readiness_blocker(readiness: dict[str, Any], codes: set[str]) -> bool:
    return any(
        str(blocker.get("code") or "").upper() in codes
        for blocker in readiness.get("blockers", [])
        if isinstance(blocker, dict)
    )


def _redact_internal_scope_keys(value: Any) -> Any:
    internal_scope_keys = {
        "tenant_code",
        "tenantCode",
        "internal_tenant_code",
        "internalTenantCode",
        "tenant_scope",
        "tenantScope",
    }
    if isinstance(value, dict):
        return {
            key: _redact_internal_scope_keys(item)
            for key, item in value.items()
            if key not in internal_scope_keys
        }
    if isinstance(value, list):
        return [_redact_internal_scope_keys(item) for item in value]
    return value


def _link_issue_status(body: dict[str, Any], status_code: int) -> str:
    error_code = str(body.get("error_code") or "")
    if error_code == "MISSING_FIELDS":
        return "REJECTED_MISSING_FIELDS"
    if error_code == "ACCEPTED_TERMS_REQUIRED":
        return "REJECTED_TERMS_REQUIRED"
    if status_code >= 400:
        return "FAILED"
    return "CREATED" if body.get("created") else "EXISTING"


def _reject_unsafe_link_code_payload(value: Any) -> None:
    unsafe_keys = {
        "tenant_code",
        "tenantCode",
        "internal_tenant_code",
        "internalTenantCode",
        "activate",
        "goLive",
        "campaignActivation",
        "webhook",
        "credential",
        "credentials",
        "providerSecret",
        "secret",
        "invite",
        "seat",
        "seatId",
        "authClaim",
        "authClaims",
        "billing",
        "rewardAmount",
        "rewardAmounts",
        "funding",
        "fulfilment",
        "settlement",
        "commission",
        "wallet",
        "invoice",
        "payout",
        "sponsorBilling",
    }

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, nested in node.items():
                if str(key) in unsafe_keys:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "REJECTED_UNSAFE_PAYLOAD",
                            "message": (
                                "Customer-scoped Links and Codes does not accept "
                                "tenant codes, credentials, activation, webhook, "
                                "billing, money, invite, seat, or auth payloads."
                            ),
                            "guardrails": sorted(LINK_CODE_GUARDRAILS),
                            "redactions": sorted(LINK_CODE_REDACTIONS),
                            "no_campaign_activation_confirmed": True,
                            "no_webhook_delivery_confirmed": True,
                            "no_billing_or_money_movement_confirmed": True,
                        },
                    )
                walk(nested)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(value)


def _reject_unsafe_report_export_request_payload(value: Any) -> None:
    unsafe_keys = {
        "tenant_code",
        "tenantCode",
        "internal_tenant_code",
        "internalTenantCode",
        "downloadUrl",
        "download_url",
        "filePath",
        "file_path",
        "storageBucket",
        "storage_bucket",
        "storageKey",
        "storage_key",
        "delivery",
        "deliver",
        "scheduledDelivery",
        "webhook",
        "credential",
        "credentials",
        "providerSecret",
        "secret",
        "billing",
        "invoice",
        "rewardAmount",
        "rewardAmounts",
        "funding",
        "fulfilment",
        "settlement",
        "commission",
        "wallet",
        "payout",
        "sponsorBilling",
    }

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, nested in node.items():
                if str(key) in unsafe_keys:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "REJECTED_UNSAFE_PAYLOAD",
                            "message": (
                                "Customer-scoped report export requests do not "
                                "accept tenant codes, file paths, download URLs, "
                                "storage, delivery, webhook, credential, billing, "
                                "or money payloads."
                            ),
                            "guardrails": sorted(REPORT_EXPORT_REQUEST_GUARDRAILS),
                            "redactions": sorted(REPORT_EXPORT_REQUEST_REDACTIONS),
                            "no_export_file_created_confirmed": True,
                            "no_download_url_created_confirmed": True,
                            "no_storage_or_delivery_confirmed": True,
                            "no_billing_or_money_movement_confirmed": True,
                        },
                    )
                walk(nested)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(value)


def _reject_unsafe_support_case_payload(value: Any) -> None:
    unsafe_keys = {
        "tenant_code",
        "tenantCode",
        "internal_tenant_code",
        "internalTenantCode",
        "rawUcn",
        "raw_ucn",
        "providerPayload",
        "provider_payload",
        "auditPayload",
        "audit_payload",
        "dlqPayload",
        "dlq_payload",
        "sqlError",
        "sql_error",
        "stackTrace",
        "stack_trace",
        "repair",
        "replay",
        "retry",
        "requeue",
        "override",
        "activate",
        "activation",
        "webhook",
        "credential",
        "credentials",
        "secret",
        "token",
        "authClaim",
        "authClaims",
        "invite",
        "seat",
        "billing",
        "invoice",
        "rewardAmount",
        "rewardAmounts",
        "funding",
        "fulfilment",
        "settlement",
        "commission",
        "wallet",
        "payout",
        "sponsorBilling",
    }

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, nested in node.items():
                if str(key) in unsafe_keys:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "REJECTED_UNSAFE_PAYLOAD",
                            "message": (
                                "Support cases only accept safe selected-customer "
                                "case summaries and evidence references. They do "
                                "not accept raw evidence, repair/replay/retry, "
                                "credential, invite, seat, billing, or money payloads."
                            ),
                            "guardrails": sorted(SUPPORT_CASE_ROUTE_GUARDRAILS),
                            "redactions": sorted(SUPPORT_CASE_ROUTE_REDACTIONS),
                            "no_repair_replay_retry_confirmed": True,
                            "no_credential_or_auth_claim_change_confirmed": True,
                            "no_billing_or_money_movement_confirmed": True,
                        },
                    )
                walk(nested)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(value)


def _require_active_campaign(campaign_code: str, campaign: Any | None) -> None:
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "campaign_not_found",
                "message": "Campaign was not found for the selected customer.",
                "guardrails": sorted(LINK_CODE_GUARDRAILS),
                "redactions": sorted(LINK_CODE_REDACTIONS),
            },
        )

    campaign_status = str(getattr(campaign, "status", "") or "").upper()
    campaign_lifecycle = str(getattr(campaign, "lifecycle", "") or "").upper()
    if campaign_status != "ACTIVE" or campaign_lifecycle != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "campaign_not_active",
                "message": (
                    f"{campaign_code} must be activated before referral links "
                    "or codes are issued or validated for this customer."
                ),
                "guardrails": sorted(LINK_CODE_GUARDRAILS),
                "redactions": sorted(LINK_CODE_REDACTIONS),
                "no_campaign_activation_confirmed": True,
                "no_webhook_delivery_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            },
        )


async def _resolve_active_campaign_link_code_context(
    *,
    account_ref: str,
    campaign_code: str,
    account_scope: dict[str, Any],
) -> tuple[str, Any, Any]:
    if not isinstance(account_scope, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "accountScope is required.",
                "guardrails": sorted(LINK_CODE_GUARDRAILS),
                "redactions": sorted(LINK_CODE_REDACTIONS),
            },
        )
    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = (_optional_text(account_scope.get("context")) or "setup").lower()
    if not ref_type or not external_ref:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "accountScope.refType and accountScope.externalRef are required.",
                "guardrails": sorted(LINK_CODE_GUARDRAILS),
                "redactions": sorted(LINK_CODE_REDACTIONS),
            },
        )

    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)
    campaign = await get_referral_saas_account_campaign(
        tenant_code=account.tenant_code,
        campaign_code=campaign_code,
    )
    _require_active_campaign(campaign_code, campaign)
    return normalised_context, account, campaign


async def _resolve_referral_saas_account_context(
    *,
    ref_type: str,
    external_ref: str,
    context: str,
) -> tuple[str, Any]:
    normalised_context = str(context or "").strip().lower()
    if normalised_context not in REFERRAL_SAAS_ACCOUNT_CONTEXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "context must be runtime or setup.",
            },
        )

    try:
        if normalised_context == "setup":
            account = await resolve_setup_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
        else:
            account = await resolve_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
    except AccountFoundationResolutionError as exc:
        raise _resolution_error(exc) from exc

    return normalised_context, account


def _assert_account_path_scope(account_ref: str, account: Any) -> str:
    safe_account_ref = _optional_text(account_ref)
    if safe_account_ref not in {account.account_id, account.account_code}:
        raise _membership_invitation_error(
            MembershipInvitationUnsafeScope(
                "Path account reference does not match resolved account context."
            )
        )
    return safe_account_ref


def _report_filters(
    *,
    beneficiary_type: str | None,
    campaign_ref: str | None,
    campaign_code: str | None,
    link_code_status: str | None,
    product: str | None,
    reward_source: str | None,
    reward_status: str | None,
    reward_type: str | None,
    sponsor_code: str | None,
    source_type: str | None,
    sub_product: str | None,
) -> dict[str, str]:
    return {
        key: value.strip()
        for key, value in {
            "beneficiary_type": beneficiary_type,
            "campaign_ref": campaign_ref,
            "campaign_code": campaign_code,
            "link_code_status": link_code_status,
            "product": product,
            "reward_source": reward_source,
            "reward_status": reward_status,
            "reward_type": reward_type,
            "sponsor_code": sponsor_code,
            "source_type": source_type,
            "sub_product": sub_product,
        }.items()
        if value is not None and value.strip()
    }


async def _resolve_maybe_awaitable(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def _redact_customer_report_payload(value: Any) -> Any:
    hidden_keys = {
        "tenant_code",
        "tenantCode",
        "tenant_scope",
        "tenantScope",
        "internal_tenant_code",
        "internalTenantCode",
    }
    if isinstance(value, dict):
        return {
            key: _redact_customer_report_payload(nested)
            for key, nested in value.items()
            if str(key) not in hidden_keys
        }
    if isinstance(value, list):
        return [_redact_customer_report_payload(item) for item in value]
    return value


def _customer_report_account_scope(account: Any) -> dict[str, Any]:
    return {
        "source": "selected_customer_account",
        "account_ref": account.account_id,
        "account_code": account.account_code,
        "external_tenant_ref": account.external_ref,
    }


def _customer_report_guardrail() -> str:
    return (
        "Customer-scoped Referral SaaS report wrapper. The selected account "
        "resolves reporting scope internally; callers do not enter or receive "
        "tenant code. This endpoint does not mutate report data, create export "
        "files, write storage records, deliver email, create credentials, or "
        "move billing, funding, reward, settlement, wallet, invoice, or DLaaS "
        "marketplace records."
    )


def _support_case_resolution_context(value: str | None) -> str:
    normalised_context = (_optional_text(value) or "support").lower()
    if normalised_context == "support":
        return "setup"
    return normalised_context


def _resolution_error(exc: AccountFoundationResolutionError) -> HTTPException:
    if isinstance(exc, InvalidExternalReferenceType):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, ExternalReferenceNotFound):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(
        exc,
        (
            ExternalReferenceConflict,
            ExternalReferenceNotActive,
            AccountNotResolvable,
            TenantLinkNotResolvable,
        ),
    ):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return HTTPException(
        status_code=status_code,
        detail={
            "code": exc.safe_code,
            "message": str(exc),
        },
    )


def _command_error(exc: AccountSetupCommandError) -> HTTPException:
    if isinstance(exc, AccountSetupPermissionDenied):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, AccountSetupDraftNotFound):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(
        exc,
        (
            AccountSetupInvalidDraftState,
            AccountSetupMissingScope,
            AccountSetupDuplicateInternalTenantScope,
            AccountSetupDuplicateReference,
        ),
    ):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return HTTPException(
        status_code=status_code,
        detail={
            "code": exc.safe_code,
            "message": str(exc),
            "guardrails": _account_creation_guardrails(),
            "redactions": ["internal_tenant_identifier"],
            "no_adjacent_live_action_confirmed": True,
        },
    )


def _membership_invitation_error(exc: MembershipInvitationCommandError) -> HTTPException:
    if isinstance(exc, MembershipInvitationValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, (MembershipInvitationUnsafePayload, MembershipInvitationUnsafeScope)):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(
        exc,
        (
            MembershipInvitationAccountNotReady,
            MembershipInvitationDuplicate,
            MembershipInvitationDeliveryNotInvited,
            MembershipInvitationDeliveryProviderNotConfigured,
            MembershipInvitationNotEditable,
            MembershipInvitationNotFound,
            MembershipInvitationIdempotencyConflict,
        ),
    ):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return HTTPException(
        status_code=status_code,
        detail={
            "code": exc.safe_code,
            "message": str(exc),
            "guardrails": _membership_invitation_guardrails(),
            "redactions": _membership_invitation_redactions(),
            "no_invite_delivery_confirmed": True,
            "no_auth_claim_change_confirmed": True,
            "no_seat_assignment_confirmed": True,
            "no_money_movement_confirmed": True,
        },
    )


def _membership_activation_error(exc: MembershipInvitationCommandError) -> HTTPException:
    if isinstance(exc, MembershipInvitationValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, (MembershipInvitationUnsafePayload, MembershipInvitationUnsafeScope)):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, MembershipInvitationIdempotencyConflict):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_409_CONFLICT

    return HTTPException(
        status_code=status_code,
        detail={
            "code": exc.safe_code,
            "message": str(exc),
            "guardrails": _membership_activation_guardrails(),
            "redactions": _membership_activation_redactions(),
            "no_invite_delivery_confirmed": True,
            "no_auth_claim_change_confirmed": True,
            "no_seat_assignment_confirmed": True,
            "no_money_movement_confirmed": True,
        },
    )


def _access_provisioning_error(exc: MembershipInvitationCommandError) -> HTTPException:
    if isinstance(exc, MembershipInvitationValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, (MembershipInvitationUnsafePayload, MembershipInvitationUnsafeScope)):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, MembershipInvitationIdempotencyConflict):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_409_CONFLICT

    return HTTPException(
        status_code=status_code,
        detail={
            "code": exc.safe_code,
            "message": str(exc),
            "guardrails": _access_provisioning_guardrails(),
            "redactions": _access_provisioning_redactions(),
            "no_invite_delivery_confirmed": True,
            "no_auth_claim_change_confirmed": True,
            "no_credential_creation_confirmed": True,
            "no_campaign_activation_confirmed": True,
            "no_go_live_change_confirmed": True,
            "no_money_movement_confirmed": True,
        },
    )


def _campaign_setup_error(exc: ReferralSaasCampaignCommandError) -> HTTPException:
    if isinstance(exc, CampaignSetupValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(
        exc,
        (
            CampaignSetupAccountNotReady,
            CampaignSetupDuplicate,
            CampaignSetupIdempotencyConflict,
        ),
    ):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return HTTPException(
        status_code=status_code,
        detail={
            "code": exc.safe_code,
            "message": str(exc),
            "guardrails": list(CAMPAIGN_SETUP_GUARDRAILS),
            "redactions": list(CAMPAIGN_SETUP_REDACTIONS),
            "no_campaign_activation_confirmed": True,
            "no_link_generation_confirmed": True,
            "no_validation_track_created_confirmed": True,
            "no_policy_write_confirmed": True,
            "no_webhook_delivery_confirmed": True,
            "no_money_movement_confirmed": True,
        },
    )


def _campaign_policy_settings_error(
    exc: ReferralSaasCampaignCommandError,
) -> HTTPException:
    if isinstance(exc, CampaignPolicySettingsValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, CampaignPolicySettingsCampaignNotFound):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(
        exc,
        (
            CampaignPolicySettingsAccountNotReady,
            CampaignPolicySettingsIdempotencyConflict,
        ),
    ):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return HTTPException(
        status_code=status_code,
        detail={
            "code": exc.safe_code,
            "message": str(exc),
            "guardrails": list(CAMPAIGN_POLICY_SETTINGS_GUARDRAILS),
            "redactions": list(CAMPAIGN_POLICY_SETTINGS_REDACTIONS),
            "no_campaign_activation_confirmed": True,
            "no_link_generation_confirmed": True,
            "no_validation_track_created_confirmed": True,
            "no_webhook_delivery_confirmed": True,
            "no_money_movement_confirmed": True,
        },
    )


def _campaign_review_error(exc: ReferralSaasCampaignCommandError) -> HTTPException:
    if isinstance(exc, CampaignReviewValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, CampaignReviewCampaignNotFound):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(
        exc,
        (
            CampaignReviewNotReady,
            CampaignReviewInvalidState,
            CampaignReviewIdempotencyConflict,
        ),
    ):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return HTTPException(
        status_code=status_code,
        detail={
            "code": exc.safe_code,
            "message": str(exc),
            "guardrails": list(CAMPAIGN_REVIEW_GUARDRAILS),
            "redactions": list(CAMPAIGN_REVIEW_REDACTIONS),
            "no_campaign_activation_confirmed": True,
            "no_link_generation_confirmed": True,
            "no_validation_track_created_confirmed": True,
            "no_webhook_delivery_confirmed": True,
            "no_invite_or_seat_change_confirmed": True,
            "no_money_movement_confirmed": True,
        },
    )


def _campaign_activation_error(exc: ReferralSaasCampaignCommandError) -> HTTPException:
    if isinstance(exc, CampaignActivationValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, CampaignActivationCampaignNotFound):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(
        exc,
        (
            CampaignActivationAlreadyActive,
            CampaignActivationNotReady,
            CampaignActivationIdempotencyConflict,
        ),
    ):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return HTTPException(
        status_code=status_code,
        detail={
            "code": exc.safe_code,
            "message": str(exc),
            "guardrails": list(CAMPAIGN_ACTIVATION_GUARDRAILS),
            "redactions": list(CAMPAIGN_ACTIVATION_REDACTIONS),
            "no_link_generation_confirmed": True,
            "no_validation_track_created_confirmed": True,
            "no_webhook_delivery_confirmed": True,
            "no_invite_or_seat_change_confirmed": True,
            "no_credential_creation_confirmed": True,
            "no_billing_or_money_movement_confirmed": True,
        },
    )


def _profile_maintenance_error(exc: AccountProfileMaintenanceError) -> HTTPException:
    if isinstance(exc, AccountProfilePermissionDenied):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, AccountProfileNotFound):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, AccountProfileValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, (AccountProfileNotMaintainable, AccountProfileUnsafePayload)):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return HTTPException(
        status_code=status_code,
        detail={
            "code": exc.safe_code,
            "message": str(exc),
            "guardrails": _profile_maintenance_guardrails(),
            "redactions": _profile_maintenance_redactions(),
            "no_external_reference_rotation_confirmed": True,
            "no_account_activation_confirmed": True,
            "no_membership_write_confirmed": True,
            "no_money_movement_confirmed": True,
        },
    )


def _account_foundation_activation_error(
    exc: AccountFoundationActivationError,
) -> HTTPException:
    if isinstance(exc, AccountFoundationActivationPermissionDenied):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, AccountFoundationActivationNotFound):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, AccountFoundationActivationValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(
        exc,
        (
            AccountFoundationActivationNotReady,
            AccountFoundationActivationIdempotencyConflict,
        ),
    ):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return HTTPException(
        status_code=status_code,
        detail={
            "code": exc.safe_code,
            "message": str(exc),
            "guardrails": list(ACCOUNT_FOUNDATION_ACTIVATION_GUARDRAILS),
            "redactions": list(ACCOUNT_FOUNDATION_ACTIVATION_REDACTIONS),
            "no_membership_write_confirmed": True,
            "no_seat_assignment_confirmed": True,
            "no_invite_delivery_confirmed": True,
            "no_auth_claim_change_confirmed": True,
            "no_credential_creation_confirmed": True,
            "no_campaign_activation_confirmed": True,
            "no_go_live_action_confirmed": True,
            "no_billing_or_money_movement_confirmed": True,
        },
    )


def _support_case_error(exc: ReferralSaasSupportCaseCommandError) -> HTTPException:
    if isinstance(exc, SupportCaseValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, SupportCaseNotFound):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, SupportCaseIdempotencyConflict):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, SupportCaseUnsafePayload):
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return HTTPException(
        status_code=status_code,
        detail={
            "code": exc.safe_code,
            "message": str(exc),
            "guardrails": sorted(SUPPORT_CASE_ROUTE_GUARDRAILS),
            "redactions": sorted(SUPPORT_CASE_ROUTE_REDACTIONS),
            "no_repair_replay_retry_confirmed": True,
            "no_referral_or_campaign_mutation_confirmed": True,
            "no_progress_or_attribution_mutation_confirmed": True,
            "no_report_or_export_mutation_confirmed": True,
            "no_invite_delivery_confirmed": True,
            "no_credential_or_auth_claim_change_confirmed": True,
            "no_billing_or_money_movement_confirmed": True,
        },
    )


def _integration_configuration_error(
    exc: ReferralSaasIntegrationConfigurationCommandError,
) -> HTTPException:
    if isinstance(exc, IntegrationConfigurationValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, IntegrationConfigurationIdempotencyConflict):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, IntegrationConfigurationUnsafePayload):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, IntegrationCredentialRequestNotFound):
        status_code = status.HTTP_404_NOT_FOUND
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return HTTPException(
        status_code=status_code,
        detail={
            "code": exc.safe_code,
            "message": str(exc),
            "guardrails": sorted(
                set(INTEGRATION_CONFIGURATION_ROUTE_GUARDRAILS)
                | set(CREDENTIAL_REQUEST_GUARDRAILS)
            ),
            "redactions": sorted(
                set(INTEGRATION_CONFIGURATION_ROUTE_REDACTIONS)
                | set(CREDENTIAL_REQUEST_REDACTIONS)
            ),
            "no_secret_or_credential_storage_confirmed": True,
            "no_credential_creation_confirmed": True,
            "no_credential_lifecycle_execution_confirmed": True,
            "no_credential_reveal_or_download_confirmed": True,
            "no_vault_write_confirmed": True,
            "no_provider_call_confirmed": True,
            "no_webhook_dispatch_confirmed": True,
            "no_invite_delivery_confirmed": True,
            "no_membership_activation_confirmed": True,
            "no_seat_assignment_confirmed": True,
            "no_auth_claim_change_confirmed": True,
            "no_campaign_activation_confirmed": True,
            "no_go_live_action_confirmed": True,
            "no_billing_or_money_movement_confirmed": True,
        },
    )


@router.post("/accounts/from-draft")
async def create_referral_saas_account_from_draft(
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    draft_ref = _optional_text(payload.get("draft_ref"))
    internal_tenant_code = _optional_text(payload.get("internal_tenant_code"))
    idempotency_key = _optional_text(payload.get("idempotency_key"))
    if not draft_ref or not internal_tenant_code or not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "draft_ref, internal_tenant_code, and idempotency_key are required."
                ),
                "guardrails": _account_creation_guardrails(),
                "redactions": ["internal_tenant_identifier"],
                "no_adjacent_live_action_confirmed": True,
            },
        )

    try:
        result = await create_durable_account_from_onboarding_draft(
            draft_ref=draft_ref,
            tenant_code=internal_tenant_code,
            actor_ref=_actor_ref(admin_identity),
            actor_role=str(admin_identity.get("role") or "").upper(),
            correlation_id=_optional_text(payload.get("correlation_id")) or None,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_ACCOUNT_FROM_DRAFT",
                    "draft_ref": draft_ref,
                    "idempotency_key": idempotency_key,
                }
            ),
        )
    except AccountSetupCommandError as exc:
        raise _command_error(exc) from exc

    return {
        "status": "created",
        "account": result.to_safe_dict(),
        "guardrails": _account_creation_guardrails(),
        "redactions": ["internal_tenant_identifier"],
        "no_adjacent_live_action_confirmed": True,
    }


@router.post("/accounts/{account_ref}/activation-requests")
async def request_referral_saas_account_foundation_activation(
    account_ref: str,
    request: ReferralSaasAccountFoundationActivationRequest,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    account_scope = request.accountScope or {}
    activation = request.activation or {}
    idempotency_key = _optional_text(request.idempotencyKey)
    correlation_id = _optional_text(request.correlationId)
    reason_code = (
        _optional_text(request.reasonCode)
        or "CUSTOMER_ACCOUNT_FOUNDATION_ACTIVATION"
    )

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = (_optional_text(account_scope.get("context")) or "setup").lower()
    if not ref_type or not external_ref or not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": list(ACCOUNT_FOUNDATION_ACTIVATION_GUARDRAILS),
                "redactions": list(ACCOUNT_FOUNDATION_ACTIVATION_REDACTIONS),
                "no_membership_write_confirmed": True,
                "no_seat_assignment_confirmed": True,
                "no_invite_delivery_confirmed": True,
                "no_auth_claim_change_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            },
        )
    if context != "setup":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.context must be setup for account foundation "
                    "activation."
                ),
                "guardrails": list(ACCOUNT_FOUNDATION_ACTIVATION_GUARDRAILS),
                "redactions": list(ACCOUNT_FOUNDATION_ACTIVATION_REDACTIONS),
            },
        )

    seat_types = _normalise_activation_request_seat_types(activation.get("seatTypes"))
    try:
        account = await resolve_setup_account_by_external_reference(
            ref_type=ref_type,
            external_ref=external_ref,
        )
    except AccountFoundationResolutionError as exc:
        raise _resolution_error(exc) from exc

    safe_account_ref = _assert_account_path_scope(account_ref, account)
    command_payload = {
        "accountScope": {
            "accountRef": safe_account_ref,
            "refType": ref_type,
            "externalRef": external_ref,
            "context": context,
        },
        "activation": {"seatTypes": seat_types},
        "reasonCode": reason_code,
    }

    try:
        result = await activate_referral_saas_account_foundation(
            account_id=account.account_id,
            tenant_code=account.tenant_code,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            seat_types=seat_types,
            actor_ref=_actor_ref(admin_identity),
            actor_role=str(admin_identity.get("role") or "").upper(),
            reason_code=reason_code,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_ACCOUNT_FOUNDATION_ACTIVATION",
                    "account_ref": safe_account_ref,
                    "idempotency_key": idempotency_key,
                }
            ),
            command_payload_hash=hash_payload(command_payload),
        )
    except AccountFoundationActivationError as exc:
        raise _account_foundation_activation_error(exc) from exc

    return {
        "status": "ok",
        "context": context,
        "account": account.to_safe_dict(),
        "activation": result.to_safe_dict(),
        "guardrails": list(ACCOUNT_FOUNDATION_ACTIVATION_GUARDRAILS),
        "redactions": list(ACCOUNT_FOUNDATION_ACTIVATION_REDACTIONS),
        "no_membership_write_confirmed": True,
        "no_seat_assignment_confirmed": True,
        "no_invite_delivery_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_credential_creation_confirmed": True,
        "no_campaign_activation_confirmed": True,
        "no_go_live_action_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }


@router.post("/accounts/{account_ref}/membership-invitations")
async def record_referral_saas_membership_invitation(
    account_ref: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    _reject_unsafe_invitation_payload(payload)

    account_scope = payload.get("accountScope") or {}
    actor = payload.get("actor") or {}
    membership = payload.get("membership") or {}
    idempotency_key = _optional_text(payload.get("idempotencyKey"))
    correlation_id = _optional_text(payload.get("correlationId"))
    reason_code = _optional_text(payload.get("reasonCode")) or "ACCOUNT_SETUP_USER_ROLE"

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = (_optional_text(account_scope.get("context")) or "setup").lower()
    if not ref_type or not external_ref or not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": _membership_invitation_guardrails(),
                "redactions": _membership_invitation_redactions(),
                "no_invite_delivery_confirmed": True,
                "no_auth_claim_change_confirmed": True,
                "no_seat_assignment_confirmed": True,
                "no_money_movement_confirmed": True,
            },
        )
    if context not in REFERRAL_SAAS_ACCOUNT_CONTEXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "accountScope.context must be runtime or setup.",
            },
        )

    try:
        if context == "setup":
            account = await resolve_setup_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
        else:
            account = await resolve_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
    except AccountFoundationResolutionError as exc:
        raise _resolution_error(exc) from exc

    safe_account_ref = _optional_text(account_ref)
    if safe_account_ref not in {account.account_id, account.account_code}:
        raise _membership_invitation_error(
            MembershipInvitationUnsafeScope(
                "Path account reference does not match resolved account context."
            )
        )

    command_payload = {
        "accountScope": {
            "accountRef": safe_account_ref,
            "refType": ref_type,
            "externalRef": external_ref,
            "context": context,
        },
        "actor": actor,
        "membership": membership,
        "reasonCode": reason_code,
    }

    try:
        result = await record_referral_saas_membership_invitation_intent(
            account_id=account.account_id,
            tenant_code=account.tenant_code,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            actor_type=_optional_text(actor.get("actorType")) or "USER",
            subject=_optional_text(actor.get("subject")) or None,
            client_id=_optional_text(actor.get("clientId")) or None,
            email_hash=_optional_text(actor.get("emailHash")) or None,
            display_name=_optional_text(actor.get("displayName")) or None,
            role_family=_optional_text(membership.get("roleFamily")),
            permission_set=_optional_text(membership.get("permissionSet")),
            tenant_scope=(
                _optional_text(membership.get("tenantScope"))
                or "PRIMARY_ACCOUNT_TENANT"
            ),
            reason_code=reason_code,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_MEMBERSHIP_INVITATION_INTENT",
                    "account_ref": safe_account_ref,
                    "idempotency_key": idempotency_key,
                }
            ),
            command_payload_hash=hash_payload(command_payload),
            command_payload=payload,
            command_actor_ref=_actor_ref(admin_identity),
            command_actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except MembershipInvitationCommandError as exc:
        raise _membership_invitation_error(exc) from exc

    return {
        "status": "ok",
        "context": context,
        "account": account.to_safe_dict(),
        "invitation": result.to_safe_dict(),
        "guardrails": _membership_invitation_guardrails(),
        "redactions": _membership_invitation_redactions(),
        "no_invite_delivery_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_seat_assignment_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.patch("/accounts/{account_ref}/membership-invitations/{membership_ref}")
async def update_referral_saas_membership_invitation(
    account_ref: str,
    membership_ref: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    _reject_unsafe_invitation_payload(payload)

    account_scope = payload.get("accountScope") or {}
    actor = payload.get("actor") or {}
    membership = payload.get("membership") or {}
    idempotency_key = _optional_text(payload.get("idempotencyKey"))
    correlation_id = _optional_text(payload.get("correlationId"))
    reason_code = (
        _optional_text(payload.get("reasonCode"))
        or "CUSTOMER_PROFILE_ACCESS_INTENT_UPDATE"
    )

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = (_optional_text(account_scope.get("context")) or "setup").lower()
    role_family = _optional_text(membership.get("roleFamily"))
    permission_set = _optional_text(membership.get("permissionSet"))
    if (
        not ref_type
        or not external_ref
        or not idempotency_key
        or not correlation_id
        or not role_family
        or not permission_set
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "membership.roleFamily, membership.permissionSet, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": _membership_invitation_guardrails(),
                "redactions": _membership_invitation_redactions(),
                "no_invite_delivery_confirmed": True,
                "no_auth_claim_change_confirmed": True,
                "no_seat_assignment_confirmed": True,
                "no_money_movement_confirmed": True,
            },
        )
    if context not in REFERRAL_SAAS_ACCOUNT_CONTEXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "accountScope.context must be runtime or setup.",
            },
        )

    try:
        if context == "setup":
            account = await resolve_setup_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
        else:
            account = await resolve_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
    except AccountFoundationResolutionError as exc:
        raise _resolution_error(exc) from exc

    safe_account_ref = _optional_text(account_ref)
    safe_membership_ref = _optional_text(membership_ref)
    if safe_account_ref not in {account.account_id, account.account_code}:
        raise _membership_invitation_error(
            MembershipInvitationUnsafeScope(
                "Path account reference does not match resolved account context."
            )
        )

    command_payload = {
        "accountScope": {
            "accountRef": safe_account_ref,
            "refType": ref_type,
            "externalRef": external_ref,
            "context": context,
        },
        "membershipRef": safe_membership_ref,
        "actor": {
            "emailHashPresent": bool(_optional_text(actor.get("emailHash"))),
            "displayNamePresent": bool(_optional_text(actor.get("displayName"))),
        },
        "membership": {
            "roleFamily": role_family,
            "permissionSet": permission_set,
        },
        "reasonCode": reason_code,
    }

    try:
        result = await update_referral_saas_membership_invitation_intent(
            account_id=account.account_id,
            tenant_code=account.tenant_code,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            membership_id=safe_membership_ref,
            email_hash=_optional_text(actor.get("emailHash")) or None,
            display_name=_optional_text(actor.get("displayName")) or None,
            role_family=role_family,
            permission_set=permission_set,
            reason_code=reason_code,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_MEMBERSHIP_INVITATION_INTENT_UPDATE",
                    "account_ref": safe_account_ref,
                    "membership_ref": safe_membership_ref,
                    "idempotency_key": idempotency_key,
                }
            ),
            command_payload_hash=hash_payload(command_payload),
            command_payload=payload,
            command_actor_ref=_actor_ref(admin_identity),
            command_actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except MembershipInvitationCommandError as exc:
        raise _membership_invitation_error(exc) from exc

    return {
        "status": "ok",
        "context": context,
        "account": account.to_safe_dict(),
        "invitation": result.to_safe_dict(),
        "guardrails": _membership_invitation_guardrails(),
        "redactions": _membership_invitation_redactions(),
        "no_invite_delivery_confirmed": True,
        "no_membership_activation_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_seat_assignment_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.delete("/accounts/{account_ref}/membership-invitations/{membership_ref}")
async def cancel_referral_saas_membership_invitation(
    account_ref: str,
    membership_ref: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    _reject_unsafe_invitation_payload(payload)

    account_scope = payload.get("accountScope") or {}
    idempotency_key = _optional_text(payload.get("idempotencyKey"))
    correlation_id = _optional_text(payload.get("correlationId"))
    reason_code = (
        _optional_text(payload.get("reasonCode"))
        or "CUSTOMER_PROFILE_ACCESS_INTENT_CANCEL"
    )

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = (_optional_text(account_scope.get("context")) or "setup").lower()
    if not ref_type or not external_ref or not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": _membership_invitation_guardrails(),
                "redactions": _membership_invitation_redactions(),
                "no_invite_delivery_confirmed": True,
                "no_auth_claim_change_confirmed": True,
                "no_seat_assignment_confirmed": True,
                "no_money_movement_confirmed": True,
            },
        )
    if context not in REFERRAL_SAAS_ACCOUNT_CONTEXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "accountScope.context must be runtime or setup.",
            },
        )

    try:
        if context == "setup":
            account = await resolve_setup_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
        else:
            account = await resolve_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
    except AccountFoundationResolutionError as exc:
        raise _resolution_error(exc) from exc

    safe_account_ref = _optional_text(account_ref)
    safe_membership_ref = _optional_text(membership_ref)
    if safe_account_ref not in {account.account_id, account.account_code}:
        raise _membership_invitation_error(
            MembershipInvitationUnsafeScope(
                "Path account reference does not match resolved account context."
            )
        )

    command_payload = {
        "accountScope": {
            "accountRef": safe_account_ref,
            "refType": ref_type,
            "externalRef": external_ref,
            "context": context,
        },
        "membershipRef": safe_membership_ref,
        "reasonCode": reason_code,
    }

    try:
        result = await cancel_referral_saas_membership_invitation_intent(
            account_id=account.account_id,
            tenant_code=account.tenant_code,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            membership_id=safe_membership_ref,
            reason_code=reason_code,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_MEMBERSHIP_INVITATION_INTENT_CANCEL",
                    "account_ref": safe_account_ref,
                    "membership_ref": safe_membership_ref,
                    "idempotency_key": idempotency_key,
                }
            ),
            command_payload_hash=hash_payload(command_payload),
            command_payload=payload,
            command_actor_ref=_actor_ref(admin_identity),
            command_actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except MembershipInvitationCommandError as exc:
        raise _membership_invitation_error(exc) from exc

    return {
        "status": "ok",
        "context": context,
        "account": account.to_safe_dict(),
        "invitation": result.to_safe_dict(),
        "guardrails": _membership_invitation_guardrails(),
        "redactions": _membership_invitation_redactions(),
        "no_invite_delivery_confirmed": True,
        "no_membership_activation_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_seat_assignment_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.post("/accounts/{account_ref}/membership-invitations/{membership_ref}/delivery")
async def request_referral_saas_membership_invitation_delivery_route(
    account_ref: str,
    membership_ref: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)

    account_scope = payload.get("accountScope") or {}
    delivery = payload.get("delivery") or {}
    idempotency_key = _optional_text(payload.get("idempotencyKey"))
    correlation_id = _optional_text(payload.get("correlationId"))
    reason_code = (
        _optional_text(payload.get("reasonCode"))
        or "CUSTOMER_PROFILE_INVITE_DELIVERY_REQUEST"
    )

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = (_optional_text(account_scope.get("context")) or "setup").lower()
    provider_ref = _optional_text(delivery.get("providerRef"))
    channel = _optional_text(delivery.get("channel"))
    template_ref = _optional_text(delivery.get("templateRef"))
    recipient_hash = _optional_text(delivery.get("recipientHash"))

    if (
        not ref_type
        or not external_ref
        or not idempotency_key
        or not correlation_id
        or not provider_ref
        or not channel
        or not template_ref
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, delivery.providerRef, "
                    "delivery.channel, delivery.templateRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": _membership_invitation_guardrails()
                + ["NO_PROVIDER_SECRET_EXPOSURE"],
                "redactions": _membership_invitation_redactions()
                + ["recipient_hash", "provider_secret"],
                "no_invite_delivery_confirmed": True,
                "no_membership_activation_confirmed": True,
                "no_auth_claim_change_confirmed": True,
                "no_seat_assignment_confirmed": True,
                "no_money_movement_confirmed": True,
            },
        )
    if context not in REFERRAL_SAAS_ACCOUNT_CONTEXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "accountScope.context must be runtime or setup.",
            },
        )

    try:
        if context == "setup":
            account = await resolve_setup_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
        else:
            account = await resolve_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
    except AccountFoundationResolutionError as exc:
        raise _resolution_error(exc) from exc

    safe_account_ref = _optional_text(account_ref)
    if safe_account_ref not in {account.account_id, account.account_code}:
        raise _membership_invitation_error(
            MembershipInvitationUnsafeScope(
                "Path account reference does not match resolved account context."
            )
        )

    command_payload = {
        "accountScope": {
            "accountRef": safe_account_ref,
            "refType": ref_type,
            "externalRef": external_ref,
            "context": context,
        },
        "membershipRef": _optional_text(membership_ref),
        "delivery": {
            "providerRef": provider_ref,
            "channel": channel,
            "templateRef": template_ref,
            "recipientHashPresent": bool(recipient_hash),
        },
        "reasonCode": reason_code,
    }

    try:
        result = await request_referral_saas_membership_invitation_delivery(
            account_id=account.account_id,
            tenant_code=account.tenant_code,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            membership_id=membership_ref,
            provider_ref=provider_ref,
            channel=channel,
            template_ref=template_ref,
            recipient_hash=recipient_hash,
            reason_code=reason_code,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_MEMBERSHIP_INVITATION_DELIVERY_REQUEST",
                    "account_ref": safe_account_ref,
                    "membership_ref": _optional_text(membership_ref),
                    "idempotency_key": idempotency_key,
                }
            ),
            command_payload_hash=hash_payload(command_payload),
            command_payload=payload,
            command_actor_ref=_actor_ref(admin_identity),
            command_actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except MembershipInvitationCommandError as exc:
        raise _membership_invitation_error(exc) from exc

    return {
        "status": "blocked",
        "context": context,
        "account": account.to_safe_dict(),
        "deliveryRequest": result.to_safe_dict(),
        "guardrails": _membership_invitation_guardrails()
        + ["NO_PROVIDER_SECRET_EXPOSURE"],
        "redactions": _membership_invitation_redactions()
        + ["recipient_hash", "provider_secret"],
        "no_invite_delivery_confirmed": True,
        "no_membership_activation_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_seat_assignment_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.post("/accounts/{account_ref}/memberships/{membership_ref}/activation")
async def request_referral_saas_membership_activation_route(
    account_ref: str,
    membership_ref: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)

    account_scope = payload.get("accountScope") or {}
    activation = payload.get("activation") or {}
    idempotency_key = _optional_text(payload.get("idempotencyKey"))
    correlation_id = _optional_text(payload.get("correlationId"))
    reason_code = (
        _optional_text(payload.get("reasonCode"))
        or "CUSTOMER_PROFILE_MEMBERSHIP_ACTIVATION_REQUEST"
    )

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = (_optional_text(account_scope.get("context")) or "setup").lower()
    accepted_subject = _optional_text(activation.get("acceptedSubject"))
    acceptance_evidence_ref = _optional_text(activation.get("acceptanceEvidenceRef"))

    if not ref_type or not external_ref or not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": _membership_activation_guardrails(),
                "redactions": _membership_activation_redactions(),
                "no_invite_delivery_confirmed": True,
                "no_auth_claim_change_confirmed": True,
                "no_seat_assignment_confirmed": True,
                "no_money_movement_confirmed": True,
            },
        )
    if context not in REFERRAL_SAAS_ACCOUNT_CONTEXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "accountScope.context must be runtime or setup.",
            },
        )

    try:
        if context == "setup":
            account = await resolve_setup_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
        else:
            account = await resolve_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
    except AccountFoundationResolutionError as exc:
        raise _resolution_error(exc) from exc

    safe_account_ref = _optional_text(account_ref)
    if safe_account_ref not in {account.account_id, account.account_code}:
        raise _membership_activation_error(
            MembershipInvitationUnsafeScope(
                "Path account reference does not match resolved account context."
            )
        )

    command_payload = {
        "accountScope": {
            "accountRef": safe_account_ref,
            "refType": ref_type,
            "externalRef": external_ref,
            "context": context,
        },
        "membershipRef": _optional_text(membership_ref),
        "activation": {
            "acceptedSubjectPresent": bool(accepted_subject),
            "acceptanceEvidenceRefPresent": bool(acceptance_evidence_ref),
        },
        "reasonCode": reason_code,
    }

    try:
        result = await request_referral_saas_membership_activation(
            account_id=account.account_id,
            tenant_code=account.tenant_code,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            account_status=account.account_status,
            tenant_link_status=account.tenant_link_status,
            external_reference_status=account.reference_status,
            membership_id=membership_ref,
            accepted_subject=accepted_subject or None,
            acceptance_evidence_ref=acceptance_evidence_ref or None,
            reason_code=reason_code,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_MEMBERSHIP_ACTIVATION_REQUEST",
                    "account_ref": safe_account_ref,
                    "membership_ref": _optional_text(membership_ref),
                    "idempotency_key": idempotency_key,
                }
            ),
            command_payload_hash=hash_payload(command_payload),
            command_payload=payload,
            command_actor_ref=_actor_ref(admin_identity),
            command_actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except MembershipInvitationCommandError as exc:
        raise _membership_activation_error(exc) from exc

    response_status = (
        "ok" if result.command_status == "MEMBERSHIP_ACTIVATED" else "blocked"
    )
    return {
        "status": response_status,
        "context": context,
        "account": account.to_safe_dict(),
        "activationRequest": result.to_safe_dict(),
        "guardrails": _membership_activation_guardrails(),
        "redactions": _membership_activation_redactions(),
        "no_invite_delivery_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_seat_assignment_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.post("/accounts/{account_ref}/memberships/{membership_ref}/access-provisioning")
async def request_referral_saas_access_provisioning_route(
    account_ref: str,
    membership_ref: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)

    account_scope = payload.get("accountScope") or {}
    provisioning = payload.get("provisioning") or {}
    idempotency_key = _optional_text(payload.get("idempotencyKey"))
    correlation_id = _optional_text(payload.get("correlationId"))
    reason_code = (
        _optional_text(payload.get("reasonCode"))
        or "CUSTOMER_PROFILE_ACCESS_PROVISIONING_REQUEST"
    )

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = (_optional_text(account_scope.get("context")) or "runtime").lower()
    seat_type = _optional_text(provisioning.get("seatType"))
    seat_assignment_evidence_ref = _optional_text(
        provisioning.get("seatAssignmentEvidenceRef")
    )
    auth_provider_ref = _optional_text(provisioning.get("authProviderRef"))
    auth_claim_evidence_ref = _optional_text(
        provisioning.get("authClaimEvidenceRef")
    )
    operator_notes = _optional_text(provisioning.get("operatorNotes"))

    if (
        not ref_type
        or not external_ref
        or not idempotency_key
        or not correlation_id
        or not seat_type
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "provisioning.seatType, idempotencyKey, and correlationId "
                    "are required."
                ),
                "guardrails": _access_provisioning_guardrails(),
                "redactions": _access_provisioning_redactions(),
                "no_invite_delivery_confirmed": True,
                "no_auth_claim_change_confirmed": True,
                "no_credential_creation_confirmed": True,
                "no_campaign_activation_confirmed": True,
                "no_go_live_change_confirmed": True,
                "no_money_movement_confirmed": True,
            },
        )
    if context not in REFERRAL_SAAS_ACCOUNT_CONTEXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "accountScope.context must be runtime or setup.",
            },
        )

    try:
        if context == "setup":
            account = await resolve_setup_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
        else:
            account = await resolve_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
    except AccountFoundationResolutionError as exc:
        raise _resolution_error(exc) from exc

    safe_account_ref = _optional_text(account_ref)
    if safe_account_ref not in {account.account_id, account.account_code}:
        raise _access_provisioning_error(
            MembershipInvitationUnsafeScope(
                "Path account reference does not match resolved account context."
            )
        )

    command_payload = {
        "accountScope": {
            "accountRef": safe_account_ref,
            "refType": ref_type,
            "externalRef": external_ref,
            "context": context,
        },
        "membershipRef": _optional_text(membership_ref),
        "provisioning": {
            "seatType": seat_type,
            "seatAssignmentEvidenceRefPresent": bool(seat_assignment_evidence_ref),
            "authProviderRefPresent": bool(auth_provider_ref),
            "authClaimEvidenceRefPresent": bool(auth_claim_evidence_ref),
            "operatorNotesPresent": bool(operator_notes),
        },
        "reasonCode": reason_code,
    }

    try:
        result = await request_referral_saas_access_provisioning(
            account_id=account.account_id,
            tenant_code=account.tenant_code,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            account_status=account.account_status,
            tenant_link_status=account.tenant_link_status,
            external_reference_status=account.reference_status,
            membership_id=membership_ref,
            seat_type=seat_type,
            seat_assignment_evidence_ref=seat_assignment_evidence_ref or None,
            auth_provider_ref=auth_provider_ref or None,
            auth_claim_evidence_ref=auth_claim_evidence_ref or None,
            operator_notes=operator_notes or None,
            reason_code=reason_code,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_ACCESS_PROVISIONING_REQUEST",
                    "account_ref": safe_account_ref,
                    "membership_ref": _optional_text(membership_ref),
                    "idempotency_key": idempotency_key,
                }
            ),
            command_payload_hash=hash_payload(command_payload),
            command_payload=payload,
            command_actor_ref=_actor_ref(admin_identity),
            command_actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except MembershipInvitationCommandError as exc:
        raise _access_provisioning_error(exc) from exc

    response_status = (
        "ok"
        if result.command_status
        in {"PROVISIONING_REQUEST_RECORDED", "PROVISIONING_REPLAYED"}
        else "blocked"
    )
    return {
        "status": response_status,
        "context": context,
        "account": account.to_safe_dict(),
        "accessProvisioning": result.to_safe_dict(),
        "guardrails": _access_provisioning_guardrails(),
        "redactions": _access_provisioning_redactions(),
        "no_invite_delivery_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_credential_creation_confirmed": True,
        "no_campaign_activation_confirmed": True,
        "no_go_live_change_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.patch("/accounts/{account_ref}/profile")
async def update_referral_saas_account_profile_route(
    account_ref: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    _reject_unsafe_profile_payload(payload)

    profile = payload.get("profile") or {}
    idempotency_key = _optional_text(payload.get("idempotencyKey"))
    correlation_id = _optional_text(payload.get("correlationId"))
    if not isinstance(profile, dict):
        raise _profile_maintenance_error(
            AccountProfileValidationError("profile must be an object.")
        )
    if not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "idempotencyKey and correlationId are required.",
                "guardrails": _profile_maintenance_guardrails(),
                "redactions": _profile_maintenance_redactions(),
                "no_external_reference_rotation_confirmed": True,
                "no_account_activation_confirmed": True,
                "no_membership_write_confirmed": True,
                "no_money_movement_confirmed": True,
            },
        )

    command_payload = {
        "accountRef": _optional_text(account_ref),
        "profile": profile,
        "correlationId": correlation_id,
    }

    try:
        result = await update_referral_saas_account_profile(
            account_ref=account_ref,
            account_name=_optional_text(profile.get("accountName")),
            account_type=_optional_text(profile.get("accountType")) or "ORGANISATION",
            operating_jurisdiction_code=(
                _optional_text(profile.get("operatingJurisdictionCode")) or "ZA"
            ),
            customer_type=_optional_text(profile.get("customerType")) or None,
            industry=_optional_text(profile.get("industry")) or None,
            actor_ref=_actor_ref(admin_identity),
            actor_role=str(admin_identity.get("role") or "").upper(),
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_ACCOUNT_PROFILE_UPDATE",
                    "account_ref": _optional_text(account_ref),
                    "idempotency_key": idempotency_key,
                }
            ),
            command_payload_hash=hash_payload(command_payload),
        )
    except AccountProfileMaintenanceError as exc:
        raise _profile_maintenance_error(exc) from exc

    return {
        "status": "ok",
        "profile": result.to_safe_dict(),
        "guardrails": _profile_maintenance_guardrails(),
        "redactions": _profile_maintenance_redactions(),
        "no_external_reference_rotation_confirmed": True,
        "no_account_activation_confirmed": True,
        "no_membership_write_confirmed": True,
        "no_invite_delivery_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.get("/accounts/resolve")
async def resolve_referral_saas_account(
    ref_type: Annotated[
        str,
        Query(
            min_length=1,
            description=(
                "External reference type, for example external_tenant_ref or "
                "organisation_ref."
            ),
        ),
    ],
    external_ref: Annotated[
        str,
        Query(
            min_length=1,
            description="External account/tenant reference value.",
        ),
    ],
    context: Annotated[
        str,
        Query(
            description=(
                "runtime requires active account/reference/tenant-link state; "
                "setup allows pending/suspended setup evidence for account setup "
                "and maintenance review."
            ),
        ),
    ] = "runtime",
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)

    normalised_context = str(context or "").strip().lower()
    if normalised_context not in REFERRAL_SAAS_ACCOUNT_CONTEXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "context must be runtime or setup.",
            },
        )

    try:
        if normalised_context == "setup":
            account = await resolve_setup_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
        else:
            account = await resolve_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
    except AccountFoundationResolutionError as exc:
        raise _resolution_error(exc) from exc

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "guardrail": (
            "Read-only Referral SaaS account resolver. This endpoint does not "
            "create accounts, create tenants, convert onboarding drafts, invite "
            "users, write memberships, rotate references, activate campaigns, "
            "trigger go-live, write audit events, repair, replay, retry, or "
            "mutate funding, fulfilment, settlement, reward, commission, wallet, "
            "invoice, billing, or DLaaS marketplace records."
        ),
    }


@router.get("/accounts/membership-posture")
async def read_referral_saas_account_membership_posture(
    ref_type: Annotated[
        str,
        Query(
            min_length=1,
            description="External reference type used to resolve the account.",
        ),
    ],
    external_ref: Annotated[
        str,
        Query(
            min_length=1,
            description="External account/tenant reference value.",
        ),
    ],
    context: Annotated[
        str,
        Query(
            description=(
                "runtime requires active account/reference/tenant-link state; "
                "setup allows pending/suspended setup evidence."
            ),
        ),
    ] = "setup",
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    reader_identity = _require_referral_saas_account_reader(identity)

    normalised_context = str(context or "").strip().lower()
    if normalised_context not in REFERRAL_SAAS_ACCOUNT_CONTEXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "context must be runtime or setup.",
            },
        )

    try:
        if normalised_context == "setup":
            account = await resolve_setup_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
        else:
            account = await resolve_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
    except AccountFoundationResolutionError as exc:
        raise _resolution_error(exc) from exc

    posture = await get_referral_saas_account_membership_posture(
        account_id=account.account_id,
        tenant_code=account.tenant_code,
        actor_ref=_optional_text(reader_identity.get("subject")) or None,
        actor_client_id=_optional_text(reader_identity.get("client_id")) or None,
    )

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "membershipPosture": posture.to_safe_dict(),
        "guardrail": (
            "Read-only Referral SaaS account membership posture. This endpoint "
            "does not invite users, create users, assign seats, write "
            "memberships, modify auth claims, expose internal tenant codes, "
            "activate accounts, trigger go-live, or mutate adjacent DLaaS money "
            "or marketplace records."
        ),
        "no_membership_write_confirmed": True,
        "no_invite_delivery_confirmed": True,
    }


@router.get("/accounts/{account_ref}/membership-activation-readiness")
async def read_referral_saas_membership_activation_readiness(
    account_ref: str,
    ref_type: Annotated[
        str,
        Query(
            min_length=1,
            description="External reference type used to resolve the account.",
        ),
    ],
    external_ref: Annotated[
        str,
        Query(
            min_length=1,
            description="External account/customer reference value.",
        ),
    ],
    context: Annotated[
        str,
        Query(
            description=(
                "setup allows pending setup evidence; runtime requires active "
                "account/reference/tenant-link state."
            ),
        ),
    ] = "setup",
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)

    normalised_context = str(context or "").strip().lower()
    if normalised_context not in REFERRAL_SAAS_ACCOUNT_CONTEXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "context must be runtime or setup.",
            },
        )

    try:
        if normalised_context == "setup":
            account = await resolve_setup_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
        else:
            account = await resolve_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
    except AccountFoundationResolutionError as exc:
        raise _resolution_error(exc) from exc

    safe_account_ref = _optional_text(account_ref)
    if safe_account_ref not in {account.account_id, account.account_code}:
        raise _membership_invitation_error(
            MembershipInvitationUnsafeScope(
                "Path account reference does not match resolved account context."
            )
        )

    readiness = await get_referral_saas_membership_activation_readiness(
        account_id=account.account_id,
        tenant_code=account.tenant_code,
        account_status=account.account_status,
        tenant_link_status=account.tenant_link_status,
        external_reference_status=account.reference_status,
    )

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "activationReadiness": readiness.to_safe_dict(),
        "guardrail": (
            "Read-only Referral SaaS membership activation readiness. This "
            "endpoint does not send invitations, activate memberships, create "
            "users, assign seats, modify auth claims, expose internal tenant "
            "codes, activate accounts, trigger go-live, or mutate adjacent "
            "DLaaS money or marketplace records."
        ),
        "no_invite_delivery_confirmed": True,
        "no_membership_activation_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_seat_assignment_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.get("/accounts/{account_ref}/technical-setup-readiness")
async def read_referral_saas_technical_setup_readiness(
    account_ref: str,
    ref_type: Annotated[
        str,
        Query(
            min_length=1,
            description="External reference type used to resolve the account.",
        ),
    ],
    external_ref: Annotated[
        str,
        Query(
            min_length=1,
            description="External account/customer reference value.",
        ),
    ],
    context: Annotated[
        str,
        Query(
            description=(
                "setup allows pending setup evidence; runtime requires active "
                "account/reference/tenant-link state."
            ),
        ),
    ] = "setup",
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)

    normalised_context = str(context or "").strip().lower()
    if normalised_context not in REFERRAL_SAAS_ACCOUNT_CONTEXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "context must be runtime or setup.",
            },
        )

    try:
        if normalised_context == "setup":
            account = await resolve_setup_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
        else:
            account = await resolve_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
    except AccountFoundationResolutionError as exc:
        raise _resolution_error(exc) from exc

    safe_account_ref = _optional_text(account_ref)
    if safe_account_ref not in {account.account_id, account.account_code}:
        raise _membership_invitation_error(
            MembershipInvitationUnsafeScope(
                "Path account reference does not match resolved account context."
            )
        )

    readiness = build_referral_saas_technical_setup_readiness(
        account_id=account.account_id,
        account_status=account.account_status,
        tenant_link_status=account.tenant_link_status,
        external_reference_status=account.reference_status,
    )

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "technicalSetupReadiness": readiness.to_safe_dict(),
        "guardrail": (
            "Read-only Referral SaaS technical setup readiness. This endpoint "
            "does not create credentials, expose provider secrets, dispatch "
            "webhooks, send invitations, activate memberships, assign seats, "
            "modify auth claims, activate campaigns, trigger go-live, expose "
            "internal tenant codes, or mutate adjacent DLaaS money or "
            "marketplace records."
        ),
        "no_credential_creation_confirmed": True,
        "no_webhook_dispatch_confirmed": True,
        "no_invite_delivery_confirmed": True,
        "no_membership_activation_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_seat_assignment_confirmed": True,
        "no_campaign_activation_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.get("/accounts/{account_ref}/integrations/configuration")
async def read_referral_saas_integration_configuration(
    account_ref: str,
    ref_type: Annotated[
        str,
        Query(
            min_length=1,
            description="External reference type used to resolve the account.",
        ),
    ],
    external_ref: Annotated[
        str,
        Query(
            min_length=1,
            description="External account/customer reference value.",
        ),
    ],
    context: Annotated[
        str,
        Query(
            description=(
                "setup allows pending setup evidence; runtime requires active "
                "account/reference/tenant-link state."
            ),
        ),
    ] = "setup",
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)
    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)

    readiness = build_referral_saas_technical_setup_readiness(
        account_id=account.account_id,
        account_status=account.account_status,
        tenant_link_status=account.tenant_link_status,
        external_reference_status=account.reference_status,
    )
    try:
        configuration = await get_referral_saas_integration_configuration(
            account_id=account.account_id,
        )
    except ReferralSaasIntegrationConfigurationCommandError as exc:
        raise _integration_configuration_error(exc) from exc

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "integrationConfiguration": (
            configuration.to_safe_dict() if configuration else None
        ),
        "technicalSetupReadiness": readiness.to_safe_dict(),
        "guardrail": (
            "Read-only selected-customer Integrations configuration view. "
            "It returns saved setup evidence and readiness only; it does not "
            "store secrets, create credentials, dispatch webhooks, send "
            "invites, activate memberships, assign seats, change auth claims, "
            "activate campaigns, trigger go-live, bill, or move money."
        ),
        "guardrails": sorted(INTEGRATION_CONFIGURATION_ROUTE_GUARDRAILS),
        "redactions": sorted(INTEGRATION_CONFIGURATION_ROUTE_REDACTIONS),
        "no_secret_or_credential_storage_confirmed": True,
        "no_credential_creation_confirmed": True,
        "no_webhook_dispatch_confirmed": True,
        "no_invite_delivery_confirmed": True,
        "no_membership_activation_confirmed": True,
        "no_seat_assignment_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_campaign_activation_confirmed": True,
        "no_go_live_action_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }


@router.get("/accounts/{account_ref}/integrations/execution-readiness")
async def read_referral_saas_integration_execution_readiness(
    account_ref: str,
    ref_type: Annotated[
        str,
        Query(
            min_length=1,
            description="External reference type used to resolve the account.",
        ),
    ],
    external_ref: Annotated[
        str,
        Query(
            min_length=1,
            description="External account/customer reference value.",
        ),
    ],
    context: Annotated[
        str,
        Query(
            description=(
                "setup allows pending setup evidence; runtime requires active "
                "account/reference/tenant-link state."
            ),
        ),
    ] = "setup",
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)
    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)

    try:
        configuration = await get_referral_saas_integration_configuration(
            account_id=account.account_id,
        )
    except ReferralSaasIntegrationConfigurationCommandError as exc:
        raise _integration_configuration_error(exc) from exc

    readiness = build_referral_saas_integration_execution_readiness(
        account_status=account.account_status,
        tenant_link_status=account.tenant_link_status,
        external_reference_status=account.reference_status,
        configuration=configuration,
    )

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "integrationExecutionReadiness": readiness.to_safe_dict(),
        "integrationConfiguration": (
            configuration.to_safe_dict() if configuration else None
        ),
        "guardrail": (
            "Read-only selected-customer Integrations execution readiness. "
            "It shows whether saved setup evidence can move into governed API, "
            "webhook, message-provider, or credential-lifecycle checks; it "
            "does not create credentials, dispatch webhooks, send invites or "
            "messages, activate memberships, assign seats, change auth claims, "
            "activate campaigns, trigger go-live, bill, or move money."
        ),
        "guardrails": sorted(INTEGRATION_EXECUTION_ROUTE_GUARDRAILS),
        "redactions": sorted(INTEGRATION_EXECUTION_ROUTE_REDACTIONS),
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


@router.post("/accounts/{account_ref}/integrations/api-access/verification")
async def record_referral_saas_account_api_access_verification(
    account_ref: str,
    request: ReferralSaasApiAccessVerificationRequest,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    request_payload = request.model_dump(exclude_none=True)
    try:
        assert_safe_referral_saas_integration_execution_payload(request_payload)
    except ReferralSaasIntegrationConfigurationCommandError as exc:
        raise _integration_configuration_error(exc) from exc

    account_scope = request.accountScope
    if not isinstance(account_scope, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "accountScope must be an object.",
                "guardrails": sorted(INTEGRATION_EXECUTION_ROUTE_GUARDRAILS),
                "redactions": sorted(INTEGRATION_EXECUTION_ROUTE_REDACTIONS),
                "no_verification_recorded_confirmed": True,
            },
        )
    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = _optional_text(account_scope.get("context")) or "setup"
    idempotency_key = _optional_text(request.idempotencyKey)
    correlation_id = _optional_text(request.correlationId)
    if not ref_type or not external_ref or not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": sorted(INTEGRATION_EXECUTION_ROUTE_GUARDRAILS),
                "redactions": sorted(INTEGRATION_EXECUTION_ROUTE_REDACTIONS),
                "no_verification_recorded_confirmed": True,
            },
        )

    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    safe_account_ref = _assert_account_path_scope(account_ref, account)
    try:
        configuration = await get_referral_saas_integration_configuration(
            account_id=account.account_id,
        )
        command_payload = {
            "accountScope": {
                "accountRef": safe_account_ref,
                "refType": ref_type,
                "externalRef": external_ref,
                "context": normalised_context,
            },
            "verification": request_payload.get("verification") or {},
            "reasonCode": request.reasonCode or "CUSTOMER_API_ACCESS_VERIFICATION",
        }
        result = await record_referral_saas_api_access_verification(
            account_id=account.account_id,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            tenant_code=account.tenant_code,
            account_status=account.account_status,
            tenant_link_status=account.tenant_link_status,
            external_reference_status=account.reference_status,
            configuration=configuration,
            reason_code=request.reasonCode,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_API_ACCESS_VERIFICATION",
                    "account_ref": safe_account_ref,
                    "idempotency_key": idempotency_key,
                }
            ),
            request_payload_hash=hash_payload(command_payload),
            actor_ref=_actor_ref(admin_identity),
            actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except ReferralSaasIntegrationConfigurationCommandError as exc:
        raise _integration_configuration_error(exc) from exc

    return {
        "status": "accepted",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "integrationApiAccessVerification": result.to_safe_dict(),
        "account_scope": _customer_report_account_scope(account),
        "guardrail": (
            "API-access verification evidence recorded for the selected "
            "customer only. This command does not create, reveal, rotate, or "
            "accept credentials; it does not call a provider, dispatch a "
            "webhook, send invites or messages, activate memberships, assign "
            "seats, change auth claims, activate campaigns, trigger go-live, "
            "bill, or move money."
        ),
        "guardrails": sorted(INTEGRATION_EXECUTION_ROUTE_GUARDRAILS),
        "redactions": sorted(INTEGRATION_EXECUTION_ROUTE_REDACTIONS),
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


@router.post("/accounts/{account_ref}/integrations/webhooks/test-dispatch")
async def record_referral_saas_account_webhook_test_dispatch(
    account_ref: str,
    request: ReferralSaasWebhookTestDispatchRequest,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    request_payload = request.model_dump(exclude_none=True)
    try:
        assert_safe_referral_saas_integration_execution_payload(request_payload)
    except ReferralSaasIntegrationConfigurationCommandError as exc:
        raise _integration_configuration_error(exc) from exc

    account_scope = request.accountScope
    if not isinstance(account_scope, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "accountScope must be an object.",
                "guardrails": sorted(INTEGRATION_EXECUTION_ROUTE_GUARDRAILS),
                "redactions": sorted(INTEGRATION_EXECUTION_ROUTE_REDACTIONS),
                "no_webhook_test_recorded_confirmed": True,
            },
        )
    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = _optional_text(account_scope.get("context")) or "setup"
    idempotency_key = _optional_text(request.idempotencyKey)
    correlation_id = _optional_text(request.correlationId)
    if not ref_type or not external_ref or not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": sorted(INTEGRATION_EXECUTION_ROUTE_GUARDRAILS),
                "redactions": sorted(INTEGRATION_EXECUTION_ROUTE_REDACTIONS),
                "no_webhook_test_recorded_confirmed": True,
            },
        )

    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    safe_account_ref = _assert_account_path_scope(account_ref, account)
    try:
        configuration = await get_referral_saas_integration_configuration(
            account_id=account.account_id,
        )
        command_payload = {
            "accountScope": {
                "accountRef": safe_account_ref,
                "refType": ref_type,
                "externalRef": external_ref,
                "context": normalised_context,
            },
            "webhookTest": request_payload.get("webhookTest") or {},
            "reasonCode": request.reasonCode or "CUSTOMER_WEBHOOK_TEST_DISPATCH",
        }
        result = await record_referral_saas_webhook_test_dispatch(
            account_id=account.account_id,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            tenant_code=account.tenant_code,
            account_status=account.account_status,
            tenant_link_status=account.tenant_link_status,
            external_reference_status=account.reference_status,
            configuration=configuration,
            reason_code=request.reasonCode,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_WEBHOOK_TEST_DISPATCH",
                    "account_ref": safe_account_ref,
                    "idempotency_key": idempotency_key,
                }
            ),
            request_payload_hash=hash_payload(command_payload),
            actor_ref=_actor_ref(admin_identity),
            actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except ReferralSaasIntegrationConfigurationCommandError as exc:
        raise _integration_configuration_error(exc) from exc

    return {
        "status": "accepted",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "integrationWebhookTestDispatch": result.to_safe_dict(),
        "account_scope": _customer_report_account_scope(account),
        "guardrail": (
            "Webhook test-dispatch evidence recorded for the selected customer "
            "only. This command does not dispatch a webhook, register a "
            "subscription, create or reveal signing material, send invites or "
            "messages, activate memberships, assign seats, change auth claims, "
            "activate campaigns, trigger go-live, bill, or move money."
        ),
        "guardrails": sorted(INTEGRATION_EXECUTION_ROUTE_GUARDRAILS),
        "redactions": sorted(INTEGRATION_EXECUTION_ROUTE_REDACTIONS),
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


@router.post("/accounts/{account_ref}/integrations/message-providers/test-check")
async def record_referral_saas_account_message_provider_test(
    account_ref: str,
    request: ReferralSaasMessageProviderTestRequest,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    request_payload = request.model_dump(exclude_none=True)
    try:
        assert_safe_referral_saas_integration_execution_payload(request_payload)
    except ReferralSaasIntegrationConfigurationCommandError as exc:
        raise _integration_configuration_error(exc) from exc

    account_scope = request.accountScope
    if not isinstance(account_scope, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "accountScope must be an object.",
                "guardrails": sorted(INTEGRATION_EXECUTION_ROUTE_GUARDRAILS),
                "redactions": sorted(INTEGRATION_EXECUTION_ROUTE_REDACTIONS),
                "no_message_provider_test_recorded_confirmed": True,
            },
        )
    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = _optional_text(account_scope.get("context")) or "setup"
    idempotency_key = _optional_text(request.idempotencyKey)
    correlation_id = _optional_text(request.correlationId)
    if not ref_type or not external_ref or not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": sorted(INTEGRATION_EXECUTION_ROUTE_GUARDRAILS),
                "redactions": sorted(INTEGRATION_EXECUTION_ROUTE_REDACTIONS),
                "no_message_provider_test_recorded_confirmed": True,
            },
        )

    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    safe_account_ref = _assert_account_path_scope(account_ref, account)
    try:
        configuration = await get_referral_saas_integration_configuration(
            account_id=account.account_id,
        )
        command_payload = {
            "accountScope": {
                "accountRef": safe_account_ref,
                "refType": ref_type,
                "externalRef": external_ref,
                "context": normalised_context,
            },
            "messageProviderTest": request_payload.get("messageProviderTest") or {},
            "reasonCode": request.reasonCode or "CUSTOMER_MESSAGE_PROVIDER_TEST",
        }
        result = await record_referral_saas_message_provider_test(
            account_id=account.account_id,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            tenant_code=account.tenant_code,
            account_status=account.account_status,
            tenant_link_status=account.tenant_link_status,
            external_reference_status=account.reference_status,
            configuration=configuration,
            reason_code=request.reasonCode,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_MESSAGE_PROVIDER_TEST",
                    "account_ref": safe_account_ref,
                    "idempotency_key": idempotency_key,
                }
            ),
            request_payload_hash=hash_payload(command_payload),
            actor_ref=_actor_ref(admin_identity),
            actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except ReferralSaasIntegrationConfigurationCommandError as exc:
        raise _integration_configuration_error(exc) from exc

    return {
        "status": "accepted",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "integrationMessageProviderTest": result.to_safe_dict(),
        "account_scope": _customer_report_account_scope(account),
        "guardrail": (
            "Message-provider test evidence recorded for the selected customer "
            "only. This command does not call a provider, create credentials, "
            "send an invite or referral message, dispatch a webhook, activate "
            "memberships, assign seats, change auth claims, activate campaigns, "
            "trigger go-live, bill, or move money."
        ),
        "guardrails": sorted(INTEGRATION_EXECUTION_ROUTE_GUARDRAILS),
        "redactions": sorted(INTEGRATION_EXECUTION_ROUTE_REDACTIONS),
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


@router.post("/accounts/{account_ref}/integrations/credential-requests")
async def create_referral_saas_account_integration_credential_request(
    account_ref: str,
    request: ReferralSaasCredentialRequestCreateRequest,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    request_payload = request.model_dump(exclude_none=True)
    try:
        assert_safe_referral_saas_integration_execution_payload(request_payload)
    except ReferralSaasIntegrationConfigurationCommandError as exc:
        raise _integration_configuration_error(exc) from exc

    account_scope = request.accountScope
    credential_request = request.credentialRequest or {}
    if not isinstance(account_scope, dict) or not isinstance(credential_request, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "accountScope and credentialRequest must be objects.",
                "guardrails": sorted(CREDENTIAL_REQUEST_GUARDRAILS),
                "redactions": sorted(CREDENTIAL_REQUEST_REDACTIONS),
                "no_credential_request_recorded_confirmed": True,
            },
        )
    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = _optional_text(account_scope.get("context")) or "setup"
    idempotency_key = _optional_text(request.idempotencyKey)
    correlation_id = _optional_text(request.correlationId)
    request_type = _optional_text(credential_request.get("requestType"))
    capability = _optional_text(credential_request.get("capability"))
    if (
        not ref_type
        or not external_ref
        or not idempotency_key
        or not correlation_id
        or not request_type
        or not capability
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "credentialRequest.requestType, credentialRequest.capability, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": sorted(CREDENTIAL_REQUEST_GUARDRAILS),
                "redactions": sorted(CREDENTIAL_REQUEST_REDACTIONS),
                "no_credential_request_recorded_confirmed": True,
            },
        )

    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    safe_account_ref = _assert_account_path_scope(account_ref, account)
    try:
        configuration = await get_referral_saas_integration_configuration(
            account_id=account.account_id,
        )
        command_payload = {
            "accountScope": {
                "accountRef": safe_account_ref,
                "refType": ref_type,
                "externalRef": external_ref,
                "context": normalised_context,
            },
            "credentialRequest": credential_request,
            "reasonCode": request.reasonCode or "CUSTOMER_CREDENTIAL_REQUEST",
        }
        result = await create_referral_saas_integration_credential_request(
            account_id=account.account_id,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            tenant_code=account.tenant_code,
            account_status=account.account_status,
            tenant_link_status=account.tenant_link_status,
            external_reference_status=account.reference_status,
            configuration=configuration,
            request_type=request_type,
            capability=capability,
            environment=_optional_text(credential_request.get("environment")),
            intended_use=credential_request.get("intendedUse"),
            requested_for=credential_request.get("requestedFor"),
            reason_code=request.reasonCode,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_CREDENTIAL_REQUEST",
                    "account_ref": safe_account_ref,
                    "idempotency_key": idempotency_key,
                }
            ),
            request_payload_hash=hash_payload(command_payload),
            actor_ref=_actor_ref(admin_identity),
            actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except ReferralSaasIntegrationConfigurationCommandError as exc:
        raise _integration_configuration_error(exc) from exc

    return {
        "status": "accepted",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "integrationCredentialRequestResult": result.to_safe_dict(),
        "account_scope": _customer_report_account_scope(account),
        "guardrail": (
            "Credential request recorded for the selected customer only. This "
            "does not create, reveal, store, rotate, revoke, download, or send "
            "credentials; it does not write a vault, call a provider, dispatch "
            "webhooks, send invites or messages, activate memberships, assign "
            "seats, change auth claims, activate campaigns, trigger go-live, "
            "bill, or move money."
        ),
        "guardrails": sorted(CREDENTIAL_REQUEST_GUARDRAILS),
        "redactions": sorted(CREDENTIAL_REQUEST_REDACTIONS),
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


@router.get("/accounts/{account_ref}/integrations/credential-requests")
async def list_referral_saas_account_integration_credential_requests(
    account_ref: str,
    ref_type: Annotated[
        str,
        Query(
            min_length=1,
            description="External reference type used to resolve the account.",
        ),
    ],
    external_ref: Annotated[
        str,
        Query(
            min_length=1,
            description="External account/customer reference value.",
        ),
    ],
    context: Annotated[str, Query(description="Selected-customer context.")] = "setup",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)
    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)
    try:
        requests = await list_referral_saas_integration_credential_requests(
            account_id=account.account_id,
            limit=limit,
        )
    except ReferralSaasIntegrationConfigurationCommandError as exc:
        raise _integration_configuration_error(exc) from exc

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "credentialRequests": [item.to_safe_dict() for item in requests],
        "account_scope": _customer_report_account_scope(account),
        "guardrail": (
            "Read-only selected-customer credential request list. It returns "
            "request metadata only; no secrets, vault records, provider calls, "
            "webhooks, invites, messages, auth, campaign, billing, or money "
            "actions are performed."
        ),
        "guardrails": sorted(CREDENTIAL_REQUEST_GUARDRAILS),
        "redactions": sorted(CREDENTIAL_REQUEST_REDACTIONS),
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


@router.get(
    "/accounts/{account_ref}/integrations/credential-requests/{credential_request_ref}"
)
async def read_referral_saas_account_integration_credential_request(
    account_ref: str,
    credential_request_ref: str,
    ref_type: Annotated[
        str,
        Query(
            min_length=1,
            description="External reference type used to resolve the account.",
        ),
    ],
    external_ref: Annotated[
        str,
        Query(
            min_length=1,
            description="External account/customer reference value.",
        ),
    ],
    context: Annotated[str, Query(description="Selected-customer context.")] = "setup",
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)
    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)
    try:
        credential_request = await get_referral_saas_integration_credential_request(
            account_id=account.account_id,
            credential_request_ref=credential_request_ref,
        )
    except ReferralSaasIntegrationConfigurationCommandError as exc:
        raise _integration_configuration_error(exc) from exc

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "credentialRequest": credential_request.to_safe_dict(),
        "account_scope": _customer_report_account_scope(account),
        "guardrail": (
            "Read-only selected-customer credential request detail. It returns "
            "safe request metadata only; no secret material or adjacent live "
            "workflow is exposed or changed."
        ),
        "guardrails": sorted(CREDENTIAL_REQUEST_GUARDRAILS),
        "redactions": sorted(CREDENTIAL_REQUEST_REDACTIONS),
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


@router.post(
    "/accounts/{account_ref}/integrations/credential-requests/{credential_request_ref}/review-decisions"
)
async def review_referral_saas_account_integration_credential_request(
    account_ref: str,
    credential_request_ref: str,
    request: ReferralSaasCredentialRequestReviewDecisionRequest,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    request_payload = request.model_dump(exclude_none=True)
    try:
        assert_safe_referral_saas_integration_execution_payload(request_payload)
    except IntegrationConfigurationUnsafePayload as exc:
        raise _integration_configuration_error(exc) from exc

    account_scope = request.accountScope
    review_decision = request.reviewDecision or {}
    if not isinstance(account_scope, dict) or not isinstance(review_decision, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "accountScope and reviewDecision must be objects.",
                "guardrails": sorted(CREDENTIAL_REQUEST_GUARDRAILS),
                "redactions": sorted(CREDENTIAL_REQUEST_REDACTIONS),
                "no_credential_review_recorded_confirmed": True,
            },
        )

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = _optional_text(account_scope.get("context")) or "setup"
    decision_value = _optional_text(
        review_decision.get("reviewStatus") or review_decision.get("decision")
    )
    review_reason = _optional_text(review_decision.get("reason"))
    idempotency_key = _optional_text(request.idempotencyKey)
    correlation_id = _optional_text(request.correlationId)
    if (
        not ref_type
        or not external_ref
        or not decision_value
        or not review_reason
        or not idempotency_key
        or not correlation_id
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "reviewDecision.decision/reviewStatus, reviewDecision.reason, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": sorted(CREDENTIAL_REQUEST_GUARDRAILS),
                "redactions": sorted(CREDENTIAL_REQUEST_REDACTIONS),
                "no_credential_review_recorded_confirmed": True,
            },
        )

    review_status = {
        "APPROVE": "REVIEW_APPROVED",
        "APPROVED": "REVIEW_APPROVED",
        "REVIEW_APPROVED": "REVIEW_APPROVED",
        "BLOCK": "REVIEW_REJECTED",
        "BLOCKED": "REVIEW_REJECTED",
        "REJECT": "REVIEW_REJECTED",
        "REJECTED": "REVIEW_REJECTED",
        "REVIEW_REJECTED": "REVIEW_REJECTED",
    }.get(decision_value.upper(), decision_value.upper())

    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    safe_account_ref = _assert_account_path_scope(account_ref, account)
    command_payload = {
        "accountScope": {
            "accountRef": safe_account_ref,
            "refType": ref_type,
            "externalRef": external_ref,
            "context": normalised_context,
        },
        "credentialRequestRef": credential_request_ref,
        "reviewDecision": {
            "reviewStatus": review_status,
            "reasonCode": request.reasonCode
            or review_decision.get("reasonCode")
            or "CREDENTIAL_REQUEST_REVIEW",
        },
    }
    try:
        result = await record_referral_saas_integration_credential_review_decision(
            account_id=account.account_id,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            tenant_code=account.tenant_code,
            credential_request_ref=credential_request_ref,
            review_status=review_status,
            review_reason=review_reason,
            reason_code=request.reasonCode or review_decision.get("reasonCode"),
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_CREDENTIAL_REQUEST_REVIEW",
                    "account_ref": safe_account_ref,
                    "credential_request_ref": credential_request_ref,
                    "idempotency_key": idempotency_key,
                }
            ),
            command_payload_hash=hash_payload(command_payload),
            actor_ref=_actor_ref(admin_identity),
            actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except ReferralSaasIntegrationConfigurationCommandError as exc:
        raise _integration_configuration_error(exc) from exc

    return {
        "status": "accepted",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "integrationCredentialReviewDecisionResult": result.to_safe_dict(),
        "account_scope": _customer_report_account_scope(account),
        "guardrail": (
            "Credential request review decision recorded for the selected "
            "customer. This approves or blocks later governed execution only; "
            "it does not create, store, reveal, rotate, revoke, download, or "
            "send credentials."
        ),
        "guardrails": sorted(CREDENTIAL_REQUEST_GUARDRAILS),
        "redactions": sorted(CREDENTIAL_REQUEST_REDACTIONS),
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


@router.post(
    "/accounts/{account_ref}/integrations/credential-requests/{credential_request_ref}/execution-checks"
)
async def check_referral_saas_account_integration_credential_execution(
    account_ref: str,
    credential_request_ref: str,
    request: ReferralSaasCredentialExecutionCheckRequest,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    request_payload = request.model_dump(exclude_none=True)
    try:
        assert_safe_referral_saas_integration_execution_payload(request_payload)
    except IntegrationConfigurationUnsafePayload as exc:
        raise _integration_configuration_error(exc) from exc

    account_scope = request.accountScope
    execution_check = request.executionCheck or {}
    if not isinstance(account_scope, dict) or not isinstance(execution_check, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "accountScope and executionCheck must be objects.",
                "guardrails": sorted(CREDENTIAL_REQUEST_GUARDRAILS),
                "redactions": sorted(CREDENTIAL_REQUEST_REDACTIONS),
                "no_credential_execution_check_recorded_confirmed": True,
            },
        )

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = _optional_text(account_scope.get("context")) or "setup"
    check_reason = _optional_text(execution_check.get("reason"))
    idempotency_key = _optional_text(request.idempotencyKey)
    correlation_id = _optional_text(request.correlationId)
    if (
        not ref_type
        or not external_ref
        or not check_reason
        or not idempotency_key
        or not correlation_id
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "executionCheck.reason, idempotencyKey, and correlationId "
                    "are required."
                ),
                "guardrails": sorted(CREDENTIAL_REQUEST_GUARDRAILS),
                "redactions": sorted(CREDENTIAL_REQUEST_REDACTIONS),
                "no_credential_execution_check_recorded_confirmed": True,
            },
        )

    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    safe_account_ref = _assert_account_path_scope(account_ref, account)
    command_payload = {
        "accountScope": {
            "accountRef": safe_account_ref,
            "refType": ref_type,
            "externalRef": external_ref,
            "context": normalised_context,
        },
        "credentialRequestRef": credential_request_ref,
        "executionCheck": {
            "reasonCode": request.reasonCode
            or execution_check.get("reasonCode")
            or "CREDENTIAL_EXECUTION_CHECK",
        },
    }
    try:
        result = await record_referral_saas_integration_credential_execution_check(
            account_id=account.account_id,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            tenant_code=account.tenant_code,
            credential_request_ref=credential_request_ref,
            check_reason=check_reason,
            reason_code=request.reasonCode or execution_check.get("reasonCode"),
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_CREDENTIAL_EXECUTION_CHECK",
                    "account_ref": safe_account_ref,
                    "credential_request_ref": credential_request_ref,
                    "idempotency_key": idempotency_key,
                }
            ),
            command_payload_hash=hash_payload(command_payload),
            actor_ref=_actor_ref(admin_identity),
            actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except ReferralSaasIntegrationConfigurationCommandError as exc:
        raise _integration_configuration_error(exc) from exc

    return {
        "status": "accepted",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "integrationCredentialExecutionCheckResult": result.to_safe_dict(),
        "account_scope": _customer_report_account_scope(account),
        "guardrail": (
            "Credential execution check recorded for the selected customer. "
            "This only verifies that an approved credential request is ready "
            "for a later governed provider/vault workflow; it does not create, "
            "store, reveal, rotate, revoke, download, or send credentials."
        ),
        "guardrails": sorted(CREDENTIAL_REQUEST_GUARDRAILS),
        "redactions": sorted(CREDENTIAL_REQUEST_REDACTIONS),
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


@router.post("/accounts/{account_ref}/integrations/configuration/validate")
async def validate_referral_saas_account_integration_configuration(
    account_ref: str,
    request: ReferralSaasIntegrationConfigurationRequest,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)
    account_scope = request.accountScope
    if not isinstance(account_scope, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "accountScope must be an object.",
                "guardrails": sorted(INTEGRATION_CONFIGURATION_ROUTE_GUARDRAILS),
                "redactions": sorted(INTEGRATION_CONFIGURATION_ROUTE_REDACTIONS),
                "no_configuration_saved_confirmed": True,
            },
        )
    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = _optional_text(account_scope.get("context")) or "setup"
    if not ref_type or not external_ref:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "accountScope.refType and accountScope.externalRef are required.",
                "guardrails": sorted(INTEGRATION_CONFIGURATION_ROUTE_GUARDRAILS),
                "redactions": sorted(INTEGRATION_CONFIGURATION_ROUTE_REDACTIONS),
                "no_configuration_saved_confirmed": True,
            },
        )

    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)
    try:
        validation = validate_referral_saas_integration_configuration(
            account_status=account.account_status,
            tenant_link_status=account.tenant_link_status,
            external_reference_status=account.reference_status,
            api_environment=request.apiEnvironment,
            webhook_intent=request.webhookIntent,
            message_providers=request.messageProviders,
        )
    except ReferralSaasIntegrationConfigurationCommandError as exc:
        raise _integration_configuration_error(exc) from exc

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "validation": validation.to_safe_dict(),
        "guardrails": sorted(INTEGRATION_CONFIGURATION_ROUTE_GUARDRAILS),
        "redactions": sorted(INTEGRATION_CONFIGURATION_ROUTE_REDACTIONS),
        "no_configuration_saved_confirmed": True,
        "no_secret_or_credential_storage_confirmed": True,
        "no_credential_creation_confirmed": True,
        "no_webhook_dispatch_confirmed": True,
        "no_invite_delivery_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }


@router.put("/accounts/{account_ref}/integrations/configuration")
async def upsert_referral_saas_account_integration_configuration(
    account_ref: str,
    request: ReferralSaasIntegrationConfigurationRequest,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    request_payload = request.model_dump(exclude_none=True)
    account_scope = request.accountScope
    if not isinstance(account_scope, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "accountScope must be an object.",
                "guardrails": sorted(INTEGRATION_CONFIGURATION_ROUTE_GUARDRAILS),
                "redactions": sorted(INTEGRATION_CONFIGURATION_ROUTE_REDACTIONS),
                "no_configuration_saved_confirmed": True,
            },
        )
    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = _optional_text(account_scope.get("context")) or "setup"
    idempotency_key = _optional_text(request.idempotencyKey)
    correlation_id = _optional_text(request.correlationId)
    if not ref_type or not external_ref or not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": sorted(INTEGRATION_CONFIGURATION_ROUTE_GUARDRAILS),
                "redactions": sorted(INTEGRATION_CONFIGURATION_ROUTE_REDACTIONS),
                "no_configuration_saved_confirmed": True,
            },
        )

    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    safe_account_ref = _assert_account_path_scope(account_ref, account)
    command_payload = {
        "accountScope": {
            "accountRef": safe_account_ref,
            "refType": ref_type,
            "externalRef": external_ref,
            "context": normalised_context,
        },
        "apiEnvironment": request_payload.get("apiEnvironment") or {},
        "webhookIntent": request_payload.get("webhookIntent") or {},
        "messageProviders": request_payload.get("messageProviders") or {},
        "reasonCode": request.reasonCode or "CUSTOMER_INTEGRATION_CONFIGURATION",
    }
    try:
        result = await upsert_referral_saas_integration_configuration(
            account_id=account.account_id,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            tenant_code=account.tenant_code,
            account_status=account.account_status,
            tenant_link_status=account.tenant_link_status,
            external_reference_status=account.reference_status,
            api_environment=request.apiEnvironment,
            webhook_intent=request.webhookIntent,
            message_providers=request.messageProviders,
            reason_code=request.reasonCode,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_INTEGRATIONS_CONFIGURATION",
                    "account_ref": safe_account_ref,
                    "idempotency_key": idempotency_key,
                }
            ),
            request_payload_hash=hash_payload(command_payload),
            actor_ref=_actor_ref(admin_identity),
            actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except ReferralSaasIntegrationConfigurationCommandError as exc:
        raise _integration_configuration_error(exc) from exc

    return {
        "status": "accepted",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "integrationConfigurationResult": result.to_safe_dict(),
        "account_scope": _customer_report_account_scope(account),
        "guardrail": (
            "Integrations configuration intent saved for the selected "
            "customer. This persists safe setup evidence only; it does not "
            "store secrets, create credentials, dispatch webhooks, send "
            "invites, activate memberships, assign seats, change auth claims, "
            "activate campaigns, trigger go-live, bill, or move money."
        ),
        "guardrails": sorted(INTEGRATION_CONFIGURATION_ROUTE_GUARDRAILS),
        "redactions": sorted(INTEGRATION_CONFIGURATION_ROUTE_REDACTIONS),
        "no_secret_or_credential_storage_confirmed": True,
        "no_credential_creation_confirmed": True,
        "no_webhook_dispatch_confirmed": True,
        "no_invite_delivery_confirmed": True,
        "no_membership_activation_confirmed": True,
        "no_seat_assignment_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_campaign_activation_confirmed": True,
        "no_go_live_action_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }


@router.get("/accounts/{account_ref}/reports/{report_type}")
async def read_referral_saas_account_report(
    account_ref: str,
    report_type: str,
    ref_type: Annotated[
        str,
        Query(
            min_length=1,
            description="External reference type used to resolve the account.",
        ),
    ],
    external_ref: Annotated[
        str,
        Query(
            min_length=1,
            description="External account/customer reference value.",
        ),
    ],
    context: Annotated[
        str,
        Query(
            description=(
                "setup allows pending setup evidence; runtime requires active "
                "account/reference/tenant-link state."
            ),
        ),
    ] = "setup",
    dimensions: Annotated[list[str] | None, Query()] = None,
    beneficiary_type: str | None = None,
    campaign_ref: str | None = None,
    campaign_code: str | None = None,
    link_code_status: str | None = None,
    product: str | None = None,
    reward_source: str | None = None,
    reward_status: str | None = None,
    reward_type: str | None = None,
    sponsor_code: str | None = None,
    source_type: str | None = None,
    sub_product: str | None = None,
    data_window_start: datetime | None = None,
    data_window_end: datetime | None = None,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)
    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)

    try:
        report = await _resolve_maybe_awaitable(
            get_referral_saas_report(
                tenant_code=account.tenant_code,
                report_type=report_type,
                dimensions=dimensions,
                filters=_report_filters(
                    beneficiary_type=beneficiary_type,
                    campaign_ref=campaign_ref,
                    campaign_code=campaign_code,
                    link_code_status=link_code_status,
                    product=product,
                    reward_source=reward_source,
                    reward_status=reward_status,
                    reward_type=reward_type,
                    sponsor_code=sponsor_code,
                    source_type=source_type,
                    sub_product=sub_product,
                ),
                data_window_start=data_window_start,
                data_window_end=data_window_end,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "report": _redact_customer_report_payload(report),
        "account_scope": _customer_report_account_scope(account),
        "guardrail": _customer_report_guardrail(),
        "guardrails": sorted(REPORT_GUARDRAILS),
        "redactions": sorted(REPORT_REDACTIONS),
        "no_report_mutation_confirmed": True,
        "no_export_creation_confirmed": True,
        "no_storage_or_delivery_confirmed": True,
        "no_tenant_code_exposure_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.post("/accounts/{account_ref}/reports/{report_type}/exports/validate")
async def validate_referral_saas_account_report_export(
    account_ref: str,
    report_type: str,
    request: ReferralSaasAccountReportExportRequest,
    ref_type: Annotated[
        str,
        Query(
            min_length=1,
            description="External reference type used to resolve the account.",
        ),
    ],
    external_ref: Annotated[
        str,
        Query(
            min_length=1,
            description="External account/customer reference value.",
        ),
    ],
    context: Annotated[str, Query()] = "setup",
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)
    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)

    try:
        export_request = validate_referral_saas_report_export_request(
            tenant_code=account.tenant_code,
            report_type=report_type,
            export_format=request.format,
            redaction_profile=request.redaction_profile,
            dimensions=request.dimensions,
            filters=request.filters,
            row_limit=request.row_limit,
            data_window_start=request.data_window_start,
            data_window_end=request.data_window_end,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "export_request": _redact_customer_report_payload(export_request),
        "account_scope": _customer_report_account_scope(account),
        "guardrail": _customer_report_guardrail(),
        "guardrails": sorted(REPORT_GUARDRAILS),
        "redactions": sorted(REPORT_REDACTIONS),
        "no_export_creation_confirmed": True,
        "no_storage_or_delivery_confirmed": True,
        "no_tenant_code_exposure_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.post("/accounts/{account_ref}/reports/{report_type}/exports/preview")
async def preview_referral_saas_account_report_export(
    account_ref: str,
    report_type: str,
    request: ReferralSaasAccountReportExportRequest,
    ref_type: Annotated[
        str,
        Query(
            min_length=1,
            description="External reference type used to resolve the account.",
        ),
    ],
    external_ref: Annotated[
        str,
        Query(
            min_length=1,
            description="External account/customer reference value.",
        ),
    ],
    context: Annotated[str, Query()] = "setup",
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)
    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)

    try:
        export_preview = await _resolve_maybe_awaitable(
            build_referral_saas_report_export_preview(
                tenant_code=account.tenant_code,
                report_type=report_type,
                export_format=request.format,
                redaction_profile=request.redaction_profile,
                dimensions=request.dimensions,
                filters=request.filters,
                row_limit=request.row_limit,
                data_window_start=request.data_window_start,
                data_window_end=request.data_window_end,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "export_preview": _redact_customer_report_payload(export_preview),
        "account_scope": _customer_report_account_scope(account),
        "guardrail": _customer_report_guardrail(),
        "guardrails": sorted(REPORT_GUARDRAILS),
        "redactions": sorted(REPORT_REDACTIONS),
        "no_export_creation_confirmed": True,
        "no_storage_or_delivery_confirmed": True,
        "no_tenant_code_exposure_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.post("/accounts/{account_ref}/reports/{report_type}/exports")
async def create_referral_saas_account_report_export_request(
    account_ref: str,
    report_type: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    request_payload = dict(payload or {})
    _reject_unsafe_report_export_request_payload(request_payload)

    account_scope = request_payload.get("accountScope") or {}
    if not isinstance(account_scope, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "accountScope must be an object.",
                "guardrails": sorted(REPORT_EXPORT_REQUEST_GUARDRAILS),
                "redactions": sorted(REPORT_EXPORT_REQUEST_REDACTIONS),
                "no_export_file_created_confirmed": True,
                "no_download_url_created_confirmed": True,
                "no_storage_or_delivery_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            },
        )

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = (_optional_text(account_scope.get("context")) or "setup").lower()
    idempotency_key = _optional_text(request_payload.get("idempotencyKey"))
    correlation_id = _optional_text(request_payload.get("correlationId"))
    reason_code = (
        _optional_text(request_payload.get("reasonCode"))
        or "CUSTOMER_PROFILE_REPORT_EXPORT_REQUEST"
    )
    if not ref_type or not external_ref or not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": sorted(REPORT_EXPORT_REQUEST_GUARDRAILS),
                "redactions": sorted(REPORT_EXPORT_REQUEST_REDACTIONS),
                "no_export_file_created_confirmed": True,
                "no_download_url_created_confirmed": True,
                "no_storage_or_delivery_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            },
        )

    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)
    row_limit = request_payload.get("rowLimit", request_payload.get("row_limit"))
    export_format = _optional_text(request_payload.get("format")) or None
    redaction_profile = (
        _optional_text(
            request_payload.get("redactionProfile")
            or request_payload.get("redaction_profile")
        )
        or None
    )
    dimensions = request_payload.get("dimensions")
    filters = request_payload.get("filters")
    data_window_start = _optional_datetime(
        request_payload.get("dataWindowStart")
        or request_payload.get("data_window_start")
    )
    data_window_end = _optional_datetime(
        request_payload.get("dataWindowEnd")
        or request_payload.get("data_window_end")
    )

    command_payload = {
        "accountScope": {
            "accountRef": _optional_text(account_ref),
            "refType": ref_type,
            "externalRef": external_ref,
            "context": normalised_context,
        },
        "reportType": _optional_text(report_type),
        "export": {
            "format": export_format,
            "redactionProfile": redaction_profile,
            "dimensions": dimensions,
            "filters": filters,
            "rowLimit": row_limit,
            "dataWindowStart": data_window_start.isoformat()
            if data_window_start
            else None,
            "dataWindowEnd": data_window_end.isoformat() if data_window_end else None,
        },
        "reasonCode": reason_code,
    }

    try:
        result = await create_referral_saas_report_export_request(
            account_id=account.account_id,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            tenant_code=account.tenant_code,
            report_type=report_type,
            export_format=export_format,
            redaction_profile=redaction_profile,
            dimensions=dimensions,
            filters=filters,
            row_limit=row_limit,
            data_window_start=data_window_start,
            data_window_end=data_window_end,
            reason_code=reason_code,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_REPORT_EXPORT_REQUEST",
                    "account_ref": _optional_text(account_ref),
                    "report_type": _optional_text(report_type),
                    "idempotency_key": idempotency_key,
                }
            ),
            request_payload_hash=hash_payload(command_payload),
            requested_by_ref=_actor_ref(admin_identity),
            requested_by_role=str(admin_identity.get("role") or "").upper(),
        )
    except ReportExportRequestIdempotencyConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": exc.safe_code,
                "message": str(exc),
                "guardrails": sorted(REPORT_EXPORT_REQUEST_GUARDRAILS),
                "redactions": sorted(REPORT_EXPORT_REQUEST_REDACTIONS),
                "no_export_file_created_confirmed": True,
                "no_download_url_created_confirmed": True,
                "no_storage_or_delivery_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            },
        ) from exc
    except (ReferralSaasReportExportCommandError, ValueError) as exc:
        safe_code = getattr(exc, "safe_code", "validation_error")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": safe_code,
                "message": str(exc),
                "guardrails": sorted(REPORT_EXPORT_REQUEST_GUARDRAILS),
                "redactions": sorted(REPORT_EXPORT_REQUEST_REDACTIONS),
                "no_export_file_created_confirmed": True,
                "no_download_url_created_confirmed": True,
                "no_storage_or_delivery_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            },
        ) from exc

    return {
        "status": "accepted",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "reportExport": _redact_customer_report_payload(result.to_safe_dict()),
        "account_scope": _customer_report_account_scope(account),
        "guardrail": (
            "Report export request recorded for the selected customer. This "
            "creates request and audit evidence only; it does not create an "
            "export file, download URL, scheduled delivery, invoice, billing "
            "event, or money movement."
        ),
        "guardrails": sorted(REPORT_EXPORT_REQUEST_GUARDRAILS),
        "redactions": sorted(REPORT_EXPORT_REQUEST_REDACTIONS),
        "no_export_file_created_confirmed": True,
        "no_download_url_created_confirmed": True,
        "no_storage_or_delivery_confirmed": True,
        "no_tenant_code_exposure_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }


@router.post("/accounts/{account_ref}/support-cases")
async def create_referral_saas_account_support_case(
    account_ref: str,
    request: ReferralSaasSupportCaseCreateRequest,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    request_payload = request.model_dump(exclude_none=True)
    _reject_unsafe_support_case_payload(request_payload)

    account_scope = request.accountScope or {}
    if not isinstance(account_scope, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "accountScope must be an object.",
                "guardrails": sorted(SUPPORT_CASE_ROUTE_GUARDRAILS),
                "redactions": sorted(SUPPORT_CASE_ROUTE_REDACTIONS),
                "no_support_case_created_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            },
        )

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = _support_case_resolution_context(account_scope.get("context"))
    idempotency_key = _optional_text(request.idempotencyKey)
    correlation_id = _optional_text(request.correlationId)
    if not ref_type or not external_ref or not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": sorted(SUPPORT_CASE_ROUTE_GUARDRAILS),
                "redactions": sorted(SUPPORT_CASE_ROUTE_REDACTIONS),
                "no_support_case_created_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            },
        )

    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)
    evidence_links = [
        link.model_dump(exclude_none=True) for link in request.evidenceLinks or []
    ]
    command_payload = {
        "accountScope": {
            "accountRef": _optional_text(account_ref),
            "refType": ref_type,
            "externalRef": external_ref,
            "context": normalised_context,
        },
        "supportCase": {
            "category": request.category,
            "priority": request.priority,
            "title": request.title,
            "summary": request.summary,
            "sourceSurface": request.sourceSurface,
            "evidenceLinks": evidence_links,
        },
        "reasonCode": request.reasonCode or "CUSTOMER_SUPPORT_CASE_CREATED",
    }
    try:
        result = await create_referral_saas_support_case(
            account_id=account.account_id,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            tenant_code=account.tenant_code,
            category=request.category or "",
            priority=request.priority or "",
            title=request.title or "",
            summary=request.summary or "",
            source_surface=request.sourceSurface,
            evidence_links=evidence_links,
            reason_code=request.reasonCode,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_SUPPORT_CASE_CREATE",
                    "account_ref": _optional_text(account_ref),
                    "idempotency_key": idempotency_key,
                }
            ),
            request_payload_hash=hash_payload(command_payload),
            actor_ref=_actor_ref(admin_identity),
            actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except ReferralSaasSupportCaseCommandError as exc:
        raise _support_case_error(exc) from exc

    return {
        "status": "accepted",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "supportCase": _redact_customer_report_payload(result.to_safe_dict()),
        "account_scope": _customer_report_account_scope(account),
        "guardrail": (
            "Support case recorded for the selected customer. This creates "
            "safe case and audit evidence only; it does not repair, replay, "
            "retry, mutate product state, create credentials, change auth "
            "claims, bill, or move money."
        ),
        "guardrails": sorted(SUPPORT_CASE_ROUTE_GUARDRAILS),
        "redactions": sorted(SUPPORT_CASE_ROUTE_REDACTIONS),
        "no_repair_replay_retry_confirmed": True,
        "no_referral_or_campaign_mutation_confirmed": True,
        "no_progress_or_attribution_mutation_confirmed": True,
        "no_report_or_export_mutation_confirmed": True,
        "no_invite_delivery_confirmed": True,
        "no_credential_or_auth_claim_change_confirmed": True,
        "no_tenant_code_exposure_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }


@router.post("/accounts/{account_ref}/support-cases/{case_ref}/notes")
async def add_referral_saas_account_support_case_note(
    account_ref: str,
    case_ref: str,
    request: ReferralSaasSupportCaseNoteRequest,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    request_payload = request.model_dump(exclude_none=True)
    _reject_unsafe_support_case_payload(request_payload)

    account_scope = request.accountScope or {}
    if not isinstance(account_scope, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "accountScope must be an object.",
                "guardrails": sorted(SUPPORT_CASE_ROUTE_GUARDRAILS),
                "redactions": sorted(SUPPORT_CASE_ROUTE_REDACTIONS),
                "no_support_case_note_created_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            },
        )

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = _support_case_resolution_context(account_scope.get("context"))
    idempotency_key = _optional_text(request.idempotencyKey)
    correlation_id = _optional_text(request.correlationId)
    if not ref_type or not external_ref or not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": sorted(SUPPORT_CASE_ROUTE_GUARDRAILS),
                "redactions": sorted(SUPPORT_CASE_ROUTE_REDACTIONS),
                "no_support_case_note_created_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            },
        )

    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)
    command_payload = {
        "accountScope": {
            "accountRef": _optional_text(account_ref),
            "refType": ref_type,
            "externalRef": external_ref,
            "context": normalised_context,
        },
        "supportCaseRef": _optional_text(case_ref),
        "note": {
            "noteType": request.noteType,
            "noteText": request.noteText,
        },
        "reasonCode": request.reasonCode or "CUSTOMER_SUPPORT_CASE_NOTE_ADDED",
    }
    try:
        result = await add_referral_saas_support_case_note(
            account_id=account.account_id,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            tenant_code=account.tenant_code,
            case_ref=case_ref,
            note_type=request.noteType or "",
            note_text=request.noteText or "",
            reason_code=request.reasonCode,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_SUPPORT_CASE_NOTE_ADD",
                    "account_ref": _optional_text(account_ref),
                    "case_ref": _optional_text(case_ref),
                    "idempotency_key": idempotency_key,
                }
            ),
            request_payload_hash=hash_payload(command_payload),
            actor_ref=_actor_ref(admin_identity),
            actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except ReferralSaasSupportCaseCommandError as exc:
        raise _support_case_error(exc) from exc

    return {
        "status": "accepted",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "supportCaseLifecycle": _redact_customer_report_payload(result.to_safe_dict()),
        "account_scope": _customer_report_account_scope(account),
        "guardrail": (
            "Support case note recorded for the selected customer. This "
            "adds operator evidence only; it does not repair, replay, retry, "
            "mutate referrals, campaigns, reports, progress, attribution, "
            "credentials, auth claims, billing, or money."
        ),
        "guardrails": sorted(SUPPORT_CASE_ROUTE_GUARDRAILS),
        "redactions": sorted(SUPPORT_CASE_ROUTE_REDACTIONS),
        "no_repair_replay_retry_confirmed": True,
        "no_referral_or_campaign_mutation_confirmed": True,
        "no_progress_or_attribution_mutation_confirmed": True,
        "no_report_or_export_mutation_confirmed": True,
        "no_invite_delivery_confirmed": True,
        "no_credential_or_auth_claim_change_confirmed": True,
        "no_tenant_code_exposure_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }


@router.post("/accounts/{account_ref}/support-cases/{case_ref}/status")
async def change_referral_saas_account_support_case_status(
    account_ref: str,
    case_ref: str,
    request: ReferralSaasSupportCaseStatusRequest,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    request_payload = request.model_dump(exclude_none=True)
    _reject_unsafe_support_case_payload(request_payload)

    account_scope = request.accountScope or {}
    if not isinstance(account_scope, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "accountScope must be an object.",
                "guardrails": sorted(SUPPORT_CASE_ROUTE_GUARDRAILS),
                "redactions": sorted(SUPPORT_CASE_ROUTE_REDACTIONS),
                "no_support_case_status_changed_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            },
        )

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = _support_case_resolution_context(account_scope.get("context"))
    idempotency_key = _optional_text(request.idempotencyKey)
    correlation_id = _optional_text(request.correlationId)
    if not ref_type or not external_ref or not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": sorted(SUPPORT_CASE_ROUTE_GUARDRAILS),
                "redactions": sorted(SUPPORT_CASE_ROUTE_REDACTIONS),
                "no_support_case_status_changed_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            },
        )

    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)
    command_payload = {
        "accountScope": {
            "accountRef": _optional_text(account_ref),
            "refType": ref_type,
            "externalRef": external_ref,
            "context": normalised_context,
        },
        "supportCaseRef": _optional_text(case_ref),
        "statusChange": {
            "status": request.status,
            "transitionReason": request.transitionReason,
        },
        "reasonCode": request.reasonCode or "CUSTOMER_SUPPORT_CASE_STATUS_CHANGED",
    }
    try:
        result = await change_referral_saas_support_case_status(
            account_id=account.account_id,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            tenant_code=account.tenant_code,
            case_ref=case_ref,
            to_status=request.status or "",
            transition_reason=request.transitionReason or "",
            reason_code=request.reasonCode,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_SUPPORT_CASE_STATUS_CHANGE",
                    "account_ref": _optional_text(account_ref),
                    "case_ref": _optional_text(case_ref),
                    "idempotency_key": idempotency_key,
                }
            ),
            request_payload_hash=hash_payload(command_payload),
            actor_ref=_actor_ref(admin_identity),
            actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except ReferralSaasSupportCaseCommandError as exc:
        raise _support_case_error(exc) from exc

    return {
        "status": "accepted",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "supportCaseLifecycle": _redact_customer_report_payload(result.to_safe_dict()),
        "account_scope": _customer_report_account_scope(account),
        "guardrail": (
            "Support case status recorded for the selected customer. This "
            "moves the case lifecycle only; it does not repair, replay, retry, "
            "mutate referrals, campaigns, reports, progress, attribution, "
            "credentials, auth claims, billing, or money."
        ),
        "guardrails": sorted(SUPPORT_CASE_ROUTE_GUARDRAILS),
        "redactions": sorted(SUPPORT_CASE_ROUTE_REDACTIONS),
        "no_repair_replay_retry_confirmed": True,
        "no_referral_or_campaign_mutation_confirmed": True,
        "no_progress_or_attribution_mutation_confirmed": True,
        "no_report_or_export_mutation_confirmed": True,
        "no_invite_delivery_confirmed": True,
        "no_credential_or_auth_claim_change_confirmed": True,
        "no_tenant_code_exposure_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }


@router.get("/accounts/{account_ref}/support-cases")
async def list_referral_saas_account_support_cases(
    account_ref: str,
    ref_type: Annotated[str, Query(min_length=1)],
    external_ref: Annotated[str, Query(min_length=1)],
    context: Annotated[str, Query()] = "setup",
    case_status: Annotated[str | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)
    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=_support_case_resolution_context(context),
    )
    _assert_account_path_scope(account_ref, account)
    try:
        cases = await list_referral_saas_support_cases(
            account_id=account.account_id,
            status_filter=case_status,
            limit=limit,
        )
    except ReferralSaasSupportCaseCommandError as exc:
        raise _support_case_error(exc) from exc

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "supportCases": [case.to_safe_dict() for case in cases],
        "account_scope": _customer_report_account_scope(account),
        "guardrails": sorted(SUPPORT_CASE_ROUTE_GUARDRAILS),
        "redactions": sorted(SUPPORT_CASE_ROUTE_REDACTIONS),
        "no_tenant_code_exposure_confirmed": True,
        "no_product_state_mutation_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }


@router.get("/operator/support-cases")
async def list_referral_saas_operator_support_cases(
    case_status: Annotated[str | None, Query(alias="status")] = None,
    priority: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    account_ref: Annotated[str | None, Query()] = None,
    source_surface: Annotated[str | None, Query()] = None,
    assignee_ref: Annotated[str | None, Query()] = None,
    created_from: Annotated[str | None, Query()] = None,
    created_to: Annotated[str | None, Query()] = None,
    updated_from: Annotated[str | None, Query()] = None,
    updated_to: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query()] = None,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)
    try:
        queue = await list_referral_saas_operator_support_queue(
            status_filter=case_status,
            priority=priority,
            category=category,
            account_ref=account_ref,
            source_surface=source_surface,
            assignee_ref=assignee_ref,
            created_from=created_from,
            created_to=created_to,
            updated_from=updated_from,
            updated_to=updated_to,
            limit=limit,
            cursor=cursor,
        )
    except ReferralSaasSupportCaseCommandError as exc:
        raise _support_case_error(exc) from exc

    return {
        "status": "ok",
        "operatorScope": {
            "surface": "operator_support_queue",
            "role": str(identity.get("role") or ""),
        },
        "supportQueue": queue.to_safe_dict(),
        "guardrail": (
            "Operator support queue is a read-only aggregate over persisted "
            "customer support cases. Open a queue item inside the selected "
            "customer Support page for case lifecycle work."
        ),
        "guardrails": sorted(SUPPORT_QUEUE_ROUTE_GUARDRAILS),
        "redactions": sorted(SUPPORT_CASE_ROUTE_REDACTIONS),
        "no_assignment_from_queue_confirmed": True,
        "no_case_lifecycle_mutation_confirmed": True,
        "no_repair_replay_retry_confirmed": True,
        "no_referral_or_campaign_mutation_confirmed": True,
        "no_progress_or_attribution_mutation_confirmed": True,
        "no_report_or_export_mutation_confirmed": True,
        "no_invite_delivery_confirmed": True,
        "no_credential_or_auth_claim_change_confirmed": True,
        "no_tenant_code_exposure_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }


@router.get("/accounts/{account_ref}/support-cases/{case_ref}")
async def read_referral_saas_account_support_case(
    account_ref: str,
    case_ref: str,
    ref_type: Annotated[str, Query(min_length=1)],
    external_ref: Annotated[str, Query(min_length=1)],
    context: Annotated[str, Query()] = "setup",
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)
    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=_support_case_resolution_context(context),
    )
    _assert_account_path_scope(account_ref, account)
    try:
        support_case = await get_referral_saas_support_case(
            account_id=account.account_id,
            case_ref=case_ref,
        )
    except ReferralSaasSupportCaseCommandError as exc:
        raise _support_case_error(exc) from exc

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "supportCase": support_case.to_safe_dict(),
        "account_scope": _customer_report_account_scope(account),
        "guardrails": sorted(SUPPORT_CASE_ROUTE_GUARDRAILS),
        "redactions": sorted(SUPPORT_CASE_ROUTE_REDACTIONS),
        "no_tenant_code_exposure_confirmed": True,
        "no_product_state_mutation_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }


@router.get("/accounts/{account_ref}/campaigns")
async def list_referral_saas_account_campaign_registry(
    account_ref: str,
    ref_type: Annotated[
        str,
        Query(
            min_length=1,
            description="External reference type used to resolve the account.",
        ),
    ],
    external_ref: Annotated[
        str,
        Query(
            min_length=1,
            description="External account/customer reference value.",
        ),
    ],
    context: Annotated[
        str,
        Query(
            description=(
                "setup allows pending setup evidence; runtime requires active "
                "account/reference/tenant-link state."
            ),
        ),
    ] = "setup",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)
    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)

    campaigns = await list_referral_saas_account_campaigns(
        tenant_code=account.tenant_code,
        limit=limit,
    )

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "count": len(campaigns),
        "campaigns": [campaign.to_safe_dict() for campaign in campaigns],
        "guardrail": (
            "Read-only Referral SaaS customer-scoped campaign list. This "
            "endpoint resolves the selected account internally and does not "
            "expose tenant_code, create campaigns, update policies, generate "
            "links, activate campaigns, trigger go-live, or move money."
        ),
        "redactions": ["internal_tenant_identifier"],
        "no_campaign_mutation_confirmed": True,
        "no_policy_write_confirmed": True,
        "no_link_generation_confirmed": True,
        "no_campaign_activation_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.post("/accounts/{account_ref}/campaigns/{campaign_code}/referral-codes")
async def issue_referral_saas_account_campaign_code(
    account_ref: str,
    campaign_code: str,
    response: Response,
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)
    _reject_unsafe_link_code_payload(payload)
    normalised_context, account, campaign = await _resolve_active_campaign_link_code_context(
        account_ref=account_ref,
        campaign_code=_optional_text(campaign_code),
        account_scope=payload.get("accountScope") or {},
    )
    issue_request = payload.get("issueRequest") or {}
    if not isinstance(issue_request, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "issueRequest must be an object.",
                "guardrails": sorted(LINK_CODE_GUARDRAILS),
                "redactions": sorted(LINK_CODE_REDACTIONS),
            },
        )

    body, code = await get_or_create_referrer_code(
        referrer_ucn=_optional_text(issue_request.get("referrerUcn")),
        tenant=account.tenant_code,
        sticker=_optional_text(issue_request.get("sticker")),
        segment=_optional_text(issue_request.get("segment")),
        preferred_handle=_optional_text(issue_request.get("preferredHandle")) or None,
        accepted_terms=bool(issue_request.get("acceptedTerms")),
    )

    response.status_code = code
    return {
        "status": "ok" if code < 400 else "rejected",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "campaign": campaign.to_safe_dict(),
        "linkCode": {
            "issueStatus": _link_issue_status(body, code),
            "referralCode": body.get("referral_code"),
            "publicHandle": body.get("gaming_handle"),
            "created": bool(body.get("created")),
            "sourceType": "REFERRAL_CODE",
            "errorCode": body.get("error_code"),
            "message": body.get("message"),
        },
        "guardrails": sorted(LINK_CODE_GUARDRAILS),
        "redactions": sorted(LINK_CODE_REDACTIONS),
        "no_tenant_code_exposure_confirmed": True,
        "no_campaign_activation_confirmed": True,
        "no_webhook_delivery_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }


@router.post("/accounts/{account_ref}/campaigns/{campaign_code}/referrals/validate")
async def validate_referral_saas_account_campaign_code(
    account_ref: str,
    campaign_code: str,
    response: Response,
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)
    _reject_unsafe_link_code_payload(payload)
    normalised_context, account, campaign = await _resolve_active_campaign_link_code_context(
        account_ref=account_ref,
        campaign_code=_optional_text(campaign_code),
        account_scope=payload.get("accountScope") or {},
    )
    validation_request = payload.get("validationRequest") or {}
    if not isinstance(validation_request, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": "validationRequest must be an object.",
                "guardrails": sorted(LINK_CODE_GUARDRAILS),
                "redactions": sorted(LINK_CODE_REDACTIONS),
            },
        )

    body, code = await validate_referral_code(
        referral_code=_optional_text(validation_request.get("referralCode")),
        tenant_code=account.tenant_code,
        accepted_terms=bool(validation_request.get("acceptedTerms")),
        alias=_optional_text(validation_request.get("alias")) or None,
        device_fingerprint=_optional_text(validation_request.get("deviceFingerprint")) or None,
        ip_address=_optional_text(validation_request.get("ipAddress")) or None,
        qr_code=_optional_text(validation_request.get("qrCode")) or None,
    )

    response.status_code = code
    return {
        "status": "ok" if code < 400 else "rejected",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "campaign": campaign.to_safe_dict(),
        "validation": build_referral_saas_validation_result(body, code),
        "guardrails": sorted(LINK_CODE_GUARDRAILS),
        "redactions": sorted(LINK_CODE_REDACTIONS),
        "no_tenant_code_exposure_confirmed": True,
        "no_campaign_activation_confirmed": True,
        "no_webhook_delivery_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }


@router.post("/accounts/{account_ref}/campaigns")
async def create_referral_saas_account_campaign_route(
    account_ref: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    _reject_unsafe_campaign_setup_payload(payload)

    account_scope = payload.get("accountScope") or {}
    campaign = payload.get("campaign") or {}
    setup_intent = payload.get("setupIntent") or {}
    if not isinstance(account_scope, dict) or not isinstance(campaign, dict):
        raise _campaign_setup_error(
            CampaignSetupValidationError(
                "accountScope and campaign must be objects."
            )
        )

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = (_optional_text(account_scope.get("context")) or "setup").lower()
    idempotency_key = _optional_text(payload.get("idempotencyKey"))
    correlation_id = _optional_text(payload.get("correlationId"))
    reason_code = (
        _optional_text(payload.get("reasonCode"))
        or _optional_text(setup_intent.get("reason"))
        or "CUSTOMER_PROFILE_CAMPAIGN_SETUP"
    )

    if not ref_type or not external_ref or not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": list(CAMPAIGN_SETUP_GUARDRAILS),
                "redactions": list(CAMPAIGN_SETUP_REDACTIONS),
                "no_campaign_activation_confirmed": True,
                "no_link_generation_confirmed": True,
                "no_validation_track_created_confirmed": True,
                "no_policy_write_confirmed": True,
                "no_webhook_delivery_confirmed": True,
                "no_money_movement_confirmed": True,
            },
        )

    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)

    max_uses = campaign.get("maxUses")
    if max_uses is not None:
        try:
            max_uses = int(max_uses)
        except (TypeError, ValueError) as exc:
            raise _campaign_setup_error(
                CampaignSetupValidationError("campaign.maxUses must be a number.")
            ) from exc

    command_payload = {
        "accountScope": {
            "accountRef": _optional_text(account_ref),
            "refType": ref_type,
            "externalRef": external_ref,
            "context": normalised_context,
        },
        "campaign": {
            "name": _optional_text(campaign.get("name")),
            "segment": _optional_text(campaign.get("segment")),
            "startsAt": _optional_text(campaign.get("startsAt")) or None,
            "endsAt": _optional_text(campaign.get("endsAt")) or None,
            "maxUses": max_uses,
        },
        "setupIntent": {
            "requestedStatus": "DRAFT",
            "reason": reason_code,
        },
    }

    try:
        result = await create_referral_saas_account_campaign_setup(
            account_id=account.account_id,
            tenant_code=account.tenant_code,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            account_status=account.account_status,
            tenant_link_status=account.tenant_link_status,
            external_reference_status=account.reference_status,
            name=_optional_text(campaign.get("name")),
            segment=_optional_text(campaign.get("segment")),
            starts_at=_optional_datetime(campaign.get("startsAt")),
            ends_at=_optional_datetime(campaign.get("endsAt")),
            max_uses=max_uses,
            reason_code=reason_code,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_CAMPAIGN_SETUP_CREATE",
                    "account_ref": _optional_text(account_ref),
                    "idempotency_key": idempotency_key,
                }
            ),
            command_payload_hash=hash_payload(command_payload),
            command_payload=payload,
            command_actor_ref=_actor_ref(admin_identity),
            command_actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except ReferralSaasCampaignCommandError as exc:
        raise _campaign_setup_error(exc) from exc

    return {
        "status": "created",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "campaignSetup": result.to_safe_dict(),
        "guardrails": list(CAMPAIGN_SETUP_GUARDRAILS),
        "redactions": list(CAMPAIGN_SETUP_REDACTIONS),
        "no_campaign_activation_confirmed": True,
        "no_link_generation_confirmed": True,
        "no_validation_track_created_confirmed": True,
        "no_policy_write_confirmed": True,
        "no_webhook_delivery_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.get("/accounts/{account_ref}/campaigns/{campaign_code}")
async def read_referral_saas_account_campaign(
    account_ref: str,
    campaign_code: str,
    ref_type: Annotated[
        str,
        Query(
            min_length=1,
            description="External reference type used to resolve the account.",
        ),
    ],
    external_ref: Annotated[
        str,
        Query(
            min_length=1,
            description="External account/customer reference value.",
        ),
    ],
    context: Annotated[
        str,
        Query(
            description=(
                "setup allows pending setup evidence; runtime requires active "
                "account/reference/tenant-link state."
            ),
        ),
    ] = "setup",
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)
    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)

    campaign = await get_referral_saas_account_campaign(
        tenant_code=account.tenant_code,
        campaign_code=campaign_code,
    )
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "campaign_not_found",
                "message": "Campaign was not found for the selected customer.",
                "redactions": ["internal_tenant_identifier"],
            },
        )

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "campaign": campaign.to_safe_dict(),
        "guardrail": (
            "Read-only Referral SaaS customer-scoped campaign detail. This "
            "endpoint resolves the selected account internally and does not "
            "expose tenant_code, create campaigns, update policies, generate "
            "links, activate campaigns, trigger go-live, or move money."
        ),
        "redactions": ["internal_tenant_identifier"],
        "no_campaign_mutation_confirmed": True,
        "no_policy_write_confirmed": True,
        "no_link_generation_confirmed": True,
        "no_campaign_activation_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.put("/accounts/{account_ref}/campaigns/{campaign_code}/policy-settings")
async def upsert_referral_saas_account_campaign_policy_settings_route(
    account_ref: str,
    campaign_code: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    _reject_unsafe_campaign_policy_settings_payload(payload)

    account_scope = payload.get("accountScope") or {}
    policy_settings = payload.get("policySettings") or {}
    setup_intent = payload.get("setupIntent") or {}
    if not isinstance(account_scope, dict) or not isinstance(policy_settings, dict):
        raise _campaign_policy_settings_error(
            CampaignPolicySettingsValidationError(
                "accountScope and policySettings must be objects."
            )
        )

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = (_optional_text(account_scope.get("context")) or "setup").lower()
    idempotency_key = _optional_text(payload.get("idempotencyKey"))
    correlation_id = _optional_text(payload.get("correlationId"))
    reason_code = (
        _optional_text(payload.get("reasonCode"))
        or _optional_text(setup_intent.get("reason"))
        or "CUSTOMER_PROFILE_CAMPAIGN_POLICY_SETTINGS"
    )

    if not ref_type or not external_ref or not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": list(CAMPAIGN_POLICY_SETTINGS_GUARDRAILS),
                "redactions": list(CAMPAIGN_POLICY_SETTINGS_REDACTIONS),
                "no_campaign_activation_confirmed": True,
                "no_link_generation_confirmed": True,
                "no_validation_track_created_confirmed": True,
                "no_webhook_delivery_confirmed": True,
                "no_money_movement_confirmed": True,
            },
        )

    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)

    version = policy_settings.get("version") or 1
    attribution_window_days = policy_settings.get("attributionWindowDays")
    command_payload = {
        "accountScope": {
            "accountRef": _optional_text(account_ref),
            "refType": ref_type,
            "externalRef": external_ref,
            "context": normalised_context,
        },
        "campaignRef": _optional_text(campaign_code),
        "policySettings": {
            "version": version,
            "attributionWindowDays": attribution_window_days,
            "eligibilityRules": policy_settings.get("eligibilityRules") or [],
            "productWindows": policy_settings.get("productWindows") or {},
            "productRules": policy_settings.get("productRules") or {},
            "rewardVisibility": policy_settings.get("rewardVisibility") or {},
        },
        "setupIntent": {
            "requestedStatus": (
                _optional_text(setup_intent.get("requestedStatus"))
                or "POLICY_SETTINGS_RECORDED"
            ),
            "reason": reason_code,
        },
    }

    try:
        result = await upsert_referral_saas_account_campaign_policy_settings(
            account_id=account.account_id,
            tenant_code=account.tenant_code,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            account_status=account.account_status,
            tenant_link_status=account.tenant_link_status,
            external_reference_status=account.reference_status,
            campaign_code=campaign_code,
            version=version,
            attribution_window_days=attribution_window_days,
            eligibility_rules=policy_settings.get("eligibilityRules") or [],
            product_windows=policy_settings.get("productWindows") or {},
            product_rules=policy_settings.get("productRules") or {},
            reward_visibility=policy_settings.get("rewardVisibility") or {},
            reason_code=reason_code,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_CAMPAIGN_POLICY_SETTINGS",
                    "account_ref": _optional_text(account_ref),
                    "campaign_ref": _optional_text(campaign_code),
                    "idempotency_key": idempotency_key,
                }
            ),
            command_payload_hash=hash_payload(command_payload),
            command_payload=payload,
            command_actor_ref=_actor_ref(admin_identity),
            command_actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except ReferralSaasCampaignCommandError as exc:
        raise _campaign_policy_settings_error(exc) from exc

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "policySettings": result.to_safe_dict(),
        "guardrails": list(CAMPAIGN_POLICY_SETTINGS_GUARDRAILS),
        "redactions": list(CAMPAIGN_POLICY_SETTINGS_REDACTIONS),
        "no_campaign_activation_confirmed": True,
        "no_link_generation_confirmed": True,
        "no_validation_track_created_confirmed": True,
        "no_webhook_delivery_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.post("/accounts/{account_ref}/campaigns/{campaign_code}/review-submissions")
async def submit_referral_saas_account_campaign_review_route(
    account_ref: str,
    campaign_code: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    _reject_unsafe_campaign_review_payload(payload)

    account_scope = payload.get("accountScope") or {}
    review_submission = payload.get("reviewSubmission") or {}
    if not isinstance(account_scope, dict) or not isinstance(review_submission, dict):
        raise _campaign_review_error(
            CampaignReviewValidationError(
                "accountScope and reviewSubmission must be objects."
            )
        )

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = (_optional_text(account_scope.get("context")) or "setup").lower()
    idempotency_key = _optional_text(payload.get("idempotencyKey"))
    correlation_id = _optional_text(payload.get("correlationId"))
    reason_code = (
        _optional_text(payload.get("reasonCode"))
        or "CUSTOMER_PROFILE_CAMPAIGN_REVIEW_SUBMIT"
    )

    if not ref_type or not external_ref or not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": list(CAMPAIGN_REVIEW_GUARDRAILS),
                "redactions": list(CAMPAIGN_REVIEW_REDACTIONS),
                "no_campaign_activation_confirmed": True,
                "no_link_generation_confirmed": True,
                "no_validation_track_created_confirmed": True,
                "no_webhook_delivery_confirmed": True,
                "no_invite_or_seat_change_confirmed": True,
                "no_money_movement_confirmed": True,
            },
        )

    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)

    command_payload = {
        "accountScope": {
            "accountRef": _optional_text(account_ref),
            "refType": ref_type,
            "externalRef": external_ref,
            "context": normalised_context,
        },
        "campaignRef": _optional_text(campaign_code),
        "reviewSubmission": {
            "setupSummary": _optional_text(review_submission.get("setupSummary")),
            "requestedReviewStatus": (
                _optional_text(review_submission.get("requestedReviewStatus"))
                or "READY_FOR_REVIEW"
            ),
            "operatorNotesPresent": bool(
                _optional_text(review_submission.get("operatorNotes"))
            ),
        },
    }

    try:
        result = await submit_referral_saas_account_campaign_review(
            account_id=account.account_id,
            tenant_code=account.tenant_code,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            campaign_code=campaign_code,
            setup_summary=_optional_text(review_submission.get("setupSummary")),
            operator_notes=_optional_text(review_submission.get("operatorNotes")) or None,
            requested_review_status=(
                _optional_text(review_submission.get("requestedReviewStatus"))
                or "READY_FOR_REVIEW"
            ),
            reason_code=reason_code,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_CAMPAIGN_REVIEW_SUBMIT",
                    "account_ref": _optional_text(account_ref),
                    "campaign_ref": _optional_text(campaign_code),
                    "idempotency_key": idempotency_key,
                }
            ),
            command_payload_hash=hash_payload(command_payload),
            command_actor_ref=_actor_ref(admin_identity),
            command_actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except ReferralSaasCampaignCommandError as exc:
        raise _campaign_review_error(exc) from exc

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "campaignReview": result.to_safe_dict(),
        "guardrails": list(CAMPAIGN_REVIEW_GUARDRAILS),
        "redactions": list(CAMPAIGN_REVIEW_REDACTIONS),
        "no_campaign_activation_confirmed": True,
        "no_link_generation_confirmed": True,
        "no_validation_track_created_confirmed": True,
        "no_webhook_delivery_confirmed": True,
        "no_invite_or_seat_change_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.post("/accounts/{account_ref}/campaigns/{campaign_code}/review-decisions")
async def record_referral_saas_account_campaign_review_decision_route(
    account_ref: str,
    campaign_code: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    _reject_unsafe_campaign_review_payload(payload)

    account_scope = payload.get("accountScope") or {}
    review_decision = payload.get("reviewDecision") or {}
    if not isinstance(account_scope, dict) or not isinstance(review_decision, dict):
        raise _campaign_review_error(
            CampaignReviewValidationError(
                "accountScope and reviewDecision must be objects."
            )
        )

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = (_optional_text(account_scope.get("context")) or "setup").lower()
    idempotency_key = _optional_text(payload.get("idempotencyKey"))
    correlation_id = _optional_text(payload.get("correlationId"))
    reason_code = (
        _optional_text(payload.get("reasonCode"))
        or "CUSTOMER_PROFILE_CAMPAIGN_REVIEW_DECISION"
    )

    if not ref_type or not external_ref or not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": list(CAMPAIGN_REVIEW_GUARDRAILS),
                "redactions": list(CAMPAIGN_REVIEW_REDACTIONS),
                "no_campaign_activation_confirmed": True,
                "no_link_generation_confirmed": True,
                "no_validation_track_created_confirmed": True,
                "no_webhook_delivery_confirmed": True,
                "no_invite_or_seat_change_confirmed": True,
                "no_money_movement_confirmed": True,
            },
        )

    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=context,
    )
    _assert_account_path_scope(account_ref, account)

    command_payload = {
        "accountScope": {
            "accountRef": _optional_text(account_ref),
            "refType": ref_type,
            "externalRef": external_ref,
            "context": normalised_context,
        },
        "campaignRef": _optional_text(campaign_code),
        "reviewDecision": {
            "decision": _optional_text(review_decision.get("decision")).upper(),
            "reasonPresent": bool(_optional_text(review_decision.get("reason"))),
            "reviewerRef": _optional_text(review_decision.get("reviewerRef")),
        },
    }

    try:
        result = await record_referral_saas_account_campaign_review_decision(
            account_id=account.account_id,
            tenant_code=account.tenant_code,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            campaign_code=campaign_code,
            decision=_optional_text(review_decision.get("decision")),
            reason=_optional_text(review_decision.get("reason")),
            reviewer_ref=_optional_text(review_decision.get("reviewerRef")),
            reason_code=reason_code,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_CAMPAIGN_REVIEW_DECISION",
                    "account_ref": _optional_text(account_ref),
                    "campaign_ref": _optional_text(campaign_code),
                    "idempotency_key": idempotency_key,
                }
            ),
            command_payload_hash=hash_payload(command_payload),
            command_actor_ref=_actor_ref(admin_identity),
            command_actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except ReferralSaasCampaignCommandError as exc:
        raise _campaign_review_error(exc) from exc

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "campaignReview": result.to_safe_dict(),
        "guardrails": list(CAMPAIGN_REVIEW_GUARDRAILS),
        "redactions": list(CAMPAIGN_REVIEW_REDACTIONS),
        "no_campaign_activation_confirmed": True,
        "no_link_generation_confirmed": True,
        "no_validation_track_created_confirmed": True,
        "no_webhook_delivery_confirmed": True,
        "no_invite_or_seat_change_confirmed": True,
        "no_money_movement_confirmed": True,
    }


@router.post("/accounts/{account_ref}/campaigns/{campaign_code}/activation-requests")
async def request_referral_saas_account_campaign_activation_route(
    account_ref: str,
    campaign_code: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_referral_saas_account_reader(identity)
    _reject_unsafe_campaign_activation_payload(payload)

    account_scope = payload.get("accountScope") or {}
    activation_request = payload.get("activationRequest") or {}
    if not isinstance(account_scope, dict) or not isinstance(activation_request, dict):
        raise _campaign_activation_error(
            CampaignActivationValidationError(
                "accountScope and activationRequest must be objects."
            )
        )

    ref_type = _optional_text(account_scope.get("refType"))
    external_ref = _optional_text(account_scope.get("externalRef"))
    context = (
        _optional_text(account_scope.get("context")) or "campaign_activation"
    ).lower()
    idempotency_key = _optional_text(payload.get("idempotencyKey"))
    correlation_id = _optional_text(payload.get("correlationId"))
    reason_code = (
        _optional_text(payload.get("reasonCode"))
        or "CUSTOMER_PROFILE_CAMPAIGN_ACTIVATION"
    )

    if not ref_type or not external_ref or not idempotency_key or not correlation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, "
                    "idempotencyKey, and correlationId are required."
                ),
                "guardrails": list(CAMPAIGN_ACTIVATION_GUARDRAILS),
                "redactions": list(CAMPAIGN_ACTIVATION_REDACTIONS),
                "no_link_generation_confirmed": True,
                "no_validation_track_created_confirmed": True,
                "no_webhook_delivery_confirmed": True,
                "no_invite_or_seat_change_confirmed": True,
                "no_credential_creation_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            },
        )

    resolve_context = "setup" if context == "campaign_activation" else context
    normalised_context, account = await _resolve_referral_saas_account_context(
        ref_type=ref_type,
        external_ref=external_ref,
        context=resolve_context,
    )
    if context == "campaign_activation":
        normalised_context = "campaign_activation"
    _assert_account_path_scope(account_ref, account)

    activation_window = activation_request.get("activationWindow") or {}
    if not isinstance(activation_window, dict):
        raise _campaign_activation_error(
            CampaignActivationValidationError(
                "activationRequest.activationWindow must be an object."
            )
        )

    starts_at = _optional_activation_datetime(activation_window.get("startsAt"))
    ends_at = _optional_activation_datetime(activation_window.get("endsAt"))
    requested_lifecycle = (
        _optional_text(activation_request.get("requestedLifecycleStatus")) or "ACTIVE"
    )
    requested_review_status = (
        _optional_text(activation_request.get("reviewStatus")) or "REVIEW_APPROVED"
    )

    command_payload = {
        "accountScope": {
            "accountRef": _optional_text(account_ref),
            "refType": ref_type,
            "externalRef": external_ref,
            "context": normalised_context,
        },
        "campaignRef": _optional_text(campaign_code),
        "activationRequest": {
            "requestedLifecycleStatus": requested_lifecycle.upper(),
            "reviewStatus": requested_review_status.upper(),
            "goLiveReasonPresent": bool(
                _optional_text(activation_request.get("goLiveReason"))
            ),
            "operatorNotesPresent": bool(
                _optional_text(activation_request.get("operatorNotes"))
            ),
            "activationWindow": {
                "startsAt": _optional_text(activation_window.get("startsAt")) or None,
                "endsAt": _optional_text(activation_window.get("endsAt")) or None,
            },
        },
    }

    try:
        result = await request_referral_saas_account_campaign_activation(
            account_id=account.account_id,
            tenant_code=account.tenant_code,
            account_tenant_id=account.account_tenant_id,
            external_ref_id=account.external_ref_id,
            campaign_code=campaign_code,
            requested_lifecycle_status=requested_lifecycle,
            review_status=requested_review_status,
            go_live_reason=_optional_text(activation_request.get("goLiveReason")),
            operator_notes=_optional_text(activation_request.get("operatorNotes"))
            or None,
            activation_starts_at=starts_at,
            activation_ends_at=ends_at,
            reason_code=reason_code,
            correlation_id=correlation_id,
            idempotency_key_hash=hash_payload(
                {
                    "operation": "REFERRAL_SAAS_CAMPAIGN_ACTIVATION",
                    "account_ref": _optional_text(account_ref),
                    "campaign_ref": _optional_text(campaign_code),
                    "idempotency_key": idempotency_key,
                }
            ),
            command_payload_hash=hash_payload(command_payload),
            command_actor_ref=_actor_ref(admin_identity),
            command_actor_role=str(admin_identity.get("role") or "").upper(),
        )
    except ReferralSaasCampaignCommandError as exc:
        raise _campaign_activation_error(exc) from exc

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "campaignActivation": result.to_safe_dict(),
        "guardrails": list(CAMPAIGN_ACTIVATION_GUARDRAILS),
        "redactions": list(CAMPAIGN_ACTIVATION_REDACTIONS),
        "no_link_generation_confirmed": True,
        "no_validation_track_created_confirmed": True,
        "no_webhook_delivery_confirmed": True,
        "no_invite_or_seat_change_confirmed": True,
        "no_credential_creation_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }


@router.get("/accounts/{account_ref}/campaigns/{campaign_code}/readiness")
async def read_referral_saas_account_campaign_readiness(
    account_ref: str,
    campaign_code: str,
    ref_type: Annotated[
        str,
        Query(
            min_length=1,
            description="External reference type used to resolve the account.",
        ),
    ],
    external_ref: Annotated[
        str,
        Query(
            min_length=1,
            description="External account/customer reference value.",
        ),
    ],
    operation: Annotated[str, Query(min_length=1)] = "CONTROL_PLANE_VIEW",
    context: Annotated[
        str,
        Query(
            description=(
                "setup allows pending setup evidence; runtime requires active "
                "account/reference/tenant-link state."
            ),
        ),
    ] = "setup",
    opportunity_id: str | None = Query(default=None),
    include_evidence: bool = Query(default=True),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)

    normalised_context = str(context or "").strip().lower()
    if normalised_context not in REFERRAL_SAAS_ACCOUNT_CONTEXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "context must be runtime or setup.",
            },
        )

    try:
        if normalised_context == "setup":
            account = await resolve_setup_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
        else:
            account = await resolve_account_by_external_reference(
                ref_type=ref_type,
                external_ref=external_ref,
            )
    except AccountFoundationResolutionError as exc:
        raise _resolution_error(exc) from exc

    safe_account_ref = _optional_text(account_ref)
    if safe_account_ref not in {account.account_id, account.account_code}:
        raise _membership_invitation_error(
            MembershipInvitationUnsafeScope(
                "Path account reference does not match resolved account context."
            )
        )

    try:
        readiness = await get_campaign_readiness(
            tenant_code=account.tenant_code,
            campaign_code=campaign_code,
            operation=operation,
            opportunity_id=opportunity_id,
            include_evidence=include_evidence,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": str(exc),
            },
        ) from exc

    if _has_readiness_blocker(readiness, CAMPAIGN_READINESS_NOT_FOUND_BLOCKERS):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "campaign_readiness_not_found",
                "message": (
                    "Campaign readiness was not found for the selected customer."
                ),
                "redactions": ["internal_tenant_identifier"],
            },
        )

    return {
        "status": "ok",
        "context": normalised_context,
        "account": account.to_safe_dict(),
        "readiness": _redact_internal_scope_keys(readiness),
        "guardrail": (
            "Read-only Referral SaaS customer-scoped campaign readiness. This "
            "endpoint resolves the selected account internally and does not "
            "expose tenant_code, create campaigns, update policies, generate "
            "links, activate campaigns, trigger go-live, or move money."
        ),
        "redactions": ["internal_tenant_identifier"],
        "no_campaign_mutation_confirmed": True,
        "no_policy_write_confirmed": True,
        "no_link_generation_confirmed": True,
        "no_campaign_activation_confirmed": True,
        "no_money_movement_confirmed": True,
    }


def _account_creation_guardrails() -> list[str]:
    return [
        "DURABLE_ACCOUNT_FOUNDATION_ONLY",
        "BOUNDED_INTERNAL_TENANT_SEED",
        "NO_EXTERNAL_TENANT_IDENTIFIER_EXPOSURE",
        "NO_MEMBERSHIP_WRITE",
        "NO_INVITE_DELIVERY",
        "NO_ACCOUNT_ACTIVATION",
        "NO_CAMPAIGN_PUBLICATION",
        "NO_CREDENTIAL_LIFECYCLE",
        "NO_WEBHOOK_DISPATCH",
        "NO_MONEY_MOVEMENT",
    ]


def _membership_invitation_guardrails() -> list[str]:
    return [
        "NO_RAW_EMAIL_STORAGE",
        "NO_EMAIL_DELIVERY_WITHOUT_PROVIDER",
        "NO_AUTH_CLAIM_CHANGE",
        "NO_SEAT_ASSIGNMENT",
        "NO_TENANT_CODE_EXPOSURE",
        "NO_MONEY_MOVEMENT",
    ]


def _membership_invitation_redactions() -> list[str]:
    return [
        "internal_tenant_identifier",
        "user_identifier",
        "client_identifier",
        "email_hash",
        "idempotency_key_hash",
    ]


def _membership_activation_guardrails() -> list[str]:
    return _membership_invitation_guardrails() + [
        "NO_INVITE_DELIVERY",
        "NO_AUTH_PROVIDER_WRITE",
    ]


def _membership_activation_redactions() -> list[str]:
    return _membership_invitation_redactions() + [
        "accepted_subject",
        "acceptance_evidence_ref",
    ]


def _access_provisioning_guardrails() -> list[str]:
    return list(ACCESS_PROVISIONING_GUARDRAILS)


def _access_provisioning_redactions() -> list[str]:
    return list(ACCESS_PROVISIONING_REDACTIONS)


def _profile_maintenance_guardrails() -> list[str]:
    return [
        "DURABLE_PROFILE_FIELDS_ONLY",
        "NO_EXTERNAL_REFERENCE_ROTATION",
        "NO_ACCOUNT_ACTIVATION",
        "NO_MEMBERSHIP_WRITE",
        "NO_INVITE_DELIVERY",
        "NO_CREDENTIAL_LIFECYCLE",
        "NO_WEBHOOK_DISPATCH",
        "NO_CAMPAIGN_PUBLICATION",
        "NO_GO_LIVE_ACTION",
        "NO_MONEY_MOVEMENT",
    ]


def _profile_maintenance_redactions() -> list[str]:
    return [
        "internal_tenant_identifier",
        "raw_secret",
        "idempotency_key_hash",
    ]


@router.get("/accounts")
async def list_referral_saas_account_registry(
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=MAX_ACCOUNT_LIST_LIMIT,
            description="Maximum number of Referral SaaS account foundations to return.",
        ),
    ] = 50,
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_referral_saas_account_reader(identity)
    accounts = await list_referral_saas_accounts(limit=limit)
    return {
        "status": "ok",
        "count": len(accounts),
        "accounts": [account.to_safe_dict() for account in accounts],
        "guardrail": (
            "Read-only Referral SaaS account registry. This endpoint does not "
            "create accounts, create tenants, convert onboarding drafts, invite "
            "users, write memberships, rotate references, activate campaigns, "
            "trigger go-live, write audit events, repair, replay, retry, or "
            "mutate funding, fulfilment, settlement, reward, commission, wallet, "
            "invoice, billing, or DLaaS marketplace records."
        ),
        "redactions": ["internal_tenant_identifier"],
    }


UNSAFE_INVITATION_KEYS = {
    "tenant_code",
    "tenantCode",
    "internal_tenant_code",
    "internalTenantCode",
    "email",
    "rawEmail",
    "password",
    "secret",
    "token",
    "credentials",
    "authClaims",
    "seatId",
    "sendInvite",
    "delivery",
    "activate",
    "goLive",
    "campaignActivation",
    "webhook",
    "reward",
    "funding",
    "fulfilment",
    "settlement",
    "commission",
    "wallet",
    "invoice",
    "payout",
    "sponsorBilling",
}

UNSAFE_PROFILE_KEYS = {
    "tenant_code",
    "tenantCode",
    "internal_tenant_code",
    "internalTenantCode",
    "externalRef",
    "external_ref",
    "externalTenantRef",
    "external_tenant_ref",
    "organisationRef",
    "organisation_ref",
    "email",
    "rawEmail",
    "password",
    "secret",
    "token",
    "credentials",
    "authClaims",
    "seatId",
    "sendInvite",
    "delivery",
    "activate",
    "goLive",
    "campaignActivation",
    "webhook",
    "reward",
    "funding",
    "fulfilment",
    "settlement",
    "commission",
    "wallet",
    "invoice",
    "payout",
    "sponsorBilling",
}

UNSAFE_CAMPAIGN_SETUP_KEYS = {
    "tenant_code",
    "tenantCode",
    "internal_tenant_code",
    "internalTenantCode",
    "campaign_code",
    "campaignCode",
    "isActive",
    "is_active",
    "activate",
    "goLive",
    "campaignActivation",
    "generateLinks",
    "linkGeneration",
    "validate",
    "campaignTrackId",
    "campaign_track_id",
    "policy",
    "policyWrite",
    "webhook",
    "reward",
    "funding",
    "fulfilment",
    "settlement",
    "commission",
    "wallet",
    "invoice",
    "payout",
    "sponsorBilling",
}

UNSAFE_CAMPAIGN_POLICY_SETTINGS_KEYS = {
    "tenant_code",
    "tenantCode",
    "internal_tenant_code",
    "internalTenantCode",
    "campaign_code",
    "campaignCode",
    "isActive",
    "is_active",
    "activate",
    "activation",
    "goLive",
    "campaignActivation",
    "generateLinks",
    "linkGeneration",
    "validate",
    "campaignTrackId",
    "campaign_track_id",
    "webhook",
    "credential",
    "credentials",
    "providerSecret",
    "secret",
    "rewardAmount",
    "rewardAmounts",
    "reward_amounts_json",
    "funding",
    "fulfilment",
    "settlement",
    "commission",
    "wallet",
    "invoice",
    "payout",
    "sponsorBilling",
}

UNSAFE_CAMPAIGN_REVIEW_KEYS = {
    "tenant_code",
    "tenantCode",
    "internal_tenant_code",
    "internalTenantCode",
    "campaign_code",
    "campaignCode",
    "isActive",
    "is_active",
    "activate",
    "activation",
    "goLive",
    "campaignActivation",
    "generateLinks",
    "linkGeneration",
    "link",
    "track",
    "validate",
    "campaignTrackId",
    "campaign_track_id",
    "webhook",
    "credential",
    "credentials",
    "providerSecret",
    "secret",
    "invite",
    "seat",
    "seatId",
    "authClaim",
    "authClaims",
    "billing",
    "rewardAmount",
    "rewardAmounts",
    "funding",
    "fulfilment",
    "settlement",
    "commission",
    "wallet",
    "invoice",
    "payout",
    "sponsorBilling",
}

UNSAFE_CAMPAIGN_ACTIVATION_KEYS = {
    "tenant_code",
    "tenantCode",
    "internal_tenant_code",
    "internalTenantCode",
    "campaign_code",
    "campaignCode",
    "isActive",
    "is_active",
    "generateLinks",
    "linkGeneration",
    "link",
    "track",
    "validate",
    "campaignTrackId",
    "campaign_track_id",
    "webhook",
    "credential",
    "credentials",
    "providerSecret",
    "secret",
    "invite",
    "seat",
    "seatId",
    "authClaim",
    "authClaims",
    "billing",
    "rewardAmount",
    "rewardAmounts",
    "funding",
    "fulfilment",
    "settlement",
    "commission",
    "wallet",
    "invoice",
    "payout",
    "sponsorBilling",
}


def _reject_unsafe_invitation_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in UNSAFE_INVITATION_KEYS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "REJECTED_UNSAFE_PAYLOAD",
                        "message": (
                            "Membership invitation payload includes unsafe "
                            "live-action fields."
                        ),
                        "guardrails": _membership_invitation_guardrails(),
                        "redactions": _membership_invitation_redactions(),
                        "no_invite_delivery_confirmed": True,
                        "no_auth_claim_change_confirmed": True,
                        "no_seat_assignment_confirmed": True,
                        "no_money_movement_confirmed": True,
                    },
                )
            _reject_unsafe_invitation_payload(child)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_invitation_payload(item)


def _reject_unsafe_profile_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in UNSAFE_PROFILE_KEYS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "REJECTED_UNSAFE_PAYLOAD",
                        "message": (
                            "Customer profile payload includes fields that belong "
                            "to reference rotation, access, activation, credentials, "
                            "or adjacent money workflows."
                        ),
                        "guardrails": _profile_maintenance_guardrails(),
                        "redactions": _profile_maintenance_redactions(),
                        "no_external_reference_rotation_confirmed": True,
                        "no_account_activation_confirmed": True,
                        "no_membership_write_confirmed": True,
                        "no_money_movement_confirmed": True,
                    },
                )
            _reject_unsafe_profile_payload(child)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_profile_payload(item)


def _reject_unsafe_campaign_setup_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in UNSAFE_CAMPAIGN_SETUP_KEYS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "REJECTED_UNSAFE_PAYLOAD",
                        "message": (
                            "Campaign setup payload includes fields that belong "
                            "to activation, policy, link generation, validation, "
                            "webhook, or adjacent money workflows."
                        ),
                        "guardrails": list(CAMPAIGN_SETUP_GUARDRAILS),
                        "redactions": list(CAMPAIGN_SETUP_REDACTIONS),
                        "no_campaign_activation_confirmed": True,
                        "no_link_generation_confirmed": True,
                        "no_validation_track_created_confirmed": True,
                        "no_policy_write_confirmed": True,
                        "no_webhook_delivery_confirmed": True,
                        "no_money_movement_confirmed": True,
                    },
                )
            _reject_unsafe_campaign_setup_payload(child)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_campaign_setup_payload(item)


def _reject_unsafe_campaign_policy_settings_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in UNSAFE_CAMPAIGN_POLICY_SETTINGS_KEYS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "REJECTED_UNSAFE_PAYLOAD",
                        "message": (
                            "Campaign policy/settings payload includes fields "
                            "that belong to tenant scope, activation, link "
                            "generation, validation, webhook, credential, or "
                            "money workflows."
                        ),
                        "guardrails": list(CAMPAIGN_POLICY_SETTINGS_GUARDRAILS),
                        "redactions": list(CAMPAIGN_POLICY_SETTINGS_REDACTIONS),
                        "no_campaign_activation_confirmed": True,
                        "no_link_generation_confirmed": True,
                        "no_validation_track_created_confirmed": True,
                        "no_webhook_delivery_confirmed": True,
                        "no_money_movement_confirmed": True,
                    },
                )
            _reject_unsafe_campaign_policy_settings_payload(child)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_campaign_policy_settings_payload(item)


def _reject_unsafe_campaign_review_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in UNSAFE_CAMPAIGN_REVIEW_KEYS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "REJECTED_UNSAFE_PAYLOAD",
                        "message": (
                            "Campaign review payload includes fields that "
                            "belong to tenant scope, activation, link "
                            "generation, validation, webhook, access, billing, "
                            "or money workflows."
                        ),
                        "guardrails": list(CAMPAIGN_REVIEW_GUARDRAILS),
                        "redactions": list(CAMPAIGN_REVIEW_REDACTIONS),
                        "no_campaign_activation_confirmed": True,
                        "no_link_generation_confirmed": True,
                        "no_validation_track_created_confirmed": True,
                        "no_webhook_delivery_confirmed": True,
                        "no_invite_or_seat_change_confirmed": True,
                        "no_money_movement_confirmed": True,
                    },
                )
            _reject_unsafe_campaign_review_payload(child)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_campaign_review_payload(item)


def _reject_unsafe_campaign_activation_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in UNSAFE_CAMPAIGN_ACTIVATION_KEYS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "REJECTED_UNSAFE_PAYLOAD",
                        "message": (
                            "Campaign activation payload includes fields that "
                            "belong to tenant scope, link generation, "
                            "validation, webhook, access, billing, credential, "
                            "or money workflows."
                        ),
                        "guardrails": list(CAMPAIGN_ACTIVATION_GUARDRAILS),
                        "redactions": list(CAMPAIGN_ACTIVATION_REDACTIONS),
                        "no_link_generation_confirmed": True,
                        "no_validation_track_created_confirmed": True,
                        "no_webhook_delivery_confirmed": True,
                        "no_invite_or_seat_change_confirmed": True,
                        "no_credential_creation_confirmed": True,
                        "no_billing_or_money_movement_confirmed": True,
                    },
                )
            _reject_unsafe_campaign_activation_payload(child)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_campaign_activation_payload(item)


def _actor_ref(identity: dict[str, Any]) -> str:
    return (
        _optional_text(identity.get("subject"))
        or _optional_text(identity.get("client_id"))
        or _optional_text(identity.get("role"))
        or "REFERRAL_SAAS_ACCOUNT_OPERATOR"
    )


def _normalise_activation_request_seat_types(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [_optional_text(item) for item in value if _optional_text(item)]
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "code": "validation_error",
            "message": "activation.seatTypes must be a list of seat type values.",
            "guardrails": list(ACCOUNT_FOUNDATION_ACTIVATION_GUARDRAILS),
            "redactions": list(ACCOUNT_FOUNDATION_ACTIVATION_REDACTIONS),
            "no_membership_write_confirmed": True,
            "no_seat_assignment_confirmed": True,
            "no_invite_delivery_confirmed": True,
            "no_auth_claim_change_confirmed": True,
            "no_billing_or_money_movement_confirmed": True,
        },
    )


def _optional_text(value: Any) -> str:
    return str(value or "").strip()


def _optional_datetime(value: Any) -> datetime | None:
    safe_value = _optional_text(value)
    if not safe_value:
        return None
    try:
        return datetime.fromisoformat(safe_value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise _campaign_setup_error(
            CampaignSetupValidationError(
                "campaign startsAt and endsAt must be ISO datetime values."
            )
        ) from exc


def _optional_activation_datetime(value: Any) -> datetime | None:
    safe_value = _optional_text(value)
    if not safe_value:
        return None
    try:
        return datetime.fromisoformat(safe_value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise _campaign_activation_error(
            CampaignActivationValidationError(
                "activationRequest.activationWindow dates must be ISO datetime values."
            )
        ) from exc
