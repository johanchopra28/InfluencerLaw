# HYPECHECK — Pre-Publication Legal Review Engine (India)

**Live demo: [influencerlaw.streamlit.app](https://influencerlaw.streamlit.app/)**
*(the repo and live URL still say "influencerlaw" — that's the original project name,
kept as-is so existing shared links don't break; the product itself is now branded
HYPECHECK throughout the app, per HYPECHECK_SPEC.md.)*

HYPECHECK is a screening tool, not legal advice. It reviews an influencer marketing
campaign for legal risk *before* it's published, by cross-referencing three inputs —
the brand's contract with the influencer, the campaign brief, and the actual content
(caption/transcript/screenshot) — against the ASCI Code, ASCI's Influencer Advertising
Guidelines, the CCPA Misleading Advertisement Guidelines 2022, the Consumer Protection
Act 2019, and the Consumer Protection (E-Commerce) Rules 2020. It never states a
definitive legal conclusion — only "this provision is potentially implicated, here's
why, consult a lawyer" — and that framing is enforced in every module's prompt, not
just the UI copy.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and add a free Gemini API key (required -- no
   card needed, get one at https://aistudio.google.com/apikey) and, optionally,
   an AudD API key for the music licensing module:
   ```
   GEMINI_API_KEY=...
   AUDD_API_KEY=...          # optional -- get a free-tier key at https://dashboard.audd.io/
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```
   This opens the landing/marketing page. Click "Run a review" (or use the
   sidebar) to reach the actual tool at `pages/1_Run_Review.py`.

## How it works

Six modules share one pipeline pattern — **extract → classify → check against
source → verdict with citation** — implemented once and applied six ways:

| Module | File | What it checks |
|---|---|---|
| Disclosure | `app/modules/disclosure.py` | Is the commercial relationship disclosed, prominently, with a permitted label? |
| ClaimCheck (flagship) | `app/modules/claimcheck.py` | Does every factual/efficacy claim in the content have supporting evidence in the brief? |
| Contract ↔ Content Cross-Check | `app/modules/contract_cross_check.py` | Does the content violate a restriction clause in the influencer's contract? |
| Consumer Protection & E-Commerce | `app/modules/consumer_protection.py` | Surrogate advertising, endorsement due diligence, e-commerce/transactional misrepresentation, and the general CPA 2019 "misleading advertisement" catch-all. |
| Comparative Advertising | `app/modules/comparative.py` | Are competitor comparisons/superiority claims substantiated? |
| Music Licensing | `app/modules/music.py` | Does the audio contain an identifiable commercial track (via AudD)? |

Every flag is traceable through: **Detected issue → Evidence (exact quote) →
Legal basis (retrieved provision) → Risk level → Suggested fix**, and every HIGH-risk
issue additionally and explicitly says to consult a lawyer before publishing. The LLM
never free-hands legal reasoning — `app/legal_retrieval.py` retrieves the actual
statutory/guideline text chunk first (TF-IDF over `data/legal_sources/*.md`), and every
module must cite a retrieved chunk or explicitly say no relevant provision was found.

A persistent disclaimer banner ("HYPECHECK is a screening tool, not legal advice...")
appears on both the landing page and every dashboard view (`app/config.py`
`DISCLAIMER_TEXT`) — not a dismissible toast.

Compliance scoring (`app/scoring.py`) is a simple, visible deduction rule shown
in the dashboard itself — not a black box. Overall status is one of HIGH RISK /
NEEDS REVISION / POST APPROVED.

Music Licensing is real, not mocked: it calls AudD's audio-fingerprinting API and is
built to never overclaim. A match is reported as *"Track identified: [artist –
title]. Commercial usage rights not verified — confirm licensing before
publication"* — never "cleared". Any issue that needs an external license
(currently: an identified track) exposes a **"Generate license-later
document"** button (`app/pdfgen.py`) that produces a signable PDF acknowledging
the flag is unresolved, for the brand/legal team to sign off once it's
actually cleared. This is a deferral document, not a purchase, checkout, or
licensing marketplace of any kind.

## Design

Brand palette and typography (`app/theme.py`, `.streamlit/config.toml`) follow
HYPECHECK_SPEC.md Section 5: Paper Cream / Ink base, Cobalt as the one UI accent color,
Signal Coral / Caution Amber / Cleared Green reserved strictly for HIGH / MEDIUM /
APPROVED status badges (never reused decoratively), Fraunces for headings and IBM Plex
Sans for body text. The spec's full illustrated design system (pen-and-ink character
illustrations, a Next.js/Tailwind rebuild) is **not** built here — this is a palette/
typography/copy port onto the existing Streamlit app, not the from-scratch rebuild the
spec describes; see "What wasn't ported" below.

