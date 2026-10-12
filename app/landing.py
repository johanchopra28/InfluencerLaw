"""Markup and styles for the HYPECHECK landing page (app.py).

Four sections: the hero, what HYPECHECK does for you (three service cards),
how each service works, and what HYPECHECK cannot do. The landing page is
purely informational. Nothing here asks for input; each service has its own
page that collects only the fields it needs.

Links to the service pages are real Streamlit page links, not anchors:
Streamlit Cloud serves the app inside an iframe where a plain href resolves
to the wrong URL.
"""
from __future__ import annotations

import streamlit as st

from app.config import APP_NAME, DISCLAIMER_TEXT
from app.ai_disclosure import AI_DISCLOSURE_PATH
from app.faq import FAQ_PATH
from app.site import (
    BLUSH,
    CREAM,
    HAIR,
    INK,
    PAD,
    PRIVACY_PATH,
    RED,
    SANS,
    SERIF,
    SERVICES,
    compact,
    esc,
    icon,
    inject_site_css,
)

_CARD_ICONS = {"contract": "doc", "campaign": "list", "content": "chat"}

_FLOWS = [
    (
        "A",
        "Contract review",
        [
            "Select the contract-checking tool.",
            "Upload or provide the relevant contract details.",
            f"{APP_NAME} identifies potentially risky clauses, missing terms and areas requiring attention.",
            "Review the findings and suggested revisions.",
        ],
    ),
    (
        "B",
        "Campaign review",
        [
            "Select the campaign-checking tool.",
            "Provide the campaign brief, brand details, deliverables and relevant requirements.",
            f"{APP_NAME} flags potential compliance issues and missing disclosures.",
            "Review the findings before proceeding with the campaign.",
        ],
    ),
    (
        "C",
        "Caption and content review",
        [
            "Select the content-checking tool.",
            "Paste the caption or provide the relevant post, reel script or campaign content.",
            f"{APP_NAME} analyses the content for potential risks.",
            "Review the result and revise the content where necessary.",
        ],
    ),
]

_LIMITS = [
    "It does not replace a qualified lawyer or provide a definitive legal opinion.",
    "It cannot guarantee that a contract, campaign, caption or advertisement is legally compliant.",
    "It cannot guarantee that a platform, regulator or advertising body will approve the content.",
    "It cannot independently verify every factual claim, contractual representation or third-party permission.",
    "Its findings depend on the information and documents provided, the applicable rules and the tool's analytical capabilities.",
    "High-risk or ambiguous issues should be escalated for qualified human review.",
]

