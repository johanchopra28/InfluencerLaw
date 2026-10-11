"""One runner per HYPECHECK service. Each runs only the checks that make sense
for the inputs that service collects, then scores them together."""
from __future__ import annotations

from dataclasses import dataclass

from app.modules.claimcheck import run_claimcheck
from app.modules.comparative import run_comparative_check
from app.modules.consumer_protection import run_consumer_protection_check
from app.modules.contract_cross_check import run_contract_cross_check
from app.modules.contract_review import run_contract_review_check
from app.modules.disclosure import run_disclosure_check
from app.modules.music import run_music_check
from app.pipeline import Issue
from app.scoring import CampaignReport, score_campaign


@dataclass
class RunResult:
    report: CampaignReport
    details: dict  # check -> detail dict from that check
    modules: list[str]  # the checks that ran, in display order


def _finish(issues: list[Issue], details: dict, modules: list[str]) -> RunResult:
    return RunResult(report=score_campaign(issues, modules), details=details, modules=modules)


def review_contract(contract_text: str, content_text: str = "") -> RunResult:
    """Contract service. Reviews the agreement itself and, if a caption or script
    is supplied, also checks that content against the contract's own restrictions."""
    issues: list[Issue] = []
    details: dict = {}
    modules = ["contract_review"]

    found, detail = run_contract_review_check(contract_text)
    issues += found
    details["contract_review"] = detail

    if content_text.strip():
        modules.append("contract")
        found, detail = run_contract_cross_check(contract_text, content_text)
        issues += found
        details["contract"] = detail

    return _finish(issues, details, modules)


def review_campaign(
    *,
    brand: str = "",
    product: str = "",
    objective: str = "",
    audience: str = "",
    claims: str = "",
    evidence: str = "",
    deliverables: str = "",
    disclosure_plan: str = "",
    usage: str = "",
) -> RunResult:
    """Campaign service. Checks the brief before any content exists: the claims
    the brand wants made against the evidence behind them, the planned
    disclosure, comparisons, and consumer-protection exposure."""
    issues: list[Issue] = []
    details: dict = {}
    modules = ["disclosure", "claims", "comparative", "consumer_protection"]

    context = "\n".join(
        line
        for line in (
            f"Brand: {brand}" if brand.strip() else "",
            f"Product: {product}" if product.strip() else "",
            f"Objective: {objective}" if objective.strip() else "",
            f"Target audience: {audience}" if audience.strip() else "",
            f"Planned deliverables: {deliverables}" if deliverables.strip() else "",
            f"Usage and permissions: {usage}" if usage.strip() else "",
            f"Evidence on file: {evidence}" if evidence.strip() else "",
        )
        if line
    )
    planned_message = "\n".join(t for t in (claims.strip(), objective.strip()) if t)

    plan_text = (
        f"Planned deliverables: {deliverables.strip() or 'not specified'}\n"
        f"Planned disclosure: {disclosure_plan.strip() or 'not specified'}"
    )
    found, detail = run_disclosure_check(plan_text)
    issues += found
    details["disclosure"] = detail

    found, detail = run_claimcheck(claims, evidence)
    issues += found
    details["claims"] = detail

    found, detail = run_comparative_check(planned_message, context)
    issues += found
    details["comparative"] = detail

    found, detail = run_consumer_protection_check(planned_message, context)
    issues += found
    details["consumer_protection"] = detail

    return _finish(issues, details, modules)


def review_content(
    content_text: str,
    evidence: str = "",
    audio_bytes: bytes | None = None,
    audio_filename: str = "",
) -> RunResult:
    """Content service. Reviews a caption, post or script, plus an optional audio track."""
    issues: list[Issue] = []
    details: dict = {}
    modules = ["disclosure", "claims", "comparative", "consumer_protection", "music"]
    brief = f"Evidence and supporting material: {evidence.strip()}" if evidence.strip() else ""

    found, detail = run_disclosure_check(content_text)
    issues += found
    details["disclosure"] = detail

    found, detail = run_claimcheck(content_text, evidence)
    issues += found
    details["claims"] = detail

    found, detail = run_comparative_check(content_text, brief)
    issues += found
    details["comparative"] = detail

    found, detail = run_consumer_protection_check(content_text, brief)
    issues += found
    details["consumer_protection"] = detail

    found, detail = run_music_check(audio_bytes, audio_filename)
    issues += found
    details["music"] = detail

    return _finish(issues, details, modules)
