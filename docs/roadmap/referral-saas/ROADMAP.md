# Referral Management and Campaign Attribution SaaS Roadmap

## Objective

Productize the existing referral management and campaign attribution
capabilities into a focused SaaS product before broad DLaaS expansion.

## Current Foundation

Already present in source code:

- referral code creation and reuse
- accepted-terms enforcement
- referral code validation
- referral instance creation
- QR scan evidence
- referee UCN capture
- progress event ingestion
- journey and identifier validation
- dedupe keys and event payload hashes
- campaign creation and validation
- campaign track updates
- campaign policy read/write
- campaign attribution records and track events
- campaign readiness checks
- canonical link/code inspection
- role-specific frontend and API surfaces
- relevant unit, service, API, and journey tests

## Roadmap Themes

### 1. SaaS Account Packaging

Goal: wrap existing tenant-scoped behavior in a product-ready SaaS account
model.

Needed:

- account/company setup
- user membership and roles
- tenant setup checklist
- basic plan/limit gates
- external references that do not expose internal `tenant_code`
- tenant isolation verification

### 2. Campaign Productization

Goal: make campaign setup feel like one coherent SaaS workflow.

Needed:

- campaign draft/setup UX
- readiness gates before activation
- attribution window settings
- policy version visibility
- campaign lifecycle status for users
- campaign reporting defaults

### 3. Referral Link And Code Hardening

Goal: turn existing referral code/link behavior into a complete product
workflow.

Needed:

- documented public API contract
- lifecycle actions such as revoke, expire, and reissue where required
- safe operator investigation flow
- audit consistency for sensitive actions
- frontend handling for validation failure and recovery states

### 4. Attribution Trace Product

Goal: unify existing campaign attribution, progress events, campaign links, and
route links into an explainable attribution trace.

Needed:

- attribution trace response contract
- attribution windows and precedence rules
- conflict/missing-evidence handling
- override policy and audit evidence
- tenant-safe attribution reporting

### 5. SaaS Operations

Goal: make the focused product supportable and production-ready.

Needed:

- tenant-safe reporting and exports
- support dashboard for failed validation and missing evidence
- event replay posture and safe retry classes
- observability and smoke checks
- live DB/state verification
- full golden-path and failure-path E2E tests

## 10/10 Gap Matrix

The current focused gap matrix is:

- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`

It classifies the remaining work as SaaS packaging and hardening, not
greenfield referral construction.

## Recommended Ordered Task Sequence

1. TASK-134: Define Referral SaaS account setup contract.
2. TASK-135: Productize Referral SaaS campaign setup and readiness contract.
3. TASK-136: Harden Referral SaaS referral code issue contract.
4. TASK-137: Harden Referral SaaS validation and recovery contract.
5. TASK-138: Productize Referral SaaS progress event contract.
6. TASK-139: Define Referral SaaS attribution trace contract.
7. TASK-147: Define Referral SaaS E2E and live verification plan.
8. TASK-140: Add Referral SaaS operator link/code investigation contract.
9. TASK-141: Define Referral SaaS safe status contract.
10. TASK-142: Define Referral SaaS reporting and export contract.
11. TASK-143: Create Referral SaaS public API contract map.
12. TASK-144: Define Referral SaaS frontend IA and workflow contract.
13. TASK-145: Define Referral SaaS operator support workflow.
14. TASK-146: Inventory Referral SaaS audit and idempotency posture.

## 10/10 Exit Criteria

- A new tenant can onboard, configure a campaign, issue/validate referral links
  or codes, ingest progress events, and see attribution status without manual DB
  intervention.
- Operators can investigate link/code, validation, progress, and attribution
  failures from safe evidence.
- Referrer/customer surfaces show safe status and next action without leaking
  internal states.
- Public APIs have clear auth, idempotency, error, and schema contracts.
- Reports are tenant-safe and reconcile to source event evidence.
- Live DB/state verification has been completed for all launch-critical tables,
  constraints, statuses, and smoke routes.

## Completed Contract Outputs

- TASK-134: `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`
- TASK-135: `docs/sa/referral-saas/REFERRAL_SAAS_CAMPAIGN_SETUP_READINESS_CONTRACT.md`
- TASK-136: `docs/sa/referral-saas/REFERRAL_SAAS_REFERRAL_CODE_ISSUE_CONTRACT.md`
- TASK-137: `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`
- TASK-138: `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`
- TASK-139: `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`
- TASK-147: `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`
- TASK-140: `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md`
- TASK-141: `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`

## Explicit Deferrals

The following are DLaaS expansion work, not blockers for this SaaS roadmap:

- distributor marketplace depth
- commission settlement
- funding operations
- fulfilment provider routing
- settlement batches
- sponsor billing
- white-label/embed
