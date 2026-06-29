# Onboarding Draft Save API Boundary

Status: Accepted for TASK-086 on 2026-06-29.

## Purpose

This document defines the smallest safe future API boundary for onboarding draft/save behavior in DLaaS.

It exists so later implementation tasks can add onboarding persistence without accidentally creating live platform records, enabling go-live actions, exposing internal identifiers, or bypassing audit, idempotency, validation, permission, and redaction controls.

This is a contract document only. It does not add routes, services, schema, migrations, persistence, database access, frontend behavior, account creation, invite delivery, credential lifecycle, webhook delivery, campaign publication, funding, wallet movement, fulfilment, settlement, retry, audit writes, go-live activation, or money movement.

## Source Documents

- `docs/sa/ONBOARDING_DATA_CONTRACT.md`
- `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md`
- `docs/sa/TENANT_IDENTIFIER_BOUNDARY_DECISION.md`
- `docs/sa/TENANT_ACCOUNT_BOUNDARY_MAP.md`
- `docs/sa/TENANT_ACCOUNT_LIFECYCLE_MEMBERSHIP_MODEL.md`
- `docs/sa/PARTICIPANT_TAXONOMY_PERMISSION_MAP.md`
- `docs/API_PERMISSION_MATRIX.md`
- `services/onboarding/onboarding_state_projection_service.py`
- `services/onboarding/onboarding_readiness_aggregation_service.py`
- `apps/api/routers/admin_onboarding.py`
- `frontend/src/pages/admin/OperatorDemoHomePage.tsx`

## Future Boundary, Not Current Implementation

The current onboarding backend is read-only:

- TASK-082 projects onboarding state from supplied evidence.
- TASK-083 aggregates readiness from that projection.
- TASK-084 exposes `GET /admin/onboarding/state` as an authenticated read-only admin endpoint.
- TASK-085 consumes the read-only state on the operator demo home while preserving demo fallback.

No current source in this task provides a persisted onboarding draft table, draft command service, draft route, idempotency store, draft audit writer, or external reference resolver. Future implementation must add those pieces in separate tasks after schema, permission, idempotency, audit, and rollback review.

## Smallest Safe Capability

The smallest safe draft/save capability is:

1. Accept a bounded onboarding draft payload shaped by `ONBOARDING_DATA_CONTRACT.md`.
2. Store or update draft intent only.
3. Preserve external references as the user-facing scope.
4. Resolve internal tenant context only after permission and reference checks.
5. Validate draft data and return missing evidence safely.
6. Return a draft state suitable for read-only readiness review.
7. Record audit evidence without sensitive values.
8. Be idempotent for repeated requests.

The smallest safe capability must not create or mutate live platform entities.

## Draft Lifecycle States

Future implementation should use explicit draft states. These are contract states, not current database enum values.

| State | Meaning | Live action allowed? |
| --- | --- | --- |
| `DRAFT_CREATED` | A new onboarding draft was accepted and stored. | No |
| `DRAFT_UPDATED` | An existing draft was updated safely. | No |
| `VALIDATION_FAILED` | Draft input was rejected or saved as invalid according to future route policy. | No |
| `READY_FOR_REVIEW` | Draft evidence is complete enough for operator review. | No |
| `BLOCKED` | A blocker prevents review or future activation. | No |
| `DISCARDED` | Draft is no longer active for review or update. | No |

`READY_FOR_REVIEW` is not go-live. It only means the draft can be reviewed.

## Strict Separation From Live Platform Actions

Draft/save behavior is separate from all live platform actions.

| Draft/save may do later | Draft/save must not do |
| --- | --- |
| Save organisation setup intent | Create a real tenant, account, or organisation |
| Save producer/sponsor setup intent | Create sponsor wallets, funding contracts, invoices, or budget reservations |
| Save distributor setup intent | Create, activate, suspend, or terminate distributors |
| Save member/role setup intent | Create users, memberships, seats, identity-provider records, or deliver invites |
| Save campaign/opportunity setup intent | Create, publish, launch, pause, or close campaigns/opportunities |
| Save webhook/API setup intent | Generate credentials, register callback URLs, subscribe webhooks, sign payloads, or deliver webhooks |
| Validate readiness for review | Activate go-live |
| Return missing evidence and blockers | Reserve, release, fulfil, settle, reverse, retry, or move money |

