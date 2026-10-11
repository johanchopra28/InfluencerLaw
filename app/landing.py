"""Markup and styles for the HYPECHECK landing page (app.py).

The page is an editorial layout: cream and blush full-width bands, Georgia
display type, hairline rules, square buttons. The hero's two CTAs stay real
Streamlit widgets (page_link / link_button) so navigation keeps working on
Streamlit Cloud, which serves the app inside an iframe where plain anchors
resolve to the wrong URL; everything else is static HTML.
"""
from __future__ import annotations

import streamlit as st

from app.config import APP_NAME, DISCLAIMER_TEXT

ASCI_URL = "https://www.ascionline.in/the-asci-code/"

_CREAM = "#F9F3EC"
_BLUSH = "#EDD9CF"
_INK = "#1A1A1A"
_RED = "#C0463A"
_MUSTARD = "#C9982E"
_GREEN = "#4A7A52"

_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Gelasio:ital,wght@0,400;0,700;1,400&display=swap');

[data-testid="stHeader"], [data-testid="stDecoration"], [data-testid="stToolbar"] {{ display: none !important; }}
[data-testid="stAppViewContainer"], [data-testid="stMain"], .stApp {{ background: {_CREAM} !important; }}
[data-testid="stMainBlockContainer"], .block-container {{ padding: 0 !important; max-width: 100% !important; }}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {{ gap: 0 !important; }}

.st-key-hero {{ max-width: 1100px; width: 100%; margin: 0 auto; padding: 72px 48px 64px; box-sizing: border-box; gap: 0 !important; }}
.st-key-hero [data-testid="stVerticalBlock"] {{ gap: 0 !important; }}
.st-key-hero [data-testid="stHorizontalBlock"] {{ align-items: flex-start; }}

