from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any, Final

CONTRACT_VERSION: Final = "onboarding.v1"

EVIDENCE_PRESENT: Final = "PRESENT"
EVIDENCE_PARTIAL: Final = "PARTIAL"
EVIDENCE_MISSING: Final = "MISSING"
EVIDENCE_SHELL_ONLY: Final = "SHELL_ONLY"
EVIDENCE_UNKNOWN_REFERENCE: Final = "UNKNOWN_REFERENCE"
EVIDENCE_BLOCKED: Final = "BLOCKED"

STATUS_NOT_STARTED: Final = "NOT_STARTED"
STATUS_DRAFT: Final = "DRAFT"
STATUS_IN_PROGRESS: Final = "IN_PROGRESS"
STATUS_READY: Final = "READY"
STATUS_BLOCKED: Final = "BLOCKED"
STATUS_UNAVAILABLE: Final = "UNAVAILABLE"
STATUS_REVIEW_ONLY: Final = "REVIEW_ONLY"

SAFE_STATUS_LABELS: Final[dict[str, str]] = {
    STATUS_NOT_STARTED: "Not started",
    STATUS_DRAFT: "Draft",
    STATUS_IN_PROGRESS: "In progress",
    STATUS_READY: "Ready",
    STATUS_BLOCKED: "Blocked",
    STATUS_UNAVAILABLE: "Unavailable",
    STATUS_REVIEW_ONLY: "Review only",
}

EVIDENCE_LABELS: Final[dict[str, str]] = {
    EVIDENCE_PRESENT: "Present",
    EVIDENCE_PARTIAL: "Partial",
    EVIDENCE_MISSING: "Missing",
    EVIDENCE_SHELL_ONLY: "Shell only",
    EVIDENCE_UNKNOWN_REFERENCE: "Unknown reference",
    EVIDENCE_BLOCKED: "Blocked",
}

SCOPE_FIELDS: Final = (
    "external_tenant_ref",
    "organisation_ref",
    "producer_ref",
    "sponsor_ref",
    "distributor_ref",
    "campaign_code",
    "opportunity_ref",
)

SECTION_DEFINITIONS: Final[dict[str, dict[str, Any]]] = {
    "company": {
        "category": "ORGANISATION_PROFILE",
        "label": "Organisation profile",
        "path": "/admin/onboarding/company",
        "fields": (
            "organisation_name",
            "external_tenant_ref",
            "organisation_ref",
            "country",
            "organisation_type",
            "industry",
            "admin_contact",
            "intended_role",
        ),
    },
    "producer_sponsor": {
        "category": "PRODUCER_SPONSOR_SETUP",
        "label": "Producer / sponsor setup",
        "path": "/admin/onboarding/producer-sponsor",
        "fields": (
            "producer_sponsor_name",
            "external_tenant_ref",
            "producer_ref",
            "sponsor_ref",
            "organisation_ref",
            "industry",
            "funding_model_intention",
            "admin_contact",
            "campaign_opportunity_role",
        ),
    },
    "distributor": {
        "category": "DISTRIBUTOR_SETUP",
        "label": "Distributor setup",
        "path": "/admin/onboarding/distributor",
        "fields": (
            "distributor_name",
            "external_tenant_ref",
            "distributor_ref",
            "organisation_ref",
            "channel_type",
            "market_country",
            "admin_contact",
            "distribution_model",
            "campaign_opportunity_participation",
        ),
    },
    "member_role": {
        "category": "MEMBERS_AND_ROLES",
        "label": "Members and roles",
        "path": "/admin/onboarding/members",
        "fields": (
            "organisation_ref",
            "external_tenant_ref",
            "user_email",
            "display_name",
            "role_family",
            "participant_type",
            "access_scope",
            "invite_status",
        ),
    },
    "campaign_opportunity": {
        "category": "CAMPAIGN_OPPORTUNITY_SETUP",
        "label": "Campaign / opportunity setup",
        "path": "/admin/onboarding/campaign",
        "fields": (
            "organisation_ref",
            "producer_ref",
            "sponsor_ref",
            "campaign_code",
            "opportunity_ref",
            "campaign_name",
            "market_country",
            "distribution_model",
            "eligible_distributor_type",
            "intended_outcome_event",
            "reward_commission_policy_intention",
            "funding_model_intention",
            "go_live_target_status",
            "link_code_intent",
        ),
    },
    "webhook_api": {
        "category": "WEBHOOK_API_SETUP",
        "label": "Webhook / API setup",
        "path": "/admin/onboarding/webhook-api",
        "fields": (
            "organisation_ref",
            "external_tenant_ref",
            "integration_owner_contact",
            "api_environment_intention",
            "callback_url_placeholder",
            "selected_webhook_event_categories",
            "intended_authentication_method",
            "ip_allowlist_notes",
            "payload_format_version",
            "go_live_readiness_status",
        ),
    },
}

