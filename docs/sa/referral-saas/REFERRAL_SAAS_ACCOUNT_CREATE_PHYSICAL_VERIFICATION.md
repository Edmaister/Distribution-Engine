# Referral SaaS Account Creation Physical Verification

Date: 2026-07-17

Task: TASK-206

Product boundary: Referral SaaS

## Purpose

Physically verify that the Referral SaaS account setup API can create a durable
account foundation from a reviewed onboarding draft, resolve that account through
the product resolver, and preserve the Referral SaaS boundary before the frontend
create action is wired.

This proof is intentionally limited to account foundation creation. It does not
create tenants, memberships, invitations, campaigns, credentials, webhooks,
go-live actions, rewards, funding, fulfilment, settlement, or money movement.

## Verified Path

The local physical checker creates or reuses reviewed setup evidence, calls the
guarded product account creation API, resolves the created account through the
product resolver, and optionally verifies the resulting database rows.

Command used for the passing local proof:

```powershell
.venv_codex\Scripts\python.exe scripts\referral_saas_account_create_physical_check.py --base-url http://127.0.0.1:8000 --admin-key test-admin-key --internal-tenant-code FNB --suffix local-206b --db-dsn postgresql://user:pass@localhost:5432/referrals --seed-reviewed-draft-db
```

Passing proof summary:

- Draft reference: `draft_task_206_local_206b`
- External tenant reference: `task-206-local-206b`
- Organisation reference: `org-task-206-local-206b`
- Account code: `ACCT_B9C8E8BF29B647DBAA12`
- Account id: `88c83466-142c-4856-8cf6-899ff3cbb549`
- Account status: `PENDING_ONBOARDING`
- Onboarding status: `READY_FOR_REVIEW`
- Tenant link status: `PENDING_SETUP`
- Audit event id: `16da28a7-ac16-49e7-b435-8de3c7af645b`
- External reference rows verified: `2`
- Account audit rows verified: `1`

The create response and resolve response were checked for internal tenant
identifier leakage. No `tenantCode` or `tenant_code` field was exposed in the
product payload.

## Guardrails Verified

The physical proof confirmed these account creation guardrails:

- `DURABLE_ACCOUNT_FOUNDATION_ONLY`
- `EXISTING_INTERNAL_TENANT_REQUIRED`
- `NO_TENANT_CREATION`
- `NO_MEMBERSHIP_WRITE`
- `NO_INVITE_DELIVERY`
- `NO_CAMPAIGN_PUBLICATION`
- `NO_CREDENTIAL_LIFECYCLE`
- `NO_WEBHOOK_DISPATCH`
- `NO_MONEY_MOVEMENT`

The checker also reports:

- no adjacent live action
- no money movement
- no campaign activation
- internal tenant identifier redaction

## Findings

The first local run through the normal draft save and submit-for-review API path
returned a validation-blocked response because the local draft evidence did not
produce a review-valid set of all required sections. The physical checker now
supports an explicit local/staging reviewed-draft DB seed mode so TASK-206 can
prove the account creation boundary without pretending that the full UI draft
journey is already complete.

A repeated physical create attempt against the same internal tenant scope exposed
a backend hardening gap: the database uniqueness rule for a tenant owner link
could surface as an internal server error after duplicate external-reference
checks passed. The account setup service now prechecks an existing active or
pending owner link for the trusted internal tenant scope and raises a safe
duplicate conflict before opening the write transaction.

## Outcome

TASK-206 closes the physical create-account proof gap for the current backend
wrapper. The next Account Setup task can wire the frontend create action only if
the product flow deliberately uses reviewed draft evidence. The remaining setup
gap is not whether the backend can create a durable account foundation; it is the
operator workflow around when that command is shown, how the reviewed draft is
selected, and how duplicate or already-created account states are explained.

## Remaining Account Setup Gaps

- Wire the Referral SaaS Account Setup UI create action to the guarded API.
- Decide whether to harden the normal save -> submit -> review path before
  exposing the create action to testers.
- Add membership-aware account setup authorization.
- Add invitation and role membership flows.
- Add account lifecycle and Account Maintenance commands.
- Keep campaign setup blocked until account setup evidence is clear enough for
  referral testing.
