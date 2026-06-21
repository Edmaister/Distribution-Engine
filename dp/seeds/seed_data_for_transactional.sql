DO $$
BEGIN
    IF to_regclass('progress_definitions') IS NOT NULL THEN
        INSERT INTO progress_definitions (
            product,
            sub_product,
            completion_event,
            milestones_json,
            is_active
        )
        SELECT
            'TRANSACTIONAL',
            'EASY_ACCOUNT',
            'DEBIT_ORDER_SWITCHED',
            '[
              {
                "event": "ACCOUNT_OPENED",
                "percent": 25,
                "progressBand": "STARTED",
                "displayStatus": "Referral received",
                "nextMilestone": "Progressing to the next milestone"
              },
              {
                "event": "ACCOUNT_ACTIVATED",
                "percent": 50,
                "progressBand": "IN_PROGRESS",
                "displayStatus": "Progressing",
                "nextMilestone": "Progressing to the next milestone"
              },
              {
                "event": "FUNDED",
                "percent": 80,
                "progressBand": "NEAR_COMPLETE",
                "displayStatus": "Near completion",
                "nextMilestone": "Final milestone remaining"
              },
              {
                "event": "DEBIT_ORDER_SWITCHED",
                "percent": 100,
                "progressBand": "COMPLETE",
                "displayStatus": "Completed",
                "nextMilestone": "Reward achieved"
              }
            ]'::jsonb,
            TRUE
        WHERE NOT EXISTS (
            SELECT 1
            FROM progress_definitions
            WHERE product = 'TRANSACTIONAL'
              AND sub_product = 'EASY_ACCOUNT'
              AND completion_event = 'DEBIT_ORDER_SWITCHED'
        );
    END IF;
END $$;
