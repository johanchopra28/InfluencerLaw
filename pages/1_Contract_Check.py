"""HYPECHECK - contract check: upload an agreement, review it, optionally test a caption against it."""
from __future__ import annotations

import streamlit as st

from app.config import APP_NAME
from app.dashboard import render_results
from app.llm import LLMConfigError
from app.orchestrator import review_contract
from app.parsing import parse_contract
from app.site import eyebrow, inject_site_css, page_head, render_nav, require_api_key

st.set_page_config(
    page_title=f"{APP_NAME} - Contract check",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_site_css()
render_nav("contract")
page_head(
    "Contract check",
    "Check a contract",
    "Review an influencer agreement for potentially risky clauses, missing terms and points "
    "that need attention before anyone signs.",
    needs=("The contract as a PDF or DOCX", "Optional: a caption or script to test against it"),
)

with st.container(key="body"):
    eyebrow("1. The contract")
    contract_file = st.file_uploader(
        "Upload the influencer agreement (PDF or DOCX)", type=["pdf", "docx"], key="contract_file"
    )

    st.write("")
    eyebrow("2. A caption or script to test against it (optional)")
    content_text = st.text_area(
        "Caption or script",
        height=140,
        placeholder="Paste a caption or script to see whether it breaks the content rules in this contract.",
        key="contract_content",
    )

    st.write("")
    if st.button("Check contract", type="primary", key="contract_run"):
        require_api_key()
        if contract_file is None:
            st.error("Upload the contract first.")
            st.stop()
        try:
            with st.spinner("Reading the contract..."):
                contract_text = parse_contract(contract_file.name, contract_file.read())
        except Exception as e:
            st.error(f"Could not read the contract: {e}")
            st.stop()
        if not contract_text.strip():
            st.error("No text could be read from this file. Scanned PDFs are not supported yet.")
            st.stop()
        try:
            with st.spinner("Reviewing the contract..."):
                st.session_state["contract_result"] = review_contract(contract_text, content_text)
        except LLMConfigError as e:
            st.error(str(e))
            st.stop()
        except Exception as e:
            st.error(f"The review failed: {e}")
            st.stop()

    result = st.session_state.get("contract_result")
    if result is not None:
        st.write("")
        render_results(
            result,
            key="contract",
            lawyer_note="Consult a lawyer before signing this.",
            points=result.details["contract_review"]["points_to_confirm"],
        )
