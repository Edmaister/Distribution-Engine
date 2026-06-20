CREATE TABLE IF NOT EXISTS provider_sla_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    provider_key TEXT NOT NULL,

    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    retry_count INTEGER NOT NULL DEFAULT 0,

    total_latency_ms BIGINT NOT NULL DEFAULT 0,
    total_settlement_time_seconds BIGINT NOT NULL DEFAULT 0,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_provider_sla_metrics_provider_key
ON provider_sla_metrics (provider_key);
