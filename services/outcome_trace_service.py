from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from services.fulfilment_safe_status import map_fulfilment_status, map_settlement_status
from utils.db import db_connection

DEFAULT_SECTIONS = [
    "outcome",
    "attribution",
    "participants",
    "events",
    "reward",
    "commission",
    "funding",
    "fulfilment",
    "settlement",
    "audit",
    "webhooks",
]

OPTIONAL_SECTIONS = set(DEFAULT_SECTIONS) - {"outcome"}


class OutcomeTraceNotFound(LookupError):
    """Raised when a tenant-scoped outcome lookup has no source row."""


def _normalise_tenant_code(tenant_code: str) -> str:
    tenant = str(tenant_code or "").strip().upper()
    if not tenant:
        raise ValueError("tenant_code is required")
    return tenant


def _normalise_referral_track_id(referral_track_id: str) -> str:
    track_id = str(referral_track_id or "").strip()
    if not track_id:
        raise ValueError("referral_track_id is required")
    return track_id


def _normalise_sections(include_sections: list[str] | None) -> list[str]:
    if include_sections is None:
        return list(DEFAULT_SECTIONS)

    sections = ["outcome"]
    for section in include_sections:
        normalised = str(section or "").strip().lower()
        if not normalised:
            continue
        if normalised not in DEFAULT_SECTIONS:
            raise ValueError(f"Unsupported outcome trace section: {section}")
        if normalised not in sections:
            sections.append(normalised)
    return sections


def _serialise_value(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, list):
        return [_serialise_value(item) for item in value]
    if isinstance(value, tuple):
        return [_serialise_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialise_value(inner) for key, inner in value.items()}
    if isinstance(value, str) and value[:1] in {"{", "["}:
        try:
            return _serialise_value(json.loads(value))
        except json.JSONDecodeError:
            return value
    return value


def _row(row: Any) -> dict[str, Any]:
    return {key: _serialise_value(value) for key, value in dict(row or {}).items()}


def _rows(rows: list[Any]) -> list[dict[str, Any]]:
    return [_row(row) for row in rows or []]


def _rows_with_safe_status(
    rows: list[Any],
    mapper,
) -> list[dict[str, Any]]:
    items = _rows(rows)
    for item in items:
        item["operator_safe_status"] = mapper(item.get("status"), surface="operator")
        item["external_safe_status"] = mapper(item.get("status"), surface="external")
    return items


def _missing(
    *,
    section: str,
    code: str,
    message: str,
    source: str,
    severity: str = "INFO",
    next_verification: str | None = None,
) -> dict[str, Any]:
    item = {
        "section": section,
        "code": code,
        "severity": severity,
        "message": message,
        "source": source,
    }
    if next_verification:
        item["next_verification"] = next_verification
    return item


def _trace_completeness(missing_evidence: list[dict[str, Any]]) -> str:
    if not missing_evidence:
        return "COMPLETE"
    if any(item["code"] == "SOURCE_CONFLICT" for item in missing_evidence):
        return "INCONSISTENT"
    if any(item["code"] == "SOURCE_UNAVAILABLE" for item in missing_evidence):
        return "UNAVAILABLE"
    return "PARTIAL"


def _section_rows(
    *,
    section: str,
    rows: list[dict[str, Any]],
    missing_evidence: list[dict[str, Any]],
    missing_code: str = "NO_SOURCE_EVIDENCE",
    missing_source: str,
    missing_message: str,
    missing_severity: str = "INFO",
    next_verification: str | None = None,
) -> dict[str, Any]:
    if not rows:
        missing_evidence.append(
            _missing(
                section=section,
                code=missing_code,
                source=missing_source,
                message=missing_message,
                severity=missing_severity,
                next_verification=next_verification,
            )
        )
    return {"items": rows, "count": len(rows)}


