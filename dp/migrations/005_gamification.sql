-- Missions, badges, and user progress
CREATE TABLE IF NOT EXISTS missions (
  mission_code TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  goal INT NOT NULL,
  reward_points INT NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS user_mission_progress (
  referrer_hash TEXT NOT NULL,
  mission_code TEXT NOT NULL REFERENCES missions(mission_code),
  progress INT NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (referrer_hash, mission_code)
);

CREATE TABLE IF NOT EXISTS badges (
  badge_code TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  reward_points INT
);

CREATE TABLE IF NOT EXISTS user_badges (
  referrer_hash TEXT NOT NULL,
  badge_code TEXT NOT NULL REFERENCES badges(badge_code),
  awarded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (referrer_hash, badge_code)
);
