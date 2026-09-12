"""Module C - Contract <-> Content Cross-Check (key differentiator).

This is a diff between two independently-extracted structured lists:
  1. restriction clauses extracted from the contract, and
  2. claims/statements extracted from the content.
Each extraction is its own clean, independently-testable function; only after
both exist do we connect them via cross_check().
"""
from __future__ import annotations

from dataclasses import dataclass

from app.config import RISK_NONE
from app.legal_retrieval import retrieve
from app.llm import call_json
from app.pipeline import Issue, format_chunks_for_prompt, normalize_risk, resolve_citation

MODULE = "contract"


@dataclass
class ContractRestriction:
    restriction_text: str  # verbatim clause quote
    category: str  # short normalized label, e.g. "no medical/therapeutic claims"
    plain_summary: str


@dataclass
class ContentStatement:
    statement_text: str  # verbatim quote from content
    statement_type: str  # e.g. "medical/health claim", "comparative claim", "brand mention"


_RESTRICTION_SYSTEM = """You are a contracts analyst. Extract every restriction, prohibition \
or "must not" obligation placed on the influencer/creator's content from this influencer \
marketing contract (e.g. "no medical or therapeutic claims", "no comparative claims", "no \
mentions of competitor brands", "no profanity", "must not disparage the brand", exclusivity \
restrictions, mandatory disclosure clauses, restrictions on claims about ingredients or \
results, etc.). Only extract restrictions that could be checked against a piece of published \
content -- ignore purely commercial/payment/IP-ownership terms that don't constrain content.

Return ONLY a JSON array of objects shaped like:
{
  "restriction_text": "verbatim quote of the clause (trim to the operative sentence)",
  "category": "short normalized label for the restriction type",
  "plain_summary": "one plain-English sentence restating the restriction"
}

If there are no content restrictions in the contract, return an empty array []."""


def extract_contract_restrictions(contract_text: str) -> list[ContractRestriction]:
    if not contract_text.strip():
        return []
    result = call_json(
        system=_RESTRICTION_SYSTEM,
        user_text=f"CONTRACT TEXT:\n\n{contract_text}",
        max_tokens=8192,
    )
    if not isinstance(result, list):
        return []
    return [
        ContractRestriction(
            restriction_text=r.get("restriction_text", ""),
            category=r.get("category", ""),
            plain_summary=r.get("plain_summary", ""),
        )
        for r in result
        if r.get("restriction_text")
    ]


_STATEMENT_SYSTEM = """You are a content analyst. Extract every distinct factual claim, \
brand/competitor mention, comparative statement, or notable assertion made in this piece of \
influencer marketing content (caption/transcript/on-image text). Be thorough -- include \
health/medical/efficacy claims, comparative claims, mentions of any brand other than the \
sponsoring brand, and any other statement that a contract might restrict.

Return ONLY a JSON array of objects shaped like:
{
  "statement_text": "verbatim quote from the content",
  "statement_type": "short label, e.g. 'medical/health claim', 'comparative claim', \
'competitor brand mention', 'general claim'"
}

If there is nothing extractable, return an empty array []."""


def extract_content_statements(content_text: str) -> list[ContentStatement]:
    if not content_text.strip():
        return []
    result = call_json(
        system=_STATEMENT_SYSTEM,
        user_text=f"CONTENT TEXT:\n\n{content_text}",
    )
    if not isinstance(result, list):
        return []
    return [
        ContentStatement(
            statement_text=s.get("statement_text", ""),
            statement_type=s.get("statement_type", ""),
        )
        for s in result
        if s.get("statement_text")
    ]


_CROSSCHECK_SYSTEM = """You are a legal-compliance analyst doing a contract-compliance cross \
check for influencer marketing. You are given two independently-extracted lists: (1) content \
restrictions from the influencer's contract, and (2) statements/claims actually made in the \
published content. You are also given numbered excerpts from the ASCI Code / CCPA guidelines \
-- the ONLY provisions you may cite for legal grounding (a restriction being contractual does \
not require a legal citation, but cite one if the restriction reflects a general advertising \
law principle, e.g. medical claims substantiation, comparative advertising fairness).

For each contract restriction, check whether ANY of the content statements violate it. Only \
report an actual violation -- a statement that plainly matches something the restriction \
prohibits. Judge risk: HIGH if the violation is clear and the restricted category is high-harm \
(e.g. medical/therapeutic claims, safety); MEDIUM for other clear violations; LOW for a \
borderline/partial violation. Do not report a restriction with no matching violating statement.

Return ONLY a JSON array (empty if no violations found) of objects shaped like:
{
  "restriction_text": "the contract restriction (copy verbatim from input)",
  "violating_statement": "the exact content statement that violates it (copy verbatim from input)",
  "risk": "HIGH" or "MEDIUM" or "LOW",
  "provision_index": <integer index of the most relevant numbered legal provision, or null if none apply>,
  "explanation": "why this statement potentially violates this restriction -- frame as a \
POTENTIALLY implicated restriction needing human legal/contract review, never a definitive \
conclusion (do not say 'this violates the contract'; say 'this potentially conflicts with \
... and should be reviewed by a lawyer before publication')",
  "suggested_fix": "how to rewrite or remove the offending statement to comply with the contract"
}"""


def cross_check(
    restrictions: list[ContractRestriction], statements: list[ContentStatement]
) -> list[Issue]:
    if not restrictions or not statements:
        return []

    # Ground the whole cross-check in whatever legal provisions are relevant to
    # the restriction categories present (claims substantiation + comparative
    # advertising cover the two restriction types the build spec calls out).
    query_terms = " ".join(r.category for r in restrictions)
    retrieved = retrieve(
        f"truthful claims substantiation comparative advertising medical therapeutic {query_terms}",
        top_k=4,
    )
    chunk_block = format_chunks_for_prompt(retrieved)

    user_text = (
        f"CONTRACT RESTRICTIONS (JSON):\n{[r.__dict__ for r in restrictions]!r}\n\n"
        f"CONTENT STATEMENTS (JSON):\n{[s.__dict__ for s in statements]!r}\n\n"
        f"NUMBERED LEGAL PROVISIONS RETRIEVED:\n{chunk_block}"
    )
    result = call_json(system=_CROSSCHECK_SYSTEM, user_text=user_text, max_tokens=8192)
    if not isinstance(result, list):
        result = []

    issues: list[Issue] = []
    for item in result:
        risk = normalize_risk(item.get("risk", "MEDIUM"))
        if risk == RISK_NONE:
            continue
        citation, legal_text = resolve_citation(retrieved, item.get("provision_index"))
        issues.append(
            Issue(
                module=MODULE,
                title="Content violates a contract restriction",
                risk=risk,
                evidence=item.get("violating_statement", ""),
                legal_citation=citation,
                legal_text=legal_text,
                explanation=item.get("explanation", ""),
                suggested_fix=item.get("suggested_fix", ""),
                original_text=item.get("violating_statement", ""),
                rewritten_text=item.get("suggested_fix", ""),
                extra={"contract_restriction": item.get("restriction_text", "")},
            )
        )
    return issues


def run_contract_cross_check(contract_text: str, content_text: str) -> tuple[list[Issue], dict]:
    restrictions = extract_contract_restrictions(contract_text)
    statements = extract_content_statements(content_text)
    issues = cross_check(restrictions, statements)
    detail = {
        "restrictions": [r.__dict__ for r in restrictions],
        "statements": [s.__dict__ for s in statements],
    }
    return issues, detail
