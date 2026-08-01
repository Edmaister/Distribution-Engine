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
- `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_INTEGRATIONS_CONFIGURATION_CONTRACT.md`

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
| `/v1/referral-saas/accounts/{accountRef}/membership-invitations/{membershipRef}` | `PATCH` | TASK-276 invited access intent update wrapper | Account admin bridge | Implemented as guarded seeded write. Updates only invited membership intent details and account audit evidence; active, disabled, suspended, or archived memberships are rejected. No email delivery, membership activation, seat assignment, auth-claim change, campaign activation, go-live, or money behavior. |
| `/v1/referral-saas/accounts/{accountRef}/membership-invitations/{membershipRef}` | `DELETE` | TASK-276 invited access intent cancel wrapper | Account admin bridge | Implemented as guarded seeded write. Marks invited membership intent `DISABLED` and records audit evidence; it does not hard-delete access history, send invitations, activate membership, assign seats, change auth claims, activate campaigns, trigger go-live, or move money. |
| `/v1/referral-saas/accounts/{accountRef}/memberships/{membershipRef}/access-provisioning` | `POST` | TASK-284 contract plus TASK-285 guarded API wrapper | Account admin bridge or future provisioning permission | Implemented as guarded seeded write. Requires active account, active tenant link, active external reference, active membership, available seat, audit, idempotency, and redaction before assigning a platform seat. It does not send invites, create credentials, mutate auth claims, activate campaigns, trigger go-live, bill, or move money. |
| `/v1/referral-saas/accounts/{accountRef}/profile` | `PATCH` | TASK-238 customer profile settings maintenance wrapper | Account admin bridge | Implemented as guarded seeded write. Updates bounded durable profile metadata only: account name, account type, operating jurisdiction, customer type, and industry. Customer identifiers remain read-only; no external-reference rotation, account activation, membership write, invitation delivery, seat assignment, auth-claim change, credential lifecycle, campaign activation, go-live, billing, money, or DLaaS marketplace behavior. |

### Integrations

