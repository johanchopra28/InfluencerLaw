"""Module 8 (HYPECHECK spec) - Consumer Protection & E-Commerce Check.

Checks for surrogate advertising, misleading endorsements / undisclosed
material connection at the statutory (not just ASCI-label) level, e-commerce
seller/pricing misrepresentation, and the general Consumer Protection Act
"misleading advertisement" catch-all (Section 2(28)) -- things the
disclosure-label check (Module 1) and the efficacy-claim check (Module 2)
don't already cover. Grounded in the Consumer Protection Act 2019, the
Consumer Protection (E-Commerce) Rules 2020, and the CCPA 2022 Guidelines.
"""
from __future__ import annotations

from app.config import RISK_NONE
from app.legal_retrieval import retrieve_for_module
from app.llm import call_json
from app.pipeline import Issue, format_chunks_for_prompt, normalize_risk, resolve_citation

MODULE = "consumer_protection"

_SYSTEM = """You are a legal-compliance analyst checking influencer marketing content \
against the Consumer Protection Act 2019, the Consumer Protection (E-Commerce) Rules \
2020, and the CCPA Misleading Advertisement Guidelines 2022 -- the ONLY provisions you \
may cite here. You are given the content, the campaign brief, and numbered excerpts from \
these sources.

Do NOT re-flag things that belong to other checks: don't flag a missing "Ad"/"Sponsored" \
disclosure LABEL (that is a separate ASCI-label check) and don't flag an efficacy/health \
claim purely for lacking brief evidence (that is a separate claim-substantiation check). \
Instead, look specifically for:

1. Surrogate advertising: does the content promote a product/brand extension in a way that \
indirectly advertises a good or service whose advertising is otherwise prohibited or \
restricted by law (e.g. a "music CD" or "soda" ad that is really promoting a restricted \
category under the same brand name)?
2. Endorsement due diligence: does the content present a personal endorsement/opinion \
that is NOT a genuine, reasonably current opinion based on adequate experience with the \
product (e.g. an influencer endorsing a product/service category -- financial products, \
health outcomes -- they plainly have no basis to evaluate), separate from whether a \
disclosure label is present?
3. E-commerce / transactional misrepresentation: false or unverifiable claims about price, \
discounts, "free" offers, availability, returns/refunds, warranties, or seller identity in \
a way a consumer could rely on to their detriment.
4. General misleading-advertisement catch-all: any statement that falsely describes the \
product/service's nature, substance, quantity, or quality, or gives a false guarantee, that \
isn't already covered by 1-3 above or by a separate claim/disclosure check.

Return ONLY a JSON array (empty if nothing applies) of objects shaped like:
{
  "quote": "exact quote from the content",
  "category": "surrogate_advertising" or "endorsement_due_diligence" or "ecommerce_misrepresentation" or "general_misleading",
  "risk": "HIGH" or "MEDIUM" or "LOW" or "NONE",
  "provision_index": <integer index of the most relevant numbered provision, or null if none apply -- never fabricate a citation>,
  "explanation": "why this was flagged, framed as a POTENTIALLY implicated provision needing human legal review -- never a definitive legal conclusion (do not say 'this violates the Act'; say 'this potentially implicates ... and should be reviewed by a lawyer before publication')",
  "suggested_fix": "the next action to take (e.g. what to verify, remove, or qualify), or empty string if risk is NONE"
}"""


def run_consumer_protection_check(content_text: str, brief_text: str) -> tuple[list[Issue], dict]:
    if not content_text.strip():
        return [], {"findings": []}

    retrieved = retrieve_for_module(MODULE)
    chunk_block = format_chunks_for_prompt(retrieved)
    user_text = (
        f"CONTENT TO ANALYZE:\n\n{content_text}\n\n"
        f"CAMPAIGN BRIEF:\n{brief_text}\n\n"
        f"NUMBERED LEGAL PROVISIONS RETRIEVED:\n{chunk_block}"
    )
    result = call_json(system=_SYSTEM, user_text=user_text)
    if not isinstance(result, list):
        result = []

    issues: list[Issue] = []
    detail_rows = []
    category_labels = {
        "surrogate_advertising": "Surrogate advertising",
        "endorsement_due_diligence": "Endorsement due diligence",
        "ecommerce_misrepresentation": "E-commerce misrepresentation",
        "general_misleading": "Potentially misleading advertisement",
    }
    for item in result:
        risk = normalize_risk(item.get("risk", "NONE"))
        citation, legal_text = resolve_citation(retrieved, item.get("provision_index"))
        detail_rows.append({**item, "risk": risk})
        if risk == RISK_NONE:
            continue
        label = category_labels.get(item.get("category", ""), "Consumer protection issue")
        issues.append(
            Issue(
                module=MODULE,
                title=label,
                risk=risk,
                evidence=item.get("quote", ""),
                legal_citation=citation,
                legal_text=legal_text,
                explanation=item.get("explanation", ""),
                suggested_fix=item.get("suggested_fix", ""),
                original_text=item.get("quote", ""),
            )
        )

    return issues, {"findings": detail_rows}
