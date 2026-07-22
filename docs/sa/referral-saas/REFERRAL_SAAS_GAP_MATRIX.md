# Referral Management and Campaign Attribution SaaS Gap Matrix

Product boundary: Referral SaaS.

Required boundary docs checked:

- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`

Supporting source docs checked:

- `docs/sa/CURRENT_STATE_MAP.md`
- `docs/sa/CAPABILITY_GAP_MATRIX.md`

## Purpose

This matrix converts the current code assessment into a focused path to a
10/10 Referral Management and Campaign Attribution SaaS product.

This is not a DLaaS-wide matrix. Funding, fulfilment, settlement, commissions,
sponsor billing, white-label/embed, and broad DLaaS marketplace expansion are
explicitly deferred unless required to support the focused SaaS wedge.

## Current Assessment Summary

The product is not greenfield. Core referral and attribution-adjacent
capabilities already exist:

- referral code creation and reuse
- accepted-terms enforcement
- referral code validation
- referral instance creation
- QR scan evidence
- referee UCN capture
- progress event ingestion
- journey and identifier validation
- dedupe keys and event payload hashes
- campaign creation and validation
- campaign track updates
- campaign policy read/write
- campaign attribution records and track events
- campaign readiness checks
- canonical link/code inspection
- role-specific frontend and API surfaces
- relevant unit, service, API, and journey tests

The remaining work is mainly SaaS packaging, contract hardening, attribution
trace unification, safe reporting, operator workflow, frontend coherence, E2E
coverage, and live DB/state verification.

## Gap Matrix

| Area | Current code capability | 10/10 SaaS requirement | Gap | Priority | Next task candidate | Tests/validation |
| --- | --- | --- | --- | --- | --- | --- |
| SaaS account packaging | `tenant_code` is used across important flows; admin tenant APIs, onboarding draft persistence, onboarding validation, submit-for-review, review-decision, and permission helpers exist. TASK-190 through TASK-230 establish account setup, durable account creation, account registry selection, Client Workspace physical proof, and repeatable fresh-client physical proof. TASK-231 adds persisted account operating jurisdiction and reframes the selected Client Workspace into a customer profile model: jurisdiction/customer selection first, then a standalone selected-customer profile route with customer-home context, plain-language health, next actions, and customer-scoped functions. TASK-232 removes demo Account Setup defaults and adds identifier guidance so setup starts from explicit operator-entered customer references. TASK-233 simplifies Review & Create to one primary create action while preserving save, submit, review, idempotency, duplicate-reference, and account-foundation guardrails behind the product action. TASK-234 removes the hidden default `FNB` owner-scope collision by deriving a bounded internal setup seed from customer identifiers, creating/updating that seed inside the guarded account-foundation transaction, and returning a distinct internal-scope duplicate conflict when needed. TASK-235 ends Account Setup at Review & Create and routes successful account-foundation creation to customer-profile-first next actions. TASK-236 keeps selected-customer people/access and customer settings actions inside Customer Profile modules. TASK-237 wires People and Access to the guarded membership invitation intent API. TASK-238 adds guarded Customer Settings maintenance. TASK-241 splits Customer Profile into separate customer-scoped pages. TASK-242 adds membership activation readiness. TASK-243 adds a safe invitation delivery request boundary. TASK-244 adds customer-scoped Technical Setup readiness and aligns Email as a shared channel provider readiness item. TASK-245 adds the standalone selected-customer Technical Setup page wired to that readiness API. TASK-246 adds an explicit approved-provider readiness gate so Email channel configuration is separate from Referral SaaS invite-provider approval and scope. TASK-247 adds safe recipient contact readiness from hashed contact evidence without exposing raw email or sending invites. TASK-248 productizes a guarded People and Access invite-delivery check from the selected customer profile without requiring browser-held recipient hashes or sending email. TASK-249 adds the audited/idempotent membership activation command boundary, including identity acceptance, active account/link/reference gates, duplicate-active prevention, and no adjacent seat/auth/campaign/go-live/money side effects. TASK-250 wires the selected-customer People and Access UI to that activation boundary with accepted-access feedback and posture/readiness refresh. TASK-251 clarifies the People and Access person-name placeholder so operators enter an actual individual name rather than a role label. TASK-252 exposes access provisioning readiness separately from membership lifecycle so active membership does not imply seat assignment or login/auth-claim propagation. | SaaS customer can onboard company/account, setup state, limits, and external identifiers without exposing internal identifiers; existing accounts can be maintained through a selected-customer workspace for scoped health, evidence, membership, identifiers, users, roles, technical posture, readiness, activities, dashboards, and audit workflows. | Durable account, organisation, account-tenant, external-reference, user, membership, seat, and account-audit schema exists; account setup, customer profile selection, standalone customer pages, customer-scoped people/access, customer settings, membership activation readiness, blocked invitation delivery boundary, technical setup readiness, Technical Setup UI productization, invite-provider approval readiness, safe recipient contact readiness, guarded delivery-check UI, membership activation command boundary, frontend activation action, clearer People and Access person-name guidance, and explicit provisioning readiness now exist. Product package, billing-plan fields, live invite delivery provider integration, actual seat assignment, actual auth-claim propagation, account lifecycle commands, external-reference rotation, and broader account maintenance commands remain open as bounded future work. | P0 | TASK-252 complete; next account task should implement the live invite-delivery adapter contract once provider readiness is approved or start bounded seat/auth provisioning command design | Tenant/account contract tests; API wrapper tests; migration replay tests; onboarding draft wrapper tests; role/membership tests; activation-readiness tests; provisioning-readiness tests; activation command tests; activation UI tests; technical-setup readiness tests; technical-setup UI tests; provider approval tests; recipient contact readiness tests; guarded delivery-check tests; invitation idempotency/audit tests; duplicate membership tests; profile maintenance command tests; external-reference resolver tests; tenant isolation tests; maintenance read-model tests; frontend wizard/workspace tests; local physical setup evidence. |
| Campaign setup and readiness | Campaign create/validate, track update, policy read/write, attribution tables, campaign readiness service, tests, TASK-172 read-only Referral SaaS readiness UI, TASK-253 customer/account-scoped campaign readiness wrapper/page, TASK-254 customer-scoped campaign list/read wrappers, TASK-255 customer-scoped campaign draft/create command contract, TASK-256 guarded customer-scoped campaign setup create API wrapper, TASK-257 selected-customer campaign setup create UX, and TASK-258 customer-scoped campaign policy/settings command contract exist. | One coherent campaign setup workflow with readiness gates, lifecycle states, attribution settings, policy visibility, product write wrappers, and activation guardrails. | Customer-scoped campaign readiness, list/read, create-command design, runtime inactive setup-create wrapper, standalone selected-customer create UX, and policy/settings command contract are now packaged without operator tenant-code entry. Runtime policy/settings wrapper, policy/settings UX, submit/review, activation, and full campaign workflow E2E remain open. | P0 | TASK-258 complete; next campaign task should implement the guarded customer-scoped campaign policy/settings API wrapper | Campaign setup API tests; account-scoped campaign list/read tests; account-scoped readiness tests; create idempotency/audit tests; duplicate campaign tests; readiness blocker tests; lifecycle/status tests; frontend create workflow tests; policy/settings contract/API tests; activation/idempotency/audit tests before commands ship. |
| Referral code creation | Code creation, preferred handle handling, existing-code reuse, accepted-terms enforcement, TASK-173 focused issue/reuse UI, and TASK-174 product issue wrapper exist. | Tenant-scoped, documented, auditable issue/reuse flow with clear product API, account-scoped setup UX, and operational evidence. | Product wrapper and first UI surface now exist; account/membership scope, schema uniqueness decision, audit consistency, and lifecycle operations remain open. | P0 | TASK-174: Add Referral SaaS link/code product API wrappers; next task should harden account-scope/idempotency/audit decisions | Duplicate issue tests; terms-required tests; tenant-scope tests; audit/readback tests; frontend no-leak tests. |
| Referral validation and terms | Validation enforces terms, alias rules, referral instance creation, QR scan evidence, safe failures, TASK-173 focused validation UI, TASK-174 product validation wrapper, TASK-175 dedicated validation recovery mapper, TASK-176 explicit idempotency posture, and TASK-177 recovery/retry UI exist. | Public validation API has stable errors, idempotency posture, operator trace, recovery UX, and no sensitive leakage. | Product wrapper now has centralized, tested safe validation/recovery mapping and the UI shows recovery plus non-idempotent retry posture; schema-backed idempotent reuse, operator trace linkage, and deeper recovery workflow actions still need hardening. | P0 | TASK-177: Add Referral SaaS validation recovery UI; next task should implement schema-backed duplicate reuse or add operator trace linkage | Validation contract tests; duplicate submit tests; safe error tests; QR evidence tests; frontend recovery tests. |
| Progress and journey checks | Progress events validate identifiers, product/sub-product binding, journey compatibility, self-referral, dedupe key, payload hash, queue emission, TASK-182 exposes a read-only operator progress/status diagnostics wrapper, TASK-183 adds the focused operator progress/status UI, and TASK-184 links it into support triage. | Productized event catalog, clear retry/error classes, tenant diagnostics, replay posture, and visible status updates. | Event ingestion and first support-facing diagnostics API/UI are strong; remaining gaps are event catalog/OpenAPI packaging, replay posture, account-safe status surfaces, and live E2E evidence. | P0 | TASK-184: Add Referral SaaS operator support workflow hub; next task should add OpenAPI/event catalog or replay posture proof | Event contract tests; dedupe/idempotency tests; invalid payload tests; replay/diagnostic tests; E2E status tests. |
| Campaign attribution trace | Campaign attribution records, track events, referral instances, progress events, campaign referral links, route referral links, journey tests, TASK-139 contract, admin outcome trace, TASK-180 read-only product attribution trace wrapper, TASK-181 focused operator trace UI, TASK-182 progress/status support API, TASK-183 progress/status UI, and TASK-184 support hub exist. | One explainable trace from campaign/link/code/event to attributed outcome, including missing evidence and conflict handling. | Product attribution trace API/UI, progress/status API/UI, and support triage now exist, but conflict/precedence UX and live E2E evidence remain open. | P0 | TASK-184: Add Referral SaaS operator support workflow hub; next task should add conflict/precedence UX or E2E proof | Product wrapper tests; golden-path trace tests; missing-evidence tests; conflict tests; cross-tenant tests; UI workflow tests. |
| Link/code inspection | Canonical inspection covers referral codes, campaign codes, campaign referral links, route referral links, composite-code compatibility, redactions, missing evidence, TASK-178 read-only product operator wrapper, TASK-179 focused operator UI, TASK-180 product attribution trace target, TASK-181 adjacent trace navigation, TASK-182 progress/status diagnostics target, TASK-183 progress/status UI navigation, and TASK-184 support hub triage. | Operator can investigate any SaaS link/code source from safe evidence and jump to related campaign, referral, progress, and attribution state. | Product operator inspection API/UI, product attribution trace API/UI, progress/status API/UI, and support triage hub now exist, but support-case persistence remains open. | P1 | TASK-184: Add Referral SaaS operator support workflow hub; next task should add support-case persistence contract or account-safe surfaces | Admin inspection tests; product wrapper tests; redaction tests; missing source tests; UI workflow tests. |
| Referrer/customer safe status | Consumer, distributor, reward summary, and experience routes exist; progress summaries exist for referrers. | Referrer/customer views show safe current status, next action, and progress without leaking internal fraud, audit, provider, or money details. | Role surfaces exist but SaaS safe status copy and contracts are not unified. | P1 | TASK-141: Define Referral SaaS safe status contract | Safe status tests; privacy/no-leak tests; role-scope tests; frontend status tests. |
| Tenant-safe reporting | Distribution reporting, materialized views, finance/admin metrics, and tenant-safe analytics service exist in broader repo. | SaaS tenant can report on campaigns, referrals, links/codes, progress events, attribution, conversion, and exports with freshness rules. | Reporting exists by domain, but Referral SaaS reporting package and export contract need focus. | P1 | TASK-142: Define Referral SaaS reporting and export contract | Reporting accuracy tests; tenant filter tests; export tests; freshness tests. |
| Public API contracts | Referral, progress, campaign, reward summary, partner-ish APIs exist; TASK-174 adds first link/code product wrappers beside the report/export wrappers, TASK-175 centralizes validation recovery mapping, TASK-176 exposes validation idempotency posture, TASK-177 renders recovery/retry posture in the UI, TASK-178 adds the first operator diagnostics wrapper, TASK-180 adds the product attribution trace wrapper, TASK-182 adds the product progress/status diagnostics wrapper, TASK-183 renders that wrapper in the UI, TASK-184 adds the support workflow hub, and TASK-256 adds the first customer-scoped campaign setup create command wrapper. | Versioned Referral SaaS public API with auth, schemas, idempotency, errors, examples, and contract tests. | Reporting/export, link/code, operator inspect, attribution trace, progress/status, support triage, account, membership, profile, and guarded campaign setup wrappers now exist with tested validation recovery, idempotency posture, and UI visibility, but OpenAPI packaging and later campaign policy/activation command routes remain incomplete. | P1 | Next API task should either package OpenAPI/customer examples or add campaign policy/settings boundary after create UX is usable | OpenAPI/schema tests; auth tests; idempotency tests; error-shape tests. |
| Frontend SaaS workflow | Role-specific React pages and tests exist; TASK-170 through TASK-258 provide the focused Referral SaaS admin/API surfaces, Account Setup wizard, account creation path, account selector, selected customer profile routes, customer-scoped people/access, customer settings, activation readiness, invitation delivery boundary, membership activation command boundary, technical setup readiness API, selected-customer Technical Setup page, visible invite-provider approval readiness, safe contact readiness indicators, guarded invite-delivery check, guarded accepted-access action, clearer person-name guidance, explicit provisioning readiness in People and Access, customer-scoped Campaigns readiness, selected-customer campaign list selection, campaign create command boundary, guarded runtime campaign setup create API, standalone selected-customer campaign setup create UX, and customer-scoped policy/settings command contract. | Coherent Referral SaaS workflow: account setup, setup checkpoint, customer profile selection, customer home/readiness summary, customer activity routing, campaign setup, technical setup, referral link/code management, event/attribution investigation, reporting, safe status. | Focused surfaces now cover Account Setup, customer selection, standalone selected customer home, customer-scoped function pages, people/access intent, activation readiness, safe invitation delivery boundary, activation command boundary, activation action wiring, technical setup readiness, Technical Setup UI page, explicit provider approval status, recipient contact readiness visibility, a customer-scoped guarded delivery-check action, clearer person-name guidance, visible membership-versus-provisioned-login boundary, customer-scoped campaign readiness, campaign selection from selected-account data, backend guarded campaign setup create, frontend create UX for inactive campaign setup drafts, and the policy/settings contract for the next page/API slice. Live invite delivery, account lifecycle/reference rotation, seat/auth provisioning workflows, campaign policy/settings implementation, campaign submit/activate implementation, link/code customer scoping, report customer scoping, and full campaign workflow productization remain bounded future capabilities. | P1 | Next frontend/API task should implement and then productize campaign policy/settings inside the selected customer campaign context | Frontend route tests; accessibility tests; no-internal-leak tests; setup workflow smoke tests; account create-action tests; membership invitation tests in Account Maintenance; activation-readiness UI tests; provisioning-readiness UI tests; activation command UI tests; activation action UI tests; recipient contact readiness UI tests; guarded delivery-check UI tests; technical setup readiness UI tests; campaign list/read/readiness UI tests; campaign create UX tests; campaign policy/settings contract/API/UX tests; provider approval UI tests; profile maintenance tests in Customer Profile; duplicate/already-created state tests; maintenance read-model/workspace tests; local physical setup proof. |
| Operator support workflow | Admin audit, failure, DLQ, enterprise events, campaign readiness, link inspection routes, TASK-178 read-only product operator inspection wrapper, TASK-179 focused operator inspect surface, TASK-180 read-only product attribution trace wrapper, TASK-181 focused trace UI, TASK-182 read-only progress/status diagnostics wrapper, TASK-183 progress/status UI, and TASK-184 support hub exist. | Operator can resolve validation, progress, link/code, attribution, and reporting issues through safe evidence without DB access. | Product operator diagnostic API/UI, attribution trace API/UI, progress/status API/UI, and support triage hub exist, but support-case persistence and repair/replay guardrails remain open. | P1 | TASK-184: Add Referral SaaS operator support workflow hub; next task should add support-case persistence contract or repair/replay guardrail proof | Support workflow tests; permission tests; redaction tests; evidence-link tests. |
| Audit and idempotency posture | Domain-specific audit and idempotency exist; progress dedupe is concrete. | Every SaaS command/event has a stated idempotency, retry, audit, and failure posture. | Coverage is uneven by command type. | P1 | TASK-146: Inventory Referral SaaS audit and idempotency posture | Static inventory; duplicate request tests; audit evidence tests; retry/failure tests. |
| E2E and live DB confidence | Broad domain tests exist; static migrations exist; live DB verification remains unavailable. | Full tenant-to-campaign-to-code-to-validation-to-progress-to-attribution-to-report E2E suite and live DB/state verification for launch-critical tables/routes. | No focused Referral SaaS golden-path suite and no live DB/state result for this wedge. | P0 | TASK-147: Define Referral SaaS E2E and live verification plan | E2E plan; migration replay; live schema/status/index checklist; route smoke checklist. |

## Recommended Ordered Task Sequence

1. TASK-134: Define Referral SaaS account setup contract.
2. TASK-135: Productize Referral SaaS campaign setup and readiness contract.
3. TASK-136: Harden Referral SaaS referral code issue contract.
4. TASK-137: Harden Referral SaaS validation and recovery contract.
5. TASK-138: Productize Referral SaaS progress event contract.
6. TASK-139: Define Referral SaaS attribution trace contract.
7. TASK-147: Define Referral SaaS E2E and live verification plan.
8. TASK-140: Add Referral SaaS operator link/code investigation contract.
9. TASK-141: Define Referral SaaS safe status contract.
10. TASK-142: Define Referral SaaS reporting and export contract.
11. TASK-143: Create Referral SaaS public API contract map.
12. TASK-144: Define Referral SaaS frontend IA and workflow contract.
13. TASK-145: Define Referral SaaS operator support workflow.
14. TASK-146: Inventory Referral SaaS audit and idempotency posture.

TASK-147 is intentionally pulled forward before lower-priority product polish
because live DB/state uncertainty can cap production confidence even when code
coverage is strong.

## First Implementation Recommendation

After this matrix, the next concrete task should be TASK-134. The account/setup
contract is the commercial packaging layer that lets existing referral,
campaign, and attribution capabilities become a SaaS product instead of a set
of strong internal flows.

TASK-134 should remain contract/design first unless it discovers a small,
well-contained implementation path that does not require schema, auth, or
membership changes beyond its scope.

## Explicit Deferrals

These are not blockers for the 10/10 Referral SaaS wedge:

- distributor marketplace expansion
- distributor commission settlement
- funding account operations
- fulfilment provider routing
- settlement batches, reversals, exceptions, and certifications
- sponsor billing
- white-label/embed infrastructure
- advanced platform SaaS billing beyond basic product limits

If any deferred item becomes necessary for Referral SaaS launch, it must be
rescoped as a separate task with money/audit/live-state guardrails.

