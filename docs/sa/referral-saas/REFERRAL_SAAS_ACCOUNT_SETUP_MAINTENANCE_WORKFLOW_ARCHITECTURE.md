# Referral SaaS Account Setup And Maintenance Workflow Architecture

TASK ID: TASK-190

Product boundary: Referral SaaS.

Status: Architecture contract only. No runtime behavior, route, component, CSS,
API wrapper, database migration, permission, schema, or test implementation is
made by this task.

## Boundary

This document defines how Referral Management and Campaign Attribution SaaS
should build the real account setup workflow, integrated readiness check, and
account maintenance workflow without creating a fake SaaS account layer.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`
- `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

Implementation/source files inspected:

- `dp/migrations/080_onboarding_draft_persistence.sql`
- `services/onboarding/onboarding_draft_repository.py`
- `services/onboarding/onboarding_state_projection_service.py`
- `apps/api/routers/admin_onboarding.py`
- `services/tenant_service.py`
- `apps/api/routers/admin_tenants.py`
- `frontend/src/api/endpoints/adminOnboarding.ts`
- `frontend/src/pages/admin/CompanyOnboardingPage.tsx`
- `frontend/src/pages/admin/MemberRoleOnboardingPage.tsx`
- `frontend/src/pages/admin/OnboardingReadinessChecklistPage.tsx`
- `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`

## Architecture Decision

Build Account Setup and Account Maintenance as real product workflows, not as
decorative frontend shells.

The current system has strong onboarding draft and readiness primitives, but it
does not yet have durable Referral SaaS account records, account-to-tenant
links, account membership, safe account search, user invitations, or account
maintenance commands. Therefore:

- Account Setup may begin by writing safe onboarding draft intent.
- Account Setup Readiness remains an integrated checkpoint inside setup.
- Account Maintenance must start as read-only/account-evidence review until
  durable account and membership primitives exist.
- No UI may claim account creation, invitation delivery, membership activation,
  tenant-link persistence, or account maintenance commands until those backend
  primitives and tests exist.

## Current Foundation

Reusable current primitives:

| Foundation | Current fact | Safe use |
| --- | --- | --- |
| Onboarding draft persistence | `onboarding_drafts`, sections, validation results, idempotency keys, and audit links exist. | Capture setup intent and section evidence. |
| Draft save API | `POST /admin/onboarding/drafts` saves safe draft intent with idempotency and audit evidence. | First write-enabled setup foundation. |
| Validation API | `POST /admin/onboarding/validate` validates setup evidence without persistence. | Pre-save checks and field-level feedback. |
| Submit for review | `POST /admin/onboarding/drafts/{draft_ref}/submit-for-review` exists. | Review handoff, not account activation. |
| Review decision | `POST /admin/onboarding/drafts/{draft_ref}/review-decision` exists. | Internal review evidence, not go-live activation. |
| Readiness projection | `GET /admin/onboarding/state` and readiness aggregation exist. | Integrated readiness checkpoint. |
| External references | `external_tenant_ref` and `organisation_ref` are accepted user-facing scope. | Keep `tenant_code` internal. |

Missing product primitives:

| Missing primitive | Required before claiming |
| --- | --- |
| Durable account record | Real account creation, account selector, account lifecycle. |
| Account-to-tenant link | Trusted resolution from account to internal `tenant_code`. |
| External reference mapping table | Safe account/workspace lookup and disabled/suspended reference behavior. |
| Membership/user model | User invitations, role assignment, account-scoped authorization. |
| Maintenance commands | Profile updates, role changes, reference rotation, status transitions. |
| Account audit/support history | Maintenance timeline and operator accountability. |

## Product Model

### Account Setup Workflow

Account Setup is the first-time workflow for getting a Referral SaaS customer
ready to configure campaigns.

Target steps:

1. Company profile
2. Organisation and external references
3. Users and role intent
4. Integration/API setup intent
5. Integrated readiness check
6. Submit for review
7. Operator review decision
8. Handoff to campaign setup

Allowed first implementation foundation:

- save onboarding draft sections
- validate setup evidence
- submit draft for review
- record review decision
- display readiness and blockers

Not allowed until future primitives exist:

- create durable account row
- create internal tenant row as part of product setup
- persist account-to-tenant links
- invite users
- activate memberships
- enable go-live
- activate campaigns

### Integrated Readiness Check

Readiness is not a separate product area. It is a checkpoint inside Account
Setup and later a health checkpoint inside Account Maintenance.

In Account Setup, readiness answers:

- Is the setup evidence complete enough to continue?
- Which setup section must be completed next?
- Is the setup ready to submit for review?
- Is the reviewed setup ready to hand off to campaign setup?

Readiness must not:

- create accounts
- activate tenants
- send invitations
- mutate campaign state
- enable go-live
- move money

### Account Maintenance Workflow

Account Maintenance is for existing accounts after initial setup intent exists.
It should not be mixed into first-time setup.

Target maintenance areas:

1. Select existing account
2. View account status and readiness drift
3. Review setup evidence and blockers
4. Update profile/setup evidence through safe draft or future account commands
5. Manage users/roles after membership primitives exist
6. Rotate references/credentials after resolver and credential lifecycle exist
7. Review audit/support history

Allowed first maintenance foundation:

- read existing setup draft/readiness evidence
- show missing evidence and blockers
- route to safe setup sections

Not allowed until future primitives exist:

