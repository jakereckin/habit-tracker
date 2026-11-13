import pandas as pd
import streamlit as st

from py.auth import require_user
from py.habit_logic import (
    best_streak,
    completed_habits_for_date,
    current_streak,
    local_today,
)
from py.habits import get_habits, get_tracking


email = require_user()

st.title("Your progress")
st.caption("Notice what is working and keep showing up.")

habits = get_habits(email)
tracking = get_tracking(email)
active_habits = habits[habits["ACTIVE"].astype(str).str.upper() == "Y"]
today = local_today()
completed_today = completed_habits_for_date(tracking, today)
tracked_habits = (
    int(tracking["HABIT_NAME"].nunique()) if not tracking.empty else 0
)
longest_streak = max(
    (
        best_streak(tracking, habit)
        for habit in habits["HABIT_NAME"].dropna().astype(str)
    ),
    default=0,
)

metric_columns = st.columns(3)
metric_columns[0].metric("Completed today", len(completed_today))
metric_columns[1].metric("Habits tracked", tracked_habits)
metric_columns[2].metric("Longest streak", f"{longest_streak} days")

st.subheader("Check-ins over the last 30 days")
if tracking.empty:
    st.info("Your progress chart will appear after your first check-in.")
else:
    parsed_dates = pd.to_datetime(tracking["DATE"], errors="coerce")
    daily_counts = (
        tracking.assign(DATE_PARSED=parsed_dates)
        .dropna(subset=["DATE_PARSED"])
        .groupby("DATE_PARSED")["HABIT_NAME"]
        .nunique()
    )
    chart_dates = pd.date_range(end=pd.Timestamp(today), periods=30, freq="D")
    recent_counts = daily_counts.reindex(chart_dates, fill_value=0)
    recent_counts.index.name = "Date"
    st.bar_chart(recent_counts.rename("Completed habits"))

st.subheader("Streaks")
if active_habits.empty:
    st.info("Resume or add a habit to see its streak.")
else:
    streak_rows = [
        {
            "Habit": habit,
            "Current streak": current_streak(tracking, habit, today),
            "Best streak": best_streak(tracking, habit),
        }
        for habit in active_habits["HABIT_NAME"].dropna().astype(str)
    ]
    st.dataframe(
        pd.DataFrame(streak_rows),
        hide_index=True,
        width="stretch",
    )
