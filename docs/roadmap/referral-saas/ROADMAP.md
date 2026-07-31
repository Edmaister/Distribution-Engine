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
53. TASK-187: Stabilize Referral SaaS account setup scope inputs.
54. TASK-188: Clarify Referral SaaS account setup next action.
55. TASK-189: Position Account Setup Readiness inside setup workflow.
56. TASK-190: Define Referral SaaS account setup and maintenance workflow architecture.
57. TASK-191: Define Referral SaaS account setup wrapper contract.
58. TASK-192: Build Account Setup workflow shell using draft/readiness primitives.
59. TASK-193: Connect Account Setup workflow to draft save, validation, submit, and review APIs.
60. TASK-194: Define Account Maintenance workflow contract and read model.
61. TASK-195: Build Account Maintenance read-only shell.
62. TASK-196: Add Account Maintenance draft selector from safe onboarding source.
63. TASK-197: Add account/tenant-link/external-reference schema final review.
64. TASK-198: Add Referral SaaS account foundation migration and contract tests.
65. TASK-199: Add Referral SaaS account foundation read resolver service.
66. TASK-200: Add Referral SaaS account read API wrapper.
67. TASK-201: Wire Account Setup frontend to durable account resolver.
68. TASK-202: Physically verify Account Setup draft save against local app/API/DB.
69. TASK-203: Add Account Setup durable account creation service.
70. TASK-204: Add Referral SaaS account creation API wrapper.
71. TASK-205: Clarify Account Setup parent workflow and Step 1 company profile UX.
72. TASK-206: Physically verify Referral SaaS account creation from reviewed draft.
73. TASK-207: Wire Account Setup UI create action to reviewed-draft account creation.
74. TASK-208: Physically verify full Account Setup UI save-review-create path.
75. TASK-209: Add Referral SaaS membership read boundary.
76. TASK-210: Define Referral SaaS membership invitation write boundary.
77. TASK-211: Add Referral SaaS membership invitation intent API.
78. TASK-212: Wire Account Setup Users and Roles to invitation intent API.
79. TASK-213: Physically verify Account Setup membership invitation intent.
80. TASK-214: Define membership activation and invitation delivery boundary.
81. TASK-215: Clarify Account Setup find-or-start CX copy.
82. TASK-216: Redesign Account Setup as guided wizard.
83. TASK-217: Gate Account Setup wizard navigation by completed steps.
84. TASK-218: Require explicit Account Setup Step 1 account check.
85. TASK-219: Keep Account Setup Company Profile inside the wizard with bounded field controls.
86. TASK-220: Add Account Setup draft conflict recovery UX.
87. TASK-221: Clarify Account Setup contact responsibility field.
88. TASK-222: Load saved Account Setup Company Profile drafts.
89. TASK-223: Clarify Account Setup saved Company Profile next action.
90. TASK-224: Remove People and Roles from Account Setup.
91. TASK-225: Split Technical Setup from Account Setup and align customer identification language.
92. TASK-226: Move full Account Setup readiness evidence to Account Maintenance.
93. TASK-227: Add Account Maintenance durable account selector.
94. TASK-228: Reframe Account Maintenance as a Client Workspace hub.
95. TASK-229: Add Client Workspace physical verification.
96. TASK-230: Add repeatable fresh-client physical seed proof.
97. TASK-231: Reframe Client Workspace as a customer profile landing experience.
98. TASK-232: Start Account Setup from blank customer identifiers with field guidance.
99. TASK-233: Simplify Account Setup Review & Create UX.
100. TASK-234: Remove hidden default account setup owner-scope collision.
101. TASK-235: End Account Setup at Review & Create and route successful creation to Customer Profile.
102. TASK-236: Keep selected-customer access actions inside Customer Profile modules.
103. TASK-237: Add customer-scoped People and Access maintenance flow.
104. TASK-238: Add customer profile settings maintenance command.
105. TASK-239: Fix People and Access email identity, campaign manager role, and error wrapping.
106. TASK-240: Simplify Account Setup customer workspace language.
107. TASK-241: Split Customer Profile modules into customer-scoped pages.
108. TASK-242: Add Referral SaaS membership activation readiness read model.
109. TASK-243: Add Referral SaaS invitation delivery request boundary.
110. TASK-244: Add Referral SaaS technical setup readiness read model.
111. TASK-245: Add Referral SaaS customer technical setup page.
112. TASK-246: Add Referral SaaS invite provider approval readiness.
113. TASK-247: Add Referral SaaS membership recipient readiness.
114. TASK-248: Add Referral SaaS guarded invite delivery UI.
115. TASK-249: Add Referral SaaS membership activation command boundary.
116. TASK-250: Wire selected-customer People and Access activation action.
117. TASK-251: Clarify People and Access person-name placeholder.
118. TASK-252: Add Referral SaaS access provisioning readiness boundary.
119. TASK-253: Add customer-scoped campaign readiness page.
120. TASK-254: Add customer-scoped campaign list and read wrappers.
121. TASK-255: Define customer-scoped campaign draft/create command contract.
122. TASK-256: Add guarded customer-scoped campaign setup create API wrapper.
123. TASK-257: Add selected-customer campaign setup create UX.
124. TASK-258: Define customer-scoped campaign policy/settings command contract.
125. TASK-259: Add guarded customer-scoped campaign policy/settings API wrapper.
126. TASK-260: Add selected-customer campaign policy/settings UX.
127. TASK-261: Define customer-scoped campaign submit/review command contract.
128. TASK-262: Add guarded customer-scoped campaign submit/review API wrappers.
129. TASK-263: Add selected-customer campaign submit/review UX.
130. TASK-264: Define selected-customer campaign activation/go-live command contract.
131. TASK-265: Add guarded selected-customer campaign activation/go-live API wrapper.
132. TASK-266: Wire selected-customer campaign activation action.
133. TASK-267: Continue customer-scoped Links and Codes from activated campaigns.
134. TASK-268: Continue customer-scoped Reports from selected customer context.
135. TASK-269: Add selected-customer E2E physical proof runner.
136. TASK-270: Fix selected-customer E2E proof redaction and report wrapper blockers.
137. TASK-271: Add selected-customer mutation-path E2E physical proof runner.
138. TASK-272: Record selected-customer mutation-path E2E physical proof execution.
139. TASK-273: Persist customer-scoped report export requests.
140. TASK-274: Clarify selected-customer selector, profile header, and health action labels.
141. TASK-275: Fix accepted-access membership activation SQL parameter typing.
142. TASK-276: Add People and Access intent maintenance.
143. TASK-277: Fix People and Access drawer surface opacity.
144. TASK-278: Fix People and Access access-intent idempotency reuse.
145. TASK-279: Add Amplifi Admin manual access acceptance.
146. TASK-280: Refresh People and Access after intent changes.
147. TASK-281: Fix People and Access re-add after remove idempotency.
148. TASK-282: Allow manual accepted access during account setup.
149. TASK-283: Expose People and Access login and seat provisioning next actions.
150. TASK-284: Define Referral SaaS access provisioning command contract.
151. TASK-285: Add guarded Referral SaaS access provisioning API wrapper.
152. TASK-286: Wire People and Access provisioning action to the guarded access provisioning API.
153. TASK-293: Simplify People and Access language and separate optional login setup.
154. TASK-294: Record activated People and Access provisioning proof execution.
155. TASK-295: Define Referral SaaS support case persistence contract.
156. TASK-296: Scope Customer Health account-foundation activation results.
157. TASK-298: Clarify optional Platform login setup positioning.
158. TASK-300: Reframe selected-customer Technical Setup as Integrations.
159. TASK-301: Define customer-scoped Integrations configuration contract.
160. TASK-302: Add customer-scoped Integrations configuration API foundation.
161. TASK-303: Add customer-scoped Integrations configuration UI.
162. TASK-304: Define customer-scoped Integrations live execution contract.
163. TASK-305: Add customer-scoped Integrations execution readiness API.
164. TASK-306: Wire Integrations execution readiness into selected-customer UI.
165. TASK-307: Add governed Integrations API-access verification command.
166. TASK-308: Wire Integrations API-access verification action into selected-customer UI.
167. TASK-309: Add governed Integrations webhook test-dispatch command.
168. TASK-310: Wire Integrations webhook test evidence action.
169. TASK-311: Align Integrations page with Plan Save Verify CX.
170. TASK-312: Add governed Integrations message-provider test-check command.
171. TASK-313: Wire Integrations message-provider check UI.
172. TASK-314: Define Integrations credential lifecycle request contract.
173. TASK-315: Add Integrations credential request API foundation.
174. TASK-316: Wire Integrations credential request UI.

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
- TASK-190:
  `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_MAINTENANCE_WORKFLOW_ARCHITECTURE.md`
