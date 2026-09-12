"""Module D - Comparative Advertising Check.

Detects references to named competitors and comparative/superiority language,
and checks whether the brief substantiates the comparison, grounded in ASCI
Code Chapter IV (Fair in Competition).
"""
from __future__ import annotations

from app.config import RISK_NONE
from app.legal_retrieval import retrieve_for_module
from app.llm import call_json
from app.pipeline import Issue, format_chunks_for_prompt, normalize_risk, resolve_citation

MODULE = "comparative"

_SYSTEM = """You are a legal-compliance analyst checking influencer marketing content for \
comparative advertising issues under the ASCI Code, Chapter IV (Fair in Competition). You \
are given the content and the campaign brief (which may contain substantiation for \
comparisons), plus numbered excerpts from the ASCI Code -- the ONLY provisions you may cite.

Find every instance where the content:
(a) names or clearly identifies a specific competitor brand/product, and/or
(b) makes comparative or superiority language ("better than X", "outperforms Y", "#1", \
"India's best", "unlike other brands") -- even without naming a specific competitor.

For each instance found, check whether the campaign brief contains substantiation for the \
comparison. Judge risk: HIGH if a named competitor is directly disparaged or the comparison \
is factually specific (e.g. numeric performance claim) with zero substantiation in the brief; \
MEDIUM if there's unsubstantiated superiority language without naming a competitor, or a \
named competitor comparison with partial substantiation; LOW if substantiation is present but \
incomplete; NONE if there's no comparative language, or the comparison is fully substantiated \
in the brief.

Return ONLY a JSON array (empty array if no comparative instances are found at all) of \
objects shaped like:
{
  "quote": "exact quote of the comparative/competitor language from the content",
  "competitor_named": "name of competitor if named, else empty string",
  "risk": "HIGH" or "MEDIUM" or "LOW" or "NONE",
  "provision_index": <integer index of the most relevant numbered provision, or null>,
  "explanation": "why this risk level was assigned",
  "suggested_fix": "rewritten, lower-risk version of this comparison, or empty string if risk is NONE"
}"""


def run_comparative_check(content_text: str, brief_text: str) -> tuple[list[Issue], dict]:
    if not content_text.strip():
        return [], {"comparisons": []}

    retrieved = retrieve_for_module(MODULE)
    chunk_block = format_chunks_for_prompt(retrieved)
    user_text = (
        f"CONTENT TO ANALYZE:\n\n{content_text}\n\n"
        f"CAMPAIGN BRIEF (may contain substantiation for comparisons):\n{brief_text}\n\n"
        f"NUMBERED LEGAL PROVISIONS RETRIEVED:\n{chunk_block}"
    )
    result = call_json(system=_SYSTEM, user_text=user_text)
    if not isinstance(result, list):
        result = []

    issues: list[Issue] = []
    detail_rows = []
    for item in result:
        risk = normalize_risk(item.get("risk", "NONE"))
        citation, legal_text = resolve_citation(retrieved, item.get("provision_index"))
        detail_rows.append({**item, "risk": risk})
        if risk == RISK_NONE:
            continue
        competitor = item.get("competitor_named") or "an unnamed competitor"
        issues.append(
            Issue(
                module=MODULE,
                title=f"Unsubstantiated comparison vs {competitor}",
                risk=risk,
                evidence=item.get("quote", ""),
                legal_citation=citation,
                legal_text=legal_text,
                explanation=item.get("explanation", ""),
                suggested_fix=item.get("suggested_fix", ""),
                original_text=item.get("quote", ""),
                rewritten_text=item.get("suggested_fix", ""),
            )
        )

    return issues, {"comparisons": detail_rows}
