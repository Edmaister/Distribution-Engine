# Onboarding Dry-Run Validation Endpoint Contract

Status: Accepted for TASK-099 on 2026-06-30.

## Purpose And Scope

This document defines the future API contract for dry-run onboarding validation. The dry-run validates onboarding intent and returns safe readiness feedback without persisting drafts, creating records, writing audit rows, emitting events, delivering webhooks, generating credentials, activating go-live, or moving money.

This is contract-only. It does not add backend routes, frontend code, services, tests, schema, migrations, database access, draft persistence, audit writes, event persistence, credential lifecycle, webhook delivery, funding, wallet, fulfilment, settlement, retry, go-live activation, or money movement.

## Source Documents

- `docs/sa/ONBOARDING_DATA_CONTRACT.md`
- `docs/sa/ONBOARDING_DRAFT_SAVE_API_BOUNDARY.md`
- `docs/sa/ONBOARDING_AUDIT_EVENT_CAPTURE_DESIGN.md`
- `docs/sa/ONBOARDING_DRAFT_PERSISTENCE_SCHEMA_DESIGN.md`
- `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md`
- `docs/API_PERMISSION_MATRIX.md`
- `docs/roadmap/ONBOARDING_READ_MODEL_WAVE_CHECKPOINT_TASK_090.md`

## Dry-Run Semantics

A dry-run validation endpoint may later evaluate:

1. An unsaved onboarding payload supplied in the request.
2. A future saved onboarding draft referenced by `draft_ref`.
3. A mixed request where caller-supplied fields temporarily override a saved draft for preview only.

In all cases the dry-run must be no-op:

- no draft write;
- no section write;
- no validation-result persistence;
- no idempotency persistence in the initial dry-run version;
- no audit row;
- no event persistence;
- no webhook dispatch;
- no credential lifecycle;
- no account, user, invite, campaign, distributor, funding, wallet, fulfilment, settlement, retry, go-live, or money movement side effect.

Dry-run output is advisory. `READY_FOR_REVIEW` or `READY` in dry-run output is not approval, publication, activation, fulfilment, settlement, or go-live.

## Endpoint Sketches

These endpoint shapes are contract sketches only and are not implemented by TASK-099.

### `POST /admin/onboarding/validate`

Validates an unsaved onboarding payload using external references and supplied section data.

Intended use:

- onboarding shell preview;
- operator review before saving a future draft;
- safe readiness preview before any persistence exists.

### `POST /admin/onboarding/drafts/{draft_ref}/validate`

Validates a future saved draft by reference.

Intended use:

- preview current saved draft readiness;
- preview proposed changes without committing them;
- prepare for future submit-for-review workflows.

Both endpoints must use authenticated actor context from the auth/session layer. Actor identity, role, and tenant permissions must not be trusted from the request body.

## Request Shape

Recommended request envelope:

```json
{
  "contract_version": "onboarding.v1",
  "scope": {
    "external_tenant_ref": "acme-distribution",
    "organisation_ref": "org-acme",
    "producer_ref": "producer-acme",
    "sponsor_ref": "sponsor-acme",
    "distributor_ref": "dist-north",
    "campaign_code": "ACME-LAUNCH",
    "opportunity_ref": "opp-acme-launch"
  },
  "draft_ref": "draft_123",
  "validation_scope": [
    "company",
    "producer_sponsor",
    "distributor",
    "member_role",
    "campaign_opportunity",
    "webhook_api",
    "readiness"
  ],
  "sections": {
    "company": {},
    "producer_sponsor": {},
    "distributor": {},
    "member_role": {},
    "campaign_opportunity": {},
    "webhook_api": {}
  },
  "idempotency_key": "client-generated-key",
  "correlation_id": "corr_123"
}
```

Required fields:

- `contract_version`
- `scope.external_tenant_ref` or another approved external reference sufficient for the future route purpose
- `validation_scope`
- `correlation_id` where caller can provide one

Optional fields:

- `organisation_ref`
- `producer_ref`
- `sponsor_ref`
- `distributor_ref`
- `campaign_code`
- `opportunity_ref`
- `draft_ref`
- `sections`
- `idempotency_key`

Actor context:

- actor reference comes from authentication;
- actor role comes from authentication;
- permission scope comes from route dependencies and membership/role checks;
- request body actor fields must be ignored or rejected.

