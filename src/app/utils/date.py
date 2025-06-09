from datetime import datetime, timezone, timedelta


def utcnow() -> datetime:
    """Get the current UTC datetime."""
    return datetime.now(timezone.utc)

def to_iso(dt: datetime) -> str:
    """Convert a datetime to an ISO 8601 string (always UTC)."""
    return dt.astimezone(timezone.utc).isoformat()

def from_iso(iso_str: str) -> datetime:
    """Parse an ISO 8601 string to a datetime (assumes UTC if no tzinfo)."""
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def add_minutes(dt: datetime, minutes: int) -> datetime:
    """Add minutes to a datetime."""
    return dt + timedelta(minutes=minutes)

def add_days(dt: datetime, days: int) -> datetime:
    """Add days to a datetime."""
    return dt + timedelta(days=days)
