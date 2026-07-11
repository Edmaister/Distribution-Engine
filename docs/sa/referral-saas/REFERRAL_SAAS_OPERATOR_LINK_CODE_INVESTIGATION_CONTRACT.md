# Referral SaaS Operator Link/Code Investigation Contract

TASK ID: TASK-140

Product boundary: Referral Management and Campaign Attribution SaaS.

Status: Contract only. No runtime behavior, schema, route, permission, frontend,
or test changes are made by this task.

## Boundary

This contract packages existing link/code inspection capability for the Referral
SaaS operator workflow. It does not redefine the shared canonical link/code
facade and does not create new Referral SaaS source tables.

Required boundary docs checked:

- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`
- `docs/sa/LINK_CODE_CONTRACT.md`

Source files inspected:

- `services/link_code_service.py`
- `apps/api/routers/admin_links.py`
- `apps/api/main.py`
- `test/test_link_code_service.py`
- `test/api/test_admin_links_api.py`
- `docs/roadmap/OPERATOR_DEMO_READINESS_SMOKE_CHECKLIST.md`
- `docs/roadmap/ORDERED_TASK_LIST.md` TASK-053 and TASK-054 entries

## Purpose

Referral SaaS operators need to answer a narrow but important support question:

```text
What is this code/link, what source created it, what tenant does it belong to,
what referral/campaign/route evidence is connected, and what should I inspect
next?
```

The repository already has the core inspection primitive:

- `services.link_code_service.inspect_link_code`
- `GET /admin/links/inspect`

TASK-140 defines the Referral SaaS operator investigation contract around that
existing primitive. It does not rebuild link/code inspection.

## Current Implementation Facts

Current source types:

- `REFERRAL_CODE`
- `CAMPAIGN_CODE`
- `CAMPAIGN_REFERRAL_LINK`
- `ROUTE_REFERRAL_LINK`
- `COMPOSITE_CODE`

Current derived statuses:

- `ISSUED`
- `ACTIVE`
- `LINKED`
- `VOIDED`
- `EXPIRED`
- `INVALID`
- `UNKNOWN`

Current service behavior:

- normalizes tenant code and source type
- inspects tenant-scoped source evidence
- supports lookup by `link_code_id` or `code_or_ref`
- can include or omit source evidence with `include_evidence`
- returns missing evidence for source-not-found and tenant-mismatch cases
- returns source warnings for unavailable source inspection
- redacts sensitive key parts such as UCNs, secrets, tokens, provider payloads,
  and raw values
- treats `COMPOSITE_CODE` as compatibility-only evidence because it has no
  durable source table

Current admin route:

- `GET /admin/links/inspect`
- implemented in `apps/api/routers/admin_links.py`
- requires distribution-admin style permission through
  `require_distribution_admin_key`
- returns a read-only guardrail message
- does not issue, resolve, void, rotate, mutate, or generate codes
- returns safe validation errors for invalid source type or missing lookup
  reference

Current tests cover:

- safe canonical shape
- referral code inspection and redaction
- active and expired campaign code status mapping
- campaign/referral bridge link inspection
- active and voided route referral link status mapping
- compatibility-only composite code inspection
- missing source evidence
- tenant mismatch diagnostics without leaking the other tenant
- source-unavailable warnings
- evidence omission
- invalid input handling
- admin auth, adjacent-role rejection, guardrail text, and API response shape

## Operator Investigation Entry Points

### Primary Inspect Request

Current route:

```text
GET /admin/links/inspect
```

Required query inputs:

- `tenant_code`
- `source_type`
- either `link_code_id` or `code_or_ref`

Optional query input:

- `include_evidence`

Recommended Referral SaaS operator labels:

| Product label | Route/source input |
|---|---|
| Referral code | `source_type=REFERRAL_CODE`, `code_or_ref=<code>` |
| Campaign code | `source_type=CAMPAIGN_CODE`, `code_or_ref=<campaign_code>` |
| Campaign/referral bridge | `source_type=CAMPAIGN_REFERRAL_LINK`, `link_code_id=<campaign_track_id/referral_track_id/composite>` |
| Route/referral link | `source_type=ROUTE_REFERRAL_LINK`, `link_code_id=<route_id/referral_track_id/composite>` |
| Composite compatibility code | `source_type=COMPOSITE_CODE`, `code_or_ref=<code>` |

The product UI may use friendlier labels, but it must send the canonical source
types unless a later API wrapper maps them explicitly.

## Operator Response Contract

The existing service response is already the minimum operator evidence shape:

```json
{
  "link_code_id": "referrer_codes:...",
  "source_type": "REFERRAL_CODE",
  "source": "referrer_codes",
  "tenant_code": "FNB",
  "status": "ISSUED",
  "code": "REF123",
  "campaign": {
    "campaign_code": null,
    "campaign_track_id": null
  },
  "participant": {
    "participant_type": "REFERRER",
    "participant_ref": "SafeHandle",
    "source": "referrer_codes"
  },
  "attribution": {
    "referral_track_id": null,
    "route_id": null,
    "opportunity_id": null
  },
  "metadata": {},
  "evidence": {},
  "missing_evidence": [],
  "source_warnings": [],
  "redactions": [],
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "inspected_at": "ISO-8601"
}
```

Referral SaaS should preserve these fields for operator diagnostics. A product
wrapper may convert response casing, but it must not remove:

- source type
- source table/service
- derived status
- tenant scope
- campaign identity
- participant identity
- attribution identifiers
- missing evidence
- source warnings
- redactions
- inspected timestamp

## Operator Status Semantics

| Status | Operator meaning | Recommended next step |
|---|---|---|
| `ISSUED` | Source exists and can be inspected, but no link to a downstream referral outcome is guaranteed from this response alone. | Inspect campaign readiness or validation/progress evidence if an outcome is expected. |
| `ACTIVE` | Source evidence is active and currently usable for attribution, usually route/referral evidence. | Follow `referral_track_id`, `route_id`, or `opportunity_id` into attribution trace/support workflow. |
| `LINKED` | Campaign and referral journey evidence are connected. | Open attribution trace for the `referral_track_id`. |
| `VOIDED` | Route/referral link exists but should not be treated as active attribution. | Confirm whether a later support workflow should explain or repair the void state. |
| `EXPIRED` | Campaign/source window has expired. | Inspect campaign readiness and campaign status before promising attribution. |
| `INVALID` | Source was not found, tenant mismatched, or source-specific validation failed. | Review `missing_evidence`; do not retry as a mutation from this screen. |
| `UNKNOWN` | Source could not be inspected safely or is compatibility-only without durable evidence. | Review `source_warnings`; escalate to support workflow if investigation must continue. |

Do not present `INVALID` or `UNKNOWN` as a clean customer-facing failure reason.
TASK-141 defines customer/referrer safe status language.

## Investigation Next Links

The operator investigation view should provide safe navigation from inspected
evidence to related read-only diagnostics when identifiers are present:

| Evidence present | Next diagnostic |
|---|---|
| `campaign.campaign_code` | campaign readiness/read-only campaign details |
| `campaign.campaign_track_id` | campaign attribution/track evidence |
| `attribution.referral_track_id` | `/admin/outcomes/{referral_track_id}/trace` |
| `attribution.route_id` | route/opportunity attribution evidence where mounted and permitted |
| `attribution.opportunity_id` | opportunity evidence where mounted and permitted |
| `missing_evidence` | support workflow triage in TASK-145 |
| `source_warnings` | support workflow triage in TASK-145 |

TASK-140 does not implement those links. It defines the operator contract that
later frontend/API work should follow.

## Redaction And Privacy Rules

Operator link/code investigation may show source evidence only when it remains
safe:

- raw UCNs must be redacted
- UCN hashes must be redacted unless a specific support contract allows them
- tokens, secrets, provider payloads, raw payloads, and credential material must
  be redacted
- tenant mismatch diagnostics must not disclose the other tenant
- public/customer-facing views must not expose this operator evidence shape
- evidence omission with `include_evidence=false` must remain supported for
  lower-detail operator surfaces

The current tests already assert redaction for UCN/hash fields and reject raw
UCN, provider payload, secret, and token leakage in the API response.

## Permission Contract

Current permission boundary:

- Platform admin can inspect.
- Distribution admin can inspect.
- Missing credentials are rejected.
- Adjacent finance-only identity is rejected.

Referral SaaS should preserve this as an operator/admin diagnostic route until
a specific account/partner support permission model is designed. Do not expose
this exact evidence envelope to ordinary SaaS account users or public visitors.

## Missing Evidence And Warning Taxonomy

Current diagnostics:

| Code | Meaning |
|---|---|
| `SOURCE_NOT_FOUND` | No source evidence was found for the requested tenant and lookup. |
| `TENANT_MISMATCH` | Source evidence exists outside the requested tenant, but the other tenant is not exposed. |
| `SOURCE_UNAVAILABLE` | Source evidence could not be inspected safely. |
| `COMPATIBILITY_SOURCE_ONLY` | Composite code inspection has no durable source-table evidence. |

Future operator workflow may add product copy or triage categories, but should
not rename current service codes without a contract-tested mapping layer.

## First-Launch Operator Workflow

Minimum first-launch flow:

1. Operator opens link/code investigation.
2. Operator chooses a source type using product labels.
3. Operator enters code, link ID, campaign track ID, referral track ID, route
   ID, or composite lookup reference as appropriate.
4. System calls read-only inspect route.
5. System shows status, source, tenant, participant, campaign, attribution,
   missing evidence, warnings, redactions, and inspect timestamp.
6. System offers safe next links to campaign readiness, attribution trace, or
   support triage when the relevant identifiers exist.

This first-launch workflow remains diagnostic only.

## Future Tests

When this contract becomes implementation work, add or preserve focused tests
for:

- UI source-type selection maps to canonical source types
- operator lookup requires tenant and one lookup reference
- evidence can be toggled off
- redactions are visible and no raw sensitive values leak
- `INVALID`, `UNKNOWN`, missing-evidence, and tenant-mismatch states render
  safely
- next-link affordances appear only when the required identifier exists
- adjacent roles cannot access operator link/code investigation
- trace navigation uses `referral_track_id` and preserves tenant scope

## Explicit Non-Goals

- no schema changes
- no service, route, permission, frontend, or test implementation
- no public resolve API
- no code issue/reissue/revoke/expire behavior
- no void command
- no track creation
- no accepted-terms behavior changes
- no mutation, repair, retry, replay, queueing, webhook, reward, funding,
  fulfilment, settlement, commission, sponsor billing, or marketplace workflow
- no replacement of the existing shared `link_code_service`

## Readiness Decision

Referral SaaS already has a strong link/code inspection primitive. TASK-140
packages it into an operator investigation contract and defines the bridge to
attribution trace and later support workflow tasks. It does not claim that the
full support workflow, safe customer status, reporting, or frontend IA is
complete.
