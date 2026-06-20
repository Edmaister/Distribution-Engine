	
INSERT INTO progress_definitions (
product,
sub_product,
completion_event,
milestones_json,
is_active
)
VALUES (
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
);