_CSS = """
.st-key-hero { max-width: 1100px; width: 100%; margin: 0 auto; padding: 72px 48px 64px; box-sizing: border-box; gap: 0 !important; }
.st-key-hero [data-testid="stVerticalBlock"] { gap: 0 !important; }
.st-key-hero [data-testid="stHorizontalBlock"] { align-items: flex-start; }

.st-key-cta-primary [data-testid="stPageLink-NavLink"], [class*="st-key-cardcta-"] [data-testid="stPageLink-NavLink"] {
    background: @INK@; border-radius: 0; padding: 14px 26px; display: inline-flex; width: auto; min-height: 48px;
    align-items: center; justify-content: center; transition: background 0.12s ease;
}
.st-key-cta-primary [data-testid="stPageLink-NavLink"]:hover, [class*="st-key-cardcta-"] [data-testid="stPageLink-NavLink"]:hover { background: #3A3A3A; }
.st-key-cta-primary [data-testid="stPageLink-NavLink"] *, [class*="st-key-cardcta-"] [data-testid="stPageLink-NavLink"] * { color: #FFFFFF !important; font-size: 14px !important; font-family: @SANS@ !important; }
.st-key-cta-primary, [class*="st-key-cardcta-"] { height: 48px; }

.hc h1.hc-h1--hero { font-size: 68px !important; line-height: 1 !important; margin: 0 0 22px !important; }
.hc .hc-tagline { font-family: @SERIF@; font-style: italic; font-size: 25px; margin: 0 0 24px; }
.hc p.hc-lede--hero { max-width: 430px; margin: 0 0 20px !important; }
.hc p.hc-note--hero { max-width: 430px; margin: 0 0 30px !important; }

.hc-cards { position: relative; width: 100%; max-width: 380px; height: 330px; margin-left: auto; }
.hc-card { position: absolute; width: 215px; height: 140px; border-radius: 5px; padding: 24px 22px; font-family: @SERIF@; font-size: 13px; letter-spacing: 0.16em; text-transform: uppercase; }
.hc-card--red { background: @RED@; color: #FBEDE6; left: 20px; top: 0; transform: rotate(-4.5deg); }
.hc-card--mustard { background: #C9982E; color: #3B2B0B; left: 150px; top: 72px; transform: rotate(3deg); }
.hc-card--green { background: #4A7A52; color: #EAF1EA; left: 0; top: 168px; transform: rotate(-3deg); }
.hc-hero-rule { height: 1px; background: @HAIR@; margin: 64px 0 0; }

.hc-band { width: 100%; padding: 76px @PAD@ 84px; }
.hc-band--blush { background: @BLUSH@; }
.hc-band--cream { background: @CREAM@; }
.hc-band .hc-eyebrow { margin-bottom: 40px; }
.hc-intro { font-family: @SERIF@; font-style: italic; font-size: 21px; margin: -14px 0 40px; }

.st-key-band-services { background: @BLUSH@; padding: 76px @PAD@ 84px; }
.st-key-band-services [data-testid="stHorizontalBlock"] { align-items: stretch; }
[class*="st-key-card-"] { background: #FAF4EE; border: 1px solid #D8CCC0; padding: 30px 28px 32px; flex: 1 1 auto; gap: 0 !important; transition: border-color 0.15s ease; }
[class*="st-key-card-"]:hover { border-color: @INK@; }
[class*="st-key-cardtitle-"] { min-height: 84px; }
[class*="st-key-cardtitle-"] [data-testid="stPageLink-NavLink"] { background: transparent; padding: 0; min-height: 0; margin: 20px 0 12px; }
[class*="st-key-cardtitle-"] [data-testid="stPageLink-NavLink"] p { font-family: @SERIF@; font-weight: 700; font-size: 24px; line-height: 1.2; color: @INK@; margin: 0; text-decoration: underline; text-decoration-color: transparent; text-underline-offset: 6px; transition: text-decoration-color 0.12s ease; }
[class*="st-key-cardtitle-"] [data-testid="stPageLink-NavLink"]:hover p { text-decoration-color: @INK@; }
[class*="st-key-cardtitle-"] [data-testid="stPageLink-NavLink"], [class*="st-key-cardtitle-"] [data-testid="stPageLink-NavLink"] span, [class*="st-key-cardtitle-"] [data-testid="stPageLink-NavLink"] p { white-space: normal !important; overflow: visible !important; text-overflow: clip !important; }
.hc p.hc-card-p { font-size: 14px !important; line-height: 1.7 !important; color: #4A423C !important; margin: 0 0 26px !important; min-height: 124px; }

.hc-flows { display: grid; grid-template-columns: repeat(3, 1fr); }
.hc-flow { padding: 4px 32px; border-left: 1px solid #CDBBB0; }
.hc-flow:first-child { padding-left: 0; border-left: none; }
.hc-flow-tag { font-family: @SERIF@; font-size: 40px; color: #9C918A; line-height: 1; margin-bottom: 14px; }
.hc-flow-title { font-weight: 700; font-size: 16px; margin-bottom: 18px; }
.hc-flow ol { list-style: none; margin: 0; padding: 0; }
.hc-flow li { display: grid; grid-template-columns: 26px 1fr; gap: 6px; font-size: 13.5px; line-height: 1.6; color: #5B524B; padding: 10px 0; border-top: 1px solid #E3D6CB; }
.hc-flow li span { font-family: @SERIF@; color: @INK@; }

.hc-limits { display: grid; grid-template-columns: 1fr 1fr; column-gap: 56px; }
.hc-limit { display: grid; grid-template-columns: 40px 1fr; padding: 18px 0; border-top: 1px solid #CDBBB0; font-size: 14px; line-height: 1.65; color: #3E3731; }
.hc-limit span { font-family: @SERIF@; color: #9C918A; font-size: 18px; }
.hc-closing { font-family: @SERIF@; font-style: italic; font-size: 21px; line-height: 1.5; max-width: 640px; margin: 44px 0 0; }

.st-key-footer-privacy { padding: 0 0 56px; display: flex; flex-direction: row; flex-wrap: wrap; justify-content: center; gap: 12px 36px; }
.st-key-footer-privacy [data-testid="stPageLink"] { width: auto; display: flex; justify-content: center; }
.st-key-footer-privacy [data-testid="stPageLink-NavLink"] { justify-content: center; }
.st-key-footer-privacy [data-testid="stPageLink-NavLink"] p { font-size: 17px; font-weight: 700; text-decoration: underline; color: @INK@; }
.hc-footer { max-width: 1170px; margin: 0 auto; border-top: 1px solid @HAIR@; padding: 30px 48px 20px; text-align: center; font-size: 12px; line-height: 1.7; color: #7A726B; }

@media (max-width: 820px) {
    .st-key-hero { padding: 48px 24px 40px; }
    .hc h1.hc-h1--hero { font-size: 48px !important; }
    .hc-cards { margin: 32px 0 0; }
    .hc-band, .st-key-band-services { padding: 52px 24px 56px; }
    .hc-flows { grid-template-columns: 1fr; }
    .hc-flow, .hc-flow:first-child { border-left: none; border-top: 1px solid #CDBBB0; padding: 24px 0; }
    .hc-flow:first-child { border-top: none; }
    .hc-limits { grid-template-columns: 1fr; }
    .hc-footer { padding: 28px 24px 56px; }
    [class*="st-key-cardtitle-"], .hc p.hc-card-p { min-height: 0 !important; }
}
@media (max-width: 640px) {
    .hc h1.hc-h1--hero { font-size: 38px !important; }
    .hc .hc-tagline { font-size: 21px; }
}
"""


