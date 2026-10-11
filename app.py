"""HYPECHECK - landing page (entry point).

Purely informational: what HYPECHECK does, how each service works and what it
cannot do. Each service has its own page under pages/. Run with:
    streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from app.config import APP_NAME
from app.landing import render_landing

st.set_page_config(
    page_title=f"{APP_NAME} - Pre-Publication Legal Review",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
render_landing()
