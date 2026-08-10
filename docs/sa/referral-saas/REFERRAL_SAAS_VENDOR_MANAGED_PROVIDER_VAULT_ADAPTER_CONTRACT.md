# Referral SaaS Vendor/Managed Provider-Vault Adapter Contract

Product boundary: Shared Platform with Referral SaaS impact.

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
- `docs/sa/referral-saas/REFERRAL_SAAS_PLATFORM_REFERENCE_PROVIDER_VAULT_ADAPTERS.md`

Source duplication: No.

## Purpose

TASK-353 added the first safe `PLATFORM_REFERENCE` provider/vault adapter pair.
That adapter proves the runtime seam can return opaque provider and vault
references without handling raw secrets or dispatching a vendor.

TASK-354 defines the next adapter class: vendor/managed provider-vault adapters.
These adapters are the bridge from approved Referral SaaS credential requests to
real provider and vault execution evidence, but only through a governed platform
boundary.

## Product Meaning

For Referral SaaS operators, this capability should eventually mean:

- an approved Integrations credential request can be executed by a platform
  adapter;
- the product receives opaque provider and vault references, not raw secrets;
- the selected customer can see whether provider/vault setup is complete;
- live invite delivery, webhook dispatch, referral-message delivery, and login
  provider work stay behind their own readiness and execution gates.

It must not turn the Referral SaaS UI into a secret-entry, provider-console, or
generic integration-mutation screen.

## Adapter Classes

| Adapter class | Allowed responsibility | Examples | Forbidden responsibility |
| --- | --- | --- | --- |
| Vendor provider adapter | Validate that a platform-approved provider execution target can return an opaque provider runtime reference. | Email provider reference, webhook provider reference, message provider reference, identity-provider reference. | Accept raw secrets from the browser, send an invite, dispatch a webhook, deliver a message, create credentials, assign seats, change auth claims, activate campaigns, bill, or move money. |
| Managed vault adapter | Store or resolve platform-controlled secret material through an approved vault implementation and return an opaque vault reference. | Managed vault secret reference, rotation reference, version reference. | Reveal, download, log, or return raw secret material to Referral SaaS routes or UI. |
| Runtime execution adapter | Combine an approved credential request, provider adapter, vault adapter, account scope, audit, idempotency, and redaction checks into a safe execution result. | `PROVIDER_VAULT_EXECUTION_READY`, `PROVIDER_ADAPTER_NOT_CONFIGURED`, `VAULT_ADAPTER_NOT_CONFIGURED`, `PROVIDER_VAULT_EXECUTION_BLOCKED`. | Dispatch downstream provider work outside the explicit adapter contract. |

## Required Gates

A vendor/managed adapter may run only when all gates pass:

1. Selected-customer account scope is resolved by account reference.
2. Account, tenant link, and external reference are active and selected.
3. Integrations configuration exists for the customer and target capability.
4. Credential request exists, is current-version, and is approved.
5. Provider key, environment, and capability are on the approved adapter allowlist.
6. Vault adapter is configured for the approved environment.
7. Idempotency key is present and payload replay rules pass.
8. Audit evidence is written with safe references only.
9. Response redactions remove tenant code, raw provider payloads, raw vault paths,
   raw secrets, tokens, signing material, and internal account identifiers.

## Safe Response Contract

Successful execution returns:

- execution reference;
- provider key;
- capability;
- environment;
- opaque provider runtime reference;
- opaque vault reference;
- adapter reference;
- vault adapter reference;
- audit correlation reference;
- safe next action;
- plain-language summary.

The response must not return:

- raw secret values;
- raw provider payloads;
- vault paths, bucket names, object keys, or secret names;
- provider credentials;
- tenant code;
- internal user identifiers;
- auth claims or session information.

## Failure Contract

| Failure | Meaning | Operator message |
| --- | --- | --- |
| `PROVIDER_ADAPTER_NOT_CONFIGURED` | The provider key/capability/environment is not installed or approved. | Provider adapter is not ready for this customer setup. |
| `VAULT_ADAPTER_NOT_CONFIGURED` | The provider can be targeted but the managed vault adapter is missing. | Managed vault setup is required before provider execution can complete. |
| `PROVIDER_VAULT_EXECUTION_BLOCKED` | Scope, credential request, provider approval, environment, idempotency, or audit gates failed. | Fix the listed setup evidence before trying again. |
| `PROVIDER_VAULT_EXECUTION_READY` | Opaque provider and vault references were produced. | Provider/vault setup evidence is ready; downstream delivery remains separately gated. |

## Implementation Sequence

1. Add the adapter allowlist and managed-vault adapter registry contract.
2. Add focused runtime tests for configured vendor/provider and vault adapter
   success without provider dispatch.
3. Add blocked-state tests for missing vendor adapter, missing vault adapter,
   unsupported environment, unsupported capability, stale request, and
   idempotency conflict.
4. Wire the execution API to return vendor/managed adapter results without
   changing selected-customer UI behavior.
5. Add UI copy only after backend states are stable, if the existing
   Integrations page needs clearer provider/vault readiness messaging.
6. Repeat local and non-local proof only after approved credentials and
   execution permissions are available.

## Non-Goals

This contract does not implement:

- vendor calls;
- webhook dispatch;
- invite delivery;
- referral-message delivery;
- raw secret capture, reveal, rotation, or download;
- credential creation from a browser payload;
- identity-provider login creation;
- auth/session claim propagation;
- campaign activation;
- repair, replay, or retry execution;
- export delivery execution;
- billing;
- money movement;
- DLaaS expansion;
- source forks.

## 10/10 Impact

This task closes the design ambiguity between the platform-reference adapter and
future vendor/managed adapters. It moves the campaign attribution capability from
`9.99994/10` to `9.99995/10`.

The remaining blockers to a full `10/10` are:

- vendor/managed adapter runtime implementation;
- governed repair/replay command execution, if launch scope requires it;
- approved non-local launch verification evidence.
