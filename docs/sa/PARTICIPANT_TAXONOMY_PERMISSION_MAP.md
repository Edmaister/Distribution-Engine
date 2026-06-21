# Participant Taxonomy And Permission Map

Status: Accepted for TASK-008 on 2026-06-22.

## Purpose

TASK-008 defines the current and target participant language for DLaaS. It maps referrers, distributors, partners, producers/sponsors, customers/consumers, and operators to current tables, services, routes, auth claims, and permission boundaries.

This is a mapping document only. It does not implement a participant service, participant table, migration, route, permission helper, auth change, role rename, or frontend workspace change.

## Source Documents And Code

- `docs/product/DLAAS_TARGET_STATE.md`
- `docs/sa/TENANT_IDENTIFIER_BOUNDARY_DECISION.md`
- `docs/sa/TENANT_ACCOUNT_BOUNDARY_MAP.md`
- `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`
- `docs/sa/CAMPAIGN_OPPORTUNITY_LIFECYCLE_MAP.md`
- `docs/sa/CAMPAIGN_READINESS_SERVICE_CONTRACT.md`
- `docs/API_PERMISSION_MATRIX.md`
- `dp/migrations/001_init.sql`
- `dp/migrations/057_sponsor_wallets.sql`
- `dp/migrations/059_funding_contracts.sql`
- `dp/migrations/064_distribution_distributors.sql`
- `dp/migrations/067_distribution_opportunities.sql`
- `dp/migrations/077_partner_seam.sql`
- `utils/security.py`
- `utils/permissions.py`
- `apps/api/routers/session.py`
- `apps/api/routers/referrals.py`
- `apps/api/routers/consumer_experience.py`
- `apps/api/routers/sponsor_experience.py`
- `apps/api/routers/sponsor_portal_billing.py`
- `apps/api/routers/distribution/distributor_portal.py`
- `apps/api/routers/partner_seam.py`
- `services/referral_code.py`
- `services/distribution/distributor_service.py`
- `services/partner_seam_service.py`
- `services/marketplace_funding/*`

## Taxonomy Summary

DLaaS should use `participant` as an umbrella product term, not as a current database table.

Current backend truth is role-specific:

| Participant family | Current canonical source | Current identity key | Current auth role | Notes |
| --- | --- | --- | --- | --- |
| Operator | Auth/session identity only | `role`, `tenant_code = INTERNAL` | `ADMIN`, `FINANCE_ADMIN`, `DISTRIBUTION_ADMIN`, `SYSTEM_ADMIN` | Cross-tenant operational roles; no operator profile table was identified. |
| Partner integration client | `partner_clients`, `partner_access_tokens` | `client_id`, `tenant_code`, `scopes` | `PARTNER` | Tenant-scoped integration credential; bearer-token sessions are client-scoped. |
| Producer / sponsor | Funding, billing, and opportunity records | `sponsor_code`; auth claim uses `producer_code` | `PRODUCER`, plus `PARTNER` and `ADMIN` where allowed | No standalone producer table was identified; current sponsor identity is derived from sponsor/funding records. |
| Distributor | `distribution_distributors` | `distributor_code`, `tenant_code` | `DISTRIBUTOR`, plus `PARTNER` and `ADMIN` where allowed | First-class marketplace participant with lifecycle status and portal scope checks. |
| Referrer / advocate | `referrer_codes` | `referrer_ucn_hash`, `referral_code`, `gaming_handle`; raw `referrer_ucn` is internal-sensitive | No dedicated `REFERRER` role | Referral participant created when a code is issued. Raw UCN must not be exposed in public contracts. |
| Customer / consumer / referred user | `referral_instances` and journey/progress evidence | `referral_track_id`, `referee_ucn_hash`, optional alias | `CONSUMER` for consumer workspace access | No canonical customer table was identified. Consumer role currently proves tenant access, not a durable customer membership. |

The target participant model should wrap these sources; it should not collapse them into one table until a later implementation task proves the schema boundary.

## Current Auth Claims And Roles

`utils/security.py` currently produces identity dictionaries with:

- `authenticated`
- `role`
- `tenant_code`
- `tenant`
- `auth_source`
- optional `subject`
- optional `producer_code`
- optional `distributor_code`
- optional `client_id`
- optional `scopes`

Current role families:

