from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any, Final

from services.onboarding.onboarding_state_projection_service import (
    EVIDENCE_BLOCKED,
    EVIDENCE_MISSING,
    EVIDENCE_PARTIAL,
    EVIDENCE_PRESENT,
    EVIDENCE_SHELL_ONLY,
    EVIDENCE_UNKNOWN_REFERENCE,
)

READINESS_READY: Final = "READY"
READINESS_IN_PROGRESS: Final = "IN_PROGRESS"
READINESS_BLOCKED: Final = "BLOCKED"
READINESS_MISSING_EVIDENCE: Final = "MISSING_EVIDENCE"
READINESS_PERMISSION_LIMITED: Final = "PERMISSION_LIMITED"
READINESS_GO_LIVE_DISABLED: Final = "GO_LIVE_DISABLED"

READINESS_LABELS: Final[dict[str, str]] = {
    READINESS_READY: "Ready",
    READINESS_IN_PROGRESS: "In progress",
    READINESS_BLOCKED: "Blocked",
    READINESS_MISSING_EVIDENCE: "Missing evidence",
    READINESS_PERMISSION_LIMITED: "Permission limited",
    READINESS_GO_LIVE_DISABLED: "Go-live disabled",
}

SECTION_CATEGORY_MAP: Final[tuple[dict[str, str], ...]] = (
    {
        "section": "company",
        "category": "ORGANISATION_PROFILE",
        "label": "Organisation profile",
        "path": "/admin/onboarding/company",
    },
    {
        "section": "producer_sponsor",
        "category": "PRODUCER_SPONSOR_SETUP",
        "label": "Producer / sponsor setup",
        "path": "/admin/onboarding/producer-sponsor",
    },
    {
        "section": "distributor",
        "category": "DISTRIBUTOR_SETUP",
        "label": "Distributor setup",
        "path": "/admin/onboarding/distributor",
    },
    {
        "section": "member_role",
        "category": "MEMBERS_AND_ROLES",
        "label": "Members and roles",
        "path": "/admin/onboarding/members-roles",
    },
    {
        "section": "campaign_opportunity",
        "category": "CAMPAIGN_OPPORTUNITY_SETUP",
        "label": "Campaign / opportunity setup",
        "path": "/admin/onboarding/campaign-opportunity",
    },
    {
        "section": "webhook_api",
        "category": "WEBHOOK_API_SETUP",
        "label": "Webhook / API setup",
        "path": "/admin/onboarding/webhook-api",
    },
)

CONTROL_CATEGORIES: Final[tuple[dict[str, str], ...]] = (
    {
        "category": "SECURITY_AND_PERMISSIONS",
        "label": "Security and permissions",
        "path": "/admin/onboarding/members-roles",
        "status": READINESS_BLOCKED,
        "evidence": "TASK_027_028_BLOCKED",
        "blocker": "Membership APIs, live DB verification, and drift checks remain blocked before release signoff.",
        "next_action": "Keep tenant_code internal and complete approved read-only live verification before release.",
    },
    {
        "category": "GO_LIVE_CONTROLS",
        "label": "Go-live controls",
        "path": "/admin/onboarding/readiness",
        "status": READINESS_GO_LIVE_DISABLED,
        "evidence": "GO_LIVE_DISABLED",
        "blocker": "Go-live activation, campaign publication, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, and money movement are disabled.",
        "next_action": "Use this readiness output for review only until explicit go-live tasks are implemented.",
    },
)

EXTERNAL_SCOPE_FIELDS: Final = (
    "external_tenant_ref",
    "organisation_ref",
    "producer_ref",
    "sponsor_ref",
    "distributor_ref",
    "campaign_code",
    "opportunity_ref",
)

