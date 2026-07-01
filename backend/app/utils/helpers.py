"""General utility helpers"""

import json
import uuid
from datetime import date, datetime, timedelta
from typing import Any


def generate_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


def utcnow() -> datetime:
    """Return current UTC datetime."""
    from datetime import timezone
    return datetime.now(tz=timezone.utc)


def safe_json_loads(value: str | None, default: Any = None) -> Any:
    """Safely parse a JSON string, returning default on failure."""
    if value is None:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


def calculate_streak(dates: list[date]) -> tuple[int, int]:
    """
    Calculate current and longest streaks from a sorted list of active dates.

    Args:
        dates: List of date objects with activity (sorted ascending)

    Returns:
        (current_streak, longest_streak)
    """
    if not dates:
        return 0, 0

    unique_dates = sorted(set(dates))
    today = date.today()

    # Check if activity exists today or yesterday (to keep streak alive)
    if unique_dates[-1] < today - timedelta(days=1):
        current_streak = 0
    else:
        # Count consecutive days backwards from the last active date
        current_streak = 1
        for i in range(len(unique_dates) - 1, 0, -1):
            if (unique_dates[i] - unique_dates[i - 1]).days == 1:
                current_streak += 1
            else:
                break

    # Calculate longest streak
    longest_streak = 1
    temp_streak = 1
    for i in range(1, len(unique_dates)):
        if (unique_dates[i] - unique_dates[i - 1]).days == 1:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 1

    return current_streak, max(longest_streak, current_streak)


def parse_submission_calendar(calendar_json: str) -> dict[str, int]:
    """
    Parse LeetCode submission calendar from JSON string.

    LeetCode returns timestamps as keys, counts as values:
    {"1701388800": 3, "1701475200": 1, ...}

    Returns a dict with ISO date strings as keys: {"2023-12-01": 3}
    """
    data = safe_json_loads(calendar_json, {})
    result = {}
    for ts_str, count in data.items():
        try:
            ts = int(ts_str)
            d = date.fromtimestamp(ts)
            result[d.isoformat()] = int(count)
        except (ValueError, OSError):
            continue
    return result


def normalize_score(value: float, min_val: float, max_val: float) -> float:
    """Normalize a value to 0–100 scale."""
    if max_val <= min_val:
        return 0.0
    normalized = (value - min_val) / (max_val - min_val) * 100
    return round(max(0.0, min(100.0, normalized)), 2)


def paginate_query(page: int, page_size: int) -> tuple[int, int]:
    """Calculate offset and limit from page number and size."""
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    offset = (page - 1) * page_size
    return offset, page_size


def mask_email(email: str) -> str:
    """Mask email for logging: 'user@example.com' → 'u***@example.com'"""
    parts = email.split("@")
    if len(parts) != 2:
        return "***"
    local, domain = parts
    return f"{local[0]}***@{domain}"


def format_file_size(size_bytes: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes //= 1024
    return f"{size_bytes:.1f} TB"