| Role | Current use | Tenant boundary |
| --- | --- | --- |
| `ADMIN` | Platform admin and break-glass operations. | `INTERNAL`; can cross tenant by design. |
| `FINANCE_ADMIN` | Funding, billing, settlement, FX, and finance operations. | `INTERNAL`; explicit tenant filters required. |
| `DISTRIBUTION_ADMIN` | Distributor, opportunity, route, channel, and distribution governance operations. | `INTERNAL`; explicit tenant filters required. |
| `SYSTEM_ADMIN` | Enterprise events, DLQ, replay, audit, runtime health, and system operations. | `INTERNAL`; explicit tenant filters required. |
| `PARTNER` | Tenant-bound integration and broad tenant workspace access. | Derived from partner key, JWT, or partner access token. |
| `PRODUCER` | Sponsor/producer workspace. | Tenant-bound and optionally bound to `producer_code`. |
| `DISTRIBUTOR` | Distributor workspace. | Tenant-bound and optionally bound to `distributor_code`. |
| `CONSUMER` | Consumer/customer journey workspace. | Tenant-bound; no durable customer claim was identified. |
| Worker | Internal async processing. | Worker secret plus event payload scope; not a user participant. |
| Public | Pre-auth referral validation. | No privileged identity; request validation only. |

## Permission Helpers

Current permission helpers are the contract for implementation tasks until the account/membership model is built.

| Helper | Allowed identities | Scope rule |
| --- | --- | --- |
| `require_admin_key` | `ADMIN` | Cross-tenant platform admin. |
| `require_finance_admin_key` | `ADMIN`, `FINANCE_ADMIN` | Finance routes; explicit tenant filters. |
| `require_distribution_admin_key` | `ADMIN`, `DISTRIBUTION_ADMIN` | Distribution routes; explicit tenant filters. |
| `require_system_admin_key` | `ADMIN`, `SYSTEM_ADMIN` | System/replay/audit routes; explicit tenant filters. |
| `require_partner_key` | `ADMIN`, `PARTNER` | Partner credential resolves tenant. |
| `require_admin_or_partner_key` | `ADMIN`, `PARTNER` | Admin can cross tenant; partner is tenant-scoped. |
| `require_partner_identity` | `ADMIN`, `PARTNER` and partner access tokens | Partner bearer token resolves `tenant_code`, `client_id`, and `scopes`. |
| `require_admin_partner_or_producer_key` | `ADMIN`, `PARTNER`, `PRODUCER` | Producer routes must call `require_producer_scope` for `producer_code`/`sponsor_code`. |
| `require_admin_partner_or_distributor_key` | `ADMIN`, `PARTNER`, `DISTRIBUTOR` | Distributor routes must call `require_distributor_scope`. |
| `require_admin_partner_or_consumer_key` | `ADMIN`, `PARTNER`, `CONSUMER` | Consumer routes must call `require_consumer_scope`; current check is tenant-scoped. |
| `require_session_key` | Admin, scoped admins, partner, producer, distributor, consumer | Session introspection only; returns public identity and workspace access. |

`utils/permissions.py` adds the current tenant and role-specific claim guards:

- `require_tenant_scope`
- `require_partner_tenant_scope`
- `require_producer_scope`
- `require_distributor_scope`
- `require_consumer_scope`

Future participant APIs should reuse or replace these helpers only through a deliberate auth task. TASK-008 does not change them.

## Participant Source Mapping

### Operator

Current source:

- `utils/security.py`
- `apps/api/routers/session.py`
- `docs/API_PERMISSION_MATRIX.md`

Current facts:

- Operators are auth roles, not domain participants in a table.
- `ADMIN` is broad platform admin.
- `FINANCE_ADMIN`, `DISTRIBUTION_ADMIN`, and `SYSTEM_ADMIN` are narrower operational roles.
- Session workspaces map these roles to admin, funding, settlement, distribution, event, audit, and health areas.

Boundary:

- Operators may act across tenants only through admin routes with explicit tenant filters.
- Mutating money, replay, settlement, fulfilment, distribution, or audit actions must follow the audit/retry standard.

### Partner Integration Client

Current source:

- `partner_clients`
- `partner_access_tokens`
- `partner_webhook_subscriptions`
- `partner_webhook_deliveries`
- `services/partner_seam_service.py`
- `apps/api/routers/partner_seam.py`

Current facts:

- `partner_clients.client_id` is the current partner integration credential identifier.
- Partner clients are tenant-scoped by `tenant_code`.
- Client status is constrained to `ACTIVE`, `SUSPENDED`, and `REVOKED`.
- Partner access tokens carry `client_id`, `tenant_code`, and `scopes`.
- Partner API-key sessions can be tenant-scoped without a `client_id`; bearer-token sessions are client-scoped.

Boundary:

