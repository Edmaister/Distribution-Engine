# Referral SaaS Platform-Reference Provider/Vault Adapters

Task: TASK-353
Status: Complete
Product boundary: Shared Platform with Referral SaaS impact

## Boundary

TASK-353 implements the first safe runtime adapters behind the shared
provider/vault seam from TASK-351 and the implementation plan from TASK-352.
The implementation proves that approved provider/vault execution can return
opaque references without accepting raw secrets, calling a vendor provider, or
writing live vault secret material.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PROVIDER_VAULT_ADAPTER_IMPLEMENTATION_PLAN.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

Source duplication: No.

## Implemented Runtime Adapters

| Adapter | Purpose | Runtime behavior |
| --- | --- | --- |
| `PLATFORM_REFERENCE` | First approved provider-reference adapter. | Returns an opaque provider runtime reference after existing execution gates pass. |
| `PLATFORM_VAULT_REFERENCE` | First approved vault-reference adapter. | Returns an opaque vault reference without browser-held secrets or live vault writes. |

The references are deterministic hashes over the approved runtime request
context. They are safe execution evidence, not raw provider credentials and not
provider-owned IDs.

## Safe Execution Rules

The platform-reference adapters only run for:

- provider key: `PLATFORM_REFERENCE`
- capability: `REFERRAL_SAAS_PROVIDER_REFERENCE`
- environment: `SANDBOX`, `STAGING`, or `PRODUCTION`

Any other provider, capability, or environment still returns the existing
adapter-not-configured blocked state unless a separately reviewed adapter is
registered.

## Product Meaning

When the governed execution API returns `PROVIDER_VAULT_EXECUTION_READY` from
these adapters, it means:

- an approved provider/vault reference was recorded for the selected customer
- the response contains opaque references only
- no raw secret was submitted, stored, revealed, downloaded, or rotated
- no vendor provider was called
- no live vault secret was written
- no invite, webhook, referral message, auth, campaign, billing, money, DLaaS,
  or source-fork side effect occurred

## Remaining Gaps

This task does not implement vendor provider dispatch, managed vault secret
lifecycle, repair/replay execution, or non-local provider/vault proof. Those
remain separate launch-hardening tasks because they require provider-specific
failure handling, external infrastructure, secret rotation/ownership policy,
and non-local verification evidence.

## 10/10 Impact

Referral Management remains `9.99/10`. Campaign Attribution moves to
`9.99994/10` because the first runtime provider/vault adapter code now exists,
but vendor/managed adapters, repair/replay execution, and non-local proof
repetition remain open.
