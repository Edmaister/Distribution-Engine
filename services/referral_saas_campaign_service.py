from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from utils.db import db_connection


MAX_CAMPAIGN_LIST_LIMIT = 100
CAMPAIGN_SETUP_CREATE_EVENT = "CAMPAIGN_SETUP_DRAFT_RECORDED"
CAMPAIGN_SETUP_RECORDED = "RECORDED"
CAMPAIGN_SETUP_REPLAYED = "REPLAYED"
CAMPAIGN_SETUP_GUARDRAILS = [
    "NO_TENANT_CODE_EXPOSURE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_LINK_GENERATION",
    "NO_VALIDATION_TRACK_CREATED",
    "NO_POLICY_WRITE",
    "NO_WEBHOOK_DELIVERY",
    "NO_MONEY_MOVEMENT",
]
CAMPAIGN_SETUP_REDACTIONS = [
    "internal_tenant_identifier",
    "idempotency_key_hash",
    "payload_hash",
]


class ReferralSaasCampaignCommandError(Exception):
    safe_code = "CAMPAIGN_COMMAND_ERROR"


class CampaignSetupValidationError(ReferralSaasCampaignCommandError):
    safe_code = "VALIDATION_ERROR"


class CampaignSetupAccountNotReady(ReferralSaasCampaignCommandError):
    safe_code = "ACCOUNT_NOT_READY_FOR_CAMPAIGN_SETUP"


class CampaignSetupDuplicate(ReferralSaasCampaignCommandError):
    safe_code = "CAMPAIGN_SETUP_ALREADY_EXISTS"


class CampaignSetupIdempotencyConflict(ReferralSaasCampaignCommandError):
    safe_code = "IDEMPOTENCY_CONFLICT"


@dataclass(frozen=True)
class ReferralSaasCampaignSummary:
    campaign_code: str
    name: str
    segment: str
    status: str
    lifecycle: str
    starts_at: str | None
    ends_at: str | None
    max_uses: int | None
    uses_count: int
    policy_status: str
    created_at: str | None
    updated_at: str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "campaignCode": self.campaign_code,
            "name": self.name,
            "segment": self.segment,
            "status": self.status,
            "lifecycle": self.lifecycle,
            "startsAt": self.starts_at,
            "endsAt": self.ends_at,
            "maxUses": self.max_uses,
            "usesCount": self.uses_count,
            "policyStatus": self.policy_status,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }


@dataclass(frozen=True)
class ReferralSaasCampaignSetupResult:
    command_status: str
    account_id: str
    campaign_code: str
    name: str
    segment: str
    setup_status: str
    is_active: bool
    starts_at: str | None
    ends_at: str | None
    max_uses: int | None
    idempotency_status: str
    audit_event_id: str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "accountRef": self.account_id,
            "campaign": {
                "campaignRef": self.campaign_code,
                "campaignCode": self.campaign_code,
                "name": self.name,
                "segment": self.segment,
                "setupStatus": self.setup_status,
                "isActive": self.is_active,
                "startsAt": self.starts_at,
                "endsAt": self.ends_at,
                "maxUses": self.max_uses,
            },
            "idempotency": {"status": self.idempotency_status},
            "audit": {"accountAuditEventId": self.audit_event_id},
            "nextActions": [
                "Complete policy and attribution settings",
                "Run campaign readiness",
                "Review before activation",
            ],
            "guardrails": list(CAMPAIGN_SETUP_GUARDRAILS),
            "redactions": list(CAMPAIGN_SETUP_REDACTIONS),
        }


def _as_iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    return None


def _as_aware_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    return None


def _campaign_lifecycle(*, is_active: bool, starts_at: Any, ends_at: Any) -> str:
    now = datetime.now(timezone.utc)
    safe_starts_at = _as_aware_utc(starts_at)
    safe_ends_at = _as_aware_utc(ends_at)
    if not is_active:
        return "PAUSED"
    if safe_starts_at and safe_starts_at > now:
        return "SCHEDULED"
    if safe_ends_at and safe_ends_at < now:
        return "EXPIRED"
    return "ACTIVE"


def _campaign_status(*, lifecycle: str, policy_status: str) -> str:
    if lifecycle in {"PAUSED", "EXPIRED"}:
        return lifecycle
    if policy_status != "ACTIVE_POLICY":
        return "NEEDS_POLICY"
    return lifecycle


