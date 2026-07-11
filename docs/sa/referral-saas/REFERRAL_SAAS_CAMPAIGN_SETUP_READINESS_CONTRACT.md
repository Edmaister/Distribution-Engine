# Referral SaaS Campaign Setup And Readiness Contract

TASK ID: TASK-135

Product boundary: Referral SaaS.

Required boundary docs checked:

- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`

Supporting SA docs checked:

- `docs/sa/CAMPAIGN_OPPORTUNITY_LIFECYCLE_MAP.md`
- `docs/sa/CAMPAIGN_READINESS_SERVICE_CONTRACT.md`
- `docs/sa/LINK_CODE_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`

Current implementation files inspected:

- `dp/migrations/002_campaigns.sql`
- `dp/migrations/003_policies.sql`
- `dp/migrations/014_campaign_referral_links.sql`
- `services/campaign_service.py`
- `services/campaign_policy_service.py`
- `services/campaign_readiness_service.py`
- `apps/api/routers/campaigns.py`
- `apps/api/routers/admin_campaign_readiness.py`
- `apps/api/schemas/campaigns.py`
- `test/test_campaign_service.py`
- `test/test_campaign_policy_service.py`
- `test/test_campaign_readiness_service.py`
- `test/test_campaigns.py`
- `test/api/test_campaign_readiness_api.py`

## Purpose

Define the Referral SaaS campaign setup and readiness contract needed to turn
existing campaign, policy, validation, track, and readiness capabilities into a
coherent SaaS workflow.

This is a contract document only. It does not authorize schema, service, route,
frontend, API behavior, campaign lifecycle mutation, policy mutation, link/code
mutation, attribution mutation, billing, funding, fulfilment, settlement, or
live database changes.

## Boundary Decision

Referral SaaS campaign setup should package current campaign primitives rather
than replacing them.

Rules:

- Keep `campaign_code` as the stable campaign definition identity.
- Keep `campaign_track_id` as the post-validation campaign interaction thread.
- Keep `tenant_code` internal and resolve it from account/external references
  before service calls in future productized APIs.
- Do not merge campaign setup with distributor marketplace opportunity,
  commission, funding, fulfilment, settlement, or sponsor billing work.
- Use existing `campaign_readiness_service` as the current source for derived
  readiness until a later task deliberately extends it.
- Do not copy campaign services into product-specific folders.

## Current Facts

Current campaign schema:

- `marketing_campaigns.campaign_code` is the primary stable campaign identity.
- `marketing_campaigns.campaign_id` is a UUID surrogate.
- Campaign definition availability is currently represented by `is_active`,
  `starts_at`, `ends_at`, `max_uses`, and `uses_count`.
- `marketing_campaign_policies` stores versioned policy rows keyed by
  `(campaign_code, tenant_code, version)`.
- `campaign_attributions.campaign_track_id` is created after campaign
  validation and has checked statuses: `SCANNED`, `VALIDATED`, `ATTRIBUTED`,
  `COMPLETED`, `BLOCKED`, `EXPIRED`, and `INVALID`.
- `campaign_track_events` stores unconstrained event names for track evidence.
- `campaign_referral_links` bridges `campaign_track_id` to `referral_track_id`
  and enforces one referral journey to one campaign journey.

Current service behavior:

- `create_campaign` validates segment/name/date window, generates
  `campaign_code` when omitted, and inserts `marketing_campaigns`.
- `validate_campaign_and_create_track` checks campaign existence, tenant
  mismatch, active flag, date window, then creates a `campaign_attributions`
  row with status `VALIDATED`.
- `update_campaign_track_status` allows track status updates across the checked
  campaign attribution states.
- `get_effective_policy` resolves active tenant-specific policy first, then
  global active policy, falling back to defaults.
- `get_campaign_readiness` derives lifecycle/readiness from campaign definition
  and policy evidence for operations such as `CREATE_TRACK`,
  `PUBLISH_OPPORTUNITY`, `ROUTE_OPPORTUNITY`, `GENERATE_LINKS`,
  `ACTIVATE_CAMPAIGN`, and `CONTROL_PLANE_VIEW`.

Current API behavior:

- `POST /campaigns` creates a campaign and requires admin authentication.
- `POST /campaigns/validate` validates a campaign code and creates a campaign
  track.
- `PATCH /campaigns/tracks/{campaign_track_id}` updates interaction status and
  requires partner authentication.
- `GET /campaigns/{campaign_code}/policy` returns effective policy for partner
  scope.
- `PUT /campaigns/{campaign_code}/policy` upserts policy and requires admin
  authentication.
- `GET /admin/campaigns/{campaign_code}/readiness` returns read-only readiness
  for distribution/platform admin scope and does not mutate campaigns,
  policies, referrals, attribution, funding, fulfilment, settlement, audit, or
  rewards.

## Current SaaS Gaps

The current implementation is capable but not yet packaged as one Referral SaaS
campaign setup workflow.

Gaps:

- No product-facing campaign setup projection exists.
- No campaign setup checklist joins account readiness, campaign definition,
  policy, referral terms, progress event contract, and attribution reporting.
- No Referral SaaS-specific lifecycle language separates setup state from
  campaign interaction state.
- Current public-ish routes still accept or expose `tenant_code`.
- Campaign policy defaults can make a policy appear usable when no persisted
  active policy exists; readiness warns for `CREATE_TRACK` but blocks
  publish/activation operations.
- Opportunity-scoped readiness returns safe unknowns in the current first slice;
  this is acceptable for Referral SaaS unless marketplace distribution enters
  scope.
- Campaign track event names are unconstrained and need a later event contract
  before being treated as a public event catalog.
- No focused Referral SaaS frontend campaign setup IA is defined yet.
- No focused E2E proves account setup to campaign setup to campaign validation
  to referral attribution reporting.

## Referral SaaS Campaign Concepts

### Campaign Setup

The product workflow for configuring a campaign before referral links/codes,
validation, progress events, and attribution reporting are used.

Minimum setup fields:

| Field | Purpose | Current source |
| --- | --- | --- |
| `campaign_ref` | Product-facing campaign reference; may map to `campaign_code`. | Future wrapper or existing `campaign_code`. |
| `account_ref` | Product-facing account reference. | TASK-134 future setup. |
| `campaign_code` | Internal/stable campaign definition identity. | `marketing_campaigns`. |
| `campaign_name` | User-visible campaign name. | `marketing_campaigns.name`. |
| `segment` | Target segment or audience label. | `marketing_campaigns.segment`. |
| `starts_at`, `ends_at` | Availability window. | `marketing_campaigns`. |
| `max_uses` | Optional use cap. | `marketing_campaigns.max_uses`. |
| `policy_version` | Active policy version evidence. | `marketing_campaign_policies.version`. |
| `attribution_window` | Campaign attribution behavior. | Existing policy JSON or future explicit setting. |
| `setup_status` | Product setup state. | Future derived projection. |

### Campaign Readiness

The read-only derived decision describing whether a campaign can support a
requested operation.

Current readiness states remain:

- `READY`
- `READY_WITH_WARNINGS`
- `NOT_READY`
- `UNKNOWN`

Current operations remain:

- `CREATE_TRACK`
- `PUBLISH_OPPORTUNITY`
- `ROUTE_OPPORTUNITY`
- `GENERATE_LINKS`
- `ACTIVATE_CAMPAIGN`
- `CONTROL_PLANE_VIEW`

For Referral SaaS first launch, the priority operations are:

1. `CONTROL_PLANE_VIEW`
2. `CREATE_TRACK`
3. `GENERATE_LINKS`
4. `ACTIVATE_CAMPAIGN`

`PUBLISH_OPPORTUNITY` and `ROUTE_OPPORTUNITY` belong to broader marketplace
distribution unless a specific Referral SaaS task brings them into scope.

### Campaign Interaction

The customer or user journey that begins when a campaign code is validated.

Interaction identity and states:

- identity: `campaign_track_id`
- states: `SCANNED`, `VALIDATED`, `ATTRIBUTED`, `COMPLETED`, `BLOCKED`,
  `EXPIRED`, `INVALID`

These are not campaign setup states and must not be shown as campaign lifecycle
states in SaaS setup UX.

## Product Setup States

Referral SaaS should use product-facing setup states derived from account,
campaign, policy, link/code, event, and reporting evidence.

Recommended setup states:

| State | Meaning | Allowed behavior |
| --- | --- | --- |
| `DRAFT` | Campaign setup has started but required configuration is incomplete. | Edit only; no public validation or link generation. |
| `NEEDS_POLICY` | Campaign definition exists but policy or attribution settings are incomplete. | Edit policy/settings; readiness preview allowed. |
| `READY_FOR_REVIEW` | Required setup evidence is present for operator/product review. | Readiness and preview allowed. |
| `READY_TO_ACTIVATE` | Account and campaign readiness pass required checks. | Activation command can be considered by a later task. |
| `ACTIVE` | Campaign can support Referral SaaS validation and attribution flows. | Link/code, validation, progress, and attribution allowed by role. |
| `PAUSED` | Campaign is intentionally unavailable. | Reads and investigation allowed; new validation/link actions blocked. |
| `SCHEDULED` | Campaign is configured but starts in the future. | Reads and preview allowed; public validation blocked until start. |
| `EXPIRED` | Campaign window has ended. | Reads/reporting allowed; new validation/link actions blocked. |
| `ARCHIVED` | Campaign retained for historical reporting. | No new activity. |

These setup states are a product projection. They do not authorize immediate
schema changes.

## Setup Checklist

Minimum future campaign setup readiness checklist:

| Checklist item | Required for first launch | Source |
| --- | --- | --- |
| Account ready for campaign setup | Yes | TASK-134 account setup projection |
| Internal tenant resolved | Yes | Account/external ref resolver future task |
| Campaign definition exists | Yes | `marketing_campaigns` |
| Campaign tenant matches resolved tenant | Yes | `marketing_campaigns.tenant_code` |
| Campaign date window valid | Yes | `starts_at`, `ends_at` |
| Campaign capacity available | Yes | `max_uses`, `uses_count` |
| Active/effective policy present | Yes for activation; warning for draft preview | `marketing_campaign_policies` |
| Referral terms configured | Yes before public validation | TASK-136/TASK-137 future contracts |
| Link/code issue path available | Yes before launch | TASK-136 future contract |
| Progress event contract selected | Yes before launch | TASK-138 future contract |
| Attribution trace/reporting baseline available | Yes before launch | TASK-139/TASK-142 future contracts |
| Marketplace opportunity/routing ready | No | DLaaS/distribution expansion deferral |
| Funding/fulfilment/settlement ready | No | Explicitly deferred |

## Minimum API Contract Direction

Future Referral SaaS campaign setup APIs should be product-scoped wrappers
around current services and readiness projections.

Candidate route family:

| Route | Purpose | Auth |
| --- | --- | --- |
| `POST /referral-saas/accounts/{account_ref}/campaigns` | Create campaign setup draft/definition. | Account campaign manager or admin/operator. |
| `GET /referral-saas/accounts/{account_ref}/campaigns/{campaign_ref}` | Read campaign setup projection. | Account member or admin/operator. |
| `PUT /referral-saas/accounts/{account_ref}/campaigns/{campaign_ref}/policy` | Upsert product policy/settings. | Campaign manager or admin/operator. |
| `GET /referral-saas/accounts/{account_ref}/campaigns/{campaign_ref}/readiness` | Read setup/readiness checklist. | Account member or admin/operator. |
| `POST /referral-saas/accounts/{account_ref}/campaigns/{campaign_ref}/submit-for-review` | Submit campaign setup for review. | Campaign manager or admin/operator. |
| `POST /referral-saas/accounts/{account_ref}/campaigns/{campaign_ref}/activate` | Future activation command. | Admin/operator or approved account owner role. |
| `POST /referral-saas/campaigns/{campaign_ref}/validate` | Productized validation wrapper. | Public/partner rules to be finalized in TASK-137. |

Route prefix and auth style must be finalized in a later implementation task.
Current `/campaigns` routes remain backward-compatible current facts.

## Required Read Projection

Recommended future campaign setup read shape:

```json
{
  "account_ref": "acct_...",
  "campaign_ref": "camp_...",
  "campaign_code": "REDACT_OR_INCLUDE_BY_ROLE",
  "campaign_name": "Summer Referral Push",
  "setup_status": "READY_TO_ACTIVATE",
  "canonical_lifecycle": "ACTIVE",
  "readiness": {
    "state": "READY_WITH_WARNINGS",
    "can_proceed": true,
    "operation": "ACTIVATE_CAMPAIGN",
    "blockers": [],
    "warnings": [
      {
        "code": "NO_ACTIVE_POLICY",
        "severity": "WARNING",
        "source": "marketing_campaign_policies",
        "message": "No active effective campaign policy was found."
      }
    ],
    "unknowns": []
  },
  "setup_checklist": [
    {
      "code": "CAMPAIGN_DEFINITION_EXISTS",
      "status": "READY",
      "severity": "BLOCKER",
      "message": "Campaign definition exists."
    }
  ],
  "policy": {
    "version": 1,
    "is_active": true,
    "summary": {
      "rolling_window_days": 60
    }
  },
  "permissions": {
    "can_edit": true,
    "can_submit_for_review": true,
    "can_activate": false,
    "can_validate": true,
    "can_generate_links": true
  },
  "internal": {
    "tenant_code": "REDACT_OR_OMIT_FOR_NON_OPERATOR"
  }
}
```

Rules:

- Non-operator responses should omit or redact internal `tenant_code`.
- `campaign_code` may remain visible if it is the customer-facing code; if a
  future `campaign_ref` is introduced, product APIs should prefer it.
- Setup state, readiness state, and campaign interaction state must remain
  distinct.
- Source evidence should be available to operators but reduced for customer or
  public surfaces.

## Idempotency And Audit Expectations

Future campaign setup write commands must define idempotency before
implementation.

Required idempotent commands:

- campaign setup draft/create
- campaign policy upsert
- submit for review
- activate
- pause/resume
- archive

Audit evidence must capture:

- actor identity and role
- account reference
- campaign reference or campaign code
- resolved tenant code where available
- command name
- idempotency key or hashed idempotency reference
- previous setup state and next setup state
- readiness summary at decision time
- reason for activation, pause, resume, or archive
- correlation ID
- timestamp

Readiness reads should remain read-only and should not write audit by default.

## Permission Expectations

Initial implementation should use conservative admin/operator control until
account membership is implemented.

Future product roles:

| Role | Allowed campaign setup behavior |
| --- | --- |
| Account owner | Read setup, submit for review, possibly activate after approval policy exists. |
| Campaign manager | Create/edit campaign draft and policy, submit for review. |
| Analyst | Read setup, readiness, and reporting only. |
| Support operator | Inspect readiness and evidence, no product mutation unless explicitly allowed. |
| Integration actor | Validate campaign or ingest events only through scoped public/API contracts. |

Existing `require_admin_key`, `require_partner_key`, and
`require_distribution_admin_key` behavior remains current implementation truth.
Future product wrappers must not let a caller self-authorize by sending
`tenant_code`, `account_ref`, or `campaign_ref`.

## Validation And Test Expectations

Future implementation tasks should add tests in this order:

1. Campaign setup projection response shape and redaction tests.
2. Account not ready blocks campaign setup readiness.
3. Campaign definition exists/tenant mismatch/not found tests.
4. Campaign date window and cap readiness tests.
5. Missing/active policy tests for draft, review, and activation operations.
6. Product setup state mapping tests distinct from track interaction status.
7. Idempotency replay/conflict tests for create and policy upsert.
8. Audit evidence tests for submit/activate/pause/archive.
9. Auth and adjacent-role rejection tests.
10. Regression tests proving current `/campaigns` routes still work.
11. Frontend campaign setup workflow tests once UI is scoped.
12. E2E path from account setup to campaign setup to campaign validation.

## Implementation Slices

Recommended future task slices:

1. Add campaign setup projection contract tests.
2. Add read-only campaign setup projection service using existing campaign,
   policy, account setup, and readiness evidence.
3. Add guarded admin/operator product route for campaign setup projection.
4. Add campaign setup draft/policy write contract after projection is stable.
5. Add activation command only after audit, idempotency, and readiness gates are
   tested.
6. Add frontend campaign setup workflow after backend projection and route
   contracts are stable.

Do not combine activation with campaign creation. Keep the first implementation
read-only if possible.

## Explicit Non-Goals

This contract does not implement:

- database schema
- campaign setup projection service
- route handlers
- frontend setup UI
- campaign lifecycle mutation
- campaign activation/pause/archive commands
- changes to current `/campaigns` behavior
- changes to campaign validation or track creation
- changes to campaign attribution trace
- changes to referral code/link issue behavior
- marketplace opportunity publish/routing
- distributor commissions
- funding, fulfilment, settlement, wallets, sponsor billing, or money movement
- white-label/embed
- live DB checks

## Readiness Decision

Referral SaaS campaign setup can proceed to implementation planning after this
contract. The next implementation should preferably be a read-only campaign
setup projection that composes existing account setup, campaign, policy, and
readiness evidence without changing current campaign behavior.

