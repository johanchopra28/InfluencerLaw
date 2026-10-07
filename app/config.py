import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
LEGAL_SOURCES_DIR = ROOT_DIR / "data" / "legal_sources"

try:
    from dotenv import load_dotenv

    # Explicit path, not a bare load_dotenv(): the Streamlit process is not
    # always launched with this project directory as its cwd (e.g. some
    # process-launcher setups start it from an unrelated working directory),
    # and load_dotenv()'s default upward search from cwd can silently find
    # nothing -- or worse, an unrelated .env elsewhere up the tree.
    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    pass

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
# gemini-3.6-flash (and its siblings gemini-3.8-flash / gemini-flash-latest) were
# returning persistent 503 "high demand" errors as of 2026-10-07 -- confirmed via
# direct API testing with a live key, not specific to any one key/account. The
# "-lite" tier responded reliably (text and vision) during the same test, so that's
# the default now. Override with INFLUENCERLAW_MODEL if/when the flash tier recovers.
MODEL_NAME = os.environ.get("INFLUENCERLAW_MODEL", "gemini-flash-lite-latest")
VISION_MODEL_NAME = os.environ.get("INFLUENCERLAW_VISION_MODEL", MODEL_NAME)

AUDD_API_KEY = os.environ.get("AUDD_API_KEY", "")
AUDD_ENDPOINT = "https://api.audd.io/"

APP_NAME = "HYPECHECK"

# Persistent disclaimer (HYPECHECK_SPEC.md Section 10 - hard requirement, verbatim,
# must appear on every report/dashboard view, never dismissible).
DISCLAIMER_TEXT = (
    "HYPECHECK is a screening tool, not legal advice. "
    "It does not replace review by a qualified lawyer."
)
LAWYER_CONSULT_NOTE = "⚠ Consult a lawyer before publishing this."

# Brand palette (HYPECHECK_SPEC.md Section 5.1). Status colors are reserved for their
# functional role only -- never reused as decorative/editorial color.
COLOR_PAPER_CREAM = "#F5EFE4"
COLOR_INK = "#1B1812"
COLOR_COBALT = "#2C4A9E"
COLOR_MUSTARD = "#D9A125"
COLOR_EDITORIAL_PINK = "#C24B82"

# Risk severities used consistently across all modules.
RISK_HIGH = "HIGH"
RISK_MEDIUM = "MEDIUM"
RISK_LOW = "LOW"
RISK_NONE = "NONE"

# Exact status-color hex values from the brand spec. Reserved for HIGH/MEDIUM/APPROVED
# badges only -- paired with an icon + plain-language label everywhere they're used, so
# risk is never conveyed by color alone.
RISK_COLOR_HEX = {
    RISK_HIGH: "#C13A2A",    # Signal Coral
    RISK_MEDIUM: "#B8791E",  # Caution Amber
    RISK_LOW: "#206B45",     # Cleared Green
    RISK_NONE: "#206B45",
}

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
    "consumer_protection": "Consumer Protection & E-Commerce",
    "comparative": "Comparative Advertising",
    "music": "Music Licensing",
}
