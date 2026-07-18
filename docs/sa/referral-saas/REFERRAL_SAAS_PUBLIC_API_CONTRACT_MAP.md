# Referral SaaS Public API Contract Map

TASK ID: TASK-143

Product boundary: Referral Management and Campaign Attribution SaaS.

Status: Contract/map only. No runtime behavior, schema, route, auth helper,
OpenAPI, frontend, or test changes are made by this task.

## Boundary

This map defines how current referral, campaign, progress, status, reporting,
and operator routes should be packaged into a future versioned Referral SaaS
API. It separates current implementation facts from target product APIs.

Required boundary docs checked:

- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/API_PERMISSION_MATRIX.md`
- `docs/sa/API_SURFACE_MAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_CAMPAIGN_SETUP_READINESS_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_REFERRAL_CODE_ISSUE_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_WRAPPER_CONTRACT.md`

Source files inspected:

- `apps/api/main.py`
- `apps/api/routers/referrals.py`
- `apps/api/routers/campaigns.py`
- `apps/api/routers/progress.py`
- `apps/api/routers/admin_campaign_readiness.py`
- `apps/api/routers/admin_links.py`
- `apps/api/routers/admin_outcomes.py`
- `apps/api/routers/admin_analytics.py`
- `apps/api/routers/consumer_experience.py`
- `apps/api/routers/reward_summary.py`
- `apps/api/schemas/referrals.py`
- `apps/api/schemas/campaigns.py`
- `apps/api/schemas/progress.py`

## Purpose

Referral SaaS needs a stable public API contract before frontend IA and API
implementation work continue. The repository already has useful current routes,
but they are not packaged as one SaaS product surface.

This map answers:

1. Which current routes already support the product wedge?
2. Which future route families should wrap or compose those primitives?
3. What auth, tenant-scope, idempotency, error, and privacy rules must every
   future Referral SaaS API follow?

## Current Mounted Route Facts

Current route facts relevant to Referral SaaS:

| Capability | Current route | Current auth | Current source |
|---|---|---|---|
| Public referral validation | `POST /public/referrals/validate` | Public request validation | `apps/api/routers/referrals.py` |
| Referral code issue/reuse | `POST /referrals/codes` | Partner key | `apps/api/routers/referrals.py` |
| Referee UCN capture | `POST /referrals/referees/ucn` | Partner key | `apps/api/routers/referrals.py` |
| Campaign create | `POST /campaigns` | Admin key | `apps/api/routers/campaigns.py` |
| Campaign validation/track create | `POST /campaigns/validate` | Public request validation | `apps/api/routers/campaigns.py` |
| Campaign track status update | `PATCH /campaigns/tracks/{campaign_track_id}` | Partner key | `apps/api/routers/campaigns.py` |
| Campaign policy read | `GET /campaigns/{campaign_code}/policy` | Partner key | `apps/api/routers/campaigns.py` |
| Campaign policy upsert | `PUT /campaigns/{campaign_code}/policy` | Admin key | `apps/api/routers/campaigns.py` |
| Progress event ingestion | `POST /v1/progress` | Partner key | `apps/api/routers/progress.py` |
| Referrer progress summary | `GET /v1/referrers/{referrerUcn}` | Admin or partner key | `apps/api/routers/progress.py` |
| Consumer/referrer BFF | `GET /v1/experience/consumer` | Admin, partner, or consumer key | `apps/api/routers/consumer_experience.py` |
| Reward summary | `GET /v1/rewards/summary/*` | Admin or partner key | `apps/api/routers/reward_summary.py` |
| Campaign readiness | `GET /admin/campaigns/{campaign_code}/readiness` | Distribution admin key | `apps/api/routers/admin_campaign_readiness.py` |
| Link/code inspect | `GET /admin/links/inspect` | Distribution admin key | `apps/api/routers/admin_links.py` |
| Outcome trace | `GET /admin/outcomes/{referral_track_id}/trace` | Operator/admin session key | `apps/api/routers/admin_outcomes.py` |
| Tenant-safe analytics | `GET /admin/analytics/reports/{report_type}` | Admin analytics roles | `apps/api/routers/admin_analytics.py` |

Current route gaps:

- current public/partner routes still expose internal names such as
  `tenant_code`, `referrer_ucn`, and `referee_ucn`
- current admin/operator routes are not public SaaS APIs
- current reporting route is admin/internal and not Referral SaaS report-specific
- current safe-status route wrapper is not yet a focused Referral SaaS API
- current product API versioning is not unified

## Target API Principles

Future Referral SaaS APIs should follow these rules:

- use a versioned product namespace such as `/v1/referral-saas`
- resolve tenant/account scope from authenticated identity or safe external
  account reference, not caller-supplied internal `tenant_code`
- preserve shared services as the source of truth instead of duplicating
  referral, campaign, progress, trace, status, or reporting logic
- use camelCase in external payloads unless a route is explicitly internal
- return safe error envelopes with machine-readable code, safe message,
  correlation ID where available, and bounded details
- require idempotency keys for commands that may create, mutate, or enqueue
  durable state
- make reads side-effect free
- keep operator/admin evidence out of public customer/referrer responses
- never expose raw UCNs, provider payloads, audit payloads, DLQ payloads,
  secrets, tokens, signing material, funding internals, settlement internals, or
  raw worker errors

## Target Route Map

### Account And Setup

| Target route | Method | Current source/wrapper | Auth | Notes |
|---|---|---|---|---|
| `/v1/referral-saas/account` | `GET` | TASK-134 contract; future account wrapper | SaaS account admin/member | Not currently implemented as product route. |
| `/v1/referral-saas/account-setup/drafts` | `POST` | TASK-191 wrapper over `POST /admin/onboarding/drafts` | Admin/onboarding bridge first; future account setup role | Future wrapper contract only. Saves setup evidence, carries idempotency/audit posture, and must reject internal `tenant_code`. |
| `/v1/referral-saas/account-setup/validate` | `POST` | TASK-191 wrapper over `POST /admin/onboarding/validate` | Admin/onboarding bridge first; future account setup role | Future wrapper contract only. Validates setup evidence without saving or live actions. |
| `/v1/referral-saas/account-setup/readiness` | `GET` | TASK-191 wrapper over `GET /admin/onboarding/state` | Admin/onboarding bridge first; future account setup/member/support role | Future wrapper contract only. Read-only integrated readiness in product language. |
| `/v1/referral-saas/account-setup/drafts/{draftRef}/submit-for-review` | `POST` | TASK-191 wrapper over `POST /admin/onboarding/drafts/{draft_ref}/submit-for-review` | Admin/onboarding bridge first; future account setup submit role | Future wrapper contract only. Review handoff, not account activation or go-live. |
| `/v1/referral-saas/account-setup/drafts/{draftRef}/review-decision` | `POST` | TASK-191 wrapper over `POST /admin/onboarding/drafts/{draft_ref}/review-decision` | Operator/admin reviewer | Future wrapper contract only. Records review outcome, not account creation, invitation, tenant-link, or campaign activation. |
| `/v1/referral-saas/accounts/resolve` | `GET` | TASK-200 wrapper over account foundation resolver | Account reader/admin bridge | Implemented as safe account resolution from external references without exposing internal tenant code. |
| `/v1/referral-saas/accounts/membership-posture` | `GET` | TASK-209 membership posture wrapper | Account reader/admin bridge | Implemented as read-only membership posture. Does not invite users, create users, assign seats, write memberships, change auth claims, activate accounts, trigger go-live, or move money. |
| `/v1/referral-saas/accounts/from-draft` | `POST` | TASK-204 account creation wrapper over reviewed onboarding draft evidence | Account admin bridge | Implemented as guarded seeded write. Creates durable account foundation only; no tenant creation, membership write, invitation delivery, activation, campaign launch, go-live, or money behavior. |
| `/v1/referral-saas/accounts/{accountRef}/membership-invitations` | `POST` | TASK-211 membership invitation intent wrapper | Account admin bridge | Implemented as guarded seeded write. Records invited membership intent and account audit evidence only; no email delivery, membership activation, seat assignment, auth-claim change, campaign activation, go-live, or money behavior. |

### Campaigns

| Target route | Method | Current source/wrapper | Auth | Notes |
|---|---|---|---|---|
| `/v1/referral-saas/campaigns` | `POST` | `POST /campaigns` plus TASK-135 contract | SaaS account admin or integration credential | Requires idempotency and audit posture before implementation. |
| `/v1/referral-saas/campaigns/{campaignRef}` | `GET` | campaign service/readiness service | SaaS account admin/member | Product read shape only; no raw readiness internals. |
| `/v1/referral-saas/campaigns/{campaignRef}/readiness` | `GET` | `GET /admin/campaigns/{campaign_code}/readiness` | SaaS account admin/member or operator | Must map blockers to product-safe categories. |
| `/v1/referral-saas/campaigns/{campaignRef}/policy` | `GET` | `GET /campaigns/{campaign_code}/policy` | SaaS account admin/integration | Tenant scope must be credential-derived. |

### Referral Links And Codes

| Target route | Method | Current source/wrapper | Auth | Notes |
|---|---|---|---|---|
| `/v1/referral-saas/referral-codes` | `POST` | TASK-174 wrapper over `POST /referrals/codes` plus TASK-136 contract | SaaS account integration or partner/member role | Implemented as a bounded partner-identity scoped wrapper. It derives tenant scope from the credential, returns `issueStatus`, safe code/handle fields, and does not expose raw UCN/hash evidence. Schema uniqueness, explicit idempotency keys, lifecycle commands, and audit writes remain future work. |
| `/v1/referral-saas/referral-codes/{code}` | `GET` | `inspect_link_code` wrapper | SaaS account admin/member | Safe read only; no raw UCN/hash evidence. |
| `/v1/referral-saas/referral-codes/{code}/revoke` | `POST` | Future lifecycle task | SaaS account admin | Not currently implemented; do not imply available. |

### Public Validation

| Target route | Method | Current source/wrapper | Auth | Notes |
|---|---|---|---|---|
| `/v1/referral-saas/public/referrals/validate` | `POST` | TASK-174 wrapper over `POST /public/referrals/validate`, TASK-175 validation recovery mapper, TASK-176 validation idempotency posture, plus TASK-137 contract | Public validation | Implemented as a bounded product wrapper. It returns `validationStatus`, safe `referralTrackId`, alias, safe error/recovery fields, and redacts internal attributes through a centralized mapper. It also exposes that successful duplicate submits are not idempotent today and idempotency keys are not supported. Schema-backed duplicate reuse/conflict behavior and operator trace linkage remain future work. |
| `/v1/referral-saas/public/campaigns/validate` | `POST` | `POST /campaigns/validate` plus TASK-135 contract | Public validation | Must distinguish campaign code from campaign track ID. |
| `/v1/referral-saas/referrals/{referral_track_id}/referee-ucn` | `POST` | TASK-174 wrapper over `POST /referrals/referees/ucn` plus TASK-137 contract | SaaS account integration or partner/member role | Implemented as a bounded partner-identity scoped wrapper. It derives tenant scope from the credential and returns `captureStatus` without exposing raw UCN/hash evidence. |

### Progress Events

| Target route | Method | Current source/wrapper | Auth | Notes |
|---|---|---|---|---|
| `/v1/referral-saas/events/progress` | `POST` | `POST /v1/progress` plus TASK-138 contract | Integration/partner credential | Requires source event ID/dedupe posture and safe outcome mapping. |
| `/v1/referral-saas/referrals/{safeReferralRef}/progress` | `GET` | `GET /v1/referrers/{referrerUcn}` plus status wrapper | SaaS account/member or referrer/customer role | Must not expose raw referrer UCN. |
| `/v1/referral-saas/operator/referrals/{referral_track_id}/progress-status` | `GET` | TASK-182 wrapper over existing dashboard progress read and TASK-141 safe-status projection | Operator/support/admin bridge | Implemented as read-only operator progress/status diagnostics. Returns safe progress, safe status, missing evidence, redactions, and next diagnostics; no progress mutation, retry, replay, repair, support-case write, reward, money, or raw UCN exposure. |

### Attribution And Trace

| Target route | Method | Current source/wrapper | Auth | Notes |
|---|---|---|---|---|
| `/v1/referral-saas/attribution-traces/{safeReferralRef}` | `GET` | `GET /admin/outcomes/{referral_track_id}/trace` plus TASK-139 contract | SaaS account admin/support role | Product trace sections only; no money internals. |
| `/v1/referral-saas/referrals/{safeReferralRef}/status` | `GET` | TASK-141 safe-status projection | Referrer/customer/account scoped | Safe status only; no operator trace evidence. |

### Reporting And Exports

| Target route | Method | Current source/wrapper | Auth | Notes |
|---|---|---|---|---|
| `/v1/referral-saas/reports/{reportType}` | `GET` | TASK-156 report catalog helper plus TASK-157 route wrapper, TASK-158 scope resolver, TASK-159 referral funnel helper, TASK-160 progress event health helper, TASK-161 attribution quality helper, TASK-162 safe-status distribution helper, TASK-163 link/code performance helper, and TASK-164 reward visibility helper | Admin/report-reader bridge until SaaS account membership exists | Implemented for read-only `campaign_performance`, `referral_funnel`, `link_code_performance`, `progress_event_health`, `attribution_quality`, `safe_status_distribution`, and `reward_visibility_summary`; tenant-scoped identities may omit `tenant_code`, while internal report readers still need explicit tenant scope. |
| `/v1/referral-saas/reports/{reportType}/exports/validate` | `POST` | TASK-165 export validation gate over TASK-156/TASK-164 report catalog | Admin/report-reader bridge until SaaS account membership exists | Implemented as validation-only. Accepts supported report types, `json`/`csv`, `tenant_safe` redaction, approved dimensions/filters, row limits, and data windows; returns `VALIDATED_NOT_CREATED` and does not create export files, IDs, storage, delivery jobs, audit rows, retention records, or download URLs. |
| `/v1/referral-saas/reports/{reportType}/exports/preview` | `POST` | TASK-167 inline export preview over TASK-156/TASK-164 report catalog | Admin/report-reader bridge until SaaS account membership exists | Implemented as side-effect-free inline JSON/CSV preview. Does not create export IDs, files, storage records, delivery jobs, audit rows, retention records, or download URLs. |
| `/v1/referral-saas/reports/{reportType}/exports` | `POST` | TASK-142 future export contract | SaaS account admin/member | Export API/storage/audit not implemented. |
| `/v1/referral-saas/exports/{exportId}` | `GET` | TASK-142 future export contract | SaaS account admin/member | Requires retention/expiry/access controls before implementation. |

### Operator Diagnostics

| Target route | Method | Current source/wrapper | Auth | Notes |
|---|---|---|---|---|
| `/v1/referral-saas/operator/links/inspect` | `GET` | TASK-178 wrapper over `inspect_link_code` / `GET /admin/links/inspect` plus TASK-140 contract | Operator/support/admin bridge | Implemented as read-only operator diagnostics. Preserves evidence toggling, redactions, missing evidence, source warnings, safe validation errors, and product `nextDiagnostics`; no mutation, retry, replay, repair, reward, money, or code generation. |
| `/v1/referral-saas/operator/outcomes/{referral_track_id}/trace` | `GET` | TASK-180 wrapper over `get_outcome_trace` / `GET /admin/outcomes/{referral_track_id}/trace` plus TASK-139 contract | Operator/support/admin bridge | Implemented as read-only operator attribution trace. Defaults to outcome, attribution, participants, events, and audit; rejects reward, commission, funding, fulfilment, settlement, webhook, and unknown sections; no mutation, retry, replay, repair, reward, money, or support-case write. Future account-safe aliases may hide raw internal referral track IDs after account membership exists. |
| `/v1/referral-saas/operator/support-cases` | `GET` | TASK-145 future contract | Operator/support role | Not implemented by this map. |

## Auth And Tenant Scope Rules

| Surface | Auth rule | Tenant/account rule |
|---|---|---|
| Public validation | Public request validation only | Safe account/link context must resolve to tenant internally. |
| Integration commands | Partner/integration credential | Tenant derived from credential; do not trust request tenant ownership. |
| Account/member reads | Future SaaS membership/auth | Account membership resolves tenant and permitted campaigns. |
| Referrer/customer status | Consumer/referrer-scoped credential or safe token | Participant ownership must be verified before status is returned. |
| Operator diagnostics | Operator/support/admin role | Explicit tenant scope is allowed only for internal/operator routes. |
| Reports/exports | Account admin/member for tenant reports; operator/admin for internal reports | Tenant/account scope is mandatory; cross-tenant requires operator role. |

## Idempotency Rules

| Operation type | Idempotency expectation |
|---|---|
| Campaign create/setup mutation | Required before product route implementation. |
| Referral code issue/reuse | Must define idempotency around existing get-or-create behavior and schema uniqueness. |
| Public validation | Must define duplicate validation behavior before claiming idempotent validation. |
| Progress ingestion | Current dedupe/source-event behavior is the source of truth. |
| Exports | Required if export creation persists a file/job or external delivery. |
| Reads | No idempotency key; must be side-effect free. |

## Safe Error Shape

Future product APIs should return:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Safe client-facing message.",
    "correlationId": "request-correlation-id",
    "details": []
  }
}
```

Rules:

- do not expose stack traces, SQL errors, raw service exceptions, provider
  payloads, worker errors, DLQ payloads, private identifiers, or other tenant
  existence
- use 400 for validation errors
- use 401 for missing/invalid credentials
- use 403 for authenticated but unauthorized role/scope
- use 404 for inaccessible subjects where revealing existence would leak data
- use 409 for duplicate/conflict states only when the contract defines recovery
- use 429 for rate limits where gateway/app middleware supports it
- use 500 only with safe generic message and correlation ID

## Current Productization Gaps

- TASK-157 adds the first bounded `/v1/referral-saas/*` route:
  `GET /v1/referral-saas/reports/{report_type}`.
- TASK-174 adds bounded link/code product wrapper routes:
  `POST /v1/referral-saas/referral-codes`,
  `POST /v1/referral-saas/public/referrals/validate`, and
  `POST /v1/referral-saas/referrals/{referral_track_id}/referee-ucn`.
  These compose existing referral primitives, return product-shaped safe
  statuses, and redact raw UCN/hash/internal attribute evidence. They do not
  implement lifecycle commands, schema changes, audit writes, explicit
  validation idempotency, or account membership resolution.
- TASK-175 centralizes product validation status and recovery mapping in
  `services/referral_saas_validation_service.py` and tests terms, alias,
  missing-code, code-not-found, logging-recovery, failed, success, and
  redaction behavior. It does not implement duplicate-submit idempotency,
  operator trace linkage, schema changes, lifecycle commands, or audit writes.
- TASK-176 exposes the current validation idempotency posture in the product
  validation response: successful duplicate submits are treated as new
  validation journeys, the duplicate-submit guarantee is `NOT_IDEMPOTENT`, and
  idempotency keys are not supported. It does not implement schema-backed
  duplicate reuse, conflict detection, operator trace linkage, lifecycle
  commands, or audit writes.
- TASK-177 renders the product validation recovery and idempotency posture in
  the focused frontend link/code workflow. It does not add routes, schema,
  duplicate reuse, conflict detection, operator trace linkage, lifecycle
  commands, or audit writes.
- TASK-178 adds a read-only operator diagnostics product wrapper:
  `GET /v1/referral-saas/operator/links/inspect`. It composes
  `inspect_link_code`, keeps the response operator-scoped, and returns safe
  `nextDiagnostics` for campaign readiness, attribution trace, missing
  evidence, and source warnings. It does not add support-case mutations,
  repair/replay/retry commands, schema, audit writes, reward, funding,
  fulfilment, settlement, or broad DLaaS behavior.
- TASK-180 adds a read-only operator attribution trace product wrapper:
  `GET /v1/referral-saas/operator/outcomes/{referral_track_id}/trace`. It
  composes `get_outcome_trace`, keeps the response operator-scoped, defaults
  to outcome, attribution, participants, events, and audit sections, and
  rejects reward, commission, funding, fulfilment, settlement, webhook, and
  unknown sections from the Referral SaaS product surface. It does not add
  attribution mutation, support-case writes, repair/replay/retry commands,
  schema, audit writes, reward, funding, fulfilment, settlement, or broad
  DLaaS behavior.
- TASK-182 adds a read-only operator progress/status diagnostics product
  wrapper:
  `GET /v1/referral-saas/operator/referrals/{referral_track_id}/progress-status`.
  It composes the existing dashboard progress read and Referral SaaS
  safe-status projection helper, keeps the response operator-scoped, and
  returns safe progress, safe status, missing evidence, redactions, and next
  diagnostics. It does not add progress ingestion mutation, support-case
  writes, repair/replay/retry commands, schema, audit writes, reward, funding,
  fulfilment, settlement, or broad DLaaS behavior.
- TASK-166 lets report/export-validation envelopes carry trusted `account_ref`
  and `external_tenant_ref` identity claims. TASK-200/TASK-209/TASK-211 now
  provide bounded account resolver, membership posture, and membership
  invitation intent wrappers for Account Setup, but broader membership-aware
  route authorization and auth-claim integration remain future work.
- Some legacy current schemas expose raw `tenant_code`, `referrer_ucn`, or
  `referee_ucn`; TASK-174 product link/code wrappers use credential-derived
  scope for protected calls and product-shaped safe responses, while future
  product APIs must continue moving toward safe refs or credential-derived
  scope.
- Current admin/operator routes are useful diagnostics but are not public SaaS
  APIs.
- Current Referral SaaS reporting route supports read-only
  `campaign_performance`, `referral_funnel`, `progress_event_health`, and
  `attribution_quality`. TASK-158 lets tenant-scoped identities derive scope
  from identity claims, but internal report readers still need explicit
  `tenant_code` until full SaaS account membership resolution exists. TASK-166
  carries trusted account refs in the response envelope when identity claims
  provide them. TASK-167 adds inline export preview for JSON/CSV payload shape
  without persisted export storage or audit writes. TASK-159
  keeps the referral funnel source warning visible until dedicated
  validation-state and progress-milestone report sources exist. TASK-160 keeps
  progress-health deduped/rejected counts as partial coverage until those
  states are persisted in reportable form. TASK-161 derives aggregate
  attribution quality and does not expose raw outcome trace payloads. TASK-162
  derives aggregate safe-status distribution without exposing raw viewer, UCN,
  reward, audit, provider, or money evidence. TASK-163 adds aggregate
  link/code performance across durable referral code, campaign code,
  campaign-referral link, and route-referral link sources while excluding
  composite-code compatibility internals. TASK-164 adds reward visibility
  counts only from persisted rewards and pending mission bonus evidence while
  excluding reward amount totals, beneficiary references, fulfilment, funding,
  settlement, wallet, commission, invoice, payout, and broader money evidence.
- Persisted export APIs/storage/downloads are not implemented.
- Lifecycle commands such as revoke, expire, reissue, repair, replay, or retry
  are not authorized by this map.

## Future Contract Tests

When API implementation work starts, add tests for:

- OpenAPI/schema shape for every product route
- auth success and rejected adjacent roles
- tenant/account scope derived from credentials
- cross-tenant 403/404 behavior
- idempotency for mutating commands
- safe error envelopes
- no raw UCN, tenant internals, provider payload, audit payload, DLQ payload,
  token, secret, funding, settlement, or raw trace leakage
- backwards-compatible wrappers over current services
- read-only routes do not mutate state

## Explicit Non-Goals

- no schema, migration, service, route, auth helper, OpenAPI, frontend, or test
  implementation
- no public API namespace implementation
- no membership activation, invitation delivery, seat assignment, or auth-claim
  implementation
- no export API/storage implementation
- no lifecycle commands such as revoke, expire, reissue, repair, retry, replay,
  fulfil, settle, payout, invoice, or webhook dispatch
- no replacement of existing referral, campaign, progress, attribution,
  safe-status, reporting, or operator primitives
- no broader DLaaS marketplace, commission, funding, fulfilment, settlement,
  sponsor billing, white-label/embed, or SaaS billing work

## Readiness Decision

Referral SaaS has enough current route primitives to define a stable product
API map, but it does not yet have a versioned `/v1/referral-saas/*` API surface.
TASK-143 defines the wrapper direction, auth/tenant/idempotency/error rules,
and current gaps so future implementation can be small and contract-tested.
