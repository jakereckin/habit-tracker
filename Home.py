import streamlit as st
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd


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
    users_db = my_db['users']
    users = pd.DataFrame(data=list(users_db.find())).drop(columns=['_id'])
    return users


st.header(body='Habit Tracker', divider='blue')


if st.session_state.login_status:
    st.write('Welcome', st.session_state.user_name)
else:
    user_name = st.text_input(label='Username')
    password = st.text_input(label='Password', type='password')
    login = st.button(label='Login')
    signup = st.button(label='Sign Up')
    if login:
        client = get_client()
        users = get_my_db(client=client)
        this_user = users[(users['Username'] == user_name) & (users['Password'] == password)]
        if this_user.shape[0] > 0:
            st.write('Login Successful')
            st.session_state.login_status = True
            st.session_state.user_name = user_name
        else:
            st.write('Login Failed')

    if signup:
        client = get_client()
        users = get_my_db(client=client)
        this_user = users[(users['Username'] == user_name)]
        if this_user.shape[0] > 0:
            st.write('User already exists')
        else:
            user = {
                'Username': user_name,
                'Password': password,
            }
            users_db = client['habit-tracker']['users']
            users_db.insert_one(document=user)
            st.write('User Added')
            st.session_state.login_status = True
            st.session_state.user_name = user_name