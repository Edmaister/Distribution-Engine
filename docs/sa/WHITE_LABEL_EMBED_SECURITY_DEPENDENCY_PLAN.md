# White-Label And Embed Security Dependency Plan

Status: Accepted for TASK-026 on 2026-06-22.

## Purpose

TASK-026 defines the future white-label, embed, custom-domain, tenant-branding, SDK, and allowed-origin security plan for DLaaS.

This is a dependency-gated plan only. It does not add schema, migrations, API routes, frontend screens, embed clients, SDKs, CORS behavior, domain verification, token issuance, tenant branding configuration, billing changes, or live database checks.

## Problem Statement

DLaaS target state includes tenant-branded and embeddable partner/customer UX. Current source maps show no first-class tenant branding, custom domain, embed client, SDK token, or allowed-origin model. Existing frontend brand notes are product styling notes, not a tenant-owned white-label configuration model.

White-label and embed features can expose public surfaces, customer status, partner status, campaign links, tenant identity, and potentially billing or support information. They must not be implemented before tenant isolation, public API contracts, partner/customer-safe statuses, account membership, credential lifecycle, and origin/token controls are mature.

## Decision

White-label/embed work is blocked from implementation until the dependency gates in this document are satisfied.

Future implementation may introduce tenant branding, portal configuration, custom domains, allowed origins, embed clients, scoped embed tokens, and SDK candidates only as additive primitives. These primitives must preserve tenant isolation, safe status boundaries, public/internal API separation, reporting redaction, SaaS/sponsor billing separation, and audit/security policy.

## Current Source Truth

| Source | Current relevance |
| --- | --- |
| `docs/product/DLAAS_TARGET_STATE.md` | Defines TS-18 as dependent on mature isolation and status APIs. |
| `docs/sa/CAPABILITY_GAP_MATRIX.md` | Marks white-label/embed as missing and dependent on tenant isolation and safe portal APIs. |
| `docs/API_PERMISSION_MATRIX.md` | Defines current API family auth, tenant scope, safe errors, and credential guardrails. |
| `docs/sa/API_SURFACE_MAP.md` | States public APIs, webhooks, onboarding, SaaS setup, and white-label/embed surfaces should use external tenant references. |
| `docs/sa/TENANT_SAFE_ANALYTICS_REPORTING_CONTRACT.md` | Defines reporting redaction, export, and tenant-safe rules for any embedded analytics. |
| `docs/sa/SAAS_USAGE_BILLING_SEPARATION_MODEL.md` | Defines SaaS usage/billing boundaries that white-label usage may later consume. |
| `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md` | Defines audit, idempotency, retry, and safe failure rules for sensitive config writes. |

## Non-Goals

TASK-026 does not:

- implement tenant branding or theme storage;
- implement custom domain verification;
- implement CORS or allowed-origin enforcement;
- issue embed tokens or SDK keys;
- add public white-label or embed APIs;
- add frontend portals, iframes, scripts, widgets, or SDK packages;
- expose partner/customer status APIs;
- change SaaS billing, sponsor billing, analytics, funding, fulfilment, settlement, audit, webhook, tenant, or data-isolation behavior.

## Dependency Gates

White-label/embed implementation may begin only after these gates are satisfied:

| Gate | Required readiness | Why it matters |
| --- | --- | --- |
| Tenant/account ownership | Account, tenant, environment, membership, and external tenant references are implemented or explicitly scoped for the task. | Branding and domains must belong to the right account and tenant. |
| Public API contract | Public/partner/customer APIs expose stable tenant-scoped contracts and safe errors. | Embeds must not call broad internal/admin routes. |
| Partner/customer safe status | Role-safe status APIs are implemented for the intended audience. | Embeds must not expose raw provider, settlement, audit, DLQ, or private identifier details. |
| Credential lifecycle | API credentials or embed clients have scoped lifecycle, rotation, revocation, audit, and usage attribution. | Embeds need revocable trust boundaries. |
| Tenant-safe reporting | Any embedded analytics must follow approved dimensions, freshness, export, and redaction rules. | Embedded charts cannot leak cross-tenant or ledger-internal data. |
| SaaS usage/billing | Embed usage, SDK calls, custom domains, seats, and storage have a billing boundary if they are commercialized. | White-label usage must not be confused with sponsor utilisation billing. |
| Audit/security policy | Sensitive config writes, domain verification, token issuance, and origin changes have audit/idempotency rules. | Operators need proof and replay safety for security-sensitive changes. |

