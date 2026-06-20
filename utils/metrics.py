# utils/metrics.py
try:
    from prometheus_client import Counter, Gauge, Histogram

    rewards_applied_total = Counter(
        "rewards_applied_total",
        "Number of rewards successfully applied",
        ["tenant", "sticker", "campaign_code", "reward_type", "product"],
    )

    def rewards_applied_inc(
        tenant: str | None = None,
        sticker: str | None = None,
        campaign_code: str | None = None,
        reward_type: str | None = None,
        product: str | None = None,
    ):
        rewards_applied_total.labels(
            tenant or "unknown",
            sticker or "unknown",
            campaign_code or "none",
            reward_type or "unknown",
            product or "unknown",
        ).inc()

    enterprise_events_ingested_total = Counter(
        "enterprise_events_ingested_total",
        "Number of enterprise events ingested by source, event type, and status",
        ["source_system", "event_type", "processing_status"],
    )

    enterprise_event_replays_total = Counter(
        "enterprise_event_replays_total",
        "Number of enterprise inbox replay attempts by event type and status",
        ["event_type", "status"],
    )

    enterprise_event_inbox_current = Gauge(
        "enterprise_event_inbox_current",
        "Current enterprise inbox event count by processing status",
        ["processing_status"],
    )

    admin_audit_writes_total = Counter(
        "admin_audit_writes_total",
        "Number of admin audit write attempts by domain, action type, status, and result",
        ["action_domain", "action_type", "action_status", "result"],
    )

    bff_aggregate_requests_total = Counter(
        "bff_aggregate_requests_total",
        "Number of BFF aggregate responses by route, tenant, and status",
        ["route", "tenant", "status"],
    )

    bff_aggregate_sections_total = Counter(
        "bff_aggregate_sections_total",
        "Number of BFF aggregate section responses by route, tenant, section, and status",
        ["route", "tenant", "section", "status"],
    )

    bff_aggregate_section_latency_seconds = Histogram(
        "bff_aggregate_section_latency_seconds",
        "Latency of BFF aggregate section loaders by route, tenant, section, and status",
        ["route", "tenant", "section", "status"],
        buckets=(0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
    )

    partner_webhook_delivery_attempts_total = Counter(
        "partner_webhook_delivery_attempts_total",
        "Partner webhook delivery attempts by tenant, client, event type, status, and HTTP status",
        ["tenant", "client_id", "event_type", "delivery_status", "http_status"],
    )

    partner_webhook_delivery_latency_seconds = Histogram(
        "partner_webhook_delivery_latency_seconds",
        "Partner webhook delivery latency by tenant, client, event type, and status",
        ["tenant", "client_id", "event_type", "delivery_status"],
        buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30),
    )

    channel_dispatch_attempts_total = Counter(
        "channel_dispatch_attempts_total",
        "Outbound channel dispatch attempts by tenant, channel, adapter, status, and provider status",
        ["tenant", "channel", "adapter", "delivery_status", "provider_status"],
    )

    channel_dispatch_latency_seconds = Histogram(
        "channel_dispatch_latency_seconds",
        "Outbound channel dispatch latency by tenant, channel, adapter, and status",
        ["tenant", "channel", "adapter", "delivery_status"],
        buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30),
    )

    def enterprise_event_ingested_inc(
        *,
        source_system: str | None,
        event_type: str | None,
        processing_status: str | None,
    ):
        enterprise_events_ingested_total.labels(
            source_system or "unknown",
            event_type or "unknown",
            processing_status or "unknown",
        ).inc()

    def enterprise_event_replay_inc(
        *,
        event_type: str | None,
        status: str | None,
    ):
        enterprise_event_replays_total.labels(
            event_type or "unknown",
            status or "unknown",
        ).inc()

    def enterprise_event_inbox_current_set(
        *,
        processing_status: str | None,
        value: int,
    ):
        enterprise_event_inbox_current.labels(
            processing_status or "unknown",
        ).set(value)

    def admin_audit_write_inc(
        *,
        action_domain: str | None,
        action_type: str | None,
        action_status: str | None,
        result: str | None,
    ):
        admin_audit_writes_total.labels(
            action_domain or "unknown",
            action_type or "unknown",
            action_status or "unknown",
            result or "unknown",
        ).inc()

    def bff_aggregate_request_inc(
        *,
        route: str | None,
        tenant: str | None,
        status: str | None,
    ):
        bff_aggregate_requests_total.labels(
            route or "unknown",
            tenant or "unknown",
            status or "unknown",
        ).inc()

    def bff_aggregate_section_observe(
        *,
        route: str | None,
        tenant: str | None,
        section: str | None,
        status: str | None,
        latency_seconds: float,
    ):
        labels = (
            route or "unknown",
            tenant or "unknown",
            section or "unknown",
            status or "unknown",
        )
        bff_aggregate_sections_total.labels(*labels).inc()
        bff_aggregate_section_latency_seconds.labels(*labels).observe(latency_seconds)

    def partner_webhook_delivery_observe(
        *,
        tenant: str | None,
        client_id: str | None,
        event_type: str | None,
        delivery_status: str | None,
        http_status: int | str | None,
        latency_seconds: float,
    ):
        labels = (
            tenant or "unknown",
            client_id or "unknown",
            event_type or "unknown",
            delivery_status or "unknown",
        )
        partner_webhook_delivery_attempts_total.labels(
            *labels,
            str(http_status if http_status is not None else "unknown"),
        ).inc()
        partner_webhook_delivery_latency_seconds.labels(*labels).observe(
            latency_seconds
        )

    def channel_dispatch_observe(
        *,
        tenant: str | None,
        channel: str | None,
        adapter: str | None,
        delivery_status: str | None,
        provider_status: int | str | None,
        latency_seconds: float,
    ):
        labels = (
            tenant or "unknown",
            channel or "unknown",
            adapter or "unknown",
            delivery_status or "unknown",
        )
        channel_dispatch_attempts_total.labels(
            *labels,
            str(provider_status if provider_status is not None else "unknown"),
        ).inc()
        channel_dispatch_latency_seconds.labels(*labels).observe(latency_seconds)

except Exception:
    # Fallback if prometheus_client isn't installed
    def rewards_applied_inc(*args, **kwargs):
        return

    def enterprise_event_ingested_inc(*args, **kwargs):
        return

    def enterprise_event_replay_inc(*args, **kwargs):
        return

    def enterprise_event_inbox_current_set(*args, **kwargs):
        return

    def admin_audit_write_inc(*args, **kwargs):
        return

    def bff_aggregate_request_inc(*args, **kwargs):
        return

    def bff_aggregate_section_observe(*args, **kwargs):
        return

    def partner_webhook_delivery_observe(*args, **kwargs):
        return

    def channel_dispatch_observe(*args, **kwargs):
        return
