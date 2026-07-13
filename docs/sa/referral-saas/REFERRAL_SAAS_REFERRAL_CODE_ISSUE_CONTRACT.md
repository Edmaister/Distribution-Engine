# Referral SaaS Referral Code Issue Contract

TASK ID: TASK-136

## Boundary

This contract belongs to the Referral Management and Campaign Attribution SaaS
product boundary. It hardens the issue/get-or-create referral code workflow
without redefining broader DLaaS marketplace, funding, fulfilment, settlement,
or sponsor billing scope.

Required boundary docs checked:

- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_CAMPAIGN_SETUP_READINESS_CONTRACT.md`
- `docs/sa/LINK_CODE_CONTRACT.md`

Source files inspected:

- `services/referral_code.py`
- `apps/api/routers/referrals.py`
- `apps/api/schemas/referrals.py`
- `dp/migrations/001_init.sql`
- `dp/migrations/026_referrer_code_terms_and_conditions_update.sql`
- `dp/migrations/031_tenent.sql`
- `test/test_referral_code.py`
- `test/test_referrals_api.py`

## Purpose

Referral SaaS needs a product-ready contract for issuing or reusing referrer
codes before validation, progress, and attribution can be packaged as a clean
customer workflow.

The issue workflow answers one question:

Can this authenticated account context issue or retrieve a safe referral code
for this referrer, sticker/program context, segment, and accepted-terms state?

It must not:

- validate a referred customer referral
- create or mutate a referral instance
- capture referee UCN
- ingest progress events
- decide reward eligibility
- create attribution traces
- trigger funding, fulfilment, settlement, or commissions

## Current Implementation Facts

Current route:

- `POST /referrals/codes`
- implemented in `apps/api/routers/referrals.py`
- protected by `require_partner_key`
- derives `tenant_code` from authenticated partner identity
- ignores the request body `tenant` value for service routing

Current product wrapper:

- `POST /v1/referral-saas/referral-codes`
- implemented by TASK-174 in `apps/api/routers/referral_saas_links.py`
- protected by `require_partner_key`
- composes `get_or_create_referrer_code` without forking issue logic
- derives tenant scope from authenticated partner identity
- returns product-shaped `issueStatus`, `referralCode`, `publicHandle`,
  `created`, `sourceType`, `errorCode`, and `message`
- redacts raw UCN and UCN hash evidence from the response
- does not implement revoke, expire, reissue, schema changes, audit writes,
  explicit idempotency keys, rewards, funding, fulfilment, settlement, wallet,
  or DLaaS expansion behavior

Current request schema:

- `referrer_ucn`
- `sticker`
- `tenant`
- `segment`
- `preferred_handle`
- `acceptedTerms`

Current service:

- `services/referral_code.py::get_or_create_referrer_code`
- requires `referrer_ucn`, `tenant`, `sticker`, and `segment`
- requires `accepted_terms is True`
- hashes the referrer UCN before lookup
- returns an existing code when found
- creates a new `referrer_codes` record when not found
- records `accepted_terms` and `accepted_terms_at`
- allocates `referral_code` and `gaming_handle`
- accepts a valid and available preferred handle, otherwise generates one

Current response:

- `201` with `created=true` for a new code
- `200` with `created=false` for an existing code
- `400` with `MISSING_FIELDS` for missing required inputs
- `400` with `ACCEPTED_TERMS_REQUIRED` when terms were not accepted
- response fields include `referral_code`, `gaming_handle`, `created`,
  `message`, and `error_code`

Current tests cover:

- missing required inputs
- accepted terms enforcement
- new code creation
- existing code reuse
- preferred handle behavior at the service level
- route use of the service return status

## Schema Posture

The current `referrer_codes` table stores:

- raw `referrer_ucn`
- `referrer_ucn_hash`
- `referral_code`
- `gaming_handle`
- `sticker`
- `tenant_code`
- `segment`
- `accepted_terms`
- `accepted_terms_at`
- create/update timestamps

Current uniqueness constraints are global for:

- `referrer_ucn_hash`
- `referral_code`
- `gaming_handle`

Current service lookup is scoped by:

- `tenant_code`
- `sticker`
- `referrer_ucn_hash`

This is an important implementation wrinkle. Before changing issue behavior,
the product must decide whether the canonical rule is:

- one global referral code per referrer hash, or
- one referral code per tenant/sticker/referrer hash.

Until that decision is implemented in schema and tests, the product contract
must preserve current behavior and treat per-tenant/per-sticker multi-code
support as not yet proven.

## Product Concepts

Account context:

- Referral SaaS product account or tenant context resolved from authentication
- must not rely on a user-supplied internal `tenant_code`

Referrer identity:

- current implementation uses `referrer_ucn`
- future product API should prefer a safe product reference once membership and
  participant identity are available
- raw UCN must not appear in public responses

Issue context:

- `sticker` is the current program/link context
- `segment` is the current segment classification
- future campaign setup may map these values from product campaign references

Issue result:

- safe referral code
- safe public handle
- created/reused indicator
- error code when rejected

Terms evidence:

- `acceptedTerms=true` is required today
- future product API should include terms version or policy reference when the
  source of truth exists

## Target Contract Direction

Candidate product route:

```text
POST /referral-saas/accounts/{account_ref}/referral-codes
```

The current implementation route remains in place. TASK-174 introduces the
first bounded product wrapper and composes existing service behavior rather than
forking referral code creation logic.

Minimum product request:

```json
{
  "referrerRef": "safe-referrer-or-member-reference",
  "sticker": "QR001",
  "segment": "PERSONAL",
  "preferredHandle": "edwin",
  "acceptedTerms": true,
  "termsVersion": "optional-until-policy-source-exists"
}
```

Transitional request support may still accept `referrer_ucn` behind authenticated
partner/API contexts, but the product API should not make raw UCN the long-term
primary identifier.

Minimum product response:

```json
{
  "issueStatus": "CREATED",
  "referralCode": "ABC123DEF0",
  "publicHandle": "edwin",
  "created": true,
  "sourceType": "REFERRAL_CODE",
  "errorCode": null
}
```

Allowed product issue statuses:

- `CREATED`
- `EXISTING`
- `REJECTED_MISSING_FIELDS`
- `REJECTED_TERMS_REQUIRED`
- `REJECTED_IDENTITY_SCOPE`
- `CONFLICT`
- `FAILED`

## Authentication And Tenant Boundary

The issue workflow must derive tenant/account context from authenticated
identity, not from untrusted request body fields.

Current route behavior already follows this direction by using
`identity["tenant_code"]` from `require_partner_key`.

Future product API requirements:

- resolve `account_ref` or external account reference to internal tenant context
- reject account/tenant mismatches
- record authenticated actor and credential context for creates
- keep internal `tenant_code` out of public product contracts where possible

## Idempotency

Current natural idempotency is based on the service returning an existing code
for the same tenant, sticker, and referrer hash lookup.

Before implementation changes:

- preserve existing `200` existing-code response behavior
- do not add a second code for the same logical issue request
- do not expose raw UCN or referrer hash in response payloads
- resolve the schema uniqueness decision before promising per-tenant/per-sticker
  independent codes

Future explicit idempotency keys are optional only if the natural key is not
enough for product API retries.

## Audit And Privacy

Create events should be auditable with:

- authenticated actor or credential reference
- account/product reference
- internal tenant reference
- referrer lookup hash or safe participant reference
- sticker
- segment
- terms accepted flag
- terms version or policy reference when available
- created/reused result
- correlation or request identifier

Privacy rules:

- do not return raw UCN
- do not return UCN hash in public APIs
- do not log raw UCN in public/operator responses
- expose only code, handle, created/reused state, and safe references

## Failure Contract

Current failure codes:

- `MISSING_FIELDS`
- `ACCEPTED_TERMS_REQUIRED`

Future product wrapper failure codes should include:

- `ACCOUNT_NOT_FOUND`
- `ACCOUNT_SCOPE_MISMATCH`
- `REFERRER_NOT_FOUND`
- `TERMS_REQUIRED`
- `HANDLE_UNAVAILABLE`
- `DUPLICATE_CONFLICT`
- `ISSUE_TEMPORARILY_UNAVAILABLE`

Do not introduce new runtime error codes until the service, schema, and tests
are updated together.

## Future Tests

Implementation work following this contract should add or preserve tests for:

- tenant/account context is derived from authentication
- body-supplied tenant cannot override authenticated tenant
- accepted terms are required
- new issue returns `201`/`CREATED`
- repeated issue returns `200`/`EXISTING`
- raw UCN and UCN hash are never returned
- preferred handle is used only when valid and available
- invalid or unavailable preferred handle falls back to generated handle unless
  product behavior is intentionally changed
- unique constraint conflict handling and retry posture are explicit
- audit evidence exists for new code creation
- schema uniqueness matches the chosen product idempotency rule

## Implementation Slices

Recommended sequence:

1. Add product wrapper contract tests around existing route/service behavior.
2. Decide and document the `referrer_ucn_hash` uniqueness rule.
3. Add safe response/redaction tests.
4. Add audit evidence for new code creation if not already covered by a shared
   audit primitive.
5. Introduce a product API wrapper only after account reference resolution is
   available.

## Explicit Non-Goals

This task does not implement:

- schema migrations
- new routes
- service behavior changes
- frontend changes
- referral code validation
- validation recovery states
- referee UCN capture
- progress event ingestion
- attribution trace
- operator investigation workflow
- reporting/export
- rewards, funding, fulfilment, settlement, or sponsor billing
- live DB verification

## Readiness Decision

Referral SaaS has enough existing code creation capability to build from. The
next work should not recreate referral code issuing. It should wrap and harden
the current primitive with tenant/account-safe product contracts, redaction,
idempotency clarity, audit evidence, and tests.
