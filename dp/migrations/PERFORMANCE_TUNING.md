# Performance Tuning (Partitions + Materialized Views)

See migrations `010_partitioning.sql` and `011_materialized_views.sql`.

## Partitions
- New partitioned parents: `enterprise_events_p`, `referral_qr_scans_p`
- Views: `enterprise_events_v`, `referral_qr_scans_v`
- Helpers: `ensure_enterprise_events_partition(y,m)`, `ensure_qr_scans_partition(y,m)`
- Steps:
  1. Backfill from legacy tables.
  2. Switch writers to partitioned parents or views.
  3. Drop old tables after verification.

## Materialized Views
- `mv_campaign_conversion_30d`: quick campaign KPIs.
- `mv_referrer_best_hour`: per-user hour histogram.

### Refresh (cron)
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_campaign_conversion_30d;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_referrer_best_hour;
```
