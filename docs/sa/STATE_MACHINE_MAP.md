# State Machine Map

## Source Of Truth

This map records current state fields and statuses found in schema and service code. Target recommendations are labeled separately.

Audit, idempotency, retry, and failure handling policy for future state-machine work is defined in `docs/sa/AUDIT_RETRY_POLICY_STANDARD.md`.

## Current State Machines

| Entity | Source of truth | Current states observed | Current transition owners |
| --- | --- | --- | --- |
| Referral instance | `referral_instances.status`; migration `016_fix_referral_instances_status_constraint.sql`; referral/progress services | Referral status values are constrained in migrations; journey events update progress toward completion. Inspect migration/service before changing values. | Referral validation, progress ingestion, worker processing. |
| Campaign track | `campaign_track_events.status`; campaign services/routes | `SCANNED`, `VALIDATED`, `ATTRIBUTED`, `COMPLETED`, `BLOCKED`, `EXPIRED`, `INVALID` observed in implementation history. | Campaign validation, tracking, attribution, completion updates. |
| QR/campaign scan | `referral_qr_scans.status`, `campaign_qr_scans.status` | Scan-specific statuses are defined by migration checks. | Public scan/validation flows. |
| Reward | `rewards.status`; `services/reward_service.py` | `APPLIED`, `EARNED`, `PENDING_FULFILMENT`, `FULFILLED`, `FAILED`, `REVERSED` observed in service behavior. | Reward application, journey completion, fulfilment processing, reversal/repair actions. |
| Distributor | `distribution_distributors.distributor_status` | `ONBOARDING`, `ACTIVE`, `SUSPENDED`, `TERMINATED` observed in distribution services/docs. | Distribution admin onboarding/governance actions. |
| Distribution opportunity | `distribution_opportunities.opportunity_status` | `DRAFT`, `PUBLISHED`, `CLOSED` observed in distribution services/docs. | Distribution admin create/publish/close/reopen. |
| Offer route | `distribution_offer_routes.route_status` | `ROUTED`, `ACCEPTED`, `DECLINED` observed in distribution services/docs. | Admin routing and distributor portal accept/decline. |
| Route referral link | `distribution_route_referral_links.link_status` | `ACTIVE`, `VOIDED` observed in migration check. | Route/link generation and voiding logic. |
| Commission event | `distribution_commission_events.commission_status` | `CALCULATED`, `CREDITED` observed in distribution services/docs. | Commission calculation and optional wallet credit. |
| Funding reservation | `funding_reservations.status` | `RESERVED`, `RELEASED`, `SETTLED` observed in funding services. | Funding orchestrator, release/settlement operations. |
| Sponsor allocation | marketplace funding allocation state | `RESERVED`, `RELEASED`, `DEBITED`, `REVERSED` observed in funding docs/services. | Marketplace funding services. |
| Funding contract | `funding_contracts.status` | `ACTIVE`, `SUSPENDED`, `CANCELLED` observed in funding contract services/docs. | Finance/funding admin operations. |
| Fulfilment | fulfilment status fields/services | `PENDING`, `PROCESSING`, `SUCCESS`, `FAILED_RETRYABLE`, `FAILED_FINAL`, `DLQ`, `SKIPPED_DUPLICATE` observed in fulfilment status service. | Fulfilment workers, retry scheduler, replay/admin actions. |
| Settlement | settlement status fields/services | `PENDING`, `PROCESSING`, `SETTLED`, `FAILED`, `REVERSED`, `DISPUTED` observed in settlement status code/docs. | Finance settlement services/admin actions. |
| Settlement batch | settlement batch status | `DRAFT`, `READY_FOR_APPROVAL`, `APPROVED`, `PROCESSING`, `SETTLED` observed in settlement services/docs. | Finance admin batch workflow. |
| Settlement approval | settlement approval status | `PENDING`, `APPROVED`, `REJECTED` observed in settlement approval services/docs. | Finance admin approval/rejection. |
| Enterprise event inbox | `enterprise_event_inbox.processing_status` | `RECEIVED`, `QUEUED`, `IGNORED`, `FAILED`, `DUPLICATE` observed in inbox services/docs. | Enterprise event ingestion, queueing, replay. |
| Partner client | `partner_clients.status` | `ACTIVE`, `SUSPENDED`, `REVOKED` in `077_partner_seam.sql`. | Partner/admin credential management. |
| Webhook subscription | `partner_webhook_subscriptions.status` | `ACTIVE`, `PAUSED`, `REVOKED` in `077_partner_seam.sql`. | Partner/admin webhook management. |
| Webhook delivery | `partner_webhook_deliveries.delivery_status` | `PENDING`, `SENT`, `FAILED`, `CANCELLED` in `077_partner_seam.sql`. | Webhook worker, retry actions, admin/partner actions. |
| Admin audit event | `admin_audit_log` | Audit rows are event records, not lifecycle entities. | Admin/audit service writes. |

