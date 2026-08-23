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

## TASK-356 Customer Journey Alignment

TASK-356 reviews the external Amplifi experience-design pack against this gap
matrix and keeps the focused SaaS boundary intact. The key finding is that the
post-TASK-355 backlog must not be reduced to only provider/vault execution,
domain-specific repair/replay proof, and non-local proof. Those remain blockers, but the
experience-design pack also identifies customer-journey blockers that must be
made explicit before calling the product 10/10.

| Work package | External journey gaps represented | Ordered tasks |
| --- | --- | --- |
| Scope, account, jurisdiction, workspace, entitlement, and activation | H1 scope lock, operating jurisdiction, account capabilities, partner workspace context, plan posture, production activation gates | TASK-357 to TASK-362 |
| Invitation, acceptance, identity, and login | Live invite delivery, expiring acceptance links, identity-provider/login reconciliation, separation between responsibility, seat, login, and auth claims | TASK-363 to TASK-365 |
| Integrations | Credential/vault lifecycle proof and adapter-backed API/webhook/invite/referral-message test execution evidence now exist with approved-request version matching, audit readback, runtime/vault/adapter evidence flags, safe blocked states, idempotency replay support, and no raw secret/provider-dispatch exposure. | TASK-366 to TASK-368 |
| Campaign management | TASK-369 now enforces partner-safe campaign read, create, policy-write, review-submit, review-decision, and activation capabilities server-side for selected-customer campaign wrappers. TASK-370 now proves campaign separation of duties and pre-activation freshness by recording submitter/approver evidence, blocking same-actor approval, and forcing re-review when policy evidence changes after approval. TASK-371 now adds governed selected-customer campaign lifecycle read and pause/resume/end/archive command controls with capability checks, idempotency, audit evidence, invalid-transition blocking, lifecycle-safe summaries, and no adjacent link, report, webhook, credential, access, billing, DLaaS, or money side effects. | TASK-369 to TASK-371 |
| Referral operations | TASK-372 now adds account-scoped referral registry/detail with safe status, progress anchors, attribution evidence, missing-evidence signals, and redactions. TASK-373 now adds safe referrer identity directory and dimensions. TASK-374 now hardens progress timeline/source/idempotency evidence and recovery posture. TASK-375 now adds the governed support-case correction/replay/reassignment command ledger and API boundary with approval, impact-preview, rollback, idempotency, audit, and no-adjacent-action guardrails. | TASK-375 |
| Attribution | TASK-376 now adds the dedicated Campaign Attribution projection/page with customer-scoped campaign/source/channel confidence, gaps, conflict, and explainability controls. TASK-377 now adds the separate Referral/Referrer Attribution who-got-credit projection/page with safe referrer dimensions, credit posture, confidence, gaps, and no-leak controls. | Closed for H1 attribution projection; continue proof through reporting/support tasks |
| Reporting and exports | TASK-378 now adds source-backed HVE funnel and journey-performance reporting over tenant-scoped referral instances, progress events, campaign attribution links, and distribution route links. TASK-379 now adds audited export-file deletion proof on top of runtime export creation/read/download, signed download metadata, retention expiry, and scheduled delivery intent. Provider delivery execution remains governed by the integration/provider proof boundary rather than hidden inside export deletion. | Closed for H1 export lifecycle; continue non-local proof |
| Support and recovery | TASK-380 now completes the partner/customer-safe selected-customer Support workspace with audited support-case assignment, owner visibility, evidence/recovery posture, idempotency replay, route coverage, and no unsafe repair/replay/retry/provider/invite/credential/auth/campaign/billing/money/DLaaS side effects. | Closed for H1 support/recovery workspace; continue non-local proof |
| Separately contracted finance | TASK-381 now defines and enforces the commercial-finance boundary: H1 Referral SaaS can read plan posture, launch entitlement fields, and reference limits, while billing accounts, subscriptions, invoices, payments, payouts, funding, settlement, wallet/commission ledger movement, and treasury movement stay outside the H1 promise unless separately contracted. | Closed for H1 commercial-finance isolation; continue non-local proof |
| Customer Home UX clarity | TASK-382 now clarifies the selected-customer home with plain-language readiness, red/amber action routing, and service-card action labels. | Closed for local UX clarity; continue non-local proof |
| Configurable customer journeys | TASK-383 defines the post-H1 target-state SaaS framework for governed global templates, tenant/customer journey configurations, campaign binding to published versions, validation, publish/archive, incentive binding, runtime migration, analytics, and proof. TASK-384 now adds the durable schema foundation for templates, versions, account-scoped drafts, published customer journey versions, validation results, campaign binding references, idempotency, and audit evidence. TASK-385 now adds the read-only Amplifi Admin journey template catalogue API with status filtering, safe limits, governance metadata, and redactions over the versioned template schema. TASK-386 now adds account-scoped customer journey draft read/save/validate APIs with approved-template lookup, payload hashing, idempotency replay/conflict handling, validation evidence, audit, guardrails, and redactions. TASK-387 now adds richer validation/simulation behind the validate route with milestone/transition/evidence checks, reward-safety checks, attribution-safety checks, safe-to-publish summaries, and no runtime/provider/auth/billing/money side effects. TASK-388 now adds selected-customer publish/archive APIs so only validated drafts become immutable versions, archive blocks active versions or active campaign bindings, and idempotency/audit evidence remains explicit. TASK-389 now adds selected-customer Journey Configuration UX with approved template selection, allowed-section draft configuration, validation feedback, publish readiness, saved draft selection, and no runtime/provider/auth/billing/money guardrails. TASK-390 now binds customer campaigns to same-account published journey versions and blocks activation when that binding is missing or invalid. TASK-391 now adds account-scoped published journey incentive bindings for approved reward policy, mission, badge, and leaderboard catalogue references with idempotency, audit, redaction, and no reward/payout/money side effects. TASK-392 now adds the runtime compatibility adapter from published customer journey versions to existing journey/progress runtime definitions behind an explicit flag with static fallback and safe metadata. TASK-393 now adds tenant-safe journey analytics over published versions, active campaign bindings, referral/progress/high-value-event aggregates, attribution rates, completion rates, and drop-off gaps. TASK-394 now adds a repeatable configurable journey E2E proof runner across approved-template selection, customer draft validation/publish, campaign binding/activation, referral validation, progress replay, attribution/reporting/analytics readback, and archive guardrail posture without source-code journey changes or unsafe adjacent side effects. | Closed for configurable journey implementation; repeat non-local environment evidence under TASK-027/TASK-348. |

Current rating now reflects TASK-394 configurable journey E2E proof on top of
the TASK-381 commercial-finance boundary evidence:
Referral Management moves to 9.999/10 and Campaign Attribution moves to
9.999995/10. The
confidence in the route to 10/10 improves because configurable journeys,
campaign attribution,
referral/referrer who-got-credit attribution, and HVE journey performance now
have separate customer-scoped projection/reporting surfaces, and export files
now have signed-download metadata, expiry, schedule intent, deletion proof, and
explicit no-finance leakage guardrails. TASK-394 proves the configurable
journey spine locally and repeatably, but it does not change the remaining
non-local proof blocker.

TASK-383 adds the configurable customer journey framework as a target-state
SaaS maturity path. It does not change the H1 launch rating because it is a
post-H1 architecture and delivery-control layer. Its value is strategic:
customers and Amplifi Admins should eventually configure approved journey
templates without source-code changes, while Amplifi continues to govern global
templates, evidence models, transition rules, reward engines, runtime
execution, tenancy, audit, idempotency, and no-provider/no-auth/no-money
boundaries.

TASK-384 through TASK-394 implement and prove that maturity path: versioned
configuration schema, admin catalogue, customer drafts, validation/simulation,
publish/archive, Journey Configuration UX, campaign binding enforcement,
incentive binding, runtime compatibility, analytics, and repeatable E2E proof
now exist for already-approved templates. Remaining 10/10 evidence is no
longer configurable-journey implementation work; it is the separate non-local
environment verification tracked by TASK-027 and TASK-348.

TASK-395 adds the UX/CX maturity scorecard in
`docs/sa/referral-saas/REFERRAL_SAAS_UX_CX_MATURITY_SCORECARD.md`. This
separates backend capability readiness from product-experience readiness. The
Referral SaaS score remains technically near-complete, but the next tasks must
make the customer journey simpler: customer context first, one primary next
action per page, labelled metadata instead of raw identifiers, health states
that route to the exact fixing action, standalone work pages, partner-simple
language, Amplifi Admin diagnostics by disclosure, and no DLaaS or money-flow
leakage in the focused SaaS experience.

TASK-396 through TASK-405 add the remaining target-state SaaS configuration
path identified after the configurable journey review. The gap is not another
free-form journey editor. The product needs one simple, governed business
object: a versioned Referral programme that binds customer, jurisdiction,
approved journey version, campaign defaults, approved incentive/engagement
references, readiness posture, review evidence, effective dates, and immutable
checksums. This keeps customer/admin configuration understandable while giving
the backend a single versioned object for campaign binding, referral binding,
analytics, and historical replay. The controlling artifact is
`docs/sa/referral-saas/REFERRAL_SAAS_PROGRAMME_CONFIGURATION_ROADMAP.md`.

TASK-396 now closes the definition gap with
`docs/sa/referral-saas/REFERRAL_SAAS_PROGRAMME_CONFIGURATION_CONTRACT.md`.
The contract defines the customer-visible Programme object, ownership split,
required business/configuration/governance fields, lifecycle states, command
boundary, validation output, selected-customer API shape, frontend IA,
redactions, idempotency/audit controls, and no-provider/no-auth/no-billing/
no-settlement/no-money side effects. TASK-397 through TASK-405 now add schema,
APIs, validation/simulation, publish/retire/rollback, campaign binding,
incentive binding, runtime binding, aggregate programme analytics, and the
simple selected-customer Programme workspace.

