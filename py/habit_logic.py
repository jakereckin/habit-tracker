import datetime as dt
from zoneinfo import ZoneInfo

import pandas as pd


CENTRAL_TIMEZONE = ZoneInfo("America/Chicago")


def local_now() -> dt.datetime:
    return dt.datetime.now(CENTRAL_TIMEZONE)


def local_today() -> dt.date:
    return local_now().date()


def completed_habits_for_date(
    tracking: pd.DataFrame, target_date: dt.date
) -> set[str]:
    if tracking.empty or "DATE" not in tracking:
        return set()

    dates = pd.to_datetime(tracking["DATE"], errors="coerce")
    completed_rows = tracking.loc[dates.dt.date == target_date]
    if "COUNT_COMPLETED" in completed_rows:
        counts = pd.to_numeric(
            completed_rows["COUNT_COMPLETED"], errors="coerce"
        ).fillna(0)
        completed_rows = completed_rows.loc[counts > 0]
    return set(completed_rows["HABIT_NAME"].dropna().astype(str))


def _dates_for_habit(tracking: pd.DataFrame, habit_name: str) -> set[dt.date]:
    if tracking.empty or not {"DATE", "HABIT_NAME"}.issubset(tracking.columns):
        return set()

    rows = tracking.loc[tracking["HABIT_NAME"] == habit_name]
    dates = pd.to_datetime(rows["DATE"], errors="coerce").dropna().dt.date
    if "COUNT_COMPLETED" in rows:
        counts = pd.to_numeric(rows["COUNT_COMPLETED"], errors="coerce").fillna(0)
        dates = pd.to_datetime(
            rows.loc[counts > 0, "DATE"], errors="coerce"
        ).dropna().dt.date
    return set(dates)


def current_streak(
    tracking: pd.DataFrame, habit_name: str, as_of: dt.date
) -> int:
    completed_dates = _dates_for_habit(tracking, habit_name)
    current_date = as_of
    if current_date not in completed_dates:
        current_date -= dt.timedelta(days=1)

    streak = 0
    while current_date in completed_dates:
        streak += 1
        current_date -= dt.timedelta(days=1)
    return streak


def best_streak(tracking: pd.DataFrame, habit_name: str) -> int:
    completed_dates = sorted(_dates_for_habit(tracking, habit_name))
    longest = 0
    run = 0
    previous_date = None

    for completed_date in completed_dates:
        if (
            previous_date is not None
            and completed_date == previous_date + dt.timedelta(days=1)
        ):
            run += 1
        else:
            run = 1
        longest = max(longest, run)
        previous_date = completed_date
    return longest
