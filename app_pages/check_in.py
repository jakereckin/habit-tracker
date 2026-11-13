import pandas as pd
import streamlit as st

from py.auth import require_user
from py.habit_logic import completed_habits_for_date, local_today
from py.habits import get_habits, get_tracking, set_habit_completion


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
    active_names = active_habits["HABIT_NAME"].tolist()
    completed_count = len(completed.intersection(active_names))
    st.progress(
        completed_count / len(active_habits),
        text=f"{completed_count} of {len(active_habits)} habits complete",
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