- TASK-191:
  `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_WRAPPER_CONTRACT.md`
- TASK-194:
  `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_MAINTENANCE_READ_MODEL_CONTRACT.md`
- TASK-197:
  `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SCHEMA_FINAL_REVIEW.md`
- TASK-210:
  `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_INVITATION_BOUNDARY.md`
- TASK-255:
  `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_CAMPAIGN_CREATE_CONTRACT.md`
- TASK-301:
  `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_INTEGRATIONS_CONFIGURATION_CONTRACT.md`
- TASK-304:
  `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_INTEGRATIONS_LIVE_EXECUTION_CONTRACT.md`
- TASK-314:
  `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_INTEGRATIONS_CREDENTIAL_LIFECYCLE_CONTRACT.md`

## Completed Implementation Outputs

- TASK-302:
  `dp/migrations/087_referral_saas_integrations_configuration.sql`;
  `services/referral_saas_integrations_configuration_service.py`;
  `GET/PUT /v1/referral-saas/accounts/{account_ref}/integrations/configuration`;
  `POST /v1/referral-saas/accounts/{account_ref}/integrations/configuration/validate`.

- TASK-303:
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  selected-customer Integrations read/validate/save UI for safe non-secret
  setup evidence.

- TASK-305:
  `GET /v1/referral-saas/accounts/{account_ref}/integrations/execution-readiness`;
  `services/referral_saas_integrations_configuration_service.py`;
  read-only execution readiness over saved Integrations configuration, active
  account/link/reference posture, provider evidence, guardrails, and redactions.

- TASK-306:
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  selected-customer Integrations execution-readiness UI over the TASK-305
  read model, showing blockers, safe ready actions, post-save refresh, and
  explicit no-live-execution boundaries.

- TASK-307:
  `POST /v1/referral-saas/accounts/{account_ref}/integrations/api-access/verification`;
  `services/referral_saas_integrations_configuration_service.py`;
  first governed Integrations execution command for API-access verification
  evidence, with account/link/reference gates, saved configuration gates,
  idempotency/audit evidence, unsafe-payload rejection, and no credential,
  provider, webhook, invite/message, auth, campaign, billing, or money side
  effects.

- TASK-308:
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  selected-customer Integrations API-access verification action over the
  TASK-307 command, with safe verification evidence, idempotency/correlation,
  plain-language success feedback, readiness refresh, and no credential,
  provider, webhook, invite/message, auth, campaign, billing, or money side
  effects.

- TASK-309:
  `POST /v1/referral-saas/accounts/{account_ref}/integrations/webhooks/test-dispatch`;
  `services/referral_saas_integrations_configuration_service.py`;
  second governed Integrations execution command for webhook test-dispatch
  evidence, with account/link/reference gates, saved webhook configuration
  gates, idempotency/audit evidence, unsafe-payload rejection, and no webhook
  dispatch, subscription activation, signing-material creation, credential,
  provider, invite/message, auth, campaign, billing, or money side effects.

- TASK-310:
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  selected-customer Integrations webhook test evidence action over the
  TASK-309 command, with plain-language action copy, idempotency/correlation,
  no-secret/no-internal-tenant payload checks, success/error feedback,
  readiness refresh, and no live webhook, provider, credential, invite/message,
  auth, campaign, billing, or money side effects.

