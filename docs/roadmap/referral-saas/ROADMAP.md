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

## Amplifi Experience Design Alignment

TASK-356 reconciles the current roadmap with the external Amplifi experience
design pack, including:

- `customer-journey-architecture-and-maturity.md`
- `production-readiness-matrix.md`
- `service-coverage-map.md`
- `simplified-experience-architecture.md`

The important change is that the path to 10/10 is no longer only the final
provider/vault, repair/replay, and non-local proof tail. Those remain real
technical blockers, but the customer-journey architecture also requires a
clearer production-grade sequence across account establishment, partner
workspace entry, integrations, campaign attribution, referral attribution,
reporting, and support.

The post-TASK-356 sequence is:

| Task range | Work package | What it closes |
| --- | --- | --- |
| TASK-357 to TASK-362 | Scope, account, jurisdiction, workspace, entitlement, and activation gates | The customer/partner journey can be promised only inside explicit H1 scope, account context, jurisdiction, capability, and production activation rules. |
| TASK-363 to TASK-365 | Invitation, acceptance, identity, and login | People and access becomes a complete governed journey from named person to invite, acceptance, seat/login posture, and auth reconciliation. |
| TASK-366 to TASK-368 | Integrations | Customer-scoped API, webhook, invite-provider, and referral-message provider setup moves from saved evidence/readiness into bound execution evidence. |
| TASK-369 to TASK-371 | Campaign management | Partner-safe campaign workspace actions, pre-activation review, separation of duties, and lifecycle controls become server-enforced. |
| TASK-372 to TASK-375 | Referral operations | Account-scoped referral registry/detail, safe identity dimensions, timeline evidence, and governed correction/replay/reassignment close the referral operations gap. |
| TASK-376 to TASK-377 | Attribution | Dedicated Campaign Attribution and Referral/Referrer Attribution surfaces separate campaign performance from who-got-credit explanations. |
| TASK-378 to TASK-379 | Reporting and exports | HVE funnel, journey performance, saved reports, signed exports, scheduled delivery, expiry, deletion, and provider delivery proof become complete. |
| TASK-380 | Support and recovery | Customer/partner-safe support, audit, assignment, evidence, and governed recovery become operationally complete. |
| TASK-381 | Separately contracted finance | Commercial-finance capability is isolated from the H1 SaaS promise while minimum entitlement posture remains visible. |

This keeps the Referral SaaS product boundary intact. It does not pull in
DLaaS distributor marketplace depth, settlement, funding, fulfilment, sponsor
billing, or broad white-label/embed work.

TASK-357 locks the H1 release scope in
`docs/sa/referral-saas/REFERRAL_SAAS_H1_RELEASE_SCOPE_AND_JOURNEY_GATES.md`.
The release promise is now explicit: account/customer context, people/access,
integrations, campaign setup/activation, links/codes, referral progress,
attribution, reporting/export, and support are H1 Referral SaaS journeys. Broad
DLaaS marketplace, fulfilment, settlement, funding, sponsor billing,
white-label/embed, raw secrets, unmanaged provider dispatch, generic replay,
and money movement remain disabled or separately contracted. Later tasks must
enforce the same release gates server-side and keep the UI honest when a
journey is deferred, blocked, or controlled.

