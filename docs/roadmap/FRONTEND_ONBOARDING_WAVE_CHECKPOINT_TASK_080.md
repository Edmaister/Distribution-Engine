# TASK-080 Frontend Onboarding Wave Checkpoint

Date: 2026-06-28

Status: Accepted for TASK-080.

This checkpoint records the completed frontend onboarding/demo wave from TASK-070 through TASK-079 and defines the next implementation wave. It is documentation only. No frontend code, backend code, tests, schema, migrations, secrets, or database access changed in TASK-080.

## Completed Wave

| Task | Completed capability | Current posture |
| --- | --- | --- |
| TASK-070 | Company / organisation onboarding shell | Local UI shell for organisation profile, `external_tenant_ref`, `organisation_ref`, country, industry, admin contact, and intended role. |
| TASK-071 | Producer / sponsor onboarding shell | Local UI shell for producer/sponsor setup, producer/sponsor references, funding intention, and campaign ownership context. |
| TASK-072 | Distributor onboarding shell | Local UI shell for distributor setup, channel model, market, participation intent, and disabled lifecycle/wallet placeholders. |
| TASK-073 | User/member invite and role assignment shell | Local UI shell for invite intent, participant type, role family, access scope, and disabled invite/role actions. |
| TASK-074 | Campaign / opportunity setup wizard shell | Local UI wizard for campaign, opportunity, participant, distribution, outcome, reward/commission, funding, and go-live intent. |
| TASK-075 | Webhook / API credential setup shell | Local UI shell for integration owner, callback placeholder, event categories, auth method intent, payload format, and disabled credential/webhook actions. |
| TASK-076 | Onboarding readiness checklist | Local/demo readiness view linking onboarding categories, blockers, and disabled go-live review controls. |
| TASK-077 | Operator demo home | Frontend demo home linking onboarding, readiness, existing monitoring, backend-ready diagnostics, and distributor-safe status. |
| TASK-078 | Distributor safe status display enhancement | Distributor portal can render safe status fields without exposing raw provider, settlement, tenant, UCN, or sensitive identifiers. |
| TASK-079 | End-to-end frontend demo journey smoke test | Smoke proof validates the frontend demo path across onboarding, readiness, operations monitoring, and distributor-safe status using local shell state and mocked-safe responses. |

## What The Platform Can Demonstrate Now

The product can now demonstrate an onboarding-first DLaaS journey in the frontend:

1. A platform operator starts at the operator demo home.
2. The operator walks through company / organisation setup.
3. The operator drafts producer / sponsor setup intent.
4. The operator drafts distributor setup intent.
5. The operator drafts member, invite, and role-family intent.
6. The operator drafts campaign / opportunity setup intent.
7. The operator drafts webhook / API credential setup intent without creating secrets.
8. The operator reviews onboarding readiness and blockers.
9. The operator moves into existing read-only monitoring surfaces.
10. The distributor portal shows safe outcome/status language without internal leakage.

This supports internal product demos, roadmap alignment, and UI walkthroughs using local or mocked data. It does not prove live runtime data, live database state, production onboarding, or command workflows.

## Shell-Only And Local-Only Areas

The following areas are intentionally shell-only or local-only:

- company / organisation form state;
- producer / sponsor form state;
- distributor onboarding form state;
- member invite and role assignment form state;
- campaign / opportunity wizard form state;
- webhook / API setup form state;
- onboarding readiness status aggregation;
- operator demo home readiness/status counters;
- frontend smoke test data for Distribution Command Centre and distributor portal.

These screens make unavailable backend integrations explicit. They should not be presented as production onboarding, persistence, or lifecycle command workflows.

## Explicitly Not Live Yet

The completed frontend wave does not implement:

- real tenant, company, account, or organisation creation;
- distributor creation, activation, suspension, or route enablement;
- real user invites, membership creation, seat assignment, role enforcement, or auth claim changes;
- campaign creation, opportunity publication, route generation, launch, pause, close, or go-live approval;
- API key creation, secret generation, secret rotation, callback registration, webhook subscription, webhook signing, or webhook delivery;
- funding account creation, wallet creation, budget reservation, invoice generation, sponsor billing mutation, fulfilment, settlement, payout, retry, replay, repair, or money movement;
- live DB verification, production smoke tests, external E2E environment checks, or production data usage.

## Demo Flow

Recommended demo flow:

1. Open `/admin/demo-home`.
2. Use setup journey links for:
   - `/admin/onboarding/company`;
   - `/admin/onboarding/producer-sponsor`;
   - `/admin/onboarding/distributor`;
   - `/admin/onboarding/members-roles`.
3. Continue to readiness setup:
   - `/admin/onboarding/campaign-opportunity`;
   - `/admin/onboarding/webhook-api`;
   - `/admin/onboarding/readiness`.
4. Move into monitoring:
   - `/admin/distribution`;
   - `/admin/distribution/operations`;
   - `/admin/channels`;
   - `/admin/events`;
   - `/admin/health`.
5. Show distributor-safe status at `/distributor` or `/distributor/operations`.

Guardrails to call out during the demo:

- `tenant_code` stays internal.
- External setup uses `external_tenant_ref`, `organisation_ref`, `producer_ref`, `sponsor_ref`, and `distributor_ref`.
- Live action buttons remain disabled where backend commands are not intentionally wired.
- Distributor-safe status hides raw provider, settlement, tenant, UCN, and sensitive internal details.

## Test Coverage And Validation Baseline

Current validation baseline from TASK-079:

- `npm.cmd test -- OnboardingDemoJourneySmoke.test.tsx` passed with 5 tests.
- Related onboarding/demo/distribution/distributor tests passed with 36 tests across 10 files.
- Full `npm.cmd test` passed with 66 tests across 20 files.
- `npm.cmd run build` passed.
- `npm.cmd run lint` passed with 0 errors and the existing 42 warnings in pre-existing frontend files.

The smoke proof covers route rendering, onboarding navigation, readiness links, disabled live actions, read-only operations monitoring, and distributor-safe status redaction checks.

## Remaining Blockers

TASK-027 remains blocked by missing approved safe read-only runtime database access. No DB connection should be attempted without environment name, read-only credentials, write-protection confirmation, and explicit approval for runtime/API smoke checks.

TASK-028 remains blocked because TASK-027 has not produced verified live/schema drift evidence. TASK-028 should only resolve confirmed live/schema mismatches or explicitly deferred unknowns.

These blockers do not prevent local frontend demo walkthroughs, but they prevent claiming live-state readiness or release confidence.

## Recommended Next Implementation Wave

The next wave should move from UI shells to safe backend/read-model contracts without jumping straight to live mutations.

Recommended order:

1. Consolidate onboarding data contracts from the frontend shells.
2. Add read-only onboarding state projection helpers using existing source truth where available and explicit missing-evidence markers where not.
3. Add an onboarding readiness aggregation service.
4. Add a read-only admin onboarding state endpoint.
5. Integrate the operator demo home with read-only onboarding readiness state.
6. Add safe draft/save API design and stop conditions, without implementing writes yet unless separately approved.
7. Define audit/event capture requirements for future onboarding mutations.
8. Add RBAC and permission contract tests for onboarding/readiness routes.
9. Connect frontend shells to read-only/mock-safe backend state where available.
10. Add a checkpoint after the next wave.

## Guardrails For Next Wave

- Prefer read-only service/API contracts before mutation.
- Keep `tenant_code` internal and map external references explicitly.
- Do not implement account creation, invites, campaign publication, credentials, webhook delivery, funding, fulfilment, settlement, billing, retries, or money movement unless a later task explicitly scopes it.
- Do not add schema or migrations unless the task proves they are required and keeps them additive.
- Preserve auth, audit, tenant, privacy, redaction, and data-isolation boundaries.
- Preserve TASK-027/TASK-028 blocked status until approved live verification access exists.
