# Referral SaaS Account Membership Intent Physical Verification

Status: TASK-213 complete.
Product boundary: Referral SaaS.

## Purpose

TASK-213 proves Account Setup Step 2 can record Users/Roles invitation intent
through the running local API and database after durable account setup has
created a resolvable account foundation.

This proof intentionally remains bounded:

- invited membership intent is recorded
- membership posture can read the invited evidence back
- email delivery remains unconfigured
- membership activation remains unavailable
- seat assignment remains unavailable
- auth/session claim changes remain unavailable
- campaign activation, go-live, and money movement remain unavailable

## Verified Path

The physical checker exercises the same product chain the Account Setup UI now
drives:

1. Validate setup evidence with `POST /admin/onboarding/validate`.
2. Save setup intent with `POST /admin/onboarding/drafts`.
3. Submit the setup draft for review.
4. Record accepted internal review.
5. Create the durable account foundation through
   `POST /v1/referral-saas/accounts/from-draft`.
6. Resolve the account foundation through
   `GET /v1/referral-saas/accounts/resolve`.
7. Record Step 2 role intent through
   `POST /v1/referral-saas/accounts/{account_ref}/membership-invitations`.
8. Read membership posture through
   `GET /v1/referral-saas/accounts/membership-posture`.

## Local Command

Use a local tenant code that exists in `tenants` and is not already attached as
an account owner.

```powershell
.venv_codex\Scripts\python.exe scripts\referral_saas_account_membership_intent_physical_check.py --base-url http://127.0.0.1:8000 --admin-key test-admin-key --internal-tenant-code TASK213 --suffix local-213c
```

For the verified run, the local database first needed an unused test tenant:

```sql
INSERT INTO tenants (tenant_code, tenant_name, industry, currency, locale, is_active)
VALUES ('TASK213', 'TASK 213 Local Proof Tenant', 'Referral management and campaign attribution', 'ZAR', 'en-ZA', true)
ON CONFLICT (tenant_code) DO NOTHING;
```

## Observed Local Result

Verified local run:

```powershell
.venv_codex\Scripts\python.exe scripts\referral_saas_account_membership_intent_physical_check.py --base-url http://127.0.0.1:8000 --admin-key test-admin-key --internal-tenant-code TASK213 --suffix local-213c
```

Observed output included:

- `status: passed`
- `task: TASK-213`
- `membership_command_status: INVITATION_INTENT_RECORDED`
- `membership_status: INVITED`
- `delivery_status: DELIVERY_NOT_CONFIGURED`
- `membership_posture.invitedCount: 1`
- `no_invite_delivery_confirmed: true`
- `no_auth_claim_change_confirmed: true`
- `no_seat_assignment_confirmed: true`
- `no_money_movement_confirmed: true`
- `no_campaign_activation: true`
- `no_go_live: true`

The resolved proof account was `3048f250-367b-4c9c-a592-2ce3acd75345` for
external tenant reference `task-213-local-213c`.

## Boundary Notes

- The checker creates local/staging proof data only.
- The checker rejects unsafe payload terms for delivery, activation, internal
  tenant identifiers, campaign activation, webhooks, rewards, funding,
  settlement, wallet, invoice, payout, and adjacent money behavior.
- TASK-213 does not add invitation delivery provider integration, membership
  activation, seat assignment, auth-claim integration, account lifecycle
  commands, account maintenance commands, campaign activation, go-live, or
  DLaaS expansion behavior.

## Next Gap

Account Setup now has physical proof for company/account creation and Step 2
membership invitation intent. Remaining Account Setup gaps are membership
activation lifecycle, invitation delivery provider integration, account-safe
status/customer surfaces, account lifecycle commands, and deeper Account
Maintenance commands.
