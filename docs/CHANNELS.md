# Channel Provider Adapters

Outbound WhatsApp, SMS, and USSD sends use explicit provider adapters instead of a
generic payload shape. The dispatch service still owns validation, metrics, and
provider configuration checks; adapters own provider-specific request bodies,
signing headers, and provider identity.

## Delivery Lifecycle

Every live messaging dispatch now creates an operational delivery record before
provider handoff. The lifecycle supports:

- `QUEUED` when the message is accepted for outbound processing.
- `SENT` when the provider accepts the request.
- `FAILED` when the provider rejects or errors the request.
- `DELIVERED` when a signed provider callback confirms downstream delivery.
- `DEAD_LETTERED` when a provider response is non-retryable or retry attempts
  are exhausted.

Admin operations can inspect sanitized delivery records through
`GET /admin/channels/deliveries` and audit evidence through
`GET /admin/channels/audit`. These views expose recipient and message
references, not raw recipient values or message bodies.

## Retry And Dead-Letter Handling

Failed channel deliveries are retryable only when the provider response is
recoverable:

- no provider status was returned
- HTTP `429`
- HTTP `5xx`

Retry attempts are capped at three total send attempts. Each retry writes a
`RETRY_QUEUED` audit event and reuses the original private payload without
exposing message text through admin operations. Non-retryable provider responses
such as HTTP `4xx`, and retryable responses that exhaust the max attempts, move
to `DEAD_LETTERED`.

Admins can retry a recoverable failed delivery through
`POST /admin/channels/deliveries/{delivery_id}/retry` after the provider issue
has been corrected.

## Consumer And Distributor Preferences

Consumer and distributor sessions can manage channel preferences through:

- `GET /channels/preferences/{audience}/{subject_id}?tenant_code=...`
- `PUT /channels/preferences/{audience}/{subject_id}`

Preferences include preferred channels, consented channels, and opted-out
channels. Recommendation logic applies preferred channels as a positive signal
and excludes opted-out channels from recommended live contact.

## Consent And Opt-Out Controls

WhatsApp and SMS dispatches require explicit consent evidence in the request
context before send. Supported consent keys are:

- `consent_verified`
- `channel_consent`
- `recipient_consent`

Dispatch is blocked when opt-out evidence is present. Supported opt-out keys
are:

- `opt_out`
- `opted_out`
- `recipient_opted_out`
- `channel_opt_out`

## Implemented Adapters

| Channel | Adapter | Payload Shape | Signature |
| --- | --- | --- | --- |
| WhatsApp | `WHATSAPP_PROVIDER` | `{ to, type: "text", text: { body }, metadata }` | `X-Amplifi-Signature` HMAC-SHA256 over compact JSON body |
| SMS | `SMS_PROVIDER` | `{ to, body, metadata }` | `X-Amplifi-Signature` HMAC-SHA256 over compact JSON body |
| USSD | `USSD_PROVIDER` | `{ session_id, msisdn, text, metadata }` | `X-Amplifi-Signature` HMAC-SHA256 over compact JSON body |

Both adapters add:

- `X-Amplifi-Channel`
- `X-Amplifi-Adapter`
- `X-Amplifi-Signature`
- `Content-Type: application/json`

## Guardrails

- Provider secrets never appear in response bodies or metric labels.
- Dispatch metrics exclude recipient and message text.
- Provider responses are truncated before being returned to operators.
- Delivery and audit views use hashed recipient and message references.
- Retry attempts are capped and audited; dead-lettered sends require operational
  review before further customer contact.
- Messaging dispatch requires consent evidence and blocks opted-out recipients.
- Consumer and distributor preference writes are scoped by session identity.
- Provider URLs and secrets must be configured before live dispatch.
- Inbound callbacks require signature verification through
  `/channels/webhooks/{channel_code}` before delivery status is captured.

## Verification

Adapter behavior is covered by `test/test_channel_readiness_service.py`.
The tests prove WhatsApp, SMS, and USSD payload shape, signing headers, consent
and opt-out enforcement, preference scoping, queued/sent/delivered/dead-lettered
status capture, bounded retry handling, dispatch metrics, sanitized delivery
operations, audit records, and inbound signature validation.