- TASK-311:
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/styles/base.css`;
  selected-customer Integrations page aligned to the recommended Plan, Save,
  Verify CX. Operators now plan API/webhook/message setup, save the non-secret
  connection plan, then run available verification checks from a dedicated
  Verify stage with explicit People and Access and Campaigns handoffs. Existing
  TASK-302, TASK-305, TASK-307, and TASK-309 APIs remain the source of truth.

- TASK-312:
  `POST /v1/referral-saas/accounts/{account_ref}/integrations/message-providers/test-check`;
  `services/referral_saas_integrations_configuration_service.py`;
  third governed Integrations execution command for message-provider test
  evidence, with account/link/reference gates, saved message-provider
  configuration gates, idempotency/audit evidence, unsafe-payload rejection,
  and no provider call, invite/message delivery, credential, webhook, auth,
  campaign, billing, or money side effects.

- TASK-313:
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  selected-customer Integrations UI action for the governed message-provider
  test-check command, with safe provider-readiness payloads,
  idempotency/correlation, plain-language feedback, and readiness refresh while
  preserving no provider call, invite/message delivery, credential, webhook,
  auth, campaign, billing, or money side effects.

- TASK-314:
  `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_INTEGRATIONS_CREDENTIAL_LIFECYCLE_CONTRACT.md`;
  selected-customer Integrations credential lifecycle request contract for
  future API key, webhook signing key, and provider credential-reference
  requests. The contract defines supported request types, selected-customer
  gates, idempotency/audit/redaction requirements, review states, response
  shape, and explicit no-secret/no-provider/no-webhook/no-message/no-auth/no-
  campaign/no-billing/no-money side-effect boundaries. It is contract-only and
  does not add schema, routes, UI, secret storage, provider execution, or DLaaS
  behavior.

- TASK-315:
  `dp/migrations/088_referral_saas_integration_credential_requests.sql`;
  `services/referral_saas_integrations_configuration_service.py`;
  `POST/GET /v1/referral-saas/accounts/{account_ref}/integrations/credential-requests`;
  `GET /v1/referral-saas/accounts/{account_ref}/integrations/credential-requests/{credential_request_ref}`;
  selected-customer credential request persistence/API foundation for safe
  request intent, review-ready posture, audit/idempotency evidence, and
  redacted metadata. It does not create, reveal, store, rotate, revoke,
  download, or send credentials; does not write a vault or call a provider; and
  does not trigger webhook, invite/message, auth, campaign, billing, money, or
  DLaaS side effects.

- TASK-316:
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  selected-customer Integrations credential request UI over the TASK-315 API.
  Operators can request governed credential setup from a saved connection plan,
  list safe request metadata, see plain-language feedback, and refresh
  readiness/request state while preserving no credential creation, reveal,
  storage, download, provider, vault, webhook, invite/message, auth, campaign,
  billing, money, or DLaaS side effects.

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
- TASK-187: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`
- TASK-188: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`
- TASK-189: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`
- TASK-192: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `frontend/src/styles/base.css`
- TASK-193: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`
- TASK-195: `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `frontend/src/api/referralSaasAccountQueries.ts`;
  `frontend/src/api/queryKeys.ts`;
  `frontend/src/app/App.tsx`;
  `frontend/src/layout/Sidebar.tsx`;
  `frontend/src/pages/admin/ReferralSaasWorkspacePage.tsx`
- TASK-196: `services/onboarding/onboarding_draft_repository.py`;
  `apps/api/routers/admin_onboarding.py`;
  `frontend/src/api/endpoints/adminOnboarding.ts`;
  `frontend/src/api/referralSaasAccountQueries.ts`;
  `frontend/src/api/queryKeys.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `test/test_onboarding_draft_repository.py`;
  `test/api/test_admin_onboarding_api.py`;
  `frontend/src/api/endpoints/adminOnboarding.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`
- TASK-197: `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SCHEMA_FINAL_REVIEW.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-198: `dp/migrations/082_referral_saas_account_foundation.sql`;
  `test/test_referral_saas_account_foundation_migration.py`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-199: `services/referral_saas_account_foundation_service.py`;
  `test/test_referral_saas_account_foundation_service.py`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-200: `apps/api/routers/referral_saas_accounts.py`;
  `apps/api/main.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-201: `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/api/referralSaasAccountQueries.ts`;
  `frontend/src/api/queryKeys.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-202: `services/onboarding/onboarding_draft_repository.py`;
  `test/test_onboarding_draft_repository.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_PHYSICAL_VERIFICATION.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_FRONTEND_IA_WORKFLOW_CONTRACT.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-203: `services/referral_saas_account_setup_service.py`;
  `test/test_referral_saas_account_setup_service.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_DURABLE_ACCOUNT_COMMAND.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-204: `apps/api/routers/referral_saas_accounts.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-205: `frontend/src/pages/admin/CompanyOnboardingPage.tsx`;
  `frontend/src/pages/admin/CompanyOnboardingPage.test.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `frontend/src/pages/admin/OnboardingDemoJourneySmoke.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-206: `scripts/referral_saas_account_create_physical_check.py`;
  `test/test_referral_saas_account_create_physical_check.py`;
  `services/referral_saas_account_setup_service.py`;
  `test/test_referral_saas_account_setup_service.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_CREATE_PHYSICAL_VERIFICATION.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-207: `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-208: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `apps/api/routers/admin_onboarding.py`;
  `test/api/test_admin_onboarding_api.py`;
  `scripts/referral_saas_account_setup_ui_physical_check.py`;
  `test/test_referral_saas_account_setup_ui_physical_check.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_SETUP_UI_PHYSICAL_VERIFICATION.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-209: `services/referral_saas_account_membership_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `test/test_referral_saas_account_membership_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/api/referralSaasAccountQueries.ts`;
  `frontend/src/api/queryKeys.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-210:
  `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_INVITATION_BOUNDARY.md`;
  `test/test_referral_saas_membership_invitation_boundary_contract.py`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-211: `services/referral_saas_account_membership_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `test/test_referral_saas_account_membership_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-212: `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-213:
  `scripts/referral_saas_account_membership_intent_physical_check.py`;
  `test/test_referral_saas_account_membership_intent_physical_check.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_MEMBERSHIP_INTENT_PHYSICAL_VERIFICATION.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-214:
  `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_ACTIVATION_DELIVERY_BOUNDARY.md`;
  `test/test_referral_saas_membership_activation_delivery_boundary_contract.py`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-215: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-216: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `frontend/src/styles/base.css`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-217: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `frontend/src/styles/base.css`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-218: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-219: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-220: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-221: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-222: `apps/api/routers/admin_onboarding.py`;
  `services/onboarding/onboarding_draft_repository.py`;
  `test/api/test_admin_onboarding_api.py`;
  `frontend/src/api/endpoints/adminOnboarding.ts`;
  `frontend/src/api/endpoints/adminOnboarding.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-223: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-224: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `apps/api/routers/admin_onboarding.py`;
  `test/api/test_admin_onboarding_api.py`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-225: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-226: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-227: `services/referral_saas_account_foundation_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/referralSaasAccountQueries.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `test/test_referral_saas_account_foundation_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-228: `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-229: `scripts/referral_saas_client_workspace_physical_check.py`;
  `test/test_referral_saas_client_workspace_physical_check.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_CLIENT_WORKSPACE_PHYSICAL_VERIFICATION.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-230: `scripts/referral_saas_fresh_client_workspace_physical_check.py`;
  `test/test_referral_saas_fresh_client_workspace_physical_check.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_FRESH_CLIENT_PHYSICAL_SEED_VERIFICATION.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`
- TASK-231: `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `dp/migrations/083_referral_saas_account_operating_jurisdiction.sql`;
  `services/referral_saas_account_foundation_service.py`;
  `services/referral_saas_account_setup_service.py`;
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/app/App.tsx`;
  `frontend/src/layout/Sidebar.tsx`;
  `frontend/src/styles/base.css`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - persisted account operating jurisdiction, jurisdiction-first customer finder, and standalone selected-customer profile route.
- TASK-232: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Account Setup starts from blank customer identifiers with tooltip guidance and no silent demo lookup.
- TASK-233: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Account Setup Review & Create now presents one primary create action and one save-for-later action while preserving the existing save, submit, review, and account-creation guardrails behind the product action.
- TASK-234: `services/referral_saas_account_setup_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `test/test_referral_saas_account_setup_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ACCOUNT_CREATE_PHYSICAL_VERIFICATION.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Account Setup no longer silently reuses the default `FNB` owner scope for new customer account foundations; it derives a bounded internal setup seed from the customer identifiers, creates/updates that seed inside the guarded account-foundation transaction, and returns a distinct internal-scope duplicate conflict when needed.
- TASK-235: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Account Setup now ends at Review & Create, removes the separate Handoff step and `Go to Campaigns` footer, and shows customer-profile-first next-best actions after account foundation creation.
- TASK-236: `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - selected-customer next actions now route people/access and customer settings into customer-profile modules instead of sending existing customers back into Account Setup.
- TASK-237: `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - People and Access in the selected Customer Profile now records customer-scoped access intent through the existing guarded membership invitation API without sending invite email, activating login, assigning seats, changing auth claims, or leaving customer context.
- TASK-238: `services/referral_saas_account_foundation_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Customer Settings in the selected Customer Profile now saves bounded durable profile fields through a guarded account profile maintenance command, preserving read-only customer identifiers and no activation, membership, campaign, credential, go-live, billing, money, or DLaaS behavior.
- TASK-239: `services/referral_saas_account_membership_service.py`;
  `dp/migrations/082_referral_saas_account_foundation.sql`;
  `dp/migrations/084_referral_saas_campaign_manager_role_family.sql`;
  `frontend/src/api/client.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/styles/base.css`;
  `test/test_referral_saas_account_membership_service.py`;
  `test/test_referral_saas_account_foundation_migration.py`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - People and Access now captures Work email as the customer-facing access identity, accepts Campaign manager as a bounded Referral SaaS role family, and keeps long API feedback contained inside the page.