TASK-358 starts that runtime enforcement path. The selected-customer account
resolver, membership posture, and membership activation readiness routes now
carry operating jurisdiction in the safe account context and fail closed when
the caller identity is scoped to a different account, a different operating
jurisdiction, or lacks the required Referral SaaS account-read capability.
Partner workspace, entitlement, invitation/login, integration execution,
campaign control, referral operations, attribution, reporting, support, and
non-local proof gates remain on TASK-359 through TASK-380.

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
175. TASK-317: Add Integrations credential request review-decision API foundation.
176. TASK-318: Wire Integrations credential request review UI.
177. TASK-319: Add Integrations credential execution-check API foundation.
178. TASK-320: Wire Integrations credential execution-check UI.
179. TASK-321: Add selected-customer support-case UI.
180. TASK-322: Add selected-customer support-case notes and status API.
181. TASK-323: Wire selected-customer support-case lifecycle UI.
182. TASK-324: Define operator aggregate support queue contract.
183. TASK-325: Add operator aggregate support queue API.
184. TASK-326: Add operator aggregate support queue UI.
185. TASK-327: Define export file storage and download lifecycle contract.
186. TASK-328: Add Referral SaaS export file runtime foundation.
187. TASK-329: Add selected-customer report export download UI.
188. TASK-330: Enforce Referral SaaS report export retention expiry.
189. TASK-331: Define Referral SaaS export object-store signed URL contract.
190. TASK-332: Add Referral SaaS export signed URL runtime.
191. TASK-333: Define Referral SaaS scheduled report delivery contract.
192. TASK-334: Add scheduled report delivery API foundation.
193. TASK-335: Wire selected-customer scheduled report delivery UI.
194. TASK-336: Define governed repair and replay guardrails contract.
195. TASK-337: Add support-case repair/replay readiness API.
196. TASK-338: Wire support-case repair/replay readiness UI.
197. TASK-339: Define progress and attribution mutation proof contract.
198. TASK-340: Add progress and attribution mutation proof runner.
199. TASK-341: Record progress and attribution mutation proof execution.
200. TASK-342: Define provider/vault runtime adapter contract.
201. TASK-343: Add provider/vault execution readiness API.
202. TASK-344: Wire provider/vault execution readiness UI.
203. TASK-345: Define governed auth/login completion contract.
204. TASK-346: Add governed auth/login completion API boundary.
205. TASK-347: Wire governed auth/login completion UI.
206. TASK-348: Run non-local Referral SaaS launch verification.
207. TASK-349: Define provider/vault runtime execution command contract.
208. TASK-350: Add provider/vault runtime execution API foundation.
209. TASK-351: Add provider/vault runtime adapter seam.
210. TASK-352: Define provider/vault adapter implementation plan.
211. TASK-353: Add platform-reference provider/vault adapters.
212. TASK-354: Define vendor/managed provider-vault adapter contract.
213. TASK-355: Add vendor/managed provider-vault runtime adapters.

