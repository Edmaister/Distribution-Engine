from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "docs" / "ENTERPRISE_READINESS_9_CHECKLIST.md"


def _parse_weight(value: str) -> int:
    return int(value.strip().rstrip("%"))


def main() -> int:
    completed = 0
    total = 0
    rows = []

    for line in CHECKLIST.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 5 or cells[0] in {"Status", "---"}:
            continue
        if cells[3].startswith("---"):
            continue

        status, area, task, weight_text, evidence = cells
        weight = _parse_weight(weight_text)
        total += weight
        if status.lower() == "done":
            completed += weight
        rows.append((status, area, task, weight, evidence))

    percent = round((completed / total) * 100) if total else 0
    done_count = sum(1 for status, *_ in rows if status.lower() == "done")

    print(f"Enterprise readiness 9/10 checklist: {completed}/{total} weight complete ({percent}%)")
    print(f"Tasks complete: {done_count}/{len(rows)}")

    next_items = [(area, task, weight) for status, area, task, weight, _ in rows if status.lower() != "done"]
    if next_items:
        area, task, weight = sorted(next_items, key=lambda item: item[2], reverse=True)[0]
        print(f"Highest-impact remaining task: [{area}] {task} ({weight})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
