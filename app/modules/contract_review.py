"""Contract review: reads an influencer agreement on its own.

Two outputs, kept apart on purpose:
  - findings: clauses (or missing clauses) that potentially conflict with a
    retrieved ASCI / CCPA / Consumer Protection provision. Each one must cite
    the provision it was grounded in, so these are scored like every other check.
  - points_to_confirm: commercial and drafting points a careful reviewer would
    want clear (usage rights, exclusivity, payment timing, termination), and
    concerns that no retrieved provision covers. These are never scored; they are
    listed for a human to look at.
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

_SYSTEM = """You are a compliance analyst reviewing an influencer marketing contract. You are given \
the contract text, the reviewer's settings, and numbered excerpts from the ASCI Code, the ASCI \
Influencer Guidelines and the CCPA / Consumer Protection guidelines. Those numbered excerpts are the \
ONLY legal provisions you may cite.

Produce two lists.

1. "findings": clauses that potentially conflict with, or fail to support, one of the numbered \
provisions. Typical examples: a clause that requires or allows the influencer to make absolute, \
guaranteed or unsubstantiated claims; a clause that restricts, discourages or omits a clear \
advertising disclosure; a clause that has the influencer endorse something they have not used or \
that is not their genuine opinion; a clause that puts all responsibility for claims or disclosure \
on one party only; a clause that asks the influencer to hide the commercial relationship. You may \
also report the ABSENCE of a clause when a numbered provision expects one. Before you report an \
absence, search the whole contract: if the point is dealt with anywhere in it, even under a \
different heading, do not report it; and if the term would be unnecessary for this kind of \
agreement, do not report it. Only report a finding you can ground in one numbered provision.

2. "points_to_confirm": commercial and drafting terms a careful reviewer would want to be clear, \
whether or not any legal provision applies: scope and number of deliverables, usage rights and \
their duration, exclusivity, payment amount and timing, approval process, termination, \
confidentiality, liability and indemnity. List only the ones that are missing or unclear in this \
contract, and only if relevant to this type of agreement.

Risk levels: HIGH means the clause could expose a party to a misleading advertisement or an \
undisclosed endorsement, or clearly conflicts with a numbered provision. MEDIUM means it is \
potentially unfavourable, ambiguous or one-sided in a way that deserves review. LOW means a minor \
drafting point. Set "needs_human_review" to true when the clause is ambiguous, depends on facts or \
law outside the numbered provisions, or you are unsure.

Where the settings name a role, frame each risk from that party's point of view. Where they name \
focus areas, give those the most attention, but still report any HIGH finding elsewhere. If the \
settings say the governing law is not India or is unknown, do not assume Indian law applies to the \
contract: treat the numbered provisions as reference points and say so in the explanation.

Return ONLY a JSON object, no other text, shaped like:
{
  "findings": [
    {
      "kind": "clause" or "missing",
      "clause_ref": "where it is in the document, for example 'Clause 4.2' or 'Section 3, paragraph 2'; empty string if the document gives no numbering",
      "clause_quote": "verbatim quote of the clause, or empty string if kind is missing",
      "risk": "HIGH" or "MEDIUM" or "LOW",
      "needs_human_review": true or false,
      "provision_index": <integer index of the numbered provision this is grounded in, or null>,
      "explanation": "why the clause may be unfavourable, unclear, incomplete or potentially non-compliant, framed as a potential issue needing human legal review, never a definitive legal conclusion (do not say 'this violates'; say 'this potentially implicates ... and should be reviewed by a lawyer before signing')",
      "questions": ["a point the reader may wish to clarify or negotiate"],
      "suggested_fix": "sample language or a drafting direction, written as a suggestion"
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

Use empty arrays when there is nothing to report."""


def _settings_text(role: str, jurisdiction: str, focus: tuple[str, ...], context: str) -> str:
    return "\n".join(
        [
            f"Reader's role: {role or 'not specified'}",
            f"Governing law or jurisdiction: {jurisdiction or 'not specified'}",
            f"Focus areas: {', '.join(focus) if focus else 'none specified, review the whole agreement'}",
            f"Additional context from the reader: {context.strip() or 'none'}",
        ]
    )


def run_contract_review_check(
    contract_text: str,
    *,
    role: str = "",
    jurisdiction: str = "",
    focus: tuple[str, ...] = (),
    context: str = "",
) -> tuple[list[Issue], dict]:
    if not contract_text.strip():
        return [], {"findings_count": 0, "points_to_confirm": []}

    retrieved = retrieve(_RETRIEVAL_QUERY, top_k=5)
    user_text = (
        f"REVIEW SETTINGS:\n{_settings_text(role, jurisdiction, focus, context)}\n\n"
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
            "clause_ref": "",
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
        clause_ref = item.get("clause_ref", "")
        if citation == NO_PROVISION_FOUND:
            # Not grounded in a retrieved provision: keep it visible for a human
            # to look at instead of letting an uncited flag affect the review.
            points.append(
                {
                    "topic": "Clause to review",
                    "status": "needs human review",
                    "note": item.get("explanation", ""),
                    "clause_ref": clause_ref,
                }
            )
            continue

        missing = item.get("kind") == "missing"
        quote = item.get("clause_quote", "")
        questions = [q for q in item.get("questions", []) if isinstance(q, str) and q.strip()]
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
                extra={
                    "evidence_label": "Missing clause" if missing else "Clause",
                    "reference": clause_ref,
                    "questions": questions,
                    "needs_human_review": bool(item.get("needs_human_review", False)),
                    "finding_type": "Missing information" if missing else "Potential risk",
                },
            )
        )

    return issues, {"findings_count": len(issues), "points_to_confirm": points}