## Target Canonical State Layers

| Target entity | Recommendation | Traces to gaps |
| --- | --- | --- |
| Campaign | Define canonical lifecycle over current campaign/opportunity concepts without deleting existing statuses. TASK-006 maps this in `docs/sa/CAMPAIGN_OPPORTUNITY_LIFECYCLE_MAP.md`; TASK-007 defines readiness states and blocker categories in `docs/sa/CAMPAIGN_READINESS_SERVICE_CONTRACT.md`. | GAP-02 |
| Participant | Normalize partner/referrer/distributor/sponsor/customer status for control plane and portal use. TASK-008 maps current participant sources and permission boundaries in `docs/sa/PARTICIPANT_TAXONOMY_PERMISSION_MAP.md`. | GAP-03 |
| Distribution link/code | Define canonical `issued/active/resolved/linked/voided/expired/invalid/unknown` semantics mapped to current referral, campaign, campaign-referral, composite, and route link sources. TASK-009 defines this in `docs/sa/LINK_CODE_CONTRACT.md`. | GAP-04 |
| Attribution/outcome | Add or derive a canonical outcome state from current campaign track, referral instance, progress events, reward, commission, funding, fulfilment, settlement, and audit records. TASK-010 defines the response contract and trace-completeness values in `docs/sa/OUTCOME_TRACE_RESPONSE_CONTRACT.md`. | GAP-05 |
| Qualification decision | Capture qualification result, source events, rule version, and auditability as a target-state recommendation. | GAP-07 |
| Money lifecycle | Normalize operator-facing statuses for calculated liability, reserved funding, fulfilled reward/commission, settled amount, reversed/disputed/failed states. | GAP-08, GAP-09, GAP-10 |
| Integration delivery | TASK-012 defines the public event ingestion contract in `docs/sa/EVENT_INGESTION_PUBLIC_CONTRACT.md`; later work must publish the DLaaS outbound webhook event catalog mapped to partner seam delivery states. | GAP-12, GAP-13 |

## Customer/Partner Visibility Rules

- Customer-visible statuses should be derived and safe: pending, in progress, approved, fulfilled, failed, action required.
- Partner/distributor statuses should show campaign availability, routed offers, accepted offers, conversions, earnings, wallet movement, payout/settlement readiness, and failed/action-required states.
- Internal states such as fraud flags, raw provider errors, DLQ payloads, settlement exceptions, and audit internals should remain operator-visible only unless explicitly transformed into safe copy.

## Missing Or Ambiguous States

| ID | Issue | Impact | Trace |
| --- | --- | --- | --- |
| SM-GAP-01 | No implemented canonical distribution outcome state or trace service. TASK-010 now defines the response shape and missing-evidence taxonomy, but implementation remains in TASK-011. | Hard to build reusable UX, reporting, webhooks, and support trace until the service is implemented and joins are verified. | GAP-05 |
| SM-GAP-02 | Campaign lifecycle is split between marketing campaigns and distribution opportunities. | Campaign builder/control plane may make invalid assumptions. | GAP-02 |
| SM-GAP-03 | Reward and commission lifecycles are related but separate. | Money reporting can double-count or hide obligations if not reconciled. | GAP-08 |
| SM-GAP-04 | Multiple audit tables exist without one canonical state-transition event taxonomy. | Operator investigations require domain-specific joins. | GAP-11 |
| SM-GAP-05 | Customer/partner-safe status mapping is not the source of truth. | Frontend may expose internal or confusing statuses. | GAP-15 |
