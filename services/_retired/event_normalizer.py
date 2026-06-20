from __future__ import annotations

from typing import Any, Dict


EVENT_TYPE_MAPPING = {
    # source event -> internal normalized event
    "UCN_CREATED": "ACCOUNT_OPENED",
    "ACCOUNT_OPENED": "ACCOUNT_OPENED",
    "ACCOUNT_ACTIVATED": "ACCOUNT_ACTIVATED",
    "ACCOUNT_FUNDED": "FUNDED",
    "FUNDED": "FUNDED",
    "DEBIT_ORDER_SWITCHED": "DEBIT_ORDER_SWITCHED",
    "SALARY_SWITCHED": "SALARY_SWITCHED",
    "FIRST_TRANSACTION_COMPLETED": "FIRST_TRANSACTION_COMPLETED",
}


def normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    source_event_type = str(event.get("progressEventType") or event.get("eventType") or "").strip()
    normalized_event_type = EVENT_TYPE_MAPPING.get(source_event_type, source_event_type)

    normalized = dict(event)
    normalized["sourceEventType"] = source_event_type
    normalized["normalizedEventType"] = normalized_event_type

    return normalized