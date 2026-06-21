# DLaaS Enhancement Backlog

This backlog is derived from `docs/sa/CAPABILITY_GAP_MATRIX.md`. It does not introduce work outside the SA findings. Each enhancement references one or more capabilities from the matrix and is scoped for MVP, Beta, or Later.

## EPIC 1: Platform Foundation

## DLaaS-001: Canonical distribution outcome spine

Platform capability: 6. Attribution tracking; 11. Reward liability tracking; 27. Observability.
Current state: Attribution, referral instances, campaign track events, reward records, funding reservations, fulfilment, settlement, and audit evidence exist across separate domains.
Target state: One canonical outcome read model or service trace links tenant, campaign, participant, link/code, customer event, reward or commission, funding, fulfilment, settlement, audit, and webhook evidence.
Gap: Attribution is implemented in several flows, but not as one DLaaS outcome trace.
Why this matters: The platform cannot support trustworthy control plane, portal status, reporting, support, or settlement investigation without a single outcome trail.
User/operator impact: Operators can search one outcome and see what happened, what is stuck, and who owns the next action.
Backend impact: Add an outcome trace aggregation contract over existing tables/services before adding new write models.
Frontend/control-plane impact: Enables outcome investigation, stuck-state views, and trust-building status displays.
API/webhook impact: Provides a stable source for future outcome status APIs and lifecycle webhook payloads.
Database impact: Prefer read model/view/service first; only add tables after proving existing schema cannot support traceability.
Funding/settlement/audit impact: Connects reward, commission, funding, fulfilment, settlement, invoice evidence, and audit into one trail.
Security/permissions impact: Must enforce tenant and role scope before returning outcome evidence.
Dependencies: Capabilities 1, 2, 5, 7, 14, 26.
Acceptance criteria: A backend call can trace a completed or failed distribution outcome across current attribution, reward/commission, funding, fulfilment, settlement, and audit evidence; missing evidence is reported explicitly.
Tests required: Golden-path attribution tests; broken-trail tests; cross-tenant outcome access tests; duplicate event/no-double-pay tests.
Risks: Existing domain identifiers may not always line up cleanly; read-model joins can become brittle without strong correlation keys.
Priority: MVP / P0.
Blocked by: Live schema confirmation for any table joins that are ambiguous.
Recommended task breakdown: Inventory identifiers; define response contract; implement aggregation service; add missing-evidence categories; add tenant/role guards; add tests.

## DLaaS-002: Platform state, idempotency, and live verification guardrails

Platform capability: 14. Audit trail; 28. Idempotency/retry handling; 30. Live DB/state verification.
Current state: Domain-specific states, audit tables, idempotency columns, retry services, and static migrations exist; live DB state was not inspected for the matrix.
Target state: State transitions, idempotency, retries, audit requirements, and live schema checks are governed as platform-level guardrails.
Gap: State and retry behavior are strong in places but not one platform-wide policy; live DB/state verification is Unknown.
Why this matters: DLaaS requires correctness under duplicate events, retries, failed fulfilment, settlement exceptions, and deployment drift.
User/operator impact: Operators can trust that repeated actions do not double-pay and that deployed state matches documented behavior.
Backend impact: Define platform standards for idempotency keys, retry exhaustion, audit requirements, and status-map ownership.
Frontend/control-plane impact: Enables consistent pending, failed, retrying, and action-required states.
API/webhook impact: Public/internal APIs can publish consistent idempotency and retry expectations.
Database impact: Add verification scripts/checklists before changing schema; use migrations as source of truth.
Funding/settlement/audit impact: Money-affecting retries and repairs require reason, actor, before/after, and audit evidence.
Security/permissions impact: Live checks must not expose sensitive data; audit exports must be role-scoped.
Dependencies: Capability 30 environment access; capability 14 audit inventory.
Acceptance criteria: Documented platform idempotency/retry/audit rules exist and a repeatable live DB/state verification checklist or smoke test is defined.
Tests required: Duplicate request tests; retry exhaustion tests; migration replay tests; live schema diff/smoke tests where environment access exists.
Risks: Live DB access may not be available in local development; static migrations may differ from deployed state.
Priority: MVP / P0.
Blocked by: Runtime database access for live verification.
Recommended task breakdown: Inventory state fields; define idempotency classes; define retry policy classes; define live DB verification checklist; add regression checks.

