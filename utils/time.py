"""Time helpers."""
from datetime import datetime, timezone
def utcnow() -> datetime: return datetime.now(timezone.utc)
def to_isoz(dt: datetime) -> str: return dt.astimezone(timezone.utc).isoformat().replace('+00:00','Z')
def parse_iso(s: str) -> datetime: return datetime.fromisoformat(s.replace('Z','+00:00'))
