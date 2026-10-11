"""HYPECHECK - landing page (entry point).

The review tool lives at pages/1_Run_Review.py, reached from the "Run a review"
button below. Run with:
    streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from app.config import APP_NAME
from app.landing import (
    ASCI_URL,
    hero_cards_html,
    hero_rule_html,
    hero_text_html,
    inject_landing_css,
    sections_html,
)

st.set_page_config(
    page_title=f"{APP_NAME} - Pre-Publication Legal Review",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_landing_css()

with st.container(key="hero"):
    left, right = st.columns([1.25, 1], gap="large")
    with left:
        st.markdown(hero_text_html(), unsafe_allow_html=True)
        run_col, asci_col, _ = st.columns([1, 1.6, 2], gap="small")
        with run_col:
            st.page_link("pages/1_Run_Review.py", label="Run a review")
        with asci_col:
            st.link_button("Read the ASCI Code", ASCI_URL)
    with right:
        st.markdown(hero_cards_html(), unsafe_allow_html=True)
    st.markdown(hero_rule_html(), unsafe_allow_html=True)

st.markdown(sections_html(), unsafe_allow_html=True)
