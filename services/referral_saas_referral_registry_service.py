from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from utils.db import db_connection


MAX_REFERRAL_REGISTRY_LIMIT = 100
REFERRAL_REGISTRY_GUARDRAILS = [
    "CUSTOMER_SCOPED_REFERRAL_REGISTRY",
    "ACCOUNT_SCOPE_RESOLVED_INTERNALLY",
    "NO_TENANT_CODE_EXPOSURE",
    "NO_RAW_UCN_EXPOSURE",
    "NO_RAW_PROGRESS_PAYLOAD_EXPOSURE",
    "NO_REFERRAL_MUTATION",
    "NO_REPAIR_REPLAY_REASSIGNMENT",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_WEBHOOK_DELIVERY",
    "NO_BILLING_OR_MONEY_MOVEMENT",
]
REFERRAL_REGISTRY_REDACTIONS = [
    "internal_tenant_identifier",
    "raw_referrer_ucn",
    "raw_referee_ucn",
    "raw_progress_payload",
    "event_payload_hash",
    "dedupe_key",
]


@dataclass(frozen=True)
class ReferralSaasTimelineEvent:
    event_type: str
    occurred_at: str | None
    source_system: str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "eventType": self.event_type,
            "occurredAt": self.occurred_at,
            "sourceSystem": self.source_system,
        }


@dataclass(frozen=True)
class ReferralSaasReferralSummary:
    referral_track_id: str
    referral_code: str | None
    public_referrer_handle: str | None
    campaign_code: str | None
    status: str
    display_status: str | None
    progress_percent: int | None
    progress_band: str | None
    next_milestone: str | None
    journey_code: str | None
    journey_version: int | None
    product: str | None
    sub_product: str | None
    referee_alias: str | None
    accepted_terms: bool
    is_complete: bool
    validated_at: str | None
    completed_at: str | None
    created_at: str | None
    updated_at: str | None
    last_progress_at: str | None
    progress_event_count: int
    has_attribution_evidence: bool

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "referralTrackId": self.referral_track_id,
            "referralCode": self.referral_code,
            "publicReferrerHandle": self.public_referrer_handle,
            "campaignCode": self.campaign_code,
            "status": self.status,
            "displayStatus": self.display_status,
            "progressPercent": self.progress_percent,
            "progressBand": self.progress_band,
            "nextMilestone": self.next_milestone,
            "journeyCode": self.journey_code,
            "journeyVersion": self.journey_version,
            "product": self.product,
            "subProduct": self.sub_product,
            "refereeAlias": self.referee_alias,
            "acceptedTerms": self.accepted_terms,
            "isComplete": self.is_complete,
            "validatedAt": self.validated_at,
            "completedAt": self.completed_at,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "lastProgressAt": self.last_progress_at,
            "progressEventCount": self.progress_event_count,
            "hasAttributionEvidence": self.has_attribution_evidence,
            "missingEvidence": _missing_evidence(self),
            "timelineAnchors": _timeline_anchors(self),
            "redactions": REFERRAL_REGISTRY_REDACTIONS,
        }


@dataclass(frozen=True)
class ReferralSaasReferralDetail:
    summary: ReferralSaasReferralSummary
    timeline: list[ReferralSaasTimelineEvent]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            **self.summary.to_safe_dict(),
            "timeline": [event.to_safe_dict() for event in self.timeline],
        }


