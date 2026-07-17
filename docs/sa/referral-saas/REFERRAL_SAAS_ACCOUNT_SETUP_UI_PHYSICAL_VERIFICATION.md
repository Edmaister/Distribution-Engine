# Referral SaaS Account Setup UI Physical Verification

Status: TASK-208 complete.
Product boundary: Referral SaaS.
Source duplication: No.
Local proof result: passed on 2026-07-17 with internal tenant scope
`TASK208C`, external tenant ref `task-208-local-208c`, and draft ref
`draft_0805b7fc9ea24fd02efc`.

## Purpose

TASK-208 closes the gap between a wired Account Setup screen and a locally
provable setup journey. The Referral SaaS Account Setup UI now builds the full
bounded onboarding evidence set required by the shared onboarding validator:

- company
- producer_sponsor
- distributor
- member_role
- campaign_opportunity
- webhook_api

This matters because submit-for-review revalidates the saved draft from the
database. A partial UI payload can save draft intent but cannot reliably move
through review and account foundation creation.

## Verified Path

The physical checker exercises the same product path the UI drives:

1. Validate setup evidence with `POST /admin/onboarding/validate`.
2. Save setup intent with `POST /admin/onboarding/drafts`.
3. Submit the saved draft with
   `POST /admin/onboarding/drafts/{draft_ref}/submit-for-review`.
4. Record bounded internal review with
   `POST /admin/onboarding/drafts/{draft_ref}/review-decision`.
5. Create the durable account foundation with
   `POST /v1/referral-saas/accounts/from-draft`.
6. Resolve the created account with
   `GET /v1/referral-saas/accounts/resolve`.

The checker blocks unsafe product payload terms such as internal tenant code
fields, secrets, wallet/settlement fields, go-live activation, and invitations.

## Local Command

Use an internal tenant code that is not already linked as an account owner in
the local database. If `FNB` was used by TASK-206, either use another seeded
tenant code or reset the local test account rows before running this proof.

```powershell
.venv_codex\Scripts\python.exe scripts\referral_saas_account_setup_ui_physical_check.py --base-url http://127.0.0.1:8000 --admin-key test-admin-key --internal-tenant-code FNB --suffix local-208
```

Verified local run:

```powershell
.venv_codex\Scripts\python.exe scripts\referral_saas_account_setup_ui_physical_check.py --base-url http://127.0.0.1:8000 --admin-key test-admin-key --internal-tenant-code TASK208C --suffix local-208c
```

Observed output included `status: passed`, `review_outcome:
APPROVED_FOR_INTERNAL_REVIEW`, `submit_status: READY_FOR_REVIEW`, created
account `ACCT_A913D269F78A1ECBCF71`, and resolver readback for
`task-208-local-208c`.

Expected result:

- `status` is `passed`
- `task` is `TASK-208`
- draft status progresses through saved, submitted, and reviewed states
- account foundation is created and then resolved by external reference
- no tenant creation, invite, campaign activation, go-live, credential, wallet,
  settlement, or value-transfer action is performed

## Guardrails

- The UI still does not expose internal tenant identifiers to the operator.
- The account creation command remains gated behind saved draft, successful
  submit-for-review, accepted internal review, and no existing resolved account.
- This task does not add membership writes, invitations, lifecycle commands,
  account maintenance commands, campaign activation, go-live, webhook delivery,
  rewards, funding, fulfilment, settlement, commission, wallet, invoice, payout,
  sponsor billing, marketplace expansion, white-label/embed, SaaS billing, or
  broad DLaaS behavior.

## Remaining Gaps

TASK-208 proves the complete account setup command chain is now bounded and
testable. The remaining Account Setup product gaps are membership-aware
authorization, invitation flows, account lifecycle commands, and deeper Account
Maintenance command workflows.