## EPIC 2: Tenant And Campaign Model

## DLaaS-003: SaaS account and tenant lifecycle foundation

Platform capability: 1. Tenant/account model; 26. Security/permissions.
Current state: `tenant_code` exists across schema, services, auth, reporting, and funding. TASK-048 decides `tenant_code` remains the internal platform tenant identifier, while external references such as `external_tenant_ref`, `organisation_ref`, `producer_ref`, `partner_ref`, and `distributor_ref` map into it. No full account/org, membership, seat, subscription, or lifecycle model was found.
Target state: Tenants belong to SaaS accounts and have lifecycle, onboarding state, owner/admin memberships, and enforceable isolation.
Gap: Tenant is mostly a runtime scope, not a SaaS account model.
Why this matters: A sellable multi-client platform needs client ownership, isolation, setup state, and permission boundaries.
User/operator impact: Operators can onboard and support clients; tenant admins can own their workspace safely.
Backend impact: Define account/tenant model and lifecycle while preserving existing internal `tenant_code` references and adding an external-reference mapping boundary.
Frontend/control-plane impact: Enables account setup, tenant readiness, user management, and permission-denied guidance.
API/webhook impact: Tenant-scoped APIs and webhooks can bind to account-level ownership, credentials, and external references rather than requiring public callers to depend on internal `tenant_code`.
Database impact: Add account/org, memberships, lifecycle, and relationship tables only after migration plan is agreed.
Funding/settlement/audit impact: Account/tenant context must be present in audit and money views.
Security/permissions impact: Adds membership and seat checks on top of existing API-key/JWT role helpers.
Dependencies: None for design; migration depends on current tenant table compatibility.
Acceptance criteria: Account/tenant lifecycle and membership design is documented and can be implemented without breaking current tenant-code behavior or public external-reference contracts.
Tests required: Tenant lifecycle tests; tenant isolation tests; membership permission tests; external-reference mapping tests; migration replay tests.
Risks: Retrofitting account ownership can expose routes that currently rely only on explicit tenant query params.
Priority: MVP / P0.
Blocked by: None. Tenant identifier boundary accepted in `docs/sa/TENANT_IDENTIFIER_BOUNDARY_DECISION.md` by TASK-048.
Recommended task breakdown: Map current tenant references; define account/tenant lifecycle; design membership model; plan migration; add permission tests.

## DLaaS-004: Canonical campaign lifecycle and readiness

Platform capability: 2. Campaign model.
Current state: Marketing campaigns, campaign policies, campaign track events, and distribution opportunities exist, but campaign lifecycle/readiness is split.
Target state: Campaigns have canonical lifecycle, readiness checks, configuration, policy, qualification, reward, funding, link/code, and reporting context.
Gap: Campaign exists but is not yet the single DLaaS campaign abstraction.
Why this matters: Tenants need to safely configure and launch campaigns without violating backend rules or money readiness.
User/operator impact: Operators and tenant admins know whether a campaign is draft, ready, active, paused, closed, or blocked by setup.
Backend impact: Define lifecycle and readiness service over current campaign and opportunity models.
Frontend/control-plane impact: Enables campaign builder/readiness screens backed by backend truth.
API/webhook impact: Campaign lifecycle APIs and webhooks can use stable state semantics.
Database impact: May require lifecycle/config versioning fields after current schema mapping.
Funding/settlement/audit impact: Campaign activation must check funding readiness and audit state changes.
Security/permissions impact: Campaign operations must enforce tenant and operator role.
Dependencies: DLaaS-003.
Acceptance criteria: Backend can evaluate campaign readiness and explain missing setup requirements without frontend inference.
Tests required: Campaign lifecycle tests; readiness guard tests; policy version tests; activation audit tests.
Risks: Marketing campaigns and distribution opportunities may not map one-to-one.
Priority: MVP / P0.
Blocked by: Tenant/account lifecycle design.
Recommended task breakdown: Map campaign/opportunity concepts; define lifecycle states; define readiness checks; add service contract; test activation blockers.

## EPIC 3: Partner/Referrer/Distributor Model

## DLaaS-005: Participant taxonomy and role mapping

