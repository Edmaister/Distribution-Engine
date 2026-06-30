from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from services.onboarding.onboarding_draft_idempotency_service import hash_payload

OPERATION_DRAFT_CREATE: Final = "ONBOARDING_DRAFT_CREATE"
EVIDENCE_TYPE_DRAFT_SAVE: Final = "DRAFT_SAVE_AUDIT_EVIDENCE"
EMPTY_STATE_HASH: Final = hash_payload({"state": "empty_onboarding_draft"})

SCOPE_FIELDS: Final = (
    "external_tenant_ref",
    "organisation_ref",
    "producer_ref",
    "sponsor_ref",
    "distributor_ref",
    "campaign_code",
    "opportunity_ref",
)

UNSAFE_KEY_CATEGORIES: Final[tuple[tuple[str, str], ...]] = (
    ("tenant_code", "internal_identifier"),
    ("ucn", "private_identifier"),
    ("api_key", "secret_or_credential"),
    ("client_secret", "secret_or_credential"),
    ("secret", "secret_or_credential"),
    ("token", "secret_or_credential"),
    ("password", "secret_or_credential"),
    ("credential", "secret_or_credential"),
    ("signing", "secret_or_credential"),
    ("certificate", "secret_or_credential"),
    ("private_key", "secret_or_credential"),
    ("provider", "provider_internal"),
    ("raw", "raw_internal"),
    ("audit", "audit_internal"),
    ("webhook_delivery", "webhook_internal"),
    ("deliver_webhook", "webhook_internal"),
    ("webhook_retry", "webhook_internal"),
    ("replay", "repair_or_replay_internal"),
    ("repair", "repair_or_replay_internal"),
    ("wallet", "money_movement_internal"),
    ("funding", "money_movement_internal"),
    ("settlement", "money_movement_internal"),
    ("fulfilment", "money_movement_internal"),
    ("retry", "retry_internal"),
    ("money", "money_movement_internal"),
    ("publish", "live_action"),
    ("launch", "live_action"),
    ("activate_go_live", "live_action"),
    ("send_invite", "live_action"),
    ("create_tenant", "live_action"),
    ("create_user", "live_action"),
)


def build_draft_save_audit_evidence(
    *,
    actor_ref: str,
    actor_role: str,
    external_scope: Mapping[str, Any],
    draft_ref: str,
    action_status: str,
    idempotency_reference: str | None,
    correlation_id: str | None,
    current_sections: Mapping[str, Mapping[str, Any]] | None,
    validation: Mapping[str, Any] | None = None,
    permission_scope: Mapping[str, Any] | None = None,
    prior_sections: Mapping[str, Mapping[str, Any]] | None = None,
    operation_type: str = OPERATION_DRAFT_CREATE,
    draft_version: int | None = None,
) -> dict[str, Any]:
    safe_scope = _safe_scope(external_scope)
    safe_current, redactions = _safe_sections(current_sections)
    safe_prior, prior_redactions = _safe_sections(prior_sections)
    redactions.update(prior_redactions)
    redactions.update(_string_set(_as_mapping(validation).get("redactions")))

    validation_summary = _validation_summary(validation)
    readiness_summary = _readiness_summary(validation)
    changed_sections = _changed_sections(safe_prior, safe_current)
    before_state_hash = (
        hash_payload({"sections": safe_prior}) if safe_prior else EMPTY_STATE_HASH
    )
    after_state_hash = hash_payload(
        {
            "draft_ref": _safe_text(draft_ref),
            "draft_version": draft_version,
            "operation_type": _safe_text(operation_type).upper(),
            "action_status": _safe_text(action_status).upper(),
            "scope": safe_scope,
            "sections": safe_current,
            "validation_summary": validation_summary,
            "readiness_summary": readiness_summary,
        }
    )

    evidence = {
        "actor_ref": _safe_text(actor_ref) or "UNKNOWN_ACTOR",
        "actor_role": _safe_text(actor_role).upper() or "UNKNOWN_ROLE",
        "permission_scope": _safe_permission_scope(permission_scope, safe_scope),
        "external_scope": safe_scope,
        "draft_ref": _safe_text(draft_ref),
        "draft_version": draft_version,
        "operation_type": _safe_text(operation_type).upper(),
        "action_status": _safe_text(action_status).upper(),
        "idempotency_reference": _safe_text(idempotency_reference),
        "correlation_id": _safe_text(correlation_id),
        "before_state_hash": before_state_hash,
        "after_state_hash": after_state_hash,
        "changed_sections": changed_sections,
        "validation_summary": validation_summary,
        "readiness_summary": readiness_summary,
        "redaction_summary": {
            "categories": sorted(redactions),
            "redacted": bool(redactions),
        },
        "no_live_action_confirmed": True,
    }
    return _drop_blank_values(evidence)


