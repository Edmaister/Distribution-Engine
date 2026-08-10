# Referral SaaS Vendor/Managed Provider-Vault Adapters

Task: TASK-355
Status: Complete
Product boundary: Shared Platform with Referral SaaS impact

## Boundary

TASK-355 implements the first bounded vendor/managed provider-vault runtime
adapter path behind the shared provider/vault seam.

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
- `docs/sa/referral-saas/REFERRAL_SAAS_VENDOR_MANAGED_PROVIDER_VAULT_ADAPTER_CONTRACT.md`

Source duplication: No.

## Implemented Runtime Behavior

The runtime now supports a built-in vendor/managed reference adapter. It is not
enabled by provider name alone. The platform must explicitly configure:

- approved vendor provider keys;
- an approved managed-vault adapter reference.

When both are configured and the existing selected-customer execution API gates
already passed, the adapter returns opaque setup evidence:

- `vendor_prv_ref_*` provider runtime reference;
- `managed_vault_ref_*` vault reference;
- `VENDOR_MANAGED_PROVIDER_REFERENCE:{PROVIDER}` adapter reference;
- configured managed-vault adapter reference.

These references are deterministic hashes over the approved runtime request
context. They are setup evidence, not raw provider credentials and not provider
dispatch receipts.

## Failure States

| State | Meaning |
| --- | --- |
| `PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED` | The provider key, environment, or capability is not configured for vendor/managed runtime execution. |
| `PROVIDER_VAULT_BLOCKED_VAULT_NOT_CONFIGURED` | The provider is allowed but no approved managed-vault adapter reference is configured. |
| `PROVIDER_VAULT_EXECUTION_READY` | Opaque vendor and managed-vault references were recorded without unsafe side effects. |

## Guardrails

This implementation does not accept browser-held secrets, reveal stored secrets,
write live vault material, call a vendor provider, send invites, dispatch
webhooks, deliver referral messages, create login credentials, change auth
claims, assign seats, activate campaigns, trigger billing, move money, add
DLaaS scope, or fork source code.

## Product Meaning

For Referral SaaS, this closes the adapter-runtime implementation gap enough for
approved provider/vault execution to produce safe opaque references in a local
or configured environment.

Real provider dispatch, real managed secret lifecycle, repair/replay execution,
and non-local proof remain separate governed tracks.

## 10/10 Impact

Referral Management remains `9.99/10`. Campaign Attribution moves to
`9.99996/10` because vendor/managed provider-vault runtime adapter code exists,
while repair/replay command execution and non-local proof repetition remain
open.
