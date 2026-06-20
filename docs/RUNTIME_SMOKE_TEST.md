# Runtime Smoke Test

Last checked: local API at `http://127.0.0.1:8000`

## Safe Startup Checks

| Check | Expected | Observed |
| --- | --- | --- |
| `GET /health` | `200` | `200` |
| `GET /readyz` | `200` when DB, schema, and SQS are ready | Schema-aware readiness |
| `GET /docs` | `200` | `200` |
| `GET /openapi.json` | `200` | `200` |
| `GET /` | `200` | `200` |

Health reported:

```json
{
  "status": "ok",
  "components": {
    "db": { "ok": true, "msg": "ok" },
    "sqs": { "ok": true, "msg": "stub mode" },
    "kafka": { "ok": true, "msg": "stdout client" },
    "version": "dev"
  }
}
```

`/readyz` includes schema groups:

- `foundation`
- `funding`
- `distribution`
- `multi_currency`

If a required table is missing, `/readyz` returns `503` with missing tables and
a migration hint for the affected group. Missing-table runtime errors now return
`SCHEMA_NOT_READY` with the same instruction to check `/readyz`.

## Authentication Checks

| Check | Expected | Observed |
| --- | --- | --- |
| `GET /admin/finance/reconciliation/metrics` without API key | Reject | `401` |
| Same endpoint with admin API key | Allow | `200` |
| Protected partner endpoints without API key | Reject | `401` |
| Protected partner endpoints with partner API key and empty body | Validate body | `422` |

The worker endpoint uses `x-worker-secret`. The running local app did not accept the test value, so authenticated worker smoke testing should be done only with the current local `WORKER_SECRET`.

## Key Request Shapes

### `POST /v1/progress`

Required:

- `referralTrackId`
- `eventType`

Optional:

- `product`
- `subProduct`
- `refereeUCN`
- `accountNumber`
- `meta`
- `sourceSystem`
- `sourceEventId`

### `POST /rewards/apply`

Required:

- `referral_track_id`
- `beneficiary_type`
- `beneficiary_ref`
- `reward_type`
- `product`
- `amount`

Optional/defaulted:

- `sub_product`
- `reward_source` default `BASE`
- `mission_code`
- `status` default `APPLIED`

### `POST /referrals/codes`

Required:

- `referrer_ucn`
- `sticker`
- `tenant`
- `segment`
- `acceptedTerms`

Optional:

- `preferred_handle`

### `POST /referrals/bootstrap`

Required:

- `referrerUcn`
- `tenantCode`

## Next Runtime Checks

1. Use known-safe local test data to create or locate a referral track.
2. Send progress events against that known referral track.
3. Send IDS/Hogan-style events through the intended ingestion path.
4. Confirm rewards are applied only after journey rules are satisfied.
5. Run worker endpoint checks with the local `WORKER_SECRET`.

## Distribution Marketplace Runtime Check

Distribution marketplace smoke testing is documented in:

- `docs/DISTRIBUTION_MARKETPLACE_SMOKE_TEST.md`

Read-only local check:

```powershell
.\.venv_codex\Scripts\python.exe scripts\distribution_marketplace_smoke.py
```

Migration readiness check:

```powershell
.\.venv_codex\Scripts\python.exe scripts\check_distribution_migrations.py
```

IDS/Hogan note:

- IDS/Hogan ingestion now uses `enterprise_event_inbox`.
- Local live IDS testing was run after applying `dp/migrations/061_enterprise_event_inbox.sql`.
- `enterprise_events` is now a compatibility view over `enterprise_event_inbox`.

## Live Business Flow Check

Smoke data used:

- Referrer UCN: `90020260610135539`
- Referral track id: `b06328c5-5906-4a79-a633-3dc7b83ec6fe`
- Source system: `SMOKE_TEST`

Observed flow:

| Step | Result |
| --- | --- |
| Issue referral code | Created |
| Validate referral code | `VALIDATED` |
| Capture referee UCN | Captured |
| Post progress event | Recorded and queued to `local_events.jsonl` |
| Worker processes `UCN_CAPTURED` | Progress moved to 20% |
| Worker processes `ACCOUNT_OPENED` | Progress moved to 40% |
| Worker processes `ACCOUNT_ACTIVATED` | Progress moved to 60% |
| Worker processes `FUNDED` | Progress moved to 80% |
| Worker processes switch event | Progress moved to 100% |

Final read model:

```json
{
  "totalReferrals": 1,
  "completedReferralsCount": 1,
  "inProgressReferralsCount": 0,
  "hasActiveReferrals": false,
  "progressPercent": 100,
  "currentMilestone": "Journey complete",
  "nextMilestone": null
}
```

Runtime issues found and fixed:

- `GET /v1/referrers/{referrerUcn}` was calling an async service from a sync route, causing a live `500`.
- Progress events were recorded but not queued because `enqueue_event(...)` was async and not awaited.
- Local/SQS/Kafka worker paths called the async journey handler without awaiting it.

Completion read-model note:

- Completed referrals are presented with `"status": "COMPLETED"` in the progress API.
- The stored journey milestone can still remain at the last core milestone, such as `FUNDED`, for audit/replay purposes.

## Live IDS/Hogan Inbox Check

Smoke data used:

- Referrer UCN: `9906108110246011`
- Referral track id: `6818c2e8-25e4-4d9f-8fa2-3abbb2a6ed7f`
- Source system: `HOGAN`

Observed flow:

| Step | Result |
| --- | --- |
| Non-qualifying Hogan event | Stored in `enterprise_event_inbox` as `IGNORED` |
| Qualifying Hogan `ACCOUNT_ACTIVATED` before prerequisites | Stored and queued, but journey did not advance out of order |
| Worker processes setup milestones `UCN_CAPTURED` and `ACCOUNT_OPENED` | Referral advanced to expected prior state |
| Qualifying Hogan `ACCOUNT_ACTIVATED` after prerequisites | Stored as `QUEUED`, normalized, worker processed successfully |

Final read model for the IDS smoke referral:

```json
{
  "progressPercent": 60,
  "currentMilestone": "Account activated",
  "nextMilestone": "FUNDED",
  "status": "ACCOUNT_ACTIVATED"
}
```

Runtime issue found and fixed:

- IDS/Hogan timestamps can arrive as ISO strings such as `2026-06-10T12:00:00Z`; the consumer now parses these before inserting into `TIMESTAMPTZ`.
