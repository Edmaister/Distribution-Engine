# Onboarding Audit And Event Capture Design

Status: Accepted for TASK-087 on 2026-06-29.

## Purpose And Scope

This document defines audit and event evidence requirements for future onboarding mutation tasks across DLaaS organisation, participant, member/role, campaign, and integration setup.

It gives future implementation tasks a stable contract for what evidence they must capture when onboarding moves from read-only projection and shell state into bounded draft/save behavior.

This is a design document only. It does not add backend routes, frontend code, service implementation, schema, migrations, persistence, database access, audit writes, event persistence, webhook dispatch, retry, replay, repair, credential lifecycle, go-live activation, funding, fulfilment, settlement, or money movement.

## Source Documents

- `docs/sa/ONBOARDING_DATA_CONTRACT.md`
- `docs/sa/ONBOARDING_DRAFT_SAVE_API_BOUNDARY.md`
- `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md`
- `docs/sa/WEBHOOK_EVENT_CATALOG.md`
- `docs/API_PERMISSION_MATRIX.md`
- `docs/sa/TENANT_IDENTIFIER_BOUNDARY_DECISION.md`
- `services/onboarding/onboarding_state_projection_service.py`
- `services/onboarding/onboarding_readiness_aggregation_service.py`
- `apps/api/routers/admin_onboarding.py`

`docs/sa/WEBHOOK_PAYLOAD_ENVELOPE_CONTRACT.md` does not exist at the time of TASK-087. This design therefore uses the payload envelope and naming rules in `WEBHOOK_EVENT_CATALOG.md` as the current webhook contract source.

## Future Design Only

The current onboarding surface is read-only:

- TASK-081 defines onboarding data fields.
- TASK-082 projects read-only onboarding state.
- TASK-083 aggregates readiness.
- TASK-084 exposes read-only admin onboarding state.
- TASK-085 integrates operator demo home with that read-only state.
- TASK-086 defines a future draft/save boundary.

TASK-087 does not change that behavior. It describes what future draft/save and review tasks must audit and what event evidence they may produce after a separate implementation task approves persistence, schema, permissions, idempotency, and redaction.

## Mutation Areas Requiring Future Evidence

Future onboarding mutation tasks must capture audit and event evidence for these draft/review operations:

| Operation area | Example operation | Evidence requirement |
| --- | --- | --- |
| Organisation/company draft save | Create or update company draft intent. | Actor, external tenant reference, organisation reference, before/after safe summary, validation result. |
| Producer/sponsor draft save | Create or update producer/sponsor setup intent. | Actor, producer/sponsor references, funding-intent redaction, no money guardrail. |
| Distributor draft save | Create or update distributor setup intent. | Actor, distributor reference, distribution model intent, no activation guardrail. |
| Member/role draft save | Create or update member/role setup intent. | Actor, role intent, permission scope, invite-delivery disabled guardrail. |
| Campaign/opportunity draft save | Create or update campaign/opportunity setup intent. | Actor, campaign/opportunity reference, readiness blockers, no publication guardrail. |
| Webhook/API draft save | Create or update integration setup intent. | Actor, integration intent, credential redaction, no secret/webhook delivery guardrail. |
| Readiness validation | Evaluate draft sections for review. | Validation/readiness result, missing evidence, blockers, correlation ID. |
| Submit for review | Move a draft to review-only readiness. | Actor, permission scope, idempotency key, before/after state, no go-live guardrail. |
| Discard draft | Mark a draft inactive or discarded. | Actor, reason, prior state hash, discarded state hash, correlation ID. |

## Explicitly Excluded Live Actions

Audit and event design for onboarding draft/save must stay separate from live platform actions.

TASK-087 does not authorize:

- tenant, account, or organisation creation;
- producer, sponsor, distributor, partner, member, user, seat, role, or identity-provider creation;
- user invite delivery;
- campaign or opportunity publication;
- credential, API key, token, certificate, signing material, or secret generation;
- webhook subscription activation, signing, queueing, dispatch, retry, replay, or delivery;
- go-live activation;
- funding, wallet, fulfilment, settlement, retry, payout, reversal, reconciliation, or money movement.

Any request attempting those actions from a future onboarding draft/save surface must be rejected as unsafe unless a later reviewed task explicitly implements that live command with its own audit, permission, idempotency, and test contract.

## Required Audit Evidence

Future onboarding mutation tasks must capture bounded audit evidence. Values must be safe summaries or references, not unrestricted raw payloads.

