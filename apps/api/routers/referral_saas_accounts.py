from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from services.campaign_readiness_service import get_campaign_readiness
from services.referral_saas_account_foundation_service import (
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
    list_referral_saas_accounts,
    resolve_account_by_external_reference,
    resolve_setup_account_by_external_reference,
    update_referral_saas_account_profile,
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
from services.referral_saas_account_membership_service import (
    MembershipInvitationAccountNotReady,
    MembershipInvitationCommandError,
    MembershipInvitationDuplicate,
    MembershipInvitationDeliveryNotInvited,
    MembershipInvitationDeliveryProviderNotConfigured,
    MembershipInvitationIdempotencyConflict,
    MembershipInvitationUnsafePayload,
    MembershipInvitationUnsafeScope,
    MembershipInvitationValidationError,
    get_referral_saas_membership_activation_readiness,
    get_referral_saas_account_membership_posture,
    record_referral_saas_membership_invitation_intent,
    request_referral_saas_membership_activation,
    request_referral_saas_membership_invitation_delivery,
)
from services.referral_saas_campaign_service import (
    CAMPAIGN_ACTIVATION_GUARDRAILS,
    CAMPAIGN_ACTIVATION_REDACTIONS,
    CAMPAIGN_SETUP_GUARDRAILS,
    CAMPAIGN_SETUP_REDACTIONS,
    CAMPAIGN_POLICY_SETTINGS_GUARDRAILS,
    CAMPAIGN_POLICY_SETTINGS_REDACTIONS,
    CAMPAIGN_REVIEW_GUARDRAILS,
    CAMPAIGN_REVIEW_REDACTIONS,
    CampaignSetupAccountNotReady,
    CampaignSetupDuplicate,
    CampaignSetupIdempotencyConflict,
    CampaignSetupValidationError,
    CampaignPolicySettingsAccountNotReady,
    CampaignPolicySettingsCampaignNotFound,
    CampaignPolicySettingsIdempotencyConflict,
    CampaignPolicySettingsValidationError,
    CampaignReviewCampaignNotFound,
    CampaignReviewIdempotencyConflict,
    CampaignReviewInvalidState,
    CampaignReviewNotReady,
    CampaignReviewValidationError,
    CampaignActivationAlreadyActive,
    CampaignActivationCampaignNotFound,
    CampaignActivationIdempotencyConflict,
    CampaignActivationNotReady,
    CampaignActivationValidationError,
    ReferralSaasCampaignCommandError,
    create_referral_saas_account_campaign_setup,
    record_referral_saas_account_campaign_review_decision,
    submit_referral_saas_account_campaign_review,
    request_referral_saas_account_campaign_activation,
    upsert_referral_saas_account_campaign_policy_settings,
    list_referral_saas_account_campaigns,
    get_referral_saas_account_campaign,
)
from services.referral_code import (
    get_or_create_referrer_code,
    validate_referral_code,
)
from services.referral_saas_validation_service import (
    build_referral_saas_validation_result,
)
from services.referral_saas_technical_setup_service import (
    build_referral_saas_technical_setup_readiness,
)
from services.referral_saas_reporting_service import (
    build_referral_saas_report_export_preview,
    get_referral_saas_report,
    validate_referral_saas_report_export_request,
)
from services.onboarding.onboarding_draft_idempotency_service import hash_payload
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


class ReferralSaasAccountReportExportRequest(BaseModel):
    format: str | None = Field(default=None, description="json or csv.")
    redaction_profile: str | None = Field(default=None)
    dimensions: list[str] | None = Field(default=None)
    filters: dict[str, Any] | None = Field(default=None)
    row_limit: int | None = Field(default=None)
    data_window_start: datetime | None = Field(default=None)
    data_window_end: datetime | None = Field(default=None)


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
        report = get_referral_saas_report(
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
        export_preview = build_referral_saas_report_export_preview(
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
        "readiness": readiness,
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