- TASK-240: `frontend/src/pages/admin/ReferralSaasAccountSetupPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountSetupPage.test.tsx`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Account Setup now presents customer workspace language while keeping internal tenant/account mapping hidden behind the existing guarded APIs.
- TASK-241: `frontend/src/app/App.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Customer Profile now follows the separate-page model from the customer-profile mock: customer finder, selected customer home, and customer-scoped module routes for health, settings, people/access, campaigns, links/codes, reports, support, attribution, and progress instead of stacking every function on one page.
- TASK-242: `services/referral_saas_account_membership_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_account_membership_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/api/queryKeys.ts`;
  `frontend/src/api/referralSaasAccountQueries.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - People and Access now has a read-only membership activation readiness view that explains invite-delivery, account, tenant-link, external-reference, identity-acceptance, and missing-responsibility blockers without sending invites, activating users, assigning seats, changing auth claims, or moving money.
- TASK-243: `services/referral_saas_account_membership_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_account_membership_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Referral SaaS now has a customer/account-scoped invitation delivery request boundary that validates the selected account and invited membership, records blocked provider evidence with idempotency and audit posture, and returns a safe `DELIVERY_PROVIDER_NOT_CONFIGURED` result without sending email, activating memberships, assigning seats, changing auth claims, creating credentials, or moving money.
- TASK-244: `services/channel_readiness_service.py`;
  `services/referral_saas_technical_setup_service.py`;
  `apps/api/settings.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_channel_readiness_service.py`;
  `test/test_referral_saas_technical_setup_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Referral SaaS now has a customer/account-scoped technical setup readiness read model that reuses the shared channel catalog, adds Email provider readiness alongside messaging channels, and safely explains provider configuration gaps without creating credentials, dispatching webhooks, sending invites, activating memberships, assigning seats, changing auth claims, launching campaigns, or moving money.
- TASK-245: `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/referralSaasAccountQueries.ts`;
  `frontend/src/api/queryKeys.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Referral SaaS Customer Profile now has a standalone customer-scoped Technical Setup page wired to the technical setup readiness API, keeping the customer home short while explaining Email invite-delivery and referral-message provider gaps without creating credentials, dispatching webhooks, sending invites, activating memberships, assigning seats, changing auth claims, launching campaigns, or moving money.
- TASK-246: `apps/api/settings.py`;
  `services/channel_readiness_service.py`;
  `services/referral_saas_technical_setup_service.py`;
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `test/test_channel_readiness_service.py`;
  `test/test_referral_saas_technical_setup_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Referral SaaS technical setup now distinguishes channel provider configuration from approved Referral SaaS invite-provider scope. Email can be configured at the shared channel layer while invite delivery remains blocked until an approved provider reference and Referral SaaS scope are present; no credentials are created, no invites are sent, no memberships are activated, and no money moves.