- TASK-341: `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_ATTRIBUTION_MUTATION_PROOF_EXECUTION_TASK_341.md`;
  `scripts/referral_saas_progress_attribution_physical_check.py`;
  `apps/api/routers/progress.py`;
  `services/outcome_trace_service.py`;
  focused progress/proof/trace tests;
  `scripts/README.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Records passing approved local execution for the progress/attribution mutation proof. The proof creates campaign/link/code evidence in a selected-customer context, validates a referral, captures identity, records and replays progress with dedupe, records a later milestone, reads progress status, reads attribution trace, and reads the campaign report while confirming no provider, webhook, invite, credential, auth, billing, money, or DLaaS side effects. The task also fixes split admin/progress credentials, controlled progress 4xx handling, and outcome-trace UUID/text readback defects found by the physical run. Current rating remains 9.99/10 for Referral Management and moves Campaign Attribution to 9.9995/10 while non-local proof, provider/vault execution, governed auth/login completion, and governed repair/replay execution remain separate launch-hardening tracks.

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

- TASK-317:
  `POST /v1/referral-saas/accounts/{account_ref}/integrations/credential-requests/{credential_request_ref}/review-decisions`;
  `services/referral_saas_integrations_configuration_service.py`;
  selected-customer credential request review-decision API foundation.
  Operators can approve or block a recorded credential request for later
  governed execution with idempotency, audit evidence, selected-customer
  scope, unsafe-payload rejection, and no credential creation, storage, reveal,
  download, provider, vault, webhook, invite/message, auth, campaign, billing,
  money, or DLaaS side effects.

- TASK-318:
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  selected-customer Integrations credential request review UI over the
  TASK-317 API. Operators can approve or block ready credential setup requests
  from the Verify tab, receive plain-language governance feedback, and refresh
  credential request/readiness state while preserving no credential creation,
  storage, reveal, download, provider, vault, webhook, invite/message, auth,
  campaign, billing, money, or DLaaS side effects.

- TASK-319:
  `POST /v1/referral-saas/accounts/{account_ref}/integrations/credential-requests/{credential_request_ref}/execution-checks`;
  `services/referral_saas_integrations_configuration_service.py`;
  selected-customer Integrations credential execution-check API foundation.
  Operators can record approved-request execution-readiness evidence with
  idempotency, audit evidence, selected-customer scope, unsafe-payload
  rejection, and no credential creation, storage, reveal, download, rotation,
  revoke, provider, vault, webhook, invite/message, auth, campaign, billing,
  money, or DLaaS side effects.

- TASK-320:
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  selected-customer Integrations credential execution-check UI over the
  TASK-319 API. Operators can check approved credential setup requests from the
  Verify tab, receive plain-language execution-readiness feedback, and refresh
  credential request/readiness state while preserving no credential creation,
  storage, reveal, download, rotation, revoke, provider, vault, webhook,
  invite/message, auth, campaign, billing, money, or DLaaS side effects.

- TASK-321:
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  selected-customer Support case list/create UI over the TASK-297 API.
  Operators can record customer-scoped support cases with safe categories,
  priority, optional safe evidence references, idempotency, plain-language
  feedback, and no repair, replay, retry, credential, provider, webhook,
  invite/message, auth, campaign, export, billing, money, or DLaaS side
  effects.

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
- TASK-320:
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Wires the
  selected-customer Integrations UI to the TASK-319 credential execution-check
  API. Approved credential setup requests now expose a plain-language
  `Check approved setup` action in the Verify tab, record safe
  execution-readiness evidence, and refresh credential request/readiness state
  without creating, storing, revealing, downloading, rotating, revoking, or
  sending credentials and without provider, vault, webhook, message, auth,
  campaign, go-live, billing, money, DLaaS, or source-fork side effects.

- TASK-321:
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the
  selected-customer Support page over the TASK-297 support-case API. Operators
  can list and create safe customer-scoped support cases, attach optional safe
  evidence references, and receive plain-language feedback while keeping
  support notes/status changes, repair/replay/retry, credentials, provider
  calls, webhook dispatch, invite/message delivery, auth, campaign activation,
  exports, billing, money, DLaaS, and source-fork side effects out of scope.

- TASK-322:
  `dp/migrations/089_referral_saas_support_case_lifecycle.sql`;
  `services/referral_saas_support_case_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `test/test_referral_saas_support_case_lifecycle_migration.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_SUPPORT_CASE_PERSISTENCE_CONTRACT.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the
  selected-customer support-case lifecycle backend foundation. Operators can
  add safe notes and move cases through bounded statuses through audited,
  idempotent account-scoped API commands while preserving no repair/replay/retry,
  referral/campaign/progress/attribution/report/export mutation, invite,
  credential, auth, billing, money, DLaaS, or source-fork side effects. Support
  notes/status UI, aggregate support queues, repair guardrails, export files,
  and non-local proof repetition remain separate tasks.

- TASK-323:
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/sa/referral-saas/REFERRAL_SAAS_SUPPORT_CASE_PERSISTENCE_CONTRACT.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Wires the
  selected-customer Support page to the TASK-322 lifecycle API. Operators can
  add safe notes and move cases through bounded statuses from the customer
  Support page, with idempotency/correlation payloads, post-save refresh, clear
  success/error feedback, and no repair/replay/retry, provider, invite,
  credential, auth, export, campaign activation, billing, money, DLaaS, or
  source-fork side effects. Aggregate support queues, repair guardrails, export
  files, progress/attribution mutation proof, and non-local proof repetition
  remain separate tasks.
- TASK-324: `docs/sa/referral-saas/REFERRAL_SAAS_SUPPORT_QUEUE_CONTRACT.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Defines the
  operator aggregate support queue contract over selected-customer support
  cases. The contract sets the future read-only route, safe filters, queue item
  fields, ordering, redactions, and no-adjacent-action guardrails without adding
  runtime routes, UI, assignment, repair/replay/retry, provider, invite,
  credential, auth, export, campaign activation, billing, money, DLaaS, or
  source-fork behavior. Runtime queue API/UI remain separate tasks.
- TASK-325: `services/referral_saas_support_case_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_SUPPORT_QUEUE_CONTRACT.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Implements
  the read-only operator aggregate support queue API over persisted
  selected-customer support cases. Operators can now read a cross-customer,
  filter-bounded, redacted support queue with safe account labels, case
  metadata, evidence/note counts, cursor pagination, and no assignment,
  repair/replay/retry, provider, invite, credential, auth, export, campaign
  activation, billing, money, DLaaS, or source-fork side effects. Queue UI
  remains a separate task.
- TASK-326: `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/api/queryKeys.ts`;
  `frontend/src/api/referralSaasAccountQueries.ts`;
  `frontend/src/layout/Sidebar.tsx`;
  `frontend/src/pages/admin/ReferralSaasSupportHubPage.tsx`;
  `frontend/src/pages/admin/ReferralSaasSupportHubPage.test.tsx`;
  `docs/sa/referral-saas/REFERRAL_SAAS_SUPPORT_QUEUE_CONTRACT.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the live
  read-only operator aggregate Support queue UI over the TASK-325 API.
  Operators can triage cross-customer support cases with KPIs, bounded filters,
  safe case rows, selected-customer Support routing, diagnostic shortcuts, and
  no assignment, repair/replay/retry, provider, invite, credential, auth,
  export, campaign activation, billing, money, DLaaS, or source-fork side
  effects.
