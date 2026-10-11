"""Contract review: reads an influencer agreement on its own, without any content.

Two outputs, kept apart on purpose:
  - findings: clauses (or missing clauses) that potentially conflict with a
    retrieved ASCI / CCPA / Consumer Protection provision. Each one must cite
    the provision it was grounded in, so these are scored like every other check.
  - points_to_confirm: commercial and drafting terms a careful reviewer would
    want clear (usage rights, exclusivity, payment timing, termination). These
    are not grounded in any retrieved provision, so they are listed but never
    scored.
"""
from __future__ import annotations

from app.config import RISK_NONE
from app.legal_retrieval import retrieve
from app.llm import call_json
from app.pipeline import (
    NO_PROVISION_FOUND,
    Issue,
    format_chunks_for_prompt,
    normalize_risk,
    resolve_citation,
)

MODULE = "contract_review"

_RETRIEVAL_QUERY = (
    "disclosure influencer material connection responsibility advertiser influencer "
    "endorsement genuine opinion due diligence claims substantiation misleading advertisement"
)

_SYSTEM = """You are a compliance analyst reviewing an influencer marketing contract for an \
Indian brand or creator. You are given the contract text and numbered excerpts from the ASCI \
Code, the ASCI Influencer Guidelines and the CCPA / Consumer Protection guidelines. Those \
numbered excerpts are the ONLY legal provisions you may cite.

Produce two lists.

1. "findings": clauses that potentially conflict with, or fail to support, one of the numbered \
provisions. Typical examples: a clause that requires or allows the influencer to make absolute, \
guaranteed or unsubstantiated claims; a clause that restricts, discourages or omits a clear \
advertising disclosure; a clause that has the influencer endorse something they have not used \
or that is not their genuine opinion; a clause that puts all responsibility for claims or \
disclosure on one party only; a clause that asks the influencer to hide the commercial \
relationship. You may also report the ABSENCE of a clause when a numbered provision expects one \
(for example no disclosure obligation anywhere in the contract). Only report a finding you can \
ground in one numbered provision.

2. "points_to_confirm": commercial and drafting terms a careful reviewer would want to be clear, \
whether or not any legal provision applies: scope and number of deliverables, usage rights and \
their duration, exclusivity, payment amount and timing, approval process, termination, \
governing terms. List only the ones that are missing or unclear in this contract.

Return ONLY a JSON object, no other text, shaped like:
{
  "findings": [
    {
      "kind": "clause" or "missing",
      "clause_quote": "verbatim quote of the clause, or empty string if kind is missing",
      "risk": "HIGH" or "MEDIUM" or "LOW",
      "provision_index": <integer index of the numbered provision this is grounded in, or null>,
      "explanation": "why this potentially implicates the provision, framed as a potential issue needing human legal review, never a definitive legal conclusion (do not say 'this violates'; say 'this potentially implicates ... and should be reviewed by a lawyer before signing')",
      "suggested_fix": "suggested replacement or additional clause wording"
    }
  ],
  "points_to_confirm": [
    {
      "topic": "short label, for example Usage rights",
      "status": "missing" or "unclear",
      "note": "one sentence on what should be made clear"
    }
  ]
}

Use empty arrays when there is nothing to report. Keep risk HIGH for clauses that could expose \
either party to a misleading advertisement or undisclosed endorsement."""


def run_contract_review_check(contract_text: str) -> tuple[list[Issue], dict]:
    if not contract_text.strip():
        return [], {"findings": [], "points_to_confirm": []}

    retrieved = retrieve(_RETRIEVAL_QUERY, top_k=5)
    user_text = (
        f"CONTRACT TEXT:\n\n{contract_text}\n\n"
        f"NUMBERED LEGAL PROVISIONS RETRIEVED:\n{format_chunks_for_prompt(retrieved)}"
    )
    result = call_json(system=_SYSTEM, user_text=user_text, max_tokens=8192)
    if not isinstance(result, dict):
        result = {}

    points: list[dict] = [
        {
            "topic": p.get("topic", "") or "Point to confirm",
            "status": p.get("status", "unclear"),
            "note": p.get("note", ""),
        }
        for p in result.get("points_to_confirm", [])
        if isinstance(p, dict) and (p.get("note") or p.get("topic"))
    ]

    issues: list[Issue] = []
    for item in result.get("findings", []):
        if not isinstance(item, dict):
            continue
        risk = normalize_risk(item.get("risk", "MEDIUM"))
        if risk == RISK_NONE:
            continue
        citation, legal_text = resolve_citation(retrieved, item.get("provision_index"))
        if citation == NO_PROVISION_FOUND:
            # Not grounded in a retrieved provision: keep it visible as a point
            # to confirm instead of letting an uncited flag affect the score.
            points.append(
                {
                    "topic": "Clause to review",
                    "status": "unclear",
                    "note": item.get("explanation", ""),
                }
            )
            continue

        missing = item.get("kind") == "missing"
        quote = item.get("clause_quote", "")
        issues.append(
            Issue(
                module=MODULE,
                title="Expected clause not found" if missing else "Potentially risky clause",
                risk=risk,
                evidence=quote or "No clause on this point was found in the contract.",
                legal_citation=citation,
                legal_text=legal_text,
                explanation=item.get("explanation", ""),
                suggested_fix=item.get("suggested_fix", ""),
                original_text="" if missing else quote,
                rewritten_text=item.get("suggested_fix", ""),
                extra={"evidence_label": "Missing clause" if missing else "Clause"},
            )
        )

    return issues, {"findings_count": len(issues), "points_to_confirm": points}
