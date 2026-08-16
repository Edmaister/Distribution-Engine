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
    sequence: int
    event_type: str
    occurred_at: str | None
    received_at: str | None
    source_system: str | None
    source_event_present: bool
    dedupe_evidence: str
    payload_hash_present: bool
    source_inbox_status: str | None
    source_evidence: list[str]
    missing_evidence: list[str]
    recovery_posture: str

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "eventType": self.event_type,
            "occurredAt": self.occurred_at,
            "receivedAt": self.received_at,
            "sourceSystem": self.source_system,
            "sourceEventPresent": self.source_event_present,
            "dedupeEvidence": self.dedupe_evidence,
            "payloadHashPresent": self.payload_hash_present,
            "sourceInboxStatus": self.source_inbox_status,
            "sourceEvidence": self.source_evidence,
            "missingEvidence": self.missing_evidence,
            "recoveryPosture": self.recovery_posture,
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
    programme_version_id: str | None = None
    programme_code: str | None = None
    programme_name: str | None = None
    programme_version_number: int | None = None
    customer_journey_version_id: str | None = None

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
            "programmeVersion": _programme_runtime_summary(self),
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
            "timelineEvidenceSummary": _timeline_evidence_summary(self.timeline),
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
                ri.programme_version_id,
                ri.programme_runtime_context->>'programmeCode' AS programme_code,
                ri.programme_runtime_context->>'programmeName' AS programme_name,
                NULLIF(ri.programme_runtime_context->>'versionNumber', '')::INT AS programme_version_number,
                ri.programme_runtime_context->>'customerJourneyVersionId' AS customer_journey_version_id,
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
                ri.programme_version_id,
                ri.programme_runtime_context->>'programmeCode' AS programme_code,
                ri.programme_runtime_context->>'programmeName' AS programme_name,
                NULLIF(ri.programme_runtime_context->>'versionNumber', '')::INT AS programme_version_number,
                ri.programme_runtime_context->>'customerJourneyVersionId' AS customer_journey_version_id,
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
                ROW_NUMBER() OVER (ORDER BY rpe.occurred_at ASC, rpe.id ASC)::INT AS sequence,
                event_type,
                occurred_at,
                received_at,
                source_system,
                source_event_id,
                event_payload_hash,
                dedupe_key,
                idempotency_version,
                inbox.processing_status AS source_inbox_status,
                COALESCE(inbox.source_event_id IS NOT NULL, FALSE) AS source_inbox_event_present,
                COALESCE(inbox.dedupe_key IS NOT NULL, FALSE) AS source_inbox_dedupe_present,
                COALESCE(inbox.payload_hash IS NOT NULL, FALSE) AS source_inbox_payload_hash_present
            FROM referral_progress_events rpe
            LEFT JOIN LATERAL (
                SELECT
                    processing_status,
                    source_event_id,
                    dedupe_key,
                    payload_hash
                FROM enterprise_event_inbox inbox
                WHERE inbox.referral_track_id = rpe.referral_track_id
                  AND UPPER(inbox.event_type) = UPPER(rpe.event_type)
                  AND (
                    rpe.source_system IS NULL
                    OR inbox.source_system IS NULL
                    OR UPPER(inbox.source_system) = UPPER(rpe.source_system)
                  )
                  AND (
                    (rpe.source_event_id IS NOT NULL AND inbox.source_event_id = rpe.source_event_id)
                    OR (rpe.dedupe_key IS NOT NULL AND inbox.dedupe_key = rpe.dedupe_key)
                    OR (rpe.source_event_id IS NULL AND rpe.dedupe_key IS NULL)
                  )
                ORDER BY inbox.received_at DESC
                LIMIT 1
            ) inbox ON TRUE
            WHERE rpe.referral_track_id::TEXT = $1
            ORDER BY rpe.occurred_at ASC, rpe.id ASC
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
        programme_version_id=_optional_text(row.get("programme_version_id")),
        programme_code=_optional_text(row.get("programme_code")),
        programme_name=_optional_text(row.get("programme_name")),
        programme_version_number=_optional_int(row.get("programme_version_number")),
        customer_journey_version_id=_optional_text(row.get("customer_journey_version_id")),
    )


