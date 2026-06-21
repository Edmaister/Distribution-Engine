# Campaign Opportunity Lifecycle Map

Status: Accepted for TASK-006 on 2026-06-21.

## Purpose

TASK-006 maps current marketing campaign, campaign policy, campaign track, distribution opportunity, and offer route lifecycle sources into a canonical campaign lifecycle proposal.

This is a design document only. It does not authorize schema migrations, service changes, route changes, status renames, or campaign readiness implementation.

## Source Documents And Code

- `docs/product/DLAAS_TARGET_STATE.md`
- `docs/sa/CURRENT_STATE_MAP.md`
- `docs/sa/CAPABILITY_GAP_MATRIX.md`
- `docs/sa/STATE_MACHINE_MAP.md`
- `docs/sa/LIVE_CRITICAL_STATE_INVENTORY.md`
- `docs/sa/TENANT_IDENTIFIER_BOUNDARY_DECISION.md`
- `docs/sa/TENANT_ACCOUNT_BOUNDARY_MAP.md`
- `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`
- `docs/API_PERMISSION_MATRIX.md`
- `dp/migrations/002_campaigns.sql`
- `dp/migrations/003_policies.sql`
- `dp/migrations/067_distribution_opportunities.sql`
- `dp/migrations/068_distribution_offer_routes.sql`
- `services/campaign_service.py`
- `services/campaign_policy_service.py`
- `services/distribution/opportunity_service.py`
- `services/distribution/routing_service.py`
- `apps/api/routers/campaigns.py`
- `apps/api/routers/distribution/admin_opportunities.py`
- `apps/api/routers/distribution/admin_routing.py`

## Current Facts

The current campaign model is split across campaign definition, policy, attribution/track, distribution opportunity, and offer routing concepts.

`marketing_campaigns` is the campaign definition table. It uses `campaign_code` as the stable campaign identity and has `campaign_id` as a UUID surrogate. Its lifecycle is currently represented by `is_active`, `starts_at`, `ends_at`, `max_uses`, and `uses_count`; there is no full campaign lifecycle status column.

`marketing_campaign_policies` stores versioned campaign policy rows. It uses `is_active`, `version`, tenant-specific overrides, and JSON rule fields. The policy resolver selects tenant-specific active policy first, then global active policy, newest by `updated_at` and `version`.

`campaign_attributions` is the campaign interaction or track anchor. Its checked status set is `SCANNED`, `VALIDATED`, `ATTRIBUTED`, `COMPLETED`, `BLOCKED`, `EXPIRED`, and `INVALID`. `campaign_track_id` becomes the golden thread after validation.

`campaign_track_events` stores unconstrained event names for a campaign track. It is an event stream, not the campaign lifecycle source itself.

`distribution_opportunities` represents sponsor/distribution marketplace availability. Its service constants are `DRAFT`, `PUBLISHED`, and `CLOSED`. It links to `campaign_code` optionally and includes sponsor, product, targeting, budget, allocation, commission, and funding contract context.

`distribution_offer_routes` represents routed offers to distributors. Its service constants are `ROUTED`, `ACCEPTED`, and `DECLINED`. Routes can only be created for published opportunities.

Admin distribution opportunity lifecycle routes write admin audit for create, publish, close, and reopen. Distribution routing routes write admin audit for route creation and route accept/decline decisions.

## Current Lifecycle Sources