- TASK-247: `services/referral_saas_account_membership_service.py`;
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `test/test_referral_saas_account_membership_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_ACTIVATION_DELIVERY_BOUNDARY.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - People and Access now exposes safe recipient contact readiness from existing hashed contact evidence. Activation readiness and People tables show whether a future invite has a contact reference without exposing email hashes or sending email; live delivery, activation, seats, auth claims, credentials, campaigns, go-live, billing, money movement, and DLaaS marketplace behavior remain blocked.
- TASK-248: `services/referral_saas_account_membership_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/styles/base.css`;
  `test/test_referral_saas_account_membership_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_ACTIVATION_DELIVERY_BOUNDARY.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - People and Access now has a guarded customer-scoped invite-delivery check. The action is disabled when contact evidence or approved invite-provider scope is missing, derives recipient readiness from backend evidence instead of browser-held hashes, records the existing blocked delivery boundary, and confirms no email, activation, seat, auth, credential, campaign, go-live, billing, money movement, or DLaaS marketplace action occurred.
- TASK-249: `services/referral_saas_account_membership_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_account_membership_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_ACTIVATION_DELIVERY_BOUNDARY.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Referral SaaS now has a customer-scoped membership activation command boundary that validates account/membership scope, identity acceptance, account/link/reference status, duplicate-active access, idempotency, and audit evidence. It can activate only the membership lifecycle and still confirms no invite email, seat assignment, auth/session claim change, credential creation, campaign activation, go-live, billing, money movement, or DLaaS marketplace action occurred.
- TASK-250: `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Selected Customer Profile People and Access now calls the guarded membership activation command boundary from the customer-scoped page. The action records accepted access evidence against a selected invited membership, refreshes membership posture/readiness, and confirms no invite email, seat assignment, auth/session claim change, credential creation, campaign activation, go-live, billing, money movement, or DLaaS marketplace action occurred.
- TASK-251: `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - People and Access now uses a real person-name placeholder so operators enter an individual name rather than a role description.
- TASK-252: `services/referral_saas_account_membership_service.py`;
  `test/test_referral_saas_account_membership_service.py`;
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - People and Access activation readiness now exposes access provisioning readiness separately from membership lifecycle, showing seat assignment and auth-claim propagation as bounded future workflows without assigning seats, changing login permissions, or leaving customer context.
- TASK-253: `apps/api/routers/referral_saas_accounts.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/api/referralSaasAccountQueries.ts`;
  `frontend/src/api/queryKeys.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Selected Customer Profile Campaigns now has a customer/account-scoped campaign readiness wrapper and standalone page. Operators check campaign readiness from the selected customer context without manually entering tenant code, while the response and UI confirm no campaign creation, policy write, link generation, activation, go-live, credential, billing, money movement, or DLaaS marketplace action occurred.
- TASK-254: `services/referral_saas_campaign_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/api/referralSaasAccountQueries.ts`;
  `frontend/src/api/queryKeys.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Selected Customer Profile Campaigns now loads and selects campaigns from the selected account before readiness checks. The backend adds read-only customer-scoped campaign list/read wrappers over existing campaign tables, redacts internal tenant identifiers, and confirms no campaign mutation, policy write, link generation, activation, go-live, billing, money movement, or DLaaS marketplace action occurred.
- TASK-256: `services/referral_saas_campaign_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_campaign_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Adds the guarded customer-scoped campaign setup create API wrapper. It resolves the selected account, creates only an inactive setup draft in existing campaign storage, records account audit/idempotency evidence, rejects unsafe activation/policy/link/webhook/money fields, and keeps tenant-code exposure out of the product payload.
- TASK-257: `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `frontend/src/app/App.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Adds the selected-customer campaign setup create UX. The Customer Profile Campaigns page opens a standalone customer-scoped create page that calls the guarded campaign setup API, saves only an inactive draft, shows safe next actions, and confirms no tenant-code entry, link generation, policy write, activation, webhook delivery, go-live, or money movement.
- TASK-258: `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_CAMPAIGN_POLICY_SETTINGS_CONTRACT.md`;
  `test/test_referral_saas_customer_campaign_policy_settings_contract.py`;
  `docs/sa/referral-saas/README.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Defines the selected-customer campaign policy/settings command boundary. It maps existing policy storage fields to product setup settings, keeps tenant-code resolution server-side, rejects activation/link/webhook/money-adjacent payloads, and sets up the next implementation slice for a guarded account-scoped policy/settings wrapper.
- TASK-259: `services/referral_saas_campaign_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_campaign_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Adds the guarded customer-scoped campaign policy/settings API wrapper. It resolves selected account and campaign scope internally, upserts policy/settings evidence into existing campaign policy storage, records account audit/idempotency evidence, rejects unsafe tenant-code/activation/link/webhook/money payloads, and does not activate campaigns, generate links, create validation tracks, deliver webhooks, bill, or move money.
- TASK-260: `frontend/src/api/client.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Adds the standalone selected-customer campaign policy/settings page, wires it to the guarded TASK-259 API wrapper, links campaign setup success into policy settings, and keeps policy evidence separate from activation, link generation, webhook delivery, billing, and money movement.
- TASK-261: `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_CAMPAIGN_SUBMIT_REVIEW_CONTRACT.md`;
  `test/test_referral_saas_customer_campaign_submit_review_contract.py`;
  `docs/sa/referral-saas/README.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Defines the selected-customer campaign submit/review command boundary. It maps existing campaign, policy, readiness, account-audit, idempotency, and onboarding-review patterns into campaign-level review without activating campaigns, generating links, creating validation tracks, delivering webhooks, changing seats/auth claims, billing, moving money, or exposing tenant code.
- TASK-262: `services/referral_saas_campaign_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_campaign_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md` - Adds guarded selected-customer campaign review submission and review decision API wrappers. The backend resolves account/campaign scope internally, requires policy evidence before review submission, records review/audit/idempotency evidence, rejects unsafe tenant-code/activation/link/webhook/access/money payloads, and keeps approval as eligibility for a future activation command rather than activation itself.
- TASK-263: `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the selected-customer Campaign Review UX. Operators can submit campaign setup evidence and record approval/block review decisions from the selected customer's Campaigns module; review approval is shown as future activation eligibility only and does not activate campaigns, generate links, create validation tracks, deliver webhooks, change access, bill, or move money.
- TASK-264: `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_CAMPAIGN_ACTIVATION_CONTRACT.md`;
  `test/test_referral_saas_customer_campaign_activation_contract.py`;
  `docs/sa/referral-saas/README.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Defines the selected-customer campaign activation/go-live command boundary. Activation now has a reviewed contract requiring approved review, readiness, idempotency, and audit evidence while keeping tenant-code exposure, link generation, validation-track creation, webhook delivery, credentials, access changes, billing, money movement, DLaaS marketplace behavior, and source forks out of scope.