| Evidence | Requirement |
| --- | --- |
| Actor reference | Required. Use actor ID only when safe for the internal surface, otherwise use a safe actor reference. |
| Actor role | Required for permission and support review. |
| Permission scope | Required. Include route/helper family, role family, and external scope. |
| External tenant reference | Preserve `external_tenant_ref` when supplied. |
| Organisation reference | Preserve `organisation_ref` when supplied. |
| Role-specific references | Preserve `producer_ref`, `sponsor_ref`, and `distributor_ref` where relevant. |
| Campaign/opportunity references | Preserve `campaign_code` and `opportunity_ref` where relevant. |
| Resolved tenant context | Internal-only. Include resolved `tenant_code` only where resolution exists and the audit store is internal/operator scoped. |
| Draft reference | Required after a draft exists. |
| Operation type | Required. Use explicit action names such as `ONBOARDING_DRAFT_CREATE`, `ONBOARDING_DRAFT_UPDATE`, `ONBOARDING_DRAFT_VALIDATE`, `ONBOARDING_DRAFT_SUBMIT_FOR_REVIEW`, and `ONBOARDING_DRAFT_DISCARD`. |
| Action status | Required. Distinguish success, validation failed, blocked, duplicate/no-op, stale, conflict, unsafe, denied, and discarded. |
| Idempotency key reference | Required for create, update, validate, submit-for-review, and discard when duplicate-sensitive. Store a reference/hash, not a raw secret-like value. |
| Correlation ID | Required for request, support trace, and event linkage. |
| Request source | Required. Examples: operator UI, admin API, integration client, system job. |
| Before state | Required as a hash, version, or safe summary when prior draft state exists. |
| After state | Required as a hash, version, or safe summary for accepted state changes. |
| Changed sections | Required. Identify sections changed without exposing sensitive field values. |
| Validation result | Required for validation or save operations with validation failures. |
| Readiness result | Required for submit-for-review and readiness evaluation. |
| Blocked reason | Required for blocked, rejected, unsafe, stale, or readiness-blocked outcomes. |
| Timestamp | Required in UTC. |
| Redaction classification | Required when input, output, or audit evidence redacts unsafe fields. |

Audit evidence must not store secrets, API keys, tokens, passwords, certificates, signing material, raw credential payloads, raw UCNs, raw provider payloads, raw webhook delivery internals, raw funding/wallet/settlement/fulfilment/retry internals, unrestricted before/after payloads, SQL errors, stack traces, or environment secret names.

## Required Event Evidence

Future onboarding events must use safe, contract-level evidence. Event emission or persistence requires a later implementation task.

| Evidence | Requirement |
| --- | --- |
| Event name | Required. Use catalog-style stable names. |
| Event version | Required. Version payload shape separately from route implementation. |
| Event category | Required. Suggested category: `onboarding`. |
| Aggregate reference | Required. Use a draft reference or safe onboarding aggregate reference. |
| External references | Include supplied external references such as `external_tenant_ref`, `organisation_ref`, `producer_ref`, `sponsor_ref`, `distributor_ref`, `campaign_code`, and `opportunity_ref`. |
| Safe actor reference | Required for actor-initiated events. |
| Correlation ID | Required for support trace and audit/event linking. |
| Idempotency key reference | Required for duplicate-sensitive commands. |
| Evidence status | Required. Examples: `accepted`, `validation_failed`, `blocked`, `duplicate`, `discarded`. |
| Redaction classification | Required when unsafe inputs or evidence were redacted. |

Events must use external references for user-facing scope. Internal `tenant_code` may be used by internal event processors only after resolution and must not become the primary external event identifier.

## Suggested Onboarding Event Catalog Entries

These entries are contract suggestions only. They are not emitted, persisted, delivered, or subscribed by TASK-087.

| Event name | Category | Trigger meaning | Subject |
| --- | --- | --- | --- |
| `onboarding.draft.created` | Onboarding | A draft intent was accepted for future persistence. | onboarding draft |
| `onboarding.draft.updated` | Onboarding | A draft intent was updated safely. | onboarding draft |
| `onboarding.draft.validation_failed` | Onboarding | Draft validation failed with safe details. | onboarding draft |
| `onboarding.draft.ready_for_review` | Onboarding | A draft reached review-only readiness. | onboarding draft |
| `onboarding.draft.blocked` | Onboarding | A blocker prevents readiness or review. | onboarding draft |
| `onboarding.draft.discarded` | Onboarding | A draft was discarded or made inactive. | onboarding draft |
| `onboarding.readiness.evaluated` | Onboarding | Readiness was evaluated without live activation. | onboarding readiness |

The existing webhook catalog uses uppercase snake case for outbound partner webhook `event_type` values. These onboarding event names are internal event-design names until a later task decides whether they need outbound webhook equivalents. If exposed externally, they must be mapped into the approved webhook catalog naming convention first.

## Event Payload Guardrails

Future onboarding event payloads must not contain:

