from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from utils.db import db_connection


SECRET_KEY_PARTS = (
    "api_key",
    "client_secret",
    "secret",
    "token",
    "signing_secret",
    "password",
    "private_key",
    "certificate",
    "credential",
)

LIVE_ACTION_KEY_PARTS = (
    "webhook_delivery",
    "wallet",
    "settlement",
    "fulfilment",
    "retry",
    "money_movement",
    "payout",
    "reservation",
    "publish_command",
    "activation_command",
    "activate_go_live",
    "create_tenant",
    "create_user",
    "send_invite",
    "deliver_webhook",
)


class UnsafeDraftPayloadError(ValueError):
    """Raised when a draft payload tries to store unsafe fields."""


class StaleDraftVersionError(ValueError):
    """Raised when an optimistic draft update does not match the current version."""


def _as_dict(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def _as_list(rows: Any) -> list[dict[str, Any]]:
    return [dict(row) for row in rows or []]


def _jsonb(value: Any, default: Any) -> str:
    return json.dumps(default if value is None else value, sort_keys=True)


def _normalize_key(key: Any) -> str:
    return str(key or "").strip().lower().replace("-", "_")


def _find_unsafe_key(value: Any, *, path: str = "") -> str | None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = _normalize_key(key)
            dotted = f"{path}.{normalized}" if path else normalized
            for part in SECRET_KEY_PARTS:
                if part in normalized:
                    return dotted
            for part in LIVE_ACTION_KEY_PARTS:
                if part in normalized:
                    return dotted
            nested = _find_unsafe_key(item, path=dotted)
            if nested:
                return nested

    if isinstance(value, list | tuple):
        for index, item in enumerate(value):
            nested = _find_unsafe_key(item, path=f"{path}[{index}]")
            if nested:
                return nested

    return None


def _ensure_safe_payload(value: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = dict(value or {})
    unsafe_key = _find_unsafe_key(payload)
    if unsafe_key:
        raise UnsafeDraftPayloadError(
            f"Unsafe onboarding draft payload key: {unsafe_key}"
        )
    return payload


async def create_draft(
    *,
    draft_ref: str,
    external_tenant_ref: str,
    organisation_ref: str,
    created_by_ref: str,
    created_by_role: str,
    contract_version: str = "onboarding.v1",
    status: str = "DRAFT_CREATED",
    producer_ref: str | None = None,
    sponsor_ref: str | None = None,
    distributor_ref: str | None = None,
    campaign_code: str | None = None,
    opportunity_ref: str | None = None,
    source: str = "ADMIN_ONBOARDING",
    correlation_id: str | None = None,
    safe_summary: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
    redactions: list[str] | None = None,
) -> dict[str, Any]:
    safe_summary_payload = _ensure_safe_payload(safe_summary)
    metadata_payload = _ensure_safe_payload(metadata)

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO onboarding_drafts (
                draft_ref,
                contract_version,
                status,
                external_tenant_ref,
                organisation_ref,
                producer_ref,
                sponsor_ref,
                distributor_ref,
                campaign_code,
                opportunity_ref,
                created_by_ref,
                created_by_role,
                source,
                correlation_id,
                safe_summary,
                metadata,
                redactions
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, $16, $17
            )
            RETURNING *
            """,
            draft_ref,
            contract_version,
            status,
            external_tenant_ref,
            organisation_ref,
            producer_ref,
            sponsor_ref,
            distributor_ref,
            campaign_code,
            opportunity_ref,
            created_by_ref,
            created_by_role,
            source,
            correlation_id,
            _jsonb(safe_summary_payload, {}),
            _jsonb(metadata_payload, {}),
            _jsonb(redactions, []),
        )

    return _as_dict(row) or {}


async def get_draft_by_ref(draft_ref: str) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM onboarding_drafts
            WHERE draft_ref = $1
            """,
            draft_ref,
        )

    return _as_dict(row)


async def list_drafts(
    *,
    external_tenant_ref: str | None = None,
    organisation_ref: str | None = None,
    status: str | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(int(limit or 25), 50))
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                draft_id,
                draft_ref,
                draft_version,
                status,
                external_tenant_ref,
                organisation_ref,
                producer_ref,
                sponsor_ref,
                distributor_ref,
                campaign_code,
                opportunity_ref,
                source,
                safe_summary,
                redactions,
                created_at,
                updated_at,
                expires_at
            FROM onboarding_drafts
            WHERE ($1::text IS NULL OR external_tenant_ref = $1)
              AND ($2::text IS NULL OR organisation_ref = $2)
              AND ($3::text IS NULL OR status = $3)
            ORDER BY updated_at DESC, created_at DESC
            LIMIT $4
            """,
            external_tenant_ref,
            organisation_ref,
            status,
            bounded_limit,
        )

    return _as_list(rows)


async def update_draft_metadata_or_status(
    *,
    draft_ref: str,
    expected_draft_version: int,
    status: str | None = None,
    metadata: Mapping[str, Any] | None = None,
    safe_summary: Mapping[str, Any] | None = None,
    updated_by_ref: str | None = None,
    correlation_id: str | None = None,
    redactions: list[str] | None = None,
) -> dict[str, Any]:
    metadata_payload = _ensure_safe_payload(metadata)
    safe_summary_payload = _ensure_safe_payload(safe_summary)

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE onboarding_drafts
            SET
                status = COALESCE($3, status),
                metadata = metadata || $4::jsonb,
                safe_summary = safe_summary || $5::jsonb,
                updated_by_ref = COALESCE($6, updated_by_ref),
                correlation_id = COALESCE($7, correlation_id),
                redactions = CASE
                    WHEN $8::jsonb = '[]'::jsonb THEN redactions
                    ELSE $8::jsonb
                END,
                draft_version = draft_version + 1,
                updated_at = NOW()
            WHERE draft_ref = $1
              AND draft_version = $2
            RETURNING *
            """,
            draft_ref,
            expected_draft_version,
            status,
            _jsonb(metadata_payload, {}),
            _jsonb(safe_summary_payload, {}),
            updated_by_ref,
            correlation_id,
            _jsonb(redactions, []),
        )

    if row is None:
        raise StaleDraftVersionError("Draft version is stale or draft is missing")
    return dict(row)


