# Referral SaaS Account Setup Physical Verification

TASK ID: TASK-202

Product boundary: Referral Management and Campaign Attribution SaaS.

Verification date: 2026-07-16.

## Boundary

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

Shared primitive impact: verifies and fixes onboarding draft persistence used
by the Account Setup workflow. Source duplication: No.

## Environment

- Frontend: `http://127.0.0.1:5173/admin/referral-saas/account-setup`
- Backend: `http://127.0.0.1:8000`
- Database: local Docker Postgres database `referrals`

## Results

- `GET /health` returned healthy API, database, and schema posture.
- The Account Setup page rendered the durable account resolver section and
  first-time setup-draft mode when no durable account reference existed.
- Local database initially did not contain the TASK-198 account foundation
  tables, so the existing additive migration
  `dp/migrations/082_referral_saas_account_foundation.sql` was applied locally.
- `GET /v1/referral-saas/accounts/resolve` then returned the expected safe
  `EXTERNAL_REFERENCE_NOT_FOUND` result for the demo setup reference.
- Dry-run validation completed with `GO_LIVE_DISABLED`, no persistence, and no
  live action.
- Draft save initially failed with an internal error because onboarding draft
  JSONB values were passed to asyncpg as raw Python dict/list objects.
- `services/onboarding/onboarding_draft_repository.py` now serializes JSONB
  payloads before persistence while preserving unsafe-key validation.
- The running local backend returned HTTP 200 for a unique physical Account
  Setup draft save through `POST /admin/onboarding/drafts`.
- The local DB confirmed persisted `onboarding_drafts` rows with
  `safe_summary` and `metadata` stored as JSONB objects and `redactions` stored
  as a JSONB array.

## Guardrails Confirmed

- No durable account was created.
- No internal tenant was created.
- No membership or invitation command was executed.
- No campaign activation or go-live action was executed.
- No webhook delivery, repair, replay, retry, reward, wallet, funding,
  fulfilment, settlement, invoice, payout, or other money action was executed.

## Remaining Account Setup Gaps

- Membership-aware authorization remains future work.
- Account creation commands remain future work.
- Invitation and membership writes remain future work.
- Submit/review physical UI proof should be completed after membership and
  review policy are productized.
- Account Maintenance command workflows remain future work.