READINESS_ONLY_ITEMS: Final[tuple[dict[str, str], ...]] = (
    {
        "category": "SECURITY_AND_PERMISSIONS",
        "label": "Security and permissions",
        "path": "/admin/onboarding/members",
        "code": "NO_MEMBERSHIP_SOURCE",
        "message": "Permission and membership evidence is not yet backed by a read-only onboarding source.",
    },
    {
        "category": "GO_LIVE_CONTROLS",
        "label": "Go-live controls",
        "path": "/admin/onboarding/readiness",
        "code": "NO_READINESS_SOURCE",
        "message": "Go-live controls remain disabled until a later task implements explicit readiness commands.",
    },
)

GUARDRAILS: Final = [
    "READ_ONLY_PROJECTION",
    "NO_LIVE_MUTATION",
    "TENANT_CODE_INTERNAL",
    "NO_SECRET_EXPOSURE",
    "NO_WEBHOOK_DELIVERY",
    "NO_MONEY_MOVEMENT",
]

UNSAFE_KEY_CATEGORIES: Final[tuple[tuple[str, str], ...]] = (
    ("tenant_code", "internal_identifier"),
    ("ucn", "private_identifier"),
    ("secret", "secret_or_credential"),
    ("token", "secret_or_credential"),
    ("password", "secret_or_credential"),
    ("credential", "secret_or_credential"),
    ("api_key", "secret_or_credential"),
    ("client_secret", "secret_or_credential"),
    ("signing", "secret_or_credential"),
    ("certificate", "secret_or_credential"),
    ("provider", "provider_internal"),
    ("raw", "raw_internal"),
    ("audit", "audit_internal"),
    ("wallet", "money_movement_internal"),
    ("settlement", "money_movement_internal"),
    ("fulfilment", "money_movement_internal"),
    ("funding", "money_movement_internal"),
    ("retry", "retry_internal"),
    ("internal_id", "internal_identifier"),
)


