from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "docs" / "STRATEGIC_9_10_TASK_LIST.md"
STATUS_WEIGHTS = {"Done": 1.0, "Partial": 0.5, "Todo": 0.0}


def _rows(markdown: str) -> list[tuple[str, str, str]]:
    pattern = re.compile(r"^\| (Done|Partial|Todo) \| (.*?) \| (.*?) \|$", re.MULTILINE)
    return [(status, task, evidence) for status, task, evidence in pattern.findall(markdown)]


def main() -> int:
    markdown = CHECKLIST.read_text(encoding="utf-8")
    rows = _rows(markdown)
    if not rows:
        print(f"No checklist rows found in {CHECKLIST}", file=sys.stderr)
        return 1

    completed = sum(STATUS_WEIGHTS[status] for status, _, _ in rows)
    percent = completed / len(rows) * 100
    counts = {status: sum(1 for row in rows if row[0] == status) for status in STATUS_WEIGHTS}

    print(
        "Strategic 9/10 task list: "
        f"{completed:.1f}/{len(rows)} effective complete ({percent:.1f}%)."
    )
    print(
        "Tasks by status: "
        f"Done {counts['Done']}, Partial {counts['Partial']}, Todo {counts['Todo']}."
    )

    next_todo = next(((task, evidence) for status, task, evidence in rows if status == "Todo"), None)
    if next_todo:
        task, evidence = next_todo
        print(f"Next open task: {task} ({evidence})")
    else:
        print("Next open task: none.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
