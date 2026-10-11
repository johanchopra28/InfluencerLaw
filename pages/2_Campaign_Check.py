"""HYPECHECK - campaign check: review a brief, planned deliverables, disclosures and claims."""
from __future__ import annotations

import streamlit as st

from app.config import APP_NAME
from app.dashboard import render_results
from app.llm import LLMConfigError
from app.orchestrator import review_campaign
from app.site import eyebrow, inject_site_css, page_head, render_nav, require_api_key

st.set_page_config(
    page_title=f"{APP_NAME} - Campaign check",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_site_css()
render_nav("campaign")
page_head(
    "Campaign check",
    "Check a campaign",
    "Assess a campaign brief, proposed deliverables, disclosures and brand claims before any "
    "content is made.",
    needs=("The campaign brief and brand details", "The claims to be made, and any evidence behind them"),
)

with st.container(key="body"):
    eyebrow("1. The brief")
    left, right = st.columns(2, gap="large")
    with left:
        brand = st.text_input("Brand", placeholder="e.g. GlowSkin Cosmetics", key="campaign_brand")
        objective = st.text_area(
            "Campaign objective",
            placeholder="e.g. Drive awareness and trial of the new serum among 20 to 35 year old women",
            key="campaign_objective",
        )
    with right:
        product = st.text_input("Product", placeholder="e.g. GlowSkin Radiance Serum", key="campaign_product")
        audience = st.text_area(
            "Target audience",
            placeholder="e.g. Women aged 20 to 35, urban India, skincare-conscious",
            key="campaign_audience",
        )

    st.write("")
    eyebrow("2. Claims and evidence")
    left, right = st.columns(2, gap="large")
    with left:
        claims = st.text_area(
            "Claims the brand wants made",
            height=140,
            placeholder="e.g. Reduces visible pigmentation. Dermatologist tested.",
            key="campaign_claims",
        )
    with right:
        evidence = st.text_area(
            "Evidence behind those claims",
            height=140,
            placeholder="e.g. 4-week in-house consumer trial (n=50). Patch test report for gentleness.",
            key="campaign_evidence",
        )

    st.write("")
    eyebrow("3. Deliverables, disclosure and permissions")
    left, right = st.columns(2, gap="large")
    with left:
        deliverables = st.text_area(
            "Planned deliverables",
            placeholder="e.g. Two reels, three stories, one static post",
            key="campaign_deliverables",
        )
        usage = st.text_area(
            "Usage and permissions (optional)",
            placeholder="e.g. Third-party logos, licensed music, testimonials, paid usage rights",
            key="campaign_usage",
        )
    with right:
        disclosure_plan = st.text_area(
            "How the partnership will be disclosed",
            placeholder="e.g. Paid partnership tag plus the word Ad at the start of each caption",
            key="campaign_disclosure",
        )

    st.write("")
    if st.button("Check campaign", type="primary", key="campaign_run"):
        require_api_key()
        if not (claims.strip() or deliverables.strip()):
            st.error("Add the claims to be made or the planned deliverables, so there is something to check.")
            st.stop()
        try:
            with st.spinner("Reviewing the campaign..."):
                st.session_state["campaign_result"] = review_campaign(
                    brand=brand,
                    product=product,
                    objective=objective,
                    audience=audience,
                    claims=claims,
                    evidence=evidence,
                    deliverables=deliverables,
                    disclosure_plan=disclosure_plan,
                    usage=usage,
                )
        except LLMConfigError as e:
            st.error(str(e))
            st.stop()
        except Exception as e:
            st.error(f"The review failed: {e}")
            st.stop()

    result = st.session_state.get("campaign_result")
    if result is not None:
        st.write("")
        render_results(result, key="campaign", lawyer_note="Consult a lawyer before proceeding with this campaign.")
