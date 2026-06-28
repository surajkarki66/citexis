"""Create Elasticsearch papers index and backfill when out of sync.

Run: python -m scripts.setup_es_index

Used by the es-init Docker service on compose up.
"""

import asyncio
import sys

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import Settings, get_settings
from app.db.elasticsearch import PAPERS_INDEX_MAPPING, close_elasticsearch, get_elasticsearch
from app.repositories.paper_repository import PaperRepository
from scripts.reindex_elasticsearch import backfill_from_mongodb


async def _wait_for_elasticsearch(client, url: str, attempts: int = 30, delay: float = 2.0) -> None:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            if await client.ping():
                return
        except Exception as exc:
            last_error = exc
        print(f"Waiting for Elasticsearch at {url} ({attempt}/{attempts})…")
        await asyncio.sleep(delay)
    message = f"Elasticsearch not ready at {url}"
    if last_error:
        raise RuntimeError(message) from last_error
    raise RuntimeError(message)


async def _mongo_paper_count(settings: Settings) -> int | None:
    mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
    try:
        col = mongo_client[settings.mongodb_db][PaperRepository.COLLECTION]
        return await col.count_documents({})
    except Exception as exc:
        print(
            f"Warning: could not reach MongoDB ({exc}); skipping Elasticsearch backfill check.",
            file=sys.stderr,
        )
        return None
    finally:
        mongo_client.close()


async def _ensure_index(client, index: str) -> bool:
    """Create the papers index if missing. Returns True when the index was created."""
    if await client.indices.exists(index=index):
        print(f"Index '{index}' already exists.")
        return False

    await client.indices.create(
        index=index,
        settings=PAPERS_INDEX_MAPPING["settings"],
        mappings=PAPERS_INDEX_MAPPING["mappings"],
    )
    print(f"Created index '{index}'.")
    return True


async def main() -> None:
    settings = get_settings()
    client = get_elasticsearch(settings)
    index = settings.elasticsearch_index
    url = settings.elasticsearch_url
    needs_backfill = False

    try:
        await _wait_for_elasticsearch(client, url)
        created = await _ensure_index(client, index)

        mongo_count = await _mongo_paper_count(settings)
        if mongo_count is None:
            if created:
                print(
                    "New Elasticsearch index created, but MongoDB was unreachable; "
                    "run reindex after MongoDB is available.",
                    file=sys.stderr,
                )
            return

        es_count = int((await client.count(index=index))["count"])

        if mongo_count == 0:
            print("No papers in MongoDB; skipping Elasticsearch backfill.")
            return

        if created or es_count < mongo_count:
            needs_backfill = True
            print(
                f"Elasticsearch backfill needed "
                f"(MongoDB: {mongo_count}, ES: {es_count})."
            )
        else:
            print(f"Elasticsearch in sync with MongoDB ({es_count} papers).")
    except Exception as exc:
        print(
            f"Elasticsearch setup failed for {url} (index: {index})\n"
            f"{type(exc).__name__}: {exc}\n"
            "Ensure Elasticsearch 8.x is running and elasticsearch-py is pinned to 8.x.",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    finally:
        await close_elasticsearch()

    if needs_backfill:
        _, failed = await backfill_from_mongodb(apply=True)
        if failed:
            raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
