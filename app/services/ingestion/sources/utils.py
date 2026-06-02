import re
from html import unescape

from app.core.doi import normalize_doi

__all__ = ["normalize_doi", "strip_html", "reconstruct_abstract", "openalex_short_id", "chunk_list"]


def strip_html(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", text)
    return unescape(re.sub(r"\s+", " ", cleaned)).strip()


def reconstruct_abstract(inverted_index: dict | None) -> str:
    if not inverted_index:
        return ""
    max_pos = max(max(positions) for positions in inverted_index.values())
    words = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for position in positions:
            words[position] = word
    return " ".join(words).strip()


def openalex_short_id(openalex_id: str) -> str:
    return openalex_id.rsplit("/", 1)[-1]


def chunk_list(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]
