"""Deterministic BM25-style retrieval over curated, cited NASA/JPL evidence.

This is intentionally not a free-form LLM. Every returned statement is an
extractive source summary; when retrieval is weak, the assistant abstains.
The evidence file is a replaceable data source and keeps mission/instrument,
acquisition time, publication time, citation URL and limitations together.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from ..services.llm_provider import LLMProviderError, generate_grounded_answer

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "evidence" / "curiosity_boxwork.json"
TOKEN = re.compile(r"[a-z0-9]+", re.I)
STOP = {"the", "and", "that", "this", "what", "which", "where", "when", "with", "from", "into", "about", "were", "was", "are", "for", "does", "did", "have", "has", "show", "shows", "near", "along", "could", "would", "should", "mars", "curiosity"}


def load_evidence() -> list[dict[str, Any]]:
    records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("Evidence store must be a JSON array.")
    return records


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN.findall(text) if len(token) > 2 and token.lower() not in STOP]


def retrieve(question: str, limit: int = 5) -> list[dict[str, Any]]:
    query_tokens = _tokens(question)
    if not query_tokens:
        return []
    docs = load_evidence()
    if not docs:
        return []
    query_terms = set(query_tokens)
    doc_tokens: list[list[str]] = []
    for item in docs:
        weighted_text = " ".join([
            (item.get("title", "") + " ") * 3,
            (item.get("instrument", "") + " ") * 2,
            " ".join(item.get("topics", [])) + " ",
            item.get("summary", ""),
        ])
        doc_tokens.append(_tokens(weighted_text))
    avgdl = sum(len(tokens) for tokens in doc_tokens) / max(1, len(doc_tokens))
    document_frequency = {term: sum(1 for tokens in doc_tokens if term in set(tokens)) for term in query_terms}
    scored: list[tuple[float, dict[str, Any]]] = []
    for item, tokens in zip(docs, doc_tokens):
        if not tokens:
            continue
        frequency: dict[str, int] = {}
        for token in tokens:
            frequency[token] = frequency.get(token, 0) + 1
        score = 0.0
        for term in query_terms:
            tf = frequency.get(term, 0)
            if not tf:
                continue
            df = document_frequency[term]
            idf = math.log(1.0 + (len(docs) - df + 0.5) / (df + 0.5))
            k1, b = 1.5, 0.75
            denominator = tf + k1 * (1.0 - b + b * len(tokens) / max(avgdl, 1.0))
            score += idf * (tf * (k1 + 1.0)) / denominator
        topic_tokens = {token for topic in item.get("topics", []) for token in _tokens(topic)}
        title_tokens = set(_tokens(item.get("title", "")))
        score += 1.25 * len(query_terms & topic_tokens)
        score += 1.75 * len(query_terms & title_tokens)
        if score > 0:
            scored.append((score, {**item, "matched_terms": sorted(query_terms & set(tokens))}))
    scored.sort(key=lambda pair: (-pair[0], pair[1].get("date", "")))
    return [{**record, "retrieval_score": round(score, 4)} for score, record in scored[:max(1, min(limit, 8))]]


def answer_question(question: str) -> dict[str, Any]:
    matches = retrieve(question)
    # Abstain if no clear relevance, rather than asking a model to fill gaps.
    if not matches or matches[0]["retrieval_score"] < 0.75:
        return {
            "answer": "I could not find sufficiently relevant evidence in the curated NASA/JPL collection. Try a narrower question about boxwork ridges, hollows, fractures, groundwater, nodules, Mastcam, MAHLI or Curiosity's instrument archives.",
            "evidence": [],
            "mode": "bm25_retrieval_abstained",
            "caution": "No scientific claim was generated because the retrieved evidence did not pass the relevance threshold.",
        }

    cited = matches[:3]
    try:
        generated = generate_grounded_answer(question, cited)
        return {
            "answer": generated["answer"],
            "evidence": cited,
            "mode": "openai_responses_rag",
            "model": generated["model"],
            "response_id": generated.get("response_id"),
            "caution": "The answer was generated from the retrieved evidence shown below. The source pages and original product label/SIS remain authoritative. Model-generated prose can still be incomplete or mistaken; verify important interpretations. This assistant does not infer astronaut safety or assign rover observations to map cells without localization metadata.",
        }
    except LLMProviderError as exc:
        paragraphs = []
        for item in cited:
            source_id = item.get("id", "UNIDENTIFIED_SOURCE")
            date = item.get("date", "date not supplied")
            paragraphs.append(f"{item['title']} (observation date: {date}; evidence ID: {source_id}): {item['summary']}")
        return {
            "answer": "\n\n".join(paragraphs),
            "evidence": cited,
            "mode": "bm25_extractively_grounded",
            "caution": "Each paragraph is a curated source summary, not a new inference. The cited page and original product label/SIS are authoritative. Optional model generation is unavailable, so MARSCOPE used its deterministic extractive fallback. This assistant does not infer astronaut safety or assign rover observations to map cells without localization metadata.",
            "generation_note": str(exc),
        }
