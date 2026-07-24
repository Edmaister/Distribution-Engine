# Referral SaaS Selected-Customer Mutation Physical Verification

Task: TASK-272
Status: Complete
Date: 2026-07-24
Product boundary: Referral SaaS

## Purpose

Record local physical evidence that an existing selected customer can complete
the guarded campaign mutation path through campaign setup, policy/settings,
review, activation posture, referral code issue, referral validation, campaign
reporting, and export preview.

This verification uses existing Referral SaaS selected-customer APIs. It does
not add schema, runtime API behavior, frontend screens, webhook delivery,
credential creation, invitation delivery, membership activation, export
persistence, billing, or money movement.

## Environment

- Base URL: `http://127.0.0.1:8000`
- API key: `test-admin-key`
- Health check: passed with DB status `ok`
- Selected customer:
  - Account name: `test-referral-fnb-002`
  - Account ref: `389eb0e5-7f27-4ed8-812f-d670f3a34cba`
  - External tenant reference: `test-fnb-sa-002`
  - Organisation reference: `test-referral-fnb-002`

## Command

```powershell
C:\Users\Carla\anaconda3\python.exe scripts\referral_saas_selected_customer_mutation_e2e_physical_check.py --base-url http://127.0.0.1:8000 --admin-key test-admin-key --external-tenant-ref test-fnb-sa-002
```

## Result

Status: `passed`

Created campaign:

- Campaign code:
  `RS_TEST_FNB_SA_002_TEST_REFERRA_VISVGX-REFERRAL-SAAS-PHYSICAL-PROOF-TASK-271-MUTATION-PROOF-178491-EE526BD2`
- Name: `TASK-271 Mutation Proof 1784915845`
- Segment: `Referral SaaS physical proof`

Issued referral code:

- `D2T8V5PCMG`

## API Checks

| Check | HTTP status |
|---|---:|
| Campaign create | 200 |
| Policy/settings | 200 |
| Review submission | 200 |
| Review decision | 200 |
| Campaign activation | 200 |
| Referral code issue | 201 |
| Referral validation | 200 |
| Campaign report | 200 |
| Export preview | 200 |

## Guardrail Evidence

| Guardrail | Result |
|---|---|
| Campaign mutation limited to setup, policy, review, and activation | Passed |
| Link/code mutation limited to issue and validation | Passed |
| No invitation delivery | Passed |
| No membership activation | Passed |
| No credential creation | Passed |
| No webhook delivery | Passed |
| No export creation | Passed |
| No storage or delivery job | Passed |
| No billing or money movement | Passed |
| No internal tenant-scope key leakage | Passed |

## Conclusion

TASK-272 closes the selected-customer mutation execution evidence gap that
remained after TASK-271. The Referral SaaS customer-scoped campaign path is now
physically proven locally from campaign setup through referral code validation
and report/export preview.

Remaining launch-readiness gaps are now narrower:

- persisted export storage, audit, and download workflow
- support-case persistence and repair/replay guardrails
- progress/attribution mutation proof beyond campaign/report preview
