from app.config import Settings
from app.core.schemas.search import SearchFilters
from app.db.pinecone_client import get_index
from app.repositories.paper_repository import PaperRepository
from app.services.indexing.pinecone_text import paper_record_text
from app.services.search.pinecone_search import search_index


class ContentBasedRecommender:
    def __init__(self, settings: Settings, paper_repo: PaperRepository) -> None:
        self._settings = settings
        self._papers = paper_repo
        self._index = get_index(settings)

    async def recommend(self, paper_id: str, top_k: int = 20) -> list[str]:
        doc = await self._papers.get_by_id(paper_id)
        if not doc:
            return []

        seed_text = paper_record_text(
            doc.get("title", ""),
            doc.get("abstract", ""),
            doc.get("tags"),
        )
        if not seed_text:
            return []

        hits = await search_index(
            self._index,
            self._settings,
            query=seed_text,
            filters=SearchFilters(),
            top_k=top_k + 1,
        )
        ids = [pid for pid, _ in hits]
        return [pid for pid in ids if pid != paper_id][:top_k]
