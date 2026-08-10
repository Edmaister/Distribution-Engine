from __future__ import annotations

import json
import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Final

from fastapi import HTTPException

from services.channel_readiness_service import (
    dispatch_channel_message,
    get_channel_readiness,
)
from utils.db import db_connection

MEMBERSHIP_STATUSES = ("INVITED", "ACTIVE", "SUSPENDED", "DISABLED", "ARCHIVED")
MEMBERSHIP_ACCEPTANCE_TOKEN_STATUSES = ("ISSUED", "ACCEPTED", "EXPIRED", "REVOKED")
MEMBERSHIP_INVITATION_EVENT: Final = "REFERRAL_SAAS_MEMBERSHIP_INVITATION_INTENT"
MEMBERSHIP_INVITATION_UPDATE_EVENT: Final = (
    "REFERRAL_SAAS_MEMBERSHIP_INVITATION_INTENT_UPDATE"
)
MEMBERSHIP_INVITATION_CANCEL_EVENT: Final = (
    "REFERRAL_SAAS_MEMBERSHIP_INVITATION_INTENT_CANCEL"
)
MEMBERSHIP_INVITATION_DELIVERY_EVENT: Final = (
    "REFERRAL_SAAS_MEMBERSHIP_INVITATION_DELIVERY_REQUEST"
)
MEMBERSHIP_INVITATION_ACCEPTANCE_TOKEN_EVENT: Final = (
    "REFERRAL_SAAS_MEMBERSHIP_INVITATION_ACCEPTANCE_TOKEN"
)
MEMBERSHIP_INVITATION_ACCEPTANCE_TOKEN_TTL_HOURS: Final = 72
MEMBERSHIP_ACTIVATION_EVENT: Final = (
    "REFERRAL_SAAS_MEMBERSHIP_ACTIVATION_REQUEST"
)
MEMBERSHIP_ACCESS_PROVISIONING_EVENT: Final = (
    "REFERRAL_SAAS_ACCESS_PROVISIONING_REQUEST"
)
MEMBERSHIP_LOGIN_COMPLETION_EVENT: Final = (
    "REFERRAL_SAAS_LOGIN_COMPLETION_INTENT"
)
EVENT_RECORDED: Final = "RECORDED"
EVENT_DUPLICATE: Final = "DUPLICATE"
USER_ACTOR: Final = "USER"
CLIENT_ACTOR: Final = "CLIENT"
PRIMARY_TENANT_SCOPE: Final = "PRIMARY_ACCOUNT_TENANT"
MANUAL_ACCESS_ACCEPTANCE_REASON: Final = "AMPLIFI_ADMIN_MANUAL_ACCESS_ACCEPTANCE"
MANUAL_ACCESS_ACCEPTANCE_ADMIN_ROLES: Final = frozenset({"ADMIN", "AMPLIFI_ADMIN"})
MANUAL_ACCESS_ACCEPTANCE_ACCOUNT_STATUSES: Final = frozenset(
    {"ACTIVE", "PENDING_ONBOARDING"}
)
MANUAL_ACCESS_ACCEPTANCE_TENANT_LINK_STATUSES: Final = frozenset(
    {"ACTIVE", "PENDING_SETUP"}
)
ACCESS_PROVISIONING_ADMIN_ROLES: Final = frozenset({"ADMIN", "AMPLIFI_ADMIN"})
ACCESS_PROVISIONING_SEAT_TYPES: Final = frozenset(
    {"ADMIN", "OPERATOR", "PARTNER", "PRODUCER", "DISTRIBUTOR", "CONSUMER", "SUPPORT"}
)
LOGIN_COMPLETION_ADMIN_ROLES: Final = frozenset({"ADMIN", "AMPLIFI_ADMIN"})
LOGIN_COMPLETION_INTENTS: Final = frozenset(
    {"PLATFORM_LOGIN_REQUIRED", "LOGIN_NOT_REQUIRED", "EXTERNAL_IDP_MANAGED"}
)
LOGIN_COMPLETION_PERMISSION_PROFILES: Final = {
    "DISTRIBUTION_ADMIN": "REFERRAL_SAAS_ACCOUNT_ADMIN",
    "CAMPAIGN_MANAGER": "REFERRAL_SAAS_CAMPAIGN_MANAGER",
    "SUPPORT": "REFERRAL_SAAS_SUPPORT",
    "FINANCE_ADMIN": "REFERRAL_SAAS_ANALYST",
}

ROLE_FAMILIES: Final = frozenset(
    {
        "PLATFORM_ADMIN",
        "SYSTEM_ADMIN",
        "FINANCE_ADMIN",
        "DISTRIBUTION_ADMIN",
        "CAMPAIGN_MANAGER",
        "PARTNER",
        "PRODUCER",
        "DISTRIBUTOR",
        "CONSUMER",
        "SUPPORT",
    }
)

INVITATION_GUARDRAILS: Final = (
    "NO_RAW_EMAIL_STORAGE",
    "NO_EMAIL_DELIVERY_WITHOUT_PROVIDER",
    "NO_AUTH_CLAIM_CHANGE",
    "NO_SEAT_ASSIGNMENT",
    "NO_TENANT_CODE_EXPOSURE",
    "NO_MONEY_MOVEMENT",
)

INVITATION_REDACTIONS: Final = (
    "internal_tenant_identifier",
    "user_identifier",
    "client_identifier",
    "email_hash",
    "idempotency_key_hash",
)

ACCESS_PROVISIONING_GUARDRAILS: Final = (
    "AVAILABLE_SEAT_REQUIRED",
    "ACTIVE_ACCOUNT_REQUIRED",
    "ACTIVE_TENANT_LINK_REQUIRED",
    "ACTIVE_EXTERNAL_REFERENCE_REQUIRED",
    "ACTIVE_MEMBERSHIP_REQUIRED",
    "NO_INVITE_DELIVERY",
    "NO_AUTH_CLAIM_CHANGE",
    "NO_CREDENTIAL_CREATION",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_GO_LIVE_CHANGE",
    "NO_TENANT_CODE_EXPOSURE",
    "NO_MONEY_MOVEMENT",
)

ACCESS_PROVISIONING_REDACTIONS: Final = INVITATION_REDACTIONS + (
    "seat_assignment_evidence_ref",
    "auth_provider_ref",
    "auth_claim_evidence_ref",
    "provider_secret",
    "raw_auth_claims",
)

LOGIN_COMPLETION_GUARDRAILS: Final = (
    "ACTIVE_ACCOUNT_REQUIRED",
    "ACTIVE_TENANT_LINK_REQUIRED",
    "ACTIVE_EXTERNAL_REFERENCE_REQUIRED",
    "ACTIVE_MEMBERSHIP_REQUIRED",
    "GOVERNED_PERMISSION_PROFILE_REQUIRED",
    "SEAT_REQUIRED_FOR_PLATFORM_LOGIN",
    "AUTH_PROVIDER_EVIDENCE_REQUIRED",
    "NO_RAW_CREDENTIAL_STORAGE",
    "NO_TOKEN_EXPOSURE",
    "NO_INVITE_DELIVERY",
    "NO_AUTH_CLAIM_MUTATION",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_BILLING_OR_MONEY_MOVEMENT",
    "NO_TENANT_CODE_EXPOSURE",
)

LOGIN_COMPLETION_REDACTIONS: Final = INVITATION_REDACTIONS + (
    "identity_subject_ref",
    "auth_provider_ref",
    "seat_evidence_ref",
    "provider_payload",
    "provider_secret",
    "raw_auth_claims",
)

IDENTITY_LOGIN_RECONCILIATION_GUARDRAILS: Final = LOGIN_COMPLETION_GUARDRAILS + (
    "READ_ONLY_RECONCILIATION",
    "NO_IDENTITY_PROVIDER_MUTATION",
    "NO_SEAT_ASSIGNMENT",
)

IDENTITY_LOGIN_RECONCILIATION_REDACTIONS: Final = LOGIN_COMPLETION_REDACTIONS + (
    "identity_provider_evidence",
    "auth_claim_evidence",
    "revocation_evidence",
)


class MembershipInvitationCommandError(Exception):
    safe_code = "MEMBERSHIP_INVITATION_FAILED"

    def __init__(self, message: str, *, safe_code: str | None = None):
        super().__init__(message)
        if safe_code:
            self.safe_code = safe_code


class MembershipInvitationValidationError(MembershipInvitationCommandError):
    safe_code = "VALIDATION_ERROR"


class MembershipInvitationUnsafePayload(MembershipInvitationCommandError):
    safe_code = "REJECTED_UNSAFE_PAYLOAD"


class MembershipInvitationUnsafeScope(MembershipInvitationCommandError):
    safe_code = "REJECTED_UNSAFE_SCOPE"


class MembershipInvitationAccountNotReady(MembershipInvitationCommandError):
    safe_code = "ACCOUNT_NOT_READY"


class MembershipInvitationDuplicate(MembershipInvitationCommandError):
    safe_code = "MEMBERSHIP_ALREADY_EXISTS"


class MembershipInvitationIdempotencyConflict(MembershipInvitationCommandError):
    safe_code = "IDEMPOTENCY_CONFLICT"


class MembershipInvitationNotFound(MembershipInvitationCommandError):
    safe_code = "MEMBERSHIP_INVITATION_NOT_FOUND"


class MembershipInvitationNotEditable(MembershipInvitationCommandError):
    safe_code = "MEMBERSHIP_INVITATION_NOT_EDITABLE"


class MembershipInvitationDeliveryNotInvited(MembershipInvitationCommandError):
    safe_code = "DELIVERY_REJECTED_MEMBERSHIP_NOT_INVITED"


class MembershipInvitationDeliveryProviderNotConfigured(
    MembershipInvitationCommandError
):
    safe_code = "DELIVERY_PROVIDER_NOT_CONFIGURED"


class MembershipInvitationDeliveryProviderFailed(MembershipInvitationCommandError):
    safe_code = "DELIVERY_PROVIDER_FAILED"


class MembershipInvitationAcceptanceTokenInvalid(MembershipInvitationCommandError):
    safe_code = "ACCEPTANCE_TOKEN_INVALID"


class MembershipInvitationAcceptanceTokenExpired(MembershipInvitationCommandError):
    safe_code = "ACCEPTANCE_TOKEN_EXPIRED"


class MembershipInvitationAcceptanceTokenReplay(MembershipInvitationCommandError):
    safe_code = "ACCEPTANCE_TOKEN_REPLAYED"


class MembershipActivationNotInvited(MembershipInvitationCommandError):
    safe_code = "ACTIVATION_REJECTED_MEMBERSHIP_NOT_INVITED"


class MembershipActivationIdentityNotAccepted(MembershipInvitationCommandError):
    safe_code = "ACTIVATION_REJECTED_IDENTITY_NOT_ACCEPTED"


class MembershipActivationAccountNotActive(MembershipInvitationCommandError):
    safe_code = "ACTIVATION_REJECTED_ACCOUNT_NOT_ACTIVE"


class MembershipActivationTenantLinkNotActive(MembershipInvitationCommandError):
    safe_code = "ACTIVATION_REJECTED_TENANT_LINK_NOT_ACTIVE"


class MembershipActivationExternalReferenceNotActive(MembershipInvitationCommandError):
    safe_code = "ACTIVATION_REJECTED_EXTERNAL_REFERENCE_NOT_ACTIVE"


class MembershipActivationDuplicateActiveMembership(MembershipInvitationCommandError):
    safe_code = "ACTIVATION_REJECTED_DUPLICATE_ACTIVE_MEMBERSHIP"


class AccessProvisioningAccountNotActive(MembershipInvitationCommandError):
    safe_code = "PROVISIONING_REJECTED_ACCOUNT_NOT_ACTIVE"


class AccessProvisioningTenantLinkNotActive(MembershipInvitationCommandError):
    safe_code = "PROVISIONING_REJECTED_TENANT_LINK_NOT_ACTIVE"


class AccessProvisioningExternalReferenceNotActive(MembershipInvitationCommandError):
    safe_code = "PROVISIONING_REJECTED_EXTERNAL_REFERENCE_NOT_ACTIVE"


class AccessProvisioningMembershipNotActive(MembershipInvitationCommandError):
    safe_code = "PROVISIONING_REJECTED_MEMBERSHIP_NOT_ACTIVE"


class AccessProvisioningSeatUnavailable(MembershipInvitationCommandError):
    safe_code = "PROVISIONING_REJECTED_SEAT_UNAVAILABLE"


class AccessProvisioningAuthProviderNotReady(MembershipInvitationCommandError):
    safe_code = "PROVISIONING_REJECTED_AUTH_PROVIDER_NOT_READY"


class LoginCompletionAccountNotActive(MembershipInvitationCommandError):
    safe_code = "LOGIN_COMPLETION_BLOCKED_ACCOUNT_NOT_ACTIVE"


class LoginCompletionTenantLinkNotActive(MembershipInvitationCommandError):
    safe_code = "LOGIN_COMPLETION_BLOCKED_TENANT_LINK_NOT_ACTIVE"


class LoginCompletionExternalReferenceNotActive(MembershipInvitationCommandError):
    safe_code = "LOGIN_COMPLETION_BLOCKED_EXTERNAL_REFERENCE_NOT_ACTIVE"


class LoginCompletionMembershipNotActive(MembershipInvitationCommandError):
    safe_code = "LOGIN_COMPLETION_BLOCKED_MEMBERSHIP_NOT_ACTIVE"


class LoginCompletionSeatNotAssigned(MembershipInvitationCommandError):
    safe_code = "LOGIN_COMPLETION_BLOCKED_SEAT_NOT_ASSIGNED"


class LoginCompletionAuthProviderNotApproved(MembershipInvitationCommandError):
    safe_code = "LOGIN_COMPLETION_BLOCKED_AUTH_PROVIDER_NOT_APPROVED"


class LoginCompletionPermissionProfileMissing(MembershipInvitationCommandError):
    safe_code = "LOGIN_COMPLETION_BLOCKED_PERMISSION_PROFILE_MISSING"


@dataclass(frozen=True)
class MembershipInvitationLifecycleResult:
    command_status: str
    account_id: str
    membership_id: str
    previous_membership_status: str
    membership_status: str
    role_family: str
    permission_set: str
    idempotency_status: str
    audit_event_id: str | None
    lifecycle_next_action: str
    guardrails: tuple[str, ...] = INVITATION_GUARDRAILS
    redactions: tuple[str, ...] = INVITATION_REDACTIONS

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "membership": {
                "membershipRef": self.membership_id,
                "previousStatus": self.previous_membership_status,
                "status": self.membership_status,
                "roleFamily": self.role_family,
                "permissionSet": self.permission_set,
            },
            "lifecycle": {
                "status": self.command_status,
                "nextAction": self.lifecycle_next_action,
            },
            "idempotency": {
                "status": self.idempotency_status,
            },
            "auditEventId": self.audit_event_id,
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noInviteDeliveryConfirmed": True,
            "noMembershipActivationConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class MembershipInvitationIntentResult:
    command_status: str
    account_id: str
    membership_id: str
    membership_status: str
    role_family: str
    permission_set: str
    can_operate_setup: bool
    delivery_status: str
    delivery_next_action: str
    idempotency_status: str
    audit_event_id: str | None
    guardrails: tuple[str, ...] = INVITATION_GUARDRAILS
    redactions: tuple[str, ...] = INVITATION_REDACTIONS

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "membership": {
                "membershipRef": self.membership_id,
                "status": self.membership_status,
                "roleFamily": self.role_family,
                "permissionSet": self.permission_set,
                "canOperateSetup": self.can_operate_setup,
            },
            "delivery": {
                "status": self.delivery_status,
                "nextAction": self.delivery_next_action,
            },
            "idempotency": {
                "status": self.idempotency_status,
            },
            "auditEventId": self.audit_event_id,
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noInviteDeliveryConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class MembershipActivationRequestResult:
    command_status: str
    account_id: str
    membership_id: str
    previous_membership_status: str
    membership_status: str
    role_family: str
    permission_set: str
    accepted_subject_status: str
    activation_next_action: str
    idempotency_status: str
    audit_event_id: str | None
    guardrails: tuple[str, ...] = INVITATION_GUARDRAILS + (
        "NO_INVITE_DELIVERY",
        "NO_AUTH_PROVIDER_WRITE",
    )
    redactions: tuple[str, ...] = INVITATION_REDACTIONS + (
        "accepted_subject",
        "acceptance_evidence_ref",
    )

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "membership": {
                "membershipRef": self.membership_id,
                "previousStatus": self.previous_membership_status,
                "status": self.membership_status,
                "roleFamily": self.role_family,
                "permissionSet": self.permission_set,
            },
            "activation": {
                "status": self.command_status,
                "acceptedSubjectStatus": self.accepted_subject_status,
                "nextAction": self.activation_next_action,
            },
            "idempotency": {
                "status": self.idempotency_status,
            },
            "auditEventId": self.audit_event_id,
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noInviteDeliveryConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class AccessProvisioningRequestResult:
    command_status: str
    account_id: str
    membership_id: str
    role_family: str
    permission_set: str
    seat_type: str
    seat_assignment_status: str
    seat_ref: str | None
    auth_claim_status: str
    provisioning_next_action: str
    idempotency_status: str
    audit_event_id: str | None
    guardrails: tuple[str, ...] = ACCESS_PROVISIONING_GUARDRAILS
    redactions: tuple[str, ...] = ACCESS_PROVISIONING_REDACTIONS

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "membership": {
                "membershipRef": self.membership_id,
                "roleFamily": self.role_family,
                "permissionSet": self.permission_set,
            },
            "seat": {
                "seatType": self.seat_type,
                "seatAssignmentStatus": self.seat_assignment_status,
                "seatRef": self.seat_ref,
            },
            "authClaims": {
                "authClaimStatus": self.auth_claim_status,
            },
            "provisioning": {
                "status": self.command_status,
                "nextAction": self.provisioning_next_action,
            },
            "idempotency": {
                "status": self.idempotency_status,
            },
            "auditEventId": self.audit_event_id,
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noInviteDeliveryConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noGoLiveChangeConfirmed": True,
            "noMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class LoginCompletionReadiness:
    login_completion_status: str
    account_id: str
    membership_id: str
    subject: str | None
    display_name: str | None
    role_family: str
    permission_profile: str | None
    membership_status: str
    seat_assignment_status: str
    identity_provider_status: str
    auth_claim_status: str
    blockers: tuple[str, ...]
    next_actions: tuple[str, ...]
    guardrails: tuple[str, ...] = LOGIN_COMPLETION_GUARDRAILS
    redactions: tuple[str, ...] = LOGIN_COMPLETION_REDACTIONS

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "loginCompletionStatus": self.login_completion_status,
            "accountRef": self.account_id,
            "membershipRef": self.membership_id,
            "person": {
                "subject": self.subject,
                "displayName": self.display_name,
                "responsibilities": [self.role_family],
            },
            "seat": {
                "seatAssignmentStatus": self.seat_assignment_status,
            },
            "identity": {
                "identityProviderStatus": self.identity_provider_status,
                "authClaimStatus": self.auth_claim_status,
                "permissionProfile": self.permission_profile,
            },
            "blockers": list(self.blockers),
            "nextActions": list(self.next_actions),
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noInviteDeliveryConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noGoLiveChangeConfirmed": True,
            "noMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class IdentityLoginReconciliationPerson:
    membership_id: str
    subject: str | None
    display_name: str | None
    role_family: str
    permission_profile: str | None
    access_status: str
    login_status: str
    seat_assignment_status: str
    identity_provider_status: str
    auth_claim_status: str
    revocation_status: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    next_action: str
    steps: tuple[dict[str, str], ...]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "membershipRef": self.membership_id,
            "person": {
                "subject": self.subject,
                "displayName": self.display_name,
                "responsibilities": [self.role_family],
            },
            "permissionProfile": self.permission_profile,
            "accessStatus": self.access_status,
            "loginStatus": self.login_status,
            "seatAssignmentStatus": self.seat_assignment_status,
            "identityProviderStatus": self.identity_provider_status,
            "authClaimStatus": self.auth_claim_status,
            "revocationStatus": self.revocation_status,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "nextAction": self.next_action,
            "steps": list(self.steps),
        }


