# services/referral_policy_service.py

import json
import time
from typing import Any, Dict, Optional

from utils.db import db_cursor


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
    DEFAULT_RULES = [
        {"action": "WARN", "minActivations": 5, "qrBelow": 0.40},
        {
            "action": "SOFT",
            "minActivations": 8,
            "qrBelow": 0.30,
            "durationDays": 14,
            "caps": {"dailyReferrals": 2, "rewardTier": "activation-only"},
        },
        {"action": "HARD", "minActivations": 12, "qrBelow": 0.20, "durationDays": 30},
    ]
    POLICY_CACHE_TTL_SEC = 60


_cache: Dict[str, Dict[str, Any]] = {}
_cache_expiry: Dict[str, float] = {}


def _key(tenant: Optional[str], sticker: Optional[str], segment: Optional[str]) -> str:
    return "::".join([(tenant or "").upper(), (sticker or "").upper(), segment or ""])


def _now() -> float:
    return time.time()


def _safe_json(text, default):
    try:
        return json.loads(text) if text else default
    except Exception:
        return default


def _row_to_policy(row) -> Dict[str, Any]:
    rolling, rules_text, win_text, ra_text, pr_text, version = row

    return {
        "enabled": ENABLE_COOLDOWNS,
        "dryRun": DRY_RUN,
        "rollingWindowDays": int(rolling or DEFAULT_ROLLING_WINDOW_DAYS),
        "rules": _safe_json(rules_text, DEFAULT_RULES),
        "productWindows": _safe_json(win_text, {}),
        "rewardAmounts": _safe_json(ra_text, {}),
        "productRules": _safe_json(pr_text, {}),
        "version": int(version or 1),
    }


def get_effective_policy(
    *,
    tenant: Optional[str] = None,
    sticker: Optional[str] = None,
    segment: Optional[str] = None,
) -> Dict[str, Any]:

    key = _key(tenant, sticker, segment)

    if key in _cache and _cache_expiry.get(key, 0) > _now():
        return _cache[key]

    policy: Optional[Dict[str, Any]] = None

    # 🔥 SINGLE DB CONTEXT (FIXED)
    with db_cursor() as cur:

        # 1) Sticker-level
        cur.execute(
            """
            SELECT rolling_window_days,
                   COALESCE(rules, rules_json)::text,
                   product_windows_json::text,
                   reward_amounts_json::text,
                   product_rules_json::text,
                   COALESCE(version, 1)
            FROM cooldown_policies
            WHERE is_active = TRUE
              AND UPPER(COALESCE(sticker, '')) = UPPER(COALESCE(%s, ''))
              AND (tenant_code = %s OR %s IS NULL)
            ORDER BY updated_at DESC, version DESC
            LIMIT 1
            """,
            (sticker, tenant, tenant),
        )

        row = cur.fetchone()
        if row:
            policy = _row_to_policy(row)

        # 2) Segment fallback
        if not policy:
            cur.execute(
                """
                SELECT rolling_window_days,
                       COALESCE(rules, rules_json)::text,
                       product_windows_json::text,
                       reward_amounts_json::text,
                       product_rules_json::text,
                       COALESCE(version, 1)
                FROM cooldown_policies
                WHERE is_active = TRUE
                  AND (segment = %s OR %s IS NULL OR segment IS NULL)
                  AND campaign_id IS NULL
                  AND (tenant_code = %s OR %s IS NULL)
                ORDER BY segment NULLS FIRST, updated_at DESC, version DESC
                LIMIT 1
                """,
                (segment, segment, tenant, tenant),
            )

            row = cur.fetchone()
            if row:
                policy = _row_to_policy(row)

    if not policy:
        policy = {
            "enabled": ENABLE_COOLDOWNS,
            "dryRun": DRY_RUN,
            "rollingWindowDays": DEFAULT_ROLLING_WINDOW_DAYS,
            "rules": DEFAULT_RULES,
            "productWindows": {},
            "rewardAmounts": {},
            "productRules": {},
            "version": 1,
        }

    _cache[key] = policy
    _cache_expiry[key] = _now() + POLICY_CACHE_TTL_SEC

    return policy