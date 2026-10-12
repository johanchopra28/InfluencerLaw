"""The shared look of every HYPECHECK page.

Flat editorial style: cream and blush bands, Georgia display type, hairline
rules, square controls. Pages build on three pieces from here: base styles
(inject_site_css), a navigation strip (render_nav) and a header band
(page_head). Static HTML is built with compact() so Markdown does not treat
indentation or blank lines as code blocks or the end of an HTML block.
"""
from __future__ import annotations

import html
import os

import streamlit as st

from app.config import APP_NAME, DISCLAIMER_TEXT, RISK_COLOR_HEX
from app.config import GEMINI_API_KEY, GROQ_API_KEY
from app.llm import describe_failure
from app.privacy import SHORT_NOTICE, SHORT_TITLE

CREAM = "#F9F3EC"
BLUSH = "#EDD9CF"
INK = "#1A1A1A"
HAIR = "#CFC7BE"
RED = RISK_COLOR_HEX["HIGH"]
MUSTARD = RISK_COLOR_HEX["MEDIUM"]
GREEN = RISK_COLOR_HEX["LOW"]
SERIF = 'Georgia, "Gelasio", "Times New Roman", serif'
SANS = '"Helvetica Neue", Helvetica, Arial, sans-serif'
# Horizontal padding that centres content in a 1004px column but never goes below 48px.
PAD = "max(48px, calc((100% - 1004px) / 2))"

HOME_PATH = "app.py"
PRIVACY_PATH = "pages/4_Privacy.py"

SERVICES = {
    "contract": {
        "path": "pages/1_Contract_Check.py",
        "nav": "Contracts",
        "title": "Contract checks",
        "cta": "Check a Contract",
        "blurb": (
            "Review influencer agreements, brand contracts, usage rights, deliverables, "
            "exclusivity, payment terms and potentially problematic clauses."
        ),
    },
    "campaign": {
        "path": "pages/2_Campaign_Check.py",
        "nav": "Campaigns",
        "title": "Campaign checks",
        "cta": "Check a Campaign",
        "blurb": (
            "Assess campaign briefs, proposed deliverables, disclosures, brand claims, usage "
            "permissions and potential advertising or compliance risks."
        ),
    },
    "content": {
        "path": "pages/3_Content_Check.py",
        "nav": "Captions",
        "title": "Captions and content checks",
        "cta": "Check Content",
        "blurb": (
            "Review captions, posts, reels and other campaign content for disclosure gaps, "
            "potentially misleading claims and content-related compliance concerns."
        ),
    },
}

_ICON = (
    '<svg class="hc-icon" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" '
    'stroke="#1A1A1A" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
)
ICONS = {
    "doc": '<path d="M6 3h9l3 3v15H6z"/><path d="M9 11h6M9 14h6M9 17h4"/>',
    "list": (
        '<circle cx="5" cy="7" r="1.2"/><circle cx="5" cy="12" r="1.2"/><circle cx="5" cy="17" r="1.2"/>'
        '<path d="M9 7h11M9 12h11M9 17h11"/>'
    ),
    "chat": '<path d="M4 5h16v11H11l-4 4v-4H4z"/>',
}


def icon(name: str, size: int = 28) -> str:
    return _ICON.format(size=size, body=ICONS[name])


def compact(markup: str) -> str:
    """One line, no indentation, no blank lines (see module docstring)."""
    return " ".join(line.strip() for line in markup.splitlines() if line.strip())


def esc(text: str) -> str:
    """Escape model- or user-supplied text for inclusion in HTML, keeping line breaks."""
    return html.escape(text or "").replace("\n", "<br>")


_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Gelasio:ital,wght@0,400;0,700;1,400&display=swap');

[data-testid="stHeader"], [data-testid="stDecoration"], [data-testid="stToolbar"] { display: none !important; }
[data-testid="stAppViewContainer"], [data-testid="stMain"], .stApp { background: @CREAM@ !important; }
[data-testid="stMainBlockContainer"], .block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { gap: 0 !important; }
.stApp, .stApp input, .stApp textarea, .stApp button, .stApp label { font-family: @SANS@; color: @INK@; }

