"""PDF export of a results page.

Built in memory and handed straight to the browser as a download. Nothing is
written to disk or kept on the server, which is what the results page tells the
user about exporting.
"""
from __future__ import annotations

import io
from datetime import date
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.config import APP_NAME, DISCLAIMER_TEXT

_RISK_COLORS = {"HIGH": "#C0463A", "MEDIUM": "#C9982E", "LOW": "#4A7A52"}
_RISK_LABELS = {"HIGH": "High priority", "MEDIUM": "Medium priority", "LOW": "Low priority"}


def _p(text: str) -> str:
    return escape(text or "").replace("\n", "<br/>")


def build_results_pdf(
    *,
    service: str,
    headline: str,
    scope: list[str],
    findings: list[dict],
    sections: list[tuple[str, list[tuple[str, str]]]],
) -> bytes:
    """findings: dicts with risk, title, tags, reference, evidence, why, next_step, questions, source.
    sections: (heading, [(label, text), ...]) blocks shown after the findings."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        title=f"{APP_NAME} results: {service}",
    )
    base = getSampleStyleSheet()
    serif = ParagraphStyle("Serif", parent=base["Title"], fontName="Times-Bold", fontSize=22, alignment=0, spaceAfter=2)
    muted = ParagraphStyle("Muted", parent=base["Normal"], fontSize=9, textColor=colors.HexColor("#6E655E"), leading=13)
    h2 = ParagraphStyle("H2", parent=base["Heading2"], fontName="Times-Bold", fontSize=14, spaceBefore=16, spaceAfter=6)
    body = ParagraphStyle("Body", parent=base["BodyText"], fontSize=10, leading=14)
    label = ParagraphStyle("Label", parent=base["Normal"], fontSize=8, textColor=colors.HexColor("#6E655E"), spaceBefore=6, leading=11)
    note = ParagraphStyle(
        "Note", parent=base["BodyText"], fontSize=9, leading=13, backColor=colors.HexColor("#F3ECE3"),
        borderPadding=7, spaceBefore=10, spaceAfter=6,
    )

    story = [
        Paragraph(f"{APP_NAME} results", serif),
        Paragraph(f"{_p(service)} · generated {date.today().isoformat()}", muted),
        Spacer(1, 8),
        HRFlowable(width="100%", color=colors.HexColor("#CFC7BE")),
        Paragraph(f"{_p(DISCLAIMER_TEXT)} Results are potential issues found by automated analysis and should be "
                  "reviewed by a qualified person before anyone relies on them.", note),
        Paragraph("Review summary", h2),
        Paragraph(f"<b>{_p(headline)}</b>", body),
    ]
    for line in scope:
        story.append(Paragraph(f"• {_p(line)}", body))

    for risk in ("HIGH", "MEDIUM", "LOW"):
        group = [f for f in findings if f["risk"] == risk]
        if not group:
            continue
        story.append(Paragraph(_RISK_LABELS[risk], h2))
        for f in group:
            tag_line = " · ".join(f.get("tags", []))
            block = [
                Paragraph(f'<font color="{_RISK_COLORS[risk]}"><b>{_p(f["title"])}</b></font>', body),
            ]
            if tag_line:
                block.append(Paragraph(_p(tag_line), muted))
            rows = [
                ("What was identified", " ".join(t for t in (f.get("reference"), f.get("evidence")) if t)),
                ("Why it matters", f.get("why", "")),
                ("Recommended next step", f.get("next_step", "")),
            ]
            if f.get("questions"):
                rows.append(("Questions to raise", "\n".join(f"- {q}" for q in f["questions"])))
            rows.append(("Legal or regulatory source", f.get("source", "")))
            for name, text in rows:
                if text:
                    block.append(Paragraph(name.upper(), label))
                    block.append(Paragraph(_p(text), body))
            block.append(Spacer(1, 8))
            block.append(HRFlowable(width="100%", color=colors.HexColor("#E0D5CA")))
            story.append(KeepTogether(block))

    for heading, rows in sections:
        story.append(Paragraph(_p(heading), h2))
        table_rows = [[Paragraph(f"<b>{_p(a)}</b>", body), Paragraph(_p(b), body)] for a, b in rows if a or b]
        if table_rows:
            table = Table(table_rows, colWidths=[1.9 * inch, 4.5 * inch])
            table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#E0D5CA")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(table)

    story.append(
        Paragraph(
            "Suggested wording and drafting directions in this report are suggestions only. They have not been "
            "reviewed or approved by a lawyer, a regulator or a platform, and are not guaranteed to be legally compliant.",
            note,
        )
    )
    doc.build(story)
    return buf.getvalue()
