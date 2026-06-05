from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.constants import InteractionType
from app.core.schemas.user import UserInteractionCreate


class UserInteractionRepository:
    COLLECTION = "user_interactions"

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col = db[self.COLLECTION]

    async def record(self, interaction: UserInteractionCreate) -> str:
        if interaction.interaction_type == InteractionType.SAVE:
            existing = await self._col.find_one(
                {
                    "user_id": interaction.user_id,
                    "paper_id": interaction.paper_id,
                    "interaction_type": InteractionType.SAVE,
                }
            )
            if existing:
                return str(existing["_id"])

        result = await self._col.insert_one(interaction.model_dump())
        return str(result.inserted_id)

    async def get_saved_paper_ids(self, user_id: str) -> list[str]:
        cursor = self._col.find(
            {"user_id": user_id, "interaction_type": InteractionType.SAVE},
            {"paper_id": 1, "_id": 0},
        )
        docs = await cursor.to_list(length=1000)
        return [doc["paper_id"] for doc in docs]

    async def remove_save(self, user_id: str, paper_id: str) -> bool:
        result = await self._col.delete_one(
            {
                "user_id": user_id,
                "paper_id": paper_id,
                "interaction_type": InteractionType.SAVE,
            }
        )
        return result.deleted_count > 0

    async def get_co_occurring_papers(self, paper_id: str, limit: int = 20) -> list[str]:
        """Papers frequently saved/viewed with this one (collaborative filtering)."""
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
