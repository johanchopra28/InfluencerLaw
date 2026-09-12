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
2. Copy `.env.example` to `.env` and add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```

## How it works

Four modules share one pipeline pattern — **extract → classify → check against
source → verdict with citation** — implemented once and applied four ways:

| Module | File | What it checks |
|---|---|---|
| A — Disclosure | `app/modules/disclosure.py` | Is the commercial relationship disclosed, prominently, with a permitted label? |
| B — ClaimCheck (flagship) | `app/modules/claimcheck.py` | Does every factual/efficacy claim in the content have supporting evidence in the brief? |
| C — Contract ↔ Content Cross-Check | `app/modules/contract_cross_check.py` | Does the content violate a restriction clause in the influencer's contract? |
| D — Comparative Advertising | `app/modules/comparative.py` | Are competitor comparisons/superiority claims substantiated? |

Every flag is traceable through: **Detected issue → Evidence (exact quote) →
Legal basis (retrieved provision) → Risk level → Suggested fix.** The LLM never
free-hands legal reasoning — `app/legal_retrieval.py` retrieves the actual ASCI/CCPA
text chunk first (TF-IDF over `data/legal_sources/*.md`), and every module must
cite a retrieved chunk or explicitly say no relevant provision was found.

Compliance scoring (`app/scoring.py`) is a simple, visible deduction rule shown
in the dashboard itself — not a black box.

## Scope (v1)

- Jurisdiction: India only.
- Legal sources: ASCI Code, ASCI Influencer Guidelines, CCPA Misleading
  Advertisement Guidelines 2022 — nothing else.
- Content input: pasted caption/transcript text, or an Instagram screenshot
  (read via Claude vision, no OCR binary required). Video upload isn't
  supported — paste the transcript instead.
- Music-rights detection is explicitly out of scope; the dashboard shows a
  labeled "Coming soon" placeholder rather than a fake result.

## Project layout

```
app.py                          Streamlit UI + dashboard
app/config.py                   models, risk levels, scoring weights (all visible)
app/legal_retrieval.py          RAG layer: chunk + TF-IDF retrieval over data/legal_sources
app/llm.py                      Anthropic API wrapper (text + vision, JSON parsing)
app/parsing.py                  PDF/DOCX contract parsing, screenshot -> text via vision
app/pipeline.py                 shared Issue type + citation-resolution helpers
app/scoring.py                  the compliance score rule
app/orchestrator.py             runs all four modules, assembles the report
app/modules/disclosure.py       Module A
app/modules/claimcheck.py       Module B
app/modules/contract_cross_check.py  Module C
app/modules/comparative.py      Module D
data/legal_sources/*.md         cleaned ASCI/CCPA source text (the RAG corpus)
data/legal_raw/                 original downloaded PDFs + raw extraction (reference only)
```
