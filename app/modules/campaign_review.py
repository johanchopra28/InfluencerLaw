"""Campaign review: reads a campaign brief before any content exists.

Two jobs:
  - extract_brief_fields: pull the structured details out of an uploaded brief so
    the form can be pre-filled for the user to confirm, instead of asking for the
    same information twice.
  - run_campaign_review_check: review the brief for disclosure gaps, deliverables
    that do not match the brief, rights and permissions concerns, and information
    that is still missing.

Only disclosure findings that cite a retrieved provision become scored issues.
Everything else is returned as plain lists for a human to read. A missing
attachment or an unconfirmed fact is reported as missing information, never as
a violation.
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

MODULE = "disclosure"

CAMPAIGN_TYPES = [
    "Sponsored post",
    "Reel or video",
    "Story",
    "Product review",
    "Affiliate promotion",
    "Giveaway",
    "Brand ambassadorship",
    "Multi-format campaign",
    "Other",
]
JURISDICTIONS = ["India", "Other jurisdiction", "Multiple jurisdictions", "Not sure"]

_EXTRACT_SYSTEM = """You read an influencer campaign brief and pull out the details it states. \
Only report what the brief actually says. If it does not say, leave the value empty. Never guess.

Return ONLY a JSON object, no other text, shaped like:
{
  "campaign_type": one of %(types)s, or "" if the brief does not say,
  "category": "the brand or product category the brief names, for example beauty or fintech, or empty",
  "jurisdiction": one of %(jurisdictions)s, or "" if the brief does not say,
  "deliverables": [
    {"item": "what is to be delivered, for example Instagram reel", "quantity": "number as text, or empty", "date": "publication date or window as written, or empty", "tags": "required tags, hashtags or disclosures as written, or empty"}
  ],
  "requirements": "the brief's advertising and disclosure instructions, mandatory disclosures, hashtags, platform requirements and approved claims, quoted or closely summarised; empty if none"
}""" % {"types": CAMPAIGN_TYPES, "jurisdictions": JURISDICTIONS}


def extract_brief_fields(brief_text: str) -> dict:
    """Structured details the brief states, for the user to confirm. Empty values mean not stated."""
    empty = {"campaign_type": "", "category": "", "jurisdiction": "", "deliverables": [], "requirements": ""}
    if not brief_text.strip():
        return empty
    result = call_json(system=_EXTRACT_SYSTEM, user_text=f"CAMPAIGN BRIEF:\n\n{brief_text}", max_tokens=4096)
    if not isinstance(result, dict):
        return empty
    campaign_type = result.get("campaign_type", "")
    jurisdiction = result.get("jurisdiction", "")
    deliverables = [
        {
            "item": str(d.get("item", "")),
            "quantity": str(d.get("quantity", "")),
            "date": str(d.get("date", "")),
            "tags": str(d.get("tags", "")),
        }
        for d in result.get("deliverables", [])
        if isinstance(d, dict) and d.get("item")
    ]
    return {
        "campaign_type": campaign_type if campaign_type in CAMPAIGN_TYPES else "",
        "category": str(result.get("category", "")),
        "jurisdiction": jurisdiction if jurisdiction in JURISDICTIONS else "",
        "deliverables": deliverables,
        "requirements": str(result.get("requirements", "")),
    }


_RETRIEVAL_QUERY = (
    "disclosure label advertisement influencer material connection prominent hashtag "
    "endorsement genuine opinion due diligence misleading advertisement"
)

_REVIEW_SYSTEM = """You are a compliance analyst reviewing an influencer campaign brief before any \
content is made, for an Indian campaign. You are given what the brief and the user supplied, and \
numbered excerpts from the ASCI Code, ASCI Influencer Guidelines and CCPA / Consumer Protection \
guidelines. Those numbered excerpts are the ONLY legal provisions you may cite.

Rules you must follow:
- A missing attachment, a missing instruction or an unconfirmed fact is NOT proof of a violation. \
Report it under "missing_information", not as a finding.
- Only put something in "disclosure_findings" if it is an instruction in the supplied material that \
potentially conflicts with, or fails to support, a numbered provision on disclosure (for example an \
instruction to bury the disclosure in hashtags, to leave out a disclosure, or to disguise the \
commercial relationship), and you can ground it in one numbered provision. If the material gives no \
disclosure instruction at all, say so under "missing_information".
- Only report a deliverable mismatch that matters: a different quantity, date, format, tag or disclosure wording between two places in the supplied material. Do not report differences in wording that mean the same thing.
- Every finding names the instruction or section of the supplied material it comes from, explains \
the concern, and suggests a practical next step. Frame everything as a potential issue needing human \
review, never a definitive legal conclusion.