Platform capability: 3. Partner/referrer/distributor model; 4. Customer/referred user model.
Current state: Referrers, distributors, partner clients, sponsors/producers, consumers, and referred users exist in separate tables/routes/services.
Target state: DLaaS has a clear participant taxonomy that maps current domain entities without erasing useful differences.
Gap: Roles are platform-relevant but fragmented by feature area.
Why this matters: Campaign setup, permissions, reporting, and portal UX need consistent language for who distributes, funds, refers, buys, or operates.
User/operator impact: Operators can manage participants consistently; portal users see role-appropriate status.
Backend impact: Create participant mapping/read model and role vocabulary across current tables/services.
Frontend/control-plane impact: Enables participant management screens and role-scoped portals.
API/webhook impact: Participant IDs/types can be used consistently in API responses and webhook payloads.
Database impact: Prefer mapping/read model first; avoid collapsing current distributor/referrer/sponsor/customer tables prematurely.
Funding/settlement/audit impact: Participant role must be clear for reward, commission, wallet, and sponsor billing views.
Security/permissions impact: Role mapping must align with existing `utils/security.py` and `utils/permissions.py`.
Dependencies: DLaaS-003; DLaaS-004.
Acceptance criteria: A participant taxonomy maps referrer, distributor, partner, sponsor/producer, customer/consumer, and admin/operator to current repo evidence.
Tests required: Role mapping tests; participant isolation tests; distributor/referrer/partner access tests; customer privacy tests.
Risks: Over-generalizing participants could hide domain-specific money rules.
Priority: MVP / P1.
Blocked by: Tenant/account model.
Recommended task breakdown: Inventory participant sources; define role taxonomy; map auth claims; map portal visibility; add permission tests.

## EPIC 4: Attribution And Event Ingestion

## DLaaS-006: Canonical link/code and attribution contract

Platform capability: 5. Distribution link/code generation; 6. Attribution tracking.
Current state: Referral codes, campaign referral links, composite code validation, route referral links, campaign attribution/events, referral instances, and progress events exist.
Target state: Link/code issuance, resolution, voiding, and attribution metadata are exposed through one canonical contract.
Gap: Link/code and attribution logic are split across referral and distribution route concepts.
Why this matters: The frontend, APIs, reporting, and webhooks need one way to understand what link/code caused which outcome.
User/operator impact: Operators can inspect links/codes and attribution without knowing legacy table origins.
Backend impact: Add wrapper service/contract over existing link/code and attribution sources.
Frontend/control-plane impact: Enables link/code manager and attribution monitor.
API/webhook impact: Public APIs can issue/resolve links and emit attribution events consistently.
Database impact: No immediate schema change required if wrapper can derive current state.
Funding/settlement/audit impact: Attribution becomes the start of the outcome-to-money trail.
Security/permissions impact: Link/code inspection must enforce tenant and participant scope.
Dependencies: DLaaS-004; DLaaS-005.
Acceptance criteria: A canonical contract can represent current referral codes, campaign links, and route referral links with source, status, tenant, campaign, and participant context.
Tests required: Link issue/resolve tests; void/expired tests; attribution metadata tests; cross-tenant tests; duplicate code tests.
Risks: Some legacy link/code records may lack enough metadata for full canonical representation.
Priority: MVP / P1.
Blocked by: Campaign and participant mapping.
Recommended task breakdown: Inventory link/code tables; define canonical shape; implement derivation plan; identify metadata gaps; add contract tests.

## DLaaS-007: Productized event ingestion contract