@dataclass(frozen=True)
class IdentityLoginReconciliation:
    account_id: str
    reconciliation_status: str
    people: tuple[IdentityLoginReconciliationPerson, ...]
    accepted_count: int
    named_count: int
    seat_assigned_count: int
    provider_evidence_count: int
    auth_claim_ready_count: int
    revoked_count: int
    action_required_count: int
    claim_mismatch_count: int
    stale_provider_evidence_count: int
    guardrails: tuple[str, ...] = IDENTITY_LOGIN_RECONCILIATION_GUARDRAILS
    redactions: tuple[str, ...] = IDENTITY_LOGIN_RECONCILIATION_REDACTIONS

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "accountRef": self.account_id,
            "reconciliationStatus": self.reconciliation_status,
            "summary": {
                "acceptedCount": self.accepted_count,
                "namedCount": self.named_count,
                "seatAssignedCount": self.seat_assigned_count,
                "providerEvidenceCount": self.provider_evidence_count,
                "authClaimReadyCount": self.auth_claim_ready_count,
                "revokedCount": self.revoked_count,
                "actionRequiredCount": self.action_required_count,
                "claimMismatchCount": self.claim_mismatch_count,
                "staleProviderEvidenceCount": self.stale_provider_evidence_count,
            },
            "people": [person.to_safe_dict() for person in self.people],
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noInviteDeliveryConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noGoLiveChangeConfirmed": True,
            "noMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class LoginCompletionIntentResult:
    command_status: str
    account_id: str
    membership_id: str
    role_family: str
    permission_profile: str
    intent: str
    seat_assignment_status: str
    identity_provider_status: str
    auth_claim_status: str
    login_next_action: str
    idempotency_status: str
    audit_event_id: str | None
    guardrails: tuple[str, ...] = LOGIN_COMPLETION_GUARDRAILS
    redactions: tuple[str, ...] = LOGIN_COMPLETION_REDACTIONS

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "loginCompletionStatus": self.command_status,
            "membership": {
                "membershipRef": self.membership_id,
                "roleFamily": self.role_family,
                "permissionProfile": self.permission_profile,
            },
            "loginCompletion": {
                "intent": self.intent,
                "seatAssignmentStatus": self.seat_assignment_status,
                "identityProviderStatus": self.identity_provider_status,
                "authClaimStatus": self.auth_claim_status,
                "nextAction": self.login_next_action,
            },
            "idempotency": {
                "status": self.idempotency_status,
            },
            "auditEventId": self.audit_event_id,
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noInviteDeliveryConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noGoLiveChangeConfirmed": True,
            "noMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class MembershipInvitationDeliveryRequestResult:
    command_status: str
    account_id: str
    membership_id: str
    membership_status: str
    role_family: str
    permission_set: str
    delivery_status: str
    delivery_next_action: str
    recipient_contact_status: str
    provider_ref: str
    channel: str
    template_ref: str
    idempotency_status: str
    audit_event_id: str | None
    provider_delivery_ref: str | None = None
    provider_status: int | None = None
    guardrails: tuple[str, ...] = INVITATION_GUARDRAILS + (
        "NO_PROVIDER_SECRET_EXPOSURE",
    )
    redactions: tuple[str, ...] = INVITATION_REDACTIONS + (
        "recipient_hash",
        "provider_secret",
    )

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "membership": {
                "membershipRef": self.membership_id,
                "status": self.membership_status,
                "roleFamily": self.role_family,
                "permissionSet": self.permission_set,
            },
            "delivery": {
                "status": self.delivery_status,
                "nextAction": self.delivery_next_action,
                "recipientContactStatus": self.recipient_contact_status,
                "providerRef": self.provider_ref,
                "channel": self.channel,
                "templateRef": self.template_ref,
                "providerDeliveryRef": self.provider_delivery_ref,
                "providerStatus": self.provider_status,
            },
            "idempotency": {
                "status": self.idempotency_status,
            },
            "auditEventId": self.audit_event_id,
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noInviteDeliveryConfirmed": self.delivery_status
            not in {"INVITATION_DELIVERY_SENT", "INVITATION_DELIVERY_FAILED"},
            "noMembershipActivationConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class MembershipAcceptanceTokenIssueResult:
    command_status: str
    account_id: str
    membership_id: str
    role_family: str
    permission_set: str
    acceptance_token: str
    token_hint: str
    expires_at: str
    idempotency_status: str
    audit_event_id: str | None
    guardrails: tuple[str, ...] = INVITATION_GUARDRAILS + (
        "EXPIRING_ACCEPTANCE_TOKEN",
        "TOKEN_HASH_AT_REST",
        "NO_MEMBERSHIP_ACTIVATION",
        "NO_LOGIN_PROVISIONING",
    )
    redactions: tuple[str, ...] = INVITATION_REDACTIONS + (
        "acceptance_token",
        "acceptance_token_hash",
        "accepted_subject",
    )

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "membership": {
                "membershipRef": self.membership_id,
                "roleFamily": self.role_family,
                "permissionSet": self.permission_set,
            },
            "acceptanceToken": {
                "token": self.acceptance_token,
                "hint": self.token_hint,
                "expiresAt": self.expires_at,
                "status": self.command_status,
            },
            "idempotency": {"status": self.idempotency_status},
            "auditEventId": self.audit_event_id,
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noInviteDeliveryConfirmed": True,
            "noMembershipActivationConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class MembershipAcceptanceTokenValidationResult:
    token_status: str
    account_id: str | None
    membership_id: str | None
    role_family: str | None
    permission_set: str | None
    account_name: str | None
    display_name: str | None
    expires_at: str | None
    next_action: str
    guardrails: tuple[str, ...] = INVITATION_GUARDRAILS + (
        "TOKEN_HASH_LOOKUP_ONLY",
        "NO_MEMBERSHIP_ACTIVATION",
        "NO_LOGIN_PROVISIONING",
    )
    redactions: tuple[str, ...] = INVITATION_REDACTIONS + (
        "acceptance_token",
        "acceptance_token_hash",
        "accepted_subject",
    )

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "tokenStatus": self.token_status,
            "account": {
                "accountRef": self.account_id,
                "accountName": self.account_name,
            },
            "membership": {
                "membershipRef": self.membership_id,
                "roleFamily": self.role_family,
                "permissionSet": self.permission_set,
            },
            "person": {
                "displayName": self.display_name,
            },
            "expiresAt": self.expires_at,
            "nextAction": self.next_action,
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noMembershipActivationConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class MembershipAcceptanceTokenAcceptResult:
    command_status: str
    token_status: str
    account_id: str
    membership_id: str
    role_family: str
    permission_set: str
    activation_status: str
    idempotency_status: str
    audit_event_id: str | None
    guardrails: tuple[str, ...] = INVITATION_GUARDRAILS + (
        "EXPIRING_ACCEPTANCE_TOKEN",
        "TOKEN_REPLAY_PROTECTION",
        "NO_LOGIN_PROVISIONING",
    )
    redactions: tuple[str, ...] = INVITATION_REDACTIONS + (
        "acceptance_token",
        "acceptance_token_hash",
        "accepted_subject",
        "acceptance_evidence_ref",
    )

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "tokenStatus": self.token_status,
            "membership": {
                "membershipRef": self.membership_id,
                "roleFamily": self.role_family,
                "permissionSet": self.permission_set,
            },
            "activation": {
                "status": self.activation_status,
            },
            "idempotency": {"status": self.idempotency_status},
            "auditEventId": self.audit_event_id,
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noInviteDeliveryConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class MembershipRoleFamilySummary:
    role_family: str
    invited_count: int = 0
    active_count: int = 0
    suspended_count: int = 0
    disabled_count: int = 0
    archived_count: int = 0

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "roleFamily": self.role_family,
            "invitedCount": self.invited_count,
            "activeCount": self.active_count,
            "suspendedCount": self.suspended_count,
            "disabledCount": self.disabled_count,
            "archivedCount": self.archived_count,
        }


@dataclass(frozen=True)
class MembershipActorPosture:
    status: str
    role_family: str | None
    permission_set: str | None
    can_operate_setup: bool
    evidence: str

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "roleFamily": self.role_family,
            "permissionSet": self.permission_set,
            "canOperateSetup": self.can_operate_setup,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class MembershipPersonSummary:
    membership_id: str
    actor_type: str
    subject: str | None
    display_name: str | None
    role_family: str
    permission_set: str
    status: str
    delivery_status: str
    recipient_contact_status: str
    seat_assignment_status: str
    auth_claim_status: str

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "membershipRef": self.membership_id,
            "actorType": self.actor_type,
            "subject": self.subject,
            "displayName": self.display_name,
            "roleFamily": self.role_family,
            "permissionSet": self.permission_set,
            "status": self.status,
            "deliveryStatus": self.delivery_status,
            "recipientContactStatus": self.recipient_contact_status,
            "seatAssignmentStatus": self.seat_assignment_status,
            "authClaimStatus": self.auth_claim_status,
        }


@dataclass(frozen=True)
class ReferralSaasAccountMembershipPosture:
    account_id: str
    total_memberships: int
    invited_count: int
    active_count: int
    suspended_count: int
    disabled_count: int
    archived_count: int
    role_families: tuple[MembershipRoleFamilySummary, ...]
    memberships: tuple[MembershipPersonSummary, ...]
    current_actor: MembershipActorPosture
    guardrails: tuple[str, ...]
    redactions: tuple[str, ...]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "accountId": self.account_id,
            "totalMemberships": self.total_memberships,
            "invitedCount": self.invited_count,
            "activeCount": self.active_count,
            "suspendedCount": self.suspended_count,
            "disabledCount": self.disabled_count,
            "archivedCount": self.archived_count,
            "roleFamilies": [
                role_family.to_safe_dict() for role_family in self.role_families
            ],
            "memberships": [membership.to_safe_dict() for membership in self.memberships],
            "currentActor": self.current_actor.to_safe_dict(),
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noMembershipWriteConfirmed": True,
            "noInviteDeliveryConfirmed": True,
        }


@dataclass(frozen=True)
class MembershipActivationReadinessItem:
    membership_id: str
    subject: str | None
    display_name: str | None
    role_family: str
    membership_status: str
    delivery_status: str
    recipient_contact_status: str
    delivery_readiness: str
    activation_readiness: str
    provisioning_readiness: str
    seat_assignment_status: str
    auth_claim_status: str
    blockers: tuple[str, ...]
    next_action: str

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "membershipRef": self.membership_id,
            "subject": self.subject,
            "displayName": self.display_name,
            "roleFamily": self.role_family,
            "membershipStatus": self.membership_status,
            "deliveryStatus": self.delivery_status,
            "recipientContactStatus": self.recipient_contact_status,
            "deliveryReadiness": self.delivery_readiness,
            "activationReadiness": self.activation_readiness,
            "provisioningReadiness": self.provisioning_readiness,
            "seatAssignmentStatus": self.seat_assignment_status,
            "authClaimStatus": self.auth_claim_status,
            "blockers": list(self.blockers),
            "nextAction": self.next_action,
        }


@dataclass(frozen=True)
class MembershipActivationReadiness:
    account_id: str
    overall_status: str
    active_count: int
    invited_count: int
    delivery_ready_count: int
    activation_ready_count: int
    missing_role_families: tuple[str, ...]
    items: tuple[MembershipActivationReadinessItem, ...]
    guardrails: tuple[str, ...]
    redactions: tuple[str, ...]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "accountId": self.account_id,
            "overallStatus": self.overall_status,
            "activeCount": self.active_count,
            "invitedCount": self.invited_count,
            "deliveryReadyCount": self.delivery_ready_count,
            "activationReadyCount": self.activation_ready_count,
            "missingRoleFamilies": list(self.missing_role_families),
            "items": [item.to_safe_dict() for item in self.items],
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noInviteDeliveryConfirmed": True,
            "noMembershipActivationConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
        }


async def get_referral_saas_account_membership_posture(
    *,
    account_id: str,
    tenant_code: str,
    actor_ref: str | None = None,
    actor_client_id: str | None = None,
) -> ReferralSaasAccountMembershipPosture:
    safe_account_id = _required_text(account_id)
    safe_tenant_code = _required_text(tenant_code)
    safe_actor_ref = _optional_text(actor_ref)
    safe_actor_client_id = _optional_text(actor_client_id)

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                platform_memberships.membership_id,
                platform_memberships.role_family,
                platform_memberships.permission_set,
                platform_memberships.status,
                COALESCE(
                    platform_memberships.metadata->>'delivery_status',
                    'DELIVERY_NOT_CONFIGURED'
                ) AS delivery_status,
                CASE
                    WHEN platform_memberships.user_id IS NOT NULL THEN 'USER'
                    WHEN platform_memberships.client_id IS NOT NULL THEN 'CLIENT'
                    ELSE 'UNKNOWN'
                END AS actor_type,
                actor_user.subject AS user_subject,
                actor_user.display_name AS user_display_name,
                CASE
                    WHEN actor_user.email_hash IS NOT NULL
                         AND actor_user.email_hash <> ''
                    THEN 'CONTACT_REFERENCE_PRESENT'
                    WHEN platform_memberships.client_id IS NOT NULL
                    THEN 'CLIENT_CONTACT_REFERENCE_NOT_REQUIRED'
                    ELSE 'CONTACT_REFERENCE_MISSING'
                END AS recipient_contact_status,
                platform_memberships.client_id AS client_id,
                CASE
                    WHEN platform_memberships.metadata->>'access_provisioning_status' IS NOT NULL
                    THEN platform_memberships.metadata->>'access_provisioning_status'
                    WHEN platform_memberships.seat_id IS NOT NULL
                    THEN 'SEAT_ASSIGNED'
                    ELSE 'SEAT_NOT_ASSIGNED'
                END AS seat_assignment_status,
                COALESCE(
                    platform_memberships.metadata->>'auth_claim_status',
                    'AUTH_CLAIMS_NOT_PROPAGATED'
                ) AS auth_claim_status,
                CASE
                    WHEN $3::text <> '' AND platform_memberships.client_id = $3 THEN TRUE
                    WHEN $4::text <> '' AND platform_memberships.user_id::text = $4 THEN TRUE
                    ELSE FALSE
                END AS is_current_actor
            FROM platform_memberships
            LEFT JOIN platform_users actor_user
                ON actor_user.user_id = platform_memberships.user_id
            WHERE platform_memberships.account_id = $1
              AND (platform_memberships.tenant_code = $2 OR platform_memberships.tenant_code IS NULL)
              AND platform_memberships.status <> 'ARCHIVED'
            ORDER BY
                CASE platform_memberships.status
                    WHEN 'ACTIVE' THEN 0
                    WHEN 'INVITED' THEN 1
                    WHEN 'SUSPENDED' THEN 2
                    WHEN 'DISABLED' THEN 3
                    ELSE 4
                END,
                platform_memberships.updated_at DESC
            """,
            safe_account_id,
            safe_tenant_code,
            safe_actor_client_id,
            safe_actor_ref,
        )

    safe_rows = [dict(row) for row in rows]
    counts = _status_counts(safe_rows)
    role_families = _role_family_summaries(safe_rows)
    memberships = _membership_person_summaries(safe_rows)
    current_actor = _current_actor_posture(safe_rows)

    return ReferralSaasAccountMembershipPosture(
        account_id=safe_account_id,
        total_memberships=len(safe_rows),
        invited_count=counts["INVITED"],
        active_count=counts["ACTIVE"],
        suspended_count=counts["SUSPENDED"],
        disabled_count=counts["DISABLED"],
        archived_count=counts["ARCHIVED"],
        role_families=tuple(role_families),
        memberships=tuple(memberships),
        current_actor=current_actor,
        guardrails=(
            "READ_ONLY_MEMBERSHIP_POSTURE",
            "NO_MEMBERSHIP_WRITE",
            "NO_INVITE_DELIVERY",
            "NO_USER_CREATION",
            "NO_SEAT_ASSIGNMENT",
            "NO_AUTH_CLAIM_CHANGE",
            "NO_TENANT_CODE_EXPOSURE",
        ),
        redactions=(
            "internal_tenant_identifier",
            "user_identifier",
            "client_identifier",
            "email_hash",
        ),
    )


async def get_referral_saas_membership_activation_readiness(
    *,
    account_id: str,
    tenant_code: str,
    account_status: str,
    tenant_link_status: str | None,
    external_reference_status: str | None,
) -> MembershipActivationReadiness:
    posture = await get_referral_saas_account_membership_posture(
        account_id=account_id,
        tenant_code=tenant_code,
    )
    return build_membership_activation_readiness(
        posture=posture,
        account_status=account_status,
        tenant_link_status=tenant_link_status,
        external_reference_status=external_reference_status,
    )


def build_membership_activation_readiness(
    *,
    posture: ReferralSaasAccountMembershipPosture,
    account_status: str,
    tenant_link_status: str | None,
    external_reference_status: str | None,
) -> MembershipActivationReadiness:
    safe_account_status = _optional_text(account_status).upper()
    safe_tenant_link_status = _optional_text(tenant_link_status).upper()
    safe_external_reference_status = _optional_text(external_reference_status).upper()

    items = tuple(
        _activation_readiness_item(
            membership=membership,
            account_status=safe_account_status,
            tenant_link_status=safe_tenant_link_status,
            external_reference_status=safe_external_reference_status,
        )
        for membership in posture.memberships
    )
    missing_role_families = _missing_required_role_families(posture.memberships)
    delivery_ready_count = sum(
        1 for item in items if item.delivery_readiness == "READY_TO_REQUEST_DELIVERY"
    )
    activation_ready_count = sum(
        1 for item in items if item.activation_readiness == "READY_TO_ACTIVATE"
    )

    if posture.active_count > 0 and not missing_role_families:
        overall_status = "ACCESS_READY"
    elif items or missing_role_families:
        overall_status = "ACTION_REQUIRED"
    else:
        overall_status = "NO_ACCESS_INTENT"

    return MembershipActivationReadiness(
        account_id=posture.account_id,
        overall_status=overall_status,
        active_count=posture.active_count,
        invited_count=posture.invited_count,
        delivery_ready_count=delivery_ready_count,
        activation_ready_count=activation_ready_count,
        missing_role_families=missing_role_families,
        items=items,
        guardrails=(
            "READ_ONLY_ACTIVATION_READINESS",
            "NO_INVITE_DELIVERY",
            "NO_MEMBERSHIP_ACTIVATION",
            "NO_SEAT_ASSIGNMENT",
            "NO_AUTH_CLAIM_CHANGE",
            "NO_TENANT_CODE_EXPOSURE",
            "NO_MONEY_MOVEMENT",
        ),
        redactions=(
            "internal_tenant_identifier",
            "user_identifier",
            "client_identifier",
            "email_hash",
            "recipient_hash",
        ),
    )


async def record_referral_saas_membership_invitation_intent(
    *,
    account_id: str,
    tenant_code: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    actor_type: str,
    subject: str | None = None,
    client_id: str | None = None,
    email_hash: str | None = None,
    display_name: str | None = None,
    role_family: str,
    permission_set: str,
    tenant_scope: str,
    reason_code: str,
    correlation_id: str,
    idempotency_key_hash: str,
    command_payload_hash: str,
    command_payload: dict[str, Any] | None = None,
    command_actor_ref: str | None = None,
    command_actor_role: str | None = None,
) -> MembershipInvitationIntentResult:
    safe_account_id = _required_account_id(account_id)
    safe_tenant_code = _required_text(tenant_code)
    safe_account_tenant_id = _optional_text(account_tenant_id) or None
    safe_external_ref_id = _optional_text(external_ref_id) or None
    safe_actor_type = _required_choice(actor_type, {USER_ACTOR, CLIENT_ACTOR})
    safe_subject = _optional_text(subject) or None
    safe_client_id = _optional_text(client_id) or None
    safe_email_hash = _optional_text(email_hash) or None
    safe_display_name = _optional_text(display_name) or None
    safe_role_family = _required_choice(role_family, ROLE_FAMILIES)
    safe_permission_set = _required_text(permission_set).upper()
    safe_tenant_scope = _required_choice(tenant_scope, {PRIMARY_TENANT_SCOPE})
    safe_reason_code = _required_text(reason_code).upper()
    safe_correlation_id = _required_text(correlation_id)
    safe_idempotency_hash = _required_text(idempotency_key_hash)
    safe_payload_hash = _required_text(command_payload_hash)
    safe_command_payload = command_payload or {}

    _reject_unsafe_payload(safe_command_payload)

    if safe_actor_type == USER_ACTOR and not safe_subject:
        raise MembershipInvitationValidationError("User subject is required.")
    if safe_actor_type == CLIENT_ACTOR and not safe_client_id:
        raise MembershipInvitationValidationError("Client identifier is required.")
    if safe_actor_type == USER_ACTOR and safe_client_id:
        raise MembershipInvitationValidationError(
            "User invitation intent must not include client identifiers."
        )
    if safe_actor_type == CLIENT_ACTOR and safe_subject:
        raise MembershipInvitationValidationError(
            "Client invitation intent must not include user subjects."
        )
    if not safe_account_tenant_id:
        raise MembershipInvitationAccountNotReady(
            "Account tenant link is required before membership invitation intent."
        )

    effective_tenant_code = (
        safe_tenant_code if safe_tenant_scope == PRIMARY_TENANT_SCOPE else None
    )
    actor_ref = safe_subject if safe_actor_type == USER_ACTOR else safe_client_id

    async with db_connection() as conn:
        existing_audit = await conn.fetchrow(
            """
            SELECT
                account_audit_event_id,
                event_status,
                membership_id,
                evidence_summary
            FROM platform_account_audit_events
            WHERE account_id = $1
              AND event_type = $2
              AND idempotency_key_hash = $3
            ORDER BY created_at DESC
            LIMIT 1
            """,
            safe_account_id,
            MEMBERSHIP_INVITATION_EVENT,
            safe_idempotency_hash,
        )
        if existing_audit:
            evidence = _as_mapping(existing_audit.get("evidence_summary"))
            if _optional_text(evidence.get("command_payload_hash")) != safe_payload_hash:
                raise MembershipInvitationIdempotencyConflict(
                    "Idempotency key was reused with different membership invitation content."
                )
            return MembershipInvitationIntentResult(
                command_status="INVITATION_INTENT_REPLAYED",
                account_id=safe_account_id,
                membership_id=_optional_text(evidence.get("membership_id"))
                or _optional_text(existing_audit.get("membership_id")),
                membership_status="INVITED",
                role_family=_optional_text(evidence.get("role_family"))
                or safe_role_family,
                permission_set=_optional_text(evidence.get("permission_set"))
                or safe_permission_set,
                can_operate_setup=False,
                delivery_status="DELIVERY_NOT_CONFIGURED",
                delivery_next_action="Configure approved invitation delivery provider",
                idempotency_status="REPLAYED",
                audit_event_id=_optional_text(
                    existing_audit.get("account_audit_event_id")
                )
                or None,
            )

        duplicate_membership = await conn.fetchrow(
            """
            SELECT membership.membership_id, membership.status
            FROM platform_memberships membership
            LEFT JOIN platform_users actor_user
                ON actor_user.user_id = membership.user_id
            WHERE membership.account_id = $1
              AND COALESCE(membership.tenant_code, '') = COALESCE($2, '')
              AND membership.role_family = $3
              AND membership.status IN ('INVITED', 'ACTIVE', 'SUSPENDED')
              AND (
                    ($4::text <> '' AND actor_user.subject = $4)
                    OR ($5::text <> '' AND membership.client_id = $5)
              )
            LIMIT 1
            """,
            safe_account_id,
            effective_tenant_code,
            safe_role_family,
            safe_subject,
            safe_client_id or "",
        )
        if duplicate_membership:
            raise MembershipInvitationDuplicate(
                "A usable membership already exists for this actor, account, tenant scope, and role."
            )

        async with conn.transaction():
            user_id = None
            if safe_actor_type == USER_ACTOR:
                user = await conn.fetchrow(
                    """
                    INSERT INTO platform_users (
                        subject,
                        email_hash,
                        display_name,
                        status,
                        metadata
                    )
                    VALUES ($1, $2, $3, 'INVITED', $4::jsonb)
                    ON CONFLICT (subject)
                    DO UPDATE SET
                        email_hash = COALESCE(platform_users.email_hash, EXCLUDED.email_hash),
                        display_name = COALESCE(platform_users.display_name, EXCLUDED.display_name),
                        updated_at = NOW()
                    RETURNING user_id, status
                    """,
                    safe_subject,
                    safe_email_hash,
                    safe_display_name,
                    _jsonb(
                        {
                            "source": "REFERRAL_SAAS_ACCOUNT_SETUP",
                            "no_raw_email_storage_confirmed": True,
                        }
                    ),
                )
                user_id = user["user_id"]

            membership = await conn.fetchrow(
                """
                INSERT INTO platform_memberships (
                    account_id,
                    tenant_code,
                    user_id,
                    client_id,
                    role_family,
                    permission_set,
                    status,
                    invited_by_ref,
                    invited_at,
                    metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, 'INVITED', $7, NOW(), $8::jsonb)
                RETURNING membership_id, status, role_family, permission_set
                """,
                safe_account_id,
                effective_tenant_code,
                user_id,
                safe_client_id,
                safe_role_family,
                safe_permission_set,
                _optional_text(command_actor_ref) or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                _jsonb(
                    {
                        "source": "TASK-211",
                        "reason_code": safe_reason_code,
                        "tenant_scope": safe_tenant_scope,
                        "delivery_status": "DELIVERY_NOT_CONFIGURED",
                        "no_email_delivery_confirmed": True,
                        "no_auth_claim_change_confirmed": True,
                        "no_seat_assignment_confirmed": True,
                    }
                ),
            )
            membership_id = str(membership["membership_id"])
            audit_evidence = {
                "membership_id": membership_id,
                "actor_type": safe_actor_type,
                "role_family": safe_role_family,
                "permission_set": safe_permission_set,
                "tenant_scope": safe_tenant_scope,
                "command_payload_hash": safe_payload_hash,
                "no_raw_email_storage_confirmed": True,
                "no_email_delivery_confirmed": True,
                "no_auth_claim_change_confirmed": True,
                "no_seat_assignment_confirmed": True,
                "no_money_movement_confirmed": True,
            }
            audit_event = await conn.fetchrow(
                """
                INSERT INTO platform_account_audit_events (
                    account_id,
                    account_tenant_id,
                    external_ref_id,
                    membership_id,
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
                    $1, $2, $3, $4, $5, $6, $7, $8, $9,
                    NULL, 'INVITED', $10, $11, $12, $13::jsonb, $14::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                safe_account_tenant_id,
                safe_external_ref_id,
                membership_id,
                effective_tenant_code,
                MEMBERSHIP_INVITATION_EVENT,
                EVENT_RECORDED,
                _optional_text(command_actor_ref)
                or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                _optional_text(command_actor_role) or "UNKNOWN",
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(audit_evidence),
                _jsonb(list(INVITATION_REDACTIONS)),
            )

    return MembershipInvitationIntentResult(
        command_status="INVITATION_INTENT_RECORDED",
        account_id=safe_account_id,
        membership_id=membership_id,
        membership_status=str(membership["status"]),
        role_family=str(membership["role_family"]),
        permission_set=str(membership["permission_set"]),
        can_operate_setup=False,
        delivery_status="DELIVERY_NOT_CONFIGURED",
        delivery_next_action="Configure approved invitation delivery provider",
        idempotency_status=EVENT_RECORDED,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
    )


