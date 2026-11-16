import datetime as dt

import pandas as pd
import streamlit as st

from py.auth import require_user
from py.habit_logic import (
    completed_habits_for_date,
    current_streak,
    daily_progress,
    local_now,
    local_today,
)
from py.habits import get_habits, get_tracking


email = require_user()

today = local_today()
habits = get_habits(email)
tracking = get_tracking(email)
active_habits = habits[habits["ACTIVE"].astype(str).str.upper() == "Y"]
completed = completed_habits_for_date(tracking, today)
completed_count = sum(
    habit in completed for habit in active_habits["HABIT_NAME"].tolist()
)
active_count = len(active_habits)
completion_rate = completed_count / active_count if active_count else 0

hour = local_now().hour
greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
display_name = str(getattr(st.user, "name", "")).strip() or email

st.title(f"{greeting}, {display_name.split()[0]}")
st.caption(f"{today:%A, %B} {today.day}, {today.year}")

metric_columns = st.columns(3)
metric_columns[0].metric(
    "Today's progress", f"{completed_count}/{active_count}", f"{completion_rate:.0%}"
)
metric_columns[1].metric("Active habits", active_count)
best_current_streak = max(
    (
        current_streak(tracking, habit, today)
        for habit in active_habits["HABIT_NAME"].tolist()
    ),
    default=0,
)
metric_columns[2].metric("Current best streak", f"{best_current_streak} days")

st.progress(completion_rate, text="Your daily progress")
st.subheader("Today's habits")

if active_habits.empty:
    st.info("Your routine starts with one small habit.")
    st.page_link(
        "app_pages/habits.py",
        label="Create your first habit",
        icon=":material/add_circle:",
    )
else:
    for habit in active_habits.itertuples(index=False):
        with st.container(border=True):
            habit_columns = st.columns([5, 1, 1], vertical_alignment="center")
            with habit_columns[0]:
                st.markdown(f"#### {habit.HABIT_NAME}")
                if pd.notna(habit.HABIT_DESCRIPTION) and habit.HABIT_DESCRIPTION:
                    st.caption(habit.HABIT_DESCRIPTION)
            with habit_columns[1]:
                st.caption(
                    f"{current_streak(tracking, habit.HABIT_NAME, today)}-day streak"
                )
            with habit_columns[2]:
                if str(habit.GOAL_TYPE).upper() == "NUMERIC":
                    amount_done, daily_goal = daily_progress(
                        tracking,
                        habit.HABIT_NAME,
                        today,
                        habit.DEFAULT_DAILY_GOAL,
                    )
                    if daily_goal is None:
                        st.caption("No target")
                    else:
                        ratio = min(amount_done / daily_goal, 1.0)
                        st.caption(
                            f"{amount_done:g}/{daily_goal:g} "
                            f"({ratio:.0%})"
                        )
                else:
                    st.markdown(
                        "**Done**" if habit.HABIT_NAME in completed else "Up next"
                    )

    st.page_link(
        "app_pages/check_in.py",
        label="Check in on your habits",
        icon=":material/check_circle:",
    )

st.subheader("A little progress adds up")
if tracking.empty:
    st.write("Your check-ins and streaks will show here as you build your routine.")
else:
    tracking_dates = pd.to_datetime(tracking["DATE"], errors="coerce")
    if tracking_dates.notna().any():
        recent_start = today - dt.timedelta(days=6)
        has_progress = (
            pd.to_numeric(tracking["COUNT_COMPLETED"], errors="coerce").fillna(0)
            > 0
        )
        recent_count = int(
            ((tracking_dates.dt.date >= recent_start) & has_progress).sum()
        )
        st.caption(
            f"You logged {recent_count} check-in"
            f"{'' if recent_count == 1 else 's'} in the last 7 days."
        )
