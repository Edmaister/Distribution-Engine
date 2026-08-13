from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any

from utils.db import db_connection


SUPPORT_CASE_CREATED_EVENT = "SUPPORT_CASE_CREATED"
SUPPORT_CASE_NOTE_ADDED_EVENT = "SUPPORT_CASE_NOTE_ADDED"
SUPPORT_CASE_STATUS_CHANGED_EVENT = "SUPPORT_CASE_STATUS_CHANGED"
SUPPORT_CASE_REPAIR_COMMAND_RECORDED_EVENT = "SUPPORT_CASE_REPAIR_COMMAND_RECORDED"
SUPPORT_CASE_RECORDED = "RECORDED"
SUPPORT_CASE_REPLAYED = "REPLAYED"
SUPPORT_CASE_REPAIR_COMMAND_TYPES = frozenset(
    {"GOVERNED_REPAIR", "GOVERNED_REPLAY", "GOVERNED_REASSIGNMENT"}
)
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
SUPPORT_CASE_QUEUE_GUARDRAILS = [
    *SUPPORT_CASE_GUARDRAILS,
    "OPERATOR_AGGREGATE_SUPPORT_QUEUE",
    "READ_ONLY_QUEUE",
    "CUSTOMER_SAFE_QUEUE_ITEMS",
    "NO_ASSIGNMENT_FROM_QUEUE",
]
SUPPORT_CASE_REPAIR_REPLAY_READINESS_GUARDRAILS = [
    *SUPPORT_CASE_GUARDRAILS,
    "READINESS_ONLY",
    "SUPPORT_CASE_LINK_REQUIRED",
    "APPROVAL_REQUIRED_BEFORE_REPAIR_REPLAY",
    "IDEMPOTENCY_REQUIRED_BEFORE_REPAIR_REPLAY",
    "BEFORE_STATE_HASH_REQUIRED_BEFORE_REPAIR_REPLAY",
    "NO_PROVIDER_DISPATCH",
    "NO_CREDENTIAL_CHANGE",
    "NO_AUTH_CLAIM_CHANGE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_BILLING",
    "NO_MONEY_MOVEMENT",
]
SUPPORT_CASE_REPAIR_COMMAND_GUARDRAILS = [
    *SUPPORT_CASE_GUARDRAILS,
    "APPROVAL_REQUIRED_BEFORE_REPAIR_REPLAY",
    "IDEMPOTENCY_REQUIRED_BEFORE_REPAIR_REPLAY",
    "BEFORE_STATE_HASH_REQUIRED_BEFORE_REPAIR_REPLAY",
    "IMPACT_PREVIEW_REQUIRED",
    "ROLLBACK_PLAN_REQUIRED",
    "COMMAND_LEDGER_ONLY",
    "NO_BROAD_DB_MUTATION",
    "NO_PROVIDER_DISPATCH",
    "NO_CREDENTIAL_CHANGE",
    "NO_AUTH_CLAIM_CHANGE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_BILLING",
    "NO_MONEY_MOVEMENT",
]


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


@dataclass(frozen=True)
class ReferralSaasSupportQueueItem:
    case_ref: str
    account_ref: str
    customer_label: str
    external_tenant_ref: str | None
    organisation_ref: str | None
    category: str
    priority: str
    status: str
    title: str
    source_surface: str | None
    assignee_ref: str | None
    created_at: str | None
    updated_at: str | None
    evidence_link_count: int
    note_count: int
    latest_activity: str
    redactions: list[str]
    next_action: str

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "caseRef": self.case_ref,
            "accountRef": self.account_ref,
            "customerLabel": self.customer_label,
            "externalTenantRef": self.external_tenant_ref,
            "organisationRef": self.organisation_ref,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "title": self.title,
            "sourceSurface": self.source_surface,
            "assigneeRef": self.assignee_ref,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "evidenceLinkCount": self.evidence_link_count,
            "noteCount": self.note_count,
            "latestActivity": self.latest_activity,
            "redactions": self.redactions,
            "nextAction": self.next_action,
        }


@dataclass(frozen=True)
class ReferralSaasSupportQueueResult:
    support_cases: list[ReferralSaasSupportQueueItem]
    filters: dict[str, Any]
    next_cursor: str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "supportCases": [case.to_safe_dict() for case in self.support_cases],
            "filters": self.filters,
            "nextCursor": self.next_cursor,
            "guardrails": SUPPORT_CASE_QUEUE_GUARDRAILS,
            "redactions": SUPPORT_CASE_REDACTIONS,
        }


