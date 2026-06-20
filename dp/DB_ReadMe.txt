# README — `db/` (Schema & Seeds) for the Referrals Platform

This document explains **what each SQL file does**, **how they fit together**, and **how the database supports the broader architecture** (white-label tenancy, stickers, campaigns, eligibility, rewards, gamification, IDS events, and optimization/recommendations). It’s written for a **Systems Analyst (SA)**.

---

## 0) Big picture: where `db/` fits

The platform is data-driven. Policies, campaigns, and events are **stored in the DB** so the services can make decisions **without redeploying code**:

* **White-label**: `tenant_code` scopes behavior per brand.
* **Sticker tiers**: Easy, Aspire, Premier, Private Clients, Private Wealth, RMB Private Banking.
* **Campaigns**: `marketing_campaigns` with **campaign policy overrides**.
* **Eligibility**: Declarative **JSON rules** and **amounts** resolved at runtime.
* **Rewards**: Idempotent writes (`referral_rewards`) with campaign attribution.
* **Gamification**: Missions, badges, points/progress for engagement.
* **IDS events**: `enterprise_events` captures Hogan/enterprise streams that drive eligibility.
* **Optimization**: Recommendation & insights caches for fast UX and marketing visibility.
* **Abuse control**: `referral_qr_scans` prevents device reuse.

---

## 1) Folder structure

```
db/
├─ migrations/
│  ├─ 001_init.sql
│  ├─ 002_campaigns.sql
│  ├─ 003_policies.sql
│  ├─ 004_enterprise_events.sql
│  ├─ 005_gamification.sql
│  ├─ 006_qr_scans.sql
│  ├─ 007_recommendations_cache.sql
│  └─ 999_indexes.sql
├─ seeds/
│  ├─ seed_policies_and_campaigns.sql
│  └─ sample_missions_badges.sql
└─ README.md (this file)
```

### Migration order (why this order?)

* `001_init.sql` — base **referrals** and **referral\_rewards** tables used by almost everything else.
* `002_campaigns.sql` — campaigns and **campaign policy overrides** that can supersede defaults.
* `003_policies.sql` — sticker-level default policies.
* `004_enterprise_events.sql` — events from Hogan IDS and other systems, later used for eligibility.
* `005_gamification.sql` — missions, badges, user progress.
* `006_qr_scans.sql` — anti-abuse telemetry for QR scans & device reuse control.
* `007_recommendations_cache.sql` — optional caches to speed up UX/insights.
* `999_indexes.sql` — cross-cutting indexes once objects exist.

---

## 2) Tables (what they store & how they’re used)

### 2.1 Referrals & Rewards (001\_init.sql)

* **`referrals`**

  * `referral_track_id` (UUID PK): the stable join key across events/rewards.
  * `referral_code`: user-facing code (unique).
  * `referrer_ucn_encrypted` / `referee_ucn_encrypted`: opaque identifiers (no raw PII).
  * `sticker`, `tenant_code`, `campaign_code`: attribution for white-label, tier, and campaign.
  * Used by: referral issuance/validation, reward application, progress, recommendations.

* **`referral_rewards`**

  * One row per **(referral\_track\_id, reward\_type)** (idempotency via unique constraint).
  * `product`, `amount`, `campaign_code`, `tenant_code`.
  * Emitted as `REWARD_APPLIED` for analytics/gamification.

**Why it matters**: These two tables form the **core ledger** of referrals and payouts.

---

### 2.2 Campaigns & Campaign Policies (002\_campaigns.sql)

* **`marketing_campaigns`**

  * Campaign lifecycle and metadata (`is_active`, dates, attributes).
  * Scopes: `sticker`, `tenant_code`.

* **`marketing_campaign_policies`**

  * Per-campaign overrides for:

    * `reward_amounts_json` (how much to pay per product/reward type)
    * `product_rules_json` (eligibility rules; e.g., “Insurance Activation requires 1 `POLICY_ACTIVATED` in 30 days”)

**Why it matters**: A campaign can **temporarily override** sticker defaults **without redeploys**, enabling marketing agility.

---

### 2.3 Sticker-level Default Policies (003\_policies.sql)

* **`cooldown_policies`**

  * Default **reward amounts** & **eligibility rules** per `sticker` (and optional `tenant_code`).
  * Campaigns can override these values when active.

**Why it matters**: This is your **baseline behavior**; campaigns layer on top.

---

### 2.4 Enterprise Events (004\_enterprise\_events.sql)

* **`enterprise_events`**

  * Ingested from Hogan IDS (or other sources): e.g., `POLICY_ACTIVATED`, `ACCOUNT_ACTIVATED`, `DEBIT_ORDER_SWITCHED`, `SALARY_DEPOSIT`.
  * Joined by `referral_track_id`; `occurred_at` & `attributes` carry evidence for eligibility.

**Why it matters**: Eligibility is evidence-driven; events are the **source of truth** for actions the referee performed.

