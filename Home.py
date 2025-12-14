import streamlit as st
import sqlitecloud
from py import sql, data_source
import pandas as pd


# ----------------------------------------------------------------------------
def get_data():
    users = data_source.run_query(
        sql=sql.select_users(),
        connection=st.secrets['habits_connection']['DB_CONNECTION']
    )
    return users


st.header(body='Habit Tracker', divider='blue')
if 'login_status' not in st.session_state:
    st.session_state.login_status = False

if st.session_state.login_status:
    st.write('Welcome', st.session_state.user_name)
    logout = st.button(label='Logout')
    if logout:
        st.session_state.login_status = False
else:
    email = st.text_input(label='Email')
    password = st.text_input(label='Password', type='password')
    login = st.button(label='Login')
    signup = st.button(label='Sign Up')
    if login:
        users = get_data()
        this_user = users[
            (users['EMAIL'] == email) 
            & (users['PASSWORD'] == password)
        ]
        if this_user.shape[0] > 0:
            del password
            del login
            del signup
            st.write('Login Successful')
            st.session_state.login_status = True
            st.session_state.email = email
            del email
        else:
            st.write('Login Failed')

    elif signup:
        users = get_data()
        this_user = users[(users['EMAIL'] == email)]
        if this_user.shape[0] > 0:
            st.write('User already exists')
        else:
            with sqlitecloud.connect(
                st.secrets['habits_connection']['DB_CONNECTION']
            ) as conn:
                conn.execute(
                    sql=sql.insert_user_sql(),
                    parameters=(email, password)
                )
                conn.commit()
            st.write('User Added')
            st.session_state.login_status = True
            st.session_state.user_name = email