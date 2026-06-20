ALTER TABLE referrer_codes
ADD COLUMN IF NOT EXISTS accepted_terms boolean NOT NULL DEFAULT false,
ADD COLUMN IF NOT EXISTS accepted_terms_at timestamp with time zone NULL;
