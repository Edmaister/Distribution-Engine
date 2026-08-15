# Referral SaaS Journey Configuration Framework

Product boundary: Referral SaaS.

Required boundary docs checked:

- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`

## Purpose

This framework defines how Referral Management and Campaign Attribution SaaS
should move from code-defined referral journeys to governed, versioned journey
configuration without weakening tenant isolation, attribution correctness,
auditability, or launch controls.

The target model is not a free-form journey builder. It is a governed
configuration system:

- Amplifi owns global journey templates.
- Customers or Amplifi Admin configure tenant/customer-specific versions of
  approved templates.
- Campaigns bind only to published customer journey versions.
- Runtime execution uses the published version, not ad hoc UI state.

## Architecture Layers

| Layer | Owner | Scope | Example | Control |
| --- | --- | --- | --- | --- |
| Global journey template | Amplifi platform governance | Universal across tenants | Account opening referral, mortgage application referral, dealer lead referral | Template review, technical validation, versioning, audit |
| Customer journey configuration | Customer admin or Amplifi Admin | Tenant/customer account | FNB mortgage journey labels, approved optional steps, reward selections, reporting labels | Account scope, draft validation, publish approval, version lock |
| Campaign journey binding | Campaign manager | Campaign-specific | Winter Home Loans campaign uses FNB mortgage journey v3 | Published-version-only binding, campaign readiness, activation gates |
| Runtime journey execution | Platform engine | Referral/event runtime | Progress ingestion, milestone checks, attribution, reporting | Immutable version execution, idempotency, audit, redaction |

## Customer Journey Outcomes

| Customer journey | Outcome for customer | Outcome for Amplifi |
| --- | --- | --- |
| Choose a journey template | Start from a proven model instead of waiting for development | Reuse governed templates across markets and customers |
| Configure journey version | Tailor labels, optional steps, rewards, missions, badges, and reporting safely | Reduce seed-file/customer-specific engineering work |
| Validate before launch | See blockers before campaigns go live | Prevent invalid transitions, missing evidence, unsafe rewards, or broken attribution |
| Publish a version | Lock an approved configuration for use | Preserve immutable audit and rollback posture |
| Bind to campaign | Reuse a published journey in campaign setup | Keep campaign behavior tied to known journey rules |
| Track and optimize | Understand drop-offs, high-value events, rewards, and attribution outcomes | Improve templates and support evidence over time |

## Configuration Ownership

| Configurable item | Customer admin | Amplifi Admin | Engineering |
| --- | --- | --- | --- |
| Select an approved template | Yes | Yes | No |
| Customer-facing milestone labels | Yes, within approved template | Yes | No |
| Optional milestone inclusion | Yes, when template allows it | Yes | No |
| Attribution window within allowed range | Yes | Yes | No |
| Reward policy selection within approved range | Yes, where enabled | Yes | No |
| Mission, badge, leaderboard binding | Yes, from approved catalogue | Yes | No |
| New global journey type | No | Review/approve | Yes |
| New milestone transition rule | No | Review/approve | Yes |
| New evidence model or event contract | No | Review/approve | Yes |
| New reward calculation engine | No | Review/approve | Yes |
| Provider, auth, billing, or money behavior | No | Separate governed workflow | Yes, where contracted |

## Required Controls

Every implementation task in this track must preserve these controls:

- Tenancy: customer journey configurations must be account-scoped and must not
  expose internal `tenant_code`.
- Versioning: published versions are immutable; changes create a new draft and
  version.
- Governance: draft, validate, submit/review where required, publish, activate,
  archive, and rollback posture must be explicit.
- Runtime integrity: campaigns bind to a published customer journey version;
  runtime events cannot execute against unversioned draft configuration.
- Audit: create, update, validate, publish, activate, archive, and campaign
  binding actions must emit audit evidence.
- Idempotency: write commands must use idempotency keys and reject conflicting
  payload reuse.
- Redaction: no raw UCN, raw event payload, source payload hash, secret,
  provider payload, internal tenant identifier, auth claim, billing, payout, or
  money evidence may leak into customer/admin screens.
- Separation of duties: publishing and activation must be distinct from
  campaign go-live when the configured journey affects rewards, provider
  execution, or regulated customer communications.
- Compatibility: existing `journey_definitions.py` and
  `progress_definitions.py` remain the trusted baseline until the runtime
  migration is explicitly implemented and proven.
- No source fork: configuration must reuse shared platform services and the
  selected-customer Referral SaaS route surface.

## Target Workflow

1. Amplifi Admin defines or imports a global journey template.
2. Amplifi Admin validates the template structure and evidence requirements.
3. A customer or Amplifi Admin creates a customer journey draft from the
   template.
4. The customer configures allowed labels, optional steps, rewards, missions,
   badges, leaderboards, attribution windows, and report labels.
5. The platform runs validation and simulation.
6. The draft is submitted or directly published according to governance rules.
7. A published version becomes available for campaign binding.
8. Campaign setup selects a published customer journey version.
9. Runtime progress, attribution, reporting, and support read from the bound
   version.
10. Performance analytics feed the next draft/version without mutating live
    history.

## Task Roadmap

| Task | Capability | Business process unlocked | Main controls |
| --- | --- | --- | --- |
| TASK-383 | Define governed journey template and customer configuration contract | Shared language for configurable journeys before schema/UI work | Ownership matrix, tenancy, versioning, no-source-fork, no-runtime-switch |
| TASK-384 | Add journey template and customer configuration schema foundation | Durable storage for templates, drafts, versions, validation, and bindings | Account scope, immutable publish version, audit columns, status constraints |
| TASK-385 | Add admin journey template catalogue read API | Amplifi Admin can see approved templates and versions | Read-only, no tenant data, no runtime mutation |
| TASK-386 | Add customer journey draft read/save/validate API | Customer/Admin can configure allowed template options | Idempotency, redaction, validation gates, no campaign activation |
| TASK-387 | Add journey validation and simulation service | Operators can see whether a journey can safely launch | Transition checks, evidence checks, reward safety, attribution safety |
| TASK-388 | Add publish/archive customer journey version API | Approved journey versions can be locked for use | Immutable versions, audit, rollback posture, SoD where required |
| TASK-389 | Wire journey template catalogue and draft UX | Customer/Admin gets a plain-language journey configuration workspace | Step-by-step UX, customer context, safe labels, no raw technical leakage |
| TASK-390 | Bind campaigns to published journey versions | Campaign setup becomes template/version driven | Published-version-only, readiness gate, no draft binding |
| TASK-391 | Add rewards, missions, badges, and leaderboard binding controls | Incentive mechanics become configurable inside approved limits | Complete - approved catalogue references can bind to published customer journey versions with account scope, idempotency, audit, redaction, and no payout/money movement |
| TASK-392 | Migrate runtime reads from code baseline to published config where proven | Runtime can execute configured journeys safely | Backward compatibility, feature flag, proof runner, no unversioned runtime |
| TASK-393 | Add journey analytics and optimization read models | Customers can optimize journeys from conversion/drop-off evidence | Tenant-safe reports, version comparison, attribution redaction |
| TASK-394 | Run configurable journey E2E and non-local proof | Proves create-config-bind-track-report path outside local-only data | Live/staging proof, no leak, no unsafe side effects |

## Definition Of Done For This Track

This track is complete when a customer or Amplifi Admin can select an approved
global journey template, configure a tenant/customer-specific version, validate
it, publish it, bind it to a campaign, track referrals against it, and report on
performance without source-code changes for already-approved journey models.

New global journey models, new evidence rules, new transition engines, new
reward-calculation engines, auth/login behavior, provider dispatch, billing,
payouts, settlement, and money movement remain separately governed platform
work.