async def get_outcome_trace(
    *,
    tenant_code: str,
    referral_track_id: str,
    identity: dict[str, Any] | None = None,
    include_sections: list[str] | None = None,
) -> dict[str, Any]:
    tenant = _normalise_tenant_code(tenant_code)
    track_id = _normalise_referral_track_id(referral_track_id)
    sections_to_include = _normalise_sections(include_sections)

    async with db_connection() as conn:
        outcome = await conn.fetchrow(
            """
            SELECT
                ri.referral_track_id::text AS referral_track_id,
                ri.tenant_code,
                ri.referral_code,
                ri.status,
                ri.is_complete,
                ri.product,
                ri.sub_product,
                ri.journey_code,
                ri.journey_version,
                ri.validated_at,
                ri.created_at,
                ri.updated_at,
                ri.completed_at,
                rc.referrer_code_id::text AS referrer_code_id,
                rc.gaming_handle AS referrer_display_ref,
                rc.sticker,
                rc.segment
            FROM referral_instances ri
            LEFT JOIN referrer_codes rc
              ON rc.referrer_code_id = ri.referrer_code_id
            WHERE ri.referral_track_id = $1::uuid
              AND ri.tenant_code = $2
            """,
            track_id,
            tenant,
        )

        if not outcome:
            raise OutcomeTraceNotFound(
                f"Outcome {track_id} was not found for tenant {tenant}"
            )

        campaign_attribution = await conn.fetch(
            """
            SELECT
                'CAMPAIGN_REFERRAL_LINK' AS source_type,
                crl.campaign_track_id::text AS campaign_track_id,
                crl.referral_track_id::text AS referral_track_id,
                ca.campaign_code,
                ca.tenant_code,
                ca.status AS campaign_track_status,
                ca.source_channel,
                ca.validation_reason,
                ca.scanned_at,
                ca.validated_at,
                ca.attributed_at,
                ca.completed_at,
                crl.created_at,
                'MEDIUM' AS source_confidence
            FROM campaign_referral_links crl
            JOIN campaign_attributions ca
              ON ca.campaign_track_id = crl.campaign_track_id
            WHERE crl.referral_track_id = $1::uuid
              AND ca.tenant_code = $2
            ORDER BY crl.created_at DESC
            """,
            track_id,
            tenant,
        )
        route_attribution = await conn.fetch(
            """
            SELECT
                'ROUTE_REFERRAL_LINK' AS source_type,
                l.route_id::text AS route_id,
                l.referral_track_id::text AS referral_track_id,
                l.tenant_code,
                l.distributor_id::text AS distributor_id,
                d.distributor_code,
                d.distributor_name,
                l.opportunity_id::text AS opportunity_id,
                o.opportunity_code,
                o.campaign_code,
                o.sponsor_code,
                o.title AS opportunity_title,
                l.link_status,
                l.created_at,
                l.updated_at,
                l.metadata,
                'MEDIUM' AS source_confidence
            FROM distribution_route_referral_links l
            JOIN distribution_distributors d
              ON d.distributor_id = l.distributor_id
            JOIN distribution_opportunities o
              ON o.opportunity_id = l.opportunity_id
            WHERE l.referral_track_id = $1::uuid
              AND l.tenant_code = $2
            ORDER BY l.updated_at DESC, l.created_at DESC
            """,
            track_id,
            tenant,
        )
        progress_events = await conn.fetch(
            """
            SELECT
                'REFERRAL_PROGRESS_EVENT' AS source,
                id::text AS event_id,
                referral_track_id::text AS referral_track_id,
                event_type,
                source_system,
                source_event_id,
                dedupe_key,
                idempotency_version,
                occurred_at,
                received_at,
                created_at,
                meta
            FROM referral_progress_events
            WHERE referral_track_id = $1::uuid
            ORDER BY occurred_at DESC, created_at DESC
            """,
            track_id,
        )
        enterprise_events = await conn.fetch(
            """
            SELECT
                'ENTERPRISE_EVENT_INBOX' AS source,
                inbox_event_id::text AS event_id,
                tenant_code,
                source_system,
                source_event_id,
                correlation_id,
                referral_track_id::text AS referral_track_id,
                event_type,
                processing_status,
                received_at,
                processed_at
            FROM enterprise_event_inbox
            WHERE referral_track_id = $1::uuid
              AND ($2::text IS NULL OR tenant_code = $2)
            ORDER BY received_at DESC
            """,
            track_id,
            tenant,
        )
        reward_rows = await conn.fetch(
            """
            SELECT
                'referral_rewards' AS source,
                rr.reward_id::text AS reward_id,
                rr.referral_track_id::text AS referral_track_id,
                rr.tenant_code,
                rr.reward_type,
                NULL::text AS reward_source,
                NULL::text AS beneficiary_type,
                NULL::text AS beneficiary_ref,
                rr.product,
                NULL::text AS sub_product,
                rr.amount,
                NULL::text AS currency,
                NULL::text AS status,
                NULL::text AS mission_code,
                rr.created_at
            FROM referral_rewards rr
            WHERE rr.referral_track_id = $1::uuid
              AND ($2::text IS NULL OR rr.tenant_code = $2)
            UNION ALL
            SELECT
                'rewards' AS source,
                r.id::text AS reward_id,
                r.referral_track_id,
                r.tenant_code,
                r.reward_type,
                r.reward_source,
                r.beneficiary_type,
                r.beneficiary_ref,
                r.product,
                r.sub_product,
                r.amount,
                NULL::text AS currency,
                r.status,
                r.mission_code,
                r.created_at
            FROM rewards r
            WHERE r.referral_track_id = $1
              AND ($2::text IS NULL OR r.tenant_code = $2)
            ORDER BY created_at DESC
            """,
            track_id,
            tenant,
        )
        commission_rows = await conn.fetch(
            """
            SELECT
                commission_event_id::text AS commission_event_id,
                tenant_code,
                distributor_id::text AS distributor_id,
                distributor_code,
                wallet_id::text AS wallet_id,
                rule_id::text AS rule_id,
                sponsor_code,
                campaign_code,
                source_event_id,
                activity_type,
                sale_amount,
                commission_amount,
                currency,
                commission_status,
                credited_at,
                correlation_id,
                metadata,
                created_at,
                updated_at
            FROM distribution_commission_events
            WHERE tenant_code = $2
              AND (source_event_id = $1 OR correlation_id = $1)
            ORDER BY created_at DESC
            """,
            track_id,
            tenant,
        )
        funding_rows = await conn.fetch(
            """
            WITH reward_ids AS (
                SELECT reward_id::text AS reward_id
                FROM referral_rewards
                WHERE referral_track_id = $1::uuid
                  AND ($2::text IS NULL OR tenant_code = $2)
                UNION
                SELECT id::text AS reward_id
                FROM rewards
                WHERE referral_track_id = $1
                  AND ($2::text IS NULL OR tenant_code = $2)
            )
            SELECT
                'funding_reservations' AS source,
                fr.reservation_id::text AS funding_id,
                fr.reward_id,
                fr.tenant_code,
                fr.account_id::text AS account_id,
                NULL::text AS wallet_id,
                NULL::text AS sponsor_code,
                fr.amount,
                NULL::text AS currency,
                fr.status,
                fr.correlation_id,
                fr.created_at,
                fr.updated_at
            FROM funding_reservations fr
            WHERE fr.tenant_code = $2
              AND (fr.reward_id IN (SELECT reward_id FROM reward_ids) OR fr.correlation_id = $1)
            UNION ALL
            SELECT
                'marketplace_funding_allocations' AS source,
                mfa.allocation_id::text AS funding_id,
                mfa.reward_id::text AS reward_id,
                mfa.tenant_code,
                NULL::text AS account_id,
                mfa.wallet_id::text AS wallet_id,
                mfa.sponsor_code,
                mfa.amount,
                NULL::text AS currency,
                mfa.status,
                mfa.correlation_id,
                mfa.created_at,
                mfa.updated_at
            FROM marketplace_funding_allocations mfa
            WHERE mfa.tenant_code = $2
              AND (mfa.reward_id::text IN (SELECT reward_id FROM reward_ids) OR mfa.correlation_id = $1)
            ORDER BY created_at DESC
            """,
            track_id,
            tenant,
        )
        fulfilment_rows = await conn.fetch(
            """
            WITH reward_ids AS (
                SELECT reward_id::text AS reward_id
                FROM referral_rewards
                WHERE referral_track_id = $1::uuid
                  AND ($2::text IS NULL OR tenant_code = $2)
                UNION
                SELECT id::text AS reward_id
                FROM rewards
                WHERE referral_track_id = $1
                  AND ($2::text IS NULL OR tenant_code = $2)
            )
            SELECT
                audit_id::text AS audit_id,
                tenant_code,
                referral_track_id,
                reward_type,
                fulfilment_provider,
                fulfilment_policy_id::text AS fulfilment_policy_id,
                idempotency_key,
                status,
                previous_status,
                attempt_no,
                max_attempts,
                provider_reference,
                provider_status,
                failure_reason,
                error_code,
                correlation_id,
                event_type,
                requested_at,
                processing_started_at,
                completed_at,
                failed_at,
                created_at,
                updated_at
            FROM fulfilment_audit
            WHERE tenant_code = $2
              AND (
                referral_track_id = $1
                OR correlation_id = $1
                OR correlation_id IN (SELECT reward_id FROM reward_ids)
              )
            ORDER BY created_at DESC
            """,
            track_id,
            tenant,
        )
        settlement_rows = await conn.fetch(
            """
            SELECT
                fsl.settlement_id::text AS settlement_id,
                fsl.tenant_code,
                fsl.reward_id::text AS reward_id,
                fsl.audit_id::text AS audit_id,
                fsl.provider_key,
                fsl.provider_reference,
                fsl.amount,
                fsl.currency,
                fsl.status,
                fsl.settlement_date,
                fsl.settled_at,
                fsl.failed_at,
                fsl.reversed_at,
                fsl.failure_reason,
                fsl.reversal_reason,
                fsl.created_at,
                fsl.updated_at,
                COUNT(DISTINCT se.exception_id)::int AS exception_count,
                COUNT(DISTINCT sr.reversal_id)::int AS reversal_count
            FROM fulfilment_settlement_ledger fsl
            JOIN referral_rewards rr
              ON rr.reward_id = fsl.reward_id
            LEFT JOIN settlement_exceptions se
              ON se.settlement_id = fsl.settlement_id
            LEFT JOIN settlement_reversals sr
              ON sr.settlement_id = fsl.settlement_id
            WHERE rr.referral_track_id = $1::uuid
              AND fsl.tenant_code = $2
            GROUP BY fsl.settlement_id
            ORDER BY fsl.created_at DESC
            """,
            track_id,
            tenant,
        )
        admin_audit_rows = await conn.fetch(
            """
            SELECT
                'admin_audit_log' AS source,
                admin_audit_id::text AS audit_id,
                action_domain,
                action_type,
                action_status,
                actor_role,
                actor_tenant_code,
                tenant_code,
                target_type,
                target_id,
                correlation_id,
                reason,
                error_message,
                created_at
            FROM admin_audit_log
            WHERE ($2::text IS NULL OR tenant_code = $2 OR actor_tenant_code = $2)
              AND (
                target_id = $1
                OR correlation_id = $1
              )
            ORDER BY created_at DESC
            """,
            track_id,
            tenant,
        )
        processing_audit_rows = await conn.fetch(
            """
            SELECT
                'referral_processing_audit' AS source,
                id::text AS audit_id,
                referral_track_id::text AS referral_track_id,
                event_id::text AS event_id,
                event_type,
                occurred_at,
                processed_at,
                processing_status,
                reason,
                previous_status,
                new_status
            FROM referral_processing_audit
            WHERE referral_track_id = $1::uuid
            ORDER BY processed_at DESC
            """,
            track_id,
        )
        webhook_rows = await conn.fetch(
            """
            SELECT
                d.delivery_id::text AS delivery_id,
                d.webhook_id::text AS webhook_id,
                d.client_id,
                d.tenant_code,
                d.event_type,
                d.delivery_status,
                d.attempt_count,
                d.next_attempt_at,
                d.delivered_at,
                CASE
                    WHEN d.last_error IS NULL THEN NULL
                    ELSE LEFT(d.last_error, 200)
                END AS last_error,
                d.created_at,
                d.updated_at
            FROM partner_webhook_deliveries d
            WHERE d.tenant_code = $2
              AND (
                d.payload->>'referral_track_id' = $1
                OR d.payload->'metadata'->>'referral_track_id' = $1
                OR d.payload->>'correlation_id' = $1
              )
            ORDER BY d.created_at DESC
            """,
            track_id,
            tenant,
        )

    outcome_data = _row(outcome)
    missing_evidence: list[dict[str, Any]] = []
    source_warnings: list[dict[str, Any]] = []
    sections: dict[str, Any] = {"outcome": outcome_data}

    if "attribution" in sections_to_include:
        campaign_items = _rows(campaign_attribution)
        route_items = _rows(route_attribution)
        attribution_items = campaign_items + route_items
        sections["attribution"] = _section_rows(
            section="attribution",
            rows=attribution_items,
            missing_evidence=missing_evidence,
            missing_source="campaign_referral_links, distribution_route_referral_links",
            missing_message="No campaign or route attribution evidence was found for this outcome.",
        )
        sections["attribution"]["campaign_links"] = campaign_items
        sections["attribution"]["route_links"] = route_items

    if "participants" in sections_to_include:
        sections["participants"] = {
            "items": _participants(outcome_data, _rows(route_attribution)),
        }
        sections["participants"]["count"] = len(sections["participants"]["items"])

    if "events" in sections_to_include:
        event_items = _rows(progress_events) + _rows(enterprise_events)
        sections["events"] = _section_rows(
            section="events",
            rows=event_items,
            missing_evidence=missing_evidence,
            missing_source="referral_progress_events, enterprise_event_inbox",
            missing_message="No progress or enterprise event evidence was found for this outcome.",
        )

    if "reward" in sections_to_include:
        sections["reward"] = _section_rows(
            section="reward",
            rows=_rows(reward_rows),
            missing_evidence=missing_evidence,
            missing_source="referral_rewards, rewards",
            missing_message="No reward evidence was found for this outcome.",
        )

    if "commission" in sections_to_include:
        sections["commission"] = _section_rows(
            section="commission",
            rows=_rows(commission_rows),
            missing_evidence=missing_evidence,
            missing_code="JOIN_AMBIGUOUS",
            missing_source="distribution_commission_events",
            missing_message="No commission evidence was found through the current source_event_id or correlation_id join.",
            missing_severity="WARNING",
            next_verification="TASK-011 verifies only current referral_track_id joins; source-event taxonomy remains a follow-up.",
        )
        if commission_rows:
            source_warnings.append(
                _missing(
                    section="commission",
                    code="JOIN_AMBIGUOUS",
                    severity="WARNING",
                    source="distribution_commission_events",
                    message="Commission evidence is joined through source_event_id or correlation_id matching referral_track_id.",
                    next_verification="Confirm source-event taxonomy before exposing this outside operator traces.",
                )
            )

    if "funding" in sections_to_include:
        sections["funding"] = _section_rows(
            section="funding",
            rows=_rows(funding_rows),
            missing_evidence=missing_evidence,
            missing_code="JOIN_AMBIGUOUS",
            missing_source="funding_reservations, marketplace_funding_allocations",
            missing_message="No funding evidence was found through reward_id or referral correlation joins.",
            missing_severity="WARNING",
            next_verification="Funding is not directly keyed by referral_track_id; verify reward/allocation joins before broader use.",
        )

    if "fulfilment" in sections_to_include:
        sections["fulfilment"] = _section_rows(
            section="fulfilment",
            rows=_rows_with_safe_status(fulfilment_rows, map_fulfilment_status),
            missing_evidence=missing_evidence,
            missing_source="fulfilment_audit",
            missing_message="No fulfilment audit evidence was found for this outcome.",
        )

    if "settlement" in sections_to_include:
        sections["settlement"] = _section_rows(
            section="settlement",
            rows=_rows_with_safe_status(settlement_rows, map_settlement_status),
            missing_evidence=missing_evidence,
            missing_source="fulfilment_settlement_ledger",
            missing_message="No settlement evidence was found for this outcome.",
        )

    if "audit" in sections_to_include:
        audit_items = _rows(admin_audit_rows) + _rows(processing_audit_rows)
        sections["audit"] = _section_rows(
            section="audit",
            rows=audit_items,
            missing_evidence=missing_evidence,
            missing_source="admin_audit_log, referral_processing_audit",
            missing_message="No audit evidence was found for this outcome.",
        )

    if "webhooks" in sections_to_include:
        sections["webhooks"] = _section_rows(
            section="webhooks",
            rows=_rows(webhook_rows),
            missing_evidence=missing_evidence,
            missing_code="JOIN_AMBIGUOUS",
            missing_source="partner_webhook_deliveries",
            missing_message="No webhook delivery evidence was found through the current payload/correlation lookup.",
            missing_severity="WARNING",
            next_verification="TASK-020 must define the webhook event catalog before broad webhook trace matching.",
        )

    for section in DEFAULT_SECTIONS:
        if section not in sections_to_include:
            missing_evidence.append(
                _missing(
                    section=section,
                    code="SECTION_NOT_REQUESTED",
                    severity="INFO",
                    source="outcome_trace_service",
                    message=f"{section} evidence was not requested.",
                )
            )

    return {
        "trace_id": f"outcome:referral_track_id:{track_id}",
        "trace_type": "OUTCOME",
        "lookup": {"type": "REFERRAL_TRACK_ID", "value": track_id},
        "tenant_code": tenant,
        "trace_completeness": _trace_completeness(missing_evidence),
        "sections": sections,
        "missing_evidence": missing_evidence,
        "source_warnings": source_warnings,
        "redactions": [
            {
                "field": "referrer_ucn",
                "reason": "Raw UCN is internal-sensitive and is not returned by the outcome trace service.",
            },
            {
                "field": "referee_ucn",
                "reason": "Raw UCN is internal-sensitive and is not returned by the outcome trace service.",
            },
            {
                "field": "provider_response",
                "reason": "Provider payloads are excluded from the service trace response.",
            },
        ],
        "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
    }


