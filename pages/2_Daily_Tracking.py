import streamlit as st
import sys
import pandas as pd
pd.options.mode.chained_assignment = None
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

st.cache_data.clear()

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
def get_my_db(client):
    my_db = client['habit-tracker']
    habits_db = my_db['habits']
    habit_tracker_db = my_db['habit-daily']
    habits = pd.DataFrame(data=list(habits_db.find())).drop(columns=['_id'])
    habit_tracking = (
        pd.DataFrame(data=list(habit_tracker_db.find())).drop(columns=['_id'])
    )
    return habits, habit_tracking


# ----------------------------------------------------------------------------
password = st.text_input(label='Password', type='password')
if password == st.secrets['page_password']['PAGE_PASSWORD']:
    client = get_client()
    habits, habit_tracking = get_my_db(client=client)
    todays_date = pd.to_datetime('today').strftime('%Y-%m-%d')
    done_today = habit_tracking[habit_tracking['Date'] == todays_date]
    merge_drop = pd.merge(
        left=habits, right=done_today, on='Habit Name', how='left'
    )
    merge_drop = merge_drop[merge_drop['Date'].isnull()]
    habit_options = merge_drop['Habit Name'].unique().tolist()
    habit_option = st.selectbox(label='Choose Habit', options=habit_options)
    completed = st.radio(label='Completed?', options=['Y', 'N'])
    save = st.button(label='Save')
    if save:
        habit_id = habit_option + '_' + str(object=todays_date)
        habit = {
            'Habit Name': habit_option,
            'Date': str(todays_date),
            'Completed': completed,
            '_id': habit_id
        }
        habits_db = client['habit-tracker']['habit-daily']
        habits_db.insert_one(document=habit)
        st.write('Habit Added')
        st.rerun()

