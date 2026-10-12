"""HYPECHECK - FAQ: plain answers about using the tool and reading its results."""
from __future__ import annotations

import streamlit as st

from app.ai_disclosure import AI_DISCLOSURE_PATH
from app.config import APP_NAME
from app.faq import GROUPS, LEDE, TITLE
from app.site import PRIVACY_PATH, compact, esc, inject_site_css, page_head, render_nav

st.set_page_config(
    page_title=f"{APP_NAME} - FAQ",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_site_css()
render_nav("")
page_head("FAQ", TITLE, LEDE)

with st.container(key="body"):
    # Every answer is on the page, not behind a click.
    for group, items in GROUPS:
        qa = "".join(
            f'<p class="hc-body" style="font-weight:700;font-size:15px;margin:22px 0 4px">{esc(q)}</p>'
            f'<p class="hc-body" style="max-width:760px">{esc(a)}</p>'
            for q, a in items
        )
        st.markdown(compact(f'<div class="hc"><h2 class="hc-h2">{esc(group)}</h2>{qa}</div>'), unsafe_allow_html=True)
    st.write("")
    left, right, _ = st.columns([1, 1, 3], gap="small")
    with left:
        st.page_link(AI_DISCLOSURE_PATH, label="AI disclosure")
    with right:
        st.page_link(PRIVACY_PATH, label="Privacy and data handling")