`tenant_code` must not be accepted as a user-facing scope field. If a future implementation needs resolved tenant context, it must derive it internally after permission and external-reference checks.

## Response Shape

Recommended response envelope:

```json
{
  "status": "ok",
  "validation_result": {
    "status": "BLOCKED",
    "contract_version": "onboarding.v1",
    "validated_scope": {
      "external_tenant_ref": "acme-distribution",
      "organisation_ref": "org-acme",
      "resolved_tenant": {
        "status": "UNAVAILABLE"
      }
    },
    "validated_sections": [
      "company",
      "campaign_opportunity"
    ],
    "checks": []
  },
  "readiness_preview": {
    "overall_status": "GO_LIVE_DISABLED",
    "categories": [],
    "summary": {
      "ready_count": 0,
      "in_progress_count": 0,
      "blocked_count": 0,
      "missing_evidence_count": 0,
      "permission_limited_count": 0,
      "go_live_disabled_count": 1,
      "total_count": 1
    }
  },
  "missing_evidence": [],
  "blockers": [],
  "warnings": [],
  "safe_errors": [],
  "next_actions": [],
  "guardrails": [
    "DRY_RUN_ONLY",
    "NO_PERSISTENCE",
    "NO_LIVE_MUTATION",
    "TENANT_CODE_INTERNAL",
    "NO_MONEY_MOVEMENT"
  ],
  "redactions": [],
  "no_persistence_confirmed": true
}
```

Response rules:

- `status` should be `ok` when validation completed, even if readiness is blocked.
- Validation failures should appear in `validation_result`, `safe_errors`, `missing_evidence`, or `blockers` unless the request itself is malformed or unauthorized.
- `no_persistence_confirmed` must be `true` for the dry-run contract.
- `readiness_preview` must not imply live activation.
- Responses must not expose `tenant_code` as a user-facing identifier.

## Validation Categories

The dry-run contract supports these categories:

| Category | Purpose |
| --- | --- |
| Field validation | Required fields, enum values, bounded string lengths, URL/email format where appropriate, and unsafe key rejection. |
| Cross-section validation | Consistency across organisation, producer/sponsor, distributor, campaign/opportunity, and webhook/API intent. |
| Permission validation | Actor role, route helper, membership, and scope checks. |
| Readiness validation | Review-only readiness preview using TASK-083 category language. |
| External-reference resolution | Safe check of external references where resolver exists; missing resolver becomes missing evidence. |
| Redaction validation | Detects and redacts or rejects secrets, private identifiers, internal identifiers, and unsafe internals. |
| No-live-action validation | Rejects attempts to create, publish, invite, generate, deliver, activate, fund, fulfil, settle, retry, or move money. |

## Safe Error Model

Dry-run validation should return bounded errors. Recommended error item shape:

```json
{
  "code": "VALIDATION_FAILED",
  "message": "Campaign code is required before readiness review.",
  "section": "campaign_opportunity",
  "field": "campaign_code",
  "severity": "BLOCKER"
}
```

Recommended safe error codes:

| Code | Meaning | HTTP direction |
| --- | --- | --- |
| `VALIDATION_FAILED` | Field or cross-section validation failed. | 200 with validation result, or 422 for malformed payload. |
| `UNKNOWN_REFERENCE` | External reference cannot be resolved or is inaccessible. | 200 with blocker, 404, or 422 depending on route purpose. |
| `PERMISSION_DENIED` | Actor lacks required role, membership, or scope. | 403. |
| `MISSING_EVIDENCE` | Required evidence is unavailable. | 200 with missing evidence. |
| `READINESS_BLOCKED` | Readiness cannot progress due to blockers. | 200 with blockers. |
| `UNSAFE_OPERATION` | Request attempted a live action or unsafe field. | 400 or 422. |
| `IDEMPOTENCY_CONFLICT` | Same idempotency key reused with different payload where future tracking exists. | 409. |
| `CONTRACT_VERSION_UNSUPPORTED` | Contract version is unsupported. | 400 or 422. |

Errors must not expose stack traces, SQL, table names, environment variable names, secrets, raw provider payloads, raw audit payloads, private identifiers, webhook delivery internals, funding/wallet/settlement/fulfilment/retry internals, or money details.

