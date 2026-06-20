# config/

Central home for application settings and operational configuration.

## Files
- `settings.py`: Pydantic-powered loader with YAML overlays + env vars.
- `settings.dev.yaml` / `settings.prod.yaml`: Declarative per-env configs.
- `logging.yaml`: Python logging config.
- `kafka.yaml`: Kafka brokers and topics.
- `db.yaml`: DB pool/migration settings.
- `cooldown.py`: Feature flags + cooldown policy defaults.
- `__init__.py`: Exposes `settings` singleton.

## Precedence
1. Defaults in `settings.py`
2. YAML overlay (`settings.<APP_ENV>.yaml`)
3. Environment variables
