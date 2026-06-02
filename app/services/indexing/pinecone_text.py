MAX_RECORD_TEXT_CHARS = 12_000


def paper_record_text(title: str, abstract: str = "", tags: list[str] | None = None) -> str:
    """Text sent to Pinecone for server-side embedding and rerank."""
    parts = [title.strip(), abstract.strip()]
    if tags:
        parts.append("Keywords: " + ", ".join(t.strip() for t in tags if t.strip()))
    text = "\n\n".join(p for p in parts if p)
    if len(text) > MAX_RECORD_TEXT_CHARS:
        return text[:MAX_RECORD_TEXT_CHARS]
    return text
