"""Copy for the AI disclosure page.

Every statement here describes what the app does today. If the AI services,
the sources, or the way results are produced change, update this page and the
date below. Do not add claims about a provider's data handling that have not
been checked against that provider's own terms. First draft for review by a
qualified Indian lawyer.
"""
from __future__ import annotations

from app.legal import ASCI_NOTE, LEGAL_UPDATED, SENSITIVE_WARNING, THIRD_PARTY_DISCLAIMER

AI_DISCLOSURE_PATH = "pages/5_AI_Disclosure.py"
TITLE = "How HYPECHECK uses AI"
LEDE = (
    "HYPECHECK uses artificial intelligence to read documents and text and point out possible legal and "
    "compliance problems. This page explains what the AI does, which services it runs on, what it cannot do, "
    "the known concerns, and where a person is still needed."
)
LAST_UPDATED = LEGAL_UPDATED

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
            "The specific models can change without notice, because the services update or retire them.",
            "What you submit is sent to these services to produce your results. The Privacy page explains how that is handled and what the free tiers allow.",
            THIRD_PARTY_DISCLAIMER,
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
        "A note on the sources, including ASCI",
        "",
        [
            ASCI_NOTE,
            "Where a result cites an ASCI provision, the results page says so. Treat it as an industry standard that is worth checking, and look to statutory sources and your own legal advice before drawing a conclusion about the law.",
            "The sources do not cover contract law, tax, intellectual property, data-protection law in general, or the rules on AI-generated media described below.",
            "They may be incomplete or out of date, and quoted passages may be shortened. Check the official text before relying on any of them.",
        ],
    ),
    (
        "What the AI cannot do",
        "",
        [
            "It can miss problems, and it can flag things that turn out to be fine.",
            "It knows only what you give it. It does not know the real relationship between the parties, what was agreed outside the document, or a platform's current rules.",
            "It never certifies that something is compliant. If a review finds nothing, that means only that nothing was found within its limits.",
            "Suggested rewrites are suggestions. They are automated text that has not been reviewed by a lawyer, a regulator or a platform, and a rewrite can introduce a new claim that needs evidence.",
        ],
    ),
    (
        "Known limitations and concerns",
        "These are the weaknesses we know about today. They come from our own testing and may be incomplete.",
        [
            "Missing clauses: HYPECHECK is much better at spotting wording that is there than noticing a clause that is absent. In our tests it rarely reported missing clauses such as a limit on liability, a survival clause, non-solicitation, a key-person clause or the self-declaration certificate for advertisements.",
            "Contract types: it was built around influencer agreements. It scored lower on agency retainers, talent management agreements and print insertion orders.",
            "Wording it can miss: open-ended use of campaign data, take-down duties with no timeframe, broad assignment or amendment wording, who bears tax, and contradictions inside a brief such as conflicting usage rights.",
            "Results can change between runs. A second run on the same text can find more or less.",
            "It can raise false alarms, for example flagging an adequate disclosure or a harmless statement.",
            "Two AI services: results can differ depending on which one answers. In our tests the backup service was weaker at catching comparisons with named competitors and false-urgency or price claims.",
            "Testing: our tests were internal, on synthetic documents, and have not been independently audited. They caught about nine in ten clearly worded single flaws, and noticeably fewer in realistic contracts with many issues. These figures are rough, come from small samples, and are not a promise.",
            "Capacity: the AI services run on free tiers with strict limits. Several people checking at once can cause errors, and a very long text (around ten thousand words) can fail every time.",
            "Files: scanned PDFs, older Word (.doc) files and spreadsheets cannot be read, and a password-protected PDF may be reported as damaged. Images are read for visible text only and can take close to a minute.",
            "Leaving a page loses uploaded files and typed text.",
            "Privacy: your submission goes to third-party services whose handling we cannot control. See the Privacy page and the warning below.",
        ],
    ),
    (
        "AI-generated media and the IT Rules amendments of 2026",
        "",
        [
            "In February 2026 India amended the Information Technology (Intermediary Guidelines and Digital Media Ethics Code) Rules, 2021 to cover synthetically generated information. The amendment was notified on 10 February 2026 and came into force on 20 February 2026.",
            "In those rules, synthetically generated information means audio, visual or audio-visual content that is artificially or algorithmically created or altered so that it appears real, for example a realistic fake video or a cloned voice. Intermediaries that offer tools to create such content must label it and embed provenance information, and large social media platforms must require users to declare it.",
            "Our reading is that these labelling rules do not apply to HYPECHECK's output. HYPECHECK produces text only, in the form of findings and suggested rewrites. It does not create, host or publish audio, visual or audio-visual content, and it is not a social media platform. The definition, as we understand it, is limited to audio, visual and audio-visual content and does not appear to extend to text. This is our own analysis and not a formal legal opinion.",
            "HYPECHECK's suggested rewrites are AI-generated text. They are presented as automated suggestions that have not been reviewed by a lawyer.",
            "If you publish AI-generated or AI-altered images, audio or video, or write scripts for such media, the platform you publish on, and these rules, may require you to declare or label it. HYPECHECK does not currently check for that. Check the rules and the platform's policies yourself.",
            "These rules may change, and further amendments may come into force later. We will update this page when we learn of changes that affect HYPECHECK.",
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
            SENSITIVE_WARNING,
        ],
    ),
]
