# utils package: infra helpers shared across services and apps
# - db.py        : Postgres connection helpers
# - kafka.py     : Event publishing (Kafka) with safe fallbacks
# - sqlalchemy.py: Optional SQLAlchemy session factory (used by validate_referral)
# - crypto.py    : UCN encryption + hashing
# - logging.py   : Structured logging helpers
# - time.py      : ISO timestamps & UTC helpers