Future draft/save implementation must treat any live action request as unsafe unless a separate reviewed task explicitly implements that action.

## Idempotency Model

Future draft/save commands must require an idempotency model before implementation.

Minimum contract:

| Item | Requirement |
| --- | --- |
| Idempotency key | Required for create, update, validate, and submit-for-review commands. |
| Scope | Key must be scoped to actor, external tenant/account reference, route action, and draft reference where available. |
| Replay behavior | Repeating the same request with the same key and same payload returns the existing result. |
| Conflict behavior | Reusing the same key with a different payload returns `409 IDEMPOTENCY_CONFLICT`. |
| Duplicate draft | A duplicate active draft for the same external scope returns the existing draft or a `409 DUPLICATE_DRAFT`, depending on route contract. |
| Expiry | Key retention must be long enough for client retries and operational support. |
| Side effects | Duplicate/replayed requests must not create duplicate drafts, audit rows with misleading action status, tenant links, invites, credentials, campaigns, webhooks, funding, fulfilment, settlement, retry records, or money movement. |

Idempotency evidence should include a safe request hash, actor reference, action type, correlation ID, and prior result reference.

## Duplicate And Conflict Handling

Future implementation must distinguish:

| Situation | Safe response |
| --- | --- |
| Same idempotency key, same payload | Return prior result with duplicate/replayed status metadata. |
| Same idempotency key, different payload | `409 IDEMPOTENCY_CONFLICT`. |
| Active draft already exists for the same external scope | Return existing active draft or `409 DUPLICATE_DRAFT` with safe details. |
| Draft update against stale version | `409 STALE_DRAFT`. |
| Draft is discarded | `409 DRAFT_DISCARDED` or `404` if the caller cannot access it. |
| External reference unresolved | `404 UNKNOWN_REFERENCE` or `422 UNKNOWN_REFERENCE`, depending on whether the route requires existing reference resolution. |
| Invalid lifecycle transition | `409 INVALID_DRAFT_STATE`. |

Responses must not expose SQL errors, stack traces, internal table names, raw audit payloads, provider details, secrets, UCNs, wallet internals, settlement internals, fulfilment internals, or retry internals.

## Audit Model

Draft/save is not money movement, but it is still a sensitive onboarding mutation. Future implementation must write audit evidence before production use.

Minimum audit fields:

| Field | Requirement |
| --- | --- |
| Actor | Required. Human, admin, account user, integration client, or system source. |
| Actor role | Required for permission review. |
| Action type | Required. Examples: `ONBOARDING_DRAFT_CREATE`, `ONBOARDING_DRAFT_UPDATE`, `ONBOARDING_DRAFT_VALIDATE`, `ONBOARDING_DRAFT_SUBMIT_FOR_REVIEW`, `ONBOARDING_DRAFT_DISCARD`. |
| Action status | Required. Success, validation failed, duplicate/no-op, conflict, blocked, or denied. |
| External tenant reference | Required when supplied. |
| Organisation reference | Required when supplied. |
| Role-specific references | Preserve `producer_ref`, `sponsor_ref`, `distributor_ref`, `campaign_code`, and `opportunity_ref` when supplied. |
| Resolved tenant scope | Internal-only `tenant_code` where resolution is implemented and authorized. |
| Draft reference | Required after a draft exists. |
| Idempotency key reference | Required for duplicate-sensitive commands. |
| Correlation ID | Required for support trace. |
| Request source | UI, API client, system job, or integration source. |
| Before hash | Safe hash or version of prior draft state. Do not store raw sensitive values in audit. |
| After hash | Safe hash or version of new draft state. Do not store raw sensitive values in audit. |
| Reason | Required for discard, blocked override, manual review state changes, and future repair actions. |

