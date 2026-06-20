# Recommendations Optimization (Caching & Insights)

This document explains how recommendations and campaign insights are **precomputed and cached**.

---

## Why caching?
- **Performance**: Avoid expensive joins in real-time APIs.
- **Consistency**: Users and admins see stable, daily-updated data.
- **Scalability**: Heavy workloads are shifted to batch jobs.

---

## Caches

### recommendations_cache
- **Key**: `referrer_hash`
- **Value**: JSON array of recommendation cards
- **Fields**:
  - `items` (recommendation cards)
  - `generated_at`
  - `ttl_seconds` (default: 86,400 = 1 day)
- **Usage**: Read by `/me/recommendations` endpoint.

### campaign_insights_cache
- **Key**: `campaign_code`
- **Value**: JSON metrics object
- **Fields**:
  - `rewards_30d`, `referrals_30d`, `conversion`
  - `generated_at`, `ttl_seconds`
- **Usage**: Read by `/admin/recommendations/campaigns/{code}` endpoint.

---

## Nightly Refresh Job
A worker (`recommendation_refresher.py`) runs once daily:

1. Query all active users and campaigns.
2. Generate fresh recommendations per referrer → upsert into `recommendations_cache`.
3. Compute campaign conversion KPIs (30-day) → upsert into `campaign_insights_cache`.

---

## Admin API
- **Endpoint**: `GET /admin/recommendations/campaigns/{code}?prefer_cache=true`  
- **Returns**: Conversion KPIs and metadata.  
- **Purpose**: Marketing/Ops can see effectiveness without long queries.

---

## Benefits
- **Users**: Fast-loading, engaging dashboard.
- **Admins**: Instant insights on campaign ROI.
- **Bank**: Optimized infra usage and lower DB strain.
