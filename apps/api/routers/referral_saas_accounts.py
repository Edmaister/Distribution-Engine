from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from services.referral_saas_account_foundation_service import (
    AccountFoundationResolutionError,
    AccountNotResolvable,
    ExternalReferenceConflict,
    ExternalReferenceNotActive,
    ExternalReferenceNotFound,
    InvalidExternalReferenceType,
    TenantLinkNotResolvable,
    resolve_account_by_external_reference,
    resolve_setup_account_by_external_reference,
)
from services.referral_saas_account_setup_service import (
    AccountSetupCommandError,
    AccountSetupDraftNotFound,
    AccountSetupDuplicateReference,
    AccountSetupInvalidDraftState,
    AccountSetupMissingScope,
    AccountSetupPermissionDenied,
    create_durable_account_from_onboarding_draft,
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


def _account_creation_guardrails() -> list[str]:
    return [
        "DURABLE_ACCOUNT_FOUNDATION_ONLY",
        "EXISTING_INTERNAL_TENANT_REQUIRED",
        "NO_TENANT_CREATION",
        "NO_MEMBERSHIP_WRITE",
        "NO_INVITE_DELIVERY",
        "NO_ACCOUNT_ACTIVATION",
        "NO_CAMPAIGN_PUBLICATION",
        "NO_CREDENTIAL_LIFECYCLE",
        "NO_WEBHOOK_DISPATCH",
        "NO_MONEY_MOVEMENT",
    ]


def _actor_ref(identity: dict[str, Any]) -> str:
    return (
        _optional_text(identity.get("subject"))
        or _optional_text(identity.get("client_id"))
        or _optional_text(identity.get("role"))
        or "REFERRAL_SAAS_ACCOUNT_OPERATOR"
    )


def _optional_text(value: Any) -> str:
    return str(value or "").strip()
