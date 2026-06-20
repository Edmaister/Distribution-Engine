from __future__ import annotations

import argparse
import re
from pathlib import Path


NUMBERED_SQL_PATTERN = re.compile(r"^\d{3}_[a-z0-9_]+\.sql$")
MIGRATION_PREFIX_PATTERN = re.compile(r"^(\d{3})_")
DISALLOWED_SQL_PATTERNS = (
    "\\d",
    "\\dt",
    "\\i",
)
PSQL_PROMPT_PATTERN = re.compile(r"(?m)^\s*\w+=#\s+")
CREATE_TABLE_WITHOUT_GUARD_PATTERN = re.compile(
    r"(?im)^\s*CREATE\s+TABLE\s+(?!IF\s+NOT\s+EXISTS\b)"
)
CREATE_INDEX_WITHOUT_GUARD_PATTERN = re.compile(
    r"(?im)^\s*CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?!IF\s+NOT\s+EXISTS\b)"
)


def check_files(root: Path) -> list[str]:
    migration_dir = root / "dp" / "migrations"
    failures: list[str] = []

    if not migration_dir.exists():
        return [f"Migration folder not found: {migration_dir}"]

    prefixes: dict[str, list[str]] = {}
    for path in sorted(migration_dir.iterdir()):
        if not path.is_file():
            continue

        if path.suffix.lower() != ".sql":
            if MIGRATION_PREFIX_PATTERN.match(path.name):
                failures.append(
                    f"Numbered migration is not a .sql file: {path.name}"
                )
            continue

        prefix_match = MIGRATION_PREFIX_PATTERN.match(path.name)
        if not prefix_match:
            failures.append(f"Unnumbered SQL file in migration folder: {path.name}")
            continue

        prefixes.setdefault(prefix_match.group(1), []).append(path.name)
        if not NUMBERED_SQL_PATTERN.match(path.name):
            failures.append(
                "Migration filename must be lowercase snake_case with a "
                f"three-digit prefix: {path.name}"
            )

        text = path.read_text(encoding="utf-8")
        for pattern in DISALLOWED_SQL_PATTERNS:
            if pattern in text:
                failures.append(
                    f"Migration contains psql meta-command {pattern}: {path.name}"
                )
        if PSQL_PROMPT_PATTERN.search(text):
            failures.append(f"Migration contains pasted psql prompt text: {path.name}")
        if CREATE_TABLE_WITHOUT_GUARD_PATTERN.search(text):
            failures.append(
                f"Migration creates a table without IF NOT EXISTS: {path.name}"
            )
        if CREATE_INDEX_WITHOUT_GUARD_PATTERN.search(text):
            failures.append(
                f"Migration creates an index without IF NOT EXISTS: {path.name}"
            )

    for prefix, names in sorted(prefixes.items()):
        if len(names) > 1:
            failures.append(
                f"Duplicate migration prefix {prefix}: {', '.join(sorted(names))}"
            )

    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check global SQL migration naming and replay hygiene."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root. Defaults to this script's parent repository.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    failures = check_files(args.root)

    if failures:
        print("[migrations] failed")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("[migrations] passed")
    print("- Migration filenames are numbered lowercase snake_case SQL files.")
    print("- Migration prefixes are unique.")
    print("- SQL files do not contain psql prompt/meta-command artifacts.")
    print("- CREATE TABLE/INDEX statements are guarded for replay.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