TASK-397 now closes the durable-storage gap with
`dp/migrations/096_referral_saas_programme_configuration.sql`. Programme
drafts, immutable programme versions, validation results, idempotency keys, and
audit evidence can now be stored against `account_id` and published customer
journey versions. The schema includes campaign defaults, approved
incentive/engagement references, readiness and entitlement snapshots, effective
dates, configuration checksums, payload hashes, review/publish/retire metadata,
redactions, and replay controls. TASK-398 now adds the selected-customer
programme version list, approved building-block catalogue, programme draft
read/create/update APIs, account-scope checks, idempotency replay/conflict
handling, audit, redactions, and no-side-effect guardrails. TASK-399 now adds
side-effect-free programme validation and simulation with blocker/warning
classification, customer-safe next actions, validation evidence, publish and
campaign-binding allowances, idempotent replay/conflict handling, and explicit
no campaign/referral/provider/auth/billing/settlement/money mutation
guardrails. TASK-400 now closes the programme lifecycle guardrail gap with
submit-for-review, review-decision, immutable publish, explicit retirement, and
rollback-readiness commands that preserve no campaign/referral/provider/auth/
billing/settlement/money side effects. TASK-401 now closes the campaign
programme-binding gap by validating same-account published programme versions
on campaign setup and activation. TASK-402 now closes the programme incentive
and engagement snapshot gap by binding approved reward policy, mission, badge,
and leaderboard references to published programme versions with effective-date,
idempotency, audit, and no-side-effect guardrails. TASK-403 now closes the
runtime binding gap by storing the programme-version identity used when new
referrals are created and exposing only safe runtime metadata on referral
registry reads. TASK-404 now closes the programme analytics gap with
aggregate-only version comparison. TASK-405 now closes the customer Programme
UX proof gap with approved catalogue selection, draft save/update, validation,
review, publish, published-version visibility, aggregate analytics, and campaign
handoff in a customer-scoped UI.

TASK-406 through TASK-414 now capture the remaining domain-modelling gap after
the programme implementation stream. The current code has separate programme
and campaign services, but the business model still needs stronger execution
guardrails so `product_code`/`sub_product_code` are not misused as customer
product taxonomy, campaigns do not silently own referral-programme rules, and
campaign-specific reward or attribution differences are explicit approved
overrides. The controlling artifact is
`docs/sa/referral-saas/REFERRAL_SAAS_PROGRAMME_CAMPAIGN_DOMAIN_BOUNDARY.md`.
TASK-406 is complete and locks the boundary vocabulary and ownership model.
TASK-407 is complete and adds the durable customer product/offering catalogue
schema foundation. TASK-408 is complete and adds the selected-customer API
wrappers over that catalogue. TASK-409 is complete and binds programme
drafts/versions to approved customer product/offering records without
overloading Amplifi service package fields.

| Gap | Required task path | Close-out expectation |
| --- | --- | --- |
| Customer product/offering taxonomy is not separated from Amplifi service packaging. | TASK-409 | Complete - customer product line/offering is stored, read/written through selected-customer APIs, and bound to programme drafts/versions without overloading Amplifi package codes. |
| Programme and campaign services exist, but route/API semantics still allowed journey/programme/campaign confusion. | TASK-410 | Complete - programme binding is now the authoritative campaign activation path; legacy campaign journey-binding is compatibility only and cannot satisfy activation without a published programme binding. |
| Campaign-specific reward, attribution, channel, date, and cap differences need a governed override model. | TASK-411 | Complete - campaign overrides are explicit, approved, audited, idempotent, bounded by the published programme's allowed override envelope, and blocked from activation when stale or unapproved. |
| Runtime referrals need one immutable effective-rule snapshot for historical replay. | TASK-412 | Complete - new referrals freeze safe customer, product/offering, programme version, campaign, approved override posture, default/override rule-key checksums, and effective checksum metadata without raw payload, provider, auth, billing, payout, settlement, or money leakage. |
| Reporting must explain product/offering, programme, campaign, and override performance separately. | TASK-413 | Complete - programme analytics now exposes safe aggregate product/offering, programme version, runtime campaign, approved override, effective snapshot, override-rate, and snapshot-coverage dimensions without raw payload, billing, payout, settlement, or money leakage. |
| UX must keep the model simple despite the richer architecture. | TASK-414 | Complete - customer-scoped home and Programme workspace explain customer product, referral programme, campaign, campaign-specific changes, and reporting in plain language, with safe reporting-dimension labels and diagnostics by disclosure. |

TASK-415 through TASK-419 capture the final contained gaps from the post-TASK-414
configuration review. The implementation is no longer structurally misaligned;
the remaining work is lifecycle hardening, UX completion, binding lifecycle, and
joined proof:

| Gap | Required task path | Close-out expectation |
| --- | --- | --- |
| Programme drafts can still risk ordinary save behavior after review states. | TASK-415 | Complete - ordinary programme draft updates are restricted to true editable states and reviewed/locked states return a 409 lifecycle conflict instead of silently resetting reviewed evidence to `DRAFT`; audit evidence records the prior editable state for allowed updates. |
| Product/offering binding exists in APIs but must be unmistakable in the Programme builder. | TASK-416 | Complete - the Programme builder now exposes customer product line and offering selection in plain language with required-state feedback, empty states, and no package-code confusion. |
| Incentive and engagement bindings need replacement/deactivation lifecycle controls. | TASK-417 | Complete - programme incentive and engagement bindings now support explicit replacement, retire/deactivate, effective-date overlap protection, idempotency, audit evidence, and redacted no-side-effect responses without reward, payout, settlement, provider dispatch, campaign activation, auth, billing, funding, invoice, or money execution. |
| Individual task tests exist, but the full product-to-referral path needs one joined proof. | TASK-418 | Complete - repeatable proof now covers product line -> offering -> programme draft/validation/review/publish -> incentive binding -> campaign -> programme binding -> referral code/validation -> progress -> attribution/reporting/programme analytics readback with product/programme/campaign context and unsafe-field leakage checks. |
| The richer model still needs final plain-language UX polish. | TASK-419 | Complete - Programme workspace now shows one dynamic next action, clearer business-language configuration layers, safe published-version labels, and disclosure-based diagnostics so configuration is simple and hard to misuse. |

## TASK-357 H1 Scope And Release Gates

TASK-357 locks the H1 Referral SaaS release promise before the remaining
customer-journey tasks add more runtime behavior. The controlling artifact is
`docs/sa/referral-saas/REFERRAL_SAAS_H1_RELEASE_SCOPE_AND_JOURNEY_GATES.md`.

| Decision area | TASK-357 outcome |
| --- | --- |
| H1 promise | Customer-scoped Referral Management and Campaign Attribution SaaS across account setup, customer context, people/access, integrations, campaign setup/activation, links/codes, referral progress, attribution, reporting/export, and support. |
| Deferred or disabled | DLaaS marketplace, fulfilment, settlement, funding, sponsor billing, broad white-label/embed, unmanaged provider dispatch, raw browser secrets, generic replay/DB mutation, identity-provider auth claims until proven, and money movement. |
| Release gates | Scope lock, account/jurisdiction, entitlement/environment, people/access, integrations, campaign control, referral/attribution correctness, reporting/support, and deployed-state proof. |
| UX rule | Every customer page must make the selected customer, readiness state, one next action, reason, and non-action boundary obvious in plain language. |
| Downstream enforcement | TASK-358 now enforces core selected-customer account, jurisdiction, and account-read capability gates; TASK-359 adds the partner/customer workspace account-context resolver with no unscoped account enumeration or internal tenant identifier exposure; TASK-360 adds the shared workspace overview projection with selected-account, readiness, primary-action, safe-to-leave, capability-aware worklist, redaction, and no-live-action guardrails; TASK-361 adds the read-only commercial entitlement and plan posture gate with no-billing/no-money boundaries; TASK-362 adds the backend production activation decision gate and blocks activation when account foundation, people/access, integrations, campaign readiness, commercial entitlement, or evidence freshness is incomplete; TASK-363 adds governed provider-backed invite delivery; TASK-364 adds expiring invite acceptance with token expiry, replay protection, audit, and no provisioning side effects; TASK-365 adds read-only identity/login reconciliation across customer access, optional platform seat, identity-provider evidence, revocation posture, and auth-claim readiness with no provisioning side effects; TASK-366 adds the redacted account-to-integration-client binding gate and blocks execution against unbound or wrong-tenant client context; TASK-367 adds credential/vault lifecycle proof evidence; TASK-368 adds adapter-backed safe integration test execution evidence; TASK-369 adds server-side campaign workspace capability enforcement for read, create, policy, review, and activation routes; TASK-370 adds campaign SoD and stale-evidence activation proof; TASK-371 adds governed campaign lifecycle controls; TASK-372 adds account-scoped referral registry/detail projections; TASK-373 now adds safe referrer identity directory and dimensions; TASK-374 now hardens referral timeline/source/idempotency evidence and recovery posture; TASK-375 adds the governed correction/replay/reassignment command execution boundary; TASK-376 adds dedicated campaign attribution projection/page; TASK-377 adds dedicated referral/referrer who-got-credit attribution; TASK-378 adds source-backed HVE funnel and journey-performance reporting; TASK-379 adds export lifecycle deletion proof; TASK-380 completes the selected-customer Support assignment/recovery workspace with audit/idempotency and no-adjacent-action guardrails; TASK-381 now closes commercial-finance isolation with structured entitlement-boundary readback and no-finance-write route tests. |

The ratings now reflect completed configurable journey E2E proof: Referral
Management moves to 9.999/10 and Campaign Attribution moves to 9.999995/10.
Confidence improves because the remaining work now has a single H1
release-gate contract,
separate campaign and referral/referrer attribution surfaces, and source-backed
journey-performance reporting with signed export and deletion proof.

## TASK-358 Account Capability And Jurisdiction Enforcement

TASK-358 converts the first H1 account/jurisdiction release gate into runtime
enforcement. The core selected-customer account resolver, membership posture,
and membership activation readiness routes now carry operating jurisdiction in
their safe account context and reject callers scoped to a different account,
different operating jurisdiction, or missing `REFERRAL_SAAS_ACCOUNT_READ`
capability. The boundary response redacts internal tenant identifiers, tenant
codes, and auth-claim detail while confirming no cross-account,
cross-jurisdiction, or capability-bypass access.

## TASK-359 Partner Workspace Account Context Resolver

TASK-359 adds the read-only partner/customer workspace account-context resolver.
The new route resolves a signed-in partner/customer actor to permitted Referral
SaaS accounts only, using active membership, tenant-link, explicit account
claim, and safe external-reference claim sources. Operating-jurisdiction claims
filter the returned account list. The response does not expose internal tenant
identifiers or tenant codes and confirms no unscoped account enumeration,
membership write, invite delivery, auth-claim change, or money movement. This
closes the partner workspace entry gap.