## Permission Boundaries

Dry-run validation is safer than draft save, but it still validates sensitive onboarding setup intent. It must be authenticated and scoped.

| Actor family | Dry-run direction |
| --- | --- |
| Platform operator | May dry-run across explicit external scopes where authorized. |
| System admin | May support or inspect dry-run validation where route purpose is support/system; business mutation remains out of scope. |
| Distribution admin | May dry-run distributor, route, campaign/opportunity, and distribution onboarding sections where authorized. |
| Finance admin | Not allowed by default except future finance-intent review sections explicitly scoped as read-only/no-money. |
| Producer/sponsor/company admin | May dry-run own organisation, producer/sponsor, campaign-intent, and integration-intent sections after membership scope exists. |
| Distributor/partner admin | May dry-run own distributor/partner setup sections after scope exists. |
| Support/read-only viewer | May read safe validation output only if route is explicitly read-only and no audit/write side effect occurs. |
| Public/anonymous | No dry-run access. |
| Worker | No dry-run access. |

Future implementation must add permission tests for allowed roles, adjacent-role rejection, unauthenticated rejection, cross-scope rejection, and safe error behavior.

## Idempotency Expectations

In the initial dry-run contract:

- `idempotency_key` may be accepted for client traceability.
- No idempotency row is persisted.
- No audit row is written.
- No event is persisted.
- Same payload should return an equivalent validation result.
- Different payload with the same key cannot be conflict-detected unless a later persistence layer tracks dry-run requests.

If a future implementation persists dry-run request evidence, it must follow TASK-098 idempotency storage rules:

- store hashed idempotency keys only;
- scope keys by actor, external references, route, and draft reference;
- store payload hash, not raw sensitive values;
- return equivalent result for same key/same payload;
- return `IDEMPOTENCY_CONFLICT` for same key/different payload;
- avoid implying a state mutation for repeated dry-run calls.

## External Reference Scope

Dry-run validation uses external references as the request boundary:

- `external_tenant_ref`
- `organisation_ref`
- `producer_ref`
- `sponsor_ref`
- `distributor_ref`
- `campaign_code`
- `opportunity_ref`

Rules:

1. External references are safe user-facing inputs.
2. `tenant_code` is internal-only.
3. Caller-supplied `tenant_code` must be ignored or rejected.
4. Ambiguous, inaccessible, disabled, archived, or unresolved external references produce safe blockers or errors.
5. Resolved internal tenant context may be used internally only after auth and permission checks.
6. External-facing or partner/distributor/producer/customer responses must not expose internal tenant identifiers.

## Redaction And Non-Exposure

Dry-run validation must reject or redact:

- secrets;
- API keys;
- client secrets;
- signing material;
- access tokens;
- refresh tokens;
- passwords;
- certificates;
- webhook signing or delivery internals;
- raw UCNs or private identifiers;
- raw provider internals;
- raw audit payloads;
- internal tenant identifiers as user-facing scope;
- funding, wallet, settlement, fulfilment, retry, reconciliation, payout, reversal, or money movement internals;
- SQL errors;
- stack traces;
- environment secret names;
- database DSNs.

Redaction should be reported through safe categories such as:

- `TENANT_CODE_INTERNAL`
- `SECRET_OR_CREDENTIAL_REDACTED`
- `PRIVATE_IDENTIFIER_REDACTED`
- `PROVIDER_INTERNAL_REDACTED`
- `AUDIT_INTERNAL_REDACTED`
- `WEBHOOK_INTERNAL_REDACTED`
- `MONEY_MOVEMENT_INTERNAL_REDACTED`

## No-Persistence Guarantee

The dry-run version covered by this contract guarantees:

- no draft creation;
- no draft update;
- no section write;
- no validation-result write;
- no idempotency write;
- no audit write;
- no event persistence;
- no webhook dispatch;
- no credential generation, storage, reveal, or rotation;
- no account, tenant, organisation, producer, sponsor, distributor, member, user, role, or invite creation;
- no campaign/opportunity creation, publication, launch, pause, close, or activation;
- no funding, wallet, reservation, invoice, fulfilment, settlement, retry, reversal, payout, repair, reconciliation, or money movement;
- no go-live activation.