def project_onboarding_state(
    evidence: Mapping[str, Any] | None = None,
    *,
    include_internal_context: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    source = _as_mapping(evidence)
    redactions: set[str] = set()
    source_warnings: list[dict[str, str]] = []
    missing_evidence: list[dict[str, str]] = []

    scope = _project_scope(
        source,
        include_internal_context=include_internal_context,
        redactions=redactions,
        source_warnings=source_warnings,
        missing_evidence=missing_evidence,
    )
    sections = _project_sections(source, redactions=redactions)
    readiness = _project_readiness(sections)

    for section_name, section in sections.items():
        for item in section["missing_evidence"]:
            missing_evidence.append({**item, "section": section_name})

    return {
        "contract_version": CONTRACT_VERSION,
        "generated_at": generated_at or _now_iso(),
        "scope": scope,
        "sections": sections,
        "readiness": readiness,
        "missing_evidence": missing_evidence,
        "redactions": sorted(redactions),
        "guardrails": GUARDRAILS,
        "source_warnings": source_warnings,
    }


def _project_scope(
    evidence: Mapping[str, Any],
    *,
    include_internal_context: bool,
    redactions: set[str],
    source_warnings: list[dict[str, str]],
    missing_evidence: list[dict[str, str]],
) -> dict[str, Any]:
    scope_source = _as_mapping(evidence.get("scope"))
    scope = {
        field: _safe_scalar(scope_source.get(field, evidence.get(field)))
        for field in SCOPE_FIELDS
    }
    tenant_code = scope_source.get("tenant_code") or evidence.get("tenant_code")
    _collect_unsafe_key_redactions(scope_source, redactions)

    resolved_tenant: dict[str, Any] = {"status": STATUS_UNAVAILABLE}
    if include_internal_context and tenant_code:
        resolved_tenant["tenant_code"] = _safe_scalar(tenant_code)

    unknown_references = _string_list(
        scope_source.get("unknown_references") or evidence.get("unknown_references")
    )
    if unknown_references:
        resolved_tenant["status"] = EVIDENCE_UNKNOWN_REFERENCE
        missing_evidence.append(
            _missing(
                section="scope",
                code="UNKNOWN_REFERENCE",
                severity="BLOCKER",
                message="One or more external onboarding references could not be resolved.",
            )
        )
        source_warnings.append(
            {
                "code": "UNKNOWN_REFERENCE",
                "severity": "WARNING",
                "source": "onboarding_scope",
                "message": "External reference resolution is unavailable or unresolved.",
            }
        )
    elif not any(scope.values()):
        missing_evidence.append(
            _missing(
                section="scope",
                code="NO_RESOLVED_TENANT",
                severity="INFO",
                message="No external onboarding reference scope was provided.",
            )
        )

    scope["resolved_tenant"] = resolved_tenant
    return scope


def _project_sections(
    evidence: Mapping[str, Any],
    *,
    redactions: set[str],
) -> dict[str, dict[str, Any]]:
    section_sources = _as_mapping(evidence.get("sections"))
    return {
        section_name: _project_section(
            section_name,
            _as_mapping(section_sources.get(section_name, evidence.get(section_name))),
            redactions=redactions,
        )
        for section_name in SECTION_DEFINITIONS
    }


def _project_section(
    section_name: str,
    source: Mapping[str, Any],
    *,
    redactions: set[str],
) -> dict[str, Any]:
    definition = SECTION_DEFINITIONS[section_name]
    fields = tuple(definition["fields"])
    data = _safe_section_data(source, fields, redactions)

    blockers = _string_list(source.get("blockers"))
    next_actions = _string_list(source.get("next_actions"))
    missing_fields = [field for field in fields if _is_blank(data.get(field))]

    if _truthy(source.get("unknown_reference")):
        evidence_status = EVIDENCE_UNKNOWN_REFERENCE
        status = STATUS_BLOCKED
        missing = [
            _missing(
                section=section_name,
                code="UNKNOWN_REFERENCE",
                severity="BLOCKER",
                message="The onboarding reference could not be resolved safely.",
            )
        ]
        blockers = blockers or ["Resolve or correct the external onboarding reference."]
        next_actions = next_actions or [
            "Review the external reference before continuing."
        ]
    elif _truthy(source.get("blocked")) or blockers:
        evidence_status = EVIDENCE_BLOCKED
        status = STATUS_BLOCKED
        missing = [
            _missing(
                section=section_name,
                code=str(source.get("blocker_code") or "ONBOARDING_BLOCKED"),
                severity="BLOCKER",
                message="A known blocker prevents this onboarding section from being ready.",
            )
        ]
        next_actions = next_actions or ["Resolve the listed blockers."]
    elif not source:
        evidence_status = EVIDENCE_SHELL_ONLY
        status = STATUS_UNAVAILABLE
        missing = [
            _missing(
                section=section_name,
                code="NO_BACKEND_SOURCE",
                severity="INFO",
                message=f"{definition['label']} is currently shell-only.",
            )
        ]
        next_actions = next_actions or [
            f"Capture {definition['label'].lower()} when a safe source is available."
        ]
    elif len(missing_fields) == len(fields):
        evidence_status = EVIDENCE_MISSING
        status = STATUS_NOT_STARTED
        missing = [
            _missing(
                section=section_name,
                code="NO_PERSISTED_DRAFT",
                severity="INFO",
                message=f"No usable {definition['label'].lower()} evidence was provided.",
            )
        ]
        next_actions = next_actions or [f"Start {definition['label'].lower()} setup."]
    elif missing_fields:
        evidence_status = EVIDENCE_PARTIAL
        status = STATUS_IN_PROGRESS
        missing = [
            _missing(
                section=section_name,
                code="MISSING_REQUIRED_FIELD",
                severity="WARNING",
                message="Required onboarding evidence is incomplete.",
            )
        ]
        blockers = blockers or [f"Missing fields: {', '.join(missing_fields)}"]
        next_actions = next_actions or ["Complete the missing onboarding fields."]
    else:
        evidence_status = EVIDENCE_PRESENT
        status = STATUS_READY
        missing = []
        next_actions = next_actions or ["Review this section before go-live."]

    return {
        "status": status,
        "status_label": SAFE_STATUS_LABELS[status],
        "evidence_status": evidence_status,
        "evidence_label": EVIDENCE_LABELS[evidence_status],
        "data": data,
        "missing_evidence": missing,
        "blockers": blockers,
        "next_actions": next_actions,
    }


def _project_readiness(sections: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for section_name, section in sections.items():
        definition = SECTION_DEFINITIONS[section_name]
        items.append(
            {
                "category": definition["category"],
                "status": section["status"],
                "status_label": section["status_label"],
                "path": definition["path"],
                "evidence": section["evidence_status"],
                "blockers": section["blockers"],
                "next_actions": section["next_actions"],
            }
        )

    for item in READINESS_ONLY_ITEMS:
        items.append(
            {
                "category": item["category"],
                "status": STATUS_BLOCKED,
                "status_label": SAFE_STATUS_LABELS[STATUS_BLOCKED],
                "path": item["path"],
                "evidence": EVIDENCE_SHELL_ONLY,
                "blockers": [item["message"]],
                "next_actions": [
                    "Keep this control disabled until an explicit safe task implements it."
                ],
            }
        )

    ready_count = sum(1 for item in items if item["status"] == STATUS_READY)
    blocked_count = sum(1 for item in items if item["status"] == STATUS_BLOCKED)
    return {
        "status": STATUS_REVIEW_ONLY,
        "items": items,
        "summary": {
            "ready_count": ready_count,
            "blocked_count": blocked_count,
            "total_count": len(items),
        },
    }


def _safe_section_data(
    source: Mapping[str, Any],
    fields: Sequence[str],
    redactions: set[str],
) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for field in fields:
        value = source.get(field)
        if isinstance(value, list | tuple | set):
            data[field] = [_safe_scalar(item) for item in value if not _is_blank(item)]
        else:
            data[field] = _safe_scalar(value)

    for key in source:
        if key not in fields:
            _collect_unsafe_key_redactions({key: source[key]}, redactions)
    return data


def _collect_unsafe_key_redactions(
    value: Mapping[str, Any],
    redactions: set[str],
) -> None:
    for key, item in value.items():
        normalized = str(key or "").strip().lower().replace("-", "_")
        for part, category in UNSAFE_KEY_CATEGORIES:
            if part in normalized:
                redactions.add(category)
        if isinstance(item, Mapping):
            _collect_unsafe_key_redactions(item, redactions)


def _safe_scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool | int | float):
        return value
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    return str(value).strip()


def _missing(
    *,
    section: str,
    code: str,
    severity: str,
    message: str,
) -> dict[str, str]:
    return {
        "section": section,
        "code": code,
        "severity": severity,
        "message": message,
    }


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "blocked"}


def _is_blank(value: Any) -> bool:
    return value is None or value == "" or value == []


def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
