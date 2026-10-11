"""Contract review: reads an influencer agreement against a fixed checklist.

Every topic on the checklist is assessed on every run, so a one-sided payment,
exclusivity, usage-rights, termination or liability clause cannot be skipped just
because no legal provision happens to cover it. Two kinds of finding come out:

  - legal findings: the clause potentially conflicts with a retrieved ASCI / CCPA /
    Consumer Protection provision. These cite that provision.
  - commercial findings: the term is one-sided or missing, but HYPECHECK's legal
    sources do not cover the subject. They cite nothing, are shown with a
    "Commercial term" tag, and always carry "Needs human review". They are flagged
    because a careful reader would want a human to look at them, never as a breach
    of any rule.

A finding that quotes a clause must quote text that is really in the contract.
If the quote cannot be found, the item is listed under points to confirm instead
of being scored. Terms that are only unclear are listed there too.
"""
from __future__ import annotations

import re

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

# Shown in place of a legal citation for commercial findings.
NO_LEGAL_SOURCE = "Commercial term: no legal source cited"

CHECKLIST = [
    "Payment",
    "Deliverables and scope",
    "Exclusivity",
    "Usage rights and licence duration",
    "Intellectual property ownership",
    "Termination",
    "Liability and indemnity",
    "Confidentiality",
    "Disclosure and advertising obligations",
    "Claims and content instructions",
    "Approval process",
    "Governing law and disputes",
]

_RETRIEVAL_QUERY = (
    "disclosure influencer material connection responsibility advertiser influencer "
    "endorsement genuine opinion due diligence claims substantiation misleading advertisement"
)

_SYSTEM = """You are a careful reviewer of influencer marketing contracts. You are given the contract \
text, the reviewer's settings, and numbered excerpts from the ASCI Code, the ASCI Influencer \
Guidelines and the CCPA / Consumer Protection guidelines. Those numbered excerpts are the ONLY legal \
provisions you may cite.

Assess EVERY topic on this checklist, one entry each, in this order: %(topics)s.

For each topic, read the whole contract before you decide, because a term may sit under a different \
heading. Then give one assessment:
  "balanced": the contract deals with the topic in a specific, reasonably fair way (for example a \
fixed payment amount and date, a defined notice period, exclusivity limited in time and scope, usage \
rights limited in time and media).
  "one_sided": the contract deals with the topic but the term is heavily one-sided, open-ended or \
removes a core protection (for example payment at the brand's sole discretion, exclusivity with no \
end date, usage in all media forever without payment, termination at any time without notice or \
payment for delivered work, all liability placed on one party, an instruction to hide that the post \
is paid, an instruction to make guaranteed or health claims).
  "unclear": the term exists but is vague or contradictory, so a reader could not tell what applies.
  "missing": the contract says nothing on a topic that this kind of agreement would normally cover.
  "not_applicable": the topic is not needed for this kind of agreement.
Be even-handed: report a one-sided term whichever party the reader is, and frame why it matters from \
the reader's role when one is given. Do not mark a fair, specific term as one_sided.

Risk levels:
  HIGH: the term could expose a party to a misleading advertisement or an undisclosed endorsement, \
clearly conflicts with a numbered provision, or removes a core protection (payment certainty, a fair \
exit, a limit on exclusivity, usage or liability).
  MEDIUM: the term is lopsided, ambiguous or incomplete in a way that deserves review.
  LOW: a minor drafting point.

Legal provisions: set "provision_index" only when a numbered provision directly addresses the problem. \
For the topics "Disclosure and advertising obligations" and "Claims and content instructions" you MUST \
set it to the best matching numbered provision whenever the term concerns disclosing a paid or material \
connection, honest or genuine endorsement, substantiating a claim, or who is responsible for \
disclosure and claims; use null there only if no numbered provision is relevant at all. For commercial \
problems such as payment, exclusivity, usage rights, termination or liability for ordinary business \
losses, set "provision_index" to null. Never stretch a provision to fit.

Set "needs_human_review" to true when the point depends on facts or law outside the numbered \
provisions, or you are unsure. If the settings say the governing law is not India or is unknown, do \
not assume Indian law governs the contract: treat the numbered provisions as reference points and say \
so in the explanation. Where the settings name focus areas, give those the most care, but still \
assess every topic. Anything important that does not fit a checklist topic goes in "other_findings".

Return ONLY a JSON object, no other text, shaped like:
{
  "topics": [
    {
      "topic": "one name from the checklist",
      "assessment": "balanced" or "one_sided" or "unclear" or "missing" or "not_applicable",
      "clause_ref": "where it is, for example 'Clause 4.2' or 'Section 3'; empty string if the document gives no numbering",
      "clause_quote": "verbatim quote of the clause, copied exactly from the contract; empty string for missing, balanced or not_applicable",
      "risk": "HIGH" or "MEDIUM" or "LOW",
      "needs_human_review": true or false,
      "provision_index": <integer index of the numbered provision this is grounded in, or null>,
      "explanation": "why the term may be unfavourable, unclear or potentially non-compliant, framed as a potential issue for human review, never a definitive legal conclusion (do not say 'this violates'; say 'this potentially implicates ... and should be reviewed by a lawyer before signing'); empty for balanced or not_applicable",
      "questions": ["a point the reader may wish to clarify or negotiate"],
      "suggested_fix": "sample language or a drafting direction, written as a suggestion"
    }
  ],
  "other_findings": [ same fields, with "topic" as a short label of your own ]
}

For "balanced" and "not_applicable" topics you may leave every field except "topic" and "assessment" \
empty. Use an empty array for "other_findings" when there is nothing to add."""


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[\"'‘’“”]", "", text or "")).strip().lower()


