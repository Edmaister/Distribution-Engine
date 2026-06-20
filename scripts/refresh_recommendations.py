import argparse
from utils.db import get_connection
from utils.logging import get_logger
from services.recommendation_service import (
    recommend_for_referrer,
    upsert_recommendations_cache,
    compute_campaign_insights,
    upsert_campaign_insights_cache,
)

logger = get_logger(__name__)

def active_referrers(limit: int = 5000):
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("""
            SELECT DISTINCT referrer_ucn_encrypted
              FROM referrals
             WHERE created_at >= NOW() - INTERVAL '60 days'
             ORDER BY 1 DESC
             LIMIT %s
        """, (limit,))
        return [r[0] for r in cur.fetchall()]
    finally:
        cur.close(); conn.close()

def active_campaigns(limit: int = 1000):
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("""
            SELECT campaign_code, sticker, tenant_code
              FROM marketing_campaigns
             WHERE is_active = TRUE
             ORDER BY created_at DESC
             LIMIT %s
        """, (limit,))
        return [(r[0], r[1], r[2]) for r in cur.fetchall()]
    finally:
        cur.close(); conn.close()

def main():
    ap = argparse.ArgumentParser(description="Refresh recommendation caches")
    ap.add_argument("--sticker", default="PREMIER", help="Default sticker for NBA computation")
    ap.add_argument("--tenant", default=None, help="Default tenant code")
    ap.add_argument("--top-k", type=int, default=3)
    args = ap.parse_args()

    # User-level recos
    for ref_hash in active_referrers():
        items = recommend_for_referrer(ref_hash, args.sticker, args.tenant, args.top_k)
        upsert_recommendations_cache(ref_hash, items, ttl_seconds=86400)
        logger.info("Updated recommendations_cache for user=%s with %d items", ref_hash, len(items))

    # Campaign insights
    for code, sticker, tenant in active_campaigns():
        entry = compute_campaign_insights(code, sticker=sticker, tenant=tenant)
        upsert_campaign_insights_cache(entry, ttl_seconds=86400)
        logger.info("Updated campaign_insights_cache for campaign=%s", code)

if __name__ == "__main__":
    main()
