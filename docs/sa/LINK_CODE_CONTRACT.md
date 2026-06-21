# Canonical Link/Code Contract

Status: Accepted for TASK-009 on 2026-06-22.

## Purpose

TASK-009 defines the canonical DLaaS contract for issuing, resolving, inspecting, and voiding current distribution links and codes. It wraps existing referral codes, campaign validation codes, campaign/referral bridge links, and distributor route referral links without changing their current schema or service behavior.

This is a contract document only. It does not implement a link/code service, route, migration, schema field, code format, auth change, void command, or attribution/outcome service.

## Source Documents And Code

- `docs/product/DLAAS_TARGET_STATE.md`
- `docs/sa/CAMPAIGN_OPPORTUNITY_LIFECYCLE_MAP.md`
- `docs/sa/CAMPAIGN_READINESS_SERVICE_CONTRACT.md`
- `docs/sa/PARTICIPANT_TAXONOMY_PERMISSION_MAP.md`
- `docs/API_PERMISSION_MATRIX.md`
- `docs/sa/API_SURFACE_MAP.md`
- `docs/sa/CURRENT_STATE_MAP.md`
- `docs/sa/CAPABILITY_GAP_MATRIX.md`
- `docs/sa/STATE_MACHINE_MAP.md`
- `dp/migrations/001_init.sql`
- `dp/migrations/002_campaigns.sql`
- `dp/migrations/006_qr_scans.sql`
- `dp/migrations/012_composite_scan_attempts.sql`
- `dp/migrations/014_campaign_referral_links.sql`
- `dp/migrations/070_distribution_route_referral_links.sql`
- `services/referral_code.py`
- `services/composite_code_service.py`
- `services/campaign_service.py`
- `services/distribution/distributor_portal_service.py`
- `apps/api/routers/referrals.py`
- `apps/api/routers/campaigns.py`
- `apps/api/routers/composite_codes.py`
- `apps/api/routers/distribution/distributor_portal.py`

## Current Link/Code Sources

| Source type | Current source truth | Current identity | Current operations |
| --- | --- | --- | --- |
| `REFERRAL_CODE` | `referrer_codes` | `referral_code`, `referrer_code_id`, `referrer_ucn_hash` | Issue and resolve through referral service. |
| `CAMPAIGN_CODE` | `marketing_campaigns.campaign_code`; `campaign_attributions` after validation | `campaign_code`, then `campaign_track_id` | Resolve/validate and create a campaign track. |
| `CAMPAIGN_REFERRAL_LINK` | `campaign_referral_links` | `campaign_track_id`, `referral_track_id` | Bridge a validated campaign track to a referral track. |
| `ROUTE_REFERRAL_LINK` | `distribution_route_referral_links` | `route_id`, `referral_track_id` | Link an accepted distributor route to a referral track; current status is `ACTIVE` or `VOIDED`. |
| `COMPOSITE_CODE` | `services/composite_code_service.py` | `composite_code` | Interim validation path that passes the same code to campaign and referral validators. |

The canonical contract should treat these as source-specific implementations of one platform concept: a traceable distribution link/code that can resolve into campaign, participant, attribution, and outcome evidence.

## Contract Summary

Recommended future service name: `link_code_service`.

Recommended first read/write contract:

```text
issue_link_code(
  *,
  tenant_code: str,
  source_type: LinkCodeSourceType,
  campaign_code: str | None = None,
  participant_type: str | None = None,
  participant_ref: str | None = None,
  route_id: str | None = None,
  metadata: dict | None = None,
  idempotency_key: str | None = None,
) -> LinkCodeResult

resolve_link_code(
  *,
  tenant_code: str | None,
  code_or_ref: str,
  source_hint: LinkCodeSourceType | None = None,
  attributes: dict | None = None,
) -> LinkCodeResolution

inspect_link_code(
  *,
  tenant_code: str,
  link_code_id: str | None = None,
  code_or_ref: str | None = None,
  include_evidence: bool = True,
) -> LinkCodeResult

void_link_code(
  *,
  tenant_code: str,
  link_code_id: str,
  actor_identity: dict,
  reason: str,
  idempotency_key: str,
) -> LinkCodeResult
```

