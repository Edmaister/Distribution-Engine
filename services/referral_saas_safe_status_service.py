from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from services.partner_customer_safe_status_service import (
    project_partner_customer_safe_status,
)

PRODUCT_STATUS_LABELS: Final[dict[str, str]] = {
    "NOT_STARTED": "Not started",
    "WAITING": "Waiting",
    "IN_PROGRESS": "In progress",
    "QUALIFIED": "Qualified",
    "COMPLETED": "Completed",
    "EXPIRED": "Expired",
    "ACTION_NEEDED": "Action needed",
    "UNAVAILABLE": "Unavailable",
}

SAFE_TO_PRODUCT_STATUS: Final[dict[str, str]] = {
    "NOT_STARTED": "NOT_STARTED",
    "PENDING": "WAITING",
    "IN_PROGRESS": "IN_PROGRESS",
    "QUALIFIED": "QUALIFIED",
    "APPROVED": "WAITING",
    "FULFILLED": "COMPLETED",
    "SETTLED": "COMPLETED",
    "ADJUSTED": "ACTION_NEEDED",
    "DECLINED": "ACTION_NEEDED",
    "EXPIRED": "EXPIRED",
    "ACTION_REQUIRED": "ACTION_NEEDED",
    "UNAVAILABLE": "UNAVAILABLE",
}

REFERRAL_SAAS_SOURCE_STATUS_MAP: Final[dict[str, dict[str, str]]] = {
    "outcome": {
        "VALIDATED": "PENDING",
        "UCN_CAPTURED": "IN_PROGRESS",
        "ACCOUNT_OPENED": "IN_PROGRESS",
        "ACCOUNT_ACTIVATED": "IN_PROGRESS",
        "FUNDED": "QUALIFIED",
        "DEBIT_ORDER_SWITCHED": "QUALIFIED",
        "SALARY_SWITCHED": "QUALIFIED",
        "FIRST_TRANSACTION_COMPLETED": "QUALIFIED",
        "COMPLETED": "FULFILLED",
        "COMPLETE": "FULFILLED",
        "CANCELLED": "FAILED",
        "FAILED": "FAILED",
    },
    "progress": {
        "RECORDED": "IN_PROGRESS",
        "DEDUPED": "IN_PROGRESS",
        "QUEUED": "IN_PROGRESS",
        "FAILED_TO_QUEUE": "UNAVAILABLE",
        "FAILED": "UNAVAILABLE",
        "REJECTED": "FAILED",
    },
    "validation": {
        "VALIDATED": "PENDING",
        "REJECTED_TERMS_REQUIRED": "FAILED",
        "REJECTED_ALIAS": "FAILED",
        "REJECTED_CODE_NOT_FOUND": "UNAVAILABLE",
        "RECOVERY_REQUIRED_LOGGING": "FAILED",
        "RECOVERY_REQUIRED_IDENTITY_CAPTURE": "FAILED",
        "FAILED": "UNAVAILABLE",
    },
    "attribution": {
        "COMPLETE": "QUALIFIED",
        "PARTIAL": "IN_PROGRESS",
        "MISSING_EVIDENCE": "UNAVAILABLE",
        "INCONSISTENT": "FAILED",
        "UNAVAILABLE": "UNAVAILABLE",
    },
    "link_code": {
        "ISSUED": "PENDING",
        "ACTIVE": "PENDING",
        "LINKED": "IN_PROGRESS",
        "EXPIRED": "EXPIRED",
        "VOIDED": "FAILED",
        "INVALID": "UNAVAILABLE",
    },
}


def project_referral_saas_safe_status(
    *,
    viewer_role: str,
    subject: Mapping[str, Any],
    evidence: Mapping[str, Any],
    missing_evidence: Sequence[Mapping[str, Any]] | None = None,
    redactions: Sequence[str] | None = None,
) -> dict[str, Any]:
    family = str(
        evidence.get("source_family") or evidence.get("family") or "outcome"
    ).strip().lower()
    mapped_evidence = _map_evidence_status(family=family, evidence=evidence)

    projection = project_partner_customer_safe_status(
        viewer_role=viewer_role,
        subject=subject,
        evidence=mapped_evidence,
        source_family=_safe_source_family(family),
        missing_evidence=missing_evidence,
        redactions=redactions,
    )
    safe_status = projection["safe_status"]
    _apply_referral_saas_override(safe_status=safe_status, evidence=mapped_evidence)
    product_status = SAFE_TO_PRODUCT_STATUS.get(
        safe_status["status"],
        "UNAVAILABLE",
    )
    safe_status["product_status"] = product_status
    safe_status["product_label"] = PRODUCT_STATUS_LABELS[product_status]
    safe_status["product_summary"] = _product_summary(product_status)
    return projection


def _apply_referral_saas_override(
    *,
    safe_status: dict[str, Any],
    evidence: Mapping[str, Any],
) -> None:
    if evidence.get("status") != "EXPIRED":
        return
    safe_status["status"] = "EXPIRED"
    safe_status["label"] = "Expired"
    safe_status["summary"] = "Status is expired for this Referral SaaS view."
    safe_status["what_happened"] = "Referral SaaS evidence shows the window expired."
    safe_status["what_happens_next"] = "Use a current link or code if available."
    safe_status["action_required"] = False
    safe_status["action_category"] = "NONE"
    safe_status["terminal"] = True


def _safe_source_family(family: str) -> str:
    if family in {"progress", "validation", "attribution", "link_code"}:
        return "outcome"
    return family


def _map_evidence_status(*, family: str, evidence: Mapping[str, Any]) -> dict[str, Any]:
    mapped = dict(evidence)
    raw_status = str(
        evidence.get("status")
        or evidence.get("safe_status")
        or evidence.get("derived_state")
        or evidence.get("source_status")
        or ""
    ).strip().upper()
    mapped_status = REFERRAL_SAAS_SOURCE_STATUS_MAP.get(family, {}).get(raw_status)
    if mapped_status:
        mapped["status"] = mapped_status
    mapped["source_family"] = _safe_source_family(family)
    return mapped


def _product_summary(product_status: str) -> str:
    return {
        "NOT_STARTED": "The referral journey has not started.",
        "WAITING": "The platform is waiting for referral evidence.",
        "IN_PROGRESS": "The referral is in progress.",
        "QUALIFIED": "The referral has met a qualifying milestone.",
        "COMPLETED": "The referral journey is complete for this view.",
        "EXPIRED": "The referral or campaign window is no longer active.",
        "ACTION_NEEDED": "Support or the viewer needs to take action.",
        "UNAVAILABLE": "Status is not safely available yet.",
    }[product_status]
