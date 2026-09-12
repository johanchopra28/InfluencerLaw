"""HYPECHECK - marketing/landing page (entry point).

The actual review tool lives at pages/1_Run_Review.py, reached via the
sidebar or the "Run a review" button below. Run with:
    streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from app.config import APP_NAME, DISCLAIMER_TEXT
from app.theme import inject_brand_css, risk_badge_html

st.set_page_config(
    page_title=f"{APP_NAME} - Pre-Publication Legal Review",
    page_icon="⚖️",
    layout="wide",
)
inject_brand_css()

st.markdown(
    """
    <style>
    .hero-badge {
        display: inline-block; background: #E4E9F5; color: #2C4A9E;
        border-radius: 999px; padding: 4px 14px; font-size: 0.85rem;
        font-weight: 600; margin-bottom: 14px;
    }
    .step-card {
        background: #FBF8F1; border: 1px solid #E3D9C3; border-radius: 8px;
        padding: 18px; height: 100%; color: #1B1812;
    }
    .step-card b { color: #1B1812; }
    .trail-step {
        border-left: 3px solid #2C4A9E; padding-left: 12px; margin-bottom: 10px;
    }
    .scope-card {
        background: #FBF1DC; border: 1px solid #D9A125; border-radius: 8px;
        padding: 16px 20px; color: #4A3C0E;
    }
    .scope-card b { color: #332800; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- Hero
st.markdown(f'<span class="hero-badge">⚖️ {APP_NAME} · India · ASCI + CCPA + Consumer Protection</span>', unsafe_allow_html=True)
st.markdown(f"# {APP_NAME}")
st.markdown(
    "#### *Before it goes live, someone should check it.*"
)
st.write(
    "Every influencer post ships through a creative review, a brand-fit review, sometimes "
    f"a PR review. It almost never ships through a **legal** review. {APP_NAME} cross-references "
    "the contract, the campaign brief, and the actual content *before* publication, and flags "
    "exactly what's at risk, citing the specific legal provision each time."
)
st.caption(f"🔒 {DISCLAIMER_TEXT}")

col_cta1, col_cta2, _ = st.columns([1, 1, 3])
with col_cta1:
    if st.button("🚀 Run a review", type="primary", use_container_width=True):
        st.switch_page("pages/1_Run_Review.py")
with col_cta2:
    st.link_button("Read the ASCI Code ↗", "https://www.ascionline.in/the-asci-code/", use_container_width=True)

st.divider()

# ---------------------------------------------------------------- How it works
st.header("How it works")
st.write("Three inputs in → cross-referenced against real legal text → a risk dashboard out.")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        '<div class="step-card">📄<br><b>1. Contract</b><br>'
        "Upload the influencer agreement (PDF/DOCX). We extract every content "
        "restriction — no medical claims, no competitor mentions, disclosure "
        "obligations, exclusivity terms.</div>",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        '<div class="step-card">🧾<br><b>2. Campaign brief</b><br>'
        "Brand, product, objective, audience, and the claims the brand wants "
        "communicated — plus whatever evidence actually backs them.</div>",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        '<div class="step-card">📱<br><b>3. The actual content</b><br>'
        "Caption, transcript, or a screenshot of the post/reel — the words that "
        "are actually about to go live.</div>",
        unsafe_allow_html=True,
    )

st.write("")
st.subheader("Why am I being flagged? Every issue shows its full trail.")
st.write(
    "This is the difference between a real compliance tool and ChatGPT wrapped in a "
    "checklist: nothing is asserted without showing its work — and nothing is ever stated "
    "as a definitive legal conclusion. Every flag says what provision is potentially "
    "implicated and why, and recommends review by a qualified lawyer."
)

t1, t2, t3, t4 = st.columns(4)
for col, label, desc in [
    (t1, "🔍 Evidence", "The exact quote from the content that triggered the flag."),
    (t2, "📚 Legal basis", "The actual statutory/guideline provision retrieved — never invented."),
    (t3, "🚦 Risk level", "HIGH / MEDIUM / LOW, from a visible, fixed scoring rule."),
    (t4, "✏️ Suggested fix", "A rewritten, lower-risk version — or the next action to take."),
]:
    with col:
        st.markdown(f'<div class="trail-step"><b>{label}</b><br>{desc}</div>', unsafe_allow_html=True)

st.caption(
    "If no relevant provision is retrieved for a check, the tool says so explicitly instead "
    "of fabricating a citation."
)

st.divider()

# ---------------------------------------------------------------- Sample dashboard
st.header("What you get: the compliance dashboard")
st.caption("A real shape of the output — run your own campaign above to generate this from scratch.")
st.warning(DISCLAIMER_TEXT, icon="⚖️")

d1, d2, d3 = st.columns([1, 1, 2])
with d1:
    st.metric("Overall status", "🟡 NEEDS REVISION")
with d2:
    st.metric("Compliance score", "62 / 100")
with d3:
    with st.expander("Scoring rule (not a black box)"):
        st.write(
            "Start at 100. Subtract per flagged issue: HIGH -25, MEDIUM -10, LOW -3. "
            "Floors at 0. Status is HIGH RISK if any HIGH issue exists, NEEDS REVISION if any "
            "MEDIUM issue exists, otherwise POST APPROVED."
        )

sample_categories = [
    ("Advertising Disclosure", "LOW"),
    ("ClaimCheck (Substantiation)", "HIGH"),
    ("Contract Compliance", "MEDIUM"),
    ("Consumer Protection & E-Commerce", "LOW"),
    ("Comparative Advertising", "LOW"),
    ("Music Licensing", "MEDIUM"),
]
cat_cols = st.columns(len(sample_categories))
for col, (label, risk) in zip(cat_cols, sample_categories):
    with col:
        st.markdown(f"**{label}**")
        st.markdown(risk_badge_html(risk), unsafe_allow_html=True)

with st.expander("[ClaimCheck] Unsubstantiated claim: “Clinically proven to remove pigmentation in 7 days” — sample"):
    st.markdown("**Evidence**")
    st.code("Clinically proven to remove pigmentation in 7 days", language=None)
    st.markdown("**Legal basis**")
    st.write("*ASCI Code — Chapter I — Truthful & Honest Representation (1.1)*")
    st.caption(
        "Advertisements must be truthful. All descriptions, claims and comparisons, which "
        "relate to matters of objectively ascertainable fact, should be capable of "
        "substantiation."
    )
    st.markdown("**Risk level**")
    st.markdown(risk_badge_html("HIGH"), unsafe_allow_html=True)
    st.markdown("**⚠ Consult a lawyer before publishing this.**")
    st.markdown("**Suggested fix**")
    st.write("“Visibly reduces the look of pigmentation with regular use” — softened from a medical/efficacy claim to a cosmetic-effect claim, since the brief has no clinical trial evidence on file.")

st.divider()

# ---------------------------------------------------------------- Scope honesty
st.header("What this tool honestly does — and doesn't — do")
st.markdown(
    f"""
    <div class="scope-card">
    <b>🎵 Music licensing:</b> we identify a track playing in your audio using AudD's audio
    fingerprinting — genuinely useful, since it replaces manually Shazam-ing a reel. But
    identification is not clearance. If a track is found, the dashboard says exactly that —
    <i>"Track identified: [artist – title]. Commercial usage rights not verified — confirm
    licensing before publication"</i> — and gives you a signable deferral document for your
    legal team. It never shows a fake "cleared ✅".
    <br><br>
    <b>⚖️ Legal grounding:</b> every flag cites a provision retrieved from the actual ASCI Code,
    ASCI's Influencer Advertising Guidelines, the CCPA Misleading Advertisement Guidelines 2022,
    the Consumer Protection Act 2019, and the Consumer Protection (E-Commerce) Rules 2020 — not
    the model's parametric memory. If nothing relevant is retrieved, the tool says so instead of
    inventing a citation.
    <br><br>
    <b>🇮🇳 Scope:</b> India only, and only the source documents above. {APP_NAME} is a
    pre-publication risk-<i>flagging</i> aid for a human legal/compliance reviewer — not legal
    advice, and not a guarantee of compliance. {DISCLAIMER_TEXT}
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")
if st.button("🚀 Run a review now", type="primary"):
    st.switch_page("pages/1_Run_Review.py")