.st-key-nav { padding: 20px @PAD@; border-bottom: 1px solid @HAIR@; }
.st-key-nav [data-testid="stHorizontalBlock"] { align-items: center; }
.st-key-nav [data-testid="stPageLink-NavLink"] { background: transparent; padding: 6px 0; min-height: 0; border-radius: 0; }
.st-key-nav [data-testid="stPageLink-NavLink"] p { font-size: 12px; text-transform: uppercase; letter-spacing: 0.12em; color: #555; margin: 0; }
.st-key-nav [data-testid="stPageLink-NavLink"]:hover p { color: @INK@; }
[class*="st-key-navlink-"] [data-testid="stPageLink-NavLink"] { justify-content: flex-end; }
.st-key-navbrand [data-testid="stPageLink-NavLink"] p { font-family: @SERIF@; font-weight: 700; font-size: 22px; letter-spacing: 0.02em; text-transform: none; color: @INK@; }
.st-key-band-head { background: @BLUSH@; padding: 64px @PAD@ 56px; }
.st-key-body { padding: 56px @PAD@ 96px; }

.hc, .hc * { box-sizing: border-box; }
.hc { font-family: @SANS@; color: @INK@; }
.hc .hc-eyebrow { font-size: 11.5px; letter-spacing: 0.16em; text-transform: uppercase; color: #6E655E; margin-bottom: 18px; }
.hc h1.hc-h1 { font-family: @SERIF@ !important; font-weight: 700 !important; font-size: 48px !important; line-height: 1.05 !important; letter-spacing: -0.01em !important; margin: 0 0 18px !important; padding: 0 !important; color: @INK@ !important; }
.hc p.hc-lede { font-size: 16px !important; line-height: 1.75 !important; color: #333 !important; max-width: 640px; margin: 0 0 18px !important; }
.hc p.hc-note { font-size: 12.5px !important; line-height: 1.5 !important; color: #7A726B !important; max-width: 640px; margin: 0 !important; }
.hc ul.hc-needs { list-style: none; padding: 0; margin: 22px 0 22px; display: flex; flex-wrap: wrap; gap: 10px; }
.hc ul.hc-needs li { border: 1px solid #C9BBB0; background: rgba(251, 247, 242, 0.7); padding: 7px 14px; font-size: 12.5px; }
.hc .hc-mini { font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: #6E655E; margin-bottom: 8px; }
.hc h2.hc-h2 { font-family: @SERIF@ !important; font-weight: 700 !important; font-size: 24px !important; margin: 36px 0 12px !important; padding: 0 !important; color: @INK@ !important; }
.hc .hc-body { font-size: 14px; line-height: 1.65; color: #333; }
.hc .hc-small { font-size: 12.5px; line-height: 1.6; color: #6B625B; }
.hc .hc-quote { font-size: 15px; line-height: 1.5; }

.hc .hc-sample { background: #FAF4EE; border: 1px solid @INK@; padding: 36px 40px 32px; }
.hc .hc-sample-top { display: flex; gap: 48px; flex-wrap: wrap; margin-bottom: 26px; }
.hc .hc-status { font-family: @SERIF@; font-size: 25px; line-height: 1.1; }
.hc .hc-score { font-family: @SERIF@; font-size: 23px; line-height: 1.2; }
.hc .hc-chips { display: flex; flex-wrap: wrap; gap: 10px; }
.hc .hc-chip { display: inline-flex; align-items: center; gap: 9px; border: 1px solid #D8CCC0; background: #FBF7F2; padding: 8px 14px; font-size: 12.5px; }
.hc .hc-chip i { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
.hc .hc-fig { text-align: center; font-size: 10.5px; letter-spacing: 0.16em; text-transform: uppercase; color: #7A6D65; margin-top: 18px; }
.hc .hc-notice { border: 1px solid @HAIR@; background: #FBF7F2; padding: 14px 18px; font-size: 13.5px; line-height: 1.6; margin-top: 14px; }

[class*="st-key-flag-"] { border: 1px solid @INK@; background: #FAF4EE; padding: 28px 32px; margin-top: 18px; gap: 0 !important; }
.hc .hc-flag-label { font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 8px; }
.hc .hc-flag-title { font-family: @SERIF@; font-size: 21px; line-height: 1.25; margin-bottom: 4px; }
.hc .hc-field { margin-top: 18px; }
.hc .hc-lawyer { margin-top: 18px; font-size: 13px; font-weight: 700; }

.hc .hc-rewrite { border: 1px solid @HAIR@; background: #FBF7F2; padding: 22px 26px; margin-top: 14px; }
.hc .hc-rw-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
.hc .hc-rows { margin-top: 6px; }
.hc .hc-row { display: grid; grid-template-columns: 220px 1fr; gap: 24px; padding: 16px 0; border-top: 1px solid @HAIR@; }
.hc .hc-row:last-child { border-bottom: 1px solid @HAIR@; }
.hc .hc-row-topic { font-weight: 700; font-size: 14px; }
.hc .hc-row-status { display: block; margin-top: 4px; font-weight: 400; font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; color: #6E655E; }

.hc a { color: @INK@; text-decoration: underline; text-underline-offset: 3px; }
.hc .hc-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }
.hc .hc-tag { font-size: 10.5px; letter-spacing: 0.1em; text-transform: uppercase; border: 1px solid #9C918A; color: #5B524B; padding: 3px 9px; }
.hc .hc-tag--missing { border-color: @MUSTARD@; color: #8A6A1B; }
.hc .hc-tag--human { border-color: @RED@; color: @RED@; }
.hc .hc-result { font-family: @SERIF@; font-size: 22px; line-height: 1.35; margin-bottom: 14px; }
.hc .hc-counts { display: flex; gap: 22px; flex-wrap: wrap; margin-bottom: 22px; font-size: 13px; }
.hc .hc-counts i, .hc .hc-chip i.dot-none { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 7px; }
.hc .hc-chip i.dot-none { border: 1px solid #9C918A; background: transparent; margin-right: 0; }
.hc .hc-scope { margin: 6px 0 22px; padding-left: 18px; font-size: 13.5px; line-height: 1.65; color: #3E3731; }
.hc .hc-group { display: flex; align-items: baseline; gap: 14px; margin: 44px 0 4px; }
.hc .hc-group b { font-family: @SERIF@; font-size: 26px; font-weight: 700; }
.hc .hc-group span { font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: #6E655E; }
.hc .hc-criteria { margin-top: 18px; }
.hc .hc-criteria .hc-row { grid-template-columns: 170px 1fr; padding: 10px 0; }
.hc .hc-compare { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; }
.hc .hc-compare > div { border: 1px solid @HAIR@; background: #FBF7F2; padding: 20px 24px; }
.hc ins.hc-ins { background: #DCEBDD; text-decoration: none; padding: 0 2px; }
.hc del.hc-del { background: #F4DAD5; padding: 0 2px; }
.hc .hc-privacy { border: 1px solid @HAIR@; background: #FBF7F2; padding: 18px 22px; margin: 6px 0 14px; }
.hc .hc-privacy .hc-privacy-title { font-family: @SERIF@; font-weight: 700; font-size: 18px; margin-bottom: 8px; }
.st-key-privacy-link [data-testid="stPageLink-NavLink"] { background: transparent; padding: 0; min-height: 0; border-radius: 0; }
.st-key-privacy-link [data-testid="stPageLink-NavLink"] p { font-size: 13px; text-decoration: underline; text-underline-offset: 3px; margin: 0; }
[class*="st-key-field-err-"] { border-left: 3px solid @RED@; padding-left: 14px; }

.stButton > button, .stDownloadButton > button { border-radius: 0; box-shadow: none; padding: 12px 26px; min-height: 48px; transition: background 0.12s ease; }
.stButton > button p, .stDownloadButton > button p { font-size: 14px; margin: 0; }
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] { background: @INK@; border: 1px solid @INK@; }
.stButton > button[kind="primary"] p, .stButton > button[data-testid="stBaseButton-primary"] p { color: #FFFFFF !important; }
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover { background: #3A3A3A; border-color: #3A3A3A; }
.stButton > button[kind="secondary"], .stButton > button[data-testid="stBaseButton-secondary"], .stDownloadButton > button { background: transparent; border: 1px solid @INK@; }
.stButton > button[kind="secondary"]:hover, .stDownloadButton > button:hover { background: rgba(26, 26, 26, 0.06); border-color: @INK@; color: @INK@; }

[data-baseweb="input"], [data-baseweb="textarea"] { border-radius: 0 !important; border: 1px solid @HAIR@ !important; background: #FBF7F2 !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within { border-color: @INK@ !important; }
[data-baseweb="base-input"], [data-baseweb="input"] input, [data-baseweb="textarea"] textarea { background: transparent !important; border-radius: 0 !important; }
[data-testid="stWidgetLabel"] p { font-size: 13px; font-weight: 500; color: #444; }
[data-testid="stFileUploaderDropzone"] { background: #FBF7F2; border: 1px dashed #B9AD9F; border-radius: 0; }
[data-testid="stFileUploaderDropzone"] button { border-radius: 0; border: 1px solid @INK@; background: transparent; }
[data-testid="stFileUploaderDropzone"] button p { color: @INK@; }
[data-testid="stAlert"] { background: #FBF7F2; border: 1px solid @HAIR@; border-left: 3px solid @INK@; border-radius: 0; color: @INK@; }
[data-testid="stExpander"] { border: 1px solid @HAIR@; border-radius: 0; background: #FBF7F2; margin-top: 28px; }

@media (max-width: 820px) {
    .st-key-nav { padding: 16px 24px; }
    .st-key-band-head { padding: 44px 24px 40px; }
    .st-key-body { padding: 40px 24px 72px; }
    .hc h1.hc-h1 { font-size: 36px !important; }
    .hc .hc-sample { padding: 26px 22px; }
    [class*="st-key-flag-"] { padding: 22px 20px; }
    .hc .hc-rw-grid { grid-template-columns: 1fr; gap: 18px; }
    .hc .hc-row { grid-template-columns: 1fr; gap: 6px; }
}
"""


def inject_site_css(extra: str = "") -> None:
    """Base styles for every page. `extra` is page-specific CSS appended after."""
    css = _CSS
    for token, value in {
        "@CREAM@": CREAM, "@BLUSH@": BLUSH, "@INK@": INK, "@HAIR@": HAIR,
        "@SANS@": SANS, "@SERIF@": SERIF, "@PAD@": PAD, "@RED@": RED, "@MUSTARD@": MUSTARD,
    }.items():
        css = css.replace(token, value)
    st.markdown(f"<style>{compact(css + extra)}</style>", unsafe_allow_html=True)


def render_nav(active: str) -> None:
    """Top strip on tool pages: wordmark back to the landing page plus the three services."""
    rules = "".join(
        f".st-key-navlink-{key} [data-testid='stPageLink-NavLink'] {{ box-shadow: inset 0 -2px 0 {INK}; }}"
        f".st-key-navlink-{key} [data-testid='stPageLink-NavLink'] p {{ color: {INK} !important; }}"
        for key in SERVICES
        if key == active
    )
    st.markdown(f"<style>{rules}</style>", unsafe_allow_html=True)
    with st.container(key="nav"):
        cols = st.columns([3.2, 1, 1, 1], gap="small")
        with cols[0]:
            with st.container(key="navbrand"):
                st.page_link(HOME_PATH, label=APP_NAME)
        for col, (key, svc) in zip(cols[1:], SERVICES.items()):
            with col:
                with st.container(key=f"navlink-{key}"):
                    st.page_link(svc["path"], label=svc["nav"])


def page_head(eyebrow: str, title: str, blurb: str, needs: tuple[str, ...] = ()) -> None:
    """Blush header band: what this service does and what to have ready."""
    needs_html = (
        '<ul class="hc-needs">' + "".join(f"<li>{esc(n)}</li>" for n in needs) + "</ul>" if needs else ""
    )
    with st.container(key="band-head"):
        st.markdown(
            compact(
                f"""
                <div class="hc">
                <div class="hc-eyebrow">{esc(eyebrow)}</div>
                <h1 class="hc-h1">{esc(title)}</h1>
                <p class="hc-lede">{esc(blurb)}</p>
                {needs_html}
                <p class="hc-note">{esc(DISCLAIMER_TEXT)} High-risk or unclear findings should go to a qualified lawyer.</p>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )


def eyebrow(text: str) -> None:
    st.markdown(f'<div class="hc"><div class="hc-eyebrow">{esc(text)}</div></div>', unsafe_allow_html=True)


def notice(text: str) -> None:
    st.markdown(f'<div class="hc"><div class="hc-notice">{esc(text)}</div></div>', unsafe_allow_html=True)


def require_api_key() -> None:
    """Stop the page with a clear message if no analysis service is configured.
    Either a Gemini key or a Groq key is enough to run."""
    if not (GEMINI_API_KEY or GROQ_API_KEY):
        st.error(
            "No analysis service is configured. Copy .env.example to .env, add a free "
            "GEMINI_API_KEY from https://aistudio.google.com/apikey (and optionally a "
            "GROQ_API_KEY as a backup), and restart the app."
        )
        st.stop()


def privacy_notice() -> None:
    """The short privacy notice, shown beside every upload and before any submission."""
    st.markdown(
        compact(
            f"""
            <div class="hc"><div class="hc-privacy">
            <div class="hc-privacy-title">{esc(SHORT_TITLE)}</div>
            <div class="hc-body">{esc(SHORT_NOTICE)}</div>
            </div></div>
            """
        ),
        unsafe_allow_html=True,
    )
    with st.container(key="privacy-link"):
        st.page_link(PRIVACY_PATH, label="Read the full privacy notice")


def keep_state(*keys: str) -> None:
    """Keep widget values when the user visits another page and comes back.

    Streamlit drops a widget's state when its page is left. Assigning the value to
    its own key at the top of the page marks it as set through the session state
    API, which survives the page change. File uploads cannot be kept this way.
    """
    for key in keys:
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]


def reset_state(prefix: str) -> None:
    """Callback for "Run another check": forget results and form values for one service."""
    for key in [k for k in st.session_state.keys() if str(k).startswith(prefix)]:
        del st.session_state[key]
    st.session_state[f"gen-{prefix}"] = st.session_state.get(f"gen-{prefix}", 0) + 1


def upload_key(prefix: str, name: str) -> str:
    """Key for a file uploader. It changes on reset, because deleting an uploader's key
    does not clear the file the browser is already showing."""
    return f"{prefix}{name}_{st.session_state.get(f'gen-{prefix}', 0)}"


def field(name: str, errors: set[str]):
    """Container for one form field. When the field failed validation it gets a red edge,
    so the user can see which one needs attention."""
    return st.container(key=f"field-err-{name}" if name in errors else f"field-ok-{name}")


def field_message(name: str, errors: dict[str, str]) -> None:
    """The specific message for a field that failed validation, placed right under it."""
    if name in errors:
        st.markdown(
            f'<div class="hc"><div class="hc-small" style="color:{RED};margin-top:6px">{esc(errors[name])}</div></div>',
            unsafe_allow_html=True,
        )


ANALYSIS_FAILED = (
    "The review could not be completed. This is usually a temporary problem with the analysis "
    "service, so trying again often works. Everything you entered is still on this page."
)


def form_errors(prefix: str) -> dict[str, str]:
    """Validation messages from the last submit, keyed by field name."""
    return st.session_state.get(f"{prefix}errors", {})


def gate(prefix: str, triggered: bool, validate) -> bool:
    """Decide whether a submit may run the analysis.

    validate() returns {field name: message} for required information that is
    missing. If anything is missing the page reruns with that field marked and
    explained. When the user has fixed the fields, the page reruns once more so
    the marks clear before the analysis starts. Returns True when it is time to run.
    """
    errors_key, go_key = f"{prefix}errors", f"{prefix}go"
    previous = st.session_state.get(errors_key, {})
    go = st.session_state.pop(go_key, False)
    if not (triggered or go):
        return False
    errors = validate()
    if errors:
        st.session_state[errors_key] = errors
        st.rerun()
    if previous:
        st.session_state[errors_key] = {}
        st.session_state[go_key] = True
        st.rerun()
    return True


def fail_field(prefix: str, name: str, message: str) -> None:
    """Mark one field as the problem (for example an unreadable file) and rerun."""
    st.session_state[f"{prefix}errors"] = {name: message}
    st.rerun()


def note_failure(prefix: str, exc: Exception) -> None:
    """Remember that the analysis failed and why, so the page can say what happened."""
    st.session_state[f"{prefix}failed"] = True
    st.session_state[f"{prefix}failed_reason"] = describe_failure(exc)


def failure_panel(prefix: str) -> bool:
    """Shown after a failed analysis. Returns True when the user clicks Try again."""
    if not st.session_state.get(f"{prefix}failed"):
        return False
    reason = st.session_state.get(f"{prefix}failed_reason") or ANALYSIS_FAILED
    st.error(f"{reason} Everything you entered is still on this page.")
    return st.button("Try again", key=f"{prefix}retry")