- update durable account records
- activate/suspend/disable accounts
- invite/remove users
- rotate external references
- rotate credentials
- mutate permissions

## Workflow Boundaries

| Workflow | Purpose | Write model now | Future write model |
| --- | --- | --- | --- |
| Account Setup | First-time setup intent and review. | Onboarding draft save, submit, review decision. | Account/account-tenant/membership lifecycle commands. |
| Account Setup Readiness | Check setup completeness. | Read-only projection over draft/current evidence. | Same, plus account lifecycle readiness. |
| Account Maintenance | Existing account operation and drift repair. | Read-only evidence plus links to setup sections. | Account update, role maintenance, lifecycle, reference rotation. |
| Campaign Setup | Campaign draft/readiness after account setup. | Existing campaign readiness and setup surfaces. | Product campaign create/policy/activation wrappers. |

## API Direction

Do not expose a fake product API that only renames admin onboarding routes.

Recommended implementation path:

1. Keep current admin onboarding routes as the shared primitive.
2. Add Referral SaaS product wrappers only when they add product boundary value:
   account-safe response shape, account setup state mapping, permission posture,
   and no `tenant_code` exposure.
3. Add durable account/member APIs only after additive schema and service tests.

Candidate product route families:

| Route family | Timing | Purpose |
| --- | --- | --- |
| `/v1/referral-saas/account-setup/drafts` | Near-term wrapper candidate | Save setup intent from product UI using onboarding draft primitive. |
| `/v1/referral-saas/account-setup/{draft_ref}/readiness` | Near-term wrapper candidate | Read integrated readiness in product language. |
| `/v1/referral-saas/accounts` | Future after schema | Durable account creation/read lifecycle. |
| `/v1/referral-saas/accounts/{account_ref}/maintenance` | Future after schema | Account maintenance projection. |
| `/v1/referral-saas/accounts/{account_ref}/memberships` | Future after membership schema | Invite/list/update members. |
| `/v1/referral-saas/accounts/{account_ref}/external-refs` | Future after resolver schema | Register/rotate/suspend external references. |

## Frontend Direction

The Referral SaaS workspace should eventually expose separate product entries:

- Account Setup
- Account Maintenance

Account Setup target screen model:

- Stepper or task list with Company profile, Users and roles, Integrations,
  Readiness check, Review handoff, Campaign setup handoff.
- Each step contains its own primary action.
- Readiness is embedded as the checkpoint, not the whole workflow.
- Draft save/review actions only appear when wired to the existing safe draft
  APIs.

Account Maintenance target screen model:

- Account selector once safe account lookup exists.
- Account health/readiness drift.
- Setup evidence summary.
- Members and role posture.
- External reference posture.
- Audit/support history.
- Maintenance actions disabled or hidden until backend command primitives exist.

## Data And Permission Rules

- `tenant_code` remains internal.
- External references remain the user-facing scope until account membership and
  account lookup exist.
- Account/workspace picker must not be hardcoded. It needs a safe account read
  source or draft list source.
- Caller-supplied `account_ref` must not authorize access by itself.
- Membership and role checks must gate future account maintenance commands.
- Draft save and review commands must keep idempotency and audit evidence.
- Maintenance actions that alter access, references, or lifecycle must require
  reason, actor, idempotency, and audit evidence.

## Implementation Sequence

Recommended tasks after this architecture contract:

1. TASK-191: Define Referral SaaS account setup product wrapper contract over onboarding drafts.
2. TASK-192: Build Account Setup workflow shell using existing draft/readiness primitives.
3. TASK-193: Connect Account Setup workflow to draft save, validation, submit, and review APIs.
4. TASK-194: Define Account Maintenance workflow contract and read model.
5. TASK-195: Build Account Maintenance read-only shell.
6. TASK-196: Add account/draft selector using safe existing source or new account source.
7. TASK-197: Add additive account/tenant-link/external-ref schema final review.
8. TASK-198+: Implement durable account/member primitives in small backend slices.

## Acceptance Gates

Before Account Setup can be called real:

- setup evidence can be saved through a safe persisted draft
- validation and readiness are shown inline
- submit-for-review and review result are visible
- `tenant_code`, secrets, money, and live commands are not exposed
- tests cover draft save, validation, idempotency, audit link, and no-live-action
  guardrails

Before Account Maintenance can be called real:

- an account or draft can be selected from a safe source
- maintenance read model is scoped and permission checked
- maintenance actions are disabled until command primitives exist
- future write commands have idempotency, audit, reason, and permission tests

Before Account Selector can be called real:

- source records are not hardcoded
- access is derived from admin/operator role or future membership
- inactive/suspended/disabled references are handled safely
- no internal tenant identifier is required from the user

## Explicit Non-Goals

This task does not implement:

- database schema
- migrations
- account service
- membership service
- external reference resolver
- route handlers
- frontend pages
- account creation
- account maintenance commands
- user invitations
- credential rotation
- campaign activation
- support-case persistence
- repair/replay/retry commands
- reward, funding, fulfilment, settlement, commission, wallet, invoice, payout,
  sponsor billing, marketplace-depth, white-label/embed, SaaS billing, or broad
  DLaaS behavior

## Readiness Decision

The next build should not be more readiness-page polish. It should create the
real Account Setup workflow around the existing safe onboarding draft and
readiness primitives, while keeping durable account and membership behavior as
explicit future backend slices until schema and permission foundations are
implemented.
