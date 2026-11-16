import datetime as dt
from typing import Optional
from zoneinfo import ZoneInfo

import pandas as pd


CENTRAL_TIMEZONE = ZoneInfo("America/Chicago")


def local_now() -> dt.datetime:
    return dt.datetime.now(CENTRAL_TIMEZONE)


def local_today() -> dt.date:
    return local_now().date()


def _completed_rows(rows: pd.DataFrame) -> pd.DataFrame:
    if "COUNT_COMPLETED" not in rows:
        return rows

    counts = pd.to_numeric(rows["COUNT_COMPLETED"], errors="coerce").fillna(0)
    complete = counts > 0
    if "GOAL_TYPE" in rows:
        numeric = rows["GOAL_TYPE"].fillna("").astype(str).str.upper() == "NUMERIC"
        if "DAILY_GOAL" in rows:
            goals = pd.to_numeric(rows["DAILY_GOAL"], errors="coerce")
            complete.loc[numeric] = (
                goals.loc[numeric].gt(0)
                & counts.loc[numeric].ge(goals.loc[numeric])
            )
        else:
            complete.loc[numeric] = False
    return rows.loc[complete]


def completed_habits_for_date(
    tracking: pd.DataFrame, target_date: dt.date
) -> set[str]:
    if tracking.empty or "DATE" not in tracking:
        return set()

    dates = pd.to_datetime(tracking["DATE"], errors="coerce")
    completed_rows = _completed_rows(tracking.loc[dates.dt.date == target_date])
    return set(completed_rows["HABIT_NAME"].dropna().astype(str))


def daily_progress(
    tracking: pd.DataFrame,
    habit_name: str,
    target_date: dt.date,
    default_goal: Optional[float] = None,
) -> tuple[float, Optional[float]]:
    if tracking.empty:
        return 0.0, default_goal
    if not {"DATE", "HABIT_NAME"}.issubset(tracking.columns):
        return 0.0, default_goal

    dates = pd.to_datetime(tracking["DATE"], errors="coerce")
    rows = tracking.loc[
        (tracking["HABIT_NAME"] == habit_name) & (dates.dt.date == target_date)
    ]
    if rows.empty:
        return 0.0, default_goal

    counts = (
        pd.to_numeric(rows["COUNT_COMPLETED"], errors="coerce").fillna(0)
        if "COUNT_COMPLETED" in rows
        else pd.Series(0, index=rows.index)
    )
    goals = (
        pd.to_numeric(rows["DAILY_GOAL"], errors="coerce").dropna()
        if "DAILY_GOAL" in rows
        else pd.Series(dtype=float)
    )
    goal = float(goals.iloc[-1]) if not goals.empty else default_goal
    return float(counts.sum()), goal


def _dates_for_habit(tracking: pd.DataFrame, habit_name: str) -> set[dt.date]:
    if tracking.empty or not {"DATE", "HABIT_NAME"}.issubset(tracking.columns):
        return set()

    rows = tracking.loc[tracking["HABIT_NAME"] == habit_name]
    dates = pd.to_datetime(rows["DATE"], errors="coerce").dropna().dt.date
    complete_rows = _completed_rows(rows)
    complete_dates = pd.to_datetime(
        complete_rows["DATE"], errors="coerce"
    ).dropna().dt.date
    return set(complete_dates) if "COUNT_COMPLETED" in rows else set(dates)


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
