-- TASK-379: Referral SaaS report export deletion proof.
-- Adds explicit deleted storage/download states for prepared exports. The
-- command keeps the export request row and audit evidence, but removes stored
-- content and signed-download metadata from the safe runtime payload.

ALTER TABLE referral_saas_report_export_requests
    DROP CONSTRAINT IF EXISTS referral_saas_report_export_requests_storage_chk,
    ADD CONSTRAINT referral_saas_report_export_requests_storage_chk CHECK (
        storage_status IN ('NOT_STORED', 'PENDING', 'STORED', 'FAILED', 'EXPIRED', 'DELETED')
    );

ALTER TABLE referral_saas_report_export_requests
    DROP CONSTRAINT IF EXISTS referral_saas_report_export_requests_download_chk,
    ADD CONSTRAINT referral_saas_report_export_requests_download_chk CHECK (
        download_status IN ('NOT_AVAILABLE', 'PENDING', 'AVAILABLE', 'EXPIRED', 'DELETED')
    );
