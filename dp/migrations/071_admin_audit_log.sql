CREATE TABLE IF NOT EXISTS admin_audit_log (
    admin_audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_type TEXT NOT NULL,
    action_domain TEXT NOT NULL,
    action_status TEXT NOT NULL DEFAULT 'SUCCESS',
    actor_role TEXT,
    actor_tenant_code TEXT,
    actor_subject TEXT,
    tenant_code TEXT,
    target_type TEXT,
    target_id TEXT,
    correlation_id TEXT,
    reason TEXT,
    request_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_admin_audit_log_created
ON admin_audit_log(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_admin_audit_log_domain_action
ON admin_audit_log(action_domain, action_type);

CREATE INDEX IF NOT EXISTS idx_admin_audit_log_tenant
ON admin_audit_log(tenant_code);

CREATE INDEX IF NOT EXISTS idx_admin_audit_log_target
ON admin_audit_log(target_type, target_id);

CREATE INDEX IF NOT EXISTS idx_admin_audit_log_actor
ON admin_audit_log(actor_role, actor_tenant_code);
