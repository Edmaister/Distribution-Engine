# Referral SaaS Non-Local Launch Verification Command Pack

TASK ID: TASK-420  
Product boundary: Referral SaaS with Shared Platform proof trajectory  
Status: Command and evidence pack only. No non-local command was executed by this task.

## Required Boundary Docs Checked

- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

## Purpose

This pack turns the remaining TASK-348 launch verification blocker into an
executable, safe command path. It does not prove the environment by itself.
TASK-348 can close only after approved non-local access is provided, commands
are run against that approved environment, and sanitized evidence is recorded.

The pack exists so the product is not blocked by unclear instructions. It keeps
secrets out of the repository, prevents accidental production writes, and
separates product capability from environment-confidence evidence.

## What This Verifies

The non-local proof should verify:

- launch-critical database schema and status posture
- protected Referral SaaS API route availability
- selected-customer read spine
- selected-customer campaign, link/code, reporting, support, integrations, and
  People and Access readiness paths where approved
- no-side-effect guardrails for provider dispatch, credentials, auth claims,
  campaign activation, billing, settlement, payouts, and money movement
- sanitized evidence sufficient to remove the TASK-027/TASK-348
  environment-confidence blocker

## What This Does Not Do

This pack must not:

- store credentials, tokens, passwords, or DSNs in the repository
- run production write commands
- dispatch provider messages or webhooks in production
- create credentials, seats, auth claims, invoices, payouts, settlements, wallet
  movement, commissions, funding, fulfilment, or money movement
- inspect raw UCN, raw payloads, raw secrets, or cross-tenant evidence
- replace TASK-348 execution evidence

## Required Inputs

Before any non-local run, record these outside the repository:

| Input | Required value |
| --- | --- |
| Environment name | `staging`, `production-like`, or explicitly approved target |
| API base URL | Approved Referral SaaS runtime URL |
| DB access | Strict read-only DSN or approved read-only database role |
| API auth | Approved local API key and/or bearer token |
| Selected customer | Seeded or approved `external_tenant_ref` and any required account refs |
| Permission level | `read-only only` or `staging seeded writes allowed` |
| Evidence location | Approved secure location for sanitized command output |
| Write approval | Required only for staging/local seeded-write proof; never implied |

## Safety Gates

| Gate | Rule |
| --- | --- |
| Production posture | Read-only only. No seeded writes. |
| Staging seeded writes | Allowed only with explicit approval and isolated seeded data. |
| Secrets | Use environment variables or secret manager injection only. |
| Redaction | Evidence must omit raw secrets, raw tokens, raw UCN, raw payloads, and internal tenant identifiers unless explicitly approved for a secure evidence vault. |
| Correlation | Any approved staged mutation proof must use a dedicated correlation ID and test reference prefix. |
| Failure handling | Stop on unexpected 5xx, unsafe payload exposure, missing tenant guard, or any attempted adjacent money/provider/auth side effect. |

## Environment Setup

Use environment variables. Do not paste real values into docs, commits, PRs, or
screenshots.

```powershell
$env:REFERRAL_SAAS_VERIFY_ENV = "staging"
$env:REFERRAL_SAAS_API_BASE_URL = "https://approved.example"
$env:REFERRAL_SAAS_ADMIN_KEY = "<approved-secret>"
$env:REFERRAL_SAAS_BEARER_TOKEN = "<optional-approved-token>"
$env:REFERRAL_SAAS_EXTERNAL_TENANT_REF = "<approved-customer-reference>"
$env:APP_DB_DSN = "<approved-read-only-dsn>"
```

## Step 0 - Dry-Run Local Command Shape

Run these before using non-local credentials. They print the intended checks
without touching a non-local database.

```powershell
.\.venv\Scripts\python.exe scripts\referral_saas_schema_status_check.py
.\.venv\Scripts\python.exe scripts\referral_saas_route_smoke_plan.py
```

Expected result:

- command plan renders
- no secrets are printed
- no database write is attempted
- no provider, webhook, auth, campaign activation, billing, or money path is invoked

## Step 1 - Non-Local Read-Only DB Check

Run only with an approved read-only DSN or role.

```powershell
.\.venv\Scripts\python.exe scripts\referral_saas_schema_status_check.py --database --dsn $env:APP_DB_DSN
```

Evidence to capture:

- schema/table presence summary
- launch-critical status values
- index/constraint posture where reported
- connection role/read-only evidence where available
- redaction note confirming no raw sensitive payloads were copied

## Step 2 - Protected API Smoke Plan