@dataclass(frozen=True)
class ReferralSaasSupportCaseRepairReplayReadiness:
    support_case: ReferralSaasSupportCase
    overall_status: str
    action_summary: str
    allowed_actions: list[dict[str, Any]]
    required_evidence: list[str]
    owning_workflow: str
    guardrails: list[str]
    redactions: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "caseRef": self.support_case.case_ref,
            "accountRef": self.support_case.account_ref,
            "category": self.support_case.category,
            "status": self.support_case.status,
            "overallStatus": self.overall_status,
            "actionSummary": self.action_summary,
            "owningWorkflow": self.owning_workflow,
            "allowedActions": self.allowed_actions,
            "requiredEvidence": self.required_evidence,
            "supportCase": self.support_case.to_safe_dict(),
            "guardrails": self.guardrails,
            "redactions": self.redactions,
            "no_repair_replay_retry_confirmed": True,
            "no_provider_dispatch_confirmed": True,
            "no_credential_or_auth_claim_change_confirmed": True,
            "no_campaign_activation_confirmed": True,
            "no_billing_or_money_movement_confirmed": True,
        }


@dataclass(frozen=True)
class SupportCaseRepairCommand:
    repair_command_ref: str
    case_ref: str
    account_ref: str
    command_type: str
    command_status: str
    target_evidence_type: str
    target_evidence_ref: str
    before_state_hash: str
    impact_preview: dict[str, Any]
    approval_ref: str
    rollback_plan: str
    reason_code: str | None
    correlation_id: str | None
    created_by_ref: str
    created_by_role: str | None
    created_at: str | None
    redactions: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "repairCommandRef": self.repair_command_ref,
            "caseRef": self.case_ref,
            "accountRef": self.account_ref,
            "commandType": self.command_type,
            "commandStatus": self.command_status,
            "targetEvidenceType": self.target_evidence_type,
            "targetEvidenceRef": self.target_evidence_ref,
            "beforeStateHash": self.before_state_hash,
            "impactPreview": self.impact_preview,
            "approvalRef": self.approval_ref,
            "rollbackPlan": self.rollback_plan,
            "reasonCode": self.reason_code,
            "correlationId": self.correlation_id,
            "createdByRef": self.created_by_ref,
            "createdByRole": self.created_by_role,
            "createdAt": self.created_at,
            "redactions": self.redactions,
        }


@dataclass(frozen=True)
class ReferralSaasSupportCaseRepairCommandResult:
    command_status: str
    support_case: ReferralSaasSupportCase
    repair_command: SupportCaseRepairCommand
    idempotency_status: str
    audit_event_id: str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "supportCase": self.support_case.to_safe_dict(),
            "repairCommand": self.repair_command.to_safe_dict(),
            "idempotency": {"status": self.idempotency_status},
            "audit": {"accountAuditEventId": self.audit_event_id},
            "guardrails": SUPPORT_CASE_REPAIR_COMMAND_GUARDRAILS,
            "redactions": SUPPORT_CASE_REDACTIONS,
            "no_provider_dispatch_confirmed": True,
            "no_credential_or_auth_claim_change_confirmed": True,
            "no_referral_or_campaign_mutation_confirmed": True,
            "no_progress_or_attribution_mutation_confirmed": True,
            "no_report_or_export_mutation_confirmed": True,
            "no_campaign_activation_confirmed": True,
            "no_billing_or_money_movement_confirmed": True,
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


def _normalise_optional_choice(
    value: Any, allowed: frozenset[str], field_name: str
) -> str | None:
    if value is None or _clean_text(value) == "":
        return None
    return _normalise_choice(value, allowed, field_name)