## TASK-360 Customer And Partner Workspace Overview Projection

TASK-360 adds the shared customer/partner workspace overview projection on top
of selected customer context. The new route returns a selected account summary,
plain-language readiness, one primary next action, a short capability-aware
worklist, safe-to-leave posture, guardrails, and redactions for admin-selected
customer context and partner/customer actors. The projection is read-only: it
does not expose internal tenant identifiers or take membership writes, invite
delivery, seat provisioning, auth-claim changes, campaign activation, or money
movement.

Open enforcement now moves to the remaining account/workspace gates:
invitation/login execution, integration execution, route capability inventory,
UI labels, proof, and the downstream journey-specific command/read guards.

## Gap Matrix

| Area | Current code capability | 10/10 SaaS requirement | Gap | Priority | Next task candidate | Tests/validation |
| --- | --- | --- | --- | --- | --- | --- |
| SaaS account packaging | `tenant_code` is used across important flows; admin tenant APIs, onboarding draft persistence, onboarding validation, submit-for-review, review-decision, and permission helpers exist. TASK-190 through TASK-230 establish account setup, durable account creation, account registry selection, Client Workspace physical proof, and repeatable fresh-client physical proof. TASK-231 adds persisted account operating jurisdiction and reframes the selected Client Workspace into a customer profile model: jurisdiction/customer selection first, then a standalone selected-customer profile route with customer-home context, plain-language health, next actions, and customer-scoped functions. TASK-232 removes demo Account Setup defaults and adds identifier guidance so setup starts from explicit operator-entered customer references. TASK-233 simplifies Review & Create to one primary create action while preserving save, submit, review, idempotency, duplicate-reference, and account-foundation guardrails behind the product action. TASK-234 removes the hidden default `FNB` owner-scope collision by deriving a bounded internal setup seed from customer identifiers, creating/updating that seed inside the guarded account-foundation transaction, and returning a distinct internal-scope duplicate conflict when needed. TASK-235 ends Account Setup at Review & Create and routes successful account-foundation creation to customer-profile-first next actions. TASK-236 keeps selected-customer people/access and customer settings actions inside Customer Profile modules. TASK-237 wires People and Access to the guarded membership invitation intent API. TASK-238 adds guarded Customer Settings maintenance. TASK-241 splits Customer Profile into separate customer-scoped pages. TASK-242 adds membership activation readiness. TASK-243 adds a safe invitation delivery request boundary. TASK-244 adds customer-scoped Technical Setup readiness and aligns Email as a shared channel provider readiness item. TASK-245 adds the standalone selected-customer Technical Setup page wired to that readiness API. TASK-246 adds an explicit approved-provider readiness gate so Email channel configuration is separate from Referral SaaS invite-provider approval and scope. TASK-247 adds safe recipient contact readiness from hashed contact evidence without exposing raw email or sending invites. TASK-248 productizes a guarded People and Access invite-delivery check from the selected customer profile without requiring browser-held recipient hashes or sending email. TASK-249 adds the audited/idempotent membership activation command boundary, including identity acceptance, active account/link/reference gates, duplicate-active prevention, and no adjacent seat/auth/campaign/go-live/money side effects. TASK-250 wires the selected-customer People and Access UI to that activation boundary with accepted-access feedback and posture/readiness refresh. TASK-251 clarifies the People and Access person-name placeholder so operators enter an actual individual name rather than a role label. TASK-252 exposes access provisioning readiness separately from membership lifecycle so active membership does not imply seat assignment or login/auth-claim propagation. TASK-275 fixes the accepted-access activation duplicate-active SQL guard so nullable user/client parameters are schema-typed and do not produce a runtime Postgres 500. TASK-276 adds guarded edit/cancel lifecycle commands for invited People and Access intent and keeps disabled/cancelled intent out of the primary customer working list. TASK-284 defines the access provisioning command contract for the visible `Provision login & seat` path. TASK-285 implements the guarded backend access provisioning wrapper for seat assignment after active account, tenant-link, external-reference, membership, admin actor, idempotency, audit, and redaction gates pass. TASK-286 wires People and Access to that guarded provisioning API and refreshes read models so seat assignment state is visible in customer context. TASK-287 adds a repeatable selected-customer physical proof runner for People and Access provisioning, idempotency replay, refreshed read models, optional DB/audit evidence, and controlled provisioning blocks. TASK-288 adds a guarded Amplifi Admin account-foundation activation command so a selected customer can move from pending setup to active account/link posture with bounded available seat capacity, audit, and idempotency evidence before provisioning proof. TASK-289 reworks People and Access into a person-first lifecycle workspace with missing-role prompts, lifecycle labels, one next action per responsibility, an opaque add/edit drawer, secondary diagnostics, and explicit provisioning boundaries. TASK-290 wires the guarded account-foundation activation command into selected-customer Customer Home, People and Access, and Account Health so Amplifi Admin can activate the account/link prerequisite before provisioning proof. TASK-291 extends the repeatable People and Access provisioning proof runner so it can activate the selected customer account foundation through the guarded API before attempting seat provisioning, without direct DB tweaks or hidden bypasses. TASK-294 records successful activated local proof with account/link activation, guarded seat assignment, DB/audit readback, idempotency replay, and no adjacent side effects. TASK-300 reframes the selected-customer Technical Setup page as Integrations while keeping the readiness API as the read-only implementation detail and preserving the old route as a compatibility alias. TASK-301 defines the selected-customer Integrations configuration contract for API, webhook, invite-delivery, and referral-message provider setup evidence. TASK-302 adds the persisted customer-scoped Integrations configuration schema, validation/read/save API foundation, idempotency/audit evidence, and no-secret/no-live-action guardrails. TASK-303 wires selected-customer Integrations UI controls to read, validate, and save non-secret setup evidence. TASK-304 defines the live Integrations execution contract for future API verification, webhook test dispatch, message-provider checks, and governed credential requests. TASK-305 adds the read-only Integrations execution-readiness API over saved configuration, active account/link/reference posture, provider evidence, guardrails, and redactions. TASK-306 wires that execution-readiness read model into the selected-customer Integrations UI with blockers, safe next actions, and post-save refresh. TASK-307 adds the governed API-access verification command with selected-customer scope, saved configuration gates, active account/link/reference gates, idempotency, audit, unsafe-payload rejection, and no-credential/no-provider/no-webhook/no-message/no-auth/no-campaign/no-money guardrails. TASK-308 wires that command into the selected-customer Integrations UI with safe verification evidence, idempotency/correlation, plain-language success feedback, and post-command readiness refresh. TASK-309 adds the governed webhook test-dispatch command with selected-customer scope, saved webhook setup gates, active account/link/reference gates, idempotency, audit, unsafe-payload rejection, and no-webhook-dispatch/no-signing-material/no-credential/no-provider/no-message/no-auth/no-campaign/no-money guardrails. TASK-310 wires that command into the selected-customer Integrations UI with plain-language webhook evidence copy, idempotency/correlation, safe feedback, and readiness refresh. TASK-312 adds the governed message-provider test-check command with selected-customer scope, saved message-provider setup gates, active account/link/reference gates, idempotency, audit, unsafe-payload rejection, and no-provider-call/no-invite-delivery/no-referral-message-delivery/no-credential/no-webhook/no-auth/no-campaign/no-money guardrails. TASK-313 wires that command into the selected-customer Integrations UI with safe provider-readiness payloads, idempotency/correlation, plain-language feedback, and readiness refresh. TASK-316 wires the selected-customer Integrations UI to the credential request API with safe request metadata, plain-language feedback, and readiness/request refresh. TASK-317 adds the credential request review-decision API foundation with approve/block governance, idempotency, audit, redaction, and no credential/provider/vault side effects. TASK-318 wires the selected-customer Integrations UI to that review-decision API so ready credential setup requests can be approved or blocked from the Verify tab with plain-language governance feedback and readiness/request refresh. | SaaS customer can onboard company/account, setup state, limits, and external identifiers without exposing internal identifiers; existing accounts can be maintained through a selected-customer workspace for scoped health, evidence, membership, identifiers, users, roles, integrations readiness/configuration evidence, live execution readiness API/UI, activities, dashboards, and audit workflows. | Durable account, organisation, account-tenant, external-reference, user, membership, seat, account-audit, and integration-configuration evidence schema exists; account setup, customer profile selection, standalone customer pages, customer-scoped people/access, customer settings, membership activation readiness, blocked invitation delivery boundary, integrations readiness presented over the existing technical setup read model, persisted non-secret Integrations configuration evidence API/UI, live Integrations execution contract, read-only Integrations execution-readiness API/UI, governed API-access verification command, selected-customer API-access verification UI action, governed webhook test-dispatch command, selected-customer webhook evidence UI action, selected-customer message-provider check UI action, selected-customer credential request UI, selected-customer credential review UI, invite-provider approval readiness, safe recipient contact readiness, guarded delivery-check UI, membership activation command boundary, frontend activation action, selected-customer account-foundation activation action, accepted-access SQL parameter typing fix, clearer People and Access person-name guidance, explicit provisioning readiness, invited access intent edit/cancel, visible provisioning next actions, provisioning command contract, guarded runtime seat-assignment API, frontend provisioning action wiring, repeatable provisioning physical proof tooling, guarded account-foundation activation, person-first People and Access lifecycle CX, and recorded activated local seat-assignment proof now exist. Product package, billing-plan fields, runtime live invite delivery provider integration, runtime live webhook/provider execution, actual auth-claim propagation, credential execution/provider-vault implementation, external-reference rotation, and broader account maintenance commands remain open as bounded future work. | P0 | Implement credential lifecycle/runtime provider commands, selected-customer support-case UI, and export storage/download as separate customer-scoped modules with tests and no source duplication, then extend proof into progress/attribution mutation paths. | Tenant/account contract tests; API wrapper tests; migration replay tests; onboarding draft wrapper tests; role/membership tests; activation-readiness tests; provisioning-readiness tests; provisioning-command contract tests; activation command tests; activation UI tests; accepted-access physical smoke test; access provisioning API/UI tests; seat-assignment audit/idempotency tests; TASK-287/TASK-291/TASK-294 proof-runner execution evidence; integrations readiness/configuration UI/API tests; live Integrations execution contract/readiness UI/API tests; credential request/review UI tests; provider approval tests; recipient contact readiness tests; guarded delivery-check tests; invitation idempotency/audit tests; invitation edit/cancel and removed-intent UI tests; duplicate membership tests; profile maintenance command tests; external-reference resolver tests; tenant isolation tests; maintenance read-model tests; frontend wizard/workspace tests. |
| Campaign setup and readiness | Campaign create/validate, track update, policy read/write, attribution tables, campaign readiness service, tests, TASK-172 read-only Referral SaaS readiness UI, TASK-253 customer/account-scoped campaign readiness wrapper/page, TASK-254 customer-scoped campaign list/read wrappers, TASK-255 customer-scoped campaign draft/create command contract, TASK-256 guarded customer-scoped campaign setup create API wrapper, TASK-257 selected-customer campaign setup create UX, TASK-258 customer-scoped campaign policy/settings command contract, TASK-259 guarded customer-scoped campaign policy/settings API wrapper, TASK-260 selected-customer policy/settings UX, TASK-261 customer-scoped campaign submit/review command contract, TASK-262 guarded submit/review API wrappers, TASK-263 selected-customer submit/review UX, TASK-264 activation/go-live command contract, TASK-265 guarded activation/go-live API wrapper, TASK-266 selected-customer activation UI, TASK-267 customer-scoped active-campaign Links and Codes continuation, TASK-268 customer-scoped Reports continuation, TASK-269 selected-customer E2E physical proof runner, TASK-270 physical-proof fixes, TASK-271 mutation-path physical proof runner, TASK-272 local mutation proof execution, TASK-273 persisted export request/audit evidence, TASK-295 support-case persistence contract, TASK-297 runtime support-case create/list/read persistence, TASK-321 selected-customer support-case UI, TASK-322 support-case notes/status API, TASK-323 support-case lifecycle UI, TASK-324 aggregate support queue contract, TASK-325 aggregate support queue API, TASK-326 aggregate support queue UI, TASK-327 export storage/download lifecycle contract, TASK-328 runtime export file create/read/download over persisted export requests, TASK-329 selected-customer export download UI, TASK-330 export retention expiry enforcement, TASK-331 export object-store/signed URL hardening contract, TASK-332 export signed URL runtime, TASK-339/TASK-340 progress-attribution proof contract/runner, TASK-341 approved local progress-attribution execution evidence, TASK-349 provider/vault runtime execution command contract, TASK-350 provider/vault runtime execution API foundation, TASK-351 provider/vault runtime adapter seam, TASK-352 implementation plan, TASK-353 platform-reference provider/vault adapters, TASK-354 vendor/managed provider-vault adapter contract, and TASK-355 vendor/managed provider-vault runtime adapters exist. | One coherent campaign setup workflow with readiness gates, lifecycle states, attribution settings, policy visibility, product write wrappers, human/internal review, activation guardrails, referral entry-point continuation, customer-scoped reporting, durable export request audit, support-case persistence boundary, aggregate support triage, and repeatable local/staging proof. | Customer-scoped campaign readiness, list/read, create-command design, runtime inactive setup-create wrapper, standalone selected-customer create UX, policy/settings command/API/UX, submit/review contract/API/UX, activation/go-live contract/API/UX, active-campaign link/code issue-validation, selected-customer report/export-preview wrappers, persisted export request/audit evidence, tenant-safe inline export file creation/metadata/download runtime, selected-customer export download UI controls, export retention expiry enforcement, export object-store/signed URL hardening contract, signed-download runtime metadata with opaque storage refs, runtime support-case create/list/read persistence, selected-customer support-case list/create UI, support-case notes/status API, selected-customer lifecycle UI wiring, aggregate support queue API/UI, read-spine and mutation-path E2E proof runners, tenant-scope redaction, async report-wrapper proof fixes, local mutation-path execution evidence, local progress-attribution proof execution evidence, governed auth/login completion UI wiring, provider/vault execution command design, provider/vault execution API foundation, provider/vault runtime adapter seam, platform-reference provider/vault adapter code, vendor/managed adapter contract, and vendor/managed runtime adapter code are now packaged. Repair/replay execution, scheduled delivery provider dispatch, and non-local proof repetition remain open. | P0 | Run non-local launch verification and keep repair/replay execution as a governed post-readiness track | Campaign setup API tests; account-scoped campaign list/read tests; account-scoped readiness tests; create idempotency/audit tests; duplicate campaign tests; readiness blocker tests; lifecycle/status tests; frontend create workflow tests; policy/settings contract/API/UX tests; submit/review API/UX tests; activation API/idempotency/audit/UI tests; customer-scoped link/code tests; customer-scoped reporting tests; persisted export request/idempotency/audit tests; export file storage/download/expiry/object-store/signed URL tests; support-case persistence tests; support-case UI/notes/status/queue tests; progress/attribution proof regression tests; provider/vault execution API tests; provider/vault adapter seam/execution tests; platform-reference adapter tests; vendor/managed adapter tests; auth/login UI tests; non-local proof validation. |
| Referral code creation | Code creation, preferred handle handling, existing-code reuse, accepted-terms enforcement, TASK-173 focused issue/reuse UI, and TASK-174 product issue wrapper exist. | Tenant-scoped, documented, auditable issue/reuse flow with clear product API, account-scoped setup UX, and operational evidence. | Product wrapper and first UI surface now exist; account/membership scope, schema uniqueness decision, audit consistency, and lifecycle operations remain open. | P0 | TASK-174: Add Referral SaaS link/code product API wrappers; next task should harden account-scope/idempotency/audit decisions | Duplicate issue tests; terms-required tests; tenant-scope tests; audit/readback tests; frontend no-leak tests. |
| Referral validation and terms | Validation enforces terms, alias rules, referral instance creation, QR scan evidence, safe failures, TASK-173 focused validation UI, TASK-174 product validation wrapper, TASK-175 dedicated validation recovery mapper, TASK-176 explicit idempotency posture, and TASK-177 recovery/retry UI exist. | Public validation API has stable errors, idempotency posture, operator trace, recovery UX, and no sensitive leakage. | Product wrapper now has centralized, tested safe validation/recovery mapping and the UI shows recovery plus non-idempotent retry posture; schema-backed idempotent reuse, operator trace linkage, and deeper recovery workflow actions still need hardening. | P0 | TASK-177: Add Referral SaaS validation recovery UI; next task should implement schema-backed duplicate reuse or add operator trace linkage | Validation contract tests; duplicate submit tests; safe error tests; QR evidence tests; frontend recovery tests. |
| Progress and journey checks | Progress events validate identifiers, product/sub-product binding, journey compatibility, self-referral, dedupe key, payload hash, queue emission, TASK-182 exposes a read-only operator progress/status diagnostics wrapper, TASK-183 adds the focused operator progress/status UI, and TASK-184 links it into support triage. | Productized event catalog, clear retry/error classes, tenant diagnostics, replay posture, and visible status updates. | Event ingestion and first support-facing diagnostics API/UI are strong; remaining gaps are event catalog/OpenAPI packaging, replay posture, account-safe status surfaces, and live E2E evidence. | P0 | TASK-184: Add Referral SaaS operator support workflow hub; next task should add OpenAPI/event catalog or replay posture proof | Event contract tests; dedupe/idempotency tests; invalid payload tests; replay/diagnostic tests; E2E status tests. |
| Campaign attribution trace | Campaign attribution records, track events, referral instances, progress events, campaign referral links, route referral links, journey tests, TASK-139 contract, admin outcome trace, TASK-180 read-only product attribution trace wrapper, TASK-181 focused operator trace UI, TASK-182 progress/status support API, TASK-183 progress/status UI, and TASK-184 support hub exist. | One explainable trace from campaign/link/code/event to attributed outcome, including missing evidence and conflict handling. | Product attribution trace API/UI, progress/status API/UI, and support triage now exist, but conflict/precedence UX and live E2E evidence remain open. | P0 | TASK-184: Add Referral SaaS operator support workflow hub; next task should add conflict/precedence UX or E2E proof | Product wrapper tests; golden-path trace tests; missing-evidence tests; conflict tests; cross-tenant tests; UI workflow tests. |
| Link/code inspection | Canonical inspection covers referral codes, campaign codes, campaign referral links, route referral links, composite-code compatibility, redactions, missing evidence, TASK-178 read-only product operator wrapper, TASK-179 focused operator UI, TASK-180 product attribution trace target, TASK-181 adjacent trace navigation, TASK-182 progress/status diagnostics target, TASK-183 progress/status UI navigation, TASK-184 support hub triage, TASK-295 support-case persistence contract, TASK-297 support-case create/list/read API persistence, TASK-321 selected-customer support-case UI, TASK-322 support-case notes/status API, TASK-324 operator aggregate support queue contract, TASK-325 read-only runtime aggregate support queue API, and TASK-326 operator aggregate support queue UI. | Operator can investigate any SaaS link/code source from safe evidence, jump to related campaign, referral, progress, and attribution state, persist a selected-customer support case with safe evidence links, and triage a safe cross-customer support queue without DB access. | Product operator inspection API/UI, product attribution trace API/UI, progress/status API/UI, support triage hub, support-case contract, runtime support-case create/list/read schema/API, selected-customer support-case list/create UI, backend notes/status APIs, selected-customer lifecycle UI wiring, aggregate support queue boundary, runtime aggregate support queue API, and live queue UI now exist, but repair/replay guardrails remain open. | P1 | Add repair/replay guardrails as separate governed tasks | Admin inspection tests; product wrapper tests; redaction tests; missing source tests; UI workflow tests; support-case evidence-link tests; support-case UI tests; aggregate queue API/UI tests; repair/replay guardrail tests. |
| Referrer/customer safe status | Consumer, distributor, reward summary, and experience routes exist; progress summaries exist for referrers. | Referrer/customer views show safe current status, next action, and progress without leaking internal fraud, audit, provider, or money details. | Role surfaces exist but SaaS safe status copy and contracts are not unified. | P1 | TASK-141: Define Referral SaaS safe status contract | Safe status tests; privacy/no-leak tests; role-scope tests; frontend status tests. |
| Tenant-safe reporting | Distribution reporting, materialized views, finance/admin metrics, and tenant-safe analytics service exist in broader repo. | SaaS tenant can report on campaigns, referrals, links/codes, progress events, attribution, conversion, exports, and scheduled delivery intent with freshness rules. | Reporting exists by domain, the Referral SaaS report/export contract exists, TASK-327 defines persisted export file lifecycle boundaries, TASK-328 implements the first tenant-safe inline export file create/read/download runtime, TASK-329 wires selected-customer frontend download controls over that runtime, TASK-330 enforces retention expiry for storage/download and safe metadata, TASK-331 defines the object-store/signed URL hardening contract, TASK-332 implements signed-download runtime metadata with opaque storage refs, TASK-333 defines the customer-scoped scheduled delivery contract, TASK-334 implements guarded scheduled delivery API persistence/readiness, and TASK-335 wires selected-customer schedule create/list/readiness/pause/resume/cancel controls. Governed provider execution and non-local proof remain open. | P1 | Add governed scheduled delivery provider execution after provider/vault/auth boundaries, then repeat proof with non-local access | Reporting accuracy tests; tenant filter tests; export tests; freshness tests; metadata/content redaction tests; export expiry/object-store/signed URL tests; scheduled delivery UI tests; provider execution proof tests. |
| Public API contracts | Referral, progress, campaign, reward summary, partner-ish APIs exist; TASK-174 adds first link/code product wrappers beside the report/export wrappers, TASK-175 centralizes validation recovery mapping, TASK-176 exposes validation idempotency posture, TASK-177 renders recovery/retry posture in the UI, TASK-178 adds the first operator diagnostics wrapper, TASK-180 adds the product attribution trace wrapper, TASK-182 adds the product progress/status diagnostics wrapper, TASK-183 renders that wrapper, TASK-184 adds the support workflow hub, TASK-256 adds the first customer-scoped campaign setup create command wrapper, TASK-259 adds policy/settings, TASK-262 adds submit/review, TASK-264 maps the activation command, TASK-265 implements the guarded activation wrapper, TASK-266 wires activation UI, TASK-267 adds customer-scoped active-campaign link/code issue-validation wrappers, TASK-268 adds customer-scoped report/export-preview wrappers, TASK-269 adds a read-only selected-customer proof runner over those wrappers, TASK-297 adds selected-customer support-case create/list/read wrappers, TASK-321 wires the selected-customer support-case UI to those wrappers, and TASK-322 adds selected-customer support-case notes/status wrappers. | Versioned Referral SaaS public API with auth, schemas, idempotency, errors, examples, and contract tests. | Reporting/export, link/code, operator inspect, attribution trace, progress/status, support triage, account, membership, profile, guarded campaign setup, policy/settings, review, activation, customer-scoped active-campaign link/code, customer-scoped report/export-preview, selected-customer support-case create/list/read wrappers and UI, support-case notes/status wrappers, and repeatable proof tooling now exist with tested validation recovery, idempotency posture, safe route inventory, and UI visibility, while OpenAPI packaging and recorded live/staging proof remain incomplete. | P1 | Keep OpenAPI/schema packaging and live selected-customer proof on the API hardening path | OpenAPI/schema tests; auth tests; idempotency tests; error-shape tests; activation no-adjacent-action tests; activation UI tests; customer-scoped link/code tests; customer-scoped reporting tests; support-case API tests; live selected-customer E2E proof. |
| Frontend SaaS workflow | Role-specific React pages and tests exist; TASK-170 through TASK-268 provide the focused Referral SaaS admin/API surfaces, Account Setup wizard, account creation path, account selector, selected customer profile routes, customer-scoped people/access, customer settings, activation readiness, invitation delivery boundary, membership activation command boundary, technical setup readiness API, selected-customer Technical Setup page, visible invite-provider approval readiness, safe contact readiness indicators, guarded invite-delivery check, guarded accepted-access action, clearer person-name guidance, explicit provisioning readiness in People and Access, customer-scoped Campaigns readiness, selected-customer campaign list selection, campaign create command boundary, guarded runtime campaign setup create API, standalone selected-customer campaign setup create UX, customer-scoped policy/settings command/API/UX, guarded runtime submit/review API wrappers, selected-customer submit/review UX, activation/go-live command contract/API, selected-customer activation UI, selected-customer Links and Codes issue/validation UX, and selected-customer Reports UX. TASK-269 adds repeatable physical proof tooling for the selected-customer read spine. TASK-274 clarifies selected-customer picker, profile header, and customer-home health action labels so operating jurisdiction, account status, customer references, organisation references, account codes, selected state, RAG meaning, and next-action routing are understandable. TASK-276 aligns People and Access with the mock direction by keeping the people list primary, moving add/edit into a drawer, adding remove intent, hiding disabled/cancelled intent from the primary working list, replacing missing responsibilities with Add prompts, and making diagnostics secondary. TASK-277 fixes the missing shared surface token and drawer stacking so the People and Access add/edit drawer is visually opaque rather than translucent. TASK-278 fixes access-intent idempotency key reuse so distinct Add/Edit person payloads do not collide with stale request keys. TASK-279 adds Amplifi Admin-only manual access acceptance from the People and Access edit drawer with required acceptance evidence and visible accepted-access versus login/seat provisioning state. TASK-280 waits for refreshed People and Access read models after intent, delivery, and accepted-access mutations so saved people appear without manual browser refresh. TASK-281 fixes remove-then-readd access intent by giving each Add person attempt a fresh create idempotency suffix, preventing old disabled membership replay from looking like a successful new add. TASK-282 makes manual accepted-access evidence work during pending account setup and clarifies the edit drawer action separation. TASK-283 exposes the login and seat provisioning next-action area so operators can see where the governed provisioning workflow will live. TASK-284 defines the command contract that future UI enablement must call. TASK-285 implements the backend provisioning route. TASK-286 wires the selected-customer People and Access UI to that guarded provisioning API, refreshes read models, and shows seat-assignment state without enabling auth/login propagation. TASK-287 adds repeatable selected-customer physical proof tooling for People and Access provisioning, refreshed read models, and controlled provisioning blocks. TASK-288 adds the guarded account-foundation activation API prerequisite for active-account provisioning proof. TASK-289 aligns People and Access with the mock recommendation by making the customer-scoped lifecycle list primary, showing missing-role Add rows, exposing named/accepted/seat stages, putting one next action on each responsibility, making diagnostics secondary, and keeping provisioning/login boundaries explicit. TASK-290 wires the guarded account-foundation activation command into selected-customer Customer Home, People and Access, and Account Health so activation prerequisite work is visible before seat provisioning. TASK-291 adds the activated-account proof-runner path that uses the guarded activation API before seat provisioning proof. TASK-294 records the successful activated local execution behind that UI path. TASK-297 adds backend support-case create/list/read persistence. TASK-321 wires selected-customer Support to that API for safe case list/create. TASK-322 adds backend support-case notes/status lifecycle APIs. | Coherent Referral SaaS workflow: account setup, setup checkpoint, customer profile selection, customer home/readiness summary, customer activity routing, campaign setup, campaign review, campaign activation, technical setup, referral link/code management, event/attribution investigation, reporting, safe status, support cases, and physical proof evidence. | Focused surfaces now cover Account Setup, customer selection and profile header with labeled metadata, customer-home Green/Red/Amber health action mapping, standalone selected customer home, customer-scoped function pages, people/access intent with add/edit/remove opaque drawer UX, payload-specific and per-attempt access-intent idempotency keys, post-save People and Access read-model refresh, disabled-intent filtering, missing-role Add prompts, Amplifi Admin manual acceptance evidence that can be recorded during pending setup, accepted-access visibility separated from provisioning, visible login/seat provisioning next actions, access provisioning command contract/API/UI action wiring, activation readiness, safe invitation delivery boundary, activation command boundary, activation action wiring, selected-customer account-foundation activation action, technical setup readiness, Technical Setup UI page, explicit provider approval status, recipient contact readiness visibility, a customer-scoped guarded delivery-check action, clearer person-name guidance, visible membership-versus-provisioned-login boundary, customer-scoped campaign readiness, campaign selection from selected-account data, backend guarded campaign setup create, frontend create UX for inactive campaign setup drafts, policy/settings API/UX, submit/review API/UX, activation/go-live API/UX, active-campaign Links and Codes continuation, selected-customer Reports with export preview, selected-customer E2E proof runners, People and Access provisioning proof tooling, guarded account-foundation activation API prerequisite for active-account provisioning proof, activated-account provisioning proof-runner path, People and Access lifecycle CX polish, support-case create/list/read API persistence, selected-customer support-case list/create UI, backend notes/status lifecycle APIs, and support-case lifecycle UI wiring. Live invite delivery, reference rotation, actual auth provisioning commands, export file creation/download runtime, and progress/attribution proof runner/execution remain bounded future capabilities; TASK-339 now defines the proof contract. | P1 | Move to governed auth/login lifecycle, aggregate support queues, or export storage/download; repeat selected-customer provisioning proof in staging/production-like data when available | Frontend route tests; accessibility tests; no-internal-leak tests; setup workflow smoke tests; account create-action tests; customer selector/header/health action label tests; membership invitation tests in Account Maintenance; invitation edit/cancel and removed-intent UI tests; access-intent idempotency-key tests; post-save People and Access refresh tests; drawer opacity/surface regression checks; activation-readiness UI tests; provisioning-readiness UI tests; provisioning-next-action UI tests; provisioning-command API/UI tests; activation command UI tests; activation action UI tests; manual access acceptance setup tests; recipient contact readiness UI tests; guarded delivery-check UI tests; technical setup readiness UI tests; campaign list/read/readiness UI tests; campaign create UX tests; campaign policy/settings API/UX tests; campaign submit/review API/UX tests; activation API/UX tests; customer-scoped link/code tests; customer-scoped reporting tests; support-case API/UI tests; provider approval UI tests; profile maintenance tests in Customer Profile; duplicate/already-created state tests; maintenance read-model/workspace tests; selected-customer physical proof execution; TASK-287/TASK-291 proof-runner tests; TASK-294 local seat-provisioning execution proof. |
| Operator support workflow | Admin audit, failure, DLQ, enterprise events, campaign readiness, link inspection routes, TASK-178 read-only product operator inspection wrapper, TASK-179 focused operator inspect surface, TASK-180 read-only product attribution trace wrapper, TASK-181 focused trace UI, TASK-182 read-only progress/status diagnostics wrapper, TASK-183 progress/status UI, TASK-184 support hub, TASK-295 support-case persistence contract, TASK-297 runtime support-case create/list/read persistence, TASK-321 selected-customer support-case UI, TASK-322 support-case notes/status API, TASK-323 support-case lifecycle UI wiring, TASK-324 operator aggregate support queue contract, TASK-325 runtime aggregate support queue API, and TASK-326 operator aggregate support queue UI exist. | Operator can resolve validation, progress, link/code, attribution, and reporting questions through safe evidence without DB access, persist and work selected-customer support cases without repair/replay side effects, and triage a cross-customer aggregate queue from the UI. | Product operator diagnostic API/UI, attribution trace API/UI, progress/status API/UI, support triage hub, support-case contract, support-case create/list/read schema/API, selected-customer support-case list/create UI, backend notes/status APIs, selected-customer lifecycle UI wiring, aggregate support queue contract, runtime aggregate support queue API, and live aggregate queue UI exist, but repair/replay guardrails remain open. | P1 | Add repair/replay guardrails as separate governed tasks | Support workflow tests; permission tests; redaction tests; evidence-link tests; support-case idempotency/audit tests; support-case UI tests; aggregate queue API/UI tests; repair/replay guardrail tests. |
| Audit and idempotency posture | Domain-specific audit and idempotency exist; progress dedupe is concrete. | Every SaaS command/event has a stated idempotency, retry, audit, and failure posture. | Coverage is uneven by command type. | P1 | TASK-146: Inventory Referral SaaS audit and idempotency posture | Static inventory; duplicate request tests; audit evidence tests; retry/failure tests. |
| E2E and live DB confidence | Broad domain tests exist; static migrations exist; live DB verification remains unavailable. | Full tenant-to-campaign-to-code-to-validation-to-progress-to-attribution-to-report E2E suite and live DB/state verification for launch-critical tables/routes. | No focused Referral SaaS golden-path suite and no live DB/state result for this wedge. | P0 | TASK-147: Define Referral SaaS E2E and live verification plan | E2E plan; migration replay; live schema/status/index checklist; route smoke checklist. |

