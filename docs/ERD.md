# Entity-Relationship Diagram (Mermaid)

```mermaid
erDiagram
    referrals ||--o{ referral_rewards : "1:N"
    marketing_campaigns ||--o{ referrals : "1:N by campaign_code"
    marketing_campaigns ||--|| marketing_campaign_policies : "1:1 by campaign_code"
    missions ||--o{ user_mission_progress : "1:N"
    badges ||--o{ user_badges : "1:N"

    referrals {
      UUID referral_track_id PK
      TEXT referral_code UNIQUE
      TEXT referrer_ucn_encrypted
      TEXT referee_ucn_encrypted
      TEXT sticker
      TEXT tenant_code
      TEXT campaign_code
      TIMESTAMPTZ created_at
    }
    referral_rewards {
      UUID reward_id PK
      UUID referral_track_id FK
      TEXT reward_type
      TEXT product
      NUMERIC amount
      TEXT campaign_code
      TEXT tenant_code
      TIMESTAMPTZ created_at
      UNIQUE referral_track_id, reward_type
    }
    marketing_campaigns {
      TEXT campaign_code PK
      TEXT name
      TEXT sticker
      TEXT tenant_code
      BOOLEAN is_active
      TIMESTAMPTZ starts_at
      TIMESTAMPTZ ends_at
      JSONB attributes
      TIMESTAMPTZ created_at
    }
    marketing_campaign_policies {
      TEXT campaign_code PK, FK
      JSONB reward_amounts_json
      JSONB product_rules_json
      TIMESTAMPTZ updated_at
    }
    cooldown_policies {
      TEXT sticker PK
      TEXT tenant_code
      JSONB reward_amounts_json
      JSONB product_rules_json
      TIMESTAMPTZ updated_at
    }
    enterprise_events {
      UUID event_id PK
      UUID referral_track_id
      TEXT event_type
      TIMESTAMPTZ occurred_at
      JSONB attributes
      TIMESTAMPTZ created_at
    }
    missions {
      TEXT mission_code PK
      TEXT title
      INT goal
      INT reward_points
      TEXT description
    }
    user_mission_progress {
      TEXT referrer_hash PK
      TEXT mission_code PK, FK
      INT progress
      TEXT status
      TIMESTAMPTZ updated_at
    }
    badges {
      TEXT badge_code PK
      TEXT title
      TEXT description
      INT reward_points
    }
    user_badges {
      TEXT referrer_hash PK
      TEXT badge_code PK, FK
      TIMESTAMPTZ awarded_at
    }
    referral_qr_scans {
      UUID scan_id PK
      TEXT referral_code
      TEXT device_fingerprint
      TEXT ip_address
      TEXT status
      TIMESTAMPTZ created_at
    }
    recommendations_cache {
      TEXT referrer_hash PK
      JSONB items
      TIMESTAMPTZ generated_at
      INT ttl_seconds
    }
    campaign_insights_cache {
      TEXT campaign_code PK
      TEXT sticker
      TEXT tenant_code
      JSONB metrics
      TIMESTAMPTZ generated_at
      INT ttl_seconds
    }
```
