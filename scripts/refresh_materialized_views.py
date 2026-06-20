from utils.db import get_connection
from utils.logging import get_logger

logger = get_logger(__name__)

def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            logger.info("Refreshing mv_campaign_conversion_30d (if exists)")
            cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_campaign_conversion_30d;")
            logger.info("Refreshing mv_referrer_best_hour (if exists)")
            cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_referrer_best_hour;")
        conn.commit()
        logger.info("Materialized views refreshed.")
    except Exception as e:
        logger.warning("Refresh failed (views may not exist yet): %s", e)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
