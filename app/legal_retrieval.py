"""Lightweight, in-memory RAG layer over the ASCI / CCPA / CPA source texts.

Deliberately not a vector database: the corpus is a handful of markdown files.
We chunk each document by its markdown headings, then retrieve with TF-IDF
cosine similarity implemented in pure Python (stdlib only -- no scikit-learn,
no numpy). This is enough to ground every module's verdict in an actual
retrieved provision instead of letting the LLM free-hand legal reasoning from
parametric memory -- and, unlike embedding-based retrieval, it needs no extra
API key.

Pure Python is deliberate, not a style preference: scikit-learn's compiled
extensions (e.g. its internal murmurhash .pyd) get blocked outright by
Windows Application Control / Smart App Control on some machines, which took
down this exact module for a collaborator. TF-IDF over ~40 short chunks is
well within what plain Python comfortably handles, so the compiled dependency
wasn't buying anything worth that fragility.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache

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


# ---------------------------------------------------------------------------
# Pure-Python TF-IDF: tokenize -> unigrams+bigrams (stopwords dropped at the
# unigram level) -> smoothed IDF -> L2-normalized TF-IDF vectors -> cosine
# similarity via sparse dict dot product. Mirrors
# sklearn.feature_extraction.text.TfidfVectorizer(stop_words="english",
# ngram_range=(1, 2)) closely enough for this corpus's purposes.
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-zA-Z]{2,}")

_STOPWORDS = frozenset(
    """
    a about above after again against all am an and any are aren't as at be
    because been before being below between both but by can't cannot could
    couldn't did didn't do does doesn't doing don't down during each few for
    from further had hadn't has hasn't have haven't having he he'd he'll he's
    her here here's hers herself him himself his how how's i i'd i'll i'm i've
    if in into is isn't it it's its itself let's me more most mustn't my
    myself no nor not of off on once only or other ought our ours ourselves
    out over own same shan't she she'd she'll she's should shouldn't so some
    such than that that's the their theirs them themselves then there there's
    these they they'd they'll they're they've this those through to too under
    until up very was wasn't we we'd we'll we're we've were weren't what
    what's when when's where where's which while who who's whom why why's
    with won't would wouldn't you you'd you'll you're you've your yours
    yourself yourselves
    """.split()
)

Vector = dict[str, float]


def _terms(text: str) -> list[str]:
    tokens = [t.lower() for t in _TOKEN_RE.findall(text) if t.lower() not in _STOPWORDS]
    terms = list(tokens)
    terms.extend(f"{a} {b}" for a, b in zip(tokens, tokens[1:]))
    return terms


def _l2_normalize(vec: Vector) -> Vector:
    norm = math.sqrt(sum(w * w for w in vec.values()))
    if norm == 0:
        return vec
    return {term: weight / norm for term, weight in vec.items()}


def _cosine(a: Vector, b: Vector) -> float:
    # both vectors are already L2-normalized, so cosine similarity is just
    # the dot product; iterate the smaller of the two for a cheap speedup.
    if len(b) < len(a):
        a, b = b, a
    return sum(weight * b.get(term, 0.0) for term, weight in a.items())


@dataclass
class _Corpus:
    chunks: list[LegalChunk]
    idf: dict[str, float]
    doc_vectors: list[Vector]


@lru_cache(maxsize=1)
def load_corpus() -> _Corpus:
    chunks: list[LegalChunk] = []
    for path in sorted(LEGAL_SOURCES_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        chunks.extend(_split_into_chunks(path.name, raw))

    if not chunks:
        raise RuntimeError(f"No legal source chunks found in {LEGAL_SOURCES_DIR}")

    doc_terms = [_terms(c.text) for c in chunks]

    doc_freq: Counter[str] = Counter()
    for terms in doc_terms:
        doc_freq.update(set(terms))

    n_docs = len(chunks)
    # smoothed idf, matching sklearn's default: ln((1+n)/(1+df)) + 1
    idf = {term: math.log((1 + n_docs) / (1 + df)) + 1.0 for term, df in doc_freq.items()}

    doc_vectors = []
    for terms in doc_terms:
        tf = Counter(terms)
        vec = {term: count * idf[term] for term, count in tf.items()}
        doc_vectors.append(_l2_normalize(vec))

    return _Corpus(chunks=chunks, idf=idf, doc_vectors=doc_vectors)


def _vectorize_query(query: str, idf: dict[str, float]) -> Vector:
    tf = Counter(_terms(query))
    vec = {term: count * idf[term] for term, count in tf.items() if term in idf}
    return _l2_normalize(vec)


def retrieve(query: str, top_k: int = 3, min_score: float = 0.05) -> list[tuple[LegalChunk, float]]:
    """Return up to top_k (chunk, similarity_score) pairs for a query.

    If nothing clears min_score, returns an empty list -- callers must treat
    that as "no relevant provision found" rather than fabricating a citation.
    """
    corpus = load_corpus()
    query_vec = _vectorize_query(query, corpus.idf)
    sims = [_cosine(query_vec, dv) for dv in corpus.doc_vectors]
    ranked = sorted(range(len(corpus.chunks)), key=lambda i: sims[i], reverse=True)
    results = []
    for i in ranked[:top_k]:
        if sims[i] >= min_score:
            results.append((corpus.chunks[i], sims[i]))
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
