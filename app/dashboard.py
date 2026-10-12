"""Results pages for the three services.

One structure for all of them: a review summary, findings grouped by priority,
then the sections specific to the service, the sources cited, and export / run
another check. Every finding is shown in full, no click to reveal. All text that
came from a user or a model is escaped before it goes into HTML.

Rules the page follows (they come from the product spec, so keep them):
  - never show a single green "compliant" result because nothing was found;
  - tell a potential risk apart from missing information and from something
    that needs human review;
  - cite only sources that were retrieved, and link only links that were verified;
  - present suggested wording as a suggestion, never as approved or compliant.
"""
from __future__ import annotations

import difflib
import re

import streamlit as st

from app.config import APP_NAME, MODULE_NAMES, RISK_COLOR_HEX, RISK_HIGH, RISK_LOW, RISK_MEDIUM
from app.export import build_results_pdf
from app.orchestrator import RunResult
from app.pipeline import Issue
from app.site import compact, esc, notice, reset_state
from app.sources import source_url

_SHORT_NAMES = {
    "contract_review": "Contract Review",
    "disclosure": "Advertising Disclosure",
    "claims": "ClaimCheck",
    "contract": "Contract Compliance",
    "consumer_protection": "Consumer Protection",
    "comparative": "Comparative Advertising",
}
_GROUPS = [
    (RISK_HIGH, "High", "Priority flags"),
    (RISK_MEDIUM, "Medium", "Review suggested"),
    (RISK_LOW, "Low", "Lower-priority flags"),
]
_CRITERIA = [
    (
        "High",
        "Could expose someone to a misleading advertisement or an undisclosed endorsement, clearly "
        "conflicts with a cited provision, or (in a contract) removes a core protection such as payment "
        "certainty or a fair exit.",
    ),
    ("Medium", "Potentially misleading, unclear or one-sided, so a review is suggested."),
    ("Low", "A minor point."),
    (
        "Commercial term",
        "A contract term that is one-sided or missing, such as payment, exclusivity, usage rights, termination "
        "or liability. HYPECHECK's legal sources do not cover these subjects, so no legal source is cited. It is "
        "flagged for a person to judge, not as a breach of any rule.",
    ),
    ("Needs human review", "Ambiguous, dependent on facts or law outside the sources HYPECHECK uses, or uncertain."),
]
_CONTRACT_MODULES = ("contract_review", "contract")
_MARKDOWN_MARKS = re.compile(r"[*_`#]+")


def _color(risk: str) -> str:
    return RISK_COLOR_HEX.get(risk, RISK_COLOR_HEX[RISK_LOW])


def _label(module: str) -> str:
    return _SHORT_NAMES.get(module, MODULE_NAMES.get(module, module))


def _gap(px: int) -> None:
    st.markdown(f'<div style="height:{px}px"></div>', unsafe_allow_html=True)


def _heading(text: str, top: int = 44) -> None:
    st.markdown(
        f'<div class="hc"><div class="hc-eyebrow" style="margin-top:{top}px">{esc(text)}</div></div>',
        unsafe_allow_html=True,
    )


