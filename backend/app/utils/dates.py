from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """Returns the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def utc_iso() -> str:
    """Returns the current UTC timestamp formatted as ISO 8601 string."""
    return utc_now().isoformat()


def normalize_month(date_or_month_str: str) -> str:
    """
    Normalizes a date or period string to 'YYYY-MM'.
    Accepts 'YYYY-MM' or 'YYYY-MM-DD'.
    """
    cleaned = date_or_month_str.strip()
    if len(cleaned) >= 7 and cleaned[4] == "-":
        return cleaned[:7]
    return cleaned
