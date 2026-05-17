from app.core.schemas.paper import PaperCreate
from app.services.ingestion.sources.base import PaperSource


class SemanticScholarSource(PaperSource):
    """Phase 1+: implement Semantic Scholar API client."""

    async def fetch(self, query: str, limit: int) -> list[PaperCreate]:
        raise NotImplementedError("Semantic Scholar source — implement in Phase 1")
