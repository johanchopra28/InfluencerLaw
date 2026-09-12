import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
LEGAL_SOURCES_DIR = ROOT_DIR / "data" / "legal_sources"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL_NAME = os.environ.get("INFLUENCERLAW_MODEL", "claude-sonnet-5")
VISION_MODEL_NAME = os.environ.get("INFLUENCERLAW_VISION_MODEL", MODEL_NAME)

# Risk severities used consistently across all four modules.
RISK_HIGH = "HIGH"
RISK_MEDIUM = "MEDIUM"
RISK_LOW = "LOW"
RISK_NONE = "NONE"

RISK_EMOJI = {
    RISK_HIGH: "\U0001F534",  # red circle
    RISK_MEDIUM: "\U0001F7E1",  # yellow circle
    RISK_LOW: "\U0001F7E2",  # green circle
    RISK_NONE: "\U0001F7E2",
}

# Deduction applied to the 100-point compliance score per flagged issue, by severity.
# This is the ENTIRE scoring rule -- shown verbatim in the dashboard so it is auditable,
# not a black box.
SCORE_DEDUCTIONS = {
    RISK_HIGH: 25,
    RISK_MEDIUM: 10,
    RISK_LOW: 3,
}

MODULE_NAMES = {
    "disclosure": "Advertising Disclosure",
    "claims": "ClaimCheck (Substantiation)",
    "contract": "Contract Compliance",
    "comparative": "Comparative Advertising",
}