Future implementation tests must prove this by asserting that write services/tables/commands are not invoked.

## Relationship To Future Draft Persistence

Dry-run validation can exist before draft persistence.

Before persistence:

- validate request payload directly;
- return missing evidence for unavailable saved-draft sources;
- return `no_persistence_confirmed: true`;
- do not track idempotency conflicts beyond in-request deterministic behavior.

After persistence:

- may validate an existing `draft_ref`;
- may preview supplied overrides without committing them;
- may use persisted draft sections as evidence;
- must still preserve a no-op mode;
- must explicitly distinguish dry-run validation from save, submit-for-review, discard, and go-live commands.

Any transition from no-persistence dry-run to persisted validation evidence requires a separate implementation task, schema review, idempotency tests, audit/event decision, and rollback plan.

## Relationship To TASK-082 And TASK-083

TASK-082 onboarding state projection provides the safe section and missing-evidence shape that dry-run validation should reuse.

TASK-083 readiness aggregation provides the readiness categories, blockers, next actions, summary counts, and go-live-disabled posture that dry-run validation should return as `readiness_preview`.

Dry-run validation should not invent a separate readiness vocabulary unless a later task updates the canonical contract.

## Relationship To TASK-086, TASK-087, And TASK-098

| Source | Relationship |
| --- | --- |
| TASK-086 draft/save API boundary | Defines future draft commands, safe errors, idempotency, disabled live actions, and permission expectations. Dry-run validation is a no-op subset. |
| TASK-087 audit/event capture design | Defines future evidence for mutations. Dry-run validation does not write audit/events unless a later task explicitly changes the contract. |
| TASK-098 draft persistence schema design | Defines future tables and validation result storage. Dry-run validation can run before those tables exist and must not require them initially. |

## Safety Gates Before Implementation

Before implementing a dry-run route, the task must add:

1. Route permission tests.
2. Unauthenticated and adjacent-role rejection tests.
3. Cross-scope and external-reference tests.
4. No-mutation tests.
5. No-audit-write tests for the initial dry-run version.
6. No-event-persistence tests for the initial dry-run version.
7. Redaction tests.
8. Safe-error tests.
9. Missing-evidence tests.
10. Idempotency/replay tests appropriate to whether dry-run evidence is persisted.
11. Contract version tests.
12. No-secret tests.
13. No-money/no-go-live tests.
14. Tests proving credential lifecycle, webhook delivery, campaign publication, invite delivery, funding, wallet, fulfilment, settlement, retry, and money actions are not invoked.

## Explicit Non-Goals

This contract does not implement or authorize:

- backend routes;
- frontend code;
- services;
- tests;
- schema or migrations;
- draft persistence;
- audit writes;
- event persistence;
- account creation;
- tenant creation;
- organisation creation;
- user creation;
- membership creation;
- invite delivery;
- role assignment;
- campaign creation or publication;
- opportunity publication;
- credential generation, rotation, reveal, or storage;
- webhook subscription, signing, queueing, retry, replay, or delivery;
- go-live activation;
- funding, wallet, fulfilment, settlement, retry, reconciliation, payout, reversal, repair, or money movement.

## Readback Checklist

Before implementing any dry-run validation endpoint, confirm:

- dry-run remains no-op;
- route implementation is separated from this contract task;
- actor context comes from auth, not request body;
- external references define user-facing scope;
- `tenant_code` remains internal-only;
- request shape includes validation scope, correlation, and optional idempotency key;
- response shape includes validation result, readiness preview, missing evidence, blockers, warnings, safe errors, next actions, guardrails, redactions, and `no_persistence_confirmed`;
- safe errors are bounded;
- missing evidence is explicit;
- permissions are role- and scope-aware;
- redaction covers secrets, credentials, private identifiers, provider internals, audit internals, webhook internals, funding/wallet/settlement/fulfilment/retry internals, SQL, stack traces, environment names, and DSNs;
- idempotency expectations are clear for non-persisted and future persisted dry-run modes;
- no account creation, invite delivery, campaign publication, credential lifecycle, webhook delivery, funding, fulfilment, settlement, retry, wallet, go-live activation, audit mutation, event persistence, or money movement is introduced;
- TASK-027 and TASK-028 remain blocked unless separately completed or explicitly deferred.
