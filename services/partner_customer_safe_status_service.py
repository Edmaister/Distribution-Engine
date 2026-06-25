from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final, Literal

from services.fulfilment_safe_status import map_fulfilment_status, map_settlement_status

ViewerRole = Literal[
    "partner", "distributor", "sponsor", "producer", "referrer", "customer"
]

SAFE_STATUS_LABELS: Final[dict[str, str]] = {
    "NOT_STARTED": "Not started",
    "PENDING": "Pending",
    "IN_PROGRESS": "In progress",
    "QUALIFIED": "Qualified",
    "APPROVED": "Approved",
    "FULFILLED": "Fulfilled",
    "SETTLED": "Settled",
    "ADJUSTED": "Adjusted",
    "DECLINED": "Declined",
    "EXPIRED": "Expired",
    "ACTION_REQUIRED": "Action required",
    "UNAVAILABLE": "Unavailable",
}

TERMINAL_STATUSES: Final = {
    "FULFILLED",
    "SETTLED",
    "ADJUSTED",
    "DECLINED",
    "EXPIRED",
}

ACTION_REQUIRED_STATUSES: Final = {"ACTION_REQUIRED"}

ROLE_VISIBLE_FAMILIES: Final[dict[str, frozenset[str]]] = {
    "partner": frozenset(
        {
            "outcome",
            "campaign",
            "reward",
            "fulfilment",
            "settlement",
            "webhook",
            "integration",
        }
    ),
    "distributor": frozenset(
        {"outcome", "campaign", "commission", "wallet", "settlement", "webhook"}
    ),
    "sponsor": frozenset(
        {"campaign", "outcome", "funding", "liability", "billing", "settlement"}
    ),
    "producer": frozenset(
        {"campaign", "outcome", "funding", "liability", "billing", "settlement"}
    ),
    "referrer": frozenset({"outcome", "reward", "fulfilment"}),
    "customer": frozenset({"outcome", "reward", "fulfilment"}),
}

UNSAFE_FIELD_PARTS: Final = (
    "ACCESS_TOKEN",
    "ACTOR_",
    "ADMIN_AUDIT",
    "AUDIT_PAYLOAD",
    "BEFORE",
    "CLIENT_SECRET",
    "DLQ",
    "EXCEPTION_PAYLOAD",
    "FUNDING_ACCOUNT",
    "PASSWORD",
    "PROVIDER",
    "RAW",
    "SECRET",
    "SETTLEMENT_INTERNAL",
    "SIGNING",
    "TENANT_CODE",
    "TOKEN",
    "UCN",
    "WEBHOOK_SECRET",
)


def project_partner_customer_safe_status(
    *,
    viewer_role: str,
    subject: Mapping[str, Any],
    evidence: Mapping[str, Any] | None = None,
    source_family: str | None = None,
    source_status: object = None,
    missing_evidence: Sequence[Mapping[str, Any]] | None = None,
    redactions: Sequence[str] | None = None,
) -> dict[str, Any]:
    role = _normalize_role(viewer_role)
    safe_subject = _safe_subject(subject)
    family = _source_family(source_family, evidence)
    evidence_data = dict(evidence or {})
    _reject_unsafe_keys(evidence_data, "evidence")

    if family not in ROLE_VISIBLE_FAMILIES[role]:
        return _status(
            role=role,
            subject=safe_subject,
            status="UNAVAILABLE",
            summary="Status is not available for this viewer.",
            what_happened="The source family is outside this viewer's safe scope.",
            what_happens_next="Use an authorized role for this status.",
            action_category="NOT_AVAILABLE",
            source_families=[family],
            source_confidence="LOW",
            missing_evidence=[
                _safe_missing(
                    {
                        "section": family,
                        "code": "REDACTED",
                        "severity": "INFO",
                        "message": "Source family is not visible for this role.",
                    }
                )
            ],
            redactions=_safe_redactions(redactions, "role_scope"),
        )

    raw_status = source_status or _raw_status(evidence_data)
    if family == "fulfilment":
        mapped = map_fulfilment_status(raw_status, surface="external")
        status = str(mapped["status"])
        action_category = _action_category(family, raw_status, status)
    elif family == "settlement":
        mapped = map_settlement_status(raw_status, surface="external")
        status = str(mapped["status"])
        action_category = _action_category(family, raw_status, status)
    else:
        status = _map_status(family, raw_status, evidence_data)
        action_category = _action_category(family, raw_status, status)

    safe_missing = [_safe_missing(item) for item in missing_evidence or []]
    if safe_missing and status not in {"ACTION_REQUIRED", "UNAVAILABLE"}:
        status, action_category = _missing_override(
            status, action_category, safe_missing
        )

    return _status(
        role=role,
        subject=safe_subject,
        status=status,
        summary=_summary(role, family, status),
        what_happened=_what_happened(family, status),
        what_happens_next=_what_happens_next(action_category, status),
        action_category=action_category,
        source_families=[family],
        source_confidence=str(evidence_data.get("source_confidence") or "MEDIUM"),
        missing_evidence=safe_missing,
        redactions=_safe_redactions(redactions),
    )


