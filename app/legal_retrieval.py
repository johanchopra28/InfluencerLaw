"""Lightweight, in-memory RAG layer over the ASCI / CCPA source texts.

Deliberately not a vector database: the corpus is three markdown files. We chunk
each document by its markdown headings, then retrieve with TF-IDF cosine
similarity (scikit-learn). This is enough to ground every module's verdict in
an actual retrieved provision instead of letting the LLM free-hand legal
reasoning from parametric memory -- and, unlike embedding-based retrieval, it
needs no extra API key.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import LEGAL_SOURCES_DIR

SOURCE_LABELS = {
    "asci_code_core.md": "ASCI Code for Self-Regulation of Advertising Content in India",
    "asci_influencer_guidelines.md": "ASCI Guidelines for Influencer Advertising in Digital Media",
    "ccpa_misleading_ads_guidelines_2022.md": "CCPA Guidelines for Prevention of Misleading Advertisements and Endorsements, 2022",
    "consumer_protection_act_2019_ecommerce_rules_2020.md": "Consumer Protection Act, 2019 / Consumer Protection (E-Commerce) Rules, 2020",
}


@dataclass(frozen=True)
class LegalChunk:
    source_file: str
    source_label: str
    heading: str
    text: str

    @property
    def citation(self) -> str:
        return f"{self.source_label} - {self.heading}"


def _split_into_chunks(source_file: str, raw_text: str) -> list[LegalChunk]:
    """Split a markdown doc into chunks at ## / ### headings."""
    label = SOURCE_LABELS.get(source_file, source_file)
    lines = raw_text.splitlines()
    chunks: list[LegalChunk] = []
    current_heading = "Preamble"
    current_lines: list[str] = []

    def flush():
        body = "\n".join(current_lines).strip()
        if body:
            chunks.append(LegalChunk(source_file, label, current_heading, body))

    for line in lines:
        m = re.match(r"^(#{2,3})\s+(.*)", line)
        if m:
            flush()
            current_heading = m.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)
    flush()
    return [c for c in chunks if len(c.text) > 20]


@lru_cache(maxsize=1)
def load_corpus() -> tuple[list[LegalChunk], TfidfVectorizer, "object"]:
    chunks: list[LegalChunk] = []
    for path in sorted(LEGAL_SOURCES_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        chunks.extend(_split_into_chunks(path.name, raw))

    if not chunks:
        raise RuntimeError(f"No legal source chunks found in {LEGAL_SOURCES_DIR}")

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform([c.text for c in chunks])
    return chunks, vectorizer, matrix


def retrieve(query: str, top_k: int = 3, min_score: float = 0.05) -> list[tuple[LegalChunk, float]]:
    """Return up to top_k (chunk, similarity_score) pairs for a query.

    If nothing clears min_score, returns an empty list -- callers must treat
    that as "no relevant provision found" rather than fabricating a citation.
    """
    chunks, vectorizer, matrix = load_corpus()
    query_vec = vectorizer.transform([query])
    sims = cosine_similarity(query_vec, matrix)[0]
    ranked = sorted(range(len(chunks)), key=lambda i: sims[i], reverse=True)
    results = []
    for i in ranked[:top_k]:
        if sims[i] >= min_score:
            results.append((chunks[i], float(sims[i])))
    return results


def retrieve_for_module(module: str, extra_terms: str = "") -> list[tuple[LegalChunk, float]]:
    """Pre-canned queries per module, so each module always grounds itself
    against the provisions it's actually meant to check, plus any
    claim/clause-specific terms from extra_terms."""
    base_queries = {
        "disclosure": "disclosure label advertisement influencer material connection prominent hashtag",
        "claims": "truthful claims substantiation misleading advertisement objectively ascertainable fact",
        "contract": "truthful claims substantiation misleading comparative advertising disclosure",
        "comparative": "comparative advertising competitor comparison substantiation denigrate",
        "consumer_protection": "misleading advertisement surrogate advertising endorsement material connection disclosure e-commerce seller misrepresentation",
    }
    query = base_queries.get(module, module)
    if extra_terms:
        query = f"{query} {extra_terms}"
    return retrieve(query, top_k=3)
