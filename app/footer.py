"""The site footer, shown at the bottom of every page: the screening-aid notice, the
credit, and links to the FAQ, AI disclosure and privacy pages."""
from __future__ import annotations

import streamlit as st

from app.ai_disclosure import AI_DISCLOSURE_PATH
from app.config import APP_NAME, DISCLAIMER_TEXT
from app.faq import FAQ_PATH
from app.terms import TERMS_PATH
from app.site import HAIR, INK, PRIVACY_PATH, esc

CREDIT = [
    ("Vanshika Verma", "https://github.com/vanshikaverma2-7"),
    ("Johan Chopra", "https://github.com/johanchopra28"),
]

_CSS = """
<style>
.hc-sitefooter { max-width: 1170px; margin: 40px auto 0; border-top: 1px solid @HAIR@; padding: 30px 48px 30px; text-align: center; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 12px; line-height: 1.7; color: #7A726B; }
.hc-sitefooter .hc-credit { display: inline-block; margin-top: 8px; }
.hc-sitefooter .hc-name-note { display: inline-block; margin-top: 4px; font-size: 11px; }
.hc-sitefooter .hc-credit a { color: @INK@; font-weight: 700; text-decoration: underline; }
.st-key-site-footer-links { padding: 0 0 56px; display: flex; flex-direction: row; flex-wrap: wrap; justify-content: center; gap: 12px 36px; }
.st-key-site-footer-links [data-testid="stPageLink"] { width: auto; display: flex; justify-content: center; }
.st-key-site-footer-links [data-testid="stPageLink-NavLink"] { justify-content: center; }
.st-key-site-footer-links [data-testid="stPageLink-NavLink"] { background: transparent; padding: 6px 0; min-height: 0; border-radius: 0; }
.st-key-site-footer-links [data-testid="stPageLink-NavLink"] p { font-size: 12px; text-transform: uppercase; letter-spacing: 0.12em; color: #555; margin: 0; text-decoration: none; font-weight: 400; }
.st-key-site-footer-links [data-testid="stPageLink-NavLink"]:hover p { color: @INK@; }
@media (max-width: 820px) { .hc-sitefooter { padding: 28px 24px 28px; } }
</style>
""".replace("@HAIR@", HAIR).replace("@INK@", INK)


def render_footer() -> None:
    credit = " and ".join(
        f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(name)}</a>' for name, url in CREDIT
    )
    st.markdown(
        _CSS
        + '<div class="hc-sitefooter">India only. '
        + esc(APP_NAME)
        + " is a pre-publication screening aid for a human legal or compliance reviewer, not a guarantee of "
        + "compliance.<br>"
        + esc(DISCLAIMER_TEXT)
        + f'<br><span class="hc-credit">By {credit}</span>'
        + '<br><span class="hc-name-note">HYPECHECK is a working name. No trademark in it is currently owned.</span></div>',
        unsafe_allow_html=True,
    )
    with st.container(key="site-footer-links"):
        st.page_link(FAQ_PATH, label="FAQ")
        st.page_link(AI_DISCLOSURE_PATH, label="AI disclosure")
        st.page_link(TERMS_PATH, label="Terms")
        st.page_link(PRIVACY_PATH, label="Privacy and data handling")