async def request_referral_saas_membership_invitation_delivery(
    *,
    account_id: str,
    tenant_code: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    membership_id: str,
    provider_ref: str,
    channel: str,
    template_ref: str,
    recipient_hash: str | None = None,
    reason_code: str,
    correlation_id: str,
    idempotency_key_hash: str,
    command_payload_hash: str,
    command_payload: dict[str, Any] | None = None,
    command_actor_ref: str | None = None,
    command_actor_role: str | None = None,
) -> MembershipInvitationDeliveryRequestResult:
    safe_account_id = _required_account_id(account_id)
    safe_tenant_code = _required_text(tenant_code)
    safe_account_tenant_id = _optional_text(account_tenant_id) or None
    safe_external_ref_id = _optional_text(external_ref_id) or None
    safe_membership_id = _required_text(membership_id)
    safe_provider_ref = _required_text(provider_ref)
    safe_channel = _required_choice(channel, {"EMAIL"})
    safe_template_ref = _required_text(template_ref)
    safe_recipient_hash = _optional_text(recipient_hash)
    safe_reason_code = _required_text(reason_code).upper()
    safe_correlation_id = _required_text(correlation_id)
    safe_idempotency_hash = _required_text(idempotency_key_hash)
    safe_payload_hash = _required_text(command_payload_hash)
    safe_command_payload = command_payload or {}

    _reject_unsafe_delivery_payload(safe_command_payload)

    async with db_connection() as conn:
        existing_audit = await conn.fetchrow(
            """
            SELECT
                account_audit_event_id,
                membership_id,
                next_status,
                evidence_summary
            FROM platform_account_audit_events
            WHERE account_id = $1
              AND event_type = $2
              AND idempotency_key_hash = $3
            ORDER BY created_at DESC
            LIMIT 1
            """,
            safe_account_id,
            MEMBERSHIP_INVITATION_DELIVERY_EVENT,
            safe_idempotency_hash,
        )
        if existing_audit:
            evidence = _as_mapping(existing_audit.get("evidence_summary"))
            if _optional_text(evidence.get("command_payload_hash")) != safe_payload_hash:
                raise MembershipInvitationIdempotencyConflict(
                    "Idempotency key was reused with different invitation delivery content."
                )
            replayed_delivery_status = (
                _optional_text(evidence.get("delivery_status"))
                or _optional_text(existing_audit.get("next_status"))
                or "DELIVERY_PROVIDER_NOT_CONFIGURED"
            )
            return MembershipInvitationDeliveryRequestResult(
                command_status=replayed_delivery_status,
                account_id=safe_account_id,
                membership_id=_optional_text(evidence.get("membership_id"))
                or safe_membership_id,
                membership_status=_optional_text(evidence.get("membership_status"))
                or "INVITED",
                role_family=_optional_text(evidence.get("role_family")) or "UNKNOWN",
                permission_set=_optional_text(evidence.get("permission_set"))
                or "UNKNOWN",
                delivery_status=replayed_delivery_status,
                delivery_next_action=(
                    _optional_text(evidence.get("delivery_next_action"))
                    or "Configure approved invitation delivery provider before sending email invites."
                ),
                recipient_contact_status=_optional_text(
                    evidence.get("recipient_contact_status")
                )
                or "CONTACT_REFERENCE_PRESENT",
                provider_ref=_optional_text(evidence.get("provider_ref"))
                or safe_provider_ref,
                channel=_optional_text(evidence.get("channel")) or safe_channel,
                template_ref=_optional_text(evidence.get("template_ref"))
                or safe_template_ref,
                idempotency_status="REPLAYED",
                audit_event_id=_optional_text(
                    existing_audit.get("account_audit_event_id")
                )
                or None,
                provider_delivery_ref=_optional_text(
                    evidence.get("provider_delivery_ref")
                )
                or None,
                provider_status=(
                    int(evidence["provider_status"])
                    if evidence.get("provider_status") is not None
                    else None
                ),
            )

        membership = await conn.fetchrow(
            """
            SELECT
                membership_id,
                status,
                role_family,
                permission_set,
                COALESCE(platform_memberships.metadata->>'delivery_status', 'DELIVERY_NOT_CONFIGURED')
                    AS delivery_status,
                CASE
                    WHEN actor_user.email_hash IS NOT NULL
                         AND actor_user.email_hash <> ''
                    THEN 'CONTACT_REFERENCE_PRESENT'
                    WHEN platform_memberships.client_id IS NOT NULL
                    THEN 'CLIENT_CONTACT_REFERENCE_NOT_REQUIRED'
                    ELSE 'CONTACT_REFERENCE_MISSING'
                END AS recipient_contact_status,
                actor_user.subject AS recipient_subject
            FROM platform_memberships
            LEFT JOIN platform_users actor_user
                ON actor_user.user_id = platform_memberships.user_id
            WHERE platform_memberships.membership_id = $1
              AND platform_memberships.account_id = $2
              AND (platform_memberships.tenant_code = $3 OR platform_memberships.tenant_code IS NULL)
              AND platform_memberships.status <> 'ARCHIVED'
            LIMIT 1
            """,
            safe_membership_id,
            safe_account_id,
            safe_tenant_code,
        )
        if not membership:
            raise MembershipInvitationUnsafeScope(
                "Membership reference does not match the resolved account context."
            )

        membership_status = _normalise_status(membership.get("status"))
        if membership_status != "INVITED":
            raise MembershipInvitationDeliveryNotInvited(
                "Invitation delivery can only be requested for invited memberships."
            )

        recipient_contact_status = (
            _optional_text(membership.get("recipient_contact_status"))
            or "CONTACT_REFERENCE_MISSING"
        )
        recipient_hash_present = bool(safe_recipient_hash) or recipient_contact_status in {
            "CONTACT_REFERENCE_PRESENT",
            "CLIENT_CONTACT_REFERENCE_NOT_REQUIRED",
        }
        if recipient_contact_status == "CONTACT_REFERENCE_MISSING" and not safe_recipient_hash:
            delivery_command_status = "DELIVERY_RECIPIENT_CONTACT_MISSING"
            delivery_next_action = (
                "Add a safe work email contact reference before invite delivery can be requested."
            )
        else:
            provider_gate = _approved_invitation_delivery_provider(
                channel=safe_channel,
                provider_ref=safe_provider_ref,
            )
            if not provider_gate["ready"]:
                delivery_command_status = "DELIVERY_PROVIDER_NOT_CONFIGURED"
                delivery_next_action = provider_gate["next_action"]
            else:
                recipient = _optional_text(membership.get("recipient_subject"))
                if not recipient:
                    delivery_command_status = "DELIVERY_RECIPIENT_CONTACT_MISSING"
                    delivery_next_action = (
                        "Add a safe work email contact reference before invite delivery can be requested."
                    )
                else:
                    try:
                        provider_result = await dispatch_channel_message(
                            channel_code=safe_channel,
                            tenant_code=safe_tenant_code,
                            recipient=recipient,
                            message=_membership_invitation_message(
                                template_ref=safe_template_ref,
                                role_family=_optional_text(
                                    membership.get("role_family")
                                )
                                or "UNKNOWN",
                            ),
                            context={
                                "event_type": "MEMBERSHIP_INVITATION",
                                "consent_verified": True,
                                "account_id": safe_account_id,
                                "membership_id": safe_membership_id,
                                "provider_ref": safe_provider_ref,
                                "template_ref": safe_template_ref,
                                "no_membership_activation_confirmed": True,
                                "no_auth_claim_change_confirmed": True,
                                "no_seat_assignment_confirmed": True,
                                "no_money_movement_confirmed": True,
                            },
                        )
                    except HTTPException as exc:
                        provider_result = {
                            "status": "FAILED",
                            "delivery_id": None,
                            "provider_status": exc.status_code,
                            "provider_response": str(exc.detail),
                        }
                    dispatch_status = str(provider_result.get("status") or "").upper()
                    provider_status = (
                        int(provider_result["provider_status"])
                        if provider_result.get("provider_status") is not None
                        else None
                    )
                    provider_delivery_ref = _optional_text(
                        provider_result.get("delivery_id")
                    )
                    if dispatch_status == "SENT":
                        delivery_command_status = "INVITATION_DELIVERY_SENT"
                        delivery_next_action = (
                            "Invite email was sent by the approved provider. Wait for the recipient acceptance path before activating access."
                        )
                    else:
                        delivery_command_status = "INVITATION_DELIVERY_FAILED"
                        delivery_next_action = (
                            "Provider delivery failed or was dead-lettered. Review the provider status and retry with the same safe delivery command."
                        )

        audit_evidence = {
            "membership_id": safe_membership_id,
            "membership_status": membership_status,
            "role_family": _optional_text(membership.get("role_family")),
            "permission_set": _optional_text(membership.get("permission_set")),
            "provider_ref": safe_provider_ref,
            "channel": safe_channel,
            "template_ref": safe_template_ref,
            "delivery_status": delivery_command_status,
            "recipient_contact_status": recipient_contact_status,
            "recipient_hash_present": recipient_hash_present,
            "command_payload_hash": safe_payload_hash,
            "provider_configured": delivery_command_status
            in {"INVITATION_DELIVERY_SENT", "INVITATION_DELIVERY_FAILED"},
            "provider_delivery_ref": locals().get("provider_delivery_ref"),
            "provider_status": locals().get("provider_status"),
            "no_email_delivery_confirmed": delivery_command_status
            not in {"INVITATION_DELIVERY_SENT", "INVITATION_DELIVERY_FAILED"},
            "no_membership_activation_confirmed": True,
            "no_auth_claim_change_confirmed": True,
            "no_seat_assignment_confirmed": True,
            "no_money_movement_confirmed": True,
        }
        async with conn.transaction():
            if delivery_command_status in {
                "INVITATION_DELIVERY_SENT",
                "INVITATION_DELIVERY_FAILED",
            }:
                await conn.fetchrow(
                    """
                    UPDATE platform_memberships
                    SET
                        metadata = COALESCE(metadata, '{}'::jsonb) || $4::jsonb,
                        updated_at = NOW()
                    WHERE membership_id = $1
                      AND account_id = $2
                      AND (tenant_code = $3 OR tenant_code IS NULL)
                    RETURNING membership_id
                    """,
                    safe_membership_id,
                    safe_account_id,
                    safe_tenant_code,
                    _jsonb(
                        {
                            "delivery_status": delivery_command_status,
                            "delivery_channel": safe_channel,
                            "delivery_provider_ref": safe_provider_ref,
                            "delivery_template_ref": safe_template_ref,
                            "provider_delivery_ref": locals().get(
                                "provider_delivery_ref"
                            ),
                            "provider_status": locals().get("provider_status"),
                            "no_membership_activation_confirmed": True,
                            "no_auth_claim_change_confirmed": True,
                            "no_seat_assignment_confirmed": True,
                            "no_money_movement_confirmed": True,
                        }
                    ),
                )

            audit_event = await conn.fetchrow(
                """
                INSERT INTO platform_account_audit_events (
                    account_id,
                    account_tenant_id,
                    external_ref_id,
                    membership_id,
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
                    $1, $2, $3, $4, $5, $6, $7, $8, $9,
                    $10, $11, $12, $13, $14,
                    $15::jsonb, $16::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                safe_account_tenant_id,
                safe_external_ref_id,
                safe_membership_id,
                safe_tenant_code,
                MEMBERSHIP_INVITATION_DELIVERY_EVENT,
                (
                    "RECORDED"
                    if delivery_command_status == "INVITATION_DELIVERY_SENT"
                    else "FAILED"
                    if delivery_command_status == "INVITATION_DELIVERY_FAILED"
                    else "BLOCKED"
                ),
                _optional_text(command_actor_ref)
                or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                _optional_text(command_actor_role) or "UNKNOWN",
                _optional_text(membership.get("delivery_status"))
                or "DELIVERY_NOT_CONFIGURED",
                delivery_command_status,
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(audit_evidence),
                _jsonb(
                    list(
                        INVITATION_REDACTIONS
                        + ("recipient_hash", "provider_secret")
                    )
                ),
            )

    return MembershipInvitationDeliveryRequestResult(
        command_status=delivery_command_status,
        account_id=safe_account_id,
        membership_id=safe_membership_id,
        membership_status=membership_status,
        role_family=_optional_text(membership.get("role_family")) or "UNKNOWN",
        permission_set=_optional_text(membership.get("permission_set")) or "UNKNOWN",
        delivery_status=delivery_command_status,
        delivery_next_action=delivery_next_action,
        recipient_contact_status=recipient_contact_status,
        provider_ref=safe_provider_ref,
        channel=safe_channel,
        template_ref=safe_template_ref,
        idempotency_status=EVENT_RECORDED,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
        provider_delivery_ref=locals().get("provider_delivery_ref"),
        provider_status=locals().get("provider_status"),
    )


async def issue_referral_saas_membership_acceptance_token(
    *,
    account_id: str,
    tenant_code: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    membership_id: str,
    accepted_subject: str,
    ttl_hours: int | None = None,
    reason_code: str,
    correlation_id: str,
    idempotency_key_hash: str,
    command_payload_hash: str,
    command_payload: dict[str, Any] | None = None,
    command_actor_ref: str | None = None,
    command_actor_role: str | None = None,
) -> MembershipAcceptanceTokenIssueResult:
    safe_account_id = _required_account_id(account_id)
    safe_tenant_code = _required_text(tenant_code)
    safe_account_tenant_id = _optional_text(account_tenant_id) or None
    safe_external_ref_id = _optional_text(external_ref_id) or None
    safe_membership_id = _required_text(membership_id)
    safe_accepted_subject = _required_text(accepted_subject)
    safe_reason_code = _required_text(reason_code).upper()
    safe_correlation_id = _required_text(correlation_id)
    safe_idempotency_hash = _required_text(idempotency_key_hash)
    safe_payload_hash = _required_text(command_payload_hash)
    safe_command_payload = command_payload or {}
    safe_ttl_hours = int(ttl_hours or MEMBERSHIP_INVITATION_ACCEPTANCE_TOKEN_TTL_HOURS)
    if safe_ttl_hours < 1 or safe_ttl_hours > 168:
        raise MembershipInvitationValidationError(
            "Acceptance token TTL must be between 1 and 168 hours."
        )
    _reject_unsafe_activation_payload(safe_command_payload)

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
            MEMBERSHIP_INVITATION_ACCEPTANCE_TOKEN_EVENT,
            safe_idempotency_hash,
        )
        if existing_audit:
            evidence = _as_mapping(existing_audit.get("evidence_summary"))
            if _optional_text(evidence.get("command_payload_hash")) != safe_payload_hash:
                raise MembershipInvitationIdempotencyConflict(
                    "Idempotency key was reused with different acceptance-token content."
                )
            return MembershipAcceptanceTokenIssueResult(
                command_status="ACCEPTANCE_TOKEN_REPLAYED",
                account_id=safe_account_id,
                membership_id=_optional_text(evidence.get("membership_id"))
                or safe_membership_id,
                role_family=_optional_text(evidence.get("role_family")) or "UNKNOWN",
                permission_set=_optional_text(evidence.get("permission_set"))
                or "UNKNOWN",
                acceptance_token="",
                token_hint=_optional_text(evidence.get("token_hint")) or "",
                expires_at=_optional_text(evidence.get("expires_at")) or "",
                idempotency_status="REPLAYED",
                audit_event_id=_optional_text(existing_audit.get("account_audit_event_id"))
                or None,
            )

        membership = await conn.fetchrow(
            """
            SELECT
                platform_memberships.membership_id,
                platform_memberships.status,
                platform_memberships.role_family,
                platform_memberships.permission_set,
                COALESCE(platform_memberships.metadata->>'delivery_status', 'DELIVERY_NOT_CONFIGURED')
                    AS delivery_status,
                actor_user.subject AS user_subject,
                platform_memberships.client_id
            FROM platform_memberships
            LEFT JOIN platform_users actor_user
                ON actor_user.user_id = platform_memberships.user_id
            WHERE platform_memberships.membership_id = $1
              AND platform_memberships.account_id = $2
              AND (platform_memberships.tenant_code = $3 OR platform_memberships.tenant_code IS NULL)
              AND platform_memberships.status <> 'ARCHIVED'
            LIMIT 1
            """,
            safe_membership_id,
            safe_account_id,
            safe_tenant_code,
        )
        if not membership:
            raise MembershipInvitationUnsafeScope(
                "Membership reference does not match the resolved account context."
            )
        if _normalise_status(membership.get("status")) != "INVITED":
            raise MembershipInvitationDeliveryNotInvited(
                "Acceptance tokens can only be issued for invited memberships."
            )
        invited_subject = _optional_text(membership.get("user_subject")) or _optional_text(
            membership.get("client_id")
        )
        if safe_accepted_subject != invited_subject:
            raise MembershipInvitationValidationError(
                "Acceptance subject must match the invited person or client reference."
            )
        delivery_status = _optional_text(membership.get("delivery_status")) or ""
        if delivery_status != "INVITATION_DELIVERY_SENT":
            raise MembershipInvitationDeliveryNotInvited(
                "Issue an acceptance link only after the invite delivery path is sent."
            )

        acceptance_token = secrets.token_urlsafe(32)
        token_hash = _hash_acceptance_token(acceptance_token)
        token_hint = acceptance_token[-6:]
        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=safe_ttl_hours)
        audit_evidence = {
            "membership_id": safe_membership_id,
            "role_family": _optional_text(membership.get("role_family")),
            "permission_set": _optional_text(membership.get("permission_set")),
            "token_hint": token_hint,
            "expires_at": expires_at.isoformat(),
            "command_payload_hash": safe_payload_hash,
            "token_hash_stored_confirmed": True,
            "no_raw_token_storage_confirmed": True,
            "no_membership_activation_confirmed": True,
            "no_invite_delivery_confirmed": True,
            "no_auth_claim_change_confirmed": True,
            "no_seat_assignment_confirmed": True,
            "no_money_movement_confirmed": True,
        }
        async with conn.transaction():
            token_row = await conn.fetchrow(
                """
                INSERT INTO referral_saas_membership_acceptance_tokens (
                    account_id,
                    membership_id,
                    tenant_code,
                    token_hash,
                    token_hint,
                    accepted_subject_ref,
                    status,
                    expires_at,
                    metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, 'ISSUED', $7, $8::jsonb)
                RETURNING acceptance_token_id
                """,
                safe_account_id,
                safe_membership_id,
                safe_tenant_code,
                token_hash,
                token_hint,
                safe_accepted_subject,
                expires_at,
                _jsonb(
                    {
                        "source": "TASK-364",
                        "no_raw_token_storage_confirmed": True,
                        "no_membership_activation_confirmed": True,
                    }
                ),
            )
            await conn.fetchrow(
                """
                UPDATE platform_memberships
                SET
                    metadata = COALESCE(metadata, '{}'::jsonb) || $4::jsonb,
                    updated_at = NOW()
                WHERE membership_id = $1
                  AND account_id = $2
                  AND (tenant_code = $3 OR tenant_code IS NULL)
                RETURNING membership_id
                """,
                safe_membership_id,
                safe_account_id,
                safe_tenant_code,
                _jsonb(
                    {
                        "acceptance_token_status": "ISSUED",
                        "acceptance_token_hint": token_hint,
                        "acceptance_token_expires_at": expires_at.isoformat(),
                    }
                ),
            )
            audit_event = await conn.fetchrow(
                """
                INSERT INTO platform_account_audit_events (
                    account_id,
                    account_tenant_id,
                    external_ref_id,
                    membership_id,
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
                    $1, $2, $3, $4, $5, $6, 'RECORDED', $7, $8,
                    NULL, 'ACCEPTANCE_TOKEN_ISSUED', $9, $10, $11,
                    $12::jsonb, $13::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                safe_account_tenant_id,
                safe_external_ref_id,
                safe_membership_id,
                safe_tenant_code,
                MEMBERSHIP_INVITATION_ACCEPTANCE_TOKEN_EVENT,
                _optional_text(command_actor_ref) or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                _optional_text(command_actor_role) or "UNKNOWN",
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(audit_evidence),
                _jsonb(
                    list(
                        INVITATION_REDACTIONS
                        + ("acceptance_token", "acceptance_token_hash", "accepted_subject")
                    )
                ),
            )

    return MembershipAcceptanceTokenIssueResult(
        command_status="ACCEPTANCE_TOKEN_ISSUED",
        account_id=safe_account_id,
        membership_id=safe_membership_id,
        role_family=_optional_text(membership.get("role_family")) or "UNKNOWN",
        permission_set=_optional_text(membership.get("permission_set")) or "UNKNOWN",
        acceptance_token=acceptance_token,
        token_hint=token_hint,
        expires_at=expires_at.isoformat(),
        idempotency_status=EVENT_RECORDED,
        audit_event_id=(str(audit_event["account_audit_event_id"]) if audit_event else None),
    )


async def validate_referral_saas_membership_acceptance_token(
    *,
    acceptance_token: str,
) -> MembershipAcceptanceTokenValidationResult:
    token_hash = _hash_acceptance_token(acceptance_token)
    async with db_connection() as conn:
        token_row = await conn.fetchrow(
            """
            SELECT
                tokens.acceptance_token_id,
                tokens.account_id,
                tokens.membership_id,
                tokens.status,
                tokens.expires_at,
                platform_accounts.account_name,
                platform_memberships.role_family,
                platform_memberships.permission_set,
                actor_user.display_name
            FROM referral_saas_membership_acceptance_tokens tokens
            JOIN platform_accounts
                ON platform_accounts.account_id = tokens.account_id
            JOIN platform_memberships
                ON platform_memberships.membership_id = tokens.membership_id
            LEFT JOIN platform_users actor_user
                ON actor_user.user_id = platform_memberships.user_id
            WHERE tokens.token_hash = $1
            LIMIT 1
            """,
            token_hash,
        )
        if not token_row:
            return MembershipAcceptanceTokenValidationResult(
                token_status="INVALID",
                account_id=None,
                membership_id=None,
                role_family=None,
                permission_set=None,
                account_name=None,
                display_name=None,
                expires_at=None,
                next_action="Ask the sender for a fresh access link.",
            )

        token_status = _normalise_acceptance_token_status(token_row.get("status"))
        expires_at_value = token_row.get("expires_at")
        now = datetime.now(UTC)
        if (
            token_status == "ISSUED"
            and isinstance(expires_at_value, datetime)
            and expires_at_value <= now
        ):
            await conn.fetchrow(
                """
                UPDATE referral_saas_membership_acceptance_tokens
                SET status = 'EXPIRED', expired_at = NOW(), updated_at = NOW()
                WHERE acceptance_token_id = $1
                RETURNING acceptance_token_id
                """,
                token_row["acceptance_token_id"],
            )
            token_status = "EXPIRED"
        next_action = {
            "ISSUED": "Review and accept access before the link expires.",
            "ACCEPTED": "Access has already been accepted for this customer.",
            "EXPIRED": "Ask the sender for a fresh access link.",
            "REVOKED": "Ask the sender for a fresh access link.",
        }.get(token_status, "Ask the sender for a fresh access link.")
        return MembershipAcceptanceTokenValidationResult(
            token_status=token_status,
            account_id=str(token_row["account_id"]),
            membership_id=str(token_row["membership_id"]),
            role_family=_optional_text(token_row.get("role_family")),
            permission_set=_optional_text(token_row.get("permission_set")),
            account_name=_optional_text(token_row.get("account_name")),
            display_name=_optional_text(token_row.get("display_name")),
            expires_at=(
                expires_at_value.isoformat()
                if isinstance(expires_at_value, datetime)
                else _optional_text(expires_at_value)
            ),
            next_action=next_action,
        )


async def accept_referral_saas_membership_acceptance_token(
    *,
    acceptance_token: str,
    acceptance_evidence_ref: str | None,
    correlation_id: str,
    idempotency_key_hash: str,
    command_payload_hash: str,
) -> MembershipAcceptanceTokenAcceptResult:
    token_hash = _hash_acceptance_token(acceptance_token)
    safe_acceptance_evidence_ref = _optional_text(acceptance_evidence_ref)
    safe_correlation_id = _required_text(correlation_id)
    safe_idempotency_hash = _required_text(idempotency_key_hash)
    safe_payload_hash = _required_text(command_payload_hash)
    async with db_connection() as conn:
        token_row = await conn.fetchrow(
            """
            SELECT
                tokens.acceptance_token_id,
                tokens.account_id,
                tokens.membership_id,
                tokens.tenant_code,
                tokens.accepted_subject_ref,
                tokens.status AS token_status,
                tokens.expires_at,
                platform_accounts.status AS account_status,
                platform_memberships.role_family,
                platform_memberships.permission_set,
                COALESCE(account_tenants.account_tenant_id::text, '') AS account_tenant_id,
                COALESCE(account_tenants.status, 'MISSING') AS tenant_link_status,
                COALESCE(external_refs.external_ref_id::text, '') AS external_ref_id,
                COALESCE(external_refs.status, 'MISSING') AS external_reference_status
            FROM referral_saas_membership_acceptance_tokens tokens
            JOIN platform_accounts
                ON platform_accounts.account_id = tokens.account_id
            JOIN platform_memberships
                ON platform_memberships.membership_id = tokens.membership_id
            LEFT JOIN platform_account_tenants account_tenants
                ON account_tenants.account_id = tokens.account_id
               AND account_tenants.tenant_code = tokens.tenant_code
               AND account_tenants.archived_at IS NULL
            LEFT JOIN platform_external_tenant_refs external_refs
                ON external_refs.account_id = tokens.account_id
               AND external_refs.ref_type = 'external_tenant_ref'
               AND external_refs.status = 'ACTIVE'
               AND external_refs.archived_at IS NULL
            WHERE tokens.token_hash = $1
            ORDER BY external_refs.created_at DESC NULLS LAST
            LIMIT 1
            """,
            token_hash,
        )
    if not token_row:
        raise MembershipInvitationAcceptanceTokenInvalid(
            "Acceptance token is invalid or was not found."
        )
    token_status = _normalise_acceptance_token_status(token_row.get("token_status"))
    expires_at_value = token_row.get("expires_at")
    if token_status == "ACCEPTED":
        raise MembershipInvitationAcceptanceTokenReplay(
            "Acceptance token has already been used."
        )
    if token_status != "ISSUED":
        raise MembershipInvitationAcceptanceTokenInvalid(
            "Acceptance token is not in an issued state."
        )
    if isinstance(expires_at_value, datetime) and expires_at_value <= datetime.now(UTC):
        async with db_connection() as conn:
            await conn.fetchrow(
                """
                UPDATE referral_saas_membership_acceptance_tokens
                SET status = 'EXPIRED', expired_at = NOW(), updated_at = NOW()
                WHERE acceptance_token_id = $1
                RETURNING acceptance_token_id
                """,
                token_row["acceptance_token_id"],
            )
        raise MembershipInvitationAcceptanceTokenExpired(
            "Acceptance token has expired. Ask the sender for a fresh access link."
        )

    activation_payload = {
        "acceptanceToken": {
            "tokenRef": str(token_row["acceptance_token_id"]),
            "hashPresent": True,
        },
        "reasonCode": "EXPIRING_INVITE_ACCEPTANCE",
        "noInviteDeliveryConfirmed": True,
        "noSeatAssignmentConfirmed": True,
        "noAuthClaimChangeConfirmed": True,
    }
    activation = await request_referral_saas_membership_activation(
        account_id=str(token_row["account_id"]),
        tenant_code=_optional_text(token_row.get("tenant_code")) or "",
        account_tenant_id=_optional_text(token_row.get("account_tenant_id")) or None,
        external_ref_id=_optional_text(token_row.get("external_ref_id")) or None,
        account_status=_optional_text(token_row.get("account_status")) or "UNKNOWN",
        tenant_link_status=_optional_text(token_row.get("tenant_link_status")) or "MISSING",
        external_reference_status=_optional_text(token_row.get("external_reference_status"))
        or "MISSING",
        membership_id=str(token_row["membership_id"]),
        accepted_subject=_optional_text(token_row.get("accepted_subject_ref")),
        acceptance_evidence_ref=safe_acceptance_evidence_ref
        or f"acceptance-token:{token_row['acceptance_token_id']}",
        reason_code="EXPIRING_INVITE_ACCEPTANCE",
        correlation_id=safe_correlation_id,
        idempotency_key_hash=safe_idempotency_hash,
        command_payload_hash=safe_payload_hash,
        command_payload=activation_payload,
        command_actor_ref="REFERRAL_SAAS_INVITED_PERSON",
        command_actor_role="INVITED_PERSON",
    )
    if activation.command_status == "MEMBERSHIP_ACTIVATED":
        async with db_connection() as conn:
            await conn.fetchrow(
                """
                UPDATE referral_saas_membership_acceptance_tokens
                SET status = 'ACCEPTED', accepted_at = NOW(), updated_at = NOW()
                WHERE acceptance_token_id = $1
                  AND status = 'ISSUED'
                RETURNING acceptance_token_id
                """,
                token_row["acceptance_token_id"],
            )
    return MembershipAcceptanceTokenAcceptResult(
        command_status=activation.command_status,
        token_status=(
            "ACCEPTED"
            if activation.command_status == "MEMBERSHIP_ACTIVATED"
            else "ISSUED"
        ),
        account_id=str(token_row["account_id"]),
        membership_id=str(token_row["membership_id"]),
        role_family=_optional_text(token_row.get("role_family")) or "UNKNOWN",
        permission_set=_optional_text(token_row.get("permission_set")) or "UNKNOWN",
        activation_status=activation.command_status,
        idempotency_status=activation.idempotency_status,
        audit_event_id=activation.audit_event_id,
    )


async def update_referral_saas_membership_invitation_intent(
    *,
    account_id: str,
    tenant_code: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    membership_id: str,
    email_hash: str | None = None,
    display_name: str | None = None,
    role_family: str,
    permission_set: str,
    reason_code: str,
    correlation_id: str,
    idempotency_key_hash: str,
    command_payload_hash: str,
    command_payload: dict[str, Any] | None = None,
    command_actor_ref: str | None = None,
    command_actor_role: str | None = None,
) -> MembershipInvitationLifecycleResult:
    safe_account_id = _required_account_id(account_id)
    safe_tenant_code = _required_text(tenant_code)
    safe_account_tenant_id = _optional_text(account_tenant_id) or None
    safe_external_ref_id = _optional_text(external_ref_id) or None
    safe_membership_id = _required_text(membership_id)
    safe_email_hash = _optional_text(email_hash) or None
    safe_display_name = _optional_text(display_name) or None
    safe_role_family = _required_choice(role_family, ROLE_FAMILIES)
    safe_permission_set = _required_text(permission_set).upper()
    safe_reason_code = _required_text(reason_code).upper()
    safe_correlation_id = _required_text(correlation_id)
    safe_idempotency_hash = _required_text(idempotency_key_hash)
    safe_payload_hash = _required_text(command_payload_hash)
    safe_command_payload = command_payload or {}

    _reject_unsafe_payload(safe_command_payload)

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
            MEMBERSHIP_INVITATION_UPDATE_EVENT,
            safe_idempotency_hash,
        )
        if existing_audit:
            evidence = _as_mapping(existing_audit.get("evidence_summary"))
            if _optional_text(evidence.get("command_payload_hash")) != safe_payload_hash:
                raise MembershipInvitationIdempotencyConflict(
                    "Idempotency key was reused with different membership update content."
                )
            return MembershipInvitationLifecycleResult(
                command_status="INVITATION_INTENT_UPDATE_REPLAYED",
                account_id=safe_account_id,
                membership_id=_optional_text(evidence.get("membership_id"))
                or safe_membership_id,
                previous_membership_status=_optional_text(
                    evidence.get("previous_membership_status")
                )
                or "INVITED",
                membership_status=_optional_text(evidence.get("membership_status"))
                or "INVITED",
                role_family=_optional_text(evidence.get("role_family"))
                or safe_role_family,
                permission_set=_optional_text(evidence.get("permission_set"))
                or safe_permission_set,
                idempotency_status="REPLAYED",
                audit_event_id=_optional_text(
                    existing_audit.get("account_audit_event_id")
                )
                or None,
                lifecycle_next_action="Review the updated access intent before invite delivery or activation.",
            )

        membership = await conn.fetchrow(
            """
            SELECT
                platform_memberships.membership_id,
                platform_memberships.status,
                platform_memberships.role_family,
                platform_memberships.permission_set,
                platform_memberships.user_id,
                platform_memberships.client_id,
                actor_user.subject,
                actor_user.display_name
            FROM platform_memberships
            LEFT JOIN platform_users actor_user
                ON actor_user.user_id = platform_memberships.user_id
            WHERE platform_memberships.membership_id = $1
              AND platform_memberships.account_id = $2
              AND (platform_memberships.tenant_code = $3 OR platform_memberships.tenant_code IS NULL)
              AND platform_memberships.status <> 'ARCHIVED'
            LIMIT 1
            """,
            safe_membership_id,
            safe_account_id,
            safe_tenant_code,
        )
        if not membership:
            raise MembershipInvitationNotFound(
                "Membership invitation intent was not found for this customer."
            )

        previous_status = _normalise_status(membership.get("status"))
        if previous_status != "INVITED":
            raise MembershipInvitationNotEditable(
                "Only invited access intent can be edited. Active, disabled, suspended, or archived access requires a separate maintenance workflow."
            )

        duplicate_membership = await conn.fetchrow(
            """
            SELECT duplicate.membership_id
            FROM platform_memberships duplicate
            WHERE duplicate.account_id = $1
              AND (duplicate.tenant_code = $2 OR duplicate.tenant_code IS NULL)
              AND duplicate.role_family = $3
              AND duplicate.status IN ('INVITED', 'ACTIVE', 'SUSPENDED')
              AND duplicate.membership_id <> $4
              AND (
                    ($5::uuid IS NOT NULL AND duplicate.user_id = $5)
                    OR ($6::text <> '' AND duplicate.client_id = $6)
              )
            LIMIT 1
            """,
            safe_account_id,
            safe_tenant_code,
            safe_role_family,
            safe_membership_id,
            membership.get("user_id"),
            _optional_text(membership.get("client_id")) or "",
        )
        if duplicate_membership:
            raise MembershipInvitationDuplicate(
                "A usable membership already exists for this actor, account, tenant scope, and role."
            )

        async with conn.transaction():
            if membership.get("user_id"):
                await conn.fetchrow(
                    """
                    UPDATE platform_users
                    SET
                        email_hash = COALESCE($2, email_hash),
                        display_name = COALESCE($3, display_name),
                        updated_at = NOW()
                    WHERE user_id = $1
                    RETURNING user_id
                    """,
                    membership.get("user_id"),
                    safe_email_hash,
                    safe_display_name,
                )

            updated_membership = await conn.fetchrow(
                """
                UPDATE platform_memberships
                SET
                    role_family = $4,
                    permission_set = $5,
                    metadata = COALESCE(metadata, '{}'::jsonb) || $6::jsonb,
                    updated_at = NOW()
                WHERE membership_id = $1
                  AND account_id = $2
                  AND (tenant_code = $3 OR tenant_code IS NULL)
                  AND status = 'INVITED'
                RETURNING membership_id, status, role_family, permission_set
                """,
                safe_membership_id,
                safe_account_id,
                safe_tenant_code,
                safe_role_family,
                safe_permission_set,
                _jsonb(
                    {
                        "updated_reason_code": safe_reason_code,
                        "no_email_delivery_confirmed": True,
                        "no_auth_claim_change_confirmed": True,
                        "no_seat_assignment_confirmed": True,
                    }
                ),
            )
            if not updated_membership:
                raise MembershipInvitationNotEditable(
                    "Membership invitation intent changed before the edit could be recorded."
                )

            audit_evidence = {
                "membership_id": safe_membership_id,
                "previous_membership_status": previous_status,
                "membership_status": "INVITED",
                "previous_role_family": _optional_text(membership.get("role_family")),
                "role_family": safe_role_family,
                "previous_permission_set": _optional_text(
                    membership.get("permission_set")
                ),
                "permission_set": safe_permission_set,
                "command_payload_hash": safe_payload_hash,
                "no_raw_email_storage_confirmed": True,
                "no_email_delivery_confirmed": True,
                "no_membership_activation_confirmed": True,
                "no_auth_claim_change_confirmed": True,
                "no_seat_assignment_confirmed": True,
                "no_money_movement_confirmed": True,
            }
            audit_event = await conn.fetchrow(
                """
                INSERT INTO platform_account_audit_events (
                    account_id,
                    account_tenant_id,
                    external_ref_id,
                    membership_id,
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
                    $1, $2, $3, $4, $5, $6, $7, $8, $9,
                    $10, 'INVITED', $11, $12, $13, $14::jsonb, $15::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                safe_account_tenant_id,
                safe_external_ref_id,
                safe_membership_id,
                safe_tenant_code,
                MEMBERSHIP_INVITATION_UPDATE_EVENT,
                EVENT_RECORDED,
                _optional_text(command_actor_ref)
                or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                _optional_text(command_actor_role) or "UNKNOWN",
                previous_status,
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(audit_evidence),
                _jsonb(list(INVITATION_REDACTIONS)),
            )

    return MembershipInvitationLifecycleResult(
        command_status="INVITATION_INTENT_UPDATED",
        account_id=safe_account_id,
        membership_id=safe_membership_id,
        previous_membership_status=previous_status,
        membership_status=str(updated_membership["status"]),
        role_family=str(updated_membership["role_family"]),
        permission_set=str(updated_membership["permission_set"]),
        idempotency_status=EVENT_RECORDED,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
        lifecycle_next_action="Review the updated access intent before invite delivery or activation.",
    )


async def cancel_referral_saas_membership_invitation_intent(
    *,
    account_id: str,
    tenant_code: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    membership_id: str,
    reason_code: str,
    correlation_id: str,
    idempotency_key_hash: str,
    command_payload_hash: str,
    command_payload: dict[str, Any] | None = None,
    command_actor_ref: str | None = None,
    command_actor_role: str | None = None,
) -> MembershipInvitationLifecycleResult:
    safe_account_id = _required_account_id(account_id)
    safe_tenant_code = _required_text(tenant_code)
    safe_account_tenant_id = _optional_text(account_tenant_id) or None
    safe_external_ref_id = _optional_text(external_ref_id) or None
    safe_membership_id = _required_text(membership_id)
    safe_reason_code = _required_text(reason_code).upper()
    safe_correlation_id = _required_text(correlation_id)
    safe_idempotency_hash = _required_text(idempotency_key_hash)
    safe_payload_hash = _required_text(command_payload_hash)
    safe_command_payload = command_payload or {}

    _reject_unsafe_payload(safe_command_payload)

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
            MEMBERSHIP_INVITATION_CANCEL_EVENT,
            safe_idempotency_hash,
        )
        if existing_audit:
            evidence = _as_mapping(existing_audit.get("evidence_summary"))
            if _optional_text(evidence.get("command_payload_hash")) != safe_payload_hash:
                raise MembershipInvitationIdempotencyConflict(
                    "Idempotency key was reused with different membership cancellation content."
                )
            return MembershipInvitationLifecycleResult(
                command_status="INVITATION_INTENT_CANCEL_REPLAYED",
                account_id=safe_account_id,
                membership_id=_optional_text(evidence.get("membership_id"))
                or safe_membership_id,
                previous_membership_status=_optional_text(
                    evidence.get("previous_membership_status")
                )
                or "INVITED",
                membership_status=_optional_text(evidence.get("membership_status"))
                or "DISABLED",
                role_family=_optional_text(evidence.get("role_family")) or "UNKNOWN",
                permission_set=_optional_text(evidence.get("permission_set"))
                or "UNKNOWN",
                idempotency_status="REPLAYED",
                audit_event_id=_optional_text(
                    existing_audit.get("account_audit_event_id")
                )
                or None,
                lifecycle_next_action="Record a new access intent if this person should manage the customer again.",
            )

        membership = await conn.fetchrow(
            """
            SELECT membership_id, status, role_family, permission_set
            FROM platform_memberships
            WHERE membership_id = $1
              AND account_id = $2
              AND (tenant_code = $3 OR tenant_code IS NULL)
              AND status <> 'ARCHIVED'
            LIMIT 1
            """,
            safe_membership_id,
            safe_account_id,
            safe_tenant_code,
        )
        if not membership:
            raise MembershipInvitationNotFound(
                "Membership invitation intent was not found for this customer."
            )

        previous_status = _normalise_status(membership.get("status"))
        if previous_status != "INVITED":
            raise MembershipInvitationNotEditable(
                "Only invited access intent can be removed. Active, disabled, suspended, or archived access requires a separate maintenance workflow."
            )

        async with conn.transaction():
            cancelled_membership = await conn.fetchrow(
                """
                UPDATE platform_memberships
                SET
                    status = 'DISABLED',
                    disabled_by_ref = $4,
                    disabled_at = NOW(),
                    metadata = COALESCE(metadata, '{}'::jsonb) || $5::jsonb,
                    updated_at = NOW()
                WHERE membership_id = $1
                  AND account_id = $2
                  AND (tenant_code = $3 OR tenant_code IS NULL)
                  AND status = 'INVITED'
                RETURNING membership_id, status, role_family, permission_set
                """,
                safe_membership_id,
                safe_account_id,
                safe_tenant_code,
                _optional_text(command_actor_ref)
                or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                _jsonb(
                    {
                        "cancelled_reason_code": safe_reason_code,
                        "no_email_delivery_confirmed": True,
                        "no_membership_activation_confirmed": True,
                        "no_auth_claim_change_confirmed": True,
                        "no_seat_assignment_confirmed": True,
                    }
                ),
            )
            if not cancelled_membership:
                raise MembershipInvitationNotEditable(
                    "Membership invitation intent changed before it could be removed."
                )

            audit_evidence = {
                "membership_id": safe_membership_id,
                "previous_membership_status": previous_status,
                "membership_status": "DISABLED",
                "role_family": _optional_text(membership.get("role_family")),
                "permission_set": _optional_text(membership.get("permission_set")),
                "command_payload_hash": safe_payload_hash,
                "no_delete_confirmed": True,
                "no_email_delivery_confirmed": True,
                "no_membership_activation_confirmed": True,
                "no_auth_claim_change_confirmed": True,
                "no_seat_assignment_confirmed": True,
                "no_money_movement_confirmed": True,
            }
            audit_event = await conn.fetchrow(
                """
                INSERT INTO platform_account_audit_events (
                    account_id,
                    account_tenant_id,
                    external_ref_id,
                    membership_id,
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
                    $1, $2, $3, $4, $5, $6, $7, $8, $9,
                    $10, 'DISABLED', $11, $12, $13, $14::jsonb, $15::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                safe_account_tenant_id,
                safe_external_ref_id,
                safe_membership_id,
                safe_tenant_code,
                MEMBERSHIP_INVITATION_CANCEL_EVENT,
                EVENT_RECORDED,
                _optional_text(command_actor_ref)
                or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                _optional_text(command_actor_role) or "UNKNOWN",
                previous_status,
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(audit_evidence),
                _jsonb(list(INVITATION_REDACTIONS)),
            )

    return MembershipInvitationLifecycleResult(
        command_status="INVITATION_INTENT_CANCELLED",
        account_id=safe_account_id,
        membership_id=safe_membership_id,
        previous_membership_status=previous_status,
        membership_status=str(cancelled_membership["status"]),
        role_family=str(cancelled_membership["role_family"]),
        permission_set=str(cancelled_membership["permission_set"]),
        idempotency_status=EVENT_RECORDED,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
        lifecycle_next_action="Record a new access intent if this person should manage the customer again.",
    )


async def request_referral_saas_membership_activation(
    *,
    account_id: str,
    tenant_code: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    account_status: str,
    tenant_link_status: str,
    external_reference_status: str,
    membership_id: str,
    accepted_subject: str | None,
    acceptance_evidence_ref: str | None,
    reason_code: str,
    correlation_id: str,
    idempotency_key_hash: str,
    command_payload_hash: str,
    command_payload: dict[str, Any] | None = None,
    command_actor_ref: str | None = None,
    command_actor_role: str | None = None,
) -> MembershipActivationRequestResult:
    safe_account_id = _required_account_id(account_id)
    safe_tenant_code = _required_text(tenant_code)
    safe_account_tenant_id = _optional_text(account_tenant_id) or None
    safe_external_ref_id = _optional_text(external_ref_id) or None
    safe_membership_id = _required_text(membership_id)
    safe_account_status = _required_text(account_status).upper()
    safe_tenant_link_status = _required_text(tenant_link_status).upper()
    safe_external_reference_status = _required_text(external_reference_status).upper()
    safe_accepted_subject = _optional_text(accepted_subject)
    safe_acceptance_evidence_ref = _optional_text(acceptance_evidence_ref)
    safe_reason_code = _required_text(reason_code).upper()
    safe_correlation_id = _required_text(correlation_id)
    safe_idempotency_hash = _required_text(idempotency_key_hash)
    safe_payload_hash = _required_text(command_payload_hash)
    safe_command_payload = command_payload or {}
    safe_command_actor_role = _optional_text(command_actor_role).upper()
    is_manual_access_acceptance = safe_reason_code == MANUAL_ACCESS_ACCEPTANCE_REASON

    _reject_unsafe_activation_payload(safe_command_payload)
    if (
        is_manual_access_acceptance
        and safe_command_actor_role not in MANUAL_ACCESS_ACCEPTANCE_ADMIN_ROLES
    ):
        raise MembershipInvitationUnsafeScope(
            "Manual access acceptance requires an Amplifi Admin actor."
        )

    async with db_connection() as conn:
        existing_audit = await conn.fetchrow(
            """
            SELECT
                account_audit_event_id,
                membership_id,
                previous_status,
                next_status,
                evidence_summary
            FROM platform_account_audit_events
            WHERE account_id = $1
              AND event_type = $2
              AND idempotency_key_hash = $3
            ORDER BY created_at DESC
            LIMIT 1
            """,
            safe_account_id,
            MEMBERSHIP_ACTIVATION_EVENT,
            safe_idempotency_hash,
        )
        if existing_audit:
            evidence = _as_mapping(existing_audit.get("evidence_summary"))
            if _optional_text(evidence.get("command_payload_hash")) != safe_payload_hash:
                raise MembershipInvitationIdempotencyConflict(
                    "Idempotency key was reused with different membership activation content."
                )
            replayed_status = (
                _optional_text(evidence.get("activation_status"))
                or _optional_text(existing_audit.get("next_status"))
                or "MEMBERSHIP_ACTIVATION_REPLAYED"
            )
            return MembershipActivationRequestResult(
                command_status=(
                    "MEMBERSHIP_ACTIVATION_REPLAYED"
                    if replayed_status == "MEMBERSHIP_ACTIVATED"
                    else replayed_status
                ),
                account_id=safe_account_id,
                membership_id=_optional_text(evidence.get("membership_id"))
                or safe_membership_id,
                previous_membership_status=_optional_text(
                    evidence.get("previous_membership_status")
                )
                or _optional_text(existing_audit.get("previous_status"))
                or "INVITED",
                membership_status=_optional_text(evidence.get("membership_status"))
                or _optional_text(existing_audit.get("next_status"))
                or "INVITED",
                role_family=_optional_text(evidence.get("role_family")) or "UNKNOWN",
                permission_set=_optional_text(evidence.get("permission_set"))
                or "UNKNOWN",
                accepted_subject_status=_optional_text(
                    evidence.get("accepted_subject_status")
                )
                or "ACCEPTED_SUBJECT_REPLAYED",
                activation_next_action=(
                    _optional_text(evidence.get("activation_next_action"))
                    or "Activation request replayed from the existing audit record."
                ),
                idempotency_status="REPLAYED",
                audit_event_id=_optional_text(
                    existing_audit.get("account_audit_event_id")
                )
                or None,
            )

        membership = await conn.fetchrow(
            """
            SELECT
                platform_memberships.membership_id,
                platform_memberships.status,
                platform_memberships.role_family,
                platform_memberships.permission_set,
                platform_memberships.user_id,
                platform_memberships.client_id,
                COALESCE(platform_memberships.metadata->>'delivery_status', 'DELIVERY_NOT_CONFIGURED')
                    AS delivery_status,
                actor_user.subject AS user_subject
            FROM platform_memberships
            LEFT JOIN platform_users actor_user
                ON actor_user.user_id = platform_memberships.user_id
            WHERE platform_memberships.membership_id = $1
              AND platform_memberships.account_id = $2
              AND (platform_memberships.tenant_code = $3 OR platform_memberships.tenant_code IS NULL)
              AND platform_memberships.status <> 'ARCHIVED'
            LIMIT 1
            """,
            safe_membership_id,
            safe_account_id,
            safe_tenant_code,
        )
        if not membership:
            raise MembershipInvitationUnsafeScope(
                "Membership reference does not match the resolved account context."
            )

        membership_status = _normalise_status(membership.get("status"))
        role_family = _optional_text(membership.get("role_family")) or "UNKNOWN"
        permission_set = _optional_text(membership.get("permission_set")) or "UNKNOWN"
        invited_subject = _optional_text(membership.get("user_subject")) or _optional_text(
            membership.get("client_id")
        )
        accepted_subject_status = "ACCEPTED_SUBJECT_MATCHED"
        duplicate_active = None
        if _optional_text(membership.get("user_id")) or _optional_text(
            membership.get("client_id")
        ):
            duplicate_active = await conn.fetchrow(
                """
                SELECT membership_id
                FROM platform_memberships
                WHERE account_id = $1
                  AND COALESCE(tenant_code, '') = COALESCE($2, '')
                  AND role_family = $3
                  AND status = 'ACTIVE'
                  AND membership_id <> $4
                  AND (
                      ($5::uuid IS NOT NULL AND user_id = $5::uuid)
                      OR ($6::text IS NOT NULL AND client_id = $6::text)
                  )
                LIMIT 1
                """,
                safe_account_id,
                safe_tenant_code,
                role_family,
                safe_membership_id,
                membership.get("user_id"),
                _optional_text(membership.get("client_id")) or "",
            )

        if membership_status != "INVITED":
            activation_status = (
                "ACTIVATION_REJECTED_DUPLICATE_ACTIVE_MEMBERSHIP"
                if membership_status == "ACTIVE"
                else "ACTIVATION_REJECTED_MEMBERSHIP_NOT_INVITED"
            )
            accepted_subject_status = "ACCEPTED_SUBJECT_NOT_EVALUATED"
        elif duplicate_active:
            activation_status = "ACTIVATION_REJECTED_DUPLICATE_ACTIVE_MEMBERSHIP"
            accepted_subject_status = "ACCEPTED_SUBJECT_NOT_EVALUATED"
        elif not safe_accepted_subject or safe_accepted_subject != invited_subject:
            activation_status = "ACTIVATION_REJECTED_IDENTITY_NOT_ACCEPTED"
            accepted_subject_status = "ACCEPTED_SUBJECT_MISSING_OR_MISMATCHED"
        elif is_manual_access_acceptance:
            if safe_account_status not in MANUAL_ACCESS_ACCEPTANCE_ACCOUNT_STATUSES:
                activation_status = "ACTIVATION_REJECTED_ACCOUNT_NOT_ACTIVE"
                accepted_subject_status = "ACCEPTED_SUBJECT_NOT_EVALUATED"
            elif (
                safe_tenant_link_status
                not in MANUAL_ACCESS_ACCEPTANCE_TENANT_LINK_STATUSES
            ):
                activation_status = "ACTIVATION_REJECTED_TENANT_LINK_NOT_ACTIVE"
                accepted_subject_status = "ACCEPTED_SUBJECT_NOT_EVALUATED"
            elif safe_external_reference_status != "ACTIVE":
                activation_status = "ACTIVATION_REJECTED_EXTERNAL_REFERENCE_NOT_ACTIVE"
                accepted_subject_status = "ACCEPTED_SUBJECT_NOT_EVALUATED"
            else:
                activation_status = "MEMBERSHIP_ACTIVATED"
        elif safe_account_status != "ACTIVE":
            activation_status = "ACTIVATION_REJECTED_ACCOUNT_NOT_ACTIVE"
            accepted_subject_status = "ACCEPTED_SUBJECT_NOT_EVALUATED"
        elif safe_tenant_link_status != "ACTIVE":
            activation_status = "ACTIVATION_REJECTED_TENANT_LINK_NOT_ACTIVE"
            accepted_subject_status = "ACCEPTED_SUBJECT_NOT_EVALUATED"
        elif safe_external_reference_status != "ACTIVE":
            activation_status = "ACTIVATION_REJECTED_EXTERNAL_REFERENCE_NOT_ACTIVE"
            accepted_subject_status = "ACCEPTED_SUBJECT_NOT_EVALUATED"
        else:
            activation_status = "MEMBERSHIP_ACTIVATED"

        next_status = "ACTIVE" if activation_status == "MEMBERSHIP_ACTIVATED" else membership_status
        activation_next_action = _activation_command_next_action(activation_status)
        audit_evidence = {
            "membership_id": safe_membership_id,
            "previous_membership_status": membership_status,
            "membership_status": next_status,
            "role_family": role_family,
            "permission_set": permission_set,
            "delivery_status": _optional_text(membership.get("delivery_status"))
            or "DELIVERY_NOT_CONFIGURED",
            "activation_status": activation_status,
            "accepted_subject_status": accepted_subject_status,
            "acceptance_evidence_present": bool(safe_acceptance_evidence_ref),
            "activation_next_action": activation_next_action,
            "command_payload_hash": safe_payload_hash,
            "manual_access_acceptance_confirmed": is_manual_access_acceptance,
            "account_status_at_acceptance": safe_account_status,
            "tenant_link_status_at_acceptance": safe_tenant_link_status,
            "external_reference_status_at_acceptance": safe_external_reference_status,
            "no_invite_delivery_confirmed": True,
            "no_auth_claim_change_confirmed": True,
            "no_seat_assignment_confirmed": True,
            "no_money_movement_confirmed": True,
        }
        redactions = list(
            INVITATION_REDACTIONS + ("accepted_subject", "acceptance_evidence_ref")
        )

        if activation_status == "MEMBERSHIP_ACTIVATED":
            async with conn.transaction():
                updated = await conn.fetchrow(
                    """
                    UPDATE platform_memberships
                    SET
                        status = 'ACTIVE',
                        accepted_by_ref = $1,
                        accepted_at = NOW(),
                        updated_at = NOW(),
                        metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
                            'activation_status', 'MEMBERSHIP_ACTIVATED',
                            'acceptance_evidence_ref_present', $2::boolean,
                            'manual_access_acceptance_confirmed', $5::boolean,
                            'account_status_at_acceptance', $6::text,
                            'tenant_link_status_at_acceptance', $7::text,
                            'external_reference_status_at_acceptance', $8::text,
                            'no_auth_claim_change_confirmed', true,
                            'no_seat_assignment_confirmed', true
                        )
                    WHERE membership_id = $3
                      AND account_id = $4
                      AND status = 'INVITED'
                    RETURNING status
                    """,
                    safe_accepted_subject,
                    bool(safe_acceptance_evidence_ref),
                    safe_membership_id,
                    safe_account_id,
                    is_manual_access_acceptance,
                    safe_account_status,
                    safe_tenant_link_status,
                    safe_external_reference_status,
                )
                if not updated:
                    raise MembershipActivationDuplicateActiveMembership(
                        "Membership could not be activated from the invited state."
                    )
                audit_event = await _insert_activation_audit_event(
                    conn,
                    account_id=safe_account_id,
                    account_tenant_id=safe_account_tenant_id,
                    external_ref_id=safe_external_ref_id,
                    membership_id=safe_membership_id,
                    tenant_code=safe_tenant_code,
                    event_status=EVENT_RECORDED,
                    actor_ref=_optional_text(command_actor_ref)
                    or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                    actor_role=safe_command_actor_role or "UNKNOWN",
                    previous_status=membership_status,
                    next_status=activation_status,
                    reason_code=safe_reason_code,
                    correlation_id=safe_correlation_id,
                    idempotency_key_hash=safe_idempotency_hash,
                    audit_evidence=audit_evidence,
                    redactions=redactions,
                )
        else:
            audit_event = await _insert_activation_audit_event(
                conn,
                account_id=safe_account_id,
                account_tenant_id=safe_account_tenant_id,
                external_ref_id=safe_external_ref_id,
                membership_id=safe_membership_id,
                tenant_code=safe_tenant_code,
                event_status="BLOCKED",
                actor_ref=_optional_text(command_actor_ref)
                or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                actor_role=safe_command_actor_role or "UNKNOWN",
                previous_status=membership_status,
                next_status=activation_status,
                reason_code=safe_reason_code,
                correlation_id=safe_correlation_id,
                idempotency_key_hash=safe_idempotency_hash,
                audit_evidence=audit_evidence,
                redactions=redactions,
            )

    return MembershipActivationRequestResult(
        command_status=activation_status,
        account_id=safe_account_id,
        membership_id=safe_membership_id,
        previous_membership_status=membership_status,
        membership_status=next_status,
        role_family=role_family,
        permission_set=permission_set,
        accepted_subject_status=accepted_subject_status,
        activation_next_action=activation_next_action,
        idempotency_status=EVENT_RECORDED,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
    )


async def request_referral_saas_access_provisioning(
    *,
    account_id: str,
    tenant_code: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    account_status: str,
    tenant_link_status: str,
    external_reference_status: str,
    membership_id: str,
    seat_type: str,
    seat_assignment_evidence_ref: str | None,
    auth_provider_ref: str | None,
    auth_claim_evidence_ref: str | None,
    operator_notes: str | None,
    reason_code: str,
    correlation_id: str,
    idempotency_key_hash: str,
    command_payload_hash: str,
    command_payload: dict[str, Any] | None = None,
    command_actor_ref: str | None = None,
    command_actor_role: str | None = None,
) -> AccessProvisioningRequestResult:
    safe_account_id = _required_account_id(account_id)
    safe_tenant_code = _required_text(tenant_code)
    safe_account_tenant_id = _optional_text(account_tenant_id) or None
    safe_external_ref_id = _optional_text(external_ref_id) or None
    safe_membership_id = _required_text(membership_id)
    safe_account_status = _required_text(account_status).upper()
    safe_tenant_link_status = _required_text(tenant_link_status).upper()
    safe_external_reference_status = _required_text(external_reference_status).upper()
    safe_seat_type = _required_choice(seat_type, ACCESS_PROVISIONING_SEAT_TYPES)
    safe_seat_assignment_evidence_ref = _optional_text(seat_assignment_evidence_ref)
    safe_auth_provider_ref = _optional_text(auth_provider_ref)
    safe_auth_claim_evidence_ref = _optional_text(auth_claim_evidence_ref)
    safe_operator_notes = _optional_text(operator_notes)
    safe_reason_code = _required_text(reason_code).upper()
    safe_correlation_id = _required_text(correlation_id)
    safe_idempotency_hash = _required_text(idempotency_key_hash)
    safe_payload_hash = _required_text(command_payload_hash)
    safe_command_payload = command_payload or {}
    safe_command_actor_role = _optional_text(command_actor_role).upper()

    _reject_unsafe_access_provisioning_payload(safe_command_payload)
    if safe_command_actor_role not in ACCESS_PROVISIONING_ADMIN_ROLES:
        raise MembershipInvitationUnsafeScope(
            "Access provisioning requires an Amplifi Admin actor."
        )

    async with db_connection() as conn:
        existing_audit = await conn.fetchrow(
            """
            SELECT
                account_audit_event_id,
                membership_id,
                previous_status,
                next_status,
                evidence_summary
            FROM platform_account_audit_events
            WHERE account_id = $1
              AND event_type = $2
              AND idempotency_key_hash = $3
            ORDER BY created_at DESC
            LIMIT 1
            """,
            safe_account_id,
            MEMBERSHIP_ACCESS_PROVISIONING_EVENT,
            safe_idempotency_hash,
        )
        if existing_audit:
            evidence = _as_mapping(existing_audit.get("evidence_summary"))
            if _optional_text(evidence.get("command_payload_hash")) != safe_payload_hash:
                raise MembershipInvitationIdempotencyConflict(
                    "Idempotency key was reused with different access provisioning content."
                )
            replayed_status = (
                _optional_text(evidence.get("provisioning_status"))
                or _optional_text(existing_audit.get("next_status"))
                or "PROVISIONING_REPLAYED"
            )
            command_status = (
                "PROVISIONING_REPLAYED"
                if replayed_status == "PROVISIONING_REQUEST_RECORDED"
                else replayed_status
            )
            return AccessProvisioningRequestResult(
                command_status=command_status,
                account_id=safe_account_id,
                membership_id=_optional_text(evidence.get("membership_id"))
                or safe_membership_id,
                role_family=_optional_text(evidence.get("role_family")) or "UNKNOWN",
                permission_set=_optional_text(evidence.get("permission_set"))
                or "UNKNOWN",
                seat_type=_optional_text(evidence.get("seat_type")) or safe_seat_type,
                seat_assignment_status=_optional_text(
                    evidence.get("seat_assignment_status")
                )
                or "SEAT_NOT_ASSIGNED",
                seat_ref=_optional_text(evidence.get("seat_ref")) or None,
                auth_claim_status=_optional_text(evidence.get("auth_claim_status"))
                or "AUTH_CLAIMS_NOT_PROPAGATED",
                provisioning_next_action=(
                    _optional_text(evidence.get("provisioning_next_action"))
                    or _access_provisioning_next_action(command_status)
                ),
                idempotency_status="REPLAYED",
                audit_event_id=_optional_text(
                    existing_audit.get("account_audit_event_id")
                )
                or None,
            )

        membership = await conn.fetchrow(
            """
            SELECT
                membership_id,
                status,
                role_family,
                permission_set,
                seat_id
            FROM platform_memberships
            WHERE membership_id = $1
              AND account_id = $2
              AND (tenant_code = $3 OR tenant_code IS NULL)
              AND status <> 'ARCHIVED'
            LIMIT 1
            """,
            safe_membership_id,
            safe_account_id,
            safe_tenant_code,
        )
        if not membership:
            raise MembershipInvitationUnsafeScope(
                "Membership reference does not match the resolved account context."
            )

        membership_status = _normalise_status(membership.get("status"))
        role_family = _optional_text(membership.get("role_family")) or "UNKNOWN"
        permission_set = _optional_text(membership.get("permission_set")) or "UNKNOWN"
        seat_ref = _optional_text(membership.get("seat_id")) or None

        provisioning_status = "PROVISIONING_REQUEST_RECORDED"
        seat_assignment_status = "SEAT_ASSIGNED"
        next_status = "SEAT_ASSIGNED"
        selected_seat = None

        if safe_account_status != "ACTIVE":
            provisioning_status = "PROVISIONING_REJECTED_ACCOUNT_NOT_ACTIVE"
            seat_assignment_status = "SEAT_NOT_ASSIGNED"
            next_status = provisioning_status
        elif safe_tenant_link_status != "ACTIVE":
            provisioning_status = "PROVISIONING_REJECTED_TENANT_LINK_NOT_ACTIVE"
            seat_assignment_status = "SEAT_NOT_ASSIGNED"
            next_status = provisioning_status
        elif safe_external_reference_status != "ACTIVE":
            provisioning_status = "PROVISIONING_REJECTED_EXTERNAL_REFERENCE_NOT_ACTIVE"
            seat_assignment_status = "SEAT_NOT_ASSIGNED"
            next_status = provisioning_status
        elif membership_status != "ACTIVE":
            provisioning_status = "PROVISIONING_REJECTED_MEMBERSHIP_NOT_ACTIVE"
            seat_assignment_status = "SEAT_NOT_ASSIGNED"
            next_status = provisioning_status
        elif seat_ref:
            provisioning_status = "PROVISIONING_REJECTED_SEAT_UNAVAILABLE"
            seat_assignment_status = "SEAT_ALREADY_ASSIGNED"
            next_status = provisioning_status
        else:
            selected_seat = await conn.fetchrow(
                """
                SELECT seat_id, seat_type, status
                FROM platform_seats
                WHERE account_id = $1
                  AND seat_type = $2
                  AND status = 'AVAILABLE'
                ORDER BY created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
                """,
                safe_account_id,
                safe_seat_type,
            )
            if not selected_seat:
                provisioning_status = "PROVISIONING_REJECTED_SEAT_UNAVAILABLE"
                seat_assignment_status = "SEAT_UNAVAILABLE"
                next_status = provisioning_status

        provisioning_next_action = _access_provisioning_next_action(
            provisioning_status
        )
        auth_claim_status = "AUTH_CLAIMS_NOT_PROPAGATED"
        audit_evidence = {
            "membership_id": safe_membership_id,
            "membership_status": membership_status,
            "role_family": role_family,
            "permission_set": permission_set,
            "seat_type": safe_seat_type,
            "seat_ref": seat_ref,
            "seat_assignment_status": seat_assignment_status,
            "auth_claim_status": auth_claim_status,
            "auth_provider_ref_present": bool(safe_auth_provider_ref),
            "auth_claim_evidence_ref_present": bool(safe_auth_claim_evidence_ref),
            "seat_assignment_evidence_ref_present": bool(
                safe_seat_assignment_evidence_ref
            ),
            "operator_notes_present": bool(safe_operator_notes),
            "provisioning_status": provisioning_status,
            "provisioning_next_action": provisioning_next_action,
            "command_payload_hash": safe_payload_hash,
            "account_status_at_provisioning": safe_account_status,
            "tenant_link_status_at_provisioning": safe_tenant_link_status,
            "external_reference_status_at_provisioning": safe_external_reference_status,
            "no_invite_delivery_confirmed": True,
            "no_auth_claim_change_confirmed": True,
            "no_credential_creation_confirmed": True,
            "no_campaign_activation_confirmed": True,
            "no_go_live_change_confirmed": True,
            "no_money_movement_confirmed": True,
        }
        redactions = list(ACCESS_PROVISIONING_REDACTIONS)

        if provisioning_status == "PROVISIONING_REQUEST_RECORDED":
            async with conn.transaction():
                updated_seat = await conn.fetchrow(
                    """
                    UPDATE platform_seats
                    SET
                        status = 'ASSIGNED',
                        assigned_membership_id = $1,
                        updated_at = NOW(),
                        metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
                            'access_provisioning_status', 'SEAT_ASSIGNED',
                            'seat_assignment_evidence_ref_present', $5::boolean,
                            'no_auth_claim_change_confirmed', true,
                            'no_credential_creation_confirmed', true
                        )
                    WHERE seat_id = $2
                      AND account_id = $3
                      AND seat_type = $4
                      AND status = 'AVAILABLE'
                    RETURNING seat_id, seat_type, status
                    """,
                    safe_membership_id,
                    selected_seat["seat_id"],
                    safe_account_id,
                    safe_seat_type,
                    bool(safe_seat_assignment_evidence_ref),
                )
                if not updated_seat:
                    raise AccessProvisioningSeatUnavailable(
                        "No available seat could be assigned to this membership."
                    )
                seat_ref = _optional_text(updated_seat.get("seat_id")) or None
                updated_membership = await conn.fetchrow(
                    """
                    UPDATE platform_memberships
                    SET
                        seat_id = $1,
                        updated_at = NOW(),
                        metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
                            'access_provisioning_status', 'SEAT_ASSIGNED',
                            'auth_claim_status', 'AUTH_CLAIMS_NOT_PROPAGATED',
                            'auth_provider_ref_present', $4::boolean,
                            'auth_claim_evidence_ref_present', $5::boolean,
                            'no_invite_delivery_confirmed', true,
                            'no_auth_claim_change_confirmed', true,
                            'no_credential_creation_confirmed', true,
                            'no_campaign_activation_confirmed', true,
                            'no_go_live_change_confirmed', true,
                            'no_money_movement_confirmed', true
                        )
                    WHERE membership_id = $2
                      AND account_id = $3
                      AND status = 'ACTIVE'
                      AND seat_id IS NULL
                    RETURNING membership_id, seat_id
                    """,
                    seat_ref,
                    safe_membership_id,
                    safe_account_id,
                    bool(safe_auth_provider_ref),
                    bool(safe_auth_claim_evidence_ref),
                )
                if not updated_membership:
                    raise AccessProvisioningMembershipNotActive(
                        "Membership could not be provisioned from the active state."
                    )
                audit_evidence["seat_ref"] = seat_ref
                audit_event = await _insert_access_provisioning_audit_event(
                    conn,
                    account_id=safe_account_id,
                    account_tenant_id=safe_account_tenant_id,
                    external_ref_id=safe_external_ref_id,
                    membership_id=safe_membership_id,
                    tenant_code=safe_tenant_code,
                    event_status=EVENT_RECORDED,
                    actor_ref=_optional_text(command_actor_ref)
                    or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                    actor_role=safe_command_actor_role or "UNKNOWN",
                    previous_status="SEAT_AVAILABLE",
                    next_status=next_status,
                    reason_code=safe_reason_code,
                    correlation_id=safe_correlation_id,
                    idempotency_key_hash=safe_idempotency_hash,
                    audit_evidence=audit_evidence,
                    redactions=redactions,
                )
        else:
            audit_event = await _insert_access_provisioning_audit_event(
                conn,
                account_id=safe_account_id,
                account_tenant_id=safe_account_tenant_id,
                external_ref_id=safe_external_ref_id,
                membership_id=safe_membership_id,
                tenant_code=safe_tenant_code,
                event_status="BLOCKED",
                actor_ref=_optional_text(command_actor_ref)
                or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                actor_role=safe_command_actor_role or "UNKNOWN",
                previous_status=membership_status,
                next_status=next_status,
                reason_code=safe_reason_code,
                correlation_id=safe_correlation_id,
                idempotency_key_hash=safe_idempotency_hash,
                audit_evidence=audit_evidence,
                redactions=redactions,
            )

    return AccessProvisioningRequestResult(
        command_status=provisioning_status,
        account_id=safe_account_id,
        membership_id=safe_membership_id,
        role_family=role_family,
        permission_set=permission_set,
        seat_type=safe_seat_type,
        seat_assignment_status=seat_assignment_status,
        seat_ref=seat_ref,
        auth_claim_status=auth_claim_status,
        provisioning_next_action=provisioning_next_action,
        idempotency_status=EVENT_RECORDED,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
    )


async def get_referral_saas_login_completion_readiness(
    *,
    account_id: str,
    tenant_code: str,
    account_status: str,
    tenant_link_status: str | None,
    external_reference_status: str | None,
    membership_id: str,
) -> LoginCompletionReadiness:
    safe_account_id = _required_account_id(account_id)
    safe_tenant_code = _required_text(tenant_code)
    safe_membership_id = _required_text(membership_id)

    async with db_connection() as conn:
        membership = await conn.fetchrow(
            """
            SELECT
                platform_memberships.membership_id,
                platform_memberships.status,
                platform_memberships.role_family,
                platform_memberships.permission_set,
                platform_memberships.seat_id,
                platform_memberships.metadata,
                actor_user.subject AS user_subject,
                actor_user.display_name AS user_display_name
            FROM platform_memberships
            LEFT JOIN platform_users actor_user
                ON actor_user.user_id = platform_memberships.user_id
            WHERE platform_memberships.membership_id = $1
              AND platform_memberships.account_id = $2
              AND (platform_memberships.tenant_code = $3 OR platform_memberships.tenant_code IS NULL)
              AND platform_memberships.status <> 'ARCHIVED'
            LIMIT 1
            """,
            safe_membership_id,
            safe_account_id,
            safe_tenant_code,
        )
    if not membership:
        raise MembershipInvitationUnsafeScope(
            "Membership reference does not match the resolved account context."
        )

    return _build_login_completion_readiness(
        account_id=safe_account_id,
        membership=membership,
        account_status=account_status,
        tenant_link_status=tenant_link_status,
        external_reference_status=external_reference_status,
    )


async def get_referral_saas_identity_login_reconciliation(
    *,
    account_id: str,
    tenant_code: str,
    account_status: str,
    tenant_link_status: str | None,
    external_reference_status: str | None,
) -> IdentityLoginReconciliation:
    safe_account_id = _required_account_id(account_id)
    safe_tenant_code = _required_text(tenant_code)

    async with db_connection() as conn:
        memberships = await conn.fetch(
            """
            SELECT
                platform_memberships.membership_id,
                platform_memberships.status,
                platform_memberships.role_family,
                platform_memberships.permission_set,
                platform_memberships.seat_id,
                platform_memberships.metadata,
                actor_user.subject AS user_subject,
                actor_user.display_name AS user_display_name
            FROM platform_memberships
            LEFT JOIN platform_users actor_user
                ON actor_user.user_id = platform_memberships.user_id
            WHERE platform_memberships.account_id = $1
              AND (platform_memberships.tenant_code = $2 OR platform_memberships.tenant_code IS NULL)
              AND platform_memberships.status <> 'ARCHIVED'
            ORDER BY
                CASE platform_memberships.role_family
                    WHEN 'DISTRIBUTION_ADMIN' THEN 1
                    WHEN 'CAMPAIGN_MANAGER' THEN 2
                    ELSE 10
                END,
                platform_memberships.created_at ASC
            """,
            safe_account_id,
            safe_tenant_code,
        )

    return build_identity_login_reconciliation(
        account_id=safe_account_id,
        memberships=tuple(memberships),
        account_status=account_status,
        tenant_link_status=tenant_link_status,
        external_reference_status=external_reference_status,
    )


def build_identity_login_reconciliation(
    *,
    account_id: str,
    memberships: tuple[Any, ...],
    account_status: str,
    tenant_link_status: str | None,
    external_reference_status: str | None,
) -> IdentityLoginReconciliation:
    people = tuple(
        _build_identity_login_reconciliation_person(
            account_status=account_status,
            tenant_link_status=tenant_link_status,
            external_reference_status=external_reference_status,
            membership=membership,
        )
        for membership in memberships
    )
    accepted_count = sum(1 for person in people if person.access_status == "CUSTOMER_ACCESS_ACCEPTED")
    named_count = sum(1 for person in people if person.access_status in {"CUSTOMER_ACCESS_NAMED", "CUSTOMER_ACCESS_ACCEPTED"})
    seat_assigned_count = sum(1 for person in people if person.seat_assignment_status == "SEAT_ASSIGNED")
    provider_evidence_count = sum(
        1 for person in people if person.identity_provider_status == "APPROVED_EVIDENCE_RECORDED"
    )
    auth_claim_ready_count = sum(
        1 for person in people if person.auth_claim_status in {"AUTH_CLAIMS_PROPAGATED", "AUTH_CLAIMS_VERIFIED"}
    )
    revoked_count = sum(1 for person in people if person.revocation_status in {"REVOKED", "REVOCATION_RECORDED"})
    claim_mismatch_count = sum(1 for person in people if "AUTH_CLAIM_MISMATCH" in person.blockers)
    stale_provider_evidence_count = sum(1 for person in people if "PROVIDER_EVIDENCE_STALE" in person.warnings)
    action_required_count = sum(
        1
        for person in people
        if person.login_status
        not in {"LOGIN_RECONCILED", "PLATFORM_LOGIN_NOT_REQUIRED", "ACCESS_REVOKED"}
    )

    if not people:
        reconciliation_status = "NO_PEOPLE_RECORDED"
    elif action_required_count:
        reconciliation_status = "LOGIN_RECONCILIATION_ACTION_REQUIRED"
    else:
        reconciliation_status = "LOGIN_RECONCILED"

    return IdentityLoginReconciliation(
        account_id=account_id,
        reconciliation_status=reconciliation_status,
        people=people,
        accepted_count=accepted_count,
        named_count=named_count,
        seat_assigned_count=seat_assigned_count,
        provider_evidence_count=provider_evidence_count,
        auth_claim_ready_count=auth_claim_ready_count,
        revoked_count=revoked_count,
        action_required_count=action_required_count,
        claim_mismatch_count=claim_mismatch_count,
        stale_provider_evidence_count=stale_provider_evidence_count,
    )


def _build_identity_login_reconciliation_person(
    *,
    account_status: str,
    tenant_link_status: str | None,
    external_reference_status: str | None,
    membership: Any,
) -> IdentityLoginReconciliationPerson:
    metadata = _as_mapping(membership.get("metadata"))
    membership_status = _normalise_status(membership.get("status"))
    role_family = _optional_text(membership.get("role_family")) or "UNKNOWN"
    permission_profile = (
        _optional_text(metadata.get("permission_profile"))
        or LOGIN_COMPLETION_PERMISSION_PROFILES.get(role_family)
    )
    login_completion_status = _optional_text(metadata.get("login_completion_status"))
    login_intent = (
        _optional_text(metadata.get("login_completion_intent"))
        or "PLATFORM_LOGIN_REQUIRED"
    )
    metadata_seat_status = _optional_text(metadata.get("seat_assignment_status"))
    seat_assignment_status = (
        "SEAT_ASSIGNED"
        if _optional_text(membership.get("seat_id")) or metadata_seat_status == "SEAT_ASSIGNED"
        else metadata_seat_status or "SEAT_NOT_ASSIGNED"
    )
    identity_provider_status = (
        _optional_text(metadata.get("identity_provider_status")) or "NOT_RECORDED"
    )
    auth_claim_status = (
        _optional_text(metadata.get("auth_claim_status"))
        or "AUTH_CLAIMS_NOT_PROPAGATED"
    )
    revocation_status = (
        _optional_text(metadata.get("identity_revocation_status"))
        or _optional_text(metadata.get("revocation_status"))
        or "NO_REVOCATION_REQUESTED"
    )
    access_status = _identity_access_status(membership_status)

    blockers: list[str] = []
    warnings: list[str] = []
    if _optional_text(account_status).upper() != "ACTIVE":
        blockers.append("ACCOUNT_NOT_ACTIVE")
    if _optional_text(tenant_link_status).upper() != "ACTIVE":
        blockers.append("TENANT_LINK_NOT_ACTIVE")
    if _optional_text(external_reference_status).upper() != "ACTIVE":
        blockers.append("EXTERNAL_REFERENCE_NOT_ACTIVE")
    if access_status != "CUSTOMER_ACCESS_ACCEPTED":
        blockers.append("CUSTOMER_ACCESS_NOT_ACCEPTED")
    if login_intent != "LOGIN_NOT_REQUIRED" and seat_assignment_status != "SEAT_ASSIGNED":
        blockers.append("PLATFORM_SEAT_NOT_ASSIGNED")
    if identity_provider_status in {"PROVIDER_EVIDENCE_STALE", "STALE_PROVIDER_EVIDENCE"}:
        warnings.append("PROVIDER_EVIDENCE_STALE")
    if auth_claim_status in {"AUTH_CLAIM_MISMATCH", "CLAIM_MISMATCH"}:
        blockers.append("AUTH_CLAIM_MISMATCH")

    login_status = _identity_login_status(
        access_status=access_status,
        login_completion_status=login_completion_status,
        login_intent=login_intent,
        seat_assignment_status=seat_assignment_status,
        identity_provider_status=identity_provider_status,
        auth_claim_status=auth_claim_status,
        revocation_status=revocation_status,
        blockers=blockers,
    )
    next_action = _identity_login_next_action(login_status)
    steps = _identity_login_steps(
        access_status=access_status,
        login_status=login_status,
        seat_assignment_status=seat_assignment_status,
        identity_provider_status=identity_provider_status,
        auth_claim_status=auth_claim_status,
    )

    return IdentityLoginReconciliationPerson(
        membership_id=_optional_text(membership.get("membership_id")) or "",
        subject=_optional_text(membership.get("user_subject")) or None,
        display_name=_optional_text(membership.get("user_display_name")) or None,
        role_family=role_family,
        permission_profile=permission_profile,
        access_status=access_status,
        login_status=login_status,
        seat_assignment_status=seat_assignment_status,
        identity_provider_status=identity_provider_status,
        auth_claim_status=auth_claim_status,
        revocation_status=revocation_status,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
        next_action=next_action,
        steps=steps,
    )


async def request_referral_saas_login_completion_intent(
    *,
    account_id: str,
    tenant_code: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    account_status: str,
    tenant_link_status: str | None,
    external_reference_status: str | None,
    membership_id: str,
    intent: str,
    identity_subject_ref: str | None,
    auth_provider_ref: str | None,
    seat_evidence_ref: str | None,
    permission_profile: str | None,
    operator_reason: str | None,
    reason_code: str,
    correlation_id: str,
    idempotency_key_hash: str,
    command_payload_hash: str,
    command_payload: dict[str, Any] | None = None,
    command_actor_ref: str | None = None,
    command_actor_role: str | None = None,
) -> LoginCompletionIntentResult:
    safe_account_id = _required_account_id(account_id)
    safe_tenant_code = _required_text(tenant_code)
    safe_account_tenant_id = _optional_text(account_tenant_id) or None
    safe_external_ref_id = _optional_text(external_ref_id) or None
    safe_membership_id = _required_text(membership_id)
    safe_intent = _required_choice(intent, LOGIN_COMPLETION_INTENTS)
    safe_identity_subject_ref = _optional_text(identity_subject_ref)
    safe_auth_provider_ref = _optional_text(auth_provider_ref)
    safe_seat_evidence_ref = _optional_text(seat_evidence_ref)
    safe_permission_profile = _optional_text(permission_profile)
    safe_operator_reason = _optional_text(operator_reason)
    safe_reason_code = _required_text(reason_code).upper()
    safe_correlation_id = _required_text(correlation_id)
    safe_idempotency_hash = _required_text(idempotency_key_hash)
    safe_payload_hash = _required_text(command_payload_hash)
    safe_command_payload = command_payload or {}
    safe_command_actor_role = _optional_text(command_actor_role).upper()

    _reject_unsafe_login_completion_payload(safe_command_payload)
    if safe_command_actor_role not in LOGIN_COMPLETION_ADMIN_ROLES:
        raise MembershipInvitationUnsafeScope(
            "Login completion intent requires an Amplifi Admin actor."
        )

    async with db_connection() as conn:
        existing_audit = await conn.fetchrow(
            """
            SELECT
                account_audit_event_id,
                membership_id,
                next_status,
                evidence_summary
            FROM platform_account_audit_events
            WHERE account_id = $1
              AND event_type = $2
              AND idempotency_key_hash = $3
            ORDER BY created_at DESC
            LIMIT 1
            """,
            safe_account_id,
            MEMBERSHIP_LOGIN_COMPLETION_EVENT,
            safe_idempotency_hash,
        )
        if existing_audit:
            evidence = _as_mapping(existing_audit.get("evidence_summary"))
            if _optional_text(evidence.get("command_payload_hash")) != safe_payload_hash:
                raise MembershipInvitationIdempotencyConflict(
                    "Idempotency key was reused with different login completion content."
                )
            replayed_status = (
                _optional_text(evidence.get("login_completion_status"))
                or _optional_text(existing_audit.get("next_status"))
                or "LOGIN_COMPLETION_REPLAYED"
            )
            command_status = (
                "LOGIN_COMPLETION_REPLAYED"
                if replayed_status == "LOGIN_COMPLETION_RECORDED"
                else replayed_status
            )
            return LoginCompletionIntentResult(
                command_status=command_status,
                account_id=safe_account_id,
                membership_id=_optional_text(evidence.get("membership_id"))
                or safe_membership_id,
                role_family=_optional_text(evidence.get("role_family")) or "UNKNOWN",
                permission_profile=_optional_text(evidence.get("permission_profile"))
                or "UNKNOWN",
                intent=_optional_text(evidence.get("intent")) or safe_intent,
                seat_assignment_status=_optional_text(
                    evidence.get("seat_assignment_status")
                )
                or "SEAT_NOT_ASSIGNED",
                identity_provider_status=_optional_text(
                    evidence.get("identity_provider_status")
                )
                or "NOT_RECORDED",
                auth_claim_status=_optional_text(evidence.get("auth_claim_status"))
                or "AUTH_CLAIMS_NOT_PROPAGATED",
                login_next_action=(
                    _optional_text(evidence.get("login_next_action"))
                    or _login_completion_next_action(command_status)
                ),
                idempotency_status="REPLAYED",
                audit_event_id=_optional_text(
                    existing_audit.get("account_audit_event_id")
                )
                or None,
            )

        membership = await conn.fetchrow(
            """
            SELECT
                membership_id,
                status,
                role_family,
                permission_set,
                seat_id,
                metadata
            FROM platform_memberships
            WHERE membership_id = $1
              AND account_id = $2
              AND (tenant_code = $3 OR tenant_code IS NULL)
              AND status <> 'ARCHIVED'
            LIMIT 1
            """,
            safe_membership_id,
            safe_account_id,
            safe_tenant_code,
        )
        if not membership:
            raise MembershipInvitationUnsafeScope(
                "Membership reference does not match the resolved account context."
            )

        membership_status = _normalise_status(membership.get("status"))
        role_family = _optional_text(membership.get("role_family")) or "UNKNOWN"
        derived_permission_profile = LOGIN_COMPLETION_PERMISSION_PROFILES.get(
            role_family
        )
        requested_permission_profile = (
            safe_permission_profile or derived_permission_profile or ""
        )
        if (
            derived_permission_profile
            and requested_permission_profile != derived_permission_profile
        ):
            raise LoginCompletionPermissionProfileMissing(
                "Login permission profile does not match the governed responsibility mapping."
            )

        seat_assignment_status = (
            "SEAT_ASSIGNED"
            if _optional_text(membership.get("seat_id"))
            else "SEAT_NOT_ASSIGNED"
        )
        auth_claim_status = "AUTH_CLAIMS_NOT_PROPAGATED"
        identity_provider_status = (
            "APPROVED_EVIDENCE_RECORDED"
            if safe_auth_provider_ref
            else "NOT_RECORDED"
        )
        command_status = "LOGIN_COMPLETION_RECORDED"

        if _optional_text(account_status).upper() != "ACTIVE":
            command_status = "LOGIN_COMPLETION_BLOCKED_ACCOUNT_NOT_ACTIVE"
        elif _optional_text(tenant_link_status).upper() != "ACTIVE":
            command_status = "LOGIN_COMPLETION_BLOCKED_TENANT_LINK_NOT_ACTIVE"
        elif _optional_text(external_reference_status).upper() != "ACTIVE":
            command_status = "LOGIN_COMPLETION_BLOCKED_EXTERNAL_REFERENCE_NOT_ACTIVE"
        elif membership_status != "ACTIVE":
            command_status = "LOGIN_COMPLETION_BLOCKED_MEMBERSHIP_NOT_ACTIVE"
        elif not derived_permission_profile:
            command_status = "LOGIN_COMPLETION_BLOCKED_PERMISSION_PROFILE_MISSING"
        elif safe_intent == "PLATFORM_LOGIN_REQUIRED" and not _optional_text(
            membership.get("seat_id")
        ):
            command_status = "LOGIN_COMPLETION_BLOCKED_SEAT_NOT_ASSIGNED"
        elif safe_intent in {"PLATFORM_LOGIN_REQUIRED", "EXTERNAL_IDP_MANAGED"} and not safe_auth_provider_ref:
            command_status = "LOGIN_COMPLETION_BLOCKED_AUTH_PROVIDER_NOT_APPROVED"
        elif safe_intent == "LOGIN_NOT_REQUIRED":
            command_status = "LOGIN_COMPLETION_NOT_REQUIRED"

        login_next_action = _login_completion_next_action(command_status)
        audit_evidence = {
            "membership_id": safe_membership_id,
            "membership_status": membership_status,
            "role_family": role_family,
            "permission_profile": requested_permission_profile
            or derived_permission_profile
            or "UNKNOWN",
            "intent": safe_intent,
            "seat_assignment_status": seat_assignment_status,
            "identity_provider_status": identity_provider_status,
            "auth_claim_status": auth_claim_status,
            "identity_subject_ref_present": bool(safe_identity_subject_ref),
            "auth_provider_ref_present": bool(safe_auth_provider_ref),
            "seat_evidence_ref_present": bool(safe_seat_evidence_ref),
            "operator_reason_present": bool(safe_operator_reason),
            "login_completion_status": command_status,
            "login_next_action": login_next_action,
            "command_payload_hash": safe_payload_hash,
            "account_status_at_login_completion": _optional_text(
                account_status
            ).upper(),
            "tenant_link_status_at_login_completion": _optional_text(
                tenant_link_status
            ).upper(),
            "external_reference_status_at_login_completion": _optional_text(
                external_reference_status
            ).upper(),
            "no_invite_delivery_confirmed": True,
            "no_credential_creation_confirmed": True,
            "no_auth_claim_change_confirmed": True,
            "no_campaign_activation_confirmed": True,
            "no_go_live_change_confirmed": True,
            "no_money_movement_confirmed": True,
        }

        async with conn.transaction():
            if command_status in {
                "LOGIN_COMPLETION_RECORDED",
                "LOGIN_COMPLETION_NOT_REQUIRED",
            }:
                await conn.execute(
                    """
                    UPDATE platform_memberships
                    SET
                        updated_at = NOW(),
                        metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
                            'login_completion_status', $3::text,
                            'login_completion_intent', $4::text,
                            'permission_profile', $5::text,
                            'identity_provider_status', $6::text,
                            'auth_claim_status', 'AUTH_CLAIMS_NOT_PROPAGATED',
                            'no_invite_delivery_confirmed', true,
                            'no_credential_creation_confirmed', true,
                            'no_auth_claim_change_confirmed', true,
                            'no_campaign_activation_confirmed', true,
                            'no_go_live_change_confirmed', true,
                            'no_money_movement_confirmed', true
                        )
                    WHERE membership_id = $1
                      AND account_id = $2
                    """,
                    safe_membership_id,
                    safe_account_id,
                    command_status,
                    safe_intent,
                    requested_permission_profile
                    or derived_permission_profile
                    or "UNKNOWN",
                    identity_provider_status,
                )
            audit_event = await _insert_login_completion_audit_event(
                conn,
                account_id=safe_account_id,
                account_tenant_id=safe_account_tenant_id,
                external_ref_id=safe_external_ref_id,
                membership_id=safe_membership_id,
                tenant_code=safe_tenant_code,
                event_status=(
                    EVENT_RECORDED
                    if command_status
                    in {"LOGIN_COMPLETION_RECORDED", "LOGIN_COMPLETION_NOT_REQUIRED"}
                    else "BLOCKED"
                ),
                actor_ref=_optional_text(command_actor_ref)
                or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                actor_role=safe_command_actor_role or "UNKNOWN",
                previous_status=membership_status,
                next_status=command_status,
                reason_code=safe_reason_code,
                correlation_id=safe_correlation_id,
                idempotency_key_hash=safe_idempotency_hash,
                audit_evidence=audit_evidence,
                redactions=list(LOGIN_COMPLETION_REDACTIONS),
            )

    return LoginCompletionIntentResult(
        command_status=command_status,
        account_id=safe_account_id,
        membership_id=safe_membership_id,
        role_family=role_family,
        permission_profile=requested_permission_profile
        or derived_permission_profile
        or "UNKNOWN",
        intent=safe_intent,
        seat_assignment_status=seat_assignment_status,
        identity_provider_status=identity_provider_status,
        auth_claim_status=auth_claim_status,
        login_next_action=login_next_action,
        idempotency_status=EVENT_RECORDED,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
    )


def _current_actor_posture(rows: list[dict[str, Any]]) -> MembershipActorPosture:
    actor_rows = [row for row in rows if bool(row.get("is_current_actor"))]
    active = _first_with_status(actor_rows, "ACTIVE")
    if active:
        return MembershipActorPosture(
            status="MEMBERSHIP_CONFIRMED",
            role_family=_optional_text(active.get("role_family")) or None,
            permission_set=_optional_text(active.get("permission_set")) or None,
            can_operate_setup=True,
            evidence="Active account membership matched the current actor.",
        )

    invited = _first_with_status(actor_rows, "INVITED")
    if invited:
        return MembershipActorPosture(
            status="INVITED_NOT_ACTIVE",
            role_family=_optional_text(invited.get("role_family")) or None,
            permission_set=_optional_text(invited.get("permission_set")) or None,
            can_operate_setup=False,
            evidence="The current actor has invited membership evidence, but it is not active.",
        )

    blocked = _first_with_status(actor_rows, "SUSPENDED") or _first_with_status(
        actor_rows, "DISABLED"
    )
    if blocked:
        return MembershipActorPosture(
            status="MEMBERSHIP_NOT_USABLE",
            role_family=_optional_text(blocked.get("role_family")) or None,
            permission_set=_optional_text(blocked.get("permission_set")) or None,
            can_operate_setup=False,
            evidence="The current actor membership evidence is suspended or disabled.",
        )

    return MembershipActorPosture(
        status="NO_MEMBERSHIP_EVIDENCE",
        role_family=None,
        permission_set=None,
        can_operate_setup=False,
        evidence=(
            "No active account membership matched the current actor. Operator API "
            "access may still read this posture, but invitation and membership "
            "writes remain outside Account Setup."
        ),
    )


def _first_with_status(
    rows: list[dict[str, Any]],
    status: str,
) -> dict[str, Any] | None:
    for row in rows:
        if _normalise_status(row.get("status")) == status:
            return row
    return None


def _status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in MEMBERSHIP_STATUSES}
    for row in rows:
        counts[_normalise_status(row.get("status"))] = (
            counts.get(_normalise_status(row.get("status")), 0) + 1
        )
    return counts