Platform capability: 7. Event ingestion; 28. Idempotency/retry handling.
Current state: Progress API, enterprise event inbox, worker route, queueing, DLQ/replay, and failure governance exist.
Target state: External systems can ingest events through documented DLaaS contracts with validation, idempotency, diagnostics, replay, and tenant scope.
Gap: Core ingestion exists, but public DLaaS event contract and tenant-facing diagnostics need productization.
Why this matters: Real clients will integrate their systems through events, and duplicate or malformed events must not create money errors.
User/operator impact: Operators and partners can see whether events were received, queued, ignored, failed, duplicated, or replayed.
Backend impact: Formalize event schemas, idempotency behavior, validation errors, and diagnostics using existing services.
Frontend/control-plane impact: Enables event monitor and integration troubleshooting.
API/webhook impact: Stabilizes event ingestion API and downstream lifecycle webhook semantics.
Database impact: Existing inbox/progress tables may be reused; add fields only for missing diagnostics.
Funding/settlement/audit impact: Event ingestion must not trigger duplicate rewards, fulfilment, or settlement obligations.
Security/permissions impact: Partner credentials must determine tenant scope unless admin override is explicitly allowed.
Dependencies: DLaaS-001; DLaaS-006.
Acceptance criteria: Event ingestion behavior is documented and testable for accepted, invalid, duplicate, queued, failed, and replayed events.
Tests required: Ingestion contract tests; idempotency tests; replay tests; invalid payload tests; tenant auth tests.
Risks: Public API stabilization may expose inconsistencies in current progress and enterprise-event payloads.
Priority: MVP / P1.
Blocked by: Attribution contract.
Recommended task breakdown: Inventory event routes; define event catalog; define idempotency rules; define diagnostics; add API tests.

## EPIC 5: Rules Engine

## DLaaS-008: Qualification and campaign rules boundary

Platform capability: 8. Qualification rules.
Current state: Journey definitions, progress definitions, campaign policies, and vertical journeys exist; no general rules engine boundary was found for eligibility, qualification, fraud/risk, and campaign limits.
Target state: Campaign qualification is evaluated by explicit rule boundaries covering eligibility, qualification, limits, risk checks, and reward triggers.
Gap: Qualification logic exists but is journey/policy-specific rather than a platform rules engine.
Why this matters: Tenants need different campaign logic without creating one-off backend branches.
User/operator impact: Operators can explain why an outcome qualified, did not qualify, or needs review.
Backend impact: Define modules/contracts for rule evaluation over current journey/policy services.
Frontend/control-plane impact: Enables campaign rule configuration/readiness and qualification explanation views.
API/webhook impact: Qualification decisions can appear in outcome APIs and lifecycle webhooks.
Database impact: Rule version/audit storage may be needed after current policy mapping.
Funding/settlement/audit impact: Qualification decisions must be auditable before reward/funding obligations are created.
Security/permissions impact: Only authorized tenant/admin users can change campaign rules.
Dependencies: DLaaS-004; DLaaS-007.
Acceptance criteria: Qualification decisions can be explained from backend events and rule context without frontend inference.
Tests required: Rule evaluation tests; event-to-qualification tests; negative qualification tests; rule version/audit tests.
Risks: A premature generic DSL could add complexity before platform rules are fully understood.
Priority: MVP / P1.
Blocked by: Campaign lifecycle and event ingestion contract.
Recommended task breakdown: Map existing journey/policy logic; define rule categories; define decision output; add audit requirements; add tests.

## EPIC 6: Reward Engine

## DLaaS-009: Reward and commission policy boundary

Platform capability: 9. Reward rules; 11. Reward liability tracking.
Current state: Reward policies and records exist; distribution commission rules/events exist separately; no unified outcome-to-money policy contract exists.
Target state: Rewards and commissions remain distinct where needed but share a clear DLaaS policy boundary, versioning, and outcome-to-money mapping.
Gap: Reward and commission rules are both present but need a clear platform taxonomy.
Why this matters: The platform must avoid double-pay, incorrect liability, and confusing reward/commission reporting.
User/operator impact: Operators can explain who earned what, why, and under which rule.
Backend impact: Define policy taxonomy and liability calculation contract over reward and commission services.
Frontend/control-plane impact: Enables reward/commission operations and safe status display.
API/webhook impact: Reward/commission lifecycle APIs and events can use consistent money semantics.
Database impact: May require rule version/evidence storage if current tables are insufficient.
Funding/settlement/audit impact: Reward/commission calculation must feed funding, fulfilment, settlement, and audit.
Security/permissions impact: Money rule changes require strict role checks and audit.
Dependencies: DLaaS-008.
Acceptance criteria: Reward and commission decisions can be traced to rule source, outcome, participant, amount, and lifecycle status.
Tests required: Reward calculation tests; commission calculation tests; no-double-pay tests; rule precedence tests; liability rollup tests.
Risks: Combining rewards and commissions too aggressively could blur customer/referrer versus distributor money flows.
Priority: MVP / P1.
Blocked by: Rules boundary.
Recommended task breakdown: Inventory reward/commission rules; define policy taxonomy; define decision evidence; map to liability; add tests.

