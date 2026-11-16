import pandas as pd
import streamlit as st

from py.auth import require_user
from py.habit_logic import (
    best_streak,
    completed_habits_for_date,
    current_streak,
    habit_period_progress,
    local_today,
    skipped_dates_for_habit,
    skipped_habits_for_date,
)
from py.habits import get_habits, get_skip_days, get_tracking


email = require_user()

st.title("Your progress")
st.caption("Notice what is working and keep showing up.")

habits = get_habits(email)
tracking = get_tracking(email)
skip_days = get_skip_days(email)
active_habits = habits[habits["ACTIVE"].astype(str).str.upper() == "Y"]
today = local_today()
completed_today = completed_habits_for_date(
    tracking,
    today,
    skipped_habits_for_date(skip_days, today),
)
tracked_habits = (
    int(tracking["HABIT_NAME"].nunique()) if not tracking.empty else 0
)
daily_habit_names = habits.loc[
    habits["GOAL_FREQUENCY"].astype(str).str.upper() == "DAILY",
    "HABIT_NAME",
].dropna().astype(str)
longest_streak = max(
    (
        best_streak(
            tracking,
            habit,
            skipped_dates_for_habit(skip_days, habit),
        )
        for habit in daily_habit_names
    ),
    default=0,
)

metric_columns = st.columns(3)
metric_columns[0].metric("Completed today", len(completed_today))
metric_columns[1].metric("Habits tracked", tracked_habits)
metric_columns[2].metric("Longest daily streak", f"{longest_streak} days")

st.subheader("Check-ins over the last 30 days")
if tracking.empty:
    st.info("Your progress chart will appear after your first check-in.")
else:
    chart_dates = pd.date_range(end=pd.Timestamp(today), periods=30, freq="D")
    recent_counts = pd.Series(
        [
            len(
                completed_habits_for_date(
                    tracking,
                    chart_date.date(),
                    skipped_habits_for_date(skip_days, chart_date.date()),
                )
            )
            for chart_date in chart_dates
        ],
        index=chart_dates,
    )
    recent_counts.index.name = "Date"
    st.bar_chart(recent_counts.rename("Completed habits"))

st.subheader("Cadence progress")
if active_habits.empty:
    st.info("Resume or add a habit to see its progress.")
else:
    streak_rows = []
    for habit in active_habits.itertuples(index=False):
        habit_name = str(habit.HABIT_NAME)
        frequency = str(habit.GOAL_FREQUENCY).upper()
        skipped_dates = skipped_dates_for_habit(skip_days, habit_name)
        done_count, target_count, period_label = habit_period_progress(
            tracking,
            habit_name,
            today,
            frequency,
            habit.SCHEDULED_DAYS,
            habit.PERIOD_TARGET,
            skipped_dates,
        )
        streak_rows.append(
            {
                "Habit": habit_name,
                "Cadence": frequency.title(),
                "Period progress": (
                    f"{done_count}/{target_count} {period_label}"
                ),
                "Current streak": (
                    f"{current_streak(tracking, habit_name, today, skipped_dates)} days"
                    if frequency == "DAILY"
                    else "—"
                ),
                "Best streak": (
                    f"{best_streak(tracking, habit_name, skipped_dates)} days"
                    if frequency == "DAILY"
                    else "—"
                ),
            }
        )
    st.dataframe(
        pd.DataFrame(streak_rows),
        hide_index=True,
        width="stretch",
    )
