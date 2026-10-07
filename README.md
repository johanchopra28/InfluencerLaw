# HYPECHECK

Pre-publication legal review for influencer marketing campaigns, built for India.

**Live demo: [influencerlaw.streamlit.app](https://influencerlaw.streamlit.app/)**
(the repo and deployment URL kept their original name, InfluencerLaw, so existing
links keep working; the product itself is HYPECHECK throughout.)

HYPECHECK reads a brand's contract with an influencer, the campaign brief, and the
actual content together, and flags legal risk before anything goes live. Every flag
cites the specific provision behind it. Nothing is a black box, and nothing is stated
as a definitive legal conclusion: the tool tells you what provision is potentially
implicated, why, and that a qualified lawyer should review it.

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
   This opens the landing page. Click "Run a review" to reach the tool itself.

## How it works

Six checks share one pipeline: extract the relevant claim or clause, classify it,
check it against the source material, and return a verdict with a citation.

| Check | File | What it looks for |
|---|---|---|
| Disclosure | `app/modules/disclosure.py` | Is the commercial relationship disclosed, prominently, with a permitted label? |
| ClaimCheck | `app/modules/claimcheck.py` | Does every factual or efficacy claim in the content have supporting evidence in the brief? |
| Contract Cross-Check | `app/modules/contract_cross_check.py` | Does the content violate a restriction in the influencer's contract? |
| Consumer Protection & E-Commerce | `app/modules/consumer_protection.py` | Surrogate advertising, endorsement due diligence, e-commerce misrepresentation, and the general "misleading advertisement" catch-all. |
| Comparative Advertising | `app/modules/comparative.py` | Are competitor comparisons or superiority claims substantiated? |
| Music Licensing | `app/modules/music.py` | Does the audio contain an identifiable commercial track? |

Every flag shows its full trail: detected issue, the exact evidence quote, the legal
basis, a risk level, and a suggested fix. HIGH-risk flags also say to consult a lawyer
before publishing. The model never free-hands legal reasoning: `app/legal_retrieval.py`
retrieves the actual provision text first, and every flag either cites what it
retrieved or says plainly that nothing relevant was found.

Compliance scoring (`app/scoring.py`) is a visible, fixed deduction rule shown
directly in the dashboard. Overall status is HIGH RISK, NEEDS REVISION, or POST
APPROVED.

Music licensing calls AudD's real audio-fingerprinting API. A match is reported as
identified, not cleared: *"Track identified: [artist, title]. Commercial usage rights
not verified, confirm licensing before publication."* Any flag that needs an outside
license gets a "Generate license-later document" button that produces a signable PDF
for the brand's legal team to sign off once it's actually cleared.

## Design

Paper Cream and Ink as the base palette, Cobalt as the one UI accent color. Signal
Coral, Caution Amber, and Cleared Green are reserved strictly for HIGH, MEDIUM, and
APPROVED status badges and never used decoratively. Fraunces for headings, IBM Plex
Sans for body text.

## Scope

- Jurisdiction: India. Legal sources: the ASCI Code, ASCI's Influencer Advertising
  Guidelines, the CCPA Misleading Advertisement Guidelines 2022, the Consumer
  Protection Act 2019, and the Consumer Protection (E-Commerce) Rules 2020.
- Content input: pasted caption or transcript text, or an Instagram screenshot. Video
  upload isn't supported yet; paste the transcript instead.
- Music licensing takes an audio file directly (mp3, wav, m4a, ogg). Video files
  aren't accepted for audio extraction; export or record just the audio track.
  Without an AudD key, this check is skipped and the dashboard says so, rather than
  scoring it as clear.
- AI-generated content detection isn't built yet.

## Project layout

```
app.py                                Landing page (Streamlit entry point)
pages/1_Run_Review.py                 The review tool: upload form + dashboard
app/config.py                         brand name, disclaimer text, colors, risk levels, scoring weights
app/theme.py                          typography + status-color badge helpers
app/legal_retrieval.py                retrieval layer: chunk + TF-IDF search over data/legal_sources
app/llm.py                            Gemini API wrapper (text + vision, JSON parsing)
app/parsing.py                        PDF/DOCX contract parsing, screenshot to text via vision
app/pipeline.py                       shared Issue type + citation-resolution helpers
app/scoring.py                        the compliance score rule
app/orchestrator.py                   runs all six checks, assembles the report
app/pdfgen.py                         the license-later deferral document generator
app/modules/disclosure.py             Disclosure
app/modules/claimcheck.py             ClaimCheck
app/modules/contract_cross_check.py   Contract Cross-Check
app/modules/consumer_protection.py    Consumer Protection & E-Commerce
app/modules/comparative.py            Comparative Advertising
app/modules/music.py                  Music Licensing (AudD)
data/legal_sources/*.md               cleaned source text for the retrieval layer
data/legal_raw/                       original source PDFs and raw extraction, for reference
```
