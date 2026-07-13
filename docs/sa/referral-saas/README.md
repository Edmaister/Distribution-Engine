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
  partial-source warning until dedicated validation-state and
  progress-milestone report sources are implemented.
- TASK-160 adds `progress_event_health` as the third bounded report type. It
  reads tenant-scoped `referral_progress_events` and `referral_event_failures`
  evidence, excludes unscoped failure rows, and keeps deduped/rejected counts
  as partial coverage until those states are persisted in reportable form.
- TASK-161 adds `attribution_quality` as the fourth bounded report type. It
  derives aggregate complete, partial, missing-evidence, inconsistent, and
  unattributed counts from tenant-scoped referral, campaign-link, and route-link
  evidence without exposing raw trace payloads.
- TASK-162 adds `safe_status_distribution` as the fifth bounded report type. It
  derives aggregate product/safe status counts from tenant-scoped referral
  outcome evidence using the Referral SaaS safe-status vocabulary without
  exposing raw viewer, UCN, reward, audit, provider, or money evidence.
- TASK-163 adds `link_code_performance` as the sixth bounded report type. It
  reads durable referral code, campaign code, campaign-referral link, and
  route-referral link evidence for tenant-safe aggregate counts without
  exposing raw UCNs, raw link payloads, composite-code compatibility internals,
  reward, funding, fulfilment, settlement, wallet, commission, or invoice
  evidence.
- TASK-164 adds `reward_visibility_summary` as the seventh bounded report type.
  It reads persisted reward rows and pending mission bonus evidence for
  tenant-safe status/source/beneficiary/product counts only. It deliberately
  excludes reward amount totals, beneficiary references, fulfilment, funding,
  settlement, wallet, commission, invoice, payout, and broader money evidence.
- TASK-165 adds a validation-only export gate for current Referral SaaS report
  requests. It validates supported report types, `json`/`csv` formats,
  `tenant_safe` redaction, approved dimensions/filters, row limits, and data
  windows without creating export files, storage records, delivery jobs, audit
  rows, scheduled exports, or any money/reporting mutations.
- TASK-166 carries trusted `account_ref` and `external_tenant_ref` identity
  claims through the report/export account-scope envelope. It does not add
  account tables, membership resolution, external-reference persistence, or
  caller-supplied account-ref authorization.
- TASK-167 adds side-effect-free inline export previews for current report
  outputs. It returns JSON rows or CSV text plus metadata without creating
  export IDs, files, storage records, delivery jobs, audit rows, retention
  records, download URLs, or scheduled exports.
- TASK-168 adds the first frontend API client seam for Referral SaaS report,
  export validation, and export preview calls. It does not add a report screen,
  persisted export UX, account membership UI, or new backend behavior.
- TASK-169 adds a focused admin frontend surface for the Referral SaaS report
  catalog. It renders tenant-safe metrics, freshness, warnings, redactions,
  account-scope posture, and export-preview guardrails without adding persisted
  export UX, account membership UI, backend behavior, schema, or money flows.
- TASK-170 adds a focused admin frontend surface for Referral SaaS account
  setup readiness. It consumes existing onboarding readiness evidence through
  external references and links the account, membership, campaign, and report
  setup path without adding account tables, membership writes, backend routes,
  schema, tenant-link persistence, or money flows.
- TASK-171 adds inline JSON/CSV export preview actions to the focused Referral
  SaaS report catalog. It consumes the existing preview endpoint and shows
  preview status, content type, row count, and payload evidence without adding
  export IDs, stored files, download actions, scheduled exports, audit writes,
  backend routes, schema, or money flows.
- TASK-172 adds a focused admin frontend surface for Referral SaaS campaign
  readiness. It consumes the existing read-only admin campaign readiness
  endpoint, renders the four first-launch operations from TASK-135, and shows
  setup checklist, lifecycle, blockers, warnings, and safe campaign/policy
  evidence without adding campaign creation, policy writes, activation,
  link/code generation, backend routes, schema, marketplace, or money flows.
- TASK-173 adds a focused admin frontend surface for Referral SaaS link/code
  workflow execution. It reuses the existing referral code issue, public
  validation, and referee UCN capture client calls, renders only whitelisted
  result fields, and keeps reissue, revoke, expire, repair, replay, reward,
  money, backend route, schema, and DLaaS expansion behavior out of scope.
