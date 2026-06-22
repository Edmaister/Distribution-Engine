# Partner And Customer Safe Status Contract

Status: Accepted for TASK-023.

This document defines safe status and action-required categories for partner, distributor, sponsor/producer, referrer, and customer-facing DLaaS surfaces. It is a contract only: it does not add routes, schema, migrations, frontend screens, or state-mutating workflows.

## Problem Statement

Current backend sources expose many raw statuses across referral outcomes, rewards, distributor commissions, wallets, funding, fulfilment, settlement, webhooks, and audit. Those statuses are useful for operators, but they are not all safe or meaningful for partners, distributors, sponsors, referrers, or customers.

Portal and public surfaces need a stable answer to four questions:

- what happened;
- what happens next;
- whether action is required;
- which backend state family supports the answer.

They must answer those questions without exposing raw provider failures, DLQ details, settlement internals, private identifiers, secrets, or unrestricted audit metadata.

## Decision

Define a derived safe-status contract for role-scoped partner/customer surfaces. The contract is additive and read-only. It maps current source statuses and evidence families into safe categories, action-required categories, and source-family references.

Raw source statuses remain the backend source of truth. Future portal APIs may include raw status only for operator-safe surfaces. Partner/customer-safe responses must expose derived safe statuses and bounded evidence references.

## Non-Goals

- No new route, schema, migration, seed, or frontend implementation is added by TASK-023.
- No reward, commission, funding, fulfilment, settlement, liability, webhook, audit, or tenant record is mutated.
- No money movement, replay, repair, retry, reversal, fulfilment, settlement approval, or payout command is part of this task.
- No public/external endpoint is authorized by this document alone.

## Roles And Visibility

| Role surface | Safe visibility | Must not expose |
| --- | --- | --- |
| `customer` | Own journey/outcome progress, safe reward/fulfilment status, action required, next step. | Raw UCNs, distributor internals, funding accounts, settlement internals, provider errors, DLQ, audit payloads. |
| `referrer` | Own referral progress, safe reward status, reward fulfilment status, action required, next step. | Referee private identifiers, raw fraud/risk flags, provider payloads, settlement internals, funding account internals. |
| `distributor` | Own offers, routes, conversions, commission, wallet credit, payout/settlement readiness, safe action required. | Other distributors, raw customer identifiers, sponsor funding account internals, raw settlement/provider internals, DLQ payloads. |
| `partner` | Tenant/client-scoped campaign, event, webhook, outcome, reward summary, and integration health in safe form. | Cross-tenant data, secrets, signing material, raw worker errors, raw provider payloads, private participant identifiers. |
| `sponsor` / `producer` | Own campaign/funding/sponsor-billing status, safe liability or invoice summary where authorized. | Customer private identifiers, distributor internals outside authorized campaign context, funding account internals not intended for portal use. |

Operator/admin surfaces are outside this contract except where they generate role-safe views for support.

## Safe Status Vocabulary

Use these top-level safe statuses for partner/customer-facing surfaces:

| Safe status | Meaning | Typical source families |
| --- | --- | --- |
| `NOT_STARTED` | The relevant journey, fulfilment, payment, delivery, or settlement work has not begun. | Outcome, reward, fulfilment, settlement, webhook. |
| `PENDING` | Work is waiting for required events, checks, funding, fulfilment, settlement, or partner action. | Outcome, reward, commission, funding, fulfilment, settlement, webhook. |
| `IN_PROGRESS` | Work is actively processing or retryable without user-visible failure details. | Event, reward, commission, fulfilment, settlement, webhook. |
| `QUALIFIED` | The outcome or participant has met qualification requirements, but downstream money/fulfilment may still be pending. | Qualification, outcome, reward, commission. |
| `APPROVED` | A decision has been approved or accepted, but final delivery or settlement may still be pending. | Reward, commission, route, invoice, settlement approval. |
| `FULFILLED` | The relevant reward, benefit, commission credit, or value delivery is complete from the user-visible perspective. | Reward, fulfilment, wallet, commission. |
| `SETTLED` | The relevant payment, payout, or invoice settlement is complete from the authorized role's perspective. | Settlement, wallet, invoice, sponsor billing. |
| `ADJUSTED` | A visible correction, reversal, credit, debit, or settlement adjustment occurred. | Reward, wallet, funding, settlement, invoice. |
| `DECLINED` | A route, offer, qualification, reward, or request was declined or not approved. | Route, qualification, policy, reward. |
| `EXPIRED` | The opportunity, link, offer, or campaign window is no longer valid. | Campaign, route, link/code. |
| `ACTION_REQUIRED` | The viewer or support team must take action, or support must be contacted. | Outcome, reward, fulfilment, settlement, webhook, funding, profile/onboarding. |
| `UNAVAILABLE` | Current source truth cannot safely show a status. | Missing evidence, redaction, unavailable source. |

