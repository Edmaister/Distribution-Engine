from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from utils.db import db_connection


SUPPORT_CASE_CREATED_EVENT = "SUPPORT_CASE_CREATED"
SUPPORT_CASE_NOTE_ADDED_EVENT = "SUPPORT_CASE_NOTE_ADDED"
SUPPORT_CASE_STATUS_CHANGED_EVENT = "SUPPORT_CASE_STATUS_CHANGED"
SUPPORT_CASE_RECORDED = "RECORDED"
SUPPORT_CASE_REPLAYED = "REPLAYED"
SUPPORT_CASE_NOTE_TYPES = frozenset(
    {"OPERATOR_NOTE", "CUSTOMER_UPDATE", "EVIDENCE_SUMMARY", "RESOLUTION_NOTE"}
)
SUPPORT_CASE_GUARDRAILS = [
    "CUSTOMER_SCOPED_SUPPORT_CASE",
    "ACCOUNT_SCOPE_RESOLVED_INTERNALLY",
    "NO_TENANT_CODE_EXPOSURE",
    "NO_REPAIR_REPLAY_RETRY",
    "NO_REFERRAL_MUTATION",
    "NO_CAMPAIGN_MUTATION",
    "NO_PROGRESS_OR_ATTRIBUTION_MUTATION",
    "NO_REPORT_OR_EXPORT_MUTATION",
    "NO_ACCESS_OR_ACCOUNT_LIFECYCLE_MUTATION",
    "NO_INVITE_DELIVERY",
    "NO_CREDENTIAL_OR_AUTH_CLAIM_CHANGE",
    "NO_BILLING_OR_MONEY_MOVEMENT",
]
SUPPORT_CASE_REDACTIONS = [
    "internal_tenant_identifier",
    "raw_ucn",
    "provider_payload",
    "audit_payload",
    "dlq_payload",
    "secret",
    "token",
    "credential",
    "sql_error",
    "stack_trace",
    "idempotency_key_hash",
    "payload_hash",
]
SUPPORT_CASE_CATEGORIES = frozenset(
    {
        "VALIDATION_RECOVERY",
        "PROGRESS_DIAGNOSTIC",
        "ATTRIBUTION_REVIEW",
        "READINESS_BLOCKER",
        "REPORTING_FRESHNESS",
        "INTEGRATION_HEALTH",
        "ACCESS_SCOPE",
        "MANUAL_REVIEW_REQUIRED",
    }
)
SUPPORT_CASE_PRIORITIES = frozenset({"LOW", "MEDIUM", "HIGH", "CRITICAL"})
SUPPORT_CASE_STATUSES = frozenset(
    {"OPEN", "INVESTIGATING", "WAITING", "RESOLVED", "CLOSED"}
)
SUPPORT_CASE_EVIDENCE_TYPES = frozenset(
    {
        "LINK_CODE_INSPECTION",
        "ATTRIBUTION_TRACE",
        "PROGRESS_STATUS",
        "CAMPAIGN_READINESS",
        "REPORTING_EVIDENCE",
        "TECHNICAL_SETUP",
        "PEOPLE_ACCESS",
        "OPERATOR_NOTE",
    }
)
SAFE_SOURCE_SURFACES = frozenset(
    {
        "support_hub",
        "link_inspection",
        "attribution_trace",
        "progress_status",
        "reports",
        "customer_home",
        "account_health",
        "people_access",
        "technical_setup",
        "campaigns",
    }
)
FORBIDDEN_METADATA_KEYS = {
    "tenant_code",
    "tenantCode",
    "internal_tenant_code",
    "internalTenantCode",
    "raw_ucn",
    "rawUcn",
    "provider_payload",
    "providerPayload",
    "audit_payload",
    "auditPayload",
    "dlq_payload",
    "dlqPayload",
    "secret",
    "token",
    "credential",
    "sql_error",
    "sqlError",
    "stack_trace",
    "stackTrace",
}
MAX_CASE_LIST_LIMIT = 100


class ReferralSaasSupportCaseCommandError(Exception):
    safe_code = "SUPPORT_CASE_COMMAND_ERROR"


class SupportCaseValidationError(ReferralSaasSupportCaseCommandError):
    safe_code = "VALIDATION_ERROR"


class SupportCaseNotFound(ReferralSaasSupportCaseCommandError):
    safe_code = "SUPPORT_CASE_NOT_FOUND"