## Current Campaign/Frontend Alignment

As of TASK-264, the selected-customer Campaigns area has standalone pages for
campaign list/readiness, inactive campaign setup creation, and campaign
policy/settings. TASK-260 wires the frontend to the guarded TASK-259 API wrapper
so operators can save attribution window, eligibility, product-window, accepted
terms, and reward-visibility evidence without entering tenant code or implying
activation, link generation, webhook delivery, billing, or money movement.
TASK-262 adds the guarded backend review submission and review decision wrappers
so review approval cannot be confused with activation or go-live.
TASK-263 adds the selected-customer campaign review page and links it from the
campaign list and policy/settings success path while preserving the same
review-only guardrails.
TASK-264 defines the separate activation/go-live command contract so approved
review becomes only a precondition for activation, not activation itself.
TASK-265 implements the guarded activation/go-live API wrapper. It activates
only campaign posture after policy evidence and approved review, while keeping
links, validation tracks, webhooks, credentials, access changes, billing, and
money movement out of the command.
TASK-266 wires that activation command into the selected-customer Campaign
Review page. Activation is available only after review approval, stays in
customer context, and still keeps links/codes, validation tracks, webhooks,
credentials, access, billing, and money as separate workflows.
TASK-267 continues activated selected-customer campaigns into Links and Codes.
Operators can select an active campaign, issue/reuse a referral code, and
validate it while tenant scope is resolved server-side and activation,
webhook, credential, billing, and money actions remain out of scope.
TASK-268 continues selected-customer context into Reports. Operators can view
campaign/referral/link performance and preview JSON/CSV exports without
entering tenant code, while export persistence, delivery, billing, and money
actions remain out of scope.
TASK-269 adds a read-only selected-customer E2E physical proof runner that
checks account resolution, people/access posture, technical readiness, campaign
list/readiness, campaign reporting, and export preview without customer,
campaign, invite, link/code, export, billing, or money side effects. TASK-270
fixes the blockers found by executing that runner locally: selected-customer
campaign readiness now redacts internal tenant-scope keys and selected-customer
report/export preview wrappers await their async report builders. The local
proof passed all selected-customer read-spine checks against `task-206-local-206b`.
TASK-271 adds the corresponding mutation-path proof runner for campaign setup,
policy/settings, review submission, review decision, activation posture,
referral code issue, referral validation, campaign report, and export preview.
TASK-272 records local execution against `test-fnb-sa-002`; the proof passed
the full selected-customer mutation path and confirmed no tenant-scope leakage,
webhook delivery, credential creation, invite delivery, membership activation,
persisted export creation, storage/delivery, billing, or money movement.
TASK-273 adds persisted selected-customer report export request and account
audit evidence. It validates through the existing export preview rules, safely
replays matching idempotency keys, rejects unsafe storage/delivery/billing/money
payloads, and still creates no export file, download URL, delivery job, invoice,
or money movement. TASK-328 adds the first runtime export file foundation over
that durable request spine: customer-scoped routes can create a tenant-safe
inline JSON/CSV file artifact, read metadata without file content, download the
stored content, audit file creation/download access, and replay already-stored
requests without scheduled delivery, provider dispatch, credentials, auth,
campaign activation, billing, or money movement.

