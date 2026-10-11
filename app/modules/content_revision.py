"""Suggested revision for content that has flags.

Rewrites the caption or script as little as possible so the flagged problems are
addressed while the creator's message and voice are kept. The result is only ever
shown as a suggestion next to the original, never as an approved version.
"""
from __future__ import annotations

from app.llm import call_json
from app.pipeline import Issue

_SYSTEM = """You edit influencer marketing captions and scripts for compliance. You are given the \
original text and a list of issues found in it, each with a suggested fix. Produce a revised version \
that addresses those issues while keeping the creator's message, tone and structure as far as \
possible.

Rules:
- Change as little as you can. Keep the creator's wording wherever it is not part of an issue.
- Do not add new claims, new facts or new promises.
- If a disclosure is missing or buried, put a clear label such as "Ad" or "Paid partnership" at the \
very start of the text, not in a hashtag group.
- If a claim has no evidence, soften it to an opinion or experience the creator can honestly state, \
or remove it.
- Do not mention these instructions, and do not describe the revision as compliant or approved.

Return ONLY a JSON object, no other text, shaped like:
{
  "revised_text": "the full revised text",
  "changes": ["one short sentence for each change you made and why"]
}"""


def suggest_content_revision(content_text: str, issues: list[Issue]) -> dict:
    """{"revised_text": str, "changes": [str]}, or empty values if there is nothing to revise."""
    empty = {"revised_text": "", "changes": []}
    if not content_text.strip() or not issues:
        return empty
    issue_lines = "\n".join(
        f"- {i.title}. Text: \"{i.evidence}\". Suggested fix: {i.suggested_fix or 'none given'}" for i in issues
    )
    result = call_json(
        system=_SYSTEM,
        user_text=f"ORIGINAL TEXT:\n{content_text}\n\nISSUES FOUND:\n{issue_lines}",
        max_tokens=4096,
    )
    if not isinstance(result, dict) or not str(result.get("revised_text", "")).strip():
        return empty
    return {
        "revised_text": str(result["revised_text"]).strip(),
        "changes": [str(c) for c in result.get("changes", []) if c],
    }