| Target route | Method | Current source/wrapper | Auth | Notes |
|---|---|---|---|---|
| `/v1/referral-saas/accounts/{accountRef}/integrations/configuration` | `GET` | TASK-301 contract plus TASK-302 runtime API wrapper | SaaS account admin/operator bridge | Implemented as read-only selected-customer Integrations configuration evidence plus technical setup readiness. No secrets, credential creation, webhook dispatch, invite delivery, membership activation, seat assignment, auth-claim changes, campaign activation, go-live, billing, or money movement. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/configuration` | `PUT` | TASK-301 contract plus TASK-302 guarded save wrapper | SaaS account admin/operator bridge | Implemented as guarded seeded write for non-secret setup evidence. Requires selected-customer scope, correlation, idempotency, redaction, and safe catalogs; rejects raw secrets, internal tenant code, live dispatch, invite delivery, auth changes, campaign activation, billing, and money movement. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/configuration/validate` | `POST` | TASK-301 contract plus TASK-302 validation wrapper | SaaS account admin/operator bridge | Implemented as side-effect-free validation. No persistence, credential creation, webhook registration, message dispatch, invite delivery, auth changes, campaign activation, billing, or money movement. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/webhook-catalog` | `GET` | TASK-301 contract over webhook catalog source material | SaaS account admin/operator bridge | Future safe event-category/catalog read for setup. No subscription activation, callback registration, or webhook dispatch. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/execution-readiness` | `GET` | TASK-304 contract plus TASK-305 runtime API wrapper | SaaS account admin/operator bridge or future customer integration admin | Implemented as read-only selected-customer live execution readiness over saved configuration, active account/link/reference posture, provider/catalog gates, guardrails, and redactions. No credential lifecycle, webhook dispatch, invite/message delivery, membership activation, seat assignment, auth changes, campaign activation, go-live, billing, or money movement. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/api-access/verification` | `POST` | TASK-304 contract plus TASK-307 runtime command | SaaS account admin/operator bridge or future customer integration admin | Implemented as governed selected-customer API-access verification evidence. Requires saved Integrations configuration, active account/link/reference posture, correlation, idempotency, audit, redaction, and no-secret/no-provider/no-webhook/no-invite/no-message/no-auth/no-campaign/no-billing/no-money guardrails. It does not create, reveal, rotate, or accept credentials. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/webhooks/test-dispatch` | `POST` | TASK-304 contract | SaaS account admin/operator bridge or future customer integration admin | Future guarded webhook test-dispatch command. Must require approved callback, catalog, signing, idempotency, audit, and redaction gates before any test dispatch evidence is recorded. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/message-providers/test-delivery-check` | `POST` | TASK-304 contract | SaaS account admin/operator bridge or future customer integration admin | Future provider test-readiness command. Must not send live invite or referral messages unless a later approved provider execution task explicitly implements that behavior. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/credential-requests` | `POST` | TASK-314 credential lifecycle request contract plus TASK-315 runtime API foundation | SaaS account admin/operator bridge or future customer integration admin | Implemented as a governed selected-customer credential request metadata command. Requires saved Integrations configuration, selected-customer scope, supported request type, correlation, idempotency, audit, redactions, and no-adjacent-action confirmations. It rejects raw secrets, tokens, signing keys, credential material, provider payloads, and live execution fields. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/credential-requests` | `GET` | TASK-315 runtime API foundation | SaaS account admin/operator bridge or future customer integration admin | Implemented as a safe selected-customer credential request list. Returns summaries only; no secret reveal, credential download, provider payload, auth claim, campaign, billing, or money behavior. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/credential-requests/{requestRef}` | `GET` | TASK-315 runtime API foundation | SaaS account admin/operator bridge or future customer integration admin | Implemented as a safe selected-customer credential request read. Shows lifecycle/review/audit posture without rendering secrets or provider internals. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/credential-requests/{requestRef}/review-decisions` | `POST` | TASK-314 contract plus TASK-317 runtime API foundation | SaaS account admin/operator bridge or future governed reviewer | Implemented as a selected-customer credential request approval/block decision. Requires account scope, correlation, idempotency, review reason, audit evidence, and unsafe-payload rejection. Approval does not itself create, store, reveal, rotate, revoke, download, or send credentials and does not call providers, write a vault, dispatch webhooks, deliver messages, change auth, activate campaigns, bill, or move money. |
| `/v1/referral-saas/accounts/{accountRef}/integrations/credential-requests/{requestRef}/execution-checks` | `POST` | TASK-314 contract plus TASK-319 runtime API foundation | SaaS account admin/operator bridge or future customer integration admin | Implemented as safe execution-readiness evidence after approved review. Requires selected-customer scope, correlation, idempotency, audit evidence, unsafe-payload rejection, and no credential creation/storage/reveal/download/rotation/revoke, provider call, vault write, webhook dispatch, invite/message delivery, auth/session change, campaign activation, billing, or money movement. Provider/vault execution remains a separate governed task. |

### Campaigns

| Target route | Method | Current source/wrapper | Auth | Notes |
|---|---|---|---|---|
| `/v1/referral-saas/accounts/{accountRef}/campaigns` | `POST` | TASK-256 wrapper over existing campaign tables and account audit evidence | SaaS account admin bridge | Implemented as guarded seeded write. Resolves selected customer account scope internally, creates an inactive campaign setup draft, records idempotency/audit evidence, and does not activate campaigns, generate links, create validation tracks, write policy, send webhooks, or move money. |
| `/v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/policy-settings` | `PUT` | TASK-259 wrapper over existing campaign policy table and account audit evidence | SaaS account admin bridge | Implemented as guarded seeded write. Resolves selected customer account and campaign scope internally, persists policy/settings evidence without caller-supplied tenant code, records idempotency/audit evidence, and does not activate campaigns, generate links, create validation tracks, deliver webhooks, bill, or move money. |
| `/v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/review-submissions` | `POST` | TASK-262 wrapper over existing campaign, policy, account audit, and idempotency evidence | SaaS account admin bridge | Implemented as guarded seeded write. Submits selected-customer campaign setup evidence for review only after policy evidence exists, records campaign review/audit/idempotency evidence, and does not activate campaigns, generate links, create validation tracks, deliver webhooks, change seats/auth claims, bill, or move money. |
| `/v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/review-decisions` | `POST` | TASK-262 wrapper over existing campaign, policy, account audit, and idempotency evidence | Operator/admin reviewer bridge | Implemented as guarded seeded write. Records campaign review approval or block decision; approval only marks the campaign eligible for a future activation command and does not activate the campaign. |
| `/v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/activation-requests` | `POST` | TASK-265 wrapper over existing campaign lifecycle, review, policy, account audit, and idempotency evidence | SaaS account admin/operator bridge | Implemented as guarded seeded write. Requires approved review and policy evidence, resolves tenant scope internally, mutates only campaign activation posture, and does not generate links, create validation tracks, deliver webhooks, create credentials, change access, bill, or move money. |
| `/v1/referral-saas/campaigns` | `POST` | `POST /campaigns` plus TASK-135 contract | SaaS account admin or integration credential | Legacy target shape only; account-scoped create wrapper is the implemented product route. |
| `/v1/referral-saas/campaigns/{campaignRef}` | `GET` | campaign service/readiness service | SaaS account admin/member | Product read shape only; no raw readiness internals. |
| `/v1/referral-saas/campaigns/{campaignRef}/readiness` | `GET` | `GET /admin/campaigns/{campaign_code}/readiness` | SaaS account admin/member or operator | Must map blockers to product-safe categories. |
| `/v1/referral-saas/campaigns/{campaignRef}/policy` | `GET` | `GET /campaigns/{campaign_code}/policy` | SaaS account admin/integration | Tenant scope must be credential-derived. |

### Referral Links And Codes

| Target route | Method | Current source/wrapper | Auth | Notes |
|---|---|---|---|---|
| `/v1/referral-saas/referral-codes` | `POST` | TASK-174 wrapper over `POST /referrals/codes` plus TASK-136 contract | SaaS account integration or partner/member role | Implemented as a bounded partner-identity scoped wrapper. It derives tenant scope from the credential, returns `issueStatus`, safe code/handle fields, and does not expose raw UCN/hash evidence. Schema uniqueness, explicit idempotency keys, lifecycle commands, and audit writes remain future work. |
| `/v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/referral-codes` | `POST` | TASK-267 wrapper over existing referral code issue/reuse primitive and selected-customer campaign scope | SaaS account admin/operator bridge | Implemented as a guarded seeded write. Resolves selected customer account scope internally, requires the selected campaign to be active, returns safe issue/reuse code fields, and does not expose tenant code, activate campaigns, deliver webhooks, create credentials, bill, or move money. |
| `/v1/referral-saas/referral-codes/{code}` | `GET` | `inspect_link_code` wrapper | SaaS account admin/member | Safe read only; no raw UCN/hash evidence. |
| `/v1/referral-saas/referral-codes/{code}/revoke` | `POST` | Future lifecycle task | SaaS account admin | Not currently implemented; do not imply available. |

### Public Validation

| Target route | Method | Current source/wrapper | Auth | Notes |
|---|---|---|---|---|
| `/v1/referral-saas/public/referrals/validate` | `POST` | TASK-174 wrapper over `POST /public/referrals/validate`, TASK-175 validation recovery mapper, TASK-176 validation idempotency posture, plus TASK-137 contract | Public validation | Implemented as a bounded product wrapper. It returns `validationStatus`, safe `referralTrackId`, alias, safe error/recovery fields, and redacts internal attributes through a centralized mapper. It also exposes that successful duplicate submits are not idempotent today and idempotency keys are not supported. Schema-backed duplicate reuse/conflict behavior and operator trace linkage remain future work. |
| `/v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/referrals/validate` | `POST` | TASK-267 wrapper over existing referral validation primitive and selected-customer campaign scope | SaaS account admin/operator bridge | Implemented as a guarded seeded write. Resolves selected customer account scope internally, requires the selected campaign to be active, returns the safe product validation result, and does not expose tenant code, activate campaigns, deliver webhooks, create credentials, bill, or move money. |
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
| `/v1/referral-saas/accounts/{accountRef}/reports/{reportType}` | `GET` | TASK-268 account-scoped adapter over the existing Referral SaaS report catalog | SaaS account admin/operator bridge | Implemented as a selected-customer wrapper. Resolves account scope internally from `accountRef` plus external context, supports campaign filters, redacts internal tenant/report scope, and does not mutate reports, create exports, deliver files, bill, or move money. |
| `/v1/referral-saas/reports/{reportType}/exports/validate` | `POST` | TASK-165 export validation gate over TASK-156/TASK-164 report catalog | Admin/report-reader bridge until SaaS account membership exists | Implemented as validation-only. Accepts supported report types, `json`/`csv`, `tenant_safe` redaction, approved dimensions/filters, row limits, and data windows; returns `VALIDATED_NOT_CREATED` and does not create export files, IDs, storage, delivery jobs, audit rows, retention records, or download URLs. |
| `/v1/referral-saas/accounts/{accountRef}/reports/{reportType}/exports/validate` | `POST` | TASK-268 account-scoped adapter over existing export validation | SaaS account admin/operator bridge | Implemented as validation-only from selected customer context. Caller does not provide tenant code; response confirms no export file, export ID, storage record, delivery job, audit-retention record, download URL, billing, or money movement is created. |
| `/v1/referral-saas/reports/{reportType}/exports/preview` | `POST` | TASK-167 inline export preview over TASK-156/TASK-164 report catalog | Admin/report-reader bridge until SaaS account membership exists | Implemented as side-effect-free inline JSON/CSV preview. Does not create export IDs, files, storage records, delivery jobs, audit rows, retention records, or download URLs. |
| `/v1/referral-saas/accounts/{accountRef}/reports/{reportType}/exports/preview` | `POST` | TASK-268 account-scoped adapter over existing inline export preview | SaaS account admin/operator bridge | Implemented as side-effect-free inline preview from selected customer context. Supports JSON/CSV previews through internal account scope and does not expose tenant code, persist exports, deliver files, bill, or move money. |
| `/v1/referral-saas/accounts/{accountRef}/reports/{reportType}/exports` | `POST` | TASK-273 account-scoped persisted export request wrapper | SaaS account admin/operator bridge | Implemented as request/audit persistence only. Resolves account scope internally, validates through existing report export preview rules, records idempotent request and account audit evidence, and does not create export files, download URLs, storage objects, scheduled delivery, invoices, billing events, or money movement. |
| `/v1/referral-saas/reports/{reportType}/exports` | `POST` | TASK-142 future export contract | SaaS account admin/member | Export API/storage/audit not implemented. |
| `/v1/referral-saas/exports/{exportId}` | `GET` | TASK-142 future export contract | SaaS account admin/member | Requires retention/expiry/access controls before implementation. |

### Operator Diagnostics

| Target route | Method | Current source/wrapper | Auth | Notes |
|---|---|---|---|---|
| `/v1/referral-saas/operator/links/inspect` | `GET` | TASK-178 wrapper over `inspect_link_code` / `GET /admin/links/inspect` plus TASK-140 contract | Operator/support/admin bridge | Implemented as read-only operator diagnostics. Preserves evidence toggling, redactions, missing evidence, source warnings, safe validation errors, and product `nextDiagnostics`; no mutation, retry, replay, repair, reward, money, or code generation. |
| `/v1/referral-saas/operator/outcomes/{referral_track_id}/trace` | `GET` | TASK-180 wrapper over `get_outcome_trace` / `GET /admin/outcomes/{referral_track_id}/trace` plus TASK-139 contract | Operator/support/admin bridge | Implemented as read-only operator attribution trace. Defaults to outcome, attribution, participants, events, and audit; rejects reward, commission, funding, fulfilment, settlement, webhook, and unknown sections; no mutation, retry, replay, repair, reward, money, or support-case write. Future account-safe aliases may hide raw internal referral track IDs after account membership exists. |
| `/v1/referral-saas/accounts/{accountRef}/support-cases` | `POST` | TASK-297 implementation of TASK-295 contract | SaaS account admin/operator bridge | Implemented selected-customer support-case create command. Resolves account scope internally, records idempotency/audit evidence, links only safe diagnostic evidence, and rejects raw UCNs, provider payloads, secrets, tokens, repair/replay/retry, campaign activation, export file creation, invite delivery, credential/auth changes, billing, money movement, and DLaaS marketplace side effects. |
| `/v1/referral-saas/accounts/{accountRef}/support-cases` | `GET` | TASK-297 implementation of TASK-295 contract | SaaS account admin/operator bridge | Implemented selected-customer support-case list. Returns only customer-scoped cases and safe evidence links. |
| `/v1/referral-saas/accounts/{accountRef}/support-cases/{caseRef}` | `GET` | TASK-297 implementation of TASK-295 contract | SaaS account admin/operator bridge | Implemented selected-customer support-case read. Does not expose raw diagnostic payloads, secrets, tokens, UCNs, DLQ payloads, or cross-tenant evidence. |
| `/v1/referral-saas/operator/support-cases` | `GET` | TASK-145 future contract; TASK-295/TASK-297 selected-customer persistence boundary | Operator/support role | Future operator aggregate only. First implementation starts from selected-customer account routes; aggregate queue, notes, and status changes remain separate. |

## Auth And Tenant Scope Rules

| Surface | Auth rule | Tenant/account rule |
|---|---|---|
| Public validation | Public request validation only | Safe account/link context must resolve to tenant internally. |
| Integration commands | Partner/integration credential | Tenant derived from credential; do not trust request tenant ownership. |
| Account/member reads | Future SaaS membership/auth | Account membership resolves tenant and permitted campaigns. |
| Referrer/customer status | Consumer/referrer-scoped credential or safe token | Participant ownership must be verified before status is returned. |
| Operator diagnostics | Operator/support/admin role | Explicit tenant scope is allowed only for internal/operator routes. |
| Reports/exports | Account admin/member for tenant reports; operator/admin for internal reports | Customer/account-scoped report routes resolve tenant scope internally from the selected account; internal/operator report routes may require explicit tenant scope. Cross-tenant access requires operator role. |

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
  route authorization and auth-claim integration remain future work. TASK-284
  defines the access provisioning command contract for accepted memberships,
  seat assignment, and login/auth-claim propagation. TASK-285 implements the
  guarded runtime route for available-seat assignment only; credential creation
  and auth-claim propagation remain separate future governed workflows.
- TASK-256 adds `POST /v1/referral-saas/accounts/{accountRef}/campaigns` as a
  customer-scoped campaign setup create wrapper. It creates inactive campaign
  setup only and preserves idempotency/audit evidence while excluding
  activation, link generation, validation-track creation, policy write,
  webhook delivery, and money movement.
- TASK-301 defines the selected-customer Integrations configuration route
  family for future API access, webhook callback intent, event-category
  subscription intent, invite-delivery provider approval intent, and
  referral-message channel readiness. It is contract-only and does not add
  runtime schema, credential lifecycle, webhook dispatch, invite delivery,
  auth/login changes, campaign activation, billing, money movement, or DLaaS
  marketplace behavior.
- TASK-314 defines the selected-customer Integrations credential lifecycle
  request family for future API key, webhook signing key, and provider
  credential-reference requests. It is contract-only and does not add schema,
  runtime routes, UI controls, secret storage/reveal, provider/vault execution,
  webhook dispatch, invite/message delivery, auth/login changes, campaign
  activation, billing, money movement, or DLaaS marketplace behavior.
- TASK-262 implements the selected-customer campaign submit/review routes:
  `POST /v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/review-submissions`
  and
  `POST /v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/review-decisions`.
  The guarded wrappers keep review separate from activation, link/code
  generation, validation-track creation, webhook delivery, invite/seat/auth
  changes, billing, and money movement.
- TASK-264 defines the future selected-customer activation route:
  `POST /v1/referral-saas/accounts/{accountRef}/campaigns/{campaignRef}/activation-requests`.
  The contract requires approved review and activation-ready campaign evidence
  before any lifecycle change, keeps tenant-code resolution server-side, and
  preserves links/codes, validation tracks, webhooks, credentials, access,
  billing, and money as separate workflows.
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