- secrets;
- API keys;
- tokens;
- passwords;
- certificates;
- signing material;
- webhook signing or delivery internals;
- webhook retry, DLQ, or provider internals;
- raw UCNs or private identifiers;
- raw provider payloads;
- raw audit payloads;
- raw before/after sensitive payloads;
- funding, wallet, settlement, fulfilment, retry, payout, reversal, or money movement internals;
- SQL errors, stack traces, database DSNs, or environment secret names.

Payloads should include safe references, safe summaries, hashes, redaction categories, and missing-evidence codes instead of raw values.

## Before And After State Expectations

Future audit/event capture must identify what changed without leaking sensitive values.

Minimum expectations:

1. Use a stable draft version, ETag, or hash for before and after state.
2. Include a bounded section summary such as `company`, `producer_sponsor`, `distributor`, `member_role`, `campaign_opportunity`, or `webhook_api`.
3. Include changed field names only when the field names are safe.
4. Redact unsafe field names and values using categories such as `secret_or_credential`, `private_identifier`, `internal_identifier`, `provider_internal`, `audit_internal`, `webhook_internal`, and `money_movement_internal`.
5. Do not store raw before/after payloads in external-facing event data.
6. Do not store sensitive raw values in audit evidence unless a later internal-only audit schema explicitly supports encrypted restricted storage and tests redaction behavior.

## Idempotency And Duplicate Handling

Future onboarding mutations must follow the TASK-086 idempotency model.

| Scenario | Audit/event requirement |
| --- | --- |
| Same idempotency key and same payload | Return the prior result. Audit/event evidence may record duplicate/no-op metadata, but must not imply a second state change. |
| Same idempotency key and different payload | Reject with `IDEMPOTENCY_CONFLICT`. Capture safe conflict evidence without storing raw payloads. |
| Duplicate active draft for same external scope | Return existing draft or reject with `DUPLICATE_DRAFT`, according to the future route contract. Do not create duplicate draft events. |
| Retry after transient client failure | Preserve the same correlation/idempotency linkage and avoid duplicate state transitions. |
| Stale draft update | Reject with `STALE_DRAFT`. Include safe before-version and supplied-version evidence where safe. |
| Unsafe operation attempted | Reject with `UNSAFE_OPERATION_ATTEMPTED`. Capture the attempted operation category, not raw unsafe content. |

Duplicate event prevention must be based on the idempotency key reference, aggregate reference, event name, and resulting draft version or safe state hash.

## Correlation And Tracing

Future onboarding audit and event capture must support support-trace reconstruction.

Minimum correlation model:

- Request correlation ID: inbound request trace reference.
- Audit correlation ID: audit row or audit event linkage.
- Event correlation ID: event evidence linkage.
- Draft reference: future onboarding draft aggregate reference.
- Idempotency key reference: duplicate-safe command reference.
- External references: user-facing onboarding scope.
- Resolved internal tenant context: internal-only, where authorized and available.

Correlation IDs must be safe to show in operator/support surfaces. They must not include secrets, tokens, raw payload fragments, UCNs, database IDs intended to remain private, or environment details.

## Permission And Tenant Boundary Expectations

Future onboarding mutation tasks must use the narrowest role and scope available.

| Actor family | Expected boundary |
| --- | --- |
| Platform operator | May operate across explicit external scopes when authorized and audited. |
| System admin | May support or inspect onboarding evidence where route purpose is system/support; business mutation should remain narrow. |
| Distribution admin | May manage distributor, route, campaign, and distribution onboarding draft sections where authorized. |
| Producer/sponsor/company admin | May manage own organisation, producer/sponsor, campaign-intent, and integration-intent drafts after membership scope exists. |
| Distributor/partner admin | May manage own distributor/partner setup draft sections after scope exists. |
| Support/read-only viewer | May read safe onboarding state only; cannot save, discard, validate, or submit if those operations mutate audit or draft state. |
| Public/anonymous | No onboarding mutation access. |
| Worker | No onboarding mutation access. |

`tenant_code` remains internal. External references such as `external_tenant_ref`, `organisation_ref`, `producer_ref`, `sponsor_ref`, `distributor_ref`, `campaign_code`, and `opportunity_ref` are the user-facing boundary. Future implementation must resolve external references into internal tenant scope only after permission checks and must audit both the external reference and resolved internal context where authorized.

## Safe Error And Rejection Capture

Future onboarding mutation tasks must capture safe rejection evidence for:

- permission denied;
- validation failed;
- duplicate draft;
- idempotency conflict;
- stale draft;
- unknown reference;
- readiness blocked;
- unsafe operation attempted;
- live DB verification blocked;
- drift verification blocked.

