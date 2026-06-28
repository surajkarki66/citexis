from typing import Annotated

from fastapi import Depends, Request

from app.config import Settings, get_settings
from app.db.elasticsearch import get_elasticsearch
from app.db.mongodb import get_database
from app.repositories.account_repository import AccountRepository
from app.repositories.paper_repository import PaperRepository
from app.repositories.user_repository import UserInteractionRepository
from app.services.auth.service import AuthService
from app.services.ingestion.pipeline import IngestionPipeline
from app.services.indexing.elasticsearch_indexer import ElasticsearchIndexer
from app.services.indexing.pinecone_indexer import PineconeIndexer
from app.services.explore.queries import ExploreService
from app.services.recommendations.engine import RecommendationEngine
from app.services.search.hybrid import HybridSearchService
from app.services.search.keyword import KeywordSearchService
from app.services.search.semantic import SemanticSearchService


def get_account_repo(request: Request) -> AccountRepository:
    return request.app.state.account_repo


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def get_paper_repo(request: Request) -> PaperRepository:
    return request.app.state.paper_repo


def get_user_repo(request: Request) -> UserInteractionRepository:
    return request.app.state.user_repo


def get_ingestion_pipeline(request: Request) -> IngestionPipeline:
    return request.app.state.ingestion_pipeline


def get_hybrid_search(request: Request) -> HybridSearchService:
    return request.app.state.hybrid_search


def get_keyword_search(request: Request) -> KeywordSearchService:
    return request.app.state.keyword_search


def get_semantic_search(request: Request) -> SemanticSearchService:
    return request.app.state.semantic_search


def get_recommendations(request: Request) -> RecommendationEngine:
    return request.app.state.recommendations


def get_explore(request: Request) -> ExploreService:
    return request.app.state.explore


SettingsDep = Annotated[Settings, Depends(get_settings)]
PaperRepoDep = Annotated[PaperRepository, Depends(get_paper_repo)]
UserRepoDep = Annotated[UserInteractionRepository, Depends(get_user_repo)]
IngestionDep = Annotated[IngestionPipeline, Depends(get_ingestion_pipeline)]
SearchDep = Annotated[HybridSearchService, Depends(get_hybrid_search)]
KeywordSearchDep = Annotated[KeywordSearchService, Depends(get_keyword_search)]
SemanticSearchDep = Annotated[SemanticSearchService, Depends(get_semantic_search)]
RecommendationsDep = Annotated[RecommendationEngine, Depends(get_recommendations)]
ExploreDep = Annotated[ExploreService, Depends(get_explore)]


def wire_app_state(app) -> None:
    """Attach shared services to app.state — called from lifespan."""
    settings = get_settings()
    db = get_database(settings)
    es = get_elasticsearch(settings)

    paper_repo = PaperRepository(db)
    account_repo = AccountRepository(db)
    user_repo = UserInteractionRepository(db)
    es_indexer = ElasticsearchIndexer(settings, es)
    pinecone_indexer = PineconeIndexer(settings)
    keyword_search = KeywordSearchService(settings, es)
    semantic_search = SemanticSearchService(settings)

    app.state.paper_repo = paper_repo
    app.state.account_repo = account_repo
    app.state.user_repo = user_repo
    app.state.auth_service = AuthService(settings, account_repo)
    app.state.ingestion_pipeline = IngestionPipeline(
        settings, paper_repo, es_indexer, pinecone_indexer
    )
    app.state.keyword_search = keyword_search
    app.state.semantic_search = semantic_search
    app.state.hybrid_search = HybridSearchService(settings, paper_repo, keyword_search, semantic_search)
    app.state.recommendations = RecommendationEngine(settings, db, paper_repo, user_repo)
    app.state.explore = ExploreService(db)
