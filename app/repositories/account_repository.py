from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.constants import UserRole
from app.core.schemas.auth import UserInDB


class AccountRepository:
    COLLECTION = "users"

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col = db[self.COLLECTION]

    async def get_by_email(self, email: str) -> dict | None:
        return await self._col.find_one({"email": email.lower()})

    async def get_by_id(self, user_id: str) -> dict | None:
        if not ObjectId.is_valid(user_id):
            return None
        return await self._col.find_one({"_id": ObjectId(user_id)})

    async def create(self, email: str, password_hash: str, role: UserRole = UserRole.USER) -> str:
        now = datetime.now(UTC)
        result = await self._col.insert_one(
            {
                "email": email.lower(),
                "password_hash": password_hash,
                "role": role.value,
                "is_active": True,
                "created_at": now,
            }
        )
        return str(result.inserted_id)

    async def count_all(self) -> int:
        return await self._col.count_documents({})

    async def upsert_bootstrap_admin(self, email: str, password_hash: str) -> None:
        await self._col.update_one(
            {"email": email.lower()},
            {
                "$set": {
                    "email": email.lower(),
                    "password_hash": password_hash,
                    "role": UserRole.ADMIN.value,
                    "is_active": True,
                },
                "$setOnInsert": {"created_at": datetime.now(UTC)},
            },
            upsert=True,
        )

    @staticmethod
    def to_user(doc: dict) -> UserInDB:
        return UserInDB.model_validate({**doc, "_id": str(doc["_id"])})
