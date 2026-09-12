"""Module B - ClaimCheck (flagship feature).

extract -> classify -> check-against-source -> verdict, applied to every
factual/efficacy claim made in the content, checked against the campaign
brief's stated evidence and grounded in the CCPA Misleading Advertisement
Guidelines / ASCI Code.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.config import RISK_HIGH, RISK_LOW, RISK_MEDIUM, RISK_NONE
from app.legal_retrieval import retrieve_for_module
from app.llm import call_json
from app.pipeline import Issue, format_chunks_for_prompt, normalize_risk, resolve_citation

MODULE = "claims"


@dataclass
class ClaimAnalysis:
    claim_text: str
    classification: str  # "objective" | "subjective"
    classification_reason: str
    supported_by_brief: bool
    supporting_evidence_in_brief: str
    risk: str
    legal_citation: str
    legal_text: str
    explanation: str
    suggested_fix: str
    fix_explanation: str


_EXTRACT_SYSTEM = """You are a legal-compliance analyst extracting factual claims from \
influencer marketing content for an Indian ad-compliance review. \
Extract every claim in the content that asserts something about the product/service's \
effect, performance, efficacy, composition, origin, or comparative standing \
(e.g. "removes pigmentation in 7 days", "clinically proven", "India's No. 1"). \
Do NOT extract pure opinion/puffery with no factual assertion (e.g. "I love this!", \
"my new favorite"), but DO extract borderline cases and classify them.

Return ONLY a JSON array, no other text, of objects shaped like:
{
  "claim_text": "verbatim quote of the claim from the content",
  "classification": "objective" or "subjective",
  "classification_reason": "one sentence: why this is an objective/factual claim \
requiring evidence, or subjective puffery that doesn't"
}

If there are no extractable claims, return an empty array []."""


def extract_claims(content_text: str) -> list[dict]:
    result = call_json(
        system=_EXTRACT_SYSTEM,
        user_text=f"CONTENT TO ANALYZE:\n\n{content_text}",
    )
    if not isinstance(result, list):
        return []
    return result


_CHECK_SYSTEM = """You are a legal-compliance analyst. You are given:
1. A list of claims already extracted from influencer marketing content, each pre-classified \
as "objective" (factual/efficacy claim requiring evidence) or "subjective" (puffery, no \
evidence needed).
2. The campaign brief's "claims the brand wants communicated" field, which may or may not \
contain supporting evidence for each claim.
3. Numbered excerpts from the CCPA Misleading Advertisement Guidelines and the ASCI Code -- \
these are the ONLY legal provisions you may cite.

For EACH objective claim, decide whether the brief contains supporting evidence for it. If \
the brief contains NO supporting evidence for an objective claim, flag it as a substantiation \
risk. Judge severity: HIGH if the claim relates to health/medical/safety efficacy (e.g. cures, \
removes a medical condition, treats an illness) with zero support in the brief; MEDIUM for \
other unsubstantiated objective claims (e.g. performance, superiority, origin); LOW if the \
brief provides partial/weak support that doesn't fully cover the claim as worded. Subjective \
claims always get risk "NONE" and need no rewrite.

For every objective claim that is NOT fully supported (risk HIGH/MEDIUM/LOW), you MUST also \
produce a rewritten, lower-risk version of the claim, plus a one-line explanation of what \
changed and why (e.g. softened to opinion, added a qualifier, removed an absolute).

Return ONLY a JSON array, one object per input claim, in the same order, shaped like:
{
  "claim_text": "...(copy verbatim from input)",
  "classification": "objective" or "subjective",
  "supported_by_brief": true or false,
  "supporting_evidence_in_brief": "quote from the brief if any, else empty string",
  "risk": "HIGH" or "MEDIUM" or "LOW" or "NONE",
  "provision_index": <integer index from the numbered list that best supports this verdict, \
or null if none of the provided provisions are relevant to this specific claim>,
  "explanation": "why this claim was flagged (or why it's fine) -- frame as a POTENTIALLY \
implicated provision needing human legal review, never a definitive legal conclusion (do \
not say 'this violates CCPA guidelines'; say 'this potentially implicates ... and should be \
reviewed by a lawyer before publication')",
  "suggested_fix": "rewritten claim text, or empty string if risk is NONE",
  "fix_explanation": "one line: what changed and why, or empty string if risk is NONE"
}

If none of the numbered provisions actually apply to a given claim, set provision_index to \
null rather than guessing -- do not fabricate a citation."""


def check_claims_against_brief(claims: list[dict], brief_claims_text: str) -> list[ClaimAnalysis]:
    if not claims:
        return []

    retrieved = retrieve_for_module(MODULE, extra_terms=brief_claims_text[:300])
    chunk_block = format_chunks_for_prompt(retrieved)

    user_text = (
        f"CLAIMS ALREADY EXTRACTED FROM CONTENT (JSON):\n{claims!r}\n\n"
        f"CAMPAIGN BRIEF - CLAIMS THE BRAND WANTS COMMUNICATED (this is the only evidence "
        f"source available; if it doesn't support a claim, the claim is unsubstantiated):\n"
        f"{brief_claims_text or '(brief left this field empty)'}\n\n"
        f"NUMBERED LEGAL PROVISIONS RETRIEVED:\n{chunk_block}"
    )
    result = call_json(system=_CHECK_SYSTEM, user_text=user_text, max_tokens=8192)
    if not isinstance(result, list):
        result = []

    analyses = []
    for item in result:
        risk = normalize_risk(item.get("risk", "NONE"))
        citation, legal_text = resolve_citation(retrieved, item.get("provision_index"))
        analyses.append(
            ClaimAnalysis(
                claim_text=item.get("claim_text", ""),
                classification=item.get("classification", "objective"),
                classification_reason=item.get("explanation", ""),
                supported_by_brief=bool(item.get("supported_by_brief", False)),
                supporting_evidence_in_brief=item.get("supporting_evidence_in_brief", ""),
                risk=risk,
                legal_citation=citation if risk != RISK_NONE else "",
                legal_text=legal_text if risk != RISK_NONE else "",
                explanation=item.get("explanation", ""),
                suggested_fix=item.get("suggested_fix", ""),
                fix_explanation=item.get("fix_explanation", ""),
            )
        )
    return analyses


def run_claimcheck(content_text: str, brief_claims_text: str) -> tuple[list[Issue], dict]:
    """Full Module B pipeline. Returns (issues_for_dashboard, detail_dict)."""
    if not content_text.strip():
        return [], {"claims": []}

    extracted = extract_claims(content_text)
    analyses = check_claims_against_brief(extracted, brief_claims_text)

    issues: list[Issue] = []
    for a in analyses:
        if a.risk == RISK_NONE:
            continue
        issues.append(
            Issue(
                module=MODULE,
                title=f"Unsubstantiated claim: “{a.claim_text[:80]}”",
                risk=a.risk,
                evidence=a.claim_text,
                legal_citation=a.legal_citation,
                legal_text=a.legal_text,
                explanation=a.explanation,
                suggested_fix=a.suggested_fix,
                original_text=a.claim_text,
                rewritten_text=a.suggested_fix,
                extra={"fix_explanation": a.fix_explanation, "classification": a.classification},
            )
        )

    detail = {"claims": [a.__dict__ for a in analyses]}
    return issues, detail
