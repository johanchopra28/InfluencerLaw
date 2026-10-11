"""HYPECHECK - content check: review a caption, post or script, plus an optional audio track."""
from __future__ import annotations

import streamlit as st

from app.config import APP_NAME, AUDD_API_KEY
from app.dashboard import render_results
from app.llm import LLMConfigError
from app.orchestrator import review_content
from app.parsing import content_image_to_text, ocr_content_image
from app.site import eyebrow, inject_site_css, page_head, render_nav, require_api_key

st.set_page_config(
    page_title=f"{APP_NAME} - Content check",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_site_css()
render_nav("content")
page_head(
    "Caption and content check",
    "Check content",
    "Review a caption, post or reel script for disclosure gaps, potentially misleading claims "
    "and other content concerns.",
    needs=("The caption, script or a screenshot of the post", "Optional: evidence behind any claims, and the audio track"),
)

with st.container(key="body"):
    eyebrow("1. The content")
    # The radio and the widgets that depend on it must stay outside st.form: form widgets
    # only rerun the script on submit, so a conditional uploader would never appear.
    mode = st.radio(
        "How are you providing the content?",
        ["Paste caption or transcript", "Upload a screenshot of the post"],
        horizontal=True,
        key="content_mode",
    )
    content_text = ""
    content_image = None
    if mode.startswith("Paste"):
        content_text = st.text_area(
            "Caption or transcript",
            height=160,
            placeholder="Paste the exact caption, transcript or on-screen text of the post or reel.",
            key="content_text",
        )
    else:
        content_image = st.file_uploader("Screenshot", type=["png", "jpg", "jpeg"], key="content_image")
        st.caption("Video upload isn't supported yet. For a reel or video, paste its transcript instead.")

    st.write("")
    eyebrow("2. Evidence for any claims (optional)")
    evidence = st.text_area(
        "Evidence behind claims made in the content",
        placeholder="e.g. 4-week in-house consumer trial (n=50). Dermatologist tested.",
        key="content_evidence",
    )

    st.write("")
    eyebrow("3. Music (optional)")
    audio_file = st.file_uploader(
        "Upload the audio track to check for identifiable commercial music",
        type=["mp3", "wav", "m4a", "ogg", "flac"],
        key="content_audio",
    )
    st.caption(
        "Video files aren't accepted directly. Export or record just the audio track and upload that "
        "instead. This uses AudD (https://audd.io) to identify the track; it tells you what song it is, "
        "not whether you're licensed to use it."
        + ("" if AUDD_API_KEY else " AUDD_API_KEY is not set, so this check will be skipped.")
    )
    left, right = st.columns(2, gap="large")
    with left:
        brand = st.text_input("Brand (optional)", key="content_brand")
    with right:
        product = st.text_input("Product (optional)", key="content_product")
    st.caption("Brand and product are only used to fill in the license-later document if a track is identified.")

    st.write("")
    if st.button("Check content", type="primary", key="content_run"):
        require_api_key()
        try:
            with st.spinner("Reading the content..."):
                if content_image is not None:
                    content_text = content_image_to_text(
                        ocr_content_image(content_image.read(), content_image.type or "image/png")
                    )
        except LLMConfigError as e:
            st.error(str(e))
            st.stop()
        except Exception as e:
            st.error(f"Could not read the screenshot: {e}")
            st.stop()
        if not content_text.strip():
            st.error("Paste a caption or transcript, or upload a screenshot, so there is something to check.")
            st.stop()
        try:
            with st.spinner("Reviewing the content..."):
                st.session_state["content_result"] = (
                    review_content(
                        content_text,
                        evidence,
                        audio_file.read() if audio_file is not None else None,
                        audio_file.name if audio_file is not None else "",
                    ),
                    brand,
                    product,
                )
        except LLMConfigError as e:
            st.error(str(e))
            st.stop()
        except Exception as e:
            st.error(f"The review failed: {e}")
            st.stop()

    saved = st.session_state.get("content_result")
    if saved is not None:
        result, saved_brand, saved_product = saved
        st.write("")
        render_results(result, key="content", brand=saved_brand, product=saved_product)
