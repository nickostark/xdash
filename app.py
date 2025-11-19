import os
import streamlit as st
import Authenticate
from runxdash import run_xdash


def _required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


cookie_name = _required_env("XDASH_COOKIE_NAME")
cookie_key = _required_env("XDASH_COOKIE_KEY")

auth = Authenticate.Authenticate(cookie_name, cookie_key, cookie_expiry_days=0.01)

email, auth_status = auth.login()


# --- Check the Authentication Status ---

if st.session_state.auth_status:
    run_xdash()
    auth.logout("Log out", "sidebar")
    #if os.path.exists("source_data.csv"):
        #os.remove("source_data.csv")