- TASK-327: `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Defines the
  persisted export file storage/download/retention lifecycle over the existing
  TASK-273 export request/audit spine. The contract defines request, pending,
  stored/downloadable, expired, and failed states; candidate customer-scoped
  file/read/download routes; redaction, freshness, row-limit, account-scope,
  expiry, retention, and audit expectations; and explicit no scheduled
  delivery, provider, invite/message, credential/auth, campaign activation,
  repair/replay/retry, billing, money, DLaaS, or source-fork side effects.
  TASK-328 follows as the bounded runtime export file creation/download
  implementation.
- TASK-328: `services/referral_saas_reporting_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `test/test_referral_saas_reporting_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the
  first runtime export file foundation over persisted selected-customer export
  requests. The backend can create tenant-safe inline JSON/CSV file artifacts,
  read file metadata without exposing content, download stored content, audit
  file creation/download access, replay already-stored exports safely, and keep
  object storage, signed URLs, scheduled delivery, providers, webhooks,
  invite/message delivery, credentials, auth/session changes, campaign
  activation, repair/replay/retry, billing, money, DLaaS, and source-fork side
  effects out of scope. Scores remain 9.99/10 for Referral Management and move
  to 9.995/10 for Campaign Attribution.
- TASK-329: `frontend/src/api/endpoints/referralSaasReports.ts`;
  `frontend/src/api/endpoints/referralSaasReports.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the
  selected-customer Reports Prepare CSV and Download file UI over the TASK-328
  runtime routes. Operators can create the persisted export request, prepare a
  tenant-safe inline CSV file, see file metadata, and download the stored
  content without tenant-code entry, signed URLs, scheduled delivery, provider
  dispatch, invite/message delivery, credentials, auth/session changes,
  campaign activation, repair/replay/retry, billing, money, DLaaS, or
  source-fork side effects. Scores remain 9.99/10 for Referral Management and
  move to 9.997/10 for Campaign Attribution.
- TASK-330: `services/referral_saas_reporting_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `test/test_referral_saas_reporting_service.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Enforces
  report export retention expiry over the TASK-328/TASK-329 runtime. Expired
  export requests cannot be converted into files or downloaded, metadata is
  returned as expired without a download URL, and safe `409
  REPORT_EXPORT_FILE_EXPIRED` conflicts preserve no scheduled delivery,
  provider, credential/auth, campaign, billing, money, DLaaS, or source-fork
  side effects. Scores remain 9.99/10 for Referral Management and move to
  9.998/10 for Campaign Attribution.
- TASK-331: `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Defines the
  object-store/signed URL hardening contract for report exports. The contract
  requires opaque storage references, signed URL TTL bounded by retention,
  safe storage/signing failure states, audit evidence, no raw bucket/object
  paths or signing material in public responses, and no scheduled delivery,
  provider, credential/auth, campaign, billing, money, DLaaS, or source-fork
  side effects. Scores remain 9.99/10 for Referral Management and 9.998/10 for
  Campaign Attribution because runtime hardening remains the next task.
- TASK-332: `services/referral_saas_reporting_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `test/test_referral_saas_reporting_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the
  runtime signed-download layer for persisted customer-scoped report export
  files. Export file creation now stores an opaque storage reference and a
  short-lived signed download URL bounded by retention, public file metadata
  stays content-free and storage-safe, and no raw object path, bucket, signing
  material, tenant code, provider payload, credential/auth, campaign, billing,
  money, DLaaS, or source-fork side effect is exposed. Scores remain 9.99/10
  for Referral Management and move to 9.999/10 for Campaign Attribution.
- TASK-333: `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Defines the
  customer-scoped scheduled report delivery contract. The contract covers
  schedule routes, safe schedule fields, cadence, recipients, report/export
  readiness, signed URL and retention interaction, lifecycle states, safe
  error codes, audit/idempotency, and no-side-effect boundaries. Scores remain
  9.99/10 for Referral Management and 9.999/10 for Campaign Attribution
  because runtime schedule API/UI and governed provider execution remain open.
