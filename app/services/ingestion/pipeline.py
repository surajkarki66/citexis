from app.config import Settings
from app.core.constants import EmbeddingStatus
from app.core.schemas.paper import PaperCreate
from app.repositories.paper_repository import PaperRepository
from app.services.embeddings import get_embedding_service
from app.services.ingestion.normalizer import normalize_paper
from app.services.indexing.elasticsearch_indexer import ElasticsearchIndexer
from app.services.indexing.pinecone_indexer import PineconeIndexer


class IngestionPipeline:
    """
    Fetch → normalize → MongoDB → embed → Pinecone → Elasticsearch.
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
        self._embeddings = get_embedding_service(settings.embedding_model)

    async def ingest_one(self, paper: PaperCreate) -> str:
        normalized = normalize_paper(paper)
        paper_id = await self._papers.create(normalized)
        await self.index_paper(paper_id)
        return paper_id

    async def index_paper(self, paper_id: str) -> None:
        await self._papers.update_status(paper_id, EmbeddingStatus.PROCESSING)
        doc = await self._papers.get_by_id(paper_id)
        if not doc:
            return

        try:
            vector = self._embeddings.embed_paper(
                doc["title"],
                doc.get("abstract", ""),
                doc.get("tags", []),
            )
            await self._pinecone.upsert_paper(paper_id, vector, doc)
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
