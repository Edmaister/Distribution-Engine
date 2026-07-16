-- Referral SaaS account foundation primitives only.
-- This migration is additive and does not enable account creation routes,
-- invitations, membership commands, credential lifecycle, campaign activation,
-- go-live actions, webhook delivery, repair/replay/retry, or money movement.

CREATE TABLE IF NOT EXISTS platform_accounts (
    account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_code TEXT NOT NULL,
    account_name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING_ONBOARDING',
    onboarding_status TEXT NOT NULL DEFAULT 'NOT_STARTED',
    primary_external_tenant_ref TEXT,
    safe_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by_ref TEXT,
    updated_by_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ,
    CONSTRAINT platform_accounts_account_code_key UNIQUE (account_code),
    CONSTRAINT platform_accounts_type_chk CHECK (
        account_type IN (
            'ORGANISATION',
            'PRODUCER',
            'PARTNER',
            'DISTRIBUTOR',
            'SPONSOR',
            'OPERATOR',
            'MIXED'
        )
    ),
    CONSTRAINT platform_accounts_status_chk CHECK (
        status IN (
            'PENDING_ONBOARDING',
            'ACTIVE',
            'SUSPENDED',
            'DISABLED',
            'ARCHIVED'
        )
    ),
    CONSTRAINT platform_accounts_onboarding_status_chk CHECK (
        onboarding_status IN (
            'NOT_STARTED',
            'IN_PROGRESS',
            'READY_FOR_REVIEW',
            'APPROVED',
            'BLOCKED',
            'DISCARDED'
        )
    )
);

CREATE TABLE IF NOT EXISTS platform_organisations (
    organisation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    organisation_ref TEXT NOT NULL,
    organisation_name TEXT NOT NULL,
    organisation_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    safe_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ,
    CONSTRAINT platform_organisations_type_chk CHECK (
        organisation_type IN (
            'PRODUCER',
            'PARTNER',
            'DISTRIBUTOR',
            'SPONSOR',
            'CUSTOMER_ORGANISATION',
            'PLATFORM_OPERATOR',
            'MIXED'
        )
    ),
    CONSTRAINT platform_organisations_status_chk CHECK (
        status IN ('ACTIVE', 'SUSPENDED', 'DISABLED', 'ARCHIVED')
    )
);

CREATE TABLE IF NOT EXISTS platform_account_tenants (
    account_tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    tenant_code TEXT NOT NULL REFERENCES tenants(tenant_code),
    relationship_type TEXT NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT NOT NULL DEFAULT 'PENDING_SETUP',
    safe_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ,
    CONSTRAINT platform_account_tenants_relationship_chk CHECK (
        relationship_type IN (
            'OWNER',
            'OPERATOR',
            'RESELLER',
            'SPONSOR',
            'INTEGRATION',
            'SUPPORT'
        )
    ),
    CONSTRAINT platform_account_tenants_status_chk CHECK (
        status IN (
            'PENDING_SETUP',
            'ACTIVE',
            'SUSPENDED',
            'DISABLED',
            'ARCHIVED'
        )
    )
);

CREATE TABLE IF NOT EXISTS platform_external_tenant_refs (
    external_ref_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    account_tenant_id UUID REFERENCES platform_account_tenants(account_tenant_id),
    tenant_code TEXT NOT NULL REFERENCES tenants(tenant_code),
    ref_type TEXT NOT NULL,
    external_ref TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    source_system TEXT,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until TIMESTAMPTZ,
    safe_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    rotated_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ,
    CONSTRAINT platform_external_tenant_refs_type_chk CHECK (
        ref_type IN (
            'external_tenant_ref',
            'organisation_ref',
            'producer_ref',
            'partner_ref',
            'distributor_ref',
            'sponsor_ref'
        )
    ),
    CONSTRAINT platform_external_tenant_refs_status_chk CHECK (
        status IN (
            'PENDING',
            'ACTIVE',
            'SUSPENDED',
            'DISABLED',
            'ROTATED',
            'ARCHIVED'
        )
    ),
    CONSTRAINT platform_external_tenant_refs_window_chk CHECK (
        valid_until IS NULL OR valid_until > valid_from
    )
);

CREATE TABLE IF NOT EXISTS platform_users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject TEXT NOT NULL,
    email_hash TEXT,
    display_name TEXT,
    status TEXT NOT NULL DEFAULT 'INVITED',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ,
    CONSTRAINT platform_users_subject_key UNIQUE (subject),
    CONSTRAINT platform_users_status_chk CHECK (
        status IN (
            'INVITED',
            'ACTIVE',
            'SUSPENDED',
            'DISABLED',
            'ARCHIVED'
        )
    )
);

CREATE TABLE IF NOT EXISTS platform_seats (
    seat_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    seat_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'AVAILABLE',
    assigned_membership_id UUID,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ,
    CONSTRAINT platform_seats_type_chk CHECK (
        seat_type IN (
            'ADMIN',
            'OPERATOR',
            'PARTNER',
            'PRODUCER',
            'DISTRIBUTOR',
            'CONSUMER',
            'SUPPORT'
        )
    ),
    CONSTRAINT platform_seats_status_chk CHECK (
        status IN (
            'AVAILABLE',
            'ASSIGNED',
            'SUSPENDED',
            'DISABLED',
            'ARCHIVED'
        )
    )
);

