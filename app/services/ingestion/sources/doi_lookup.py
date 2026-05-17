from app.core.schemas.paper import PaperCreate
from app.services.ingestion.sources.base import PaperSource


class DoiLookupSource(PaperSource):
    """Phase 1+: resolve metadata via Crossref / DOI."""

    async def fetch(self, query: str, limit: int) -> list[PaperCreate]:
        # query is treated as DOI for this source
        raise NotImplementedError("DOI lookup — implement in Phase 1")
