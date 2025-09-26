import datetime as dt
from config.settings import SESSION_START_DAY, SESSION_HOLIDAYS

def prereq_total_count(prereq_str: str) -> int:
    """
    Count total number of prerequisite *requirements* in a prereq string:
    - Each AND prerequisite counts as 1
    - Each OR group (inside []) counts as 1
    """
    if not prereq_str or prereq_str.lower() in {"none", "nan"}:
        return 0  # No prereqs

    count = 0
    tokens = prereq_str.split('|')

    for token in tokens:
        token = token.strip()
        if token.startswith('[') and token.endswith(']'):
            # OR group counts as 1 requirement
            count += 1
        else:
            # AND prerequisite counts as 1 requirement
            count += 1

    return count
 

def round_to_nearest_weekday_start(
        target_date: dt.date,
        target_month: int,
        target_weekday: int = 6,  # Sunday by default
        holidays: list[str] = SESSION_HOLIDAYS,
        ) -> dt.date:
    """
    Round a date to the nearest Sunday (default) within ±1 week, skipping holidays
    only if within the 1-week window. If outside, holiday is ignored.

    Args:
        target_date (dt.date): Input date.
        target_month (int): Month anchor (not used directly for window).
        target_weekday (int, optional): Weekday (Mon=0, Sun=6). Defaults to Sunday.
        holidays (list[str], optional): Holiday identifiers. Defaults to SESSION_HOLIDAYS.

    Returns:
        dt.date: Nearest valid weekday.
    """
    holiday_dates = get_holiday_dates(target_date.year, holidays)

    # Generate candidate Sundays within ±1 week
    candidates = []
    for offset in range(-7, 8):
        candidate = target_date + dt.timedelta(days=offset)
        if candidate.weekday() == target_weekday:
            # Only skip if candidate is within ±1 week and holiday-weekend
            if abs((candidate - target_date).days) <= 7:
                if any((candidate + dt.timedelta(days=o)) in holiday_dates for o in (-2, -1, 0, 1)):
                    continue
            candidates.append(candidate)

    # Pick candidate closest to target_date (tie → earlier)
    nearest = min(candidates, key=lambda d: (abs((d - target_date).days), d))
    return nearest



def get_holiday_dates(year: int, holidays: list[str]) -> list[dt.date]:
    def nth_weekday_in_month(year, month, weekday, n):
        """Return the date of the nth weekday in a given month."""
        first = dt.date(year, month, 1)
        offset = (weekday - first.weekday()) % 7
        return first + dt.timedelta(days=offset + 7 * (n - 1))

    def last_weekday_in_month(year, month, weekday):
        """Return the last weekday in a given month."""
        last_day = dt.date(year, month + 1, 1) - dt.timedelta(days=1) if month < 12 else dt.date(year, 12, 31)
        offset = (last_day.weekday() - weekday) % 7
        return last_day - dt.timedelta(days=offset)

    HOLIDAY_MAP = {
        "new_year": dt.date(year, 1, 1),
        "mlk_day": nth_weekday_in_month(year, 1, 0, 3),          # 3rd Monday in Jan
        "presidents_day": nth_weekday_in_month(year, 2, 0, 3),   # 3rd Monday in Feb
        "memorial_day": last_weekday_in_month(year, 5, 0),       # Last Monday in May
        "juneteenth": dt.date(year, 6, 19),
        "independence_day": dt.date(year, 7, 4),
        "labor_day": nth_weekday_in_month(year, 9, 0, 1),        # 1st Monday in Sep
        "columbus_day": nth_weekday_in_month(year, 10, 0, 2),    # 2nd Monday in Oct
        "veterans_day": dt.date(year, 11, 11),
        "thanksgiving": nth_weekday_in_month(year, 11, 3, 4),    # 4th Thursday in Nov
        "christmas": dt.date(year, 12, 25),
    }

    result = []
    for h in holidays:
        if h not in HOLIDAY_MAP:
            raise ValueError(f"Unknown holiday identifier: {h}")
        result.append(HOLIDAY_MAP[h])
    return result
