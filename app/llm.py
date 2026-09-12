"""Thin wrapper around the Anthropic API used by every pipeline module.

Centralising the call here means every module gets JSON-parsing, retry-on-bad-
json, and error handling for free, and the rest of the codebase never touches
the Anthropic SDK directly.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache

import anthropic

from app.config import ANTHROPIC_API_KEY, MODEL_NAME, VISION_MODEL_NAME


class LLMConfigError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _client() -> anthropic.Anthropic:
    if not ANTHROPIC_API_KEY:
        raise LLMConfigError(
            "ANTHROPIC_API_KEY is not set. Add it to a .env file or export it "
            "before running the app (see .env.example)."
        )
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


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
    raise ValueError(f"Could not parse JSON from LLM response:\n{raw_text[:2000]}")


def call_json(system: str, user_text: str, max_tokens: int = 4096) -> dict | list:
    """Send a system+user prompt, expect a JSON object/array back."""
    resp = _client().messages.create(
        model=MODEL_NAME,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_text}],
    )
    raw_text = "".join(block.text for block in resp.content if block.type == "text")
    return _extract_json(raw_text)


def call_vision_json(
    system: str,
    user_text: str,
    image_bytes: bytes,
    media_type: str,
    max_tokens: int = 4096,
) -> dict | list:
    """Same as call_json but attaches a single image to the user turn."""
    import base64

    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    resp = _client().messages.create(
        model=VISION_MODEL_NAME,
        max_tokens=max_tokens,
        system=system,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": b64},
                    },
                    {"type": "text", "text": user_text},
                ],
            }
        ],
    )
    raw_text = "".join(block.text for block in resp.content if block.type == "text")
    return _extract_json(raw_text)
