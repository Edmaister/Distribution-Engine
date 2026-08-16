-- TASK-409: Bind Referral SaaS programmes to customer product/offering taxonomy.
-- The existing product_code/sub_product_code columns remain Amplifi service packaging.
-- These references identify the customer's real-world product line and offering.

ALTER TABLE referral_saas_programme_drafts
    ADD COLUMN IF NOT EXISTS customer_product_line_id UUID,
    ADD COLUMN IF NOT EXISTS customer_product_offering_id UUID;

ALTER TABLE referral_saas_programme_versions
    ADD COLUMN IF NOT EXISTS customer_product_line_id UUID,
    ADD COLUMN IF NOT EXISTS customer_product_offering_id UUID;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'referral_saas_programme_drafts_product_line_fk'
    ) THEN
        ALTER TABLE referral_saas_programme_drafts
            ADD CONSTRAINT referral_saas_programme_drafts_product_line_fk
            FOREIGN KEY (customer_product_line_id)
            REFERENCES referral_saas_customer_product_lines(customer_product_line_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'referral_saas_programme_drafts_product_offering_fk'
    ) THEN
        ALTER TABLE referral_saas_programme_drafts
            ADD CONSTRAINT referral_saas_programme_drafts_product_offering_fk
            FOREIGN KEY (customer_product_offering_id)
            REFERENCES referral_saas_customer_product_offerings(customer_product_offering_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'referral_saas_programme_versions_product_line_fk'
    ) THEN
        ALTER TABLE referral_saas_programme_versions
            ADD CONSTRAINT referral_saas_programme_versions_product_line_fk
            FOREIGN KEY (customer_product_line_id)
            REFERENCES referral_saas_customer_product_lines(customer_product_line_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'referral_saas_programme_versions_product_offering_fk'
    ) THEN
        ALTER TABLE referral_saas_programme_versions
            ADD CONSTRAINT referral_saas_programme_versions_product_offering_fk
            FOREIGN KEY (customer_product_offering_id)
            REFERENCES referral_saas_customer_product_offerings(customer_product_offering_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'referral_saas_programme_drafts_product_binding_pair_ck'
    ) THEN
        ALTER TABLE referral_saas_programme_drafts
            ADD CONSTRAINT referral_saas_programme_drafts_product_binding_pair_ck
            CHECK (
                (customer_product_line_id IS NULL AND customer_product_offering_id IS NULL)
                OR
                (customer_product_line_id IS NOT NULL AND customer_product_offering_id IS NOT NULL)
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'referral_saas_programme_versions_product_binding_pair_ck'
    ) THEN
        ALTER TABLE referral_saas_programme_versions
            ADD CONSTRAINT referral_saas_programme_versions_product_binding_pair_ck
            CHECK (
                (customer_product_line_id IS NULL AND customer_product_offering_id IS NULL)
                OR
                (customer_product_line_id IS NOT NULL AND customer_product_offering_id IS NOT NULL)
            );
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_referral_saas_programme_drafts_product_offering
    ON referral_saas_programme_drafts (
        account_id,
        customer_product_line_id,
        customer_product_offering_id
    )
    WHERE archived_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_referral_saas_programme_versions_product_offering
    ON referral_saas_programme_versions (
        account_id,
        customer_product_line_id,
        customer_product_offering_id
    )
    WHERE version_status <> 'RETIRED';
