import datetime as dt

import sqlitecloud
import streamlit as st

from py import data_source, sql
from py.habit_logic import local_now


def get_db_connection() -> str:
    connection = st.secrets.get("habits_connection", {}).get("DB_CONNECTION")
    if not connection:
        st.error(
            "The database is not configured. Add "
            "[habits_connection].DB_CONNECTION to .streamlit/secrets.toml."
        )
        st.stop()
    return connection


def ensure_user(email: str) -> None:
    connection = get_db_connection()
    with sqlitecloud.connect(connection) as conn:
        conn.execute(sql.ensure_user(), (email, email))
        conn.execute(sql.clear_legacy_password(), (email,))
        conn.commit()


def get_habits(email: str):
    return data_source.run_query(
        sql=sql.get_habits(),
        connection=get_db_connection(),
        params=[email],
    )


def get_tracking(email: str):
    return data_source.run_query(
        sql=sql.get_tracking(),
        connection=get_db_connection(),
        params=[email],
    )


def create_habit(
    email: str,
    name: str,
    description: str,
    start_date: dt.date,
    goal_type: str,
    difficulty: int,
) -> None:
    with sqlitecloud.connect(get_db_connection()) as conn:
        conn.execute(
            sql=sql.insert_habits(),
            parameters=(
                email,
                name,
                description,
                start_date.strftime("%m/%d/%Y"),
                "Y",
                goal_type,
                difficulty,
            ),
        )
        conn.commit()


def set_habit_active(email: str, habit_name: str, active: bool) -> None:
    with sqlitecloud.connect(get_db_connection()) as conn:
        conn.execute(
            sql=sql.set_habit_active(),
            parameters=("Y" if active else "N", email, habit_name),
        )
        conn.commit()


def set_habit_completion(
    email: str, habit_name: str, target_date: dt.date, completed: bool
) -> None:
    connection = get_db_connection()
    date_value = target_date.strftime("%m/%d/%Y")
    with sqlitecloud.connect(connection) as conn:
        if completed:
            now = local_now().strftime("%H:%M")
            conn.execute(
                sql=sql.add_daily_habits(),
                parameters=(
                    email,
                    habit_name,
                    date_value,
                    now,
                    1,
                    email,
                    habit_name,
                    date_value,
                ),
            )
        else:
            conn.execute(
                sql=sql.remove_daily_habit(),
                parameters=(email, habit_name, date_value),
            )
        conn.commit()
