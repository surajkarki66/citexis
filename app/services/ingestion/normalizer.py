from app.core.schemas.paper import PaperCreate
from app.core.doi import normalize_doi


def normalize_paper(raw: PaperCreate) -> PaperCreate:
    """Canonical cleanup before MongoDB insert."""
    return PaperCreate(
        doi=normalize_doi(raw.doi) if raw.doi else None,
        title=raw.title.strip(),
        authors=raw.authors,
        abstract=raw.abstract.strip(),
        year=raw.year,
        venue=raw.venue,
        citations=raw.citations,
        cited_by_count=max(0, raw.cited_by_count),
        tags=[t.lower().strip() for t in raw.tags],
        full_text_url=raw.full_text_url,
    )