- TASK-174 adds bounded `/v1/referral-saas` product API wrappers for referral
  code issue/reuse, public referral validation, and referee UCN capture. The
  wrappers compose existing referral primitives, derive partner tenant scope
  from identity where protected, return product-shaped safe statuses, redact
  raw UCN/hash/internal attribute evidence, and keep lifecycle commands,
  schema, audit writes, reward, money, and DLaaS expansion out of scope.
- TASK-175 adds a dedicated Referral SaaS validation recovery mapper over the
  existing product validation wrapper. It centralizes product status and safe
  recovery mapping for terms, alias, missing-code, code-not-found, and logging
  recovery states, keeps internal validation attributes redacted, and leaves
  duplicate-submit idempotency, operator trace linkage, schema, lifecycle,
  audit, reward, money, and DLaaS expansion behavior out of scope.
- TASK-176 exposes the current public validation idempotency posture in the
  product validation response. It states that successful duplicate submits
  currently create new validation journeys and that idempotency keys are not
  supported until a schema-backed duplicate/reuse contract is implemented.
- TASK-177 shows product validation recovery and retry posture in the focused
  Referral SaaS link/code workflow UI. It renders safe recovery next action and
  non-idempotent retry evidence from the product wrapper without exposing raw
  validation attributes, UCNs, hashes, reward, money, or DLaaS internals.
- TASK-178 adds a read-only Referral SaaS operator link/code inspection API
  wrapper over the existing `inspect_link_code` primitive. It preserves
  redactions, missing evidence, source warnings, evidence toggling, and safe
  validation errors, adds product `nextDiagnostics`, and does not issue,
  resolve, mutate, retry, replay, repair, reward, fund, fulfil, settle, or
  generate codes.
- TASK-179 adds the focused Referral SaaS operator link/code inspection
  frontend surface at `/admin/referral-saas/operator-links`. It calls the
  TASK-178 product wrapper, renders safe source summary, campaign/participant
  and attribution identifiers, missing evidence, source warnings, redactions,
  and next diagnostics, and keeps raw evidence, support-case writes, mutation,
  retry/replay/repair, reward, money, and DLaaS behavior out of scope.
- TASK-180 adds the read-only Referral SaaS operator attribution trace API
  wrapper at `/v1/referral-saas/operator/outcomes/{referral_track_id}/trace`.
  It composes the existing outcome trace primitive, limits first-launch product
  sections to outcome, attribution, participants, events, and audit, rejects
  reward/commission/funding/fulfilment/settlement/webhook sections, and keeps
  trace UI, repair/replay, support-case writes, reward, money, and DLaaS
  behavior out of scope.
- TASK-181 adds the focused Referral SaaS operator attribution trace frontend
  surface at `/admin/referral-saas/attribution-trace`. It calls the TASK-180
  product wrapper, renders safe trace summary, attribution links, participants,
  events, audit evidence, missing evidence, source warnings, redactions, and
  next diagnostics, links from the operator link/code inspection surface, and
  keeps money/webhook evidence, mutation controls, support-case writes,
  repair/replay/retry, reward, money, and DLaaS behavior out of scope.
- TASK-182 adds the read-only Referral SaaS operator progress/status API
  wrapper at
  `/v1/referral-saas/operator/referrals/{referral_track_id}/progress-status`.
  It composes the existing dashboard progress read and Referral SaaS
  safe-status projection helper, returns safe progress, redactions, missing
  evidence, and next diagnostics, and keeps progress ingestion mutation,
  support-case writes, repair/replay/retry, reward, money, and DLaaS behavior
  out of scope.
- TASK-183 adds the focused Referral SaaS operator progress/status frontend
  surface at `/admin/referral-saas/progress-status`. It calls the TASK-182
  product wrapper, renders safe progress, safe status copy, action posture,
  missing evidence, redactions, and next diagnostics, links from adjacent
  operator support surfaces, and keeps progress mutation, support-case writes,
  repair/replay/retry, reward, money, and DLaaS behavior out of scope.
- TASK-184 adds the focused Referral SaaS operator support workflow hub at
  `/admin/referral-saas/support`. It routes common validation, progress,
  link/code, attribution, readiness, and reporting support cases into existing
  read-only product surfaces, shows evidence order and mutation guardrails, and
  keeps support-case writes, repair/replay/retry, reward, money, and DLaaS
  behavior out of scope.
