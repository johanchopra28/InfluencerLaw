"""InfluencerLaw - Pre-Publication Legal Review Engine (India).

Streamlit app shell + dashboard. Run with:
    streamlit run app.py
"""
from __future__ import annotations

import os

import streamlit as st

# Load .env before importing anything that reads ANTHROPIC_API_KEY at import time.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from app.config import MODULE_NAMES, RISK_EMOJI
from app.llm import LLMConfigError
from app.orchestrator import CampaignInput, run_all_modules
from app.parsing import content_image_to_text, ocr_content_image, parse_contract
from app.scoring import SCORING_RULE_TEXT

st.set_page_config(page_title="InfluencerLaw", page_icon="⚖️", layout="wide")

st.title("⚖️ InfluencerLaw")
st.caption(
    "Influencer campaigns are reviewed for creativity, engagement and brand fit. "
    "InfluencerLaw adds the missing layer: legal risk before the post goes live."
)
st.caption("Jurisdiction: India (ASCI Code, ASCI Influencer Guidelines, CCPA Misleading Advertisement Guidelines 2022)")

if "run_result" not in st.session_state:
    st.session_state.run_result = None
if "campaign" not in st.session_state:
    st.session_state.campaign = None


def _risk_badge(risk: str) -> str:
    return f"{RISK_EMOJI.get(risk, '')} {risk}"


with st.form("campaign_form"):
    st.header("1. Campaign Brief")
    col1, col2 = st.columns(2)
    with col1:
        brand = st.text_input("Brand", placeholder="e.g. GlowSkin Cosmetics")
        product = st.text_input("Product", placeholder="e.g. GlowSkin Radiance Serum")
        objective = st.text_area("Campaign objective", placeholder="e.g. Drive awareness and trial of the new serum among 20-35 year old women")
    with col2:
        target_audience = st.text_area("Target audience", placeholder="e.g. Women aged 20-35, urban India, skincare-conscious")
        claims_to_communicate = st.text_area(
            "Claims the brand wants communicated (include any supporting evidence you have)",
            placeholder="e.g. 'Reduces visible pigmentation' - supported by a 4-week in-house consumer trial (n=50); 'Dermatologist tested'",
            height=120,
        )

    st.header("2. Influencer Contract")
    contract_file = st.file_uploader("Upload the influencer contract (PDF or DOCX)", type=["pdf", "docx"])

    st.header("3. Content")
    content_mode = st.radio(
        "How are you providing the content?",
        ["Paste caption / transcript text", "Upload a screenshot (Instagram post/reel image)"],
        horizontal=True,
    )
    content_text_input = ""
    content_image = None
    if content_mode.startswith("Paste"):
        content_text_input = st.text_area(
            "Caption / transcript text", height=150,
            placeholder="Paste the exact caption, transcript, or on-screen text of the post/reel here...",
        )
    else:
        content_image = st.file_uploader("Upload screenshot", type=["png", "jpg", "jpeg"])
        st.caption(
            "Video upload isn't supported in this build -- if you have a reel/video, paste its "
            "transcript above instead."
        )

    submitted = st.form_submit_button("Run Legal Review", type="primary")

