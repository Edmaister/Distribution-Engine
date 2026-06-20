import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Optional

LOGGER_NAME = "referral-platform"


def _resolve_log_level(default: int = logging.INFO) -> int:
    raw = os.environ.get("LOG_LEVEL", "").upper().strip()
    if not raw:
        return default
    return getattr(logging, raw, default)


def configure_logging(level: Optional[int] = None) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)

    if logger.handlers:
        return logger

    resolved_level = level if level is not None else _resolve_log_level()
    logger.setLevel(resolved_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(resolved_level)
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = configure_logging()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(
    *,
    level: str,
    component: str,
    message: str,
    correlation_id: Optional[str] = None,
    referral_track_id: Optional[str] = None,
    source_event_id: Optional[str] = None,
    source_system: Optional[str] = None,
    event_type: Optional[str] = None,
    status_before: Optional[str] = None,
    status_after: Optional[str] = None,
    decision: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> None:
    payload = {
        "timestamp": _utc_now(),
        "level": level.upper(),
        "service": LOGGER_NAME,
        "component": component,
        "message": message,
        "correlation_id": correlation_id or referral_track_id,
        "referral_track_id": referral_track_id,
        "source_event_id": source_event_id,
        "source_system": source_system,
        "event_type": event_type,
        "status_before": status_before,
        "status_after": status_after,
        "decision": decision,
    }

    if extra:
        for key, value in extra.items():
            if key not in payload:
                payload[key] = value
            else:
                payload[f"extra_{key}"] = value

    cleaned = {k: v for k, v in payload.items() if v is not None}
    line = json.dumps(cleaned, default=str)

    if level.upper() == "DEBUG":
        logger.debug(line)
    elif level.upper() == "WARNING":
        logger.warning(line)
    elif level.upper() == "ERROR":
        logger.error(line)
    else:
        logger.info(line)