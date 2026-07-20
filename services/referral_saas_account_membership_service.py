from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Final

from utils.db import db_connection

MEMBERSHIP_STATUSES = ("INVITED", "ACTIVE", "SUSPENDED", "DISABLED", "ARCHIVED")
MEMBERSHIP_INVITATION_EVENT: Final = "REFERRAL_SAAS_MEMBERSHIP_INVITATION_INTENT"
EVENT_RECORDED: Final = "RECORDED"
EVENT_DUPLICATE: Final = "DUPLICATE"
USER_ACTOR: Final = "USER"
CLIENT_ACTOR: Final = "CLIENT"
PRIMARY_TENANT_SCOPE: Final = "PRIMARY_ACCOUNT_TENANT"

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
    actor_type: str
    subject: str | None
    display_name: str | None
    role_family: str
    permission_set: str
    status: str
    delivery_status: str

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "actorType": self.actor_type,
            "subject": self.subject,
            "displayName": self.display_name,
            "roleFamily": self.role_family,
            "permissionSet": self.permission_set,
            "status": self.status,
            "deliveryStatus": self.delivery_status,
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
                platform_memberships.client_id AS client_id,
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
            )
        )
    return summaries


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