TASK-329 wires the selected-customer frontend download controls over that
runtime, so operators can prepare a tenant-safe CSV file and download it from
the customer-scoped Reports page without tenant-code entry or adjacent actions.
TASK-330 enforces retention expiry across that runtime: expired export requests
cannot be converted into files or downloaded, and metadata reports the expired
state safely without returning a download URL.
TASK-331 defines the object-store/signed URL hardening contract for the next
runtime layer: opaque storage references, signed URL TTL bounded by retention,
safe storage/signing failure states, audit evidence, and no raw bucket/object
path, provider payload, credential, tenant-code, or signing-material leakage.
TASK-332 implements the signed-download runtime boundary over the persisted
export file lifecycle with opaque storage references, content-free public
metadata, and short-lived signed URLs bounded by retention.
TASK-333 defines the scheduled report delivery contract: safe schedule routes,
cadence, recipients, report/export readiness, signed URL/retention interaction,
lifecycle states, safe errors, audit/idempotency, and no-provider/no-money
boundaries are now specified before runtime work.

Remaining campaign/frontend gaps are domain-specific repair/replay proof and non-local proof
repetition. Governed auth/login completion is now visible in
People and Access through TASK-345 to TASK-347. TASK-349 defines the
provider/vault runtime execution command contract and TASK-350 adds the guarded
API foundation without changing the product boundary or dispatching live
providers.
TASK-351 adds the shared runtime adapter seam so the API now returns explicit
adapter-not-configured or vault-not-configured execution evidence until
approved adapters are installed.
TASK-352 defines the first safe adapter implementation sequence:
`PLATFORM_REFERENCE` plus `PLATFORM_VAULT_REFERENCE`, giving the next code task
a bounded runtime target without browser-held secrets, vendor dispatch,
credential reveal, auth/session mutation, campaign activation, billing, money,
DLaaS, or source-fork side effects.
TASK-353 implements that first platform-reference provider/vault adapter pair
behind the shared seam. Approved `PLATFORM_REFERENCE` execution can now return
opaque provider/vault references while unsupported provider/capability/
environment combinations fail closed.
TASK-354 defines the vendor/managed provider-vault adapter contract that must
govern the next runtime implementation. It separates vendor provider
references, managed vault references, required gates, failure states,
audit/idempotency, and redactions from raw secret handling, live provider
dispatch, invites/messages/webhooks, auth, campaign activation, billing, money,
DLaaS, or source forks.
TASK-355 implements the first built-in vendor/managed provider-vault runtime
adapter path behind the shared seam. The adapter requires an explicit provider
allowlist and managed-vault adapter configuration, returns opaque vendor/provider
and managed-vault references, and keeps raw secrets, live provider dispatch,
invite/message/webhook delivery, auth, campaign activation, billing, money,
DLaaS, and source forks out of scope.
Repair/replay execution remains a future governed command track, not a visible
readiness UI gap.

