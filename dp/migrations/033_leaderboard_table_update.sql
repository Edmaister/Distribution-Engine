UPDATE leaderboard_definitions
SET tenant_code = 'FNB'
WHERE tenant_code IS NULL;

UPDATE leaderboard_entries
SET tenant_code = 'FNB'
WHERE tenant_code IS NULL;