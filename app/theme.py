"""HYPECHECK brand theme for Streamlit (HYPECHECK_SPEC.md Section 5).

Streamlit's own theming (.streamlit/config.toml) sets the base palette and
font family; this module injects the two Google Fonts (Fraunces for
headlines, IBM Plex Sans for body/UI text) that config.toml can't specify on
its own, plus small CSS tweaks (status-color alert borders) that only CSS can
reach. Kept deliberately light -- this is a CSS/typography port onto the
existing Streamlit app, not a rebuild of the illustrated design system in the
spec (that's a from-scratch Next.js build, out of scope here).
"""
from __future__ import annotations

import streamlit as st

from app.config import (
    COLOR_COBALT,
    COLOR_INK,
    RISK_COLOR_HEX,
    RISK_EMOJI,
    RISK_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
)

# Overall-status strings (app/scoring.py) mapped to the risk severity whose
# color they should borrow -- so "HIGH RISK" reads the same red as a HIGH
# issue, etc.
_STATUS_RISK = {
    "HIGH RISK": RISK_HIGH,
    "NEEDS REVISION": RISK_MEDIUM,
    "POST APPROVED": RISK_LOW,
    "APPROVED": RISK_LOW,
}

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em;
}}
html, body, [class*="css"], .stMarkdown, .stTextInput, .stTextArea, .stButton {{
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
}}
[data-testid="stMetricValue"] {{
    font-family: 'Fraunces', Georgia, serif !important;
}}
a {{ color: {COLOR_COBALT} !important; }}

/* A neutral ink left-border on every Streamlit alert box (the disclaimer
   banner, warnings, errors); per-issue severity color is applied inline via
   risk_border_css() instead, since Streamlit gives every stAlert the same
   class regardless of content. */
[data-testid="stAlert"] {{
    border-left: 4px solid {COLOR_INK};
    border-radius: 6px;
    box-shadow: 0 1px 2px rgba(27, 24, 18, 0.06);
}}

/* Primary buttons: a touch of depth + a gentle lift on hover, instead of the
   flat default. Secondary/link buttons get a matching but quieter hover. */
.stButton > button[kind="primary"], .stButton > button[kind="primaryFormSubmit"] {{
    box-shadow: 0 2px 6px rgba(44, 74, 158, 0.25);
    transition: transform 0.12s ease, box-shadow 0.12s ease;
    border: none;
}}
.stButton > button[kind="primary"]:hover, .stButton > button[kind="primaryFormSubmit"]:hover {{
    transform: translateY(-1px);
    box-shadow: 0 4px 10px rgba(44, 74, 158, 0.32);
}}
.stButton > button[kind="secondary"], .stLinkButton > a {{
    transition: transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
}}
.stButton > button[kind="secondary"]:hover, .stLinkButton > a:hover {{
    transform: translateY(-1px);
    border-color: {COLOR_COBALT} !important;
    box-shadow: 0 2px 6px rgba(27, 24, 18, 0.1);
}}

/* Expanders (used for issue cards, scoring rule, sample flags): give them
   the same card depth as everything else instead of a flat outline. */
[data-testid="stExpander"] {{
    border-radius: 8px !important;
    box-shadow: 0 1px 3px rgba(27, 24, 18, 0.07);
}}

.hc-card {{
    background: #FBF8F1;
    border: 1px solid #E3D9C3;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(27, 24, 18, 0.06);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}}
.hc-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(27, 24, 18, 0.1);
}}

/* Category-breakdown badge cards, used on both the landing page's sample
   dashboard and the real Run Review dashboard. */
.cat-card {{
    background: #FBF8F1; border: 1px solid #E3D9C3; border-radius: 8px;
    padding: 12px 14px; text-align: center; height: 100%;
    box-shadow: 0 1px 3px rgba(27, 24, 18, 0.06);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}}
.cat-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(27, 24, 18, 0.1);
}}
.cat-card .cat-label {{
    font-size: 0.82rem; font-weight: 600; color: {COLOR_INK};
    display: block; margin-bottom: 8px; min-height: 2.2em;
}}