class SupportCaseIdempotencyConflict(ReferralSaasSupportCaseCommandError):
    safe_code = "IDEMPOTENCY_CONFLICT"


class SupportCaseUnsafePayload(ReferralSaasSupportCaseCommandError):
    safe_code = "REJECTED_UNSAFE_PAYLOAD"


@dataclass(frozen=True)
class SupportCaseEvidenceLink:
    evidence_link_id: str | None
    evidence_type: str
    evidence_ref: str
    safe_status: str | None
    warning_code: str | None
    missing_evidence_code: str | None
    redactions: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "evidenceLinkId": self.evidence_link_id,
            "evidenceType": self.evidence_type,
            "evidenceRef": self.evidence_ref,
            "safeStatus": self.safe_status,
            "warningCode": self.warning_code,
            "missingEvidenceCode": self.missing_evidence_code,
            "redactions": self.redactions,
        }


@dataclass(frozen=True)
class SupportCaseNote:
    note_ref: str
    case_ref: str
    note_type: str
    note_text: str
    correlation_id: str | None
    created_by_ref: str
    created_by_role: str | None
    created_at: str | None
    redactions: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "noteRef": self.note_ref,
            "caseRef": self.case_ref,
            "noteType": self.note_type,
            "noteText": self.note_text,
            "correlationId": self.correlation_id,
            "createdByRef": self.created_by_ref,
            "createdByRole": self.created_by_role,
            "createdAt": self.created_at,
            "redactions": self.redactions,
        }


@dataclass(frozen=True)
class SupportCaseStatusEvent:
    status_event_ref: str
    case_ref: str
    from_status: str
    to_status: str
    transition_reason: str
    correlation_id: str | None
    changed_by_ref: str
    changed_by_role: str | None
    created_at: str | None
    redactions: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "statusEventRef": self.status_event_ref,
            "caseRef": self.case_ref,
            "fromStatus": self.from_status,
            "toStatus": self.to_status,
            "transitionReason": self.transition_reason,
            "correlationId": self.correlation_id,
            "changedByRef": self.changed_by_ref,
            "changedByRole": self.changed_by_role,
            "createdAt": self.created_at,
            "redactions": self.redactions,
        }


@dataclass(frozen=True)
class ReferralSaasSupportCase:
    case_ref: str
    account_ref: str
    category: str
    priority: str
    status: str
    title: str
    summary: str
    source_surface: str | None
    assignee_ref: str | None
    correlation_id: str | None
    created_by_ref: str
    created_by_role: str | None
    created_at: str | None
    updated_at: str | None
    evidence_links: list[SupportCaseEvidenceLink]
    notes: list[SupportCaseNote]
    status_events: list[SupportCaseStatusEvent]
    redactions: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "caseRef": self.case_ref,
            "accountRef": self.account_ref,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "title": self.title,
            "summary": self.summary,
            "sourceSurface": self.source_surface,
            "assigneeRef": self.assignee_ref,
            "correlationId": self.correlation_id,
            "createdByRef": self.created_by_ref,
            "createdByRole": self.created_by_role,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "evidenceLinks": [link.to_safe_dict() for link in self.evidence_links],
            "notes": [note.to_safe_dict() for note in self.notes],
            "statusEvents": [event.to_safe_dict() for event in self.status_events],
            "redactions": self.redactions,
        }


@dataclass(frozen=True)
class ReferralSaasSupportCaseCreateResult:
    command_status: str
    support_case: ReferralSaasSupportCase
    idempotency_status: str
    audit_event_id: str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "supportCase": self.support_case.to_safe_dict(),
            "idempotency": {"status": self.idempotency_status},
            "audit": {"accountAuditEventId": self.audit_event_id},
            "guardrails": SUPPORT_CASE_GUARDRAILS,
            "redactions": SUPPORT_CASE_REDACTIONS,
        }


@dataclass(frozen=True)
class ReferralSaasSupportCaseNoteResult:
    command_status: str
    support_case: ReferralSaasSupportCase
    note: SupportCaseNote
    idempotency_status: str
    audit_event_id: str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "supportCase": self.support_case.to_safe_dict(),
            "note": self.note.to_safe_dict(),
            "idempotency": {"status": self.idempotency_status},
            "audit": {"accountAuditEventId": self.audit_event_id},
            "guardrails": SUPPORT_CASE_GUARDRAILS,
            "redactions": SUPPORT_CASE_REDACTIONS,
        }


