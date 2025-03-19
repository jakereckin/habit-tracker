import streamlit as st
import pandas as pd
import time
import datetime as dt
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
    habits_db = my_db['habit-list']
    habit_tracker_db = my_db['habit-daily-tracking']
    habits = pd.DataFrame(data=list(habits_db.find())).drop(columns=['_id'])
    habit_tracking = (
        pd.DataFrame(data=list(habit_tracker_db.find())).drop(columns=['_id'])
    )
    habits = habits[habits['Username'] == st.session_state.user_name]
    habit_tracking = habit_tracking[habit_tracking['Username'] == st.session_state.user_name]
    return habits, habit_tracking


# ----------------------------------------------------------------------------
if st.session_state.login_status:
    client = get_client()
    habits, habit_tracking = get_my_db(client=client)
    todays_data = pd.merge(
        left=habits, right=habit_tracking, on='Habit Name', how='left'
    )
    todays_data['DATE_ONLY'] = pd.to_datetime(todays_data['Date']).dt.date
    #st.write('Last Habit Added:', habit_tracking['Date'].max())
    date = dt.datetime.now(dt.timezone.utc)
    todays_date = pd.to_datetime(date, utc=True)
    date_df = pd.DataFrame(data=[todays_date], columns=['Date'])
    date_df['Date'] = date_df['Date'].dt.tz_convert('US/Central')

    date_col, time_col =  st.columns(spec=2)
    with date_col:
        date = st.date_input(
            label='Date', value=date_df['Date'].dt.date.values[0]
        )
    with time_col:
        time_now = st.time_input(label='Time')
    
    my_points = todays_data[todays_data['DATE_ONLY'] == date]
    my_points = my_points.Difficulty.sum()
    st.write('Current Daily Points:', my_points)
    my_date = (
        date.strftime('%Y-%m-%d') + ' ' + time_now.strftime(format='%H:%M')
    )
    habit_options = habits['Habit Name'].unique().tolist()
    habit_option = st.selectbox(label='Choose Habit', options=habit_options)
    completed = st.radio(label='Completed?', options=['Y', 'N'])
    save = st.button(label='Save')
    if save:
        habit_id = habit_option + '_' + str(object=my_date)
        st.write(habit_id)
        habit = {
                'Habit Name': habit_option,
                'Date': str(my_date),
                'Completed': completed,
                'Username': st.session_state.user_name,
                '_id': habit_id
        }
        habits_db = client['habit-tracker']['habit-daily-tracking']
        habits_db.insert_one(document=habit)
        st.write('Habit Added')
        time.sleep(1)
        st.rerun()
else:
    st.write('Please login to track habits')
