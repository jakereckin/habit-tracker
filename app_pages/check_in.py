import pandas as pd
import streamlit as st

from py.auth import require_user
from py.habit_logic import completed_habits_for_date, daily_progress, local_today
from py.habits import (
    add_numeric_progress,
    get_habits,
    get_tracking,
    save_daily_goal,
    set_habit_completion,
)


email = require_user()

st.title("Daily check-in")
st.caption("Small, steady actions make a routine.")
today = local_today()
target_date = st.date_input(
    "Check-in date",
    value=today,
    max_value=today,
)

habits = get_habits(email)
active_habits = habits[habits["ACTIVE"].astype(str).str.upper() == "Y"]
tracking = get_tracking(email)
completed = completed_habits_for_date(tracking, target_date)

if active_habits.empty:
    st.info("Add a habit first, then come back here to check in.")
    st.page_link(
        "app_pages/habits.py",
        label="Add a habit",
        icon=":material/add_circle:",
    )
else:
    progress_units = 0.0
    for habit in active_habits.itertuples(index=False):
        if str(habit.GOAL_TYPE).upper() == "NUMERIC":
            amount_done, daily_goal = daily_progress(
                tracking,
                habit.HABIT_NAME,
                target_date,
                habit.DEFAULT_DAILY_GOAL,
            )
            if daily_goal is not None and daily_goal > 0:
                progress_units += min(amount_done / daily_goal, 1.0)
        elif habit.HABIT_NAME in completed:
            progress_units += 1
    st.progress(
        progress_units / len(active_habits),
        text=(
            f"{progress_units:g} of {len(active_habits)} daily goals "
            "complete (numeric progress included)"
        ),
    )
    for index, habit in enumerate(active_habits.itertuples(index=False)):
        is_complete = habit.HABIT_NAME in completed
        with st.container(border=True):
            columns = st.columns([5, 2, 1], vertical_alignment="center")
            with columns[0]:
                st.markdown(f"#### {habit.HABIT_NAME}")
                description = (
                    ""
                    if pd.isna(habit.HABIT_DESCRIPTION)
                    else str(habit.HABIT_DESCRIPTION).strip()
                )
                if description:
                    st.caption(description)
            if str(habit.GOAL_TYPE).upper() == "NUMERIC":
                amount_done, saved_goal = daily_progress(
                    tracking,
                    habit.HABIT_NAME,
                    target_date,
                    habit.DEFAULT_DAILY_GOAL,
                )
                with columns[1]:
                    if saved_goal is None:
                        st.caption("Set a target for today")
                    else:
                        ratio = min(amount_done / saved_goal, 1.0)
                        st.progress(
                            ratio,
                            text=(
                                f"{amount_done:g}/{saved_goal:g} done "
                                f"({ratio:.0%})"
                            ),
                        )

                with st.form(f"numeric_checkin_{index}_{target_date}"):
                    goal_column, amount_column = st.columns(2)
                    with goal_column:
                        daily_goal = st.number_input(
                            "Today's target",
                            min_value=0.01,
                            value=float(saved_goal or 1.0),
                            step=1.0,
                            format="%.2f",
                            key=f"numeric_goal_{index}_{target_date}",
                        )
                    with amount_column:
                        amount = st.number_input(
                            "Add progress",
                            min_value=0.01,
                            value=1.0,
                            step=1.0,
                            format="%.2f",
                            key=f"numeric_amount_{index}_{target_date}",
                        )
                    save_goal = st.form_submit_button("Save target")
                    add_amount = st.form_submit_button(
                        "Add amount", type="primary"
                    )

                if save_goal:
                    save_daily_goal(
                        email, habit.HABIT_NAME, target_date, daily_goal
                    )
                    st.rerun()
                if add_amount:
                    add_numeric_progress(
                        email,
                        habit.HABIT_NAME,
                        target_date,
                        amount,
                        daily_goal,
                    )
                    st.rerun()
            else:
                with columns[1]:
                    st.caption("Completed" if is_complete else "One step at a time")
                with columns[2]:
                    if st.button(
                        "Undo" if is_complete else "Complete",
                        key=f"checkin_{index}",
                        type="secondary" if is_complete else "primary",
                        icon=(
                            ":material/check:"
                            if is_complete
                            else ":material/add_task:"
                        ),
                    ):
                        set_habit_completion(
                            email, habit.HABIT_NAME, target_date, not is_complete
                        )
                        st.rerun()
