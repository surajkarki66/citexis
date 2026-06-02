"""Clean orphaned Elasticsearch/Pinecone records not found in MongoDB.

Usage:
  python -m scripts.cleanup_orphan_indexes              # dry-run
  python -m scripts.cleanup_orphan_indexes --apply      # actually delete
"""

import argparse
import asyncio
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.db.elasticsearch import get_elasticsearch
from app.db.pinecone_client import get_index


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cleanup orphaned search index records")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete detected orphan IDs from Elasticsearch and Pinecone",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=200,
        help="Batch size for delete operations (default: 200)",
    )
    return parser


async def _load_mongo_ids(mongo_client: AsyncIOMotorClient, db_name: str) -> set[str]:
    col = mongo_client[db_name]["papers"]
    ids: set[str] = set()
    cursor = col.find({}, {"_id": 1})
    async for doc in cursor:
        ids.add(str(doc["_id"]))
    return ids


async def _load_es_ids(es_client, index_name: str) -> list[str]:
    ids: list[str] = []
    scroll_id: str | None = None
    try:
        response = await es_client.search(
            index=index_name,
            size=1000,
            scroll="2m",
            sort=["_doc"],
            _source=False,
        )
        scroll_id = response.get("_scroll_id")
        hits = response.get("hits", {}).get("hits", [])
        while hits:
            ids.extend(str(hit["_id"]) for hit in hits)
            response = await es_client.scroll(scroll_id=scroll_id, scroll="2m")
            scroll_id = response.get("_scroll_id")
            hits = response.get("hits", {}).get("hits", [])
    finally:
        if scroll_id:
            await es_client.clear_scroll(scroll_id=scroll_id, ignore=[404])
    return ids


def _pinecone_delete_sync(index: Any, namespace: str, ids: list[str]) -> None:
    if not ids:
        return
    delete_records = getattr(index, "delete_records", None)
    if callable(delete_records):
        delete_records(namespace=namespace, ids=ids)
        return

    delete = getattr(index, "delete", None)
    if callable(delete):
        delete(ids=ids, namespace=namespace)


async def _delete_es_ids(es_client, index_name: str, ids: list[str]) -> None:
    for paper_id in ids:
        await es_client.delete(index=index_name, id=paper_id, ignore=[404])


async def _main(apply_changes: bool, batch_size: int) -> None:
    settings = get_settings()
    es_client = get_elasticsearch(settings)
    mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
    pinecone_index = get_index(settings)

    try:
        mongo_ids = await _load_mongo_ids(mongo_client, settings.mongodb_db)
        es_ids = await _load_es_ids(es_client, settings.elasticsearch_index)
        orphan_ids = [paper_id for paper_id in es_ids if paper_id not in mongo_ids]

        print(f"Mongo papers: {len(mongo_ids)}")
        print(f"Elasticsearch records: {len(es_ids)}")
        print(f"Orphan IDs detected: {len(orphan_ids)}")
        if orphan_ids:
            print(f"Sample orphan IDs: {orphan_ids[:10]}")

        if not apply_changes:
            print("Dry-run only. Re-run with --apply to delete orphans.")
            return

        for i in range(0, len(orphan_ids), batch_size):
            batch = orphan_ids[i : i + batch_size]
            await _delete_es_ids(es_client, settings.elasticsearch_index, batch)
            await asyncio.to_thread(
                _pinecone_delete_sync,
                pinecone_index,
                settings.pinecone_namespace,
                batch,
            )

        print(f"Deleted {len(orphan_ids)} orphan IDs from Elasticsearch and Pinecone.")
    finally:
        mongo_client.close()
        await es_client.close()


if __name__ == "__main__":
    args = _build_parser().parse_args()
    asyncio.run(_main(apply_changes=args.apply, batch_size=args.batch_size))