Confirm the mounted Referral SaaS API surface before runtime smoke execution.

```powershell
.\.venv\Scripts\python.exe scripts\referral_saas_route_smoke_plan.py
```

Evidence to capture:

- mounted route list
- read-only versus seeded-write classification
- any route-inventory drift requiring a test update

## Step 3 - Selected-Customer Read Spine

Run against an approved selected customer. This is the default non-local API
proof because it should not mutate customer state.

```powershell
.\.venv\Scripts\python.exe scripts\referral_saas_selected_customer_e2e_physical_check.py --base-url $env:REFERRAL_SAAS_API_BASE_URL --admin-key $env:REFERRAL_SAAS_ADMIN_KEY --external-tenant-ref $env:REFERRAL_SAAS_EXTERNAL_TENANT_REF
```

Evidence to capture:

- customer resolution
- account/profile readback
- people/access posture
- integrations readiness
- campaign list/readiness
- reporting/export preview posture
- support/readiness surfaces
- no unsafe adjacent side effects

## Step 4 - Optional Staging-Only Seeded Proofs

Run only when the target is not production and explicit seeded-write approval is
recorded. These proofs create or mutate test-only data.

```powershell
.\.venv\Scripts\python.exe scripts\referral_saas_selected_customer_mutation_e2e_physical_check.py --base-url $env:REFERRAL_SAAS_API_BASE_URL --admin-key $env:REFERRAL_SAAS_ADMIN_KEY --external-tenant-ref $env:REFERRAL_SAAS_EXTERNAL_TENANT_REF
```

```powershell
.\.venv\Scripts\python.exe scripts\referral_saas_progress_attribution_physical_check.py --base-url $env:REFERRAL_SAAS_API_BASE_URL --admin-key $env:REFERRAL_SAAS_ADMIN_KEY --external-tenant-ref $env:REFERRAL_SAAS_EXTERNAL_TENANT_REF
```

```powershell
.\.venv\Scripts\python.exe scripts\referral_saas_people_access_provisioning_physical_check.py --base-url $env:REFERRAL_SAAS_API_BASE_URL --admin-key $env:REFERRAL_SAAS_ADMIN_KEY --external-tenant-ref $env:REFERRAL_SAAS_EXTERNAL_TENANT_REF --database
```

```powershell
.\.venv\Scripts\python.exe scripts\referral_saas_configurable_journey_e2e_physical_check.py --base-url $env:REFERRAL_SAAS_API_BASE_URL --admin-key $env:REFERRAL_SAAS_ADMIN_KEY --external-tenant-ref $env:REFERRAL_SAAS_EXTERNAL_TENANT_REF
```

```powershell
.\.venv\Scripts\python.exe scripts\referral_saas_product_programme_referral_e2e_physical_check.py --base-url $env:REFERRAL_SAAS_API_BASE_URL --admin-key $env:REFERRAL_SAAS_ADMIN_KEY --external-tenant-ref $env:REFERRAL_SAAS_EXTERNAL_TENANT_REF
```

Expected result:

- only approved seeded customer/test records change
- every command has idempotency/correlation evidence
- no provider dispatch, credential creation, auth-claim propagation, campaign
  activation outside the tested path, billing, settlement, payout, funding,
  invoice, wallet, commission, or money movement occurs

## Evidence Template

| Check | Command | Environment | Result | Evidence reference | Redactions | Follow-up |
| --- | --- | --- | --- | --- | --- | --- |
| DB schema/status | `referral_saas_schema_status_check.py --database` |  |  |  |  |  |
| Route smoke plan | `referral_saas_route_smoke_plan.py` |  |  |  |  |  |
| Selected-customer read spine | `referral_saas_selected_customer_e2e_physical_check.py` |  |  |  |  |  |
| Optional seeded mutation proof | Approved staging-only runner |  |  |  |  |  |

## Completion Decision

| Outcome | Meaning | Next action |
| --- | --- | --- |
| Green | DB, route, read-spine, and any approved seeded proof pass with sanitized evidence. | Close TASK-348 and remove the non-local evidence blocker from the gap matrix. |
| Amber | Product paths pass but environment, credentials, or seeded-data setup is incomplete. | Keep TASK-348 blocked and record the environment/access gap. |
| Red | Unsafe exposure, tenant guard failure, unexpected side effect, or product regression is found. | Stop launch proof, open a defect task, and do not claim 10/10. |

TASK-420 is complete when this command pack is reviewed and linked from the
roadmap/gap matrix. TASK-348 remains open until the approved non-local evidence
is actually captured.
