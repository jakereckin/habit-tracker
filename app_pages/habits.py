import pandas as pd
import streamlit as st

from py.auth import require_user
from py.habit_logic import WEEKDAYS, parse_scheduled_days
from py.habits import (
    create_habit,
    get_habits,
    set_habit_active,
    update_habit_cadence,
)


email = require_user()

st.title("Your habits")
st.caption("Create a routine that fits your day. You can pause habits any time.")

with st.container(border=True):
    st.subheader("Create a habit")
    goal_type = st.selectbox("Goal type", ["BINARY", "NUMERIC"])
    frequency_label = st.segmented_control(
        "Goal cadence",
        ["Daily", "Weekly", "Monthly"],
        default="Daily",
    )
    frequency = frequency_label.upper()
    with st.form("add_habit_form", clear_on_submit=True):
        habit_name = st.text_input("Habit name", max_chars=80)
        habit_description = st.text_area(
            "Why is this important to you?", max_chars=300
        )
        form_columns = st.columns(3)
        with form_columns[0]:
            start_date = st.date_input("Start date")
        with form_columns[1]:
            difficulty = st.select_slider(
                "Difficulty", options=[1, 2, 3, 4, 5], value=3
            )
        scheduled_day_names = []
        period_target = None
        if frequency == "WEEKLY":
            scheduled_day_names = st.multiselect(
                "Days to complete",
                WEEKDAYS,
                default=list(WEEKDAYS[:5]),
            )
            st.caption(
                "Selected weekdays are your weekly target. Weeks start Monday."
            )
        elif frequency == "MONTHLY":
            period_target = st.number_input(
                "Completions per month",
                min_value=1,
                max_value=31,
                value=1,
                step=1,
            )
            st.caption(
                "Complete the habit on any dates during the month."
            )
        if goal_type == "NUMERIC":
            daily_goal = st.number_input(
                "Target amount per check-in",
                min_value=0.01,
                value=1.0,
                step=1.0,
                format="%.2f",
                help="Set the amount to complete on each scheduled check-in.",
            )
        else:
            daily_goal = None
        submitted = st.form_submit_button(
            "Add habit", type="primary", icon=":material/add:"
        )

    if submitted:
        cleaned_name = habit_name.strip()
        habits = get_habits(email)
        existing_names = (
            habits["HABIT_NAME"].dropna().astype(str).str.casefold().tolist()
        )
        if not cleaned_name:
            st.error("Enter a name for your habit.")
        elif cleaned_name.casefold() in existing_names:
            st.error("A habit with that name already exists.")
        else:
            create_habit(
                email,
                cleaned_name,
                habit_description.strip(),
                start_date,
                goal_type,
                difficulty,
                daily_goal,
                frequency=frequency,
                scheduled_days=[
                    WEEKDAYS.index(day) for day in scheduled_day_names
                ],
                period_target=period_target,
            )
            st.success(f"{cleaned_name} added to your routine.")
            st.rerun()

habits = get_habits(email)
if habits.empty:
    st.info("Your habits will appear here after you add one.")
else:
    st.subheader("Manage habits")
    for index, habit in enumerate(habits.itertuples(index=False)):
        is_active = str(habit.ACTIVE).upper() == "Y"
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
            with columns[1]:
                frequency = str(habit.GOAL_FREQUENCY).upper()
                if frequency == "WEEKLY":
                    days = ", ".join(
                        WEEKDAYS[day]
                        for day in sorted(
                            parse_scheduled_days(habit.SCHEDULED_DAYS)
                        )
                    )
                    goal_summary = f"Weekly: {days}"
                elif frequency == "MONTHLY":
                    goal_summary = (
                        f"Monthly: {int(habit.PERIOD_TARGET)}x"
                    )
                else:
                    goal_summary = "Daily"
                st.caption(
                    f"{goal_summary} | {habit.GOAL_TYPE.title()} goal | "
                    f"Difficulty {habit.DIFFICULTY}/5"
                )
            with columns[2]:
                if st.button(
                    "Pause" if is_active else "Resume",
                    key=f"habit_active_{index}",
                ):
                    set_habit_active(email, habit.HABIT_NAME, not is_active)
                    st.rerun()

            with st.expander("Change cadence"):
                frequency_label = st.segmented_control(
                    "Goal cadence",
                    ["Daily", "Weekly", "Monthly"],
                    default=frequency.title(),
                    key=f"cadence_frequency_{index}",
                )
                with st.form(f"cadence_form_{index}"):
                    scheduled_day_names = []
                    period_target = None
                    if frequency_label == "Weekly":
                        existing_days = parse_scheduled_days(
                            habit.SCHEDULED_DAYS
                        )
                        scheduled_day_names = st.multiselect(
                            "Days to complete",
                            WEEKDAYS,
                            default=(
                                [WEEKDAYS[day] for day in sorted(existing_days)]
                                if existing_days
                                else list(WEEKDAYS[:5])
                            ),
                        )
                        st.caption(
                            "Selected weekdays define the weekly target. "
                            "Weeks start Monday."
                        )
                    elif frequency_label == "Monthly":
                        current_target = (
                            int(habit.PERIOD_TARGET)
                            if pd.notna(habit.PERIOD_TARGET)
                            else 1
                        )
                        period_target = st.number_input(
                            "Completions per month",
                            min_value=1,
                            max_value=31,
                            value=current_target,
                            step=1,
                        )
                    save_cadence = st.form_submit_button("Save cadence")

                if save_cadence:
                    update_habit_cadence(
                        email,
                        habit.HABIT_NAME,
                        str(frequency_label).upper(),
                        scheduled_days=[
                            WEEKDAYS.index(day)
                            for day in scheduled_day_names
                        ],
                        period_target=period_target,
                    )
                    st.success("Goal cadence updated.")
                    st.rerun()