def _to_timeline_event(row: dict[str, Any]) -> ReferralSaasTimelineEvent:
    source_event_present = bool(row.get("source_event_id")) or bool(row.get("source_inbox_event_present"))
    dedupe_key_present = bool(row.get("dedupe_key")) or bool(row.get("source_inbox_dedupe_present"))
    payload_hash_present = bool(row.get("event_payload_hash")) or bool(
        row.get("source_inbox_payload_hash_present")
    )
    source_inbox_status = _optional_text(row.get("source_inbox_status"))
    dedupe_evidence = _dedupe_evidence(source_event_present, dedupe_key_present)
    source_evidence = _source_evidence(
        source_system=_optional_text(row.get("source_system")),
        source_event_present=source_event_present,
        dedupe_key_present=dedupe_key_present,
        payload_hash_present=payload_hash_present,
        source_inbox_status=source_inbox_status,
    )
    missing_evidence = _timeline_missing_evidence(
        source_system=_optional_text(row.get("source_system")),
        source_event_present=source_event_present,
        dedupe_key_present=dedupe_key_present,
        payload_hash_present=payload_hash_present,
        source_inbox_status=source_inbox_status,
    )
    return ReferralSaasTimelineEvent(
        sequence=int(row.get("sequence") or 0),
        event_type=_optional_text(row.get("event_type")) or "UNKNOWN",
        occurred_at=_iso(row.get("occurred_at")),
        received_at=_iso(row.get("received_at")),
        source_system=_optional_text(row.get("source_system")),
        source_event_present=source_event_present,
        dedupe_evidence=dedupe_evidence,
        payload_hash_present=payload_hash_present,
        source_inbox_status=source_inbox_status,
        source_evidence=source_evidence,
        missing_evidence=missing_evidence,
        recovery_posture=_timeline_recovery_posture(
            source_inbox_status=source_inbox_status,
            missing_evidence=missing_evidence,
        ),
    )


def _dedupe_evidence(source_event_present: bool, dedupe_key_present: bool) -> str:
    if source_event_present and dedupe_key_present:
        return "SOURCE_EVENT_AND_DEDUPE_KEY_PRESENT"
    if source_event_present:
        return "SOURCE_EVENT_ONLY"
    if dedupe_key_present:
        return "DEDUPE_KEY_ONLY"
    return "MISSING_DEDUPE_EVIDENCE"


def _source_evidence(
    *,
    source_system: str | None,
    source_event_present: bool,
    dedupe_key_present: bool,
    payload_hash_present: bool,
    source_inbox_status: str | None,
) -> list[str]:
    evidence: list[str] = []
    if source_system:
        evidence.append("SOURCE_SYSTEM_PRESENT")
    if source_event_present:
        evidence.append("SOURCE_EVENT_PRESENT")
    if dedupe_key_present:
        evidence.append("DEDUPE_KEY_PRESENT")
    if payload_hash_present:
        evidence.append("PAYLOAD_HASH_PRESENT")
    if source_inbox_status:
        evidence.append(f"SOURCE_INBOX_{source_inbox_status}")
    return evidence


def _timeline_missing_evidence(
    *,
    source_system: str | None,
    source_event_present: bool,
    dedupe_key_present: bool,
    payload_hash_present: bool,
    source_inbox_status: str | None,
) -> list[str]:
    missing: list[str] = []
    if not source_system:
        missing.append("SOURCE_SYSTEM_MISSING")
    if not source_event_present:
        missing.append("SOURCE_EVENT_ID_MISSING")
    if not dedupe_key_present:
        missing.append("DEDUPE_KEY_MISSING")
    if not payload_hash_present:
        missing.append("PAYLOAD_HASH_MISSING")
    if not source_inbox_status:
        missing.append("SOURCE_INBOX_EVIDENCE_MISSING")
    return missing


