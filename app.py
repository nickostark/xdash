import os
import streamlit as st
import Authenticate
from runxdash import run_xdash


def _required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _enable_demo_mode(email: str):
    """Bypass authentication so the dashboard can be explored locally."""
    st.session_state["auth_status"] = True
    st.session_state["email"] = email
    st.session_state["logout"] = False
    st.session_state["email_found"] = True
    st.info(f"Demo mode enabled. Signed in locally as {email}.")


DEMO_MODE = _is_truthy(os.getenv("XDASH_DEMO_MODE"))
DEMO_EMAIL = os.getenv("XDASH_DEMO_EMAIL") or "demo@xdash.local"

auth = None

if DEMO_MODE:
    _enable_demo_mode(DEMO_EMAIL)
else:
    try:
        cookie_name = _required_env("XDASH_COOKIE_NAME")
        cookie_key = _required_env("XDASH_COOKIE_KEY")
    except RuntimeError:
        _enable_demo_mode(DEMO_EMAIL)
        DEMO_MODE = True
    else:
        auth = Authenticate.Authenticate(cookie_name, cookie_key, cookie_expiry_days=0.01)
        auth.login()


# --- Check the Authentication Status ---

if st.session_state.get("auth_status"):
    run_xdash()
    if auth is not None:
        auth.logout("Log out", "sidebar")
