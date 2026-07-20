-- TASK-239: Add Referral SaaS campaign manager as a durable membership role family.
--
-- This is intentionally narrow: it updates the account membership role-family
-- constraint only. It does not activate memberships, assign seats, deliver
-- invitations, change auth claims, or move money.

ALTER TABLE platform_memberships
    DROP CONSTRAINT IF EXISTS platform_memberships_role_family_chk;

ALTER TABLE platform_memberships
    ADD CONSTRAINT platform_memberships_role_family_chk CHECK (
        role_family IN (
            'PLATFORM_ADMIN',
            'SYSTEM_ADMIN',
            'FINANCE_ADMIN',
            'DISTRIBUTION_ADMIN',
            'CAMPAIGN_MANAGER',
            'PARTNER',
            'PRODUCER',
            'DISTRIBUTOR',
            'CONSUMER',
            'SUPPORT'
        )
    );
