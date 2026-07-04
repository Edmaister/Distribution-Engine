from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any, Final

from services.onboarding.onboarding_readiness_aggregation_service import (
    READINESS_GO_LIVE_DISABLED,
    aggregate_onboarding_readiness,
)
from services.onboarding.onboarding_state_projection_service import (
    SECTION_DEFINITIONS,
    project_onboarding_state,
)

VALIDATION_VALID: Final = "VALID"
VALIDATION_INVALID: Final = "INVALID"
VALIDATION_BLOCKED: Final = "BLOCKED"
VALIDATION_MISSING_EVIDENCE: Final = "MISSING_EVIDENCE"
VALIDATION_PERMISSION_LIMITED: Final = "PERMISSION_LIMITED"

ERROR_REQUIRED_FIELD_MISSING: Final = "REQUIRED_FIELD_MISSING"
ERROR_CROSS_SECTION_MISMATCH: Final = "CROSS_SECTION_MISMATCH"
ERROR_PERMISSION_DENIED: Final = "PERMISSION_DENIED"
ERROR_MISSING_EVIDENCE: Final = "MISSING_EVIDENCE"
ERROR_UNSAFE_FIELD: Final = "UNSAFE_FIELD"
ERROR_UNSAFE_OPERATION: Final = "UNSAFE_OPERATION"
ERROR_GO_LIVE_DISABLED: Final = "GO_LIVE_DISABLED"

GUARDRAILS: Final = [
    "DRY_RUN_ONLY",
    "NO_PERSISTENCE",
    "NO_LIVE_MUTATION",
    "TENANT_CODE_INTERNAL",
    "NO_SECRET_EXPOSURE",
    "NO_WEBHOOK_DELIVERY",
    "GO_LIVE_DISABLED",
    "NO_MONEY_MOVEMENT",
]

SCOPE_FIELDS: Final = (
    "external_tenant_ref",
    "organisation_ref",
    "producer_ref",
    "sponsor_ref",
    "distributor_ref",
    "campaign_code",
    "opportunity_ref",
)

PERMISSION_CATEGORY_BY_SECTION: Final = {
    name: definition["category"] for name, definition in SECTION_DEFINITIONS.items()
}

UNSAFE_KEY_CATEGORIES: Final[tuple[tuple[str, str, str], ...]] = (
    ("tenant_code", "internal_identifier", ERROR_UNSAFE_FIELD),
    ("ucn", "private_identifier", ERROR_UNSAFE_FIELD),
    ("secret", "secret_or_credential", ERROR_UNSAFE_FIELD),
    ("token", "secret_or_credential", ERROR_UNSAFE_FIELD),
    ("password", "secret_or_credential", ERROR_UNSAFE_FIELD),
    ("credential", "secret_or_credential", ERROR_UNSAFE_FIELD),
    ("api_key", "secret_or_credential", ERROR_UNSAFE_FIELD),
    ("client_secret", "secret_or_credential", ERROR_UNSAFE_FIELD),
    ("signing", "secret_or_credential", ERROR_UNSAFE_FIELD),
    ("certificate", "secret_or_credential", ERROR_UNSAFE_FIELD),
    ("private_key", "secret_or_credential", ERROR_UNSAFE_FIELD),
    ("provider", "provider_internal", ERROR_UNSAFE_FIELD),
    ("raw", "raw_internal", ERROR_UNSAFE_FIELD),
    ("audit", "audit_internal", ERROR_UNSAFE_FIELD),
    ("webhook_delivery", "webhook_internal", ERROR_UNSAFE_OPERATION),
    ("wallet", "money_movement_internal", ERROR_UNSAFE_OPERATION),
    ("settlement", "money_movement_internal", ERROR_UNSAFE_OPERATION),
    ("fulfilment", "money_movement_internal", ERROR_UNSAFE_OPERATION),
    ("funding_internal", "money_movement_internal", ERROR_UNSAFE_OPERATION),
    ("funding_reservation", "money_movement_internal", ERROR_UNSAFE_OPERATION),
    ("funding_transaction", "money_movement_internal", ERROR_UNSAFE_OPERATION),
    ("retry", "retry_internal", ERROR_UNSAFE_OPERATION),
    ("money", "money_movement_internal", ERROR_UNSAFE_OPERATION),
    ("publish", "live_action", ERROR_UNSAFE_OPERATION),
    ("launch", "live_action", ERROR_UNSAFE_OPERATION),
    ("activate_go_live", "live_action", ERROR_UNSAFE_OPERATION),
    ("send_invite", "live_action", ERROR_UNSAFE_OPERATION),
    ("create_tenant", "live_action", ERROR_UNSAFE_OPERATION),
    ("create_user", "live_action", ERROR_UNSAFE_OPERATION),
    ("deliver_webhook", "webhook_internal", ERROR_UNSAFE_OPERATION),
)


