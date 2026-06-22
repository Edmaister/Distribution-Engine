from __future__ import annotations

from typing import Literal

SafeStatusSurface = Literal["operator", "external"]
SafeStatusDomain = Literal["fulfilment", "settlement"]


_FULFILMENT_OPERATOR = {
    "PENDING": ("PENDING", "Pending", "Fulfilment is waiting to start.", False, False),
    "PROCESSING": (
        "IN_PROGRESS",
        "Processing",
        "Fulfilment is currently being processed.",
        False,
        False,
    ),
    "SUCCESS": (
        "FULFILLED",
        "Fulfilled",
        "Fulfilment completed successfully.",
        False,
        True,
    ),
    "FAILED_RETRYABLE": (
        "RETRYABLE_FAILURE",
        "Retryable failure",
        "Fulfilment failed and can be retried.",
        True,
        False,
    ),
    "FAILED_FINAL": (
        "FAILED",
        "Failed",
        "Fulfilment reached a final failure state.",
        True,
        True,
    ),
    "DLQ": (
        "ACTION_REQUIRED",
        "Action required",
        "Fulfilment is in a dead-letter state and needs operator review.",
        True,
        False,
    ),
    "SKIPPED_DUPLICATE": (
        "DUPLICATE_NOOP",
        "Duplicate skipped",
        "Duplicate fulfilment evidence was skipped without a new action.",
        False,
        True,
    ),
}

_FULFILMENT_EXTERNAL = {
    "PENDING": ("PENDING", "Pending", "Fulfilment is waiting to start.", False, False),
    "PROCESSING": (
        "IN_PROGRESS",
        "In progress",
        "Fulfilment is in progress.",
        False,
        False,
    ),
    "SUCCESS": ("FULFILLED", "Fulfilled", "Fulfilment is complete.", False, True),
    "FAILED_RETRYABLE": (
        "IN_PROGRESS",
        "In progress",
        "Fulfilment is still being processed.",
        False,
        False,
    ),
    "FAILED_FINAL": (
        "ACTION_REQUIRED",
        "Action required",
        "Fulfilment needs support review.",
        True,
        True,
    ),
    "DLQ": (
        "ACTION_REQUIRED",
        "Action required",
        "Fulfilment needs support review.",
        True,
        False,
    ),
    "SKIPPED_DUPLICATE": (
        "FULFILLED",
        "Fulfilled",
        "Fulfilment is complete.",
        False,
        True,
    ),
}

_SETTLEMENT_OPERATOR = {
    "PENDING": ("PENDING", "Pending", "Settlement is waiting to start.", False, False),
    "PROCESSING": (
        "IN_PROGRESS",
        "Processing",
        "Settlement is currently being processed.",
        False,
        False,
    ),
    "SETTLED": (
        "SETTLED",
        "Settled",
        "Settlement completed successfully.",
        False,
        True,
    ),
    "FAILED": (
        "FAILED",
        "Failed",
        "Settlement failed and needs operator review.",
        True,
        True,
    ),
    "REVERSED": (
        "REVERSED",
        "Reversed",
        "Settlement was reversed.",
        True,
        True,
    ),
    "DISPUTED": (
        "DISPUTED",
        "Disputed",
        "Settlement has an active dispute or exception.",
        True,
        False,
    ),
}

_SETTLEMENT_EXTERNAL = {
    "PENDING": ("PENDING", "Pending", "Settlement is waiting to start.", False, False),
    "PROCESSING": (
        "IN_PROGRESS",
        "In progress",
        "Settlement is in progress.",
        False,
        False,
    ),
    "SETTLED": ("SETTLED", "Settled", "Settlement is complete.", False, True),
    "FAILED": (
        "ACTION_REQUIRED",
        "Action required",
        "Settlement needs support review.",
        True,
        True,
    ),
    "REVERSED": (
        "ADJUSTED",
        "Adjusted",
        "Settlement has been adjusted.",
        False,
        True,
    ),
    "DISPUTED": (
        "ACTION_REQUIRED",
        "Action required",
        "Settlement needs support review.",
        True,
        False,
    ),
}


def _normalise_status(status: object) -> str:
    return str(status or "").strip().upper()


def _safe_status(
    *,
    domain: SafeStatusDomain,
    raw_status: object,
    surface: SafeStatusSurface,
    mapping: dict[str, tuple[str, str, str, bool, bool]],
) -> dict[str, object]:
    normalised = _normalise_status(raw_status)
    mapped = mapping.get(normalised)

    if mapped is None:
        result = {
            "domain": domain,
            "surface": surface,
            "status": "UNKNOWN" if surface == "operator" else "UNAVAILABLE",
            "label": "Unknown" if surface == "operator" else "Unavailable",
            "description": (
                "Source status is not mapped yet."
                if surface == "operator"
                else "Status is not currently available."
            ),
            "action_required": surface == "operator",
            "terminal": False,
        }
    else:
        status, label, description, action_required, terminal = mapped
        result = {
            "domain": domain,
            "surface": surface,
            "status": status,
            "label": label,
            "description": description,
            "action_required": action_required,
            "terminal": terminal,
        }

    if surface == "operator":
        result["source_status"] = normalised or "UNKNOWN"
        result["detail_code"] = normalised or "UNKNOWN"

    return result


def map_fulfilment_status(
    status: object,
    *,
    surface: SafeStatusSurface = "operator",
) -> dict[str, object]:
    mapping = _FULFILMENT_OPERATOR if surface == "operator" else _FULFILMENT_EXTERNAL
    return _safe_status(
        domain="fulfilment",
        raw_status=status,
        surface=surface,
        mapping=mapping,
    )


def map_settlement_status(
    status: object,
    *,
    surface: SafeStatusSurface = "operator",
) -> dict[str, object]:
    mapping = _SETTLEMENT_OPERATOR if surface == "operator" else _SETTLEMENT_EXTERNAL
    return _safe_status(
        domain="settlement",
        raw_status=status,
        surface=surface,
        mapping=mapping,
    )
