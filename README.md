# HYPECHECK

Pre-publication legal review for influencer marketing campaigns, built for India.

**Live demo: [influencerlaw.streamlit.app](https://influencerlaw.streamlit.app/)**
(the repo and deployment URL kept their original name, InfluencerLaw, so existing
links keep working; the product itself is HYPECHECK throughout.)

By Vanshika Verma ([@vanshikaverma2-7](https://github.com/vanshikaverma2-7)) and Johan Chopra ([@johanchopra28](https://github.com/johanchopra28)).

HYPECHECK reviews the three things an influencer campaign is made of, a contract, a
campaign brief and the content itself, and flags legal risk before anything goes live.
Every flag cites the specific provision behind it. Nothing is a black box, and nothing
is stated as a definitive legal conclusion: the tool tells you what provision is
potentially implicated, why, and that a qualified lawyer should review it.

HYPECHECK is a screening tool, not legal advice.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and add a free Gemini API key (no card needed, get
   one at https://aistudio.google.com/apikey).
   ```
   GEMINI_API_KEY=...
   GROQ_API_KEY=...          # optional backup if Gemini fails (https://console.groq.com/keys)
   ```
   On Streamlit Community Cloud, put the same two keys in the app's Secrets instead
   (never in the repo). Keys are read from the environment first, then from Secrets.
   Gemini (`gemini-flash-lite-latest`) answers first; Groq (`openai/gpt-oss-120b`, and a
   vision model for images) takes over if Gemini fails. Set `HYPECHECK_PROVIDER=groq` to
   flip the order. If both fail, the page says why in plain words and never shows the
   document text in logs.
3. Run it:
   ```bash
   streamlit run app.py
   ```

## The three services

The landing page is purely informational: what HYPECHECK does, how each service works
and what it cannot do. Nothing is asked for there. Each service is its own page and
asks only for the fields it needs.

| Service | Page | What it takes | What it checks |
|---|---|---|---|
| Contract check | `pages/1_Contract_Check.py` | A contract (PDF, DOCX or TXT), optional role, jurisdiction and focus areas, optionally a caption to test against it | Potentially risky or one-sided clauses (legal flags with a cited provision, and commercial terms marked for human review), suggested drafting directions, and (with a caption) whether the content breaks the contract's own rules |
| Campaign check | `pages/2_Campaign_Check.py` | A brief (PDF, DOCX or TXT) that pre-fills the form, or the details entered by hand: campaign type, deliverables, requirements, supporting materials | Claim substantiation, disclosure plan, comparisons, consumer-protection exposure |
| Content check | `pages/3_Content_Check.py` | Pasted text, a file, or an image of a post; optional format, platform, relationship and context | Disclosure, claim substantiation, comparisons, consumer-protection exposure, plus a suggested revised caption with the changes highlighted (`app/modules/content_revision.py`) |

Each service runs only the checks that make sense for its inputs
(`app/orchestrator.py`), groups the flags by priority, and shows the results on the same page. There is no score and no "approved" status: the tool never certifies content as compliant.

## How the checks work

Every check follows one pipeline: extract the relevant claim or clause, classify it,
check it against retrieved source text, and return a verdict with a citation.

| Check | File |
|---|---|
| Contract Review | `app/modules/contract_review.py` |
| Contract Compliance (content against the contract) | `app/modules/contract_cross_check.py` |
| Advertising Disclosure | `app/modules/disclosure.py` |
| ClaimCheck | `app/modules/claimcheck.py` |
| Comparative Advertising | `app/modules/comparative.py` |
| Consumer Protection & E-Commerce | `app/modules/consumer_protection.py` |

Every flag shows its full trail: the evidence quote, the legal basis, why it was
flagged, a risk level and a suggested fix. High-risk flags also say to consult a lawyer.
The model never free-hands legal reasoning: `app/legal_retrieval.py` retrieves the
actual provision text first, and every legal flag cites what was retrieved. Contract
review (`app/modules/contract_review.py`) assesses a fixed 12-topic checklist on every
run. Commercial problems that no provision covers (payment, exclusivity, usage rights,
termination, liability) are still scored, but they carry a "Commercial term" tag, always
need human review, and cite no legal source. Quoted clauses are checked against the
contract text.

Results (`app/report.py`) are grouped as High, Medium and Low priority, with the criteria
shown on the page. A finding is tagged Potential risk, Missing information or Needs human
review. Results can be exported as a PDF generated for the session (`app/export.py`).

Suggested wording of any kind (claim and comparative rewrites, contract drafting
directions, the suggested caption revision, and the PDF export) is labelled as a starting
point that needs a contextualised factual and legal check and must not be used as is.
Drafting directions also carry a line asking for legal advice specific to the context and
the contractual dealing. A result that cites only an ASCI provision says that ASCI is a
private self-regulatory body and asks the reader to follow it up with the relevant law
and professional legal advice.

## Legal and policy pages

All of this copy is a first draft for review by a qualified Indian lawyer. Each page
reads from a module in `app/`, and the shared wording lives in `app/legal.py` so it
stays consistent. Update `LEGAL_UPDATED` there whenever any of it changes.

- **Terms of use** (`app/terms.py`): screening tool only, no lawyer-client relationship,
  no warranty, user responsibility, the name notice (no trademark claimed).
- **Privacy policy** (`app/privacy.py`): what is sent to Gemini, Groq and Streamlit,
  that nothing is written to disk by the app, that submissions are not used to train
  models by HYPECHECK, and a warning not to upload sensitive contractual information.
  Providers handle data under their own terms, and users must check those themselves.
  Revisit it if the app moves to a paid Gemini key.
- **AI disclosure** (`app/ai_disclosure.py`): what the AI does and cannot do, the
  services, the legal sources (including ASCI's status), known limitations from our own
  testing, and an analysis of the February 2026 IT Rules amendments on synthetic media
  (our reading is that they do not reach a text-only tool; not a formal opinion).
- **FAQ** (`app/faq.py`) and a shared **footer** (`app/footer.py`) on every page.

`CONTACT_EMAIL` in `app/legal.py` is empty on purpose: the contact line stays hidden
until a real contact or grievance address is set.

## Design

Flat editorial style: cream and blush bands, Georgia display type, Helvetica body text,
hairline rules and square controls. Red, mustard and green are used only for risk
status. The shared look lives in `app/site.py`; the landing page adds its own styles in
`app/landing.py`.

## Scope

- Jurisdiction: India. Legal sources: the ASCI Code, ASCI's Influencer Advertising
  Guidelines, the CCPA Misleading Advertisement Guidelines 2022, the Consumer
  Protection Act 2019, and the Consumer Protection (E-Commerce) Rules 2020.
- Content input: pasted text, a PDF, DOCX or TXT file, or an image (only text visible in
  the image is read). Video upload isn't supported yet; paste the script instead.
- Documents: text-based PDF, DOCX or TXT up to 25 MB. Scanned PDFs, .doc, Excel and
  PowerPoint aren't supported yet, and the page says so. Uploads and typed text are
  cleared when you leave a page.
- Music and audio checking, and other audio features, are not part of HYPECHECK.
- The IT Rules (2026) on AI-generated media and a legal resource repository aren't built
  into the checks.
- Known weaknesses are listed on the AI disclosure page: missing clauses are rarely
  detected, results can vary between runs, accuracy is lower on agency, talent and print
  contracts, and free-tier limits mean several simultaneous checks can fail.

## Deploying

The app is deployed on Streamlit Community Cloud. Cloud keeps old imported modules after a
push, so `requirements.txt` carries a `# restart-marker:` comment; change it with any push
that edits Python modules to force a clean restart.

## Project layout

```
app.py                                Landing page (Streamlit entry point)
pages/1_Contract_Check.py             Contract service
pages/2_Campaign_Check.py             Campaign service
pages/3_Content_Check.py              Content service
pages/4_Privacy.py                    Privacy policy
pages/5_AI_Disclosure.py               AI disclosure: what the AI does, what it runs on, its limits
pages/6_FAQ.py                         Frequently asked questions
pages/7_Terms.py                       Terms of use
app/site.py                           shared look: palette, base styles, navigation, page header
app/landing.py                        landing page markup and styles
app/dashboard.py                      results display shared by the three services
app/orchestrator.py                   one runner per service
app/config.py                         brand name, disclaimer text, risk levels
app/legal_retrieval.py                retrieval layer: chunk + TF-IDF search over data/legal_sources
app/llm.py                            Gemini API wrapper with a Groq fallback (text + vision, JSON parsing, retries)
app/parsing.py                        PDF/DOCX/TXT reading with clear errors, screenshot to text via vision
app/pipeline.py                       shared Issue type + citation-resolution helpers
app/report.py                         groups findings by priority (no score)
app/export.py                         PDF export of results
app/privacy.py                        privacy copy
app/ai_disclosure.py                   AI disclosure copy
app/faq.py                            FAQ copy
app/terms.py                          terms of use copy
app/legal.py                          shared legal wording (third-party disclaimer, sensitive-data warning, ASCI note, name notice)
app/footer.py                         the shared footer
app/sources.py                        verified links to legal sources
app/modules/                          the individual checks (see the table above)
data/legal_sources/*.md               cleaned source text for the retrieval layer
data/legal_raw/                       original source PDFs and raw extraction, for reference
```
