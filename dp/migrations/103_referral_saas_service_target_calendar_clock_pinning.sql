-- TASK-441: Pin one approved business-calendar version to each eligible clock.
-- Existing elapsed-time clocks remain valid with all calendar fields NULL.

ALTER TABLE referral_saas_operational_service_target_clocks
    ADD COLUMN IF NOT EXISTS service_target_calendar_version_id UUID
        REFERENCES referral_saas_service_target_calendar_versions(
            service_target_calendar_version_id
        ),
    ADD COLUMN IF NOT EXISTS calendar_code TEXT,
    ADD COLUMN IF NOT EXISTS calendar_version_number INTEGER,
    ADD COLUMN IF NOT EXISTS calendar_timezone TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'referral_saas_service_target_clock_calendar_pin_ck'
    ) THEN
        ALTER TABLE referral_saas_operational_service_target_clocks
            ADD CONSTRAINT referral_saas_service_target_clock_calendar_pin_ck CHECK (
                (
                    service_target_calendar_version_id IS NULL
                    AND calendar_code IS NULL
                    AND calendar_version_number IS NULL
                    AND calendar_timezone IS NULL
                ) OR (
                    service_target_calendar_version_id IS NOT NULL
                    AND calendar_code IS NOT NULL
                    AND calendar_version_number > 0
                    AND calendar_timezone IS NOT NULL
                )
            );
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_referral_saas_service_target_clock_calendar_version
    ON referral_saas_operational_service_target_clocks (
        service_target_calendar_version_id,
        clock_status
    )
    WHERE service_target_calendar_version_id IS NOT NULL;
