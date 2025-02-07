import streamlit as st
import pandas as pd
from datetime import timedelta
pd.options.mode.chained_assignment = None
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import numpy as np
import plotly.express as px

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
    habits = pd.DataFrame(data=list(habits_db.find()))
    habit_tracking = (
        pd.DataFrame(data=list(habit_tracker_db.find())).drop(columns=['_id'])
    )
    return habits, habit_tracking

# ----------------------------------------------------------------------------
def clean_habit_data(habits, habit_tracking):
    habit_tracking['Date'] = pd.to_datetime(habit_tracking['Date'])
    habits['Start Date'] = pd.to_datetime(habits['Start Date'])
    return habits, habit_tracking

# ----------------------------------------------------------------------------
def get_dates(habits):
    todays_date = pd.to_datetime('today')
    min_date = habits['Start Date'].min()
    delta = todays_date - min_date   # returns timedelta
    my_dates = []
    for i in range(delta.days + 1):
        day = min_date + timedelta(days=i)
        my_dates.append(day)
    return my_dates

# ----------------------------------------------------------------------------
def merge_dates_habits(habits, my_dates):
    unique_habits = habits['_id'].unique()
    dates_frame = pd.DataFrame(data=my_dates, columns=['Date'])
    dates_frame['Key'] = 1
    unique_habits_frame = pd.DataFrame(data=unique_habits, columns=['_id'])
    unique_habits_frame['Key'] = 1
    crossed = pd.merge(left=dates_frame, right=unique_habits_frame, on='Key')
    crossed = crossed.drop(columns=['Key'])
    return crossed

# ----------------------------------------------------------------------------
def clean_crossed(crossed, habits):
    all_habits = pd.merge(left=crossed, right=habits, how='inner', on=['_id'])
    all_habits = all_habits[all_habits['Start Date'] <= all_habits['Date']]
    all_habits = all_habits.drop(
        columns=['Start Date', '_id', 'Habit Description']
    )
    return all_habits
    
# ----------------------------------------------------------------------------
def join_tracking(all_habits, habit_tracking):
    all_habit_tracked = pd.merge(
        left=all_habits, right=habit_tracking, how='left', 
        on=['Habit Name', 'Date']
    )
    all_habit_tracked['Completed'] = (
        all_habit_tracked['Completed'].fillna(value='N')
    )
    all_habit_tracked['Day of Week'] = all_habit_tracked['Date'].dt.day_name()
    all_habit_tracked['Week Start Date'] = (
        all_habit_tracked['Date'] 
        - pd.to_timedelta(arg=all_habit_tracked['Date'].dt.dayofweek, 
                          unit='D')
    )
    all_habit_tracked['Completed_Flag'] = np.where(
        all_habit_tracked['Completed'] == 'Y', 1, 0
    )
    all_habit_tracked['Habit_Count'] = 1
    return all_habit_tracked

get_client()
habits, habit_tracking = get_my_db(client=get_client())
habits, habit_tracking = clean_habit_data(
    habits=habits, habit_tracking=habit_tracking
)
my_dates = get_dates(habits=habits)
crossed = merge_dates_habits(habits=habits, my_dates=my_dates)
all_habits = clean_crossed(crossed=crossed, habits=habits)
all_habit_tracked = join_tracking(
    all_habits=all_habits, habit_tracking=habit_tracking
)

my_button = st.radio(
    label='Date Level', options=['Day', 'Week', 'Day of Week', 'Habit'],
    horizontal=True
)

if my_button == 'Day':
    day_habits = (
        all_habit_tracked.groupby(by=['Date'], as_index=False)
                         .agg(Completed_Count=('Completed_Flag', 'sum'),
                              Habit_Count=('Habit_Count', 'sum'))
    )
    day_habits['Completion_Rate'] = (
        day_habits['Completed_Count'] / day_habits['Habit_Count']
    )
    day_habits = day_habits.sort_values(by='Date')
    day_habits['Date'] = (
        day_habits['Date'].dt.strftime(date_format='%m/%d/%Y')
    )
    fig = px.line(
        data_frame=day_habits, 
        x='Date', 
        y='Completion_Rate', 
        text=(day_habits['Completion_Rate']*100).apply(func=lambda x: '{0:1.1f}%'.format(x)),
        labels={'Completion_Rate': '% Habits Completed'}
    )
    #fig.update_traces(textposition='outside')
    fig.layout.yaxis.tickformat = ',.1%'
    fig.update_layout(xaxis=dict(type='category'), hovermode=False)
    st.plotly_chart(figure_or_data=fig, use_container_width=True)

if my_button == 'Week':
    week_habits = (
        all_habit_tracked.groupby(by=['Week Start Date'], as_index=False)
                         .agg(Completed_Count=('Completed_Flag', 'sum'),
                              Habit_Count=('Habit_Count', 'sum'))
    )
    week_habits['Completion_Rate'] = (
        week_habits['Completed_Count'] / week_habits['Habit_Count']
    )
    week_habits = week_habits.sort_values(by='Week Start Date')
    week_habits['Week Start Date'] = (
        week_habits['Week Start Date'].dt.strftime(date_format='%m/%d/%Y')
    )
    fig = px.bar(
        data_frame=week_habits, 
        x='Week Start Date', 
        y='Completion_Rate', 
        text=(week_habits['Completion_Rate']*100).apply(func=lambda x: '{0:1.1f}%'.format(x)),
        labels={'Completion_Rate': '% Habits Completed'}
    )
    fig.update_traces(textposition='outside')
    fig.layout.yaxis.tickformat = ',.1%'
    fig.update_layout(xaxis=dict(type='category'), hovermode=False)
    st.plotly_chart(figure_or_data=fig, use_container_width=True)


if my_button == 'Day of Week':
    dow_habits = (
        all_habit_tracked.groupby(by=['Day of Week'], as_index=False)
                         .agg(Completed_Count=('Completed_Flag', 'sum'),
                              Habit_Count=('Habit_Count', 'sum'))
    )
    dow_habits['Completion_Rate'] = (
        dow_habits['Completed_Count'] / dow_habits['Habit_Count']
    )
    fig = px.bar(
        data_frame=dow_habits, 
        y='Day of Week', 
        x='Completion_Rate', 
        text=(dow_habits['Completion_Rate']*100).apply(func=lambda x: '{0:1.1f}%'.format(x)),
        orientation='h',
        labels={'Completion_Rate': '% Habits Completed'}
    )
    fig.update_traces(textposition='outside')
    fig.layout.xaxis.tickformat = ',.1%'
    fig.update_layout(hovermode=False)
    st.plotly_chart(figure_or_data=fig, use_container_width=True)

if my_button == 'Habit':
    hab_habits = (
        all_habit_tracked.groupby(by=['Habit Name'], as_index=False)
                         .agg(Completed_Count=('Completed_Flag', 'sum'),
                              Habit_Count=('Habit_Count', 'sum'))
    )
    hab_habits['Completion_Rate'] = (
        hab_habits['Completed_Count'] / hab_habits['Habit_Count']
    )
    fig = px.bar(
        data_frame=hab_habits, 
        y='Habit Name', 
        x='Completion_Rate', 
        text=(hab_habits['Completion_Rate']*100).apply(func=lambda x: '{0:1.1f}%'.format(x)),
        orientation='h',
        labels={'Completion_Rate': '% Habits Completed'}
    )
    fig.update_traces(textposition='outside')
    fig.layout.xaxis.tickformat = ',.1%'
    fig.update_layout(hovermode=False)
    st.plotly_chart(figure_or_data=fig, use_container_width=True)