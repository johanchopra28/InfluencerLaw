# HYPECHECK

Pre-publication legal review for influencer marketing campaigns, built for India.

**Live demo: [influencerlaw.streamlit.app](https://influencerlaw.streamlit.app/)**
(the repo and deployment URL kept their original name, InfluencerLaw, so existing
links keep working; the product itself is HYPECHECK throughout.)

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
   one at https://aistudio.google.com/apikey). Add an AudD API key too if you want
   music licensing checks.
   ```
   GEMINI_API_KEY=...
   AUDD_API_KEY=...          # optional, enables music licensing
   ```
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
| Contract check | `pages/1_Contract_Check.py` | A contract (PDF or DOCX), optionally a caption to test against it | Potentially risky clauses, expected clauses that are missing, missing or unclear commercial terms, and (with a caption) whether the content breaks the contract's own rules |
| Campaign check | `pages/2_Campaign_Check.py` | The brief, claims and evidence, planned deliverables, planned disclosure | Claim substantiation, disclosure plan, comparisons, consumer-protection exposure |
| Content check | `pages/3_Content_Check.py` | A caption or transcript (or a screenshot), optional evidence and audio track | Disclosure, claim substantiation, comparisons, consumer-protection exposure, music licensing |

Each service runs only the checks that make sense for its inputs
(`app/orchestrator.py`), scores them together, and shows the results on the same page.

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
| Music Licensing | `app/modules/music.py` |

Every flag shows its full trail: the evidence quote, the legal basis, why it was
flagged, a risk level and a suggested fix. High-risk flags also say to consult a lawyer.
The model never free-hands legal reasoning: `app/legal_retrieval.py` retrieves the
actual provision text first, and every scored flag cites what was retrieved. Contract
review keeps terms that no provision covers (usage rights, payment timing, termination)
in a separate "points to confirm" list that is never scored.

Compliance scoring (`app/scoring.py`) is a visible, fixed deduction rule shown in the
results. Overall status is High risk, Needs revision, or Post approved.

Music licensing calls AudD's audio-fingerprinting API. A match is reported as
identified, not cleared, and any flag that needs an outside license offers a
license-later PDF for the brand's legal team to sign off once it is actually cleared.

## Design

Flat editorial style: cream and blush bands, Georgia display type, Helvetica body text,
hairline rules and square controls. Red, mustard and green are used only for risk
status. The shared look lives in `app/site.py`; the landing page adds its own styles in
`app/landing.py`.

## Scope

- Jurisdiction: India. Legal sources: the ASCI Code, ASCI's Influencer Advertising
  Guidelines, the CCPA Misleading Advertisement Guidelines 2022, the Consumer
  Protection Act 2019, and the Consumer Protection (E-Commerce) Rules 2020.
- Content input: pasted caption or transcript text, or an Instagram screenshot. Video
  upload isn't supported yet; paste the transcript instead.
- Contracts: text-based PDF or DOCX. Scanned PDFs aren't supported yet.
- Music licensing takes an audio file directly (mp3, wav, m4a, ogg). Without an AudD
  key this check is skipped and the results say so, rather than scoring it as clear.
- A legal resource repository and AI-generated content detection aren't built yet.

## Project layout

```
app.py                                Landing page (Streamlit entry point)
pages/1_Contract_Check.py             Contract service
pages/2_Campaign_Check.py             Campaign service
pages/3_Content_Check.py              Content service
app/site.py                           shared look: palette, base styles, navigation, page header
app/landing.py                        landing page markup and styles
app/dashboard.py                      results display shared by the three services
app/orchestrator.py                   one runner per service
app/config.py                         brand name, disclaimer text, risk levels, scoring weights
app/legal_retrieval.py                retrieval layer: chunk + TF-IDF search over data/legal_sources
app/llm.py                            Gemini API wrapper (text + vision, JSON parsing, retries)
app/parsing.py                        PDF/DOCX parsing, screenshot to text via vision
app/pipeline.py                       shared Issue type + citation-resolution helpers
app/scoring.py                        the compliance score rule
app/pdfgen.py                         the license-later deferral document generator
app/modules/                          the individual checks (see the table above)
data/legal_sources/*.md               cleaned source text for the retrieval layer
data/legal_raw/                       original source PDFs and raw extraction, for reference
```
