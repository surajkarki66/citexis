import asyncio

from app.config import Settings
from app.db.pinecone_client import get_index
from app.services.indexing.pinecone_text import paper_record_text


class PineconeIndexer:
    """Upsert text records; Pinecone embeds using the index's configured model."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._index = get_index(settings)
        self._text_field = settings.pinecone_text_field

    def _record(self, paper_id: str, doc: dict) -> dict:
        record = {
            "_id": paper_id,
            self._text_field: paper_record_text(
                doc.get("title", ""),
                doc.get("abstract", ""),
                doc.get("tags"),
            ),
            "paper_id": paper_id,
            "title": doc.get("title", ""),
            "year": doc.get("year") or 0,
            "venue": doc.get("venue") or "",
            "citation_count": int(doc.get("cited_by_count") or 0),
        }
        if doc.get("tags"):
            record["tags"] = doc.get("tags")
        return record

    async def upsert_paper(self, paper_id: str, doc: dict) -> None:
        await asyncio.to_thread(
            self._index.upsert_records,
            namespace=self._settings.pinecone_namespace,
            records=[self._record(paper_id, doc)],
        )

    async def delete_paper(self, paper_id: str) -> None:
        delete_records = getattr(self._index, "delete_records", None)
        if callable(delete_records):
            await asyncio.to_thread(
                delete_records,
                namespace=self._settings.pinecone_namespace,
                ids=[paper_id],
            )
            return

        # Fallback for index clients exposing the standard delete API.
        delete = getattr(self._index, "delete", None)
        if callable(delete):
            await asyncio.to_thread(
                delete,
                ids=[paper_id],
                namespace=self._settings.pinecone_namespace,
            )
