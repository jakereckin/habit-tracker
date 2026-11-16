import datetime as dt
from typing import Optional
from zoneinfo import ZoneInfo

import pandas as pd


CENTRAL_TIMEZONE = ZoneInfo("America/Chicago")
WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


def local_now() -> dt.datetime:
    return dt.datetime.now(CENTRAL_TIMEZONE)


def local_today() -> dt.date:
    return local_now().date()


def parse_scheduled_days(value: Optional[str]) -> set[int]:
    if not value:
        return set()
    try:
        days = {int(day) for day in str(value).split(",")}
    except ValueError as error:
        raise ValueError(
            "Scheduled weekdays must be comma-separated numbers from 0 to 6."
        ) from error
    if any(day < 0 or day > 6 for day in days):
        raise ValueError("Scheduled weekdays must be numbers from 0 to 6.")
    return days


def is_habit_due(
    frequency: str,
    scheduled_days: Optional[str],
    target_date: dt.date,
) -> bool:
    normalized_frequency = frequency.upper()
    if normalized_frequency == "DAILY":
        return True
    if normalized_frequency == "WEEKLY":
        return target_date.weekday() in parse_scheduled_days(scheduled_days)
    if normalized_frequency == "MONTHLY":
        return False
    raise ValueError(f"Unsupported habit frequency: {frequency}")


def skipped_habits_for_date(
    skip_days: pd.DataFrame, target_date: dt.date
) -> set[str]:
    if skip_days.empty or not {"DATE", "HABIT_NAME"}.issubset(skip_days.columns):
        return set()
    dates = pd.to_datetime(skip_days["DATE"], errors="coerce")
    rows = skip_days.loc[dates.dt.date == target_date]
    return set(rows["HABIT_NAME"].dropna().astype(str))


def skipped_dates_for_habit(
    skip_days: pd.DataFrame, habit_name: str
) -> set[dt.date]:
    if skip_days.empty or not {"DATE", "HABIT_NAME"}.issubset(skip_days.columns):
        return set()
    rows = skip_days.loc[skip_days["HABIT_NAME"] == habit_name]
    return set(pd.to_datetime(rows["DATE"], errors="coerce").dropna().dt.date)


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
    tracking: pd.DataFrame,
    target_date: dt.date,
    skipped_habits: Optional[set[str]] = None,
) -> set[str]:
    if tracking.empty or "DATE" not in tracking:
        return set()

    dates = pd.to_datetime(tracking["DATE"], errors="coerce")
    completed_rows = _completed_rows(tracking.loc[dates.dt.date == target_date])
    completed = set(completed_rows["HABIT_NAME"].dropna().astype(str))
    return completed - (skipped_habits or set())


def habit_period_progress(
    tracking: pd.DataFrame,
    habit_name: str,
    target_date: dt.date,
    frequency: str,
    scheduled_days: Optional[str] = None,
    period_target: Optional[int] = None,
    skipped_dates: Optional[set[dt.date]] = None,
) -> tuple[int, int, str]:
    normalized_frequency = frequency.upper()
    excluded_dates = skipped_dates or set()

    if normalized_frequency == "DAILY":
        period_start = target_date
        period_end = target_date
        target_count = 0 if target_date in excluded_dates else 1
        period_label = "today"
        scheduled_dates = {target_date} if target_count else set()
    elif normalized_frequency == "WEEKLY":
        period_start = target_date - dt.timedelta(days=target_date.weekday())
        period_end = period_start + dt.timedelta(days=6)
        scheduled_dates = {
            period_start + dt.timedelta(days=day)
            for day in parse_scheduled_days(scheduled_days)
        } - excluded_dates
        target_count = len(scheduled_dates)
        period_label = "this week"
    elif normalized_frequency == "MONTHLY":
        period_start = target_date.replace(day=1)
        if target_date.month == 12:
            next_month = dt.date(target_date.year + 1, 1, 1)
        else:
            next_month = dt.date(target_date.year, target_date.month + 1, 1)
        period_end = next_month - dt.timedelta(days=1)
        if period_target is None or period_target <= 0:
            raise ValueError("Monthly habits require a positive period target.")
        target_count = period_target
        scheduled_dates = set()
        period_label = "this month"
    else:
        raise ValueError(f"Unsupported habit frequency: {frequency}")

    if tracking.empty or not {"DATE", "HABIT_NAME"}.issubset(tracking.columns):
        return 0, target_count, period_label

    dates = pd.to_datetime(tracking["DATE"], errors="coerce")
    rows = tracking.loc[
        (tracking["HABIT_NAME"] == habit_name)
        & (dates.dt.date >= period_start)
        & (dates.dt.date <= period_end)
    ]
    complete_dates = set(
        pd.to_datetime(_completed_rows(rows)["DATE"], errors="coerce")
        .dropna()
        .dt.date
    ) - excluded_dates
    if normalized_frequency in {"DAILY", "WEEKLY"}:
        complete_dates &= scheduled_dates
    return len(complete_dates), target_count, period_label


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
    tracking: pd.DataFrame,
    habit_name: str,
    as_of: dt.date,
    skipped_dates: Optional[set[dt.date]] = None,
) -> int:
    neutral_dates = skipped_dates or set()
    completed_dates = _dates_for_habit(tracking, habit_name) - neutral_dates
    current_date = as_of
    if current_date not in completed_dates and current_date not in neutral_dates:
        current_date -= dt.timedelta(days=1)

    streak = 0
    while current_date in completed_dates or current_date in neutral_dates:
        if current_date in completed_dates:
            streak += 1
        current_date -= dt.timedelta(days=1)
    return streak


def best_streak(
    tracking: pd.DataFrame,
    habit_name: str,
    skipped_dates: Optional[set[dt.date]] = None,
) -> int:
    neutral_dates = skipped_dates or set()
    completed_dates = _dates_for_habit(tracking, habit_name) - neutral_dates
    streak_dates = sorted(completed_dates | neutral_dates)
    longest = 0
    run = 0
    previous_date = None

    for completed_date in streak_dates:
        if (
            previous_date is not None
            and completed_date == previous_date + dt.timedelta(days=1)
        ):
            if completed_date in completed_dates:
                run += 1
        else:
            run = 1 if completed_date in completed_dates else 0
        longest = max(longest, run)
        previous_date = completed_date
    return longest