| Source | Field | Current values | Owner | Notes |
| --- | --- | --- | --- | --- |
| Campaign definition | `marketing_campaigns.is_active` | Boolean | Campaign service/admin route | Not a full lifecycle; combines active/inactive availability. |
| Campaign timing | `starts_at`, `ends_at` | Timestamps | Campaign service/admin route | Used during validation to reject not-started or expired campaigns. |
| Campaign capacity | `max_uses`, `uses_count` | Numeric counters | Campaign schema/service | Hard cap exists, but no canonical readiness state yet. |
| Campaign policy | `marketing_campaign_policies.is_active`, `version` | Boolean plus integer version | Campaign policy service | Effective policy is resolved, not lifecycle-managed. |
| Campaign track | `campaign_attributions.status` | `SCANNED`, `VALIDATED`, `ATTRIBUTED`, `COMPLETED`, `BLOCKED`, `EXPIRED`, `INVALID` | Campaign validation and track update service | This is interaction/outcome progress, not campaign configuration lifecycle. |
| Track events | `campaign_track_events.event_type` | Unconstrained text | Campaign/event writers | Needs event catalog in later task before public contracts. |
| Distribution opportunity | `distribution_opportunities.opportunity_status` | `DRAFT`, `PUBLISHED`, `CLOSED` | Distribution opportunity service/admin routes | Best current source for marketplace publish/close workflow. |
| Offer route | `distribution_offer_routes.route_status` | `ROUTED`, `ACCEPTED`, `DECLINED` | Distribution routing service/admin routes | Distributor-specific offer state, not campaign state. |

## Canonical Campaign Lifecycle Proposal

The target canonical campaign lifecycle should be a derived/read-model layer at first. It should not replace existing fields until implementation tasks explicitly add schema.

Recommended canonical campaign lifecycle:

| Canonical state | Meaning | Current evidence |
| --- | --- | --- |
| `DRAFT` | Campaign or opportunity is being configured and is not externally available. | Distribution opportunity `DRAFT`; campaign definition exists before validation availability. |
| `READY_FOR_REVIEW` | Required configuration appears present but has not been activated/published. | Future readiness service output; not a current persisted state. |
| `ACTIVE` | Campaign can accept validation or marketplace distribution. | `marketing_campaigns.is_active = TRUE` with valid date window; distribution opportunity `PUBLISHED`. |
| `PAUSED` | Temporarily unavailable but expected to resume. | No direct current state; can only be inferred from `is_active = FALSE` or future explicit lifecycle. |
| `SCHEDULED` | Campaign is configured but starts in the future. | `starts_at > now()` during validation. |
| `EXPIRED` | Campaign or opportunity date window has ended. | `ends_at < now()` during validation; campaign track `EXPIRED`. |
| `CLOSED` | Campaign/opportunity has been intentionally closed to new activity. | Distribution opportunity `CLOSED`; future campaign lifecycle field may distinguish closed from inactive. |
| `BLOCKED` | Campaign cannot operate because a guard failed. | Campaign track `BLOCKED`; future readiness service can produce blocker reasons. |
| `ARCHIVED` | Retained for history and reporting only. | No current persisted state; future lifecycle field if needed. |

This canonical lifecycle must distinguish configuration lifecycle from interaction lifecycle. Campaign track statuses such as `VALIDATED`, `ATTRIBUTED`, and `COMPLETED` describe individual customer or attribution outcomes, not whether the campaign itself is active.

## Current-To-Canonical Mapping

| Current evidence | Proposed canonical interpretation |
| --- | --- |
| `distribution_opportunities.opportunity_status = 'DRAFT'` | `DRAFT` |
| `distribution_opportunities.opportunity_status = 'PUBLISHED'` | `ACTIVE` for marketplace availability |
| `distribution_opportunities.opportunity_status = 'CLOSED'` | `CLOSED` |
| `marketing_campaigns.is_active = TRUE` and current time before `starts_at` | `SCHEDULED` |
| `marketing_campaigns.is_active = TRUE` and current time within window | `ACTIVE` |
| `marketing_campaigns.is_active = TRUE` and current time after `ends_at` | `EXPIRED` |
| `marketing_campaigns.is_active = FALSE` | `PAUSED` or `CLOSED`; current schema does not distinguish |
| no active effective policy | `BLOCKED` for readiness; current campaign validation does not enforce this |
| missing funding contract or budget evidence for distribution opportunity | `BLOCKED` for readiness; current opportunity can still exist |
| route status `ROUTED` | Campaign/opportunity remains `ACTIVE`; route-specific state is pending distributor decision |
| route status `ACCEPTED` | Campaign/opportunity remains `ACTIVE`; participant route is active for distribution |
| route status `DECLINED` | Campaign/opportunity remains `ACTIVE`; route is not available to that distributor |
| track status `SCANNED` | Interaction state; campaign lifecycle unchanged |
| track status `VALIDATED` | Interaction state; campaign lifecycle unchanged |
| track status `ATTRIBUTED` | Interaction/outcome state; campaign lifecycle unchanged |
| track status `COMPLETED` | Interaction/outcome state; campaign lifecycle unchanged |
| track status `BLOCKED`, `INVALID`, or `EXPIRED` | Interaction failure/terminal state; campaign lifecycle unchanged unless aggregate readiness later detects systemic blocker |

