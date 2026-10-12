"""HYPECHECK - AI disclosure: what the AI does, what it runs on, and where its limits are."""
from __future__ import annotations

import streamlit as st

from app.ai_disclosure import LAST_UPDATED, LEDE, SECTIONS, TITLE
from app.config import APP_NAME
from app.footer import render_footer
from app.faq import FAQ_PATH
from app.site import PRIVACY_PATH, compact, esc, inject_site_css, page_head, render_nav

st.set_page_config(
    page_title=f"{APP_NAME} - AI disclosure",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_site_css()
render_nav("")
page_head("AI disclosure", TITLE, LEDE)

with st.container(key="body"):
    for heading, intro, bullets in SECTIONS:
        intro_html = f'<p class="hc-body">{esc(intro)}</p>' if intro else ""
        items = "".join(f"<li>{esc(b)}</li>" for b in bullets)
        st.markdown(
            compact(
                f'<div class="hc"><h2 class="hc-h2">{esc(heading)}</h2>{intro_html}'
                f'<ul class="hc-scope" style="font-size:14px;max-width:760px">{items}</ul></div>'
            ),
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<div class="hc"><p class="hc-small" style="margin-top:28px">Last updated {esc(LAST_UPDATED)}. '
        "This page is updated when the AI services or the way results are produced change.</p></div>",
        unsafe_allow_html=True,
    )
    left, right, _ = st.columns([1, 1, 3], gap="small")
    with left:
        st.page_link(PRIVACY_PATH, label="Privacy and data handling")
    with right:
        st.page_link(FAQ_PATH, label="Frequently asked questions")

render_footer()
