"""Groups a service's findings into a report.

There is deliberately no numeric score and no "approved" or "compliant" status.
A review that finds nothing has only found nothing within its scope, and the
results page must say exactly that, so the headline here never certifies anything.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.config import MODULE_NAMES, RISK_HIGH, RISK_LOW, RISK_MEDIUM, RISK_NONE
from app.pipeline import Issue, worst_risk

_ORDER = {RISK_HIGH: 3, RISK_MEDIUM: 2, RISK_LOW: 1, RISK_NONE: 0}


@dataclass
class Report:
    category_risk: dict[str, str]  # check -> worst risk found, NONE if nothing was flagged
    issues: list[Issue]  # most severe first

    @property
    def counts(self) -> dict[str, int]:
        return {r: sum(1 for i in self.issues if i.risk == r) for r in (RISK_HIGH, RISK_MEDIUM, RISK_LOW)}

    @property
    def headline(self) -> str:
        if not self.issues:
            return (
                "No issues were identified within the scope of this review. "
                "This is not a certification that the material is compliant."
            )
        counts = self.counts
        return (
            "Potential issues were identified: "
            f"{counts[RISK_HIGH]} high, {counts[RISK_MEDIUM]} medium and {counts[RISK_LOW]} low priority."
        )


def build_report(issues: list[Issue], modules: list[str] | None = None) -> Report:
    """`modules` limits the category breakdown to the checks that ran for this service."""
    by_module: dict[str, list[str]] = {}
    for issue in issues:
        by_module.setdefault(issue.module, []).append(issue.risk)
    keys = modules if modules is not None else list(MODULE_NAMES)
    return Report(
        category_risk={m: worst_risk(by_module.get(m, [])) for m in keys},
        issues=sorted(issues, key=lambda i: -_ORDER.get(i.risk, 0)),
    )
