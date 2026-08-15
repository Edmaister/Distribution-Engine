# Referral SaaS UX/CX Maturity Scorecard

Product boundary: Referral SaaS.

Required boundary docs checked:

- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `docs/roadmap/ORDERED_TASK_LIST.md`

Supporting experience-design docs checked:

- `C:/Users/Carla/OneDrive/Documents/Referral Management and campaign attribution a-a-S/docs/amplifi-experience-design/simplified-experience-architecture.md`
- `C:/Users/Carla/OneDrive/Documents/Referral Management and campaign attribution a-a-S/docs/amplifi-experience-design/customer-journey-architecture-and-maturity.md`

## Purpose

TASK-395 starts the UX/CX hardening stream after the core Referral SaaS
capability, configurable journey path, and local E2E proof are in place. The
backend maturity is not reset by this work. This scorecard defines what the
customer and Amplifi Admin experience must feel like before the product can be
called world class.

The goal is simple: a user should understand each page in five seconds, know
what to do next, and never have to interpret raw platform state unless they ask
for diagnostic detail.

## Five-second contract

Every customer-facing Referral SaaS screen must answer these questions without
training or explanation:

| Question | UX standard |
| --- | --- |
| Where am I? | The selected customer, market, status, and page purpose are visible at the top. |
| What is this page for? | The page title and one-line description use business language, not service or schema language. |
| Is anything wrong or incomplete? | Red/amber/green states are plain-language and point to the exact responsible page. |
| What should I do next? | There is one primary next action, with secondary actions clearly lower priority. |
| Can I safely leave? | Saved, blocked, ready, or optional states are explicit, and no hidden live action is implied. |

## UX principles

| Principle | Required behavior |
| --- | --- |
| Customer context first | Select jurisdiction and customer before showing customer-scoped work. All actions stay inside that customer context until switched. |
| Separate work pages | Customer Home is a landing page. People, integrations, campaigns, reports, support, attribution, links, and health open as standalone pages. |
| One primary action | Each page has one dominant action or one clearly stated blocker. Competing equal-weight actions are avoided. |
| Plain language first | Labels explain business meaning first. Raw identifiers, guardrail names, route names, and technical statuses move to details or diagnostics. |
| Health maps to action | Every red or amber state names the matching page/action that resolves it. |
| Partner-simple, Amplifi-capable | Partner/customer users see task completion and safe status. Amplifi Admins can reveal evidence, diagnostics, and governed fallback actions. |
| Unsupported means unavailable | Future-state capabilities are not simulated. They are absent or labelled as separate future workflow. |
| No DLaaS leakage | Funding, settlement, payouts, sponsor billing, fulfilment, marketplace, and money movement stay outside Referral SaaS screens unless separately scoped. |

## Page scorecard

| Surface | Target UX | Current concern to watch | Next UX task |
| --- | --- | --- | --- |
| Account Setup | Create a new customer account foundation through a short guided path. Ends at customer home, not maintenance. | Review/save/internal gates can still feel like system ceremony if not collapsed into a single business action. | Covered by programme configuration tranche TASK-396 through TASK-405 |
| Customer Selection | Pick market, then customer, then open customer home. Customer cards show labelled identity, not raw duplicate strings. | Raw identifiers can look duplicated or unexplained. | Covered by programme configuration tranche TASK-396 through TASK-405 |
| Customer Home | Show customer health, the one next action, and service entry points. No stacked operational workflows. | Red/amber counts need obvious linked actions. | Covered by programme configuration tranche TASK-396 through TASK-405 |
| Account Health | Explain what blocks safe referral testing, what can wait, and which page fixes each item. | Health must not duplicate Customer Home without adding diagnostic value. | Covered by programme configuration tranche TASK-396 through TASK-405 |
| People and Access | Person-first list of required responsibilities, missing roles, confirmed people, optional login setup, and diagnostics behind disclosure. | Progress should be per person/responsibility, not a vague global bar. | Covered by programme configuration tranche TASK-396 through TASK-405 |
| Integrations | Replace "technical setup" language with a connection workspace: plan, request credentials, configure provider, test safely, approve readiness. | Provider/vault/adapter wording must not be the default user language. | Covered by programme configuration tranche TASK-396 through TASK-405 |
| Campaigns | Customer-scoped campaign list, create, configure, review, activate, pause/resume/end/archive with clear status and next action. | Campaign creation should feel like a business setup journey, not API wrapper exposure. | Covered by programme configuration tranche TASK-396 through TASK-405 |
| Links and Codes | Issue, reuse, validate, inspect, expire/revoke/reissue referral entry points for the selected campaign/customer. | Must keep campaign context obvious and validation outcomes plain. | Covered by programme configuration tranche TASK-396 through TASK-405 |
| Reports and Insights | Performance, funnels, exports, schedule intent, and journey analytics in one understandable insight model. | Reporting should avoid raw export lifecycle language unless in diagnostics. | Covered by programme configuration tranche TASK-396 through TASK-405 |
| Attribution | Separate campaign attribution and referral/referrer attribution, both explain "who/what got credit and why". | Confidence and missing evidence need plain-language explanations. | Covered by programme configuration tranche TASK-396 through TASK-405 |
| Support | Customer-scoped cases, notes, statuses, evidence links, and governed recovery requests. | Repair/replay controls must stay gated and not appear as ordinary user buttons. | Covered by programme configuration tranche TASK-396 through TASK-405 |

