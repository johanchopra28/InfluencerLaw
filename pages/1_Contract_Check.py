"""HYPECHECK - contract check: upload an agreement and review it clause by clause."""
from __future__ import annotations

import streamlit as st

from app.config import APP_NAME
from app.footer import render_footer
from app.dashboard import render_contract_results
from app.llm import LLMConfigError
from app.orchestrator import review_contract
from app.parsing import DOCUMENT_TYPES, DOCUMENT_TYPES_LABEL, UnreadableDocument, read_document
from app.site import (
    eyebrow,
    fail_field,
    failure_panel,
    field,
    field_message,
    form_errors,
    gate,
    inject_site_css,
    keep_state,
    note_failure,
    page_head,
    privacy_notice,
    render_nav,
    upload_key,
    require_api_key,
)

P = "contract_"
ROLES = ["Creator/Influencer", "Brand", "Agency", "Manager", "Other"]
JURISDICTIONS = ["India", "Other jurisdiction", "Not sure"]
FOCUS = [
    "Payment",
    "Deliverables",
    "Exclusivity",
    "Intellectual property and usage rights",
    "Termination",
    "Liability and indemnity",
    "Confidentiality",
    "Disclosure and advertising obligations",
    "Entire agreement review",
    "Other",
]

st.set_page_config(
    page_title=f"{APP_NAME} - Contract check",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_site_css()
keep_state(f"{P}role", f"{P}jurisdiction", f"{P}jurisdiction_other", f"{P}focus", f"{P}context", f"{P}caption")
render_nav("contract")
page_head(
    "Contract check",
    "Review an Influencer Contract",
    "Identify clauses that may require attention before signing an influencer, creator, agency, or brand "
    "agreement. HYPECHECK reviews the document for potentially unfavourable terms, missing protections, and "
    "legal or compliance concerns.",
    needs=("Clause-by-clause review", "Risk flags", "Suggested revisions"),
)

errors = form_errors(P)
with st.container(key="body"):
    eyebrow("1. Upload the contract")
    left, right = st.columns([3, 2], gap="large")
    with left:
        with field("upload", set(errors)):
            contract_file = st.file_uploader(
                "Contract (required)",
                type=DOCUMENT_TYPES,
                key=upload_key(P, "file"),
                help=f"Accepted: {DOCUMENT_TYPES_LABEL}. Maximum size 25 MB.",
            )
            field_message("upload", errors)
        st.caption(
            f"Accepted: {DOCUMENT_TYPES_LABEL}. Maximum size 25 MB. A searchable PDF works best. Scanned PDFs "
            "can't be read yet. If you leave this page the upload is cleared; everything else you enter is kept."
        )
    with right:
        privacy_notice()

    st.write("")
    eyebrow("2. Tailor the review (all optional)")
    left, right = st.columns(2, gap="large")
    with left:
        role = st.selectbox("Your role in the agreement", ROLES, index=None, placeholder="Choose a role", key=f"{P}role")
        st.caption("Helps tailor the review to your perspective.")
        jurisdiction = st.selectbox(
            "Governing law or jurisdiction", JURISDICTIONS, index=None, placeholder="Choose one", key=f"{P}jurisdiction"
        )
        jurisdiction_other = ""
        if jurisdiction == "Other jurisdiction":
            jurisdiction_other = st.text_input("Which jurisdiction?", key=f"{P}jurisdiction_other")
        st.caption(
            "HYPECHECK's legal sources cover Indian advertising and consumer-protection rules only. "
            "It does not assume Indian law applies to your contract."
        )
    with right:
        focus = st.multiselect(
            "What would you like us to focus on?", FOCUS, placeholder="Choose any that apply", key=f"{P}focus"
        )
        context = st.text_area(
            "Additional context",
            placeholder="Specific questions, concerns or negotiation priorities.",
            key=f"{P}context",
        )

    st.write("")
    eyebrow("3. Test a caption against the contract (optional)")
    caption = st.text_area(
        "Caption or script",
        placeholder="Paste a caption or script to see whether it breaks the content rules in this contract.",
        key=f"{P}caption",
    )

    st.write("")
    clicked = st.button("Review Contract", type="primary", key=f"{P}run")
    retry = failure_panel(P)

    def validate() -> dict[str, str]:
        if contract_file is None:
            return {"upload": "Upload the contract to continue. Accepted: " + DOCUMENT_TYPES_LABEL + "."}
        return {}

    if gate(P, clicked or retry, validate):
        require_api_key()
        try:
            document = read_document(contract_file.name, contract_file.getvalue())
        except UnreadableDocument as e:
            fail_field(P, "upload", str(e))
        st.session_state[f"{P}failed"] = False
        jurisdiction_value = jurisdiction or ""
        context_value = context
        if jurisdiction_other.strip():
            context_value = f"Governing law: {jurisdiction_other.strip()}. {context}".strip()
        try:
            with st.spinner("Reviewing the contract..."):
                st.session_state[f"{P}result"] = review_contract(
                    document.text,
                    role=role or "",
                    jurisdiction=jurisdiction_value,
                    focus=tuple(focus),
                    context=context_value,
                    content_text=caption,
                    read_notes=tuple(document.notes),
                )
        except LLMConfigError as e:
            st.error(str(e))
            st.stop()
        except Exception as e:
            note_failure(P, e)
            st.rerun()

    result = st.session_state.get(f"{P}result")
    if result is not None:
        st.write("")
        render_contract_results(result, reset_prefix=P)

render_footer()
