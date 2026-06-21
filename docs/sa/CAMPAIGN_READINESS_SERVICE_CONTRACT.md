# Campaign Readiness Service Contract

Status: Accepted for TASK-007 on 2026-06-21.

## Purpose

TASK-007 defines the backend contract for a future campaign readiness service. The service should evaluate whether a campaign or linked distribution opportunity is ready for activation, publication, routing, attribution, funding, and operator visibility.

This is a contract document only. It does not implement a service, route, migration, schema field, lifecycle mutation, funding mutation, or audit write.

## Source Documents And Code

- `docs/sa/CAMPAIGN_OPPORTUNITY_LIFECYCLE_MAP.md`
- `docs/sa/STATE_MACHINE_MAP.md`
- `docs/sa/API_SURFACE_MAP.md`
- `docs/sa/CURRENT_STATE_MAP.md`
- `docs/sa/CAPABILITY_GAP_MATRIX.md`
- `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md`
- `docs/product/DLAAS_TARGET_STATE.md`
- `dp/migrations/002_campaigns.sql`
- `dp/migrations/014_campaign_referral_links.sql`
- `dp/migrations/067_distribution_opportunities.sql`
- `dp/migrations/068_distribution_offer_routes.sql`
- `dp/migrations/070_distribution_route_referral_links.sql`
- `services/campaign_service.py`
- `services/campaign_policy_service.py`
- `services/distribution/opportunity_service.py`
- `services/distribution/routing_service.py`
- `services/distribution/distributor_portal_service.py`
- `services/funding/account_resolution.py`
- `services/funding/account_rules.py`
- `services/marketplace_funding/funding_contract_service.py`
- `apps/api/routers/campaigns.py`
- `apps/api/routers/distribution/admin_opportunities.py`
- `apps/api/routers/distribution/admin_routing.py`

## Contract Summary

Recommended future service name: `campaign_readiness_service`.

Recommended first method:

```text
get_campaign_readiness(
  *,
  tenant_code: str,
  campaign_code: str,
  opportunity_id: str | None = None,
  include_evidence: bool = True,
) -> CampaignReadinessResult
```

The service is read-only. It must not create campaign tracks, publish opportunities, route distributors, reserve funding, mutate policies, or write audit records by itself.

Readiness is a derived decision over existing source truth. It should return:

- the resolved canonical campaign lifecycle from TASK-006
- an overall readiness state
- blocking and warning reasons
- source evidence references
- unavailable evidence notes where current source truth cannot prove a requirement

## Readiness States

| State | Meaning |
| --- | --- |
| `READY` | Required checks pass for the requested operation. |
| `NOT_READY` | At least one required blocker prevents activation, publication, routing, or validation. |
| `READY_WITH_WARNINGS` | Required checks pass but non-blocking risks or missing optional evidence exist. |
| `UNKNOWN` | The service cannot make a reliable decision because source evidence is unavailable, inconsistent, or outside current schema truth. |

These states are not campaign lifecycle states. They describe readiness to act.

## Operations To Evaluate

The first contract should support operation-specific readiness because a campaign can be ready for one action but not another.

| Operation | Meaning |
| --- | --- |
| `CREATE_TRACK` | Campaign can accept validation and create a campaign track. |
| `PUBLISH_OPPORTUNITY` | Linked opportunity can be made available to distributors. |
| `ROUTE_OPPORTUNITY` | Published opportunity can be matched/routed to eligible distributors. |
| `GENERATE_LINKS` | Active route or campaign can support link/code generation. |
| `ACTIVATE_CAMPAIGN` | Future lifecycle command can safely mark campaign active. |
| `CONTROL_PLANE_VIEW` | Operator can see a safe readiness summary even when some checks are unknown. |

## Required Inputs

| Input | Required? | Notes |
| --- | --- | --- |
| `tenant_code` | Yes | Internal tenant scope, resolved before service call. |
| `campaign_code` | Yes for campaign-scoped checks | Stable campaign definition identity. |
| `opportunity_id` | Required for opportunity/routing checks | Distribution opportunity identity. |
| `operation` | Yes | Determines which blockers are required. |
| `actor_identity` | No for pure service contract; required at API layer | API layer must enforce auth and tenant scope before calling. |
| `include_evidence` | Optional | Allows compact UI responses or detailed operator diagnostics. |

The service should accept internal `tenant_code` only after authentication and external-reference resolution have already happened.

## Required Output Shape

Recommended response contract:

```json
{
  "tenant_code": "FNB",
  "campaign_code": "FNB-GOLD-SUMMER-ABCD1234",
  "opportunity_id": "uuid-or-null",
  "operation": "PUBLISH_OPPORTUNITY",
  "canonical_lifecycle": "ACTIVE",
  "readiness": "NOT_READY",
  "can_proceed": false,
  "blockers": [
    {
      "code": "NO_ACTIVE_POLICY",
      "severity": "BLOCKER",
      "source": "marketing_campaign_policies",
      "message": "No active effective campaign policy was found."
    }
  ],
  "warnings": [],
  "evidence": {
    "campaign": {},
    "policy": {},
    "opportunity": {},
    "routing": {},
    "links": {},
    "funding": {},
    "audit": {}
  },
  "unknowns": [],
  "evaluated_at": "ISO-8601 timestamp"
}
```

The final API response can use camelCase if route conventions require it, but the service contract should preserve source field names in evidence.

## Blocker Categories

| Code | Severity | Source family | Meaning |
| --- | --- | --- | --- |
| `CAMPAIGN_NOT_FOUND` | Blocker | Campaign definition | No `marketing_campaigns` row for tenant/campaign. |
| `TENANT_MISMATCH` | Blocker | Campaign definition | Campaign tenant does not match resolved tenant scope. |
| `CAMPAIGN_INACTIVE` | Blocker | Campaign definition | Current `is_active` is false. |
| `CAMPAIGN_NOT_STARTED` | Blocker | Campaign timing | `starts_at` is in the future for activation/validation. |
| `CAMPAIGN_EXPIRED` | Blocker | Campaign timing | `ends_at` has passed. |
| `CAMPAIGN_CAP_EXHAUSTED` | Blocker | Campaign capacity | `uses_count` has reached `max_uses` where max is set. |
| `NO_ACTIVE_POLICY` | Blocker | Campaign policy | Effective policy resolver finds no active policy. |
| `POLICY_UNKNOWN` | Unknown | Campaign policy | Policy cannot be resolved because source table/query failed. |
| `OPPORTUNITY_NOT_FOUND` | Blocker | Distribution opportunity | Opportunity ID or linked campaign opportunity is missing. |
| `OPPORTUNITY_NOT_DRAFT` | Blocker | Distribution opportunity | Publish requested but opportunity is not in `DRAFT`. |
| `OPPORTUNITY_NOT_PUBLISHED` | Blocker | Distribution routing | Routing requested but opportunity is not `PUBLISHED`. |
| `OPPORTUNITY_CLOSED` | Blocker | Distribution opportunity | Opportunity is closed for new activity. |
| `MISSING_COMMISSION_RULE` | Blocker or warning | Commission | Opportunity has no commission rule where commission is required. |
| `NO_ELIGIBLE_DISTRIBUTORS` | Blocker or warning | Routing | Distributor matching yields no eligible candidates. |
| `NO_ACTIVE_ROUTE` | Blocker | Links/routing | Link generation requested but no active/accepted route exists. |
| `NO_ACTIVE_LINK` | Warning | Links | No active distribution route referral link exists yet. |
| `FUNDING_CONTRACT_MISSING` | Blocker | Funding | Opportunity requires funding but has no funding contract. |
| `FUNDING_CONTRACT_NOT_ACTIVE` | Blocker | Funding | Linked contract is suspended, cancelled, or not active. |
| `FUNDING_RULE_MISSING` | Blocker or warning | Funding | No active funding account/rule can resolve for campaign context. |
| `FUNDING_EXPOSURE_UNKNOWN` | Unknown | Funding | Funding exposure/readiness cannot be computed from current evidence. |
| `AUDIT_EVIDENCE_MISSING` | Warning | Audit | No prior lifecycle audit evidence found where expected. |
| `SOURCE_INCONSISTENT` | Unknown | Any | Source rows disagree or violate expected tenant/campaign relationship. |

Severity should be operation-specific. For example, missing links should not block `PUBLISH_OPPORTUNITY`, but it may block `GENERATE_LINKS` or warn for `CONTROL_PLANE_VIEW`.

## Source Ownership

| Check | Source owner | Current source truth |
| --- | --- | --- |
| Campaign exists and tenant matches | Campaign service | `marketing_campaigns.campaign_code`, `tenant_code`. |
| Campaign active/window/capacity | Campaign service | `is_active`, `starts_at`, `ends_at`, `max_uses`, `uses_count`. |
| Effective policy exists | Campaign policy service | `get_effective_policy`, `marketing_campaign_policies`. |
| Campaign track readiness | Campaign service | `campaign_attributions`, `campaign_track_events`. |
| Opportunity exists and status | Distribution opportunity service | `distribution_opportunities.opportunity_status`. |
| Routing readiness | Distribution routing service | Published-opportunity guard and distributor matching. |
| Link/code readiness | Distribution portal/link services | `distribution_route_referral_links.link_status`, `campaign_referral_links`. |
| Commission readiness | Distribution commission service | Commission rules tied by tenant/campaign/opportunity context. |
| Funding readiness | Funding and marketplace funding services | `funding_contract_id`, active funding contracts, active funding rules/account resolution. |
| Audit readiness | Admin audit service | Distribution opportunity and route audit actions where currently written. |

