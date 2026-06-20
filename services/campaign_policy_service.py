from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

from utils.db import db_connection

try:
    from config.cooldown import (
        ENABLE_COOLDOWNS,
        DRY_RUN,
        DEFAULT_ROLLING_WINDOW_DAYS,
        DEFAULT_RULES,
        POLICY_CACHE_TTL_SEC,
    )
except Exception:
    ENABLE_COOLDOWNS = True
    DRY_RUN = False
    DEFAULT_ROLLING_WINDOW_DAYS = 60
    DEFAULT_RULES = []
    POLICY_CACHE_TTL_SEC = 60


_cache: Dict[str, Dict[str, Any]] = {}
_cache_expiry: Dict[str, float] = {}


def _norm(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    t = s.strip().upper()
    return t or None


def _key(tenant: Optional[str], campaign_code: Optional[str]) -> str:
    return "::".join([_norm(tenant) or "", _norm(campaign_code) or ""])


def _now() -> float:
    return time.time()


def _json_load_or(default: Any, text: Optional[str]) -> Any:
    if not text:
        return default
    try:
        return json.loads(text)
    except Exception:
        return default


def _row_get(row: Any, key_or_index: Any, default: Any = None) -> Any:
    try:
        return row[key_or_index]
    except Exception:
        return default


def _row_to_policy(row: Any) -> Dict[str, Any]:
    rolling = _row_get(row, "rolling_window_days", _row_get(row, 0))
    rules_text = _row_get(row, "rules_text", _row_get(row, 1))
    win_text = _row_get(row, "product_windows_text", _row_get(row, 2))
    ra_text = _row_get(row, "reward_amounts_text", _row_get(row, 3))
    pr_text = _row_get(row, "product_rules_text", _row_get(row, 4))
    version = _row_get(row, "version", _row_get(row, 5))

    return {
        "enabled": ENABLE_COOLDOWNS,
        "dryRun": DRY_RUN,
        "rollingWindowDays": int(rolling or DEFAULT_ROLLING_WINDOW_DAYS),
        "rules": _json_load_or(DEFAULT_RULES, rules_text),
        "productWindows": _json_load_or({}, win_text),
        "rewardAmounts": _json_load_or({}, ra_text),
        "productRules": _json_load_or({}, pr_text),
        "version": int(version or 1),
    }


def _default_policy() -> Dict[str, Any]:
    return {
        "enabled": ENABLE_COOLDOWNS,
        "dryRun": DRY_RUN,
        "rollingWindowDays": DEFAULT_ROLLING_WINDOW_DAYS,
        "rules": DEFAULT_RULES,
        "productWindows": {},
        "rewardAmounts": {},
        "productRules": {},
        "version": 1,
    }


async def get_effective_policy(
    *,
    tenant: Optional[str] = None,
    campaign_code: Optional[str] = None,
) -> Dict[str, Any]:
    tenant_n = _norm(tenant)
    code_n = _norm(campaign_code)

    key = _key(tenant_n, code_n)

    if key in _cache and _cache_expiry.get(key, 0) > _now():
        return _cache[key]

    policy: Optional[Dict[str, Any]] = None

    if code_n:
        async with db_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    rolling_window_days,
                    COALESCE(rules_json, '[]'::jsonb)::text AS rules_text,
                    COALESCE(product_windows_json, '{}'::jsonb)::text AS product_windows_text,
                    COALESCE(reward_amounts_json, '{}'::jsonb)::text AS reward_amounts_text,
                    COALESCE(product_rules_json, '{}'::jsonb)::text AS product_rules_text,
                    COALESCE(version, 1) AS version
                FROM marketing_campaign_policies
                WHERE is_active = TRUE
                  AND UPPER(campaign_code) = UPPER($1)
                  AND (
                        tenant_code IS NULL
                        OR UPPER(tenant_code) = UPPER($2)
                      )
                ORDER BY (tenant_code IS NOT NULL) DESC,
                         updated_at DESC,
                         version DESC
                LIMIT 1
                """,
                code_n,
                tenant_n or "",
            )

        if row:
            policy = _row_to_policy(row)

    if not policy:
        policy = _default_policy()

    _cache[key] = policy
    _cache_expiry[key] = _now() + POLICY_CACHE_TTL_SEC

    return policy