def _timeline_recovery_posture(
    *,
    source_inbox_status: str | None,
    missing_evidence: list[str],
) -> str:
    if source_inbox_status == "DUPLICATE":
        return "DEDUPE_REPLAY_RECORDED"
    if source_inbox_status in {"FAILED", "IGNORED"}:
        return "SOURCE_EVENT_FAILED_OR_DELAYED"
    if "SOURCE_SYSTEM_MISSING" in missing_evidence or "SOURCE_INBOX_EVIDENCE_MISSING" in missing_evidence:
        return "CHECK_SOURCE_PROVENANCE"
    if {"SOURCE_EVENT_ID_MISSING", "DEDUPE_KEY_MISSING", "PAYLOAD_HASH_MISSING"}.intersection(
        missing_evidence
    ):
        return "CHECK_IDEMPOTENCY_EVIDENCE"
    return "READY_FOR_SUPPORT_AND_ATTRIBUTION"


def _timeline_evidence_summary(timeline: list[ReferralSaasTimelineEvent]) -> dict[str, Any]:
    missing_source_count = sum(
        1
        for event in timeline
        if "SOURCE_SYSTEM_MISSING" in event.missing_evidence
        or "SOURCE_INBOX_EVIDENCE_MISSING" in event.missing_evidence
    )
    missing_idempotency_count = sum(
        1
        for event in timeline
        if {"SOURCE_EVENT_ID_MISSING", "DEDUPE_KEY_MISSING", "PAYLOAD_HASH_MISSING"}.intersection(
            event.missing_evidence
        )
    )
    duplicate_count = sum(1 for event in timeline if event.recovery_posture == "DEDUPE_REPLAY_RECORDED")
    failed_or_delayed_count = sum(
        1 for event in timeline if event.recovery_posture == "SOURCE_EVENT_FAILED_OR_DELAYED"
    )
    missing_evidence = sorted({item for event in timeline for item in event.missing_evidence})
    return {
        "eventCount": len(timeline),
        "sourceMatchedCount": sum(1 for event in timeline if event.source_inbox_status),
        "missingSourceEvidenceCount": missing_source_count,
        "missingIdempotencyEvidenceCount": missing_idempotency_count,
        "duplicateReplayCount": duplicate_count,
        "failedOrDelayedCount": failed_or_delayed_count,
        "missingEvidence": missing_evidence,
        "recoveryPosture": _timeline_summary_recovery_posture(
            timeline=timeline,
            missing_source_count=missing_source_count,
            missing_idempotency_count=missing_idempotency_count,
            duplicate_count=duplicate_count,
            failed_or_delayed_count=failed_or_delayed_count,
        ),
    }


def _timeline_summary_recovery_posture(
    *,
    timeline: list[ReferralSaasTimelineEvent],
    missing_source_count: int,
    missing_idempotency_count: int,
    duplicate_count: int,
    failed_or_delayed_count: int,
) -> str:
    if not timeline:
        return "NO_TIMELINE_EVIDENCE"
    if failed_or_delayed_count:
        return "SOURCE_EVENT_FAILED_OR_DELAYED"
    if missing_source_count:
        return "CHECK_SOURCE_PROVENANCE"
    if missing_idempotency_count:
        return "CHECK_IDEMPOTENCY_EVIDENCE"
    if duplicate_count:
        return "DEDUPE_REPLAY_RECORDED"
    return "READY_FOR_SUPPORT_AND_ATTRIBUTION"


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


def _programme_runtime_summary(summary: ReferralSaasReferralSummary) -> dict[str, Any]:
    if not summary.programme_version_id:
        return {"bindingStatus": "LEGACY_OR_UNBOUND"}
    return {
        "bindingStatus": "BOUND_AT_REFERRAL_CREATION",
        "programmeVersionId": summary.programme_version_id,
        "programmeCode": summary.programme_code,
        "programmeName": summary.programme_name,
        "versionNumber": summary.programme_version_number,
        "customerJourneyVersionId": summary.customer_journey_version_id,
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
