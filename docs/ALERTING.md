# Alerting (Prometheus & Grafana)

## Alerts included
- **HighErrorRate (critical)** — 5xx > 5% for 10m
- **ApiDown (critical)** — `/metrics` target down for 2m
- **DatabaseDown (critical)** — `db_ready` near 0 for 5m
- **KafkaDown (warning)** — `kafka_ready` near 0 for 5m
- **SlowRequestsP95 (warning)** — p95 latency > 1s for 10m

## Where
- Rules file: `monitoring/prometheus/alert_rules.yml`

## How to load
- **Prometheus Operator**: Create a `PrometheusRule` and copy the `groups:` section into `spec.groups`.
- **Vanilla Prometheus**: Mount the file and reference it in `rule_files:` in `prometheus.yml`.

## Grafana-based Alerts
- Import `monitoring/grafana/dashboards/referrals_overview.json` and add panel alerts for 5xx or latency thresholds.

## Notes
- Tune thresholds for staging/prod separately.
- Ensure the Service scrape job label in Prometheus matches `job="referrals"` or update the `ApiDown` rule.
