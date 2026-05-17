from typing import Annotated

from fastapi import Depends, Request

from app.config import Settings, get_settings
from app.db.elasticsearch import get_elasticsearch
from app.db.mongodb import get_database
from app.repositories.paper_repository import PaperRepository
from app.repositories.user_repository import UserInteractionRepository
from app.services.ingestion.pipeline import IngestionPipeline
from app.services.indexing.elasticsearch_indexer import ElasticsearchIndexer
from app.services.indexing.pinecone_indexer import PineconeIndexer
from app.services.knowledge_graph.queries import KnowledgeGraphService
from app.services.recommendations.engine import RecommendationEngine
from app.services.search.hybrid import HybridSearchService
from app.services.search.keyword import KeywordSearchService
from app.services.search.semantic import SemanticSearchService


def get_paper_repo(request: Request) -> PaperRepository:
    return request.app.state.paper_repo


def get_user_repo(request: Request) -> UserInteractionRepository:
    return request.app.state.user_repo


def get_ingestion_pipeline(request: Request) -> IngestionPipeline:
    return request.app.state.ingestion_pipeline


def get_hybrid_search(request: Request) -> HybridSearchService:
    return request.app.state.hybrid_search


def get_recommendations(request: Request) -> RecommendationEngine:
    return request.app.state.recommendations


def get_knowledge_graph(request: Request) -> KnowledgeGraphService:
    return request.app.state.knowledge_graph


SettingsDep = Annotated[Settings, Depends(get_settings)]
PaperRepoDep = Annotated[PaperRepository, Depends(get_paper_repo)]
UserRepoDep = Annotated[UserInteractionRepository, Depends(get_user_repo)]
IngestionDep = Annotated[IngestionPipeline, Depends(get_ingestion_pipeline)]
SearchDep = Annotated[HybridSearchService, Depends(get_hybrid_search)]
RecommendationsDep = Annotated[RecommendationEngine, Depends(get_recommendations)]
KnowledgeGraphDep = Annotated[KnowledgeGraphService, Depends(get_knowledge_graph)]


def wire_app_state(app) -> None:
    """Attach shared services to app.state — called from lifespan."""
    settings = get_settings()
    db = get_database(settings)
    es = get_elasticsearch(settings)

    paper_repo = PaperRepository(db)
    user_repo = UserInteractionRepository(db)
    es_indexer = ElasticsearchIndexer(settings, es)
    pinecone_indexer = PineconeIndexer(settings)

    app.state.paper_repo = paper_repo
    app.state.user_repo = user_repo
    app.state.ingestion_pipeline = IngestionPipeline(
        settings, paper_repo, es_indexer, pinecone_indexer
    )
    app.state.hybrid_search = HybridSearchService(
        settings,
        paper_repo,
        KeywordSearchService(settings, es),
        SemanticSearchService(settings),
    )
    app.state.recommendations = RecommendationEngine(settings, db, paper_repo, user_repo)
    app.state.knowledge_graph = KnowledgeGraphService(db)
