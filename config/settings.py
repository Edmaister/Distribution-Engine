from __future__ import annotations

import os
from typing import Any, Dict

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


# ---------------------------------------------------------
# ENV + YAML CONFIG
# ---------------------------------------------------------
APP_ENV = os.getenv("APP_ENV", "dev").lower()
YAML_PATH = os.path.join(
    os.path.dirname(__file__),
    f"settings.{APP_ENV}.yaml",
)


def _load_yaml(path: str) -> Dict[str, Any]:
    if yaml is None:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


# ---------------------------------------------------------
# SETTINGS MODEL
# ---------------------------------------------------------
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -----------------------------
    # CORE APP
    # -----------------------------
    app_name: str = Field("Referral Engine API", env="APP_NAME")
    app_env: str = Field(APP_ENV, env="APP_ENV")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")

    # -----------------------------
    # DATABASE
    # -----------------------------
    db_dsn: str = Field(
        "postgresql://<db-user>:<db-password>@<db-host>:<db-port>/<db-name>",
        env="APP_DB_DSN",
    )

    # Alias for compatibility with older services
    database_url: str | None = Field(None, env="APP_DB_DSN")

    # -----------------------------
    # KAFKA / EVENTS
    # -----------------------------
    kafka_broker: str = Field("kafka:9092", env="APP_KAFKA_BROKER")
    kafka_client: str = Field("stdout", env="APP_KAFKA_CLIENT")

    # -----------------------------
    # FEATURE FLAGS
    # -----------------------------
    enable_cooldowns: bool = Field(True, env="ENABLE_COOLDOWNS")

    # -----------------------------
    # SECURITY / AUTH
    # -----------------------------
    admin_api_key: str | None = Field(None, env="ADMIN_API_KEY")
    partner_api_key: str | None = Field(None, env="PARTNER_API_KEY")

    worker_secret: str | None = Field(None, env="WORKER_SECRET")
    referral_code_secret: str | None = Field(None, env="REFERRAL_CODE_SECRET")

    # -----------------------------
    # TENANCY
    # -----------------------------
    tenant_default: str = Field("DEFAULT", env="APP_TENANT_DEFAULT")

    # -----------------------------
    # INFRA
    # -----------------------------
    aws_region: str | None = Field(None, env="AWS_REGION")

    # ---------------------------------------------------------
    # LOAD WITH YAML OVERRIDE
    # ---------------------------------------------------------
    @classmethod
    def load(cls) -> "Settings":
        yaml_data = _load_yaml(YAML_PATH)
        return cls(**yaml_data)


# ---------------------------------------------------------
# SINGLETON INSTANCE
# ---------------------------------------------------------
settings = Settings.load()
