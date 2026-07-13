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
| SaaS account packaging | `tenant_code` is used across important flows; admin tenant APIs and permission helpers exist. | SaaS customer can onboard company/account, users, roles, setup state, limits, and external references without exposing internal `tenant_code`. | Account/user/membership/seat/setup model is not productized for Referral SaaS. | P0 | TASK-134: Define Referral SaaS account setup contract | Tenant/account contract tests; role/membership tests; external-reference tests; tenant isolation tests. |
| Campaign setup and readiness | Campaign create/validate, track update, policy read/write, attribution tables, campaign readiness service, tests, and TASK-172 read-only Referral SaaS readiness UI exist. | One coherent campaign setup workflow with readiness gates, lifecycle states, attribution settings, policy visibility, product write wrappers, and activation guardrails. | Read-only readiness is now packaged, but product campaign create/policy/submit/activate wrappers, account-scope resolution, idempotency, audit, and full workflow UX remain open. | P0 | TASK-172: Add Referral SaaS campaign readiness frontend surface; next task should add product campaign wrapper planning/implementation | Campaign setup API tests; readiness blocker tests; lifecycle/status tests; frontend workflow tests; activation/idempotency/audit tests before commands ship. |
| Referral code creation | Code creation, preferred handle handling, existing-code reuse, accepted-terms enforcement, TASK-173 focused issue/reuse UI, and TASK-174 product issue wrapper exist. | Tenant-scoped, documented, auditable issue/reuse flow with clear product API, account-scoped setup UX, and operational evidence. | Product wrapper and first UI surface now exist; account/membership scope, schema uniqueness decision, audit consistency, and lifecycle operations remain open. | P0 | TASK-174: Add Referral SaaS link/code product API wrappers; next task should harden account-scope/idempotency/audit decisions | Duplicate issue tests; terms-required tests; tenant-scope tests; audit/readback tests; frontend no-leak tests. |
| Referral validation and terms | Validation enforces terms, alias rules, referral instance creation, QR scan evidence, safe failures, TASK-173 focused validation UI, TASK-174 product validation wrapper, TASK-175 dedicated validation recovery mapper, TASK-176 explicit idempotency posture, and TASK-177 recovery/retry UI exist. | Public validation API has stable errors, idempotency posture, operator trace, recovery UX, and no sensitive leakage. | Product wrapper now has centralized, tested safe validation/recovery mapping and the UI shows recovery plus non-idempotent retry posture; schema-backed idempotent reuse, operator trace linkage, and deeper recovery workflow actions still need hardening. | P0 | TASK-177: Add Referral SaaS validation recovery UI; next task should implement schema-backed duplicate reuse or add operator trace linkage | Validation contract tests; duplicate submit tests; safe error tests; QR evidence tests; frontend recovery tests. |
| Progress and journey checks | Progress events validate identifiers, product/sub-product binding, journey compatibility, self-referral, dedupe key, payload hash, queue emission, TASK-182 exposes a read-only operator progress/status diagnostics wrapper, TASK-183 adds the focused operator progress/status UI, and TASK-184 links it into support triage. | Productized event catalog, clear retry/error classes, tenant diagnostics, replay posture, and visible status updates. | Event ingestion and first support-facing diagnostics API/UI are strong; remaining gaps are event catalog/OpenAPI packaging, replay posture, account-safe status surfaces, and live E2E evidence. | P0 | TASK-184: Add Referral SaaS operator support workflow hub; next task should add OpenAPI/event catalog or replay posture proof | Event contract tests; dedupe/idempotency tests; invalid payload tests; replay/diagnostic tests; E2E status tests. |
| Campaign attribution trace | Campaign attribution records, track events, referral instances, progress events, campaign referral links, route referral links, journey tests, TASK-139 contract, admin outcome trace, TASK-180 read-only product attribution trace wrapper, TASK-181 focused operator trace UI, TASK-182 progress/status support API, TASK-183 progress/status UI, and TASK-184 support hub exist. | One explainable trace from campaign/link/code/event to attributed outcome, including missing evidence and conflict handling. | Product attribution trace API/UI, progress/status API/UI, and support triage now exist, but conflict/precedence UX and live E2E evidence remain open. | P0 | TASK-184: Add Referral SaaS operator support workflow hub; next task should add conflict/precedence UX or E2E proof | Product wrapper tests; golden-path trace tests; missing-evidence tests; conflict tests; cross-tenant tests; UI workflow tests. |
| Link/code inspection | Canonical inspection covers referral codes, campaign codes, campaign referral links, route referral links, composite-code compatibility, redactions, missing evidence, TASK-178 read-only product operator wrapper, TASK-179 focused operator UI, TASK-180 product attribution trace target, TASK-181 adjacent trace navigation, TASK-182 progress/status diagnostics target, TASK-183 progress/status UI navigation, and TASK-184 support hub triage. | Operator can investigate any SaaS link/code source from safe evidence and jump to related campaign, referral, progress, and attribution state. | Product operator inspection API/UI, product attribution trace API/UI, progress/status API/UI, and support triage hub now exist, but support-case persistence remains open. | P1 | TASK-184: Add Referral SaaS operator support workflow hub; next task should add support-case persistence contract or account-safe surfaces | Admin inspection tests; product wrapper tests; redaction tests; missing source tests; UI workflow tests. |
| Referrer/customer safe status | Consumer, distributor, reward summary, and experience routes exist; progress summaries exist for referrers. | Referrer/customer views show safe current status, next action, and progress without leaking internal fraud, audit, provider, or money details. | Role surfaces exist but SaaS safe status copy and contracts are not unified. | P1 | TASK-141: Define Referral SaaS safe status contract | Safe status tests; privacy/no-leak tests; role-scope tests; frontend status tests. |
| Tenant-safe reporting | Distribution reporting, materialized views, finance/admin metrics, and tenant-safe analytics service exist in broader repo. | SaaS tenant can report on campaigns, referrals, links/codes, progress events, attribution, conversion, and exports with freshness rules. | Reporting exists by domain, but Referral SaaS reporting package and export contract need focus. | P1 | TASK-142: Define Referral SaaS reporting and export contract | Reporting accuracy tests; tenant filter tests; export tests; freshness tests. |
| Public API contracts | Referral, progress, campaign, reward summary, partner-ish APIs exist; TASK-174 adds first link/code product wrappers beside the report/export wrappers, TASK-175 centralizes validation recovery mapping, TASK-176 exposes validation idempotency posture, TASK-177 renders recovery/retry posture in the UI, TASK-178 adds the first operator diagnostics wrapper, TASK-180 adds the product attribution trace wrapper, TASK-182 adds the product progress/status diagnostics wrapper, TASK-183 renders that wrapper in the UI, and TASK-184 adds the support workflow hub. | Versioned Referral SaaS public API with auth, schemas, idempotency, errors, examples, and contract tests. | Reporting/export, link/code, operator inspect, attribution trace, progress/status, and support triage wrappers now exist with tested validation recovery, explicit non-idempotent validation posture, and UI visibility, but campaign/support write contracts and OpenAPI packaging remain incomplete. | P1 | TASK-184: Add Referral SaaS operator support workflow hub; next tasks should add OpenAPI packaging or support-case persistence guardrails | OpenAPI/schema tests; auth tests; idempotency tests; error-shape tests. |
| Frontend SaaS workflow | Role-specific React pages and tests exist; TASK-170 account setup, TASK-169/TASK-171 reports/export preview, TASK-172 campaign readiness, TASK-173 link/code workflow, TASK-174 product link/code API seam, TASK-177 validation recovery/retry UI, TASK-179 operator inspect UI, TASK-180 attribution trace API, TASK-181 attribution trace UI, TASK-182 progress/status API, TASK-183 progress/status UI, and TASK-184 support hub now provide focused Referral SaaS admin/API surfaces. | Coherent Referral SaaS workflow: account setup, campaign setup, referral link/code management, event/attribution investigation, reporting, safe status. | Focused surfaces now cover setup, campaign readiness, reports, exports preview, product-backed link/code execution, validation recovery posture, operator inspection, attribution trace, progress/status, and support triage; full product shell cohesion, account-safe status, and customer-facing surfaces remain open. | P1 | TASK-184: Add Referral SaaS operator support workflow hub; next tasks should add account-safe status or product shell cohesion | Frontend route tests; accessibility tests; no-internal-leak tests; workflow smoke tests. |
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

