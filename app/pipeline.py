"""Shared types and helpers for the extract -> classify -> check-against-source
-> verdict pipeline. Every one of the four modules (A-D) is built out of these
same pieces so the reasoning stays consistent and auditable across the app.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.config import RISK_HIGH, RISK_LOW, RISK_MEDIUM, RISK_NONE
from app.legal_retrieval import LegalChunk

RISK_ORDER = {RISK_HIGH: 3, RISK_MEDIUM: 2, RISK_LOW: 1, RISK_NONE: 0}


def normalize_risk(value: str) -> str:
    v = (value or "").strip().upper()
    if v in (RISK_HIGH, RISK_MEDIUM, RISK_LOW, RISK_NONE):
        return v
    # tolerate emoji/short forms the LLM might use despite instructions
    if v in ("RED", "HIGH RISK"):
        return RISK_HIGH
    if v in ("YELLOW", "AMBER", "NEEDS REVISION"):
        return RISK_MEDIUM
    if v in ("GREEN", "OK", "APPROVED"):
        return RISK_LOW if v == "GREEN" else RISK_NONE
    return RISK_MEDIUM  # fail safe: never silently drop an uncertain flag to NONE


def worst_risk(risks: list[str]) -> str:
    if not risks:
        return RISK_NONE
    return max(risks, key=lambda r: RISK_ORDER.get(r, 0))


@dataclass
class Issue:
    """One flagged item, always traceable through the required
    detected-issue -> evidence -> legal-basis -> risk -> fix trail."""

    module: str  # "disclosure" | "claims" | "contract" | "comparative"
    title: str  # short label for the issue card
    risk: str
    evidence: str  # exact quote from the content
    legal_citation: str  # e.g. "ASCI Code - Chapter I - Truthful & Honest Representation"
    legal_text: str  # the actual retrieved provision text backing the flag
    explanation: str  # why this was flagged
    suggested_fix: str = ""
    original_text: str = ""  # for Fix Campaign view: original claim/line
    rewritten_text: str = ""  # for Fix Campaign view: suggested rewrite
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "module": self.module,
            "title": self.title,
            "risk": self.risk,
            "evidence": self.evidence,
            "legal_citation": self.legal_citation,
            "legal_text": self.legal_text,
            "explanation": self.explanation,
            "suggested_fix": self.suggested_fix,
            "original_text": self.original_text,
            "rewritten_text": self.rewritten_text,
            "extra": self.extra,
        }


NO_PROVISION_FOUND = "No relevant ASCI/CCPA provision was retrieved for this check"


def format_chunks_for_prompt(chunks: list[tuple[LegalChunk, float]]) -> str:
    """Render retrieved legal chunks into a numbered block to paste into a
    prompt, so the model can only cite what was actually retrieved."""
    if not chunks:
        return "(No relevant provisions were retrieved for this check. If you cannot ground a finding in one of the numbered provisions below, do not fabricate a citation -- say so explicitly.)"
    lines = []
    for i, (chunk, score) in enumerate(chunks, start=1):
        lines.append(f"[{i}] {chunk.citation}\n{chunk.text}")
    return "\n\n".join(lines)


def resolve_citation(chunks: list[tuple[LegalChunk, float]], index: int | None) -> tuple[str, str]:
    """Map a 1-based index the LLM returned back to (citation, text). Returns
    the NO_PROVISION_FOUND sentinel if the index is missing/out of range --
    never guesses."""
    if not chunks or index is None:
        return NO_PROVISION_FOUND, ""
    try:
        idx = int(index) - 1
    except (TypeError, ValueError):
        return NO_PROVISION_FOUND, ""
    if 0 <= idx < len(chunks):
        chunk, _score = chunks[idx]
        return chunk.citation, chunk.text
    return NO_PROVISION_FOUND, ""