- TASK-265: `services/referral_saas_campaign_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_campaign_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the guarded selected-customer campaign activation API wrapper. The backend resolves account/campaign scope internally, requires policy evidence and approved review posture, activates only campaign lifecycle posture, records audit/idempotency evidence, rejects unsafe adjacent payload fields, and confirms no link generation, validation-track creation, webhook delivery, credential creation, access change, billing, DLaaS marketplace behavior, or money movement.
- TASK-266: `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Wires the selected-customer campaign activation action to the guarded TASK-265 API wrapper from the Campaign Review page. Activation is available only after review approval, stays inside the selected customer context, refreshes campaign list state, and confirms no link generation, validation-track creation, webhook delivery, credential creation, access change, billing, DLaaS marketplace behavior, or money movement.
- TASK-267: `apps/api/routers/referral_saas_accounts.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `frontend/src/api/endpoints/referralSaasLinks.ts`;
  `frontend/src/api/endpoints/referralSaasLinks.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds customer-scoped Links and Codes continuation from activated selected-customer campaigns. Operators can choose an active campaign, issue/reuse a referral code, validate it, and stay in customer context while the backend resolves tenant scope internally and blocks activation, webhook, credential, billing, and money side effects.
- TASK-268: `apps/api/routers/referral_saas_accounts.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `frontend/src/api/endpoints/referralSaasReports.ts`;
  `frontend/src/api/endpoints/referralSaasReports.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds selected-customer Reports continuation. Operators can open reports from the selected customer home, filter by report type and campaign, and preview JSON/CSV exports while the backend resolves tenant scope internally and blocks export persistence, storage, delivery, credentials, billing, and money side effects.
- TASK-269: `scripts/referral_saas_selected_customer_e2e_physical_check.py`;
  `test/test_referral_saas_selected_customer_e2e_physical_check.py`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `scripts/README.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds a repeatable selected-customer E2E physical proof runner. The runner selects an existing customer, verifies account resolution, people/access posture, technical readiness, campaign list, campaign readiness, campaign report, and export preview without tenant-code exposure or live side effects. At TASK-269 completion, scores remained 9.95/10 for Referral Management and 9.82/10 for Campaign Attribution until the runner could be executed against local/staging data; TASK-270 records that execution and the required fixes.
- TASK-270: `apps/api/routers/referral_saas_accounts.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Fixes the blockers found while executing the TASK-269 selected-customer proof runner. The selected-customer campaign readiness wrapper now redacts internal tenant-scope keys returned by shared readiness primitives, the selected-customer report/export preview wrappers await their async builders, and the local physical proof passed account registry, account resolve, people/access posture, technical readiness, campaign list, campaign readiness, campaign report, and export preview checks with no live side effects. Scores move to 9.96/10 for Referral Management and 9.84/10 for Campaign Attribution.
- TASK-271: `scripts/referral_saas_selected_customer_mutation_e2e_physical_check.py`;
  `test/test_referral_saas_selected_customer_mutation_e2e_physical_check.py`;
  `scripts/README.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds a repeatable selected-customer mutation-path physical proof runner. The runner selects an existing customer, creates a uniquely suffixed campaign setup draft, saves policy/settings, submits and approves review, activates campaign posture, issues and validates a referral code, and then verifies report/export preview while failing on tenant-scope leakage and confirming no webhook delivery, credential creation, invite delivery, membership activation, persisted export creation, billing, or money movement. Scores move to 9.97/10 for Referral Management and 9.86/10 for Campaign Attribution until the runner is executed against local/staging data and persisted export/support persistence gaps are closed.
- TASK-272: `docs/sa/referral-saas/REFERRAL_SAAS_SELECTED_CUSTOMER_MUTATION_PHYSICAL_VERIFICATION.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Records local execution of the TASK-271 mutation proof against `test-fnb-sa-002`. The proof passed campaign create, policy/settings, review submission, review decision, activation posture, referral code issue, referral validation, campaign performance report, and export preview while confirming no tenant-scope leakage, webhook delivery, credential creation, invitation delivery, membership activation, persisted export creation, storage/delivery, billing, or money movement. Scores move to 9.98/10 for Referral Management and 9.88/10 for Campaign Attribution.
- TASK-273: `dp/migrations/085_referral_saas_report_export_requests.sql`;
  `services/referral_saas_reporting_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_report_export_request_migration.py`;
  `test/test_referral_saas_reporting_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds persisted selected-customer report export request and audit evidence. The backend validates export requests through existing tenant-safe report preview rules, records request/idempotency/audit metadata, replays matching idempotency keys, rejects conflicting idempotency and unsafe storage/delivery/billing/money payloads, and still does not create export files, download URLs, scheduled deliveries, invoices, billing events, or money movement. Scores move to 9.99/10 for Referral Management and 9.90/10 for Campaign Attribution.
- TASK-274: `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `frontend/src/styles/base.css`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Clarifies the selected-customer picker and selected-customer profile header by labeling customer, operating jurisdiction, account status, customer reference, organisation reference, account code, and selected state. This is a frontend-only UX improvement over the existing account registry response; it adds no backend fields, schema, account mutations, tenant-code exposure, or DLaaS scope.
- TASK-275: `services/referral_saas_account_membership_service.py`;
  `test/test_referral_saas_account_membership_service.py`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Fixes the accepted-access membership activation command path found during local UI testing. The duplicate-active membership guard now casts nullable `user_id` and `client_id` parameters to their schema-backed types before comparison, preventing Postgres from raising an ambiguous-parameter 500 while preserving the existing no-invite, no-seat, no-auth-claim, no-campaign, no-billing, and no-money guardrails.
