# Referral SaaS Attribution Trace Contract

TASK ID: TASK-139

## Boundary

This contract belongs to the Referral Management and Campaign Attribution SaaS
product boundary. It productizes the attribution-trace slice needed for
Referral SaaS while preserving the existing shared outcome trace service.

Required boundary docs checked:

- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_CAMPAIGN_SETUP_READINESS_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`
- `docs/sa/OUTCOME_TRACE_RESPONSE_CONTRACT.md`
- `docs/sa/LINK_CODE_CONTRACT.md`

Source files inspected:

- `services/outcome_trace_service.py`
- `apps/api/routers/admin_outcomes.py`
- `services/link_code_service.py`
- `dp/migrations/002_campaigns.sql`
- `dp/migrations/014_campaign_referral_links.sql`
- `dp/migrations/070_distribution_route_referral_links.sql`
- `test/test_outcome_trace_service.py`
- `test/test_distribution_attribution_journey_contract.py`

## Purpose

Referral SaaS needs an explainable trace from campaign/link/code/event evidence
to the referral outcome so operators can answer:

1. Which source created or influenced this referral outcome?
2. Which campaign, referral code, route, progress events, and evidence rows are
   connected?
3. What evidence is missing, ambiguous, redacted, or unavailable?

This task does not build a new trace service. The repository already has
`services.outcome_trace_service.get_outcome_trace` and admin routes for outcome
trace access. TASK-139 defines the Referral SaaS product contract around that
existing capability.

## Current Implementation Facts

Current service:

- `services.outcome_trace_service.get_outcome_trace`
- lookup by tenant and `referral_track_id`
- returns trace envelope, sections, support trace, missing evidence, source
  warnings, redactions, and generated timestamp
- raises `OutcomeTraceNotFound` when the tenant-scoped outcome is absent
- supports `include_sections`

Current admin route:

- `GET /admin/outcomes/{referral_track_id}/trace`
- implemented in `apps/api/routers/admin_outcomes.py`
- requires `require_session_key`
- allows operator/admin roles only
- normalizes `tenant_code`
- rejects cross-tenant access unless identity tenant is `INTERNAL`
- returns a read-only guardrail message

Current outcome trace sections:

- `outcome`
- `attribution`
- `participants`
- `events`
- `reward`
- `commission`
- `funding`
- `fulfilment`
- `settlement`
- `audit`
- `webhooks`

Current tests cover:

- complete source trail response shape
- missing evidence for broken trails
- tenant-scoped missing outcome
- requested section filtering
- support trace audit/correlation references
- redaction of raw UCN fields in outcome trace output

## Referral SaaS Attribution Sources

Referral SaaS first-launch attribution should prioritize these sections:

| Section | Current source truth | Current join |
| --- | --- | --- |
| Outcome | `referral_instances` plus `referrer_codes` | `referral_track_id`, `tenant_code`, `referrer_code_id` |
| Link/code | `referrer_codes`, `campaign_referral_links`, `distribution_route_referral_links` | `referral_code`, `referral_track_id`, route/campaign links |
| Campaign attribution | `campaign_referral_links`, `campaign_attributions`, `campaign_track_events` | `referral_track_id` to `campaign_track_id` |
| Route attribution | `distribution_route_referral_links`, distributors, opportunities | `referral_track_id`, `route_id`, `opportunity_id` |
| Progress events | `referral_progress_events`, `enterprise_event_inbox` | `referral_track_id`, event keys |
| Audit/support | `referral_processing_audit`, `admin_audit_log`, support trace | `referral_track_id`, correlation IDs, dedupe keys |

Money sections such as reward, commission, funding, fulfilment, and settlement
exist in the shared outcome trace, but they are not required for the first
Referral SaaS attribution trace surface. They may remain operator-only optional
sections and must not become first-launch blockers.

## Product Trace Types

Referral SaaS should expose three trace views over the same source evidence.

### Operator Attribution Trace

Purpose:

- support investigation
- source evidence inspection
- missing-evidence diagnosis
- campaign/link/progress attribution review

Current implementation route:

- `/admin/outcomes/{referral_track_id}/trace`

Recommended first product section set:

- `outcome`
- `attribution`
- `participants`
- `events`
- `audit`

### Account/Partner Attribution Trace

Purpose:

- show tenant/customer-safe attribution status to SaaS account users
- support campaign performance investigation without raw identity leakage

Future route direction:

```text
GET /referral-saas/accounts/{account_ref}/attribution-traces/{referral_track_id}
```

This is not implemented by TASK-139.

### Customer/Referrer Safe Trace

Purpose:

- show high-level safe status and next action only

This belongs mostly to TASK-141 safe status and should not expose source
tables, raw trace evidence, internal status names, or operator diagnostics.

## Recommended Product Response

Minimum operator/product trace response:

```json
{
  "traceStatus": "PARTIAL",
  "lookup": {
    "type": "REFERRAL_TRACK_ID",
    "value": "uuid"
  },
  "outcome": {
    "referralTrackId": "uuid",
    "status": "FUNDED",
    "product": "TRANSACTIONAL",
    "subProduct": "DDA13",
    "journeyCode": "BANKING_TRANSACTIONAL",
    "journeyVersion": "v1"
  },
  "attribution": {
    "campaignLinks": [],
    "routeLinks": [],
    "sourceConfidence": "PARTIAL"
  },
  "events": {
    "progressEvents": [],
    "enterpriseEvents": []
  },
  "missingEvidence": [],
  "sourceWarnings": [],
  "redactions": []
}
```

The product wrapper may convert snake_case service fields to camelCase, but it
must preserve source evidence names inside operator-only evidence blocks.

## Trace Completeness

Referral SaaS should reuse current trace completeness semantics:

- `COMPLETE`
- `PARTIAL`
- `MISSING_EVIDENCE`
- `INCONSISTENT`
- `UNAVAILABLE`

For product UX, map them conservatively:

| Trace completeness | Product meaning |
| --- | --- |
| `COMPLETE` | All requested attribution evidence is present or proven not applicable. |
| `PARTIAL` | Core outcome exists, but one or more attribution sections are missing. |
| `MISSING_EVIDENCE` | Required attribution evidence is absent. |
| `INCONSISTENT` | Source evidence conflicts and needs operator review. |
| `UNAVAILABLE` | Source cannot be safely evaluated. |

Do not present a `PARTIAL` or `UNAVAILABLE` trace as a clean attribution win.

## Missing Evidence Contract

Referral SaaS should preserve the current missing-evidence taxonomy:

- `OUTCOME_NOT_FOUND`
- `TENANT_MISMATCH`
- `SECTION_NOT_REQUESTED`
- `NO_SOURCE_EVIDENCE`
- `JOIN_AMBIGUOUS`
- `SOURCE_CONFLICT`
- `SOURCE_UNAVAILABLE`
- `REDACTED`
- `NOT_APPLICABLE`

For the first SaaS trace, the most important cases are:

| Code | Product handling |
| --- | --- |
| `NO_SOURCE_EVIDENCE` | Show as unattributed/missing source evidence for the section. |
| `JOIN_AMBIGUOUS` | Operator review required before relying on that section. |
| `SOURCE_CONFLICT` | Do not use for reporting totals until resolved. |
| `REDACTED` | Evidence exists but is hidden for the caller role. |
| `SECTION_NOT_REQUESTED` | Not a product failure; caller asked for a smaller trace. |

## Attribution Decision Rules

The trace response is evidence, not an attribution mutation.

Rules:

- do not create or update campaign attribution from the trace read
- do not infer campaign attribution from campaign code alone when no
  `campaign_referral_links` or `campaign_attributions` evidence exists
- do not infer route attribution without `distribution_route_referral_links`
  evidence
- do not treat progress events as attribution source by themselves
- do not hide `JOIN_AMBIGUOUS` joins in reporting or support UX
- preserve campaign attribution status from `campaign_attributions`
- preserve route link status from `distribution_route_referral_links`

## Privacy And Redaction

Trace responses must not expose:

- raw referrer UCN
- raw referee UCN
- raw account numbers
- provider payloads
- webhook signing material
- API keys, secrets, or tokens
- unrestricted audit metadata

Allowed safe evidence:

- referral track ID
- campaign code and campaign track ID where role-allowed
- route ID and opportunity ID where role-allowed
- safe referrer handle
- source system and source event ID
- dedupe key
- safe missing-evidence codes
- operator-safe fulfilment/settlement statuses only when optional money sections
  are included

## Permission Model

Current implementation is operator/admin only.

Current allowed roles:

- `ADMIN`
- `SYSTEM_ADMIN`
- `FINANCE_ADMIN`
- `DISTRIBUTION_ADMIN`
- `PLATFORM_ADMIN`

Referral SaaS account/partner access should be a later wrapper task after
account membership and public API contract mapping are ready.

Future account-level access must:

- resolve `account_ref` to tenant
- reject cross-tenant access
- return redacted evidence by role
- avoid exposing internal money, fulfilment, settlement, webhook, or audit
  sections unless explicitly authorized

## Relationship To Reporting

Attribution trace explains one outcome. Reporting aggregates many outcomes.

TASK-139 does not define reporting totals, export formats, freshness windows, or
reconciliation rules. Those remain TASK-142.

Reporting should consume trace-compatible source rules:

- campaign attribution requires campaign link/track evidence
- route attribution requires route link evidence
- missing evidence must not be counted as attributed
- ambiguous joins must be excluded or surfaced separately until resolved

## Future Tests

Implementation work following this contract should add or preserve tests for:

- operator trace can request first-launch section set only
- account/partner wrapper redacts internal sections when implemented
- cross-tenant trace access is rejected
- missing campaign attribution is distinct from unavailable attribution
- route attribution is present only when route link evidence exists
- progress events appear as evidence but do not by themselves prove attribution
- raw UCNs and account numbers are not returned
- `JOIN_AMBIGUOUS` and `SOURCE_CONFLICT` are surfaced in response and not
  collapsed into clean attribution
- requested-section filtering preserves `SECTION_NOT_REQUESTED`
- support trace references include dedupe/source/correlation evidence

## Implementation Slices

Recommended sequence:

1. Add Referral SaaS attribution trace projection tests over
   `get_outcome_trace`.
2. TASK-180 adds a narrow product API wrapper that includes only first-launch
   sections: outcome, attribution, participants, events, and audit.
3. Add a focused Referral SaaS attribution trace frontend surface over the
   TASK-180 wrapper.
4. Add redaction/role tests for account-safe trace output after account
   membership exists.
5. Link operator link/code investigation UI to the outcome trace workflow.
6. Define reporting aggregation rules in TASK-142.

## Current Product Wrapper Fact

TASK-180 implements
`GET /v1/referral-saas/operator/outcomes/{referral_track_id}/trace` as a
read-only Referral SaaS operator wrapper over `get_outcome_trace`.

The wrapper:

- requires the Referral SaaS operator/distribution-admin bridge
- accepts required `tenant_code` and optional repeated `include_sections`
- defaults to `outcome`, `attribution`, `participants`, `events`, and `audit`
- rejects reward, commission, funding, fulfilment, settlement, webhook, and
  unknown sections before the shared trace service is called
- preserves missing evidence, source warnings, redactions, support trace, and
  safe next diagnostics
- does not mutate attribution, progress, campaign, reward, funding,
  fulfilment, settlement, audit, webhook, or money state

## Explicit Non-Goals

This task does not implement:

- schema migrations
- new routes
- service behavior changes
- frontend changes
- attribution mutation
- campaign validation changes
- progress ingestion changes
- operator link/code investigation workflow
- tenant-safe reporting/export
- customer/referrer safe status
- reward, commission, funding, fulfilment, settlement, sponsor billing, or
  money movement changes
- live DB verification

## Readiness Decision

Referral SaaS now has a strong trace foundation through `outcome_trace_service`,
`/admin/outcomes/{referral_track_id}/trace`, and the TASK-180 product wrapper.
The next work should add a focused trace UI and progress/status support links
over that wrapper instead of creating a separate attribution system.