def _role_family_summaries(
    rows: list[dict[str, Any]],
) -> list[MembershipRoleFamilySummary]:
    summaries: dict[str, dict[str, int]] = {}
    for row in rows:
        role_family = _optional_text(row.get("role_family")) or "UNKNOWN"
        if role_family not in summaries:
            summaries[role_family] = {status: 0 for status in MEMBERSHIP_STATUSES}
        summaries[role_family][_normalise_status(row.get("status"))] += 1

    return [
        MembershipRoleFamilySummary(
            role_family=role_family,
            invited_count=counts["INVITED"],
            active_count=counts["ACTIVE"],
            suspended_count=counts["SUSPENDED"],
            disabled_count=counts["DISABLED"],
            archived_count=counts["ARCHIVED"],
        )
        for role_family, counts in sorted(summaries.items())
    ]


def _membership_person_summaries(
    rows: list[dict[str, Any]],
) -> list[MembershipPersonSummary]:
    summaries: list[MembershipPersonSummary] = []
    for row in rows:
        actor_type = _optional_text(row.get("actor_type")) or "UNKNOWN"
        subject = (
            _optional_text(row.get("user_subject"))
            if actor_type == USER_ACTOR
            else _optional_text(row.get("client_id"))
        )
        display_name = _optional_text(row.get("user_display_name")) or subject
        summaries.append(
            MembershipPersonSummary(
                membership_id=_optional_text(row.get("membership_id")) or "UNKNOWN",
                actor_type=actor_type,
                subject=subject or None,
                display_name=display_name or None,
                role_family=_optional_text(row.get("role_family")) or "UNKNOWN",
                permission_set=_optional_text(row.get("permission_set")) or "UNKNOWN",
                status=_normalise_status(row.get("status")),
                delivery_status=(
                    _optional_text(row.get("delivery_status"))
                    or "DELIVERY_NOT_CONFIGURED"
                ),
                recipient_contact_status=(
                    _optional_text(row.get("recipient_contact_status"))
                    or "CONTACT_REFERENCE_MISSING"
                ),
                seat_assignment_status=(
                    _optional_text(row.get("seat_assignment_status"))
                    or "SEAT_NOT_ASSIGNED"
                ),
                auth_claim_status=(
                    _optional_text(row.get("auth_claim_status"))
                    or "AUTH_CLAIMS_NOT_PROPAGATED"
                ),
            )
        )
    return summaries


