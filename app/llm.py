"""Thin wrapper around the Google Gemini API used by every pipeline module.

Centralising the call here means every module gets JSON-parsing, retry-on-bad-
json, and error handling for free, and the rest of the codebase never touches
the Gemini SDK directly.

Uses Gemini rather than a paid-only API deliberately: Google AI Studio issues
free-tier API keys with no card required, so a publicly hosted demo of this
app costs nothing to run, regardless of how many people use it.

Groq is an optional backup. If GROQ_API_KEY is set and the first-choice service
fails (after its own retries), the same request is sent to the other service.
With no Groq key the behaviour is exactly as before. Failures are logged by type
and status code only, never with any document text.
"""
from __future__ import annotations

import base64
import json
import logging
import re
import time
from functools import lru_cache

import httpx
from google import genai
from google.genai import errors, types

from app.config import (
    GEMINI_API_KEY,
    GROQ_API_KEY,
    GROQ_MODEL_NAME,
    GROQ_VISION_MODEL_NAME,
    MODEL_NAME,
    PRIMARY_PROVIDER,
    VISION_MODEL_NAME,
)

log = logging.getLogger("hypecheck.llm")

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


class GroqError(RuntimeError):
    """A failed Groq call. Carries the HTTP status (None for a network error) and
    never the response body, which could quote the user's document."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class _Reply:
    """The one attribute _request_json reads from a Gemini response."""

    def __init__(self, text):
        self.text = text


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


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


# Groq's free tier is limited by tokens per minute, so a rate-limit reply is normal.
# Wait as long as Groq asks (capped) and try more times than the Gemini path does.
_GROQ_MAX_ATTEMPTS = 6
_GROQ_MAX_WAIT_SECONDS = 30.0


def _groq_wait(resp, attempt):
    try:
        asked = float(resp.headers.get("retry-after", ""))
    except (TypeError, ValueError, AttributeError):
        asked = _BASE_DELAY_SECONDS * (2**attempt)
    return min(asked + 1.0, _GROQ_MAX_WAIT_SECONDS)


def _groq_request(model, messages, max_tokens, temperature):
    """One chat-completions call to Groq in JSON mode.

    Handles three Groq specifics: 429 and 503 are retried after the wait Groq asks for;
    JSON mode rejects a top-level array even when the model answered correctly, in which
    case the model's own answer (returned in the error) is used; and models that think
    before answering can run out of tokens, in which case the budget is raised and the
    call repeated."""
    completion_budget = max_tokens + 1024
    body = {"model": model, "messages": messages, "response_format": {"type": "json_object"}}
    if temperature is not None:
        body["temperature"] = temperature
    if model.startswith("openai/gpt-oss"):
        body["reasoning_effort"] = "low"
    for attempt in range(_GROQ_MAX_ATTEMPTS):
        body["max_completion_tokens"] = completion_budget
        try:
            resp = httpx.post(
                GROQ_URL, headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json=body, timeout=90.0
            )
        except httpx.HTTPError as e:
            raise GroqError(None, f"Groq network error ({type(e).__name__})") from e
        if resp.status_code == 200:
            try:
                return _Reply(resp.json()["choices"][0]["message"]["content"] or "")
            except (ValueError, KeyError, IndexError, TypeError) as e:
                raise GroqError(200, "Groq returned a response in an unexpected shape") from e
        last = attempt == _GROQ_MAX_ATTEMPTS - 1
        if resp.status_code == 400:
            try:
                err = resp.json().get("error", {})
            except ValueError:
                err = {}
            if err.get("code") == "json_validate_failed":
                answer = (err.get("failed_generation") or "").strip()
                if answer:
                    return _Reply(answer)
                if not last:
                    completion_budget += 2048  # the model ran out of tokens while thinking
                    continue
        if resp.status_code not in _RETRYABLE_CODES or last:
            raise GroqError(resp.status_code, f"Groq returned status {resp.status_code}")
        time.sleep(_groq_wait(resp, attempt))
    raise GroqError(None, "Groq call did not complete")


def _provider_order():
    """The services that have a key, first-choice first."""
    order = ["groq", "gemini"] if PRIMARY_PROVIDER == "groq" else ["gemini", "groq"]
    have = {"gemini": bool(GEMINI_API_KEY), "groq": bool(GROQ_API_KEY)}
    return [name for name in order if have[name]]


def _with_fallback(runners):
    """Try each configured service in order. If all fail, raise the first error."""
    providers = _provider_order()
    if not providers:
        raise LLMConfigError(
            "No analysis service is configured. Set GEMINI_API_KEY (a free key, no card "
            "required, at https://aistudio.google.com/apikey). GROQ_API_KEY can be added "
            "as a backup."
        )
    first_error = None
    for position, name in enumerate(providers):
        try:
            return runners[name]()
        except Exception as e:  # noqa: BLE001 - any failure of one service means try the other
            first_error = first_error or e
            code = getattr(e, "code", None)
            more = position < len(providers) - 1
            log.warning(
                "Analysis call failed on %s (%s%s)%s",
                name,
                type(e).__name__,
                f", status {code}" if code else "",
                f"; trying {providers[position + 1]}" if more else "",
            )
    raise first_error


def call_json(system, user_text, max_tokens=4096, temperature=None):
    """Send a system+user prompt, expect a JSON object/array back. A low temperature
    makes repeated runs on the same input agree more often."""
    return _with_fallback(
        {
            "gemini": lambda: _request_json(
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
            ),
            "groq": lambda: _request_json(
                lambda: _groq_request(
                    GROQ_MODEL_NAME,
                    [{"role": "system", "content": system}, {"role": "user", "content": user_text}],
                    max_tokens,
                    temperature,
                )
            ),
        }
    )


def call_vision_json(system, user_text, image_bytes, media_type, max_tokens=4096):
    """Same as call_json but attaches a single image to the user turn."""
    data_url = f"data:{media_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    return _with_fallback(
        {
            "gemini": lambda: _request_json(
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
            ),
            "groq": lambda: _request_json(
                lambda: _groq_request(
                    GROQ_VISION_MODEL_NAME,
                    [
                        {"role": "system", "content": system},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_text},
                                {"type": "image_url", "image_url": {"url": data_url}},
                            ],
                        },
                    ],
                    max_tokens,
                    None,
                )
            ),
        }
    )
