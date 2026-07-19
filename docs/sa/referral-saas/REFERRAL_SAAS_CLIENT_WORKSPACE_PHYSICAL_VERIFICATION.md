# Referral SaaS Client Workspace Physical Verification

Task: TASK-229
Product boundary: Referral SaaS.

## Purpose

Verify the local Account Setup to Client Workspace handoff before deeper
campaign work continues.

The check proves that a client created through the guarded Account Setup path
can be selected from the Referral SaaS account registry and used to load the
Client Workspace readiness projection by external customer identifiers.

## Verification Scope

- Runs the existing Account Setup physical proof.
- Loads `GET /v1/referral-saas/accounts`.
- Confirms the created client appears in the account registry.
- Loads `GET /admin/onboarding/state` for the selected client identifiers.
- Confirms the returned maintenance/readiness state is scoped to that client.
- Confirms the Client Workspace route set stays inside Referral SaaS surfaces.

## Boundary Guardrails

The check does not create or update a durable profile after account creation.
It does not send invitations, change auth claims, rotate credentials, deliver
webhooks, activate campaigns, enable go-live, repair/replay events, or move
money.

The Client Workspace route set is restricted to:

- Account Setup
- Account Maintenance / Client Workspace
- Technical Setup
- Campaigns
- Links and Codes
- Attribution Trace
- Reports
- Support

## Local Command

```powershell
python scripts\referral_saas_client_workspace_physical_check.py --suffix local-229
```

Use a unique suffix for repeated physical runs.

## Expected Result

The script prints a JSON payload with:

- `status: passed`
- `task: TASK-229`
- created account evidence
- selected client evidence
- selected maintenance scope
- readiness summary
- no adjacent live-action confirmations

## Current Result

Recorded 2026-07-19 against the local API at `http://127.0.0.1:8000`.

The strict create-first run reached account creation but returned `409
DUPLICATE_EXTERNAL_REFERENCE` because every local internal tenant seed is
already attached to an account owner. Local read-only DB inspection showed
available tenant codes `FNB`, `TASK208`, `TASK208C`, and `TASK213`, each with
one account link.

The Client Workspace verification was then run in existing-client mode:

```powershell
.venv_codex\Scripts\python.exe scripts\referral_saas_client_workspace_physical_check.py --reuse-existing-client --suffix local-229
```

Result:

- `status`: `passed`
- `task`: `TASK-229`
- `account_setup_creation_mode`: `reused_existing_client`
- selected client: `3048f250-367b-4c9c-a592-2ce3acd75345`
- selected customer reference: `task-213-local-213c`
- selected organisation reference: `org-task-213-local-213c`
- readiness status: `GO_LIVE_DISABLED`
- readiness summary: 0 ready, 1 blocked, 6 missing evidence, 1 go-live disabled
- confirmed no profile update, invitation delivery, campaign activation, go-live,
  or money movement

This proves the running local API can load the Referral SaaS account registry,
select an existing durable client, and hydrate the Client Workspace readiness
projection with external customer identifiers. A fresh create-first physical
run still needs a new local internal tenant seed that is not already attached
to an account owner.