## EPIC 7: Funding Engine

## DLaaS-010: Campaign funding readiness and liability projection

Platform capability: 10. Funding/budget allocation; 11. Reward liability tracking.
Current state: Funding accounts, reservations, limits, exposure, alerts, sponsor wallets, contracts, allocations, budget governance, rewards, commissions, and settlement evidence exist.
Target state: Campaigns expose funding readiness, pending obligations, available funds, reserved liabilities, fulfilled liabilities, settled amounts, and exceptions.
Gap: Strong funding foundation exists, but campaign-level DLaaS readiness/liability needs tighter linkage to canonical outcome.
Why this matters: Campaigns should not launch or continue blindly when funds, limits, or settlement readiness are unsafe.
User/operator impact: Finance and operators can answer what is owed, funded, settled, stuck, and at risk.
Backend impact: Add liability/readiness projection over reward, commission, funding, fulfilment, settlement, and invoice evidence.
Frontend/control-plane impact: Enables funding dashboard, campaign readiness, and outcome money trace.
API/webhook impact: Funding readiness can be exposed to internal APIs and eventually tenant APIs/webhooks.
Database impact: Prefer read models/queries first; add rollup tables only if performance requires.
Funding/settlement/audit impact: This is the core money observability enhancement.
Security/permissions impact: Finance data must be tenant-scoped and role-gated.
Dependencies: DLaaS-001; DLaaS-009.
Acceptance criteria: Campaign and outcome views can show calculated, reserved, fulfilled, settled, reversed, failed, and disputed amounts without double-counting.
Tests required: Reservation/release/settle tests; liability rollup tests; double-count prevention tests; reconciliation tests; tenant filter tests.
Risks: Money views can become misleading if reward, commission, wallet, invoice, and settlement evidence are not clearly separated.
Priority: MVP / P0.
Blocked by: Outcome spine and reward/commission boundary.
Recommended task breakdown: Define money states; map source tables; build liability service; add missing-evidence categories; test reconciliation.

## EPIC 8: Fulfilment And Settlement Engine

## DLaaS-011: Fulfilment and settlement status integration

Platform capability: 12. Fulfilment lifecycle; 13. Settlement lifecycle.
Current state: Fulfilment and settlement operations are strong, with provider routing, idempotency, retries, replay, audit, batches, approvals, exceptions, reversals, periods, and certifications.
Target state: Fulfilment and settlement states are connected to canonical outcome/liability trace and exposed safely to operators, partners, and customers.
Gap: Operational lifecycle exists, but DLaaS needs canonical status and customer/partner-safe visibility.
Why this matters: Users must not confuse calculated, fulfilled, processing, settled, failed, reversed, or disputed states.
User/operator impact: Operators can resolve failed/stuck fulfilment and settlement; portal users see safe status and next action.
Backend impact: Map fulfilment and settlement states into canonical outcome status and action-required categories.
Frontend/control-plane impact: Enables fulfilment dashboard, settlement dashboard, and portal reward/commission status.
API/webhook impact: Lifecycle webhooks can reflect safe status transitions.
Database impact: No immediate schema change required unless mapping reveals missing correlation data.
Funding/settlement/audit impact: Settlement and fulfilment transitions must be audit-linked to money evidence.
Security/permissions impact: Internal settlement details must not leak to customers/partners.
Dependencies: DLaaS-010.
Acceptance criteria: Outcome trace shows fulfilment and settlement status, failure reason category, retry/replay eligibility, and safe external status.
Tests required: Provider success/failure tests; retry scheduler tests; replay tests; batch lifecycle tests; exception/reversal tests; safe status mapping tests.
Risks: Raw provider or settlement exception details may be too sensitive for portal users.
Priority: MVP / P1.
Blocked by: Liability projection.
Recommended task breakdown: Map statuses; define safe status categories; connect to outcome trace; add retry/action flags; add tests.

## EPIC 9: Audit And Observability

## DLaaS-012: Audit taxonomy and observable support trace

