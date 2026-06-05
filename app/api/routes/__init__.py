from fastapi import APIRouter

from app.api.routes import authors, explore, interactions, papers, search

api_router = APIRouter()
api_router.include_router(search.router, tags=["search"])
api_router.include_router(papers.router, prefix="/papers", tags=["papers"])
api_router.include_router(authors.router, prefix="/authors", tags=["authors"])
api_router.include_router(explore.router, prefix="/explore", tags=["explore"])
api_router.include_router(interactions.router, prefix="/interactions", tags=["interactions"])
