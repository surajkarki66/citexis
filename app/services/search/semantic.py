from app.config import Settings
from app.core.schemas.search import SearchFilters
from app.db.pinecone_client import get_index
from app.services.embeddings import get_embedding_service


class SemanticSearchService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._index = get_index(settings)
        self._embeddings = get_embedding_service(settings.embedding_model)

    def _build_filter(self, filters: SearchFilters) -> dict | None:
        conditions = []
        if filters.year_min is not None:
            conditions.append({"year": {"$gte": filters.year_min}})
        if filters.year_max is not None:
            conditions.append({"year": {"$lte": filters.year_max}})
        if filters.venue:
            conditions.append({"venue": {"$eq": filters.venue}})
        if not conditions:
            return None
        return {"$and": conditions} if len(conditions) > 1 else conditions[0]

    async def search(self, query: str, filters: SearchFilters, top_k: int = 50) -> list[str]:
        vector = self._embeddings.embed_text(query)
        pinecone_filter = self._build_filter(filters)
        result = self._index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            namespace=self._settings.pinecone_namespace,
            filter=pinecone_filter,
        )
        return [m["id"] for m in result.get("matches", [])]