- TASK-334: `dp/migrations/090_referral_saas_report_delivery_schedules.sql`;
  `services/referral_saas_reporting_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `test/test_referral_saas_report_delivery_schedule_migration.py`;
  `test/test_referral_saas_reporting_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `test/test_referral_saas_route_smoke_plan.py`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the
  guarded customer-scoped scheduled report delivery API foundation. The backend
  now persists schedule intent/readiness, supports create/list/read/update and
  readiness inspection, records audit/idempotency evidence, keeps recipient
  references opaque, blocks unsafe raw delivery payloads, and confirms no live
  report delivery, email, webhook dispatch, credential/auth change, campaign
  activation, billing, money, DLaaS, or source-fork side effect. Scores remain
  9.99/10 for Referral Management and 9.999/10 for Campaign Attribution
  because selected-customer schedule UI and governed provider execution remain
  open.
- TASK-335: `frontend/src/api/endpoints/referralSaasReports.ts`;
  `frontend/src/api/endpoints/referralSaasReports.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_REPORTING_EXPORT_CONTRACT.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Wires
  selected-customer Reports to the scheduled report delivery API foundation.
  Operators can create schedule intent, list existing schedules, check
  readiness, pause/resume, and cancel without leaving customer context. The UI
  keeps cadence, timezone, format, recipient contact reference, retention, and
  no-live-delivery guardrails explicit. Scores remain 9.99/10 for Referral
  Management and 9.999/10 for Campaign Attribution because governed provider
  execution, repair/replay guardrails, progress/attribution mutation proof,
  governed auth/login completion, and non-local proof repetition remain open.
- TASK-336:
  `docs/sa/referral-saas/REFERRAL_SAAS_REPAIR_REPLAY_GUARDRAILS_CONTRACT.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_OPERATOR_SUPPORT_WORKFLOW.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Defines the
  governed repair/replay guardrails contract before any runtime command exists.
  The contract classifies read-only diagnostics, readiness-only answers,
  dry-run evidence, governed repair, governed replay, and hard-excluded
  actions; requires support-case linkage, actor, reason, correlation,
  idempotency, target evidence, before-state hash, redactions, audit, and
  side-effect boundaries; and explicitly blocks provider dispatch,
  credentials/auth changes, campaign activation, billing, money movement,
  broad DLaaS actions, and generic DB mutation consoles. Scores remain
  9.99/10 for Referral Management and 9.999/10 for Campaign Attribution
  because the runtime readiness API, progress/attribution mutation proof,
  governed provider execution, governed
  auth/login completion, and non-local proof repetition remain open.
- TASK-337:
  `services/referral_saas_support_case_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_support_case_repair_replay_readiness.py`;
  route smoke inventory; `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the
  read-only selected-customer support-case repair/replay readiness API. The
  route classifies diagnostic, governed repair, governed replay, and
  hard-excluded posture; returns required evidence, owning workflow, redactions,
  blocked reasons, and safe next posture; and confirms no repair, replay, retry,
  provider dispatch, credential/auth change, campaign activation, billing,
  money movement, or DLaaS action is performed.
- TASK-338:
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Wires the
  selected-customer Support UI to the read-only support-case repair/replay
  readiness API. Operators can select a support case, see safe diagnostic
  posture, blocked future governed repair/replay actions, required evidence
  counts, owning workflow navigation, and safe evidence rows while the UI
  exposes no repair/replay/retry/provider/auth/campaign/billing/money action.
  Scores remain 9.99/10 for Referral Management and 9.999/10 for Campaign
  Attribution because progress/attribution mutation proof, governed provider
  execution, governed auth/login completion, and non-local proof repetition
  remain open.
- TASK-339:
  `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_ATTRIBUTION_MUTATION_PROOF_CONTRACT.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_E2E_LIVE_VERIFICATION_PLAN.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Defines the
  selected-customer progress/attribution mutation proof contract. The contract
  requires the next runner to resolve a selected customer, prepare campaign and
  link/code evidence, validate referral entry, record progress events, prove
  dedupe replay, read attribution trace and customer-scoped reports, classify
  controlled failures, and confirm no provider/webhook/credential/invite/auth,
  support repair/replay, export delivery, billing, money, DLaaS, or source-fork
  side effects. Scores remain 9.99/10 for Referral Management and 9.999/10 for
  Campaign Attribution because runner implementation, recorded execution,
  governed provider execution, governed auth/login completion, and non-local
  proof repetition remain open.
