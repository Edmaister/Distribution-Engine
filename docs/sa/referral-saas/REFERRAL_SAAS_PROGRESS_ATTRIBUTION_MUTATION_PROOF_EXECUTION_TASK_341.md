# Referral SaaS Progress And Attribution Mutation Proof Execution

Task: TASK-341
Status: Complete
Product boundary: Referral SaaS
Execution date: 2026-08-03

## Boundary

Required boundary docs checked:

- `AGENTS.md`
- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_ATTRIBUTION_MUTATION_PROOF_CONTRACT.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

Source duplication: No.

## Environment

Approved local environment:

- API base URL: `http://127.0.0.1:8000`
- Selected customer external reference: `task-206-local-206b`
- Selected customer account reference: `88c83466-142c-4856-8cf6-899ff3cbb549`
- Selected customer organisation reference: `org-task-206-local-206b`
- Tenant scope used by progress primitive: `FNB`
- Admin key: local test admin key
- Progress key: local test partner key

The runner uses separate admin and progress credentials because selected
customer setup/readback routes are admin-scoped while `/v1/progress` is
partner-scoped.

## Command

```powershell
.\.venv\Scripts\python.exe scripts\referral_saas_progress_attribution_physical_check.py `
  --base-url http://127.0.0.1:8000 `
  --admin-key test-admin-key `
  --progress-key test-partner-key `
  --tenant-code FNB `
  --external-tenant-ref task-206-local-206b `
  --suffix task341local007
```

## Result

The proof passed.

```json
{
  "status": "passed",
  "proof_suffix": "task341local007",
  "selected_customer": {
    "accountName": "org-task-206-local-206b",
    "accountRef": "88c83466-142c-4856-8cf6-899ff3cbb549",
    "externalTenantRef": "task-206-local-206b",
    "organisationRef": "org-task-206-local-206b"
  },
  "referral_track_id": "683a9a34-f5b0-4b5d-827a-ae75ac9bb648",
  "issued_referral_code": "GQZHVVVP48",
  "progress_events": {
    "first": {
      "status": 201,
      "eventType": "UCN_CAPTURED",
      "sourceEventId": "task-340-ucn-captured-task341local007",
      "deduped": false
    },
    "replay": {
      "status": 200,
      "eventType": "UCN_CAPTURED",
      "sourceEventId": "task-340-ucn-captured-task341local007",
      "deduped": true
    },
    "later": {
      "status": 201,
      "eventType": "ACCOUNT_OPENED",
      "sourceEventId": "task-340-account-opened-task341local007",
      "deduped": false
    }
  },
  "identity_capture": {
    "status": 200,
    "captureStatus": "CAPTURED"
  },
  "readbacks": {
    "progress_status": 200,
    "attribution_trace": 200,
    "campaign_report": 200,
    "trace_status": "PARTIAL"
  }
}
```

The attribution trace returned `PARTIAL`, which is an allowed safe proof state
under the TASK-339 contract because the current environment does not provide all
optional reward, commission, funding, fulfilment, settlement, audit, and webhook
source evidence for this proof referral. The trace endpoint returned controlled
missing-evidence posture rather than a silent empty trace or cross-customer
fallback.

## Defects Found And Fixed

The first live execution exposed two real integration issues:

- `/v1/progress` requires partner credentials while selected-customer setup and
  readback routes require admin credentials. The runner now accepts
  `--progress-key` so the proof uses the correct credential boundary.
- The outcome trace service compared text-backed reward/funding/fulfilment
  references to a UUID parameter in some joined evidence queries. The trace
  service now casts those text comparisons explicitly and the regression test
  locks that behavior.

The progress API route also now returns controlled service-layer 4xx responses
instead of masking them as response-model 500s.

## No-Adjacent-Action Confirmations

The runner confirmed:

- no provider call
- no webhook delivery
- no invitation delivery
- no credential creation
- no auth-claim change
- no login activation
- no billing or money movement
- no DLaaS marketplace mutation

## Launch Readiness Impact

TASK-341 closes the local selected-customer progress/attribution mutation proof
gap. Remaining launch-hardening items stay separate:

- repeat the proof against staging or production-like data
- governed provider/vault runtime execution
- governed auth/login completion
- governed repair/replay command execution