If any gate is missing, the implementation task must either stop or explicitly scope itself to a smaller safe prerequisite.

## Future Primitive Model

| Primitive | Purpose | Required boundary |
| --- | --- | --- |
| `tenant_branding` | Tenant-owned colors, logos, display names, copy preferences, and safe asset references. | Stored per tenant/account/environment; no executable content; asset scanning and size/type limits required. |
| `portal_config` | Role-specific portal feature flags and visible sections. | Must bind to role, tenant, participant, and safe status contracts. |
| `custom_domain` | Tenant-owned domain for hosted portals or links. | Requires DNS proof, TLS lifecycle, ownership verification, status, and audit. |
| `allowed_origin` | Browser origin allowed to embed or call public/partner surfaces. | Must be exact-origin scoped; wildcard rules need explicit approval and tests. |
| `embed_client` | Scoped client identity for widgets, iframe embeds, or SDKs. | Must have tenant, audience, scopes, allowed origins, expiry/rotation, and revocation. |
| `embed_token` | Short-lived token for a specific embed session or subject. | Must be signed, audience-bound, origin-bound where possible, tenant-scoped, and non-reusable beyond intended TTL. |
| `sdk_package` | Versioned client library for approved public APIs. | Must call stable APIs only and avoid embedding secrets in browser code. |
| `embed_usage_event` | Optional future usage event for billable embed/API/SDK consumption. | Must follow TASK-025 usage event and billing separation rules. |

These are future primitives, not current schema names.

## Branding Rules

Future tenant branding must:

- use tenant/account ownership from the account lifecycle model;
- keep `tenant_code` internal and expose external references where public;
- validate asset types, size, dimensions, and content safety;
- store references to assets rather than accepting raw executable HTML or scripts;
- support draft/active lifecycle and audit for publish/unpublish;
- preserve platform accessibility standards and safe fallback branding;
- prevent one tenant from reading or referencing another tenant's assets.

Branding configuration must not carry secrets, API keys, private identifiers, raw provider data, settlement details, or billing records.

## Custom Domain Rules

Future custom domain support must:

- require tenant/account ownership proof before activation;
- use exact domain records and DNS verification tokens;
- require TLS certificate lifecycle and renewal monitoring;
- reject domains already assigned to another tenant;
- track status such as `PENDING_VERIFICATION`, `ACTIVE`, `SUSPENDED`, `FAILED_VERIFICATION`, and `REVOKED` in a future contract before implementation;
- audit create, verify, activate, suspend, revoke, and delete actions;
- avoid exposing internal tenant identifiers through DNS records or public errors.

Custom domain errors must not confirm another tenant's ownership of a domain.

## Allowed-Origin And CORS Rules

Future allowed-origin enforcement must:

- use exact origins including scheme, host, and port where applicable;
- avoid broad wildcard origins for authenticated embeds;
- require HTTPS except for local/test development modes;
- bind origins to tenant/account and embed client;
- audit origin creation, removal, and status changes;
- return safe CORS and validation errors without leaking tenant existence;
- include regression tests for cross-tenant origin rejection and adjacent-role denial.

## Embed Client And Token Rules

Future embed clients must define:

- tenant/account scope;
- audience or surface, such as customer status, distributor portal, campaign card, reporting widget, or onboarding widget;
- allowed origins;
- scopes and role limits;
- expiry, rotation, and revocation behavior;
- usage attribution hooks;
- audit evidence for create, rotate, revoke, and permission changes.

Future embed tokens must be short-lived and scoped to:

- tenant or external tenant reference;
- viewer role or audience;
- subject reference where applicable;
- allowed origin or embed client;
- scopes;
- issued-at and expiry timestamps;
- correlation reference for audit/support.

