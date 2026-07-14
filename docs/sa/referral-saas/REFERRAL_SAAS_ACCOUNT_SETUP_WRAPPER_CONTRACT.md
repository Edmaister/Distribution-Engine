# Referral SaaS Account Setup Wrapper Contract

TASK ID: TASK-191

Product boundary: Referral SaaS.

Status: Contract only. No runtime behavior, route, frontend, CSS, database
migration, permission, OpenAPI, or test implementation is made by this task.

## Boundary

This document defines how a future Referral SaaS Account Setup product wrapper
should compose the existing admin onboarding draft/readiness primitives without
pretending that durable SaaS account creation, membership, tenant-link, or
account maintenance primitives exist.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_MAINTENANCE_WORKFLOW_ARCHITECTURE.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

Implementation/source files inspected:

- `apps/api/routers/admin_onboarding.py`
- `frontend/src/api/endpoints/adminOnboarding.ts`
- `services/onboarding/onboarding_draft_repository.py`
- `dp/migrations/080_onboarding_draft_persistence.sql`

## Current Source Of Truth

The current setup write/read foundation is the admin onboarding stack:

| Current primitive | Current route/source | Product wrapper use |
| --- | --- | --- |
| Save draft intent | `POST /admin/onboarding/drafts` | Save first-time account setup evidence. |
| Validate evidence | `POST /admin/onboarding/validate` | Dry-run setup evidence before save or submit. |
| Submit draft | `POST /admin/onboarding/drafts/{draft_ref}/submit-for-review` | Hand setup evidence to operator review. |
| Record review decision | `POST /admin/onboarding/drafts/{draft_ref}/review-decision` | Record review outcome, not activation. |
| Read setup state | `GET /admin/onboarding/state` | Show integrated readiness in product language. |
| Draft persistence | `onboarding_drafts` and related tables | Store setup intent, validation, idempotency, and audit links. |

Current enforced safety facts:

- User-supplied `tenant_code` is rejected by the admin onboarding routes.
- Unsafe payload keys, secrets, credential material, money actions, live launch
  actions, invite actions, tenant creation, and user creation are blocked.
- Draft save and review flows require idempotency keys.
- Draft save creates validation, idempotency, and audit-link evidence.
- The state endpoint is read-only and uses external references as untrusted
  lookup markers.

## Wrapper Decision

Add product wrappers only when they add product boundary value:

- product route names under `/v1/referral-saas/account-setup`
- account-setup vocabulary instead of admin onboarding vocabulary
- safe response states for setup users
- no internal `tenant_code` exposure
- no raw validation, audit, provider, credential, secret, webhook, money, or
  worker payload exposure
- idempotency and audit carry-through from the existing primitive
- clear no-live-action posture

Do not add a wrapper that merely renames the admin route and leaks the same
admin shape.

## Future Product Route Contract

The near-term product wrapper family should be:

| Product route | Method | Composes | Purpose |
| --- | --- | --- | --- |
| `/v1/referral-saas/account-setup/drafts` | `POST` | `POST /admin/onboarding/drafts` | Save product account setup evidence. |
| `/v1/referral-saas/account-setup/validate` | `POST` | `POST /admin/onboarding/validate` | Validate setup evidence without saving. |
| `/v1/referral-saas/account-setup/drafts/{draftRef}/submit-for-review` | `POST` | `POST /admin/onboarding/drafts/{draft_ref}/submit-for-review` | Submit saved setup evidence for review. |
| `/v1/referral-saas/account-setup/drafts/{draftRef}/review-decision` | `POST` | `POST /admin/onboarding/drafts/{draft_ref}/review-decision` | Record operator review outcome. |
| `/v1/referral-saas/account-setup/readiness` | `GET` | `GET /admin/onboarding/state` | Read integrated setup readiness for external references. |

Review-decision access should remain operator/admin scoped. It must not be
available to ordinary account setup users.

## Request Shape

Product wrapper requests should use product names while mapping to the current
primitive internally:

```json
{
  "accountScope": {
    "externalTenantRef": "demo-platform-operator",
    "organisationRef": "demo-organisation",
    "producerRef": "optional-producer",
    "sponsorRef": "optional-sponsor",
    "distributorRef": "optional-distributor",
    "campaignCode": "optional-campaign",
    "opportunityRef": "optional-opportunity"
  },
  "sections": {
    "company": {},
    "producerSponsor": {},
    "distributor": {},
    "memberRole": {},
    "campaignOpportunity": {},
    "webhookApi": {}
  },
  "idempotencyKey": "client-generated-key"
}
```

Mapping rules:

