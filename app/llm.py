"""Thin wrapper around the Google Gemini API used by every pipeline module.

Centralising the call here means every module gets JSON-parsing, retry-on-bad-
json, and error handling for free, and the rest of the codebase never touches
the Gemini SDK directly.

Uses Gemini rather than a paid-only API deliberately: Google AI Studio issues
free-tier API keys with no card required, so a publicly hosted demo of this
app costs nothing to run, regardless of how many people use it.
"""
from __future__ import annotations

import json
import re
import time
from functools import lru_cache

from google import genai
from google.genai import errors, types

from app.config import GEMINI_API_KEY, MODEL_NAME, VISION_MODEL_NAME

# Confirmed by direct load-testing on 2026-10-07: the free tier returns genuine,
# transient 503s under model-level high demand and 429s under concurrent load
# from this same key (both recovered on retry, not auth/billing failures -- see
# git log for app/config.py). Worth a short retry with backoff rather than
# failing a whole review over a blip.
_RETRYABLE_CODES = {429, 503}
_MAX_ATTEMPTS = 3
_BASE_DELAY_SECONDS = 2.0


class LLMConfigError(RuntimeError):
    pass


def _with_retry(fn):
    last_error = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            return fn()
        except errors.APIError as e:
            last_error = e
            if getattr(e, "code", None) not in _RETRYABLE_CODES or attempt == _MAX_ATTEMPTS - 1:
                raise
            time.sleep(_BASE_DELAY_SECONDS * (2**attempt))
    raise last_error


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise LLMConfigError(
            "GEMINI_API_KEY is not set. Add it to a .env file or export it "
            "before running the app (see .env.example). Get a free key (no "
            "card required) at https://aistudio.google.com/apikey"
        )
    return genai.Client(api_key=GEMINI_API_KEY)


def _extract_json(raw_text: str):
    """Pull a JSON object/array out of a model response, tolerating markdown
    code fences or stray prose around it."""
    text = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fall back to grabbing the outermost {...} or [...] span.
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
    # Last resort: the model sometimes drops the quotes on a key at the start of a
    # line (for example `_reason: "..."`). Only reached once normal parsing has failed.
    repaired = re.sub(r'(?m)^(\s*)_?([A-Za-z][A-Za-z0-9_]*)\s*:', r'\1"\2":', text)
    if repaired != text:
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass
    # The response itself is deliberately left out of the message: it can quote
    # the user's documents, and this error ends up in logs and on screen.
    raise ValueError("The analysis service returned a response that could not be read.")


_JSON_ATTEMPTS = 2


def _request_json(make_request) -> dict | list:
    """Run a request and parse its JSON. The model occasionally returns malformed
    JSON (an unquoted key, a cut-off string), so a bad response is retried once."""
    last_error: ValueError | None = None
    for _ in range(_JSON_ATTEMPTS):
        resp = _with_retry(make_request)
        try:
            return _extract_json(resp.text or "")
        except ValueError as e:
            last_error = e
    raise last_error


def call_json(
    system: str, user_text: str, max_tokens: int = 4096, temperature: float | None = None
) -> dict | list:
    """Send a system+user prompt, expect a JSON object/array back. A low temperature
    makes repeated runs on the same input agree more often."""
    return _request_json(
        lambda: _client().models.generate_content(
            model=MODEL_NAME,
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )
    )


def call_vision_json(
    system: str,
    user_text: str,
    image_bytes: bytes,
    media_type: str,
    max_tokens: int = 4096,
) -> dict | list:
    """Same as call_json but attaches a single image to the user turn."""
    return _request_json(
        lambda: _client().models.generate_content(
            model=VISION_MODEL_NAME,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=media_type),
                user_text,
            ],
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                max_output_tokens=max_tokens,
            ),
        )
    )