def _activation_readiness_item(
    *,
    membership: MembershipPersonSummary,
    account_status: str,
    tenant_link_status: str,
    external_reference_status: str,
) -> MembershipActivationReadinessItem:
    blockers: list[str] = []
    delivery_status = _optional_text(membership.delivery_status).upper()
    membership_status = _normalise_status(membership.status)

    if membership_status == "ACTIVE":
        seat_assignment_status = (
            _optional_text(membership.seat_assignment_status) or "SEAT_NOT_ASSIGNED"
        )
        auth_claim_status = (
            _optional_text(membership.auth_claim_status)
            or "AUTH_CLAIMS_NOT_PROPAGATED"
        )
        seat_assigned = seat_assignment_status == "SEAT_ASSIGNED"
        return MembershipActivationReadinessItem(
            membership_id=membership.membership_id,
            subject=membership.subject,
            display_name=membership.display_name,
            role_family=membership.role_family,
            membership_status=membership_status,
            delivery_status=delivery_status or "NOT_REQUIRED",
            recipient_contact_status=membership.recipient_contact_status,
            delivery_readiness="DELIVERY_NOT_REQUIRED",
            activation_readiness="ACTIVE",
            provisioning_readiness=(
                "SEAT_ASSIGNED" if seat_assigned else "READY_TO_PROVISION_SEAT"
            ),
            seat_assignment_status=seat_assignment_status,
            auth_claim_status=auth_claim_status,
            blockers=(),
            next_action=(
                "Seat is assigned. Configure auth claims through the separate "
                "governed workflow before login access is live."
                if seat_assigned
                else "Membership is active. Provision a seat before login access "
                "is live; auth claims remain a separate governed workflow."
            ),
        )

    if membership_status != "INVITED":
        return MembershipActivationReadinessItem(
            membership_id=membership.membership_id,
            subject=membership.subject,
            display_name=membership.display_name,
            role_family=membership.role_family,
            membership_status=membership_status,
            delivery_status=delivery_status or "DELIVERY_NOT_CONFIGURED",
            recipient_contact_status=membership.recipient_contact_status,
            delivery_readiness="BLOCKED",
            activation_readiness="BLOCKED",
            provisioning_readiness="WAITING_FOR_MEMBERSHIP_ACTIVATION",
            seat_assignment_status=membership.seat_assignment_status,
            auth_claim_status=membership.auth_claim_status,
            blockers=(f"MEMBERSHIP_{membership_status}",),
            next_action="Resolve the membership status before delivery or activation.",
        )

    if delivery_status in {"", "DELIVERY_NOT_CONFIGURED"}:
        blockers.append("DELIVERY_PROVIDER_NOT_CONFIGURED")
    if membership.recipient_contact_status == "CONTACT_REFERENCE_MISSING":
        blockers.append("RECIPIENT_CONTACT_REFERENCE_MISSING")

    activation_blockers = list(blockers)
    if account_status != "ACTIVE":
        activation_blockers.append("ACCOUNT_NOT_ACTIVE")
    if tenant_link_status != "ACTIVE":
        activation_blockers.append("TENANT_LINK_NOT_ACTIVE")
    if external_reference_status != "ACTIVE":
        activation_blockers.append("EXTERNAL_REFERENCE_NOT_ACTIVE")
    activation_blockers.append("IDENTITY_ACCEPTANCE_NOT_RECORDED")
    if delivery_status not in {"INVITATION_DELIVERY_REQUESTED", "DELIVERED"}:
        activation_blockers.append("INVITATION_NOT_DELIVERED")

    return MembershipActivationReadinessItem(
        membership_id=membership.membership_id,
        subject=membership.subject,
        display_name=membership.display_name,
        role_family=membership.role_family,
        membership_status=membership_status,
        delivery_status=delivery_status or "DELIVERY_NOT_CONFIGURED",
        recipient_contact_status=membership.recipient_contact_status,
        delivery_readiness=(
            "READY_TO_REQUEST_DELIVERY" if not blockers else "BLOCKED"
        ),
        activation_readiness=(
            "READY_TO_ACTIVATE" if not activation_blockers else "BLOCKED"
        ),
        provisioning_readiness="WAITING_FOR_MEMBERSHIP_ACTIVATION",
        seat_assignment_status=membership.seat_assignment_status,
        auth_claim_status=membership.auth_claim_status,
        blockers=tuple(dict.fromkeys(activation_blockers)),
        next_action=_activation_next_action(activation_blockers),
    )