def _excerpt(legal_text: str, hint: str, limit: int = 480) -> str:
    """The part of a retrieved legal chunk that best matches the finding, as plain text.

    Chunks are whole sections of a source document (Chapter I runs to several
    screens), so showing one unabridged buries the sentence that matters. Prefer
    the clause the finding names outright (for example "ASCI Code 1.1"); else
    take the paragraph, and within a long one the lettered item or sentence,
    that shares the most words with the evidence and explanation. Markdown
    marks are stripped and the text is cut at a sentence end.
    """
    paragraphs = [
        re.sub(r"\s+", " ", _MARKDOWN_MARKS.sub("", p)).strip() for p in re.split(r"\n\s*\n", legal_text)
    ]
    paragraphs = [p for p in paragraphs if p]
    if not paragraphs:
        return ""

    named = re.findall(r"\b\d+\.\d+\b", hint)
    best = next((p for n in named for p in paragraphs if p.startswith(f"{n} ")), None)
    start_at_item = 0
    items: list[str] = []
    if best is None:
        hint_words = set(re.findall(r"[a-z]{4,}", hint.lower()))

        def overlap(text: str) -> float:
            words = set(re.findall(r"[a-z]{4,}", text.lower()))
            return len(hint_words & words) / (len(words) ** 0.5 or 1)

        best = max(paragraphs, key=overlap)
        if len(best) > limit:
            items = re.split(r"(?<=[.;])\s+(?=\([a-z]\)|[A-Z0-9])", best)
            start_at_item = max(range(len(items)), key=lambda i: overlap(items[i]))
    if items:
        best = " ".join(items[start_at_item:])
    if len(best) <= limit:
        return best
    cut = best[:limit]
    stop = max(cut.rfind(". "), cut.rfind("; "))
    return (cut[: stop + 1] if stop > limit // 2 else cut.rstrip()) + " ..."


def _tags(issue: Issue) -> list[str]:
    tags = [issue.extra.get("finding_type", "Potential risk")]
    if issue.extra.get("needs_human_review") or issue.risk == RISK_HIGH:
        tags.append("Needs human review")
    return tags


def _tag_class(tag: str) -> str:
    if tag == "Needs human review":
        return "hc-tag hc-tag--human"
    if tag == "Missing information":
        return "hc-tag hc-tag--missing"
    return "hc-tag"


_ASCI_SUFFIX = "ASCI is a private self-regulatory body. Please follow this up with a thorough reading of the relevant law and contextualised professional legal advice."


def _is_asci(issue: Issue) -> bool:
    return issue.legal_citation.strip().upper().startswith("ASCI")


def _source_text(issue: Issue) -> str:
    if issue.extra.get("commercial"):
        return "No legal source cited (commercial term)"
    url = source_url(issue.legal_citation)
    text = f"{issue.legal_citation} ({url})" if url else issue.legal_citation
    return f"{text}. {_ASCI_SUFFIX}" if _is_asci(issue) else text


def _link(label: str, url: str | None) -> str:
    text = esc(label)
    if not url:
        return text
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{text}</a>'


def _summary_html(result: RunResult, overview: str) -> str:
    report = result.report
    counts = report.counts
    count_html = "".join(
        f'<span><i style="background:{_color(r)}"></i>{counts[r]} {name}</span>'
        for r, name in ((RISK_HIGH, "high"), (RISK_MEDIUM, "medium"), (RISK_LOW, "low"))
    )
    chips = []
    for module in result.modules:
        risk = report.category_risk.get(module, "NONE")
        dot = f'<i style="background:{_color(risk)}"></i>' if risk != "NONE" else '<i class="dot-none"></i>'
        chips.append(f'<span class="hc-chip">{dot}{esc(_label(module))}</span>')
    scope = "".join(f"<li>{esc(line)}</li>" for line in result.scope)
    overview_html = f'<div class="hc-body" style="margin-bottom:20px">{esc(overview)}</div>' if overview else ""
    criteria = "".join(
        f'<div class="hc-row"><div class="hc-row-topic">{esc(name)}</div><div class="hc-body">{esc(text)}</div></div>'
        for name, text in _CRITERIA
    )
    return compact(
        f"""
        <div class="hc">
        <div class="hc-eyebrow">Your {APP_NAME} results</div>
        <p class="hc-small" style="max-width:700px;margin:0 0 16px">These are potential issues found by automated
        analysis. Review them before relying on them, and have a qualified person look at anything marked high priority.</p>
        <div class="hc-sample">
        <div class="hc-mini">Review summary</div>
        {overview_html}
        <div class="hc-mini">Overall result</div>
        <div class="hc-result">{esc(report.headline)}</div>
        <div class="hc-counts">{count_html}</div>
        <div class="hc-mini">Scope and limitations</div>
        <ul class="hc-scope">{scope}</ul>
        <div class="hc-mini">Checks run</div>
        <div class="hc-chips">{"".join(chips)}</div>
        <div class="hc-small" style="margin-top:10px">A filled dot means that check flagged something. An empty dot
        means it found nothing within its scope, which is not the same as clearing it.</div>
        </div>
        <div class="hc-mini" style="margin-top:22px">How priority is set</div>
        <div class="hc-rows hc-criteria">{criteria}</div>
        </div>
        """
    )


def _flag_html(issue: Issue, lawyer_note: str) -> str:
    tag_html = "".join(f'<span class="{_tag_class(t)}">{esc(t)}</span>' for t in _tags(issue))
    evidence = esc(issue.evidence or "(none)")
    if issue.extra.get("evidence_label") != "Missing clause":
        evidence = f"&quot;{evidence}&quot;"
    reference = issue.extra.get("reference", "")
    identified = f'<div class="hc-quote">{evidence}</div>'
    if reference:
        identified = f'<div class="hc-small" style="margin-bottom:4px">{esc(reference)}</div>' + identified
    if issue.extra.get("contract_restriction"):
        identified += (
            f'<div class="hc-small" style="margin-top:8px">Contract restriction: '
            f'{esc(issue.extra["contract_restriction"])}</div>'
        )
    fields = [f'<div class="hc-field"><div class="hc-mini">What was identified</div>{identified}</div>']
    if issue.explanation:
        fields.append(
            '<div class="hc-field"><div class="hc-mini">Why it matters</div>'
            f'<div class="hc-body">{esc(issue.explanation)}</div></div>'
        )
    fix = issue.suggested_fix
    if fix and issue.module in ("claims", "comparative"):
        fix = f"Suggested wording: “{fix}”"
    step = f'<div class="hc-body">{esc(fix or "No next step suggested.")}</div>'
    if issue.suggested_fix and issue.module in ("claims", "comparative"):
        step += f'<div class="hc-small" style="margin-top:6px">{esc(_WORDING_NOTE)}</div>'
    elif issue.module in _CONTRACT_MODULES and issue.suggested_fix:
        step += (
            '<div class="hc-small" style="margin-top:6px">A suggestion for discussion, '
            f"not a clause approved by a lawyer. {esc(_WORDING_NOTE)}</div>"
        )
    questions = issue.extra.get("questions") or []
    if questions:
        items = "".join(f"<li>{esc(q)}</li>" for q in questions)
        step += f'<div class="hc-mini" style="margin-top:14px">Questions to raise</div><ul class="hc-scope" style="margin:0">{items}</ul>'
    fields.append(f'<div class="hc-field"><div class="hc-mini">Recommended next step</div>{step}</div>')

    if issue.extra.get("commercial"):
        fields.append(
            '<div class="hc-field"><div class="hc-mini">Basis for this flag</div>'
            '<div class="hc-body">This is a commercial term. HYPECHECK&#39;s legal sources do not cover this subject, '
            "so no legal source is cited. It is flagged because the term is one-sided or missing, not because it "
            "breaches a rule. A person should decide whether it is acceptable.</div></div>"
        )
    else:
        source = f'<div class="hc-body">{_link(issue.legal_citation, source_url(issue.legal_citation))}</div>'
        if _is_asci(issue):
            source += f'<div class="hc-small" style="margin-top:6px">{esc(_ASCI_SUFFIX)}</div>'
        excerpt = _excerpt(issue.legal_text, f"{issue.evidence} {issue.explanation}") if issue.legal_text else ""
        if excerpt:
            source += f'<div class="hc-small" style="margin-top:6px">{esc(excerpt)}</div>'
        fields.append(f'<div class="hc-field"><div class="hc-mini">Legal or regulatory source</div>{source}</div>')

    if issue.risk == RISK_HIGH:
        fields.append(f'<div class="hc-lawyer">{esc(lawyer_note)}</div>')
    head = (
        f'<div class="hc-flag-label" style="color:{_color(issue.risk)}">{esc(_label(issue.module).upper())}</div>'
        f'<div class="hc-tags">{tag_html}</div>'
        f'<div class="hc-flag-title">{esc(issue.title)}</div>'
    )
    return compact(f'<div class="hc">{head}{"".join(fields)}</div>')


def _group_head_html(risk: str, name: str, caption: str) -> str:
    return (
        f'<div class="hc"><div class="hc-group"><b style="color:{_color(risk)}">{esc(name)}</b>'
        f"<span>{esc(caption)}</span></div></div>"
    )


def _rows_html(rows: list[tuple[str, str, str]]) -> str:
    """rows: (topic, small caption under the topic, body)."""
    inner = ""
    for topic, caption, body in rows:
        caption_html = f'<span class="hc-row-status">{esc(caption)}</span>' if caption else ""
        inner += (
            f'<div class="hc-row"><div class="hc-row-topic">{esc(topic)}{caption_html}</div>'
            f'<div class="hc-body">{esc(body)}</div></div>'
        )
    return f'<div class="hc"><div class="hc-rows">{inner}</div></div>'


_WORDING_NOTE = (
    "This wording is a starting point only. Apply a more contextualised factual and legal check before "
    "considering it, and do not use it as is."
)
_ADVICE_LINE = "Please take legal advice as applicable to the context and the contractual dealing."


def _rewrites_html(issues: list[Issue], heading: str) -> str:
    cards = []
    for issue in issues:
        original = (
            f'<div><div class="hc-mini">Original</div><div class="hc-body">{esc(issue.original_text)}</div></div>'
            if issue.original_text
            else ""
        )
        cards.append(
            f'<div class="hc-rewrite" style="border-left:4px solid {_color(issue.risk)}">'
            f'<div class="hc-flag-label" style="color:{_color(issue.risk)}">{esc(_label(issue.module).upper())}</div>'
            f'<div class="hc-rw-grid">{original}'
            f'<div><div class="hc-mini">Suggested</div><div class="hc-body">{esc(issue.rewritten_text)}</div>'
            f'<div class="hc-small" style="margin-top:8px">{esc(_ADVICE_LINE)}</div></div></div></div>'
        )
    return compact(
        f'<div class="hc"><div class="hc-eyebrow" style="margin-top:44px">{esc(heading)}</div>'
        '<p class="hc-small" style="max-width:640px">Suggestions for discussion. They have not been reviewed or '
        "approved by a lawyer, a regulator or a platform, and are not guaranteed to be legally compliant.</p>"
        f'{"".join(cards)}</div>'
    )


def _diff_html(original: str, revised: str) -> tuple[str, str]:
    """The original and revised text as HTML with the differences highlighted."""
    a = re.findall(r"\S+|\n", original)
    b = re.findall(r"\S+|\n", revised)

    def render(tokens: list[str], mark: str | None = None) -> str:
        text = " ".join("<br>" if t == "\n" else esc(t) for t in tokens)
        return f'<{mark} class="hc-{mark}">{text}</{mark}>' if mark and text.strip() else text

    left: list[str] = []
    right: list[str] = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            left.append(render(a[i1:i2]))
            right.append(render(b[j1:j2]))
        else:
            if i2 > i1:
                left.append(render(a[i1:i2], "del"))
            if j2 > j1:
                right.append(render(b[j1:j2], "ins"))
    return " ".join(left), " ".join(right)


def _issue_payload(issue: Issue) -> dict:
    return {
        "risk": issue.risk,
        "title": issue.title,
        "tags": _tags(issue),
        "reference": issue.extra.get("reference", ""),
        "evidence": issue.evidence,
        "why": issue.explanation,
        "next_step": (
            f"{issue.suggested_fix} ({_WORDING_NOTE})"
            if issue.suggested_fix and issue.module in ("claims", "comparative", *_CONTRACT_MODULES)
            else issue.suggested_fix
        ),
        "questions": issue.extra.get("questions") or [],
        "source": _source_text(issue),
    }


# ---------------------------------------------------------------------------
# building blocks used by every service
# ---------------------------------------------------------------------------


def _render_findings(result: RunResult, *, key: str, lawyer_note: str) -> None:
    issues = result.report.issues
    if not issues:
        _gap(24)
        notice(
            "No issues were identified within the scope of this review. That is not a confirmation that "
            "the material is compliant."
        )
        return
    st.markdown(
        "<style>"
        + "".join(
            f".st-key-flag-{key}-{i} {{ border-left: 4px solid {_color(issue.risk)} !important; }}"
            for i, issue in enumerate(issues)
        )
        + "</style>",
        unsafe_allow_html=True,
    )
    for risk, name, caption in _GROUPS:
        group = [(i, issue) for i, issue in enumerate(issues) if issue.risk == risk]
        if not group:
            continue
        st.markdown(_group_head_html(risk, name, caption), unsafe_allow_html=True)
        for i, issue in group:
            with st.container(key=f"flag-{key}-{i}"):
                st.markdown(_flag_html(issue, lawyer_note), unsafe_allow_html=True)



def _render_sources(result: RunResult, heading: str) -> None:
    cited: list[str] = []
    for issue in result.report.issues:
        if issue.extra.get("commercial"):
            continue
        if issue.legal_citation not in cited:
            cited.append(issue.legal_citation)
    if not cited:
        return
    _heading(heading)
    items = "".join(f"<li>{_link(c, source_url(c))}</li>" for c in cited)
    st.markdown(
        f'<div class="hc"><ul class="hc-scope" style="font-size:14px">{items}</ul>'
        '<div class="hc-small">Sources are linked only where the link has been checked.</div></div>',
        unsafe_allow_html=True,
    )


def _render_actions(
    result: RunResult,
    *,
    key: str,
    service: str,
    reset_prefix: str,
    sections: list[tuple[str, list[tuple[str, str]]]],
    overview: str = "",
) -> None:
    scope = ([overview] if overview else []) + result.scope
    pdf = build_results_pdf(
        service=service,
        headline=result.report.headline,
        scope=scope,
        findings=[_issue_payload(i) for i in result.report.issues],
        sections=sections,
    )
    _heading("What next", top=52)
    st.markdown(
        '<div class="hc"><p class="hc-small" style="max-width:640px">Exporting creates a PDF of these results '
        "for your session and downloads it to your device. HYPECHECK does not keep a copy. The file can "
        "contain confidential material, so store it securely.</p></div>",
        unsafe_allow_html=True,
    )
    left, right, _ = st.columns([1.1, 1, 2], gap="small")
    with left:
        st.download_button(
            "Export results (PDF)",
            data=pdf,
            file_name=f"hypecheck-{key}-results.pdf",
            mime="application/pdf",
            key=f"export-{key}",
        )
    with right:
        st.button("Run another check", key=f"again-{key}", on_click=reset_state, args=(reset_prefix,))


def _render_summary(result: RunResult, overview: str = "") -> None:
    st.markdown(_summary_html(result, overview), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# the three services
# ---------------------------------------------------------------------------


def render_contract_results(result: RunResult, *, reset_prefix: str) -> None:
    key = "contract"
    _render_summary(result)
    _render_findings(result, key=key, lawyer_note="Consult a lawyer before signing this.")

    rewrites = [i for i in result.report.issues if i.rewritten_text]
    if rewrites:
        st.markdown(_rewrites_html(rewrites, "Suggested drafting directions"), unsafe_allow_html=True)
    _render_sources(result, "Legal and regulatory sources cited")
    _render_actions(
        result,
        key=key,
        service="Contract check",
        reset_prefix=reset_prefix,
        sections=[],
    )


def render_campaign_results(result: RunResult, *, reset_prefix: str) -> None:
    key = "campaign"
    detail = result.details["campaign"]
    overview = detail["overview"]
    _render_summary(result, overview)
    _render_findings(
        result, key=key, lawyer_note="Consult a lawyer before proceeding with this campaign."
    )

    consistency = detail["deliverable_consistency"]
    _heading("Deliverable consistency")
    if consistency:
        rows = [
            (d.get("deliverable", ""), d.get("reference", ""), f"{d.get('issue', '')} Next step: {d.get('next_step', '')}")
            for d in consistency
        ]
        st.markdown(_rows_html(rows), unsafe_allow_html=True)
    else:
        notice("No mismatches between the deliverables and the supplied brief were identified.")

    rights = detail["rights_permissions"]
    _heading("Rights and permissions")
    if rights:
        rows = [
            (str(r.get("topic", "")).capitalize(), r.get("reference", ""), f"{r.get('concern', '')} Next step: {r.get('next_step', '')}")
            for r in rights
        ]
        st.markdown(_rows_html(rows), unsafe_allow_html=True)
    else:
        notice("No rights or permissions concerns were identified in the supplied material.")

    missing = detail["missing_information"]
    _heading("Information still needed")
    if missing:
        rows = [(m.get("item", ""), "Missing information", m.get("reason", "")) for m in missing]
        st.markdown(_rows_html(rows), unsafe_allow_html=True)
    else:
        notice("No further information was identified as needed.")

    _render_sources(result, "Applicable requirements")

    steps = [f"{_label(i.module)}: {i.suggested_fix}" for i in result.report.issues if i.suggested_fix]
    steps += [f"Provide: {m.get('item', '')}" for m in missing if m.get("item")]
    if any(i.risk == RISK_HIGH for i in result.report.issues):
        steps.append("Escalate the high-priority flags for qualified human review before the campaign goes ahead.")
    _heading("Recommended next steps")
    if steps:
        st.markdown(_rows_html([(f"{n}.", "", s) for n, s in enumerate(steps, 1)]), unsafe_allow_html=True)
    else:
        notice("No specific next steps were identified.")

    _render_actions(
        result,
        key=key,
        service="Campaign check",
        reset_prefix=reset_prefix,
        overview=overview,
        sections=[
            (
                "Deliverable consistency",
                [(d.get("deliverable", ""), f"{d.get('issue', '')} Next step: {d.get('next_step', '')}") for d in consistency],
            ),
            (
                "Rights and permissions",
                [(str(r.get("topic", "")), f"{r.get('concern', '')} Next step: {r.get('next_step', '')}") for r in rights],
            ),
            ("Information still needed", [(m.get("item", ""), m.get("reason", "")) for m in missing]),
            ("Recommended next steps", [(f"{n}.", s) for n, s in enumerate(steps, 1)]),
        ],
    )


def render_content_results(result: RunResult, *, original: str, reset_prefix: str) -> None:
    key = "content"
    revision = result.details.get("revision", {})
    _render_summary(result)
    _render_findings(
        result, key=key, lawyer_note="Consult a lawyer before publishing this."
    )

    sections: list[tuple[str, list[tuple[str, str]]]] = []
    if revision.get("revised_text"):
        left, right = _diff_html(original, revision["revised_text"])
        _heading("Suggested revision")
        st.markdown(
            compact(
                f"""
                <div class="hc">
                <p class="hc-small" style="max-width:700px">A suggested caption that addresses the flags above while keeping
                your message. Changes are highlighted. It is a suggestion: it has not been reviewed or approved by a lawyer,
                a regulator or a platform, and it is not guaranteed to be legally compliant. {esc(_WORDING_NOTE)}</p>
                <div class="hc-compare">
                <div><div class="hc-mini">Original</div><div class="hc-body">{left}</div></div>
                <div><div class="hc-mini">Suggested</div><div class="hc-body">{right}</div></div>
                </div></div>
                """
            ),
            unsafe_allow_html=True,
        )
        changes = revision.get("changes", [])
        if changes:
            items = "".join(f"<li>{esc(c)}</li>" for c in changes)
            st.markdown(
                f'<div class="hc"><div class="hc-mini" style="margin-top:18px">What changed and why</div><ul class="hc-scope">{items}</ul></div>',
                unsafe_allow_html=True,
            )
        sections.append(
            ("Suggested revision", [("Original", original), ("Suggested", revision["revised_text"]), ("Note", _WORDING_NOTE)] + [("Change", c) for c in changes])
        )

    _render_sources(result, "Legal and regulatory sources cited")
    _render_actions(result, key=key, service="Content check", reset_prefix=reset_prefix, sections=sections)