def _quote_in_contract(quote: str, contract_norm: str) -> bool:
    q = _norm(quote)
    if len(q) < 12:
        return False
    return q in contract_norm or q[:60] in contract_norm


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
    result = call_json(
        system=_SYSTEM % {"topics": "; ".join(CHECKLIST)},
        user_text=user_text,
        max_tokens=8192,
        temperature=0,
    )
    if not isinstance(result, dict):
        result = {}

    entries = [e for e in result.get("topics", []) if isinstance(e, dict)]
    entries += [
        {**e, "topic": e.get("topic") or "Other point"} for e in result.get("other_findings", []) if isinstance(e, dict)
    ]
    contract_norm = _norm(contract_text)

    points: list[dict] = []
    issues: list[Issue] = []
    for entry in entries:
        assessment = str(entry.get("assessment", "")).strip().lower()
        if assessment in ("balanced", "not_applicable", ""):
            continue
        topic = str(entry.get("topic", "")).strip() or "Contract term"
        explanation = entry.get("explanation", "") or ""
        clause_ref = entry.get("clause_ref", "") or ""
        quote = entry.get("clause_quote", "") or ""
        missing = assessment == "missing"

        if assessment == "unclear":
            points.append({"topic": topic, "status": "unclear", "note": explanation, "clause_ref": clause_ref})
            continue
        risk = normalize_risk(entry.get("risk", "MEDIUM"))
        if risk == RISK_NONE:
            continue
        # A quoted clause has to be in the contract. If it is not, keep the point for a
        # human to look at rather than scoring something that may not exist.
        if not missing and not _quote_in_contract(quote, contract_norm):
            points.append(
                {"topic": topic, "status": "needs human review", "note": explanation, "clause_ref": clause_ref}
            )
            continue

        citation, legal_text = resolve_citation(retrieved, entry.get("provision_index"))
        commercial = citation == NO_PROVISION_FOUND
        if commercial:
            citation, legal_text = NO_LEGAL_SOURCE, ""
        questions = [q for q in entry.get("questions", []) if isinstance(q, str) and q.strip()]
        if commercial:
            title = f"Missing term: {topic}" if missing else f"One-sided term: {topic}"
            finding_type = "Commercial term"
        else:
            title = "Expected clause not found" if missing else "Potentially risky clause"
            finding_type = "Missing information" if missing else "Potential risk"
        issues.append(
            Issue(
                module=MODULE,
                title=title,
                risk=risk,
                evidence=quote or "No clause on this point was found in the contract.",
                legal_citation=citation,
                legal_text=legal_text,
                explanation=explanation,
                suggested_fix=entry.get("suggested_fix", "") or "",
                original_text="" if missing else quote,
                rewritten_text=entry.get("suggested_fix", "") or "",
                extra={
                    "evidence_label": "Missing clause" if missing else "Clause",
                    "reference": clause_ref,
                    "questions": questions,
                    "needs_human_review": True if commercial else bool(entry.get("needs_human_review", False)),
                    "finding_type": finding_type,
                    "commercial": commercial,
                    "topic": topic,
                },
            )
        )

    return issues, {"findings_count": len(issues), "points_to_confirm": points}