def _missing_required_role_families(
    memberships: tuple[MembershipPersonSummary, ...],
) -> tuple[str, ...]:
    usable_roles = {
        membership.role_family
        for membership in memberships
        if _normalise_status(membership.status) in {"INVITED", "ACTIVE"}
    }
    required = ("DISTRIBUTION_ADMIN", "CAMPAIGN_MANAGER")
    return tuple(role for role in required if role not in usable_roles)


def _activation_next_action(blockers: list[str]) -> str:
    if "RECIPIENT_CONTACT_REFERENCE_MISSING" in blockers:
        return "Add a safe work email contact reference before invite delivery can be requested."
    if "DELIVERY_PROVIDER_NOT_CONFIGURED" in blockers:
        return "Configure an approved invitation delivery provider before sending invites."
    if "ACCOUNT_NOT_ACTIVE" in blockers:
        return "Complete account activation before runtime membership activation."
    if "TENANT_LINK_NOT_ACTIVE" in blockers:
        return "Activate the customer workspace link before runtime access can operate."
    if "IDENTITY_ACCEPTANCE_NOT_RECORDED" in blockers:
        return "Wait for identity acceptance evidence before activation."
    return "Ready for activation once the activation command exists."


def _activation_command_next_action(activation_status: str) -> str:
    if activation_status == "MEMBERSHIP_ACTIVATED":
        return (
            "Membership lifecycle is active. Configure seats and auth claims only "
            "through their separate governed workflows."
        )
    if activation_status == "ACTIVATION_REJECTED_IDENTITY_NOT_ACCEPTED":
        return "Wait for identity acceptance evidence that matches the invited person."
    if activation_status == "ACTIVATION_REJECTED_ACCOUNT_NOT_ACTIVE":
        return "Activate the customer account foundation before runtime access can operate."
    if activation_status == "ACTIVATION_REJECTED_TENANT_LINK_NOT_ACTIVE":
        return "Activate the customer workspace link before runtime access can operate."
    if activation_status == "ACTIVATION_REJECTED_EXTERNAL_REFERENCE_NOT_ACTIVE":
        return "Activate the customer external reference before runtime access can operate."
    if activation_status == "ACTIVATION_REJECTED_DUPLICATE_ACTIVE_MEMBERSHIP":
        return "Review the existing active access for this person and responsibility."
    return "Resolve the membership status before activation can continue."


