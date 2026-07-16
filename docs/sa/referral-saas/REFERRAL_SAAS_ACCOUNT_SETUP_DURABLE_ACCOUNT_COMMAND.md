# Referral SaaS Account Setup Durable Account Command

TASK ID: TASK-203

Product boundary: Referral Management and Campaign Attribution SaaS.

Status: Implemented as an internal service primitive. No route or frontend
control is added by this task.

## Boundary

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SCHEMA_FINAL_REVIEW.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_PHYSICAL_VERIFICATION.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

Shared primitive impact: Adds a durable account setup service over the shared
account foundation schema. Source duplication: No.

## Capability

`services/referral_saas_account_setup_service.py` creates the durable account
foundation from a `READY_FOR_REVIEW` onboarding draft and an existing internal
tenant scope supplied by a trusted caller.

The command writes:

- `platform_accounts`
- `platform_organisations`
- `platform_account_tenants`
- `platform_external_tenant_refs`
- `platform_account_audit_events`

The safe result returns account and reference identifiers, but redacts the
internal tenant identifier.

## Guardrails

- Requires an onboarding/admin role.
- Requires an existing internal `tenant_code`; it does not create tenants.
- Requires source draft status `READY_FOR_REVIEW`.
- Rejects duplicate active/pending/suspended external tenant references before
  opening the write transaction.
- Creates account status `PENDING_ONBOARDING` and tenant-link status
  `PENDING_SETUP`; it does not activate the account.
- Records account audit evidence.
- Does not create memberships, users, seats, invitations, credentials,
  campaigns, go-live state, webhooks, rewards, funding, fulfilment, settlement,
  wallet, invoice, payout, repair, replay, or retry behavior.

## Remaining Work

- Add a product/admin API wrapper around this service with explicit internal
  tenant resolution rules.
- Wire Account Setup review/creation UI to that wrapper.
- Physically test create account -> resolve account -> Account Setup UI state
  against the local app/API/DB.
- Add membership-aware authorization and invitation workflows after account
  foundation creation is proven end to end.
