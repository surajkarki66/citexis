from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.schemas.user import UserInteractionCreate


class UserInteractionRepository:
    COLLECTION = "user_interactions"

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col = db[self.COLLECTION]

    async def record(self, interaction: UserInteractionCreate) -> str:
        result = await self._col.insert_one(interaction.model_dump())
        return str(result.inserted_id)

    async def get_co_occurring_papers(self, paper_id: str, limit: int = 20) -> list[str]:
        """Papers frequently saved/viewed with this one — Phase 3 collaborative filtering."""
        pipeline = [
            {"$match": {"paper_id": paper_id}},
            {"$group": {"_id": "$user_id"}},
            {
                "$lookup": {
                    "from": self.COLLECTION,
                    "localField": "_id",
                    "foreignField": "user_id",
                    "as": "other",
                }
            },
            {"$unwind": "$other"},
            {"$match": {"other.paper_id": {"$ne": paper_id}}},
            {"$group": {"_id": "$other.paper_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]
        cursor = self._col.aggregate(pipeline)
        rows = await cursor.to_list(length=limit)
        return [row["_id"] for row in rows]
