"""Copy for the FAQ page. Answers describe what the app does today; keep them in step with the pages."""
from __future__ import annotations

FAQ_PATH = "pages/6_FAQ.py"
TITLE = "Frequently asked questions"
LEDE = "Short answers about what HYPECHECK does, how to use it, and how to read its results."

# (group heading, [(question, answer), ...])
GROUPS = [
    (
        "The basics",
        [
            (
                "What is HYPECHECK?",
                "A screening tool for influencer marketing in India. You give it a contract, a campaign brief or a caption, and it points out things that may need attention before you sign or publish.",
            ),
            (
                "Is this legal advice?",
                "No. It is an automated aid that flags possible problems. It does not replace a qualified lawyer, and it cannot tell you that something is legal or safe.",
            ),
            (
                "Who is it for?",
                "Creators, brands, agencies and managers who want a second look before signing an agreement, approving a brief or posting content.",
            ),
            (
                "Do I need an account? Does it cost anything?",
                "There is no sign-up, no contact details are asked for, and there is no charge to use it today.",
            ),
            (
                "Which rules does it check against?",
                "Indian advertising and consumer-protection sources: the ASCI Code, the ASCI Influencer Advertising Guidelines, the CCPA Guidelines for Prevention of Misleading Advertisements and Endorsements 2022, the Consumer Protection Act 2019 and the Consumer Protection (E-Commerce) Rules 2020. It does not cover other countries or other areas of law.",
            ),
        ],
    ),
    (
        "Using it",
        [
            (
                "What files can I upload?",
                "PDF, Word (.docx) or plain text (.txt) files up to 25 MB, ideally with searchable text. On the Captions page you can also upload a PNG or JPG image of a post.",
            ),
            (
                "Why was my file rejected?",
                "Scanned PDFs with no selectable text cannot be read yet, and older Word (.doc) files and spreadsheets are not supported. Save the file as a searchable PDF or .docx and try again.",
            ),
            (
                "Can I check a video or a Reel?",
                "Not directly. Paste its script or transcript on the Captions page.",
            ),
            (
                "Do I have to fill in every field?",
                "No. Only fields marked required must be filled in. The rest are optional and help tailor the review.",
            ),
            (
                "How long does a check take?",
                "Usually a few seconds to about a minute. Checks on images take longest.",
            ),
            (
                "Can I keep a copy of the results?",
                "Yes. Use Export results (PDF) at the bottom of the results. The file is created for your session and downloaded to your device.",
            ),
            (
                "I left the page and my text or file disappeared. Why?",
                "Uploaded files are cleared when you leave a page, and typed text may be lost too. Finish a check before moving to another page.",
            ),
        ],
    ),
    (
        "Reading the results",
        [
            (
                "What do High, Medium and Low mean?",
                "High means the wording could expose someone to a misleading advertisement or an undisclosed endorsement, clearly conflicts with a cited provision, or removes a core protection in a contract. Medium means it is unclear, one-sided or potentially misleading enough to review. Low is a minor point.",
            ),
            (
                "What does Commercial term mean?",
                "A contract term that is one-sided or missing, such as payment, exclusivity, usage rights, termination or liability. HYPECHECK's legal sources do not cover these subjects, so no legal source is cited. It is flagged for a person to judge, not as a breach of any rule.",
            ),
            (
                "What does Needs human review mean?",
                "The point is ambiguous, depends on facts or law outside HYPECHECK's sources, or the AI is unsure. Have a qualified person look at it.",
            ),
            (
                "It found nothing. Does that mean my document is fine?",
                "No. It means nothing was found within the tool's limits. It can miss problems, so a clean result is not approval.",
            ),
            (
                "Can I rely on the suggested rewrites?",
                "Treat them as starting points. They have not been reviewed by a lawyer, a regulator or a platform, and a rewrite can add a new claim that needs evidence.",
            ),
            (
                "I ran the same text twice and got different results. Is that a bug?",
                "It is a known limit of AI. Small differences between runs are normal, so do not rely on a single run alone.",
            ),
            (
                "It flagged something that is fine, or missed something real. What now?",
                "Both can happen. Use the results as a screening step, and ask a qualified person to review anything you are about to sign or publish.",
            ),
        ],
    ),
    (
        "Privacy and AI",
        [
            (
                "Is my document stored?",
                "This app does not write your documents or text to disk or to a database. Your submission is sent to outside AI services to produce the results, and the Privacy page explains how that is handled.",
            ),
            (
                "Which AI does it use?",
                "Google Gemini, with Groq as a backup if Gemini is unavailable. The AI disclosure page has the details.",
            ),
            (
                "Should I upload a confidential contract?",
                "Think carefully first. On free tiers, an AI provider may use submitted content to improve its products and may have people review it. Remove sensitive parts, or avoid uploading material you are not authorised to share.",
            ),
        ],
    ),
    (
        "When something goes wrong",
        [
            (
                "It says the analysis service rejected the site's API key.",
                "That is a setup problem on the site, not something you did. Trying again will not help until the site owner fixes it.",
            ),
            (
                "It says the analysis service is busy or over its limit.",
                "Too many checks were running at once. Wait a minute and try again. Everything you entered stays on the page.",
            ),
            (
                "A very long text fails every time.",
                "Very long texts, around ten thousand words, can fail. Try a shorter version or split it into parts.",
            ),
        ],
    ),
]
