INSERT INTO progress_definitions (
    product,
    sub_product,
    completion_event,
    milestones_json,
    is_active
)
VALUES (
    'INSURANCE',
    'FUNERAL_PLAN',
    'FIRST_TRANSACTION_COMPLETED',
    '[
      {
        "event": "ACCOUNT_OPENED",
        "percent": 30,
        "progressBand": "STARTED",
        "displayStatus": "Referral received",
        "nextMilestone": "Progressing to the next milestone"
      },
      {
        "event": "ACCOUNT_ACTIVATED",
        "percent": 60,
        "progressBand": "IN_PROGRESS",
        "displayStatus": "Progressing",
        "nextMilestone": "Progressing to the next milestone"
      },
      {
        "event": "FIRST_TRANSACTION_COMPLETED",
        "percent": 100,
        "progressBand": "COMPLETE",
        "displayStatus": "Completed",
        "nextMilestone": "Reward achieved"
      }
    ]'::jsonb,
    TRUE
);