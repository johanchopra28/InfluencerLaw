"""HYPECHECK - the actual review tool (upload -> pipeline -> dashboard).

Run via: streamlit run app.py  (this page is reached from the sidebar, or the
landing page's "Run a review" button).
"""
from __future__ import annotations

import os

import streamlit as st

from app.config import (
    AUDD_API_KEY,
    APP_NAME,
    DISCLAIMER_TEXT,
    LAWYER_CONSULT_NOTE,
    MODULE_NAMES,
    RISK_COLOR_HEX,
    RISK_EMOJI,
    RISK_HIGH,
)
from app.llm import LLMConfigError
from app.orchestrator import CampaignInput, run_all_modules
from app.parsing import content_image_to_text, ocr_content_image, parse_contract
from app.pdfgen import generate_license_later_pdf
from app.scoring import SCORING_RULE_TEXT
from app.theme import (
    inject_brand_css,
    render_tab_strip,
    risk_badge_html,
    risk_container_style,
    status_summary_html,
)

st.set_page_config(page_title=f"{APP_NAME} - Run Review", page_icon="⚖️", layout="wide")
inject_brand_css()

render_tab_strip("pages/1_Run_Review.py")

st.title(f"⚖️ {APP_NAME}")
st.caption(
    "Influencer campaigns are reviewed for creativity, engagement and brand fit. "
    f"{APP_NAME} adds the missing layer: legal risk before the post goes live."
)
st.caption(
    "Jurisdiction: India (ASCI Code, ASCI Influencer Guidelines, CCPA Misleading "
    "Advertisement Guidelines 2022, Consumer Protection Act 2019, "
    "Consumer Protection (E-Commerce) Rules 2020)"
)
st.warning(DISCLAIMER_TEXT, icon="⚖️")

if "run_result" not in st.session_state:
    st.session_state.run_result = None
if "campaign" not in st.session_state:
    st.session_state.campaign = None


def _risk_badge(risk: str) -> str:
    return f"{RISK_EMOJI.get(risk, '')} {risk}"


st.header("1. Campaign Brief")
col1, col2 = st.columns(2)
with col1:
    brand = st.text_input("Brand", placeholder="e.g. GlowSkin Cosmetics")
    product = st.text_input("Product", placeholder="e.g. GlowSkin Radiance Serum")
    objective = st.text_area(
        "Campaign objective",
        placeholder="e.g. Drive awareness and trial of the new serum among 20-35 year old women",
    )
with col2:
    target_audience = st.text_area(
        "Target audience",
        placeholder="e.g. Women aged 20-35, urban India, skincare-conscious",
    )
    claims_to_communicate = st.text_area(
        "Claims the brand wants communicated (include any supporting evidence you have)",
        placeholder="e.g. 'Reduces visible pigmentation' - supported by a 4-week in-house consumer trial (n=50); 'Dermatologist tested'",
        height=120,
    )

st.header("2. Influencer Contract")
contract_file = st.file_uploader("Upload the influencer contract (PDF or DOCX)", type=["pdf", "docx"])

st.header("3. Content")
# NOTE: this radio (and everything that branches on it) must live outside
# st.form -- form widgets only rerun the script on submit, so a conditional
# file_uploader/text_area keyed off a radio inside a form never appears when
# the user switches the radio. Keeping the whole input section un-formed
# (plain widgets + st.button below) keeps the conditional reactive.
content_mode = st.radio(
    "How are you providing the content?",
    ["Paste caption / transcript text", "Upload a screenshot (Instagram post/reel image)"],
    horizontal=True,
    key="content_mode",
)
content_text_input = ""
content_image = None
if content_mode.startswith("Paste"):
    content_text_input = st.text_area(
        "Caption / transcript text",
        height=150,
        placeholder="Paste the exact caption, transcript, or on-screen text of the post/reel here...",
        key="content_text_input",
    )
else:
    content_image = st.file_uploader(
        "Upload screenshot", type=["png", "jpg", "jpeg"], key="content_image"
    )
    st.caption(
        "Video upload isn't supported in this build -- if you have a reel/video, paste its "
        "transcript above instead."
    )

st.header("4. Music Licensing Check (optional)")
audio_file = st.file_uploader(
    "Upload the reel/video's AUDIO TRACK (mp3, wav, m4a, ogg) to check for identifiable "
    "commercial music",
    type=["mp3", "wav", "m4a", "ogg", "flac"],
)
st.caption(
    "Video files aren't accepted directly (no server-side audio extraction in this build) "
    "-- export or record just the audio track and upload that. This uses AudD "
    "(https://audd.io) to identify the track; it tells you WHAT SONG it is, not whether "
    "you're licensed to use it."
    + ("" if AUDD_API_KEY else " **AUDD_API_KEY is not set -- this check will be skipped.**")
)

submitted = st.button("Run Legal Review", type="primary")