- A partner client is not automatically a distributor, producer, sponsor, referrer, or customer.
- Partner credentials may operate tenant-scoped surfaces where allowed by route helper and scope checks.
- Future public API work should prefer external identifier boundaries from TASK-048 rather than exposing internal `tenant_code` as the primary integration identifier.

### Producer / Sponsor

Current source:

- `distribution_opportunities.sponsor_code`
- `sponsor_wallets`
- `funding_contracts`
- `sponsor_invoices`
- sponsor billing/payment tables
- sponsor and producer experience routes
- funding and marketplace funding services

Current facts:

- Current business records use `sponsor_code`.
- Current auth identity uses optional `producer_code`.
- Producer workspace routes compare `producer_code` to the requested sponsor/producer code through `require_producer_scope`.
- Sponsor portal billing routes currently allow admin or partner tenant access and then verify returned invoice/contract/receipt ownership by `tenant_code` and `sponsor_code`.
- No standalone `producers` or `sponsors` registry table was identified beyond wallet, funding contract, billing, and opportunity records.

Boundary:

- `producer_code` in identity should be treated as the auth claim that scopes a producer user.
- `sponsor_code` is the current domain key used by funding, billing, opportunity, commission, and reporting records.
- Future implementation should explicitly decide whether producer and sponsor remain aliases or become separate participant subtypes.

### Distributor

Current source:

- `distribution_distributors`
- `distribution_offer_routes`
- `distribution_route_referral_links`
- distributor wallet/ledger and commission records
- `services/distribution/distributor_service.py`
- `apps/api/routers/distribution/distributor_portal.py`

Current facts:

- `distribution_distributors` is the current first-class distributor registry.
- The stable distributor key is `(tenant_code, distributor_code)`.
- Current status values are service/state-map owned as `ONBOARDING`, `ACTIVE`, `SUSPENDED`, and `TERMINATED`.
- Distributor portal routes call `require_distributor_scope` so a `DISTRIBUTOR` identity can only operate its own `distributor_code`; `PARTNER` and `ADMIN` can operate where route policy allows.
- Distributor route and link records are offer/link state, not the distributor identity itself.

Boundary:

- Distributor participant identity should be resolved from `distribution_distributors` before route/link/commission work.
- Distributor portal APIs must keep tenant and distributor checks together.
- Distribution admin operations should use `require_distribution_admin_key` or an explicitly justified broader helper.

### Referrer / Advocate

Current source:

- `referrer_codes`
- `referral_instances`
- `services/referral_code.py`
- referral, leaderboard, mission, badge, and reward-summary services

Current facts:

- `referrer_codes` is the current referrer registry.
- It stores raw `referrer_ucn`, internal deterministic `referrer_ucn_hash`, public `gaming_handle`, and public/shareable `referral_code`.
- `referral_instances.referrer_ucn` preserves the referrer for each referral outcome.
- There is no dedicated `REFERRER` auth role.
- Referral-code issue currently requires partner auth; public validation is pre-auth and validates request payload.

Boundary:

- Raw UCN is internal-sensitive and must not become a public participant identifier.
- External/API surfaces should prefer safe handles, referral codes, referral-track IDs, or future external participant references where appropriate.
- Referrer is not the same as distributor unless a later link/code task explicitly maps distributor referral links to referral participants.

### Customer / Consumer / Referred User

Current source:

- `referral_instances`
- `referral_progress_events`
- journey/progress services
- consumer experience and reward-summary routes

Current facts:

- The current customer/referred user is represented inside referral and progress records, not a canonical customer table.
- `referral_track_id` is the current golden thread for a referral instance.
- `referee_ucn_hash` is the internal lookup key where UCN capture occurs.
- `referee_alias` and `referee_alias_normalized` provide optional alias context.
- `CONSUMER` auth exists for consumer workspace access, but no durable consumer membership/customer claim beyond tenant scope was identified.

Boundary:

- Consumer/customer APIs must not expose raw internal UCN values unless an existing route already explicitly does so and is covered by current tests.
- Future participant implementation should introduce a customer-safe lookup/read model before broad public customer APIs.
- Consumer workspace access is currently tenant-scoped; tighter customer-specific identity is a follow-up implementation gap.

## Route Family Mapping