async def list_referral_saas_account_referrals(
    *,
    tenant_code: str,
    limit: int = 50,
) -> list[ReferralSaasReferralSummary]:
    safe_tenant_code = str(tenant_code or "").strip()
    if not safe_tenant_code:
        return []
    safe_limit = max(1, min(int(limit or 50), MAX_REFERRAL_REGISTRY_LIMIT))
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            WITH progress AS (
                SELECT
                    referral_track_id,
                    COUNT(*)::INT AS progress_event_count,
                    MAX(occurred_at) AS last_progress_at
                FROM referral_progress_events
                GROUP BY referral_track_id
            )
            SELECT
                ri.referral_track_id,
                ri.referral_code,
                rc.gaming_handle AS public_referrer_handle,
                ca.campaign_code,
                ri.status,
                ri.display_status,
                ri.progress_percent,
                ri.progress_band,
                ri.next_milestone,
                ri.journey_code,
                ri.journey_version,
                ri.product,
                ri.sub_product,
                ri.referee_alias,
                ri.accepted_terms,
                ri.is_complete,
                ri.validated_at,
                ri.completed_at,
                ri.created_at,
                ri.updated_at,
                progress.last_progress_at,
                COALESCE(progress.progress_event_count, 0) AS progress_event_count,
                (ca.campaign_track_id IS NOT NULL) AS has_attribution_evidence
            FROM referral_instances ri
            LEFT JOIN referrer_codes rc
                ON rc.referrer_code_id = ri.referrer_code_id
            LEFT JOIN campaign_referral_links crl
                ON crl.referral_track_id = ri.referral_track_id
            LEFT JOIN campaign_attributions ca
                ON ca.campaign_track_id = crl.campaign_track_id
               AND (
                    ca.tenant_code IS NULL
                    OR UPPER(ca.tenant_code) = UPPER($1)
               )
            LEFT JOIN progress
                ON progress.referral_track_id = ri.referral_track_id
            WHERE UPPER(ri.tenant_code) = UPPER($1)
            ORDER BY
                COALESCE(progress.last_progress_at, ri.updated_at, ri.created_at) DESC,
                ri.referral_track_id ASC
            LIMIT $2
            """,
            safe_tenant_code,
            safe_limit,
        )
    return [_to_referral_summary(dict(row)) for row in rows]


async def get_referral_saas_account_referral(
    *,
    tenant_code: str,
    referral_track_id: str,
) -> ReferralSaasReferralDetail | None:
    safe_tenant_code = str(tenant_code or "").strip()
    safe_referral_track_id = str(referral_track_id or "").strip()
    if not safe_tenant_code or not safe_referral_track_id:
        return None
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            WITH progress AS (
                SELECT
                    referral_track_id,
                    COUNT(*)::INT AS progress_event_count,
                    MAX(occurred_at) AS last_progress_at
                FROM referral_progress_events
                GROUP BY referral_track_id
            )
            SELECT
                ri.referral_track_id,
                ri.referral_code,
                rc.gaming_handle AS public_referrer_handle,
                ca.campaign_code,
                ri.status,
                ri.display_status,
                ri.progress_percent,
                ri.progress_band,
                ri.next_milestone,
                ri.journey_code,
                ri.journey_version,
                ri.product,
                ri.sub_product,
                ri.referee_alias,
                ri.accepted_terms,
                ri.is_complete,
                ri.validated_at,
                ri.completed_at,
                ri.created_at,
                ri.updated_at,
                progress.last_progress_at,
                COALESCE(progress.progress_event_count, 0) AS progress_event_count,
                (ca.campaign_track_id IS NOT NULL) AS has_attribution_evidence
            FROM referral_instances ri
            LEFT JOIN referrer_codes rc
                ON rc.referrer_code_id = ri.referrer_code_id
            LEFT JOIN campaign_referral_links crl
                ON crl.referral_track_id = ri.referral_track_id
            LEFT JOIN campaign_attributions ca
                ON ca.campaign_track_id = crl.campaign_track_id
               AND (
                    ca.tenant_code IS NULL
                    OR UPPER(ca.tenant_code) = UPPER($1)
               )
            LEFT JOIN progress
                ON progress.referral_track_id = ri.referral_track_id
            WHERE UPPER(ri.tenant_code) = UPPER($1)
              AND ri.referral_track_id::TEXT = $2
            LIMIT 1
            """,
            safe_tenant_code,
            safe_referral_track_id,
        )
        if not row:
            return None
        timeline_rows = await conn.fetch(
            """
            SELECT
                event_type,
                occurred_at,
                source_system
            FROM referral_progress_events
            WHERE referral_track_id::TEXT = $1
            ORDER BY occurred_at ASC, id ASC
            LIMIT 100
            """,
            safe_referral_track_id,
        )
    return ReferralSaasReferralDetail(
        summary=_to_referral_summary(dict(row)),
        timeline=[_to_timeline_event(dict(row)) for row in timeline_rows],
    )


def _to_referral_summary(row: dict[str, Any]) -> ReferralSaasReferralSummary:
    return ReferralSaasReferralSummary(
        referral_track_id=str(row.get("referral_track_id") or ""),
        referral_code=_optional_text(row.get("referral_code")),
        public_referrer_handle=_optional_text(row.get("public_referrer_handle")),
        campaign_code=_optional_text(row.get("campaign_code")),
        status=_optional_text(row.get("status")) or "UNKNOWN",
        display_status=_optional_text(row.get("display_status")),
        progress_percent=_optional_int(row.get("progress_percent")),
        progress_band=_optional_text(row.get("progress_band")),
        next_milestone=_optional_text(row.get("next_milestone")),
        journey_code=_optional_text(row.get("journey_code")),
        journey_version=_optional_int(row.get("journey_version")),
        product=_optional_text(row.get("product")),
        sub_product=_optional_text(row.get("sub_product")),
        referee_alias=_optional_text(row.get("referee_alias")),
        accepted_terms=bool(row.get("accepted_terms")),
        is_complete=bool(row.get("is_complete")),
        validated_at=_iso(row.get("validated_at")),
        completed_at=_iso(row.get("completed_at")),
        created_at=_iso(row.get("created_at")),
        updated_at=_iso(row.get("updated_at")),
        last_progress_at=_iso(row.get("last_progress_at")),
        progress_event_count=int(row.get("progress_event_count") or 0),
        has_attribution_evidence=bool(row.get("has_attribution_evidence")),
    )


def _to_timeline_event(row: dict[str, Any]) -> ReferralSaasTimelineEvent:
    return ReferralSaasTimelineEvent(
        event_type=_optional_text(row.get("event_type")) or "UNKNOWN",
        occurred_at=_iso(row.get("occurred_at")),
        source_system=_optional_text(row.get("source_system")),
    )


def _missing_evidence(summary: ReferralSaasReferralSummary) -> list[str]:
    missing: list[str] = []
    if not summary.referral_code:
        missing.append("REFERRAL_CODE_MISSING")
    if not summary.public_referrer_handle:
        missing.append("SAFE_REFERRER_HANDLE_MISSING")
    if not summary.campaign_code:
        missing.append("CAMPAIGN_LINK_MISSING")
    if not summary.accepted_terms:
        missing.append("ACCEPTED_TERMS_NOT_CONFIRMED")
    if summary.progress_event_count == 0:
        missing.append("PROGRESS_TIMELINE_MISSING")
    if not summary.has_attribution_evidence:
        missing.append("ATTRIBUTION_EVIDENCE_MISSING")
    return missing


def _timeline_anchors(summary: ReferralSaasReferralSummary) -> dict[str, Any]:
    return {
        "validatedAt": summary.validated_at,
        "lastProgressAt": summary.last_progress_at,
        "completedAt": summary.completed_at,
        "nextMilestone": summary.next_milestone,
    }


def _iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None:
        return None
    return str(value)


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
