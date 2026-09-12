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

from app.config import COLOR_COBALT, COLOR_INK, RISK_COLOR_HEX, RISK_EMOJI

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-weight: 700 !important;
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
    border-radius: 4px;
}}
</style>
"""


def inject_brand_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def risk_border_css(risk: str) -> str:
    """Inline style string for a left-border accent in the exact brand hex for
    this severity, to wrap around an issue card's own markdown block."""
    color = RISK_COLOR_HEX.get(risk, RISK_COLOR_HEX["LOW"])
    return f"border-left:4px solid {color};padding-left:12px;"


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
