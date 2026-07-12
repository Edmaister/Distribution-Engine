# Referral SaaS Route Smoke Inventory

TASK ID: TASK-151

Product boundary: Referral Management and Campaign Attribution SaaS.

Status: Source-backed route inventory and local contract test. No route,
schema, auth, frontend, live database, or runtime behavior changes are made by
this task.

## Boundary

This inventory classifies the currently mounted API routes that can support
Referral SaaS route smoke planning. It uses the active FastAPI app route table
as source truth and keeps future `/v1/referral-saas/*` product wrapper routes
separate from current shared primitives.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`

Source files inspected:

- `apps/api/main.py`
- `apps/api/routers/referrals.py`
- `apps/api/routers/campaigns.py`
- `apps/api/routers/progress.py`
- `apps/api/routers/admin_campaign_readiness.py`
- `apps/api/routers/admin_links.py`
- `apps/api/routers/admin_outcomes.py`
- `apps/api/routers/admin_analytics.py`
- `apps/api/routers/consumer_experience.py`
- `apps/api/routers/reward_summary.py`
- `test/test_referral_saas_route_smoke_inventory.py`

## Current Route Facts

The active application mounts these Referral SaaS-relevant shared primitives:

| Smoke class | Method | Mounted route | Current product role |
|---|---:|---|---|
| Read-only diagnostic | GET | `/admin/campaigns/{campaign_code}/readiness` | Campaign readiness evidence |
| Read-only diagnostic | GET | `/admin/links/inspect` | Operator link/code investigation |
| Read-only diagnostic | GET | `/admin/outcomes/{referral_track_id}/trace` | Attribution trace evidence |
| Read-only reporting | GET | `/admin/analytics/reports/{report_type}` | Tenant-safe analytics foundation |
| Read-only status | GET | `/v1/experience/consumer` | Consumer/referrer experience foundation |
| Read-only status | GET | `/v1/rewards/summary/{referral_track_id}` | Reward summary foundation |
| Read-only status | GET | `/v1/rewards/summary/referrers/{referrer_ucn}` | Referrer reward summary foundation |
| Read-only status | GET | `/v1/referrers/{referrerUcn}` | Referrer progress summary |
| Seeded local/staging write | POST | `/campaigns` | Campaign create primitive |
| Seeded local/staging write | POST | `/campaigns/validate` | Campaign validation/track primitive |
| Seeded local/staging write | PATCH | `/campaigns/tracks/{campaign_track_id}` | Campaign track status update |
| Seeded local/staging write | PUT | `/campaigns/{campaign_code}/policy` | Campaign policy upsert |
| Seeded local/staging write | POST | `/public/referrals/validate` | Public referral validation |
| Seeded local/staging write | POST | `/referrals/codes` | Referral code issue/reuse |
| Seeded local/staging write | POST | `/referrals/referees/ucn` | Referee UCN capture |
| Seeded local/staging write | POST | `/v1/progress` | Progress ingestion |

## Product Wrapper Fact

No mounted route currently starts with `/v1/referral-saas`.

That is expected for this stage. The current smoke surface is made of shared
platform primitives. TASK-143 remains the product API map for future wrapper
implementation.

## Smoke Safety Classification

Read-only routes may be considered for staging or production smoke only when
auth permits and test subjects are known:

- campaign readiness
- link/code inspection
- attribution trace
- tenant-safe analytics
- consumer/referrer status summaries
- reward summaries

Write routes must remain local or staging-only unless a future task creates an
approved seeded production-safe process:

- campaign creation and updates
- campaign validation or track creation
- referral code issue/reuse
- public referral validation
- referee UCN capture
- progress ingestion

## Launch Implication

This inventory improves launch confidence because the route smoke surface is
now executable and source-backed. It does not make Referral SaaS production
ready by itself.

Remaining blockers before a 10/10 claim:

- choose actual seeded subjects for local/staging route smoke
- perform live or staging schema/status/index verification using
  `scripts/referral_saas_schema_status_check.py`
- add product wrapper routes when the product API implementation begins
- add safe-status and reporting E2E assertions over product-ready surfaces
- keep production smoke read-only unless separately approved

## Validation

`test/test_referral_saas_route_smoke_inventory.py` asserts that the current
read-only and seeded-write smoke route families are mounted, and that
`/v1/referral-saas/*` product wrapper routes remain unimplemented.
