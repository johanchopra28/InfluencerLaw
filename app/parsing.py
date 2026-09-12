"""Document parsing: contract PDF/DOCX -> text, content image -> OCR'd text.

Kept as small pure functions with no Streamlit dependency so they're testable
in isolation, per the build order's step 2.
"""
from __future__ import annotations

import io

import pdfplumber
from docx import Document as DocxDocument

from app.llm import call_vision_json


def parse_pdf(file_bytes: bytes) -> str:
    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n\n".join(text_parts).strip()


def parse_docx(file_bytes: bytes) -> str:
    doc = DocxDocument(io.BytesIO(file_bytes))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text.strip() for cell in row.cells))
    return "\n".join(parts).strip()


def parse_contract(filename: str, file_bytes: bytes) -> str:
    """Dispatch on extension. Raises ValueError for unsupported types."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return parse_pdf(file_bytes)
    if lower.endswith(".docx"):
        return parse_docx(file_bytes)
    raise ValueError(f"Unsupported contract file type: {filename}. Use PDF or DOCX.")


_OCR_SYSTEM_PROMPT = """You transcribe the visible text from a screenshot of a social \
media post (e.g. Instagram post, reel cover, story). Return ONLY a JSON object with \
this shape, no other prose:

{
  "caption_text": "the caption / body text of the post, verbatim",
  "hashtags": ["list", "of", "hashtags", "without the # sign"],
  "on_image_text": "any text overlaid directly on the image/video itself (titles, \
captions burned into the video, disclosure labels shown on-screen), verbatim",
  "visible_disclosure_labels": ["any disclosure-looking labels you can see, e.g. \
'Paid Partnership', 'Ad', 'Sponsored' -- exactly as shown"],
  "platform_ui_notes": "brief note on what platform UI is visible, if identifiable \
(e.g. Instagram post, Instagram Story, YouTube video thumbnail) - do not include \
UI chrome (like counts, timestamps, or their own button text) in caption_text"
}

If a field has nothing to report, use an empty string or empty list. Do not \
invent text that is not actually visible in the image."""


def ocr_content_image(image_bytes: bytes, media_type: str) -> dict:
    """Use vision LLM to transcribe an uploaded screenshot into structured text
    fields (caption, hashtags, on-image text, visible disclosure labels)."""
    result = call_vision_json(
        system=_OCR_SYSTEM_PROMPT,
        user_text="Transcribe this social media post screenshot as instructed.",
        image_bytes=image_bytes,
        media_type=media_type,
    )
    return result


def content_image_to_text(ocr_result: dict) -> str:
    """Flatten the structured OCR result into a single text blob for modules
    that just need "the content as text"."""
    parts = []
    if ocr_result.get("caption_text"):
        parts.append(ocr_result["caption_text"])
    if ocr_result.get("on_image_text"):
        parts.append(f"[On-screen text]: {ocr_result['on_image_text']}")
    if ocr_result.get("hashtags"):
        parts.append(" ".join(f"#{h}" for h in ocr_result["hashtags"]))
    if ocr_result.get("visible_disclosure_labels"):
        parts.append(
            "[Visible disclosure labels]: " + ", ".join(ocr_result["visible_disclosure_labels"])
        )
    return "\n".join(parts).strip()
