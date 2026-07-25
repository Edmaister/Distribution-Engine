# Referral SaaS People and Access Provisioning Physical Verification

Last updated: 2026-07-25

## Scope

TASK-287 verifies the selected-customer People and Access provisioning path from
Referral SaaS account context through the guarded API and optional DB/audit
evidence.

Product boundary: Referral SaaS.
Shared primitive impact: account registry, membership posture, activation
readiness, membership lifecycle, seat provisioning, account audit, idempotency,
and redaction primitives.
Source duplication: No.

## Local Run

Command:

```powershell
.\.venv_codex\Scripts\python.exe scripts\referral_saas_people_access_provisioning_physical_check.py --base-url http://127.0.0.1:8000 --admin-key test-admin-key --external-tenant-ref test-fnb-sa-002 --database --db-dsn postgresql://user:pass@localhost:5432/referrals
```

Result: Passed with a controlled provisioning block.

Selected customer:

- Customer reference: `test-fnb-sa-002`
- Organisation reference: `test-referral-fnb-002`
- Account ref: `389eb0e5-7f27-4ed8-812f-d670f3a34cba`

Provisioning result:

- Status: `PROVISIONING_REJECTED_ACCOUNT_NOT_ACTIVE`
- Replay status: `PROVISIONING_REJECTED_ACCOUNT_NOT_ACTIVE`
- Audit event type: `REFERRAL_SAAS_ACCESS_PROVISIONING_REQUEST`
- Audit event status: `BLOCKED`
- Membership status: `ACTIVE`
- Seat assignment: `SEAT_NOT_ASSIGNED`
- Auth claims: `AUTH_CLAIMS_NOT_PROPAGATED`

## Guardrails Confirmed

- No invite delivery occurred.
- No credential was created.
- No auth/session claim was propagated.
- No campaign activation occurred.
- No go-live state changed.
- No billing or money movement occurred.
- The blocked provisioning request was audited.
- The idempotency replay returned the same controlled provisioning status.

## Remaining Proof Gap

TASK-287 proved the controlled blocked path for an inactive customer. TASK-294
now records successful local execution of the activated path with active
account/link posture, accepted membership, available seat evidence, DB readback,
audit evidence, idempotency replay, and no adjacent side effects.

## TASK-291 Activated Proof Path

TASK-291 extends the same physical proof runner with an optional guarded
account-foundation activation step before People and Access provisioning.

Command:

```powershell
.\.venv_codex\Scripts\python.exe scripts\referral_saas_people_access_provisioning_physical_check.py --base-url http://127.0.0.1:8000 --admin-key test-admin-key --external-tenant-ref test-fnb-sa-002 --activate-account-foundation --database --db-dsn postgresql://user:pass@localhost:5432/referrals
```

What this proves when run against suitable local/staging data:

- The selected customer is activated through
  `POST /v1/referral-saas/accounts/{account_ref}/activation-requests`.
- Account/link activation happens before seat provisioning.
- Seat provisioning still runs through the guarded People and Access
  provisioning route.
- Idempotency replay remains checked.
- No direct DB tweak or hidden setup bypass is used.

TASK-294 records that proof locally. Remaining future proof should repeat this
against staging or production-like data when those environments are available,
and should stay separate from governed credential creation and auth-claim
propagation work.

## TASK-294 Activated Local Proof Execution

Command:

```powershell
.\.venv_codex\Scripts\python.exe scripts\referral_saas_people_access_provisioning_physical_check.py --base-url http://127.0.0.1:8000 --admin-key test-admin-key --external-tenant-ref test-fnb-sa-002 --activate-account-foundation --database --db-dsn postgresql://user:pass@localhost:5432/referrals --suffix task-294-local-proof
```

Result: Passed with actual seat assignment completed.

Selected customer:

- Account name: `test-referral-fnb-002`
- Customer reference: `test-fnb-sa-002`
- Organisation reference: `test-referral-fnb-002`
- Account ref: `389eb0e5-7f27-4ed8-812f-d670f3a34cba`

Account foundation activation:

- Command status: `ACCOUNT_FOUNDATION_ACTIVATED`
- Account status: `ACTIVE`
- Tenant-link status: `ACTIVE`
- Onboarding status: `APPROVED`
- Available seat types confirmed: `ADMIN`, `OPERATOR`
- Audit event: `0075fd88-b073-4aea-9f3a-d57b2fd78c28`

People and Access provisioning:

- Membership ref: `5979fafe-12ce-43b4-a2ea-2c4b19d77740`
- Accepted subject: `edwin.tait1@gmail.com`
- Provisioning status: `PROVISIONING_REQUEST_RECORDED`
- Replay status: `PROVISIONING_REPLAYED`
- Seat assignment: `SEAT_ASSIGNED`
- Seat ref: `83075a48-e630-4225-8c30-077d2513a9b4`
- Seat type: `OPERATOR`
- Auth claims: `AUTH_CLAIMS_NOT_PROPAGATED`
- Audit event: `6c4e7ba7-57bb-457b-aaae-68969c845816`

DB/audit readback:

- Membership status: `ACTIVE`
- Access provisioning status: `SEAT_ASSIGNED`
- Audit event type: `REFERRAL_SAAS_ACCESS_PROVISIONING_REQUEST`
- Audit event status: `RECORDED`
- Refreshed provisioning readiness: `SEAT_ASSIGNED`
- Refreshed seat assignment status: `SEAT_ASSIGNED`

Guardrails confirmed:

- No invite delivery occurred.
- No credential was created.
- No auth/session claim was propagated.
- No campaign activation occurred.
- No go-live state changed.
- No billing or money movement occurred.
- The successful provisioning request was audited.
- The idempotency replay returned the same provisioning result.