AGGREGATION_GUARDRAILS: Final = [
    "READ_ONLY_AGGREGATION",
    "NO_LIVE_MUTATION",
    "TENANT_CODE_INTERNAL",
    "EXTERNAL_REFS_ONLY",
    "GO_LIVE_DISABLED",
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


def aggregate_onboarding_readiness(
    projection: Mapping[str, Any],
    *,
    permission_limited_categories: Sequence[str] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    source = _as_mapping(projection)
    redactions = set(_string_list(source.get("redactions")))
    _collect_unsafe_key_redactions(source, redactions)

    limited_categories = {
        str(category or "").strip().upper()
        for category in permission_limited_categories or []
        if str(category or "").strip()
    }
    scope = _safe_scope(_as_mapping(source.get("scope")))
    categories = _category_items(
        _as_mapping(source.get("sections")),
        limited_categories=limited_categories,
    )
    categories.extend(
        _control_items(
            limited_categories=limited_categories,
        )
    )

    return {
        "contract_version": source.get("contract_version") or "onboarding.v1",
        "generated_at": generated_at or _now_iso(),
        "scope": scope,
        "overall_status": _overall_status(categories),
        "categories": categories,
        "summary": _summary(categories),
        "guardrails": _guardrails(_string_list(source.get("guardrails"))),
        "missing_evidence": _safe_missing(source.get("missing_evidence")),
        "source_warnings": _safe_source_warnings(source.get("source_warnings")),
        "redactions": sorted(redactions),
    }


def _category_items(
    sections: Mapping[str, Any],
    *,
    limited_categories: set[str],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for definition in SECTION_CATEGORY_MAP:
        category = definition["category"]
        section = _as_mapping(sections.get(definition["section"]))
        status = _category_status(
            section,
            permission_limited=category in limited_categories,
        )
        evidence_status = str(section.get("evidence_status") or "UNKNOWN")
        blockers = _safe_string_list(section.get("blockers"))
        next_actions = _safe_string_list(section.get("next_actions"))
        if status == READINESS_PERMISSION_LIMITED:
            blockers = ["Current identity cannot see all evidence for this category."]
            next_actions = [
                "Use an authorized operator/admin view for this readiness category."
            ]

        items.append(
            {
                "category": category,
                "display_label": definition["label"],
                "status": status,
                "safe_display_status": _safe_display_status(status),
                "path": definition["path"],
                "evidence_summary": _evidence_summary(evidence_status, status),
                "blockers": blockers,
                "next_actions": next_actions,
                "source_evidence_refs": _source_refs(definition["section"], section),
                "guardrails": _category_guardrails(status),
            }
        )
    return items


def _control_items(*, limited_categories: set[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for definition in CONTROL_CATEGORIES:
        status = definition["status"]
        blockers = [definition["blocker"]]
        next_actions = [definition["next_action"]]
        if definition["category"] in limited_categories:
            status = READINESS_PERMISSION_LIMITED
            blockers = ["Current identity cannot see all evidence for this category."]
            next_actions = [
                "Use an authorized operator/admin view for this readiness category."
            ]

        items.append(
            {
                "category": definition["category"],
                "display_label": definition["label"],
                "status": status,
                "safe_display_status": _safe_display_status(status),
                "path": definition["path"],
                "evidence_summary": definition["evidence"],
                "blockers": blockers,
                "next_actions": next_actions,
                "source_evidence_refs": [
                    {
                        "section": definition["category"].lower(),
                        "evidence_status": definition["evidence"],
                        "missing_evidence_codes": [
                            "LIVE_DB_VERIFICATION_BLOCKED",
                            "DRIFT_VERIFICATION_BLOCKED",
                        ],
                    }
                ],
                "guardrails": _category_guardrails(status),
            }
        )
    return items


def _category_status(
    section: Mapping[str, Any],
    *,
    permission_limited: bool,
) -> str:
    if permission_limited:
        return READINESS_PERMISSION_LIMITED

    status = str(section.get("status") or "").strip().upper()
    evidence = str(section.get("evidence_status") or "").strip().upper()

    if status == "READY" and evidence == EVIDENCE_PRESENT:
        return READINESS_READY
    if status == "BLOCKED" or evidence in {
        EVIDENCE_BLOCKED,
        EVIDENCE_UNKNOWN_REFERENCE,
    }:
        return READINESS_BLOCKED
    if evidence in {EVIDENCE_SHELL_ONLY, EVIDENCE_MISSING} or status in {
        "UNAVAILABLE",
        "NOT_STARTED",
    }:
        return READINESS_MISSING_EVIDENCE
    if evidence == EVIDENCE_PARTIAL or status in {"IN_PROGRESS", "DRAFT"}:
        return READINESS_IN_PROGRESS
    return READINESS_MISSING_EVIDENCE


def _safe_scope(scope: Mapping[str, Any]) -> dict[str, Any]:
    safe = {field: _safe_scalar(scope.get(field)) for field in EXTERNAL_SCOPE_FIELDS}
    resolved = _as_mapping(scope.get("resolved_tenant"))
    safe["resolved_tenant"] = {
        "status": _safe_scalar(resolved.get("status") or "UNAVAILABLE")
    }
    return safe


def _source_refs(section_name: str, section: Mapping[str, Any]) -> list[dict[str, Any]]:
    missing_codes = [
        str(item.get("code"))
        for item in _safe_missing(section.get("missing_evidence"))
        if item.get("code")
    ]
    return [
        {
            "section": section_name,
            "evidence_status": _safe_scalar(
                section.get("evidence_status") or "UNKNOWN"
            ),
            "missing_evidence_codes": missing_codes,
        }
    ]


def _safe_display_status(status: str) -> dict[str, Any]:
    return {
        "status": status,
        "label": READINESS_LABELS[status],
        "action_required": status
        in {
            READINESS_BLOCKED,
            READINESS_MISSING_EVIDENCE,
            READINESS_PERMISSION_LIMITED,
            READINESS_GO_LIVE_DISABLED,
        },
        "go_live_enabled": False,
    }


def _evidence_summary(evidence_status: str, status: str) -> str:
    if status == READINESS_READY:
        return "Required read-only evidence is present."
    if status == READINESS_IN_PROGRESS:
        return "Some read-only evidence is present, but setup is incomplete."
    if status == READINESS_BLOCKED:
        return "A blocker prevents this category from being ready."
    if status == READINESS_PERMISSION_LIMITED:
        return "Evidence is limited by the current permission boundary."
    return f"Required evidence is unavailable or shell-only ({evidence_status})."


def _category_guardrails(status: str) -> list[str]:
    guardrails = ["READ_ONLY", "NO_MUTATION", "TENANT_CODE_INTERNAL"]
    if status == READINESS_GO_LIVE_DISABLED:
        guardrails.append("GO_LIVE_DISABLED")
    if status in {READINESS_MISSING_EVIDENCE, READINESS_PERMISSION_LIMITED}:
        guardrails.append("MISSING_EVIDENCE_EXPLICIT")
    return guardrails


def _overall_status(categories: Sequence[Mapping[str, Any]]) -> str:
    if any(item.get("status") == READINESS_GO_LIVE_DISABLED for item in categories):
        return READINESS_GO_LIVE_DISABLED
    if any(item.get("status") == READINESS_BLOCKED for item in categories):
        return READINESS_BLOCKED
    if any(item.get("status") == READINESS_PERMISSION_LIMITED for item in categories):
        return READINESS_PERMISSION_LIMITED
    if any(item.get("status") == READINESS_MISSING_EVIDENCE for item in categories):
        return READINESS_MISSING_EVIDENCE
    if any(item.get("status") == READINESS_IN_PROGRESS for item in categories):
        return READINESS_IN_PROGRESS
    return READINESS_READY


def _summary(categories: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {
        READINESS_READY: 0,
        READINESS_IN_PROGRESS: 0,
        READINESS_BLOCKED: 0,
        READINESS_MISSING_EVIDENCE: 0,
        READINESS_PERMISSION_LIMITED: 0,
        READINESS_GO_LIVE_DISABLED: 0,
    }
    for item in categories:
        status = str(item.get("status") or "")
        if status in counts:
            counts[status] += 1
    return {
        "ready_count": counts[READINESS_READY],
        "in_progress_count": counts[READINESS_IN_PROGRESS],
        "blocked_count": counts[READINESS_BLOCKED],
        "missing_evidence_count": counts[READINESS_MISSING_EVIDENCE],
        "permission_limited_count": counts[READINESS_PERMISSION_LIMITED],
        "go_live_disabled_count": counts[READINESS_GO_LIVE_DISABLED],
        "total_count": len(categories),
    }


def _guardrails(source_guardrails: Sequence[str]) -> list[str]:
    return sorted(set(source_guardrails).union(AGGREGATION_GUARDRAILS))


def _safe_missing(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        return []
    items: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        items.append(
            {
                "section": _safe_scalar(item.get("section") or "unknown"),
                "code": _safe_scalar(item.get("code") or "NO_SOURCE_EVIDENCE"),
                "severity": _safe_scalar(item.get("severity") or "INFO"),
                "message": _safe_scalar(item.get("message") or ""),
            }
        )
    return items


def _safe_source_warnings(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        return []
    warnings: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        warnings.append(
            {
                "code": _safe_scalar(item.get("code") or "SOURCE_WARNING"),
                "severity": _safe_scalar(item.get("severity") or "WARNING"),
                "source": _safe_scalar(item.get("source") or "onboarding"),
                "message": _safe_scalar(item.get("message") or ""),
            }
        )
    return warnings


def _safe_string_list(value: Any) -> list[str]:
    return [_safe_scalar(item) for item in _string_list(value)]


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


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


def _safe_scalar(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    return str(value).strip()


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
