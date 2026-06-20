ALTER TABLE referral_instances
DROP CONSTRAINT IF EXISTS referral_instances_status_chk;

ALTER TABLE referral_instances
ADD CONSTRAINT referral_instances_status_chk
CHECK (
    status IN (
        'VALIDATED',
        'UCN_CAPTURED',
        'ACCOUNT_OPENED',
        'ACCOUNT_ACTIVATED',
        'FUNDED',
        'COMPLETED',
        'CANCELLED'
    )
);