if submitted:
    if not os.environ.get("GEMINI_API_KEY"):
        st.error(
            "GEMINI_API_KEY is not set. Copy .env.example to .env, add a free key from "
            "https://aistudio.google.com/apikey, and restart the app."
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

        audio_bytes = audio_file.read() if audio_file is not None else None
        audio_filename = audio_file.name if audio_file is not None else ""

    if not contract_text.strip():
        st.warning("No contract text was extracted -- the Contract Compliance check will have nothing to check against.")
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
        audio_bytes=audio_bytes,
        audio_filename=audio_filename,
    )

    try:
        with st.spinner(
            "Running the legal-review modules (Disclosure, ClaimCheck, Contract "
            "Compliance, Consumer Protection & E-Commerce, Comparative Advertising, "
            "Music Licensing)..."
        ):
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

    st.markdown('<div class="hero-rule"></div>', unsafe_allow_html=True)
    st.header("Dashboard")
    st.warning(DISCLAIMER_TEXT, icon="⚖️")

    st.markdown(
        status_summary_html(report.status, report.status_emoji, report.score),
        unsafe_allow_html=True,
    )
    st.write("")
    with st.expander("Scoring rule (not a black box)"):
        st.write(SCORING_RULE_TEXT)

    st.subheader("Category breakdown")
    cat_cols = st.columns(len(MODULE_NAMES))
    for col, (module_key, module_label) in zip(cat_cols, MODULE_NAMES.items()):
        risk = report.category_risk.get(module_key, "NONE")
        with col:
            st.markdown(
                f'<div class="cat-card"><span class="cat-label">{module_label}</span>'
                f"{risk_badge_html(risk)}</div>",
                unsafe_allow_html=True,
            )

    music_detail = result.details.get("music", {})
    if music_detail.get("configured") is False:
        st.info(
            f"🎵 Music Licensing: {music_detail.get('error', 'AUDD_API_KEY not set')} "
            "-- this category was skipped, not scored as clear."
        )
    elif music_detail.get("error"):
        st.warning(f"🎵 Music Licensing check failed: {music_detail['error']}")
    elif music_detail.get("identified") is False:
        st.success(f"🎵 {music_detail.get('message', 'No copyrighted track detected.')}")

    st.subheader("Issue list")
    if not report.issues:
        st.success("No issues were flagged by any module.")
    else:
        for i, issue in enumerate(report.issues):
            module_label = MODULE_NAMES.get(issue.module, issue.module)
            with st.expander(f"{_risk_badge(issue.risk)} [{module_label}] {issue.title}"):
                issue_key = f"issue-{i}"
                st.markdown(risk_container_style(issue_key, issue.risk), unsafe_allow_html=True)
                with st.container(border=True, key=issue_key):
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
                    st.markdown(risk_badge_html(issue.risk), unsafe_allow_html=True)
                    if issue.risk == RISK_HIGH:
                        st.markdown(f"**{LAWYER_CONSULT_NOTE}**")
                    st.markdown("**Suggested fix / next action**")
                    st.write(issue.suggested_fix or "(no fix suggested)")

                if issue.extra.get("requires_license_later_doc"):
                    st.markdown("---")
                    st.markdown(
                        f"**This item can't be resolved by this tool** -- {APP_NAME} "
                        "identifies and flags music; it does not broker or verify licenses. "
                        "Generate an acknowledgment document for your legal/brand team to "
                        "sign off once the track is actually cleared:"
                    )
                    pdf_bytes = generate_license_later_pdf(
                        brand=campaign.brand,
                        product=campaign.product,
                        items=[
                            {
                                "what_detected": f"{issue.extra.get('artist', '')} - "
                                f"{issue.extra.get('title', '')}"
                                + (
                                    f" ({issue.extra.get('label')})"
                                    if issue.extra.get("label")
                                    else ""
                                ),
                                "why_flagged": issue.explanation,
                                "required_action": issue.suggested_fix,
                            }
                        ],
                    )
                    st.download_button(
                        "📄 Generate license-later document (PDF)",
                        data=pdf_bytes,
                        file_name=f"license-later-{(campaign.brand or 'campaign').replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        key=f"license_pdf_{i}",
                    )

    st.subheader("Fix Campaign view")
    rewrites = [i for i in report.issues if i.rewritten_text]
    if not rewrites:
        st.info("No rewrites to show -- no flagged claim/statement had a suggested rewrite.")
    else:
        for ri, issue in enumerate(rewrites):
            module_label = MODULE_NAMES.get(issue.module, issue.module)
            rewrite_key = f"rewrite-{ri}"
            st.markdown(risk_container_style(rewrite_key, issue.risk), unsafe_allow_html=True)
            with st.container(border=True, key=rewrite_key):
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
            st.write("")

    with st.expander("Module detail data (debug / transparency)"):
        st.json(result.details)
