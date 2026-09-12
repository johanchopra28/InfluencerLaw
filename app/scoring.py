"""The entire compliance-scoring rule lives in this one small module, and the
dashboard shows this rule verbatim -- per the build spec, the score must be
transparent, not a black box.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.config import (
    MODULE_NAMES,
    RISK_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
    RISK_NONE,
    SCORE_DEDUCTIONS,
)
from app.pipeline import Issue, worst_risk

SCORING_RULE_TEXT = (
    "Start at 100 points. For every flagged issue, subtract points by severity: "
    f"HIGH -{SCORE_DEDUCTIONS[RISK_HIGH]}, MEDIUM -{SCORE_DEDUCTIONS[RISK_MEDIUM]}, "
    f"LOW -{SCORE_DEDUCTIONS[RISK_LOW]}. Score floors at 0. "
    "Overall status is HIGH RISK if any HIGH issue exists, NEEDS REVISION if any "
    "MEDIUM issue exists (and no HIGH), otherwise POST APPROVED."
)


@dataclass
class CampaignReport:
    score: int
    status: str
    status_emoji: str
    category_risk: dict[str, str]
    issues: list[Issue]

    @property
    def issues_by_module(self) -> dict[str, list[Issue]]:
        out: dict[str, list[Issue]] = {m: [] for m in MODULE_NAMES}
        for issue in self.issues:
            out.setdefault(issue.module, []).append(issue)
        return out


def score_campaign(issues: list[Issue]) -> CampaignReport:
    score = 100
    for issue in issues:
        score -= SCORE_DEDUCTIONS.get(issue.risk, 0)
    score = max(0, score)

    risks = [i.risk for i in issues]
    if RISK_HIGH in risks:
        status, emoji = "HIGH RISK", "\U0001F534"
    elif RISK_MEDIUM in risks:
        status, emoji = "NEEDS REVISION", "\U0001F7E1"
    else:
        status, emoji = "POST APPROVED", "\U0001F7E2"

    category_risk = {}
    by_module: dict[str, list[str]] = {m: [] for m in MODULE_NAMES}
    for issue in issues:
        by_module.setdefault(issue.module, []).append(issue.risk)
    for module in MODULE_NAMES:
        category_risk[module] = worst_risk(by_module.get(module, []))

    return CampaignReport(
        score=score,
        status=status,
        status_emoji=emoji,
        category_risk=category_risk,
        issues=sorted(issues, key=lambda i: -{"HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}.get(i.risk, 0)),
    )
