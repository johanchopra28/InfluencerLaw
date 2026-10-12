"""Terms of use copy. First draft for review by a qualified Indian lawyer."""
from __future__ import annotations

from app.legal import ASCI_NOTE, SENSITIVE_WARNING, THIRD_PARTY_DISCLAIMER, TRADEMARK_NOTE

TERMS_PATH = "pages/7_Terms.py"
TITLE = "Terms of use"
LEDE = "The rules for using HYPECHECK. By using the site you accept them, so please read them first."

# (heading, [paragraphs])
SECTIONS = [
    (
        "1. About HYPECHECK",
        [
            "HYPECHECK is an automated screening aid for influencer marketing in India. It reads a contract, a "
            "campaign brief or content you provide and points out matters that may need attention. It is run by "
            "the people credited in the footer of this site (the team).",
            "By using HYPECHECK you agree to these terms. If you do not agree, please do not use it.",
        ],
    ),
    (
        "2. Not legal advice",
        [
            "HYPECHECK does not give legal advice, and using it does not create a lawyer-client relationship "
            "with anyone. It does not certify that any contract, brief or content is lawful, compliant or safe. "
            "A result that finds nothing means only that nothing was found within the tool's limits.",
            "Its results are produced by artificial intelligence and can be wrong or incomplete. Have a "
            "qualified person review anything you are about to sign or publish. You alone are responsible for "
            "what you decide to do.",
        ],
    ),
    (
        "3. What you must and must not upload",
        [
            "Only submit material you are authorised to share, and use the service lawfully.",
            SENSITIVE_WARNING,
            "You are responsible for having the right to submit what you upload, including any personal data "
            "or confidential information of other people that it contains.",
        ],
    ),
    (
        "4. Third-party services",
        [
            THIRD_PARTY_DISCLAIMER,
            "Their terms and privacy policies, not these terms, govern how they handle your data. Free tiers in "
            "particular may allow a provider to use submitted content to improve its products and to have people "
            "review it. The Privacy page lists the policies to read.",
        ],
    ),
    (
        "5. Sources and standards",
        [
            "HYPECHECK relies on a small library of Indian advertising and consumer-protection sources. It may "
            "be incomplete or out of date, so check the official text of any rule before relying on it.",
            ASCI_NOTE,
        ],
    ),
    (
        "6. Name and intellectual property",
        [
            TRADEMARK_NOTE,
            "What you submit remains yours. You allow HYPECHECK, and the third-party services it uses, to "
            "process it only to produce your results. Source texts and any third-party material quoted in "
            "results belong to their owners.",
        ],
    ),
    (
        "7. No warranty and limit of liability",
        [
            "HYPECHECK is provided as it is and as available, without any warranty of accuracy, completeness, "
            "availability or fitness for a particular purpose.",
            "To the extent the law allows, the team is not liable for any loss or damage arising from your use "
            "of, or reliance on, HYPECHECK or its results, or from the acts or omissions of third-party services.",
        ],
    ),
    (
        "8. Changes and law",
        [
            "We may change the service or these terms. The date at the end of this page shows the latest "
            "update, and continuing to use HYPECHECK after a change means you accept it.",
            "These terms are governed by the laws of India, and disputes are subject to the jurisdiction of the "
            "competent courts in India.",
        ],
    ),
]
