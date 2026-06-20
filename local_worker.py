from __future__ import annotations

import asyncio
import inspect
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

from apps.core.logging_utils import log_event
from services.journey_orchestrator import handle_referral_progress_recorded

LOCAL_QUEUE_FILE = os.environ.get("LOCAL_QUEUE_FILE", "local_events.jsonl")
LOCAL_QUEUE_POLL_SECONDS = float(os.environ.get("LOCAL_QUEUE_POLL_SECONDS", "1"))


def _read_events(queue_path: Path) -> List[Dict[str, Any]]:
    if not queue_path.exists():
        return []

    events: List[Dict[str, Any]] = []

    with queue_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    queue_path.write_text("", encoding="utf-8")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        try:
            event = json.loads(line)
            if isinstance(event, dict):
                events.append(event)
        except Exception as exc:
            log_event(
                level="ERROR",
                component="local_worker",
                message="LOCAL_EVENT_PARSE_FAILED",
                extra={"error": str(exc), "raw": line},
            )

    return events


def _process_event(event: Dict[str, Any]) -> None:
    tenant_code = event.get("tenantCode") or event.get("tenant_code")

    if not tenant_code:
        log_event(
            level="ERROR",
            component="local_worker",
            message="LOCAL_EVENT_MISSING_TENANT_CODE",
            extra={"eventType": event.get("eventType")},
        )
        return

    event_type = event.get("eventType")

    if event_type != "REFERRAL_PROGRESS_RECORDED":
        log_event(
            level="INFO",
            component="local_worker",
            message="LOCAL_EVENT_IGNORED_UNSUPPORTED_TYPE",
            extra={"eventType": event_type},
        )
        return

    result = handle_referral_progress_recorded(event, tenant_code=tenant_code)
    if inspect.isawaitable(result):
        asyncio.run(result)

    log_event(
        level="INFO",
        component="local_worker",
        message="LOCAL_EVENT_PROCESSED",
        extra={
            "eventType": event_type,
            "referralTrackId": event.get("referralTrackId"),
            "tenantCode": tenant_code,
        },
    )


def main() -> None:
    queue_path = Path(LOCAL_QUEUE_FILE)

    print(f"Local worker started. Reading from: {queue_path.resolve()}")

    while True:
        events = _read_events(queue_path)

        for event in events:
            try:
                _process_event(event)
            except Exception as exc:
                log_event(
                    level="ERROR",
                    component="local_worker",
                    message="LOCAL_EVENT_PROCESSING_FAILED",
                    extra={
                        "error": str(exc),
                        "eventType": event.get("eventType"),
                        "referralTrackId": event.get("referralTrackId"),
                    },
                )

        time.sleep(LOCAL_QUEUE_POLL_SECONDS)


if __name__ == "__main__":
    main()