Audit must not store secrets, API keys, client secrets, signing material, tokens, passwords, certificates, raw provider payloads, raw audit payloads, raw UCNs, settlement internals, fulfilment internals, retry internals, or unrestricted draft payloads.

## Tenant And External Reference Resolution

User-facing onboarding uses external references. `tenant_code` remains internal.

Supported external reference fields:

- `external_tenant_ref`
- `organisation_ref`
- `producer_ref`
- `sponsor_ref`
- `distributor_ref`
- `campaign_code`
- `opportunity_ref`

Resolution rules for future implementation:

1. Validate supplied external references before resolving internal tenant context.
2. Resolve references through an approved account/tenant identity layer when implemented.
3. A resolvable external reference must map to exactly one active internal tenant scope.
4. Suspended, disabled, archived, rotated, or ambiguous references must not authorize writes.
5. Operator/admin routes may include internal `tenant_code` in audit and internal support metadata only.
6. Partner, distributor, producer, sponsor, customer, or public-facing responses must not expose `tenant_code` as the primary identifier.
7. Drafts created before reference resolution exists must be marked as unresolved, shell-only, or missing evidence rather than fabricating tenant scope.

## Draft Payload Scope

Future draft payloads should follow sections from `ONBOARDING_DATA_CONTRACT.md`:

- `company`
- `producer_sponsor`
- `distributor`
- `member_role`
- `campaign_opportunity`
- `webhook_api`

Each section must use the contract field names already documented in TASK-081. Unknown fields should be rejected or safely ignored according to future route policy, but unsafe field names must trigger redaction handling.

Unsafe field categories include:

- `tenant_code` as a user-facing identifier
- raw UCNs or private identifiers
- secrets, API keys, client secrets, tokens, passwords, certificates, or signing material
- raw provider payloads
- raw audit payloads
- wallet, funding, settlement, fulfilment, retry, or money movement internals

## Validation Model

Future draft/save implementation must validate at multiple layers.

| Layer | Examples |
| --- | --- |
| Field validation | Required strings, allowed enum values, email shape where needed, URL shape for callback placeholders, bounded lengths, no unsafe keys. |
| Cross-section validation | Campaign references should match organisation and producer/sponsor intent; distributor setup should match intended distribution model; webhook setup should match campaign integration intent. |
| Permission validation | Actor role and membership must allow creating/updating the requested draft scope. |
| Reference validation | External references must be unique, resolvable, active, and accessible where resolver exists. |
| Readiness validation | Draft can be `READY_FOR_REVIEW` only when required evidence is present and no blocker remains. |
| Safety validation | Requests must not include live action directives such as create tenant, send invite, publish campaign, generate credential, deliver webhook, activate go-live, fund, fulfil, settle, retry, or move money. |

Validation outcomes should use bounded missing-evidence and blocker shapes compatible with TASK-082 and TASK-083.

## Permission Boundaries

Future draft/save routes must use the narrowest helper and membership checks available at implementation time.

| Actor family | Draft/save capability direction |
| --- | --- |
| Platform operator | May create, update, validate, discard, or submit drafts across explicit external scopes, subject to audit. |
| System admin | May inspect/support drafts where route purpose is system/support; broad business mutation should be avoided. |
| Distribution admin | May manage distribution, distributor, route, and campaign setup draft sections where authorized. |
| Finance admin | Should not manage onboarding drafts by default except future funding-intent review sections explicitly designed for finance. No money actions. |
| Producer/sponsor/company admin | May manage own organisation, producer/sponsor, campaign-intent, and integration-intent drafts after membership model exists. |
| Distributor/partner admin | May manage own distributor/partner setup draft sections after membership and role scope exist. |
| Read-only/support viewer | May read safe draft/readiness state only; cannot save, submit, discard, or validate if validation writes audit. |
| Public/anonymous | No draft/save access. |
| Worker | No draft/save access. |

Partner credentials must not imply producer, sponsor, distributor, or customer ownership unless the route explicitly checks that scope.

