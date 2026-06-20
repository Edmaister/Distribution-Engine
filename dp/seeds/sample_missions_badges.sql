-- Example missions
INSERT INTO missions (mission_code, title, goal, reward_points, description) VALUES
('INVITE_5','Invite 5 friends',5,25,'Get 25 points when you invite 5 friends'),
('EARN_3_REWARDS','Earn 3 rewards',3,30,'Collect 3 rewards to earn bonus points')
ON CONFLICT DO NOTHING;

-- Example badges
INSERT INTO badges (badge_code, title, description, reward_points) VALUES
('FIRST_REFERRAL','First Referral','Awarded when you make your first referral',10),
('LOYAL_REFERRER','Loyal Referrer','Awarded when you refer 20+ friends',50)
ON CONFLICT DO NOTHING;
