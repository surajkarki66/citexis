from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import Settings

_client: AsyncIOMotorClient | None = None


def get_client(settings: Settings) -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client


def get_database(settings: Settings) -> AsyncIOMotorDatabase:
    return get_client(settings)[settings.mongodb_db]


async def close_mongodb() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
