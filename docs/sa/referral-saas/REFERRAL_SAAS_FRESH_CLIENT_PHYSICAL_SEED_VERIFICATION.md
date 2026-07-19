# Referral SaaS Fresh Client Physical Seed Verification

Task: TASK-230
Product boundary: Referral SaaS.

## Purpose

Make the local Account Setup to Client Workspace physical proof repeatable for
fresh client creation.

TASK-229 proved the selected Client Workspace path with an existing durable
client, but the strict create-first run was blocked because every local tenant
seed was already attached to an account owner. TASK-230 adds a local-only seed
guard that prepares a new unlinked test tenant before delegating to the existing
guarded Account Setup and Client Workspace physical proof.

## Verification Scope

- Creates or updates one local `TASK230...` tenant row when that tenant has no
  active owner link.
- Rejects the run if the requested local tenant seed is already attached to an
  account owner.
- Runs the existing Account Setup to Client Workspace physical proof in
  fresh-client mode.
- Confirms the created client appears in the safe Referral SaaS account
  registry and hydrates Client Workspace readiness by external references.

## Boundary Guardrails

This is not a product API and does not relax account creation rules.

The helper does not delete or reset local account data. It does not create
users, assign permissions, send invitations, rotate credentials, deliver
webhooks, activate campaigns, enable go-live, repair/replay events, or move
money.

## Local Command

```powershell
.venv_codex\Scripts\python.exe scripts\referral_saas_fresh_client_workspace_physical_check.py --db-dsn $env:APP_DB_DSN --suffix local-230
```

Use a unique suffix for repeated local physical runs.

## Expected Result

The script prints a JSON payload with:

- `status: passed`
- `task: TASK-230`
- prepared local tenant seed evidence
- created account evidence
- selected Client Workspace evidence
- no adjacent live-action confirmations

## Current Result

Recorded 2026-07-19 against the local API at `http://127.0.0.1:8000` and
local DB `postgresql://user:pass@localhost:5432/referrals`.

Command:

```powershell
.venv_codex\Scripts\python.exe scripts\referral_saas_fresh_client_workspace_physical_check.py --db-dsn postgresql://user:pass@localhost:5432/referrals --suffix local-230
```

Result:

- `status`: `passed`
- `task`: `TASK-230`
- tenant seed: `TASK230LOCAL230`
- seed owner-link status before account creation: `UNLINKED`
- created account: `f3471a47-69c9-4953-9f73-be2b397e5871`
- created account code: `ACCT_7788B683DA4FE71057A3`
- selected customer reference: `task-230-local-230`
- selected organisation reference: `org-task-230-local-230`
- readiness status: `GO_LIVE_DISABLED`
- readiness summary: 0 ready, 1 blocked, 6 missing evidence, 1 go-live disabled
- confirmed no profile update, invitation delivery, campaign activation, go-live,
  or money movement

This proves fresh Account Setup to selected Client Workspace physical
verification is repeatable locally by creating a bounded unlinked test tenant
seed before invoking the existing guarded account creation path.
