-- 001_init.sql — Referral Domain Core (STRICT SEPARATION)
-- Model:
-- 1) referrer_codes: referrer registry (created when referrer joins programme / requests code)
--    - stores raw UCN (allowed per your design)
--    - stores referral_code (hashed/encrypted share token derived from UCN)
--    - stores gaming_handle (only public identity for leaderboards)
-- 2) referral_instances: created each time a referee validates/uses referral_code
--    - referral_track_id is the golden thread for lineage, rewards, progress
-- 3) referral_rewards: referral domain only; linked to referral_track_id
--
-- NO campaign tables/fields included here.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ----------------------------
-- 1) Referrer registry
-- ----------------------------
CREATE TABLE IF NOT EXISTS referrer_codes (
  referrer_code_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Allowed by your rule (do not surface via API/events)
  referrer_ucn           TEXT NOT NULL,

  -- Opaque identifiers
  referrer_ucn_hash      TEXT UNIQUE NOT NULL,   -- internal deterministic key (HMAC/hashed UCN)
  referral_code          TEXT UNIQUE NOT NULL,   -- share token (short code / QR payload)

  -- Public identity
  gaming_handle          TEXT UNIQUE NOT NULL,

  -- Referral-domain context
  sticker                TEXT NOT NULL,
  tenant_code            TEXT,
  segment                TEXT,

  created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_referrer_codes_referral_code
  ON referrer_codes (referral_code);

CREATE INDEX IF NOT EXISTS idx_referrer_codes_referrer_ucn_hash
  ON referrer_codes (referrer_ucn_hash);

-- ----------------------------
-- 2) Referral instances (golden thread starts at validation)
-- ----------------------------
CREATE TABLE IF NOT EXISTS referral_instances (
  referral_track_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  referrer_code_id       UUID NOT NULL REFERENCES referrer_codes(referrer_code_id),

  -- store the code used for audit/traceability
  referral_code          TEXT NOT NULL,

  -- allowed by your rule; do not surface via API/events
  referrer_ucn           TEXT NOT NULL,
  referee_ucn            TEXT,

  status                 TEXT NOT NULL DEFAULT 'VALIDATED',

  validated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT referral_instances_status_chk
    CHECK (status IN ('VALIDATED', 'UCN_CAPTURED', 'COMPLETED', 'CANCELLED'))
);

CREATE INDEX IF NOT EXISTS idx_referral_instances_referrer_code_id
  ON referral_instances (referrer_code_id);

CREATE INDEX IF NOT EXISTS idx_referral_instances_referrer_ucn
  ON referral_instances (referrer_ucn);

CREATE INDEX IF NOT EXISTS idx_referral_instances_referee_ucn
  ON referral_instances (referee_ucn);
  
ALTER TABLE referral_instances
ADD COLUMN IF NOT EXISTS salary_switched_at TIMESTAMPTZ NULL,
ADD COLUMN IF NOT EXISTS first_transaction_at TIMESTAMPTZ NULL;

-- ----------------------------
-- 3) Referral rewards (referral domain only)
-- ----------------------------
CREATE TABLE IF NOT EXISTS referral_rewards (
  reward_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  referral_track_id UUID NOT NULL REFERENCES referral_instances(referral_track_id),

  reward_type       TEXT NOT NULL,
  product           TEXT,
  amount            NUMERIC,
  tenant_code       TEXT,

  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  UNIQUE(referral_track_id, reward_type)
);

CREATE INDEX IF NOT EXISTS idx_referral_rewards_track_type
  ON referral_rewards (referral_track_id, reward_type);
  
 ALTER TABLE referral_instances
ADD COLUMN IF NOT EXISTS progress_percent INTEGER,
ADD COLUMN IF NOT EXISTS progress_band VARCHAR(50),
ADD COLUMN IF NOT EXISTS display_status VARCHAR(255),
ADD COLUMN IF NOT EXISTS next_milestone VARCHAR(255),
ADD COLUMN IF NOT EXISTS is_complete BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP;

ALTER TABLE referral_instances
ADD COLUMN IF NOT EXISTS product VARCHAR(100),
ADD COLUMN IF NOT EXISTS sub_product VARCHAR(100);

ALTER TABLE referral_instances
ADD COLUMN IF NOT EXISTS referee_alias VARCHAR(30) NULL,
ADD COLUMN IF NOT EXISTS referee_alias_normalized VARCHAR(30) NULL;

ALTER TABLE referral_instances
ADD COLUMN IF NOT EXISTS accepted_terms BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS accepted_terms_at TIMESTAMPTZ NULL;

ALTER TABLE referral_instances
ADD COLUMN IF NOT EXISTS journey_code VARCHAR(100),
ADD COLUMN IF NOT EXISTS journey_version VARCHAR(20);

UPDATE referral_instances
SET journey_code = COALESCE(journey_code, 'BANKING_TRANSACTIONAL'),
    journey_version = COALESCE(journey_version, 'v1');

ALTER TABLE referral_instances
ALTER COLUMN journey_code SET DEFAULT 'BANKING_TRANSACTIONAL',
ALTER COLUMN journey_version SET DEFAULT 'v1';

