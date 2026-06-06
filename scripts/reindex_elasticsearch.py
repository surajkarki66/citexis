"""Backfill Elasticsearch from MongoDB.

Usage:
  python -m scripts.reindex_elasticsearch              # dry-run
  python -m scripts.reindex_elasticsearch --apply      # index all papers into ES
"""

import argparse
import asyncio
import sys

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.db.elasticsearch import close_elasticsearch, get_elasticsearch
from app.repositories.paper_repository import PaperRepository
from app.services.indexing.elasticsearch_indexer import ElasticsearchIndexer


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Re-index MongoDB papers into Elasticsearch",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write documents to Elasticsearch (default is dry-run)",
    )
    return parser


async def _main(apply: bool) -> None:
    settings = get_settings()
    es_client = get_elasticsearch(settings)
    mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
    col = mongo_client[settings.mongodb_db][PaperRepository.COLLECTION]
    indexer = ElasticsearchIndexer(settings, es_client)

    indexed = 0
    failed = 0
    failed_reasons: list[str] = []

    try:
        if not await es_client.ping():
            print(f"Elasticsearch not reachable at {settings.elasticsearch_url}", file=sys.stderr)
            raise SystemExit(1)

        total = await col.count_documents({})
        print(f"MongoDB papers: {total}")
        print(f"Target ES index: {settings.elasticsearch_index}")

        if not apply:
            print("Dry-run only. Re-run with --apply to backfill Elasticsearch.")
            return

        cursor = col.find({})
        async for doc in cursor:
            paper_id = str(doc["_id"])
            try:
                await indexer.index_paper(paper_id, doc)
                indexed += 1
                if indexed % 50 == 0:
                    print(f"Indexed {indexed}/{total}…")
            except Exception as exc:
                failed += 1
                failed_reasons.append(f"{paper_id}: {exc.__class__.__name__}: {exc}")

        print(f"Done. Indexed: {indexed}, failed: {failed}")
        for reason in failed_reasons[:10]:
            print(f"  {reason}")
        if len(failed_reasons) > 10:
            print(f"  … and {len(failed_reasons) - 10} more")
        if failed:
            raise SystemExit(1)
    finally:
        mongo_client.close()
        await close_elasticsearch()


if __name__ == "__main__":
    args = _build_parser().parse_args()
    asyncio.run(_main(apply=args.apply))