- TASK-340:
  `scripts/referral_saas_progress_attribution_physical_check.py`;
  `test/test_referral_saas_progress_attribution_physical_check.py`;
  `scripts/referral_saas_selected_customer_mutation_e2e_physical_check.py`;
  `test/test_referral_saas_selected_customer_mutation_e2e_physical_check.py`;
  `scripts/README.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_ATTRIBUTION_MUTATION_PROOF_CONTRACT.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the
  repeatable TASK-340 proof runner. The runner reuses the selected-customer
  campaign/link/code mutation path, captures `referralTrackId`, records and
  replays `/v1/progress`, records a later milestone, reads progress status,
  attribution trace, and customer-scoped campaign report evidence, and fails on
  dedupe mismatch or unsafe adjacent payloads. Scores remain 9.99/10 for
  Referral Management and 9.999/10 for Campaign Attribution because TASK-341
  execution evidence, governed provider execution, governed auth/login
  completion, and non-local proof repetition remain open.
- TASK-341:
  `docs/sa/referral-saas/REFERRAL_SAAS_PROGRESS_ATTRIBUTION_MUTATION_PROOF_EXECUTION_TASK_341.md`;
  `scripts/referral_saas_progress_attribution_physical_check.py`;
  `apps/api/routers/progress.py`;
  `services/outcome_trace_service.py`;
  focused tests; script README, proof-contract, roadmap, gap-matrix, and
  infographic updates - Records passing local execution for selected-customer
  campaign/link/code setup, referral validation, identity capture,
  `/v1/progress` ingestion, dedupe replay, later milestone ingestion, progress
  status readback, attribution trace readback, and campaign report readback.
  The proof also fixes split admin/progress credentials, controlled progress
  4xx handling, and trace UUID/text readback defects while confirming no
  provider/webhook/invite/credential/auth/billing/money/DLaaS side effects.
  Scores remain 9.99/10 for Referral Management and move Campaign Attribution
  to 9.9995/10 because governed provider/vault execution, governed auth/login
  completion, and non-local proof repetition remain open.
- TASK-342:
  `docs/sa/referral-saas/REFERRAL_SAAS_PROVIDER_VAULT_RUNTIME_ADAPTER_CONTRACT.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Defines the
  shared provider/vault runtime adapter contract consumed first by Referral
  SaaS Integrations. The contract covers approved credential request execution
  readiness, opaque vault/provider references, adapter gates, failure taxonomy,
  audit/idempotency, redactions, UI-safe visibility, and no raw secret,
  provider dispatch, invite/webhook/message delivery, auth, campaign, billing,
  money, DLaaS, or source-fork side effects. Scores remain 9.99/10 for
  Referral Management and 9.9995/10 for Campaign Attribution at the time of
  completion because TASK-343 readiness API, TASK-344 UI visibility, governed
  auth/login completion, and non-local proof repetition were still open.
- TASK-343:
  `apps/api/routers/referral_saas_accounts.py`;
  `services/referral_saas_integrations_configuration_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `scripts/referral_saas_route_smoke_plan.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PROVIDER_VAULT_RUNTIME_ADAPTER_CONTRACT.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the
  read-only selected-customer provider/vault readiness API for Integrations.
  The API classifies active account posture, saved Integrations configuration,
  provider approval, approved credential requests, stale request versions, and
  missing/unapproved request blockers without exposing secrets, executing
  credential lifecycle work, writing a vault, calling providers, dispatching
  webhooks/messages, sending invites, changing auth, activating campaigns,
  billing, moving money, adding DLaaS scope, or duplicating source code. Scores
  remained 9.99/10 for Referral Management and 9.9995/10 for Campaign
  Attribution at the time of completion because TASK-344 UI visibility,
  governed provider/vault runtime execution, governed auth/login completion,
  and non-local proof repetition were still open.
- TASK-344:
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Wires the
  read-only provider/vault readiness model into the selected-customer
  Integrations Verify tab with plain-language handoff status, blockers,
  approved credential-request evidence, and explicit no-secret/no-live-action
  boundary copy. Scores remain 9.99/10 for Referral Management and move to
  9.9996/10 for Campaign Attribution because the visible provider/vault
  readiness gap is closed while governed provider/vault runtime execution,
  governed auth/login completion, and non-local proof repetition remain open.
