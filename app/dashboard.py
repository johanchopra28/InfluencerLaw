"""Results display shared by the three service pages.

Every flag is shown in full, no click to reveal: the trail (evidence, legal
basis, why, suggested fix) is the product, so it is never collapsed. All text
that came from a user or a model is escaped before it goes into HTML.
"""
from __future__ import annotations

import re

import streamlit as st

from app.config import APP_NAME, MODULE_NAMES, RISK_COLOR_HEX, RISK_HIGH, RISK_LOW, RISK_MEDIUM
from app.orchestrator import RunResult
from app.pdfgen import generate_license_later_pdf
from app.pipeline import Issue
from app.scoring import SCORING_RULE_TEXT
from app.site import compact, esc, eyebrow, notice

_SHORT_NAMES = {
    "contract_review": "Contract Review",
    "disclosure": "Advertising Disclosure",
    "claims": "ClaimCheck",
    "contract": "Contract Compliance",
    "consumer_protection": "Consumer Protection",
    "comparative": "Comparative Advertising",
    "music": "Music Licensing",
}
_STATUS_RISK = {"HIGH RISK": RISK_HIGH, "NEEDS REVISION": RISK_MEDIUM, "POST APPROVED": RISK_LOW}


_MARKDOWN_MARKS = re.compile(r"[*_`#]+")


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


def _color(risk: str) -> str:
    return RISK_COLOR_HEX.get(risk, RISK_COLOR_HEX[RISK_LOW])


def _label(module: str) -> str:
    return _SHORT_NAMES.get(module, MODULE_NAMES.get(module, module))


def _summary_html(result: RunResult) -> str:
    report = result.report
    status_color = _color(_STATUS_RISK.get(report.status, RISK_MEDIUM))
    chips = "".join(
        f'<span class="hc-chip"><i style="background:{_color(report.category_risk.get(m, "NONE"))}"></i>'
        f"{esc(_label(m))}</span>"
        for m in result.modules
    )
    return compact(
        f"""
        <div class="hc"><div class="hc-eyebrow">Results</div>
        <div class="hc-sample">
        <div class="hc-sample-top">
        <div><div class="hc-mini">Overall status</div>
        <div class="hc-status" style="color:{status_color}">{esc(report.status.capitalize())}</div></div>
        <div><div class="hc-mini">Compliance score</div><div class="hc-score">{report.score} / 100</div></div>
        </div>
        <div class="hc-chips">{chips}</div>
        </div>
        <div class="hc-small" style="margin-top:14px">Scoring rule: {esc(SCORING_RULE_TEXT)}</div>
        </div>
        """
    )


def _flag_html(issue: Issue, lawyer_note: str) -> str:
    label = issue.extra.get("evidence_label", "Evidence")
    evidence = esc(issue.evidence or "(none)")
    if label != "Missing clause":
        evidence = f"&quot;{evidence}&quot;"
    fields = [f'<div class="hc-field"><div class="hc-mini">{esc(label)}</div><div class="hc-quote">{evidence}</div></div>']
    if issue.extra.get("contract_restriction"):
        fields.append(
            '<div class="hc-field"><div class="hc-mini">Contract restriction</div>'
            f'<div class="hc-body">{esc(issue.extra["contract_restriction"])}</div></div>'
        )
    legal = f'<div class="hc-body">{esc(issue.legal_citation)}</div>'
    excerpt = _excerpt(issue.legal_text, f"{issue.evidence} {issue.explanation}") if issue.legal_text else ""
    if excerpt:
        legal += f'<div class="hc-small" style="margin-top:6px">{esc(excerpt)}</div>'
    fields.append(f'<div class="hc-field"><div class="hc-mini">Legal basis</div>{legal}</div>')
    if issue.explanation:
        fields.append(
            f'<div class="hc-field"><div class="hc-mini">Why it was flagged</div>'
            f'<div class="hc-body">{esc(issue.explanation)}</div></div>'
        )
    fields.append(
        '<div class="hc-field"><div class="hc-mini">Suggested fix</div>'
        f'<div class="hc-body">{esc(issue.suggested_fix or "No fix suggested.")}</div></div>'
    )
    if issue.risk == RISK_HIGH:
        fields.append(f'<div class="hc-lawyer">{esc(lawyer_note)}</div>')
    head = (
        f'<div class="hc-flag-label" style="color:{_color(issue.risk)}">'
        f"{esc(f'{issue.risk} · {_label(issue.module)}'.upper())}</div>"
        f'<div class="hc-flag-title">{esc(issue.title)}</div>'
    )
    return compact(f'<div class="hc">{head}{"".join(fields)}</div>')