Do not expose source status strings such as `FAILED_RETRYABLE`, `FAILED_FINAL`, `DLQ`, provider failure codes, settlement exception internals, or webhook worker error details to partner/customer-safe surfaces.

## Action-Required Categories

| Category | Meaning | Safe for |
| --- | --- | --- |
| `NONE` | No action required from the viewer. | All roles. |
| `COMPLETE_PROFILE` | Viewer must complete onboarding, profile, compliance, or payment setup. | Distributor, sponsor/producer, partner, customer where applicable. |
| `ACCEPT_OFFER` | Distributor or partner must accept, decline, or review an offer/route. | Distributor, partner. |
| `SUBMIT_EVENT` | Partner must submit or correct an expected source event. | Partner. |
| `WAITING_FOR_EVENT` | The system is waiting for backend evidence; no immediate viewer action. | All roles. |
| `CONTACT_SUPPORT` | Support review is required; raw failure details remain hidden. | All roles. |
| `RETRY_LATER` | A retry or downstream process is still active; no raw retry internals exposed. | All roles. |
| `VERIFY_PAYMENT_DETAILS` | Payment, wallet, or billing details require review. | Distributor, sponsor/producer, referrer/customer where applicable. |
| `REVIEW_DISPUTE` | A visible dispute or adjustment requires review without exposing settlement internals. | Distributor, sponsor/producer, partner. |
| `NOT_AVAILABLE` | The platform cannot safely determine action from current evidence. | All roles. |

## Source Family Mapping

| Source family | Current source truth | Safe status guidance |
| --- | --- | --- |
| Outcome/referral | `referral_instances`, progress events, outcome trace. | `NOT_STARTED`, `PENDING`, `IN_PROGRESS`, `QUALIFIED`, `FULFILLED`, `ACTION_REQUIRED`, `UNAVAILABLE`. |
| Campaign/link/route | Marketing campaigns, campaign links, route referral links, opportunities, offer routes. | `PENDING`, `APPROVED`, `DECLINED`, `EXPIRED`, `ACTION_REQUIRED`, `UNAVAILABLE`. |
| Reward | `rewards`, `referral_rewards`, reward summaries. | `PENDING`, `APPROVED`, `IN_PROGRESS`, `FULFILLED`, `ADJUSTED`, `ACTION_REQUIRED`, `UNAVAILABLE`. |
| Commission | `distribution_commission_events`, distributor wallet evidence. | `PENDING`, `APPROVED`, `FULFILLED`, `ADJUSTED`, `ACTION_REQUIRED`, `UNAVAILABLE`. |
| Funding/liability | Liability projection, funding reservations/allocations where safe and authorized. | `PENDING`, `IN_PROGRESS`, `APPROVED`, `ADJUSTED`, `ACTION_REQUIRED`, `UNAVAILABLE`; do not expose funding account internals externally. |
| Fulfilment | `fulfilment_audit`, `services/fulfilment_safe_status.py`. | Use external-safe mapping: `PENDING`, `IN_PROGRESS`, `FULFILLED`, `ACTION_REQUIRED`, `UNAVAILABLE`. |
| Settlement | Settlement ledger/batch/exception/reversal evidence, `services/fulfilment_safe_status.py`. | Use external-safe mapping: `PENDING`, `IN_PROGRESS`, `SETTLED`, `ADJUSTED`, `ACTION_REQUIRED`, `UNAVAILABLE`. |
| Wallet/billing | Distributor wallets, sponsor billing, invoices, receipts. | `PENDING`, `IN_PROGRESS`, `SETTLED`, `ADJUSTED`, `ACTION_REQUIRED`, `UNAVAILABLE`. |
| Webhook/integration | Partner seam subscriptions, deliveries, alerts, event catalog. | `PENDING`, `IN_PROGRESS`, `FULFILLED` for delivered/healthy, `ACTION_REQUIRED` for tenant/client-visible configuration or support issues, `UNAVAILABLE` for hidden details. |
| Missing evidence | Outcome trace and liability missing-evidence contracts. | `UNAVAILABLE` or `ACTION_REQUIRED`, with safe `missing_evidence` code only when role-authorized. |