---

### 2.5 Gamification (005\_gamification.sql)

* **`missions`, `user_mission_progress`**

  * Missions like `INVITE_5` or `EARN_3_REWARDS`. Progress increments on events (referrals created, rewards applied).

* **`badges`, `user_badges`**

  * One-time achievements for milestones (e.g., first referral).

**Why it matters**: Keeps users engaged and provides **inputs into recommendations**.

---

### 2.6 QR Scans / Anti-abuse (006\_qr\_scans.sql)

* **`referral_qr_scans`**

  * Tracks scans with `status` (`SCANNED` → `COMPLETED` → (optional) `BLOCKED`).
  * Device/IP signals help **detect UCN farming / device reuse**.

**Why it matters**: Protects against abuse before onboarding and before rewards are attempted.

---

### 2.7 Optimization caches (007\_recommendations\_cache.sql)

* **`recommendations_cache`**

  * Stores precomputed “Next-Best-Action” cards per user (24h TTL by default).

* **`campaign_insights_cache`**

  * Stores recent 30-day conversion metrics (rewards/referrals) per campaign for fast admin insights.

**Why it matters**: Enables **fast UX** for recommendations and **quick marketing visibility** without heavy live aggregation.

---

### 2.8 Cross-cutting Indexes (999\_indexes.sql)

* Indexes to keep common lookups fast:

  * Referrals by referrer (`referrer_ucn_encrypted`)
  * Campaign filters on referrals & rewards
  * Events by `referral_track_id`

---

## 3) JSON policy shapes (how services read them)

### `reward_amounts_json` (per product → reward\_type → amount)

```json
{
  "BANKING":   { "ACTIVATION": 60, "DEBIT_ORDER": 35, "SALARY": 45 },
  "INSURANCE": { "ACTIVATION": 150 }
}
```

### `product_rules_json` (per product → reward\_type → list of rules)

Example for Insurance Activation requiring an event within 30 days:

```json
{
  "INSURANCE": {
    "ACTIVATION": [
      { "kind": "event_count", "eventTypes": ["POLICY_ACTIVATED"], "atLeast": 1, "windowDays": 30 }
    ]
  }
}
```

> Services resolve **effective policy** as:
> **campaign override** (if `campaign_code` in context and active) → **sticker defaults** → fallback.

---

## 4) How services use these tables (end-to-end flows)

1. **Issue referral** (`referral_code.py`)

   * Writes to `referrals` with `referral_code`, `referrer_ucn_encrypted`, `sticker`, `tenant_code`, optional `campaign_code`.

2. **Validate scan** (`validate_referral.py`)

   * Inserts into `referral_qr_scans` with `SCANNED`; blocks further actions if device previously `COMPLETED` for same referral.
   * Emits `REFERRAL_CODE_PENDING`.

3. **Capture UCN** (`update_ucn.py`)

   * Sets `referee_ucn_encrypted` (idempotent).
   * Emits `REFEREE_UCN_CAPTURED` (hash only; no raw UCN).

4. **Ingest events** (`apps/workers/ids_consumer.py`)

   * Inserts evidence into `enterprise_events`.

5. **Apply reward** (`reward_service.py`)

   * Reads **effective policy** (campaign override → sticker defaults).
   * Checks policy **rules** against `enterprise_events` (and cooldowns).
   * Upserts into `referral_rewards` (unique constraint enforces idempotency).
   * Emits `REWARD_APPLIED`.

6. **Gamification** (`gamification_service.py`)

   * Updates `user_mission_progress`, `user_badges` on `REFERRAL_CODE_ISSUED` / `REWARD_APPLIED`.

7. **Optimization** (`recommendation_service.py`, nightly refresher)

   * Reads referrals/rewards/missions/events; writes recommendation cards to `recommendations_cache`.
   * Computes 30-day conversion proxy and writes to `campaign_insights_cache`.

---

## 5) Applying migrations & seeds

### Environment variable

* `APP_DB_DSN`: e.g., `postgresql://user:pass@localhost:5432/referrals`

### Apply in order

```bash
psql $APP_DB_DSN -f db/migrations/001_init.sql
psql $APP_DB_DSN -f db/migrations/002_campaigns.sql
psql $APP_DB_DSN -f db/migrations/003_policies.sql
psql $APP_DB_DSN -f db/migrations/004_enterprise_events.sql
psql $APP_DB_DSN -f db/migrations/005_gamification.sql
psql $APP_DB_DSN -f db/migrations/006_qr_scans.sql
psql $APP_DB_DSN -f db/migrations/007_recommendations_cache.sql
psql $APP_DB_DSN -f db/migrations/999_indexes.sql
```

### Seed baseline data

```bash
psql $APP_DB_DSN -f db/seeds/seed_policies_and_campaigns.sql
psql $APP_DB_DSN -f db/seeds/sample_missions_badges.sql
```