- TASK-345:
  `docs/sa/referral-saas/REFERRAL_SAAS_AUTH_LOGIN_COMPLETION_CONTRACT.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Defines the
  governed auth/login completion boundary after named people, accepted customer
  access, and optional seat assignment. The contract separates confirmed
  customer work from actual platform sign-in readiness, defines candidate
  readiness/intent routes, allowed payloads, permission-profile mapping,
  account/membership/seat/provider gates, audit/idempotency, redactions, safe
  UI language, and explicit no credential, invite, auth-claim, campaign,
  billing, money, DLaaS, or source-fork side effects. Scores remain 9.99/10 for
  Referral Management and 9.9996/10 for Campaign Attribution because the
  contract gap is closed while the runtime API, UI wiring, governed
  provider/vault runtime execution, and non-local proof repetition remain open.
- TASK-346:
  `services/referral_saas_account_membership_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_AUTH_LOGIN_COMPLETION_CONTRACT.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PUBLIC_API_CONTRACT_MAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the
  governed auth/login completion API boundary. The readiness and intent routes
  are account-scoped and membership-scoped, enforce active account/link/reference
  and membership gates, require governed permission, seat, auth-provider,
  idempotency, audit, and redaction evidence, and record only safe
  login-completion intent/evidence in membership metadata and account audit
  events. No credential, invite, auth-claim, campaign activation, billing,
  money, DLaaS, or source-fork side effect is introduced. Scores remain
  9.99/10 for Referral Management and move Campaign Attribution to 9.9997/10
  because the backend auth/login API gap is closed while TASK-347 UI wiring,
  governed provider/vault runtime execution, and non-local proof repetition
  remain open.
- TASK-347:
  `frontend/src/api/endpoints/referralSaasAccounts.ts`;
  `frontend/src/api/endpoints/referralSaasAccounts.test.ts`;
  `frontend/src/api/queryKeys.ts`;
  `frontend/src/api/referralSaasAccountQueries.ts`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.tsx`;
  `frontend/src/pages/admin/ReferralSaasAccountMaintenancePage.test.tsx`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Wires the
  selected-customer People and Access UI to the governed auth/login completion
  readiness and intent API. Operators can see per-person login-completion
  posture after customer access and seat assignment, record login completion or
  login-not-required intent, see provider-evidence gating, and keep credentials,
  auth claims, invite delivery, campaign activation, billing, money, DLaaS, and
  source forks out of scope. Scores remain 9.99/10 for Referral Management and
  move Campaign Attribution to 9.9998/10 because the visible auth/login UI gap
  is closed while governed provider/vault runtime execution and non-local proof
  repetition remain open.
- TASK-349:
  `docs/sa/referral-saas/REFERRAL_SAAS_PROVIDER_VAULT_RUNTIME_EXECUTION_COMMAND_CONTRACT.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Defines the
  governed provider/vault runtime execution command contract after approved
  credential requests and visible readiness. The contract specifies
  selected-customer execution/read routes, allowed request payloads,
  no-adjacent-action confirmations, safe response states,
  approved-request/version/provider/vault gates, failure taxonomy,
  audit/idempotency, UI-safe copy, and explicit no raw secret, provider
  dispatch, invite/webhook/message delivery, auth/session change, campaign
  activation, billing, money, DLaaS, or source-fork side effects. Current rating
  remains 9.99/10 for Referral Management and 9.9998/10 for Campaign
  Attribution because this closes command-design ambiguity while runtime
  provider/vault execution and non-local proof repetition remain separate gaps.
- TASK-350:
  `apps/api/routers/referral_saas_accounts.py`;
  `services/referral_saas_integrations_configuration_service.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `test/test_referral_saas_route_smoke_inventory.py`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the
  governed provider/vault runtime execution API foundation after the TASK-349
  contract. The selected-customer routes record and read safe execution
  evidence, enforce approved credential request/version/provider/environment/
  capability gates, replay identical idempotent requests, reject changed
  payload reuse, and return blocked/not-implemented states without raw secret,
  provider dispatch, vault write, invite/webhook/message delivery, auth/session
  change, campaign activation, billing, money, DLaaS, or source-fork side
  effects. Current rating remains 9.99/10 for Referral Management and moves
  Campaign Attribution to 9.9999/10 because the runtime API boundary exists
  while real provider/vault adapters and non-local proof repetition remain
  separate gaps.
- TASK-351:
  `services/referral_saas_provider_vault_runtime.py`;
  `services/referral_saas_integrations_configuration_service.py`;
  `test/test_referral_saas_provider_vault_runtime.py`;
  provider/vault execution API tests;
  `docs/sa/referral-saas/REFERRAL_SAAS_PROVIDER_VAULT_RUNTIME_SEAM.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the
  shared provider/vault runtime adapter seam behind the governed execution API.
  The execution command now hands off to a registry that returns explicit
  adapter-not-configured, vault-not-configured, or adapter-ready states while
  preserving selected-customer scope, audit evidence, idempotency, redactions,
  and no raw secret/provider/vault/auth/campaign/billing/money side effects.
  Current rating remains 9.99/10 for Referral Management and moves Campaign
  Attribution to 9.99992/10 because the adapter handoff architecture exists
  while real provider/vault adapters and non-local proof repetition remain
  separate gaps.
