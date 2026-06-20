UPDATE mission_definitions
SET mission_description = 'A bonus reward may be applied when a qualifying debit order switch is completed.'
WHERE mission_code = 'FIRST_DEBIT_ORDER_SWITCH';

UPDATE mission_definitions
SET mission_description = 'A bonus reward may be applied when a qualifying salary switch is completed.'
WHERE mission_code = 'FIRST_SALARY_SWITCH';