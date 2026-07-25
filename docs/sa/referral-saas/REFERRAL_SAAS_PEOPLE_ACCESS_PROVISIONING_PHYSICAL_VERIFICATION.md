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

The local customer used for this run is not active for seat provisioning, so
TASK-287 proves the controlled blocked path. A successful seat-assignment proof
still needs an active selected customer with active tenant-link,
external-reference, accepted membership, and available platform seat evidence.

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

Remaining proof gap after implementation: execute the TASK-291 runner against a
local or staging customer with active account/link posture and available seat
capacity, then record a successful seat-assignment result and DB/audit evidence.