Client-facing errors must use bounded codes and safe messages. Audit/event evidence may include internal categorization, but must not leak raw payloads, secrets, SQL, stack traces, provider internals, webhook delivery internals, money internals, or private identifiers.

## Retry, Replay, And Repair Boundaries

TASK-087 does not implement retry, replay, repair, DLQ, webhook retry, or event re-emission.

Future onboarding mutation tasks must distinguish:

- client request replay using an idempotency key;
- duplicate/no-op handling;
- manual repair of bad draft state;
- event replay or event store repair;
- webhook delivery retry.

Only the first two are part of the safe draft/save boundary. Manual repair, event replay, webhook retry, DLQ, and repair workflows require separate reviewed tasks with explicit audit actor, reason, before/after state, permission, idempotency, and redaction tests.

## Safety Gates Before Implementation

Before a future task implements onboarding audit/event capture, it must complete these gates:

1. Schema review for draft storage, audit evidence, event evidence, idempotency references, state hashes, and retention.
2. Audit table or event store review against current source truth.
3. Permission matrix update if any new route, helper, or role behavior is introduced.
4. Idempotency tests for create, update, validate, submit-for-review, discard, replay, and conflict.
5. Duplicate prevention tests for drafts, audit evidence, and events.
6. Stale version tests.
7. Audit tests for actor, actor role, permission scope, external references, resolved tenant context, idempotency key reference, correlation ID, before/after hash, action status, and blocked reason.
8. Event tests for event name, version, category, aggregate reference, correlation ID, idempotency reference, evidence status, and redaction classification.
9. Redaction tests for secrets, credentials, private identifiers, tenant internals, provider payloads, raw audit payloads, webhook internals, funding, wallet, fulfilment, settlement, retry, SQL, stack traces, and DSNs.
10. Permission tests for allowed role, rejected adjacent role, read-only viewer denial, public denial, worker denial, and cross-tenant denial.
11. Safe error tests for validation, duplicate, idempotency conflict, stale draft, unknown reference, permission denied, readiness blocked, and unsafe operation attempted.
12. No-secret tests.
13. No-money/no-go-live tests.
14. Rollback plan for schema, route, audit, and event behavior.
15. TASK-027/TASK-028 decision: either complete live DB verification/drift resolution or explicitly document why onboarding draft persistence can proceed without that evidence.

## Mapping To Existing Contracts

| Source | Mapping |
| --- | --- |
| TASK-081 onboarding data contract | Defines the safe section names and field vocabulary for draft/event summaries. |
| TASK-086 draft/save API boundary | Defines draft lifecycle, idempotency, duplicate handling, safe errors, and disabled live actions. |
| `AUDIT_RETRY_POLICY_STANDARD.md` | Defines platform audit, idempotency, retry, failure, and repair expectations. |
| `WEBHOOK_EVENT_CATALOG.md` | Defines webhook event naming, envelope, tenant/external reference, redaction, and non-delivery boundaries for future webhook-facing events. |
| `API_PERMISSION_MATRIX.md` | Defines current role families and new-route gates for permission, tenant scope, audit, and regression evidence. |
| `TENANT_IDENTIFIER_BOUNDARY_DECISION.md` | Confirms `tenant_code` is internal and external references are user-facing. |

## Readback Checklist

Before implementing future onboarding audit/event behavior, confirm:

- actor reference is captured safely;
- actor role is captured;
- permission scope is captured;
- `external_tenant_ref` is captured when supplied;
- `organisation_ref` is captured when supplied;
- `producer_ref`, `sponsor_ref`, and `distributor_ref` are captured where relevant;
- `campaign_code` and `opportunity_ref` are captured where relevant;
- resolved internal tenant context is internal-only;
- `tenant_code` is not a user-facing onboarding identifier;
- operation type and action status are explicit;
- before state is a hash, version, or safe summary;
- after state is a hash, version, or safe summary;
- changed sections are captured without exposing sensitive values;
- idempotency key reference is captured for duplicate-sensitive commands;
- correlation ID links request, audit, event, and draft evidence;
- validation and readiness results are captured;
- blocked and rejection reasons are safe;
- event name, version, category, aggregate reference, evidence status, and redaction classification are defined;
- event payloads contain no secrets, API keys, tokens, passwords, certificates, signing material, UCNs, provider internals, webhook delivery internals, raw audit payloads, raw before/after sensitive payloads, funding, wallet, settlement, fulfilment, retry, or money internals;
- retry, replay, repair, DLQ, and webhook retry are not implemented by this design;
- TASK-027 and TASK-028 remain blocked until separately resolved or explicitly deferred;
- no route, service, frontend code, schema, migration, persistence, database access, audit write, event persistence, webhook dispatch, credential lifecycle, go-live activation, funding, fulfilment, settlement, retry, repair, or money movement was introduced by TASK-087.
