import streamlit as st
import Authenticate
from runxdash import run_xdash
import os


auth = Authenticate.Authenticate("cookies_namelkanflnef", "cookie_keyajnfkjankfjan", cookie_expiry_days=0.01)

email, auth_status = auth.login()


# --- Check the Authentication Status ---

if st.session_state.auth_status:
    run_xdash()
    auth.logout("Log out", "sidebar")
    #if os.path.exists("source_data.csv"):
        #os.remove("source_data.csv")


