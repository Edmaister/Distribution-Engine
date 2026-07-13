# Referral SaaS Validation And Recovery Contract

TASK ID: TASK-137

## Boundary

This contract belongs to the Referral Management and Campaign Attribution SaaS
product boundary. It hardens public referral validation and immediate recovery
flows without redefining referral code issuing, progress events, attribution
trace, reporting, or broader DLaaS money flows.

Required boundary docs checked:

- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_REFERRAL_CODE_ISSUE_CONTRACT.md`
- `docs/sa/LINK_CODE_CONTRACT.md`

Source files inspected:

- `services/referral_code.py`
- `apps/api/routers/referrals.py`
- `apps/api/schemas/referrals.py`
- `dp/migrations/001_init.sql`
- `dp/migrations/006_qr_scans.sql`
- `dp/migrations/013_progress_events.sql`
- `dp/migrations/015_add_ucn_captured_at.sql`
- `dp/migrations/016_fix_referral_instances_status_constraint.sql`
- `dp/migrations/031_tenent.sql`
- `test/test_referral_code.py`
- `test/test_referrals_api.py`

## Purpose

Referral SaaS needs a product-ready validation and recovery contract for the
public moment when a referred customer scans or enters a referral code.

This workflow answers three questions:

1. Is this referral code valid for the tenant context?
2. Can a privacy-safe referral journey be created with accepted terms evidence?
3. If validation or follow-up identity capture fails, what safe recovery path
   should the customer, partner, or operator see?

This task does not change runtime behavior. It documents the current source of
truth and the narrow hardening path needed before implementation work.

## Current Implementation Facts

Current public validation route:

- `POST /public/referrals/validate`
- implemented in `apps/api/routers/referrals.py`
- validates tenant with `require_valid_tenant(req.tenant_code)`
- calls `services.referral_code.validate_referral_code`
- accepts `tenantCode`, `referralCode`, `acceptedTerms`, `alias`,
  `deviceFingerprint`, `ipAddress`, and `qrCode`
- normalizes default response fields when the service omits them

Current product validation wrapper:

- `POST /v1/referral-saas/public/referrals/validate`
- implemented by TASK-174 in `apps/api/routers/referral_saas_links.py`
- composes `validate_referral_code` without forking validation logic
- uses the TASK-175 mapper in `services/referral_saas_validation_service.py`
  for product status, recovery action, and safe response shape
- returns product-shaped `validationStatus`, `valid`, `referralTrackId`,
  `alias`, `errorCode`, `message`, `recovery`, and `idempotency`
- maps `REFERRAL_LOG_FAILED` to `RECOVERY_REQUIRED_LOGGING` with a safe
  retry/contact-support recovery action
- redacts raw UCN, UCN hash, and internal `attributes` evidence from the
  response
- TASK-176 exposes that successful duplicate submits are not idempotent today
  and that idempotency keys are not supported until schema-backed duplicate
  reuse or conflict behavior is implemented
- TASK-177 renders the safe recovery next action and non-idempotent retry
  posture in the focused link/code workflow UI
- does not implement duplicate-submit idempotency, operator trace linkage,
  schema changes, repair/replay, audit writes, rewards, funding, fulfilment,
  settlement, wallet, or DLaaS expansion behavior

Current validation service:

- `services/referral_code.py::validate_referral_code`
- requires `tenant_code`
- requires `referral_code`
- requires `accepted_terms is True`
- normalizes or auto-generates a referee alias
- validates alias length, format, and blocked terms
- looks up `referrer_codes` by tenant and referral code
- creates a `referral_instances` row with status `VALIDATED`
- stores accepted terms evidence on the referral instance
- writes `referral_qr_scans` telemetry with status `VALIDATED`
- returns a `referral_track_id` as the golden thread

Current validation success response:

- HTTP `200`
- `valid=true`
- `validation_outcome=VALIDATED`
- `referral_track_id`
- alias
- attributes including tenant/referrer metadata

Current validation failures:

- `TENANT_CODE_REQUIRED`
- `REFERRAL_CODE_REQUIRED`
- `ACCEPTED_TERMS_REQUIRED`
- `ALIAS_REQUIRED`
- `ALIAS_TOO_SHORT`
- `ALIAS_TOO_LONG`
- `ALIAS_INVALID_FORMAT`
- `ALIAS_NOT_ALLOWED`
- `REFERRAL_CODE_NOT_FOUND`
- `REFERRAL_LOG_FAILED`

Current partial-success wrinkle:

- if code lookup succeeds but instance or scan logging fails, the service
  currently returns HTTP `200`, `valid=true`, `validation_outcome=FAILED`, and
  `error_code=REFERRAL_LOG_FAILED`
- this must be treated as a recovery state, not as a clean validation success

## Follow-On Referee UCN Capture

Current capture route:

- `POST /referrals/referees/ucn`
- protected by `require_partner_key`
- derives `tenant_code` from authenticated partner identity
- calls `services.referral_code.capture_referee_ucn`

Current product capture wrapper:

- `POST /v1/referral-saas/referrals/{referral_track_id}/referee-ucn`
- implemented by TASK-174 in `apps/api/routers/referral_saas_links.py`
- protected by `require_partner_key`
- composes `capture_referee_ucn` without forking identity-capture logic
- derives tenant scope from authenticated partner identity
- returns product-shaped `captureStatus`, `referralTrackId`, `errorCode`, and
  `message`
- maps progress-event handoff failure to
  `RECOVERY_REQUIRED_PROGRESS_EVENT`
- redacts raw referee UCN and hash evidence from the response

Current capture service:

- requires `referral_track_id`
- requires `referee_ucn`
- looks up the referral instance by `referral_track_id` and tenant
- joins `referrer_codes` and `tenants`
- rejects inactive tenants with `TENANT_INACTIVE`
- stores raw referee UCN and hashed referee UCN
- emits a `UCN_CAPTURED` progress event via `handle_progress_event`

Current capture failures:

- `REFEREE_UCN_REQUIRED`
- `REFERRAL_TRACK_NOT_FOUND`
- `TENANT_INACTIVE`
- `REFEREE_UCN_PROGRESS_EVENT_FAILED`

Capture is included in this contract only as validation recovery and identity
completion. Productized progress-event ingestion remains TASK-138.

## Schema Posture

Validation writes to `referral_instances`, which is the referral golden-thread
table.

Relevant `referral_instances` fields include:

- `referral_track_id`
- `referrer_code_id`
- `referral_code`
- `referrer_ucn`
- `referee_ucn`
- `referee_ucn_hash`
- `tenant_code`
- `status`
- `validated_at`
- `accepted_terms`
- `accepted_terms_at`
- `referee_alias`
- `referee_alias_normalized`
- journey and progress columns used by later flows

Current referral instance statuses include:

- `VALIDATED`
- `UCN_CAPTURED`
- `ACCOUNT_OPENED`
- `ACCOUNT_ACTIVATED`
- `FUNDED`
- `COMPLETED`
- `CANCELLED`

Validation also writes `referral_qr_scans` evidence with:

- `referral_code`
- `qr_code`
- `referral_track_id`
- `device_fingerprint`
- `ip_address`
- `status`

The product contract must preserve `referral_track_id` as the downstream
golden thread for progress, rewards, attribution, reporting, and operator
support.

## Product Validation States

Referral SaaS should expose product states that map cleanly to the current
service response while hiding internal details.

Recommended product states:

- `VALIDATED`
- `REJECTED_MISSING_TENANT`
- `REJECTED_MISSING_CODE`
- `REJECTED_TERMS_REQUIRED`
- `REJECTED_ALIAS`
- `REJECTED_CODE_NOT_FOUND`
- `RECOVERY_REQUIRED_LOGGING`
- `RECOVERY_REQUIRED_IDENTITY_CAPTURE`
- `FAILED`

Current `REFERRAL_LOG_FAILED` should map to
`RECOVERY_REQUIRED_LOGGING` because the code lookup succeeded but durable
journey evidence is incomplete or uncertain.

## Target Contract Direction

Candidate public validation route:

```text
POST /referral-saas/public/referrals/validate
```

The current route remains in place. TASK-174 introduces the first bounded
versioned product wrapper and composes the existing validation service rather
than duplicating validation logic.

Minimum product request:

```json
{
  "accountRef": "safe-account-or-tenant-reference",
  "referralCode": "ABC123DEF0",
  "acceptedTerms": true,
  "alias": "customer-alias",
  "scanEvidence": {
    "deviceFingerprint": "optional",
    "ipAddress": "optional",
    "qrCode": "optional"
  }
}
```

Minimum product response:

```json
{
  "validationStatus": "VALIDATED",
  "valid": true,
  "referralTrackId": "uuid",
  "alias": "customer-alias",
  "errorCode": null,
  "recovery": null,
  "idempotency": {
    "validationAttemptPolicy": "NEW_JOURNEY_PER_SUCCESSFUL_VALIDATION",
    "duplicateSubmitGuarantee": "NOT_IDEMPOTENT",
    "idempotencyKeySupported": false
  }
}
```

Recovery response example:

```json
{
  "validationStatus": "RECOVERY_REQUIRED_LOGGING",
  "valid": false,
  "referralTrackId": null,
  "alias": null,
  "errorCode": "REFERRAL_LOG_FAILED",
  "recovery": {
    "action": "RETRY_VALIDATION_OR_CONTACT_SUPPORT",
    "safeMessage": "We could not finish setting up this referral. Try again or contact support."
  }
}
```

## Idempotency And Duplicate Submission

Current validation appears to create a new `referral_instances` row for each
successful validation request. No explicit validation idempotency key is present
in the inspected route or service.

TASK-176 makes that current posture explicit in the product wrapper response:

- `validationAttemptPolicy=NEW_JOURNEY_PER_SUCCESSFUL_VALIDATION`
- `duplicateSubmitGuarantee=NOT_IDEMPOTENT`
- `idempotencyKeySupported=false`

Before implementation changes, Referral SaaS must decide whether duplicate
public submissions should:

- create separate referral journeys, or
- reuse an existing journey for the same code, tenant, alias/device/session, and
  accepted-terms event.

Until that decision is implemented in schema/service/tests, product docs should
not promise duplicate-submit idempotency.

Future implementation options:

- client-provided idempotency key
- server-derived validation dedupe key from tenant, code, device/session, and
  short time window
- explicit duplicate state such as `DUPLICATE_VALIDATION_REUSED`

## Privacy And Redaction

Validation responses must not expose:

- raw referrer UCN
- raw referee UCN
- UCN hashes
- internal fraud/risk signals
- stack traces or DB failure details

Safe validation responses may expose:

- referral track ID
- alias
- high-level validation state
- safe error code
- safe next action

Current response `attributes` can include internal identifiers such as
`tenant_code` and `referrer_code_id`. A future product wrapper should redact or
replace those with safe support references before exposing them to public
customer UX.

## Recovery Contract

Recovery states should be explicit and operator-friendly.

Customer-safe recovery actions:

- `RETRY_VALIDATION`
- `RETRY_WITH_VALID_ALIAS`
- `ACCEPT_TERMS_AND_RETRY`
- `CHECK_CODE_AND_RETRY`
- `CONTACT_SUPPORT`

Partner/operator recovery actions:

- inspect referral code source
- inspect validation attempt evidence
- inspect QR scan evidence
- retry or reconcile missing scan/instance evidence where safe
- capture referee UCN only through authenticated partner route
- never ask the customer to expose raw internal identifiers

Recovery must preserve tenant boundaries and must not let one tenant inspect or
complete another tenant's referral track.

## Audit And Evidence

Validation creates or should create evidence for:

- tenant/account context
- referral code
- validation outcome
- accepted terms flag and timestamp
- alias source
- QR/scan telemetry when present
- referral track ID when created
- error/recovery state when validation is incomplete

Referee UCN capture should evidence:

- authenticated partner credential/actor
- tenant context
- referral track ID
- UCN capture timestamp
- progress-event handoff result

Raw identity values must be stored and exposed only according to the existing
privacy/security posture. Product APIs and operator UX should prefer safe
references and redacted evidence.

## Future Tests

Implementation work following this contract should add or preserve tests for:

- successful validation creates `referral_instances` and QR scan evidence
- accepted terms are required
- missing tenant and missing code return stable safe errors
- invalid aliases return stable safe errors
- code-not-found response does not leak other-tenant information
- response does not expose raw UCN or hashes
- `REFERRAL_LOG_FAILED` maps to a recovery state
- duplicate validation behavior is explicitly tested after the idempotency
  decision is made
- referee UCN capture is partner-authenticated
- capture derives tenant from identity and cannot be body-overridden
- inactive tenants cannot capture UCN
- capture progress-event failure is visible as recoverable operational failure

## Implementation Slices

Recommended sequence:

1. TASK-174 added the product validation wrapper.
2. TASK-175 added centralized product validation response mapping, redaction
   shape, and recovery contract tests.
3. TASK-176 exposed the current non-idempotent validation posture in the
   product response.
4. Decide and implement schema-backed duplicate validation/idempotency behavior.
5. TASK-177 added frontend recovery and retry-posture visibility to the
   focused link/code workflow.
6. Decide and implement schema-backed duplicate validation/idempotency behavior.
7. Add operator evidence linkage to link/code inspection under TASK-140.
8. Defer progress-event catalog hardening to TASK-138.
9. Defer attribution trace composition to TASK-139.

## Explicit Non-Goals

This task does not implement:

- schema migrations
- new routes
- service behavior changes
- frontend changes
- referral code issue/reissue/revoke/expire behavior
- progress event productization
- campaign attribution trace
- operator link/code investigation workflow
- reporting/export
- rewards, funding, fulfilment, settlement, or sponsor billing
- live DB verification

## Readiness Decision

Referral SaaS already has meaningful public validation and identity-capture
capability. The route to 10/10 is not rebuilding validation; it is stabilizing
the product-facing contract, redacting internal evidence, making recovery
states explicit, deciding duplicate-submit idempotency, and adding tests around
those promises.
