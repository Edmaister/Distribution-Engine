# Migration Notes

This folder is the active SQL migration location used by `scripts/init_db.py`.

## Runner Convention

- Migrations are applied in filename sort order.
- Only files ending in `.sql` are applied by the current runner.
- Markdown files and empty placeholders are ignored.

## Current Placeholder

- `018_add_referral_processing_audit` is an empty placeholder. The applied SQL
  migration for that step is `018_add_referral_processing_audit.sql`.

## Operational Notes

- Do not include psql meta-commands such as `\d table_name` in migration files.
- Prefer idempotent statements such as `CREATE TABLE IF NOT EXISTS` and
  `ADD COLUMN IF NOT EXISTS` when a migration may be replayed in local/dev.
- Keep future migration files numbered and suffixed with `.sql`.