def _access_provisioning_next_action(provisioning_status: str) -> str:
    if provisioning_status in {
        "PROVISIONING_REQUEST_RECORDED",
        "PROVISIONING_REPLAYED",
    }:
        return (
            "Seat assignment is recorded. Configure login permissions and auth "
            "claims only through the separate identity-provider workflow."
        )
    if provisioning_status == "PROVISIONING_REJECTED_ACCOUNT_NOT_ACTIVE":
        return "Activate the customer account foundation before seat provisioning."
    if provisioning_status == "PROVISIONING_REJECTED_TENANT_LINK_NOT_ACTIVE":
        return "Activate the customer workspace link before seat provisioning."
    if provisioning_status == "PROVISIONING_REJECTED_EXTERNAL_REFERENCE_NOT_ACTIVE":
        return "Activate the customer external reference before seat provisioning."
    if provisioning_status == "PROVISIONING_REJECTED_MEMBERSHIP_NOT_ACTIVE":
        return "Record accepted access before assigning a seat."
    if provisioning_status == "PROVISIONING_REJECTED_SEAT_UNAVAILABLE":
        return "Create or free an available seat for this account and responsibility."
    if provisioning_status == "PROVISIONING_REJECTED_AUTH_PROVIDER_NOT_READY":
        return "Approve the identity provider workflow before auth claims can be propagated."
    return "Resolve the provisioning blockers before continuing."