def inject_landing_css() -> None:
    css = _CSS
    for token, value in {
        "@INK@": INK, "@RED@": RED, "@HAIR@": HAIR, "@BLUSH@": BLUSH, "@CREAM@": CREAM,
        "@PAD@": PAD, "@SERIF@": SERIF, "@SANS@": SANS,
    }.items():
        css = css.replace(token, value)
    inject_site_css(css)


def hero_text_html() -> str:
    return compact(
        f"""
        <div class="hc">
        <h1 class="hc-h1 hc-h1--hero">{APP_NAME}</h1>
        <div class="hc-tagline">Before it goes live, someone should check it.</div>
        <p class="hc-lede hc-lede--hero">Every influencer post gets checked for creativity and brand fit. It almost never
        gets checked for legal risk. {APP_NAME} reads the contract, the brief and the content together and flags what is
        at risk, citing the provision behind each flag.</p>
        <p class="hc-note hc-note--hero">{esc(DISCLAIMER_TEXT)}</p>
        </div>
        """
    )


def hero_cards_html() -> str:
    return compact(
        """
        <div class="hc"><div class="hc-cards">
        <div class="hc-card hc-card--red">Flag</div>
        <div class="hc-card hc-card--mustard">Clause</div>
        <div class="hc-card hc-card--green">Caption</div>
        </div></div>
        """
    )


def hero_rule_html() -> str:
    return '<div class="hc-hero-rule"></div>'


def services_intro_html() -> str:
    return f'<div class="hc"><div class="hc-eyebrow">What {APP_NAME} does for you</div></div>'


def card_icon_html(key: str) -> str:
    return f'<div class="hc">{icon(_CARD_ICONS[key], 30)}</div>'


def card_text_html(key: str) -> str:
    return f'<div class="hc"><p class="hc-card-p">{esc(SERVICES[key]["blurb"])}</p></div>'


def how_and_limits_html() -> str:
    flows = "".join(
        f'<div class="hc-flow"><div class="hc-flow-tag">{tag}</div><div class="hc-flow-title">{esc(title)}</div><ol>'
        + "".join(f"<li><span>{n}</span><div>{esc(step)}</div></li>" for n, step in enumerate(steps, 1))
        + "</ol></div>"
        for tag, title, steps in _FLOWS
    )
    limits = "".join(
        f'<div class="hc-limit"><span>{n:02d}</span><div>{esc(text)}</div></div>' for n, text in enumerate(_LIMITS, 1)
    )
    return compact(
        f"""
        <div class="hc">
        <section class="hc-band hc-band--cream">
        <div class="hc-eyebrow">How each service works</div>
        <div class="hc-intro">Know what to expect before you enter any information.</div>
        <div class="hc-flows">{flows}</div>
        </section>
        <section class="hc-band hc-band--blush">
        <div class="hc-eyebrow">What {APP_NAME} cannot do</div>
        <div class="hc-intro">Clear limits, so you know what to rely on it for.</div>
        <div class="hc-limits">{limits}</div>
        <p class="hc-closing">The purpose is to help you identify potential problems early, not to eliminate the need
        for professional judgment.</p>
        </section>
        <div class="hc-footer">India only. {APP_NAME} is a pre-publication screening aid for a human legal or
        compliance reviewer, not a guarantee of compliance.<br>{esc(DISCLAIMER_TEXT)}</div>
        </div>
        """
    )


def render_landing() -> None:
    inject_landing_css()

    with st.container(key="hero"):
        left, right = st.columns([1.25, 1], gap="large")
        with left:
            st.markdown(hero_text_html(), unsafe_allow_html=True)
            with st.container(key="cta-primary"):
                st.page_link(SERVICES["content"]["path"], label="Check Your Content")
        with right:
            st.markdown(hero_cards_html(), unsafe_allow_html=True)
        st.markdown(hero_rule_html(), unsafe_allow_html=True)

    with st.container(key="band-services"):
        st.markdown(services_intro_html(), unsafe_allow_html=True)
        for col, (key, svc) in zip(st.columns(3, gap="medium"), SERVICES.items()):
            with col:
                with st.container(key=f"card-{key}"):
                    st.markdown(card_icon_html(key), unsafe_allow_html=True)
                    with st.container(key=f"cardtitle-{key}"):
                        st.page_link(svc["path"], label=svc["title"])
                    st.markdown(card_text_html(key), unsafe_allow_html=True)
                    with st.container(key=f"cardcta-{key}"):
                        st.page_link(svc["path"], label=svc["cta"])

    st.markdown(how_and_limits_html(), unsafe_allow_html=True)
    with st.container(key="footer-privacy"):
        st.page_link(FAQ_PATH, label="FAQ")
        st.page_link(AI_DISCLOSURE_PATH, label="AI disclosure")
        st.page_link(PRIVACY_PATH, label="Privacy and data handling")
