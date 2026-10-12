"""Privacy copy for every service, written to match what the app actually does.

Each statement below is checked against the code or against the providers' published
terms, not borrowed from a template. Do not strengthen a claim here ("not retained",
"not used for training") until it has been verified for the whole pipeline, including
the AI providers. The Gemini key this app uses is on Google's free tier, whose terms
allow submitted content to be used to improve Google's products and to be read by
human reviewers; a paid key is covered by different terms, and if the app moves to
one this copy should be revisited. First draft for review by a qualified Indian lawyer.
"""
from __future__ import annotations

from app.legal import SENSITIVE_WARNING, THIRD_PARTY_DISCLAIMER

SHORT_TITLE = "Before you upload"

SHORT_NOTICE = (
    "What you submit is sent to third-party AI services: Google Gemini, and Groq as a backup. On free tiers a "
    "provider may use submitted content to improve its products and may have people read it. We cannot "
    "warrant against any privacy infringement by those services, so check their privacy policies yourself. "
    "Do not upload sensitive contractual information: remove or redact personal data of other people, "
    "financial terms and confidential material first, and if you cannot, do not upload it. HYPECHECK itself "
    "does not save your documents or text; this app does not write them to disk or to a database."
)

FULL_TITLE = "Privacy policy"

FULL_NOTICE = [
    (
        "Who this policy covers",
        [
            "This policy explains how HYPECHECK handles what you submit. HYPECHECK is run by the people credited "
            "in the footer of this site (the team). You do not need an account, and you are not asked for your "
            "name or contact details to run a check.",
        ],
    ),
    (
        "What is handled",
        [
            "The documents, text and images you submit, the choices you enter on the forms (such as your role, "
            "platform or jurisdiction), and the results generated from them.",
            "The hosting service may also process technical data such as your IP address and browser type under "
            "its own policy. This app does not add its own advertising or analytics tools.",
        ],
    ),
    (
        "Why it is used",
        [
            "Only to produce the review you asked for and to let you export the results. It is not sold, and it "
            "is not used for unrelated purposes.",
        ],
    ),
    (
        "Third-party services and transfers abroad",
        [
            "Google Gemini API. Your text, documents and images are sent to Google to be analysed. This app uses "
            "the Gemini API on a free tier. Under Google's terms for unpaid services, the content you submit and "
            "the responses may be used to improve Google's products and machine learning technologies, and "
            "human reviewers may read and annotate it. Google states that it disconnects this data from your "
            "account before review, and its terms advise against submitting sensitive, confidential or personal "
            "information to these services.",
            "Groq. This app can use Groq as a backup if the Gemini service fails. In that case your text, "
            "documents or images are sent to Groq to be analysed instead. Groq's own terms govern how it handles "
            "them, and this app has not verified its retention or training practices.",
            "Streamlit Community Cloud hosts the site and operates the servers.",
            "These services may process data outside India.",
            THIRD_PARTY_DISCLAIMER,
        ],
    ),
    (
        "Do not upload sensitive contractual information",
        [
            SENSITIVE_WARNING,
            "By submitting material you confirm that you are authorised to share it. You are responsible for any "
            "personal data of other people that it contains.",
        ],
    ),
    (
        "What this app keeps",
        [
            "This app does not write your documents, text or results to disk or to a database, and it does not "
            "put their contents in its own logs. They are held in the app's memory for your session while the "
            "page is open, and results stay in your session until you close the page or start another check.",
            "HYPECHECK does not train AI models on what you submit. This describes this app only, not the "
            "third-party services above.",
            "If you export results, the file is generated for your session and downloaded to your device. "
            "HYPECHECK does not keep a copy. The downloaded copy is yours to store securely.",
        ],
    ),
    (
        "Security",
        [
            "We take reasonable steps to protect what you submit, and the site is served over an encrypted "
            "connection by its host. No system is completely secure, and we cannot guarantee that it is.",
        ],
    ),
    (
        "Children",
        [
            "HYPECHECK is not directed at children, and you should not submit personal data about children.",
        ],
    ),
    (
        "Your rights and complaints",
        [
            "Because this app does not store your submissions, there is usually nothing held by us to access, "
            "correct or erase. To the extent the Digital Personal Data Protection Act, 2023 or other law gives "
            "you rights, or if you have a privacy concern or complaint, contact us using the details below. For "
            "data held by a third-party service, contact that service under its own policy.",
        ],
    ),
    (
        "Limits of this policy",
        [
            "This policy describes how the app works today. It is not a guarantee about the third-party "
            "services above, whose terms can change. HYPECHECK provides automated assistance to identify "
            "potential issues. Its results should be reviewed before they are relied upon, and it does not "
            "guarantee legal compliance or replace qualified legal advice.",
            "We may update this policy. The date at the end of this page shows the latest update.",
        ],
    ),
]
