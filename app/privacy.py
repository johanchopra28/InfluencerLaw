"""Privacy copy for every service, written to match what the app actually does.

Each statement below is checked against the code or against Google's published
terms for the Gemini API, not borrowed from a template. Do not strengthen a
claim here ("not retained", "not used for training") until it has been verified
for the whole pipeline, including the AI provider. The Gemini key this app uses
is on Google's free tier, whose terms allow submitted content to be used to
improve Google's products and to be read by human reviewers; a paid key is
covered by different terms, and if the app moves to one this copy should be
revisited.
"""
from __future__ import annotations

SHORT_TITLE = "Your data, your control"

SHORT_NOTICE = (
    "HYPECHECK does not save your documents or text. They are held in memory while you use "
    "the page, and this app does not write them to disk or to a database. To produce your "
    "results, what you submit is sent to Google's Gemini API, which this app uses on a free "
    "tier. Under Google's terms for that tier, submitted content may be used to improve "
    "Google's products and may be read by human reviewers. If that service is unavailable and a "
    "backup is configured, the same material may be sent to Groq instead. Only upload material you are "
    "authorised to share, and avoid "
    "unnecessary personal information, passwords and confidential third-party material."
)

FULL_TITLE = "Privacy and data handling"

FULL_NOTICE = [
    (
        "What HYPECHECK does with your submission",
        [
            "HYPECHECK processes the documents and content you submit to produce the review "
            "you asked for. Each service asks only for the information that review needs. You "
            "do not need an account, and you are not asked for contact details to run a check.",
            "Your submission may contain confidential commercial information or personal data. "
            "Do not upload anything you are not authorised to share.",
        ],
    ),
    (
        "What this app keeps",
        [
            "This app does not write your documents, text or results to disk or to a database, "
            "and it does not put their contents in its own logs. They are held in the app's "
            "memory for your session while the page is open. Results stay in your session "
            "until you close the page or start another check.",
            "If you export results, the file is generated for your session and downloaded to "
            "your device. HYPECHECK does not keep a copy. The downloaded copy is yours to store "
            "securely.",
            "The app is hosted on Streamlit Community Cloud, which operates the servers. How "
            "Streamlit handles infrastructure data is described in its own privacy policy.",
        ],
    ),
    (
        "Third-party services",
        [
            "Google Gemini API. Your text, documents and images are sent to Google to be "
            "analysed. This app uses the Gemini API on a free tier. Under Google's terms for "
            "unpaid services, the content you submit and the responses may be used to improve "
            "Google's products and machine learning technologies, and human reviewers may read "
            "and annotate it. Google states that it disconnects this data from your account "
            "before review, and its terms advise against submitting sensitive, confidential or "
            "personal information to these services.",
            "Groq. This app can use Groq as a backup if the Gemini service fails. In that case your "
            "text, documents or images are sent to Groq to be analysed instead. Groq's own terms govern "
            "how it handles them, and this app has not verified its retention or training practices.",
        ],
    ),
    (
        "What this means for you",
        [
            "Because of the way the analysis service is used today, do not upload contracts or "
            "documents whose contents you could not share with a third-party service. If you "
            "need to review confidential material, remove the sensitive parts first or ask the "
            "person running this app whether it has been moved to a service with stronger "
            "data terms.",
        ],
    ),
    (
        "Limits of this notice",
        [
            "This notice describes how the app works today. It is not a guarantee about the "
            "third-party services above, whose terms can change. HYPECHECK provides automated "
            "assistance to identify potential issues. Its results should be reviewed before "
            "they are relied upon, and it does not guarantee legal compliance or replace "
            "qualified legal advice.",
        ],
    ),
]
