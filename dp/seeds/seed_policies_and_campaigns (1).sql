-- Default sticker-level reward amounts
INSERT INTO cooldown_policies (sticker, tenant_code, reward_amounts_json, product_rules_json)
VALUES ('EASY','FNB','{"BANKING":{"ACTIVATION":18,"DEBIT_ORDER":18,"SALARY":18}}','{}')
ON CONFLICT DO NOTHING;

-- Sample campaign
INSERT INTO marketing_campaigns (campaign_code, name, segment, tenant_code, is_active)
VALUES ('CAMPUS-SEP-2025','Campus Activation Sept 2025','PREMIER','FNB',TRUE)
ON CONFLICT DO NOTHING;
