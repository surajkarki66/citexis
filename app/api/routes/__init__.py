from fastapi import APIRouter

from app.api.routes import auth, authors, explore, interactions, papers, search, tasks

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(search.router, tags=["search"])
api_router.include_router(papers.router, prefix="/papers", tags=["papers"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(authors.router, prefix="/authors", tags=["authors"])
api_router.include_router(explore.router, prefix="/explore", tags=["explore"])
api_router.include_router(interactions.router, prefix="/interactions", tags=["interactions"])
