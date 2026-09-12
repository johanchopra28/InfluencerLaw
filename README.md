# InfluencerLaw — Pre-Publication Legal Review Engine (India)

Reviews an influencer marketing campaign for legal risk *before* it's published, by
cross-referencing three inputs — the brand's contract with the influencer, the
campaign brief, and the actual content (caption/transcript/screenshot) — against
the ASCI Code, ASCI's Influencer Advertising Guidelines, and the CCPA Misleading
Advertisement Guidelines, 2022.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and add your Anthropic API key (required) and,
   optionally, an AudD API key for the music licensing module:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   AUDD_API_KEY=...          # optional -- get a free-tier key at https://dashboard.audd.io/
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```
   This opens the landing/marketing page. Click "Run a review" (or use the
   sidebar) to reach the actual tool at `pages/1_Run_Review.py`.

## How it works

Five modules share one pipeline pattern — **extract → classify → check against
source → verdict with citation** — implemented once and applied five ways:

| Module | File | What it checks |
|---|---|---|
| A — Disclosure | `app/modules/disclosure.py` | Is the commercial relationship disclosed, prominently, with a permitted label? |
| B — ClaimCheck (flagship) | `app/modules/claimcheck.py` | Does every factual/efficacy claim in the content have supporting evidence in the brief? |
| C — Contract ↔ Content Cross-Check | `app/modules/contract_cross_check.py` | Does the content violate a restriction clause in the influencer's contract? |
| D — Comparative Advertising | `app/modules/comparative.py` | Are competitor comparisons/superiority claims substantiated? |
| E — Music Licensing | `app/modules/music.py` | Does the audio contain an identifiable commercial track (via AudD)? |

Every flag is traceable through: **Detected issue → Evidence (exact quote) →
Legal basis (retrieved provision) → Risk level → Suggested fix.** The LLM never
free-hands legal reasoning — `app/legal_retrieval.py` retrieves the actual ASCI/CCPA
text chunk first (TF-IDF over `data/legal_sources/*.md`), and every module must
cite a retrieved chunk or explicitly say no relevant provision was found.

Compliance scoring (`app/scoring.py`) is a simple, visible deduction rule shown
in the dashboard itself — not a black box.

Module E is real, not mocked: it calls AudD's audio-fingerprinting API and is
built to never overclaim. A match is reported as *"Track identified: [artist –
title]. Commercial usage rights not verified — confirm licensing before
publication"* — never "cleared". Any issue that needs an external license
(currently: an identified track) exposes a **"Generate license-later
document"** button (`app/pdfgen.py`) that produces a signable PDF acknowledging
the flag is unresolved, for the brand/legal team to sign off once it's
actually cleared. This is a deferral document, not a purchase, checkout, or
licensing marketplace of any kind.

## Scope (v1)

- Jurisdiction: India only.
- Legal sources: ASCI Code, ASCI Influencer Guidelines, CCPA Misleading
  Advertisement Guidelines 2022 — nothing else.
- Content input: pasted caption/transcript text, or an Instagram screenshot
  (read via Claude vision, no OCR binary required). Video upload isn't
  supported for content — paste the transcript instead.
- Music licensing (Module E) accepts an audio file directly (mp3/wav/m4a/ogg).
  Video files aren't accepted for audio extraction (no ffmpeg in this build) --
  export or record just the audio track. Without `AUDD_API_KEY` set, this
  module is skipped and the dashboard says so explicitly rather than scoring
  it as clear.
- AI-generated content flagging (Module F in the original spec) is not built
  in this version -- it was explicitly the last, optional stretch item.

## Project layout

```
app.py                          Landing/marketing page (Streamlit entry point)
pages/1_Run_Review.py           The actual tool: upload form + dashboard
app/config.py                   models, risk levels, scoring weights (all visible)
app/legal_retrieval.py          RAG layer: chunk + TF-IDF retrieval over data/legal_sources
app/llm.py                      Anthropic API wrapper (text + vision, JSON parsing)
app/parsing.py                  PDF/DOCX contract parsing, screenshot -> text via vision
app/pipeline.py                 shared Issue type + citation-resolution helpers
app/scoring.py                  the compliance score rule
app/orchestrator.py             runs all five modules, assembles the report
app/pdfgen.py                   the "license later" deferral document generator
app/modules/disclosure.py       Module A
app/modules/claimcheck.py       Module B
app/modules/contract_cross_check.py  Module C
app/modules/comparative.py      Module D
app/modules/music.py            Module E (AudD)
data/legal_sources/*.md         cleaned ASCI/CCPA source text (the RAG corpus)
data/legal_raw/                 original downloaded PDFs + raw extraction (reference only)
```
