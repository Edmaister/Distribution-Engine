# Referral SaaS SA Notes

This folder contains solution-analysis outputs for the Referral Management and
Campaign Attribution SaaS product boundary.

These documents must not redefine DLaaS-wide scope. They should focus on the
first SaaS wedge and keep DLaaS expansion items clearly marked as deferrals.

## Documents

- `REFERRAL_SAAS_GAP_MATRIX.md` - focused 10/10 gap matrix and task sequence.
- `REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md` - TASK-134 account setup contract.
- `REFERRAL_SAAS_CAMPAIGN_SETUP_READINESS_CONTRACT.md` - TASK-135 campaign
  setup and readiness contract.
- `REFERRAL_SAAS_REFERRAL_CODE_ISSUE_CONTRACT.md` - TASK-136 referral code
  issue/get-or-create contract.
- `REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md` - TASK-137 validation and
  recovery contract.
- `REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md` - TASK-138 progress event
  ingestion contract.
- `REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md` - TASK-139 attribution trace
  contract.
- `REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md` - TASK-147 E2E and live
  verification plan.
- `REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md` - TASK-140
  operator link/code investigation contract.
- `REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md` - TASK-141 referrer/customer safe
  status contract.
- `REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md` - TASK-142 reporting and export
  contract.
- `REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md` - TASK-143 public API contract
  map.
- `REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md` - TASK-144 frontend IA and
  workflow contract.
- `REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md` - TASK-145 operator support
  workflow contract.
- `REFERRAL_SAAS_AUDIT_IDEMPOTENCY_POSTURE.md` - TASK-146 audit and
  idempotency posture inventory.
- `REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md` - TASK-151 source-backed route
  smoke inventory.

## Implementation Notes

- TASK-156 adds `services/referral_saas_reporting_service.py` as the first
  Referral SaaS report catalog helper. It supports `campaign_performance` over
  the existing tenant-safe analytics foundation and keeps future report types
  and exports explicitly unimplemented.
- TASK-157 adds `GET /v1/referral-saas/reports/{report_type}` as the first
  bounded read-only product API wrapper over the report catalog helper. It does
  not implement exports, frontend screens, SaaS account membership resolution,
  or broader product route families.
- TASK-158 adds a narrow account-scope resolver for the report API. Tenant-scoped
  identities can omit `tenant_code`; internal report readers still need explicit
  tenant scope until full SaaS account membership exists.
- TASK-159 adds `referral_funnel` as the second bounded report type over the
  same tenant-safe analytics foundation. It exposes safe funnel metrics with a
  partial-source warning until dedicated code-issued, validation-state, and
  progress-milestone report sources are implemented.
- TASK-160 adds `progress_event_health` as the third bounded report type. It
  reads tenant-scoped `referral_progress_events` and `referral_event_failures`
  evidence, excludes unscoped failure rows, and keeps deduped/rejected counts
  as partial coverage until those states are persisted in reportable form.
- TASK-161 adds `attribution_quality` as the fourth bounded report type. It
  derives aggregate complete, partial, missing-evidence, inconsistent, and
  unattributed counts from tenant-scoped referral, campaign-link, and route-link
  evidence without exposing raw trace payloads.
