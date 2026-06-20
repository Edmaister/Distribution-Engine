# Partner Seam

The partner seam is the platform-facing integration layer for external producers,
distributors, and enterprise systems. It sits alongside the current API-key model
while the product moves toward self-service partner onboarding.

## What Exists Now

- System admins can create tenant-scoped partner clients.
- Clients receive OAuth-style client credentials.
- Partners can exchange client credentials for a bearer token.
- Admins can create outbound webhook subscriptions for partner lifecycle events.
- The platform can queue webhook delivery records for a tenant and event type.
- Delivery records are queryable for support and operational follow-up.
- A worker can process due delivery records, sign payloads, update sent state,
  or schedule retry/failure outcomes.
- New webhook signing secrets are stored as protected application values. In
  production, configure `PARTNER_WEBHOOK_SECRET_PROVIDER`, `PARTNER_WEBHOOK_SECRET_KEY`,
  and/or `PARTNER_WEBHOOK_KMS_KEY_ID` before creating or sending webhooks.
  Set `PARTNER_WEBHOOK_SECRET_PROVIDER=MANAGED_KMS` and
  `PARTNER_WEBHOOK_KMS_BACKEND=AWS_KMS` to use AWS KMS for physical
  encrypt/decrypt operations.
- Partners can view a tenant-scoped integration overview that shows their
  client access, webhook subscriptions, recent delivery evidence, and guardrails
  without exposing client secrets or webhook signing secrets.
- Bearer-token partner clients can create their own webhook subscriptions and
  rotate webhook signing secrets without system-admin access.
- Tenant-scoped partner sessions can self-onboard OAuth-style client
  credentials for their own tenant. Bearer-token client sessions cannot create
  sibling clients.
- Partners can review failed/cancelled webhook delivery exceptions, and
  bearer-token partner clients can requeue their own failed/cancelled deliveries
  after correcting the endpoint. Partner and admin retry requests are audited as
  `PARTNER_WEBHOOK_DELIVERY_RETRY`.
- Partners can export failed/cancelled webhook delivery rows as a CSV
  dead-letter evidence file from the API or Partner Integration workspace.
- Partners can see repeated delivery-failure alerts grouped by endpoint and
  event type, with backend-owned severity and recommended action guidance.
- System admins can record in-app notification evidence for repeated delivery
  failure alerts, and partners can see the latest notification status in their
  integration workspace.
- Partners can see webhook signing-secret readiness, including whether runtime
  protection is local fallback, application-key based, managed-KMS local
  envelope, or AWS KMS backed, and whether legacy plaintext subscriptions still
  need rotation.
- Partners and system admins can read a backend-owned production readiness
  checklist that separates code-complete Partner Seam capability from live
  deployment configuration such as KMS keys and alert endpoints.

## Admin Onboarding Flow

1. Create a client with `POST /admin/partners/clients`.
2. Store the returned `client_secret` securely. It is only returned once.
3. Create webhook subscriptions with `POST /admin/partners/clients/{client_id}/webhooks`.
4. Store the returned `signing_secret` securely. It is only returned once.

Admin routes require a system-admin key.

## Partner Token Flow

Partners call `POST /oauth/token` with:

```json
{
  "grant_type": "client_credentials",
  "client_id": "fnb_example",
  "client_secret": "secret",
  "scope": "events:write referrals:read"
}
```

The API returns a bearer token:

```json
{
  "access_token": "token",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "events:write referrals:read",
  "tenant_code": "FNB"
}
```

Partners can verify token identity with `GET /partner/me`.

Partners can review their integration posture with `GET /partner/integration`.
The route accepts either a bearer token or the current tenant-scoped partner API
key while local role keys are still in use.

Partners can also read the concise readiness contract with
`GET /partner/readiness`. System admins can read the same contract with
`GET /admin/partners/readiness`.

Bearer-token partner clients can manage their own webhook credentials with:

```text
POST /partner/clients
POST /partner/webhooks
POST /partner/webhooks/{webhook_id}/rotate-secret
POST /partner/webhooks/rotate-legacy-secrets
GET /partner/webhook-deliveries/exceptions
GET /partner/webhook-deliveries/alerts
GET /partner/webhook-deliveries/dead-letter-export
POST /partner/webhook-deliveries/{delivery_id}/retry
GET /partner/webhooks/secret-readiness
```

Webhook creation, individual secret rotation, and delivery retry require a
client-scoped bearer token. Tenant-scoped partner sessions can onboard clients,
review integration health, and rotate legacy plaintext webhook secrets for
their own tenant. Bulk legacy rotation returns the new signing secrets once,
then the stored values remain protected.

The frontend exposes this as the **Partner Integration** workspace at
`/partner`, aligned to the Producer - Supply operating area.

## Webhook Delivery Queue

`POST /admin/partners/webhook-deliveries` queues delivery rows for all active
subscriptions matching `tenant_code` and `event_type`.

Pending delivery rows are processed by:

```bash
python -m apps.Workers.partner_webhook_worker
```

The worker signs each payload with `X-Amplifi-Signature`, sends it over HTTPS,
marks successful deliveries as `SENT`, keeps retryable failures `PENDING`, and
marks exhausted or non-retryable deliveries as `FAILED`.

System admins can also trigger a delivery pass with:

```text
POST /admin/partners/webhook-deliveries/process
```

System admins can review and notify repeated delivery-failure alerts with:

```text
GET /admin/partners/webhook-deliveries/alerts
POST /admin/partners/webhook-deliveries/alerts/notify
```

The notify action always records notification evidence. By default it records
in-app evidence with `channel=IN_APP`. To deliver the same alert to a physical
notification provider, call it with `channel=WEBHOOK` and configure:

```text
PARTNER_WEBHOOK_ALERT_NOTIFICATION_URL
PARTNER_WEBHOOK_ALERT_NOTIFICATION_SECRET
```

The optional secret signs the JSON body with `X-Amplifi-Signature`.

## Target-State Fit

This gives the platform a real partner integration boundary:

- **Producer - Supply** can use partner credentials and webhooks for campaign,
  outcome, funding, and settlement lifecycle events.
- **Distributor - Demand** can receive routed opportunity, acceptance, earning,
  and wallet lifecycle webhooks.
- **Amplifi Admin** can manage clients, subscriptions, and delivery exceptions
  without bespoke integration work per partner.
- **Partner Integration** gives external partners a self-service view of whether
  credentials, subscriptions, and webhook delivery are healthy before they need
  support intervention.

## Deployment Cutover

The Partner Seam is code-complete when the readiness contract returns
`code_status=READY`. Production cutover is environment configuration:

- Set `PARTNER_WEBHOOK_SECRET_PROVIDER=MANAGED_KMS`,
  `PARTNER_WEBHOOK_KMS_BACKEND=AWS_KMS`, and
  `PARTNER_WEBHOOK_KMS_KEY_ID` for physical KMS-backed webhook signing-secret
  protection.
- Set `PARTNER_WEBHOOK_ALERT_NOTIFICATION_URL` and, where required,
  `PARTNER_WEBHOOK_ALERT_NOTIFICATION_SECRET` for physical delivery-failure
  alert notifications.