def validate_onboarding_draft(
    draft_payload: Mapping[str, Any] | None,
    *,
    actor_context: Mapping[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    payload = _as_mapping(draft_payload)
    context = _as_mapping(actor_context)
    redactions: set[str] = set()
    safe_errors: list[dict[str, str | None]] = []
    missing_evidence: list[dict[str, str | None]] = []
    blockers: list[dict[str, str | None]] = []
    warnings: list[dict[str, str | None]] = []

    safe_payload = _sanitize_mapping(
        payload,
        redactions=redactions,
        safe_errors=safe_errors,
        blockers=blockers,
    )
    scope = _safe_scope(safe_payload)
    sections = _safe_sections(safe_payload)

    _validate_required_fields(
        sections,
        safe_errors=safe_errors,
        missing_evidence=missing_evidence,
        blockers=blockers,
    )
    _validate_cross_section(
        scope,
        sections,
        safe_errors=safe_errors,
        blockers=blockers,
    )
    limited_categories = _permission_limited_categories(
        context,
        safe_errors=safe_errors,
        blockers=blockers,
    )
    go_live_error = _safe_error(
        code=ERROR_GO_LIVE_DISABLED,
        message="Go-live activation remains disabled for onboarding draft validation.",
        section="readiness",
        field=None,
        severity="INFO",
    )
    warnings.append(go_live_error)

    evidence = {"scope": scope, "sections": sections}
    projection = project_onboarding_state(evidence, generated_at=generated_at)
    readiness_preview = aggregate_onboarding_readiness(
        projection,
        permission_limited_categories=sorted(limited_categories),
        generated_at=generated_at,
    )
    redactions.update(_string_list(projection.get("redactions")))
    redactions.update(_string_list(readiness_preview.get("redactions")))
    missing_evidence.extend(_safe_missing(projection.get("missing_evidence")))

    validation_status = _validation_status(
        safe_errors=safe_errors,
        missing_evidence=missing_evidence,
        limited_categories=limited_categories,
    )
    checks = _checks(
        safe_errors=safe_errors,
        missing_evidence=missing_evidence,
        warnings=warnings,
        limited_categories=limited_categories,
    )

    return {
        "status": "ok",
        "validation_result": {
            "status": validation_status,
            "contract_version": projection["contract_version"],
            "generated_at": generated_at or _now_iso(),
            "validated_scope": projection["scope"],
            "validated_sections": sorted(sections),
            "checks": checks,
        },
        "readiness_preview": readiness_preview,
        "missing_evidence": _dedupe_items(missing_evidence),
        "blockers": _dedupe_items(blockers),
        "warnings": _dedupe_items(warnings),
        "safe_errors": _dedupe_items(safe_errors),
        "next_actions": _next_actions(readiness_preview, safe_errors, missing_evidence),
        "guardrails": sorted(set(GUARDRAILS).union(readiness_preview["guardrails"])),
        "redactions": sorted(redactions),
        "no_persistence_confirmed": True,
    }


def _validate_required_fields(
    sections: Mapping[str, Mapping[str, Any]],
    *,
    safe_errors: list[dict[str, str | None]],
    missing_evidence: list[dict[str, str | None]],
    blockers: list[dict[str, str | None]],
) -> None:
    for section_name, definition in SECTION_DEFINITIONS.items():
        section = _as_mapping(sections.get(section_name))
        if not section:
            missing_evidence.append(
                _safe_error(
                    code=ERROR_MISSING_EVIDENCE,
                    message=f"{definition['label']} evidence is missing.",
                    section=section_name,
                    field=None,
                    severity="INFO",
                )
            )
            continue

        for field in definition["fields"]:
            if _is_blank(section.get(field)):
                item = _safe_error(
                    code=ERROR_REQUIRED_FIELD_MISSING,
                    message="Required onboarding draft field is missing.",
                    section=section_name,
                    field=field,
                    severity="BLOCKER",
                )
                safe_errors.append(item)
                blockers.append(item)
                missing_evidence.append(item)


def _validate_cross_section(
    scope: Mapping[str, Any],
    sections: Mapping[str, Mapping[str, Any]],
    *,
    safe_errors: list[dict[str, str | None]],
    blockers: list[dict[str, str | None]],
) -> None:
    for section_name, section in sections.items():
        for field in SCOPE_FIELDS:
            scope_value = _safe_text(scope.get(field))
            section_value = _safe_text(section.get(field))
            if scope_value and section_value and scope_value != section_value:
                item = _safe_error(
                    code=ERROR_CROSS_SECTION_MISMATCH,
                    message="Section reference does not match the draft scope.",
                    section=section_name,
                    field=field,
                    severity="BLOCKER",
                )
                safe_errors.append(item)
                blockers.append(item)

    producer = _safe_text(sections.get("producer_sponsor", {}).get("producer_ref"))
    campaign_producer = _safe_text(
        sections.get("campaign_opportunity", {}).get("producer_ref")
    )
    if producer and campaign_producer and producer != campaign_producer:
        item = _safe_error(
            code=ERROR_CROSS_SECTION_MISMATCH,
            message="Campaign producer reference does not match producer setup.",
            section="campaign_opportunity",
            field="producer_ref",
            severity="BLOCKER",
        )
        safe_errors.append(item)
        blockers.append(item)


def _permission_limited_categories(
    actor_context: Mapping[str, Any],
    *,
    safe_errors: list[dict[str, str | None]],
    blockers: list[dict[str, str | None]],
) -> set[str]:
    limited = {
        str(item or "").strip().upper()
        for item in _string_list(actor_context.get("permission_limited_categories"))
        if str(item or "").strip()
    }
    allowed = {
        str(item or "").strip().upper()
        for item in _string_list(actor_context.get("allowed_categories"))
        if str(item or "").strip()
    }
    if allowed:
        limited.update(
            category
            for category in PERMISSION_CATEGORY_BY_SECTION.values()
            if category not in allowed
        )

    for category in sorted(limited):
        item = _safe_error(
            code=ERROR_PERMISSION_DENIED,
            message="Current actor cannot validate all evidence for this category.",
            section=_section_for_category(category),
            field=None,
            severity="BLOCKER",
        )
        safe_errors.append(item)
        blockers.append(item)
    return limited


def _validation_status(
    *,
    safe_errors: Sequence[Mapping[str, Any]],
    missing_evidence: Sequence[Mapping[str, Any]],
    limited_categories: set[str],
) -> str:
    codes = {str(item.get("code") or "") for item in safe_errors}
    if ERROR_UNSAFE_OPERATION in codes or ERROR_UNSAFE_FIELD in codes:
        return VALIDATION_BLOCKED
    if limited_categories or ERROR_PERMISSION_DENIED in codes:
        return VALIDATION_PERMISSION_LIMITED
    if safe_errors:
        return VALIDATION_INVALID
    if missing_evidence:
        return VALIDATION_MISSING_EVIDENCE
    return VALIDATION_VALID


def _checks(
    *,
    safe_errors: Sequence[Mapping[str, Any]],
    missing_evidence: Sequence[Mapping[str, Any]],
    warnings: Sequence[Mapping[str, Any]],
    limited_categories: set[str],
) -> list[dict[str, Any]]:
    return [
        {
            "category": "FIELD_VALIDATION",
            "status": "FAILED" if safe_errors else "PASSED",
        },
        {
            "category": "MISSING_EVIDENCE",
            "status": "FAILED" if missing_evidence else "PASSED",
        },
        {
            "category": "PERMISSION_VALIDATION",
            "status": "LIMITED" if limited_categories else "PASSED",
        },
        {
            "category": "GO_LIVE_CONTROLS",
            "status": READINESS_GO_LIVE_DISABLED,
            "warnings": list(warnings),
        },
    ]


def _safe_scope(payload: Mapping[str, Any]) -> dict[str, Any]:
    source = _as_mapping(payload.get("scope"))
    return {
        field: _safe_value(source.get(field, payload.get(field)))
        for field in SCOPE_FIELDS
    }


def _safe_sections(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    source = _as_mapping(payload.get("sections"))
    return {
        name: _as_mapping(source.get(name, payload.get(name)))
        for name in SECTION_DEFINITIONS
        if _as_mapping(source.get(name, payload.get(name)))
    }


def _sanitize_mapping(
    value: Mapping[str, Any],
    *,
    redactions: set[str],
    safe_errors: list[dict[str, str | None]],
    blockers: list[dict[str, str | None]],
    section: str | None = None,
) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, item in value.items():
        normalized = _normalise_key(key)
        unsafe = _unsafe_category(normalized)
        if unsafe:
            redaction, error_code = unsafe
            redactions.add(redaction)
            error = _safe_error(
                code=error_code,
                message="Unsafe onboarding draft field was omitted.",
                section=section or _section_from_key(str(key)),
                field=None,
                severity="BLOCKER",
            )
            safe_errors.append(error)
            blockers.append(error)
            continue
        if isinstance(item, Mapping):
            child_section = str(key) if str(key) in SECTION_DEFINITIONS else section
            safe[str(key)] = _sanitize_mapping(
                item,
                redactions=redactions,
                safe_errors=safe_errors,
                blockers=blockers,
                section=child_section,
            )
        elif isinstance(item, Sequence) and not isinstance(
            item, str | bytes | bytearray
        ):
            safe[str(key)] = [
                _safe_value(child) for child in item if not isinstance(child, Mapping)
            ]
        else:
            safe[str(key)] = _safe_value(item)
    return safe


def _unsafe_category(normalized_key: str) -> tuple[str, str] | None:
    for part, category, error_code in UNSAFE_KEY_CATEGORIES:
        if part in normalized_key:
            return category, error_code
    return None


def _next_actions(
    readiness_preview: Mapping[str, Any],
    safe_errors: Sequence[Mapping[str, Any]],
    missing_evidence: Sequence[Mapping[str, Any]],
) -> list[str]:
    actions: list[str] = []
    if safe_errors:
        actions.append("Resolve validation blockers before review.")
    if missing_evidence:
        actions.append("Provide the missing onboarding evidence.")
    actions.append("Keep go-live and live platform actions disabled.")
    for category in _as_sequence(readiness_preview.get("categories")):
        if not isinstance(category, Mapping):
            continue
        for action in _string_list(category.get("next_actions")):
            if action not in actions:
                actions.append(action)
    return actions


def _safe_missing(value: Any) -> list[dict[str, str | None]]:
    items: list[dict[str, str | None]] = []
    for item in _as_sequence(value):
        if not isinstance(item, Mapping):
            continue
        items.append(
            _safe_error(
                code=str(item.get("code") or ERROR_MISSING_EVIDENCE),
                message=str(item.get("message") or "Required evidence is missing."),
                section=str(item.get("section") or "unknown"),
                field=str(item.get("field")) if item.get("field") else None,
                severity=str(item.get("severity") or "INFO"),
            )
        )
    return items


def _dedupe_items(items: Sequence[Mapping[str, Any]]) -> list[dict[str, str | None]]:
    seen: set[tuple[str | None, str | None, str | None, str | None]] = set()
    deduped: list[dict[str, str | None]] = []
    for item in items:
        normalised = {
            "code": _safe_text(item.get("code")),
            "message": _safe_text(item.get("message")),
            "section": _safe_text(item.get("section")),
            "field": _safe_text(item.get("field")) or None,
            "severity": _safe_text(item.get("severity")) or "INFO",
        }
        key = (
            normalised["code"],
            normalised["section"],
            normalised["field"],
            normalised["message"],
        )
        if key not in seen:
            seen.add(key)
            deduped.append(normalised)
    return deduped


def _safe_error(
    *,
    code: str,
    message: str,
    section: str | None,
    field: str | None,
    severity: str,
) -> dict[str, str | None]:
    return {
        "code": code,
        "message": message,
        "section": section,
        "field": field,
        "severity": severity,
    }


def _section_for_category(category: str) -> str | None:
    for section, mapped_category in PERMISSION_CATEGORY_BY_SECTION.items():
        if mapped_category == category:
            return section
    return "security"


def _section_from_key(key: str) -> str:
    normalized = _normalise_key(key)
    for section in SECTION_DEFINITIONS:
        if section in normalized:
            return section
    return "draft"


def _normalise_key(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def _safe_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool | int | float):
        return value
    return str(value).strip()


def _safe_text(value: Any) -> str:
    safe = _safe_value(value)
    return "" if safe is None else str(safe)


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


def _as_sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return value
    return []


def _is_blank(value: Any) -> bool:
    return value is None or value == "" or value == []


def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