TASK-009 does not implement these methods. They define the shape a later wrapper service should follow.

## Canonical Source Types

| Canonical type | Maps to | Notes |
| --- | --- | --- |
| `REFERRAL_CODE` | `referrer_codes.referral_code` | Shareable code issued to a referrer/advocate. |
| `CAMPAIGN_CODE` | `marketing_campaigns.campaign_code` | Campaign definition code that creates `campaign_track_id` after validation. |
| `CAMPAIGN_REFERRAL_LINK` | `campaign_referral_links` | Non-shareable bridge between a campaign interaction and referral journey. |
| `ROUTE_REFERRAL_LINK` | `distribution_route_referral_links` | Distributor route-to-referral attribution link. |
| `COMPOSITE_CODE` | `validate_composite_code` | Current interim validator; not a durable source table. |

## Canonical Status Mapping

| Canonical status | Source mapping | Meaning |
| --- | --- | --- |
| `ISSUED` | Existing `referrer_codes` row; existing campaign code before validation | Code exists and can be presented or resolved subject to source rules. |
| `ACTIVE` | `distribution_route_referral_links.link_status = 'ACTIVE'`; active campaign/referral source evidence | Link is usable or currently binds attribution. |
| `RESOLVED` | Successful referral validation creates `referral_track_id`; campaign validation creates `campaign_track_id` | Code was resolved into a track/interaction. |
| `LINKED` | `campaign_referral_links` row or active route referral link | Existing track was joined to campaign or route attribution. |
| `VOIDED` | `distribution_route_referral_links.link_status = 'VOIDED'` | Link should not be used for active attribution. |
| `EXPIRED` | Campaign date/window checks fail; future explicit link expiry | Source evidence says code/link is past its usable window. |
| `INVALID` | Missing, malformed, tenant mismatch, inactive campaign, or source-specific failure | Code/link cannot be resolved. |
| `UNKNOWN` | Source table unavailable or source relationship inconsistent | Contract cannot make a reliable decision. |

Current referral codes do not have a persisted status field. Current campaign/referral bridge links do not have a status field. A future wrapper must derive those statuses from source evidence and avoid inventing persisted state unless a later schema task adds it.

## Required Canonical Output

Recommended response envelope:

```json
{
  "link_code_id": "source-qualified-id",
  "source_type": "ROUTE_REFERRAL_LINK",
  "source": "distribution_route_referral_links",
  "tenant_code": "FNB",
  "status": "ACTIVE",
  "code": null,
  "campaign": {
    "campaign_code": "FNB-GOLD-SUMMER-ABCD1234",
    "campaign_track_id": null
  },
  "participant": {
    "participant_type": "DISTRIBUTOR",
    "participant_ref": "DIST-INSURANCE-ADVOCATE",
    "source": "distribution_distributors"
  },
  "attribution": {
    "referral_track_id": "uuid",
    "route_id": "uuid",
    "opportunity_id": "uuid"
  },
  "metadata": {},
  "evidence": {},
  "created_at": "ISO-8601 timestamp",
  "updated_at": "ISO-8601 timestamp"
}
```

The API layer may use camelCase if route conventions require it. The service contract should preserve source field names in `evidence`.

## Source-Specific Contracts

### `REFERRAL_CODE`

Issue:

- Current service: `get_or_create_referrer_code`.
- Current route: `POST /referrals/codes`.
- Required identity: partner credential via `require_partner_key`.
- Required inputs: `referrer_ucn`, `tenant`, `sticker`, `segment`, `accepted_terms`.
- Current idempotency behavior: returns the existing code for `(tenant_code, sticker, referrer_ucn_hash)` when found.
- Current duplicate protection: `referral_code`, `gaming_handle`, and `referrer_ucn_hash` are unique in schema, while service lookup is tenant/sticker/hash scoped.

Resolve:

- Current service: `validate_referral_code`.
- Current route: `POST /public/referrals/validate`.
- Required inputs: `tenant_code`, `referral_code`, `accepted_terms`.
- Current result: creates `referral_instances.referral_track_id` and writes a validated QR scan row when logging succeeds.
- Current failures include missing tenant/code, missing accepted terms, alias validation failure, and code not found.