## Target information architecture

```text
Customers
  Account Setup
  Customer Profile
    Customer Home
    Account Health
    Customer Settings
    People and Access
    Integrations
    Campaigns
    Links and Codes
    Referrals
    Reports and Insights
    Attribution
    Support

Global
  Workspace Home
  Diagnostics
```

## Readiness language model

Use these plain-language states in the UI before exposing technical detail:

| State | User meaning | Expected action |
| --- | --- | --- |
| Ready | This part can be used now. | Continue or leave safely. |
| Needs attention | Something should be completed before smooth operation. | Open the named page and complete the shown action. |
| Blocking launch | This must be fixed before live referral testing or activation. | Fix first; do not present go-live as available. |
| Optional later | Useful, but not required for the current launch step. | Keep available but lower priority. |
| Diagnostic only | Evidence exists for operators or support. | Hide by default; reveal on request. |

## Controls

- Frontend wording must not invent backend states or imply unavailable actions.
- Readiness and permission decisions remain server-side.
- Customer-scoped pages must not expose internal tenant identifiers as primary
  labels.
- Admin-only fallback actions must require explicit evidence and remain
  visually separate from normal customer actions.
- Screens must remain usable without forcing users through unrelated DLaaS,
  finance, settlement, funding, fulfilment, or marketplace flows.

## Programme configuration UX requirements

The page-level CX standards above are still required, but they are now folded
into the programme-configuration roadmap instead of tracked as separate UX-only
task IDs. The next build layer is the customer-visible **Referral programme**
configuration model defined in
`docs/sa/referral-saas/REFERRAL_SAAS_PROGRAMME_CONFIGURATION_ROADMAP.md`.

The programme work keeps the product simple for customers:

- Customers configure a programme, not raw journey engine tables.
- Drafts, validation, review, publish, retire, and rollback are explicit.
- Campaigns are created from approved programme versions.
- Incentives, missions, badges, and leaderboard choices are selected from
  governed templates instead of edited as unsafe free-form rules.
- Diagnostics remain available to Amplifi Admin and support, not the default
  customer experience.

## Programme configuration backlog

| Task | Focus | Outcome |
| --- | --- | --- |
| TASK-396 | Programme configuration contract | Define the customer-facing programme object, version model, governance states, tenant scope, and simple UX language. |
| TASK-397 | Programme schema foundation | Add durable programme draft/version storage with immutable published snapshots and audit-ready metadata. |
| TASK-398 | Programme catalogue and draft APIs | Let customers and Amplifi Admins read available templates and save customer-scoped programme drafts. |
| TASK-399 | Programme validation and simulation | Validate drafts side-effect-free and show plain-language readiness, blockers, warnings, and projected outcomes. |
| TASK-400 | Programme review, publish, retire, and rollback | Add governed lifecycle controls so only approved programme versions can be used by campaigns. |
| TASK-401 | Campaigns from programme versions | Bind campaign setup to a published programme version instead of hand-picking raw journey logic. |
| TASK-402 | Incentive and engagement binding | Connect governed reward, mission, badge, and leaderboard template versions to programme versions. |
| TASK-403 | Runtime referral version binding | Ensure new referrals bind to the active programme version while historical referrals keep their original rules. |
| TASK-404 | Programme analytics and version comparison | Compare programme versions, campaign outcomes, funnel performance, and incentive impact. |
| TASK-405 | Simple Programme UX and E2E proof | Build the customer-facing Programme setup experience and prove customer-owned configuration end to end. |
