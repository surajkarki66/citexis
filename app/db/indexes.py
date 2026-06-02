from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.paper_repository import PaperRepository


async def ensure_paper_indexes(db: AsyncIOMotorDatabase) -> None:
    """Idempotent index setup — call at app startup."""
    col = db[PaperRepository.COLLECTION]
    await col.create_index(
        [("doi", 1)],
        unique=True,
        sparse=True,
        name="doi_unique",
    )
