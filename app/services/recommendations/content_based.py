from app.config import Settings
from app.db.pinecone_client import get_index
from app.repositories.paper_repository import PaperRepository


class ContentBasedRecommender:
    def __init__(self, settings: Settings, paper_repo: PaperRepository) -> None:
        self._settings = settings
        self._papers = paper_repo
        self._index = get_index(settings)

    async def recommend(self, paper_id: str, top_k: int = 20) -> list[str]:
        fetch = self._index.fetch(ids=[paper_id], namespace=self._settings.pinecone_namespace)
        vectors = fetch.get("vectors", {})
        if paper_id not in vectors:
            return []
        vector = vectors[paper_id]["values"]
        result = self._index.query(
            vector=vector,
            top_k=top_k + 1,
            namespace=self._settings.pinecone_namespace,
            filter={"paper_id": {"$ne": paper_id}},
        )
        return [m["id"] for m in result.get("matches", []) if m["id"] != paper_id][:top_k]
