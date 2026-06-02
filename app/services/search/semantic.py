from app.config import Settings
from app.core.schemas.search import SearchFilters
from app.db.pinecone_client import get_index
from app.services.search.pinecone_search import search_index


class SemanticSearchService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._index = get_index(settings)

    async def search(
        self, query: str, filters: SearchFilters, top_k: int = 50
    ) -> list[tuple[str, float]]:
        return await search_index(
            self._index,
            self._settings,
            query=query,
            filters=filters,
            top_k=top_k,
        )
