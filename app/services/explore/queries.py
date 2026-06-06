from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class ExploreService:
    """MongoDB-backed browse queries for /explore and /authors."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col = db["papers"]

    async def get_citation_neighbors(self, paper_id: str, depth: int = 1) -> list[str]:
        paper = await self._col.find_one({"_id": ObjectId(paper_id)})
        if not paper:
            return []
        return list(paper.get("citations", []))

    async def get_author_papers(self, author_name: str, limit: int = 50) -> list[dict]:
        cursor = (
            self._col.find({"authors.name": author_name})
            .sort("year", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def get_topic_clusters(self, tag: str, limit: int = 20) -> list[dict]:
        """Group papers with a shared tag by venue."""
        pipeline = [
            {"$match": {"tags": tag}},
            {"$group": {"_id": "$venue", "count": {"$sum": 1}, "papers": {"$push": "$$ROOT"}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]
        cursor = self._col.aggregate(pipeline)
        return await cursor.to_list(length=limit)