Contract notes:

- Raw `referrer_ucn` and raw `referee_ucn` are internal-sensitive.
- Public surfaces should expose `referral_code`, `referral_track_id`, safe alias, and safe status only.
- Validation is a mutating resolve operation because it creates a referral instance.

### `CAMPAIGN_CODE`

Issue:

- Current service: `create_campaign`.
- Current route: `POST /campaigns`.
- Current code generation uses tenant, segment, campaign name, and a UUID suffix when `campaign_code` is not supplied.
- Current admin route requires `require_admin_key`.

Resolve:

- Current service: `validate_campaign_and_create_track`.
- Current public route: `POST /campaigns/validate`.
- Current result: creates `campaign_attributions.campaign_track_id` when campaign is valid.
- Current blockers include missing code, campaign not found, tenant mismatch, inactive campaign, not started, and expired.

Contract notes:

- `campaign_code` is stable campaign definition identity.
- `campaign_track_id` is the post-validation campaign interaction identity.
- A future link/code wrapper must not treat campaign definition status as the same thing as a link status.

### `COMPOSITE_CODE`

Current service: `validate_composite_code`.

Current behavior:

- Normalizes `composite_code`.
- Derives tenant from `TENANT-...` format if explicit tenant is missing.
- Calls campaign validation and referral validation with the same code.
- Returns combined campaign and referral validation payloads.

Contract notes:

- This is explicitly interim behavior in the current service.
- The canonical contract should treat `COMPOSITE_CODE` as a compatibility source, not as the target durable format.
- A later implementation may split composite codes into explicit campaign and referral components, but TASK-009 does not authorize that change.

### `CAMPAIGN_REFERRAL_LINK`

Current source: `campaign_referral_links`.

Current behavior:

- Links `campaign_track_id` to `referral_track_id`.
- Enforces one referral journey maps to one campaign journey with `uq_campaign_referral_links_referral`.
- Uses composite primary key `(campaign_track_id, referral_track_id)`.
- Has no explicit status, metadata, tenant, or void fields.

Contract notes:

- This is bridge evidence, not a shareable code.
- Tenant should be derived through joined campaign/referral evidence in a future inspect service.
- Voiding is not currently supported by source schema.

### `ROUTE_REFERRAL_LINK`

Current service: `link_portal_referral_to_route`.

Current route: `POST /distribution/portal/offers/{route_id}/referrals`.

Current behavior:

- Requires distributor portal access through `require_admin_partner_or_distributor_key`.
- Enforces tenant and distributor scope with `require_distributor_scope`.
- Verifies the route belongs to the tenant and distributor.
- Allows linking only when route status is `ACCEPTED`.
- Verifies the referral track belongs to the same tenant and distributor code.
- Rejects linking a referral track to a different active route.
- Inserts or reactivates `(route_id, referral_track_id)` with `link_status = 'ACTIVE'`.

Contract notes:

- Current schema supports `ACTIVE` and `VOIDED`, but no current route/service was identified for voiding.
- `metadata` is available and should preserve source-specific attribution evidence.
- Route links are distributor attribution evidence and should be inspected with opportunity and route context.

## Required Operations

| Operation | Requirement |
| --- | --- |
| Issue | Must validate auth, tenant scope, participant scope, source-specific required fields, duplicate/idempotency behavior, and safe response. |
| Resolve | Must validate code/ref, tenant source, source status/window, accepted terms where applicable, and return track IDs/evidence. |
| Inspect | Must be read-only, tenant-scoped, and return source evidence without exposing raw UCN or internal-only provider details. |
| Void | Must require authenticated actor, reason, idempotency key, audit evidence, and source support for voiding. |

## Idempotency And Duplicate Handling

