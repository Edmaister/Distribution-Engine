# services/policy_service.py

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


def _key(
    tenant: Optional[str],
    sticker: Optional[str],
    segment: Optional[str],
    campaign_code: Optional[str],
    campaign_id: Optional[str],
) -> str:
    return "::".join([
        (tenant or "").upper(),
        (sticker or "").upper(),
        segment or "",
        campaign_code or "",
        campaign_id or "",
    ])


def _now() -> float:
    return time.time()


def _row_to_policy(row) -> Dict[str, Any]:
    rolling, rules_text, win_text, ra_text, pr_text, version = row

    try:
        rules = json.loads(rules_text) if rules_text else DEFAULT_RULES
    except Exception:
        rules = DEFAULT_RULES

    try:
        product_windows = json.loads(win_text) if win_text else {}
    except Exception:
        product_windows = {}

    try:
        reward_amounts = json.loads(ra_text) if ra_text else {}
    except Exception:
        reward_amounts = {}

    try:
        product_rules = json.loads(pr_text) if pr_text else {}
    except Exception:
        product_rules = {}

    return {
        "enabled": ENABLE_COOLDOWNS,
        "dryRun": DRY_RUN,
        "rollingWindowDays": int(rolling or DEFAULT_ROLLING_WINDOW_DAYS),
        "rules": rules,
        "productWindows": product_windows,
        "rewardAmounts": reward_amounts,
        "productRules": product_rules,
        "version": int(version or 1),
    }


def get_effective_policy(
    *,
    tenant: Optional[str],
    sticker: Optional[str],
    segment: Optional[str],
    campaign_code: Optional[str],
    campaign_id: Optional[str],
) -> Dict[str, Any]:
    key = _key(tenant, sticker, segment, campaign_code, campaign_id)

    if key in _cache and _cache_expiry.get(key, 0) > _now():
        return _cache[key]

    policy = None

    # 1) Campaign override by campaign_code
    if campaign_code:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT rolling_window_days,
                       COALESCE(rules, rules_json)::text AS rules_text,
                       product_windows_json::text,
                       reward_amounts_json::text,
                       product_rules_json::text,
                       COALESCE(version, 1)
                FROM marketing_campaign_policies
                WHERE is_active = TRUE
                  AND UPPER(campaign_code) = UPPER(%s)
                  AND (tenant_code = %s OR %s IS NULL)
                ORDER BY updated_at DESC, version DESC
                LIMIT 1
                """,
                (campaign_code, tenant, tenant),
            )
            row = cur.fetchone()
            if row:
                policy = _row_to_policy(row)

    # 2) Sticker-level policy
    if not policy:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT rolling_window_days,
                       COALESCE(rules, rules_json)::text AS rules_text,
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

    # 3) Fallback segment/campaign_id
    if not policy:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT rolling_window_days,
                       COALESCE(rules, rules_json)::text AS rules_text,
                       product_windows_json::text,
                       reward_amounts_json::text,
                       product_rules_json::text,
                       COALESCE(version, 1)
                FROM cooldown_policies
                WHERE is_active = TRUE
                  AND (segment = %s OR %s IS NULL OR segment IS NULL)
                  AND (campaign_id = %s OR %s IS NULL OR campaign_id IS NULL)
                  AND (tenant_code = %s OR %s IS NULL)
                ORDER BY campaign_id NULLS FIRST, segment NULLS FIRST, updated_at DESC, version DESC
                LIMIT 1
                """,
                (segment, segment, campaign_id, campaign_id, tenant, tenant),
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