| Route family | Participant family | Current helper | Extra scope check |
| --- | --- | --- | --- |
| `/auth/session` | All authenticated role families | `require_session_key` | Session response filters public identity fields. |
| `/referrals/*` | Partner issuing/capturing referrer/referee data | `require_partner_key` | Tenant comes from partner identity. |
| `/public/referrals/validate` | Public referred-user validation | Request validation | Tenant is validated; no privileged identity. |
| `/v1/experience/consumer` | Consumer/customer/referrer journey view | `require_admin_partner_or_consumer_key` | `require_consumer_scope`; currently tenant-scoped. |
| `/v1/experience/sponsor` | Producer/sponsor workspace | `require_admin_partner_or_producer_key` | `require_producer_scope`. |
| `/v1/tenants/{tenant_code}/sponsors/{sponsor_code}/billing/*` | Sponsor billing portal | `require_admin_or_partner_key` | Tenant access plus returned-record sponsor ownership checks. |
| `/distribution/portal/*` | Distributor workspace | `require_admin_partner_or_distributor_key` | `require_distributor_scope`. |
| `/admin/distribution/*` | Distributor/opportunity/route operations | `require_distribution_admin_key` in current admin distribution routes | Explicit tenant filters; audit where mutating. |
| `/partner/*` and partner seam routes | Partner integration client | `require_partner_identity` or partner seam token checks | Client-scoped bearer tokens include `client_id`. |
| Finance/funding/settlement admin routes | Producer/sponsor money operations and operator workflows | `require_finance_admin_key` | Explicit tenant and sponsor filters. |
| System/admin replay/audit routes | Operator workflows | `require_system_admin_key` or narrower admin helper | Audit/replay actions must preserve actor identity. |

## Target Contract Direction

Future participant-facing service or API contracts should:

- Resolve external identifiers to internal `tenant_code` before calling domain services.
- Preserve current role-specific keys: `client_id`, `producer_code`/`sponsor_code`, `distributor_code`, `referral_track_id`, and safe referrer/customer references.
- Keep `tenant_code` internal except for current backward-compatible routes.
- Keep participant family explicit in responses; do not use a generic participant row without `participant_type` and source evidence.
- Return source evidence and missing-evidence categories for operator views.
- Use narrow auth helpers and role-specific scope checks.
- Treat public/customer responses as safe derived views.

Recommended future generic participant envelope:

```json
{
  "participant_type": "DISTRIBUTOR",
  "tenant_code": "FNB",
  "source": "distribution_distributors",
  "source_id": "DIST-INSURANCE-ADVOCATE",
  "display_name": "Insurance Advocate",
  "status": "ACTIVE",
  "evidence": {}
}
```

This envelope is a target contract shape only. TASK-008 does not create this API or schema.

## Permission Rules For Future Tasks

1. Use the narrowest existing helper for the route family.
2. Derive tenant scope from identity for non-admin routes.
3. Allow explicit tenant filters only for admin/operator routes or current backward-compatible routes.
4. Enforce `producer_code`/`sponsor_code` and `distributor_code` where the route is role-specific.
5. Do not let `PARTNER` imply a specific producer, distributor, referrer, or consumer unless a route explicitly authorizes broad tenant operation.
6. Do not expose raw UCN values as public participant identifiers.
7. Do not collapse reward, commission, funding, fulfilment, settlement, or audit actors into one participant type without preserving source evidence.
8. Mutating money, distribution, replay, settlement, fulfilment, or audit actions must retain authenticated actor identity for audit.

## Missing Canonical Entities

The following are not current first-class schema entities:

- `participants`
- `participant_memberships`
- `producers`
- `sponsors`
- `customers`
- `consumers`
- `operators`
- `referrer_profiles`

Current code can still represent these concepts through existing role-specific tables and claims. Future implementation should add read models or registries only through separate tasks with migrations and tests.

## Follow-Up Implementation Tasks

Later tasks should decide and implement:

- canonical participant read service over existing source tables
- customer-safe identity/read model
- whether producer and sponsor remain aliases or become separate entities
- partner client scope model beyond tenant/client/scopes
- optional referrer profile read model that avoids raw UCN exposure
- permission-matrix updates for new participant APIs
- participant isolation tests covering partner, producer, distributor, consumer, and admin paths

## Non-Goals

TASK-008 does not start TASK-009 or define the canonical link/code contract.

TASK-008 does not implement participant APIs, participant tables, auth helpers, role changes, or migrations.

TASK-008 does not change campaign readiness, opportunity lifecycle, attribution, funding, fulfilment, settlement, audit, tenant, or data-isolation behavior.

TASK-008 does not rename existing `tenant_code`, `sponsor_code`, `producer_code`, `distributor_code`, `referrer_ucn`, `referral_track_id`, `client_id`, or referral-code fields.

## Validation Notes

This mapping is based on static repository inspection only. No live database, production data, or runtime credentials were used.

Current source truth is sufficient to document participant taxonomy and permission boundaries, but not sufficient to implement a single canonical participant table safely in TASK-008.
