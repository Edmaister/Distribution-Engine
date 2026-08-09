# Referral SaaS Provider/Vault Runtime Seam

Status: TASK-351 completed.

Product boundary: Shared Platform with Referral SaaS impact.

## Purpose

TASK-350 added the selected-customer provider/vault execution API foundation.
TASK-351 adds the runtime seam behind that API so the command no longer ends at
a generic placeholder. The execution service can now ask a shared adapter
registry to run a provider/vault action, and the registry returns explicit,
safe runtime states.

## What The Seam Does

- Accepts only already-normalized, bounded execution context from the governed
  execution API.
- Looks up an approved provider adapter by provider, environment, and
  capability.
- Requires a configured vault adapter before any registered provider adapter can
  return opaque provider/vault references.
- Returns explicit blocked states when no provider adapter or vault adapter is
  configured.
- Allows later provider-specific adapters to be registered without forking
  Referral SaaS account or Integrations code.

## Runtime States

| State | Meaning |
| --- | --- |
| `PROVIDER_VAULT_BLOCKED_ADAPTER_NOT_CONFIGURED` | The execution gates passed, but no approved provider runtime adapter exists for this provider/environment/capability. |
| `PROVIDER_VAULT_BLOCKED_VAULT_NOT_CONFIGURED` | A provider adapter exists, but no approved vault adapter is configured. |
| `PROVIDER_VAULT_EXECUTION_READY` | A registered adapter returned opaque provider/vault references. This state is only possible when both provider and vault adapters are registered. |

## Guardrails

The seam does not create, capture, reveal, rotate, revoke, download, or store raw
secret material. It does not dispatch live provider calls unless a future
approved adapter is explicitly registered behind the seam. It does not send
invites, dispatch webhooks, deliver referral messages, change auth/session
claims, activate campaigns, trigger billing, move money, add DLaaS scope, or
fork product source code.

## Next Implementation Track

The next provider/vault tasks should add reviewed provider-specific adapters and
an approved vault adapter implementation behind this seam, then repeat the
execution proof with non-local credentials and explicit production-like
permission.