Browser-visible embeds must never receive stored secrets, long-lived API keys, signing secrets, provider payloads, raw audit payloads, raw UCNs, private customer identifiers, or settlement internals.

## SDK Candidate Rules

SDK candidates may be considered only for stable public APIs. Candidate SDK families:

- JavaScript browser SDK for public link/code resolution and safe status widgets.
- Server-side SDK for partner event ingestion and webhook verification.
- Admin/operator SDK only after internal APIs are versioned and permission boundaries are stable.

SDKs must:

- avoid embedding secrets in browser packages;
- support idempotency keys for write operations where required;
- expose safe error envelopes;
- preserve tenant and participant scope;
- include versioning and deprecation policy;
- document retry behavior without causing duplicate money or fulfilment side effects.

## API Direction

TASK-026 does not add APIs. Future route families may include:

```text
GET /v1/white-label/config
POST /admin/white-label/branding
POST /admin/white-label/custom-domains
POST /admin/white-label/allowed-origins
POST /admin/embed-clients
POST /v1/embed/tokens
```

Implementation guardrails:

- Config writes require account/tenant admin authorization, idempotency, validation, and audit.
- Public reads must derive tenant from domain, credential, external tenant reference, or signed embed token.
- Public/embed surfaces must return safe status data only.
- Origin and domain validation failures must use safe errors.
- Rate limits must apply to public/embed token issuance and widget/API calls.
- Admin/operator routes must not be exposed as embed routes.

## Reporting And Billing Relationship

White-label/embed reporting must follow TASK-024:

- use tenant-safe dimensions and freshness indicators;
- avoid private identifiers, raw provider payloads, settlement internals, and raw audit payloads;
- treat embed/API/SDK usage as operational metrics unless tied to TASK-025 billing-grade usage events.

If embed usage is billable, it must follow TASK-025:

- immutable usage events;
- account/tenant/credential attribution;
- quota and plan boundaries;
- sponsor billing separation;
- safe exports and billing hooks.

## Security And Privacy Rules

White-label/embed surfaces must not expose:

- raw UCNs or private customer identifiers;
- raw provider payloads or provider failure bodies;
- settlement exception internals or provider settlement records;
- funding account internals or wallet internals outside authorized safe views;
- access tokens, signing secrets, API keys, credential hashes, or stored secrets;
- raw audit payloads, raw DLQ payloads, stack traces, SQL errors, or unrelated tenant data.

All public/embed responses must be designed as external-safe contracts, not trimmed versions of operator responses.

## Future Test Expectations

Future implementation tasks must add tests for:

- branding config validation and cross-tenant asset rejection;
- custom domain ownership, duplicate-domain rejection, verification, activation, suspension, and safe errors;
- allowed-origin exact matching, HTTPS enforcement, wildcard rejection, and cross-tenant leak prevention;
- embed client create/rotate/revoke audit;
- embed token expiry, audience, tenant, origin, and scope validation;
- public/embed auth failure, permission denial, and inaccessible subject behavior;
- safe status and redaction behavior for every embedded surface;
- rate limiting and quota behavior where applicable;
- SDK idempotency and safe retry behavior for write APIs.

## Follow-Up Implementation Tasks

Later tasks should:

- implement account/tenant membership and credential lifecycle before embed clients;
- implement role-safe partner/customer status APIs before exposing portal widgets;
- add tenant branding schema and validation as a standalone migration task;
- add custom domain and allowed-origin schema as a separate security-focused task;
- add embed client and short-lived token service only after origin/domain rules exist;
- build SDKs only after public API contracts and token scopes are stable;
- add usage metering for embed/SDK calls only after TASK-025 usage events are implemented.

## Readback Validation

TASK-026 readback should confirm that the plan defines tenant branding, custom domains, allowed origins, embed clients, SDK candidates, scoped tokens, auth/tenant validation, CORS/origin rules, rate limits, safe errors, idempotency for config writes, cross-tenant leak prevention, blockers, and future tests without adding schema, routes, services, frontend changes, billing changes, or money movement.
