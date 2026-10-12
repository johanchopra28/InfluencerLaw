"""HYPECHECK - privacy: what happens to what you submit."""
from __future__ import annotations

import streamlit as st

from app.config import APP_NAME
from app.footer import render_footer
from app.legal import LEGAL_UPDATED, contact_paragraph, links_html
from app.privacy import FULL_NOTICE, FULL_TITLE
from app.site import compact, esc, inject_site_css, page_head, render_nav

st.set_page_config(
    page_title=f"{APP_NAME} - Privacy policy",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_site_css()
render_nav("")
page_head(
    "Privacy",
    FULL_TITLE,
    "How the documents and text you submit are handled, and which outside services see them.",
)

with st.container(key="body"):
    for heading, paragraphs in FULL_NOTICE:
        body = "".join(f'<p class="hc-body">{esc(p)}</p>' for p in paragraphs)
        st.markdown(
            compact(f'<div class="hc"><h2 class="hc-h2">{esc(heading)}</h2>{body}</div>'),
            unsafe_allow_html=True,
        )
    st.markdown(
        compact(
            f'<div class="hc">{links_html()}{contact_paragraph()}'
            f'<p class="hc-small" style="margin-top:28px">Last updated {esc(LEGAL_UPDATED)}.</p></div>'
        ),
        unsafe_allow_html=True,
    )

render_footer()