## Current Status Mapping

### Fulfilment

External-safe fulfilment mapping is implemented in `services/fulfilment_safe_status.py` and must remain the source for fulfilment safe statuses.

| Source status | Partner/customer safe status | Action guidance |
| --- | --- | --- |
| `PENDING` | `PENDING` | `WAITING_FOR_EVENT` or `NONE` depending on journey context. |
| `PROCESSING` | `IN_PROGRESS` | `RETRY_LATER` or `NONE`. |
| `SUCCESS` | `FULFILLED` | `NONE`. |
| `FAILED_RETRYABLE` | `IN_PROGRESS` | `RETRY_LATER`; do not expose retry/failure internals. |
| `FAILED_FINAL` | `ACTION_REQUIRED` | `CONTACT_SUPPORT`. |
| `DLQ` | `ACTION_REQUIRED` | `CONTACT_SUPPORT`; do not expose DLQ details. |
| `SKIPPED_DUPLICATE` | `FULFILLED` | `NONE`; do not expose duplicate internals. |
| Unknown | `UNAVAILABLE` | `NOT_AVAILABLE`. |

### Settlement

External-safe settlement mapping is implemented in `services/fulfilment_safe_status.py` and must remain the source for settlement safe statuses.

| Source status | Partner/customer safe status | Action guidance |
| --- | --- | --- |
| `PENDING` | `PENDING` | `WAITING_FOR_EVENT` or `NONE`. |
| `PROCESSING` | `IN_PROGRESS` | `RETRY_LATER` or `NONE`. |
| `SETTLED` | `SETTLED` | `NONE`. |
| `FAILED` | `ACTION_REQUIRED` | `CONTACT_SUPPORT`. |
| `REVERSED` | `ADJUSTED` | `REVIEW_DISPUTE` or `CONTACT_SUPPORT` depending role. |
| `DISPUTED` | `ACTION_REQUIRED` | `REVIEW_DISPUTE`. |
| Unknown | `UNAVAILABLE` | `NOT_AVAILABLE`. |

### Reward

| Source status | Safe status | Action guidance |
| --- | --- | --- |
| `APPLIED` | `APPROVED` | `NONE` unless downstream fulfilment is missing. |
| `EARNED` | `QUALIFIED` | `NONE` or `WAITING_FOR_EVENT` for downstream fulfilment. |
| `PENDING_FULFILMENT` | `IN_PROGRESS` | `RETRY_LATER` or `NONE`. |
| `FULFILLED` | `FULFILLED` | `NONE`. |
| `FAILED` | `ACTION_REQUIRED` | `CONTACT_SUPPORT`; do not expose provider error details. |
| `REVERSED` | `ADJUSTED` | `CONTACT_SUPPORT` or `REVIEW_DISPUTE` depending role. |
| Unknown/missing | `UNAVAILABLE` | `NOT_AVAILABLE`. |

### Distributor Commission And Wallet

| Source status | Safe status | Action guidance |
| --- | --- | --- |
| `CALCULATED` | `APPROVED` | `WAITING_FOR_EVENT` if wallet credit/payout is pending. |
| `CREDITED` | `FULFILLED` | `NONE`. |
| Wallet credit posted | `FULFILLED` | `NONE`. |
| Payout/settlement pending | `PENDING` or `IN_PROGRESS` | `WAITING_FOR_EVENT`. |
| Reversal/adjustment evidence | `ADJUSTED` | `REVIEW_DISPUTE` or `CONTACT_SUPPORT`. |
| Unknown/missing | `UNAVAILABLE` | `NOT_AVAILABLE`. |

### Webhook And Integration

| Source status | Safe status | Action guidance |
| --- | --- | --- |
| Subscription `ACTIVE` | `APPROVED` | `NONE`. |
| Subscription `PAUSED` | `ACTION_REQUIRED` | `CONTACT_SUPPORT` or integration owner review. |
| Subscription `REVOKED` | `ACTION_REQUIRED` | `CONTACT_SUPPORT`. |
| Delivery `PENDING` | `PENDING` | `WAITING_FOR_EVENT`. |
| Delivery `SENT` | `FULFILLED` | `NONE`. |
| Delivery `FAILED` | `ACTION_REQUIRED` | `CONTACT_SUPPORT`; expose only safe failure category. |
| Delivery `CANCELLED` | `ADJUSTED` | `CONTACT_SUPPORT` if unexpected. |