def _participants(
    outcome: dict[str, Any], route_links: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    participants = []

    if outcome.get("referrer_code_id") or outcome.get("referrer_display_ref"):
        participants.append(
            {
                "participant_type": "REFERRER",
                "source": "referrer_codes",
                "source_id": outcome.get("referrer_code_id"),
                "safe_display_ref": outcome.get("referrer_display_ref"),
                "tenant_code": outcome.get("tenant_code"),
                "evidence": {
                    "referral_code": outcome.get("referral_code"),
                    "sticker": outcome.get("sticker"),
                    "segment": outcome.get("segment"),
                },
            }
        )

    seen_distributors = set()
    for route in route_links:
        distributor_code = route.get("distributor_code")
        if not distributor_code or distributor_code in seen_distributors:
            continue
        seen_distributors.add(distributor_code)
        participants.append(
            {
                "participant_type": "DISTRIBUTOR",
                "source": "distribution_distributors",
                "source_id": route.get("distributor_id"),
                "safe_display_ref": route.get("distributor_name") or distributor_code,
                "tenant_code": route.get("tenant_code"),
                "sponsor_code": route.get("sponsor_code"),
                "distributor_code": distributor_code,
                "evidence": {
                    "route_id": route.get("route_id"),
                    "opportunity_id": route.get("opportunity_id"),
                    "opportunity_code": route.get("opportunity_code"),
                },
            }
        )

    return participants
