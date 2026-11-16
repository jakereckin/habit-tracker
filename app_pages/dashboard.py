import datetime as dt

import pandas as pd
import streamlit as st

from py.auth import require_user
from py.daily_suggestions import (
    DailySuggestionError,
    generate_daily_suggestions,
)
from py.habit_logic import (
    completed_habits_for_date,
    current_streak,
    daily_progress,
    habit_period_progress,
    is_habit_due,
    local_now,
    local_today,
    skipped_dates_for_habit,
    skipped_habits_for_date,
)
from py.habits import get_habits, get_skip_days, get_tracking


email = require_user()

today = local_today()
habits = get_habits(email)
tracking = get_tracking(email)
skip_days = get_skip_days(email)
active_habits = habits[habits["ACTIVE"].astype(str).str.upper() == "Y"]
skipped_today = skipped_habits_for_date(skip_days, today)
completed = completed_habits_for_date(tracking, today, skipped_today)
due_habits = [
    habit
    for habit in active_habits.itertuples(index=False)
    if str(habit.GOAL_FREQUENCY).upper() != "MONTHLY"
    and is_habit_due(
        str(habit.GOAL_FREQUENCY),
        habit.SCHEDULED_DAYS,
        today,
    )
    and habit.HABIT_NAME not in skipped_today
]
completed_count = sum(
    habit.HABIT_NAME in completed for habit in due_habits
)
due_count = len(due_habits)
completion_rate = completed_count / due_count if due_count else 0

hour = local_now().hour
greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
display_name = str(getattr(st.user, "name", "")).strip() or email

st.title(f"{greeting}, {display_name.split()[0]}")
st.caption(f"{today:%A, %B} {today.day}, {today.year}")

metric_columns = st.columns(3)
metric_columns[0].metric(
    "Today's due goals",
    f"{completed_count}/{due_count}",
    f"{completion_rate:.0%}",
)
metric_columns[1].metric("Active habits", len(active_habits))
daily_habit_names = active_habits.loc[
    active_habits["GOAL_FREQUENCY"].astype(str).str.upper() == "DAILY",
    "HABIT_NAME",
].tolist()
best_current_streak = max(
    (
        current_streak(
            tracking,
            habit,
            today,
            skipped_dates_for_habit(skip_days, habit),
        )
        for habit in daily_habit_names
    ),
    default=0,
)
metric_columns[2].metric("Best daily streak", f"{best_current_streak} days")

st.progress(
    completion_rate,
    text=(
        "Today's scheduled goal progress"
        if due_count
        else "No daily or weekly habits are due today"
    ),
)

st.subheader("Ideas for today")
gemini_config = st.secrets.get("gemini", {})
gemini_api_key = gemini_config.get("api_key")
if not gemini_api_key:
    st.caption(
        "Add a Gemini API key to your app secrets to get personalized suggestions."
    )
elif active_habits.empty:
    st.caption("Add a habit to get suggestions for your day.")
else:
    suggestion_context = []
    for habit in active_habits.itertuples(index=False):
        habit_name = str(habit.HABIT_NAME)
        item = {
            "habit": habit_name,
            "status": (
                "skipped"
                if habit_name in skipped_today
                else "complete"
                if habit_name in completed
                else "not complete"
            ),
            "cadence": str(habit.GOAL_FREQUENCY).lower(),
        }
        done_count, target_count, period_label = habit_period_progress(
            tracking,
            habit_name,
            today,
            str(habit.GOAL_FREQUENCY),
            habit.SCHEDULED_DAYS,
            habit.PERIOD_TARGET,
            skipped_dates_for_habit(skip_days, habit_name),
        )
        item["period_progress"] = (
            f"{done_count} of {target_count} {period_label}"
        )
        if (
            str(habit.GOAL_FREQUENCY).upper() == "WEEKLY"
            and not is_habit_due(
                str(habit.GOAL_FREQUENCY),
                habit.SCHEDULED_DAYS,
                today,
            )
        ):
            item["status"] = "not scheduled today"
        description = (
            ""
            if pd.isna(habit.HABIT_DESCRIPTION)
            else str(habit.HABIT_DESCRIPTION).strip()
        )
        if description:
            item["description"] = description

        if str(habit.GOAL_TYPE).upper() == "NUMERIC":
            amount_done, daily_goal = daily_progress(
                tracking,
                habit_name,
                today,
                habit.DEFAULT_DAILY_GOAL,
            )
            item["progress"] = (
                f"{amount_done:g} of {daily_goal:g}"
                if daily_goal is not None
                else f"{amount_done:g} logged; no target set"
            )
        suggestion_context.append(item)

    if st.button("Suggest a focus for today", key="today_suggestions"):
        with st.spinner("Thinking of a few practical ideas..."):
            try:
                suggestions = generate_daily_suggestions(
                    gemini_api_key,
                    suggestion_context,
                )
            except DailySuggestionError as exc:
                st.error(str(exc))
            else:
                st.session_state["today_suggestions"] = suggestions
                st.session_state["today_suggestions_date"] = today.isoformat()

    if st.session_state.get("today_suggestions_date") == today.isoformat():
        suggestions = st.session_state.get("today_suggestions")
        if suggestions:
            st.markdown(suggestions)

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
        habit_name = str(habit.HABIT_NAME)
        frequency = str(habit.GOAL_FREQUENCY).upper()
        skipped_dates = skipped_dates_for_habit(skip_days, habit_name)
        is_skipped = habit_name in skipped_today
        is_due = frequency != "MONTHLY" and is_habit_due(
            frequency,
            habit.SCHEDULED_DAYS,
            today,
        )
        done_count, target_count, period_label = habit_period_progress(
            tracking,
            habit_name,
            today,
            frequency,
            habit.SCHEDULED_DAYS,
            habit.PERIOD_TARGET,
            skipped_dates,
        )
        with st.container(border=True):
            habit_columns = st.columns([5, 1, 1], vertical_alignment="center")
            with habit_columns[0]:
                st.markdown(f"#### {habit.HABIT_NAME}")
                if pd.notna(habit.HABIT_DESCRIPTION) and habit.HABIT_DESCRIPTION:
                    st.caption(habit.HABIT_DESCRIPTION)
            with habit_columns[1]:
                if frequency == "DAILY":
                    st.caption(
                        f"{current_streak(tracking, habit_name, today, skipped_dates)}-day streak"
                    )
                else:
                    st.caption(
                        f"{done_count}/{target_count} {period_label}"
                    )
            with habit_columns[2]:
                if is_skipped:
                    st.markdown("**Skipped**")
                elif frequency == "WEEKLY" and not is_due:
                    st.caption("Not scheduled")
                elif str(habit.GOAL_TYPE).upper() == "NUMERIC":
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
                        "**Done**" if habit_name in completed else "Up next"
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
        recent_count = sum(
            len(
                completed_habits_for_date(
                    tracking,
                    (today - dt.timedelta(days=offset)),
                    skipped_habits_for_date(
                        skip_days,
                        today - dt.timedelta(days=offset),
                    ),
                )
            )
            for offset in range(7)
        )
        st.caption(
            f"You logged {recent_count} check-in"
            f"{'' if recent_count == 1 else 's'} in the last 7 days."
        )
