import jwt
import bcrypt
import streamlit as st
from datetime import datetime, timedelta
import extra_streamlit_components as stx
import pandas as pd
import numpy as np
import os
import sys
import calendar
import pytz
from streamlit_agraph import agraph, Node, Edge, Config
import mysql.connector
import time
#import inspect
#st.write(inspect.getsource(stauth.Authenticate.login))

from database_handling import wp_db_query, send_verification_code, check_code, check_recent_otp

class Authenticate:

    def __init__(self, cookie_name: str, key: str, cookie_expiry_days: float=30.0): 
        
        self.cookie_name = cookie_name
        self.key = key
        self.cookie_expiry_days = cookie_expiry_days
        self.cookie_manager = stx.CookieManager()
        #self.exp_date = None

        print('In Constructor:')
        if 'email_found' not in st.session_state:
            st.session_state.email_found = None
            print(f'email_found <- {st.session_state.email_found}')
        if 'auth_status' not in st.session_state:
            st.session_state.auth_status = None
            print(f'auth_status <- {st.session_state.auth_status}')
        if 'email' not in st.session_state:
            st.session_state.email = None
        if 'logout' not in st.session_state:
            st.session_state.logout = None
            print(f'logout <- {st.session_state.logout}')

        print('---------------------------')

    def _token_encode(self):
        return jwt.encode({'email':st.session_state.email,
            'exp_date':self.exp_date}, self.key, algorithm='HS256')


    def _token_decode(self):
        try:
            return jwt.decode(self.token, self.key, algorithms=['HS256'])
        except:
            return False

    def _set_exp_date(self):
        return (datetime.utcnow() + timedelta(days=self.cookie_expiry_days)).timestamp()
        
    def _check_cookie(self):
        """
        Checks the validity of the reauthentication cookie.
        """
        self.token = self.cookie_manager.get(self.cookie_name)
        if self.token is not None:
            self.token = self._token_decode()
            if self.token is not False:
                if not st.session_state.logout:
                    print(f'logout is {st.session_state.logout} in check cookie ')
                    if self.token['exp_date'] > datetime.utcnow().timestamp():
                        if 'email' in self.token:
                            st.session_state['email'] = self.token['email']
                            print('In Check Cookie')
                            st.session_state.auth_status = True
                            print(f'auth_status <- {st.session_state.auth_status}')
                            print('---------------------------')
                            #st.write('checking cookie')


                            
    def find_email(self):
        if wp_db_query(self.email):
            st.session_state.email = self.email
            
            return True         
        return False


    def check_code(self, code):
        if check_code(st.session_state.email, code):
            print('In Check Code')
            print(f'auth_status = {st.session_state.auth_status}')
            self.exp_date = self._set_exp_date()
            self.token = self._token_encode()
            self.cookie_manager.set(self.cookie_name, self.token, 
                                    expires_at=datetime.now() + timedelta(days=self.cookie_expiry_days))
            st.session_state.auth_status = True
            print(f'auth_status <- {st.session_state.auth_status}')
            print('---------------------------')
            return True
        return False
        

    def login(self):
        if 'submit' not in st.session_state:
            st.session_state.submit = None 
        #if 'verify' not in st.session_state:
        #    st.session_state.verify = None 

        #st.write(f'st.session_state.verify = {st.session_state.verify}')
        print('In Login:')
        if not st.session_state.auth_status:
            print(f'auth_status = {st.session_state.auth_status}')
            self._check_cookie()
            print(f'auth_status <- {st.session_state.auth_status} after check cookie')
            if not st.session_state.auth_status:
                print(f'email_found = {st.session_state.email_found}')
                if not st.session_state.email_found: 
                    placeholder = st.empty()
                    login_form = placeholder.form('Login')            
                    login_form.subheader("Subscriber's Email")
                    self.email = login_form.text_input('Email').lower()
                    #st.session_state['email'] = self.email
                    submit = login_form.form_submit_button('Log in')
                    if submit:
                        st.session_state.submit = True
                    if st.session_state.submit and self.find_email():
                        if check_recent_otp(self.email) == 0:
                            st.session_state.email_found = True
                            send_verification_code(st.session_state.email)
                            print('Verification Code Sent.')
                            print(f'email_found <- {st.session_state.email_found}')
                            placeholder.empty()
                        else:
                            remaining = check_recent_otp(self.email)
                            minutes, seconds = divmod(int(remaining), 60)
                            formatted_time = f"{minutes:02d}:{seconds:02d}"
                            st.error(f'You can request a new code in {formatted_time}.')
                        
                        #st.write('HERE?')
                if st.session_state.email_found:
                    #st.write(f'st.session_state.email_found: {st.session_state.email_found}')
                    #st.text_input('something')
                    placeholder = st.empty()
                    verification_form = placeholder.form("Verification")
                    verification_form.subheader("Verification")
                    verification_form.success(f'''An email with a 6-digit verification code has been 
                    sent to :blue[{st.session_state.email}]. Enter the code to continue.''')
                    code = verification_form.text_input('Verification Code', placeholder='Your code')
                    verify = verification_form.form_submit_button('Verify')

                    temp_form = st.empty()
                    #expiry = f"{(90//60):02d}:{(90%60):02d}"
                    #for secs in range(90, 0, -1):
                    #    mm, ss = secs//60, secs%60
                    #    temp_form.metric("Your code will expire in", f"{mm:02d}:{ss:02d}")
                    #    time.sleep(1)
                        
                    if verify: 
                        if self.check_code(code):
                            placeholder.empty()
                        

        
        return st.session_state['email'], st.session_state['auth_status']



    def logout(self, button_name: str, location: str='main', key: str=None):
        if location not in ['main', 'sidebar']:
            raise ValueError("Location must be one of 'main' or 'sidebar'")
        if location == 'main':
            if st.button(button_name, key):
                self.cookie_manager.delete(self.cookie_name)
                st.session_state['logout'] = True
                st.session_state['email'] = None
                st.session_state['email_found'] = None
                st.session_state['auth_status'] = None
        elif location == 'sidebar':
            if st.sidebar.button(button_name, key):
                self.cookie_manager.delete(self.cookie_name)
                print('In logout:')
                print('cookie deleted')
                st.session_state.logout = True
                print(f'logout <- {st.session_state.logout}')
                st.session_state.email = None
                st.session_state.email_found = None 
                st.session_state.auth_status = None
                del st.session_state.auth_status
                if os.path.exists("source_data.csv"):
                    os.remove("source_data.csv")
                print('----------------------------')