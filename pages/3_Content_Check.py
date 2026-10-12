"""HYPECHECK - content check: review a caption, post or script."""
from __future__ import annotations

import streamlit as st

from app.config import APP_NAME
from app.footer import render_footer
from app.dashboard import render_content_results
from app.llm import LLMConfigError
from app.orchestrator import review_content
from app.parsing import (
    DOCUMENT_TYPES,
    DOCUMENT_TYPES_LABEL,
    UnreadableDocument,
    content_image_to_text,
    ocr_content_image,
    read_document,
)
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

P = "content_"
METHODS = ["Paste text", "Upload a file", "Upload an image"]
FORMATS = ["Caption", "Reel script", "Story", "Static post", "Video description", "Other"]
PLATFORMS = ["Instagram", "YouTube", "LinkedIn", "X", "Facebook", "Other"]
RELATIONSHIPS = ["Paid", "Gifted product", "Affiliate", "Brand ambassador", "Own brand", "Unsure"]
PLACEHOLDER = "Paste your caption, Reel script, post copy, or proposed promotional content here."

st.set_page_config(
    page_title=f"{APP_NAME} - Content check",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_site_css()
keep_state(
    f"{P}method", f"{P}text", f"{P}format", f"{P}platform", f"{P}relationship", f"{P}category", f"{P}context",
)
render_nav("content")
page_head(
    "Content check",
    "Check Your Caption or Content",
    "Review a caption, Reel script, post, or proposed promotional content before it is published. HYPECHECK "
    "checks for missing advertising disclosures, potentially misleading claims, and other compliance concerns "
    "under Indian advertising and consumer-protection rules.",
    needs=("Caption review", "Disclosure checks", "Suggested edits"),
)

errors = form_errors(P)
with st.container(key="body"):
    eyebrow("1. The content")
    left, right = st.columns([3, 2], gap="large")
    with left:
        # The method radio and the inputs it controls stay outside st.form: form widgets only
        # rerun the script on submit, so a conditional uploader would never appear.
        method = st.radio("How are you providing the content?", METHODS, horizontal=True, key=f"{P}method")
        text, upload, image = "", None, None
        with field("content", set(errors)):
            if method == "Paste text":
                text = st.text_area("Content (required)", height=180, placeholder=PLACEHOLDER, key=f"{P}text")
            elif method == "Upload a file":
                upload = st.file_uploader(
                    "Content file (required)", type=DOCUMENT_TYPES, key=upload_key(P, "file"),
                    help=f"Accepted: {DOCUMENT_TYPES_LABEL}. Maximum size 25 MB.",
                )
                st.caption(f"Accepted: {DOCUMENT_TYPES_LABEL}. Maximum size 25 MB.")
            else:
                image = st.file_uploader(
                    "Image of the post (required)", type=["png", "jpg", "jpeg"], key=upload_key(P, "image"),
                    help="Accepted: PNG, JPG. Maximum size 25 MB.",
                )
                st.caption(
                    "Accepted: PNG, JPG. Maximum size 25 MB. HYPECHECK reads the text that appears in the image. "
                    "It does not assess the visual elements of the image itself."
                )
            field_message("content", errors)
        st.caption("Video upload is not supported yet. For a Reel or video, paste its script or transcript.")
    with right:
        privacy_notice()

    st.write("")
    eyebrow("2. About the content (all optional)")
    left, right = st.columns(2, gap="large")
    with left:
        content_format = st.selectbox("Content format", FORMATS, index=None, placeholder="Choose a format", key=f"{P}format")
        platform = st.selectbox("Platform", PLATFORMS, index=None, placeholder="Choose a platform", key=f"{P}platform")
        relationship = st.selectbox(
            "Your relationship with the brand", RELATIONSHIPS, index=None, placeholder="Choose one", key=f"{P}relationship"
        )
    with right:
        category = st.text_input("Product or service category", placeholder="e.g. skincare, fintech", key=f"{P}category")
        context = st.text_area(
            "Additional context",
            placeholder="Approved claims, brand instructions, or evidence behind claims made in the content.",
            height=120,
            key=f"{P}context",
        )
    st.caption("This context is used only to review the content more accurately. None of it is required.")

    st.write("")
    clicked = st.button("Check Content", type="primary", key=f"{P}run")
    retry = failure_panel(P)

    def validate() -> dict[str, str]:
        if method == "Paste text" and not text.strip():
            return {"content": "Paste the content to check. A caption, script or post copy all work."}
        if method == "Upload a file" and upload is None:
            return {"content": "Upload a file to check. Accepted: " + DOCUMENT_TYPES_LABEL + "."}
        if method == "Upload an image" and image is None:
            return {"content": "Upload an image of the post to check. Accepted: PNG, JPG."}
        return {}

    if gate(P, clicked or retry, validate):
        require_api_key()
        notes: list[str] = []
        content_text = text
        try:
            if method == "Upload a file":
                document = read_document(upload.name, upload.getvalue())
                content_text, notes = document.text, list(document.notes)
            elif method == "Upload an image":
                with st.spinner("Reading the image..."):
                    content_text = content_image_to_text(ocr_content_image(image.getvalue(), image.type or "image/png"))
                if not content_text.strip():
                    fail_field(P, "content", "No readable text was found in this image. Paste the text instead, or try a clearer image.")
                notes.append("Only the text visible in the image was reviewed, not its visual elements.")
        except UnreadableDocument as e:
            fail_field(P, "content", str(e))
        except LLMConfigError as e:
            st.error(str(e))
            st.stop()
        except Exception:
            fail_field(P, "content", "The image could not be read. Try a clearer image, or paste the text instead.")
        if not content_text.strip():
            fail_field(P, "content", "No readable text was found. Paste the text instead.")

        st.session_state[f"{P}failed"] = False
        try:
            with st.spinner("Reviewing the content..."):
                result = review_content(
                    content_text,
                    content_format=content_format or "",
                    platform=platform or "",
                    relationship=relationship or "",
                    category=category,
                    context=context,
                    read_notes=tuple(notes),
                )
            st.session_state[f"{P}result"] = (result, content_text)
        except LLMConfigError as e:
            st.error(str(e))
            st.stop()
        except Exception as e:
            note_failure(P, e)
            st.rerun()

    saved = st.session_state.get(f"{P}result")
    if saved is not None:
        result, original = saved
        st.write("")
        render_content_results(result, original=original, reset_prefix=P)

render_footer()