if submitted:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.error(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env, add your key, and restart the app."
        )
        st.stop()

    with st.spinner("Parsing documents..."):
        contract_text = ""
        if contract_file is not None:
            try:
                contract_text = parse_contract(contract_file.name, contract_file.read())
            except Exception as e:
                st.error(f"Could not parse contract: {e}")
                st.stop()

        content_text = content_text_input
        ocr_detail = None
        if content_image is not None:
            try:
                media_type = content_image.type or "image/png"
                ocr_detail = ocr_content_image(content_image.read(), media_type)
                content_text = content_image_to_text(ocr_detail)
            except LLMConfigError as e:
                st.error(str(e))
                st.stop()
            except Exception as e:
                st.error(f"Could not read screenshot: {e}")
                st.stop()

    if not contract_text.strip():
        st.warning("No contract text was extracted -- Module C (Contract Compliance) will have nothing to check against.")
    if not content_text.strip():
        st.error("No content was provided (paste a caption/transcript or upload a screenshot).")
        st.stop()

    campaign = CampaignInput(
        brand=brand,
        product=product,
        objective=objective,
        target_audience=target_audience,
        claims_to_communicate=claims_to_communicate,
        contract_text=contract_text,
        content_text=content_text,
    )

    try:
        with st.spinner("Running the four legal-review modules (Disclosure, ClaimCheck, Contract Compliance, Comparative Advertising)..."):
            result = run_all_modules(campaign)
    except LLMConfigError as e:
        st.error(str(e))
        st.stop()
    except Exception as e:
        st.error(f"The review failed: {e}")
        st.stop()

    st.session_state.run_result = result
    st.session_state.campaign = campaign
    st.session_state.content_ocr_detail = ocr_detail


result = st.session_state.run_result
if result is not None:
    campaign = st.session_state.campaign
    report = result.report

    st.divider()
    st.header("Dashboard")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.metric("Overall status", f"{report.status_emoji} {report.status}")
    with c2:
        st.metric("Compliance score", f"{report.score} / 100")
    with c3:
        with st.expander("Scoring rule (not a black box)"):
            st.write(SCORING_RULE_TEXT)

    st.subheader("Category breakdown")
    cat_cols = st.columns(len(MODULE_NAMES))
    for col, (module_key, module_label) in zip(cat_cols, MODULE_NAMES.items()):
        risk = report.category_risk.get(module_key, "NONE")
        with col:
            st.markdown(f"**{module_label}**")
            st.markdown(f"### {_risk_badge(risk)}")

    with st.expander("\U0001F3B5 Music rights detection -- Coming soon"):
        st.info(
            "Real music-rights checking requires a licensed audio-fingerprinting API "
            "(e.g. ACRCloud) that is out of scope for this build. This category is a "
            "placeholder and does not contribute to the score above."
        )

    st.subheader("Issue list")
    if not report.issues:
        st.success("No issues were flagged by any module.")
    else:
        for i, issue in enumerate(report.issues):
            module_label = MODULE_NAMES.get(issue.module, issue.module)
            with st.expander(f"{_risk_badge(issue.risk)} [{module_label}] {issue.title}"):
                st.markdown("**Detected issue**")
                st.write(issue.title)
                st.markdown("**Evidence** (exact quote from the content)")
                st.code(issue.evidence or "(none)", language=None)
                if issue.extra.get("contract_restriction"):
                    st.markdown("**Contract restriction**")
                    st.code(issue.extra["contract_restriction"], language=None)
                st.markdown("**Legal basis** (retrieved provision)")
                st.write(f"*{issue.legal_citation}*")
                if issue.legal_text:
                    st.caption(issue.legal_text)
                st.markdown("**Risk level**")
                st.write(_risk_badge(issue.risk))
                st.markdown("**Suggested fix**")
                st.write(issue.suggested_fix or "(no fix suggested)")

    st.subheader("Fix Campaign view")
    rewrites = [i for i in report.issues if i.rewritten_text]
    if not rewrites:
        st.info("No rewrites to show -- no flagged claim/statement had a suggested rewrite.")
    else:
        for issue in rewrites:
            module_label = MODULE_NAMES.get(issue.module, issue.module)
            st.markdown(f"**[{module_label}] {_risk_badge(issue.risk)}**")
            colo, coln = st.columns(2)
            with colo:
                st.caption("Original")
                st.write(issue.original_text)
            with coln:
                st.caption("Fixed")
                st.write(issue.rewritten_text)
            if issue.extra.get("fix_explanation"):
                st.caption(f"Why: {issue.extra['fix_explanation']}")
            st.divider()

    with st.expander("Module detail data (debug / transparency)"):
        st.json(result.details)
