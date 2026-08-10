# Referral SaaS H1 Release Scope And Journey Gates

Task: TASK-357.
Product boundary: Referral SaaS.

Required boundary docs checked:

- `docs/product/referral-saas/PRODUCT_BRIEF.md`
- `docs/roadmap/referral-saas/ROADMAP.md`
- `docs/sa/referral-saas/REFERRAL_SAAS_GAP_MATRIX.md`
- `customer-journey-architecture-and-maturity.md`
- `production-readiness-matrix.md`

Shared primitive impact: This scope lock is consumed by later account,
workspace, entitlement, access, integrations, campaign, reporting, support, and
proof tasks. It does not fork source code.

## H1 Release Promise

H1 is a focused Referral Management and Campaign Attribution SaaS release. It
promises customer-scoped account setup, customer profile selection, people and
access responsibility management, integrations setup evidence, campaign setup
and controlled activation, referral link/code operation, referral progress,
campaign attribution, referral/referrer attribution, tenant-safe reporting, and
support/investigation.

H1 does not promise broad DLaaS marketplace distribution, fulfilment,
settlement, funding, sponsor billing, platform SaaS billing, white-label/embed,
or money movement unless those capabilities are separately contracted and
technically enabled behind their own gates.

## Enabled H1 Journeys

| Journey | H1 promise | Required gate evidence |
| --- | --- | --- |
| Establish the customer account | Amplifi Admin can create or select a Referral SaaS customer account with visible customer references, operating jurisdiction, and account status. | Account exists, account reference is unique, operating jurisdiction is known, account status is explicit, internal tenant identifiers stay hidden. |
| Enter customer context | Amplifi Admin works inside a selected customer profile; future partner users enter only authorised customer contexts. | Account context resolver, no cross-customer leakage, customer-scoped navigation and read models. |
| Manage people and access | Required customer responsibilities can be named, reviewed, accepted, and maintained; platform login remains separate unless enabled. | Named person, safe contact reference, responsibility, accepted-access evidence, optional seat/login posture. |
| Configure integrations | Customer API, webhook, invite-provider, referral-message, credential-request, and provider/vault readiness can be captured and verified as evidence. | Saved non-secret configuration, provider approval, credential request/review, readiness and execution evidence. |
| Create and activate campaigns | Customer-scoped campaigns can be created, configured, reviewed, approved, and activated only through server gates. | Account capability, policy evidence, review decision, activation decision, audit and idempotency evidence. |
| Operate links, codes, referrals, and progress | Referral entry points, validation, progress events, and referral status can be managed or investigated in customer context. | Account-scoped link/code evidence, stable idempotency, validation recovery, progress timeline, no unsafe identifiers. |
| Explain attribution | Campaign attribution and referral/referrer attribution are separate explainability views over shared evidence. | Account-safe source evidence, attribution trace, confidence/conflict posture, privacy controls. |
| Report and export | Customer-safe reports and exports can be prepared, downloaded, retained, expired, and scheduled where enabled. | Report scope, source freshness, export metadata, signed download, retention, delivery readiness. |
| Support and recover | Support can intake cases, inspect evidence, track status, and use governed recovery when implemented. | Case ownership, evidence links, safe notes/status, assignment, recovery approval and idempotency. |

## Deferred Or Disabled In H1

These are outside the H1 promise unless a later task explicitly enables them:

- distributor marketplace depth
- fulfilment routing and provider settlement
- sponsor billing, invoices, wallet funding, payouts, commissions, and money
  movement
- full platform SaaS billing beyond minimum entitlement posture
- broad white-label/embed
- raw secret display in the browser
- unmanaged provider dispatch
- direct database mutation or generic replay consoles
- identity-provider auth-claim propagation until the governed auth/login path is
  implemented and proven

Deferred features must be hidden, disabled, or labelled as separate workflow.
They must not appear as completed readiness.

## Release Gates