Platform capability: 14. Audit trail; 27. Observability.
Current state: Admin audit, referral processing audit, fulfilment audit, governance audit, funding audit, metrics, health, failures, DLQ, and admin diagnostic APIs exist.
Target state: Sensitive actions and state transitions use a common audit taxonomy, and outcome traces carry correlation evidence for support and operations.
Gap: Audit and observability exist by domain but are not consistently tied to canonical outcome state.
Why this matters: A SaaS platform must prove what happened, who changed it, and how to investigate failures.
User/operator impact: Support and operators can diagnose issues without reading raw database rows.
Backend impact: Define audit event taxonomy and correlation/trace contract across domains.
Frontend/control-plane impact: Enables audit viewer, support/debug console, and trust-building status.
API/webhook impact: APIs can return correlation IDs and audit references where appropriate.
Database impact: May add audit/correlation fields only after current coverage is mapped.
Funding/settlement/audit impact: Money and repair actions require reason, actor, before/after state, and audit record.
Security/permissions impact: Audit views and exports must be tightly role-scoped.
Dependencies: DLaaS-001; DLaaS-002.
Acceptance criteria: Outcome, money, webhook, and repair actions can be traced through audit/correlation evidence.
Tests required: Audit write tests; failure-to-audit tests; repair action tests; trace ID propagation tests; role-scoped audit access tests.
Risks: Multiple audit stores can make a single viewer expensive or inconsistent.
Priority: MVP / P0.
Blocked by: Outcome spine and state taxonomy.
Recommended task breakdown: Inventory audit tables; define taxonomy; map correlation IDs; define support trace API; add audit tests.

## EPIC 10: API And Webhook Layer

## DLaaS-013: Versioned public/internal API and webhook event catalog

Platform capability: 17. Public API; 18. Internal API; 19. Webhooks; 20. API keys/integration credentials.
Current state: Many public, partner, admin, worker, BFF, and webhook APIs exist. Partner seam has client credentials and webhooks. A complete DLaaS API product is not yet defined.
Target state: DLaaS exposes stable public/internal APIs and webhook events for campaigns, participants, links/codes, events, outcomes, rewards, funding, fulfilment, settlement, analytics, audit, and credentials.
Gap: API surface is broad but not packaged as stable DLaaS contracts; webhook event catalog and subscription scope need formalization.
Why this matters: External systems need predictable integration contracts, not internal implementation details.
User/operator impact: Partners can integrate, monitor delivery, rotate credentials, and troubleshoot failures.
Backend impact: Wrap existing services/routes into versioned contracts and update permission matrix.
Frontend/control-plane impact: Enables integration centre and API credential management.
API/webhook impact: This is the primary API/webhook productization enhancement.
Database impact: Existing partner client/token/webhook tables can be reused; API-key SaaS extensions depend on Epic 14.
Funding/settlement/audit impact: Money-affecting API actions and webhook emissions require idempotency and audit.
Security/permissions impact: Credentials must have scopes, tenant binding, rotation, revocation, and audit.
Dependencies: DLaaS-001; DLaaS-006; DLaaS-007; DLaaS-012.
Acceptance criteria: Public/internal API families and webhook event types are documented with auth, tenant scope, validation, idempotency, errors, emitted events, and tests.
Tests required: Contract tests; OpenAPI/schema tests; auth/scope tests; webhook signing/retry/dead-letter tests; credential lifecycle tests.
Risks: Exposing internal routes directly could freeze poor contracts.
Priority: MVP / P1.
Blocked by: Outcome/state/event contracts.
Recommended task breakdown: Classify routes; define API families; define webhook catalog; map credentials/scopes; update permission matrix; add tests.

## EPIC 11: Operator Control Plane

## DLaaS-014: Operator control-plane information architecture and BFF contracts

