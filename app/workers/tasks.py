import asyncio

from elasticsearch import AsyncElasticsearch
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.core.schemas.paper import PaperCreate
from app.repositories.paper_repository import PaperRepository
from app.services.ingestion.pipeline import IngestionPipeline
from app.services.ingestion.source_registry import SOURCE_NAMES, get_paper_source
from app.services.indexing.elasticsearch_indexer import ElasticsearchIndexer
from app.services.indexing.pinecone_indexer import PineconeIndexer
from app.workers.celery_app import celery_app


def _run_async(coro):
    return asyncio.run(coro)


def _build_pipeline(
    settings,
) -> tuple[IngestionPipeline, AsyncElasticsearch, AsyncIOMotorClient]:
    # Build fresh async clients per task run because asyncio.run() creates
    # and closes a new event loop each invocation.
    mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
    db = mongo_client[settings.mongodb_db]
    paper_repo = PaperRepository(db)
    es_client = AsyncElasticsearch(settings.elasticsearch_url)
    pipeline = IngestionPipeline(
        settings,
        paper_repo,
        ElasticsearchIndexer(settings, es_client),
        PineconeIndexer(settings),
    )
    return pipeline, es_client, mongo_client


async def _ingest_from_source(
    source_name: str,
    query: str,
    limit: int,
    enrich: bool,
) -> dict:
    settings = get_settings()
    source = get_paper_source(source_name, settings)
    pipeline, es_client, mongo_client = _build_pipeline(settings)
    try:
        return await pipeline.ingest_from_source(source, query, limit, enrich=enrich)
    finally:
        await es_client.close()
        mongo_client.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def index_paper_task(self, paper_data: dict) -> str:
    """Index a single paper: embed → Pinecone → Elasticsearch."""
    paper = PaperCreate(**paper_data)

    async def _run():
        settings = get_settings()
        pipeline, es_client, mongo_client = _build_pipeline(settings)
        try:
            return await pipeline.ingest_one(paper)
        finally:
            await es_client.close()
            mongo_client.close()

    try:
        paper_id = _run_async(_run())
        return paper_id or ""
    except Exception as exc:
        raise self.retry(exc=exc) from exc


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def ingest_source_task(
    self,
    source: str,
    query: str,
    limit: int,
    enrich: bool = True,
) -> dict:
    """Fetch from openalex or crossref (DOI) and index each paper."""
    if source not in SOURCE_NAMES:
        return {"error": f"Unknown source '{source}'. Use: {', '.join(SOURCE_NAMES)}"}

    try:
        return _run_async(_ingest_from_source(source, query, limit, enrich))
    except Exception as exc:
        raise self.retry(exc=exc) from exc


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def ingest_openalex_task(self, query: str, limit: int, enrich: bool = True) -> dict:
    """Bulk import from OpenAlex search."""
    try:
        return _run_async(_ingest_from_source("openalex", query, limit, enrich))
    except Exception as exc:
        raise self.retry(exc=exc) from exc


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def ingest_doi_task(self, doi: str, enrich: bool = True) -> dict:
    """Resolve a DOI via Crossref and index (with optional CORE PDF enrichment)."""
    try:
        return _run_async(_ingest_from_source("crossref", doi, 1, enrich))
    except Exception as exc:
        raise self.retry(exc=exc) from exc
