from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_grafana_overview_dashboard_covers_operating_domains():
    dashboard = json.loads(
        (ROOT / "monitoring/grafana/dashboards/referrals_overview.json").read_text(
            encoding="utf-8"
        )
    )

    expressions = "\n".join(
        target.get("expr", "")
        for panel in dashboard["panels"]
        for target in panel.get("targets", [])
    )

    for metric in (
        "http_requests_total",
        "http_request_duration_seconds",
        "db_ready",
        "sqs_ready",
        "kafka_ready",
        "bff_aggregate_requests_total",
        "bff_aggregate_section_latency_seconds",
        "admin_audit_writes_total",
        "partner_webhook_delivery_attempts_total",
        "partner_webhook_delivery_latency_seconds",
        "channel_dispatch_attempts_total",
        "channel_dispatch_latency_seconds",
        "enterprise_event_inbox_current",
        "enterprise_events_ingested_total",
        "rewards_applied_total",
    ):
        assert metric in expressions

    assert len(dashboard["panels"]) >= 16
    assert dashboard["title"] == "Referral Engine Operations Overview"
