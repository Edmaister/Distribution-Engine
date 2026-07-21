from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

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
    request_referral_saas_membership_invitation_delivery,
)
from services.referral_saas_technical_setup_service import (
    build_referral_saas_technical_setup_readiness,
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
        or not recipient_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "validation_error",
                "message": (
                    "accountScope.refType, accountScope.externalRef, delivery.providerRef, "
                    "delivery.channel, delivery.templateRef, delivery.recipientHash, "
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


def _actor_ref(identity: dict[str, Any]) -> str:
    return (
        _optional_text(identity.get("subject"))
        or _optional_text(identity.get("client_id"))
        or _optional_text(identity.get("role"))
        or "REFERRAL_SAAS_ACCOUNT_OPERATOR"
    )


def _optional_text(value: Any) -> str:
    return str(value or "").strip()