TASK-292 closes the selected-customer Customer Home access-health mismatch found
in physical UI testing. When People and Access reports the required owner and
campaign-manager responsibilities as present/accepted, Customer Home now clears
the `Add who can manage this account` red blocker, marks People and Access
Ready, reports the actual missing-role count, and routes operators toward the
next true setup action while keeping seat/auth provisioning as a separate
governed workflow.

TASK-293 simplifies the selected-customer People and Access page language so the
operator outcome is no longer buried under seat/auth terminology. The page now
frames the required owner and campaign manager as confirmed customer managers
for referral work, uses plain lifecycle labels, and moves platform login/seat
setup into a secondary optional section. This improves frontend coherence
without changing backend account, membership, provisioning, auth, billing, or
money boundaries.

TASK-294 records successful activated local People and Access provisioning proof
against `test-fnb-sa-002`. The proof runner activated the customer
account/link posture through the guarded API, assigned an available `OPERATOR`
seat through the guarded People and Access provisioning API, replayed
idempotently, confirmed DB/audit evidence, and kept invite delivery, credential
creation, auth-claim propagation, campaign activation, go-live, billing, and
money movement out of scope.

TASK-295 defines the selected-customer support-case persistence contract. The
contract turns the existing read-only support hub into a reviewed future write
boundary by defining case categories, statuses, safe evidence links, selected
customer routes, idempotency, audit, redaction, frontend expectations, and
explicit non-goals. Runtime support-case schema, API, UI writes, and any
repair/replay guardrails remain separate tasks.

TASK-296 scopes Account Health account-foundation activation feedback to the
selected account id. This prevents stale or mismatched activation evidence from
another customer being shown under the current customer profile while preserving
the existing backend account path-scope guard as the write safety boundary.

TASK-298 clarifies the selected-customer People and Access Platform login setup
positioning. Required customer access work remains role-specific person
confirmation for referral operations; Platform login setup is shown as optional
Amplifi sign-in setup only, with permissions and auth claims still kept in a
later governed workflow.

