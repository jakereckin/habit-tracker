import streamlit as st

from py.auth import require_user


st.set_page_config(
    page_title="Habit Tracker",
    page_icon=":material/check_circle:",
    layout="wide",
)

page = st.navigation(
    [
        st.Page(
            "app_pages/dashboard.py",
            title="Today",
            icon=":material/today:",
            default=True,
        ),
        st.Page(
            "app_pages/habits.py",
            title="Habits",
            icon=":material/checklist:",
        ),
        st.Page(
            "app_pages/check_in.py",
            title="Check-in",
            icon=":material/check_circle:",
        ),
        st.Page(
            "app_pages/progress.py",
            title="Progress",
            icon=":material/monitoring:",
        ),
    ],
    position="top" if st.user.is_logged_in else "hidden",
)
require_user()
page.run()
