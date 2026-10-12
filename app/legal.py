"""Shared legal wording, so the same text appears consistently on every page.

These are first drafts for review by a qualified Indian lawyer. Keep every statement
accurate to what the app does; update LEGAL_UPDATED when any of this changes.
"""
from __future__ import annotations

from html import escape

LEGAL_UPDATED = "12 October 2026"

# A contact and grievance address. Leave empty until one exists: pages then omit the
# contact line instead of showing a placeholder.
CONTACT_EMAIL = ""

THIRD_PARTY_LINKS = [
    ("Google Gemini API terms", "https://ai.google.dev/gemini-api/terms"),
    ("Google privacy policy", "https://policies.google.com/privacy"),
    ("Groq privacy policy", "https://groq.com/privacy-policy"),
    ("Streamlit privacy policy", "https://streamlit.io/privacy-policy"),
]

SENSITIVE_WARNING = (
    "Do not upload sensitive contractual information. Before you upload, remove or redact personal data of "
    "other people (names, contact details, identity or bank numbers), financial terms you are not free to "
    "share, trade secrets and any other confidential or privileged material. If you cannot remove it, do not "
    "upload it."
)

THIRD_PARTY_DISCLAIMER = (
    "HYPECHECK sends what you submit to third-party services: Google Gemini and, as a backup, Groq. It is "
    "hosted on Streamlit Community Cloud. We cannot warrant, and are not responsible for, any infringement of "
    "data privacy that arises on the part of those third parties. Checking their privacy policies and terms, "
    "and carrying out any other verification you need before submitting material, is your responsibility."
)

ASCI_NOTE = (
    "The Advertising Standards Council of India (ASCI) is a private, self-regulatory body. HYPECHECK uses "
    "its Code and guidelines as an additional reference alongside statutory sources such as the Consumer "
    "Protection Act, 2019 and the guidelines issued under it by the Central Consumer Protection Authority. A "
    "flag that cites only an ASCI provision should be read with that in mind. Please follow it up with a "
    "thorough reading of the relevant law and contextualised professional legal advice."
)

TRADEMARK_NOTE = (
    "HYPECHECK is a name we have chosen to use. We do not currently own a trademark in it, and we make no "
    "claim to exclusive rights in the name. Other names mentioned on this site belong to their owners."
)


def contact_paragraph() -> str:
    """HTML for the contact line, or an empty string until CONTACT_EMAIL is set."""
    if not CONTACT_EMAIL:
        return ""
    mail = escape(CONTACT_EMAIL)
    return (
        '<p class="hc-body"><b>Contact and grievances.</b> For a privacy concern, a complaint or a question '
        f'about these pages, write to <a href="mailto:{mail}">{mail}</a>.</p>'
    )


def links_html(heading: str = "Third-party policies you should read") -> str:
    items = "".join(
        f'<li><a href="{escape(url)}" target="_blank" rel="noopener">{escape(name)}</a></li>'
        for name, url in THIRD_PARTY_LINKS
    )
    return (
        f'<p class="hc-body" style="margin-top:18px"><b>{escape(heading)}</b></p>'
        f'<ul class="hc-scope" style="font-size:14px;max-width:760px">{items}</ul>'
    )