> In CI, use a migration runner (Flyway/Liquibase/Sqlx) to ensure strict ordering and repeatable deployments.

---

## 6) Governance & data handling (for compliance)

* **PII**: Never store raw UCN. We store encrypted (`*_ucn_encrypted`) and emit hashes in events.
* **Attribution**: Always populate `tenant_code`, `sticker`, `campaign_code` to enable correct policy resolution and reporting.
* **Idempotency**: Do not insert duplicate rewards; the unique key on `(referral_track_id, reward_type)` prevents double payouts.
* **Retention**:

  * `enterprise_events`: consider TTL/archival strategies (e.g., partition by month; move older partitions to cold storage).
  * Recommendation caches: short TTL by design; safe to truncate.
* **Auditing**:

  * Optionally add an audit table for UCN hash captures if required by policy.
  * Event emission provides an immutable trail for referral and reward lifecycle.

---

## 7) Operational tips & sample queries

### 7.1 Health checks

* **Referential join sanity** (rewards tied to valid referrals):

```sql
SELECT COUNT(*) AS orphans
FROM referral_rewards rr
LEFT JOIN referrals r USING (referral_track_id)
WHERE r.referral_track_id IS NULL;
```

### 7.2 Conversion proxy per campaign (last 30 days)

```sql
WITH rf AS (
  SELECT campaign_code, COUNT(*) cnt
  FROM referrals
  WHERE created_at >= NOW() - INTERVAL '30 days'
  GROUP BY 1
),
rw AS (
  SELECT campaign_code, COUNT(*) cnt
  FROM referral_rewards
  WHERE created_at >= NOW() - INTERVAL '30 days'
  GROUP BY 1
)
SELECT mc.campaign_code, mc.name,
       COALESCE(rw.cnt,0) AS rewards_30d,
       COALESCE(rf.cnt,0) AS referrals_30d,
       ROUND(COALESCE(rw.cnt,0)::numeric / NULLIF(COALESCE(rf.cnt,0),0), 4) AS conversion
FROM marketing_campaigns mc
LEFT JOIN rf ON rf.campaign_code = mc.campaign_code
LEFT JOIN rw ON rw.campaign_code = mc.campaign_code
WHERE mc.is_active = TRUE
ORDER BY conversion DESC NULLS LAST, rewards_30d DESC;
```

### 7.3 “Dangling rewards” (events present; no reward yet)

```sql
SELECT e.referral_track_id, COUNT(*) AS events_30d
FROM enterprise_events e
LEFT JOIN referral_rewards rr ON rr.referral_track_id = e.referral_track_id
WHERE e.occurred_at >= NOW() - INTERVAL '30 days'
  AND rr.referral_track_id IS NULL
GROUP BY 1
ORDER BY events_30d DESC
LIMIT 50;
```

### 7.4 Abuse signal (devices reusing completed scans)

```sql
SELECT referral_code, device_fingerprint, COUNT(*) AS times
FROM referral_qr_scans
WHERE status = 'COMPLETED'
GROUP BY 1,2
HAVING COUNT(*) > 1
ORDER BY times DESC;
```

---

## 8) Common change scenarios (how to evolve safely)

* **New product / reward type**: add keys in `reward_amounts_json` + `product_rules_json`; **no schema change needed**.
* **Campaign promo**: insert new `marketing_campaigns` row; add or update `marketing_campaign_policies`.
* **Policy change**: update JSON in `cooldown_policies` or `marketing_campaign_policies`. Services pick it up at runtime.
* **Performance**: add materialized views (MV) for heavy admin reporting; refresh nightly.
* **Partitioning**: if data grows fast:

  * Partition `enterprise_events` and `referral_qr_scans` by month.
  * Add covering indexes per workload (query plans will show what’s needed).

---

## 9) Quick glossary

* **Tenant**: White-label brand (e.g., `FNB`) used to scope policies and campaigns.
* **Sticker**: Tier (Easy, Aspire, Premier, etc.). Sticker defaults live in `cooldown_policies`.
* **Campaign**: Marketing initiative with optional policy overrides. Identified by `campaign_code`.
* **Eligibility rules**: JSON that describes required events & windows.
* **Reward type**: e.g., `ACTIVATION`, `DEBIT_ORDER`, `SALARY` (Banking) or `ACTIVATION` (Insurance).
* **Event**: Evidence (e.g., `POLICY_ACTIVATED`) used by Eligibility to approve rewards.

---

## 10) TL;DR for SAs

* **Everything is data-driven**: stickers & campaigns define **what to pay** and **when**, via JSON in tables.
* **Services** resolve **effective policy** dynamically and write **idempotent** rewards.
* **Events** are the backbone for **evidence-based** payouts.
* **Caches** are optional and purely for **speed** (they don’t change business logic).
* **No risky redeploys** for promotions: change JSON rows, not code.

If you need further diagrams (ERD, sequence flows) or sample migrations for partitioning/materialized views, I can add them.
