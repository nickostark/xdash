import os
import mysql.connector
import streamlit as st
from sendEmail import send_email
from pymongo import MongoClient
import random
import time
from datetime import datetime, timedelta


def _required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _mongo_client():
    mongo_url = _required_env("MONGO_URL")
    return MongoClient(mongo_url)


def wp_db_query(entered_email):

    user_found = False
    auth_success = False
    email_sent = False

    # Get the current time
    current_time = datetime.now()


    # Declare the database via env variables
    db_host = _required_env("WP_DB_HOST")
    db_user = _required_env("WP_DB_USER")
    db_password = _required_env("WP_DB_PASSWORD")
    db_name = _required_env("WP_DB_NAME")
    port = int(_required_env("WP_DB_PORT"))
    
    # Establish the connection
    connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=port
    )
    
    
    # Create a cursor object to interact with db
    cursor = connection.cursor()

    # -- Make the query ...

    # Execute SQL query to fetch user_login
    query_user_email = "SELECT user_email FROM `wp_users` WHERE user_email=%s"
    
    connection.reconnect()
    cursor.execute(query_user_email, (entered_email,))
    rtvd_email = cursor.fetchall()
    
    
    if len(rtvd_email) == 0:
        st.error("Email Not Found.")
        return False
    else:
        recipient_email = rtvd_email[0][0]

    
    if recipient_email == entered_email: 
        # Find the ID in wp_users 
        query_ID = "SELECT ID FROM `wp_users` WHERE user_email=%s"
        cursor.execute(query_ID, (entered_email,))
        rtvd_ID = cursor.fetchall()[0][0]

        # Find the user_id in `wp_pms_member_subscriptions` table that matches ID
        query_subscriber = "SELECT * FROM `wp_pms_member_subscriptions` WHERE user_id=%s"
        cursor.execute(query_subscriber, (rtvd_ID,))
        rtvd_subscriber = cursor.fetchall()

        # Close the connection 
        connection.close()

        # Check if current user has an active subscription plan
        if len(rtvd_subscriber) > 0:
            rtvd_sub_status = rtvd_subscriber[0][5]
            rtvd_plan_expiry = rtvd_subscriber[0][4]
            rtvd_sub_plan = rtvd_subscriber[0][2]
            #st.write("subscriber found")
            if rtvd_sub_status == 'active':
                #st.write(rtvd_sub_plan)
                #st.write("rtvd_sub_status active")
                if rtvd_plan_expiry > current_time:
                    return True
                else:
                    st.error("Your subscription plan has expired.")
            else:
                st.error("You don't have an active subscription plan.")
        else:
            st.error("You're not a subscriber.")
        

    return False
    

    

def send_verification_code(recipient_email):
    subject = "CogniMachina: Verification Code"
    verification_code, expiry_time = write_to_mongo(recipient_email)
    body = f'Your verification code is: {verification_code}'
    send_email(subject, body, recipient_email)
    

def write_to_mongo(email):
    verification_code = ''.join(str(random.randint(0, 9)) for _ in range(6))

    connection = _mongo_client()
    
    # Database object
    db = connection.database


    # Created or Switched to collection names
    collection = db.verification_collection 

    # Set expiry time to 2 minutes from now
    current_time = time.time()

    # Code expires after 1.5 mins
    code_expiry_time = current_time + 90

      
    code_record = { 
            "email":email, 
            "code":verification_code,
            "expiry": code_expiry_time
            } 

    # Insert OTP data 
    rec_id = collection.insert_one(code_record) 
      
    #print("Data inserted with record ids",rec_id1," ",rec_id2) 
      
    # Printing the data inserted 
    #cursor = collection.find() 

    

    return verification_code, code_expiry_time


def store_last_login(login_time):
    connection = _mongo_client()
    
    # Database object
    db = connection.database

    # Created or switched to collection names: my_gfg_collection 
    collection = db['cookie_collection']

    last_login = { 
            "email":email, 
            "last_login": login_time
            } 

    # Insert last login 
    rec_id = collection.insert_one(last_login) 
    
    

def check_code(email, code):
    ''' 
    This function verifies if the code exists, belongs to user under authentication process, 
    and hasn't been expired.
    '''
    current_time = time.time()
    
    connection = _mongo_client()
    
    # Database object
    db = connection.database


    # Created or Switched to collection names: my_gfg_collection 
    collection = db.verification_collection 

    count = collection.count_documents({"email":{"$eq":email}, "code":{"$eq":code}, "expiry":{"$gt":current_time}})

    # Close the connection
    #db.close()
    
    if count > 0:
        return True

    else:
        st.error("Incorrect/Expired Code.")
        return False

def check_recent_otp(email):
    connection = _mongo_client()

    current_time = time.time()

    
    # Database object
    db = connection.database

    # Created or Switched to collection names: my_gfg_collection 
    collection = db['verification_collection']

    count = collection.count_documents({"email":{"$eq":email}, "expiry":{"$gt":current_time}})

    remaining = 0

    if count > 0:
        result = collection.find_one({"email":{"$eq":email}, "expiry":{"$gt":current_time}})
        remaining = (result["expiry"]-current_time)

    return remaining


    
