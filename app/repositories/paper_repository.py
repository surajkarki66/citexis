from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.constants import EmbeddingStatus
from app.core.schemas.paper import PaperCreate, PaperSummary


class PaperRepository:
    COLLECTION = "papers"

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col = db[self.COLLECTION]

    async def create(self, paper: PaperCreate) -> str:
        doc = paper.model_dump()
        doc["embedding_status"] = EmbeddingStatus.PENDING
        doc["download_count"] = 0
        doc["view_history"] = []
        result = await self._col.insert_one(doc)
        return str(result.inserted_id)

    async def get_by_id(self, paper_id: str) -> dict | None:
        if not ObjectId.is_valid(paper_id):
            return None
        return await self._col.find_one({"_id": ObjectId(paper_id)})

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