def project_safe_statuses(
    *,
    viewer_role: str,
    subject: Mapping[str, Any],
    evidence_items: Sequence[Mapping[str, Any]],
    redactions: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    return [
        project_partner_customer_safe_status(
            viewer_role=viewer_role,
            subject=subject,
            evidence=item,
            redactions=redactions,
        )
        for item in evidence_items
    ]


def _normalize_role(viewer_role: str) -> str:
    role = str(viewer_role or "").strip().lower().replace("_", "-")
    role = "customer" if role in {"consumer", "referee"} else role
    role = "sponsor" if role == "sponsor/producer" else role
    if role not in ROLE_VISIBLE_FAMILIES:
        raise ValueError("Unsupported viewer_role for safe status projection.")
    return role


def _safe_subject(subject: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(subject, Mapping):
        raise ValueError("subject must be an object.")
    subject_type = str(subject.get("type") or "").strip()
    safe_ref = str(subject.get("safe_ref") or subject.get("id") or "").strip()
    if not subject_type or not safe_ref:
        raise ValueError("subject.type and subject.safe_ref are required.")
    _reject_unsafe_keys(subject, "subject")
    return {"type": subject_type, "safe_ref": safe_ref}


def _source_family(
    source_family: str | None, evidence: Mapping[str, Any] | None
) -> str:
    family = (
        str(
            source_family
            or (evidence or {}).get("source_family")
            or (evidence or {}).get("family")
            or "missing_evidence"
        )
        .strip()
        .lower()
    )
    return "webhook" if family == "integration" else family


def _raw_status(evidence: Mapping[str, Any]) -> object:
    return (
        evidence.get("status")
        or evidence.get("safe_status")
        or evidence.get("derived_state")
        or evidence.get("commission_status")
        or evidence.get("source_status")
        or evidence.get("delivery_status")
        or evidence.get("subscription_status")
    )


def _map_status(family: str, raw_status: object, evidence: Mapping[str, Any]) -> str:
    status = str(raw_status or "").strip().upper()
    if not status:
        return "UNAVAILABLE"
    mappings = {
        "outcome": {
            "NOT_STARTED": "NOT_STARTED",
            "PENDING": "PENDING",
            "IN_PROGRESS": "IN_PROGRESS",
            "PROCESSING": "IN_PROGRESS",
            "QUALIFIED": "QUALIFIED",
            "COMPLETED": "FULFILLED",
            "COMPLETE": "FULFILLED",
            "FULFILLED": "FULFILLED",
            "BLOCKED": "ACTION_REQUIRED",
            "FAILED": "ACTION_REQUIRED",
        },
        "campaign": {
            "DRAFT": "PENDING",
            "PENDING": "PENDING",
            "APPROVED": "APPROVED",
            "ACTIVE": "APPROVED",
            "PUBLISHED": "APPROVED",
            "DECLINED": "DECLINED",
            "REJECTED": "DECLINED",
            "CLOSED": "EXPIRED",
            "EXPIRED": "EXPIRED",
        },
        "reward": {
            "APPLIED": "APPROVED",
            "EARNED": "QUALIFIED",
            "PENDING_FULFILMENT": "IN_PROGRESS",
            "PENDING": "PENDING",
            "PROCESSING": "IN_PROGRESS",
            "FULFILLED": "FULFILLED",
            "FAILED": "ACTION_REQUIRED",
            "REVERSED": "ADJUSTED",
        },
        "commission": {
            "CALCULATED": "APPROVED",
            "APPROVED": "APPROVED",
            "CREDITED": "FULFILLED",
            "FULFILLED": "FULFILLED",
            "PENDING": "PENDING",
            "PROCESSING": "IN_PROGRESS",
            "REVERSED": "ADJUSTED",
            "ADJUSTED": "ADJUSTED",
            "FAILED": "ACTION_REQUIRED",
        },
        "wallet": {
            "CREDITED": "FULFILLED",
            "POSTED": "FULFILLED",
            "PENDING": "PENDING",
            "PROCESSING": "IN_PROGRESS",
            "REVERSED": "ADJUSTED",
            "ADJUSTED": "ADJUSTED",
        },
        "funding": {
            "PENDING": "PENDING",
            "RESERVED": "APPROVED",
            "PROCESSING": "IN_PROGRESS",
            "RELEASED": "ADJUSTED",
            "SETTLED": "SETTLED",
            "REVERSED": "ADJUSTED",
            "FAILED": "ACTION_REQUIRED",
            "DISPUTED": "ACTION_REQUIRED",
        },
        "liability": {
            "PENDING": "PENDING",
            "RESERVED": "APPROVED",
            "CALCULATED": "APPROVED",
            "FULFILLED": "FULFILLED",
            "SETTLED": "SETTLED",
            "REVERSED": "ADJUSTED",
            "FAILED": "ACTION_REQUIRED",
            "DISPUTED": "ACTION_REQUIRED",
        },
        "billing": {
            "PENDING": "PENDING",
            "PROCESSING": "IN_PROGRESS",
            "INVOICED": "APPROVED",
            "PAID": "SETTLED",
            "SETTLED": "SETTLED",
            "ADJUSTED": "ADJUSTED",
            "FAILED": "ACTION_REQUIRED",
        },
        "webhook": {
            "ACTIVE": "APPROVED",
            "PAUSED": "ACTION_REQUIRED",
            "REVOKED": "ACTION_REQUIRED",
            "PENDING": "PENDING",
            "SENT": "FULFILLED",
            "FAILED": "ACTION_REQUIRED",
            "CANCELLED": "ADJUSTED",
        },
        "missing_evidence": {
            "NO_SOURCE_EVIDENCE": "PENDING",
            "JOIN_AMBIGUOUS": "UNAVAILABLE",
            "SOURCE_UNAVAILABLE": "UNAVAILABLE",
            "SOURCE_CONFLICT": "ACTION_REQUIRED",
            "REDACTED": "UNAVAILABLE",
            "NOT_APPLICABLE": "FULFILLED",
        },
    }
    return mappings.get(family, {}).get(status, "UNAVAILABLE")


def _action_category(family: str, raw_status: object, safe_status: str) -> str:
    status = str(raw_status or "").strip().upper()
    if safe_status in {"FULFILLED", "SETTLED", "APPROVED", "QUALIFIED", "ADJUSTED"}:
        if safe_status == "ADJUSTED" and family in {
            "settlement",
            "commission",
            "funding",
        }:
            return "REVIEW_DISPUTE"
        return "NONE"
    if safe_status == "PENDING":
        return "WAITING_FOR_EVENT"
    if safe_status == "IN_PROGRESS":
        return "RETRY_LATER" if status in {"PROCESSING", "FAILED_RETRYABLE"} else "NONE"
    if safe_status == "ACTION_REQUIRED":
        if family == "settlement" and status in {"DISPUTED", "REVERSED"}:
            return "REVIEW_DISPUTE"
        if family in {"wallet", "billing", "funding"}:
            return "VERIFY_PAYMENT_DETAILS"
        if family == "campaign":
            return "ACCEPT_OFFER"
        if family == "webhook":
            return "CONTACT_SUPPORT"
        return "CONTACT_SUPPORT"
    if safe_status in {"UNAVAILABLE", "NOT_STARTED"}:
        return "NOT_AVAILABLE"
    return "NONE"


def _missing_override(
    status: str, action_category: str, missing_evidence: list[dict[str, str]]
) -> tuple[str, str]:
    codes = {item.get("code") for item in missing_evidence}
    if "SOURCE_CONFLICT" in codes:
        return "ACTION_REQUIRED", "CONTACT_SUPPORT"
    if codes & {"JOIN_AMBIGUOUS", "SOURCE_UNAVAILABLE", "REDACTED"}:
        return "UNAVAILABLE", "NOT_AVAILABLE"
    if "NO_SOURCE_EVIDENCE" in codes and status in {"UNAVAILABLE", "NOT_STARTED"}:
        return "PENDING", "WAITING_FOR_EVENT"
    return status, action_category


def _status(
    *,
    role: str,
    subject: dict[str, str],
    status: str,
    summary: str,
    what_happened: str,
    what_happens_next: str,
    action_category: str,
    source_families: list[str],
    source_confidence: str,
    missing_evidence: list[dict[str, str]],
    redactions: list[str],
) -> dict[str, Any]:
    return {
        "viewer_role": role,
        "subject": subject,
        "safe_status": {
            "status": status,
            "label": SAFE_STATUS_LABELS[status],
            "summary": summary,
            "what_happened": what_happened,
            "what_happens_next": what_happens_next,
            "action_required": status in ACTION_REQUIRED_STATUSES
            or action_category
            not in {
                "NONE",
                "WAITING_FOR_EVENT",
                "RETRY_LATER",
                "NOT_AVAILABLE",
            },
            "action_category": action_category,
            "terminal": status in TERMINAL_STATUSES,
            "source_families": source_families,
            "source_confidence": source_confidence,
            "missing_evidence": missing_evidence,
            "redactions": redactions,
        },
    }


def _summary(role: str, family: str, status: str) -> str:
    role_label = "sponsor" if role == "producer" else role
    if status == "UNAVAILABLE":
        return "Status is not currently available."
    if status == "ACTION_REQUIRED":
        return "Support review is required."
    if status == "IN_PROGRESS":
        return f"Your {family} status is in progress."
    return f"Your {family} status is {SAFE_STATUS_LABELS[status].lower()} for this {role_label} view."


def _what_happened(family: str, status: str) -> str:
    if status == "UNAVAILABLE":
        return "Current source evidence cannot safely show a status."
    if status == "ACTION_REQUIRED":
        return f"{family.title()} evidence needs safe review."
    if status in {"FULFILLED", "SETTLED"}:
        return f"{family.title()} evidence shows completion."
    return f"{family.title()} evidence was received."


def _what_happens_next(action_category: str, status: str) -> str:
    if action_category == "NONE":
        return "No action is required."
    if action_category == "WAITING_FOR_EVENT":
        return "The platform is waiting for more evidence."
    if action_category == "RETRY_LATER":
        return "The platform is still processing this status."
    if action_category == "REVIEW_DISPUTE":
        return "Review the visible dispute or adjustment with support."
    if action_category == "VERIFY_PAYMENT_DETAILS":
        return "Review payment or billing setup with support."
    if action_category == "ACCEPT_OFFER":
        return "Review the offer or route in the appropriate portal."
    if action_category == "CONTACT_SUPPORT":
        return "Contact support for help with this status."
    if action_category == "NOT_AVAILABLE" or status == "UNAVAILABLE":
        return "Status can be checked again when safe evidence is available."
    return "Follow the next action shown for this status."


def _safe_missing(item: Mapping[str, Any]) -> dict[str, str]:
    _reject_unsafe_keys(item, "missing_evidence")
    return {
        "code": str(item.get("code") or "NO_SOURCE_EVIDENCE"),
        "severity": str(item.get("severity") or "INFO"),
        "section": str(item.get("section") or "unknown"),
    }


def _safe_redactions(redactions: Sequence[str] | None, *extra: str) -> list[str]:
    values = {str(item).strip() for item in redactions or [] if str(item).strip()}
    values.update(extra)
    values.update({"provider_payload", "private_identifier", "raw_status"})
    return sorted(values)


def _reject_unsafe_keys(value: Mapping[str, Any], path: str) -> None:
    for key, item in value.items():
        normalized = str(key).strip().upper().replace("-", "_")
        if any(part in normalized for part in UNSAFE_FIELD_PARTS):
            raise ValueError(
                f"{path} must not expose raw, provider, settlement, tenant, UCN, audit, or secret fields."
            )
        if isinstance(item, Mapping):
            _reject_unsafe_keys(item, path)