def build_draft_save_audit_link_fields(
    *,
    draft_id: str,
    evidence: Mapping[str, Any],
    idempotency_id: str | None = None,
) -> dict[str, Any]:
    return {
        "draft_id": _safe_text(draft_id),
        "draft_ref": _safe_text(evidence.get("draft_ref")),
        "draft_version": evidence.get("draft_version"),
        "action_type": _safe_text(evidence.get("operation_type")),
        "action_status": _safe_text(evidence.get("action_status")),
        "actor_ref": _safe_text(evidence.get("actor_ref")),
        "actor_role": _safe_text(evidence.get("actor_role")),
        "correlation_id": _safe_text(evidence.get("correlation_id")),
        "evidence_type": EVIDENCE_TYPE_DRAFT_SAVE,
        "audit_ref": None,
        "event_ref": None,
        "idempotency_id": _safe_text(idempotency_id) or None,
        "before_state_hash": _safe_text(evidence.get("before_state_hash")),
        "after_state_hash": _safe_text(evidence.get("after_state_hash")),
        "changed_sections": list(_as_sequence(evidence.get("changed_sections"))),
        "redactions": list(
            _as_sequence(
                _as_mapping(evidence.get("redaction_summary")).get("categories")
            )
        ),
        "evidence_summary": _evidence_summary(evidence),
    }


def _evidence_summary(evidence: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "operation_type": _safe_text(evidence.get("operation_type")),
        "action_status": _safe_text(evidence.get("action_status")),
        "external_scope": _as_mapping(evidence.get("external_scope")),
        "idempotency_reference": _safe_text(evidence.get("idempotency_reference")),
        "correlation_id": _safe_text(evidence.get("correlation_id")),
        "changed_sections": list(_as_sequence(evidence.get("changed_sections"))),
        "validation_summary": _as_mapping(evidence.get("validation_summary")),
        "readiness_summary": _as_mapping(evidence.get("readiness_summary")),
        "redaction_summary": _as_mapping(evidence.get("redaction_summary")),
        "no_live_action_confirmed": True,
        "dispatch": {
            "event_dispatched": False,
            "webhook_dispatched": False,
            "event_ref": None,
        },
    }


def _safe_scope(scope: Mapping[str, Any]) -> dict[str, str]:
    return {
        field: _safe_text(scope.get(field))
        for field in SCOPE_FIELDS
        if _safe_text(scope.get(field))
    }


def _safe_sections(
    sections: Mapping[str, Mapping[str, Any]] | None,
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    safe: dict[str, dict[str, Any]] = {}
    redactions: set[str] = set()
    for section_key, section in _as_mapping(sections).items():
        if not isinstance(section, Mapping):
            continue
        section_safe = _safe_mapping(section, redactions=redactions)
        if section_safe:
            safe[_safe_text(section_key)] = section_safe
    return safe, redactions


def _safe_mapping(value: Mapping[str, Any], *, redactions: set[str]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, item in value.items():
        normalized = _normalise_key(key)
        unsafe_category = _unsafe_category(normalized)
        if unsafe_category:
            redactions.add(unsafe_category)
            continue
        if isinstance(item, Mapping):
            nested = _safe_mapping(item, redactions=redactions)
            if nested:
                safe[str(key)] = nested
        elif isinstance(item, Sequence) and not isinstance(
            item, str | bytes | bytearray
        ):
            safe[str(key)] = [
                _safe_text(child) for child in item if not isinstance(child, Mapping)
            ]
        else:
            safe[str(key)] = _safe_value(item)
    return safe


def _changed_sections(
    prior_sections: Mapping[str, Mapping[str, Any]],
    current_sections: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    changed: list[str] = []
    section_keys = sorted(set(prior_sections).union(current_sections))
    for section_key in section_keys:
        if hash_payload(prior_sections.get(section_key)) != hash_payload(
            current_sections.get(section_key)
        ):
            changed.append(section_key)
    return changed


def _validation_summary(validation: Mapping[str, Any] | None) -> dict[str, Any]:
    source = _as_mapping(validation)
    validation_result = _as_mapping(source.get("validation_result"))
    return {
        "status": _safe_text(validation_result.get("status")) or "UNKNOWN",
        "safe_error_count": len(_as_sequence(source.get("safe_errors"))),
        "missing_evidence_count": len(_as_sequence(source.get("missing_evidence"))),
        "blocker_count": len(_as_sequence(source.get("blockers"))),
    }


def _readiness_summary(validation: Mapping[str, Any] | None) -> dict[str, Any]:
    readiness = _as_mapping(_as_mapping(validation).get("readiness_preview"))
    summary = _as_mapping(readiness.get("summary"))
    return {
        "overall_status": _safe_text(readiness.get("overall_status")) or "UNKNOWN",
        "ready_count": summary.get("ready_count", 0),
        "blocked_count": summary.get("blocked_count", 0),
        "missing_evidence_count": summary.get("missing_evidence_count", 0),
        "go_live_disabled_count": summary.get("go_live_disabled_count", 0),
        "total_count": summary.get("total_count", 0),
    }


def _safe_permission_scope(
    permission_scope: Mapping[str, Any] | None,
    external_scope: Mapping[str, Any],
) -> dict[str, Any]:
    source = _as_mapping(permission_scope)
    return {
        "route_family": _safe_text(source.get("route_family")) or "admin_onboarding",
        "role_family": _safe_text(source.get("role_family")) or "admin_operator",
        "external_scope": dict(external_scope),
    }


def _unsafe_category(normalized_key: str) -> str | None:
    for part, category in UNSAFE_KEY_CATEGORIES:
        if part in normalized_key:
            return category
    return None


def _drop_blank_values(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: item
        for key, item in value.items()
        if item is not None and item != "" and item != {} and item != []
    }


def _string_set(value: Any) -> set[str]:
    return {_safe_text(item) for item in _as_sequence(value) if _safe_text(item)}


def _safe_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool | int | float):
        return value
    return _safe_text(value)


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _normalise_key(value: Any) -> str:
    return _safe_text(value).lower().replace("-", "_")


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return value
    return []