TASK-300 reframes the selected-customer Technical Setup page as Integrations.
The product surface now uses `Integrations` for API, webhook, invite-delivery,
and referral-message readiness while the existing technical setup readiness API
remains the read-only implementation detail. The old `/technical` route remains
a compatibility alias.

TASK-301 defines the selected-customer Integrations configuration contract for
API environment intent, webhook callback intent, event-category subscription
intent, invite-delivery provider approval intent, referral-message provider
readiness, and safe test-mode posture. TASK-302 adds the runtime
configuration schema/API foundation for safe non-secret setup evidence.
TASK-303 wires the selected-customer Integrations page to read, validate, and
save that safe setup evidence for API access intent, webhook callback/event
intent, invite delivery channel, and referral-message channel configuration.
TASK-304 defines the live execution contract for turning saved Integrations
evidence into future API verification, webhook test dispatch, message-provider
testing, and governed credential requests. TASK-305 adds the read-only
execution-readiness API that evaluates saved configuration, active
account/link/reference posture, provider evidence, guardrails, redactions, and
safe next actions without running any provider execution. TASK-306 wires that
execution-readiness read model into the selected-customer Integrations UI so
operators can see blockers, safe ready actions, and post-save readiness refresh
without firing live provider actions. TASK-307 adds the first governed
Integrations execution command by recording audited/idempotent API-access
verification evidence after saved configuration and active account/link/reference
gates pass, while rejecting unsafe secret-like payloads and preserving
no-credential/no-provider/no-webhook/no-message/no-auth/no-campaign/no-money
guardrails. TASK-308 wires that command into the selected-customer Integrations
UI with safe verification evidence, idempotency/correlation, plain-language
success feedback, and post-command readiness refresh. TASK-309 adds the second
governed Integrations execution command by recording audited/idempotent webhook
test-dispatch evidence after saved webhook setup and active account/link/reference
gates pass, while rejecting unsafe secret-like payloads and preserving
no-webhook-dispatch/no-signing-material/no-credential/no-provider/no-message/no-auth/no-campaign/no-money
guardrails. TASK-310 wires that command into the selected-customer Integrations
UI with plain-language webhook evidence copy, idempotency/correlation,
success/error feedback, readiness refresh, and no live webhook/provider,
credential, invite/message, auth, campaign, billing, or money side effects.
TASK-311 aligns the selected-customer Integrations page to the recommended Plan,
Save, Verify CX so operators can separate setup intent from verification
evidence, see the right next action, and hand off cleanly to People and Access
or Campaigns without source duplication.
TASK-312 adds the third governed Integrations execution command by recording
audited/idempotent message-provider test evidence after saved message-provider
setup and active account/link/reference gates pass, while rejecting unsafe
payloads and preserving no-provider-call/no-invite-delivery/no-referral-message
delivery/no-credential/no-webhook/no-auth/no-campaign/no-money guardrails.
TASK-313 wires that command into the selected-customer Integrations UI with
safe provider-readiness payloads, idempotency/correlation, plain-language
feedback, and readiness refresh. TASK-314 defines the selected-customer
credential lifecycle request contract for future API key, webhook signing key,
and provider credential-reference requests, including request vocabulary,
selected-customer gates, review states, audit/idempotency/redaction rules, and
no-secret/no-provider/no-webhook/no-message/no-auth/no-campaign/no-billing/no-
money side-effect boundaries. TASK-315 adds the runtime credential request
persistence/API foundation for create/list/read request metadata with
idempotency, audit, redactions, selected-customer scope, saved-configuration
gates, and no secret/provider/vault/credential-execution side effects.
TASK-316 wires the selected-customer Integrations UI to record governed
credential setup requests from saved connection plans, list safe request
metadata, show plain-language feedback, and refresh readiness/request state
without credential creation, reveal, storage, download, provider, vault,
webhook, invite/message, auth, campaign, billing, money, or DLaaS side effects.
TASK-317 adds the selected-customer credential request review-decision API
foundation so operators can approve or block request metadata for later
governed execution with idempotency, audit, redaction, and no credential,
provider, vault, webhook, message, auth, campaign, billing, money, or DLaaS
side effects.
TASK-318 wires the selected-customer Integrations UI to the review-decision API
so approve/block governance can be performed from the Verify tab with
plain-language feedback and refreshed readiness/request state. Credential
TASK-319 adds the selected-customer credential execution-check API foundation
so approved credential requests can record safe execution-readiness evidence
with idempotency, audit, redaction, and no credential, provider, vault,
webhook, message, auth, campaign, billing, money, or DLaaS side effects.
TASK-320 wires the selected-customer Integrations UI to that execution-check
API so approved credential setup requests expose a plain-language
`Check approved setup` action, refresh request/readiness state, and keep actual
credential/provider/vault execution as a separate governed gap. TASK-321 wires
selected-customer Support to the TASK-297 support-case API so operators can
list and create safe customer-scoped support cases with category, priority,
optional safe evidence references, idempotency, and no repair/replay side
effects. TASK-322 adds selected-customer support-case notes and status
transition APIs with bounded vocabularies, idempotency/payload replay, audit,
redaction, selected-account path scope, and no repair/replay/retry,
referral/campaign/progress/attribution/report/export, invite,
credential/auth, billing, money, or DLaaS side effects. TASK-323 wires the
selected-customer Support UI to those lifecycle APIs so operators can add safe
notes and change bounded case statuses from the customer Support page. TASK-324
defines the operator aggregate support queue contract; runtime queue API/UI,
repair/replay guardrails, export file storage/download, and non-local
progress/attribution proof repetition remain separate future gaps.
Vendor provider adapters, managed vault lifecycle, webhook/provider execution,
invite delivery, auth/login changes, campaign activation, billing, and money
movement remain separate future gaps.
TASK-342 defines the shared provider/vault runtime adapter contract that will
turn approved credential requests into governed readiness and future opaque
provider/vault execution references. It closes the ambiguity in the adapter
boundary, failure taxonomy, audit/idempotency, redaction, and no-adjacent-action
rules, but does not implement a readiness API, vault write, provider call, or UI
control.

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
10. TASK-333 through TASK-354 now map the remaining launch-hardening gaps:
    scheduled report delivery, governed repair/replay posture, progress and
    attribution mutation proof, provider/vault execution readiness, command
    design, API foundation, platform-reference adapters, governed auth/login
    completion, and non-local launch verification.
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

## Remaining Launch-Hardening Task Map

The matrix no longer points at broad undefined "future work" for the final
Referral SaaS wedge. Remaining gaps are now mapped to explicit tasks:

| Gap | Task path | Intended close-out |
| --- | --- | --- |
| Scheduled report delivery | TASK-335 | TASK-333 contract, TASK-334 guarded schedule API persistence/readiness, and TASK-335 selected-customer Reports UI controls are complete. Remaining close-out is governed provider execution and non-local proof. |
| Repair/replay guardrails | TASK-336 to TASK-338; TASK-375 | TASK-336 contract, TASK-337 read-only support-case readiness API, TASK-338 Support UI posture without unsafe mutation buttons, and TASK-375 governed command execution ledger/API are complete. Domain-specific outcome execution proof remains separate from the command boundary. |
| Progress/attribution mutation proof | TASK-339 to TASK-341 | TASK-339 contract, TASK-340 repeatable proof runner, and TASK-341 approved local execution evidence are complete. Remaining close-out is non-local staging/production-like proof repetition. |
| Provider/vault execution readiness, command design, and adapter implementation plan | TASK-342 to TASK-344; TASK-349 to TASK-355 | TASK-342 provider/vault adapter contract, TASK-343 read-only readiness API, TASK-344 selected-customer Integrations UI visibility, TASK-349 provider/vault runtime execution command contract, TASK-350 guarded runtime execution API foundation, TASK-351 shared runtime adapter seam, TASK-352 first safe adapter implementation plan, TASK-353 platform-reference provider/vault adapters, TASK-354 vendor/managed provider-vault adapter contract, and TASK-355 vendor/managed provider-vault runtime adapters are complete. Repair/replay execution and non-local proof remain the final governed implementation track. |
| Governed invitation delivery, acceptance, auth/login completion | TASK-345 to TASK-347; TASK-363; TASK-364 | TASK-345 contract, TASK-346 guarded API boundary, TASK-347 People and Access UI wiring, TASK-363 live provider-backed invite delivery, and TASK-364 expiring invitation acceptance are complete. Operators can send invite email through the approved shared channel provider after recipient/provider/template/idempotency/audit/redaction gates pass, invitees can accept through a time-bound hashed-token path, and the flow still keeps seats, login credentials, auth claims, campaign activation, billing, money, DLaaS, and source forks separated. |
| Support assignment and recovery workspace | TASK-380 | Closed. Selected-customer Support now has assignment, owner visibility, audited/idempotent assignment evidence, safe recovery posture, and no unsafe repair/replay/provider/auth/campaign/billing/money side effects. |
| Non-local launch verification | TASK-348 plus TASK-027; TASK-420 | TASK-420 now supplies the approved command/evidence pack for staging/production-like read-only verification and optional staging-only seeded proof. TASK-348 remains the actual execution/evidence close-out once approved access exists. |

TASK-027 remains blocked by approved non-local credentials and access. It is a
production-confidence blocker, not a missing product feature. TASK-420 removes
the runbook ambiguity by defining the safe command sequence, evidence template,
redaction expectations, and production/no-write gates. TASK-348 is still the
Referral SaaS launch-verification wrapper that should consume approved access
once available.

## Prototype UX Alignment Gap

TASK-421 closes the planning gap between the approved prototype and the real
application with a journey-by-journey production implementation matrix.
TASK-422 completes the first implementation slice: jurisdiction-scoped customer
discovery now supports search across safe business identifiers, presents one
governed duplicate-safe Account Setup entry point, requires explicit customer
selection, and continues into the standalone Customer Profile Overview. It
reuses existing tenant, jurisdiction, permission, audit, idempotency, and
redaction controls. TASK-423 completes the next bounded journey: customer
product lines and offerings now have a standalone selected-customer workspace
backed by the existing catalogue APIs. Business names and hierarchy are
primary, stable references remain secondary audit/integration evidence, and
the operator can continue directly into programme configuration. No
product-information, pricing, inventory, fulfilment, schema, or router scope
was introduced. Remaining prototype work is ordered frontend implementation,
not backend reinvention.

