# Referral SaaS Account Maintenance Read Model Contract

TASK ID: TASK-194

Product boundary: Referral SaaS.

Status: Contract only. No runtime behavior, frontend page, route, schema,
migration, permission, OpenAPI, or test implementation is made by this task.

## Boundary

This document defines the first Account Maintenance workflow contract and read
model for Referral Management and Campaign Attribution SaaS. It keeps Account
Maintenance separate from first-time Account Setup and prevents fake
maintenance commands until durable account, tenant-link, external-reference,
membership, and lifecycle primitives exist.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_MAINTENANCE_WORKFLOW_ARCHITECTURE.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_WRAPPER_CONTRACT.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

Implementation/source files inspected:

- `apps/api/routers/admin_onboarding.py`
- `frontend/src/api/endpoints/adminOnboarding.ts`
- `services/onboarding/onboarding_state_projection_service.py`
- `services/onboarding/onboarding_draft_validation_service.py`
- `services/onboarding/onboarding_draft_repository.py`
- `dp/migrations/080_onboarding_draft_persistence.sql`
- `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`

## Product Decision

Account Maintenance starts as a read-only evidence and drift workflow over the
current safe onboarding setup sources. It must not be presented as profile
editing, role administration, lifecycle control, reference rotation, or
credential maintenance until real account and membership primitives exist.

Account Setup answers:

- How do we capture first-time setup intent?
- Is setup evidence complete enough to submit for review?
- Can the customer move to campaign setup?

Account Maintenance answers:

- Which existing setup/account evidence is currently visible?
- Has setup evidence drifted, gone missing, or become blocked?
- Which setup area should the operator revisit?
- Which future maintenance command is still unavailable because backend
  primitives are missing?

## Current Source Of Truth

Near-term Account Maintenance may read only from current safe sources:

| Source | Current fact | Maintenance use |
| --- | --- | --- |
| `GET /admin/onboarding/state` | Read-only setup state over external references. | Account health/readiness snapshot. |
| Onboarding readiness aggregation | Safe category, blocker, missing-evidence, guardrail, and redaction projection exists. | Drift and maintenance checklist. |
| Saved onboarding drafts | Draft persistence tables and guarded draft actions exist. | Evidence that setup intent was captured, when a safe lookup source exists. |
| Setup draft actions | Validation, save, submit-for-review, and review-decision actions exist. | Route user back to setup workflow for evidence correction. |

Not source of truth yet:

- account table
- account-to-tenant link
- external-reference resolver table
- membership table
- invitation table
- account lifecycle/status table
- account maintenance command audit timeline

## Read Model

The Account Maintenance read model should be product-shaped and safe:

```json
{
  "accountMaintenanceStatus": "READ_ONLY_EVIDENCE",
  "accountScope": {
    "externalTenantRef": "demo-platform-operator",
    "organisationRef": "demo-organisation"
  },
  "accountSummary": {
    "displayName": "demo-organisation",
    "accountRef": null,
    "membershipSource": "FUTURE",
    "tenantLinkSource": "FUTURE"
  },
  "health": {
    "overallStatus": "GO_LIVE_DISABLED",
    "readyCount": 0,
    "blockedCount": 1,
    "missingEvidenceCount": 6,
    "goLiveEnabled": false
  },
  "maintenanceAreas": [],
  "blockedCommands": [],
  "nextActions": [],
  "guardrails": [],
  "redactions": []
}
```

### Maintenance Areas

The first read model should project these areas:

| Area | Current source | Allowed action now | Future command |
| --- | --- | --- | --- |
| Account profile | Onboarding company evidence/readiness category. | View evidence and route to setup draft. | Update durable account profile. |
| External references | External scope and readiness evidence. | View checked references. | Register, rotate, suspend, or disable references. |
| Users and roles | Member-role setup evidence/readiness category. | View setup intent and route to setup draft. | Invite, remove, change role, disable access. |
| Integration posture | Webhook/API setup evidence/readiness category. | View setup intent and missing evidence. | Rotate credential, update callback, enable delivery. |
| Campaign handoff | Campaign readiness link and setup evidence. | Route to campaign readiness. | Product campaign create/activate commands. |
| Reporting posture | Referral SaaS report surface. | Route to reports. | Persisted export/download scheduling. |
| Audit/support posture | Existing safe audit references where available. | Show reference-only evidence. | Maintenance timeline and support-case write workflow. |

### Blocked Commands

The read model must explicitly mark these as unavailable:

- create account
- activate account
- suspend or disable account
- update account profile as durable source of truth
- invite user
- remove user
- change member role
- rotate external reference
- rotate credential
- enable webhook delivery
- enable go-live
- activate campaign
- retry, replay, or repair events
- reward, funding, fulfilment, settlement, payout, invoice, wallet, or money
  movement

## Product Route Direction

Do not add a product route until it adds product boundary value.

Candidate future route:

| Route | Method | Source | Notes |
| --- | --- | --- | --- |
| `/v1/referral-saas/account-maintenance/readiness` | `GET` | `GET /admin/onboarding/state` plus product mapper | Read-only product shape over external refs. |
| `/v1/referral-saas/accounts/{accountRef}/maintenance` | `GET` | Future durable account/read model | Requires account membership and trusted account resolver first. |

The first implementation may build a frontend read-only shell over the existing
admin onboarding state query before introducing a product API route, as long as
it is clearly labelled as maintenance evidence and does not imply account
commands exist.

## Permission And Scope Rules

- External references may be used for the first maintenance evidence lookup.
- Internal `tenant_code` must not be displayed or requested from the operator.
- Caller-supplied `accountRef` must not authorize access by itself.
- Future account maintenance must derive access from account membership,
  operator role, or a trusted account/external-reference resolver.
- Any future command must require actor, role, reason, idempotency, audit
  evidence, and safe error mapping.

## Frontend Contract

The first Account Maintenance shell should:

- sit beside Account Setup in the Referral SaaS workspace
- state that it is read-only maintenance evidence
- show current account scope from external references
- show account health/readiness drift
- group maintenance areas by profile, references, roles, integrations,
  campaigns, reports, and audit/support
- route evidence fixes back to Account Setup draft actions
- hide or disable all command actions that do not have backend primitives
- never show `tenant_code`, secrets, raw provider payloads, audit payloads,
  webhook delivery payloads, wallet/funding/settlement evidence, or raw UCNs

## Tests Required When Implemented

When the read-only shell or API is implemented, add tests for:

- read model uses external references, not internal tenant identifier
- maintenance areas map from current readiness evidence safely
- blocked commands are present and disabled/hidden
- account creation, invitations, role changes, reference rotation, credential
  rotation, go-live, campaign activation, retry/replay/repair, and money actions
  are absent
- cross-scope/account-ref access is not trusted without a resolver
- no secret, raw identifier, provider payload, webhook payload, audit payload,
  or money evidence leaks

## Explicit Non-Goals

TASK-194 does not add:

- backend routes
- frontend pages
- schema or migrations
- account creation
- account selector
- account lifecycle commands
- tenant-link persistence
- external-reference resolver
- membership writes
- user invitations
- role changes
- reference rotation
- credential lifecycle
- webhook delivery
- campaign activation
- support-case writes
- repair, replay, retry commands
- rewards, funding, fulfilment, settlement, commission, wallet, invoice, payout,
  sponsor billing, treasury, or other money behavior
- broad DLaaS marketplace or distributor behavior
- source-code forks

## Definition Of Done

Account Maintenance has a source-backed read model contract that can drive the
next read-only shell task without confusing maintenance with first-time setup or
pretending unavailable backend account commands exist.