Platform capability: 15. Admin/operator workflow.
Current state: Admin command centre and domain admin APIs exist for failures, DLQ, audit, finance, funding, fulfilment, settlement, distribution, and reporting.
Target state: Operator UX is organized around setup, readiness, monitoring, investigation, repair, audit, integration health, and money safety.
Gap: Backend operations exist, but operator workflow is not yet organized around canonical campaign/outcome trace.
Why this matters: Operators need to run the platform safely, not navigate disconnected admin tools.
User/operator impact: Operators can see stuck states, owners, risks, and allowed repair actions.
Backend impact: Add BFF contracts over existing admin services using canonical outcome/status/audit concepts.
Frontend/control-plane impact: Defines the control plane screens and components.
API/webhook impact: Internal APIs support operator views and repair actions.
Database impact: Use existing read paths first; add saved investigations/notes only if required later.
Funding/settlement/audit impact: Repair actions must be audited and money-safe.
Security/permissions impact: Finance, distribution, system, and platform admin boundaries must remain clear.
Dependencies: DLaaS-001; DLaaS-010; DLaaS-012.
Acceptance criteria: Control-plane BFF contracts support campaign readiness, outcome trace, funding, fulfilment, settlement, integration health, audit, and failure investigation.
Tests required: BFF aggregation tests; partial-section tests; permission tests; repair workflow tests; audit tests.
Risks: A page-first build could recreate a generic dashboard instead of platform operations.
Priority: MVP / P1.
Blocked by: Outcome trace and audit taxonomy.
Recommended task breakdown: Define screens from backend states; define BFF contracts; map permissions; define repair actions; add tests.

## EPIC 12: Partner/Customer Experience Layer

## DLaaS-015: Partner/customer safe status and action-required APIs

Platform capability: 16. Partner/customer portal; 21. Notifications.
Current state: Distributor portal, sponsor portal billing, partner integration, consumer experience, reward summary, partner webhook alerts, and channel dispatch exist. Status and notification models are role/domain-specific.
Target state: Partners, distributors, sponsors, referrers, and customers receive safe status, next step, action-required states, and relevant notifications without internal-only details.
Gap: Portal surfaces exist by role, but safe DLaaS status/action mapping and notification preferences are fragmented.
Why this matters: Users need to trust status without seeing raw operational or settlement internals.
User/operator impact: Reduces support load and makes pending, approved, failed, fulfilled, settled, and action-required states understandable.
Backend impact: Add safe status mapping APIs and notification event definitions over canonical states.
Frontend/control-plane impact: Enables partner/customer portal screens and trust-building copy.
API/webhook impact: Safe statuses can be shared through portal APIs and selected webhooks.
Database impact: Notification preferences/templates may be needed later; status mapping should derive first.
Funding/settlement/audit impact: Money statuses must not imply payment/settlement before backend truth supports it.
Security/permissions impact: Hide fraud flags, provider errors, DLQ payloads, and settlement internals from portal users.
Dependencies: DLaaS-011; DLaaS-013.
Acceptance criteria: Portal APIs can answer what happened, what happens next, whether action is required, and what safe state the backend is in.
Tests required: Role-scoped portal tests; safe status tests; no internal-detail leakage tests; action-required tests; notification dispatch tests.
Risks: Overexposing internal states can create trust and compliance issues.
Priority: Beta / P2.
Blocked by: Canonical state mapping and permissions.
Recommended task breakdown: Define safe statuses; map by role; define action-required rules; define notification events; add portal tests.

## EPIC 13: Analytics And Reporting

## DLaaS-016: Tenant-safe analytics and ledger-aware reporting

Platform capability: 22. Analytics/reporting.
Current state: Distribution reporting, finance metrics, materialized views, admin dashboards, and Prometheus metrics exist by domain.
Target state: Tenants and operators can report on campaigns, participants, attribution, rewards, funding, settlement, webhooks, and operations with tenant-safe filters and ledger-aware totals.
Gap: Reporting exists by domain but not as unified DLaaS analytics/reporting product.
Why this matters: A platform customer needs performance, conversion, obligation, settlement, and operational reporting they can trust.
User/operator impact: Tenant admins and operators can compare campaign performance and reconcile reported money to ledger evidence.
Backend impact: Define reporting dimensions, freshness, and rollups across existing reporting services.
Frontend/control-plane impact: Enables campaign, partner, attribution, reward, funding, settlement, and integration reporting.
API/webhook impact: Reporting APIs must expose tenant-scoped filters and export behavior.
Database impact: Add materialized views/rollups only where current queries cannot scale.
Funding/settlement/audit impact: Money reports must reconcile with reward/funding/settlement sources.
Security/permissions impact: Reports must enforce tenant filters and avoid cross-tenant aggregation leakage.
Dependencies: DLaaS-001; DLaaS-010; DLaaS-012.
Acceptance criteria: Reporting contracts define dimensions, filters, freshness, tenant scope, and ledger reconciliation expectations.
Tests required: Reporting accuracy tests; tenant filter tests; export tests; freshness tests; ledger reconciliation tests.
Risks: Analytics can drift from ledger truth if rollups are not reconciled.
Priority: Beta / P2.
Blocked by: Outcome and liability spine.
Recommended task breakdown: Define dimensions; map existing reports; define freshness; define export rules; add accuracy tests.