/* Thin brand-gradient rule used in place of plain st.divider(). */
.hero-rule {{
    height: 3px; width: 64px; border-radius: 999px;
    background: linear-gradient(90deg, {COLOR_COBALT}, #D9A125);
    margin: 28px 0 32px;
}}

/* Headline status+score summary (replaces two cramped st.metric() boxes,
   which truncate long status text like "NEEDS REVISION" in a narrow
   column). One wide card, natural-width HTML instead of a fixed-size
   widget, so nothing ever clips. */
.summary-card {{
    background: #FBF8F1; border: 1px solid #E3D9C3; border-radius: 10px;
    padding: 20px 26px; box-shadow: 0 1px 3px rgba(27, 24, 18, 0.06);
    display: flex; align-items: center; gap: 40px; flex-wrap: wrap;
}}
.summary-eyebrow {{
    font-size: 0.75rem; font-weight: 600; color: #8A8068;
    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;
}}
.summary-score {{
    font-family: 'Fraunces', Georgia, serif; font-weight: 700;
    font-size: 2.1rem; color: {COLOR_INK}; line-height: 1;
}}
.summary-score span {{
    font-family: 'IBM Plex Sans', system-ui, sans-serif; font-weight: 500;
    font-size: 1.05rem; color: #8A8068;
}}
</style>
"""


def inject_brand_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def risk_border_css(risk: str) -> str:
    """Inline style string for a left-border accent in the exact brand hex for
    this severity. NOTE: only safe to use on a single st.markdown() call's own
    HTML -- an opening <div> in one st.markdown() and its closing </div> in a
    later, separate st.markdown() call do NOT nest (each call is its own
    isolated DOM fragment in Streamlit), so this cannot wrap multiple widgets.
    To wrap real widgets (st.code, st.write, st.columns, ...) in a colored
    border, use risk_container_style() + st.container(key=...) instead."""
    color = RISK_COLOR_HEX.get(risk, RISK_COLOR_HEX["LOW"])
    return f"border-left:4px solid {color};padding-left:12px;"


def risk_container_style(key: str, risk: str) -> str:
    """A <style> block that gives an st.container(key=key) a left-border
    accent in this severity's brand color, via the stable `st-key-<key>` CSS
    class Streamlit attaches to keyed containers. Render this markdown BEFORE
    opening the `with st.container(border=True, key=key):` block it targets."""
    color = RISK_COLOR_HEX.get(risk, RISK_COLOR_HEX["LOW"])
    return (
        f"<style>.st-key-{key} {{ border-left: 4px solid {color} !important; "
        f"border-radius: 8px; }}</style>"
    )


def risk_badge_html(risk: str, label: str | None = None) -> str:
    """A status pill in the exact brand hex for this severity, with the
    plain-language label inside it -- never color alone conveys risk."""
    color = RISK_COLOR_HEX.get(risk, RISK_COLOR_HEX["LOW"])
    text = label if label is not None else risk
    return (
        f'<span style="background:{color};color:#FBF7EF;padding:2px 10px;'
        f'border-radius:4px;font-weight:600;font-size:0.85em;">'
        f"{RISK_EMOJI.get(risk, '')} {text}</span>"
    )


def status_summary_html(status: str, status_emoji: str, score: int) -> str:
    """The headline overall-status + compliance-score card. Natural-width
    HTML (not st.metric, which silently truncates a long status string like
    "NEEDS REVISION" in a narrow column) -- always renders in full."""
    risk = _STATUS_RISK.get(status.upper(), RISK_MEDIUM)
    color = RISK_COLOR_HEX.get(risk, RISK_COLOR_HEX["LOW"])
    status_pill = (
        f'<span style="background:{color};color:#FBF7EF;padding:6px 18px;'
        f'border-radius:6px;font-weight:700;font-size:1.3rem;display:inline-block;'
        f'white-space:nowrap;">{status_emoji} {status}</span>'
    )
    return (
        '<div class="summary-card">'
        '<div><div class="summary-eyebrow">Overall status</div>'
        f"{status_pill}</div>"
        '<div><div class="summary-eyebrow">Compliance score</div>'
        f'<div class="summary-score">{score} <span>/ 100</span></div></div>'
        "</div>"
    )
