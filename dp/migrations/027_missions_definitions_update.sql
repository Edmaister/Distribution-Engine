BEGIN;

-- 1) mission_definitions: add mission_category for UX grouping / product semantics
ALTER TABLE mission_definitions
ADD COLUMN IF NOT EXISTS mission_category TEXT NOT NULL DEFAULT 'CORE';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_mission_definitions_mission_category'
    ) THEN
        ALTER TABLE mission_definitions
        ADD CONSTRAINT chk_mission_definitions_mission_category
        CHECK (mission_category IN ('CORE', 'BOOST', 'MILESTONE'));
    END IF;
END $$;

-- Backfill common existing mission categories
UPDATE mission_definitions
SET mission_category = 'CORE'
WHERE event_type IN (
    'ACCOUNT_OPENED',
    'ACCOUNT_ACTIVATED',
    'FUNDED'
);

UPDATE mission_definitions
SET mission_category = 'BOOST'
WHERE event_type IN (
    'FIRST_TRANSACTION_COMPLETED',
    'DEBIT_ORDER_SWITCHED',
    'SALARY_SWITCHED'
);

-- 2) referral_instances: support fast holistic mission lookup by referrer UCN
CREATE INDEX IF NOT EXISTS idx_referral_instances_referrer_ucn
ON referral_instances (referrer_ucn);

-- Optional but recommended if created_at exists on referral_instances.
-- Uncomment only if the column exists and you want the compound index.
-- CREATE INDEX IF NOT EXISTS idx_referral_instances_referrer_ucn_created_at
-- ON referral_instances (referrer_ucn, created_at);

-- 3) mission_display_audit: extend auditability for referrer-level / portfolio mission views
ALTER TABLE mission_display_audit
ADD COLUMN IF NOT EXISTS referrer_ucn TEXT;

ALTER TABLE mission_display_audit
ADD COLUMN IF NOT EXISTS mission_category TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_mission_display_audit_mission_category'
    ) THEN
        ALTER TABLE mission_display_audit
        ADD CONSTRAINT chk_mission_display_audit_mission_category
        CHECK (
            mission_category IS NULL
            OR mission_category IN ('CORE', 'BOOST', 'MILESTONE')
        );
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_mission_display_audit_referrer_ucn_shown_at
ON mission_display_audit (referrer_ucn, shown_at DESC);

COMMIT;