Return ONLY a JSON object, no other text, shaped like:
{
  "overview": "two to four plain sentences saying what was analysed (the campaign type, deliverables, and which material was supplied) and the scope of the review",
  "limitations": ["information that was not available and limits what this review can say, for example no brief document was supplied"],
  "disclosure_findings": [
    {
      "reference": "the instruction or section of the supplied material this comes from",
      "quote": "short verbatim quote of the instruction",
      "risk": "HIGH" or "MEDIUM" or "LOW",
      "provision_index": <integer index of the numbered provision, or null>,
      "explanation": "why it may be a problem",
      "next_step": "a practical next step"
    }
  ],
  "deliverable_consistency": [
    {"deliverable": "a deliverable or requirement", "reference": "where it appears", "issue": "how it does not match elsewhere in the brief or supplied material", "next_step": "what to clarify"}
  ],
  "rights_permissions": [
    {"topic": "content reuse or image rights or music or trademarks or other", "concern": "the potential issue, for example the brief mentions licensed music but gives no permission", "reference": "where it appears", "next_step": "a practical next step"}
  ],
  "missing_information": [
    {"item": "what is missing", "reason": "why it is needed to complete the review"}
  ]
}

Use empty arrays when there is nothing to report."""


def run_campaign_review_check(
    *,
    brief_text: str,
    campaign_type: str,
    category: str,
    jurisdiction: str,
    deliverables_text: str,
    requirements: str,
    supporting_text: str,
) -> tuple[list[Issue], dict]:
    retrieved = retrieve(_RETRIEVAL_QUERY, top_k=5)
    supplied = "\n\n".join(
        part
        for part in (
            f"CAMPAIGN BRIEF DOCUMENT:\n{brief_text.strip()}" if brief_text.strip() else "CAMPAIGN BRIEF DOCUMENT: none uploaded",
            f"Campaign type: {campaign_type or 'not specified'}",
            f"Brand or product category: {category or 'not specified'}",
            f"Target jurisdiction: {jurisdiction or 'not specified'}",
            f"Deliverables entered:\n{deliverables_text.strip() or 'none entered'}",
            f"Advertising and disclosure requirements entered:\n{requirements.strip() or 'none entered'}",
            f"SUPPORTING MATERIALS:\n{supporting_text.strip()}" if supporting_text.strip() else "SUPPORTING MATERIALS: none uploaded",
        )
    )
    result = call_json(
        system=_REVIEW_SYSTEM,
        user_text=f"{supplied}\n\nNUMBERED LEGAL PROVISIONS RETRIEVED:\n{format_chunks_for_prompt(retrieved)}",
        max_tokens=8192,
    )
    if not isinstance(result, dict):
        result = {}

    missing = [m for m in result.get("missing_information", []) if isinstance(m, dict)]
    issues: list[Issue] = []
    for item in result.get("disclosure_findings", []):
        if not isinstance(item, dict):
            continue
        risk = normalize_risk(item.get("risk", "MEDIUM"))
        if risk == RISK_NONE:
            continue
        citation, legal_text = resolve_citation(retrieved, item.get("provision_index"))
        if citation == NO_PROVISION_FOUND:
            missing.append(
                {
                    "item": f"Clarify: {item.get('reference', 'a disclosure instruction')}",
                    "reason": item.get("explanation", ""),
                }
            )
            continue
        issues.append(
            Issue(
                module=MODULE,
                title="Disclosure instruction may be inadequate",
                risk=risk,
                evidence=item.get("quote") or item.get("reference", ""),
                legal_citation=citation,
                legal_text=legal_text,
                explanation=item.get("explanation", ""),
                suggested_fix=item.get("next_step", ""),
                extra={
                    "evidence_label": "Campaign instruction",
                    "reference": item.get("reference", ""),
                    "finding_type": "Potential risk",
                },
            )
        )

    detail = {
        "overview": str(result.get("overview", "")),
        "limitations": [str(x) for x in result.get("limitations", []) if x],
        "deliverable_consistency": [d for d in result.get("deliverable_consistency", []) if isinstance(d, dict)],
        "rights_permissions": [r for r in result.get("rights_permissions", []) if isinstance(r, dict)],
        "missing_information": missing,
    }
    return issues, detail
