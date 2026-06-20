"""Structured JSON logging helpers."""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional, Union


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        if hasattr(record, "extra") and isinstance(record.extra, dict):
            payload.update(record.extra)

        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str, level: Optional[Union[str, int]] = None) -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    resolved_level = level or os.environ.get("LOG_LEVEL", "INFO")
    logger.setLevel(resolved_level)

    return logger