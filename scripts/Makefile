# Makefile — convenience wrappers for scripts/

PY?=python

# ----- Environment -----
.PHONY: env
env:
	@echo "APP_DB_DSN=$${APP_DB_DSN}"
	@echo "APP_KAFKA_BROKER=$${APP_KAFKA_BROKER}"
	@echo "APP_KAFKA_CLIENT=$${APP_KAFKA_CLIENT}"
	@echo "LOG_LEVEL=$${LOG_LEVEL}"

# ----- Database -----
.PHONY: db-init
db-init:
	$(PY) scripts/init_db.py

.PHONY: db-seed
db-seed:
	$(PY) scripts/seed_db.py

# Apply all migrations then seeds
.PHONY: db-setup
db-setup: db-init db-seed

# ----- Data backfill -----
# Usage: make backfill FILE=./events.csv
.PHONY: backfill
backfill:
	@test -n "$(FILE)" || (echo "Usage: make backfill FILE=./events.csv"; exit 1)
	$(PY) scripts/backfill_events.py --file $(FILE)

# ----- Recommendations & Insights -----
# Usage: make recos STICKER=PREMIER TENANT=FNB TOPK=3
.PHONY: recos
recos:
	$(PY) scripts/refresh_recommendations.py --sticker "$(STICKER)" --tenant "$(TENANT)" --top-k $(TOPK)

# ----- Materialized Views -----
.PHONY: refresh-mv
refresh-mv:
	$(PY) scripts/refresh_materialized_views.py

# ----- Health -----
.PHONY: health
health:
	$(PY) scripts/health_check.py

# ----- Lint (optional, local) -----
.PHONY: lint
lint:
	@echo "Add your linter here (ruff/flake8)."

# ----- Help -----
.PHONY: help
help:
	@echo "Targets:"
	@echo "  env                 Show important env vars"
	@echo "  db-init             Apply migrations in db/migrations"
	@echo "  db-seed             Apply seeds in db/seeds"
	@echo "  db-setup            Run db-init then db-seed"
	@echo "  backfill FILE=...   Backfill enterprise events from CSV/JSON"
	@echo "  recos STICKER=... TENANT=... TOPK=3   Refresh recommendation caches"
	@echo "  refresh-mv          Refresh materialized views"
	@echo "  health              Check DB & Kafka connectivity"
	@echo "  lint                Run linter (placeholder)"
