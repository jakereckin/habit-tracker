import streamlit as st
import sys
import pandas as pd
pd.options.mode.chained_assignment = None
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


# ----------------------------------------------------------------------------
@st.cache_resource
def get_client():
    """
    Establishes a connection to the MongoDB server using credentials
    stored in Streamlit secrets.

    Returns:
        MongoClient: A MongoClient instance connected to the
                     specified MongoDB server.
    """
    pwd = st.secrets['mongo_habits']['MONGO_HABITS_PASSWORD']
    uri =  f"mongodb+srv://jake-habits-admin:{pwd}@habits.sn5lb.mongodb.net/"
    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))
    return client


# ----------------------------------------------------------------------------

if st.session_state.login_status:
    habit_name = st.text_input(label='Habit Name')
    habit_description = st.text_area(label='Habit Description')
    habit_start_date = st.date_input(label='Start Date')
    habit_active = st.radio(label='Active', options=['Y', 'N'])
    difficulty = st.number_input(
            label='Difficulty', min_value=1, max_value=5
    )
    add = st.button(label='Add Habit')
    if add:
        client = get_client()
        my_db = client['habit-tracker']
        habits_db = my_db['habit-list']
        habit_id = habit_name + '_' + str(object=habit_start_date)
        habit = {
                'Habit Name': habit_name,
                'Habit Description': habit_description,
                'Start Date': str(habit_start_date),
                'Active': habit_active,
                'Difficulty': difficulty,
                'Username': st.session_state.user_name,
                '_id': habit_id
        }
        habits_db.insert_one(document=habit)
        st.write('Habit Added')
else:
    st.write('Please login to add a habit')