| Product field | Current primitive field |
| --- | --- |
| `accountScope.externalTenantRef` | `scope.external_tenant_ref` |
| `accountScope.organisationRef` | `scope.organisation_ref` |
| `accountScope.producerRef` | `scope.producer_ref` |
| `accountScope.sponsorRef` | `scope.sponsor_ref` |
| `accountScope.distributorRef` | `scope.distributor_ref` |
| `accountScope.campaignCode` | `scope.campaign_code` |
| `accountScope.opportunityRef` | `scope.opportunity_ref` |
| `sections.producerSponsor` | `sections.producer_sponsor` |
| `sections.memberRole` | `sections.member_role` |
| `sections.campaignOpportunity` | `sections.campaign_opportunity` |
| `sections.webhookApi` | `sections.webhook_api` |
| `idempotencyKey` | `idempotency_key` |

The wrapper must reject or strip any caller-supplied internal `tenant_code`.
Rejection is preferred for command routes because silent stripping can hide
unsafe client behavior.

## Response Shape

Product responses should expose product-safe setup state, not raw admin
internals:

```json
{
  "setupStatus": "DRAFT_SAVED",
  "draftRef": "draft_...",
  "draftStatus": "DRAFT_CREATED",
  "idempotencyStatus": "RECORDED",
  "readiness": {
    "ready": false,
    "blockers": [],
    "missingEvidence": []
  },
  "nextAction": {
    "code": "COMPLETE_SETUP_EVIDENCE",
    "label": "Complete setup evidence"
  },
  "guardrails": [
    "NO_LIVE_ACTION",
    "NO_INTERNAL_TENANT_IDENTIFIER"
  ],
  "redactions": []
}
```

Suggested product setup statuses:

| Product status | Current evidence |
| --- | --- |
| `DRAFT_SAVED` | New or updated draft saved safely. |
| `DRAFT_REPLAYED` | Idempotency replay returned existing draft outcome. |
| `VALIDATED_NOT_SAVED` | Dry-run validation completed without persistence. |
| `READY_FOR_REVIEW` | Saved draft has been submitted for review. |
| `REVIEW_RECORDED` | Operator review decision was recorded. |
| `BLOCKED` | Validation/readiness includes blocking evidence. |
| `REJECTED_UNSAFE_SCOPE` | Internal tenant identifier or unsafe scope supplied. |
| `REJECTED_UNSAFE_PAYLOAD` | Secret/live/money/credential/invite/create payload supplied. |
| `IDEMPOTENCY_CONFLICT` | Idempotency key reused with different setup intent. |

## Readiness Contract

`GET /v1/referral-saas/account-setup/readiness` should accept external setup
references and return:

- product account setup stage
- safe setup checklist categories
- blockers and missing evidence
- whether submit-for-review can be attempted
- whether campaign setup can be started
- guardrails and redactions
- no internal tenant identifier

It must not create, update, submit, review, invite, activate, or launch
anything.

## Permission Contract

Initial wrapper permissions may bridge current admin/operator auth until SaaS
account membership exists, but the response must still be Referral SaaS shaped.

| Route family | Initial permitted caller | Future permitted caller |
| --- | --- | --- |
| Draft save/validate | Admin/onboarding admin bridge | Account setup admin/member with setup permission. |
| Submit for review | Admin/onboarding admin bridge | Account setup admin/member with submit permission. |
| Review decision | Operator/admin bridge | Operator/reviewer role only. |
| Readiness read | Admin/onboarding admin bridge | Account member, support, or operator with scoped access. |

Caller-supplied `accountRef` must not authorize access by itself. A future
account resolver must derive tenant/account scope from membership or a trusted
external-reference mapping.

## Explicit Non-Goals

TASK-191 does not add:

- backend routes
- frontend screens
- OpenAPI output
- account creation
- internal tenant creation
- account-to-tenant links
- membership writes
- user invitations
- account selector
- account maintenance commands
- reference rotation
- credential lifecycle
- campaign activation
- webhook delivery
- support-case writes
- repair, replay, or retry commands
- reward, funding, fulfilment, settlement, commission, wallet, invoice, payout,
  sponsor billing, treasury, or other money behavior
- broad DLaaS marketplace or distributor behavior
- source-code forks

## Tests Required When Implemented

When the wrapper is implemented, it needs focused tests for:

- product route surface remains bounded to account setup
- request field mapping to admin onboarding primitives
- camelCase product response shape
- `tenant_code` rejection and no internal tenant identifier leakage
- unsafe payload rejection
- idempotency replay and conflict mapping
- draft save audit/idempotency evidence carry-through
- submit-for-review expected-version behavior
- review-decision operator permission posture
- readiness remains read-only
- no account creation, membership write, invitation, go-live, campaign
  activation, webhook delivery, or money behavior

## Definition Of Done

The future Account Setup wrapper can proceed only when implementation preserves
the existing onboarding draft safety controls, returns a product-safe setup
shape, and makes clear that setup evidence capture is not the same as durable
account creation.
