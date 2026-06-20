import argparse, csv, json
from datetime import datetime, timezone
from pathlib import Path
from utils.db import get_connection
from utils.logging import get_logger

logger = get_logger(__name__)

def parse_dt(s: str) -> datetime:
    # Accept ISO or 'YYYY-MM-DD HH:MM:SS' and force UTC
    try:
        return datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(timezone.utc)
    except Exception:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

def upsert_event(cur, row):
    cur.execute(
        """
        INSERT INTO enterprise_events (referral_track_id, event_type, occurred_at, attributes)
        VALUES (%s, %s, %s, %s::jsonb)
        """, (row["referral_track_id"], row["event_type"], row["occurred_at"], json.dumps(row.get("attributes") or {}))
    )

def load_csv(path: Path):
    with path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            yield {
                "referral_track_id": r["referral_track_id"],
                "event_type": r["event_type"],
                "occurred_at": parse_dt(r["occurred_at"]),
                "attributes": json.loads(r.get("attributes") or "{}"),
            }

def load_json(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    for r in data:
        r["occurred_at"] = parse_dt(r["occurred_at"])
        yield r

def main():
    ap = argparse.ArgumentParser(description="Backfill enterprise events into DB")
    ap.add_argument("--file", required=True, help="Path to CSV or JSON with events")
    args = ap.parse_args()
    p = Path(args.file)
    if not p.exists():
        logger.error("File not found: %s", p); return

    loader = load_csv if p.suffix.lower()==".csv" else load_json
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            count = 0
            for row in loader(p):
                upsert_event(cur, row); count += 1
            conn.commit()
        logger.info("Backfilled %s events from %s", count, p.name)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