- TASK-276: `services/referral_saas_account_membership_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/styles/base.css`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_account_membership_service.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_MEMBERSHIP_INVITATION_BOUNDARY.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds guarded edit/cancel lifecycle commands for invited People and Access intent, fixes the accepted-access ambiguous-parameter backend failure path, and moves the selected-customer People and Access UI toward the mock recommendation with a primary people list, opaque add/edit drawer, remove intent action, disabled/cancelled intent hidden from the primary working list, missing-role Add prompts, hashed work-email evidence, and diagnostics kept secondary. No live invitation delivery, membership activation side effects, seat assignment, auth-claim propagation, billing, or money movement are introduced.
- TASK-277: `frontend/src/styles/tokens.css`;
  `frontend/src/styles/base.css`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Fixes the People and Access add/edit drawer surface so the drawer is visually opaque over the dimmed page. This defines the missing shared surface tokens and hardens drawer stacking without changing backend behavior, schemas, routes, account state, membership lifecycle commands, invitation delivery, activation, seats, auth claims, billing, or money movement.
- TASK-278: `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Fixes People and Access add/edit access-intent idempotency reuse by composing keys from account, email, display name, and responsibility. The backend idempotency conflict guard remains intact while distinct operator-entered person payloads no longer collide with stale keys; no invite email, login activation, seat assignment, auth-claim propagation, billing, or money movement is introduced.
- TASK-279: `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds an Amplifi Admin-only manual access acceptance action inside the selected-customer People and Access edit drawer. The UI requires acceptance evidence, shows accepted access separately from login/seat provisioning, and reuses the existing audited membership activation command boundary, while preserving no live invite delivery, no seat assignment, no auth-claim propagation, no billing, and no money movement.
- TASK-280: `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Fixes the People and Access post-save refresh path so add/edit/remove, invite-delivery checks, and accepted-access actions wait for the refreshed membership posture and activation readiness read models before presenting completion feedback. The refreshed people list now shows the newly saved person without requiring a manual browser refresh while preserving the existing no-invite, no-login, no-seat, no-auth-claim, no-billing, and no-money guardrails.
- TASK-281: `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Fixes the remove-then-readd People and Access path by giving each Add person drawer attempt a fresh create idempotency suffix. Backend idempotency replay remains intact for the same submitted action, while a later re-add of the same person and responsibility creates a fresh invited intent instead of replaying an old disabled membership; no invite email, login activation, seat assignment, auth-claim propagation, billing, or money movement is introduced.
- TASK-282: `services/referral_saas_account_membership_service.py`;
  `test/test_referral_saas_account_membership_service.py`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Fixes the Amplifi Admin manual accepted-access path found during physical UI testing. Manual acceptance can now record accepted membership evidence for a pending-onboarding setup account when the invited identity matches and the external reference is active, while login, seats, auth claims, invite delivery, billing, and money remain separate guarded workflows. The edit drawer now separates `Save person details` from `Record accepted access`.
- TASK-283: `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Makes the selected-customer People and Access provisioning boundary visible as a first-class Login and Seat Provisioning section. Accepted people now show per-person accepted-access, seat-assignment, login-permission, and disabled `Provision login & seat` next-action rows so operators can see where the future governed provisioning workflow belongs without silently creating login access, assigning seats, changing auth claims, sending invites, billing, or moving money.
- TASK-284: `docs/sa/referral-saas/REFERRAL_SAAS_ACCESS_PROVISIONING_COMMAND_CONTRACT.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Defines the governed access provisioning command boundary for the visible People and Access `Provision login & seat` next action. The contract separates accepted-access evidence from actual seat assignment and auth/login claim propagation, identifies the candidate account-scoped membership route, records required account/link/reference/membership/seat/auth-provider/idempotency/audit gates, and keeps the UI action disabled until a runtime API task implements those guardrails. No backend route, schema migration, frontend action enablement, seat assignment, auth-claim change, invite delivery, campaign activation, billing, or money movement is introduced.
- TASK-285: `services/referral_saas_account_membership_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_account_membership_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_ROUTE_SMOKE_INVENTORY.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Implements the governed access provisioning API wrapper for accepted customer access. The route can assign an available platform seat only after active account, tenant-link, external-reference, active membership, admin actor, idempotency, audit, and redaction gates pass. Blocked gates are audited without assignment. The task keeps invite delivery, credential creation, auth/session claim propagation, campaign activation, go-live, billing, and money movement outside this route.
- TASK-286: `services/referral_saas_account_membership_service.py`;
  `test/test_referral_saas_account_membership_service.py`;
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Wires selected-customer People and Access to the guarded access provisioning API. The UI enables `Provision login & seat` only for active accepted memberships that are ready for seat assignment, sends the account-scoped guarded request, refreshes People and Access read models, and shows seat-assignment state while credential creation and auth/session claim propagation remain separate governed workflows.
- TASK-287: `scripts/referral_saas_people_access_provisioning_physical_check.py`;
  `test/test_referral_saas_people_access_provisioning_physical_check.py`;
  `scripts/README.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PEOPLE_ACCESS_PROVISIONING_PHYSICAL_VERIFICATION.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds a repeatable selected-customer People and Access provisioning physical proof runner. The runner selects a customer, creates or reuses accepted access evidence, calls the guarded access provisioning API, verifies idempotency replay, verifies refreshed posture/readiness read models, optionally checks DB/audit evidence, and fails if invite delivery, credential creation, auth-claim propagation, campaign activation, go-live, billing, or money movement occur. It reports controlled provisioning blocks when local account/link/reference/seat gates are not ready.
  Local API/DB execution against `test-fnb-sa-002` passed with controlled status
  `PROVISIONING_REJECTED_ACCOUNT_NOT_ACTIVE`, DB audit status `BLOCKED`, active
  membership evidence, no seat assignment, and no auth-claim propagation.
- TASK-288: `services/referral_saas_account_foundation_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `test/test_referral_saas_account_foundation_activation_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the
  guarded Referral SaaS account-foundation activation command. Amplifi Admin can
  activate a selected customer foundation from setup scope, move the account to
  `ACTIVE`, approve onboarding, activate the owner tenant link, create bounded
  available `ADMIN`/`OPERATOR` seat capacity, and record audit/idempotency
  evidence without assigning seats, activating memberships, delivering invites,
  creating credentials, changing auth claims, activating campaigns, triggering
  go-live, billing, moving money, or adding DLaaS marketplace behavior.