| Gate | Blocks launch when | Evidence required | Fail-closed behavior |
| --- | --- | --- | --- |
| Gate 0: Scope lock | A feature, role, channel, jurisdiction, vertical, or finance promise is not in the H1 scope decision. | Named H1 cohort, enabled journeys, disabled journeys, release owner, and launch limitations. | Hide or disable the capability and remove it from customer-facing promises. |
| Gate 1: Account and jurisdiction | Customer context is missing, duplicated, stale, or jurisdiction-only UI filtered. | Server-side account context, operating jurisdiction, account reference, capability checks, cross-account denial tests. | Deny customer-scoped commands and show the exact missing account/jurisdiction action. |
| Gate 2: Entitlement and environment | Production actions can run from POC/test posture or without active entitlement. | Contracted plan posture, environment lifecycle, expiry, entitlement audit, stale entitlement rejection. | Block production-capable commands and keep pilot/test labels visible. |
| Gate 3: People and access | Required responsibilities are missing or accepted access is confused with login/seat/auth provisioning. | Required roles named, safe contact reference, accepted-access evidence, optional seat/login state. | Keep campaign/live work blocked or limited and route to People and Access. |
| Gate 4: Integrations | API, webhook, invite, referral-message, credential, provider, or vault setup is unapproved or unverified for the promised action. | Saved config, provider approval, credential request decision, execution-readiness proof, no raw secrets. | Disable live integration actions and route to Integrations. |
| Gate 5: Campaign control | Campaign actions lack account capability, reviewed policy evidence, separation-of-duties posture, or activation decision. | Campaign setup evidence, policy/settings, review decision, activation audit, lifecycle state. | Keep campaign draft/review-only and block activation. |
| Gate 6: Referral and attribution correctness | Referral/progress/attribution lacks stable source evidence, idempotency, traceability, or safe identity handling. | Source event IDs, dedupe/replay evidence, account-scoped referral registry, trace readback, privacy redaction. | Reject unsafe events or show investigation-only state. |
| Gate 7: Reporting and support | Reports, exports, schedules, or support actions expose unsafe data or imply unproven delivery/recovery. | Report source contracts, export storage/download/retention, schedule delivery proof, support case audit, recovery approval. | Limit to safe read-only/status surfaces and disable unproven delivery/recovery. |
| Gate 8: Deployed-state proof | The release has only local/static proof for a production claim. | Migration replay, smoke routes, live/staging DB readback, cross-tenant/wrong-role negative tests, residual limitation log. | Do not call the release production-ready. |

## Role Scope

| Actor | H1 allowed posture |
| --- | --- |
| Amplifi Admin | Can onboard, activate, support, inspect, and configure within permitted customer scope. |
| Customer or partner admin | Future self-service actor; can operate only the accounts resolved from their membership and capability grants. |
| Campaign manager | Future self-service actor; can create and manage campaigns only where account capability and campaign gates allow. |
| Technical admin | Future self-service actor; can configure integrations only where account capability and provider/vault gates allow. |
| Support operator | Can inspect safe evidence and work support cases; recovery commands remain governed and case-linked. |
| Finance actor | Outside H1 unless separately contracted and isolated behind finance capability gates. |

## Plain-Language UX Contract

Every H1 customer page must answer these questions within five seconds:

- Which customer am I working on?
- Is this customer ready, blocked, or waiting?
- What is the one next action?
- Why does the action matter?
- What is deliberately not happening here?

The frontend may compose information for clarity, but it must not infer
authoritative readiness, entitlement, permission, production activation, or
money decisions. Those decisions must come from server-side gates.

## Downstream Enforcement

TASK-358 through TASK-381 must use this scope lock as their boundary:

- account, jurisdiction, capability, and entitlement tasks enforce Gates 1 and
  2
- invitation, acceptance, login, and access tasks enforce Gate 3
- integrations tasks enforce Gate 4
- campaign tasks enforce Gate 5
- referral, progress, and attribution tasks enforce Gate 6
- reporting, support, recovery, finance isolation, and proof tasks enforce
  Gates 7 and 8

Any future task that enables a deferred H1 item must update this document,
the gap matrix, the roadmap, tests, and customer-facing UX labels.
