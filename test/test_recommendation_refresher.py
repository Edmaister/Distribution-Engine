"""Nightly job to refresh recommendation caches for active referrers,
and to compute admin campaign insights for active campaigns.
Schedule via cron or K8s CronJob once per night.
"""

from __future__ import annotations

from utils.db import get_async_connection
from services.recommendation_service import (
    recommend_for_referrer,
    upsert_recommendations_cache,
    compute_campaign_insights,
)


async def _active_referrers(limit: int = 5000) -> list[str]:
    async with get_async_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT referrer_ucn_encrypted
              FROM referrals
             WHERE created_at >= NOW() - INTERVAL '60 days'
             ORDER BY 1 DESC
             LIMIT $1
            """,
            limit,
        )

    return [row["referrer_ucn_encrypted"] for row in rows]


async def _active_campaigns(limit: int = 1000) -> list[tuple[str, str | None, str | None]]:
    async with get_async_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT campaign_code, sticker, tenant_code
              FROM marketing_campaigns
             WHERE is_active = TRUE
             ORDER BY created_at DESC
             LIMIT $1
            """,
            limit,
        )

    return [
        (row["campaign_code"], row["sticker"], row["tenant_code"])
        for row in rows
    ]


async def run_once(
    default_sticker: str = "PREMIER",
    default_tenant: str | None = None,
    top_k: int = 3,
):
    for ref_hash in await _active_referrers():
        items = await recommend_for_referrer(
            ref_hash,
            default_sticker,
            default_tenant,
            top_k,
        )
        await upsert_recommendations_cache(
            ref_hash,
            items,
            ttl_seconds=86400,
        )

    for code, sticker, tenant in await _active_campaigns():
        await compute_campaign_insights(
            code,
            sticker=sticker,
            tenant=tenant,
        )