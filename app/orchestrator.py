"""One runner per HYPECHECK service. Each runs only the checks that make sense
for the inputs that service collects, then groups the findings into a report."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.campaign_review import run_campaign_review_check
from app.modules.claimcheck import run_claimcheck
from app.modules.comparative import run_comparative_check
from app.modules.consumer_protection import run_consumer_protection_check
from app.modules.content_revision import suggest_content_revision
from app.modules.contract_cross_check import run_contract_cross_check
from app.modules.contract_review import run_contract_review_check
from app.modules.disclosure import run_disclosure_check
from app.modules.music import run_music_check
from app.pipeline import Issue
from app.report import Report, build_report

NON_INDIA_NOTE = (
    "HYPECHECK's legal sources cover Indian advertising and consumer-protection rules only. "
    "Because the governing law is not confirmed as India, treat the cited provisions as "
    "reference points, not as the law that governs this item."
)


@dataclass
class RunResult:
    report: Report
    details: dict  # check -> detail dict from that check
    modules: list[str]  # the checks that ran, in display order
    scope: list[str] = field(default_factory=list)  # plain statements about what was and was not reviewed


def _scope(read_notes: tuple[str, ...] | list[str], jurisdiction: str, *lines: str) -> list[str]:
    scope = [line for line in lines if line] + list(read_notes)
    if jurisdiction in ("Other jurisdiction", "Multiple jurisdictions", "Not sure"):
        scope.append(NON_INDIA_NOTE)
    return scope


def review_contract(
    contract_text: str,
    *,
    role: str = "",
    jurisdiction: str = "",
    focus: tuple[str, ...] = (),
    context: str = "",
    content_text: str = "",
    read_notes: tuple[str, ...] = (),
) -> RunResult:
    """Contract service. Reviews the agreement itself and, if a caption or script
    is supplied, also checks that content against the contract's own restrictions."""
    issues: list[Issue] = []
    details: dict = {}
    modules = ["contract_review"]

    found, detail = run_contract_review_check(
        contract_text, role=role, jurisdiction=jurisdiction, focus=focus, context=context
    )
    issues += found
    details["contract_review"] = detail

    if content_text.strip():
        modules.append("contract")
        found, detail = run_contract_cross_check(contract_text, content_text)
        issues += found
        details["contract"] = detail

    scope = _scope(
        read_notes,
        jurisdiction,
        "Reviewed the text of the uploaded contract against HYPECHECK's legal sources.",
        "Commercial terms such as payment, exclusivity, usage rights, termination and liability were checked "
        "against a drafting checklist. No legal source covers them, so those flags cite none.",
        f"Focus areas: {', '.join(focus)}." if focus else "",
        "Also checked the supplied caption or script against the contract's own content rules."
        if content_text.strip()
        else "",
    )
    return RunResult(build_report(issues, modules), details, modules, scope)


def _deliverables_text(deliverables: list[dict]) -> str:
    lines = []
    for d in deliverables:
        item = str(d.get("item", "")).strip()
        if not item:
            continue
        parts = [f"{str(d.get('quantity', '')).strip()} x {item}" if str(d.get("quantity", "")).strip() else item]
        if str(d.get("date", "")).strip():
            parts.append(f"publish {str(d['date']).strip()}")
        if str(d.get("tags", "")).strip():
            parts.append(f"required tags or disclosures: {str(d['tags']).strip()}")
        lines.append("- " + "; ".join(parts))
    return "\n".join(lines)


def review_campaign(
    *,
    brief_text: str = "",
    campaign_type: str,
    category: str = "",
    jurisdiction: str = "",
    deliverables: list[dict] | None = None,
    requirements: str = "",
    supporting_text: str = "",
    read_notes: tuple[str, ...] = (),
) -> RunResult:
    """Campaign service. Reviews the brief before any content exists: disclosure
    instructions, deliverables that do not match, rights and permissions, the
    claims the brand wants made against the evidence behind them, comparisons,
    and consumer-protection exposure."""
    issues: list[Issue] = []
    details: dict = {}
    modules = ["disclosure", "claims", "comparative", "consumer_protection"]
    deliverables_text = _deliverables_text(deliverables or [])

    found, detail = run_campaign_review_check(
        brief_text=brief_text,
        campaign_type=campaign_type,
        category=category,
        jurisdiction=jurisdiction,
        deliverables_text=deliverables_text,
        requirements=requirements,
        supporting_text=supporting_text,
    )
    issues += found
    details["campaign"] = detail

    claims_source = "\n\n".join(t for t in (requirements.strip(), brief_text.strip()) if t)
    # The brief cannot be its own evidence: only the supporting materials count.
    evidence_source = supporting_text.strip()
    context = "\n".join(
        line
        for line in (
            f"Campaign type: {campaign_type}",
            f"Brand or product category: {category}" if category.strip() else "",
            f"Deliverables:\n{deliverables_text}" if deliverables_text else "",
            f"Evidence and supporting material:\n{evidence_source}" if evidence_source else "",
        )
        if line
    )

    found, detail = run_claimcheck(claims_source, evidence_source)
    for issue in found:
        # Before any content exists, a claim with nothing behind it is a gap to close.
        issue.title = issue.title.replace("Unsubstantiated claim", "Claim that may need substantiation", 1)
        issue.extra["finding_type"] = "Potential risk" if evidence_source else "Missing information"
    issues += found
    details["claims"] = detail

    found, detail = run_comparative_check(claims_source, context)
    issues += found
    details["comparative"] = detail

    found, detail = run_consumer_protection_check(claims_source, context)
    issues += found
    details["consumer_protection"] = detail

    scope = _scope(
        read_notes,
        jurisdiction,
        "Reviewed the campaign details and any brief and supporting materials you supplied.",
        *details["campaign"]["limitations"],
    )
    return RunResult(build_report(issues, modules), details, modules, scope)


def review_content(
    content_text: str,
    *,
    content_format: str = "",
    platform: str = "",
    relationship: str = "",
    category: str = "",
    context: str = "",
    audio_bytes: bytes | None = None,
    audio_filename: str = "",
    read_notes: tuple[str, ...] = (),
) -> RunResult:
    """Content service. Reviews a caption, post or script, plus an optional audio
    track, and proposes a revision if anything was flagged."""
    issues: list[Issue] = []
    details: dict = {}
    modules = ["disclosure", "claims", "comparative", "consumer_protection", "music"]

    meta = "\n".join(
        line
        for line in (
            f"Content format: {content_format}" if content_format else "",
            f"Platform: {platform}" if platform else "",
            f"Relationship between the creator and the brand: {relationship}" if relationship else "",
            f"Product or service category: {category}" if category.strip() else "",
        )
        if line
    )
    with_meta = f"{content_text}\n\n[Context supplied by the user, not part of the post]\n{meta}" if meta else content_text
    brief = "\n".join(t for t in (meta, f"Approved claims, instructions and evidence supplied: {context.strip()}" if context.strip() else "") if t)

    found, detail = run_disclosure_check(with_meta)
    issues += found
    details["disclosure"] = detail

    found, detail = run_claimcheck(content_text, context)
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

    details["revision"] = suggest_content_revision(content_text, issues)

    scope = _scope(
        read_notes,
        "India",
        "Reviewed the text you provided against HYPECHECK's legal sources.",
        "Audio was checked for identifiable commercial music only." if audio_bytes else "",
    )
    return RunResult(build_report(issues, modules), details, modules, scope)
