from app.config import Settings
from app.core.constants import EmbeddingStatus
from app.core.schemas.paper import PaperCreate
from app.repositories.paper_repository import PaperRepository
from app.services.ingestion.normalizer import normalize_paper
from app.services.ingestion.source_registry import get_paper_source
from app.services.ingestion.sources.base import PaperSource
from app.services.ingestion.sources.core_enricher import CoreEnricher
from app.services.indexing.elasticsearch_indexer import ElasticsearchIndexer
from app.services.indexing.pinecone_indexer import PineconeIndexer


class IngestionPipeline:
    """
    Fetch → normalize → MongoDB → Pinecone → Elasticsearch.
    Long-running steps are triggered via Celery tasks in production.
    """

    def __init__(
        self,
        settings: Settings,
        paper_repo: PaperRepository,
        es_indexer: ElasticsearchIndexer,
        pinecone_indexer: PineconeIndexer,
    ) -> None:
        self._settings = settings
        self._papers = paper_repo
        self._es = es_indexer
        self._pinecone = pinecone_indexer
        self._core = CoreEnricher(settings)

    async def ingest_one(self, paper: PaperCreate, *, enrich: bool = True) -> str | None:
        if enrich:
            paper = await self._core.enrich(paper)
        normalized = normalize_paper(paper)
        paper_id = await self._papers.create_if_new(normalized)
        if not paper_id:
            return None
        await self.index_paper(paper_id)
        return paper_id

    async def ingest_from_source(
        self,
        source: PaperSource,
        query: str,
        limit: int,
        *,
        enrich: bool = True,
    ) -> dict:
        papers = await source.fetch(query, limit)
        return await self.ingest_many(papers, enrich=enrich)

    async def ingest_by_source_name(
        self,
        source_name: str,
        query: str,
        limit: int,
        *,
        enrich: bool = True,
    ) -> dict:
        source = get_paper_source(source_name, self._settings)
        return await self.ingest_from_source(source, query, limit, enrich=enrich)

    async def ingest_many(
        self,
        papers: list[PaperCreate],
        *,
        enrich: bool = True,
    ) -> dict:
        imported: list[str] = []
        skipped: list[str] = []
        failed: list[str] = []
        failed_reasons: list[str] = []

        for paper in papers:
            label = paper.doi or paper.title
            try:
                paper_id = await self.ingest_one(paper, enrich=enrich)
                if paper_id:
                    imported.append(paper_id)
                else:
                    skipped.append(label)
            except Exception as exc:
                failed.append(label)
                failed_reasons.append(
                    f"{label}: {exc.__class__.__name__}: {exc}"
                )

        return {
            "imported": len(imported),
            "skipped": len(skipped),
            "failed": len(failed),
            "paper_ids": imported,
            "skipped_items": skipped,
            "failed_items": failed,
            "failed_reasons": failed_reasons,
        }

    async def index_paper(self, paper_id: str) -> None:
        await self._papers.update_status(paper_id, EmbeddingStatus.PROCESSING)
        doc = await self._papers.get_by_id(paper_id)
        if not doc:
            return

        try:
            await self._pinecone.upsert_paper(paper_id, doc)
            await self._es.index_paper(paper_id, doc)
            await self._papers.update_status(
                paper_id,
                EmbeddingStatus.INDEXED,
                pinecone_id=paper_id,
                es_id=paper_id,
            )
        except Exception:
            await self._papers.update_status(paper_id, EmbeddingStatus.FAILED)
            raise

    async def delete_paper(self, paper_id: str) -> bool:
        """Delete paper from Pinecone + Elasticsearch + MongoDB."""
        doc = await self._papers.get_by_id(paper_id)
        if not doc:
            return False

        await self._pinecone.delete_paper(paper_id)
        await self._es.delete_paper(paper_id)
        return await self._papers.delete_by_id(paper_id)