## Readiness Ownership Boundaries

TASK-006 does not implement readiness, but it identifies source ownership for TASK-007.

Recommended readiness source areas:

| Readiness area | Current owner | Evidence |
| --- | --- | --- |
| Tenant/account scope | Tenant boundary and future account model | TASK-004 and TASK-005 docs; `tenant_code` remains internal. |
| Campaign definition | Campaign service | `marketing_campaigns`, `campaign_service.py`. |
| Date window and active flag | Campaign service | `is_active`, `starts_at`, `ends_at`. |
| Campaign policy | Campaign policy service | `marketing_campaign_policies`, effective policy resolver. |
| Attribution tracking | Campaign service | `campaign_attributions`, `campaign_track_id`, `campaign_track_events`. |
| Marketplace publication | Distribution opportunity service | `distribution_opportunities.opportunity_status`. |
| Distributor matching/routing | Distribution routing service | Published-opportunity guard, `distribution_offer_routes`. |
| Funding context | Funding and marketplace funding services | `funding_contract_id`, budget fields, funding contract services. |
| Commission context | Distribution commission service/rules | `commission_rule_id`, commission rules/events. |
| Audit evidence | Admin audit service | Distribution opportunity and route admin audit writes. |

## API Implications

No API changes are authorized by TASK-006.

Future campaign lifecycle/readiness APIs should:

- derive tenant scope from identity or validated account/external-reference resolution
- keep `tenant_code` internal except existing backward-compatible routes
- return canonical lifecycle as derived status with current source evidence
- include readiness blockers separately from lifecycle status
- keep interaction statuses separate from campaign configuration statuses
- use 400/401/403/404/409/422 consistently with existing route patterns
- require audit for lifecycle-changing admin actions such as activate, pause, close, publish, reopen, and route

## Implementation Guidance For Later Tasks

The next implementation or contract tasks should be split.

Suggested follow-ups:

- TASK-007 should define a campaign readiness service contract using this map.
- A later schema task may add a canonical campaign lifecycle column only after the readiness contract proves current fields are insufficient.
- A later API task may add a read-only lifecycle/readiness endpoint before adding mutating lifecycle commands.
- A later event catalog task should constrain or document campaign track event types.
- A later audit task should standardize campaign lifecycle audit events across campaign and distribution opportunity actions.

## Non-Goals

TASK-006 does not implement TASK-007 readiness service.

TASK-006 does not change campaign, opportunity, route, funding, commission, or audit business logic.

TASK-006 does not rename `tenant_code`, `campaign_code`, `campaign_track_id`, `opportunity_id`, `opportunity_code`, or route identifiers.

TASK-006 does not merge campaign tracks and distribution opportunities into one table.

TASK-006 does not start outcome trace, funding readiness, participant taxonomy, or public API work.

## Validation Notes

This mapping is based on static repository inspection only. No live database state was inspected.

Current schema has a check constraint on `campaign_attributions.status`; opportunity and route status values are service-owned and do not have DB check constraints in the inspected migrations. Future implementation should add tests around service-level allowed values before relying on them for public contracts.
