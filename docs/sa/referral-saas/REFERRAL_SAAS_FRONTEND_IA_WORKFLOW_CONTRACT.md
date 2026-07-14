# Referral SaaS Frontend IA And Workflow Contract

TASK ID: TASK-144

Product boundary: Referral Management and Campaign Attribution SaaS.

Status: Contract only. No runtime behavior, route, component, CSS, API wrapper,
permission, schema, or test changes are made by this task.

## Boundary

This contract defines the focused Referral SaaS information architecture and
workflow path that should package existing frontend surfaces into a coherent
SaaS product experience.

Required boundary docs checked:

- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md`

Source files inspected:

- `frontend/src/app/App.tsx`
- `frontend/src/layout/AppShell.tsx`
- `frontend/src/layout/Sidebar.tsx`
- `frontend/src/api/endpoints/adminOnboarding.ts`
- `frontend/src/api/endpoints/consumerPortal.ts`
- `frontend/src/api/endpoints/distribution.ts`
- `frontend/src/api/experienceQueries.ts`
- `frontend/src/pages/admin/CampaignOpportunitySetupPage.tsx`
- `frontend/src/pages/admin/DistributionCommandCentrePage.tsx`
- `frontend/src/pages/admin/OperatorDemoHomePage.tsx`
- `frontend/src/pages/admin/OnboardingReadinessChecklistPage.tsx`
- `frontend/src/pages/admin/WebhookApiSetupPage.tsx`
- `frontend/src/pages/partner/PartnerIntegrationPage.tsx`
- `frontend/src/pages/consumer/ConsumerPortalPage.tsx`
- `frontend/src/pages/distributor/DistributorPortalPage.tsx`
- related frontend tests listed in `frontend/src/pages/**`

## Purpose

Referral SaaS already has meaningful frontend foundations. The gap is not a
missing UI from scratch; it is that the available pages are currently organized
around broader admin, onboarding, distributor, sponsor, partner, and consumer
workspaces.

This contract defines how those foundations should become a focused product IA
for:

1. account setup
2. campaign setup and readiness
3. referral link/code issue and management
4. public validation and recovery
5. progress/status visibility
6. attribution trace and investigation
7. tenant-safe reports and exports
8. integration setup
9. operator support entry points

It keeps broader DLaaS distribution marketplace, wallets, settlements, funding,
commissions, sponsor billing, and white-label/embed surfaces outside first
launch unless a later task scopes them explicitly.

## Current Frontend Facts

Current route foundations in `frontend/src/app/App.tsx`:

| Current route | Current page | Referral SaaS relevance |
|---|---|---|
| `/admin/onboarding/company` | `CompanyOnboardingPage` | Account/company setup shell. |
| `/admin/onboarding/members-roles` | `MemberRoleOnboardingPage` | Membership and role setup shell. |
| `/admin/onboarding/campaign-opportunity` | `CampaignOpportunitySetupPage` | Campaign/opportunity setup and readiness-adjacent shell. |
| `/admin/onboarding/webhook-api` | `WebhookApiSetupPage` | Integration, credential, callback, and payload preview shell. |
| `/admin/onboarding/readiness` | `OnboardingReadinessChecklistPage` | Go-live readiness checklist and blockers. |
| `/admin/demo-home` | `OperatorDemoHomePage` | Demo-safe journey and monitoring entry point. |
| `/partner` | `PartnerIntegrationPage` | Partner/integration operations surface. |
| `/consumer` | `ConsumerPortalPage` | Referrer/customer journey, referral code, validation, terms, progress, and reward-adjacent surface. |
| `/distributor` | `DistributorPortalPage` | Route/link/code and conversion journey evidence in broader distribution context. |
| `/admin/distribution` | `DistributionCommandCentrePage` | Marketplace/demand operations with attribution and route evidence, broader than first-launch SaaS. |
| `/admin/audit` | `AdminAuditPage` | Trust and audit visibility. |
| `/admin/events` | `EnterpriseEventsPage` | Event intake monitoring. |
| `/admin/health` | `HealthPage` | Runtime readiness signals. |

Current API/client foundations:

- `adminOnboarding.ts` already uses external setup refs, readiness projections,
  draft validation, idempotency keys, safe redaction, and no-live-action
  guardrails.
- `consumerPortal.ts` already calls referral code issue, public validation,
  referee UCN capture, consumer experience, reward summary, missions, and
  leaderboard endpoints.
- `referralSaasReports.ts` now provides the TASK-168 frontend API seam for
  Referral SaaS report reads, export validation, and inline export previews.
  It keeps `account_ref` and `external_tenant_ref` response-only and uses the
  existing internal `tenant_code` bridge only as an optional transitional query
  until full account membership exists.
- `/admin/referral-saas/reports` now provides the TASK-169 focused report
  catalog surface. It consumes the TASK-168 report client through React Query
  and renders tenant-safe metrics, freshness, warnings, redactions,
  account-scope posture, and export-preview guardrails. TASK-171 adds inline
  JSON/CSV preview actions and payload display on this same surface without
  adding persisted exports, download actions, scheduled delivery, audit writes,
  or account membership UX.
- `/admin/referral-saas/account-setup` now provides the TASK-170 focused
  account setup readiness surface. It consumes existing onboarding readiness
  evidence through external references and shows account profile, tenant-link,
  membership, campaign-readiness, and report-baseline gates without creating
  account records, memberships, tenant links, invitations, backend routes, or
  schema.
- `/admin/referral-saas/campaigns` now provides the TASK-172 focused campaign
  readiness surface. It consumes the existing read-only admin campaign
  readiness endpoint and renders campaign setup checklist, lifecycle,
  operation readiness, blockers, warnings, and safe campaign/policy evidence
  without campaign creation, policy writes, activation, link/code generation,
  backend routes, schema, marketplace, or money behavior.
- `/admin/referral-saas/link-codes` now provides the TASK-173 focused
  link/code workflow surface. It reuses the current referral code issue, public
  validation, and referee UCN capture client calls, labels tenant/referrer UCN
  input as a transitional bridge, shows only whitelisted result fields, and
  keeps reissue, revoke, expire, repair, replay, reward, money, backend route,
  schema, and DLaaS expansion behavior out of scope.
- `/admin/referral-saas/operator-links` now provides the TASK-179 focused
  operator link/code inspection surface. It consumes the TASK-178 read-only
  product wrapper, lets operators choose canonical source type and lookup
  reference, renders source summary, connected campaign/participant/attribution
  identifiers, missing evidence, source warnings, redactions, and next
  diagnostics, and does not render raw source evidence or expose support-case,
  retry, replay, repair, lifecycle, reward, money, or DLaaS controls.
- `/admin/referral-saas/attribution-trace` now provides the TASK-181 focused
  operator attribution trace surface. It consumes the TASK-180 read-only product
  wrapper, lets operators inspect a referral track with safe first-launch
  section toggles, renders trace summary, attribution links, participants,
  events, audit evidence, missing evidence, source warnings, redactions, and
  next diagnostics, and does not render reward, commission, funding,
  fulfilment, settlement, wallet, invoice, payout, webhook, raw provider
  payload, support-case write, repair, retry, replay, override, or attribution
  mutation controls.
- `GET /v1/referral-saas/operator/referrals/{referral_track_id}/progress-status`
  now provides the TASK-182 read-only progress/status diagnostics API over
  existing dashboard progress evidence and safe-status projection.
- `/admin/referral-saas/progress-status` now provides the TASK-183 focused
  operator progress/status surface. It consumes the TASK-182 read-only product
  wrapper, lets operators choose a safe viewer projection, renders safe
  progress, product status copy, action posture, missing evidence, redactions,
  and next diagnostics, and does not render raw UCNs, provider payloads,
  support-case writes, progress mutation, repair, retry, replay, reward,
  money, or DLaaS controls.
- `/admin/referral-saas/support` now provides the TASK-184 focused support
  workflow hub. It routes first-launch support case types to the existing
  read-only Referral SaaS setup, link/code, progress/status, attribution trace,
  campaign readiness, and reporting surfaces, shows evidence order and
  mutation guardrails, and does not render support-case write, repair, retry,
  replay, reward, money, or DLaaS controls.
- `/admin/referral-saas` now provides the TASK-185 focused workspace shell. It
  ringfences Referral Management and Campaign Attribution SaaS navigation from
  broader DLaaS/demo/admin surfaces and links only to account setup, campaign
  readiness, link/code workflow, reports, support, link inspection,
  attribution trace, and progress/status routes.
- TASK-186 adds explicit testing guidance to `/admin/referral-saas`: the page
  now states what the workspace is for, what users can do there, what to do
  first, and the recommended local testing path through account setup, campaign
  readiness, links/codes, and support evidence.
- `distribution.ts` includes broader route, offer, conversion, reporting, and
  wallet calls. Some are useful evidence for attribution and link/code status;
  money and marketplace depth remain outside first-launch Referral SaaS.
- `experienceQueries.ts` already composes admin, consumer, distributor, and
  sponsor experience queries.

Current frontend gaps:

- Dedicated Referral SaaS admin routes now have a focused `/admin/referral-saas`
  workspace shell and sidebar mode for the first-launch product workflow.
- Broader Distribution OS/DLaaS navigation still exists outside the Referral
  SaaS workspace, but it is no longer mixed into `/admin/referral-saas/*`
  product routes.
- Current consumer-facing calls still pass `tenantCode`, `referrerUcn`, and
  sometimes `referralTrackId` directly.
- Link/code issue, validation, identity capture, operator inspection, and
  attribution trace, progress/status, and support triage now have focused
  admin workflow surfaces. Account-safe status and support-case execution are
  still future work.
- Reporting/export screens now have a focused Referral SaaS report catalog
  surface with inline JSON/CSV preview handling, but persisted exports,
  download URLs, scheduled delivery, audit writes, and account membership UX
  remain future work.
- Operator diagnostics are scattered across admin, distribution, events, audit,
  and health surfaces.

## Target IA

Future Referral SaaS frontend packaging should use a focused workspace such as
`/referral-saas` or an equivalent product shell. The implementation task may
choose the exact route after API/auth packaging is ready.

Recommended top-level IA:

| Product area | User intent | Current foundation | First-launch rule |
|---|---|---|---|
| Home | See setup state, campaign health, referral volume, and open support items. | Admin overview, readiness, health. | Product summary only; no generic dashboard. |
| Account setup | Configure company, members, roles, external refs, and readiness. | Company/member onboarding and readiness pages. | Hide internal tenant code behind safe account refs. |
| Campaigns | Create campaign draft, review readiness, policy, and activation blockers. | Campaign setup and readiness pages. | Use TASK-135 product states and blockers. |
| Links and codes | Issue, inspect, reuse, validate, and explain referral codes/links. | Consumer referral code actions; TASK-178 wrapper; TASK-179 operator inspect UI. | Do not expose operator evidence to public users. |
| Validation | Validate referral/campaign code and recover safely from terms/alias/evidence gaps. | Consumer portal validation actions. | Use TASK-137 recovery states and safe copy. |
| Progress and status | Show referral journey progress, dedupe-safe status, and next action. | Consumer experience, progress queries, safe-status contract. | Use TASK-141 labels, not raw backend state names. |
| Attribution | Explain how campaign/link/event evidence produced the attribution outcome. | Outcome trace contract; distribution attribution evidence. | Account/support view only; referrer/customer gets summary status. |
| Reports | Show campaign, funnel, link/code, progress, attribution, and safe-status reports. | Tenant-safe analytics and distribution reporting foundations. | Use TASK-142 report catalog and redaction rules. |
| Integrations | Manage credential setup, webhooks, event payloads, and API readiness. | Webhook/API setup and partner integration pages. | Pair with TASK-143 API contract map. |
| Support | Investigate failed validation, missing progress, stuck status, and attribution gaps. | Operator demo, TASK-179 link/code inspect UI, audit, events, health. | Read-only diagnostics first; mutation/replay requires later task. |

## Workflow Contracts

### Account Setup

Use TASK-134 as the source contract.

Workflow:

1. account/admin lands on setup state
2. company and external refs are captured
3. members and roles are configured
4. integration readiness is checked
5. readiness blockers are displayed with safe next actions

UI rules:

- prefer safe account refs over internal `tenant_code`
- show incomplete, blocked, ready, and permission-limited states
- keep draft validation separate from live activation

### Campaign Setup And Readiness

Use TASK-135 as the source contract.

Workflow:

1. create or continue campaign draft
2. define campaign/referral journey settings
3. review policy and attribution settings
4. run readiness
5. show blockers before any go-live action

UI rules:

- keep campaign setup distinct from marketplace opportunity routing
- do not imply campaign activation until backend activation contract exists
- show readiness blockers as product-safe categories

### Referral Links And Codes

Use TASK-136, TASK-137, and TASK-140 as source contracts.

Workflow:

1. issue or reuse referral code/link
2. confirm accepted terms requirement
3. validate code/link publicly
4. recover from terms, alias, missing-code, or evidence failures
5. let operators inspect source evidence from a separate support surface

UI rules:

- show issue/reuse outcomes with product labels
- public validation must not expose raw UCNs, tenant internals, hashes, QR
  evidence internals, or operator trace details
- operator inspect views remain read-only until a later support task authorizes
  repair/retry/replay actions

### Progress And Safe Status

Use TASK-138 and TASK-141 as source contracts.

Workflow:

1. progress event is ingested by the integration/API
2. product status updates show recorded, deduped, queued, waiting, action
   needed, unavailable, or completed outcomes as safe copy
3. public/referrer/customer views show next action without internal error
   details
4. support views may link to diagnostic evidence

UI rules:

- do not show event queue errors, DLQ payloads, worker errors, audit payloads,
  or raw event rejection internals to public users
- customer/referrer copy maps through TASK-141 product labels
- support diagnostics must be visibly separated from public status

### Attribution Trace

Use TASK-139 as the source contract.

Workflow:

1. account/support user searches by safe referral/campaign/link context
2. trace view shows source evidence, completeness, warnings, and missing
   evidence categories
3. user can navigate to related code/link, progress, campaign, and report
   context

UI rules:

- account/support views may show product-safe trace sections
- public/referrer/customer views only receive a bounded status summary
- do not expose raw table names, raw UCNs, operator-only missing-evidence
  joins, or money-operation internals

### Reports And Exports

Use TASK-142 as the source contract.

Workflow:

1. select a first-launch report type
2. apply account/campaign/date filters
3. show freshness, redactions, source warnings, and operational metric class
4. optionally request JSON/CSV export when export implementation exists

UI rules:

- first-launch reports are operational and tenant-safe
- reports must show partial, stale, and unavailable source states
- export preview can use TASK-167/TASK-168 inline payloads; persisted export
  actions stay disabled or absent until API/storage/audit behavior exists

### Integrations

Use TASK-143 as the source contract.

Workflow:

1. show credential and API readiness state
2. display allowed event/API payload examples
3. explain idempotency and safe error behavior for integration developers
4. link to progress/event and campaign/referral API setup

UI rules:

- product API wrappers must not require callers to provide internal tenant code
- do not display secrets, signing material, tokens, or raw payload failures
- current routes may be documented as implementation facts, but future UI
  should orient around `/v1/referral-saas/*` product APIs when implemented

## Role Boundaries

| Role | Allowed first-launch surfaces | Must not see |
|---|---|---|
| Account admin | Account setup, campaigns, links/codes, reports, integrations, support summaries. | Other tenants, raw secrets, DLQ payloads, money internals unless later scoped. |
| Campaign manager | Campaigns, readiness, link/code performance, attribution summaries, reports. | Account credentials, operator-only raw evidence, settlement/funding internals. |
| Integration developer | API setup, payload examples, progress ingestion health, safe errors. | Customer PII, raw UCNs, operator trace details, admin billing/funding. |
| Support/operator | Link/code inspect, validation recovery, progress diagnostics, attribution trace, audit links. | Mutation/replay/repair controls unless a later task authorizes them. |
| Referrer/customer | Own safe status, next action, public validation/recovery, visible rewards where supported. | Tenant code, raw UCNs, audit/provider/DLQ payloads, operator evidence, broader money operations. |

## Copy And State Rules

- UI copy must distinguish current facts from unavailable future behavior.
- Do not invent backend statuses. Map backend/source states through the product
  states already defined in TASK-135 through TASK-143.
- Use safe labels such as `Ready`, `Blocked`, `Action needed`, `Waiting`,
  `In progress`, `Completed`, `Unavailable`, and `Expired` where contracts
  allow them.
- Do not show raw `tenant_code`, raw UCNs, raw referral hashes, provider
  payloads, audit payloads, DLQ payloads, secrets, tokens, funding internals,
  settlement internals, commission internals, wallet internals, invoices, or
  payout details on first-launch SaaS surfaces.
- Operator-only evidence must stay visually and permission-wise separate from
  public/referrer/customer status.

## Future Frontend Tests

When implementation starts, add or preserve tests for:

- product shell route rendering and sidebar/navigation grouping
- account setup to campaign setup workflow smoke path
- campaign readiness blocker rendering
- referral code issue/reuse and validation recovery UI states
- progress/safe-status label mapping with no raw internal states
- attribution trace access only for account/support roles
- report catalog rendering, freshness, redactions, inline preview handling, and
  disabled persisted export states
- public/referrer/customer no-leak assertions for tenant code, UCN, audit,
  provider, DLQ, secrets, tokens, and money internals
- mobile layout and accessibility for the main workflow

## Explicit Non-Goals

- no React route, component, CSS, API wrapper, schema, backend, permission, or
  test implementation
- no generic dashboard implementation
- no marketing landing page
- no public API wrapper implementation
- no export API/storage implementation
- no mutation, repair, retry, replay, activation, publish, revoke, expire,
  reissue, fulfil, settle, payout, invoice, or webhook dispatch controls
- no broader DLaaS marketplace, commission, funding, fulfilment, settlement,
  sponsor billing, wallet, white-label/embed, or SaaS billing implementation

## Readiness Decision

Referral SaaS has enough frontend foundation to support a strong product
workflow, and TASK-185 now packages the existing first-launch admin surfaces
behind a focused Referral SaaS workspace shell. TASK-186 makes that shell
usable as a local testing entry point by adding explicit purpose, action, and
first-step guidance. Remaining frontend work should focus on account-safe
customer/referrer status, support-case execution guardrails, live E2E proof,
and deeper campaign/account workflows rather than mixing Referral SaaS with
broader DLaaS navigation.
