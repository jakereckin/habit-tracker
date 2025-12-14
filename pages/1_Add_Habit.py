import streamlit as st
import pandas as pd
import time
import sqlitecloud
pd.options.mode.chained_assignment = None
from py import sql, data_source

def get_habits():
    habits = data_source.run_query(
        sql=sql.get_habits(),
        connection=st.secrets['habits_connection']['DB_CONNECTION']
    )
    return habits


# ----------------------------------------------------------------------------
if 'login_status' not in st.session_state:
    st.session_state.login_status = False
    
if st.session_state.login_status:
    habits_db = get_habits()
    current_habits = habits_db[
        habits_db['EMAIL'] == st.session_state.email
    ]
    st.dataframe(data=current_habits)
    goal_types = ['NUMERIC', 'BINARY']
    with st.form(key='add_habit_form', clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            habit_name = st.text_input(label='Habit Name')
            habit_active = st.radio(label='Active', options=['Y', 'N'])
        with col2:
            habit_description = st.text_area(label='Habit Description')
            habit_start_date = st.date_input(label='Start Date')
        with col3:
            goal_type = st.radio(label='Goal Type', options=goal_types)
            difficulty = st.number_input(
                    label='Difficulty', min_value=1, max_value=5
            )
        add = st.form_submit_button(label='Add Habit', key='add_habit')
        if add:
            time.sleep(1) 
            with sqlitecloud.connect(
                st.secrets['habits_connection']['DB_CONNECTION']
            ) as conn:
                conn.execute(
                    sql=sql.insert_habits(),
                    parameters=(
                        st.session_state.email,
                        habit_name,
                        habit_description,
                        habit_start_date,
                        habit_active,
                        goal_type,
                        difficulty
                    )
                )
                conn.commit()
                
            st.write('Habit Added')
            st.rerun()
else:
    st.write('Please login to add a habit')
    login_page = st.button(label='Login')
    if login_page:
        st.switch_page('Home.py')