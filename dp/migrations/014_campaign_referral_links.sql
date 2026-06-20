-- 003_campaign_referral_link.sql
-- Bridge between campaign and referral domains (strict separation preserved)

CREATE TABLE IF NOT EXISTS campaign_referral_links (
    campaign_track_id UUID NOT NULL
        REFERENCES campaign_attributions(campaign_track_id) ON DELETE RESTRICT,

    referral_track_id UUID NOT NULL
        REFERENCES referral_instances(referral_track_id) ON DELETE RESTRICT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- One referral journey maps to ONE campaign journey
    CONSTRAINT uq_campaign_referral_links_referral UNIQUE (referral_track_id),

    -- Composite PK allows 1 campaign → many referrals (if ever needed)
    PRIMARY KEY (campaign_track_id, referral_track_id)
);

-- Lookup indexes
CREATE INDEX IF NOT EXISTS idx_campaign_referral_links_campaign_track
    ON campaign_referral_links (campaign_track_id);

CREATE INDEX IF NOT EXISTS idx_campaign_referral_links_referral_track
    ON campaign_referral_links (referral_track_id);