## Safe Error Model

Future endpoints should return stable, safe errors.

Recommended envelope:

```json
{
  "code": "VALIDATION_FAILED",
  "message": "The onboarding draft could not be saved.",
  "correlation_id": "corr_123",
  "details": [
    {
      "section": "campaign_opportunity",
      "field": "campaign_code",
      "code": "REQUIRED",
      "message": "Campaign code is required before review."
    }
  ]
}
```

Recommended safe error codes:

| Code | Meaning | HTTP direction |
| --- | --- | --- |
| `VALIDATION_FAILED` | Field or cross-section validation failed. | 400 or 422 |
| `DUPLICATE_DRAFT` | An active draft already exists for the same scope. | 409 |
| `IDEMPOTENCY_CONFLICT` | Same idempotency key was reused with a different payload. | 409 |
| `STALE_DRAFT` | Caller attempted to update an old draft version. | 409 |
| `UNKNOWN_REFERENCE` | External reference cannot be resolved or is inaccessible. | 404 or 422 |
| `PERMISSION_DENIED` | Actor lacks required role, membership, or scope. | 403 |
| `READINESS_BLOCKED` | Draft cannot move to review because blockers remain. | 409 or 422 |
| `UNSAFE_OPERATION_ATTEMPTED` | Request attempted a live action outside draft/save. | 400 |
| `LIVE_DB_VERIFICATION_BLOCKED` | Runtime verification dependency remains blocked. | 409 or 503 depending on route purpose |
| `DRIFT_VERIFICATION_BLOCKED` | Drift resolution dependency remains blocked. | 409 or 503 depending on route purpose |

Errors must not include internal table names, SQL, stack traces, unrestricted exception details, secrets, private identifiers, raw payloads, or money movement internals.

## Redaction And Non-Exposure Rules

All future draft/save routes must preserve these redaction rules:

- Do not expose `tenant_code` as the primary user-facing onboarding identifier.
- Do not expose raw UCNs or private customer identifiers.
- Do not expose secrets, API keys, client secrets, signing material, access tokens, refresh tokens, passwords, certificates, or stored credentials.
- Do not expose webhook signing, delivery, retry, dead-letter, or provider internals.
- Do not expose funding, wallet, settlement, fulfilment, retry, or reconciliation internals.
- Do not expose raw audit payloads.
- Do not log sensitive draft field values.
- Do not return stack traces, SQL errors, environment variable names, or database DSNs.

Redaction should be observable through safe redaction categories, not through leaked values.

## Future Endpoint Shapes

These endpoint shapes are contract sketches only. They are not implemented by TASK-086.

### `POST /admin/onboarding/drafts`

Creates a new onboarding draft intent.

Requirements:

- Authenticated admin/operator or future authorized account role.
- Idempotency key required.
- External reference scope required.
- Stores draft only after a future schema/service task exists.
- Does not create account, tenant, organisation, user, membership, invitation, campaign, credential, webhook, funding, wallet, fulfilment, settlement, retry, audit side effect beyond future audit evidence, or money movement.

### `PUT /admin/onboarding/drafts/{draft_ref}`

Updates an existing draft intent.

Requirements:

- Authenticated actor with draft ownership or admin/operator authority.
- Idempotency key required.
- Version or ETag required for stale update prevention.
- Unsafe operation fields rejected.

### `GET /admin/onboarding/drafts/{draft_ref}`

Reads a persisted draft when future persistence exists.

Requirements:

- Read-only.
- Redacted response.
- External references visible; internal tenant scope operator-only if included at all.

### `POST /admin/onboarding/drafts/{draft_ref}/validate`

Validates a draft and returns readiness/missing evidence.

Requirements:

- Idempotency key required if validation writes audit or validation result state.
- Does not activate go-live.
- Does not create downstream records.

### `POST /admin/onboarding/drafts/{draft_ref}/submit-for-review`

Moves a draft to `READY_FOR_REVIEW` if validation passes.

Requirements:

