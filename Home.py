import os
import sys

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

import streamlit as st

from py.auth import require_user


st.set_page_config(
    page_title="Habit Tracker",
    page_icon=":material/check_circle:",
    layout="wide",
)

user = getattr(st, "user", None)
is_logged_in = bool(getattr(user, "is_logged_in", False)) if user is not None else False

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
    position="top" if is_logged_in else "hidden",
)
require_user()
page.run()