CREATE TABLE IF NOT EXISTS platform_memberships (
    membership_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES platform_accounts(account_id),
    tenant_code TEXT REFERENCES tenants(tenant_code),
    user_id UUID REFERENCES platform_users(user_id),
    client_id TEXT REFERENCES partner_clients(client_id),
    role_family TEXT NOT NULL,
    permission_set TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'INVITED',
    seat_id UUID REFERENCES platform_seats(seat_id),
    invited_by_ref TEXT,
    accepted_by_ref TEXT,
    disabled_by_ref TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    invited_at TIMESTAMPTZ,
    accepted_at TIMESTAMPTZ,
    disabled_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ,
    CONSTRAINT platform_memberships_actor_chk CHECK (
        user_id IS NOT NULL OR client_id IS NOT NULL
    ),
    CONSTRAINT platform_memberships_role_family_chk CHECK (
        role_family IN (
            'PLATFORM_ADMIN',
            'SYSTEM_ADMIN',
            'FINANCE_ADMIN',
            'DISTRIBUTION_ADMIN',
            'PARTNER',
            'PRODUCER',
            'DISTRIBUTOR',
            'CONSUMER',
            'SUPPORT'
        )
    ),
    CONSTRAINT platform_memberships_status_chk CHECK (
        status IN (
            'INVITED',
            'ACTIVE',
            'SUSPENDED',
            'DISABLED',
            'ARCHIVED'
        )
    )
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'platform_seats_assigned_membership_fk'
    ) THEN
        ALTER TABLE platform_seats
        ADD CONSTRAINT platform_seats_assigned_membership_fk
        FOREIGN KEY (assigned_membership_id)
        REFERENCES platform_memberships(membership_id);
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS platform_account_audit_events (
    account_audit_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES platform_accounts(account_id),
    account_tenant_id UUID REFERENCES platform_account_tenants(account_tenant_id),
    external_ref_id UUID REFERENCES platform_external_tenant_refs(external_ref_id),
    membership_id UUID REFERENCES platform_memberships(membership_id),
    tenant_code TEXT REFERENCES tenants(tenant_code),
    event_type TEXT NOT NULL,
    event_status TEXT NOT NULL,
    actor_ref TEXT NOT NULL,
    actor_role TEXT,
    previous_status TEXT,
    next_status TEXT,
    reason_code TEXT,
    correlation_id TEXT,
    idempotency_key_hash TEXT,
    evidence_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    redactions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT platform_account_audit_events_status_chk CHECK (
        event_status IN (
            'RECORDED',
            'DUPLICATE',
            'DENIED',
            'FAILED',
            'BLOCKED'
        )
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_account_tenants_unique_active_link
    ON platform_account_tenants (account_id, tenant_code, relationship_type)
    WHERE status IN ('PENDING_SETUP', 'ACTIVE', 'SUSPENDED');

CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_account_tenants_primary_owner
    ON platform_account_tenants (tenant_code)
    WHERE relationship_type = 'OWNER'
      AND status IN ('PENDING_SETUP', 'ACTIVE', 'SUSPENDED');

CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_account_tenants_primary_per_account
    ON platform_account_tenants (account_id)
    WHERE is_primary = TRUE
      AND status IN ('PENDING_SETUP', 'ACTIVE', 'SUSPENDED');

CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_external_tenant_refs_active_ref
    ON platform_external_tenant_refs (ref_type, external_ref)
    WHERE status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS idx_platform_external_tenant_refs_scope
    ON platform_external_tenant_refs (account_id, tenant_code, ref_type);

CREATE INDEX IF NOT EXISTS idx_platform_external_tenant_refs_status
    ON platform_external_tenant_refs (status);

CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_organisations_active_ref
    ON platform_organisations (organisation_ref)
    WHERE status IN ('ACTIVE', 'SUSPENDED');

CREATE INDEX IF NOT EXISTS idx_platform_organisations_account
    ON platform_organisations (account_id);

CREATE INDEX IF NOT EXISTS idx_platform_accounts_status
    ON platform_accounts (status);

CREATE INDEX IF NOT EXISTS idx_platform_accounts_primary_external_ref
    ON platform_accounts (primary_external_tenant_ref);

CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_memberships_active_user_role
    ON platform_memberships (
        account_id,
        COALESCE(tenant_code, ''),
        user_id,
        role_family
    )
    WHERE user_id IS NOT NULL
      AND status IN ('INVITED', 'ACTIVE', 'SUSPENDED');

CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_memberships_active_client_role
    ON platform_memberships (
        account_id,
        COALESCE(tenant_code, ''),
        client_id,
        role_family
    )
    WHERE client_id IS NOT NULL
      AND status IN ('INVITED', 'ACTIVE', 'SUSPENDED');

CREATE INDEX IF NOT EXISTS idx_platform_memberships_account_status
    ON platform_memberships (account_id, status);

CREATE INDEX IF NOT EXISTS idx_platform_memberships_tenant_status
    ON platform_memberships (tenant_code, status);

CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_seats_assigned_membership
    ON platform_seats (assigned_membership_id)
    WHERE assigned_membership_id IS NOT NULL
      AND status = 'ASSIGNED';

CREATE INDEX IF NOT EXISTS idx_platform_seats_account_status
    ON platform_seats (account_id, status);

CREATE INDEX IF NOT EXISTS idx_platform_account_audit_events_account
    ON platform_account_audit_events (account_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_platform_account_audit_events_tenant
    ON platform_account_audit_events (tenant_code, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_platform_account_audit_events_external_ref
    ON platform_account_audit_events (external_ref_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_platform_account_audit_events_membership
    ON platform_account_audit_events (membership_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_platform_account_audit_events_correlation
    ON platform_account_audit_events (correlation_id);