def _required_text(value: Any, field_name: str) -> str:
    safe_value = str(value or "").strip()
    if not safe_value:
        raise CampaignSetupValidationError(f"{field_name} is required.")
    return safe_value


def _optional_text(value: Any) -> str:
    return str(value or "").strip()


def _jsonb(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _generate_campaign_code(tenant_code: str, segment: str, name: str) -> str:
    tenant = (_optional_text(tenant_code) or "GEN").upper().replace(" ", "-")
    safe_segment = (_optional_text(segment) or "GENERAL").upper().replace(" ", "-")
    safe_name = (_optional_text(name) or "CAMPAIGN").upper().replace(" ", "-")
    token = str(uuid4())[:8].upper()
    return f"{tenant}-{safe_segment}-{safe_name[:30]}-{token}"


def _to_campaign_summary(row: dict[str, Any]) -> ReferralSaasCampaignSummary:
    is_active = bool(row.get("is_active"))
    lifecycle = _campaign_lifecycle(
        is_active=is_active,
        starts_at=row.get("starts_at"),
        ends_at=row.get("ends_at"),
    )
    active_policy_count = int(row.get("active_policy_count") or 0)
    policy_status = "ACTIVE_POLICY" if active_policy_count > 0 else "NO_ACTIVE_POLICY"
    return ReferralSaasCampaignSummary(
        campaign_code=str(row["campaign_code"]),
        name=str(row["name"]),
        segment=str(row["segment"]),
        status=_campaign_status(lifecycle=lifecycle, policy_status=policy_status),
        lifecycle=lifecycle,
        starts_at=_as_iso(row.get("starts_at")),
        ends_at=_as_iso(row.get("ends_at")),
        max_uses=int(row["max_uses"]) if row.get("max_uses") is not None else None,
        uses_count=int(row.get("uses_count") or 0),
        policy_status=policy_status,
        created_at=_as_iso(row.get("created_at")),
        updated_at=_as_iso(row.get("updated_at")),
    )


async def create_referral_saas_account_campaign_setup(
    *,
    account_id: str,
    tenant_code: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    account_status: str,
    tenant_link_status: str,
    external_reference_status: str,
    name: str,
    segment: str,
    starts_at: datetime | None = None,
    ends_at: datetime | None = None,
    max_uses: int | None = None,
    reason_code: str,
    correlation_id: str,
    idempotency_key_hash: str,
    command_payload_hash: str,
    command_payload: dict[str, Any] | None = None,
    command_actor_ref: str | None = None,
    command_actor_role: str | None = None,
) -> ReferralSaasCampaignSetupResult:
    safe_account_id = _required_text(account_id, "account_id")
    safe_tenant_code = _required_text(tenant_code, "tenant_code")
    safe_name = _required_text(name, "campaign.name")
    safe_segment = _required_text(segment, "campaign.segment")
    safe_reason_code = _required_text(reason_code, "reason_code").upper()
    safe_correlation_id = _required_text(correlation_id, "correlation_id")
    safe_idempotency_hash = _required_text(
        idempotency_key_hash,
        "idempotency_key_hash",
    )
    safe_payload_hash = _required_text(command_payload_hash, "command_payload_hash")
    safe_account_status = _optional_text(account_status).upper()
    safe_tenant_link_status = _optional_text(tenant_link_status).upper()
    safe_external_reference_status = _optional_text(external_reference_status).upper()

    if safe_account_status not in {"PENDING_ONBOARDING", "ACTIVE"}:
        raise CampaignSetupAccountNotReady(
            "Account must exist before campaign setup can start."
        )
    if safe_tenant_link_status not in {"PENDING_SETUP", "ACTIVE"}:
        raise CampaignSetupAccountNotReady(
            "Account tenant link must exist before campaign setup can start."
        )
    if safe_external_reference_status not in {"ACTIVE"}:
        raise CampaignSetupAccountNotReady(
            "Selected customer reference must be active before campaign setup can start."
        )
    if starts_at and ends_at and ends_at < starts_at:
        raise CampaignSetupValidationError("campaign.endsAt must be after startsAt.")
    if max_uses is not None and int(max_uses) < 1:
        raise CampaignSetupValidationError("campaign.maxUses must be at least 1.")

    async with db_connection() as conn:
        existing_audit = await conn.fetchrow(
            """
            SELECT
                account_audit_event_id,
                event_status,
                evidence_summary
            FROM platform_account_audit_events
            WHERE account_id = $1
              AND event_type = $2
              AND idempotency_key_hash = $3
            ORDER BY created_at DESC
            LIMIT 1
            """,
            safe_account_id,
            CAMPAIGN_SETUP_CREATE_EVENT,
            safe_idempotency_hash,
        )
        if existing_audit:
            evidence = existing_audit.get("evidence_summary") or {}
            if isinstance(evidence, str):
                evidence = json.loads(evidence)
            if _optional_text(evidence.get("command_payload_hash")) != safe_payload_hash:
                raise CampaignSetupIdempotencyConflict(
                    "Idempotency key was reused with different campaign setup content."
                )
            return ReferralSaasCampaignSetupResult(
                command_status="CAMPAIGN_SETUP_DRAFT_REPLAYED",
                account_id=safe_account_id,
                campaign_code=_optional_text(evidence.get("campaign_code")),
                name=_optional_text(evidence.get("name")) or safe_name,
                segment=_optional_text(evidence.get("segment")) or safe_segment,
                setup_status=_optional_text(evidence.get("setup_status")) or "DRAFT",
                is_active=False,
                starts_at=_optional_text(evidence.get("starts_at")) or None,
                ends_at=_optional_text(evidence.get("ends_at")) or None,
                max_uses=(
                    int(evidence["max_uses"])
                    if evidence.get("max_uses") is not None
                    else None
                ),
                idempotency_status=CAMPAIGN_SETUP_REPLAYED,
                audit_event_id=_optional_text(
                    existing_audit.get("account_audit_event_id")
                )
                or None,
            )

        duplicate_campaign = await conn.fetchrow(
            """
            SELECT campaign_code
            FROM marketing_campaigns
            WHERE UPPER(tenant_code) = UPPER($1)
              AND UPPER(name) = UPPER($2)
              AND UPPER(segment) = UPPER($3)
            LIMIT 1
            """,
            safe_tenant_code,
            safe_name,
            safe_segment,
        )
        if duplicate_campaign:
            raise CampaignSetupDuplicate(
                "A campaign setup already exists for this selected customer, name, and segment."
            )

        campaign_code = _generate_campaign_code(safe_tenant_code, safe_segment, safe_name)
        attributes = {
            "source": "TASK-256",
            "referral_saas_setup_status": "DRAFT",
            "account_id": safe_account_id,
            "command_payload_hash": safe_payload_hash,
            "no_campaign_activation_confirmed": True,
            "no_link_generation_confirmed": True,
            "no_validation_track_created_confirmed": True,
            "no_policy_write_confirmed": True,
            "no_money_movement_confirmed": True,
        }

        async with conn.transaction():
            campaign = await conn.fetchrow(
                """
                INSERT INTO marketing_campaigns (
                    campaign_code,
                    tenant_code,
                    segment,
                    name,
                    is_active,
                    starts_at,
                    ends_at,
                    max_uses,
                    attributes
                )
                VALUES ($1, $2, $3, $4, FALSE, $5, $6, $7, $8::jsonb)
                RETURNING
                    campaign_code,
                    name,
                    segment,
                    is_active,
                    starts_at,
                    ends_at,
                    max_uses
                """,
                campaign_code,
                safe_tenant_code,
                safe_segment,
                safe_name,
                starts_at,
                ends_at,
                max_uses,
                _jsonb(attributes),
            )
            audit_evidence = {
                "campaign_code": str(campaign["campaign_code"]),
                "name": str(campaign["name"]),
                "segment": str(campaign["segment"]),
                "setup_status": "DRAFT",
                "is_active": bool(campaign["is_active"]),
                "starts_at": _as_iso(campaign.get("starts_at")),
                "ends_at": _as_iso(campaign.get("ends_at")),
                "max_uses": (
                    int(campaign["max_uses"])
                    if campaign.get("max_uses") is not None
                    else None
                ),
                "command_payload_hash": safe_payload_hash,
                "no_tenant_code_exposure_confirmed": True,
                "no_campaign_activation_confirmed": True,
                "no_link_generation_confirmed": True,
                "no_validation_track_created_confirmed": True,
                "no_policy_write_confirmed": True,
                "no_webhook_delivery_confirmed": True,
                "no_money_movement_confirmed": True,
            }
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
                    NULL, 'DRAFT', $9, $10, $11, $12::jsonb, $13::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                _optional_text(account_tenant_id) or None,
                _optional_text(external_ref_id) or None,
                safe_tenant_code,
                CAMPAIGN_SETUP_CREATE_EVENT,
                CAMPAIGN_SETUP_RECORDED,
                _optional_text(command_actor_ref)
                or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                _optional_text(command_actor_role) or "UNKNOWN",
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(audit_evidence),
                _jsonb(CAMPAIGN_SETUP_REDACTIONS),
            )

    return ReferralSaasCampaignSetupResult(
        command_status="CAMPAIGN_SETUP_DRAFT_RECORDED",
        account_id=safe_account_id,
        campaign_code=str(campaign["campaign_code"]),
        name=str(campaign["name"]),
        segment=str(campaign["segment"]),
        setup_status="DRAFT",
        is_active=bool(campaign["is_active"]),
        starts_at=_as_iso(campaign.get("starts_at")),
        ends_at=_as_iso(campaign.get("ends_at")),
        max_uses=(
            int(campaign["max_uses"])
            if campaign.get("max_uses") is not None
            else None
        ),
        idempotency_status=CAMPAIGN_SETUP_RECORDED,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
    )