| Operation | Current behavior | Future requirement |
| --- | --- | --- |
| Referral code issue | Existing row returned for tenant/sticker/referrer hash. | Keep idempotent issue behavior; add explicit idempotency key only if the future API cannot rely on natural key. |
| Referral code resolve | Creates a new referral instance per validation. | Treat as mutating; avoid accidental duplicate journey creation in future public APIs. |
| Campaign code issue | Campaign code is unique at campaign definition level. | Preserve duplicate detection and return 409 for conflicting supplied codes in future wrapper routes. |
| Campaign code resolve | Creates a new campaign track per validation. | Treat as mutating; emit track evidence clearly. |
| Route referral link issue/link | Upserts same route/referral pair and rejects another active route for same referral track. | Keep one active route attribution per referral track unless future business rules change explicitly. |
| Void | Route-link schema supports `VOIDED`; service route not identified. | Future void must be idempotent and audited. |

## Auth And Tenant Rules

- Public referral validation remains pre-auth but must validate request tenant and expose only safe fields.
- Partner referral-code issue must derive tenant from partner identity.
- Campaign create remains admin-only; campaign validation remains public/validation-oriented unless future API packaging changes it.
- Distributor route referral linking must enforce tenant and distributor scope.
- Admin/operator inspect APIs should use the narrowest admin helper for the domain and explicit tenant filters.
- Future public/partner APIs should use external identifier boundaries from TASK-048 where possible and resolve them to internal `tenant_code` before service calls.

## Error Contract Direction

Future link/code APIs should use:

| Status | Use |
| --- | --- |
| 400 | Invalid source type, invalid status transition, accepted terms missing, or unsupported operation for source. |
| 401 | Missing or invalid credential where auth is required. |
| 403 | Authenticated caller lacks tenant, participant, or operation scope. |
| 404 | Code/link/source evidence not found or inaccessible. |
| 409 | Duplicate or conflicting active link/code relationship. |
| 422 | Malformed request body or invalid required field shape. |
| 500 | Unexpected failure only; do not expose secret/config/source internals. |

## Evidence And Privacy Rules

Canonical inspect responses should include evidence references for:

- source table and source type
- tenant scope
- campaign code and campaign track where available
- participant family and source key
- referral track ID where available
- route ID and opportunity ID for route links
- source status and timestamps
- metadata, with unsafe fields redacted

Canonical responses must not expose:

- raw `referrer_ucn`
- raw `referee_ucn`
- internal secret values
- private partner/client token material
- provider payloads or audit internals unless an operator-only route explicitly requires them

## Gaps For Later Implementation

- No single `link_code_service` exists yet.
- No canonical persisted `link_code_id` exists.
- Referral codes have no status/void/expiry fields.
- Campaign/referral bridge links have no tenant/status/metadata/void fields.
- Route referral links support `VOIDED` in schema, but no current void route/service was identified.
- Composite-code validation is explicitly interim and does not parse independent campaign/referral components.
- Current resolve operations can create track rows; future public APIs must make this mutation explicit and test duplicate behavior.

## Future Tests

Later implementation should add or update tests for:

- referral code issue idempotency
- referral code resolve creates one expected referral track per valid request
- missing accepted terms
- invalid/missing referral code
- campaign code resolve blocked by tenant mismatch, inactive, not started, expired
- composite-code compatibility behavior
- route referral link requires accepted route
- route referral link rejects cross-tenant or wrong distributor referral tracks
- route referral link rejects conflicting active route for the same referral track
- route referral link void idempotency once a void command exists
- inspect redacts raw UCN and secret/token material
- role-specific auth and tenant/participant isolation

## Non-Goals

TASK-009 does not implement a canonical link/code service.

TASK-009 does not add issue, inspect, resolve, or void routes.

TASK-009 does not change referral, campaign, route, attribution, funding, fulfilment, settlement, audit, auth, permission, tenant, or data-isolation behavior.

TASK-009 does not start TASK-010 or define the outcome trace response contract.

TASK-009 does not create, rename, or migrate schema fields.

TASK-009 does not change the current composite-code format or generation behavior.

## Validation Notes

This contract is based on static repository inspection only. No live database, production data, or runtime credentials were used.

Current source truth is sufficient to define a canonical wrapper contract, but not sufficient to implement a unified persisted link/code table inside TASK-009.
