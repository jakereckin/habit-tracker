import pandas as pd
import streamlit as st

from py.auth import require_user
from py.habits import create_habit, get_habits, set_habit_active


email = require_user()

st.title("Your habits")
st.caption("Create a routine that fits your day. You can pause habits any time.")

with st.container(border=True):
    st.subheader("Create a habit")
    goal_type = st.selectbox("Goal type", ["BINARY", "NUMERIC"])
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
        if goal_type == "NUMERIC":
            daily_goal = st.number_input(
                "Daily goal",
                min_value=0.01,
                value=1.0,
                step=1.0,
                format="%.2f",
                help="Set the amount you want to complete each day.",
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
                st.caption(
                    f"{habit.GOAL_TYPE.title()} goal | "
                    f"Difficulty {habit.DIFFICULTY}/5"
                )
            with columns[2]:
                if st.button(
                    "Pause" if is_active else "Resume",
                    key=f"habit_active_{index}",
                ):
                    set_habit_active(email, habit.HABIT_NAME, not is_active)
                    st.rerun()