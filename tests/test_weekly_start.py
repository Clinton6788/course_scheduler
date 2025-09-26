import datetime as dt
from src.helpers import round_to_nearest_weekday_start, get_holiday_dates


# Local to ensure all active
SESSION_HOLIDAYS = [
    "new_year",
    "mlk_day",
    "presidents_day",
    "memorial_day",
    "juneteenth",
    "independence_day",
    "labor_day",
    "columbus_day",
    "veterans_day",
    "thanksgiving",
    "christmas",
]


def test_round_to_nearest_weekday_start():
    """
    Unit test for round_to_nearest_weekday_start(), Sundays only,
    respecting ±1 week window and skipping holidays within the window.
    """
    target_month = 9
    target_weekday = 6  # Sunday

    # Example 1: Sep 1, 2025 (Labor Day weekend)
    input_date = dt.date(2025, 9, 1)
    expected = dt.date(2025, 9, 7)  # Nearest valid Sunday within ±1 week
    result = round_to_nearest_weekday_start(input_date, target_month, target_weekday, SESSION_HOLIDAYS)
    assert result == expected, f"Expected {expected}, got {result}"

    # Example 2: Normal case with no holidays interfering
    input_date = dt.date(2025, 9, 10)
    expected = dt.date(2025, 9, 7)  # Nearest previous Sunday within ±1 week
    result = round_to_nearest_weekday_start(input_date, target_month, target_weekday, SESSION_HOLIDAYS)
    assert result == expected, f"Expected {expected}, got {result}"

    # Example 3: Date very early in month; nearest Sunday within ±1 week
    input_date = dt.date(2025, 9, 2)
    expected = dt.date(2025, 9, 7)  # Aug 24 is outside ±1 week, so ignored
    result = round_to_nearest_weekday_start(input_date, target_month, target_weekday, SESSION_HOLIDAYS)
    assert result == expected, f"Expected {expected}, got {result}"

    print("All tests passed!")

