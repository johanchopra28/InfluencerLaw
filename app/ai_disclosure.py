"""Copy for the AI disclosure page.

Every statement here describes what the app does today. If the AI services,
the sources, or the way results are produced change, update this page and the
date below. Do not add claims about a provider's data handling that have not
been checked against that provider's own terms.
"""
from __future__ import annotations

AI_DISCLOSURE_PATH = "pages/5_AI_Disclosure.py"
TITLE = "How HYPECHECK uses AI"
LEDE = (
    "HYPECHECK uses artificial intelligence to read documents and text and point out possible legal and "
    "compliance problems. This page explains what the AI does, which services it runs on, what it cannot do, "
    "and where a person is still needed."
)
LAST_UPDATED = "12 October 2026"

# (heading, short intro paragraph or "", bullet points)
SECTIONS = [
    (
        "What the AI does",
        "",
        [
            "Contract check: reads a contract and flags clauses that may be one-sided, missing or risky. It can suggest wording as a starting point for discussion.",
            "Campaign check: reads a campaign brief and the details you enter, and flags concerns about disclosure, claims, deliverables, rights and permissions.",
            "Content check: reads a caption, script or the text found in an image, and flags missing disclosures, unsupported claims and similar issues. It can propose a rewritten caption.",
            "When you upload a brief, the AI also reads it to fill in the campaign form for you to check.",
            "For images, it reads only the words that appear in the picture. It does not judge the visuals.",
        ],
    ),
    (
        "Which AI services are used",
        "",
        [
            "Google Gemini is the main service that analyses your text.",
            "If Gemini is unavailable, HYPECHECK may use Groq as a backup, running an open-source model. The results page does not currently say which service answered a particular request.",
            "If you add an audio track, AudD identifies the music. It is an audio recognition service, not a language model.",
            "The specific models can change without notice, because the services update or retire them.",
            "What you submit is sent to these services to produce your results. The Privacy page explains how that is handled and what the free tiers allow.",
        ],
    ),
    (
        "How the answers are produced",
        "",
        [
            "Legal findings rest on a small library of Indian sources: the ASCI Code, the ASCI Influencer Advertising Guidelines, the CCPA Guidelines for Prevention of Misleading Advertisements and Endorsements 2022, the Consumer Protection Act 2019 and the Consumer Protection (E-Commerce) Rules 2020.",
            "For each request, HYPECHECK first finds the passages from those sources that best match your text and gives only those to the AI. Each legal finding names the passage it relies on.",
            "Contract terms such as payment, exclusivity, usage rights, termination and liability are checked against a drafting checklist, not against a law. These findings carry a Commercial term tag, cite no legal source, and are marked for human review.",
            "The AI is instructed to describe potential issues, not to give final legal conclusions.",
        ],
    ),
    (
        "What the AI cannot do",
        "",
        [
            "It can miss problems, and it can flag things that turn out to be fine. It is most likely to miss clauses that are absent from a contract, and wording in less common contract types such as agency, talent management and print agreements.",
            "Results can change if you run the same text twice.",
            "It knows only what you give it. It does not know the real relationship between the parties, what was agreed outside the document, or a platform's current rules.",
            "Its sources cover Indian advertising and consumer-protection rules. They do not cover contract law, tax, intellectual property or data-protection law in general.",
            "It does not check whether a cited source is still current. Check the official text before relying on it.",
            "It never certifies that something is compliant. If a review finds nothing, that means only that nothing was found within its limits.",
            "Suggested rewrites are suggestions. They have not been reviewed by a lawyer, a regulator or a platform, and a rewrite can introduce a new claim that needs evidence.",
        ],
    ),
    (
        "Where a person is still needed",
        "",
        [
            "No person reviews your results before you see them.",
            "HYPECHECK does not replace a qualified lawyer. Have a qualified person check anything marked High priority or Needs human review, and anything you are about to sign or publish.",
        ],
    ),
    (
        "Your data and the AI",
        "",
        [
            "HYPECHECK does not train AI models on what you submit.",
            "The outside services listed above handle your submission under their own terms. On free tiers, a provider may use submitted content to improve its products and may have people review it. This app has not verified every provider's practices.",
            "Avoid submitting material you are not authorised to share, and think carefully before uploading a confidential contract.",
        ],
    ),
]
