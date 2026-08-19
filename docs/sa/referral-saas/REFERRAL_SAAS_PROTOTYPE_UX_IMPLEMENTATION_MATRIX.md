# Referral SaaS Prototype UX Implementation Matrix

## Purpose

This matrix maps the approved customer-journey prototype in
`ACTUAL_APPLICATION_UX_HANDOFF.md` to the production Referral SaaS frontend.
It is the implementation gate between the prototype and code: the prototype
defines the intended experience, while existing schemas, services, APIs,
permissions, audit controls, and tenant boundaries remain authoritative.

## Sources Reviewed

- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_JOURNEY_UX_IMPLEMENTATION_HANDOFF.md`
- `frontend/src/app/App.tsx`
- `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`
- Referral SaaS account, programme, campaign, referral, integration, reporting,
  attribution, and support endpoint modules

## Experience Contexts

| Context | Purpose | Boundary |
| --- | --- | --- |
| Amplifi Global | Find or create customers and perform governed platform administration. | No customer-scoped mutation without an explicitly selected account. |
| Selected customer | Operate one customer's products, programmes, campaigns, referrals, people, integrations, reports, and support. | Account reference, tenant context, permissions, and jurisdiction remain sticky. |
| Partner | Complete assigned referral work and view only permitted progress and outcomes. | No Amplifi administration or cross-customer visibility. |

## Journey Matrix

| Journey | Current production surface/capability | Maturity | Prototype target | Gap and implementation solution | Scope |
| --- | --- | --- | --- | --- | --- |
| 1. Customer discovery | Account registry and customer selection in Account Maintenance; account list/resolve APIs. | Partial | Country/market first, then searchable customer list, then open customer home. | Separate discovery from the selected-customer home; add labelled identity fields, useful empty/error states, and preserve explicit selection. | UX plus frontend composition; reuse APIs. |
| 2. Duplicate-safe customer creation | Account Setup wizard, onboarding drafts, account resolve, foundation creation and conflict handling. | Strong backend, partial UX | A short create flow that checks duplicates before creation and lands in the created customer. | Keep duplicate-safe backend rules; simplify wording and redirect successful creation to Customer Profile Overview. | Frontend first; no schema change expected. |
| 3. Customer Profile Overview | Selected-customer home inside `ReferralSaasAccountMaintenancePage`. | Implemented but dense | Quiet customer home with identity, health, next best actions, and scoped service entry points. | Remove raw/duplicated diagnostics from the primary view; use named fields, plain-language status, task-focused routes, and progressive disclosure. | Frontend refactor over existing read models. |
| 4. Customer products and offerings | Customer product catalogue and offering APIs plus programme bindings. | Implemented via TASK-423 | Customer-owned product catalogue with offering hierarchy and clear use in programmes. | Product lines and offerings are business-first, technical references are secondary, and the selected customer continues directly to Programmes. | Complete; existing APIs reused. |
| 5. Programme configuration | Governed drafts, validation, review, publish, version, incentive bindings, and analytics. | Strong | Simple guided builder with one next action and visible lifecycle. | Split overview, edit, validation, review, and version history into focused states without weakening review locks. | Frontend composition; existing governed APIs. |
| 6. Campaign management | Customer-scoped campaign create/list/readiness, programme binding, policy settings, and activation gates. | Strong | Campaign workspace separate from referral programme design, with inherited settings and explicit overrides. | Clarify programme inheritance versus campaign-specific changes; keep campaign activation authoritative and gated. | Frontend refinement; existing APIs. |
| 7. Referral operations | Referral code creation/validation, terms, progress, rewards and customer-scoped referral services. | Strong backend, fragmented UX | Operational referral list and referral detail with clear state and next action. | Consolidate entry, status, evidence, and allowed actions under the selected customer without exposing raw payloads. | New focused frontend routes over existing APIs. |
| 8. People and access | Membership intent, invite, acceptance, activation readiness, seat/login controls. | Strong but concept-heavy | Per-person lifecycle with plain-language stages and optional login setup. | Keep responsibility, invitation, acceptance, seat, and login as separate governed states; show one next action per person. | UX refinement; existing membership APIs. |
| 9. Integrations | Customer integration configuration, readiness, provider/vault checks and execution boundaries. | Strong backend, partial UX | Integrations overview with channel/provider cards, setup flows, health, and test actions. | Replace read-only technical summary with task-focused configuration pages; preserve secret redaction and provider controls. | Frontend expansion over existing APIs. |
| 10. Reporting and analytics | Tenant-safe reports, exports, schedules, programme/campaign analytics, attribution. | Strong | Audience-oriented dashboards and reports with explainable filters and exports. | Separate operational dashboards from diagnostics and label product/programme/campaign context consistently. | Frontend information architecture; existing read models. |
| 11. Support and exceptions | Customer-scoped support cases, assignment, notes, status, recovery readiness, governed commands. | Strong | Support queue and case workspace with ownership, evidence, and safe next actions. | Move diagnostics behind disclosure and keep repair/replay governed rather than presenting raw controls. | UX refinement; existing APIs. |
| 12. Partner experience | Partner APIs/tokens and referral primitives exist; dedicated experience is limited. | Gap | Focused partner work queue and referral status experience. | Define partner personas, permissions, routes, and safe read/write surfaces before building UI. | Later vertical slice; contract and UX required. |
| 13. Governance and audit | Review decisions, audit logs, idempotency, versioning, route guards, redaction. | Strong backend, scattered UX | Contextual governance evidence, approvals, audit history, and exception handling. | Surface governance where decisions occur and keep full evidence in dedicated history/details views. | Cross-cutting frontend pattern; existing controls. |

## Amplifi Global Operations Workspace Tranche

| Task | Outcome | Architectural gate |
| --- | --- | --- |
| TASK-424 | Complete - prototype-aligned global navigation and operator shell. | Global and selected-customer contexts are explicit; only real supported global destinations are exposed. |
| TASK-425 | Authoritative operations summary and work-item read model. | No synthetic frontend metrics or cross-account leakage. |
| TASK-426 | Operations dashboard with customer search, KPIs, queue preview, and portfolio attention. | UI consumes TASK-425 evidence only. |
| TASK-427 | Full operational work queue with filters and governed destinations. | One work-item model with server-side scope and stable pagination. |
| TASK-428 | Customer portfolio and explainable attention view. | Explicit customer selection and jurisdiction-safe visibility. |
| TASK-429 | Real destinations for approvals, exceptions, reporting, support, programme, and commercial governance. | No dead links, duplicated customer modules, or invented domain APIs. |
| TASK-430 | E2E, responsive, accessibility, permission, and leakage verification. | Release gate with evidence across roles, markets, and degraded states. |

## Look And Feel Contract

The production UI should adopt the prototype's design direction without
copying prototype-only data or bypassing the repository design system:

- persistent, restrained navigation that distinguishes global and
  selected-customer work;
- a compact customer identity header with labelled business fields;
- task-focused pages rather than one vertically stacked control centre;
- one dominant next action per state and clear back/switch-customer actions;
- plain-language status labels, with technical codes available only through
  details or diagnostics;
- restrained RAG colours used for meaning, not decoration;
- consistent typography, spacing, icon alignment, table density, buttons,
  drawers, empty states, loading states, and error recovery;
- no nested cards, oversized marketing composition, decorative gradients, or
  raw API payloads in normal operator workflows;
- responsive desktop and mobile layouts with no horizontal overflow, clipped
  labels, translucent drawers, or layout shifts during input.

## First Safe Vertical Slice - Complete

TASK-422 implements the connected acquisition path:

1. find a customer by operating jurisdiction and customer identity;
2. clearly distinguish an existing customer from a new customer;
3. retain duplicate-safe account creation and governed foundation controls;
4. open the selected customer on a standalone Customer Profile Overview;
5. apply the look-and-feel contract above to all three states;
6. preserve account, tenant, jurisdiction, RBAC, audit, idempotency, and
   redaction boundaries.

The production slice now adds searchable jurisdiction-scoped discovery, one
governed customer-creation entry point, explicit selection before navigation,
clear result and empty states, and responsive controls. It retains the existing
duplicate-safe Account Setup workflow and standalone selected-customer home.
It does not redesign backend domains or fork shared source code.

## Second Safe Vertical Slice - Complete

TASK-423 implements the customer product catalogue journey:

1. open Products from the selected customer context;
2. review product lines and their offerings as business entities;
3. add account-scoped product lines and offerings through existing APIs;
4. retain stable references as secondary integration and audit evidence;
5. continue to Programmes without mixing customer products with Amplifi package codes;
6. preserve account scope, idempotency, jurisdiction, audit, and activation boundaries.

## Explicit Non-Goals

- No DLaaS marketplace, funding, fulfilment, settlement, commission, sponsor
  billing, wallet, treasury, payout, or money movement.
- No invented fields, statuses, APIs, permissions, or tenant mappings.
- No whole-application rewrite or parallel frontend.
- No weakening of review, activation, audit, idempotency, provider, or auth
  controls for visual simplicity.
