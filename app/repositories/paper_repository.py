from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.core.constants import EmbeddingStatus
from app.core.schemas.paper import PaperCreate, PaperSummary
from app.core.doi import normalize_doi


class PaperRepository:
    COLLECTION = "papers"

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col = db[self.COLLECTION]

    def _paper_document(self, paper: PaperCreate) -> dict:
        doc = paper.model_dump(exclude_none=True)
        doc["embedding_status"] = EmbeddingStatus.PENDING
        doc["download_count"] = 0
        doc["view_history"] = []
        return doc

    async def create(self, paper: PaperCreate) -> str:
        result = await self._col.insert_one(self._paper_document(paper))
        return str(result.inserted_id)

    async def find_by_doi(self, doi: str) -> dict | None:
        normalized = normalize_doi(doi)
        if not normalized:
            return None
        return await self._col.find_one({"doi": normalized})

    async def create_if_new(self, paper: PaperCreate) -> str | None:
        """
        Insert only if this paper is not already stored.

        Dedup key: normalized DOI when present (see unique sparse index `doi_unique`).
        Papers without a DOI are always inserted — avoid manual duplicates without a DOI.
        """
        normalized = normalize_doi(paper.doi) if paper.doi else None
        if normalized:
            existing = await self.find_by_doi(normalized)
            if existing:
                return None
            paper = paper.model_copy(update={"doi": normalized})

        try:
            return await self.create(paper)
        except DuplicateKeyError:
            return None

    async def get_by_id(self, paper_id: str) -> dict | None:
        if not ObjectId.is_valid(paper_id):
            return None
        return await self._col.find_one({"_id": ObjectId(paper_id)})

    async def delete_by_id(self, paper_id: str) -> bool:
        if not ObjectId.is_valid(paper_id):
            return False
        result = await self._col.delete_one({"_id": ObjectId(paper_id)})
        return result.deleted_count > 0

    async def update_status(self, paper_id: str, status: EmbeddingStatus, **extra) -> None:
        await self._col.update_one(
            {"_id": ObjectId(paper_id)},
            {"$set": {"embedding_status": status, **extra}},
        )

    async def get_many_by_ids(self, paper_ids: list[str]) -> list[dict]:
        oids = [ObjectId(pid) for pid in paper_ids if ObjectId.is_valid(pid)]
        cursor = self._col.find({"_id": {"$in": oids}})
        return await cursor.to_list(length=len(oids))

    @staticmethod
    def to_summary(doc: dict) -> PaperSummary:
        authors = [a.get("name", "") for a in doc.get("authors", [])]
        abstract = doc.get("abstract", "")
        snippet = abstract[:200] + "..." if len(abstract) > 200 else abstract
        return PaperSummary(
            id=str(doc["_id"]),
            title=doc["title"],
            authors=authors,
            year=doc.get("year"),
            venue=doc.get("venue"),
            abstract_snippet=snippet or None,
        )