def _normalise_optional_datetime(value: Any, field_name: str) -> datetime | None:
    safe_value = _optional_text(value)
    if not safe_value:
        return None
    if len(safe_value) > 64:
        raise SupportCaseValidationError(f"{field_name} must be a valid date-time.")
    try:
        return datetime.fromisoformat(safe_value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SupportCaseValidationError(
            f"{field_name} must be a valid ISO date-time."
        ) from exc


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


def _normalise_safe_json_object(value: Any, field_name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise SupportCaseValidationError(f"{field_name} must be an object.")
    _assert_safe_metadata(value, field_name)
    return value


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


def _support_queue_item_from_row(row: Any) -> ReferralSaasSupportQueueItem:
    latest_status = _optional_text(row.get("latest_status"))
    latest_note_type = _optional_text(row.get("latest_note_type"))
    latest_activity = (
        f"Status changed to {latest_status}"
        if latest_status
        else f"Latest note: {latest_note_type}"
        if latest_note_type
        else "Case updated"
    )
    return ReferralSaasSupportQueueItem(
        case_ref=str(row["support_case_id"]),
        account_ref=str(row["account_id"]),
        customer_label=str(row.get("customer_label") or row["account_id"]),
        external_tenant_ref=_optional_text(row.get("external_tenant_ref")),
        organisation_ref=_optional_text(row.get("organisation_ref")),
        category=str(row["category"]),
        priority=str(row["priority"]),
        status=str(row["status"]),
        title=str(row["title"]),
        source_surface=_optional_text(row.get("source_surface")),
        assignee_ref=_optional_text(row.get("assignee_ref")),
        created_at=_as_iso(row.get("created_at")),
        updated_at=_as_iso(row.get("updated_at")),
        evidence_link_count=int(row.get("evidence_link_count") or 0),
        note_count=int(row.get("note_count") or 0),
        latest_activity=latest_activity,
        redactions=sorted(
            {
                *_safe_json_list(row.get("redactions")),
                *SUPPORT_CASE_REDACTIONS,
            }
        ),
        next_action="Open customer support case",
    )


def _repair_replay_owning_workflow(category: str) -> str:
    return {
        "VALIDATION_RECOVERY": "links_and_codes",
        "PROGRESS_DIAGNOSTIC": "progress_status",
        "ATTRIBUTION_REVIEW": "attribution_trace",
        "READINESS_BLOCKER": "account_health",
        "REPORTING_FRESHNESS": "reports",
        "INTEGRATION_HEALTH": "integrations",
        "ACCESS_SCOPE": "people_and_access",
        "MANUAL_REVIEW_REQUIRED": "support_hub",
    }.get(category, "support_hub")


def _repair_replay_action_label(category: str, action: str) -> str:
    if action == "GOVERNED_REPAIR":
        return {
            "VALIDATION_RECOVERY": "Repair validation evidence",
            "ATTRIBUTION_REVIEW": "Repair attribution review evidence",
            "REPORTING_FRESHNESS": "Repair report freshness evidence",
            "ACCESS_SCOPE": "Route access fix",
            "READINESS_BLOCKER": "Route setup blocker",
        }.get(category, "Repair bounded support evidence")
    return {
        "PROGRESS_DIAGNOSTIC": "Replay stored progress evidence",
        "REPORTING_FRESHNESS": "Replay eligible report export evidence",
    }.get(category, "Replay stored support evidence")


def _build_repair_replay_actions(
    support_case: ReferralSaasSupportCase,
) -> list[dict[str, Any]]:
    evidence_count = len(support_case.evidence_links)
    lifecycle_status = (
        "AVAILABLE" if support_case.status not in {"RESOLVED", "CLOSED"} else "CLOSED"
    )
    actions: list[dict[str, Any]] = [
        {
            "action": "READ_ONLY_DIAGNOSTIC",
            "status": lifecycle_status,
            "label": "Review support evidence",
            "reasonCode": (
                "EVIDENCE_AVAILABLE" if evidence_count else "NO_EVIDENCE_LINKED"
            ),
        }
    ]
    repair_categories = {
        "VALIDATION_RECOVERY",
        "ATTRIBUTION_REVIEW",
        "READINESS_BLOCKER",
        "REPORTING_FRESHNESS",
        "ACCESS_SCOPE",
        "MANUAL_REVIEW_REQUIRED",
    }
    replay_categories = {"PROGRESS_DIAGNOSTIC", "REPORTING_FRESHNESS"}
    if support_case.category in repair_categories:
        actions.append(
            {
                "action": "GOVERNED_REPAIR",
                "status": "BLOCKED",
                "label": _repair_replay_action_label(
                    support_case.category, "GOVERNED_REPAIR"
                ),
                "reasonCode": "APPROVAL_AND_IMPACT_PREVIEW_REQUIRED",
            }
        )
    if support_case.category in replay_categories:
        actions.append(
            {
                "action": "GOVERNED_REPLAY",
                "status": "BLOCKED",
                "label": _repair_replay_action_label(
                    support_case.category, "GOVERNED_REPLAY"
                ),
                "reasonCode": "APPROVAL_AND_IMPACT_PREVIEW_REQUIRED",
            }
        )
    if len(actions) == 1:
        actions.append(
            {
                "action": "HARD_EXCLUDED",
                "status": "BLOCKED",
                "label": "No repair or replay action is available",
                "reasonCode": "ACTION_NOT_SUPPORTED",
            }
        )
    return actions


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


def _repair_command_from_row(row: Any) -> SupportCaseRepairCommand:
    impact_preview = row.get("impact_preview")
    if isinstance(impact_preview, str):
        try:
            impact_preview = json.loads(impact_preview)
        except json.JSONDecodeError:
            impact_preview = {}
    if not isinstance(impact_preview, dict):
        impact_preview = {}
    return SupportCaseRepairCommand(
        repair_command_ref=str(row["repair_command_id"]),
        case_ref=str(row["support_case_id"]),
        account_ref=str(row["account_id"]),
        command_type=str(row["command_type"]),
        command_status=str(row["command_status"]),
        target_evidence_type=str(row["target_evidence_type"]),
        target_evidence_ref=str(row["target_evidence_ref"]),
        before_state_hash=str(row["before_state_hash"]),
        impact_preview=impact_preview,
        approval_ref=str(row["approval_ref"]),
        rollback_plan=str(row["rollback_plan"]),
        reason_code=_optional_text(row.get("reason_code")),
        correlation_id=_optional_text(row.get("correlation_id")),
        created_by_ref=str(row["created_by_ref"]),
        created_by_role=_optional_text(row.get("created_by_role")),
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


async def list_referral_saas_operator_support_queue(
    *,
    status_filter: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    account_ref: str | None = None,
    source_surface: str | None = None,
    assignee_ref: str | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
    updated_from: str | None = None,
    updated_to: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> ReferralSaasSupportQueueResult:
    safe_status = _normalise_optional_choice(
        status_filter, SUPPORT_CASE_STATUSES, "status"
    )
    safe_priority = _normalise_optional_choice(
        priority, SUPPORT_CASE_PRIORITIES, "priority"
    )
    safe_category = _normalise_optional_choice(
        category, SUPPORT_CASE_CATEGORIES, "category"
    )
    safe_source_surface = _optional_text(source_surface)
    if safe_source_surface and safe_source_surface not in SAFE_SOURCE_SURFACES:
        raise SupportCaseValidationError(
            f"sourceSurface must be one of: {', '.join(sorted(SAFE_SOURCE_SURFACES))}."
        )
    safe_account_ref = (
        _require_bounded_text(account_ref, "account_ref", min_length=1, max_length=80)
        if _optional_text(account_ref)
        else None
    )
    safe_assignee_ref = (
        _require_bounded_text(
            assignee_ref, "assignee_ref", min_length=1, max_length=160
        )
        if _optional_text(assignee_ref)
        else None
    )
    safe_created_from = _normalise_optional_datetime(created_from, "created_from")
    safe_created_to = _normalise_optional_datetime(created_to, "created_to")
    safe_updated_from = _normalise_optional_datetime(updated_from, "updated_from")
    safe_updated_to = _normalise_optional_datetime(updated_to, "updated_to")
    safe_limit = max(1, min(int(limit or 50), MAX_CASE_LIST_LIMIT))
    safe_offset = 0
    safe_cursor = _optional_text(cursor)
    if safe_cursor:
        if not safe_cursor.isdigit():
            raise SupportCaseValidationError("cursor is not valid for this queue.")
        safe_offset = int(safe_cursor)

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            WITH evidence_counts AS (
                SELECT support_case_id, COUNT(*)::int AS evidence_link_count
                FROM referral_saas_support_case_evidence_links
                GROUP BY support_case_id
            ),
            note_counts AS (
                SELECT
                    support_case_id,
                    COUNT(*)::int AS note_count,
                    MAX(created_at) AS latest_note_at
                FROM referral_saas_support_case_notes
                WHERE archived_at IS NULL
                GROUP BY support_case_id
            ),
            latest_notes AS (
                SELECT DISTINCT ON (support_case_id)
                    support_case_id,
                    note_type AS latest_note_type
                FROM referral_saas_support_case_notes
                WHERE archived_at IS NULL
                ORDER BY support_case_id, created_at DESC, support_case_note_id DESC
            ),
            latest_status_events AS (
                SELECT DISTINCT ON (support_case_id)
                    support_case_id,
                    to_status AS latest_status,
                    created_at AS latest_status_at
                FROM referral_saas_support_case_status_events
                WHERE archived_at IS NULL
                ORDER BY support_case_id, created_at DESC, support_case_status_event_id DESC
            )
            SELECT
                support_case.*,
                COALESCE(account.account_name, account.account_code, support_case.account_id::text)
                    AS customer_label,
                account.account_code,
                (
                    SELECT external_ref.external_ref
                    FROM platform_external_tenant_refs external_ref
                    WHERE external_ref.account_id = support_case.account_id
                      AND external_ref.ref_type = 'external_tenant_ref'
                      AND external_ref.archived_at IS NULL
                    ORDER BY
                        CASE external_ref.status WHEN 'ACTIVE' THEN 0 ELSE 1 END,
                        external_ref.updated_at DESC,
                        external_ref.external_ref_id DESC
                    LIMIT 1
                ) AS external_tenant_ref,
                (
                    SELECT organisation.organisation_ref
                    FROM platform_organisations organisation
                    WHERE organisation.account_id = support_case.account_id
                      AND organisation.archived_at IS NULL
                    ORDER BY
                        CASE organisation.status WHEN 'ACTIVE' THEN 0 ELSE 1 END,
                        organisation.updated_at DESC,
                        organisation.organisation_id DESC
                    LIMIT 1
                ) AS organisation_ref,
                COALESCE(evidence_counts.evidence_link_count, 0) AS evidence_link_count,
                COALESCE(note_counts.note_count, 0) AS note_count,
                latest_notes.latest_note_type,
                latest_status_events.latest_status,
                GREATEST(
                    support_case.updated_at,
                    COALESCE(note_counts.latest_note_at, support_case.updated_at),
                    COALESCE(latest_status_events.latest_status_at, support_case.updated_at)
                ) AS latest_activity_at
            FROM referral_saas_support_cases support_case
            LEFT JOIN platform_accounts account
                ON account.account_id = support_case.account_id
            LEFT JOIN evidence_counts
                ON evidence_counts.support_case_id = support_case.support_case_id
            LEFT JOIN note_counts
                ON note_counts.support_case_id = support_case.support_case_id
            LEFT JOIN latest_notes
                ON latest_notes.support_case_id = support_case.support_case_id
            LEFT JOIN latest_status_events
                ON latest_status_events.support_case_id = support_case.support_case_id
            WHERE support_case.archived_at IS NULL
              AND ($1::text IS NULL OR support_case.status = $1)
              AND ($2::text IS NULL OR support_case.priority = $2)
              AND ($3::text IS NULL OR support_case.category = $3)
              AND (
                    $4::text IS NULL
                    OR support_case.account_id::text = $4
                    OR account.account_code = $4
                  )
              AND ($5::text IS NULL OR support_case.source_surface = $5)
              AND ($6::text IS NULL OR support_case.assignee_ref = $6)
              AND ($7::timestamptz IS NULL OR support_case.created_at >= $7)
              AND ($8::timestamptz IS NULL OR support_case.created_at <= $8)
              AND ($9::timestamptz IS NULL OR support_case.updated_at >= $9)
              AND ($10::timestamptz IS NULL OR support_case.updated_at <= $10)
            ORDER BY
                CASE support_case.status
                    WHEN 'OPEN' THEN 0
                    WHEN 'INVESTIGATING' THEN 1
                    WHEN 'WAITING' THEN 2
                    ELSE 3
                END,
                CASE support_case.priority
                    WHEN 'CRITICAL' THEN 0
                    WHEN 'HIGH' THEN 1
                    WHEN 'MEDIUM' THEN 2
                    ELSE 3
                END,
                latest_activity_at DESC,
                support_case.support_case_id DESC
            LIMIT $11
            OFFSET $12
            """,
            safe_status,
            safe_priority,
            safe_category,
            safe_account_ref,
            safe_source_surface,
            safe_assignee_ref,
            safe_created_from,
            safe_created_to,
            safe_updated_from,
            safe_updated_to,
            safe_limit + 1,
            safe_offset,
        )

    visible_rows = rows[:safe_limit]
    return ReferralSaasSupportQueueResult(
        support_cases=[_support_queue_item_from_row(row) for row in visible_rows],
        filters={
            "status": safe_status,
            "priority": safe_priority,
            "category": safe_category,
            "accountRef": safe_account_ref,
            "sourceSurface": safe_source_surface,
            "assigneeRef": safe_assignee_ref,
            "createdFrom": _as_iso(safe_created_from),
            "createdTo": _as_iso(safe_created_to),
            "updatedFrom": _as_iso(safe_updated_from),
            "updatedTo": _as_iso(safe_updated_to),
            "limit": safe_limit,
        },
        next_cursor=str(safe_offset + safe_limit) if len(rows) > safe_limit else None,
    )


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


async def get_referral_saas_support_case_repair_replay_readiness(
    *,
    account_id: str,
    case_ref: str,
) -> ReferralSaasSupportCaseRepairReplayReadiness:
    support_case = await get_referral_saas_support_case(
        account_id=account_id,
        case_ref=case_ref,
    )
    allowed_actions = _build_repair_replay_actions(support_case)
    has_future_action = any(
        action["action"] in {"GOVERNED_REPAIR", "GOVERNED_REPLAY"}
        for action in allowed_actions
    )
    overall_status = (
        "ACTION_NOT_SUPPORTED"
        if not has_future_action
        else "REVIEW_REQUIRED"
        if support_case.status not in {"RESOLVED", "CLOSED"}
        else "CASE_CLOSED"
    )
    required_evidence = [
        "support_case_link",
        "actor",
        "reason",
        "correlation_id",
        "idempotency_key",
        "target_evidence",
        "before_state_hash",
    ]
    redactions = sorted(
        {
            *SUPPORT_CASE_REDACTIONS,
            *support_case.redactions,
            *[
                redaction
                for evidence_link in support_case.evidence_links
                for redaction in evidence_link.redactions
            ],
        }
    )
    return ReferralSaasSupportCaseRepairReplayReadiness(
        support_case=support_case,
        overall_status=overall_status,
        action_summary=(
            "Readiness only. This response explains whether a future governed "
            "repair or replay can be considered; it does not execute one."
        ),
        allowed_actions=allowed_actions,
        required_evidence=required_evidence,
        owning_workflow=_repair_replay_owning_workflow(support_case.category),
        guardrails=sorted(SUPPORT_CASE_REPAIR_REPLAY_READINESS_GUARDRAILS),
        redactions=redactions,
    )


async def execute_referral_saas_support_case_repair_command(
    *,
    account_id: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    tenant_code: str,
    case_ref: str,
    command_type: str,
    target_evidence_type: str,
    target_evidence_ref: str,
    before_state_hash: str,
    impact_preview: dict[str, Any] | None,
    approval_ref: str,
    rollback_plan: str,
    reason_code: str | None,
    correlation_id: str | None,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
) -> ReferralSaasSupportCaseRepairCommandResult:
    safe_account_id = _require_bounded_text(
        account_id, "account_id", min_length=1, max_length=80
    )
    safe_tenant_code = _require_bounded_text(
        tenant_code, "tenant_code", min_length=1, max_length=120
    )
    safe_case_ref = _require_bounded_text(
        case_ref, "case_ref", min_length=1, max_length=80
    )
    safe_command_type = _normalise_choice(
        command_type, SUPPORT_CASE_REPAIR_COMMAND_TYPES, "commandType"
    )
    safe_target_evidence_type = _require_bounded_text(
        target_evidence_type, "targetEvidenceType", min_length=3, max_length=80
    ).upper()
    safe_target_evidence_ref = _require_bounded_text(
        target_evidence_ref, "targetEvidenceRef", min_length=1, max_length=160
    )
    safe_before_state_hash = _require_bounded_text(
        before_state_hash, "beforeStateHash", min_length=8, max_length=256
    )
    safe_impact_preview = _normalise_safe_json_object(
        impact_preview, "impactPreview"
    )
    if not safe_impact_preview:
        raise SupportCaseValidationError("impactPreview must describe the expected change.")
    safe_approval_ref = _require_bounded_text(
        approval_ref, "approvalRef", min_length=3, max_length=160
    )
    safe_rollback_plan = _require_bounded_text(
        rollback_plan, "rollbackPlan", min_length=10, max_length=1000
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
    safe_reason_code = _optional_text(reason_code) or "SUPPORT_CASE_REPAIR_COMMAND"
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

        support_case = _support_case_from_row(case_row)
        if support_case.status in {"RESOLVED", "CLOSED"}:
            raise SupportCaseValidationError(
                "Support case must be open before a governed command is recorded."
            )
        allowed_actions = _build_repair_replay_actions(support_case)
        allowed_command_types = {
            action["action"]
            for action in allowed_actions
            if action["action"] in SUPPORT_CASE_REPAIR_COMMAND_TYPES
        }
        if safe_command_type not in allowed_command_types:
            raise SupportCaseValidationError(
                f"{safe_command_type} is not available for this support-case category."
            )

        existing_command = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_support_case_repair_commands
            WHERE support_case_id = $1
              AND idempotency_key_hash = $2
              AND archived_at IS NULL
            LIMIT 1
            """,
            case_row["support_case_id"],
            safe_idempotency_hash,
        )
        if existing_command:
            if _optional_text(existing_command.get("request_payload_hash")) != safe_payload_hash:
                raise SupportCaseIdempotencyConflict(
                    "Idempotency key was reused with different support-case command content."
                )
            return ReferralSaasSupportCaseRepairCommandResult(
                command_status="SUPPORT_CASE_REPAIR_COMMAND_REPLAYED",
                support_case=support_case,
                repair_command=_repair_command_from_row(existing_command),
                idempotency_status=SUPPORT_CASE_REPLAYED,
                audit_event_id=None,
            )

        async with conn.transaction():
            command_row = await conn.fetchrow(
                """
                INSERT INTO referral_saas_support_case_repair_commands (
                    support_case_id,
                    account_id,
                    command_type,
                    command_status,
                    target_evidence_type,
                    target_evidence_ref,
                    before_state_hash,
                    impact_preview,
                    approval_ref,
                    rollback_plan,
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
                    $1, $2, $3, 'RECORDED', $4, $5, $6, $7::jsonb,
                    $8, $9, $10, $11, $12, $13, $14, $15, $16::jsonb,
                    $17::jsonb
                )
                RETURNING *
                """,
                case_row["support_case_id"],
                safe_account_id,
                safe_command_type,
                safe_target_evidence_type,
                safe_target_evidence_ref,
                safe_before_state_hash,
                _jsonb(safe_impact_preview),
                safe_approval_ref,
                safe_rollback_plan,
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                safe_payload_hash,
                safe_actor_ref,
                safe_actor_role,
                _jsonb(
                    {
                        "command_ledger_only": True,
                        "no_broad_db_mutation_confirmed": True,
                        "no_billing_or_money_movement_confirmed": True,
                    }
                ),
                _jsonb(redactions),
            )
            updated_case_row = await conn.fetchrow(
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
                SUPPORT_CASE_REPAIR_COMMAND_RECORDED_EVENT,
                SUPPORT_CASE_RECORDED,
                safe_actor_ref,
                safe_actor_role,
                updated_case_row["status"],
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(
                    {
                        "support_case_id": str(case_row["support_case_id"]),
                        "repair_command_id": str(command_row["repair_command_id"]),
                        "command_type": safe_command_type,
                        "target_evidence_type": safe_target_evidence_type,
                        "target_evidence_ref": safe_target_evidence_ref,
                        "before_state_hash": safe_before_state_hash,
                        "approval_ref": safe_approval_ref,
                        "request_payload_hash": safe_payload_hash,
                        "command_ledger_only": True,
                        "no_broad_db_mutation_confirmed": True,
                        "no_billing_or_money_movement_confirmed": True,
                    }
                ),
                _jsonb(redactions),
            )

    return ReferralSaasSupportCaseRepairCommandResult(
        command_status="SUPPORT_CASE_REPAIR_COMMAND_RECORDED",
        support_case=_support_case_from_row(updated_case_row),
        repair_command=_repair_command_from_row(command_row),
        idempotency_status=SUPPORT_CASE_RECORDED,
        audit_event_id=str(audit_event["account_audit_event_id"]) if audit_event else None,
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
