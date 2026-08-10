# Referral SaaS Provider/Vault Adapter Implementation Plan

Task: TASK-352
Status: Complete
Product boundary: Shared Platform with Referral SaaS impact

## Boundary

TASK-351 added the shared runtime seam. This plan defines the first safe adapter
implementation sequence behind that seam. It prevents the next task from
guessing a vendor, storing raw secrets in Referral SaaS, or presenting a fake
provider/vault success state.

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/README.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/README.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PROVIDER_VAULT_RUNTIME_ADAPTER_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PROVIDER_VAULT_RUNTIME_EXECUTION_COMMAND_CONTRACT.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PROVIDER_VAULT_RUNTIME_SEAM.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

Source duplication: No.

## Source Facts

The current code already has selected-customer Integrations evidence, credential
request/review lifecycle, provider/vault readiness, a provider/vault execution
API foundation, a shared provider/vault runtime registry/executor seam, and
audit/idempotency/redaction guardrails.

The current code does not yet have a reviewed runtime adapter implementation,
an approved vault adapter configuration source, provider-specific live
dispatch, vault-owned secret lifecycle, or non-local provider/vault execution
evidence.

## Recommended Adapter Sequence

| Order | Adapter | Purpose | Why first |
| --- | --- | --- | --- |
| 1 | `PLATFORM_REFERENCE` provider adapter | Records that an approved provider reference exists for the selected customer, capability, and environment. | Proves the runtime adapter path without raw secrets or vendor dispatch. |
| 2 | `PLATFORM_VAULT_REFERENCE` vault adapter | Records an opaque vault reference supplied by governed platform configuration, not by Referral SaaS browser fields. | Lets the execution API return a real opaque vault reference without storing or revealing secret values. |
| 3 | Vendor provider adapter | Calls or validates a specific approved provider behind platform governance. | Only safe after reference adapters, non-local credentials, and provider-specific failure states are reviewed. |
| 4 | Managed vault adapter | Owns actual secret storage/retrieval under platform policy. | Requires approved infrastructure, secret ownership, rotation, and non-local proof. |

The first implementation task should build items 1 and 2 together as a guarded
reference adapter. It should not call a live provider. It should not accept raw
secrets from the browser. It should only return opaque references when the
approved credential request, configuration, provider approval, account/link/
reference posture, adapter configuration, audit, and idempotency gates pass.

## First Code Task Shape

The next task should be:

`TASK-353: Add platform-reference provider/vault adapters`

Expected implementation:

- register a `PLATFORM_REFERENCE` provider adapter behind
  `services/referral_saas_provider_vault_runtime.py`
- register a `PLATFORM_VAULT_REFERENCE` vault adapter/configuration path
- return `PROVIDER_VAULT_EXECUTION_READY` only with opaque provider/vault
  references
- persist safe execution evidence through the existing TASK-350 execution route
- keep adapter configuration outside customer-entered Referral SaaS setup forms
- add unit/API tests for success, missing provider adapter, missing vault
  adapter, replay, changed-payload conflict, unsafe payload, and redaction

## Runtime Configuration Boundary

Adapter configuration is a Shared Platform concern. Referral SaaS may show
readiness and safe evidence, but it must not own raw provider credentials or
vault secret material.

Allowed configuration inputs:

- approved provider key
- environment
- capability
- opaque provider reference
- opaque vault reference
- adapter reference
- vault adapter reference
- governance/audit reason

Blocked configuration inputs:

- raw API keys
- signing secrets
- private keys
- passwords
- bearer tokens
- client secrets
- provider payload blobs
- arbitrary auth claim maps
- billing or money instructions

## Safe States

| State | Meaning | Product copy |
| --- | --- | --- |
| `PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED` | No approved provider adapter exists for the selected provider/environment/capability. | Configure the approved provider adapter before execution can run. |
| `PROVIDER_VAULT_BLOCKED_VAULT_NOT_CONFIGURED` | Provider adapter exists, but no approved vault/reference adapter is configured. | Configure the approved vault reference before provider/vault evidence can be recorded. |
| `PROVIDER_VAULT_EXECUTION_READY` | Approved provider and vault/reference adapters returned opaque references. | Provider/vault references are recorded. No secret was exposed and no live delivery occurred. |

## Explicit Non-Goals

This plan does not implement runtime code. The next code task must still avoid
raw secret handling, browser-submitted credential material, live provider
dispatch unless a later vendor-adapter task explicitly allows it, invite
delivery, webhook dispatch, referral-message delivery, auth/session claim
changes, campaign activation, repair/replay/retry execution, export delivery
execution, billing or money movement, DLaaS expansion, and source forks.

## 10/10 Impact

This closes the ambiguity around what "real provider/vault adapter" means for
the next implementation step. It does not remove the runtime adapter gap by
itself. Referral Management remains `9.99/10`; Campaign Attribution moves to
`9.99993/10` because the adapter implementation path is now bounded, but
runtime adapters and non-local proof repetition remain open.
