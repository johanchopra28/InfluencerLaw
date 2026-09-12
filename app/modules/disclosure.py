"""Module A - Advertising Disclosure Check.

Determines whether a commercial relationship is disclosed in the content, and
whether the disclosure is prominent/unambiguous enough per ASCI's influencer
guidelines.
"""
from __future__ import annotations

from app.config import RISK_NONE
from app.legal_retrieval import retrieve_for_module
from app.llm import call_json
from app.pipeline import Issue, format_chunks_for_prompt, normalize_risk, resolve_citation

MODULE = "disclosure"

_SYSTEM = """You are a legal-compliance analyst checking whether influencer marketing \
content properly discloses a commercial relationship, per ASCI's Guidelines for Influencer \
Advertising in Digital Media. You are given the content (caption/transcript/on-image text) \
and numbered excerpts from the ASCI Code and ASCI Influencer Guidelines -- the ONLY \
provisions you may cite.

Determine:
1. Is there ANY disclosure of a commercial relationship at all?
2. If yes, does it use a permitted, unambiguous label (e.g. "Ad", "Advertisement", \
"Sponsored", "Collaboration", "Partnership", "Paid Partnership") placed prominently -- NOT \
buried in a hashtag pile, not only in a bio/about-me, not ambiguous language like "thank you \
to Brand X" or a bare brand tag/mention?
3. Judge risk: HIGH if there is no disclosure at all despite the content clearly being \
sponsored/branded content; MEDIUM if disclosure exists but is ambiguous, weak, or buried \
(e.g. only in a hashtag pile, or vague thank-you language); LOW if disclosure is present and \
reasonably clear but has a minor placement/wording issue; NONE if disclosure is clear, \
prominent, and uses a permitted label.

Return ONLY a JSON object:
{
  "disclosure_found": true or false,
  "disclosure_quote": "the exact quote of any disclosure-like text found, or empty string",
  "risk": "HIGH" or "MEDIUM" or "LOW" or "NONE",
  "provision_index": <integer index of the most relevant numbered provision, or null if none apply>,
  "explanation": "why this risk level was assigned",
  "suggested_fix": "exact suggested disclosure wording and placement to fix the issue, or \
empty string if risk is NONE"
}"""


def run_disclosure_check(content_text: str) -> tuple[list[Issue], dict]:
    if not content_text.strip():
        return [], {"note": "No content text was provided to check for disclosure."}

    retrieved = retrieve_for_module(MODULE)
    chunk_block = format_chunks_for_prompt(retrieved)
    user_text = f"CONTENT TO ANALYZE:\n\n{content_text}\n\nNUMBERED LEGAL PROVISIONS RETRIEVED:\n{chunk_block}"

    result = call_json(system=_SYSTEM, user_text=user_text)
    if not isinstance(result, dict):
        result = {}

    risk = normalize_risk(result.get("risk", "NONE"))
    citation, legal_text = resolve_citation(retrieved, result.get("provision_index"))

    detail = {
        "disclosure_found": bool(result.get("disclosure_found", False)),
        "disclosure_quote": result.get("disclosure_quote", ""),
        "risk": risk,
    }

    if risk == RISK_NONE:
        return [], detail

    issue = Issue(
        module=MODULE,
        title="Inadequate or missing advertising disclosure",
        risk=risk,
        evidence=result.get("disclosure_quote") or "(no disclosure text found in content)",
        legal_citation=citation,
        legal_text=legal_text,
        explanation=result.get("explanation", ""),
        suggested_fix=result.get("suggested_fix", ""),
    )
    return [issue], detail