- TASK-289: `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `frontend/src/styles/base.css`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Reworks
  selected-customer People and Access into a person-first lifecycle workspace
  aligned to the CX mock recommendations. The page now prioritizes one working
  list with missing-role prompts, named/accepted/seat lifecycle labels, one next
  action per responsibility, an opaque add/edit drawer with current-stage
  guidance, diagnostics behind a toggle, and clearer provisioning-boundary copy.
  No backend route, schema, invite delivery, credential creation, auth-claim
  propagation, campaign activation, billing, money movement, or DLaaS marketplace
  behavior is introduced.
- TASK-290: `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `frontend/src/styles/base.css`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Wires the
  TASK-288 guarded account-foundation activation command into selected-customer
  Customer Home, People and Access, and Account Health. Pending customers now
  show an Amplifi Admin `Activate foundation` action before seat provisioning;
  the UI calls the account-scoped activation API, refreshes account and access
  read models, explains available seat capacity, and avoids presenting blocked
  provisioning as successful assignment. No backend route, schema, membership
  activation, direct seat assignment, invite delivery, credential creation,
  auth-claim propagation, campaign activation, go-live, billing, money movement,
  or DLaaS marketplace behavior is introduced.
- TASK-291: `scripts/referral_saas_people_access_provisioning_physical_check.py`;
  `test/test_referral_saas_people_access_provisioning_physical_check.py`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PEOPLE_ACCESS_PROVISIONING_PHYSICAL_VERIFICATION.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds an
  activated-account proof path to the repeatable People and Access physical
  check. The runner can now call the guarded account-foundation activation API
  before membership intent, accepted-access activation, and seat provisioning,
  using external setup scope, bounded seat capacity, stable idempotency, and
  no-adjacent-action evidence. This does not add backend routes, frontend
  routes, schema, invite delivery, credential creation, auth-claim propagation,
  campaign activation, billing, money movement, or DLaaS marketplace behavior.
- TASK-292: `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Aligns
  Customer Home health and next-best-action mapping with the current People and
  Access lifecycle. Once required owner/campaign-manager responsibilities are
  present and accepted, Customer Home no longer shows `Add who can manage this
  account` as the red blocker; People and Access is marked Ready, roles-missing
  uses the actual missing-role count, and remaining seat/auth work stays a
  separate governed next action. This does not add backend routes, schema,
  invite delivery, credential creation, auth-claim propagation, campaign
  activation, billing, money movement, or DLaaS marketplace behavior.
- TASK-293: `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `frontend/src/styles/base.css`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Simplifies
  selected-customer People and Access into a plain-language customer-manager
  confirmation workflow. The page now treats the required owner and campaign
  manager as `confirmed` for referral work, uses `Still needed`, `Added`,
  `Confirmed`, and `Login setup later` lifecycle labels, and moves seat/login
  setup into a secondary optional section. Existing guarded provisioning APIs
  remain available from that optional path only; no backend route, schema, invite
  delivery, credential creation, auth-claim propagation, campaign activation,
  billing, money movement, or DLaaS marketplace behavior is introduced.
- TASK-294:
  `docs/sa/referral-saas/REFERRAL_SAAS_PEOPLE_ACCESS_PROVISIONING_PHYSICAL_VERIFICATION.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Records
  successful local execution of the activated People and Access provisioning
  proof. The runner activated the selected customer account foundation through
  the guarded API, provisioned an available `OPERATOR` seat through the guarded
  People and Access provisioning route, replayed idempotently, and confirmed DB
  and audit evidence. No invite delivery, credential creation, auth-claim
  propagation, campaign activation, go-live action, billing, or money movement
  occurred.
- TASK-295:
  `docs/sa/referral-saas/REFERRAL_SAAS_SUPPORT_CASE_PERSISTENCE_CONTRACT.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Defines the
  selected-customer support-case persistence contract. The contract sets the
  case categories, statuses, safe evidence-link types, selected-customer API
  route shape, idempotency replay/conflict behavior, audit evidence, frontend
  product expectations, and non-goal guardrails for support cases. It keeps
  repair, replay, retry, campaign activation, export file creation, invite
  delivery, credential creation, auth-claim propagation, billing, money
  movement, DLaaS marketplace behavior, and source-code forks out of this
  boundary until later reviewed tasks implement them.
- TASK-296:
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Scopes the
  selected-customer Account Health activation success message to the account id
  returned by the guarded activation command. A stale or mismatched activation
  response for another customer is suppressed, while the backend account path
  scope guard remains the source of truth for write safety.
- TASK-297:
  `dp/migrations/086_referral_saas_support_cases.sql`;
  `services/referral_saas_support_case_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `test/test_referral_saas_support_case_migration.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Implements
  selected-customer support-case persistence for create/list/read. The new
  schema and service store safe case fields, safe evidence links, idempotency
  hashes, account scope, and audit evidence, and the account wrapper routes
  reject raw UCNs, provider payloads, secrets, tokens, repair/replay/retry
  commands, campaign activation, invite delivery, auth-claim changes, billing,
  money movement, and DLaaS marketplace side effects. Notes, status changes,
  and frontend case UI remain separate tasks.
- TASK-298:
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `frontend/src/styles/base.css`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Clarifies the
  selected-customer People and Access Platform login setup area. The required
  workflow remains role-specific person confirmation for customer work, while
  Platform login setup is explained as optional Amplifi sign-in setup that can be
  skipped when a person only owns the relationship outside the platform.
- TASK-300:
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Reframes the
  selected-customer Technical Setup surface as Integrations. Customer Home and
  next-best actions now route operators to `/integrations` for API, webhook,
  invite-delivery, and referral-message provider readiness, while the previous
  `/technical` path remains a compatibility alias. The backend readiness API
  remains a read-only implementation detail; no provider credentials, webhook
  dispatch, invite delivery, auth/login action, campaign activation, billing, or
  money movement is introduced.
- TASK-301:
  `docs/sa/referral-saas/REFERRAL_SAAS_CUSTOMER_INTEGRATIONS_CONFIGURATION_CONTRACT.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Defines the
  future selected-customer Integrations configuration boundary for API access,
  webhook callback intent, event-category subscription intent, invite-delivery
  provider approval intent, referral-message provider readiness, and safe
  test-mode posture. This is contract-only; no runtime route, schema,
  credential lifecycle, webhook dispatch, invite delivery, auth/login change,
  campaign activation, billing, money movement, or DLaaS behavior is introduced.

## Explicit Deferrals

The following are DLaaS expansion work, not blockers for this SaaS roadmap:

- distributor marketplace depth
- commission settlement
- funding operations
- fulfilment provider routing
- settlement batches
- sponsor billing
- white-label/embed
