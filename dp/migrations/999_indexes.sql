-- Useful indexes
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'referrals'
          AND column_name = 'referrer_ucn_encrypted'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_referrals_referrer
        ON referrals(referrer_ucn_encrypted);
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'referrals'
          AND column_name = 'campaign_code'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_referrals_campaign
        ON referrals(campaign_code);
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'referral_rewards'
          AND column_name = 'campaign_code'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_rewards_campaign
        ON referral_rewards(campaign_code);
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'enterprise_event_inbox'
          AND column_name = 'referral_track_id'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_events_referral
        ON enterprise_event_inbox(referral_track_id);
    END IF;
END $$;