[data-testid="stPageLink-NavLink"] {{
    background: {_INK}; border-radius: 0; padding: 14px 24px; justify-content: center;
    display: inline-flex; width: auto; transition: background 0.12s ease;
}}
[data-testid="stPageLink-NavLink"]:hover {{ background: #3A3A3A; }}
[data-testid="stPageLink-NavLink"] * {{ color: #FFFFFF !important; font-size: 14px !important; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif !important; }}
[data-testid="stLinkButton"] a {{
    background: transparent; color: {_INK}; border: 1px solid {_INK}; border-radius: 0;
    padding: 14px 24px; min-height: 0; font-size: 14px; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    transition: background 0.12s ease;
}}
[data-testid="stLinkButton"] {{ margin-left: 14px; }}
[data-testid="stPageLink"], [data-testid="stLinkButton"] {{ height: 48px; }}
[data-testid="stLinkButton"] a, [data-testid="stPageLink-NavLink"] {{ line-height: 1.2; min-height: 48px; align-items: center; }}
[data-testid="stLinkButton"] a:hover {{ background: rgba(26, 26, 26, 0.06); border-color: {_INK}; color: {_INK}; }}
[data-testid="stLinkButton"] a * {{ color: {_INK} !important; font-size: 14px !important; }}

.hc, .hc * {{ box-sizing: border-box; }}
.hc {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; color: {_INK}; }}
.hc-serif {{ font-family: Georgia, "Gelasio", "Times New Roman", serif; }}

.hc-pill {{
    display: inline-block; border: 1px solid {_INK}; border-radius: 999px; padding: 7px 16px;
    font-size: 11.5px; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 30px;
}}
.hc h1.hc-h1 {{ font-family: Georgia, "Gelasio", "Times New Roman", serif !important; font-weight: 700 !important; font-size: 68px !important; line-height: 1 !important; letter-spacing: -0.01em !important; margin: 0 0 22px !important; padding: 0 !important; color: {_INK} !important; }}
.hc .hc-tagline {{ font-family: Georgia, "Gelasio", "Times New Roman", serif; font-style: italic; font-size: 25px; margin: 0 0 24px; }}
.hc p.hc-lede {{ font-size: 16px !important; line-height: 1.75 !important; color: #333 !important; max-width: 430px; margin: 0 0 20px !important; }}
.hc p.hc-note {{ font-size: 12.5px !important; line-height: 1.5 !important; color: #7A726B !important; max-width: 430px; margin: 0 0 30px !important; }}

.hc-cards {{ position: relative; width: 100%; max-width: 380px; height: 330px; margin-left: auto; }}
.hc-card {{
    position: absolute; width: 215px; height: 140px; border-radius: 5px; padding: 24px 22px;
    font-family: Georgia, "Gelasio", "Times New Roman", serif; font-size: 13px; letter-spacing: 0.16em; text-transform: uppercase;
}}
.hc-card--red {{ background: {_RED}; color: #FBEDE6; left: 20px; top: 0; transform: rotate(-4.5deg); }}
.hc-card--mustard {{ background: {_MUSTARD}; color: #3B2B0B; left: 150px; top: 72px; transform: rotate(3deg); }}
.hc-card--green {{ background: {_GREEN}; color: #EAF1EA; left: 0; top: 168px; transform: rotate(-3deg); }}

.hc-hero-rule {{ height: 1px; background: #CFC7BE; margin: 64px 0 0; }}

.hc-band {{ width: 100%; padding: 76px 0 84px; }}
.hc-band--blush {{ background: {_BLUSH}; }}
.hc-band--cream {{ background: {_CREAM}; }}
.hc-inner {{ max-width: 1100px; margin: 0 auto; padding: 0 48px; }}
.hc-eyebrow {{ font-size: 11.5px; letter-spacing: 0.16em; text-transform: uppercase; color: #6E655E; margin-bottom: 40px; }}

.hc-steps {{ display: grid; grid-template-columns: repeat(3, 1fr); }}
.hc-step {{ padding: 4px 30px 4px; border-left: 1px solid #CDBBB0; }}
.hc-step:first-child {{ padding-left: 0; border-left: none; }}
.hc-num {{ font-family: Georgia, "Gelasio", "Times New Roman", serif; font-size: 40px; color: #9C918A; line-height: 1; margin-bottom: 22px; }}
.hc-icon {{ display: block; margin-bottom: 20px; }}
.hc-step-title {{ font-weight: 700; font-size: 16px; margin-bottom: 10px; }}
.hc-step p {{ font-size: 13.5px; line-height: 1.65; color: #5B524B; margin: 0; max-width: 270px; }}

.hc-trail {{ position: relative; display: grid; grid-template-columns: repeat(4, 1fr); margin-top: 8px; }}
.hc-trail-line {{ position: absolute; top: 5px; left: 7%; right: 7%; height: 1px; background: #CFC7BE; }}
.hc-trail-item {{ text-align: center; padding: 0 14px; }}
.hc-dot {{ display: block; width: 11px; height: 11px; border-radius: 50%; background: {_INK}; margin: 0 auto 22px; position: relative; z-index: 1; }}
.hc-trail-label {{ font-size: 12px; letter-spacing: 0.14em; text-transform: uppercase; color: #333; margin-bottom: 8px; }}
.hc-trail-item p {{ font-size: 13px; line-height: 1.55; color: #5B524B; margin: 0 auto; max-width: 220px; }}

.hc-sample {{ background: #FAF4EE; border: 1px solid {_INK}; padding: 40px 40px 34px; }}
.hc-sample-top {{ display: flex; gap: 48px; flex-wrap: wrap; margin-bottom: 28px; }}
.hc-mini {{ font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: #6E655E; margin-bottom: 8px; }}
.hc-status {{ font-family: Georgia, "Gelasio", "Times New Roman", serif; font-size: 25px; color: {_MUSTARD}; line-height: 1.1; }}
.hc-score {{ font-family: Georgia, "Gelasio", "Times New Roman", serif; font-size: 23px; line-height: 1.2; }}
.hc-chips {{ display: flex; flex-wrap: wrap; gap: 10px; }}
.hc-chip {{ display: inline-flex; align-items: center; gap: 9px; border: 1px solid #D8CCC0; background: #FBF7F2; padding: 8px 14px; font-size: 12.5px; }}
.hc-chip i {{ width: 7px; height: 7px; border-radius: 50%; display: inline-block; }}
.hc-chip i.g {{ background: {_GREEN}; }}
.hc-chip i.r {{ background: {_RED}; }}
.hc-chip i.m {{ background: {_MUSTARD}; }}
.hc-sample-rule {{ height: 1px; background: #E0D5CA; margin: 30px 0 24px; }}
.hc-flag-label {{ font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: {_RED}; margin-bottom: 10px; }}
.hc-flag-quote {{ font-size: 15px; margin-bottom: 8px; }}
.hc-flag-meta {{ font-size: 13px; color: #5B524B; line-height: 1.6; }}
.hc-fig {{ text-align: center; font-size: 10.5px; letter-spacing: 0.16em; text-transform: uppercase; color: #7A6D65; margin-top: 22px; }}

.hc-honest {{ display: grid; grid-template-columns: 1fr 1fr; }}
.hc-honest > div {{ padding-right: 48px; }}
.hc-honest > div + div {{ padding-left: 48px; padding-right: 0; border-left: 1px solid #CFC7BE; }}
.hc-honest-label {{ font-size: 11.5px; letter-spacing: 0.14em; text-transform: uppercase; color: #555; margin-bottom: 10px; }}
.hc-honest p {{ font-size: 14px; line-height: 1.7; color: #4A423C; margin: 0; max-width: 400px; }}

.hc-footer {{ max-width: 1170px; margin: 70px auto 0; border-top: 1px solid #CFC7BE; padding: 30px 48px 70px; text-align: center; font-size: 12px; line-height: 1.6; color: #7A726B; }}

@media (max-width: 820px) {{
    .st-key-hero {{ padding: 48px 24px 0; }}
    .hc h1.hc-h1 {{ font-size: 48px !important; }}
    .hc-cards {{ margin: 32px 0 0; }}
    .hc-inner {{ padding: 0 24px; }}
    .hc-steps {{ grid-template-columns: 1fr; }}
    .hc-step, .hc-step:first-child {{ border-left: none; border-top: 1px solid #CDBBB0; padding: 24px 0; }}
    .hc-step:first-child {{ border-top: none; }}
    .hc-trail {{ grid-template-columns: 1fr 1fr; row-gap: 30px; }}
    .hc-trail-line {{ display: none; }}
    .hc-sample {{ padding: 28px 22px; }}
    .hc-honest {{ grid-template-columns: 1fr; }}
    .hc-honest > div, .hc-honest > div + div {{ padding: 0; border-left: none; }}
    .hc-honest > div + div {{ margin-top: 32px; }}
    .hc-footer {{ padding: 28px 24px 56px; }}
}}
@media (max-width: 640px) {{
    .hc h1.hc-h1 {{ font-size: 38px !important; }}
    .hc .hc-tagline {{ font-size: 21px; }}
    [data-testid="stLinkButton"] {{ margin-left: 0; margin-top: 12px; }}
}}
"""

_ICON = (
    '<svg class="hc-icon" viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="#1A1A1A" '
    'stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">{}</svg>'
)
_ICON_DOC = _ICON.format('<path d="M6 3h9l3 3v15H6z"/><path d="M9 11h6M9 14h6M9 17h4"/>')
_ICON_LIST = _ICON.format(
    '<circle cx="5" cy="7" r="1.2"/><circle cx="5" cy="12" r="1.2"/><circle cx="5" cy="17" r="1.2"/>'
    '<path d="M9 7h11M9 12h11M9 17h11"/>'
)
_ICON_CHAT = _ICON.format('<path d="M4 5h16v11H11l-4 4v-4H4z"/>')
_ICON_WAVE = _ICON.format('<path d="M5 9v6M9 5v14M13 8v8M17 4v16M21 10v4"/>')
_ICON_BOOK = _ICON.format(
    '<path d="M3 5h7a2 2 0 0 1 2 2v13a2 2 0 0 0-2-2H3z"/><path d="M21 5h-7a2 2 0 0 0-2 2v13a2 2 0 0 1 2-2h7z"/>'
)


def _compact(html: str) -> str:
    """Collapse to one line with no blank lines or indentation. Markdown treats
    indented lines as code blocks and blank lines as the end of an HTML block,
    either of which would break a multi-line HTML string."""
    return " ".join(line.strip() for line in html.splitlines() if line.strip())


def inject_landing_css() -> None:
    st.markdown(f"<style>{_compact(_CSS)}</style>", unsafe_allow_html=True)


def hero_text_html() -> str:
    return _compact(
        f"""
        <div class="hc">
        <div class="hc-pill">{APP_NAME} · India · ASCI + CCPA + Consumer Protection</div>
        <h1 class="hc-h1">{APP_NAME}</h1>
        <div class="hc-tagline">Before it goes live, someone should check it.</div>
        <p class="hc-lede">Every influencer post gets checked for creativity and brand fit. It almost never gets
        checked for legal risk. {APP_NAME} reads the contract, the brief and the content together and flags what is
        at risk, citing the provision behind each flag.</p>
        <p class="hc-note">{DISCLAIMER_TEXT}</p>
        </div>
        """
    )


def hero_cards_html() -> str:
    return _compact(
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


def sections_html() -> str:
    return _compact(
        f"""
        <div class="hc">
        <section class="hc-band hc-band--blush"><div class="hc-inner">
        <div class="hc-eyebrow">How it works</div>
        <div class="hc-steps">
        <div class="hc-step"><div class="hc-num">01</div>{_ICON_DOC}<div class="hc-step-title">Contract</div>
        <p>Upload the influencer agreement. We pull every content restriction: medical claims, competitor mentions,
        disclosure duties.</p></div>
        <div class="hc-step"><div class="hc-num">02</div>{_ICON_LIST}<div class="hc-step-title">Campaign brief</div>
        <p>Brand, product, audience and the claims the brand wants made, plus the evidence that backs them.</p></div>
        <div class="hc-step"><div class="hc-num">03</div>{_ICON_CHAT}<div class="hc-step-title">The content</div>
        <p>The caption, transcript or screenshot. The real words about to go live.</p></div>
        </div></div></section>

        <section class="hc-band hc-band--cream"><div class="hc-inner">
        <div class="hc-eyebrow">Why am I being flagged</div>
        <div class="hc-trail"><div class="hc-trail-line"></div>
        <div class="hc-trail-item"><span class="hc-dot"></span><div class="hc-trail-label">Evidence</div>
        <p>The exact quote that triggered the flag.</p></div>
        <div class="hc-trail-item"><span class="hc-dot"></span><div class="hc-trail-label">Legal basis</div>
        <p>The provision retrieved from the source text.</p></div>
        <div class="hc-trail-item"><span class="hc-dot"></span><div class="hc-trail-label">Risk level</div>
        <p>High, medium or low, from a fixed scoring rule.</p></div>
        <div class="hc-trail-item"><span class="hc-dot"></span><div class="hc-trail-label">Suggested fix</div>
        <p>A lower-risk rewrite, or the next action to take.</p></div>
        </div></div></section>

        <section class="hc-band hc-band--blush"><div class="hc-inner">
        <div class="hc-eyebrow">What you get</div>
        <div class="hc-sample">
        <div class="hc-sample-top">
        <div><div class="hc-mini">Overall status</div><div class="hc-status">Needs revision</div></div>
        <div><div class="hc-mini">Compliance score</div><div class="hc-score">62 / 100</div></div>
        </div>
        <div class="hc-chips">
        <span class="hc-chip"><i class="g"></i>Advertising Disclosure</span>
        <span class="hc-chip"><i class="r"></i>ClaimCheck</span>
        <span class="hc-chip"><i class="m"></i>Contract Compliance</span>
        <span class="hc-chip"><i class="g"></i>Consumer Protection</span>
        <span class="hc-chip"><i class="g"></i>Comparative Advertising</span>
        <span class="hc-chip"><i class="m"></i>Music Licensing</span>
        </div>
        <div class="hc-sample-rule"></div>
        <div class="hc-flag-label">High · ClaimCheck</div>
        <div class="hc-flag-quote">&quot;Clinically proven to remove pigmentation in 7 days&quot;</div>
        <div class="hc-flag-meta">ASCI Code, Chapter I, Truthful and Honest Representation (1.1). Suggested fix: soften
        to a cosmetic claim, since no clinical-trial evidence is on file.</div>
        </div>
        <div class="hc-fig">Fig. 1, sample output</div>
        </div></section>

        <section class="hc-band hc-band--cream" style="padding-bottom: 0;"><div class="hc-inner">
        <div class="hc-eyebrow">What this honestly does, and does not do</div>
        <div class="hc-honest">
        <div>{_ICON_WAVE}<div class="hc-honest-label">Music licensing</div>
        <p>Identifies a track playing in your audio. Identification is not clearance: the dashboard says what rights
        still need confirming.</p></div>
        <div>{_ICON_BOOK}<div class="hc-honest-label">Legal grounding</div>
        <p>Every flag cites a provision retrieved from the source text. If nothing relevant comes back, it says so
        instead of inventing one.</p></div>
        </div></div></section>

        <div class="hc-footer">India only. A pre-publication screening aid for a human legal or compliance reviewer,
        not a guarantee of compliance.</div>
        </div>
        """
    )
