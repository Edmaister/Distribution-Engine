ALTER TABLE referral_progress_events
DROP CONSTRAINT IF EXISTS chk_rpe_event_type;

ALTER TABLE referral_progress_events
ADD CONSTRAINT chk_rpe_event_type
CHECK (
    event_type = ANY (ARRAY[
        'VALIDATED',
        'UCN_CAPTURED',
        'ACCOUNT_OPENED',
        'ACCOUNT_ACTIVATED',
        'FUNDED',
        'DEBIT_ORDER_SWITCHED',
        'SALARY_SWITCHED',
        'FIRST_TRANSACTION_COMPLETED'
    ])
);