async def list_referral_saas_account_campaigns(
    *,
    tenant_code: str,
    limit: int = 50,
) -> list[ReferralSaasCampaignSummary]:
    safe_tenant_code = str(tenant_code or "").strip()
    if not safe_tenant_code:
        return []
    safe_limit = max(1, min(int(limit or 50), MAX_CAMPAIGN_LIST_LIMIT))
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                campaign.campaign_code,
                campaign.name,
                campaign.segment,
                campaign.is_active,
                campaign.starts_at,
                campaign.ends_at,
                campaign.max_uses,
                campaign.uses_count,
                campaign.created_at,
                campaign.updated_at,
                COUNT(policy.campaign_code) FILTER (WHERE policy.is_active = TRUE)
                    AS active_policy_count
            FROM marketing_campaigns campaign
            LEFT JOIN marketing_campaign_policies policy
                ON UPPER(policy.campaign_code) = UPPER(campaign.campaign_code)
               AND (
                    policy.tenant_code IS NULL
                    OR UPPER(policy.tenant_code) = UPPER($1)
               )
            WHERE UPPER(campaign.tenant_code) = UPPER($1)
            GROUP BY
                campaign.campaign_code,
                campaign.name,
                campaign.segment,
                campaign.is_active,
                campaign.starts_at,
                campaign.ends_at,
                campaign.max_uses,
                campaign.uses_count,
                campaign.created_at,
                campaign.updated_at
            ORDER BY campaign.updated_at DESC, campaign.created_at DESC, campaign.campaign_code ASC
            LIMIT $2
            """,
            safe_tenant_code,
            safe_limit,
        )
    return [_to_campaign_summary(dict(row)) for row in rows]


async def get_referral_saas_account_campaign(
    *,
    tenant_code: str,
    campaign_code: str,
) -> ReferralSaasCampaignSummary | None:
    safe_tenant_code = str(tenant_code or "").strip()
    safe_campaign_code = str(campaign_code or "").strip()
    if not safe_tenant_code or not safe_campaign_code:
        return None
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                campaign.campaign_code,
                campaign.name,
                campaign.segment,
                campaign.is_active,
                campaign.starts_at,
                campaign.ends_at,
                campaign.max_uses,
                campaign.uses_count,
                campaign.created_at,
                campaign.updated_at,
                COUNT(policy.campaign_code) FILTER (WHERE policy.is_active = TRUE)
                    AS active_policy_count
            FROM marketing_campaigns campaign
            LEFT JOIN marketing_campaign_policies policy
                ON UPPER(policy.campaign_code) = UPPER(campaign.campaign_code)
               AND (
                    policy.tenant_code IS NULL
                    OR UPPER(policy.tenant_code) = UPPER($1)
               )
            WHERE UPPER(campaign.tenant_code) = UPPER($1)
              AND UPPER(campaign.campaign_code) = UPPER($2)
            GROUP BY
                campaign.campaign_code,
                campaign.name,
                campaign.segment,
                campaign.is_active,
                campaign.starts_at,
                campaign.ends_at,
                campaign.max_uses,
                campaign.uses_count,
                campaign.created_at,
                campaign.updated_at
            LIMIT 1
            """,
            safe_tenant_code,
            safe_campaign_code,
        )
    return _to_campaign_summary(dict(row)) if row else None
