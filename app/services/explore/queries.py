import re

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

    async def get_tag_clusters(self, query: str, limit: int = 20) -> list[dict]:
        """Group papers whose tags match the query, clustered by tag."""
        pattern = re.escape(query.strip())
        if not pattern:
            return []

        tag_match = {"$regex": pattern, "$options": "i"}
        pipeline = [
            {"$match": {"tags": tag_match}},
            {"$unwind": "$tags"},
            {"$match": {"tags": tag_match}},
            {
                "$group": {
                    "_id": "$tags",
                    "count": {"$sum": 1},
                    "papers": {"$push": "$$ROOT"},
                },
            },
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]
        cursor = self._col.aggregate(pipeline)
        return await cursor.to_list(length=limit)
