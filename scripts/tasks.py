# tasks.py — Invoke (pip install invoke)
from invoke import task
import os

PY = os.environ.get("PY", "python")

@task
def env(c):
    print("APP_DB_DSN=", os.environ.get("APP_DB_DSN"))
    print("APP_KAFKA_BROKER=", os.environ.get("APP_KAFKA_BROKER"))
    print("APP_KAFKA_CLIENT=", os.environ.get("APP_KAFKA_CLIENT"))
    print("LOG_LEVEL=", os.environ.get("LOG_LEVEL"))

@task
def db_init(c):
    c.run(f"{PY} scripts/init_db.py", pty=True)

@task
def db_seed(c):
    c.run(f"{PY} scripts/seed_db.py", pty=True)

@task
def db_setup(c):
    db_init(c); db_seed(c)

@task(help={'file': 'Path to CSV/JSON with enterprise events'})
def backfill(c, file):
    c.run(f"{PY} scripts/backfill_events.py --file {file}", pty=True)

@task(help={
    'sticker': 'Default sticker (e.g., PREMIER)',
    'tenant': 'Tenant code (e.g., FNB)',
    'topk': 'Top-K recommendations to cache'})
def recos(c, sticker="PREMIER", tenant="", topk=3):
    c.run(f'{PY} scripts/refresh_recommendations.py --sticker "{sticker}" --tenant "{tenant}" --top-k {topk}', pty=True)

@task
def refresh_mv(c):
    c.run(f"{PY} scripts/refresh_materialized_views.py", pty=True)

@task
def health(c):
    c.run(f"{PY} scripts/health_check.py", pty=True)
