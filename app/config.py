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

def _setting(name: str, default: str = "") -> str:
    """A setting from the environment (.env or the host) or, failing that, from
    Streamlit's secrets store. The second route matters on Streamlit Cloud, where
    secrets are only copied into the environment when the app starts."""
    value = os.environ.get(name, "")
    if value:
        return value
    try:
        import streamlit as st

        return str(st.secrets.get(name, "") or default)
    except Exception:  # noqa: BLE001 - no secrets file locally, or Streamlit not running
        return default


GEMINI_API_KEY = _setting("GEMINI_API_KEY")
# gemini-3.6-flash (and its siblings gemini-3.8-flash / gemini-flash-latest) were
# returning persistent 503 "high demand" errors as of 2026-10-07 -- confirmed via
# direct API testing with a live key, not specific to any one key/account. The
# "-lite" tier responded reliably (text and vision) during the same test, so that's
# the default now. Override with HYPECHECK_MODEL if/when the flash tier recovers.
MODEL_NAME = os.environ.get("HYPECHECK_MODEL", "gemini-flash-lite-latest")
VISION_MODEL_NAME = os.environ.get("HYPECHECK_VISION_MODEL", MODEL_NAME)

# Groq is the backup analysis service. It is only used when its key is set, and only
# when the first-choice service fails. Model names can be changed without a code edit.
GROQ_API_KEY = _setting("GROQ_API_KEY")
GROQ_MODEL_NAME = os.environ.get("HYPECHECK_GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_VISION_MODEL_NAME = os.environ.get("HYPECHECK_GROQ_VISION_MODEL", "qwen/qwen3.8-27b")
# Which service is tried first: "gemini" (default) or "groq". The other is the backup.
PRIMARY_PROVIDER = os.environ.get("HYPECHECK_PROVIDER", "gemini").strip().lower()

APP_NAME = "HYPECHECK"

# Persistent disclaimer (HYPECHECK_SPEC.md Section 10 - hard requirement, verbatim,
# must appear on every report/dashboard view, never dismissible).
DISCLAIMER_TEXT = (
    "HYPECHECK is a screening tool, not legal advice. "
    "It does not replace review by a qualified lawyer."
)

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
    RISK_HIGH: "#C0463A",    # red
    RISK_MEDIUM: "#C9982E",  # mustard
    RISK_LOW: "#4A7A52",     # green
    RISK_NONE: "#4A7A52",
}



MODULE_NAMES = {
    "contract_review": "Contract Review",
    "disclosure": "Advertising Disclosure",
    "claims": "ClaimCheck (Substantiation)",
    "contract": "Contract Compliance",
    "consumer_protection": "Consumer Protection & E-Commerce",
    "comparative": "Comparative Advertising",
}