async def upsert_draft_section(
    *,
    draft_id: str,
    section_key: str,
    section_status: str,
    section_payload: Mapping[str, Any] | None = None,
    payload_hash: str | None = None,
    redaction_summary: Mapping[str, Any] | None = None,
    missing_evidence: list[dict[str, Any]] | None = None,
    source_warnings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload = _ensure_safe_payload(section_payload)
    redactions = _ensure_safe_payload(redaction_summary)

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO onboarding_draft_sections (
                draft_id,
                section_key,
                section_status,
                section_payload,
                payload_hash,
                redaction_summary,
                missing_evidence,
                source_warnings
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (draft_id, section_key)
            DO UPDATE SET
                section_status = EXCLUDED.section_status,
                section_payload = EXCLUDED.section_payload,
                payload_hash = EXCLUDED.payload_hash,
                redaction_summary = EXCLUDED.redaction_summary,
                missing_evidence = EXCLUDED.missing_evidence,
                source_warnings = EXCLUDED.source_warnings,
                section_version = onboarding_draft_sections.section_version + 1,
                updated_at = NOW()
            RETURNING *
            """,
            draft_id,
            section_key,
            section_status,
            _jsonb(payload, {}),
            payload_hash,
            _jsonb(redactions, {}),
            _jsonb(missing_evidence, []),
            _jsonb(source_warnings, []),
        )

    return _as_dict(row) or {}


async def get_draft_sections(draft_id: str) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM onboarding_draft_sections
            WHERE draft_id = $1
            ORDER BY section_key
            """,
            draft_id,
        )

    return _as_list(rows)


async def record_validation_result(
    *,
    draft_id: str,
    validation_scope: str,
    validation_status: str,
    draft_version: int | None = None,
    validation_type: str = "READINESS",
    safe_error_code: str | None = None,
    section_key: str | None = None,
    field_name: str | None = None,
    message: str | None = None,
    safe_errors: list[dict[str, Any]] | None = None,
    missing_evidence: list[dict[str, Any]] | None = None,
    blockers: list[dict[str, Any]] | None = None,
    warnings: list[dict[str, Any]] | None = None,
    readiness_preview: Mapping[str, Any] | None = None,
    details: Mapping[str, Any] | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    preview = _ensure_safe_payload(readiness_preview)
    safe_details = _ensure_safe_payload(details)

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO onboarding_draft_validation_results (
                draft_id,
                draft_version,
                validation_scope,
                validation_type,
                validation_status,
                safe_error_code,
                section_key,
                field_name,
                message,
                safe_errors,
                missing_evidence,
                blockers,
                warnings,
                readiness_preview,
                details,
                correlation_id
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8,
                $9, $10, $11, $12, $13, $14, $15, $16
            )
            RETURNING *
            """,
            draft_id,
            draft_version,
            validation_scope,
            validation_type,
            validation_status,
            safe_error_code,
            section_key,
            field_name,
            message,
            _jsonb(safe_errors, []),
            _jsonb(missing_evidence, []),
            _jsonb(blockers, []),
            _jsonb(warnings, []),
            _jsonb(preview, {}),
            _jsonb(safe_details, {}),
            correlation_id,
        )

    return _as_dict(row) or {}


async def record_idempotency_reference(
    *,
    idempotency_key_hash: str,
    scope_hash: str,
    actor_ref: str,
    external_tenant_ref: str,
    operation_type: str,
    request_hash: str,
    result_status: str,
    draft_id: str | None = None,
    draft_ref: str | None = None,
    response_hash: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO onboarding_draft_idempotency_keys (
                draft_id,
                draft_ref,
                idempotency_key_hash,
                scope_hash,
                actor_ref,
                external_tenant_ref,
                operation_type,
                request_hash,
                response_hash,
                result_status,
                correlation_id
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (idempotency_key_hash, scope_hash)
            DO UPDATE SET
                last_seen_at = NOW()
            RETURNING *
            """,
            draft_id,
            draft_ref,
            idempotency_key_hash,
            scope_hash,
            actor_ref,
            external_tenant_ref,
            operation_type,
            request_hash,
            response_hash,
            result_status,
            correlation_id,
        )

    return _as_dict(row) or {}


async def get_idempotency_reference(
    *,
    idempotency_key_hash: str,
    scope_hash: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM onboarding_draft_idempotency_keys
            WHERE idempotency_key_hash = $1
              AND scope_hash = $2
            """,
            idempotency_key_hash,
            scope_hash,
        )

    return _as_dict(row)


async def create_audit_link_reference(
    *,
    draft_id: str,
    draft_ref: str,
    action_type: str,
    action_status: str,
    actor_ref: str,
    actor_role: str,
    correlation_id: str,
    evidence_type: str,
    draft_version: int | None = None,
    audit_ref: str | None = None,
    event_ref: str | None = None,
    idempotency_id: str | None = None,
    before_state_hash: str | None = None,
    after_state_hash: str | None = None,
    changed_sections: list[str] | None = None,
    redactions: list[str] | None = None,
    evidence_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    safe_evidence = _ensure_safe_payload(evidence_summary)

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO onboarding_draft_audit_links (
                draft_id,
                draft_ref,
                draft_version,
                action_type,
                action_status,
                actor_ref,
                actor_role,
                audit_ref,
                event_ref,
                idempotency_id,
                correlation_id,
                before_state_hash,
                after_state_hash,
                changed_sections,
                redactions,
                evidence_type,
                evidence_summary
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8,
                $9, $10, $11, $12, $13, $14, $15, $16, $17
            )
            RETURNING *
            """,
            draft_id,
            draft_ref,
            draft_version,
            action_type,
            action_status,
            actor_ref,
            actor_role,
            audit_ref,
            event_ref,
            idempotency_id,
            correlation_id,
            before_state_hash,
            after_state_hash,
            _jsonb(changed_sections, []),
            _jsonb(redactions, []),
            evidence_type,
            _jsonb(safe_evidence, {}),
        )

    return _as_dict(row) or {}