@dataclass(frozen=True)
class ReferralSaasSupportCaseStatusResult:
    command_status: str
    support_case: ReferralSaasSupportCase
    status_event: SupportCaseStatusEvent
    idempotency_status: str
    audit_event_id: str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "supportCase": self.support_case.to_safe_dict(),
            "statusEvent": self.status_event.to_safe_dict(),
            "idempotency": {"status": self.idempotency_status},
            "audit": {"accountAuditEventId": self.audit_event_id},
            "guardrails": SUPPORT_CASE_GUARDRAILS,
            "redactions": SUPPORT_CASE_REDACTIONS,
        }


def _jsonb(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _optional_text(value: Any) -> str | None:
    safe_value = _clean_text(value)
    return safe_value or None


def _as_iso(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _normalise_choice(value: Any, allowed: frozenset[str], field_name: str) -> str:
    safe_value = _clean_text(value).upper()
    if safe_value not in allowed:
        raise SupportCaseValidationError(
            f"{field_name} must be one of: {', '.join(sorted(allowed))}."
        )
    return safe_value


def _require_bounded_text(
    value: Any, field_name: str, *, min_length: int, max_length: int
) -> str:
    safe_value = _clean_text(value)
    if not (min_length <= len(safe_value) <= max_length):
        raise SupportCaseValidationError(
            f"{field_name} must be between {min_length} and {max_length} characters."
        )
    return safe_value


def _assert_safe_metadata(value: Any, path: str = "metadata") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key) in FORBIDDEN_METADATA_KEYS:
                raise SupportCaseUnsafePayload(
                    f"{path}.{key} is not allowed in support-case evidence."
                )
            _assert_safe_metadata(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _assert_safe_metadata(nested, f"{path}[{index}]")


def _normalise_evidence_links(
    evidence_links: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    normalised_links: list[dict[str, Any]] = []
    for raw_link in evidence_links or []:
        if not isinstance(raw_link, dict):
            raise SupportCaseValidationError("Each evidence link must be an object.")
        metadata = raw_link.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise SupportCaseValidationError("evidenceLinks.metadata must be an object.")
        _assert_safe_metadata(metadata, "evidenceLinks.metadata")
        redactions = sorted(
            {
                *_normalise_redactions(raw_link.get("redactions")),
                *SUPPORT_CASE_REDACTIONS,
            }
        )
        normalised_links.append(
            {
                "evidence_type": _normalise_choice(
                    raw_link.get("evidenceType") or raw_link.get("evidence_type"),
                    SUPPORT_CASE_EVIDENCE_TYPES,
                    "evidenceType",
                ),
                "evidence_ref": _require_bounded_text(
                    raw_link.get("evidenceRef") or raw_link.get("evidence_ref"),
                    "evidenceRef",
                    min_length=1,
                    max_length=256,
                ),
                "safe_status": _optional_text(
                    raw_link.get("safeStatus") or raw_link.get("safe_status")
                ),
                "warning_code": _optional_text(
                    raw_link.get("warningCode") or raw_link.get("warning_code")
                ),
                "missing_evidence_code": _optional_text(
                    raw_link.get("missingEvidenceCode")
                    or raw_link.get("missing_evidence_code")
                ),
                "metadata": metadata,
                "redactions": redactions,
            }
        )
    return normalised_links


def _normalise_redactions(value: Any) -> list[str]:
    if not value:
        return []
    if not isinstance(value, list):
        raise SupportCaseValidationError("redactions must be a list.")
    return sorted({_clean_text(item) for item in value if _clean_text(item)})


def _support_case_from_row(
    row: Any,
    evidence_links: list[SupportCaseEvidenceLink] | None = None,
    notes: list[SupportCaseNote] | None = None,
    status_events: list[SupportCaseStatusEvent] | None = None,
) -> ReferralSaasSupportCase:
    return ReferralSaasSupportCase(
        case_ref=str(row["support_case_id"]),
        account_ref=str(row["account_id"]),
        category=str(row["category"]),
        priority=str(row["priority"]),
        status=str(row["status"]),
        title=str(row["title"]),
        summary=str(row["summary"]),
        source_surface=_optional_text(row.get("source_surface")),
        assignee_ref=_optional_text(row.get("assignee_ref")),
        correlation_id=_optional_text(row.get("correlation_id")),
        created_by_ref=str(row["created_by_ref"]),
        created_by_role=_optional_text(row.get("created_by_role")),
        created_at=_as_iso(row.get("created_at")),
        updated_at=_as_iso(row.get("updated_at")),
        evidence_links=evidence_links or [],
        notes=notes or [],
        status_events=status_events or [],
        redactions=_safe_json_list(row.get("redactions")),
    )


def _evidence_link_from_row(row: Any) -> SupportCaseEvidenceLink:
    return SupportCaseEvidenceLink(
        evidence_link_id=str(row["evidence_link_id"]),
        evidence_type=str(row["evidence_type"]),
        evidence_ref=str(row["evidence_ref"]),
        safe_status=_optional_text(row.get("safe_status")),
        warning_code=_optional_text(row.get("warning_code")),
        missing_evidence_code=_optional_text(row.get("missing_evidence_code")),
        redactions=_safe_json_list(row.get("redactions")),
    )


def _note_from_row(row: Any) -> SupportCaseNote:
    return SupportCaseNote(
        note_ref=str(row["support_case_note_id"]),
        case_ref=str(row["support_case_id"]),
        note_type=str(row["note_type"]),
        note_text=str(row["note_text"]),
        correlation_id=_optional_text(row.get("correlation_id")),
        created_by_ref=str(row["created_by_ref"]),
        created_by_role=_optional_text(row.get("created_by_role")),
        created_at=_as_iso(row.get("created_at")),
        redactions=_safe_json_list(row.get("redactions")),
    )


def _status_event_from_row(row: Any) -> SupportCaseStatusEvent:
    return SupportCaseStatusEvent(
        status_event_ref=str(row["support_case_status_event_id"]),
        case_ref=str(row["support_case_id"]),
        from_status=str(row["from_status"]),
        to_status=str(row["to_status"]),
        transition_reason=str(row["transition_reason"]),
        correlation_id=_optional_text(row.get("correlation_id")),
        changed_by_ref=str(row["changed_by_ref"]),
        changed_by_role=_optional_text(row.get("changed_by_role")),
        created_at=_as_iso(row.get("created_at")),
        redactions=_safe_json_list(row.get("redactions")),
    )


def _safe_json_list(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return []
    if isinstance(value, list):
        return [_clean_text(item) for item in value if _clean_text(item)]
    return []


async def create_referral_saas_support_case(
    *,
    account_id: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    tenant_code: str,
    category: str,
    priority: str,
    title: str,
    summary: str,
    source_surface: str | None,
    evidence_links: list[dict[str, Any]] | None,
    reason_code: str | None,
    correlation_id: str | None,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
) -> ReferralSaasSupportCaseCreateResult:
    safe_account_id = _require_bounded_text(
        account_id, "account_id", min_length=1, max_length=80
    )
    safe_tenant_code = _require_bounded_text(
        tenant_code, "tenant_code", min_length=1, max_length=120
    )
    safe_category = _normalise_choice(category, SUPPORT_CASE_CATEGORIES, "category")
    safe_priority = _normalise_choice(priority, SUPPORT_CASE_PRIORITIES, "priority")
    safe_title = _require_bounded_text(title, "title", min_length=3, max_length=160)
    safe_summary = _require_bounded_text(
        summary, "summary", min_length=3, max_length=2000
    )
    safe_source_surface = _optional_text(source_surface)
    if safe_source_surface and safe_source_surface not in SAFE_SOURCE_SURFACES:
        raise SupportCaseValidationError(
            f"sourceSurface must be one of: {', '.join(sorted(SAFE_SOURCE_SURFACES))}."
        )
    safe_idempotency_hash = _require_bounded_text(
        idempotency_key_hash,
        "idempotency_key_hash",
        min_length=1,
        max_length=256,
    )
    safe_payload_hash = _require_bounded_text(
        request_payload_hash, "request_payload_hash", min_length=1, max_length=256
    )
    safe_actor_ref = _require_bounded_text(
        actor_ref, "actor_ref", min_length=1, max_length=160
    )
    safe_actor_role = _optional_text(actor_role)
    safe_reason_code = _optional_text(reason_code) or "CUSTOMER_SUPPORT_CASE_CREATED"
    safe_correlation_id = _optional_text(correlation_id)
    safe_evidence_links = _normalise_evidence_links(evidence_links)
    redactions = sorted(
        {
            *SUPPORT_CASE_REDACTIONS,
            *[
                redaction
                for link in safe_evidence_links
                for redaction in link.get("redactions", [])
            ],
        }
    )

    async with db_connection() as conn:
        existing_case = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_support_cases
            WHERE account_id = $1
              AND idempotency_key_hash = $2
              AND archived_at IS NULL
            LIMIT 1
            """,
            safe_account_id,
            safe_idempotency_hash,
        )
        if existing_case:
            if _optional_text(existing_case.get("request_payload_hash")) != safe_payload_hash:
                raise SupportCaseIdempotencyConflict(
                    "Idempotency key was reused with different support-case content."
                )
            evidence_rows = await conn.fetch(
                """
                SELECT *
                FROM referral_saas_support_case_evidence_links
                WHERE support_case_id = $1
                ORDER BY created_at, evidence_link_id
                """,
                existing_case["support_case_id"],
            )
            return ReferralSaasSupportCaseCreateResult(
                command_status="SUPPORT_CASE_REPLAYED",
                support_case=_support_case_from_row(
                    existing_case,
                    [_evidence_link_from_row(row) for row in evidence_rows],
                ),
                idempotency_status=SUPPORT_CASE_REPLAYED,
                audit_event_id=None,
            )

        async with conn.transaction():
            case_row = await conn.fetchrow(
                """
                INSERT INTO referral_saas_support_cases (
                    account_id,
                    account_tenant_id,
                    external_ref_id,
                    tenant_code,
                    category,
                    priority,
                    status,
                    title,
                    summary,
                    source_surface,
                    assignee_ref,
                    reason_code,
                    correlation_id,
                    idempotency_key_hash,
                    request_payload_hash,
                    created_by_ref,
                    created_by_role,
                    updated_by_ref,
                    metadata,
                    redactions
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, 'OPEN', $7, $8, $9, NULL,
                    $10, $11, $12, $13, $14, $15, $14, $16::jsonb, $17::jsonb
                )
                RETURNING *
                """,
                safe_account_id,
                _optional_text(account_tenant_id),
                _optional_text(external_ref_id),
                safe_tenant_code,
                safe_category,
                safe_priority,
                safe_title,
                safe_summary,
                safe_source_surface,
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                safe_payload_hash,
                safe_actor_ref,
                safe_actor_role,
                _jsonb(
                    {
                        "source_surface": safe_source_surface,
                        "evidence_link_count": len(safe_evidence_links),
                        "no_repair_replay_retry_confirmed": True,
                        "no_billing_or_money_movement_confirmed": True,
                    }
                ),
                _jsonb(redactions),
            )

            evidence_rows = []
            for link in safe_evidence_links:
                evidence_row = await conn.fetchrow(
                    """
                    INSERT INTO referral_saas_support_case_evidence_links (
                        support_case_id,
                        account_id,
                        evidence_type,
                        evidence_ref,
                        safe_status,
                        warning_code,
                        missing_evidence_code,
                        metadata,
                        redactions
                    )
                    VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb
                    )
                    RETURNING *
                    """,
                    case_row["support_case_id"],
                    safe_account_id,
                    link["evidence_type"],
                    link["evidence_ref"],
                    link["safe_status"],
                    link["warning_code"],
                    link["missing_evidence_code"],
                    _jsonb(link["metadata"]),
                    _jsonb(link["redactions"]),
                )
                evidence_rows.append(evidence_row)

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
                    NULL, 'OPEN', $9, $10, $11, $12::jsonb, $13::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                _optional_text(account_tenant_id),
                _optional_text(external_ref_id),
                safe_tenant_code,
                SUPPORT_CASE_CREATED_EVENT,
                SUPPORT_CASE_RECORDED,
                safe_actor_ref,
                safe_actor_role,
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(
                    {
                        "support_case_id": str(case_row["support_case_id"]),
                        "category": safe_category,
                        "priority": safe_priority,
                        "status": "OPEN",
                        "source_surface": safe_source_surface,
                        "evidence_link_count": len(evidence_rows),
                        "request_payload_hash": safe_payload_hash,
                        "no_repair_replay_retry_confirmed": True,
                        "no_billing_or_money_movement_confirmed": True,
                    }
                ),
                _jsonb(redactions),
            )

    return ReferralSaasSupportCaseCreateResult(
        command_status="SUPPORT_CASE_RECORDED",
        support_case=_support_case_from_row(
            case_row, [_evidence_link_from_row(row) for row in evidence_rows]
        ),
        idempotency_status=SUPPORT_CASE_RECORDED,
        audit_event_id=str(audit_event["account_audit_event_id"]) if audit_event else None,
    )


async def list_referral_saas_support_cases(
    *,
    account_id: str,
    status_filter: str | None = None,
    limit: int = 50,
) -> list[ReferralSaasSupportCase]:
    safe_account_id = _require_bounded_text(
        account_id, "account_id", min_length=1, max_length=80
    )
    safe_limit = max(1, min(int(limit or 50), MAX_CASE_LIST_LIMIT))
    safe_status = None
    if status_filter:
        safe_status = _normalise_choice(status_filter, SUPPORT_CASE_STATUSES, "status")

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM referral_saas_support_cases
            WHERE account_id = $1
              AND archived_at IS NULL
              AND ($2::text IS NULL OR status = $2)
            ORDER BY created_at DESC, support_case_id DESC
            LIMIT $3
            """,
            safe_account_id,
            safe_status,
            safe_limit,
        )
    return [_support_case_from_row(row) for row in rows]


async def get_referral_saas_support_case(
    *,
    account_id: str,
    case_ref: str,
) -> ReferralSaasSupportCase:
    safe_account_id = _require_bounded_text(
        account_id, "account_id", min_length=1, max_length=80
    )
    safe_case_ref = _require_bounded_text(
        case_ref, "case_ref", min_length=1, max_length=80
    )
    async with db_connection() as conn:
        case_row = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_support_cases
            WHERE account_id = $1
              AND support_case_id = $2
              AND archived_at IS NULL
            LIMIT 1
            """,
            safe_account_id,
            safe_case_ref,
        )
        if not case_row:
            raise SupportCaseNotFound("Support case was not found for this account.")
        evidence_rows = await conn.fetch(
            """
            SELECT *
            FROM referral_saas_support_case_evidence_links
            WHERE support_case_id = $1
            ORDER BY created_at, evidence_link_id
            """,
            case_row["support_case_id"],
        )
        note_rows = await conn.fetch(
            """
            SELECT *
            FROM referral_saas_support_case_notes
            WHERE support_case_id = $1
              AND archived_at IS NULL
            ORDER BY created_at, support_case_note_id
            """,
            case_row["support_case_id"],
        )
        status_event_rows = await conn.fetch(
            """
            SELECT *
            FROM referral_saas_support_case_status_events
            WHERE support_case_id = $1
              AND archived_at IS NULL
            ORDER BY created_at, support_case_status_event_id
            """,
            case_row["support_case_id"],
        )
    return _support_case_from_row(
        case_row,
        [_evidence_link_from_row(row) for row in evidence_rows],
        [_note_from_row(row) for row in note_rows],
        [_status_event_from_row(row) for row in status_event_rows],
    )


async def add_referral_saas_support_case_note(
    *,
    account_id: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    tenant_code: str,
    case_ref: str,
    note_type: str,
    note_text: str,
    reason_code: str | None,
    correlation_id: str | None,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
) -> ReferralSaasSupportCaseNoteResult:
    safe_account_id = _require_bounded_text(
        account_id, "account_id", min_length=1, max_length=80
    )
    safe_tenant_code = _require_bounded_text(
        tenant_code, "tenant_code", min_length=1, max_length=120
    )
    safe_case_ref = _require_bounded_text(
        case_ref, "case_ref", min_length=1, max_length=80
    )
    safe_note_type = _normalise_choice(note_type, SUPPORT_CASE_NOTE_TYPES, "noteType")
    safe_note_text = _require_bounded_text(
        note_text, "noteText", min_length=2, max_length=2000
    )
    safe_idempotency_hash = _require_bounded_text(
        idempotency_key_hash,
        "idempotency_key_hash",
        min_length=1,
        max_length=256,
    )
    safe_payload_hash = _require_bounded_text(
        request_payload_hash, "request_payload_hash", min_length=1, max_length=256
    )
    safe_actor_ref = _require_bounded_text(
        actor_ref, "actor_ref", min_length=1, max_length=160
    )
    safe_actor_role = _optional_text(actor_role)
    safe_reason_code = _optional_text(reason_code) or "CUSTOMER_SUPPORT_CASE_NOTE_ADDED"
    safe_correlation_id = _optional_text(correlation_id)
    redactions = sorted(SUPPORT_CASE_REDACTIONS)

    async with db_connection() as conn:
        case_row = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_support_cases
            WHERE account_id = $1
              AND support_case_id = $2
              AND archived_at IS NULL
            LIMIT 1
            """,
            safe_account_id,
            safe_case_ref,
        )
        if not case_row:
            raise SupportCaseNotFound("Support case was not found for this account.")

        existing_note = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_support_case_notes
            WHERE support_case_id = $1
              AND idempotency_key_hash = $2
              AND archived_at IS NULL
            LIMIT 1
            """,
            case_row["support_case_id"],
            safe_idempotency_hash,
        )
        if existing_note:
            if _optional_text(existing_note.get("request_payload_hash")) != safe_payload_hash:
                raise SupportCaseIdempotencyConflict(
                    "Idempotency key was reused with different support-case note content."
                )
            return ReferralSaasSupportCaseNoteResult(
                command_status="SUPPORT_CASE_NOTE_REPLAYED",
                support_case=_support_case_from_row(case_row),
                note=_note_from_row(existing_note),
                idempotency_status=SUPPORT_CASE_REPLAYED,
                audit_event_id=None,
            )

        async with conn.transaction():
            note_row = await conn.fetchrow(
                """
                INSERT INTO referral_saas_support_case_notes (
                    support_case_id,
                    account_id,
                    note_type,
                    note_text,
                    reason_code,
                    correlation_id,
                    idempotency_key_hash,
                    request_payload_hash,
                    created_by_ref,
                    created_by_role,
                    metadata,
                    redactions
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11::jsonb, $12::jsonb
                )
                RETURNING *
                """,
                case_row["support_case_id"],
                safe_account_id,
                safe_note_type,
                safe_note_text,
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                safe_payload_hash,
                safe_actor_ref,
                safe_actor_role,
                _jsonb(
                    {
                        "note_type": safe_note_type,
                        "no_repair_replay_retry_confirmed": True,
                        "no_billing_or_money_movement_confirmed": True,
                    }
                ),
                _jsonb(redactions),
            )
            case_row = await conn.fetchrow(
                """
                UPDATE referral_saas_support_cases
                SET updated_by_ref = $3,
                    updated_at = now()
                WHERE account_id = $1
                  AND support_case_id = $2
                RETURNING *
                """,
                safe_account_id,
                case_row["support_case_id"],
                safe_actor_ref,
            )
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
                    $9, $9, $10, $11, $12, $13::jsonb, $14::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                _optional_text(account_tenant_id),
                _optional_text(external_ref_id),
                safe_tenant_code,
                SUPPORT_CASE_NOTE_ADDED_EVENT,
                SUPPORT_CASE_RECORDED,
                safe_actor_ref,
                safe_actor_role,
                case_row["status"],
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(
                    {
                        "support_case_id": str(case_row["support_case_id"]),
                        "support_case_note_id": str(note_row["support_case_note_id"]),
                        "note_type": safe_note_type,
                        "request_payload_hash": safe_payload_hash,
                        "no_repair_replay_retry_confirmed": True,
                        "no_billing_or_money_movement_confirmed": True,
                    }
                ),
                _jsonb(redactions),
            )

    return ReferralSaasSupportCaseNoteResult(
        command_status="SUPPORT_CASE_NOTE_RECORDED",
        support_case=_support_case_from_row(case_row, notes=[_note_from_row(note_row)]),
        note=_note_from_row(note_row),
        idempotency_status=SUPPORT_CASE_RECORDED,
        audit_event_id=str(audit_event["account_audit_event_id"]) if audit_event else None,
    )


async def change_referral_saas_support_case_status(
    *,
    account_id: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    tenant_code: str,
    case_ref: str,
    to_status: str,
    transition_reason: str,
    reason_code: str | None,
    correlation_id: str | None,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
) -> ReferralSaasSupportCaseStatusResult:
    safe_account_id = _require_bounded_text(
        account_id, "account_id", min_length=1, max_length=80
    )
    safe_tenant_code = _require_bounded_text(
        tenant_code, "tenant_code", min_length=1, max_length=120
    )
    safe_case_ref = _require_bounded_text(
        case_ref, "case_ref", min_length=1, max_length=80
    )
    safe_to_status = _normalise_choice(to_status, SUPPORT_CASE_STATUSES, "status")
    safe_transition_reason = _require_bounded_text(
        transition_reason, "transitionReason", min_length=3, max_length=1000
    )
    safe_idempotency_hash = _require_bounded_text(
        idempotency_key_hash,
        "idempotency_key_hash",
        min_length=1,
        max_length=256,
    )
    safe_payload_hash = _require_bounded_text(
        request_payload_hash, "request_payload_hash", min_length=1, max_length=256
    )
    safe_actor_ref = _require_bounded_text(
        actor_ref, "actor_ref", min_length=1, max_length=160
    )
    safe_actor_role = _optional_text(actor_role)
    safe_reason_code = _optional_text(reason_code) or "CUSTOMER_SUPPORT_CASE_STATUS_CHANGED"
    safe_correlation_id = _optional_text(correlation_id)
    redactions = sorted(SUPPORT_CASE_REDACTIONS)

    async with db_connection() as conn:
        case_row = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_support_cases
            WHERE account_id = $1
              AND support_case_id = $2
              AND archived_at IS NULL
            LIMIT 1
            """,
            safe_account_id,
            safe_case_ref,
        )
        if not case_row:
            raise SupportCaseNotFound("Support case was not found for this account.")

        existing_event = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_support_case_status_events
            WHERE support_case_id = $1
              AND idempotency_key_hash = $2
              AND archived_at IS NULL
            LIMIT 1
            """,
            case_row["support_case_id"],
            safe_idempotency_hash,
        )
        if existing_event:
            if _optional_text(existing_event.get("request_payload_hash")) != safe_payload_hash:
                raise SupportCaseIdempotencyConflict(
                    "Idempotency key was reused with different support-case status content."
                )
            return ReferralSaasSupportCaseStatusResult(
                command_status="SUPPORT_CASE_STATUS_REPLAYED",
                support_case=_support_case_from_row(case_row),
                status_event=_status_event_from_row(existing_event),
                idempotency_status=SUPPORT_CASE_REPLAYED,
                audit_event_id=None,
            )

        safe_from_status = str(case_row["status"])
        if safe_from_status == safe_to_status:
            raise SupportCaseValidationError(
                "status must be different from the current support-case status."
            )

        async with conn.transaction():
            status_event_row = await conn.fetchrow(
                """
                INSERT INTO referral_saas_support_case_status_events (
                    support_case_id,
                    account_id,
                    from_status,
                    to_status,
                    transition_reason,
                    reason_code,
                    correlation_id,
                    idempotency_key_hash,
                    request_payload_hash,
                    changed_by_ref,
                    changed_by_role,
                    metadata,
                    redactions
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12::jsonb, $13::jsonb
                )
                RETURNING *
                """,
                case_row["support_case_id"],
                safe_account_id,
                safe_from_status,
                safe_to_status,
                safe_transition_reason,
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                safe_payload_hash,
                safe_actor_ref,
                safe_actor_role,
                _jsonb(
                    {
                        "from_status": safe_from_status,
                        "to_status": safe_to_status,
                        "no_repair_replay_retry_confirmed": True,
                        "no_billing_or_money_movement_confirmed": True,
                    }
                ),
                _jsonb(redactions),
            )
            updated_case_row = await conn.fetchrow(
                """
                UPDATE referral_saas_support_cases
                SET status = $3,
                    updated_by_ref = $4,
                    updated_at = now(),
                    closed_at = CASE WHEN $3 = 'CLOSED' THEN now() ELSE closed_at END
                WHERE account_id = $1
                  AND support_case_id = $2
                RETURNING *
                """,
                safe_account_id,
                case_row["support_case_id"],
                safe_to_status,
                safe_actor_ref,
            )
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
                    $9, $10, $11, $12, $13, $14::jsonb, $15::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                _optional_text(account_tenant_id),
                _optional_text(external_ref_id),
                safe_tenant_code,
                SUPPORT_CASE_STATUS_CHANGED_EVENT,
                SUPPORT_CASE_RECORDED,
                safe_actor_ref,
                safe_actor_role,
                safe_from_status,
                safe_to_status,
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(
                    {
                        "support_case_id": str(case_row["support_case_id"]),
                        "support_case_status_event_id": str(
                            status_event_row["support_case_status_event_id"]
                        ),
                        "from_status": safe_from_status,
                        "to_status": safe_to_status,
                        "request_payload_hash": safe_payload_hash,
                        "no_repair_replay_retry_confirmed": True,
                        "no_billing_or_money_movement_confirmed": True,
                    }
                ),
                _jsonb(redactions),
            )

    return ReferralSaasSupportCaseStatusResult(
        command_status="SUPPORT_CASE_STATUS_RECORDED",
        support_case=_support_case_from_row(
            updated_case_row,
            status_events=[_status_event_from_row(status_event_row)],
        ),
        status_event=_status_event_from_row(status_event_row),
        idempotency_status=SUPPORT_CASE_RECORDED,
        audit_event_id=str(audit_event["account_audit_event_id"]) if audit_event else None,
    )
