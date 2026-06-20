# Legacy Migration Artifacts

These files are historical SQL artifacts that are not part of the clean replay
chain. Active migrations must live in `dp/migrations` and use the
`NNN_description.sql` naming convention.

The database startup runner and CI migration hygiene checks intentionally apply
only numbered SQL files from `dp/migrations`. Move a legacy file back only after
renumbering it, making it idempotent, and proving it replays from an empty
database.
