a complete, SA-friendly **utils/** pack aligned to the folder structure and all the services we’ve built. Each module includes clear comments, safe fallbacks, and environment-driven config.


# What each does (and how it supports the broader app)

## utils/db.py

* **Single source** for Postgres connections (`get_connection()`), used by all services and workers.
* Context manager `db_cursor()` for safe commit/rollback.
* **Env:** `APP_DB_DSN` (e.g., `postgresql://user:pass@host:5432/referrals`).

## utils/kafka.py

* `publish_event(topic, payload)` with **confluent-kafka** or **kafka-python** support.
* Falls back to **stdout logging** when no Kafka client is installed (dev safe).
* **Env:** `APP_KAFKA_BROKER`, `APP_KAFKA_CLIENT` (`confluent` | `kafka-python` | `stdout`).

## utils/sqlalchemy.py

* Optional **SQLAlchemy** session factory for modules that prefer ORM access.
* If missing, services already include a **shim** via `utils.db`.
* **Env:** `APP_DB_DSN`.

## utils/crypto.py

* `encrypt_ucn(raw)` — uses **Fernet** if `UCN_ENC_KEY` is provided; otherwise **HMAC-SHA256** deterministic surrogate (non-reversible) for secure storage.
* `hash_ucn(raw)` — **SHA-256** one-way hash for events & audits (PII-safe).
* **Env:** `UCN_ENC_KEY` (base64 urlsafe Fernet key), `UCN_SALT` (fallback HMAC salt).

## utils/logging.py

* JSON structured logs with `get_logger(__name__)`.
* Good for API and workers; includes timestamp, level, name, message, and extras.
* **Env:** `LOG_LEVEL`.

## utils/time.py

* `utcnow()`, `to_isoz(dt)`, `parse_iso(s)` — consistent UTC timestamping for events and DB writes.

---

## How these utilities are used across your app

* **Services** (`services/*.py`):

  * `utils.db.get_connection()` in policy, eligibility, rewards, campaigns, referral issuance, gamification, recommendation.
  * `utils.kafka.publish_event()` to emit platform events (`REFERRAL_CODE_ISSUED`, `REWARD_APPLIED`, etc.).
  * `utils.crypto` in `update_ucn.py` for secure UCN handling.

* **API** (`apps/api/*`):

  * Routers call into services; these utils keep infra concerns uniform (DB, Kafka).

* **Workers** (`apps/workers/*`):

  * IDS consumer and recommendation refresher rely on `utils.db` and `utils.kafka` for ingestion and notifications.

---

## Environment quick reference (copy to `.env`)

```
APP_DB_DSN=postgresql://user:pass@localhost:5432/referrals
APP_KAFKA_BROKER=localhost:9092
APP_KAFKA_CLIENT=stdout   # or confluent | kafka-python
LOG_LEVEL=INFO

# Optional (strongly recommended in prod)
UCN_ENC_KEY=   # base64 urlsafe Fernet key (e.g., generate via cryptography.Fernet.generate_key())
UCN_SALT=change-me-if-no-Fernet
```

If you want, I can also:

* add a tiny **health check** that pings DB and Kafka using these utils,
* wire **structured logging** into the FastAPI app startup,
* or provide a Docker Compose for `postgres + kafka + api` to make local runs smoother.