## EPIC 14: SaaS Packaging

## DLaaS-017: SaaS usage, plan, quota, and billing boundary

Platform capability: 23. SaaS usage tracking; 24. Billing/monetization hooks; 20. API keys/integration credentials.
Current state: Metrics, rate limiting, partner credentials, and sponsor utilisation billing exist. No durable SaaS usage events, plans, subscriptions, quotas, seats, or platform billing model were found.
Target state: Accounts can be sold on plans with entitlements, seats, API credentials, usage metering, quota enforcement, and platform billing hooks separate from sponsor billing.
Gap: Runtime metrics are not billing-grade usage metering, and sponsor billing is not platform SaaS billing.
Why this matters: The product cannot be sold to multiple clients without packaging, usage tracking, and commercial boundaries.
User/operator impact: Operators can provision plans; clients can understand usage; finance can bill platform usage.
Backend impact: Add usage event, rollup, quota, plan, subscription, API-key, and billing-hook designs.
Frontend/control-plane impact: Enables account settings, usage, limits, seats, plan, billing, and credential views.
API/webhook impact: API credentials and usage events become billable and auditable.
Database impact: Requires new SaaS packaging schema separate from sponsor billing tables.
Funding/settlement/audit impact: Keep sponsor utilisation billing and SaaS platform billing explicitly separate.
Security/permissions impact: Account admins need seat and credential controls; usage and billing views need strict account scope.
Dependencies: DLaaS-003; DLaaS-013.
Acceptance criteria: SaaS packaging design separates account billing from sponsor billing and defines usage metrics, quotas, plans, subscriptions, seats, and credential lifecycle.
Tests required: Usage event tests; quota tests; plan entitlement tests; credential usage attribution tests; sponsor-vs-SaaS billing separation tests.
Risks: Mixing sponsor billing with platform billing would create accounting and product confusion.
Priority: Beta / P2.
Blocked by: Account/tenant model and API credential productization.
Recommended task breakdown: Define billable metrics; design usage events; design plans/entitlements; design billing hooks; design quota enforcement; add tests.

## EPIC 15: White-Label/Embed/SDK Layer

## DLaaS-018: White-label, embed, and SDK foundation

Platform capability: 25. White-label/embeddable UX.
Current state: No first-class branding, custom domain, embed client, SDK token, or allowed-origin model was identified. Frontend brand notes are app styling notes, not tenant white-label configuration.
Target state: Tenants can eventually expose branded or embedded partner/customer UX through safe public status contracts, allowed origins, custom domains, and SDK/embed candidates.
Gap: No white-label/embed platform primitives exist.
Why this matters: White-label/embed can increase product value, but only after tenant isolation, safe statuses, and API contracts are mature.
User/operator impact: Tenants can present distribution journeys inside their own brand or product surfaces later.
Backend impact: Design tenant branding, portal config, domain verification, allowed origins, embed clients, and SDK token model.
Frontend/control-plane impact: Enables branding settings and embeddable partner/customer surfaces later.
API/webhook impact: Embed and SDK contracts require narrow, safe, tenant-scoped APIs.
Database impact: Requires new tenant branding/domain/embed schema later.
Funding/settlement/audit impact: Embedded UX must not expose raw money, fulfilment, settlement, or audit internals.
Security/permissions impact: Custom domains, origins, and public tokens increase attack surface and need strict isolation.
Dependencies: DLaaS-003; DLaaS-013; DLaaS-015.
Acceptance criteria: White-label/embed design identifies required schema, APIs, safe status dependencies, and security guardrails without starting premature UI implementation.
Tests required: Branding config tests; domain verification tests; CORS/origin tests; embed token tests; cross-tenant leakage tests.
Risks: Building this before safe status and tenant isolation could leak sensitive data.
Priority: Later / P3.
Blocked by: Tenant isolation, public API contracts, partner/customer safe statuses.
Recommended task breakdown: Define branding config; define domain verification flow; define allowed origins; define embed client/token; define SDK candidates; add security tests.