def _rewrites_html(issues: list[Issue]) -> str:
    cards = []
    for issue in issues:
        original = (
            f'<div><div class="hc-mini">Original</div><div class="hc-body">{esc(issue.original_text)}</div></div>'
            if issue.original_text
            else ""
        )
        why = issue.extra.get("fix_explanation")
        cards.append(
            f'<div class="hc-rewrite" style="border-left:4px solid {_color(issue.risk)}">'
            f'<div class="hc-flag-label" style="color:{_color(issue.risk)}">'
            f"{esc(f'{issue.risk} · {_label(issue.module)}'.upper())}</div>"
            f'<div class="hc-rw-grid">{original}'
            f'<div><div class="hc-mini">Suggested</div><div class="hc-body">{esc(issue.rewritten_text)}</div></div></div>'
            + (f'<div class="hc-small" style="margin-top:12px">Why: {esc(why)}</div>' if why else "")
            + "</div>"
        )
    return compact(f'<div class="hc"><div class="hc-eyebrow" style="margin-top:44px">Suggested rewrites</div>{"".join(cards)}</div>')


def render_points(points: list[dict]) -> None:
    """Commercial and drafting points that need confirming. Listed, never scored."""
    eyebrow("Missing terms and points to confirm")
    if not points:
        notice("No missing or unclear commercial terms were identified.")
        return
    rows = "".join(
        f'<div class="hc-row"><div class="hc-row-topic">{esc(p.get("topic", ""))}'
        f'<span class="hc-row-status">{esc(p.get("status", ""))}</span></div>'
        f'<div class="hc-body">{esc(p.get("note", ""))}</div></div>'
        for p in points
    )
    st.markdown(f'<div class="hc"><div class="hc-rows">{rows}</div></div>', unsafe_allow_html=True)


def _music_notice(result: RunResult) -> None:
    music = result.details.get("music", {})
    if music.get("configured") is False:
        notice(
            f"Music licensing: {music.get('error', 'AUDD_API_KEY is not set')}. "
            "This check was skipped, not scored as clear."
        )
    elif music.get("error"):
        notice(f"The music licensing check failed: {music['error']}")
    elif music.get("identified") is False:
        notice(music.get("message", "No copyrighted track detected."))


def render_results(
    result: RunResult,
    *,
    key: str,
    brand: str = "",
    product: str = "",
    lawyer_note: str = "Consult a lawyer before publishing this.",
    points: list[dict] | None = None,
) -> None:
    st.markdown(_summary_html(result), unsafe_allow_html=True)
    if "music" in result.modules:
        _music_notice(result)

    issues = result.report.issues
    eyebrow_text = f"Flags ({len(issues)})"
    st.markdown(
        f'<div class="hc"><div class="hc-eyebrow" style="margin-top:44px">{eyebrow_text}</div></div>',
        unsafe_allow_html=True,
    )
    if not issues:
        notice(
            "No issues were flagged by these checks. That is not a confirmation that the item "
            "is compliant."
        )

    st.markdown(
        "<style>"
        + "".join(
            f".st-key-flag-{key}-{i} {{ border-left: 4px solid {_color(issue.risk)} !important; }}"
            for i, issue in enumerate(issues)
        )
        + "</style>",
        unsafe_allow_html=True,
    )
    for i, issue in enumerate(issues):
        with st.container(key=f"flag-{key}-{i}"):
            st.markdown(_flag_html(issue, lawyer_note), unsafe_allow_html=True)
            if issue.extra.get("requires_license_later_doc"):
                st.markdown(
                    f'<div class="hc"><div class="hc-small" style="margin-top:18px">{APP_NAME} identifies and '
                    "flags music. It does not broker or verify licenses. Generate an acknowledgment "
                    "document for your legal and brand team to sign off once the track is actually "
                    "cleared.</div></div>",
                    unsafe_allow_html=True,
                )
                label = f"{issue.extra.get('artist', '')} - {issue.extra.get('title', '')}"
                if issue.extra.get("label"):
                    label += f" ({issue.extra['label']})"
                st.download_button(
                    "Generate license-later document (PDF)",
                    data=generate_license_later_pdf(
                        brand=brand,
                        product=product,
                        items=[
                            {
                                "what_detected": label,
                                "why_flagged": issue.explanation,
                                "required_action": issue.suggested_fix,
                            }
                        ],
                    ),
                    file_name=f"license-later-{(brand or 'campaign').replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    key=f"license-pdf-{key}-{i}",
                )

    if points is not None:
        st.markdown('<div style="height:44px"></div>', unsafe_allow_html=True)
        render_points(points)

    rewrites = [i for i in issues if i.rewritten_text]
    if rewrites:
        st.markdown(_rewrites_html(rewrites), unsafe_allow_html=True)

    with st.expander("Technical detail"):
        st.json(result.details)
