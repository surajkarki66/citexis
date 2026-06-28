from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.account_repository import AccountRepository
from app.repositories.paper_repository import PaperRepository
from app.repositories.user_repository import UserInteractionRepository


async def ensure_paper_indexes(db: AsyncIOMotorDatabase) -> None:
    """Idempotent index setup — call at app startup."""
    col = db[PaperRepository.COLLECTION]
    await col.create_index(
        [("doi", 1)],
        unique=True,
        sparse=True,
        name="doi_unique",
    )

    users = db[AccountRepository.COLLECTION]
    await users.create_index([("email", 1)], unique=True, name="email_unique")

    interactions = db[UserInteractionRepository.COLLECTION]
    await interactions.create_index([("paper_id", 1), ("user_id", 1)], name="paper_user")
    await interactions.create_index(
        [("user_id", 1), ("interaction_type", 1)],
        name="user_interaction_type",
    )