def _build_login_completion_readiness(
    *,
    account_id: str,
    membership: Any,
    account_status: str,
    tenant_link_status: str | None,
    external_reference_status: str | None,
) -> LoginCompletionReadiness:
    metadata = _as_mapping(membership.get("metadata"))
    membership_status = _normalise_status(membership.get("status"))
    role_family = _optional_text(membership.get("role_family")) or "UNKNOWN"
    permission_profile = LOGIN_COMPLETION_PERMISSION_PROFILES.get(role_family)
    seat_assignment_status = (
        "SEAT_ASSIGNED"
        if _optional_text(membership.get("seat_id"))
        else "SEAT_NOT_ASSIGNED"
    )
    identity_provider_status = (
        _optional_text(metadata.get("identity_provider_status")) or "NOT_RECORDED"
    )
    auth_claim_status = (
        _optional_text(metadata.get("auth_claim_status"))
        or "AUTH_CLAIMS_NOT_PROPAGATED"
    )
    recorded_status = _optional_text(metadata.get("login_completion_status"))

    blockers: list[str] = []
    if _optional_text(account_status).upper() != "ACTIVE":
        blockers.append("LOGIN_COMPLETION_BLOCKED_ACCOUNT_NOT_ACTIVE")
    if _optional_text(tenant_link_status).upper() != "ACTIVE":
        blockers.append("LOGIN_COMPLETION_BLOCKED_TENANT_LINK_NOT_ACTIVE")
    if _optional_text(external_reference_status).upper() != "ACTIVE":
        blockers.append("LOGIN_COMPLETION_BLOCKED_EXTERNAL_REFERENCE_NOT_ACTIVE")
    if membership_status != "ACTIVE":
        blockers.append("LOGIN_COMPLETION_BLOCKED_MEMBERSHIP_NOT_ACTIVE")
    if not permission_profile:
        blockers.append("LOGIN_COMPLETION_BLOCKED_PERMISSION_PROFILE_MISSING")
    if seat_assignment_status != "SEAT_ASSIGNED":
        blockers.append("LOGIN_COMPLETION_BLOCKED_SEAT_NOT_ASSIGNED")

    if recorded_status in {"LOGIN_COMPLETION_RECORDED", "LOGIN_COMPLETION_NOT_REQUIRED"}:
        login_status = recorded_status
    elif blockers:
        login_status = blockers[0]
    else:
        login_status = "LOGIN_COMPLETION_READY"

    next_actions = tuple(
        _login_completion_next_action(blocker) for blocker in blockers[:2]
    )
    if not next_actions:
        next_actions = (_login_completion_next_action(login_status),)

    return LoginCompletionReadiness(
        login_completion_status=login_status,
        account_id=account_id,
        membership_id=_optional_text(membership.get("membership_id")) or "",
        subject=_optional_text(membership.get("user_subject")) or None,
        display_name=_optional_text(membership.get("user_display_name")) or None,
        role_family=role_family,
        permission_profile=permission_profile,
        membership_status=membership_status,
        seat_assignment_status=seat_assignment_status,
        identity_provider_status=identity_provider_status,
        auth_claim_status=auth_claim_status,
        blockers=tuple(blockers),
        next_actions=next_actions,
    )


def _login_completion_next_action(login_status: str) -> str:
    if login_status == "LOGIN_COMPLETION_RECORDED":
        return (
            "Login completion evidence is recorded. Real credentials and auth "
            "claims remain in the governed identity-provider workflow."
        )
    if login_status == "LOGIN_COMPLETION_NOT_REQUIRED":
        return "No platform login is required for this person right now."
    if login_status == "LOGIN_COMPLETION_READY":
        return "Record login completion intent or mark platform login as not required."
    if login_status == "LOGIN_COMPLETION_BLOCKED_ACCOUNT_NOT_ACTIVE":
        return "Activate the customer account foundation before login setup."
    if login_status == "LOGIN_COMPLETION_BLOCKED_TENANT_LINK_NOT_ACTIVE":
        return "Activate the customer workspace link before login setup."
    if login_status == "LOGIN_COMPLETION_BLOCKED_EXTERNAL_REFERENCE_NOT_ACTIVE":
        return "Activate the customer external reference before login setup."
    if login_status == "LOGIN_COMPLETION_BLOCKED_MEMBERSHIP_NOT_ACTIVE":
        return "Confirm customer access before login setup."
    if login_status == "LOGIN_COMPLETION_BLOCKED_SEAT_NOT_ASSIGNED":
        return "Assign a platform seat before recording platform login completion."
    if login_status == "LOGIN_COMPLETION_BLOCKED_AUTH_PROVIDER_NOT_APPROVED":
        return "Record approved identity-provider evidence before login completion."
    if login_status == "LOGIN_COMPLETION_BLOCKED_PERMISSION_PROFILE_MISSING":
        return "Map this responsibility to a governed login permission profile."
    if login_status == "LOGIN_COMPLETION_REPLAYED":
        return "The same login completion request was replayed safely."
    return "Resolve login completion blockers before continuing."


def _identity_access_status(membership_status: str) -> str:
    if membership_status == "ACTIVE":
        return "CUSTOMER_ACCESS_ACCEPTED"
    if membership_status == "INVITED":
        return "CUSTOMER_ACCESS_NAMED"
    if membership_status == "DISABLED":
        return "CUSTOMER_ACCESS_DISABLED"
    if membership_status == "SUSPENDED":
        return "CUSTOMER_ACCESS_SUSPENDED"
    return "CUSTOMER_ACCESS_NOT_READY"


def _identity_login_status(
    *,
    access_status: str,
    login_completion_status: str | None,
    login_intent: str,
    seat_assignment_status: str,
    identity_provider_status: str,
    auth_claim_status: str,
    revocation_status: str,
    blockers: list[str],
) -> str:
    if revocation_status in {"REVOKED", "REVOCATION_RECORDED"}:
        return "ACCESS_REVOKED"
    if access_status != "CUSTOMER_ACCESS_ACCEPTED":
        return "WAITING_FOR_CUSTOMER_ACCESS"
    if login_intent == "LOGIN_NOT_REQUIRED" or login_completion_status == "LOGIN_COMPLETION_NOT_REQUIRED":
        return "PLATFORM_LOGIN_NOT_REQUIRED"
    if "ACCOUNT_NOT_ACTIVE" in blockers:
        return "WAITING_FOR_ACTIVE_CUSTOMER"
    if "TENANT_LINK_NOT_ACTIVE" in blockers or "EXTERNAL_REFERENCE_NOT_ACTIVE" in blockers:
        return "WAITING_FOR_ACTIVE_CUSTOMER_SCOPE"
    if seat_assignment_status != "SEAT_ASSIGNED":
        return "WAITING_FOR_PLATFORM_SEAT"
    if identity_provider_status in {"PROVIDER_EVIDENCE_STALE", "STALE_PROVIDER_EVIDENCE"}:
        return "PROVIDER_EVIDENCE_STALE"
    if auth_claim_status in {"AUTH_CLAIM_MISMATCH", "CLAIM_MISMATCH"}:
        return "AUTH_CLAIM_REVIEW_REQUIRED"
    if identity_provider_status not in {"APPROVED_EVIDENCE_RECORDED", "EXTERNAL_IDP_MANAGED"}:
        return "WAITING_FOR_IDENTITY_PROVIDER_EVIDENCE"
    if auth_claim_status in {"AUTH_CLAIMS_PROPAGATED", "AUTH_CLAIMS_VERIFIED"}:
        return "LOGIN_RECONCILED"
    return "READY_FOR_AUTH_CLAIM_RECONCILIATION"


def _identity_login_next_action(login_status: str) -> str:
    actions = {
        "ACCESS_REVOKED": "This person's customer access has been revoked. Add a new person if access is needed again.",
        "WAITING_FOR_CUSTOMER_ACCESS": "Review and accept this person's customer access before thinking about login.",
        "PLATFORM_LOGIN_NOT_REQUIRED": "No platform login is needed. Keep this person confirmed for customer work.",
        "WAITING_FOR_ACTIVE_CUSTOMER": "Activate the customer account foundation before login setup.",
        "WAITING_FOR_ACTIVE_CUSTOMER_SCOPE": "Activate the customer workspace link and external reference before login setup.",
        "WAITING_FOR_PLATFORM_SEAT": "Only assign a platform login seat if this person must sign in to Amplifi.",
        "PROVIDER_EVIDENCE_STALE": "Review the identity provider evidence in Integrations before login permissions are trusted.",
        "AUTH_CLAIM_REVIEW_REQUIRED": "Review the permission mapping because the identity provider claim does not match this responsibility.",
        "WAITING_FOR_IDENTITY_PROVIDER_EVIDENCE": "Record approved identity provider evidence in Integrations before login permissions are trusted.",
        "LOGIN_RECONCILED": "Login evidence is reconciled. Keep credentials and auth claims governed outside People and Access.",
        "READY_FOR_AUTH_CLAIM_RECONCILIATION": "Review auth-claim propagation evidence in the governed identity workflow.",
    }
    return actions.get(login_status, "Review the person's login setup evidence before continuing.")


def _identity_login_steps(
    *,
    access_status: str,
    login_status: str,
    seat_assignment_status: str,
    identity_provider_status: str,
    auth_claim_status: str,
) -> tuple[dict[str, str], ...]:
    access_done = access_status == "CUSTOMER_ACCESS_ACCEPTED"
    login_not_required = login_status == "PLATFORM_LOGIN_NOT_REQUIRED"
    seat_done = seat_assignment_status == "SEAT_ASSIGNED" or login_not_required
    provider_done = identity_provider_status in {"APPROVED_EVIDENCE_RECORDED", "EXTERNAL_IDP_MANAGED"} or login_not_required
    claims_done = auth_claim_status in {"AUTH_CLAIMS_PROPAGATED", "AUTH_CLAIMS_VERIFIED"} or login_not_required

    return (
        {
            "label": "Customer access",
            "status": "DONE" if access_done else "WAITING",
            "description": "Person is confirmed for this customer." if access_done else "Confirm the person first.",
        },
        {
            "label": "Platform login seat",
            "status": "SKIPPED" if login_not_required else ("DONE" if seat_done else "OPTIONAL"),
            "description": "Needed only when this person signs in to Amplifi.",
        },
        {
            "label": "Identity provider",
            "status": "SKIPPED" if login_not_required else ("DONE" if provider_done else "WAITING"),
            "description": "Evidence comes from the governed Integrations/identity workflow.",
        },
        {
            "label": "Login permissions",
            "status": "SKIPPED" if login_not_required else ("DONE" if claims_done else "WAITING"),
            "description": "Auth claims stay outside People and Access.",
        },
    )


async def _insert_activation_audit_event(
    conn: Any,
    *,
    account_id: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    membership_id: str,
    tenant_code: str,
    event_status: str,
    actor_ref: str,
    actor_role: str,
    previous_status: str,
    next_status: str,
    reason_code: str,
    correlation_id: str,
    idempotency_key_hash: str,
    audit_evidence: dict[str, Any],
    redactions: list[str],
) -> Any:
    return await conn.fetchrow(
        """
        INSERT INTO platform_account_audit_events (
            account_id,
            account_tenant_id,
            external_ref_id,
            membership_id,
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
            $1, $2, $3, $4, $5, $6, $7, $8, $9,
            $10, $11, $12, $13, $14,
            $15::jsonb, $16::jsonb
        )
        RETURNING account_audit_event_id
        """,
        account_id,
        account_tenant_id,
        external_ref_id,
        membership_id,
        tenant_code,
        MEMBERSHIP_ACTIVATION_EVENT,
        event_status,
        actor_ref,
        actor_role,
        previous_status,
        next_status,
        reason_code,
        correlation_id,
        idempotency_key_hash,
        _jsonb(audit_evidence),
        _jsonb(redactions),
    )


async def _insert_access_provisioning_audit_event(
    conn: Any,
    *,
    account_id: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    membership_id: str,
    tenant_code: str,
    event_status: str,
    actor_ref: str,
    actor_role: str,
    previous_status: str,
    next_status: str,
    reason_code: str,
    correlation_id: str,
    idempotency_key_hash: str,
    audit_evidence: dict[str, Any],
    redactions: list[str],
) -> Any:
    return await conn.fetchrow(
        """
        INSERT INTO platform_account_audit_events (
            account_id,
            account_tenant_id,
            external_ref_id,
            membership_id,
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
            $1, $2, $3, $4, $5, $6, $7, $8, $9,
            $10, $11, $12, $13, $14,
            $15::jsonb, $16::jsonb
        )
        RETURNING account_audit_event_id
        """,
        account_id,
        account_tenant_id,
        external_ref_id,
        membership_id,
        tenant_code,
        MEMBERSHIP_ACCESS_PROVISIONING_EVENT,
        event_status,
        actor_ref,
        actor_role,
        previous_status,
        next_status,
        reason_code,
        correlation_id,
        idempotency_key_hash,
        _jsonb(audit_evidence),
        _jsonb(redactions),
    )


async def _insert_login_completion_audit_event(
    conn: Any,
    *,
    account_id: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    membership_id: str,
    tenant_code: str,
    event_status: str,
    actor_ref: str,
    actor_role: str,
    previous_status: str,
    next_status: str,
    reason_code: str,
    correlation_id: str,
    idempotency_key_hash: str,
    audit_evidence: dict[str, Any],
    redactions: list[str],
) -> Any:
    return await conn.fetchrow(
        """
        INSERT INTO platform_account_audit_events (
            account_id,
            account_tenant_id,
            external_ref_id,
            membership_id,
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
            $1, $2, $3, $4, $5, $6, $7, $8, $9,
            $10, $11, $12, $13, $14,
            $15::jsonb, $16::jsonb
        )
        RETURNING account_audit_event_id
        """,
        account_id,
        account_tenant_id,
        external_ref_id,
        membership_id,
        tenant_code,
        MEMBERSHIP_LOGIN_COMPLETION_EVENT,
        event_status,
        actor_ref,
        actor_role,
        previous_status,
        next_status,
        reason_code,
        correlation_id,
        idempotency_key_hash,
        _jsonb(audit_evidence),
        _jsonb(redactions),
    )


def _normalise_status(value: Any) -> str:
    status = _optional_text(value).upper()
    return status if status in MEMBERSHIP_STATUSES else "DISABLED"


def _required_account_id(value: Any) -> str:
    text = _optional_text(value)
    if not text:
        raise MembershipInvitationUnsafeScope("Account reference is required.")
    return text


def _required_text(value: Any) -> str:
    text = _optional_text(value)
    if not text:
        raise ValueError("Required text value is missing.")
    return text


def _optional_text(value: Any) -> str:
    return str(value or "").strip()


def _required_choice(value: Any, allowed: set[str] | frozenset[str]) -> str:
    text = _required_text(value).upper()
    if text not in allowed:
        raise MembershipInvitationValidationError(
            f"Value must be one of: {', '.join(sorted(allowed))}."
        )
    return text


def _jsonb(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _approved_invitation_delivery_provider(
    *,
    channel: str,
    provider_ref: str,
) -> dict[str, Any]:
    channel_code = _required_choice(channel, {"EMAIL"})
    requested_provider_ref = _required_text(provider_ref)
    readiness = get_channel_readiness()
    item = next(
        (
            item
            for item in readiness.get("items", [])
            if isinstance(item, dict)
            and _optional_text(item.get("channel_code")).upper() == channel_code
        ),
        None,
    )
    if not item:
        return {
            "ready": False,
            "next_action": (
                f"Configure {channel_code} as an approved Referral SaaS invite "
                "provider before sending invites."
            ),
        }

    configured_ref = _optional_text(item.get("provider_ref"))
    if not item.get("provider_configured"):
        return {
            "ready": False,
            "next_action": (
                "Configure Email provider URL and signing secret before sending "
                "invite emails."
            ),
        }
    if configured_ref and configured_ref != requested_provider_ref:
        return {
            "ready": False,
            "next_action": (
                "Use the approved Email provider reference configured for this "
                "customer before sending invites."
            ),
        }
    if not item.get("provider_approved") or not item.get(
        "approved_for_referral_saas"
    ):
        return {
            "ready": False,
            "next_action": (
                "Approve the Email provider for Referral SaaS invite delivery "
                "before sending invites."
            ),
        }
    return {
        "ready": True,
        "next_action": "Approved Email provider is ready for invitation delivery.",
    }


def _membership_invitation_message(*, template_ref: str, role_family: str) -> str:
    safe_template_ref = _required_text(template_ref)
    safe_role_family = _required_text(role_family).replace("_", " ").title()
    return (
        "You have been invited to manage Referral SaaS "
        f"{safe_role_family} access. Template: {safe_template_ref}."
    )


def _hash_acceptance_token(token: str) -> str:
    safe_token = _required_text(token)
    return hashlib.sha256(safe_token.encode("utf-8")).hexdigest()


def _normalise_acceptance_token_status(value: Any) -> str:
    status = _optional_text(value).upper()
    return status if status in MEMBERSHIP_ACCEPTANCE_TOKEN_STATUSES else "REVOKED"


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


UNSAFE_PAYLOAD_KEYS: Final = frozenset(
    {
        "tenant_code",
        "tenantCode",
        "internal_tenant_code",
        "internalTenantCode",
        "email",
        "raw_email",
        "rawEmail",
        "password",
        "secret",
        "token",
        "credential",
        "credentials",
        "auth_claim",
        "authClaims",
        "seat_id",
        "seatId",
        "send_invite",
        "sendInvite",
        "delivery",
        "activate",
        "go_live",
        "goLive",
        "campaign_activation",
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
        "sponsor_billing",
        "sponsorBilling",
    }
)


def _reject_unsafe_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in UNSAFE_PAYLOAD_KEYS:
                raise MembershipInvitationUnsafePayload(
                    "Membership invitation payload includes unsafe live-action fields."
                )
            _reject_unsafe_payload(child)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)


UNSAFE_DELIVERY_PAYLOAD_KEYS: Final = frozenset(
    {
        "tenant_code",
        "tenantCode",
        "internal_tenant_code",
        "internalTenantCode",
        "email",
        "raw_email",
        "rawEmail",
        "password",
        "secret",
        "token",
        "credential",
        "credentials",
        "auth_claim",
        "authClaims",
        "seat_id",
        "seatId",
        "activate",
        "go_live",
        "goLive",
        "campaign_activation",
        "campaignActivation",
        "webhook_secret",
        "webhookSecret",
        "reward",
        "funding",
        "fulfilment",
        "settlement",
        "commission",
        "wallet",
        "invoice",
        "payout",
        "sponsor_billing",
        "sponsorBilling",
    }
)


def _reject_unsafe_delivery_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in UNSAFE_DELIVERY_PAYLOAD_KEYS:
                raise MembershipInvitationUnsafePayload(
                    "Invitation delivery payload includes unsafe live-action fields."
                )
            _reject_unsafe_delivery_payload(child)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_delivery_payload(item)


UNSAFE_ACTIVATION_PAYLOAD_KEYS: Final = frozenset(
    {
        "tenant_code",
        "tenantCode",
        "internal_tenant_code",
        "internalTenantCode",
        "email",
        "raw_email",
        "rawEmail",
        "password",
        "secret",
        "token",
        "credential",
        "credentials",
        "auth_claim",
        "authClaims",
        "seat_id",
        "seatId",
        "send_invite",
        "sendInvite",
        "delivery",
        "go_live",
        "goLive",
        "campaign_activation",
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
        "sponsor_billing",
        "sponsorBilling",
    }
)


def _reject_unsafe_activation_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in UNSAFE_ACTIVATION_PAYLOAD_KEYS:
                raise MembershipInvitationUnsafePayload(
                    "Membership activation payload includes unsafe live-action fields."
                )
            _reject_unsafe_activation_payload(child)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_activation_payload(item)


UNSAFE_ACCESS_PROVISIONING_PAYLOAD_KEYS: Final = frozenset(
    {
        "tenant_code",
        "tenantCode",
        "internal_tenant_code",
        "internalTenantCode",
        "email",
        "raw_email",
        "rawEmail",
        "password",
        "secret",
        "token",
        "credential",
        "credentials",
        "auth_claim",
        "authClaims",
        "seat_id",
        "seatId",
        "send_invite",
        "sendInvite",
        "delivery",
        "go_live",
        "goLive",
        "campaign_activation",
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
        "sponsor_billing",
        "sponsorBilling",
    }
)


def _reject_unsafe_access_provisioning_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in UNSAFE_ACCESS_PROVISIONING_PAYLOAD_KEYS:
                raise MembershipInvitationUnsafePayload(
                    "Access provisioning payload includes unsafe live-action fields."
                )
            _reject_unsafe_access_provisioning_payload(child)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_access_provisioning_payload(item)


UNSAFE_LOGIN_COMPLETION_PAYLOAD_KEYS: Final = frozenset(
    {
        "tenant_code",
        "tenantCode",
        "internal_tenant_code",
        "internalTenantCode",
        "email",
        "raw_email",
        "rawEmail",
        "password",
        "secret",
        "token",
        "credential",
        "credentials",
        "auth_claim",
        "authClaims",
        "claimMap",
        "raw_claims",
        "rawClaims",
        "provider_payload",
        "providerPayload",
        "provider_secret",
        "providerSecret",
        "send_invite",
        "sendInvite",
        "delivery",
        "go_live",
        "goLive",
        "campaign_activation",
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
        "sponsor_billing",
        "sponsorBilling",
    }
)


def _reject_unsafe_login_completion_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in UNSAFE_LOGIN_COMPLETION_PAYLOAD_KEYS:
                raise MembershipInvitationUnsafePayload(
                    "Login completion payload includes unsafe live-action fields."
                )
            _reject_unsafe_login_completion_payload(child)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_login_completion_payload(item)
