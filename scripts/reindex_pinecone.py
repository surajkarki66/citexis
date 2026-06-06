"""Audit and backfill Pinecone from MongoDB.

Compares MongoDB paper IDs against Pinecone fetch results, then optionally
upserts any missing records.

Usage:
  python -m scripts.reindex_pinecone              # dry-run (audit only)
  python -m scripts.reindex_pinecone --apply      # upsert missing papers
  python -m scripts.reindex_pinecone --apply --all  # re-upsert every paper
"""

import argparse
import asyncio
import sys

from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.core.constants import EmbeddingStatus
from app.db.pinecone_client import get_index
from app.repositories.paper_repository import PaperRepository
from app.services.indexing.pinecone_indexer import PineconeIndexer


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit MongoDB papers against Pinecone and backfill missing vectors",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Upsert missing papers into Pinecone (default is dry-run)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="With --apply, re-upsert every MongoDB paper (not just missing)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for Pinecone fetch/upsert operations (default: 100)",
    )
    return parser


async def _load_mongo_papers(
    mongo_client: AsyncIOMotorClient,
    db_name: str,
) -> dict[str, dict]:
    col = mongo_client[db_name][PaperRepository.COLLECTION]
    papers: dict[str, dict] = {}
    async for doc in col.find({}):
        papers[str(doc["_id"])] = doc
    return papers


def _fetch_pinecone_ids_sync(
    index: Any,
    namespace: str,
    ids: list[str],
) -> set[str]:
    if not ids:
        return set()
    response = index.fetch(ids=ids, namespace=namespace)
    vectors = getattr(response, "vectors", None) or {}
    return set(vectors.keys())


async def _find_missing_ids(
    index: Any,
    namespace: str,
    mongo_ids: list[str],
    batch_size: int,
) -> list[str]:
    present: set[str] = set()
    for i in range(0, len(mongo_ids), batch_size):
        batch = mongo_ids[i : i + batch_size]
        found = await asyncio.to_thread(
            _fetch_pinecone_ids_sync,
            index,
            namespace,
            batch,
        )
        present.update(found)
    return [paper_id for paper_id in mongo_ids if paper_id not in present]


async def _status_breakdown(papers: dict[str, dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for doc in papers.values():
        status = doc.get("embedding_status", "unknown")
        counts[str(status)] = counts.get(str(status), 0) + 1
    return counts


async def _main(apply: bool, reindex_all: bool, batch_size: int) -> None:
    settings = get_settings()
    if not settings.pinecone_api_key:
        print("PINECONE_API_KEY is required", file=sys.stderr)
        raise SystemExit(1)

    mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
    paper_repo = PaperRepository(mongo_client[settings.mongodb_db])
    pinecone_index = get_index(settings)
    pinecone_indexer = PineconeIndexer(settings)

    indexed = 0
    failed = 0
    failed_reasons: list[str] = []

    try:
        papers = await _load_mongo_papers(mongo_client, settings.mongodb_db)
        mongo_ids = sorted(papers.keys())
        missing_ids = await _find_missing_ids(
            pinecone_index,
            settings.pinecone_namespace,
            mongo_ids,
            batch_size,
        )

        print(f"MongoDB papers: {len(mongo_ids)}")
        print(f"Pinecone index: {settings.pinecone_index}")
        print(f"Pinecone namespace: {settings.pinecone_namespace}")
        print(f"Present in Pinecone: {len(mongo_ids) - len(missing_ids)}")
        print(f"Missing from Pinecone: {len(missing_ids)}")

        status_counts = await _status_breakdown(papers)
        if status_counts:
            print("Mongo embedding_status:")
            for status, count in sorted(status_counts.items()):
                print(f"  {status}: {count}")

        if missing_ids:
            print(f"Sample missing IDs: {missing_ids[:10]}")

        stale_status_ids = [
            paper_id
            for paper_id in mongo_ids
            if paper_id not in missing_ids
            and papers[paper_id].get("embedding_status") != EmbeddingStatus.INDEXED
        ]
        if stale_status_ids:
            print(f"Present in Pinecone but not marked indexed in Mongo: {len(stale_status_ids)}")
            print(f"Sample stale status IDs: {stale_status_ids[:10]}")

        if not apply:
            print("Dry-run only. Re-run with --apply to backfill Pinecone.")
            if missing_ids or stale_status_ids:
                raise SystemExit(1)
            return

        target_ids = mongo_ids if reindex_all else missing_ids
        if stale_status_ids and not reindex_all:
            target_ids = sorted(set(target_ids) | set(stale_status_ids))
        if not target_ids:
            print("Nothing to upsert.")
            return

        action = "Re-upserting" if reindex_all else "Backfilling"
        print(f"{action} {len(target_ids)} paper(s) into Pinecone…")

        for _, paper_id in enumerate(target_ids, start=1):
            doc = papers[paper_id]
            try:
                await paper_repo.update_status(paper_id, EmbeddingStatus.PROCESSING)
                await pinecone_indexer.upsert_paper(paper_id, doc)
                await paper_repo.update_status(
                    paper_id,
                    EmbeddingStatus.INDEXED,
                    pinecone_id=paper_id,
                )
                indexed += 1
                if indexed % 50 == 0:
                    print(f"Upserted {indexed}/{len(target_ids)}…")
            except Exception as exc:
                failed += 1
                failed_reasons.append(f"{paper_id}: {exc.__class__.__name__}: {exc}")
                await paper_repo.update_status(paper_id, EmbeddingStatus.FAILED)

        print(f"Done. Upserted: {indexed}, failed: {failed}")
        for reason in failed_reasons[:10]:
            print(f"  {reason}")
        if len(failed_reasons) > 10:
            print(f"  … and {len(failed_reasons) - 10} more")
        if failed:
            raise SystemExit(1)
    finally:
        mongo_client.close()


if __name__ == "__main__":
    args = _build_parser().parse_args()
    asyncio.run(_main(apply=args.apply, reindex_all=args.all, batch_size=args.batch_size))
