# Referral SaaS Route Smoke Inventory

TASK ID: TASK-151

Product boundary: Referral Management and Campaign Attribution SaaS.

Status: Source-backed route inventory and local contract test. TASK-157 adds
the first bounded read-only product wrapper route for Referral SaaS reporting;
TASK-165 adds the validation-only report export gate; TASK-167 adds inline
export preview. No schema, frontend, live database, persisted export, or write
behavior is introduced by this inventory.

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
- `apps/api/routers/referral_saas_reports.py`
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
| Read-only product report | GET | `/v1/referral-saas/reports/{report_type}` | Referral SaaS report wrapper |
| Inline product export preview | POST | `/v1/referral-saas/reports/{report_type}/exports/preview` | Referral SaaS export payload preview |
| Validation-only product export | POST | `/v1/referral-saas/reports/{report_type}/exports/validate` | Referral SaaS export request validation gate |
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

TASK-157, TASK-165, and TASK-167 introduce exactly three mounted
`/v1/referral-saas/*` product wrappers:

- `GET /v1/referral-saas/reports/{report_type}`
- `POST /v1/referral-saas/reports/{report_type}/exports/preview`
- `POST /v1/referral-saas/reports/{report_type}/exports/validate`

The report wrapper is read-only and currently supports the TASK-156 through
TASK-164 report helpers. TASK-158 can derive tenant scope from tenant-scoped
identities. The export validation wrapper is side-effect free: it validates
report type, format, redaction profile, dimensions, filters, row limits, and
date windows. The export preview wrapper is also side-effect free: it returns
inline JSON or CSV preview content from the tenant-safe report output without
creating export files, storage records, delivery jobs, audit rows, retention
records, or download URLs. Internal report readers still require explicit
`tenant_code` until SaaS account resolution is implemented. No account
membership, frontend, persisted export, or write command wrapper is implied.

## Smoke Safety Classification

Read-only routes may be considered for staging or production smoke only when
auth permits and test subjects are known:

- campaign readiness
- link/code inspection
- attribution trace
- tenant-safe analytics
- Referral SaaS report wrapper
- Referral SaaS export preview wrapper
- Referral SaaS export validation wrapper
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

- choose actual seeded subjects for local/staging route smoke using
  `scripts/referral_saas_route_smoke_plan.py`
- perform live or staging schema/status/index verification using
  `scripts/referral_saas_schema_status_check.py`
- keep product wrapper expansion bounded beyond the report route,
  validation-only export gate, and inline export preview
- add safe-status and reporting E2E assertions over product-ready surfaces
- keep production smoke read-only unless separately approved

## Validation

`test/test_referral_saas_route_smoke_inventory.py` asserts that the current
read-only and seeded-write smoke route families are mounted, and that the
`/v1/referral-saas/*` route surface remains bounded to the report wrapper,
validation-only export gate, and inline export preview.

`scripts/referral_saas_route_smoke_plan.py` builds dry-run command templates
for the read-only smoke routes by default. Local/staging write-route templates
must be requested explicitly with `--include-seeded-writes`.
