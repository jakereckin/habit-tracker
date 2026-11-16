import datetime as dt

import pandas as pd
import streamlit as st

from py.auth import require_user
from py.habit_logic import (
    WEEKDAYS,
    completed_habits_for_date,
    daily_progress,
    habit_period_progress,
    is_habit_due,
    local_today,
    skipped_dates_for_habit,
    skipped_habits_for_date,
)
from py.habits import (
    add_numeric_progress,
    get_habits,
    get_skip_days,
    get_tracking,
    save_daily_goal,
    set_habit_completion,
    set_habit_skipped,
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
skip_days = get_skip_days(email)

if active_habits.empty:
    st.info("Add a habit first, then come back here to check in.")
    st.page_link(
        "app_pages/habits.py",
        label="Add a habit",
        icon=":material/add_circle:",
    )
else:
    skippable_habits = active_habits[
        active_habits["GOAL_FREQUENCY"].astype(str).str.upper().isin(
            ["DAILY", "WEEKLY"]
        )
    ]
    if not skippable_habits.empty:
        st.subheader("Plan or undo a skipped day")
        skip_names = skippable_habits["HABIT_NAME"].astype(str).tolist()
        skip_columns = st.columns([2, 2, 1], vertical_alignment="bottom")
        with skip_columns[0]:
            skip_habit_name = st.selectbox(
                "Habit",
                skip_names,
                key="skip_habit_name",
            )
        with skip_columns[1]:
            skip_date = st.date_input(
                "Date",
                value=today,
                min_value=today - dt.timedelta(days=365),
                max_value=today + dt.timedelta(days=365),
                key="skip_habit_date",
            )

        selected_habit = skippable_habits.loc[
            skippable_habits["HABIT_NAME"] == skip_habit_name
        ].iloc[0]
        selected_frequency = str(selected_habit.GOAL_FREQUENCY).upper()
        is_scheduled_date = is_habit_due(
            selected_frequency,
            selected_habit.SCHEDULED_DAYS,
            skip_date,
        )
        already_skipped = skip_date in skipped_dates_for_habit(
            skip_days, skip_habit_name
        )
        already_completed = skip_habit_name in completed_habits_for_date(
            tracking, skip_date
        )
        can_change_skip = (
            is_scheduled_date and (already_skipped or not already_completed)
        )
        with skip_columns[2]:
            if st.button(
                "Undo skip" if already_skipped else "Skip this day",
                disabled=not can_change_skip,
                key="toggle_habit_skip",
            ):
                set_habit_skipped(
                    email,
                    skip_habit_name,
                    skip_date,
                    skipped=not already_skipped,
                )
                st.rerun()

        if not is_scheduled_date:
            st.caption("This habit is not scheduled for that weekday.")
        elif already_completed and not already_skipped:
            st.caption(
                "This habit is already complete for that date. Undo the "
                "check-in before marking it skipped."
            )

        parsed_skip_dates = pd.to_datetime(skip_days["DATE"], errors="coerce")
        upcoming_skips = skip_days.loc[
            (parsed_skip_dates.dt.date >= today)
            & (skip_days["HABIT_NAME"].isin(skip_names))
        ]
        if not upcoming_skips.empty:
            skip_summary = [
                f"{row.HABIT_NAME}: "
                f"{pd.to_datetime(row.DATE).date():%a, %b} "
                f"{pd.to_datetime(row.DATE).day}"
                for row in upcoming_skips.itertuples(index=False)
            ]
            st.caption("Planned skips — " + "; ".join(skip_summary))

    completed = completed_habits_for_date(
        tracking,
        target_date,
        skipped_habits_for_date(skip_days, target_date),
    )
    due_habits = [
        habit
        for habit in active_habits.itertuples(index=False)
        if str(habit.GOAL_FREQUENCY).upper() != "MONTHLY"
        and is_habit_due(
            str(habit.GOAL_FREQUENCY),
            habit.SCHEDULED_DAYS,
            target_date,
        )
        and habit.HABIT_NAME
        not in skipped_habits_for_date(skip_days, target_date)
    ]
    progress_units = 0.0
    for habit in due_habits:
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
    due_count = len(due_habits)
    st.progress(
        progress_units / due_count if due_count else 0.0,
        text=(
            f"{progress_units:g} of {due_count} scheduled goals complete"
            if due_count
            else "No daily or weekly goals are due on this date"
        ),
    )

    for index, habit in enumerate(active_habits.itertuples(index=False)):
        habit_name = str(habit.HABIT_NAME)
        frequency = str(habit.GOAL_FREQUENCY).upper()
        skipped_dates = skipped_dates_for_habit(skip_days, habit_name)
        is_skipped = target_date in skipped_dates
        is_due = is_habit_due(
            frequency,
            habit.SCHEDULED_DAYS,
            target_date,
        )
        is_complete = habit_name in completed
        completed_count, target_count, period_label = habit_period_progress(
            tracking,
            habit_name,
            target_date,
            frequency,
            habit.SCHEDULED_DAYS,
            habit.PERIOD_TARGET,
            skipped_dates,
        )

        with st.container(border=True):
            columns = st.columns([5, 2], vertical_alignment="center")
            with columns[0]:
                st.markdown(f"#### {habit.HABIT_NAME}")
                description = (
                    ""
                    if pd.isna(habit.HABIT_DESCRIPTION)
                    else str(habit.HABIT_DESCRIPTION).strip()
                )
                if description:
                    st.caption(description)
            with columns[1]:
                if is_skipped:
                    st.caption("Skipped")
                elif frequency == "MONTHLY":
                    ratio = min(completed_count / target_count, 1.0)
                    st.progress(
                        ratio,
                        text=(
                            f"{completed_count}/{target_count} "
                            f"{period_label}"
                        ),
                    )
                elif frequency == "WEEKLY":
                    st.caption(
                        f"{completed_count}/{target_count} {period_label}"
                    )
                    if not is_due:
                        st.caption("Not scheduled today")

            if is_skipped:
                continue
            if frequency != "MONTHLY" and not is_due:
                continue

            if str(habit.GOAL_TYPE).upper() == "NUMERIC":
                amount_done, saved_goal = daily_progress(
                    tracking,
                    habit.HABIT_NAME,
                    target_date,
                    habit.DEFAULT_DAILY_GOAL,
                )
                if frequency != "MONTHLY":
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
                elif saved_goal is not None:
                    ratio = min(amount_done / saved_goal, 1.0)
                    st.progress(
                        ratio,
                        text=(
                            f"Today's check-in: {amount_done:g}/"
                            f"{saved_goal:g} ({ratio:.0%})"
                        ),
                    )

                with st.form(f"numeric_checkin_{index}_{target_date}"):
                    goal_column, amount_column = st.columns(2)
                    with goal_column:
                        daily_goal = st.number_input(
                            "Target for this check-in",
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
                    st.caption(
                        "Completed"
                        if is_complete
                        else "Ready for today's check-in"
                    )
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
                        email,
                        habit.HABIT_NAME,
                        target_date,
                        not is_complete,
                    )
                    st.rerun()