## Recommended Response Shape

Future role-safe APIs should return a compact status object per visible entity or section:

```json
{
  "status": "ok",
  "tenant_code": "FNB",
  "viewer_role": "distributor",
  "subject": {
    "type": "outcome",
    "safe_ref": "outcome:referral_track_id:11111111-1111-4111-8111-111111111111"
  },
  "safe_status": {
    "status": "IN_PROGRESS",
    "label": "In progress",
    "summary": "Your reward is being processed.",
    "what_happened": "The qualifying event was received and reward processing has started.",
    "what_happens_next": "The platform will update this status when fulfilment completes.",
    "action_required": false,
    "action_category": "NONE",
    "terminal": false,
    "source_families": ["outcome", "reward", "fulfilment"],
    "source_confidence": "MEDIUM",
    "missing_evidence": [],
    "redactions": ["provider_payload", "private_identifier"]
  }
}
```

The response may include multiple `safe_statuses` for sections such as campaign, reward, commission, fulfilment, settlement, wallet, webhook, and billing. It must not include raw status fields unless the route is explicitly operator-only.

## Missing Evidence Handling

Partner/customer-safe APIs may expose missing evidence only in bounded form:

| Missing evidence code | Safe status | Safe action category |
| --- | --- | --- |
| `SECTION_NOT_REQUESTED` | Do not expose unless useful to the caller. | `NONE`. |
| `NO_SOURCE_EVIDENCE` | `PENDING` or `UNAVAILABLE` depending expected evidence. | `WAITING_FOR_EVENT` or `NOT_AVAILABLE`. |
| `JOIN_AMBIGUOUS` | `UNAVAILABLE`. | `CONTACT_SUPPORT` for user-visible stuck states; otherwise `NOT_AVAILABLE`. |
| `SOURCE_UNAVAILABLE` | `UNAVAILABLE`. | `RETRY_LATER` or `CONTACT_SUPPORT`. |
| `SOURCE_CONFLICT` | `ACTION_REQUIRED`. | `CONTACT_SUPPORT`. |
| `REDACTED` | `UNAVAILABLE`. | `CONTACT_SUPPORT` only if user action can help. |
| `NOT_APPLICABLE` | Do not expose as a problem. | `NONE`. |

## API Guardrails

Future partner/customer-safe status APIs must:

- use role-scoped auth helpers from `docs/API_PERMISSION_MATRIX.md`;
- derive tenant scope from credentials for non-admin callers;
- validate participant ownership before returning a status;
- use read-only, side-effect-free GET behavior for status lookups;
- return 401 for missing/invalid credentials and 403 for adjacent-role or cross-tenant access;
- return 404 for inaccessible subjects rather than confirming another tenant's resource exists;
- include safe error envelopes and bounded validation details;
- avoid idempotency keys for reads;
- require audit, idempotency, and a separate command contract for any action that mutates state.

## Redaction Rules

Partner/customer-safe status responses must not expose:

- raw UCNs or private customer identifiers;
- provider payloads, provider error bodies, stack traces, or worker exceptions;
- DLQ payloads or retry internals;
- settlement provider internals, exception payloads, approval notes, or reversal internals;
- funding account internals or wallet internals outside the viewer's authorized scope;
- API keys, signing secrets, tokens, webhook secret material, or credential metadata;
- unrestricted audit before/after payloads or internal actor metadata.

## Future Implementation Notes

- A future helper should derive role-safe statuses from outcome trace and liability projection data, rather than duplicating raw source queries in each portal route.
- Existing fulfilment and settlement safe mappings should remain reusable source truth for those source families.
- Partner/customer portal APIs should return status sections by role, not a full operator trace.
- Public/external APIs must not expose the `admin_outcomes` route or operator trace payload directly.
- Notification copy should use this safe status vocabulary and action-required categories, not raw backend statuses.

## Validation Notes

TASK-023 validation is documentation readback only. Current code already supports source trace, liability projection, and external-safe fulfilment/settlement mappings. Broader partner/customer safe status implementation remains a later task.