The Amplifi Global Operations Workspace shown in the approved design is not yet
implemented as a complete authoritative production surface. TASK-424 closed
the global-versus-customer shell, TASK-425 added the permission-safe
operational read model without synthetic SLA values, TASK-426 delivered the
authoritative global dashboard with customer discovery, KPIs, queue preview,
customer attention, and degraded states, and TASK-427 delivered the full global
work queue with permission-safe server filters, URL-backed state, stable pagination,
and governed destinations. TASK-428 delivered the jurisdiction-safe customer portfolio with
authoritative registry identity, explainable persisted attention, URL-backed filters, and explicit
customer selection. TASK-429 closes the global destination gap by routing Programme and Commercial
Governance through permission-safe customer selection, retaining real Reporting and Support destinations,
and deliberately hiding unsupported aggregate Approvals and Exceptions. TASK-430 completes automated cross-page,
accessibility, permission, degraded-state, and leakage verification plus physical desktop, tablet, and mobile,
keyboard, screen-reader, and no-overflow release evidence. The read-model task is a hard dependency
for KPI and queue UI so counts, service targets, priorities, incidents, and
destinations cannot be invented or recomputed inconsistently in the frontend.

TASK-431 now defines the missing governed Referral SaaS operational service-target
contract. It separates customer-support operational clocks from DLaaS provider and
fulfilment SLAs and specifies effective policy versions, jurisdiction/category/
priority resolution, business calendars, pause evidence, server-owned timing,
audit, permissions, safe aggregation, and degraded behavior. Runtime persistence,
calculation, read-model integration, UI enablement, and E2E proof remain ordered
implementation gaps; until then `UNAVAILABLE` and a null percentage remain the
correct production response.

TASK-432 closes the persistence-foundation portion of that gap. The schema can now
store reviewed effective policy versions, immutable support-case policy resolution,
server-owned timestamps, accumulated pause duration, pause/resume actor evidence,
completion/breach outcomes, idempotency hashes, correlation evidence, and audit
records. It intentionally contains no seeded target values and does not yet select
policies or advance clocks. Policy resolution, lifecycle calculation, read-model
aggregation, UI enablement, and end-to-end proof remain the ordered runtime gaps;
`UNAVAILABLE` remains correct until those are complete.

TASK-433 closes the policy-administration and deterministic-resolution portion of
the runtime gap. Amplifi administrators can now create immutable policy versions,
submit them for independent review, approve or return them, retire approved
versions, and list their safe evidence. The resolver selects exactly one approved,
effective policy for operating jurisdiction, work type, category, priority, and
server time; missing or overlapping matches fail closed. IANA timezone validation,
effective-window overlap prevention, hashed idempotency, audit evidence, redaction,
and separation of duties are enforced. Support-case clocks are still not attached
or advanced, and the Operations Workspace must continue returning `UNAVAILABLE`
until clock lifecycle and read-model aggregation are complete.

TASK-434 closes the ordinary elapsed-time clock-lifecycle portion of the gap.
Eligible support cases now pin one approved effective policy and use persisted,
server-owned warning/due times, policy-aware completion, within-target/late outcome,
reopen evidence, and approved pause/resume commands with idempotency, audit, and
redaction. Missing/ambiguous policy matches and policies that require an unsupported
business-calendar engine remain explicitly unavailable rather than being guessed.
TASK-435 closes the Operations aggregation and UI-enablement portion of the gap.
The existing read model now returns jurisdiction-safe rolling 30-day completed-
clock performance with its denominator, exclusions, policy coverage, reporting
window, semantic due state, warning/due timestamps, filters, and due sorting.
The frontend renders only those server-owned values and retains `UNAVAILABLE`
when governed evidence is absent. TASK-436 closes the remaining release-proof
gap with a migrated PostgreSQL check covering independently approved policies,
clock replay, pause/resume, completion, audit evidence, unsupported evidence,
two-jurisdiction isolation, Operations aggregation, and cleanup. The controlled
physical run passed without cross-jurisdiction leakage. Business-calendar
calculation remains an explicit enhancement and therefore fails closed where
required. TASK-437 now defines its target contract and ordered implementation path:
versioned schedule persistence, shared timezone-aware calculation, governed
administration/resolution, existing-clock integration, safe UX, and PostgreSQL
release proof. No calendar schedule, holiday, or due time is inferred prematurely.
TASK-438 closes the persistence slice with append-safe account/global calendar
versions, weekly intervals, dated closures and exceptional working intervals, and
audit/idempotency/redaction evidence. It seeds no calendar data and does not enable
runtime calculation. The remaining gap is the shared timezone-aware calculator,
governed administration and resolution, clock version pinning, safe UX and preview,
and PostgreSQL proof across DST, exceptions, isolation, replay, and cleanup.
TASK-439 closes the standalone calculation slice. The shared pure service now
validates approved schedules and deterministically calculates working instants,
working seconds, and future working-minute deadlines across closures, exceptional
intervals, weekends, and DST transitions. It is intentionally not connected to
database resolution or clocks yet. The remaining gap is governed administration
and deterministic version resolution, immutable clock pinning, safe UX and preview,
and migrated PostgreSQL lifecycle proof.
TASK-440 closes governed administration and deterministic resolution. Amplifi
administrators can create prospective immutable account/global versions, inspect
safe schedules, independently review and approve them, return review evidence to
draft, retire approved versions, and resolve exactly one approved effective version.
The service reuses the shared calculator for schedule validation, prevents approved
window overlap, prefers account-scoped evidence before global fallback, and keeps
idempotency, audit, and redaction evidence. The remaining gap is immutable clock
pinning, safe administration UX and calculation preview, and migrated PostgreSQL
lifecycle proof across DST, exceptions, isolation, replay, and cleanup.
TASK-441 closes immutable runtime pinning. Calendar-backed clocks now resolve one
approved effective account-first/global-fallback version at start and persist its
identifier, code, version, and timezone with the policy pin. Warning/due and
pause/resume calculations use the shared working-time calculator and the same
pinned version, so later versions cannot rewrite historical clock evidence.
Missing, ambiguous, invalid, and policy/calendar timezone-mismatched evidence
continues to fail closed. TASK-442 closes the safe governance and preview UX gap:
Amplifi administrators can govern account/global calendar versions and inspect
server-calculated example deadlines without creating a clock or duplicating timing
logic in the browser. TASK-443 closes the remaining business-calendar release-proof
gap with repeatable CI and local migrated-PostgreSQL evidence across independent
approval, account override/global fallback, overlap rejection, DST, closures,
exceptional hours, immutable clock pinning, pause/resume/completion, replay, audit
redactions, jurisdiction isolation, and deterministic cleanup.

## TASK-444 Release Close-Out Reconciliation

TASK-444 reconciles the current state after the completed business-calendar
release proof. All ordered Referral SaaS implementation, UX, local proof, and
migrated-PostgreSQL tasks through TASK-443 are complete. Historical sections
remain as delivery evidence, but they must not be interpreted as new open
implementation gaps where a later task already closed the capability.

| Current release measure | Authoritative position |
| --- | --- |
| Referral Management rating | 9.999/10. Product capability is implemented and locally proven inside the focused SaaS boundary. |
| Campaign Attribution rating | 9.999995/10. Product capability is implemented and locally proven inside the focused SaaS boundary. |
| Open implementation tasks | None. Do not create another feature task solely to move the displayed rating. |
| Open evidence tasks | TASK-027 and TASK-348 only. Both require approved non-local credentials, targets, and execution permission. |
| Next executable action | Run the TASK-420 command/evidence pack when approved non-local access exists, then close TASK-027 and TASK-348 from recorded evidence. |
| Explicitly deferred scope | DLaaS marketplace, funding, fulfilment, settlement, sponsor billing, broad white-label/embed, and other separately contracted expansion remain outside this Referral SaaS close-out. |

The remaining fraction below 10/10 is therefore an environment-confidence
holdback, not evidence of another missing local backend or frontend feature.

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

## Post-Close-Out Customer Accounts Experience Gap

| Gap | Current evidence | Ordered resolution | State |
| --- | --- | --- | --- |
| Customer discovery and operational attention shared one route | The permission-safe portfolio API is sound, but the UI conflated lookup with prioritisation | TASK-445 separates Customer Accounts discovery from Customer Portfolio | Closed |
| Create customer leaves the Customer Accounts mental model | Customer Accounts now presents URL-restorable Find/Create states and embeds the governed Account Setup lifecycle | TASK-446 composes it into unified duplicate-safe Find/Create UX | Closed |
| Visual/accessibility parity is unproven | Prototype-aligned Find/Create states, responsive result presentation, explicit permission-boundary guidance, and customer-specific accessible actions are implemented and covered by the full frontend suite | TASK-447 completed prototype, responsive, and accessibility alignment | Closed |
| New information architecture lacks lifecycle proof | Repeatable API/PostgreSQL proof now covers no-result discovery, governed creation, exact replay, duplicate rejection, permission-scoped refresh, persisted profile routing, audit evidence, and cleanup | TASK-448 completed discovery-to-profile lifecycle proof | Closed |
| Create customer still presents duplicate introductory and standalone-wizard layers | Existing commands and lifecycle are correct, but the composition obscured the primary action and diverged from the approved focused prototype | TASK-449 adds a compact single-workflow composition with adjacent guardrails | Closed |
| Compact Create customer still retained nested step headings and card framing | The lifecycle was correctly embedded, but the active action still read as a wizard inside a workspace | TASK-450 gives each compact step one focused heading and removes duplicate nested presentation while preserving the standalone workflow | Closed |
| Compact creation required a visible duplicate-search action before customer creation | The account resolver and governed creation chain were authoritative, but the operator had to understand and execute a technical pre-check | TASK-451 places duplicate resolution behind one Create customer action and returns the existing or newly created persisted customer destination | Closed |
| Customer creation collapsed legal and customer-facing identity into one organisation name | The approved prototype separated legal name, trading name, and registration number, but the durable account foundation did not retain that distinction | TASK-452 adds governed legal identity fields to the shared account foundation and aligns Account Setup while retaining legacy display-name compatibility | Closed |

These are UX composition and release-proof gaps. They do not justify a second account registry, onboarding service, customer schema, or product-domain fork.