## Scope (v1)

- Jurisdiction: India only.
- Legal sources: ASCI Code, ASCI Influencer Guidelines, CCPA Misleading Advertisement
  Guidelines 2022, Consumer Protection Act 2019 (Sections 2(28), 21, 89), Consumer
  Protection (E-Commerce) Rules 2020 (Rules 4, 5) — nothing else.
- Content input: pasted caption/transcript text, or an Instagram screenshot
  (read via Gemini vision, no OCR binary required). Video upload isn't
  supported for content — paste the transcript instead.
- Music licensing accepts an audio file directly (mp3/wav/m4a/ogg). Video files
  aren't accepted for audio extraction (no ffmpeg in this build) -- export or record
  just the audio track. Without `AUDD_API_KEY` set, this module is skipped and the
  dashboard says so explicitly rather than scoring it as clear.
- AI-generated content flagging is not built in this version.

### What wasn't ported from HYPECHECK_SPEC.md

The spec describes a considerably larger build than what's here. Explicitly not
built, by choice, when the spec was folded onto this existing Streamlit app rather
than triggering a from-scratch rebuild:
- **Side A ("Check a Claim")** — the consumer-facing, web-search-based claim
  verification tool. This app is Side B only.
- **The illustrated design system** — pen-and-ink character illustrations,
  loading-state sketches, etc. Colors and fonts are ported; illustration is not.
- **Next.js/TypeScript rebuild** — Node.js isn't installed in this environment;
  this stays a Python/Streamlit app.
- **4-tier severity (low/medium/high/critical)** — kept the existing 3-tier
  (HIGH/MEDIUM/LOW) + NONE instead of restructuring every module's data shape.
- **Separate `/privacy` and `/terms` pages** — the disclaimer/no-liability language
  lives in the persistent banner and the scope-honesty section instead of dedicated
  routes.
- Comparative Advertising, Music Licensing, the Fix Campaign rewrite view, and the
  0–100 compliance score are all things the spec lists as later-phase/out-of-scope
  for a fresh build — but they already existed and worked here, so they were kept
  rather than removed.

## Project layout

```
app.py                                Landing/marketing page (Streamlit entry point)
pages/1_Run_Review.py                 The actual tool: upload form + dashboard
app/config.py                         brand name, disclaimer text, colors, risk levels, scoring weights (all visible)
app/theme.py                          Fraunces/IBM Plex Sans CSS injection + status-color badge helper
app/legal_retrieval.py                RAG layer: chunk + TF-IDF retrieval over data/legal_sources
app/llm.py                            Gemini API wrapper (text + vision, JSON parsing) -- free tier, no card needed
app/parsing.py                        PDF/DOCX contract parsing, screenshot -> text via vision
app/pipeline.py                       shared Issue type + citation-resolution helpers
app/scoring.py                        the compliance score rule
app/orchestrator.py                   runs all six modules, assembles the report
app/pdfgen.py                         the "license later" deferral document generator
app/modules/disclosure.py             Disclosure
app/modules/claimcheck.py             ClaimCheck
app/modules/contract_cross_check.py   Contract Cross-Check
app/modules/consumer_protection.py    Consumer Protection & E-Commerce
app/modules/comparative.py            Comparative Advertising
app/modules/music.py                  Music Licensing (AudD)
data/legal_sources/*.md               cleaned ASCI/CCPA/CPA/E-Commerce Rules source text (the RAG corpus)
data/legal_raw/                       original downloaded PDFs + raw extraction (reference only)
```
