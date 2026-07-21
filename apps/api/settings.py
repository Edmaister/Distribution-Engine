# api/settings.py
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field("Referral Engine API", env="APP_NAME")
    app_env: str = Field("local", env="APP_ENV")

    tenant_default: str = Field("DEFAULT", env="APP_TENANT_DEFAULT")

    admin_api_key: str | None = Field(None, env="ADMIN_API_KEY")
    finance_admin_api_key: str | None = Field(None, env="FINANCE_ADMIN_API_KEY")
    distribution_admin_api_key: str | None = Field(
        None, env="DISTRIBUTION_ADMIN_API_KEY"
    )
    system_admin_api_key: str | None = Field(None, env="SYSTEM_ADMIN_API_KEY")

    # Legacy/shared partner key — keep temporarily for backward compatibility
    partner_api_key: str | None = Field(None, env="PARTNER_API_KEY")

    # Tenant-bound partner keys
    fnb_partner_api_key: str | None = Field(None, env="FNB_PARTNER_API_KEY")
    fnb_tenant_user_api_key: str | None = Field(None, env="FNB_TENANT_USER_API_KEY")
    fnb_tenant_admin_api_key: str | None = Field(None, env="FNB_TENANT_ADMIN_API_KEY")
    pnp_partner_api_key: str | None = Field(None, env="PNP_PARTNER_API_KEY")
    pnp_tenant_user_api_key: str | None = Field(None, env="PNP_TENANT_USER_API_KEY")
    pnp_tenant_admin_api_key: str | None = Field(None, env="PNP_TENANT_ADMIN_API_KEY")

    # Local role-scoped keys used while the platform moves toward OAuth2/JWT claims.
    fnb_producer_api_key: str | None = Field(None, env="FNB_PRODUCER_API_KEY")
    fnb_producer_code: str | None = Field(None, env="FNB_PRODUCER_CODE")
    fnb_distributor_api_key: str | None = Field(None, env="FNB_DISTRIBUTOR_API_KEY")
    fnb_distributor_code: str | None = Field(None, env="FNB_DISTRIBUTOR_CODE")
    fnb_consumer_api_key: str | None = Field(None, env="FNB_CONSUMER_API_KEY")

    worker_secret: str | None = Field(None, env="WORKER_SECRET")
    referral_code_secret: str | None = Field(None, env="REFERRAL_CODE_SECRET")
    auth_jwt_secret: str | None = Field(None, env="AUTH_JWT_SECRET")
    auth_jwt_issuer: str | None = Field(None, env="AUTH_JWT_ISSUER")
    auth_jwt_audience: str | None = Field(None, env="AUTH_JWT_AUDIENCE")
    auth_jwt_role_claims: str = Field("role,amplifi_role", env="AUTH_JWT_ROLE_CLAIMS")
    auth_jwt_tenant_claims: str = Field(
        "tenant_code,tenant", env="AUTH_JWT_TENANT_CLAIMS"
    )
    auth_jwt_subject_claims: str = Field("sub", env="AUTH_JWT_SUBJECT_CLAIMS")
    auth_jwt_producer_claims: str = Field(
        "producer_code", env="AUTH_JWT_PRODUCER_CLAIMS"
    )
    auth_jwt_distributor_claims: str = Field(
        "distributor_code", env="AUTH_JWT_DISTRIBUTOR_CLAIMS"
    )
    auth_jwt_client_claims: str = Field("client_id", env="AUTH_JWT_CLIENT_CLAIMS")
    auth_jwt_scope_claims: str = Field("scopes,scope", env="AUTH_JWT_SCOPE_CLAIMS")
    partner_webhook_secret_key: str | None = Field(
        None, env="PARTNER_WEBHOOK_SECRET_KEY"
    )
    partner_webhook_secret_provider: str = Field(
        "APPLICATION_KEY", env="PARTNER_WEBHOOK_SECRET_PROVIDER"
    )
    partner_webhook_kms_key_id: str | None = Field(
        None, env="PARTNER_WEBHOOK_KMS_KEY_ID"
    )
    partner_webhook_kms_backend: str = Field(
        "LOCAL_ENVELOPE", env="PARTNER_WEBHOOK_KMS_BACKEND"
    )
    partner_webhook_alert_notification_url: str | None = Field(
        None, env="PARTNER_WEBHOOK_ALERT_NOTIFICATION_URL"
    )
    partner_webhook_alert_notification_secret: str | None = Field(
        None, env="PARTNER_WEBHOOK_ALERT_NOTIFICATION_SECRET"
    )
    channel_whatsapp_provider_url: str | None = Field(
        None, env="CHANNEL_WHATSAPP_PROVIDER_URL"
    )
    channel_whatsapp_provider_secret: str | None = Field(
        None, env="CHANNEL_WHATSAPP_PROVIDER_SECRET"
    )
    channel_sms_provider_url: str | None = Field(None, env="CHANNEL_SMS_PROVIDER_URL")
    channel_sms_provider_secret: str | None = Field(
        None, env="CHANNEL_SMS_PROVIDER_SECRET"
    )
    channel_ussd_provider_url: str | None = Field(None, env="CHANNEL_USSD_PROVIDER_URL")
    channel_ussd_provider_secret: str | None = Field(
        None, env="CHANNEL_USSD_PROVIDER_SECRET"
    )
    channel_email_provider_url: str | None = Field(None, env="CHANNEL_EMAIL_PROVIDER_URL")
    channel_email_provider_secret: str | None = Field(
        None, env="CHANNEL_EMAIL_PROVIDER_SECRET"
    )
    channel_email_provider_ref: str | None = Field(
        None, env="CHANNEL_EMAIL_PROVIDER_REF"
    )
    channel_email_provider_approved: bool = Field(
        False, env="CHANNEL_EMAIL_PROVIDER_APPROVED"
    )
    channel_email_provider_scopes: str = Field(
        "", env="CHANNEL_EMAIL_PROVIDER_SCOPES"
    )

    database_url: str | None = Field(None, env="APP_DB_DSN")
    redis_url: str | None = Field(None, env="REDIS_URL")
    aws_region: str | None = Field(None, env="AWS_REGION")
    app_sqs_queue_url: str | None = Field(None, env="APP_SQS_QUEUE_URL")
    app_sqs_dlq_url: str | None = Field(None, env="APP_SQS_DLQ_URL")
    app_sqs_max_receive_count: int = Field(3, env="APP_SQS_MAX_RECEIVE_COUNT")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