## Operation-Specific Required Checks

### `CREATE_TRACK`

Required blockers:

- campaign exists
- tenant scope matches
- `is_active = TRUE`
- current time is within `starts_at`/`ends_at` if set
- capacity has not been exhausted if `max_uses` is set

Warnings:

- no active effective policy if current validation still allows track creation
- no campaign track event catalog yet

### `PUBLISH_OPPORTUNITY`

Required blockers:

- campaign exists where `campaign_code` is linked
- opportunity exists
- opportunity tenant matches campaign tenant
- opportunity is `DRAFT`
- required product, sponsor, targeting, and budget fields are present for target product scope
- funding contract is present and active when the opportunity declares one
- commission rule exists where distributor commission is expected

Warnings:

- missing active route links
- missing audit evidence from earlier draft/create step
- funding exposure cannot be computed yet

### `ROUTE_OPPORTUNITY`

Required blockers:

- opportunity exists
- opportunity is `PUBLISHED`
- opportunity tenant has eligible active distributors
- route operation can determine scoring evidence
- opportunity is not closed or expired

Warnings:

- no active route referral links after routing
- low match count

### `GENERATE_LINKS`

Required blockers:

- campaign or opportunity source exists
- target route exists and is active enough for link generation
- distributor/referral target is tenant-scoped correctly
- no existing conflicting active link for the referral/route pair

Warnings:

- campaign has no active policy
- route is routed but not accepted, if future business rules require acceptance before link generation

### `ACTIVATE_CAMPAIGN`

This is a future operation and must not be implemented until a lifecycle command exists.

Required blockers should include all campaign definition checks, active policy, tenant/account readiness, funding readiness if money-backed, and audit/idempotency command requirements.

## API Contract Direction

TASK-007 does not add an API, but a future endpoint can be:

```text
GET /admin/campaigns/{campaign_code}/readiness?tenant_code=...&operation=...
GET /admin/distribution/opportunities/{opportunity_id}/readiness?operation=...
```

API requirements:

- admin/operator auth using the narrowest appropriate helper
- tenant scope must be explicit for admin reads and resolved from identity for tenant-bound reads
- read-only and idempotent behavior
- no state mutation, route generation, funding reservation, publish, or audit write
- 400 for invalid operation/filter
- 401/403 for missing or insufficient auth
- 404 for inaccessible or missing campaign/opportunity
- 409 only for future mutating readiness gates, not pure reads
- safe response shape for partner/customer surfaces if exposed later

## Audit And Idempotency

Readiness reads should not write audit by default. If a future route exports readiness evidence, opens an investigation, or performs a lifecycle command based on readiness, that action must follow `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md`.

Readiness reads do not require idempotency keys. Future mutating commands such as activate, publish, pause, close, route, or generate links must define idempotency and audit evidence before implementation.

## Test Contract For Later Implementation

Future implementation tests should cover:

- campaign not found
- tenant mismatch
- inactive campaign
- not-started and expired campaigns
- exhausted campaign cap
- no active policy
- opportunity not found
- opportunity draft/published/closed readiness
- routing blocked before publish
- no eligible distributors
- active funding contract present and missing/inactive funding contract cases
- funding rule/account resolution missing
- link generation with no active route/link and with existing conflicting link
- read-only behavior with no writes
- admin auth and cross-tenant denial
- evidence redaction and safe response for non-operator surfaces

## Non-Goals

TASK-007 does not implement `campaign_readiness_service`.

TASK-007 does not add campaign readiness routes.

TASK-007 does not change campaign, opportunity, routing, link, funding, commission, fulfilment, settlement, audit, auth, or data-isolation behavior.

TASK-007 does not start TASK-008 or any downstream outcome, qualification, funding, or public API work.

TASK-007 does not create or rename schema fields.

## Open Implementation Questions

These questions should be resolved inside later implementation tasks:

- Whether missing effective campaign policy blocks `CREATE_TRACK` or only blocks activation/publish readiness.
- Whether route acceptance is required before generating distributor referral links.
- Which funding source is canonical for publish readiness when both opportunity budget fields and funding contracts exist.
- Whether readiness should be cached or always computed live.
- Whether public/partner-facing readiness should be a reduced safe view separate from operator readiness.
