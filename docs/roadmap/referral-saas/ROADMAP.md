# Referral Management and Campaign Attribution SaaS Roadmap

## Objective

Productize the existing referral management and campaign attribution
capabilities into a focused SaaS product before broad DLaaS expansion.

## Current Foundation

Already present in source code:

- referral code creation and reuse
- accepted-terms enforcement
- referral code validation
- referral instance creation
- QR scan evidence
- referee UCN capture
- progress event ingestion
- journey and identifier validation
- dedupe keys and event payload hashes
- campaign creation and validation
- campaign track updates
- campaign policy read/write
- campaign attribution records and track events
- campaign readiness checks
- canonical link/code inspection
- role-specific frontend and API surfaces
- relevant unit, service, API, and journey tests

## Roadmap Themes

### 1. SaaS Account Packaging

Goal: wrap existing tenant-scoped behavior in a product-ready SaaS account
model.

Needed:

- account/company setup
- user membership and roles
- tenant setup checklist
- basic plan/limit gates
- external references that do not expose internal `tenant_code`
- tenant isolation verification

### 2. Campaign Productization

Goal: make campaign setup feel like one coherent SaaS workflow.

Needed:

- campaign draft/setup UX
- readiness gates before activation
- attribution window settings
- policy version visibility
- campaign lifecycle status for users
- campaign reporting defaults

### 3. Referral Link And Code Hardening

Goal: turn existing referral code/link behavior into a complete product
workflow.

Needed:

- documented public API contract
- lifecycle actions such as revoke, expire, and reissue where required
- safe operator investigation flow
- audit consistency for sensitive actions
- frontend handling for validation failure and recovery states

### 4. Attribution Trace Product

Goal: unify existing campaign attribution, progress events, campaign links, and
route links into an explainable attribution trace.

Needed:

- attribution trace response contract
- attribution windows and precedence rules
- conflict/missing-evidence handling
- override policy and audit evidence
- tenant-safe attribution reporting

### 5. SaaS Operations

Goal: make the focused product supportable and production-ready.

Needed:

- tenant-safe reporting and exports
- support dashboard for failed validation and missing evidence
- event replay posture and safe retry classes
- observability and smoke checks
- live DB/state verification
- full golden-path and failure-path E2E tests

## 10/10 Gap Matrix

The current focused gap matrix is:

- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`

It classifies the remaining work as SaaS packaging and hardening, not
greenfield referral construction.

## Recommended Ordered Task Sequence

1. TASK-134: Define Referral SaaS account setup contract.
2. TASK-135: Productize Referral SaaS campaign setup and readiness contract.
3. TASK-136: Harden Referral SaaS referral code issue contract.
4. TASK-137: Harden Referral SaaS validation and recovery contract.
5. TASK-138: Productize Referral SaaS progress event contract.
6. TASK-139: Define Referral SaaS attribution trace contract.
7. TASK-147: Define Referral SaaS E2E and live verification plan.
8. TASK-140: Add Referral SaaS operator link/code investigation contract.
9. TASK-141: Define Referral SaaS safe status contract.
10. TASK-142: Define Referral SaaS reporting and export contract.
11. TASK-143: Create Referral SaaS public API contract map.
12. TASK-144: Define Referral SaaS frontend IA and workflow contract.
13. TASK-145: Define Referral SaaS operator support workflow.
14. TASK-146: Inventory Referral SaaS audit and idempotency posture.
15. TASK-149: Add Referral SaaS local golden-path contract test.
16. TASK-150: Add Referral SaaS negative contract test coverage.
17. TASK-151: Inventory Referral SaaS mounted route smoke surface.
18. TASK-152: Add Referral SaaS read-only schema/status checker.
19. TASK-153: Add Referral SaaS route smoke plan generator.
20. TASK-154: Add Referral SaaS safe-status/reporting contract test.
21. TASK-155: Add Referral SaaS safe-status projection helper.
22. TASK-156: Add Referral SaaS report catalog helper.
23. TASK-157: Add Referral SaaS report API wrapper.
24. TASK-158: Add Referral SaaS report account-scope resolver.
25. TASK-159: Add Referral SaaS referral funnel report helper.
26. TASK-160: Add Referral SaaS progress event health report.
27. TASK-161: Add Referral SaaS attribution quality report.
28. TASK-162: Add Referral SaaS safe-status distribution report.
29. TASK-163: Add Referral SaaS link/code performance report.
30. TASK-164: Add Referral SaaS reward visibility summary report.
31. TASK-165: Add Referral SaaS export validation gate.
32. TASK-166: Carry Referral SaaS account references through report scope.
33. TASK-167: Add Referral SaaS inline export preview payload.
34. TASK-168: Add Referral SaaS report/export frontend client.
35. TASK-169: Add Referral SaaS report catalog frontend surface.
36. TASK-170: Add Referral SaaS account setup readiness frontend surface.
37. TASK-171: Add Referral SaaS inline export preview frontend surface.
38. TASK-172: Add Referral SaaS campaign readiness frontend surface.
39. TASK-173: Add Referral SaaS link/code workflow frontend surface.
40. TASK-174: Add Referral SaaS link/code product API wrappers.
41. TASK-175: Add Referral SaaS validation recovery mapper.
42. TASK-176: Expose Referral SaaS validation idempotency posture.
43. TASK-177: Add Referral SaaS validation recovery UI.
44. TASK-178: Add Referral SaaS operator link/code inspect API wrapper.
45. TASK-179: Add Referral SaaS operator link/code inspect frontend surface.
46. TASK-180: Add Referral SaaS operator attribution trace API wrapper.
47. TASK-181: Add Referral SaaS operator attribution trace frontend surface.
48. TASK-182: Add Referral SaaS operator progress/status diagnostics API wrapper.
49. TASK-183: Add Referral SaaS operator progress/status frontend surface.
50. TASK-184: Add Referral SaaS operator support workflow hub.
51. TASK-185: Add Referral SaaS focused workspace shell.
52. TASK-186: Add Referral SaaS workspace and account setup testing guidance.

## 10/10 Exit Criteria

- A new tenant can onboard, configure a campaign, issue/validate referral links
  or codes, ingest progress events, and see attribution status without manual DB
  intervention.
- Operators can investigate link/code, validation, progress, and attribution
  failures from safe evidence.
- Referrer/customer surfaces show safe status and next action without leaking
  internal states.
- Public APIs have clear auth, idempotency, error, and schema contracts.
- Reports are tenant-safe and reconcile to source event evidence.
- Live DB/state verification has been completed for all launch-critical tables,
  constraints, statuses, and smoke routes.

## Completed Contract Outputs

- TASK-134: `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_CONTRACT.md`
- TASK-135: `docs/sa/referral-saas/REFERRAL_SAAS_CAMPAIGN_SETUP_READINESS_CONTRACT.md`
- TASK-136: `docs/sa/referral-saas/REFERRAL_SAAS_REFERRAL_CODE_ISSUE_CONTRACT.md`
- TASK-137: `docs/sa/referral-saas/REFERRAL_SAAS_VALIDATION_RECOVERY_CONTRACT.md`
- TASK-138: `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_EVENT_CONTRACT.md`
- TASK-139: `docs/sa/referral-saas/REFERRAL_SAAS_ATTRIBUTION_TRACE_CONTRACT.md`
- TASK-147: `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`
- TASK-140: `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_LINK_CODE_INVESTIGATION_CONTRACT.md`
- TASK-141: `docs/sa/referral-saas/REFERRAL_SAAS_SAFE_STATUS_CONTRACT.md`
- TASK-142: `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`
- TASK-143: `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`
- TASK-144: `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`
- TASK-145: `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`
- TASK-146: `docs/sa/referral-saas/REFERRAL_SAAS_AUDIT_IDEMPOTENCY_POSTURE.md`

## Completed Implementation Outputs

- TASK-149: `test/test_referral_saas_golden_path_contract.py`
- TASK-150: `test/test_referral_saas_golden_path_contract.py`
- TASK-151: `test/test_referral_saas_route_smoke_inventory.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`
- TASK-152: `scripts/referral_saas_schema_status_check.py`;
  `test/test_referral_saas_schema_status_check.py`
- TASK-153: `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_route_smoke_plan.py`
- TASK-154: `test/test_referral_saas_status_reporting_contract.py`
- TASK-155: `services/referral_saas_safe_status_service.py`;
  `test/test_referral_saas_safe_status_service.py`
- TASK-156: `services/referral_saas_reporting_service.py`;
  `test/test_referral_saas_reporting_service.py`
- TASK-157: `apps/api/routers/referral_saas_reports.py`;
  `test/api/test_referral_saas_reports_api.py`
- TASK-158: `services/referral_saas_account_scope_service.py`;
  `test/test_referral_saas_account_scope_service.py`
- TASK-159: `services/referral_saas_reporting_service.py`;
  `test/test_referral_saas_reporting_service.py`
- TASK-160: `services/referral_saas_reporting_service.py`;
  `test/test_referral_saas_reporting_service.py`
- TASK-161: `services/referral_saas_reporting_service.py`;
  `test/test_referral_saas_reporting_service.py`
- TASK-162: `services/referral_saas_reporting_service.py`;
  `test/test_referral_saas_reporting_service.py`
- TASK-163: `services/referral_saas_reporting_service.py`;
  `test/test_referral_saas_reporting_service.py`
- TASK-164: `services/referral_saas_reporting_service.py`;
  `test/test_referral_saas_reporting_service.py`
- TASK-165: `services/referral_saas_reporting_service.py`;
  `apps/api/routers/referral_saas_reports.py`;
  `test/test_referral_saas_reporting_service.py`;
  `test/api/test_referral_saas_reports_api.py`
- TASK-166: `services/referral_saas_account_scope_service.py`;
  `apps/api/routers/referral_saas_reports.py`;
  `test/test_referral_saas_account_scope_service.py`;
  `test/api/test_referral_saas_reports_api.py`
- TASK-167: `services/referral_saas_reporting_service.py`;
  `apps/api/routers/referral_saas_reports.py`;
  `test/test_referral_saas_reporting_service.py`;
  `test/api/test_referral_saas_reports_api.py`
- TASK-168: `frontend/src/api/endpoints/referralSaasReports.ts`;
  `frontend/src/api/endpoints/referralSaasReports.test.ts`
- TASK-169: `frontend/src/pages/admin/ReferralSaasReportsPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasReportsPage.test.tsx`;
  `frontend/src/api/referralSaasQueries.ts`
- TASK-170: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `frontend/src/api/referralSaasAccountQueries.ts`
- TASK-171: `frontend/src/pages/admin/ReferralSaasReportsPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasReportsPage.test.tsx`
- TASK-172: `frontend/src/pages/admin/ReferralSaasCampaignReadinessPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasCampaignReadinessPage.test.tsx`;
  `frontend/src/api/endpoints/adminCampaignReadiness.ts`;
  `frontend/src/api/referralSaasCampaignQueries.ts`
- TASK-173: `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.test.tsx`
- TASK-174: `apps/api/routers/referral_saas_links.py`;
  `test/api/test_referral_saas_links_api.py`;
  `frontend/src/api/endpoints/referralSaasLinks.ts`;
  `frontend/src/api/endpoints/referralSaasLinks.test.ts`
- TASK-175: `services/referral_saas_validation_service.py`;
  `test/test_referral_saas_validation_service.py`;
  `apps/api/routers/referral_saas_links.py`
- TASK-176: `services/referral_saas_validation_service.py`;
  `test/test_referral_saas_validation_service.py`;
  `test/api/test_referral_saas_links_api.py`
- TASK-177: `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasLinkCodeWorkflowPage.test.tsx`
- TASK-178: `apps/api/routers/referral_saas_links.py`;
  `test/api/test_referral_saas_links_api.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`
- TASK-179: `frontend/src/api/endpoints/referralSaasLinks.ts`;
  `frontend/src/api/endpoints/referralSaasLinks.test.ts`;
  `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.test.tsx`;
  `frontend/src/app/App.tsx`;
  `frontend/src/layout/Sidebar.tsx`
- TASK-180: `apps/api/routers/referral_saas_links.py`;
  `test/api/test_referral_saas_links_api.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`
- TASK-181: `frontend/src/api/endpoints/referralSaasLinks.ts`;
  `frontend/src/api/endpoints/referralSaasLinks.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAttributionTracePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAttributionTracePage.test.tsx`;
  `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.test.tsx`;
  `frontend/src/app/App.tsx`;
  `frontend/src/layout/Sidebar.tsx`
- TASK-182: `apps/api/routers/referral_saas_links.py`;
  `test/api/test_referral_saas_links_api.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`
- TASK-183: `frontend/src/api/endpoints/referralSaasLinks.ts`;
  `frontend/src/api/endpoints/referralSaasLinks.test.ts`;
  `frontend/src/pages/admin/ReferralSaasProgressStatusPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasProgressStatusPage.test.tsx`;
  `frontend/src/pages/admin/ReferralSaasAttributionTracePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAttributionTracePage.test.tsx`;
  `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.test.tsx`;
  `frontend/src/app/App.tsx`;
  `frontend/src/layout/Sidebar.tsx`
- TASK-184: `frontend/src/pages/admin/ReferralSaasSupportHubPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasSupportHubPage.test.tsx`;
  `frontend/src/pages/admin/ReferralSaasProgressStatusPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasProgressStatusPage.test.tsx`;
  `frontend/src/pages/admin/ReferralSaasAttributionTracePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAttributionTracePage.test.tsx`;
  `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasOperatorLinkInspectPage.test.tsx`;
  `frontend/src/app/App.tsx`;
  `frontend/src/layout/Sidebar.tsx`
- TASK-185: `frontend/src/pages/admin/ReferralSaasWorkspacePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasWorkspacePage.test.tsx`;
  `frontend/src/layout/Sidebar.tsx`;
  `frontend/src/layout/Sidebar.test.tsx`;
  `frontend/src/app/App.tsx`;
  `frontend/src/layout/AppShell.tsx`
- TASK-186: `frontend/src/pages/admin/ReferralSaasWorkspacePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasWorkspacePage.test.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`

## Explicit Deferrals

The following are DLaaS expansion work, not blockers for this SaaS roadmap:

- distributor marketplace depth
- commission settlement
- funding operations
- fulfilment provider routing
- settlement batches
- sponsor billing
- white-label/embed