- TASK-352:
  `docs/sa/referral-saas/REFERRAL_SAAS_PROVIDER_VAULT_ADAPTER_IMPLEMENTATION_PLAN.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Defines the
  provider/vault adapter implementation sequence after the TASK-351 seam. The
  plan selects a first `PLATFORM_REFERENCE` provider adapter and
  `PLATFORM_VAULT_REFERENCE` vault/reference adapter so the next code task can
  return real opaque references without browser-held secrets, vendor dispatch,
  invite/webhook/message delivery, auth/session changes, campaign activation,
  billing, money, DLaaS, or source-fork side effects. Current rating remains
  9.99/10 for Referral Management and moves Campaign Attribution to 9.99993/10
  because the implementation target is now bounded while runtime adapters and
  non-local proof repetition remain open.
- TASK-353:
  `services/referral_saas_provider_vault_runtime.py`;
  `test/test_referral_saas_provider_vault_runtime.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_PLATFORM_REFERENCE_PROVIDER_VAULT_ADAPTERS.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the
  first safe runtime provider/vault adapters behind the TASK-351 seam. Approved
  `PLATFORM_REFERENCE` execution can now return opaque provider and vault
  references for supported environments without exposing tenant/account/request
  identifiers, accepting raw secrets, calling vendors, writing live vault
  secrets, delivering invites/messages/webhooks, changing auth, activating
  campaigns, billing, moving money, expanding DLaaS, or forking source. Current
  rating remains 9.99/10 for Referral Management and moves Campaign Attribution
  to 9.99994/10 because platform-reference adapter code exists while vendor/
  managed adapters, repair/replay execution, and non-local proof repetition
  remain open.
- TASK-354:
  `docs/sa/referral-saas/REFERRAL_SAAS_VENDOR_MANAGED_PROVIDER_VAULT_ADAPTER_CONTRACT.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Defines the
  vendor/managed provider-vault adapter contract after the platform-reference
  runtime adapter. The contract separates vendor provider adapters, managed
  vault adapters, runtime execution states, required account/request/provider/
  vault/idempotency/audit/redaction gates, safe failure states, and no raw
  secret/provider dispatch/auth/campaign/billing/money side-effect boundaries.
  Current rating remains 9.99/10 for Referral Management and moves Campaign
  Attribution to 9.99995/10 because vendor/managed adapter ambiguity is closed
  while runtime implementation, repair/replay execution, and non-local proof
  repetition remain open.
- TASK-355:
  `services/referral_saas_provider_vault_runtime.py`;
  `test/test_referral_saas_provider_vault_runtime.py`;
  `docs/sa/referral-saas/REFERRAL_SAAS_VENDOR_MANAGED_PROVIDER_VAULT_ADAPTERS.md`;
  `docs/sa/referral-saas/README.md`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Adds the
  first built-in vendor/managed provider-vault runtime adapter path behind the
  shared execution seam. The adapter requires an explicit provider allowlist and
  managed-vault adapter configuration, returns opaque vendor/provider and
  managed-vault references, and preserves no raw secret, no vendor dispatch, no
  invite/message/webhook delivery, no auth, no campaign, no billing, no money,
  no DLaaS, and no source-fork side effects. Current rating remains 9.99/10 for
  Referral Management and moves Campaign Attribution to 9.99996/10 because the
  vendor/managed runtime implementation gap is closed while repair/replay
  command execution and non-local proof repetition remain open.
- TASK-358:
  `services/referral_saas_account_foundation_service.py`;
  `apps/api/routers/referral_saas_accounts.py`;
  `test/api/test_referral_saas_accounts_api.py`;
  `docs/roadmap/referral-saas/ROADMAP.md`;
  `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`;
  `docs/roadmap/ORDERED_TASK_LIST.md`;
  `outputs/referral-attribution-dlaas-roadmap-infographic.html` - Enforces
  selected-customer account, operating-jurisdiction, and account-read
  capability gates on the core Referral SaaS account resolver, membership
  posture, and membership activation readiness routes. Resolved account context
  now exposes operating jurisdiction safely, and cross-account,
  cross-jurisdiction, or missing-capability callers receive forbidden boundary
  responses without exposing tenant codes, auth claims, or internal tenant
  identifiers.

## Explicit Deferrals

The following are DLaaS expansion work, not blockers for this SaaS roadmap:

- distributor marketplace depth
- commission settlement
- funding operations
- fulfilment provider routing
- settlement batches
- sponsor billing
- white-label/embed
