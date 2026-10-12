"""HYPECHECK - campaign check: review a brief, deliverables, disclosures and claims before content exists."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from app.config import APP_NAME
from app.dashboard import render_campaign_results
from app.llm import LLMConfigError
from app.modules.campaign_review import CAMPAIGN_TYPES, JURISDICTIONS, extract_brief_fields
from app.orchestrator import review_campaign
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
    notice,
    page_head,
    privacy_notice,
    render_nav,
    upload_key,
    require_api_key,
)

P = "campaign_"
DELIVERABLE_COLUMNS = ["Deliverable", "Quantity", "Publication date", "Required tags or disclosures"]

st.set_page_config(
    page_title=f"{APP_NAME} - Campaign check",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_site_css()
keep_state(
    f"{P}type", f"{P}category", f"{P}jurisdiction", f"{P}jurisdiction_detail", f"{P}requirements", f"{P}deliverables"
)
render_nav("campaign")
page_head(
    "Campaign check",
    "Check Your Influencer Campaign",
    "Review your campaign brief before it goes live. HYPECHECK examines the proposed deliverables, advertising "
    "disclosures, brand claims, usage rights, and campaign requirements to identify potential compliance gaps "
    "and areas that may need clarification.",
    needs=("Campaign requirements", "Disclosure checks", "Compliance flags"),
)


def deliverables_frame(rows: list[dict] | None = None) -> pd.DataFrame:
    return pd.DataFrame(
        [
            [r.get("item", ""), r.get("quantity", ""), r.get("date", ""), r.get("tags", "")]
            for r in (rows or [])
        ],
        columns=DELIVERABLE_COLUMNS,
    )


errors = form_errors(P)
with st.container(key="body"):
    eyebrow("1. Start with a brief, or enter the details yourself")
    left, right = st.columns([3, 2], gap="large")
    with left:
        with field("brief", set(errors)):
            brief_file = st.file_uploader(
                "Campaign brief (optional if you enter the details below)",
                type=DOCUMENT_TYPES,
                key=upload_key(P, "brief_file"),
                help=f"Accepted: {DOCUMENT_TYPES_LABEL}. Maximum size 25 MB.",
            )
            field_message("brief", errors)
        st.caption(
            f"Accepted: {DOCUMENT_TYPES_LABEL}. Maximum size 25 MB. You do not need both a brief and the details "
            "below. Text in images, charts or embedded objects in a brief can't be read, and you will be told if "
            "that applies. If you leave this page the upload is cleared; everything else you enter is kept."
        )
    with right:
        privacy_notice()

    # When a brief is uploaded, read it once and pre-fill the fields below for the user to confirm.
    brief_text = ""
    brief_notes: list[str] = []
    if brief_file is not None:
        signature = (brief_file.name, brief_file.size)
        if st.session_state.get(f"{P}brief_sig") != signature:
            try:
                with st.spinner("Reading your brief..."):
                    document = read_document(brief_file.name, brief_file.getvalue())
                    require_api_key()
                    found = extract_brief_fields(document.text)
            except UnreadableDocument as e:
                fail_field(P, "brief", str(e))
            except LLMConfigError as e:
                st.error(str(e))
                st.stop()
            except Exception:
                found = None
            st.session_state[f"{P}brief_sig"] = signature
            st.session_state[f"{P}brief_text"] = document.text
            st.session_state[f"{P}brief_notes"] = list(document.notes)
            st.session_state[f"{P}brief_found"] = [
                label
                for label, value in (
                    ("campaign type", (found or {}).get("campaign_type")),
                    ("brand or product category", (found or {}).get("category")),
                    ("jurisdiction", (found or {}).get("jurisdiction")),
                    ("deliverables", (found or {}).get("deliverables")),
                    ("advertising and disclosure requirements", (found or {}).get("requirements")),
                )
                if value
            ]
            if found:
                if found["campaign_type"]:
                    st.session_state[f"{P}type"] = found["campaign_type"]
                if found["category"]:
                    st.session_state[f"{P}category"] = found["category"]
                if found["jurisdiction"]:
                    st.session_state[f"{P}jurisdiction"] = found["jurisdiction"]
                if found["requirements"]:
                    st.session_state[f"{P}requirements"] = found["requirements"]
                if found["deliverables"]:
                    st.session_state[f"{P}deliverables"] = found["deliverables"]
                    st.session_state[f"{P}deliv_version"] = st.session_state.get(f"{P}deliv_version", 0) + 1
        brief_text = st.session_state.get(f"{P}brief_text", "")
        brief_notes = st.session_state.get(f"{P}brief_notes", [])
        for note in brief_notes:
            notice(note)
        read_back = st.session_state.get(f"{P}brief_found", [])
        if read_back:
            notice(
                "We read these details from your brief: " + ", ".join(read_back) + ". They are filled in below. "
                "Check them and change anything that is wrong."
            )
        else:
            notice("We could not find the campaign details in this brief. Fill them in below.")

    st.write("")
    eyebrow("2. About the campaign")
    left, right = st.columns(2, gap="large")
    with left:
        with field("type", set(errors)):
            campaign_type = st.selectbox(
                "Campaign type (required)", CAMPAIGN_TYPES, index=None, placeholder="Choose the campaign type", key=f"{P}type"
            )
            field_message("type", errors)
        category = st.text_input(
            "Brand or product category",
            placeholder="e.g. beauty, fintech, food",
            key=f"{P}category",
        )
        st.caption("Optional. The brand name isn't needed; a category is enough.")
    with right:
        jurisdiction = st.selectbox(
            "Target jurisdiction", JURISDICTIONS, index=None, placeholder="Choose one", key=f"{P}jurisdiction"
        )
        jurisdiction_detail = ""
        if jurisdiction in ("Other jurisdiction", "Multiple jurisdictions"):
            jurisdiction_detail = st.text_input("Which jurisdictions?", key=f"{P}jurisdiction_detail")
        st.caption(
            "Optional. HYPECHECK's legal sources cover Indian advertising and consumer-protection rules only."
        )

    st.write("")
    eyebrow("3. Deliverables")
    st.caption("Optional if they are in the brief. Add a row for each deliverable.")
    version = st.session_state.get(f"{P}deliv_version", 0)
    editor_key = f"{P}deliv_editor_{version}"
    if editor_key not in st.session_state:
        # Fresh editor (first visit, return to the page, or new brief): start from the saved rows.
        # The starting table is held constant while the user edits so their changes are not reset.
        st.session_state[f"{P}deliv_seed"] = list(st.session_state.get(f"{P}deliverables", []))
    edited = st.data_editor(
        deliverables_frame(st.session_state.get(f"{P}deliv_seed", [])),
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key=editor_key,
        column_config={
            "Deliverable": st.column_config.TextColumn(help="For example Instagram reel, story, static post"),
            "Quantity": st.column_config.TextColumn(),
            "Publication date": st.column_config.TextColumn(help="A date or a window, as you would write it"),
            "Required tags or disclosures": st.column_config.TextColumn(),
        },
    )
    deliverables = [
        {"item": r["Deliverable"], "quantity": r["Quantity"], "date": r["Publication date"], "tags": r["Required tags or disclosures"]}
        for _, r in edited.iterrows()
        if str(r["Deliverable"] or "").strip()
    ]
    st.session_state[f"{P}deliverables"] = deliverables

    st.write("")
    eyebrow("4. Advertising and disclosure requirements")
    requirements = st.text_area(
        "Brand instructions, mandatory disclosures, hashtags, platform-specific requirements and approved claims",
        height=140,
        key=f"{P}requirements",
    )

    st.write("")
    eyebrow("5. Supporting materials (optional)")
    support_files = st.file_uploader(
        "Approved product claims, campaign guidelines, usage permissions, or relevant extracts from the contract",
        type=DOCUMENT_TYPES,
        accept_multiple_files=True,
        key=upload_key(P, "support_files"),
    )
    st.caption(
        "Evidence behind the claims goes here. A brief's own claims are not treated as evidence for themselves."
    )

    st.write("")
    clicked = st.button("Review Campaign", type="primary", key=f"{P}run")
    retry = failure_panel(P)

    def validate() -> dict[str, str]:
        found: dict[str, str] = {}
        if not campaign_type:
            found["type"] = "Choose the campaign type. HYPECHECK needs it to know which requirements apply."
        if brief_file is None and not (requirements.strip() or deliverables):
            found["brief"] = "Upload a brief, or fill in the deliverables or requirements below, so there is something to review."
        return found

    if gate(P, clicked or retry, validate):
        require_api_key()
        st.session_state[f"{P}failed"] = False
        support_text, support_notes = [], []
        for upload in support_files or []:
            try:
                document = read_document(upload.name, upload.getvalue())
            except UnreadableDocument as e:
                fail_field(P, "brief", f"{upload.name}: {e}")
            support_text.append(document.text)
            support_notes += [f"{upload.name}: {n}" for n in document.notes]
        detail = f"{jurisdiction}: {jurisdiction_detail.strip()}" if jurisdiction_detail.strip() else (jurisdiction or "")
        try:
            with st.spinner("Reviewing the campaign..."):
                st.session_state[f"{P}result"] = review_campaign(
                    brief_text=brief_text,
                    campaign_type=campaign_type or "",
                    category=category,
                    jurisdiction=jurisdiction or "",
                    deliverables=deliverables,
                    requirements=f"{requirements}\n{detail}".strip() if jurisdiction_detail.strip() else requirements,
                    supporting_text="\n\n".join(support_text),
                    read_notes=tuple(brief_notes + support_notes),
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
        render_campaign_results(result, reset_prefix=P)
