from __future__ import annotations

import json
import math
import re
from collections import Counter


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_paragraphs(text: str) -> list[str]:
    blocks = re.split(r"\n\s*\n", text)
    if len(blocks) == 1:
        blocks = re.split(r"(?<=[.!?])\s{2,}", text)
    cleaned = [normalize_whitespace(block) for block in blocks if normalize_whitespace(block)]
    return cleaned


def split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", normalize_whitespace(text))
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def tail_overlap(text: str, overlap_chars: int) -> str:
    if overlap_chars <= 0 or len(text) <= overlap_chars:
        return text
    return text[-overlap_chars:].lstrip()


def safe_json_dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True)


def safe_json_loads(value: str | None, fallback: object) -> object:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[a-zA-Z0-9]+", text)]


def content_tokens(text: str) -> list[str]:
    return [token for token in tokenize(text) if token not in STOP_WORDS and len(token) > 2]


def top_keywords(text: str, limit: int = 6) -> list[str]:
    counts = Counter(content_tokens(text))
    return [word for word, _ in counts.most_common(limit)]


def keyword_label(text: str, limit: int = 4) -> str:
    keywords = top_keywords(text, limit=limit)
    return ", ".join(keywords) if keywords else "key findings"


def truncate_text(text: str, limit: int = 260) -> str:
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3].rstrip()}..."


def cosine_like_overlap(left: str, right: str) -> float:
    left_counts = Counter(content_tokens(left))
    right_counts = Counter(content_tokens(right))
    if not left_counts or not right_counts:
        return 0.0
    shared = sum(left_counts[token] * right_counts[token] for token in set(left_counts) & set(right_counts))
    left_norm = math.sqrt(sum(value * value for value in left_counts.values()))
    right_norm = math.sqrt(sum(value * value for value in right_counts.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return shared / (left_norm * right_norm)