- Idempotency key required.
- Actor and role audited.
- Requires no blockers.
- Does not activate go-live or publish any platform configuration.

## Explicitly Disabled Endpoint Families

TASK-086 does not authorize these endpoints or behaviors:

- Create tenant/account/organisation.
- Create producer, sponsor, partner, distributor, referrer, customer, user, membership, seat, invite, or identity-provider record.
- Send invite.
- Create live campaign or opportunity.
- Publish, launch, pause, close, or activate campaign/opportunity.
- Generate, rotate, reveal, or store credentials/secrets.
- Subscribe, sign, queue, retry, replay, deliver, or dispatch webhook.
- Activate go-live.
- Create funding records, wallets, reservations, releases, invoices, settlements, fulfilments, retries, reversals, payouts, or money movement.
- Write audit records in this task.

## Safety Gates Before Implementation

Before any future implementation task adds draft/save behavior, it must pass these gates:

1. Schema review for draft storage, versioning, idempotency evidence, and audit references.
2. Migration review and clean DB replay validation.
3. Permission matrix update if new route helpers or role behavior are added.
4. Idempotency tests for create, update, validate, submit-for-review, replay, and conflict.
5. Duplicate draft tests.
6. Stale draft/version conflict tests.
7. Audit tests for actor, actor role, external refs, internal tenant scope where available, correlation ID, before/after hash, and safe metadata.
8. Redaction tests for secrets, credentials, private identifiers, internal tenant identifiers, raw audit, provider, webhook, money, fulfilment, settlement, and retry internals.
9. No-money/no-go-live tests proving disabled endpoint families remain unavailable.
10. Permission tests for allowed role, rejected adjacent role, cross-tenant denial, read-only viewer denial for writes, and partner/distributor/producer scope.
11. Safe error tests for validation, duplicate, stale, unknown reference, permission denied, readiness blocked, and unsafe operation attempted.
12. Rollback plan for schema and route behavior.
13. TASK-027/TASK-028 decision: either complete live DB verification/drift resolution or explicitly document why draft persistence can safely proceed without it.

## Mapping To Existing Onboarding Tasks

| Source | Relationship to draft/save boundary |
| --- | --- |
| TASK-081 onboarding data contract | Defines section and field vocabulary for drafts. |
| TASK-082 onboarding state projection | Future draft reads should be projectable into the same safe state shape. |
| TASK-083 readiness aggregation | Future draft validation should feed the same readiness categories and safe statuses. |
| TASK-084 read-only admin endpoint | Existing read-only endpoint remains separate from future draft/save commands. |
| TASK-085 operator demo integration | Frontend can consume read-only state; future draft/save must not make the demo home a live command surface without a separate task. |
| TASK-027/TASK-028 | Remain blocked and must not be silently bypassed for live DB/state assumptions. |

## Readback Checklist

Before starting any implementation task based on this boundary, confirm:

- Draft/save is still separated from live tenant/account creation.
- Draft/save is still separated from user invite delivery.
- Draft/save is still separated from campaign publication and go-live activation.
- Draft/save is still separated from credential lifecycle and webhook delivery.
- Draft/save is still separated from funding, wallet, fulfilment, settlement, retry, and money movement.
- Every mutating draft route has an idempotency key model.
- Duplicate and replay behavior is explicit.
- Stale update handling is explicit.
- Audit actor, actor role, external references, correlation ID, idempotency evidence, and before/after hash requirements are explicit.
- `tenant_code` remains internal.
- External references are the user-facing boundary.
- Permission boundaries are role- and scope-aware.
- Safe error envelopes are bounded and do not leak internals.
- Redaction rules cover secrets, credentials, private identifiers, provider payloads, audit payloads, wallet/funding/fulfilment/settlement/retry internals, SQL, stack traces, and DSNs.
- TASK-027 and TASK-028 remain blocked unless separately completed or explicitly deferred with a reviewed decision.
- No route, service, schema, migration, persistence, DB access, frontend change, audit write, webhook dispatch, credential generation, go-live command, or money movement was introduced by TASK-086.
