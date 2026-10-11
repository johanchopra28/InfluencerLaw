"""Official links for the legal sources HYPECHECK cites.

Only links that were checked and returned a live page are listed. A source with
no entry here is still cited by name; it simply has no link, rather than a link
that has not been verified.
"""
from __future__ import annotations

SOURCE_URLS = {
    "ASCI Code for Self-Regulation of Advertising Content in India": "https://www.ascionline.in/the-asci-code/",
    "ASCI Guidelines for Influencer Advertising in Digital Media": (
        "https://www.ascionline.in/wp-content/uploads/2023/08/GUIDELINES-FOR-INFLUENCER-ADVERTISING-IN-DIGITAL-MEDIA.pdf"
    ),
    "CCPA Guidelines for Prevention of Misleading Advertisements and Endorsements, 2022": (
        "https://www.pib.gov.in/PressReleasePage.aspx?PRID=1832906"
    ),
}


def source_url(citation: str) -> str | None:
    """The verified link for a citation such as "<source label> - <heading>", if there is one."""
    for label, url in SOURCE_URLS.items():
        if citation.startswith(label):
            return url
    return None
