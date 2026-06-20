# Monitoring (Prometheus & Grafana)

## Prometheus Metrics

The API exposes `/metrics` in Prometheus format, with:

- `http_requests_total{method,path,status}`
- `http_request_duration_seconds{method,path}`
- `db_ready`
- `sqs_ready`
- `kafka_ready`
- `rewards_applied_total{tenant,sticker,campaign_code,reward_type,product}`
- `enterprise_events_ingested_total{source_system,event_type,processing_status}`
- `enterprise_event_replays_total{event_type,status}`
- `enterprise_event_inbox_current{processing_status}`
- `admin_audit_writes_total{action_domain,action_type,action_status,result}`
- `partner_webhook_delivery_attempts_total{tenant,client_id,event_type,delivery_status,http_status}`
- `partner_webhook_delivery_latency_seconds{tenant,client_id,event_type,delivery_status}`
- `channel_dispatch_attempts_total{tenant,channel,adapter,delivery_status,provider_status}`
- `channel_dispatch_latency_seconds{tenant,channel,adapter,delivery_status}`

## Enterprise Event Metrics

`enterprise_events_ingested_total` is incremented by the IDS/Hogan consumer
when an event is:

- `QUEUED`
- `IGNORED`
- `DUPLICATE`
- `FAILED`

`enterprise_event_replays_total` is incremented by admin inbox replay when a
replay is:

- `replayable`
- `replay_queued`
- `skipped`
- `not_found`

`enterprise_event_inbox_current` is set by
`GET /admin/enterprise-events/summary` using the current inbox counts grouped by
processing status.

## Admin Audit Metrics

`admin_audit_writes_total` is incremented whenever an admin audit write is
attempted through the admin audit service.

Use `result="success"` to confirm the audit row was written, and
`result="failure"` to detect cases where the application continued but audit
logging could not persist the record.

## Partner Webhook SLA Metrics

`partner_webhook_delivery_attempts_total` is incremented for every outbound
partner webhook attempt, including successful sends, retryable failures, and
terminal failures.

`partner_webhook_delivery_latency_seconds` records delivery attempt latency by
tenant, partner client, event type, and final delivery status for that attempt.

Operations should alert on:

- rising `delivery_status="FAILED"` or repeated `http_status="429"` responses
- sustained high latency by `client_id` or `event_type`
- repeated `delivery_status="PENDING"` attempts for the same tenant/client

## Channel Dispatch Metrics

`channel_dispatch_attempts_total` is incremented for every outbound channel
provider call. Labels intentionally exclude recipient, message text, and
provider secrets.

`channel_dispatch_latency_seconds` records provider-call latency by tenant,
channel, adapter, and delivery status.

Operations should alert on:

- sustained `delivery_status="FAILED"` for any launch channel
- provider status spikes by channel or adapter
- high p95 dispatch latency for WhatsApp, SMS, or USSD

## Kubernetes (Prometheus Operator)

Enable ServiceMonitor with the overlay values:

```bash
helm upgrade --install referrals ./helm/referrals -f helm/referrals/values-monitoring.yaml
```

`values-monitoring.yaml` enables scrape annotations and creates a
ServiceMonitor.

## Grafana

Import the provided operations dashboard:

- `monitoring/grafana/dashboards/referrals_overview.json`

The dashboard covers API, DB, queues, BFFs, admin audit, partner webhooks,
channels, enterprise events, and reward operations. It is arranged for operator
triage: readiness and risk stats first, then latency/error trends, then
journey-specific partner and channel signals.

Enterprise inbox panels should track:

- events ingested by source system and processing status
- duplicate and failed event trends
- replay requests by status
- current inbox counts by processing status

Admin audit panels should track:

- audit writes by action domain and result
- audit write failures over time
- top admin action types by volume

Partner webhook panels should track:

- delivery attempts by tenant, client, event type, delivery status, and HTTP status
- delivery latency p50/p95 by tenant and client
- retryable failures and terminal failures by partner client

## Notes

- For multi-process deployments, configure `prometheus_client` multiprocess
  mode; the current setup is single-process-friendly.
- Treat high `IGNORED`, `FAILED`, or `DUPLICATE` rates as operational signals,
  not necessarily application failures.
- Treat any sustained `admin_audit_writes_total{result="failure"}` increase as
  a security and compliance signal.
