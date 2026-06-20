-- 007_recommendation_views.sql
-- Referral-focused materialized views for recommendation service

-- -----------------------------------------------------------------------------
-- 1) Best hour to engage a referrer
-- -----------------------------------------------------------------------------
-- Purpose:
-- Helps determine when a referrer typically generates referrals
-- Used for SEND_INVITE optimisation in recommendation service

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_referrer_best_hour AS
SELECT
    rc.referrer_ucn_hash AS referrer_hash,
    EXTRACT(HOUR FROM ri.created_at)::int AS hour_of_day,
    COUNT(*) AS cnt
FROM referral_instances ri
JOIN referrer_codes rc
  ON rc.referrer_code_id = ri.referrer_code_id
GROUP BY 1, 2;

-- Required for CONCURRENT refresh
CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_referrer_best_hour_hash_hour
    ON mv_referrer_best_hour (referrer_hash, hour_of_day);

CREATE INDEX IF NOT EXISTS idx_mv_referrer_best_hour_hour
    ON mv_referrer_best_hour (hour_of_day);


-- -----------------------------------------------------------------------------
-- 2) (Optional) Referrer activity summary
-- -----------------------------------------------------------------------------
-- Purpose:
-- Lightweight aggregation for future recommendation expansion
-- (momentum scoring, streaks, power users)

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_referrer_activity_30d AS
SELECT
    rc.referrer_ucn_hash AS referrer_hash,
    COUNT(*) AS referrals_30d,
    MAX(ri.created_at) AS last_referral_at
FROM referral_instances ri
JOIN referrer_codes rc
  ON rc.referrer_code_id = ri.referrer_code_id
WHERE ri.created_at >= NOW() - INTERVAL '30 days'
GROUP BY 1;

CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_referrer_activity_30d_hash
    ON mv_referrer_activity_30d (referrer_hash);


-- -----------------------------------------------------------------------------
-- Refresh examples
-- -----------------------------------------------------------------------------
-- Use CONCURRENTLY in production to avoid locks

-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_referrer_best_hour;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_referrer_activity_30d;