import os


def get_secret(*names, default=""):
    """Read a secret from Streamlit secrets first, then environment variables."""
    for name in names:
        value = _read_streamlit_secret(name)
        if value:
            return value
        value = os.getenv(name)
        if value:
            return value
    return default


def _read_streamlit_secret(name):
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return ""
