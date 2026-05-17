import asyncio

from app.config import get_settings
from app.core.schemas.paper import PaperCreate
from app.db.elasticsearch import get_elasticsearch
from app.db.mongodb import get_database
from app.repositories.paper_repository import PaperRepository
from app.services.ingestion.pipeline import IngestionPipeline
from app.services.ingestion.sources.arxiv import ArxivSource
from app.services.indexing.elasticsearch_indexer import ElasticsearchIndexer
from app.services.indexing.pinecone_indexer import PineconeIndexer
from app.workers.celery_app import celery_app


def _run_async(coro):
    return asyncio.run(coro)


def _build_pipeline() -> IngestionPipeline:
    settings = get_settings()
    db = get_database(settings)
    paper_repo = PaperRepository(db)
    es = get_elasticsearch(settings)
    return IngestionPipeline(
        settings,
        paper_repo,
        ElasticsearchIndexer(settings, es),
        PineconeIndexer(settings),
    )


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def index_paper_task(self, paper_data: dict) -> str:
    """Index a single paper: embed → Pinecone → Elasticsearch."""
    pipeline = _build_pipeline()
    paper = PaperCreate(**paper_data)

    async def _run():
        return await pipeline.ingest_one(paper)

    try:
        return _run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc) from exc


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def ingest_arxiv_task(self, query: str, limit: int) -> dict:
    """Fetch from arXiv and index each paper."""
    source = ArxivSource()
    pipeline = _build_pipeline()

    async def _run():
        papers = await source.fetch(query, limit)
        ids = []
        for paper in papers:
            paper_id = await pipeline.ingest_one(paper)
            ids.append(paper_id)
        return {"imported": len(ids), "paper_ids": ids}

    try:
        return _run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc) from exc
