import streamlit as st
import pandas as pd
import time
import datetime as dt
import sqlitecloud
pd.options.mode.chained_assignment = None
from py import sql, data_source

st.cache_data.clear()



# ----------------------------------------------------------------------------
def get_habits():
    habits_tracking = data_source.run_query(
        sql=sql.get_current_day(),
        connection=st.secrets['habits_connection']['DB_CONNECTION']
    )
    habits = data_source.run_query(
        sql=sql.get_habits(),
        connection=st.secrets['habits_connection']['DB_CONNECTION']
    )
    return habits, habits_tracking


# ----------------------------------------------------------------------------
if 'login_status' not in st.session_state:
    st.session_state.login_status = False
if st.session_state.login_status:
    st.header(
        body=f'Add Daily Habit for {st.session_state.email}',
        divider='blue'
    )
    habits, habit_tracking = get_habits()
    todays_data = pd.merge(
        left=habits, right=habit_tracking, on='HABIT_NAME', how='left'
    )
    todays_data['DATE_ONLY'] = pd.to_datetime(todays_data['DATE']).dt.date
    #st.write('Last Habit Added:', habit_tracking['Date'].max())
    date = dt.datetime.now(dt.timezone.utc)
    todays_date = pd.to_datetime(date, utc=True)
    date_df = pd.DataFrame(data=[todays_date], columns=['DATE'])
    date_df['Date'] = date_df['DATE'].dt.tz_convert('US/Central')
    start_time = dt.time(0, 0)
    end_time = dt.time(23, 59)
    with st.form(key='daily_habit_form', clear_on_submit=False):
        date_col, time_col =  st.columns(spec=2)
        with date_col:
            date = st.date_input(
                label='Date', value=date_df['DATE'].dt.date.values[0]
            )
        with time_col:
            time_now =  st.slider(
                label="Select Time",
                value=(dt.time(12, 0)),
                min_value=start_time,
                max_value=end_time,
                format="HH:mm"
        )
        
        today_df = todays_data[todays_data['DATE_ONLY'] == date]
        today_df['DATE'] = pd.to_datetime(
            today_df['DATE'], errors='coerce'
        )
        today_df['TIME'] = today_df['DATE'].dt.time
        today_df = today_df.sort_values(by='DATE').reset_index(drop=True)
        need_df = today_df[['HABIT_NAME', 'TIME']]
        my_points = today_df.DIFFICULTY.sum()
        st.write('Current Daily Points:', my_points)
        my_date = (
            date.strftime('%Y-%m-%d') + ' ' + time_now.strftime(format='%H:%M')
        )
        habit_options = habits['HABIT_NAME'].unique().tolist()
        habit_option = st.radio(
            label='Choose Habit', options=habit_options, horizontal=True
        )
        count = st.number_input(
            label='Count Completed', min_value=0, value=1
        )
        st.dataframe(data=need_df,  hide_index=True)
        save = st.form_submit_button(label='Save')
        if save:
            habit_id = habit_option + '_' + str(object=my_date)
            st.write(habit_id)
            with sqlitecloud.connect(
                st.secrets['habits_connection']['DB_CONNECTION']
            ) as conn:
                # EMAIL, HABIT_NAME, DATE, TIME, COUNT_COMPLETED
                conn.execute(
                    sql=sql.add_daily_habits(),
                    parameters=(
                        st.session_state.email,
                        habit_option,
                        str(date.strftime('%m/%d/%Y')),
                        str(time_now.strftime(format='%H:%M')),
                        count
                    )
                )
                conn.commit()
            st.write('Habit Added')
            time.sleep(1)
            st.rerun()
else:
    st.write('Please login to track habits')
    login_page = st.button(label='Login')
    if login_page:
        st.switch_page('Home.py')