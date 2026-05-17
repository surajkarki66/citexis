from app.core.schemas.paper import PaperCreate


def normalize_paper(raw: PaperCreate) -> PaperCreate:
    """Canonical cleanup before MongoDB insert."""
    return PaperCreate(
        doi=raw.doi,
        title=raw.title.strip(),
        authors=raw.authors,
        abstract=raw.abstract.strip(),
        year=raw.year,
        venue=raw.venue,
        citations=raw.citations,
        cited_by=raw.cited_by,
        tags=[t.lower().strip() for t in raw.tags],
        full_text_url=raw.full_text_url,
    )
