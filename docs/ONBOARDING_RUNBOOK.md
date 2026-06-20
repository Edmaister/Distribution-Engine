# Onboarding Runbook

Use this runbook when preparing a pilot tenant, onboarding a partner client, or
enabling live communication channels. It is designed to produce release
evidence, not just setup notes.

## Entry Criteria

| Check | Standard |
| --- | --- |
| Release gates | Backend, frontend, migration, smoke, and security gates are green. |
| Permission matrix | `docs/API_PERMISSION_MATRIX.md` has been reviewed for the tenant and partner surfaces being enabled. |
| Secrets plan | Runtime secrets are owned by the deployment secret manager, not committed files or local notes. |
| Monitoring | API, database, queue, partner, audit, and channel telemetry destinations are available. |
| Rollback owner | A named owner can disable credentials, pause channels, and stop worker traffic. |

## Tenant Onboarding

| Step | Action | Evidence |
| --- | --- | --- |
| 1 | Confirm tenant code, legal entity, country, products, currency, and launch channels. | Tenant launch record |
| 2 | Provision tenant-bound partner, producer, distributor, consumer, and tenant-admin credentials as required. | Secret manager entries and access approval |
| 3 | Run migration baseline against a clean database before tenant-specific data is loaded. | CI or deployment migration log |
| 4 | Seed/bootstrap required tenant reference data, campaigns, journeys, reward rules, and marketplace records. | Bootstrap log and data-quality report |
| 5 | Validate tenant isolation with the core role smoke and permission tests. | Test output attached to release evidence |
| 6 | Confirm `/readyz`, `/healthz`, and the role workspaces load for the tenant. | Deployment smoke report |

Tenant data must not be promoted if wrong-tenant reads, missing secrets, failed
migrations, or critical data-quality issues are found.

## Partner Onboarding

| Step | Action | Evidence |
| --- | --- | --- |
| 1 | Create or approve the partner client for the tenant. | Client id and tenant mapping |
| 2 | Store the client secret once in the approved secret manager. | Secret manager audit entry |
| 3 | Confirm token exchange and `GET /partner/me` identity. | Token-flow smoke result |
| 4 | Configure webhook subscriptions for the agreed lifecycle events. | Subscription ids and callback URLs |
| 5 | Rotate or confirm webhook signing secrets before go-live. | Secret-readiness report |
| 6 | Queue and process a sandbox webhook delivery. | Delivery id with sent/delivered or expected sandbox response |
| 7 | Confirm the partner integration workspace shows credentials, webhooks, delivery evidence, and guardrails without exposing secrets. | Partner workspace screenshot or smoke output |

Partner credentials must remain tenant-bound. Partner clients must not be able
to access admin endpoints or another tenant's delivery records.

## Channel Setup

| Step | Action | Evidence |
| --- | --- | --- |
| 1 | Confirm consent, opt-out, data retention, and message templates for each launch channel. | Compliance approval |
| 2 | Configure provider credentials and callback URLs in the runtime secret manager. | Secret manager entries |
| 3 | Confirm channel readiness in the admin channel operations view or readiness endpoint. | Readiness result |
| 4 | Send sandbox or internal test messages for every enabled template. | Delivery evidence |
| 5 | Verify status capture for queued, sent, delivered, and failed outcomes where the provider supports it. | Callback or delivery log |
| 6 | Confirm retry and dead-letter handling for failed sends. | Retry/DLQ evidence |
| 7 | Confirm channel audit and metrics are visible to operations. | Audit row and metric snapshot |

Channels stay disabled for the tenant until consent checks, opt-out handling,
provider callbacks, and operational monitoring are all verified.

Sandbox WhatsApp/SMS proof command:

```bash
python scripts/channel_sandbox_smoke.py \
  --base-url https://api.example.com \
  --admin-key "$DISTRIBUTION_ADMIN_KEY" \
  --tenant-code FNB \
  --whatsapp-recipient "$SANDBOX_WHATSAPP_MSISDN" \
  --sms-recipient "$SANDBOX_SMS_MSISDN"
```

## Pilot Validation

| Journey | Validation |
| --- | --- |
| Consumer | Profile, progress, rewards, missions, leaderboard, and proof render through the consumer BFF. |
| Admin | Command centre health, events, funding, settlement, channels, and risks load through the admin BFF. |
| Sponsor | Billing, forecasts, contracts, utilisation, and alerts load through the sponsor BFF. |
| Distributor | Opportunities, wallet, routes, commissions, and performance load through the distributor BFF. |
| Partner | OAuth/token flow, webhook readiness, delivery evidence, and replay controls are available. |

Run the frontend smoke checks, backend smoke checks, and role journey smoke
against the target environment before pilot sign-off.

Pilot release evidence command:

```bash
python scripts/pilot_tenant_validation.py \
  --base-url https://api.example.com \
  --admin-key "$ADMIN_KEY" \
  --consumer-key "$CONSUMER_KEY" \
  --producer-key "$PRODUCER_KEY" \
  --distributor-key "$DISTRIBUTOR_KEY" \
  --tenant-code FNB \
  --referrer-ucn "$PILOT_REFERRER_UCN" \
  --producer-code "$PILOT_PRODUCER_CODE" \
  --distributor-code "$PILOT_DISTRIBUTOR_CODE" \
  --whatsapp-recipient "$SANDBOX_WHATSAPP_MSISDN" \
  --sms-recipient "$SANDBOX_SMS_MSISDN"
```

## Monitoring And Handover

| Area | Watch |
| --- | --- |
| API | Error rate, latency, readiness failures, and BFF aggregate failures |
| Database | Connection pressure, migration status, slow queries, and failed writes |
| Queues | Queue depth, DLQ depth, retry count, and worker lag |
| Partner | Webhook delivery latency, failed callbacks, replay attempts, and secret readiness |
| Channels | Send volume, delivery failures, provider latency, opt-outs, and callback errors |
| Audit | Admin action volume, failed audit writes, replay actions, and settlement approvals |

The handover pack should include tenant configuration, partner contacts,
channel provider contacts, monitoring links, smoke-test results, and rollback
steps.

## Rollback

If pilot validation fails:

1. Disable affected partner or channel credentials in the secret manager.
2. Pause outbound channel sends and webhook workers if external side effects are
   unsafe.
3. Stop tenant campaign activation or marketplace routing for the affected
   journey.
4. Preserve audit logs, delivery records, event inbox rows, and smoke-test
   output.
5. Re-run tenant isolation and readiness checks before re-enabling traffic.

Rollback completion is not accepted until the tenant can no longer trigger the
failed external side effect and the operations owner has confirmed monitoring is
quiet.
