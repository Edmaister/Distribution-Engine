from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from utils.db import db_connection

MEMBERSHIP_STATUSES = ("INVITED", "ACTIVE", "SUSPENDED", "DISABLED", "ARCHIVED")


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
class ReferralSaasAccountMembershipPosture:
    account_id: str
    total_memberships: int
    invited_count: int
    active_count: int
    suspended_count: int
    disabled_count: int
    archived_count: int
    role_families: tuple[MembershipRoleFamilySummary, ...]
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
                membership_id,
                role_family,
                permission_set,
                status,
                CASE
                    WHEN user_id IS NOT NULL THEN 'USER'
                    WHEN client_id IS NOT NULL THEN 'CLIENT'
                    ELSE 'UNKNOWN'
                END AS actor_type,
                CASE
                    WHEN $3::text <> '' AND client_id = $3 THEN TRUE
                    WHEN $4::text <> '' AND user_id::text = $4 THEN TRUE
                    ELSE FALSE
                END AS is_current_actor
            FROM platform_memberships
            WHERE account_id = $1
              AND (tenant_code = $2 OR tenant_code IS NULL)
              AND status <> 'ARCHIVED'
            ORDER BY
                CASE status
                    WHEN 'ACTIVE' THEN 0
                    WHEN 'INVITED' THEN 1
                    WHEN 'SUSPENDED' THEN 2
                    WHEN 'DISABLED' THEN 3
                    ELSE 4
                END,
                updated_at DESC
            """,
            safe_account_id,
            safe_tenant_code,
            safe_actor_client_id,
            safe_actor_ref,
        )

    safe_rows = [dict(row) for row in rows]
    counts = _status_counts(safe_rows)
    role_families = _role_family_summaries(safe_rows)
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


def _normalise_status(value: Any) -> str:
    status = _optional_text(value).upper()
    return status if status in MEMBERSHIP_STATUSES else "DISABLED"


def _required_text(value: Any) -> str:
    text = _optional_text(value)
    if not text:
        raise ValueError("account_id and tenant_code are required.")
    return text


def _optional_text(value: Any) -> str:
    return str(value or "").strip()
