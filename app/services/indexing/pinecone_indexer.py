from app.config import Settings
from app.db.pinecone_client import get_index


class PineconeIndexer:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._index = get_index(settings)

    async def upsert_paper(self, paper_id: str, vector: list[float], doc: dict) -> None:
        metadata = {
            "paper_id": paper_id,
            "year": doc.get("year") or 0,
            "venue": doc.get("venue") or "",
            "domain": doc.get("tags", [""])[0] if doc.get("tags") else "",
            "citation_count": len(doc.get("cited_by", [])),
        }
        self._index.upsert(
            vectors=[(paper_id, vector, metadata)],
            namespace=self._settings.pinecone_namespace,
        )
